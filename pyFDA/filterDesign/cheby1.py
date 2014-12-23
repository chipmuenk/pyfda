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
# import numpy as np

#   ['Chebychev 1','LP',['Fs','F_pb'],[48000,9600],True,True,"unt",[["dB","Squared"],["A_p"],[1]]],
#   ['Chebychev 1','HP',['Fs','F_pb'],[48000,14400],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
#   ['Chebychev 1','BP',['Fs','F_pb1','F_pb2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],
#   ['Chebychev 1','BS',['Fs','F_pb1','F_pb2'],[48000,9600,12000],True,True,"unt",[["dB","Squared"],["A_pass"],[1]]],


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
#        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'), 'man' : 'N'}
        self.name = {'cheby1':'Chebychev 1'}
        self.ft = 'IIR'
        self.rt = {
          "BP": {"man":['N', 'A_pb', 'F_pb', 'F_pb2'],
                 "min":['A_pb','A_sb','F_pb','F_pb2','F_sb','F_sb2']},
          "BS": {"man":['A_pb','F_pb','F_pb2'],
                 "min":['A_pb','A_sb','F_pb','F_pb2','F_sb','F_sb2']},
          "LP": {"man":['N', 'A_pb', 'F_pb'],
                 "min":['A_pb','A_sb','F_pb','F_sb']},
          "HP": {"man":['N', 'A_pb', 'F_pb'],
                 "min":['A_pb','A_sb','F_pb','F_sb']}
                 }
        print(self.rt["LP"]["man"])

        self.info = "Chebychev Typ 1 Filter haben nur im Passband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im PB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung unter \
        den spezifizierten Wert fällt."

    def LP(self, specs):
#        self.needs = ('N', 'A_pb', 'F_pb')
        self.zpk = sig.cheby1(specs['N'], specs['A_pb'], specs['F_pb'],
                              btype='low', analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)

    def HP(self, specs):
#        self.needs = ('N', 'A_pb', 'F_pb')
        self.zpk = sig.cheby1(specs['N'], specs['A_pb'], specs['F_pb'], 
                              btype='highpass', analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
    # For BP and BS, A_pb, F_pb and F_stop have two elements each
    def BP(self, specs):
        self.needs = ('N', 'A_pb', 'F_pb', 'F_pb2')
        self.zpk = sig.cheby1(specs['N'], specs['A_pb'],
                        [specs['F_pb'], specs['F_pb2']], btype='bandpass',
                        analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
    def BS(self, specs):
#        self.needs = ('N', 'A_pb', 'F_pb', 'F_pb2')
        self.zpk = sig.cheby1(specs['N'], specs['A_pb'],
                [specs['F_pb'], specs['F_pb2']], btype='bandstop', 
                analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
class cheby1_min(object):
    def __init__(self):
        pass
#        self.zpk = [1, 0, 1]
#        self.coeffs = [1, 1]

    def has(self):
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'),
                    'man' : 'min'}

    # LP: F_pb < F_stop
    def LP(self, specs):
        self.needs = ('N', 'A_pb', 'F_pb', 'F_sb')
        self.zpk = sig.iirdesign(specs['F_pb'], specs['F_stop'], 
                                   specs['A_pb'], specs['A_stop'],
                             analog=False, ftype='cheby1', output='zpk')
        self.coeffs = zpk2ba(self.zpk)

        
    # HP: F_stop < F_pb                          
    def HP(self, specs):
        self.zpk = self.LP(self, specs)
        self.coeffs = zpk2ba(self.zpk)
        
    # BP: F_stop[0] < F_pb[0], F_stop[1] > F_pb[1]    
    def BP(self, specs):
        self.zpk = self.LP(self, specs)
        self.coeffs = zpk2ba(self.zpk)

    # BS: F_stop[0] > F_pb[0], F_stop[1] < F_pb[1]            
    def BS(self, specs):
        self.zpk = self.LP(self, specs)
        self.coeffs = zpk2ba(self.zpk)      