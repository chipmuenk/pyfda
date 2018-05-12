# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design Chebychev 1 filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zpk (zeros, poles, gain) or second-order sections (sos) format.

Attention:
This class is re-instantiated dynamically every time the filter design method
is selected, calling its __init__ method.

API version info:   
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
    2.1: Remove empty methods construct_UI and destruct_UI and attributes 
         self.wdg and self.hdl
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import scipy.signal as sig
from scipy.signal import cheb1ord
    
from pyfda.pyfda_lib import fil_save, SOS_AVAIL, lin2unit
from pyfda.pyfda_qt_lib import qfilter_warning
from .common import Common

__version__ = "2.0"

filter_classes = {'Cheby1':'Chebychev 1'}

class Cheby1(object):
    if SOS_AVAIL:
        FRMT = 'sos' # output format of filter design routines 'zpk' / 'ba' / 'sos'
    else:
        FRMT = 'zpk'
    
    def __init__(self):
 
        self.ft = 'IIR'

        c = Common()
        self.rt_dict = c.rt_base_iir

        self.rt_dict_add = {
            'COM':{'man':{'msg':('a',
                r"Enter the filter order <b><i>N</i></b> and the critical frequency "
                 "or frequencies <b><i>F<sub>C</sub></i></b>&nbsp; where the gain first drops below "
                 "the maximum ripple "
                 "<b><i>-A<sub>PB</sub></i></b>&nbsp; allowed below unity gain in the "
                 "passband.")},                                  
                                  },
            'LP': {'man':{}, 'min':{}},
            'HP': {'man':{}, 'min':{}},
            'BS': {'man':{}, 'min':{}},
            'BP': {'man':{}, 'min':{}},
            }

        self.info = """
**Chebychev Type 1 filters**

maximize the rate of cutoff between the frequency response’s passband and stopband,
at the expense of passband ripple :math:`A_PB` and increased ringing in
the step response. The stopband drops monotonously. 

Type I filters roll off faster than Type II, but Type II filters do not
have any ripple in the passband.

The passband has a constant ripple (equiripple) with a total of :math:`N` maxima
and minima (for example, a 5th-order filter has 3 maxima and 2 minima). Consequently,
the DC gain is unity for odd-order low-pass filters, and :math:`-A_PB` dB for even-order filters.

For a manual filter design, the order :math:`N`, the passband ripple :math:`A_PB` and
the critical frequency / frequencies :math:`F_C` where the gain drops below
:math:`-A_PB` have to be specified.

The ``cheb1ord()`` helper routine calculates the minimum order :math:`N` and the 
critical passband frequency :math:`F_C` from passband / stopband specifications.

**Design routines:**

``scipy.signal.cheby1()``, ``scipy.signal.cheb1ord()``

        """

        self.info_doc = []
        self.info_doc.append('cheby1()\n========')
        self.info_doc.append(sig.cheby1.__doc__)
        self.info_doc.append('cheb1ord()\n==========')
        self.info_doc.append(sig.cheb1ord.__doc__)
      
    #--------------------------------------------------------------------------
    def _get_params(self, fil_dict):
        """
        Translate parameters from filter dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.analog = False # set to True for analog filters

        self.N     = fil_dict['N']
        # Frequencies are normalized to f_Nyq = f_S/2, ripple specs are in dB
        self.F_PB  = fil_dict['F_PB'] * 2
        self.F_SB  = fil_dict['F_SB'] * 2
        self.F_C = fil_dict['F_C'] * 2
        self.F_PB2 = fil_dict['F_PB2'] * 2
        self.F_SB2 = fil_dict['F_SB2'] * 2
        self.F_C2 = fil_dict['F_C2'] * 2
        self.F_PBC = None

        self.A_PB = lin2unit(fil_dict['A_PB'], 'IIR', 'A_PB', unit='dB')
        self.A_SB = lin2unit(fil_dict['A_SB'], 'IIR', 'A_SB', unit='dB')

        
        # cheby1 filter routines support only one amplitude spec for
        # pass- and stop band each
        if str(fil_dict['rt']) == 'BS':
            fil_dict['A_PB2'] = fil_dict['A_PB']
        elif str(fil_dict['rt']) == 'BP':
            fil_dict['A_SB2'] = fil_dict['A_SB']

    def _test_N(self):
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 30:
            return qfilter_warning(None, self.N, "Chebychev 1")
        else:
            return True


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
                fil_dict['F_C'] = self.F_PBC / 2. # HP or LP - single  corner frequency
            else: # BP or BS - two corner frequencies
                fil_dict['F_C'] = self.F_PBC[0] / 2.
                fil_dict['F_C2'] = self.F_PBC[1] / 2.
                    
#------------------------------------------------------------------------------
#
#         DESIGN ROUTINES
#
#------------------------------------------------------------------------------

    # LP: F_PB < F_SB ---------------------------------------------------------
    def LPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_PBC = cheb1ord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                              analog=self.analog)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby1(self.N, self.A_PB, self.F_PBC,
                            btype='low', analog=self.analog, output=self.FRMT))
 
    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby1(self.N, self.A_PB, self.F_C,
                            btype='low', analog=self.analog, output=self.FRMT))

    # HP: F_SB < F_PB ---------------------------------------------------------
    def HPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_PBC = cheb1ord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                          analog=self.analog)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby1(self.N, self.A_PB, self.F_PBC,
                        btype='highpass', analog=self.analog, output=self.FRMT))

    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby1(self.N, self.A_PB, self.F_C,
                        btype='highpass', analog=self.analog, output=self.FRMT))

    # For BP and BS, A_PB, F_PB and F_stop have two elements each:

    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1] --------------------------------
    def BPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_PBC = cheb1ord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB,self.A_SB, analog=self.analog)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby1(self.N, self.A_PB, self.F_PBC,
                        btype='bandpass', analog=self.analog, output=self.FRMT))

    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby1(self.N, self.A_PB,[self.F_C,self.F_C2],
                        btype='bandpass', analog=self.analog, output=self.FRMT))


    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1] --------------------------------
    def BSmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_PBC = cheb1ord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB,self.A_SB, analog = self.analog)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby1(self.N, self.A_PB, self.F_PBC,
                        btype='bandstop', analog=self.analog, output=self.FRMT))

    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby1(self.N, self.A_PB, [self.F_C,self.F_C2],
                        btype='bandstop', analog=self.analog, output=self.FRMT))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    filt = Cheby1()        # instantiate filter
    import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][filt.FRMT]) # return results in default format