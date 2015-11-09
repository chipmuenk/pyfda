# -*- coding: utf-8 -*-
"""
Design ellip-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

Attention:
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
from scipy.signal import ellipord
import numpy as np

from pyfda.pyfda_lib import save_fil

__version__ = "1.0"

frmt = 'zpk' #output format of filter design routines 'zpk' / 'ba' / 'sos'

class ellip(object):

    def __init__(self):
        self.name = {'ellip':'Elliptic'}

        # common messages for all man. / min. filter order response types:
        msg_man = ("Enter the filter order <b><i>N</i></b>, the minimum stop "
            "band attenuation <b><i>A<sub>SB</sub></i></b> and the frequency or "
            "frequencies <b><i>F<sub>PB</sub></i></b>  where the gain first "
            "drops below the maximum passband ripple <b><i>-A<sub>PB</sub></i></b> ."
            "Stop band corner frequency(ies) <b><i>F<sub>SB</sub></i></b>&nbsp;"
            "are not regarded.")
        msg_min = ("Enter maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                    "minimum stop band attenuation <b><i>A<sub>SB</sub> </i></b>"
                    "&nbsp;and the corresponding corner frequencies of pass and "
                    "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
                    "<b><i>F<sub>SB</sub></i></b> .")
        # VISIBLE widgets for all man. / min. filter order response types:
        vis_man = ['fo','tspecs'] # manual filter order
        vis_min = ['fo','tspecs'] # minimum filter order

        # DISABLED widgets for all man. / min. filter order response types:
        dis_man = [] # manual filter order
        dis_min = [] # minimum filter order

        # parameters for all man. / min. filter order response types:
        par_man = ['N', 'f_S', 'A_PB', 'A_SB']
        par_min = ['f_S', 'A_PB', 'A_SB']

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
          "BP": {"man":{"par":[]},
                 "min":{"par":['F_SB','F_PB','F_PB2','F_SB2']}},
          "BS": {"man":{"par":[]},
                 "min":{"par":['F_PB','F_SB','F_SB2','F_PB2']}}
                 }

        self.info = """
**Elliptic filters**

(also known as Cauer filters) have a constant ripple :math:`A_PB` resp.
:math:`A_SB` in both pass- and stopband(s).

For the filter design, the order :math:`N`, minimum stopband attenuation
:math:`A_SB` and
the critical frequency / frequencies :math:`F_PB` where the gain first drops below
the maximum passband ripple :math:`-A_PB` have to be specified.

The ``ellipord()`` helper routine calculates the minimum order :math:`N` and the 
critical passband frequency :math:`F_C` from pass and stop band specifications.

**Design routines:**

``scipy.signal.ellip()``
``scipy.signal.ellipord()``

        """

        self.info_doc = []
        self.info_doc.append('ellip()\n========')
        self.info_doc.append(sig.ellip.__doc__)
        self.info_doc.append('ellipord()\n==========')
        self.info_doc.append(ellipord.__doc__)

    def get_params(self, fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        # Frequencies are normalized to f_Nyq, ripple specs are in dB
        self.analog = False # set to True for analog filters
        self.N     = fil_dict['N']
        self.F_PB  = fil_dict['F_PB'] * 2
        self.F_SB  = fil_dict['F_SB'] * 2
        self.F_PB2 = fil_dict['F_PB2'] * 2
        self.F_SB2 = fil_dict['F_SB2'] * 2
        self.F_PBC = None

        self.A_PB  = -20. * np.log10(1. - fil_dict['A_PB'])
        self.A_PB2 = -20. * np.log10(1 -  fil_dict['A_PB2'])
        self.A_SB  = -20. * np.log10(fil_dict['A_SB'])
        self.A_SB2 = -20. * np.log10(fil_dict['A_SB2'])


#        self.A_PB  = fil_dict['A_PB']
#        self.A_PB2 = fil_dict['A_PB2']
#        self.A_SB  = fil_dict['A_SB']
#        self.A_SB2 = fil_dict['A_SB2']
#

    def save(self, fil_dict, arg):
        """
        Store results of filter design in the global filter dictionary. Corner
        frequencies calculated for minimum filter order are also stored in the 
        dictionary to allow for a smooth manual filter design.
        """
        save_fil(fil_dict, arg, frmt, __name__)

        if self.F_PBC is not None: # has corner frequency been calculated?
            fil_dict['N'] = self.N # yes, update filterbroker

            if np.isscalar(self.F_PBC): # HP or LP - a single corner frequency
                fil_dict['F_PB'] = self.F_PBC / 2.
            else: # BP or BS - two corner frequencies
                fil_dict['F_PB'] = self.F_PBC[0] / 2.
                fil_dict['F_PB2'] = self.F_PBC[1] / 2.
                fil_dict['A_PB2'] = self.A_PB
                fil_dict['A_SB2'] = self.A_SB
#------------------------------------------------------------------------------
#
#         DESIGN ROUTINES
#
#------------------------------------------------------------------------------

# HP & LP
#        self.save(fil_dict, iirdesign(self.F_PB, self.F_SB, self.A_PB, 
#                        self.A_SB, analog=False, ftype='ellip', output=frmt))
# BP & BS:
#        self.save(fil_dict, iirdesign([self.F_PB,self.F_PB2], [self.F_SB,self.F_SB2],
#            self.A_PB, self.A_SB, analog=False, ftype='ellip', output=frmt))


    # LP: F_PB < F_stop -------------------------------------------------------
    def LPmin(self, fil_dict):
        """Elliptic LP filter, minimum order"""
        self.get_params(fil_dict)
        self.N, self.F_PBC = ellipord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                          analog = self.analog)
        self.save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                            btype='low', analog = self.analog, output = frmt))
                            
    def LPman(self, fil_dict):
        """Elliptic LP filter, manual order"""
        self.get_params(fil_dict)
        self.save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PB,
                            btype='low', analog = self.analog, output = frmt))

    # HP: F_stop < F_PB -------------------------------------------------------
    def HPmin(self, fil_dict):
        """Elliptic HP filter, minimum order"""
        self.get_params(fil_dict)
        self.N, self.F_PBC = ellipord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                          analog = self.analog)
        self.save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='highpass', analog = self.analog, output = frmt))

    def HPman(self, fil_dict):
        """Elliptic HP filter, manual order"""
        self.get_params(fil_dict)
        self.save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PB,
                        btype='highpass', analog = self.analog, output = frmt))

    # For BP and BS, F_XX have two elements each, A_XX has only one

    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1] --------------------------------
    def BPmin(self, fil_dict):
        """Elliptic BP filter, minimum order"""
        self.get_params(fil_dict)
        self.N, self.F_PBC = ellipord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB, self.A_SB, analog = self.analog)
        self.save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='bandpass', analog = self.analog, output = frmt))
                            
    def BPman(self, fil_dict):
        """Elliptic BP filter, manual order"""
        self.get_params(fil_dict)
        self.save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, 
            [self.F_PB,self.F_PB2], btype='bandpass', analog = self.analog, 
                                                                output = frmt))

    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1] --------------------------------
    def BSmin(self, fil_dict):
        """Elliptic BP filter, minimum order"""
        self.get_params(fil_dict)
        self.N, self.F_PBC = ellipord([self.F_PB, self.F_PB2],
                                [self.F_SB, self.F_SB2], self.A_PB,self.A_SB,
                                                        analog = self.analog)
        self.save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, self.F_PBC,
                        btype='bandstop', analog = self.analog, output = frmt))

    def BSman(self, fil_dict):
        """Elliptic BS filter, manual order"""
        self.get_params(fil_dict)
        self.save(fil_dict, sig.ellip(self.N, self.A_PB, self.A_SB, 
            [self.F_PB,self.F_PB2], btype='bandstop', analog = self.analog, 
                                                                output = frmt))

                            
#------------------------------------------------------------------------------

if __name__ == '__main__':
    import pyfda.filterbroker as fb # importing filterbroker initializes all its globals 
    filt = ellip()        # instantiate filter
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][frmt]) # return results in default format