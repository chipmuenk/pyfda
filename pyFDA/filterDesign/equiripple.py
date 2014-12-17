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
# import numpy as np

# ['Equiripple','LP',['Fs','F_pb','F_sb'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["W_pb","W_sb"],[1,1]]],
# ['Equiripple','HP',['Fs','F_pb','F_sb'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["W_pb","W_sb"],[1,1]]],
# ['Equiripple','BP',['Fs','F_sb','F_pb','F_sb2','F_pb2'],[48000,7200,9600,12000,14400],True,True,"val",["Enter a weight value for each band below",["W_sb","W_pb","W_sb2"],[1,1,1]]],
# ['Equiripple','BS',['Fs','F_pb','F_sb','F_pb2','F_sb2'],[48000,7200,9600,12000,14400],True,True,"val",["Enter a weight value for each band below",["W_pb","W_sb","W_pass2"],[1,1,1]]],      


# TODO: worauf bezieht sich "self" - auf cheby1 oder auf cheby1.LP ?
# TODO: Funktioniert "Vererben" LP -> HP etc.?
# TODO: Für den 'Min'-Fall könnte man cheby1, elllip etc. verbinden mit der 
# iirdesign - Funktion verbinden. Ist das sinnvoll?

class equiripple(object):
    def __init__(self):
        self.zpk = [1, 0, 1]
        self.coeffs = [1, 1]
        
        self.name = {'equiripple':'Equiripple'}
        self.ft = 'FIR'
        self.rt = {
          "BP": {"ord":['N', 'F_pb', 'F_pb2', 'F_sb', 'F_sb2',
                        'W_pb', 'W_sb', 'W_sb2']},
          "BS": {"ord":['N', 'F_pb', 'F_pb2', 'F_sb', 'F_sb2',
                        'W_pb', 'W_pb2', 'W_sb']},
          "LP": {"ord":['N', 'A_pb', 'F_pb'],
                 "min":['A_pb','A_sb','F_pb','F_sb']},
          "HP": {"ord":['N', 'A_pb', 'F_pb'],
                 "min":['A_pb','A_sb','F_pb','F_sb']},           
                   }
        self.info = "Equiripple-Filter haben im Passband und im Stopband \
        jeweils konstanten Ripple, sie nutzen das vorgegebene Toleranzband \
        jeweils voll aus."
        
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS', 'DIFF', 'HIL'),
                    'ord' : 'N'}

    def LP(self, specs):
        self.needs = ('N', 'F_pb', 'F_sb', 'W_pb', 'W_sb')
        self.coeffs = sig.remez(specs['N'],[0, specs['F_pb'], specs['F_sb'], 
                0.5],[1, 0], weight = [specs['W_pb'],specs['W_sb']], Hz = 1)
        self.zpk = [np.roots(self.coeffs), np.zeros(specs['N']), 1]
        print(specs['N'],[0, specs['F_pb'], specs['F_sb'], 
                0.5],[1, 0], [specs['W_pb'],specs['W_sb']])


    def HP(self, specs):
        self.needs = ('N', 'F_pb', 'F_sb', 'W_pb', 'W_sb')
        self.coeffs = sig.remez(specs['N'],[0, specs['F_sb'], specs['F_pb'], 
                0.5],[0, 1], weight = [specs['W_sb'],specs['W_pb']], Hz = 1)
        self.zpk = [np.roots(self.coeffs), np.zeros(specs['N']), 1]
    # For BP and BS, F_pb and F_sb have two elements each
    def BP(self, specs):
        self.needs = ('N', 'F_pb', 'F_pb2', 'F_sb', 'F_sb2',
        'W_pb', 'W_sb', 'W_sb2' )
        self.coeffs = sig.remez(specs['N'],[0, specs['F_sb'], specs['F_pb'], 
                specs['F_pb2'], specs['F_sb2'], 0.5],[0, 1, 0], 
                weight = [specs['W_sb'],specs['W_pb'], specs['W_sb2']], Hz = 1)
        self.zpk = [np.roots(self.coeffs), np.zeros(2*specs['N']), 1]

    def BS(self, specs):
        self.needs = ('N', 'F_pb', 'F_pb2', 'F_sb', 'F_sb',
        'W_pb', 'W_pb2', 'W_sb')
        self.coeffs = sig.remez(specs['N'],[0, specs['F_pb'], specs['F_sb'], 
                specs['F_sb2'], specs['F_pb2'], 0.5],[1, 0, 1], 
                weight = [specs['W_pb'],specs['W_sb'], specs['W_pb2']], Hz = 1)
        self.zpk = [np.roots(self.coeffs), np.zeros(2*specs['N']), 1]


        