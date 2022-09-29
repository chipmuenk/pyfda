# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design elliptic Filters (LP, HP, BP, BS) with zero phase in fixed or minimum order,
return the filter design in zeros, poles, gain (zpk) format

Attention:
This class is re-instantiated dynamically every time the filter design method
is selected, calling its __init__ method.

API version info:
    2.0: initial working release
    
    2.1: Remove method destruct_UI and attributes self.wdg and self.hdl

   :2.2: Rename `filter_classes` -> `classes`    
    
    
"""
import os, io
import scipy.signal as sig
from numpy import conj, sqrt, sum, zeros
import numpy as np
from scipy.signal import ellipord
from pyfda.libs.pyfda_lib import fil_save, lin2unit
from pyfda.libs.pyfda_qt_lib import qfilter_warning
from pyfda.libs.pyfda_io_lib import extract_file_ext
import pyfda.libs.pyfda_dirs as dirs

from .common import Common
from pyfda.libs.compat import (QWidget, QFrame, pyqtSignal, QFileDialog,
                      QCheckBox, QVBoxLayout, QHBoxLayout, QPushButton)

import logging
logger = logging.getLogger(__name__)

__version__ = "2.2"

classes = {'EllipZeroPhz':'EllipZeroPhz'} #: Dict containing class name : display name

class EllipZeroPhz(QWidget):

#    Since we are also using poles/residues -> let's force zpk
    FRMT = 'zpk'
        
    info = """
**Elliptic filters with zero phase**

(also known as Cauer filters) have the steepest rate of transition between the 
frequency response’s passband and stopband of all IIR filters. This comes
at the expense of a constant ripple (equiripple) :math:`A_PB` and :math:`A_SB`
in both pass and stop band. Ringing of the step response is increased in
comparison to Chebyshev filters.
 
As the passband ripple :math:`A_PB` approaches 0, the elliptical filter becomes
a Chebyshev type II filter. As the stopband ripple :math:`A_SB` approaches 0,
it becomes a Chebyshev type I filter. As both approach 0, becomes a Butterworth
filter (butter).

For the filter design, the order :math:`N`, minimum stopband attenuation
:math:`A_SB` and the critical frequency / frequencies :math:`F_PB` where the 
gain first drops below the maximum passband ripple :math:`-A_PB` have to be specified.

The ``ellipord()`` helper routine calculates the minimum order :math:`N` and 
critical passband frequency :math:`F_C` from pass and stop band specifications.

The Zero Phase Elliptic Filter squares an elliptic filter designed in
a way to produce the required Amplitude specifications. So initially the
amplitude specs design an elliptic filter with the square root of the amp specs.
The filter is then squared to produce a zero phase filter.
The filter coefficients are applied to the signal data in a backward and forward
time fashion.  This filter can only be applied to stored signal data (not
real-time streaming data that comes in a forward time order).

We are forcing the order N of the filter to be even.  This simplifies the poles/zeros
to be complex (no real values).

**Design routines:**

``scipy.signal.ellip()``, ``scipy.signal.ellipord()``

        """
    sig_tx = pyqtSignal(object)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        QWidget.__init__(self)

        self.ft = 'IIR'

        c = Common()
        self.rt_dict = c.rt_base_iir

        self.rt_dict_add = {
            'COM':{'man':{'msg':('a',
             "Enter the filter order <b><i>N</i></b>, the minimum stop "
             "band attenuation <b><i>A<sub>SB</sub></i></b> and frequency or "
             "frequencies <b><i>F<sub>C</sub></i></b>  where gain first drops "
             "below the max passband ripple <b><i>-A<sub>PB</sub></i></b> .")}},
            'LP': {'man':{}, 'min':{}},
            'HP': {'man':{}, 'min':{}},
            'BS': {'man':{}, 'min':{}},
            'BP': {'man':{}, 'min':{}},
            }

        self.info_doc = []
        self.info_doc.append('ellip()\n========')
        self.info_doc.append(sig.ellip.__doc__)
        self.info_doc.append('ellipord()\n==========')
        self.info_doc.append(ellipord.__doc__)

    #--------------------------------------------------------------------------
    def construct_UI(self):
        """
        Create additional subwidget(s) needed for filter design:
        These subwidgets are instantiated dynamically when needed in
        select_filter.py using the handle to the filter instance, fb.fil_inst.
        """
# =============================================================================
#         self.chkComplex   = QCheckBox("ComplexFilter", self)
#         self.chkComplex.setToolTip("Designs BP or BS Filter for complex data.")
#         self.chkComplex.setObjectName('wdg_lbl_el')
#         self.chkComplex.setChecked(False)
# 
# =============================================================================
        self.butSave = QPushButton(self)
        self.butSave.setText("SAVE")
        self.butSave.setToolTip("Save filter in proprietary format")
        
        #--------------------------------------------------
        #  Layout for filter optional subwidgets
        self.layHWin = QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        #self.layHWin.addWidget(self.chkComplex)
        self.layHWin.addWidget(self.butSave)
        self.layHWin.addStretch() 
        self.layHWin.setContentsMargins(0,0,0,0)

        # Widget containing all subwidgets
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layHWin)
        
        self.butSave.clicked.connect(self.save_filter)

    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        For zero phase filter, we take square root of amplitude specs
        since we later square filter.  Define design around smallest amp spec
        """
        # Frequencies are normalized to f_Nyq = f_S/2, ripple specs are in dB
        self.analog = False # set to True for analog filters
        self.manual = False # default is normal design
        self.N     = int(fil_dict['N'])

        # force N to be even
        if (self.N % 2) == 1:
            self.N += 1
        self.F_PB  = fil_dict['F_PB'] * 2
        self.F_SB  = fil_dict['F_SB'] * 2
        self.F_PB2 = fil_dict['F_PB2'] * 2
        self.F_SB2 = fil_dict['F_SB2'] * 2
        self.F_PBC = None

        # find smallest spec'd linear value and rewrite dictionary
        ampPB = fil_dict['A_PB']
        ampSB = fil_dict['A_SB']

        # take square roots of amp specs so resulting squared
        # filter will meet specifications
        if (ampPB < ampSB):
            ampSB = sqrt(ampPB)
            ampPB = sqrt(1+ampPB)-1
        else:
            ampPB = sqrt(1+ampSB)-1
            ampSB = sqrt(ampSB)
        self.A_PB = lin2unit(ampPB, 'IIR', 'A_PB', unit='dB')
        self.A_SB = lin2unit(ampSB, 'IIR', 'A_SB', unit='dB')
        #logger.warning("design with "+str(self.A_PB)+","+str(self.A_SB))

        # ellip filter routines support only one amplitude spec for
        # pass- and stop band each
        if str(fil_dict['rt']) == 'BS':
            fil_dict['A_PB2'] = self.A_PB
        elif str(fil_dict['rt']) == 'BP':
            fil_dict['A_SB2'] = self.A_SB

#   partial fraction expansion to define residue vector
    def _partial(self, k, p, z, norder):
        # create diff array
        diff = p - z

        # now compute residual vector
        cone = complex(1.,0.)
        residues = zeros(norder, complex)
        for i in range(norder):
            residues[i] =  k * (diff[i] / p[i])
            for j in range(norder):
                if (j != i):
                    residues[i] = residues[i] * (cone + diff[j]/(p[i] - p[j]))

        # now compute DC term for new expansion
        sumRes = 0.
        for i in range(norder):
            sumRes = sumRes + residues[i].real

        dc = k - sumRes

        return (dc, residues)

#
# Take a causal filter and square it. The result has the square
#  of the amplitude response of the input, and zero phase. Filter
#  is noncausal.
# Input:
#   k - gain in pole/zero form
#   p - numpy array of poles
#   z - numpy array of zeros
#   g - gain in pole/residue form
#   r - numpy array of residues
#   nn- order of filter

# Output:
#   kn - new gain (pole/zero)
#   pn - new poles
#   zn - new zeros  (numpy array)
#   gn - new gain (pole/residue)
#   rn - new residues

    def _sqCausal (self, k, p, z, g, r, nn):

#       Anticausal poles have conjugate-reciprocal symmetry
#       Starting anticausal residues are conjugates (adjusted below)

        pA = conj(1./p)   # antiCausal poles
        zA = conj(z)      # antiCausal zeros (store reciprocal)
        rA = conj(r)      # antiCausal residues (to start)
        rC = zeros(nn, complex)

#       Adjust residues. Causal part first.
        for j in range(nn):

#           Evaluate the anticausal filter at each causal pole
            tmpx = rA / (1. - p[j]/pA)
            ztmp = g + sum(tmpx)

#           Adjust residue
            rC[j] = r[j]*ztmp

#       anticausal residues are just conjugates of causal residues
#        r3 = np.conj(r2)

#       Compute the constant term
        dc2 = (g + sum(r))*g - sum(rC)

#       Populate output (2nn elements)
        gn = dc2.real

#       Drop complex poles/residues in LHP, keep only UHP

        pA = conj(p)  #store AntiCasual pole (reciprocal)
        p0 = zeros(int(nn/2), complex)
        r0 = zeros(int(nn/2), complex)
        cnt = 0
        for j in range(nn):
            if (p[j].imag > 0.0):
                p0[cnt] = p[j]
                r0[cnt] = rC[j]
                cnt = cnt+1

#       Let operator know we squared filter
#        logger.info('After squaring filter, order: '+str(nn*2))

#       For now and our case, only store causal residues
#       Filters are symmetric and can generate antiCausal residues
        return (pA, zA, gn, p0, r0)


    def _test_N(self):
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 30:
            return qfilter_warning(self, self.N, "Zero-phase Elliptic")
        else:
            return True

#   custom save of filter dictionary
    def _save(self, fil_dict, arg):
        """
        First design initial elliptic filter meeting sqRoot Amp specs;
         - Then create residue vector from poles/zeros;
         - Then square filter (k,p,z and dc,p,r) to get zero phase filter;
         - Then Convert results of filter design to all available formats (pz, pr, ba, sos)
        and store them in the global filter dictionary.

        Corner frequencies and order calculated for minimum filter order are
        also stored to allow for an easy subsequent manual filter optimization.
        """
        fil_save(fil_dict, arg, self.FRMT, __name__)

        # For min. filter order algorithms, update filter dict with calculated
        # new values for filter order N and corner frequency(s) F_PBC

        fil_dict['N'] = self.N
        if str(fil_dict['fo']) == 'min':
            if str(fil_dict['rt']) == 'LP' or str(fil_dict['rt']) == 'HP':
#               HP or LP - single  corner frequency
                fil_dict['F_PB'] = self.F_PBC / 2.
            else: # BP or BS - two corner frequencies
                fil_dict['F_PB'] = self.F_PBC[0] / 2.
                fil_dict['F_PB2'] = self.F_PBC[1] / 2.

#       Now generate poles/residues for custom file save of new parameters
        if (not self.manual):
            z = fil_dict['zpk'][0]
            p = fil_dict['zpk'][1]
            k = fil_dict['zpk'][2]
            n = len(z)
            gain, residues = self._partial (k, p, z, n)

            pA, zA, gn, pC, rC = self._sqCausal (k, p, z, gain, residues, n)
            fil_dict['rpk'] = [rC, pC, gn]

#           save antiCausal b,a (nonReciprocal) also [easier to compute h(n)
            try:
               fil_dict['baA'] = sig.zpk2tf(zA, pA, k)
            except Exception as e:
               logger.error(e)

#       'rpk' is our signal that this is a non-Causal filter with zero phase
#       inserted into fil dictionary after fil_save and convert
        # sig_tx -> select_filter -> filter_specs   
        self.emit({'filt_changed': 'ellip_zero'})

#------------------------------------------------------------------------------

    def save_filter(self):
        file_filters = ("Text file pole/residue (*.txt_rpk)")
        dlg = QFileDialog(self)
        # return selected file name (with or without extension) and filter (Linux: full text)
        file_name, file_type = dlg.getSaveFileName_(
                caption = "Save filter as", directory=dirs.last_file_dir,
                filter = file_filters)
    
        file_name = str(file_name)  # QString -> str() needed for Python 2.x
        # Qt5 has QFileDialog.mimeTypeFilters(), but under Qt4 the mime type cannot
        # be extracted reproducibly across file systems, so it is done manually:
    
        for t in extract_file_ext(file_filters): # get a list of file extensions
            if t in str(file_type):
                file_type = t           # return the last matching extension
    
        if file_name != "": # cancelled file operation returns empty string
    
            # strip extension from returned file name (if any) + append file type:
            file_name = os.path.splitext(file_name)[0] + file_type
    
            file_type_err = False
            try:

                # save as a custom residue/pole text output for apply with custom tool
                # make sure we have the residues
                if 'rpk' in fb.fil[0]:
                    with io.open(file_name, 'w', encoding="utf8") as f:
                        self.file_dump(f)
                else:
                    file_type_err = True
                    logger.error('Filter has no residues/poles, cannot save as *.txt_rpk file')
                if not file_type_err:
                    logger.info('Successfully saved filter as\n\t"{0}"'.format(file_name))
                    dirs.last_file_dir = os.path.dirname(file_name) # save new dir
    
            except IOError as e:
                logger.error('Failed saving "{0}"!\n{1}'.format(file_name, e))
   
 
#------------------------------------------------------------------------------
       
    def file_dump (self, fOut):
        """
        Dump file out in custom text format that apply tool can read to know filter coef's
        """

#       Fixed format widths for integers and doubles
        intw = '10'
        dblW = 27
        frcW = 20

#       Fill up character string with filter output
        filtStr = '# IIR filter\n'

#       parameters that made filter (choose smallest eps)
#       Amp is stored in Volts (linear units)
#       the second amp terms aren't really used (for ellip filters)

        FA_PB  = fb.fil[0]['A_PB']
        FA_SB  = fb.fil[0]['A_SB']
        FAmp = min(FA_PB, FA_SB)

#       Freq terms in radians so move from -1:1 to -pi:pi
        f_lim = fb.fil[0]['freqSpecsRange']
        f_unit = fb.fil[0]['freq_specs_unit']

        F_S   = fb.fil[0]['f_S']
        if fb.fil[0]['freq_specs_unit'] == 'f_S':
            F_S = F_S*2
        F_SB  = fb.fil[0]['F_SB'] * F_S * np.pi
        F_SB2 = fb.fil[0]['F_SB2'] * F_S * np.pi
        F_PB  = fb.fil[0]['F_PB'] * F_S * np.pi
        F_PB2 = fb.fil[0]['F_PB2'] * F_S * np.pi

#       Determine pass/stop bands depending on filter response type
        passMin = []
        passMax = []
        stopMin = []
        stopMax = []

        if fb.fil[0]['rt'] == 'LP':
            passMin = [ -F_PB,      0,    0]
            passMax = [  F_PB,      0,    0]
            stopMin = [-np.pi,   F_SB,    0]
            stopMax = [ -F_SB,  np.pi,    0]
            f1 = F_PB
            f2 = F_SB
            f3 = f4 = 0
            Ftype = 1
            Fname = 'Low_Pass'

        if fb.fil[0]['rt'] == 'HP':
            passMin = [-np.pi,   F_PB,    0]
            passMax = [ -F_PB,  np.pi,    0]
            stopMin = [ -F_SB,      0,    0]
            stopMax = [  F_SB,      0,    0]
            f1 = F_SB
            f2 = F_PB
            f3 = f4 = 0
            Ftype = 2
            Fname = 'Hi_Pass'

        if fb.fil[0]['rt'] == 'BS':
            passMin = [-np.pi,  -F_PB, F_PB2]
            passMax = [-F_PB2,   F_PB, np.pi]
            stopMin = [-F_SB2,   F_SB,     0]
            stopMax = [ -F_SB,  F_SB2,     0]
            f1 = F_PB
            f2 = F_SB
            f3 = F_SB2
            f4 = F_PB2
            Ftype = 4
            Fname = 'Band_Stop'

        if fb.fil[0]['rt'] == 'BP':
            passMin = [-F_PB2,   F_PB,     0]
            passMax = [ -F_PB,  F_PB2,     0]
            stopMin = [-np.pi,  -F_SB, F_SB2]
            stopMax = [-F_SB2,   F_SB, np.pi]
            f1 = F_SB
            f2 = F_PB
            f3 = F_PB2
            f4 = F_SB2
            Ftype = 3
            Fname = 'Band_Pass'

        filtStr = filtStr + '{:{align}{width}}'.format('10',align='>',width=intw)+ ' IIRFILT_4SYM\n'
        filtStr = filtStr + '{:{align}{width}}'.format(str(Ftype),align='>',width=intw)+ ' ' + Fname + '\n'
        filtStr = filtStr + '{:{d}.{p}f}'.format(FAmp,d=dblW,p=frcW) + '\n'
        filtStr = filtStr + '{: {d}.{p}f}'.format(passMin[0],d=dblW,p=frcW)
        filtStr = filtStr + '{: {d}.{p}f}'.format(passMax[0],d=dblW,p=frcW) + '\n'
        filtStr = filtStr + '{: {d}.{p}f}'.format(passMin[1],d=dblW,p=frcW)
        filtStr = filtStr + '{: {d}.{p}f}'.format(passMax[1],d=dblW,p=frcW) + '\n'
        filtStr = filtStr + '{: {d}.{p}f}'.format(passMin[2],d=dblW,p=frcW)
        filtStr = filtStr + '{: {d}.{p}f}'.format(passMax[2],d=dblW,p=frcW) + '\n'
        filtStr = filtStr + '{: {d}.{p}f}'.format(stopMin[0],d=dblW,p=frcW)
        filtStr = filtStr + '{: {d}.{p}f}'.format(stopMax[0],d=dblW,p=frcW) + '\n'
        filtStr = filtStr + '{: {d}.{p}f}'.format(stopMin[1],d=dblW,p=frcW)
        filtStr = filtStr + '{: {d}.{p}f}'.format(stopMax[1],d=dblW,p=frcW) + '\n'
        filtStr = filtStr + '{: {d}.{p}f}'.format(stopMin[2],d=dblW,p=frcW)
        filtStr = filtStr + '{: {d}.{p}f}'.format(stopMax[2],d=dblW,p=frcW) + '\n'
        filtStr = filtStr + '{: {d}.{p}f}'.format(f1,d=dblW,p=frcW)
        filtStr = filtStr + '{: {d}.{p}f}'.format(f2,d=dblW,p=frcW) + '\n'
        filtStr = filtStr + '{: {d}.{p}f}'.format(f3,d=dblW,p=frcW)
        filtStr = filtStr + '{: {d}.{p}f}'.format(f4,d=dblW,p=frcW) + '\n'

#       move pol/res/gain into terms we need
        Fdc  = fb.fil[0]['rpk'][2]
        rC   = fb.fil[0]['rpk'][0]
        pC   = fb.fil[0]['rpk'][1]
        Fnum = len(pC)

#       Gain term
        filtStr = filtStr + '{: {d}.{p}e}'.format(Fdc,d=dblW,p=frcW) + '\n'

#       Real pole count inside the unit circle (none of these)

        filtStr = filtStr + '{:{align}{width}}'.format(str(0),align='>',width=intw) + '\n'

#       Complex pole/res count inside the unit circle

        filtStr = filtStr + '{:{i}d}'.format(Fnum, i=intw)+ '\n'

#       Now dump poles/residues
        for j in range(Fnum):
            filtStr = filtStr + '{:{i}d}'.format(j, i=intw) + ' '
            filtStr = filtStr + '{: {d}.{p}e}'.format(rC[j].real,d=dblW,p=frcW) + ' '
            filtStr = filtStr + '{: {d}.{p}e}'.format(rC[j].imag,d=dblW,p=frcW) + ' '
            filtStr = filtStr + '{: {d}.{p}e}'.format(pC[j].real,d=dblW,p=frcW) + ' '
            filtStr = filtStr + '{: {d}.{p}e}'.format(pC[j].imag,d=dblW,p=frcW) + '\n'

#       Real pole count outside the unit circle (none of these)
        filtStr = filtStr + '{:{align}{width}}'.format(str(0),align='>',width=intw) + '\n'

#       Complex pole count outside the unit circle (none of these)
        filtStr = filtStr + '{:{align}{width}}'.format(str(0),align='>',width=intw) + '\n'

#       Now write huge text string to file
        fOut.write(filtStr)
      


#------------------------------------------------------------------------------
#
#         DESIGN ROUTINES
#
#------------------------------------------------------------------------------

    # LP: F_PB < F_stop -------------------------------------------------------
    def LPmin(self, fil_dict):
        """Elliptic LP filter, minimum order"""
        self._get_params(fil_dict)
        self.N, self.F_PBC = ellipord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,                                                        analog=self.analog)
#       force even N
        if (self.N%2)== 1:
            self.N += 1
        if not self._test_N():
            return -1              
        #logger.warning("and "+str(self.F_PBC) + " " + str(self.N))
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                            btype='low', analog=self.analog, output=self.FRMT))

    def LPman(self, fil_dict):
        """Elliptic LP filter, manual order"""
        self._get_params(fil_dict)
        if not self._test_N():
            return -1  
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PB,
                            btype='low', analog=self.analog, output=self.FRMT))

    # HP: F_stop < F_PB -------------------------------------------------------
    def HPmin(self, fil_dict):
        """Elliptic HP filter, minimum order"""
        self._get_params(fil_dict)
        self.N, self.F_PBC = ellipord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                          analog=self.analog)
#       force even N
        if (self.N%2)== 1:
            self.N += 1
        if not self._test_N():
            return -1  
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='highpass', analog=self.analog, output=self.FRMT))

    def HPman(self, fil_dict):
        """Elliptic HP filter, manual order"""
        self._get_params(fil_dict)
        if not self._test_N():
            return -1  
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PB,
                        btype='highpass', analog=self.analog, output=self.FRMT))

    # For BP and BS, F_XX have two elements each, A_XX has only one

    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1] --------------------------------
    def BPmin(self, fil_dict):
        """Elliptic BP filter, minimum order"""
        self._get_params(fil_dict)
        self.N, self.F_PBC = ellipord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB, self.A_SB, analog=self.analog)
        #logger.warning(" "+str(self.F_PBC) + " " + str(self.N))
        if (self.N%2)== 1:
            self.N += 1
        if not self._test_N():
            return -1  
        #logger.warning("-"+str(self.F_PBC) + " " + str(self.A_SB))
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='bandpass', analog=self.analog, output=self.FRMT))

    def BPman(self, fil_dict):
        """Elliptic BP filter, manual order"""
        self._get_params(fil_dict)
        if not self._test_N():
            return -1  
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB,
            [self.F_PB,self.F_PB2], btype='bandpass', analog=self.analog,
                                                            output=self.FRMT))

    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1] --------------------------------
    def BSmin(self, fil_dict):
        """Elliptic BP filter, minimum order"""
        self._get_params(fil_dict)
        self.N, self.F_PBC = ellipord([self.F_PB, self.F_PB2],
                                [self.F_SB, self.F_SB2], self.A_PB,self.A_SB,                                                       analog=self.analog)
#       force even N
        if (self.N%2)== 1:
            self.N += 1
        if not self._test_N():
            return -1  
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='bandstop', analog=self.analog, output=self.FRMT))

    def BSman(self, fil_dict):
        """Elliptic BS filter, manual order"""
        self._get_params(fil_dict)
        if not self._test_N():
            return -1  
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB,
            [self.F_PB,self.F_PB2], btype='bandstop', analog=self.analog,
                                                            output=self.FRMT))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from pyfda.libs.compat import QApplication
# importing filterbroker initializes all its globals
    import pyfda.filterbroker as fb

    app = QApplication (sys.argv)

    # ellip filter widget
    filt = EllipZeroPhz()        # instantiate filter
    filt.construct_UI()
    wdg_ma = getattr (filt, 'wdg_fil')

    layVDynWdg = QVBoxLayout()
    layVDynWdg.addWidget(wdg_ma, stretch = 1)

    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][filt.FRMT]) # return results in default format

    form = QFrame()
    form.setFrameStyle (QFrame.StyledPanel|QFrame.Sunken)
    form.setLayout (layVDynWdg)

    form.show()

    app.exec_()
# test using "python -m pyfda.filter_widgets.ellip_zero"
#-----------------------------------------------------------------------------

