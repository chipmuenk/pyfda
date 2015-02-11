# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:13:41 2013

Design cheby1-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

@author: Christian Muenker

Expected changes in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
from scipy.signal import cheb1ord, zpk2tf, tf2zpk #, iirdesign
import numpy as np

output = 'zpk' # set output format of filter design routines to 'zpk' or 'ba'

class cheby1(object):
    
    def __init__(self):
        self.name = {'cheby1':'Chebychev 1'}
        
        # common messages for all man. / min. filter order response types:            
        msg_man = ("Enter the filter order <b><i>N</i></b>, the maximum ripple "
            "<b><i>A<sub>PB</sub></i></b> allowed below unity gain in the "
            " passband and the frequency or frequencies "
            "<b><i>F<sub>PB</sub></i></b>  where the gain first drops below "
            "<b><i>-A<sub>PB</sub></i></b> .")
        msg_min = ("Enter the desired pass band ripple and minimum stop "
            "band attenuation and the corresponding corner frequencies.")

        # enabled widgets for all man. / min. filter order response types:    
        enb_man = ['fo','fspec','aspec'] # enabled widget for man. filt. order
        enb_min = ['fo','fspec','aspec'] # enabled widget for min. filt. order
        
        # parameters for all man. / min. filter order response types:    
        par_man = ['N', 'f_S', 'F_PB', 'A_PB'] # enabled widget for man. filt. order
        par_min = ['f_S', 'A_PB', 'A_SB'] # enabled widget for min. filt. order

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
          "BP": {"man":{"par":['F_PB2']},
                 "min":{"par":['F_SB','F_PB','F_PB2','F_SB2']}},
          "BS": {"man":{"par":['F_PB2']},
                 "min":{"par":['F_PB','F_SB','F_SB2','F_PB2']}}
                 }

        self.info = "Chebychev Typ 1 Filter haben nur im Passband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im PB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung unter \
        den spezifizierten Wert fällt."

    def get_params(self,specs):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = specs['N']
        self.F_PB  = specs['F_PB'] * 2 # Frequencies are normalized to f_Nyq
        self.F_SB  = specs['F_SB'] * 2 
        self.F_PB2 = specs['F_PB2'] * 2
        self.F_SB2 = specs['F_SB2'] * 2 
        self.F_PBC = None
        self.A_PB  = specs['A_PB']
        self.A_SB  = specs['A_SB']
        self.A_PB2 = specs['A_PB2']
        self.A_SB2 = specs['A_SB2']

    def save(self, specs, arg):
        """ 
        Convert between poles / zeros / gain, filter coefficients (polynomes) 
        and second-order sections and store all available formats in the global
        database.
        """
        if output == 'zpk': # arg = [z,p,k]
            self.coeffs = zpk2tf(arg[0], arg[1], arg[2])
            self.zpk = arg
        else: # arg = [b,a]
            self.zpk = tf2zpk(arg[0], arg[1])
            self.coeffs = arg

        specs['coeffs'] = self.coeffs
        specs['zpk'] = self.zpk
        
        if self.F_PBC is not None: # has corner frequency been calculated?
            specs['N'] = self.N # yes, update filterbroker
#            print("====== cheby1.save ========\nF_PBC = ", self.F_PBC, type(self.F_PBC))
#            print("F_PBC vor", self.F_PBC, type(self.F_PBC))
            if np.isscalar(self.F_PBC): # HP or LP - a single corner frequency
                specs['F_PB'] = self.F_PBC / 2.
            else: # BP or BS - two corner frequencies
                specs['F_PB'] = self.F_PBC[0] / 2.
                specs['F_PB2'] = self.F_PBC[1] / 2.

    def LPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby1(self.N, self.A_PB, self.F_PB,
                            btype='low', analog = False, output = output))
                            
    # LP: F_PB < F_stop
    def LPmin(self, specs):
        self.get_params(specs)
        self.N, self.F_PBC = cheb1ord(self.F_PB,self.F_SB, self.A_PB,self.A_SB)
        self.save(specs, sig.cheby1(self.N, self.A_PB, self.F_PBC,
                            btype='low', analog = False, output = output))
#
#        self.save(specs, iirdesign(self.F_PB, self.F_SB, self.A_PB, self.A_SB,
#                             analog=False, ftype='cheby1', output=output))

    def HPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby1(self.N, self.A_PB, self.F_PB,
                            btype='highpass', analog = False, output = output))

    # HP: F_stop < F_PB                          
    def HPmin(self, specs):
        self.get_params(specs)
        self.N, self.F_PBC = cheb1ord(self.F_PB,self.F_SB, self.A_PB,self.A_SB)
        self.save(specs, sig.cheby1(self.N, self.A_PB, self.F_PBC,
                            btype='highpass', analog = False, output = output))
        
    # For BP and BS, A_PB, F_PB and F_stop have two elements each
        
    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1]    
    def BPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby1(self.N, self.A_PB,[self.F_PB,self.F_PB2],
                            btype='bandpass', analog = False, output = output))
                            

    def BPmin(self, specs):
        self.get_params(specs) 
        self.N, self.F_PBC = cheb1ord([self.F_PB, self.F_PB2], 
                                [self.F_SB, self.F_SB2], self.A_PB,self.A_SB)
        self.save(specs, sig.cheby1(self.N, self.A_PB, self.F_PBC,
                            btype='bandpass', analog = False, output = output))
                                
#        self.save(specs, iirdesign([self.F_PB,self.F_PB2], [self.F_SB,self.F_SB2],
#            self.A_PB, self.A_SB, analog=False, ftype='cheby1', output=output))

        
    def BSman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby1(self.N, self.A_PB, [self.F_PB,self.F_PB2],
                            btype='bandstop', analog = False, output = output))   

    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1]            
    def BSmin(self, specs):
        self.get_params(specs)
        self.N, self.F_PBC = cheb1ord([self.F_PB, self.F_PB2], 
                                [self.F_SB, self.F_SB2], self.A_PB,self.A_SB)
        self.save(specs, sig.cheby1(self.N, self.A_PB, self.F_PBC,
                            btype='bandstop', analog = False, output = output))