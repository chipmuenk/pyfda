# -*- coding: utf-8 -*-
"""
Design ellip-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

Attention:
This class is re-instantiated dynamically every time the filter design method
is selected, calling its __init__ method.

Version info:   
    1.0: initial working release
    1.1: - copy A_PB -> A_PB2 and A_SB -> A_SB2 for BS / BP designs
         - mark private methods as private
    1.2: new API using fil_save (enable SOS features when available)
    1.3: new public methods destruct_UI + construct_UI (no longer called by __init__)    
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
         `FRMT` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
from scipy.signal import ellipord
from pyfda.pyfda_lib import fil_save, SOS_AVAIL, lin2unit
from .common import Common
from ..compat import (QWidget, QFrame, pyqtSignal,
                      QCheckBox, QVBoxLayout, QHBoxLayout)

import logging
logger = logging.getLogger(__name__)

__version__ = "2.0"

filter_classes = {'Ellip':'Elliptic'}
    
class Ellip(QWidget):

    if SOS_AVAIL:
        FRMT = 'sos' # output format of filter design routines 'zpk' / 'ba' / 'sos'
    else:
        FRMT = 'zpk'
        
    info = """
**Elliptic filters**

(also known as Cauer filters) have the steepest rate of transition between the 
frequency response’s passband and stopband of all IIR filters. This comes
at the expense of a constant ripple (equiripple) :math:`A_PB` and :math:`A_SB`
in both pass and stop band. Ringing of the step response is increased in
comparison to Chebychev filters.
 
As the passband ripple :math:`A_PB` approaches 0, the elliptical filter becomes
a Chebyshev type II filter. As the stopband ripple :math:`A_SB` approaches 0,
it becomes a Chebyshev type I filter. As both approach 0, it becomes a Butterworth
filter (butter).

For the filter design, the order :math:`N`, minimum stopband attenuation
:math:`A_SB` and the critical frequency / frequencies :math:`F_PB` where the 
gain first drops below the maximum passband ripple :math:`-A_PB` have to be specified.

The ``ellipord()`` helper routine calculates the minimum order :math:`N` and the 
critical passband frequency :math:`F_C` from pass and stop band specifications.

**Design routines:**

``scipy.signal.ellip()``, ``scipy.signal.ellipord()``

        """

    sigFiltChanged = pyqtSignal()

    def __init__(self):
        QWidget.__init__(self)

        self.ft = 'IIR'

        c = Common()                   
        self.rt_dict = c.rt_base_iir
        
        self.rt_dict_add = {
            'COM':{'man':{'msg':('a',
                 "Enter the filter order <b><i>N</i></b>, the minimum stop "
                 "band attenuation <b><i>A<sub>SB</sub></i></b> and the frequency or "
                 "frequencies <b><i>F<sub>C</sub></i></b>  where the gain first drops "
                 "below the maximum passband ripple <b><i>-A<sub>PB</sub></i></b> .")}},
            'LP': {'man':{}, 'min':{}},
            'HP': {'man':{}, 'min':{}},
            'BS': {'man':{}, 'min':{}},
            'BP': {'man':{}, 'min':{}},
            }
        self.wdg = True  # has additional dynamic widgets (for non-causal and Complex BP/BS)
        
        self.hdl = ('iir_sos', 'df') # filter topologies

        self.info_doc = []
        self.info_doc.append('ellip()\n========')
        self.info_doc.append(sig.ellip.__doc__)
        self.info_doc.append('ellipord()\n==========')
        self.info_doc.append(ellipord.__doc__)

    def construct_UI(self):
        """
        Create additional subwidget(s) needed for filter design with the 
        names given in self.wdg :
        These subwidgets are instantiated dynamically when needed in 
        select_filter.py using the handle to the filter instance, fb.fil_inst.
        """
        self.chkNonCausal = QCheckBox("NonCausal", self)
        self.chkNonCausal.setToolTip("Designs Non-Causal Filter with Zero Phase.")
        self.chkNonCausal.setObjectName('wdg_lbl_el_0')
        self.chkNonCausal.setChecked(False)
        self.chkComplex   = QCheckBox("ComplexFilter", self)
        self.chkComplex.setToolTip("Designs BP or BS Filter for complex data.")
        self.chkComplex.setObjectName('wdg_lbl_el_1')
        self.chkComplex.setChecked(False)

        #--------------------------------------------------
        #  Layout for filter optional subwidgets
        self.layHWin = QHBoxLayout()
        self.layHWin.setObjectName('wdg_layGWin')
        self.layHWin.addWidget(self.chkNonCausal)
        self.layHWin.addWidget(self.chkComplex)
        self.layHWin.addStretch() 
        self.layHWin.setContentsMargins(0,0,0,0)

        # Widget containing all subwidgets 
        self.wdg_fil = QWidget(self)
        self.wdg_fil.setObjectName('wdg_fil')
        self.wdg_fil.setLayout(self.layHWin)

    def destruct_UI(self):
        """
        Disconnect all signal-slot connections to avoid crashes upon exit
        (empty method, nothing to do in this filter)
        """
        pass

    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        # Frequencies are normalized to f_Nyq = f_S/2, ripple specs are in dB
        self.analog = False # set to True for analog filters
        self.N     = fil_dict['N']
        self.F_PB  = fil_dict['F_PB'] * 2
        self.F_SB  = fil_dict['F_SB'] * 2
        self.F_PB2 = fil_dict['F_PB2'] * 2
        self.F_SB2 = fil_dict['F_SB2'] * 2
        self.F_PBC = None

        self.A_PB = lin2unit(fil_dict['A_PB'], 'IIR', 'A_PB', unit='dB')
        self.A_SB = lin2unit(fil_dict['A_SB'], 'IIR', 'A_SB', unit='dB')
        
        # ellip filter routines support only one amplitude spec for
        # pass- and stop band each
        if str(fil_dict['rt']) == 'BS':
            fil_dict['A_PB2'] = fil_dict['A_PB']
        elif str(fil_dict['rt']) == 'BP':
            fil_dict['A_SB2'] = fil_dict['A_SB']

    def _save(self, fil_dict, arg):
        """
        Convert results of filter design to all available formats (pz, ba, sos)
        and store them in the global filter dictionary. 
        
        Corner frequencies and order calculated for minimum filter order are 
        also stored to allow for an easy subsequent manual filter optimization.
        """
        fil_save(fil_dict, arg, self.FRMT, __name__)

        # For min. filter order algorithms, update filter dictionary with calculated
        # new values for filter order N and corner frequency(s) F_PBC
        if str(fil_dict['fo']) == 'min': 
            fil_dict['N'] = self.N 

            if str(fil_dict['rt']) == 'LP' or str(fil_dict['rt']) == 'HP':
                fil_dict['F_PB'] = self.F_PBC / 2. # HP or LP - single  corner frequency
            else: # BP or BS - two corner frequencies
                fil_dict['F_PB'] = self.F_PBC[0] / 2.
                fil_dict['F_PB2'] = self.F_PBC[1] / 2.

        self.sigFiltChanged.emit()
                
#------------------------------------------------------------------------------
#
#         DESIGN ROUTINES
#
#------------------------------------------------------------------------------

    # LP: F_PB < F_stop -------------------------------------------------------
    def LPmin(self, fil_dict):
        """Elliptic LP filter, minimum order"""
        self._get_params(fil_dict)
        self.N, self.F_PBC = ellipord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                          analog=self.analog)
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                            btype='low', analog=self.analog, output=self.FRMT))

    def LPman(self, fil_dict):
        """Elliptic LP filter, manual order"""
        self._get_params(fil_dict)
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PB,
                            btype='low', analog=self.analog, output=self.FRMT))

    # HP: F_stop < F_PB -------------------------------------------------------
    def HPmin(self, fil_dict):
        """Elliptic HP filter, minimum order"""
        self._get_params(fil_dict)
        self.N, self.F_PBC = ellipord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                          analog=self.analog)
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='highpass', analog=self.analog, output=self.FRMT))

    def HPman(self, fil_dict):
        """Elliptic HP filter, manual order"""
        self._get_params(fil_dict)
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PB,
                        btype='highpass', analog=self.analog, output=self.FRMT))

    # For BP and BS, F_XX have two elements each, A_XX has only one

    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1] --------------------------------
    def BPmin(self, fil_dict):
        """Elliptic BP filter, minimum order"""
        self._get_params(fil_dict)
        self.N, self.F_PBC = ellipord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB, self.A_SB, analog=self.analog)
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='bandpass', analog=self.analog, output=self.FRMT))
                            
    def BPman(self, fil_dict):
        """Elliptic BP filter, manual order"""
        self._get_params(fil_dict)
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, 
            [self.F_PB,self.F_PB2], btype='bandpass', analog=self.analog, 
                                                                output=self.FRMT))

    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1] --------------------------------
    def BSmin(self, fil_dict):
        """Elliptic BP filter, minimum order"""
        self._get_params(fil_dict)
        self.N, self.F_PBC = ellipord([self.F_PB, self.F_PB2],
                                [self.F_SB, self.F_SB2], self.A_PB,self.A_SB,
                                                        analog=self.analog)
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='bandstop', analog=self.analog, output=self.FRMT))

    def BSman(self, fil_dict):
        """Elliptic BS filter, manual order"""
        self._get_params(fil_dict)
        self._save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, 
            [self.F_PB,self.F_PB2], btype='bandstop', analog=self.analog, 
                                                                output=self.FRMT))
                            
#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    from ..compat import QApplication
    import pyfda.filterbroker as fb # importing filterbroker initializes all its globals 

    app = QApplication (sys.argv)

    # ellip filter widget
    filt = Ellip()        # instantiate filter
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

