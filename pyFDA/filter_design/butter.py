# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:13:41 2013

Design butterworth-Filters (LP, HP, BP, BS) with fixed or minimum order,
return the filter design in zeros, poles, gain (zpk) format

@author: Christian Muenker

Expected changes in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
from scipy.signal import buttord
import numpy as np

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    import sys, os
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))
    import filterbroker as fb # importing filterbroker initializes all its globals
    
import pyfda_lib

frmt = 'zpk' # output format of filter design routines 'zpk' / 'ba' / 'sos'

class butter(object):

    def __init__(self):
        self.name = {'butter':'Butterworth'}

        # common messages for all man. / min. filter order response types:
        msg_man = ("Enter the filter order <b><i>N</i></b> and the -3 dB corner "
            "frequency or frequencies <b><i>F<sub>C</sub></i></b>.")
        msg_min = ("Enter the maximum pass band ripple <b><i>A<sub>PB</sub></i></b> "
                    "and minimum stop band attenuation <b><i>A<sub>SB</sub></i></b> "
                    "and the corresponding corner frequencies of pass and "
                    "stop band, <b><i>F<sub>PB</sub></i></b> and "
                    "<b><i>F<sub>PB</sub></i></b>.")

        # VISIBLE widgets for all man. / min. filter order response types:
        vis_man = ['fo','fspecs','tspecs'] # manual filter order
        vis_min = ['fo','tspecs'] # minimum filter order

        # enabled widgets for all man. / min. filter order response types:
        enb_man = ['fo','fspecs'] # enabled widget for man. filt. order
        enb_min = ['fo','fspecs','aspecs','tspecs'] # enabled widget for min. filt. order

        # parameters for all man. / min. filter order response types:
        par_man = ['N', 'f_S', 'F_C']
        par_min = ['f_S', 'A_PB', 'A_SB']

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types
        # (common data comes first):
        self.com = {"man":{"enb":enb_man, "msg":msg_man, "par":par_man},
                    "min":{"enb":enb_min, "msg":msg_min, "par":par_min}}

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
**Butterworth filters**

have ripple in neither pass- nor stopband(s).

For the filter design, only the order :math:`N` and
the - 3dB corner frequency / frequencies :math:`F_C` can be specified.

The ``buttord()`` helper routine calculates the minimum order :math:`N` and the 
critical frequency from passband / stopband specifications.

**Design routines:**

``scipy.signal.butter()``
``scipy.signal.buttord()``

        """

        self.info_doc = []
        self.info_doc.append('butter()\n========')
        self.info_doc.append(sig.butter.__doc__)
        self.info_doc.append('buttord()\n==========')
        self.info_doc.append(buttord.__doc__)

    def get_params(self,fil_dict):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.analog = False # set to True for analog filters
        self.N     = fil_dict['N']
        # Frequencies are normalized to f_Nyq        
        self.F_PB  = fil_dict['F_PB'] * 2
        self.F_SB  = fil_dict['F_SB'] * 2
        self.F_C   = fil_dict['F_C'] * 2 
        self.F_PB2 = fil_dict['F_PB2'] * 2
        self.F_SB2 = fil_dict['F_SB2'] * 2
        self.F_C2   = fil_dict['F_C2'] * 2 
        self.F_PBC = None

        self.A_PB  = fil_dict['A_PB']
        self.A_SB  = fil_dict['A_SB']

    def save(self, fil_dict, arg):
        """
        Convert between poles / zeros / gain, filter coefficients (polynomes)
        and second-order sections and store all available formats in the global
        database.
        """
        pyfda_lib.save_fil(fil_dict, arg, frmt, __name__)

        if self.F_PBC is not None: # has corner frequency been calculated?
            fil_dict['N'] = self.N # yes, update filterbroker
#            print("====== butter.save ========\nF_PBC = ", self.F_PBC, type(self.F_PBC))
#            print("F_PBC vor", self.F_PBC, type(self.F_PBC))
            if np.isscalar(self.F_PBC): # HP or LP - a single corner frequency
                fil_dict['F_C'] = self.F_PBC / 2.
            else: # BP or BS - two corner frequencies
                fil_dict['F_C'] = self.F_PBC[0] / 2.
                fil_dict['F_C2'] = self.F_PBC[1] / 2.
                
#------------------------------------------------------------------------------
#
#         DESIGN ROUTINES
#
#------------------------------------------------------------------------------

# HP & LP
#        self.save(fil_dict, iirdesign(self.F_PB, self.F_SB, self.A_PB, 
#                        self.A_SB, analog=False, ftype='butter', output=frmt))
# BP & BS:
#        self.save(fil_dict, iirdesign([self.F_PB,self.F_PB2], [self.F_SB,self.F_SB2],
#            self.A_PB, self.A_SB, analog=False, ftype='butter', output=frmt))


    # LP: F_PB < F_SB  -------------------------------------------------------- 
    def LPmin(self, fil_dict):
        self.get_params(fil_dict)
        self.N, self.F_PBC = buttord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                     analog = self.analog)
        self.save(fil_dict, sig.butter(self.N, self.F_PBC, btype='low',
                                       analog = self.analog, output = frmt))

    def LPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.butter(self.N, self.F_C,
                            btype='low', analog = self.analog, output = frmt))

    # HP: F_SB < F_PB -------------------------------------------------------
    def HPmin(self, fil_dict):
        self.get_params(fil_dict)
        self.N, self.F_PBC = buttord(self.F_PB,self.F_SB, self.A_PB,self.A_SB,
                                                         analog = self.analog)
        self.save(fil_dict, sig.butter(self.N, self.F_PBC, btype='highpass',
                                      analog = self.analog, output = frmt))

    def HPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.butter(self.N, self.F_PB, btype='highpass',
                                      analog = self.analog, output = frmt))


    # For BP and BS, F_xx have two elements each,  A_xx only have one element

    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1] --------------------------------
    def BPmin(self, fil_dict):
        self.get_params(fil_dict)
        self.N, self.F_PBC = buttord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB, self.A_SB, analog = self.analog)
        self.save(fil_dict, sig.butter(self.N, self.F_PBC, btype='bandpass',
                                       analog = self.analog, output = frmt))

    def BPman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.butter(self.N, [self.F_C,self.F_C2],
                    btype='bandpass', analog = self.analog, output = frmt))

    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1] --------------------------------
    def BSmin(self, fil_dict):
        self.get_params(fil_dict)
        self.N, self.F_PBC = buttord([self.F_PB, self.F_PB2],
            [self.F_SB, self.F_SB2], self.A_PB,self.A_SB, analog = self.analog)
        self.save(fil_dict, sig.butter(self.N, self.F_PBC, btype='bandstop',
                                       analog = self.analog, output = frmt))

    def BSman(self, fil_dict):
        self.get_params(fil_dict)
        self.save(fil_dict, sig.butter(self.N, [self.F_C,self.F_C2],
                        btype='bandstop', analog = self.analog, output = frmt))
                           
#------------------------------------------------------------------------------

if __name__ == '__main__':
    filt = butter()        # instantiate filter
    filt.LPman(fb.fil[0])  # design a low-pass with parameters from global dict
    print(fb.fil[0][frmt]) # return results in default format