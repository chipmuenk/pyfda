# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Design Bessel filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

This class is re-instantiated dynamically every time the filter design method
is selected, reinitializing instance attributes.

API version info
----------------

    1.0: initial working release

    1.1: - copy ``a_pb`` -> ``a_pb2`` and ``a_sb -> ``a_sb2`` for BS / BP designs
          - mark private methods as private
    1.2: new API using fil_save (enable SOS features)
    1.4: - module attribute ``filter_classes`` contains class name and combo box
            name instead of class attribute ``name``
        - ``FRMT`` is now a class attribute
    2.0: Specify the parameters for each subwidget as tuples in a dict where the
        first element controls whether the widget is visible and / or enabled.
        This dict is now called ``self.rt_dict``. When present, the dict
        ``self.rt_dict_add`` is read and merged with the first one.
    2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
    2.3: Add `has_ui` attribute to filter classes
"""
from scipy.signal import bessel, buttord

from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.special_functions import lin2unit
from pyfda.libs.pyfda_qt_lib import popup_warning
from pyfda.libs.pyfda_sig_lib import fil_save


__version__ = "2.3"

classes = {'Bessel': 'Bessel'} #: Dict containing class name : display name

class Bessel():
    """
    Design digital Bessel filters (LP, HP, BP, BS) with fixed or minimum order,
    return the filter design in 'sos', 'zpk' or 'ba' format, selected by ``FRMT``.
    This is more or less a wrapper around ``scipy.signal.bessel()`` and
    ``scipy.signal.buttord()`` (which is used to approximate the minimum order
    for a Bessel filter).
    """
    FRMT = 'sos' # output format of filter design routines: 'sos', 'zpk' or 'ba'
    has_ui = False #: Flag whether the filter class has a UI or not
    info = """
    **Bessel filters**

    have the best phase linearity of all IIR filters in the pass band and hence
    maximally flat group delay. They have a monotonous magnitude response in both
    pass and stop band(s) and minimum ringing of the step response. The roll-off is
    the most gentle of all IIR filters, often it is better to choose an FIR filter
    when phase linearity is important.

    Only the order :math:`N` and critical frequency(ies) :math:`f_c` can be specified.
    :math:`f_c` is the frequency where the phase response reaches its midpoint for
    both low-pass and high-pass filters (“phase-matched”).

    The magnitude response asymptotes are the same as a Butterworth filter of the
    same order and with the same :math:`f_c`, however, the actual magnitude response
    :math:`|H(f_c)|` depends on the filter order :math:`N`.

    Currently, no proper minimum order algorithm is implemented; instead, the minimum
    order for a Butterworth filter is used as a coarse approximation for finding
    :math:`N` and :math:`f_c`. This works reasonably well for the stop band but not
    for the pass band.

    For scipy 0.18 and higher, more design options have been implemented
    (not yet in the GUI).

    **Design routines:**

    ``scipy.signal.bessel()``, ``scipy.signal.buttord()``
    """

    def __init__(self):

        self.ft = 'IIR' #: filter type
        self.rt_dict =  {
            'COM':{'man':{'fo': ('a', 'N'),
                   'msg':('a', "Enter the filter order <b><i>N</i></b> and the critical "
                               "frequency or frequencies <b><i>F<sub>C</sub></i></b> .")},
                   'min':{'fo': ('d', 'N'),
                          'msg':('a',
                   "Enter maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                    "minimum stop band attenuation <b><i>A<sub>SB</sub> </i></b>"
                    "&nbsp;and the corresponding corner frequencies of pass and "
                    "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
                    "<b><i>F<sub>SB</sub></i></b>&nbsp; (only a rough approximation).")
                        }
                    },
            'lp': {'man':{'fspecs': ('a','f_c'),
                          'tspecs': ('u', {'frq':('u','f_pb','f_sb'),
                                           'amp':('u','a_pb','a_sb')})
                          },
                   'min':{'fspecs': ('d','f_c'),
                          'tspecs': ('a', {'frq':('a','f_pb','f_sb'),
                                           'amp':('a','a_pb','a_sb')})
                        }
                },
            'hp': {'man':{'fspecs': ('a','f_c'),
                          'tspecs': ('u', {'frq':('u','f_sb','f_pb'),
                                           'amp':('u','a_sb','a_pb')})
                         },
                   'min':{'fspecs': ('d','f_c'),
                          'tspecs': ('a', {'frq':('a','f_sb','f_pb'),
                                           'amp':('a','a_sb','a_pb')})
                         }
                    },
            'bp': {'man':{'fspecs': ('a','f_c', 'f_c2'),
                          'tspecs': ('u', {'frq':('u','f_sb','f_pb','f_pb2','f_sb2'),
                                           'amp':('u','a_sb','a_pb')})
                         },
                   'min':{'fspecs': ('d','f_c','f_c2'),
                          'tspecs': ('a', {'frq':('a','f_sb','f_pb','f_pb2','f_sb2'),
                                           'amp':('a','a_sb','a_pb')})
                         },
                    },
            'bs': {'man':{'fspecs': ('a','f_c','f_c2'),
                          'tspecs': ('u', {'frq':('u','f_pb','f_sb','f_sb2','f_pb2'),
                                           'amp':('u','a_pb','a_sb')})
                          },
                   'min':{'fspecs': ('d','f_c','f_c2'),
                          'tspecs': ('a', {'frq':('a','f_pb','f_sb','f_sb2','f_pb2'),
                                           'amp':('a','a_pb','a_sb')})
                        }
                }
            }

        self.info_doc = []
        self.info_doc.append('bessel()\n========')
        self.info_doc.append(bessel.__doc__)
        self.info_doc.append('buttord()\n==========')
        self.info_doc.append(buttord.__doc__)

    #--------------------------------------------------------------------------
    def _get_params(self) -> None:
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N = fb_get('N')

        self.f_pb  = fb_get('f_pb') * 2 # Frequencies are normalized to f_Nyq
        self.f_sb  = fb_get('f_sb') * 2
        self.f_pb2 = fb_get('f_pb2') * 2
        self.f_sb2 = fb_get('f_sb2') * 2
        self.f_pb_c = None
        self.f_c   = fb_get('f_c') * 2
        self.f_c2  = fb_get('f_c2') * 2

        self.a_pb = lin2unit(fb_get('a_pb'), 'IIR', 'a_pb', unit='dB')
        self.a_sb = lin2unit(fb_get('a_sb'), 'IIR', 'a_sb', unit='dB')

        # bessel filter routines support only one amplitude spec for
        # pass- and stop band each
        if fb_get('rt') == 'bs':
            fb_set('a_pb2', fb_get('a_pb'))
        elif fb_get('rt') == 'bp':
            fb_set('a_sb2', fb_get('a_sb'))

    #--------------------------------------------------------------------------
    def _test_n(self) -> bool:
        """
        Warn the user if the calculated order N is too high for a reasonable filter
        design.
        """
        if self.N > 40:
            #in scipy, Bessel filter order is limited to 40
            return popup_warning(None, self.N, "Bessel")
        return True

    def _save(self, arg) -> int:
        """
        Convert results of filter design to all available formats (pz, ba, sos)
        and store them in the global filter dictionary.

        Corner frequencies and order calculated for minimum filter order are
        also stored to allow for an easy subsequent manual filter optimization.

        For min. filter order algorithms, update filter dictionary with calculated
        new values for filter order N (doubled for BP and BS designs)
        and corner frequency(s) f_pb_c.
        """
        if not self._test_n():
            return -1
        fil_save(arg, self.FRMT, __name__)

        fb_set('N', self.N) # always save, might have been limited by _test_n
        if fb_get('fo') == 'min':
            if fb_get('rt') in {'lp', 'hp'}:
                fb_set('f_c', self.f_pb_c / 2.) # HP or LP - single  corner frequency
            else: # BP or BS - two corner frequencies; order needs to be doubled
                fb_set('f_c', self.f_pb_c[0] / 2.)
                fb_set('f_c2', self.f_pb_c[1] / 2.)
                fb_set('N', self.N * 2)
        return 0

    # LP: f_pb < f_sb
    def lp_min(self) -> int:
        """Bessel LP filter, minimum order"""
        self._get_params()
        self.N, self.f_pb_c = buttord(self.f_pb, self.f_sb, self.a_pb, self.a_sb)
        return self._save(
            bessel(self.N, self.f_pb_c, btype='low', analog=False, output=self.FRMT))


    def lp_man(self) -> int:
        """Bessel LP filter, manual order"""
        self._get_params()
        return self._save(
            bessel(self.N, self.f_c, btype='low', analog=False, output=self.FRMT))

    # HP: f_sb < f_pb
    def hp_min(self) -> int:
        """Bessel HP filter, minimum order"""
        self._get_params()
        self.N, self.f_pb_c = buttord(self.f_pb, self.f_sb, self.a_pb,self.a_sb)
        return self._save(
            bessel(self.N, self.f_pb_c, btype='highpass', analog=False, output=self.FRMT))

    def hp_man(self) -> int:
        """Bessel HP filter, manual order"""
        self._get_params()
        return self._save(
            bessel(self.N, self.f_c, btype='highpass', analog=False, output=self.FRMT))

    # For BP and BS, a_pb, f_pb and F_stop have two elements each.
    # The min. filter order and the design algorithms use half the actual filter order,
    # hence the filter order needs to be doubled / halved before (re-)storing

    # BP: f_sb[0] < f_pb[0], f_sb[1] > f_pb[1]
    def bp_min(self) -> int:
        """Bessel BP filter, minimum order"""
        self._get_params()
        self.N, self.f_pb_c = buttord(
            [self.f_pb, self.f_pb2], [self.f_sb, self.f_sb2], self.a_pb, self.a_sb)
        return self._save(
            bessel(self.N, self.f_pb_c, btype='bandpass', analog=False, output=self.FRMT))

    def bp_man(self) -> int:
        """Bessel BP filter, manual order"""
        self._get_params()
        return self._save(
            bessel(self.N//2, [self.f_c,self. f_c2], btype='bandpass',
                   analog=False, output=self.FRMT))

    # BS: f_sb[0] > f_pb[0], f_sb[1] < f_pb[1]
    def bs_min(self) -> int:
        """Bessel BS filter, minimum order"""
        self._get_params()
        self.N, self.f_pb_c = buttord(
            [self.f_pb, self.f_pb2], [self.f_sb, self.f_sb2], self.a_pb,self.a_sb)
        return self._save(
            bessel(self.N, self.f_pb_c, btype='bandstop', analog=False, output=self.FRMT))

    def bs_man(self) -> int:
        """Bessel BS filter, manual order"""
        self._get_params()
        return self._save(
            bessel(self.N//2, [self.f_c, self.f_c2], btype='bandstop',
                   analog=False, output=self.FRMT))
#------------------------------------------------------------------------------

if __name__ == '__main__':
    # Run this module standalone with `python -m pyfda.filter_widgets.bessel`
    filt = Bessel()        # instantiate filter
    filt.lp_man()  # design a low-pass with parameters from global dict
    print(fb_get(filt.FRMT)) # return results in default format (e.g. 'ba')
