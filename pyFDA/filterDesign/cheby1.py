# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:13:41 2013

Design cheby1-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

@author: Christian Muenker

Zu erwartende Änderungen in scipy 0.15:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
import numpy as np

zpkba = 'ba' # set output format of filter design routines to 'zpk' or 'ba'

class cheby1(object):
    
    def __init__(self):
        self.name = {'cheby1':'Chebychev 1'}
        self.msg_man = ""
        self.msg_min = ""
        self.ft = 'IIR'
        self.rt = {
          "BP": {"man":{"par":['N', 'A_pb', 'F_pb', 'F_pb2']},
                 "min":{"par":['A_pb','A_sb','F_sb','F_pb','F_pb2','F_sb2']}},
          "BS": {"man":{"par":['A_pb','F_pb','F_pb2']},
                 "min":{"par":['A_pb','A_sb','F_pb','F_sb','F_sb2','F_pb2']}},
          "LP": {"man":{"par":['N', 'A_pb', 'F_pb']},
                 "min":{"par":['A_pb','A_sb','F_pb','F_sb']}},
          "HP": {"man":{"par":['N', 'A_pb', 'F_pb']},
                 "min":{"par":['A_pb','A_sb','F_sb','F_pb']}}
                 }

        self.info = "Chebychev Typ 1 Filter haben nur im Passband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im PB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung unter \
        den spezifizierten Wert fällt."

    def zpk2ba(self, arg):
        """ 
        Convert poles / zeros / gain to filter coefficients (polynomes) and the
        other way round
        """
        if zpkba == 'zpk': # arg = zpk
            self.coeffs = [arg[2] * np.poly(arg[0]), np.poly(arg[1])]
            self.zpk = arg

        else: # arg = [b,a]
            self.zpk = [np.roots(arg[0]), np.roots(arg[1]),1]
            self.coeffs = arg
        print("zpk :", self.zpk,"\nba :", self.coeffs)

    def LPman(self, specs):
        self.zpk2ba(sig.cheby1(specs['N'], specs['A_pb'], specs['F_pb'],
                              btype='low', analog = False, output = zpkba))

    def HPman(self, specs):
        self.zpk2ba(sig.cheby1(specs['N'], specs['A_pb'], specs['F_pb'], 
                             btype='highpass', analog = False, output = zpkba))
        
    # For BP and BS, A_pb, F_pb and F_stop have two elements each
    def BPman(self, specs):
        self.zpk2ba(sig.cheby1(specs['N'], specs['A_pb'],
                        [specs['F_pb'], specs['F_pb2']], btype='bandpass',
                        analog = False, output = zpkba))
        
    def BSman(self, specs):
        self.zpk2ba(sig.cheby1(specs['N'], specs['A_pb'],
                [specs['F_pb'], specs['F_pb2']], btype='bandstop', 
                analog = False, output = zpkba))

    # LP: F_pb < F_stop
    def LPmin(self, specs):
        self.zpk2ba(sig.iirdesign(specs['F_pb'], specs['F_sb'], 
                                   specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby1', output=zpkba))
   
    # HP: F_stop < F_pb                          
    def HPmin(self, specs):
        self.zpk2ba(sig.iirdesign(specs['F_pb'], specs['F_sb'], 
                                   specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby1', output=zpkba))
        
    # BP: F_stop[0] < F_pb[0], F_stop[1] > F_pb[1]    
    def BPmin(self, specs):
        self.zpk2ba(sig.iirdesign([specs['F_pb'],specs['F_pb2']], 
                [specs['F_sb'], specs['F_sb2']], specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby2', output=zpkba))

    # BS: F_stop[0] > F_pb[0], F_stop[1] < F_pb[1]            
    def BSmin(self, specs):
        self.zpk2ba(sig.iirdesign([specs['F_pb'],specs['F_pb2']], 
                [specs['F_sb'], specs['F_sb2']], specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby2', output=zpkba))