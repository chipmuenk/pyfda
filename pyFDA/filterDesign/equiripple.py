# -*- coding: utf-8 -*-
"""
Design equiripple-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format
Created on Tue Nov 26 12:13:41 2013

@author: Christian Muenker

Zu erwartende Änderungen in scipy 0.15:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division
import scipy.signal as sig
import numpy as np

# TODO: HP, BS do not work correctly
# TODO: Add remezord

zpkba = 'ba' # set output format of filter design routines to 'zpk' or 'ba'
             # currently, only 'ba' is supported for equiripple routines

class equiripple(object):
    
    def __init__(self):
        self.name = {'equiripple':'Equiripple'}
        self.msg_man = "Enter a weight value for each band below"
        
        self.ft = 'FIR'
        self.rt = {
            "LP": {"man":{"par":['N', 'W_pb', 'W_sb', 'F_pb', 'F_sb']}},
#                 "min":{"par":['A_pb','A_sb','F_pb','F_sb']}},
            "HP": {"man":{"par":['N', 'W_sb', 'W_pb', 'F_sb','F_pb']}},
            "BP": {"man":{"par":['N', 'F_sb', 'F_pb', 'F_pb2', 'F_sb2',
                        'W_sb', 'W_pb', 'W_sb2']}},
            "BS": {"man":{"par":['N', 'F_pb', 'F_sb', 'F_sb2', 'F_pb2',
                        'W_pb', 'W_sb', 'W_pb2']}}
          #"HIL":
            #"DIFF"
                   }
        self.info = "Equiripple-Filter haben im Passband und im Stopband \
        jeweils konstanten Ripple, sie nutzen das vorgegebene Toleranzband \
        jeweils voll aus."

    def zpk2ba(self, arg):
        """ 
        Convert poles / zeros / gain to filter coefficients (polynomes) and the
        other way round
        """
        if zpkba == 'zpk': # arg = zpk
            self.coeffs = [arg[2] * np.poly(arg[0]), np.poly(arg[1])]
            self.zpk = arg
        else: # arg = [b,a]
            self.zpk = [np.roots(arg), np.zeros(len(arg)),1]
            self.coeffs = arg
        print("zpk :", self.zpk,"\nba :", self.coeffs)
      

    def LPman(self, specs):
        self.zpk2ba(sig.remez(specs['N'],[0, specs['F_pb'], specs['F_sb'], 
                0.5],[1, 0], weight = [specs['W_pb'],specs['W_sb']], Hz = 1))

    def HPman(self, specs):
        self.zpk2ba(sig.remez(specs['N'],[0, specs['F_sb'], specs['F_pb'], 
                0.5],[0, 1], weight = [specs['W_sb'],specs['W_pb']], Hz = 1))
        
    # For BP and BS, F_pb and F_sb have two elements each
    def BPman(self, specs):
        self.zpk2ba(sig.remez(specs['N'],[0, specs['F_sb'], specs['F_pb'], 
                specs['F_pb2'], specs['F_sb2'], 0.5],[0, 1, 0], 
                weight = [specs['W_sb'],specs['W_pb'], specs['W_sb2']], Hz = 1))

    def BSman(self, specs):
        self.zpk2ba(sig.remez(specs['N'],[0, specs['F_pb'], specs['F_sb'], 
                specs['F_sb2'], specs['F_pb2'], 0.5],[1, 0, 1], 
                weight = [specs['W_pb'],specs['W_sb'], specs['W_pb2']], Hz = 1))


        