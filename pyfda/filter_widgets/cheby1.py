# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design Chebyshev 1 filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zpk (zeros, poles, gain) or second-order sections (sos) format.

Attention:
This class is re-instantiated dynamically every time the filter design method
is selected, calling its __init__ method.

API version info
----------------

    1.0: initial working release
    1.1: - copy a_pb -> a_pb2 and a_sb -> a_sb2 for BS / BP designs
         - mark private methods as private
    1.2: new API using fil_save (enable SOS features when available)
    1.3: new public methods destruct_ui + construct_ui (no longer called by __init__)
    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
         `FRMT` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.
    2.1: Remove empty methods construct_ui and destruct_ui and attributes
         self.wdg and self.hdl
    2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
    2.3: Add `has_ui` attribute to filter classes
"""
from scipy.signal import cheby1, cheb1ord

from pyfda.libs.special_functions import lin2unit
from pyfda.libs.pyfda_qt_lib import popup_warning
from pyfda.libs.pyfda_sig_lib import fil_save
from pyfda.filterbroker import fb_get, fb_set

from .common import Common

__version__ = "2.3"

classes = {'Cheby1': 'Chebyshev 1'} #: Dict containing class name : display name

class Cheby1():
    """
    Design digital Chebychev type I filters (LP, HP, BP, BS) with fixed or minimum
    order, return the filter design in 'sos', 'zpk' or 'ba' format, selected by ``FRMT``.
    This is more or less a wrapper around the ``scipy.signal.cheby1()`` and
    ``scipy.signal.chebord()`` routines.
    """

    FRMT = 'sos' # output format of filter design routines 'zpk' / 'ba' / 'sos'
    has_ui = False #: Flag whether the filter class has a UI or not
    info = """
    **Chebyshev Type 1 filters**

    maximize the rate of cutoff between the frequency response’s passband and stopband,
    at the expense of passband ripple :math:`a_pb` and increased ringing in
    the step response. The stopband drops monotonously.

    Type I filters roll off faster than Type II, but Type II filters do not
    have any ripple in the passband.

    The passband has a constant ripple (equiripple) with a total of :math:`N` maxima
    and minima (for example, a 5th-order filter has 3 maxima and 2 minima). Consequently,
    the DC gain is unity for odd-order low-pass filters, and :math:`-a_pb` dB for even-order
    filters.

    For a manual filter design, the order :math:`N`, the passband ripple :math:`a_pb` and
    the critical frequency / frequencies :math:`f_c` where the gain drops below
    :math:`-a_pb` have to be specified.

    The ``cheb1ord()`` helper routine calculates the minimum order :math:`N` and the
    critical passband frequency :math:`f_c` from passband / stopband specifications.

    **Design routines:**

    ``scipy.signal.cheby1()``, ``scipy.signal.cheb1ord()``
    """

    def __init__(self):

        self.ft = 'IIR'

        c = Common()
        self.rt_dict = c.rt_base_iir

        self.rt_dict_add = {
            'COM':{'man':{'msg':('a',
                r"Enter the filter order <b><i>N</i></b> and the critical frequency "
                 "or frequencies <b><i>F<sub>C</sub></i></b>&nbsp; where the gain first "
                 "drops below the maximum ripple "
                 "<b><i>-A<sub>PB</sub></i></b>&nbsp; allowed below unity gain in the "
                 "passband.")},
                                  },
            'lp': {'man':{}, 'min':{}},
            'hp': {'man':{}, 'min':{}},
            'bs': {'man':{}, 'min':{}},
            'bp': {'man':{}, 'min':{}},
            }

        self.info_doc = []
        self.info_doc.append('cheby1()\n========')
        self.info_doc.append(cheby1.__doc__)
        self.info_doc.append('cheb1ord()\n==========')
        self.info_doc.append(cheb1ord.__doc__)

    #--------------------------------------------------------------------------
    def _get_params(self) -> None:
        """
        Translate parameters from filter dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.analog = False # set to True for analog filters

        self.N     = fb_get('N')
        # Frequencies are normalized to f_Nyq = f_S/2, ripple specs are in dB
        self.f_pb  = fb_get('f_pb') * 2
        self.f_sb  = fb_get('f_sb') * 2
        self.f_c = fb_get('f_c') * 2
        self.f_pb2 = fb_get('f_pb2') * 2
        self.f_sb2 = fb_get('f_sb2') * 2
        self.f_c2 = fb_get('f_c2') * 2
        self.F_PBC = None

        self.a_pb = lin2unit(fb_get('a_pb'), 'IIR', 'a_pb', unit='dB')
        self.a_sb = lin2unit(fb_get('a_sb'), 'IIR', 'a_sb', unit='dB')


        # cheby1 filter routines support only one amplitude spec for
        # pass- and stop band each
        if fb_get('rt') == 'bs':
            fb_set('a_pb2', fb_get('a_pb'))
        elif fb_get('rt') == 'bp':
            fb_set('a_sb2', fb_get('a_sb'))

    #--------------------------------------------------------------------------
    def _test_n(self) -> bool:
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 30:
            return popup_warning(None, self.N, "Chebyshev 1")
        return True

    #--------------------------------------------------------------------------
    def _save(self, arg) -> int:
        """
        Convert results of filter design to all available formats (pz, ba, sos)
        and store them in the global filter dictionary.

        Corner frequencies and order calculated for minimum filter order are
        also stored to allow for an easy subsequent manual filter optimization.

        For min. filter order algorithms, update filter dictionary with calculated
        new values for filter order N (doubled for BP and BS designs)
        and corner frequency(s) F_PBC.
        """
        if not self._test_n():
            return -1
        fil_save(arg, self.FRMT, __name__)

        if fb_get('fo') == 'min':
            if fb_get('rt') in {'lp', 'hp'}:
                fb_set('f_c', self.F_PBC / 2.) # HP or LP - single  corner frequency
                fb_set('N', self.N)
            else: # BP or BS - two corner frequencies
                fb_set('f_c', self.F_PBC[0] / 2.)
                fb_set('f_c2', self.F_PBC[1] / 2.)
                fb_set('N', self.N * 2)
        return 0

    #------------------------------------------------------------------------------
    #
    #         DESIGN ROUTINES
    #
    #------------------------------------------------------------------------------

    # LP: f_pb < f_sb ---------------------------------------------------------
    def lp_min(self) -> int:
        """Cheby1 LP filter, minimum order"""
        self._get_params()
        self.N, self.F_PBC = cheb1ord(
            self.f_pb, self.f_sb, self.a_pb, self.a_sb, analog=self.analog)
        return self._save(
            cheby1(self.N, self.a_pb, self.F_PBC, btype='low',
                   analog=self.analog, output=self.FRMT))

    def lp_man(self) -> int:
        """Cheby1 LP filter, manual order"""
        self._get_params()
        return self._save(
            cheby1(self.N, self.a_pb, self.f_c, btype='low',
                   analog=self.analog, output=self.FRMT))

    # HP: f_sb < f_pb ---------------------------------------------------------
    def hp_min(self) -> int:
        """Cheby1 HP filter, minimum order"""
        self._get_params()
        self.N, self.F_PBC = cheb1ord(
            self.f_pb,self.f_sb, self.a_pb, self.a_sb, analog=self.analog)
        return self._save(
            cheby1(self.N, self.a_pb, self.F_PBC, btype='highpass',
                   analog=self.analog, output=self.FRMT))

    def hp_man(self) -> int:
        """Cheby1 HP filter, manual order"""
        self._get_params()
        return self._save(cheby1(
            self.N, self.a_pb, self.f_c, btype='highpass',
            analog=self.analog, output=self.FRMT))

    # For BP and BS, a_pb, f_pb and F_stop have two elements each.
    # The min. filter order and the design algorithms use half the actual filter order,
    # hence the filter order needs to be doubled / halved before (re-)storing

    # BP: f_sb[0] < f_pb[0], f_sb[1] > f_pb[1] --------------------------------
    def bp_min(self) -> int:
        """Cheby1 BP filter, minimum order"""
        self._get_params()
        self.N, self.F_PBC = cheb1ord(
            [self.f_pb, self.f_pb2], [self.f_sb, self.f_sb2], self.a_pb, self.a_sb,
            analog=self.analog)
        return self._save(
            cheby1(self.N, self.a_pb, self.F_PBC, btype='bandpass',
                   analog=self.analog, output=self.FRMT))

    def bp_man(self) -> int:
        """Cheby1 BP filter, manual order"""
        self._get_params()
        return self._save(
            cheby1(self.N//2, self.a_pb,[self.f_c, self.f_c2], btype='bandpass',
                   analog=self.analog, output=self.FRMT))

    # BS: f_sb[0] > f_pb[0], f_sb[1] < f_pb[1] --------------------------------
    def bs_min(self) -> int:
        """Cheby1 BS filter, minimum order"""
        self._get_params()
        self.N, self.F_PBC = cheb1ord(
            [self.f_pb, self.f_pb2], [self.f_sb, self.f_sb2], self.a_pb,self.a_sb,
            analog = self.analog)
        return self._save(
            cheby1(self.N, self.a_pb, self.F_PBC, btype='bandstop',
                   analog=self.analog, output=self.FRMT))

    def bs_man(self) -> int:
        """Cheby1 BS filter, manual order"""
        self._get_params()
        return self._save(
            cheby1(self.N//2, self.a_pb, [self.f_c, self.f_c2], btype='bandstop',
                   analog=self.analog, output=self.FRMT))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    # Run this module standalone with 'python -m pyfda.filter_widgets.cheby1'
    filt = Cheby1()        # instantiate filter
    fb_set('fo', 'min')
    filt.lp_min()  # design a low-pass with parameters from global dict
    print(fb_get(filt.FRMT)) # return results in default format (e.g. 'ba')
