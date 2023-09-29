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

API version info:
    :1.0: initial working release

    :1.1: - copy ``A_PB`` -> ``A_PB2`` and ``A_SB -> ``A_SB2`` for BS / BP designs

          - mark private methods as private

    :1.2: new API using fil_save (enable SOS features)

    :1.3: new public methods ``destruct_UI`` and ``construct_UI`` (no longer
         called by ``__init__``)

    :1.4: - module attribute ``filter_classes`` contains class name and combo box name instead of class attribute ``name``

          - ``FRMT`` is now a class attribute

    :2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called ``self.rt_dict``. When present, the dict ``self.rt_dict_add``
         is read and merged with the first one.

    :2.1: Remove empty methods ``construct_UI`` and ``destruct_UI`` and attributes
         ``self.wdg`` and ``self.hdl``

    :2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
"""
import scipy.signal as sig
from scipy.signal import buttord
from pyfda.libs.pyfda_lib import fil_save, lin2unit
import logging
logger = logging.getLogger(__name__)

__version__ = "2.2"

classes = {'Bessel':'Bessel'} #: Dict containing class name : display name

class Bessel(object):
    """
    Design Bessel filters (LP, HP, BP, BS) with fixed or minimum order, return
    the filter design in zeros, poles, gain (zpk) format
    """

    FRMT = 'sos' # output format of filter design routines 'zpk' / 'ba' / 'sos'

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
            'LP': {'man':{'fspecs': ('a','F_C'),
                          'tspecs': ('u', {'frq':('u','F_PB','F_SB'),
                                           'amp':('u','A_PB','A_SB')})
                          },
                   'min':{'fspecs': ('d','F_C'),
                          'tspecs': ('a', {'frq':('a','F_PB','F_SB'),
                                           'amp':('a','A_PB','A_SB')})
                        }
                },
            'HP': {'man':{'fspecs': ('a','F_C'),
                          'tspecs': ('u', {'frq':('u','F_SB','F_PB'),
                                           'amp':('u','A_SB','A_PB')})
                         },
                   'min':{'fspecs': ('d','F_C'),
                          'tspecs': ('a', {'frq':('a','F_SB','F_PB'),
                                           'amp':('a','A_SB','A_PB')})
                         }
                    },
            'BP': {'man':{'fspecs': ('a','F_C', 'F_C2'),
                          'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2'),
                                           'amp':('u','A_SB','A_PB')})
                         },
                   'min':{'fspecs': ('d','F_C','F_C2'),
                          'tspecs': ('a', {'frq':('a','F_SB','F_PB','F_PB2','F_SB2'),
                                           'amp':('a','A_SB','A_PB')})
                         },
                    },
            'BS': {'man':{'fspecs': ('a','F_C','F_C2'),
                          'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2','F_PB2'),
                                           'amp':('u','A_PB','A_SB')})
                          },
                   'min':{'fspecs': ('d','F_C','F_C2'),
                          'tspecs': ('a', {'frq':('a','F_PB','F_SB','F_SB2','F_PB2'),
                                           'amp':('a','A_PB','A_SB')})
                        }
                }
            }

        self.info = """
**Bessel filters**

have the best phase linearity of all IIR filters in the pass band and hence
maximally flat group delay. They have a monotonous magnitude response in both
pass and stop band(s) and minimum ringing of the step response. The roll-off is
the most gentle of all IIR filters, often it is better to choose an FIR filter
when phase linearity is important.

Only the order :math:`N` and critical frequency(ies) :math:`F_C` can be specified.
:math:`F_C` is the frequency where the phase response reaches its midpoint for
both low-pass and high-pass filters (“phase-matched”).

The magnitude response asymptotes are the same as a Butterworth filter of the
same order and with the same :math:`F_C`, however, the actual magnitude response
:math:`|H(F_C)|` depends on the filter order :math:`N`.

Currently, no proper minimum order algorithm is implemented; instead, the minimum
order for a Butterworth filter is used as a coarse approximation for finding
:math:`N` and :math:`F_C`. This works reasonably well for the stop band but not
for the pass band.

For scipy 0.18 and higher, more design options have been implemented
(not yet in the GUI).

**Design routines:**

``scipy.signal.bessel()``, ``scipy.signal.buttord()``
        """ #: filter variants
        self.info_doc = []
        self.info_doc.append('bessel()\n========')
        self.info_doc.append(sig.bessel.__doc__)
        self.info_doc.append('buttord()\n==========')
        self.info_doc.append(buttord.__doc__)

    #--------------------------------------------------------------------------
    def _get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N = fil_dict['N']

        self.F_PB  = fil_dict['F_PB'] * 2 # Frequencies are normalized to f_Nyq
        self.F_SB  = fil_dict['F_SB'] * 2
        self.F_PB2 = fil_dict['F_PB2'] * 2
        self.F_SB2 = fil_dict['F_SB2'] * 2
        self.F_PBC = None
        self.F_C   = fil_dict['F_C'] * 2
        self.F_C2  = fil_dict['F_C2'] * 2

        self.A_PB = lin2unit(fil_dict['A_PB'], 'IIR', 'A_PB', unit='dB')
        self.A_SB = lin2unit(fil_dict['A_SB'], 'IIR', 'A_SB', unit='dB')

        # bessel filter routines support only one amplitude spec for
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
            #in scipy, Bessel filter order is limited to 25
            logger.warning("Order N = {0} is too high for Bessel filters, limiting to 25.".format(self.N))
            self.N = 25
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
        fil_dict['N'] = self.N # always save, might have been limited by _test_N
        if str(fil_dict['fo']) == 'min':
            if str(fil_dict['rt']) == 'LP' or str(fil_dict['rt']) == 'HP':
                fil_dict['F_C'] = self.F_PBC / 2. # HP or LP - single  corner frequency
            else: # BP or BS - two corner frequencies
                fil_dict['F_C'] = self.F_PBC[0] / 2.
                fil_dict['F_C2'] = self.F_PBC[1] / 2.


    def LPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.bessel(self.N, self.F_C,
                            btype='low', analog=False, output=self.FRMT))

    # LP: F_PB < F_stop
    def LPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_PBC = buttord(self.F_PB,self.F_SB, self.A_PB,self.A_SB)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.bessel(self.N, self.F_PBC,
                            btype='low', analog=False, output=self.FRMT))

#        self._save(fil_dict, iirdesign(self.F_PB, self.F_SB, self.A_PB, self.A_SB,
#                             analog=False, ftype='bessel', output=self.FRMT))

    def HPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.bessel(self.N, self.F_C,
                            btype='highpass', analog=False, output=self.FRMT))

    # HP: F_stop < F_PB
    def HPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_PBC = buttord(self.F_PB,self.F_SB, self.A_PB,self.A_SB)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.bessel(self.N, self.F_PBC,
                            btype='highpass', analog=False, output=self.FRMT))

    # For BP and BS, A_PB, F_PB and F_stop have two elements each

    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1]
    def BPman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.bessel(self.N, [self.F_C,self.F_C2],
                            btype='bandpass', analog=False, output=self.FRMT))


    def BPmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_PBC = buttord([self.F_PB, self.F_PB2],
                                [self.F_SB, self.F_SB2], self.A_PB, self.A_SB)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.bessel(self.N, self.F_PBC,
                            btype='bandpass', analog=False, output=self.FRMT))

#        self._save(fil_dict, iirdesign([self.F_PB,self.F_PB2], [self.F_SB,self.F_SB2],
#            self.A_PB, self.A_SB, analog=False, ftype='bessel', output=FRMT))


    def BSman(self, fil_dict):
        self._get_params(fil_dict)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.bessel(self.N, [self.F_C,self.F_C2],
                            btype='bandstop', analog=False, output=self.FRMT))

    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1]
    def BSmin(self, fil_dict):
        self._get_params(fil_dict)
        self.N, self.F_PBC = buttord([self.F_PB, self.F_PB2],
                                [self.F_SB, self.F_SB2], self.A_PB,self.A_SB)
        if not self._test_N():
            return -1
        self._save(fil_dict, sig.bessel(self.N, self.F_PBC,
                            btype='bandstop', analog=False, output=self.FRMT))
#------------------------------------------------------------------------------

if __name__ == '__main__':
    import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
    filt = Bessel()        # instantiate filter
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][filt.FRMT]) # return results in default format

# test using "python -m pyfda.filter_widgets.bessel"
