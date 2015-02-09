# -*- coding: utf-8 -*-
"""
Created on Wed December 17 2014

Design cheby2-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

@author: Christian Muenker

Expected changes in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division
import scipy.signal as sig
from scipy.signal import cheb2ord, zpk2tf, tf2zpk #  iirdesign, 
#import numpy as np

output = 'ba' # set output format of filter design routines to 'zpk' or 'ba'

class cheby2(object):    
    
    def __init__(self):

        self.name = {'cheby2':'Chebychev 2'}

        # common messages for all man. / min. filter order response types:    
        msg_man = ("Enter the filter order <b><i>N</i></b>, the minimum stop band "
            "attenuation <b><i>A<sub>SB</sub></i></b>, and the frequency / "
            "frequencies <b><i>F<sub>SB</sub></i></b> where gain first drops "
            "below <b><i>A<sub>SB</sub></i></b>.")
        msg_min = ("Enter the maximum pass band ripple and minimum stop band "
                    "attenuation and the corresponding corner frequencies.")

        # enabled widgets for all man. / min. filter order response types:    
        enb_man = ['fo','fspec','aspec'] # enabled widget for man. filt. order
        enb_min = ['fo','fspec','aspec'] # enabled widget for min. filt. order
        
        # common parameters for all man. / min. filter order response types:    
        par_man = ['N', 'f_S', 'F_SB', 'A_SB'] # enabled widget for man. filt. order
        par_min = ['f_S', 'A_PB', 'A_SB'] # enabled widget for min. filt. order

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types 
        # (common data comes first):
        self.com = {"man":{"enb":enb_man, "msg":msg_man, "par": par_man},
                    "min":{"enb":enb_min, "msg":msg_min, "par": par_min}}

        self.ft = 'IIR'
        self.rt = {
          "LP": {"man":{"par":[]},
                 "min":{"par":['F_PB','F_SB']}},
          "HP": {"man":{"par":[]},
                 "min":{"par":['F_SB','F_PB']}},
          "BP": {"man":{"par":['F_SB2']},
                 "min":{"par":['F_SB','F_PB','F_PB2','F_SB2']}},
          "BS": {"man":{"par":['F_SB2']},
                 "min":{"par":['F_PB','F_SB','F_SB2','F_PB2']}}
                 }

        self.info = ("Chebychev Typ 2 Filter haben nur im Stopband Ripple. "
        "Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im SB "
        "und über die kritische(n) Frequenz(en) bei denen die Verstärkung "
        "zuerst den spezifizierten Wert A_SB erreicht.")
        
    def get_params(self,specs):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        self.N     = specs['N']
        self.F_PB  = specs['F_PB'] * 2
        self.F_SB  = specs['F_SB'] * 2
        self.F_PB2 = specs['F_PB2'] * 2
        self.F_SB2 = specs['F_SB2'] * 2 
        self.A_PB  = specs['A_PB']
        self.A_SB  = specs['A_SB']
        self.A_PB2 = specs['A_PB2']
        self.A_SB2 = specs['A_SB2']

    def save(self, specs, arg):
        """ 
        Convert poles / zeros / gain to filter coefficients (polynomes) and the
        other way round
        """
        if output == 'zpk': # arg = [z,p,k]
            self.coeffs = zpk2tf(arg[0], arg[1], arg[2])
            self.zpk = arg

        else: # arg = [b,a]
            self.zpk = tf2zpk(arg[0], arg[1])
            self.coeffs = arg
            
        specs['coeffs'] = self.coeffs
        specs['zpk'] = self.zpk
        try: # has the order been calculated by a "min" filter design?
            specs['N'] = self.N # yes, update filterbroker
            print("sbc", self.F_SBC, type(self.F_SBC))
            if self.F_SBC.type in (tuple, list):
                specs['F_SB'] = self.F_SBC[0] / 2.
                specs['F_SB2'] = self.F_SBC[1] / 2.
            else:
                specs['F_SB'] = self.F_SBC / 2.
        except AttributeError:
            pass

    def LPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby2(self.N, self.A_SB, self.F_SB,
                              btype='low', analog = False, output = output))
    # LP: F_PB < F_SB
    def LPmin(self, specs):
        self.get_params(specs)
        self.N, self.F_SBC = cheb2ord(self.F_PB,self.F_SB, self.A_PB,self.A_SB)
        self.save(specs, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                            btype='lowpass', analog = False, output = output))
#        self.save(specs, iirdesign(self.F_PB, self.F_SB, self.A_PB, self.A_SB,
#                             analog=False, ftype='cheby2', output=output))

    def HPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby2(self.N, self.A_SB, self.F_SB, 
                            btype='highpass', analog = False, output = output))
        
    # HP: F_SB < F_PB                          
    def HPmin(self, specs):
        self.get_params(specs)
        self.N, self.F_SBC = cheb2ord(self.F_PB, self.F_SB,self.A_PB,self.A_SB)
        self.save(specs, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                            btype='highpass', analog = False, output = output))



    # For BP and BS, A_PB, A_SB, F_PB and F_SB have two elements each
    def BPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby2(self.N, self.A_SB, [self.F_SB, self.F_SB2], 
                            btype='bandpass', analog = False, output = output))
        
    # BP: F_SB[0] < F_PB[0], F_SB[1] > F_PB[1]    
    def BPmin(self, specs):
        self.get_params(specs)
        self.N, self.F_SBC = cheb2ord([self.F_PB, self.F_PB2],
                                [self.F_SB, self.F_SB2],self.A_PB,self.A_SB)

        self.save(specs, sig.cheby2(self.N, self.A_SB, self.F_SBC,
                            btype='bandpass', analog = False, output = output))
#        self.save(specs, iirdesign([self.F_PB,self.F_PB2], 
#                [self.F_SB, self.F_SB2], self.A_PB, self.A_SB,
#                             analog=False, ftype='cheby2', output=output))

    def BSman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby2(self.N, self.A_SB, [self.F_SB, self.F_SB2],
                        btype='bandstop', analog = False, output = output))

    # BS: F_SB[0] > F_PB[0], F_SB[1] < F_PB[1]            
    def BSmin(self, specs):
        self.get_params(specs)
        self.N, self.F_SBC = cheb2ord([self.F_PB, self.F_PB2],
                                [self.F_SB, self.F_SB2],self.A_SB,self.A_SB)

        self.save(specs, sig.cheby2(self.N, self.A_PB, self.F_SBC,
                            btype='bandstop', analog = False, output = output))
