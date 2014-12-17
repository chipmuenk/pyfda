# -*- coding: utf-8 -*-
"""
Created on Wed December 17 2014

Design cheby2-Filters (LP, HP, BP, BS) with fixed or minimum order, return
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

#   ['cheby2','LP',['Fs','F_pb'],[48000,9600],True,True,"unit",[["dB","Squared"],["A_pb","A_sb"],[1,80]], ""],
#   ['cheby2','HP',['Fs','F_pb'],[48000,14400],True,True,"unit",[["dB","Squared"],["A_pb","A_sb"],[1,80]], ""],
#   ['cheby2','BP',['Fs','F_pb','F_pb2'],[48000,9600,12000],True,True,"unit",[["dB","Squared"],["A_sb","A_pb","A_sb2"],[60,1,80]], ""],
#   ['cheby2','BS',['Fs','F_pb','F_pb2'],[48000,9600,12000],True,True,"unit",[["dB","Squared"],["A_pb1","A_sb","A_pb2"],[5,60,1]], ""]


# TODO: Funktioniert "Vererben" LP -> HP etc.?
# TODO: Für den 'Min'-Fall könnte man cheby1, elllip etc. verbinden mit der 
# iirdesign - Funktion verbinden. Ist das sinnvoll?

def zpk2ba(zpk):
    """ 
    Convert poles / zeros / gain to filter coefficients (polynomes)
    """
    coeffs = [zpk[2] * np.poly(zpk[0]), np.poly(zpk[1])]
    return coeffs

class cheby2(object):    
    
    def __init__(self):

        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'), 'ord' : 'N'}
        self.name = {'cheby2':'Chebychev 2'}
        self.ft = 'IIR'
        self.rt = {
          "BP": {"ord":['N', 'A_sb', 'F_sb', 'F_sb2'],
                 "min":['A_pb','A_sb','F_pb','F_pb2','F_sb','F_sb2']},
          "BS": {"ord":['A_sb','F_sb','F_sb2'],
                 "min":['A_pb','A_sb','F_pb','F_pb2','F_sb','F_sb2']},
          "LP": {"ord":['N', 'A_sb', 'F_sb'],
                 "min":['A_pb','A_sb','F_pb','F_sb']},
          "HP": {"ord":['N', 'A_sb', 'F_sb'],
                 "min":['A_pb','A_sb','F_pb','F_sb']}
                 }
        print(self.rt["LP"]["ord"])

        self.info = "Chebychev Typ 2 Filter haben nur im Stopband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im SB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung zuerst\
        den spezifizierten Wert A_sb erreicht."

    def LP(self, specs):
        self.needs = ('N', 'A_sb', 'F_sb')
        self.zpk = sig.cheby2(specs['N'], specs['A_sb'], specs['F_sb'],
                              btype='low', analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)

    def HP(self, specs):
        self.needs = ('N', 'A_sb', 'F_sb')
        self.zpk = sig.cheby2(specs['N'], specs['A_sb'], specs['F_sb'], 
                              btype='highpass', analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
    # For BP and BS, A_pb, F_pb and F_stop have two elements each
    def BP(self, specs):
        self.needs = ('N', 'A_sb', 'F_sb', 'F_sb2')
        self.zpk = sig.cheby2(specs['N'], specs['A_sb'],
                        [specs['F_sb'], specs['F_sb2']], btype='bandpass',
                        analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
    def BS(self, specs):
        self.needs = ('N', 'A_sb', 'F_sb', 'F_sb2')
        self.zpk = sig.cheby2(specs['N'], specs['A_sb'],
                [specs['F_sb'], specs['F_sb2']], btype='bandstop', 
                analog = False, output = 'zpk')
        self.coeffs = zpk2ba(self.zpk)
        
class cheby2_min(object):
    def __init__(self):
        self.zpk = [1, 0, 1]
        self.coeffs = [1, 1]

    def has(self):
        self.has = {'rt' : ('LP', 'HP', 'BP', 'BS'),
                    'ord' : 'min'}

    # LP: F_pb < F_stop
    def LP(self, specs):
        self.needs = ('N', 'A_pb', 'F_pb', 'F_sb')
        self.zpk = sig.iirdesign(specs['F_pb'], specs['F_sb'], 
                                   specs['A_pb'], specs['A_sb'],
                             analog=False, ftype='cheby2', output='zpk')
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