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
class cheby1(FD, specs):
    def __init__(self):
        self.coeff = (1, 1)

    def has(self):
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'),
                    'ord' : ('min', 'fix')}

    def LP(self, specs):
        needs = ('N', 'A_pass', 'F_pass', 'F_stop')
        self.coeff = sig.cheby1(specs['N'], specs['A_pass'],
                        [specs['F_pass'], specs['F_stop']], btype='lowpass')

    def HP(self, specs):
        self.coeff = sig.cheby1(specs['N'], specs['A_pass'],
                        [specs['F_pass'], specs['F_stop']], btype='highpass')

    def BP(self, specs):
        self.coeff = sig.cheby1(specs['N'], specs['A_pass'],
                        [specs['F_pass'], specs['F_stop']], btype='bandpass')

    def BS(self, specs):
        self.coeff = sig.cheby1(specs['N'], specs['A_pass'],
                        [specs['F_pass'], specs['F_stop']], btype='bandstop')

class cheby1_min(FD, specs):
    def __init__(self):
        self.coeff = (1, 1)

    def has(self):
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS')}

    def LP(self, specs):
        self.coeff = sig.iirdesign(specs['F_pass'], specs['F_stop'], 
                                   specs['A_pass'], specs['A_stop'],
                                    analog=False, ftype='cheby1', output='ba')