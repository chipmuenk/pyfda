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
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
import numpy as np
from scipy.signal import ellipord
from pyfda.pyfda_lib import fil_save, SOS_AVAIL, lin2unit
from pyfda.pyfda_qt_lib import qfilter_warning

from .common import Common
from ..compat import (QWidget, QFrame, pyqtSignal,
                      QCheckBox, QVBoxLayout, QHBoxLayout)

import logging
logger = logging.getLogger(__name__)

__version__ = "2.0"

filter_classes = {'EllipZeroPhz':'EllipZeroPhz'}

class EllipZeroPhz(QWidget):

#    Since we are also using poles/residues -> let's force zpk
#    if SOS_AVAIL:
#       output format of filter design routines 'zpk' / 'ba' / 'sos'
#        FRMT = 'sos' 
#    else:
    FRMT = 'zpk'
        
    info = """
**Elliptic filters with zero phase**

(also known as Cauer filters) have the steepest rate of transition between the 
frequency response’s passband and stopband of all IIR filters. This comes
at the expense of a constant ripple (equiripple) :math:`A_PB` and :math:`A_SB`
in both pass and stop band. Ringing of the step response is increased in
comparison to Chebychev filters.
 
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
        self.chkComplex   = QCheckBox("ComplexFilter", self)
        self.chkComplex.setToolTip("Designs BP or BS Filter for complex data.")
        self.chkComplex.setObjectName('wdg_lbl_el')
        self.chkComplex.setChecked(False)

        #--------------------------------------------------
        #  Layout for filter optional subwidgets
        self.layHWin = QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        #self.layHWin.addWidget(self.chkComplex)
        self.layHWin.addStretch() 
        self.layHWin.setContentsMargins(0,0,0,0)

        # Widget containing all subwidgets
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layHWin)

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
            ampSB = np.sqrt(ampPB)
            ampPB = np.sqrt(1+ampPB)-1
        else:
            ampPB = np.sqrt(1+ampSB)-1
            ampSB = np.sqrt(ampSB)
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
        residues = np.zeros(norder, complex)
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

        pA = np.conj(1./p)   # antiCausal poles
        zA = np.conj(z)      # antiCausal zeros (store reciprocal)
        rA = np.conj(r)      # antiCausal residues (to start)
        rC = np.zeros(nn, complex)

#       Adjust residues. Causal part first.
        for j in range(nn):

#           Evaluate the anticausal filter at each causal pole
            tmpx = rA / (1. - p[j]/pA)
            ztmp = g + np.sum(tmpx)

#           Adjust residue
            rC[j] = r[j]*ztmp

#       anticausal residues are just conjugates of causal residues
#        r3 = np.conj(r2)

#       Compute the constant term
        dc2 = (g + np.sum(r))*g - np.sum(rC)

#       Populate output (2nn elements)
        gn = dc2.real

#       Drop complex poles/residues in LHP, keep only UHP

        pA = np.conj(p)  #store AntiCasual pole (reciprocal)
        p0 = np.zeros(int(nn/2), complex)
        r0 = np.zeros(int(nn/2), complex)
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
        self.sig_tx.emit({'sender':__name__, 'filt_changed':'ellip_zero'})

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
    from ..compat import QApplication
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

#-----------------------------------------------------------------------------

