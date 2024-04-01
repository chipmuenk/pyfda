# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design Chebyshev 2 filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) or second-order sections (sos) format.

Attention:
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

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
    2.1: Remove empty methods  construct_UI anddestruct_UI and attributes
         self.wdg and self.hdl

   :2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
"""
import scipy.signal as sig
from scipy.signal import cheb2ord
from .common import Common

from pyfda.libs.pyfda_lib import fil_save, lin2unit
from pyfda.libs.pyfda_qt_lib import popup_warning

__version__ = "2.2"

classes = {'Cheby2':'Chebyshev 2'} #: Dict containing class name : display name

class Cheby2(object):

    FRMT = 'sos' # output format of filter design routines 'zpk' / 'ba' / 'sos'

    def __init__(self):

        self.ft = 'IIR'

        c = Common()
        self.rt_dict = c.rt_base_iir

        self.rt_dict_add = {
            'COM':{'man':{'msg':('a',
                r"Enter the filter order <b><i>N</i></b> and the critical "
                 "frequency / frequencies <b><i>F<sub>C</sub></i></b>&nbsp; where the gain "
                 "first drops below the minimum stop band "
                 "attenuation <b><i>A<sub>SB</sub></i></b> .")},
                                  },
            'LP': {'man':{}, 'min':{}},
            'HP': {'man':{}, 'min':{}},
            'BS': {'man':{}, 'min':{}},
            'BP': {'man':{}, 'min':{}},
            }

        self.info = """
**Chebyshev Type 2 filters**

maximize the rate of cutoff between the frequency response’s passband and stopband,
at the expense of ripple in the stopband and increased ringing in the step response.

Type II filters do not roll off as fast as Type I but their pass band rolls off
monotonously. They have a constant ripple (equiripple) :math:`A_SB` in the stop
band(s).

For manual filter design, order :math:`N`, stop band ripple :math:`A_SB` and
critical frequency / frequencies :math:`F_C` where the stop band attenuation
:math:`A_SB` is first reached have to be specified.

The corner frequency/ies of the pass band can only be controlled indirectly
by the filter order and by adapting the value(s) of :math:`F_C`.

The ``cheb2ord()`` helper routine calculates the minimum order :math:`N` and the
critical stop band frequency :math:`F_C` from pass and stop band specifications.

**Design routines:**

``scipy.signal.cheby2()``, ``scipy.signal.cheb2ord()``
"""

        self.info_doc = []
        self.info_doc.append('cheby2()\n========')
        self.info_doc.append(sig.cheby2.__doc__)
        self.info_doc.append('cheb2ord()\n==========')
        self.info_doc.append(sig.cheb2ord.__doc__)

    #--------------------------------------------------------------------------
    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
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
        self.F_SBC = None

        self.A_PB = lin2unit(fil_dict['A_PB'], 'IIR', 'A_PB', unit='dB')
        self.A_SB = lin2unit(fil_dict['A_SB'], 'IIR', 'A_SB', unit='dB')


        # cheby2 filter routines support only one amplitude spec for
        # pass- and stop band each
        if str(fil_dict['rt']) == 'BS':
            fil_dict['A_PB2'] = fil_dict['A_PB']
        elif str(fil_dict['rt']) == 'BP':
            fil_dict['A_SB2'] = fil_dict['A_SB']

    #--------------------------------------------------------------------------
    def _test_N(self):
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 25:
            return popup_warning(None, self.N, "Chebyshev 2")
        else:
            return True

    #--------------------------------------------------------------------------
    def _save(self, fil_dict, arg):
        """
        Convert results of filter design to all available formats (pz, ba, sos)
        and store them in the global filter dictionary.

        Corner frequencies and order calculated for minimum filter order are
        also stored to allow for an easy subsequent manual filter optimization.
        """
        fil_save(fil_dict, arg, self.FRMT, __name__)

        # For min. filter order algorithms, update filter dictionary with calculated
        # new values for filter order N and corner frequency(s) F_SBC
        if str(fil_dict['fo']) == 'min':

            fil_dict['N'] = self.N

            if str(fil_dict['rt']) == 'LP' or str(fil_dict['rt']) == 'HP':
                fil_dict['F_C'] = self.F_SBC / 2. # HP or LP - single  corner frequency
            else: # BP or BS - two corner frequencies
                fil_dict['F_C'] = self.F_SBC[0] / 2.
                fil_dict['F_C2'] = self.F_SBC[1] / 2.

#------------------------------------------------------------------------------
#
#         DESIGN ROUTINES
#
#------------------------------------------------------------------------------

    # LP: F_PB < F_SB ---------------------------------------------------------
    def LPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_SBC = cheb2ord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                      analog=self.analog)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                        btype='lowpass', analog=self.analog, output=self.FRMT))
    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_C,
                             btype='low', analog=self.analog, output=self.FRMT))

    # HP: F_SB < F_PB ---------------------------------------------------------
    def HPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_SBC = cheb2ord(self.F_PB, self.F_SB,self.A_PB,self.A_SB,
                                                      analog=self.analog)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                        btype='highpass', analog=self.analog, output=self.FRMT))

    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_C,
                        btype='highpass', analog=self.analog, output=self.FRMT))

    # For BP and BS, A_PB, A_SB, F_PB and F_SB have two elements each

    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1] --------------------------------
    def BPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_SBC = cheb2ord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB, self.A_SB, analog=self.analog)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                        btype='bandpass', analog=self.analog, output=self.FRMT))

    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby2(self.N, self.A_SB, [self.F_C, self.F_C2],
                        btype='bandpass', analog=self.analog, output=self.FRMT))


    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1] --------------------------------
    def BSmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_SBC = cheb2ord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB, self.A_SB, analog=self.analog)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                        btype='bandstop', analog=self.analog, output=self.FRMT))

    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.cheby2(self.N, self.A_SB, [self.F_C, self.F_C2],
                        btype='bandstop', analog=self.analog, output=self.FRMT))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
    filt = Cheby2()        # instantiate filter
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][filt.FRMT]) # return results in default format

# test using "python -m pyfda.filter_widgets.cheby2"
