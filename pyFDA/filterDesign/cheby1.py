# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:13:41 2013

Design cheby1-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

@author: Christian Muenker

Zu erwartende Änderungen in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
#import numpy as np

output = 'zpk' # set output format of filter design routines to 'zpk' or 'ba'

class cheby1(object):
    
    def __init__(self):
        self.name = {'cheby1':'Chebychev 1'}
        self.msg_man = "Enter the filter order $N$, the maximum ripple $A_pb$ \
        allowed below unity gain in the passband and the frequency or \
        frequencies $F_pb$ where the gain first drops below $-A_pb$."
        self.msg_min = "Enter the desired pass band ripple and minimum stop \
        band attenuation and the corresponding corner frequencies."
        self.ft = 'IIR'
        self.rt = {
          "LP": {"man":{"par":['N', 'A_pb', 'F_pb']},
                 "min":{"par":['A_pb','A_sb','F_pb','F_sb']}},
          "HP": {"man":{"par":['N', 'A_pb', 'F_pb']},
                 "min":{"par":['A_pb','A_sb','F_sb','F_pb']}},
          "BP": {"man":{"par":['N', 'A_pb', 'F_pb', 'F_pb2']},
                 "min":{"par":['A_pb','A_sb','F_sb','F_pb','F_pb2','F_sb2']}},
          "BS": {"man":{"par":['A_pb','F_pb','F_pb2']},
                 "min":{"par":['A_pb','A_sb','F_pb','F_sb','F_sb2','F_pb2']}}
                 }

        self.info = "Chebychev Typ 1 Filter haben nur im Passband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im PB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung unter \
        den spezifizierten Wert fällt."

    def save(self, arg):
        """ 
        Convert between poles / zeros / gain, filter coefficients (polynomes) 
        and second-order sections and store all available formats in the global
        database.
        """
        if output == 'zpk': # arg = [z,p,k]
            self.coeffs = sig.zpk2tf(arg[0], arg[1], arg[2])
            self.zpk = arg

        else: # arg = [b,a]
            self.zpk = sig.tf2zpk(arg[0], arg[1])
            self.coeffs = arg

    def LPman(self, specs):
        self.save(sig.cheby1(specs['N'], specs['A_pb'], specs['F_pb'],
                              btype='low', analog = False, output = output))

    def HPman(self, specs):
        self.save(sig.cheby1(specs['N'], specs['A_pb'], specs['F_pb'], 
                             btype='highpass', analog = False, output = output))
        
    # For BP and BS, A_pb, F_pb and F_stop have two elements each
    def BPman(self, specs):
        self.save(sig.cheby1(specs['N'], specs['A_pb'],
                        [specs['F_pb'], specs['F_pb2']], btype='bandpass',
                        analog = False, output = output))
        
    def BSman(self, specs):
        self.save(sig.cheby1(specs['N'], specs['A_pb'],
                [specs['F_pb'], specs['F_pb2']], btype='bandstop', 
                analog = False, output = output))

    # LP: F_pb < F_stop
    def LPmin(self, specs):
        self.save(sig.iirdesign(specs['F_pb'], specs['F_sb'], 
                                   specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby1', output=output))
   
    # HP: F_stop < F_pb                          
    def HPmin(self, specs):
        self.save(sig.iirdesign(specs['F_pb'], specs['F_sb'], 
                                   specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby1', output=output))
        
    # BP: F_stop[0] < F_pb[0], F_stop[1] > F_pb[1]    
    def BPmin(self, specs):
        self.save(sig.iirdesign([specs['F_pb'],specs['F_pb2']], 
                [specs['F_sb'], specs['F_sb2']], specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby2', output=output))

    # BS: F_stop[0] > F_pb[0], F_stop[1] < F_pb[1]            
    def BSmin(self, specs):
        self.save(sig.iirdesign([specs['F_pb'],specs['F_pb2']], 
                [specs['F_sb'], specs['F_sb2']], specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby2', output=output))