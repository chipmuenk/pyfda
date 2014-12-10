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
from __future__ import print_function, division
import scipy.signal as sig
import numpy as np
# import numpy as np

#   ['Chebychev 1','LP',['Fs','F_pass'],[48000,9600],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
#   ['Chebychev 1','HP',['Fs','F_pass'],[48000,14400],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
#   ['Chebychev 1','BP',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
#   ['Chebychev 1','BS',['Fs','F_pass1','F_pass2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],


# TODO: worauf bezieht sich "self" - auf cheby1 oder auf cheby1.LP ?
# TODO: Funktioniert "Vererben" LP -> HP etc.?
# TODO: Für den 'Min'-Fall könnte man cheby1, elllip etc. verbinden mit der 
# iirdesign - Funktion verbinden. Ist das sinnvoll?

def zpk2ba(zpk):
    """ 
    Convert poles / zeros / gain to filter coefficients (polynomes)
    """
    coeffs = [zpk[2] * np.poly(zpk[0]), np.poly(zpk[1])]
    return coeffs

class cheby1(object):
    

    
    def __init__(self):

        self.zpk = [1, 0, 1]
        self.coeffs = [1, 1]
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'), 'ord' : 'N'}
        self.prop = {'name':'Chebychev 1', 'ft':'IIR'}
        self.info = "Chebychev Typ 1 Filter haben nur im Passband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im PB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung unter \
        den spezifizierten Wert fällt."

    def has(self):
        self.has = {
                    'rt' : ('LP', 'HP', 'BP', 'BS'),
                    'ord' : 'N'}
                    
#    def info():
#      """
#      usage: print(cheby1.info())
#      """
#      return {'rt' : ('LP', 'HP', 'BP', 'BS'),
#                    'ord' : 'N'}

    def LP(self, specs):
        self.needs = ('Order', 'A_pass', 'F_pass')
        self.zpk = sig.cheby1(specs['Order'], specs['A_pass'], specs['F_pass'],
                              btype='low', analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)

    def HP(self, specs):
        self.needs = ('Order', 'A_pass', 'F_pass')
        self.zpk = sig.cheby1(specs['Order'], specs['A_pass'], specs['F_pass'], 
                              btype='highpass', analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
    # For BP and BS, A_pass, F_pass and F_stop have two elements each
    def BP(self, specs):
        self.needs = ('Order', 'A_pass', 'F_pass1', 'F_pass2')
        self.zpk = sig.cheby1(specs['Order'], specs['A_pass'],
                        [specs['F_pass1'], specs['F_pass2']], btype='bandpass',
                        analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
    def BS(self, specs):
        self.needs = ('Order', 'A_pass', 'F_pass1', 'F_pass2')
        self.zpk = sig.cheby1(specs['Order'], specs['A_pass'],
                [specs['F_pass1'], specs['F_pass2']], btype='bandstop', 
                analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
class cheby1_min(object):
    def __init__(self):
        self.zpk = [1, 0, 1]
        self.coeffs = [1, 1]

    def has(self):
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'),
                    'ord' : 'min'}

    # LP: F_pass < F_stop
    def LP(self, specs):
        self.needs = ('N', 'A_pass', 'F_pass', 'F_stop')
        self.zpk = sig.iirdesign(specs['F_pass'], specs['F_stop'], 
                                   specs['A_pass'], specs['A_stop'],
                             analog=False, ftype='cheby1', output='zpk')
        self.coeffs = zpk2ba(self.zpk)

        
    # HP: F_stop < F_pass                          
    def HP(self, specs):
        self.zpk = self.LP(self, specs)
        self.coeffs = zpk2ba(self.zpk)
        
    # BP: F_stop[0] < F_pass[0], F_stop[1] > F_pass[1]    
    def BP(self, specs):
        self.zpk = self.LP(self, specs)
        self.coeffs = zpk2ba(self.zpk)

    # BS: F_stop[0] > F_pass[0], F_stop[1] < F_pass[1]            
    def BS(self, specs):
        self.zpk = self.LP(self, specs)
        self.coeffs = zpk2ba(self.zpk)      