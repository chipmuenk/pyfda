# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:13:41 2013

@author: Christian Muenker
"""
from __future__ import print_function, division
import scipy.signal as sig
# import numpy as np

#['Chebychev 1','LP',['Fs','Fpass'],[48000,9600],True,True,"ub",[["dB","Squared"],["Apass","Astop"],[1,80]]],
#['Chebychev 1','HP',['Fs','Fpass'],[48000,14400],True,True,"ub",[["dB","Squared"],["Apass","Astop"],[1,80]]],
#['Chebychev 1','BP',['Fs','Fpass1','Fpass2'],[48000,9600,12000],True,True,"ub",[["dB","Squared"],["Astopp1","Apass","Astop2"],[60,1,80]]],
#['Chebychev 1','BS',['Fs','Fpass1','Fpass2'],[48000,9600,12000],True,True,"ub",[["dB","Squared"],["Apass1","Astop","Apass2"],[5,60,1]]],                           
#

# TODO: worauf bezieht sich "self" - auf cheby1 oder auf cheby1.LP ?
# TODO: Funktioniert "Vererben" LP -> HP etc.?
# TODO: elllip etc. verbinden?

class cheby1(object):
    def __init__(self):
        self.coeff = (1, 1)

    def has(self):
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'),
                    'ord' : 'N'}

    def LP(self, specs):
        self.needs = ('N', 'A_pass', 'F_pass', 'F_stop')
        self.coeff = sig.cheby1(specs['N'], specs['A_pass'],
                        [specs['F_pass'], specs['F_stop']], btype='lowpass')

    def HP(self, specs):
        self.needs = ('N', 'A_pass', 'F_pass', 'F_stop')
        self.coeff = sig.cheby1(specs['N'], specs['A_pass'],
                        [specs['F_pass'], specs['F_stop']], btype='highpass')
    # For BP and BS, A_pass, F_pass and F_stop have two elements each
    def BP(self, specs):
        self.needs = ('N', 'A_pass', 'F_pass', 'F_stop')
        self.coeff = sig.cheby1(specs['N'], specs['A_pass'],
                        [specs['F_pass'], specs['F_stop']], btype='bandpass')

    def BS(self, specs):
        self.needs = ('N', 'A_pass', 'F_pass', 'F_stop')
        self.coeff = sig.cheby1(specs['N'], specs['A_pass'],
                        [specs['F_pass'], specs['F_stop']], btype='bandstop')

class cheby1_min(object):
    def __init__(self):
        self.coeff = (1, 1)

    def has(self):
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'),
                    'ord' : 'min'}

    # LP: F_pass < F_stop
    def LP(self, specs):
        self.coeff = sig.iirdesign(specs['F_pass'], specs['F_stop'], 
                                   specs['A_pass'], specs['A_stop'],
                             analog=False, ftype='cheby1', output='ba')
        self.needs = ('N', 'A_pass', 'F_pass', 'F_stop')
        
    # HP: F_stop < F_pass                          
    def HP(self, specs):
        self.coeff = self.LP(self, specs)
        
    # BP: F_stop[0] < F_pass[0], F_stop[1] > F_pass[1]    
    def BP(self, specs):
        self.coeff = self.LP(self, specs)

    # BS: F_stop[0] > F_pass[0], F_stop[1] < F_pass[1]            
    def BS(self, specs):
        self.coeff = self.LP(self, specs)
        