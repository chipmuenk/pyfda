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
#import numpy as np

output = 'ba' # set output format of filter design routines to 'zpk' or 'ba'

class cheby2(object):    
    
    def __init__(self):

        self.name = {'cheby2':'Chebychev 2'}
        msg_man = "Enter the filter order $N$, the maximum ripple $A_pb$ \
        allowed below unity gain in the passband and the frequency or \
        frequencies $F_pb$ where the gain first drops below $-A_pb$."
        msg_min = "Enter the desired pass band ripple and minimum stop \
        band attenuation and the corresponding corner frequencies."


 # enabled widgets and common messages for man. / min. filt. order
        self.com = {"man":{"enb":['fo','fspec','aspec'], "msg":msg_man},
                    "min":{"enb":['fo','fspec','aspec'], "msg":msg_min}}

        self.ft = 'IIR'
        self.rt = {
          "BP": {"man":{"par":['N','A_sb','F_sb','F_sb2']},
                 "min":{"par":['A_pb','A_sb','F_sb','F_pb','F_pb2','F_sb2']}},
          "BS": {"man":{"par":['A_sb','F_sb','F_sb2']},
                 "min":{"par":['A_pb','A_sb','F_pb','F_sb','F_sb2','F_pb2']}},
          "LP": {"man":{"par":['N', 'A_sb', 'F_sb']},
                 "min":{"par":['A_pb','A_sb','F_pb','F_sb']}},
          "HP": {"man":{"par":['N', 'A_sb', 'F_sb']},
                 "min":{"par":['A_pb','A_sb','F_sb','F_pb']}}
                 }

        self.msg_man = ""
        self.info = "Chebychev Typ 2 Filter haben nur im Stopband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im SB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung zuerst\
        den spezifizierten Wert A_sb erreicht."
        
    def save(self, arg):
        """ 
        Convert poles / zeros / gain to filter coefficients (polynomes) and the
        other way round
        """
        if output == 'zpk': # arg = [z,p,k]
            self.coeffs = sig.zpk2tf(arg[0], arg[1], arg[2])
            self.zpk = arg

        else: # arg = [b,a]
            self.zpk = sig.tf2zpk(arg[0], arg[1])
            self.coeffs = arg

    def LPman(self, specs):
        self.save(sig.cheby2(specs['N'], specs['A_sb'], specs['F_sb'],
                              btype='low', analog = False, output = output))

    def HPman(self, specs):
        self.save(sig.cheby2(specs['N'], specs['A_sb'], specs['F_sb'], 
                             btype='highpass', analog = False, output = output))
        
    # For BP and BS, A_pb, A_sb, F_pb and F_sb have two elements each
    def BPman(self, specs):
        self.save(sig.cheby2(specs['N'], specs['A_sb'],
                        [specs['F_sb'], specs['F_sb2']], btype='bandpass',
                        analog = False, output = output))
        
    def BSman(self, specs):
        self.save(sig.cheby2(specs['N'], specs['A_sb'],
                [specs['F_sb'], specs['F_sb2']], btype='bandstop', 
                analog = False, output = output))
        
    # LP: F_pb < F_sb
    def LPmin(self, specs):
        self.save(sig.iirdesign(specs['F_pb'], specs['F_sb'], 
                                   specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby2', output=output))

    # HP: F_sb < F_pb                          
    def HPmin(self, specs):
        self.save(sig.iirdesign(specs['F_pb'], specs['F_sb'], 
                                   specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby2', output=output))
        
    # BP: F_sb[0] < F_pb[0], F_sb[1] > F_pb[1]    
    def BPmin(self, specs):
        self.save(sig.iirdesign([specs['F_pb'],specs['F_pb2']], 
                [specs['F_sb'], specs['F_sb2']], specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby2', output=output))

    # BS: F_sb[0] > F_pb[0], F_sb[1] < F_pb[1]            
    def BSmin(self, specs):
        self.save(sig.iirdesign([specs['F_pb'],specs['F_pb2']], 
                [specs['F_sb'], specs['F_sb2']], specs['A_pb'], specs['A_sb'],
                            analog=False, ftype='cheby2', output=output)) 