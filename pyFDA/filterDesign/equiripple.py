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

# ['Equiripple','LP',['Fs','F_pass','F_stop'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["W_pass","W_stop"],[1,1]]],
# ['Equiripple','HP',['Fs','F_pass','F_stop'],[48000,9600,12000],True,True,"val",["Enter a weight value for each band below",["W_pass","W_stop"],[1,1]]],
# ['Equiripple','BP',['Fs','F_stop1','F_pass1','F_stop2','F_pass2'],[48000,7200,9600,12000,14400],True,True,"val",["Enter a weight value for each band below",["W_stop1","W_pass","W_stop2"],[1,1,1]]],
# ['Equiripple','BS',['Fs','F_pass1','F_stop1','F_pass2','F_stop2'],[48000,7200,9600,12000,14400],True,True,"val",["Enter a weight value for each band below",["W_pass1","W_stop","W_pass2"],[1,1,1]]],      


# TODO: worauf bezieht sich "self" - auf cheby1 oder auf cheby1.LP ?
# TODO: Funktioniert "Vererben" LP -> HP etc.?
# TODO: Für den 'Min'-Fall könnte man cheby1, elllip etc. verbinden mit der 
# iirdesign - Funktion verbinden. Ist das sinnvoll?

class equiripple(object):
    def __init__(self):
        self.zpk = [1, 0, 1]
        self.coeffs = [1, 1]
        self.info = "Equiripple-Filter haben im Passband und im Stopband \
        jeweils konstanten Ripple, sie nutzen das vorgegebene Toleranzband \
        jeweils voll aus."

    def has(self):
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS', 'DIFF', 'HIL'),
                    'ord' : 'N'}

    def LP(self, specs):
        self.needs = ('Order', 'F_pass', 'F_stop', 'W_pass', 'W_stop')
        self.coeffs = sig.remez(specs['Order'],[0, specs['F_pass'], specs['F_stop'], 
                0.5],[1, 0], weight = [specs['W_pass'],specs['W_stop']], Hz = 1)
        self.zpk = [np.roots(self.coeffs), np.zeros(specs['Order']), 1]


    def HP(self, specs):
        self.needs = ('Order', 'F_pass', 'F_stop', 'W_pass', 'W_stop')
        self.coeffs = sig.remez(specs['Order'],[0, specs['F_stop'], specs['F_pass'], 
                0.5],[0, 1], weight = [specs['W_stop'],specs['W_pass']], Hz = 1)
        self.zpk = [np.roots(self.coeffs), np.zeros(specs['Order']), 1]
    # For BP and BS, A_pass, F_pass and F_stop have two elements each
    def BP(self, specs):
        self.needs = ('Order', 'F_pass1', 'F_pass2', 'F_stop1', 'F_stop1',
        'W_pass', 'W_stop1', 'W_stop2' )
        self.coeffs = sig.remez(specs['Order'],[0, specs['F_stop1'], specs['F_pass1'], 
                specs['F_pass2'], specs['F_stop2'], 0.5],[0, 1, 0], 
                weight = [specs['W_stop1'],specs['W_pass'], specs['W_stop2']], Hz = 1)
        self.zpk = [np.roots(self.coeffs), np.zeros(2*specs['Order']), 1]

    def BS(self, specs):
        self.needs = ('Order', 'F_pass1', 'F_pass2', 'F_stop1', 'F_stop1',
        'W_pass1', 'W_pass2', 'W_stop')
        self.coeffs = sig.remez(specs['Order'],[0, specs['F_pass1'], specs['F_stop1'], 
                specs['F_stop2'], specs['F_pass2'], 0.5],[1, 0, 1], 
                weight = [specs['W_pass1'],specs['W_stop'], specs['W_pass2']], Hz = 1)
        self.zpk = [np.roots(self.coeffs), np.zeros(2*specs['Order']), 1]


        