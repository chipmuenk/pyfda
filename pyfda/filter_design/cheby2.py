# -*- coding: utf-8 -*-
"""
Design cheby2-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

Attention:
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
from scipy.signal import cheb2ord
import numpy as np

from pyfda.pyfda_lib import save_fil

__version__ = "1.0"

frmt = 'zpk' # output format of filter design routines 'zpk' / 'ba' / 'sos'

class cheby2(object):

    def __init__(self):

        self.name = {'cheby2':'Chebychev 2'}

        # common messages for all man. / min. filter order response types:
        msg_man = ("Enter the filter order <b><i>N</i></b> and the critical "
            "frequency / frequencies <b><i>F<sub>C</sub></i></b>&nbsp; where the gain "
            "first drops below the minimum stop band "
            "attenuation <b><i>A<sub>SB</sub></i></b> .")
        msg_min = ("Enter maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                    "minimum stop band attenuation <b><i>A<sub>SB</sub> </i></b>"
                    "&nbsp;and the corresponding corner frequencies of pass and "
                    "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
                    "<b><i>F<sub>SB</sub></i></b> .")

        # VISIBLE widgets for all man. / min. filter order response types:
        vis_man = ['fo','fspecs','tspecs','aspecs'] # manual filter order
        vis_min = ['fo','fspecs','tspecs'] # minimum filter order

        # DISABLED widgets for all man. / min. filter order response types:
        dis_man = ['tspecs'] # manual filter order
        dis_min = ['fspecs'] # minimum filter order

        # common PARAMETERS for all man. / min. filter order response types:
        par_man = ['N', 'f_S', 'F_C', 'A_SB'] # manual filter order
        par_min = ['f_S', 'A_PB', 'A_SB'] # minimum filter order

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types
        # (common data comes first):
        self.com = {"man":{"vis":vis_man, "dis":dis_man, "msg":msg_man, "par":par_man},
                    "min":{"vis":vis_min, "dis":dis_min, "msg":msg_min, "par":par_min}}

        self.ft = 'IIR'
        self.rt = {
          "LP": {"man":{"par":[]},
                 "min":{"par":['F_PB','F_SB']}},
          "HP": {"man":{"par":[]},
                 "min":{"par":['F_SB','F_PB']}},
          "BP": {"man":{"par":['F_C2']},
                 "min":{"par":['F_SB','F_PB','F_PB2','F_SB2']}},
          "BS": {"man":{"par":['F_C2']},
                 "min":{"par":['F_PB','F_SB','F_SB2','F_PB2']}}
                 }

        self.info = """
**Chebyshev Type 2 filters**

have a constant ripple :math:`A_SB` in the stop band(s) only, the pass band
drops monotonously. This is achieved by placing :math:`N/2` zeros along the stop
band.

The order :math:`N`, stop band ripple :math:`A_SB` and
the critical frequency / frequencies :math:`F_C` where the stop band attenuation
:math:`A_SB` is reached have to be specified for filter design.

The corner frequency/ies of the pass band can only be controlled indirectly
by the filter order and by slightly adapting the value(s) of :math:`F_C`.

The ``cheb2ord()`` helper routine calculates the minimum order :math:`N` and the 
critical stop band frequency :math:`F_C` from pass and stop band specifications.

**Design routines:**

``scipy.signal.cheby2()``
``scipy.signal.cheb2ord()``
"""

        self.info_doc = []
        self.info_doc.append('cheby2()\n========')
        self.info_doc.append(sig.cheby2.__doc__)
        self.info_doc.append('cheb2ord()\n==========')
        self.info_doc.append(sig.cheb2ord.__doc__)

    def get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.analog = False # set to True for analog filters
        
        self.N     = fil_dict['N']
        # Frequencies are normalized to f_Nyq = f_S/2 !
        self.F_PB  = fil_dict['F_PB'] * 2
        self.F_SB  = fil_dict['F_SB'] * 2
        self.F_C = fil_dict['F_C'] * 2
        self.F_PB2 = fil_dict['F_PB2'] * 2
        self.F_SB2 = fil_dict['F_SB2'] * 2
        self.F_C2 = fil_dict['F_C2'] * 2
        self.F_SBC = None
        
        self.A_PB  = -20. * np.log10(1. - fil_dict['A_PB'])
        self.A_SB  = -20. * np.log10(fil_dict['A_SB'])

    def save(self, fil_dict, arg):
        """
        Convert poles / zeros / gain to filter coefficients (polynomes) and the
        other way round
        """
        save_fil(fil_dict, arg, frmt, __name__)

        if self.F_SBC is not None: # has the order been calculated by a "min" filter design?
            fil_dict['N'] = self.N # yes, update filterbroker
            if np.isscalar(self.F_SBC): # HP or LP - a single corner frequency
                fil_dict['F_C'] = self.F_SBC / 2.
            else: # BP or BS - two corner frequencies
                fil_dict['F_C'] = self.F_SBC[0] / 2.
                fil_dict['F_C2'] = self.F_SBC[1] / 2

#------------------------------------------------------------------------------
#
#         DESIGN ROUTINES
#
#------------------------------------------------------------------------------

# HP & LP
#        self.save(fil_dict, iirdesign(self.F_PB, self.F_SB, self.A_PB, self.A_SB,
#                             analog=False, ftype='cheby2', output=frmt))
# BP & BS:
#        self.save(fil_dict, iirdesign([self.F_PB,self.F_PB2],
#                [self.F_SB, self.F_SB2], self.A_PB, self.A_SB,
#                             analog=False, ftype='cheby2', output=frmt))


    # LP: F_PB < F_SB ---------------------------------------------------------
    def LPmin(self, fil_dict):
        self.get_params(fil_dict)
        self.N, self.F_SBC = cheb2ord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                      analog = self.analog)
        self.save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                        btype='lowpass', analog = self.analog, output = frmt))
    def LPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_C,
                             btype='low', analog = self.analog, output = frmt))

    # HP: F_SB < F_PB ---------------------------------------------------------
    def HPmin(self, fil_dict):
        self.get_params(fil_dict)
        self.N, self.F_SBC = cheb2ord(self.F_PB, self.F_SB,self.A_PB,self.A_SB,
                                                      analog = self.analog)
        self.save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                        btype='highpass', analog = self.analog, output = frmt))

    def HPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_C,
                        btype='highpass', analog = self.analog, output = frmt))


    # For BP and BS, A_PB, A_SB, F_PB and F_SB have two elements each

    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1] --------------------------------
    def BPmin(self, fil_dict):
        self.get_params(fil_dict)
        self.N, self.F_SBC = cheb2ord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB, self.A_SB, analog = self.analog)
        self.save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                        btype='bandpass', analog = self.analog, output = frmt))

    def BPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.cheby2(self.N, self.A_SB, [self.F_C, self.F_C2],
                        btype='bandpass', analog = self.analog, output = frmt))


    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1] --------------------------------
    def BSmin(self, fil_dict):
        self.get_params(fil_dict)
        self.N, self.F_SBC = cheb2ord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB, self.A_SB, analog = self.analog)
        self.save(fil_dict, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                        btype='bandstop', analog = self.analog, output = frmt))

    def BSman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.cheby2(self.N, self.A_SB, [self.F_C, self.F_C2],
                        btype='bandstop', analog = self.analog, output = frmt))


#------------------------------------------------------------------------------

if __name__ == '__main__':
    import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
    filt = cheby2()        # instantiate filter
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][frmt]) # return results in default format