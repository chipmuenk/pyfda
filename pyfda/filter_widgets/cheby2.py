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

API version info
----------------

    1.0: initial working release
    1.1: - copy a_pb -> a_pb2 and a_sb -> a_sb2 for BS / BP designs
         - mark private methods as private
    1.2: new API using fil_save (enable SOS features when available)

    1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`
         `FRMT` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.
    2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
    2.3: Add `has_ui` attribute to filter classes
"""
from scipy.signal import cheby2, cheb2ord

from pyfda.libs.special_functions import lin2unit
from pyfda.libs.pyfda_qt_lib import popup_warning
from pyfda.libs.pyfda_sig_lib import fil_save
from pyfda.filterbroker import fb_get, fb_set

from .common import Common

__version__ = "2.3"

classes = {'Cheby2': 'Chebyshev 2'} #: Dict containing class name : display name
class Cheby2():
    """
    Design digital Chebychev type 2 filters (LP, HP, BP, BS) with fixed or minimum
    order, return the filter design in 'sos', 'zpk' or 'ba' format, selected by ``FRMT``.
    This is more or less a wrapper around the ``scipy.signal.cheby2()`` and
    ``scipy.signal.cheb2ord()`` routines.
    """

    FRMT = 'sos' # output format of filter design routines 'zpk' / 'ba' / 'sos'
    has_ui = False #: Flag whether the filter class has a UI or not
    info = """
    **Chebyshev Type 2 filters**

    maximize the rate of cutoff between the frequency response’s passband and stopband,
    at the expense of ripple in the stopband and increased ringing in the step response.

    Type II filters do not roll off as fast as Type I but their pass band rolls off
    monotonously. They have a constant ripple (equiripple) :math:`a_sb` in the stop
    band(s).

    For manual filter design, order :math:`N`, stop band ripple :math:`a_sb` and
    critical frequency / frequencies :math:`f_c` where the stop band attenuation
    :math:`a_sb` is first reached have to be specified.

    The corner frequency/ies of the pass band can only be controlled indirectly
    by the filter order and by adapting the value(s) of :math:`f_c`.

    The ``cheb2ord()`` helper routine calculates the minimum order :math:`N` and the
    critical stop band frequency :math:`f_c` from pass and stop band specifications.

    **Design routines:**

    ``scipy.signal.cheby2()``, ``scipy.signal.cheb2ord()``
    """

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
            'lp': {'man':{}, 'min':{}},
            'hp': {'man':{}, 'min':{}},
            'bs': {'man':{}, 'min':{}},
            'bp': {'man':{}, 'min':{}},
            }

        self.info_doc = []
        self.info_doc.append('cheby2()\n========')
        self.info_doc.append(cheby2.__doc__)
        self.info_doc.append('cheb2ord()\n==========')
        self.info_doc.append(cheb2ord.__doc__)

    #--------------------------------------------------------------------------
    def _get_params(self) -> None:
        """
        Translate parameters from the passed dictionary to instance
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
        self.F_SBC = None

        self.a_pb = lin2unit(fb_get('a_pb'), 'IIR', 'a_pb', unit='dB')
        self.a_sb = lin2unit(fb_get('a_sb'), 'IIR', 'a_sb', unit='dB')


        # cheby2 filter routines support only one amplitude spec for
        # pass- and stop band each
        if fb_get('rt') == 'bs':
            fb_set('a_pb2', fb_get('a_pb'))
        elif str(fb_get('rt')) == 'bp':
            fb_set('a_sb2', fb_get('a_sb'))

    #--------------------------------------------------------------------------
    def _test_n(self) -> bool:
        """
        Warn the user if the calculated order is too high for a reasonable filter
        design.
        """
        if self.N > 25:
            return popup_warning(None, self.N, "Chebyshev 2")
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
        and corner frequency(s) F_SBC.
        """
        if not self._test_n():
            return -1
        fil_save(arg, self.FRMT, __name__)

        if fb_get('fo') == 'min':
            if fb_get('rt') in {'lp', 'hp'}:
                fb_set('f_c', self.F_SBC / 2.) # HP or LP - single  corner frequency
                fb_set('N', self.N)
            else: # BP or BS - two corner frequencies
                fb_set('f_c', self.F_SBC[0] / 2.)
                fb_set('f_c2', self.F_SBC[1] / 2.)
                fb_set('N', self.N * 2)
        return 0

    #------------------------------------------------------------------------------
    #
    #         DESIGN ROUTINES
    #
    #------------------------------------------------------------------------------

    # LP: f_pb < f_sb ---------------------------------------------------------
    def lp_min(self) -> int:
        """Cheby2 LP filter, minimum order"""
        self._get_params()
        self.N, self.F_SBC = cheb2ord(
            self.f_pb,self.f_sb, self.a_pb, self.a_sb, analog=self.analog)
        return self._save(
            cheby2(self.N, self.a_sb, self.F_SBC, btype='lowpass',
                   analog=self.analog, output=self.FRMT))

    def lp_man(self) -> int:
        """Cheby2 LP filter, fixed order"""
        self._get_params()
        return self._save(
            cheby2(self.N, self.a_sb, self.f_c, btype='low',
                   analog=self.analog, output=self.FRMT))

    # HP: f_sb < f_pb ---------------------------------------------------------
    def hp_min(self) -> int:
        """Cheby2 HP filter, minimum order"""
        self._get_params()
        self.N, self.F_SBC = cheb2ord(
            self.f_pb, self.f_sb, self.a_pb, self.a_sb, analog=self.analog)
        return self._save(cheby2(
            self.N, self.a_sb, self.F_SBC, btype='highpass',
            analog=self.analog, output=self.FRMT))

    def hp_man(self) -> int:
        """Cheby2 HP filter, fixed order"""
        self._get_params()
        return self._save(
            cheby2(self.N, self.a_sb, self.f_c, btype='highpass',
                   analog=self.analog, output=self.FRMT))

    # For BP and BS, a_pb, a_sb, f_pb and f_sb have two elements each.
    # The min. filter order and the design algorithms use half the actual filter order,
    # hence the filter order needs to be doubled / halved before (re-)storing.


    # BP: f_sb[0] < f_pb[0], f_sb[1] > f_pb[1] --------------------------------
    def bp_min(self) -> int:
        """Cheby2 BP filter, minimum order"""
        self._get_params()
        self.N, self.F_SBC = cheb2ord(
            [self.f_pb, self.f_pb2], [self.f_sb, self.f_sb2], self.a_pb, self.a_sb,
             analog=self.analog)
        return self._save(
            cheby2(self.N, self.a_sb, self.F_SBC, btype='bandpass',
                   analog=self.analog, output=self.FRMT))

    def bp_man(self) -> int:
        """Cheby2 BP filter, fixed order"""
        self._get_params()
        return self._save(cheby2(
            self.N//2, self.a_sb, [self.f_c, self.f_c2], btype='bandpass',
            analog=self.analog, output=self.FRMT))

    # BS: f_sb[0] > f_pb[0], f_sb[1] < f_pb[1] --------------------------------
    def bs_min(self) -> int:
        """Cheby2 BS filter, minimum order"""
        self._get_params()
        self.N, self.F_SBC = cheb2ord(
            [self.f_pb, self.f_pb2], [self.f_sb, self.f_sb2], self.a_pb, self.a_sb,
            analog=self.analog)
        return self._save(
            cheby2(self.N, self.a_sb, self.F_SBC, btype='bandstop',
                   analog=self.analog, output=self.FRMT))

    def bs_man(self) -> int:
        """Cheby2 BS filter, fixed order"""
        self._get_params()
        return self._save(
            cheby2(self.N//2, self.a_sb, [self.f_c, self.f_c2], btype='bandstop',
                   analog=self.analog, output=self.FRMT))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    # Run this module standalone with 'python -m pyfda.filter_widgets.cheby2'
    filt = Cheby2()        # instantiate filter
    filt.lp_man()  # design a low-pass with parameters from global dict
    print(fb_get(filt.FRMT)) # return results in default format (e.g. 'ba')
