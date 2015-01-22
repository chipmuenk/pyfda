# -*- coding: utf-8 -*-
"""
Created on Wed December 17 2014

Design cheby2-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

@author: Christian Muenker

Expected changes in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division
from scipy.signal import iirdesign, cheb2ord, cheby2, zpk2tf, tf2zpk
#import numpy as np

output = 'ba' # set output format of filter design routines to 'zpk' or 'ba'

class cheby2(object):    
    
    def __init__(self):

        self.name = {'cheby2':'Chebychev 2'}

        # common messages for all man. / min. filter order response types:    
        msg_man = ("Enter the filter order $N$, the minimum stop band "
            "attenuation $A_sb$, and the frequency / frequencies $F_pb$ where "
            "gain first drops below $A_sb$.")
        msg_min = ("Enter the maximum pass band ripple and minimum stop band "
                    "attenuation and the corresponding corner frequencies.")

        # enabled widgets for all man. / min. filter order response types:    
        enb_man = ['fo','fspec','aspec'] # enabled widget for man. filt. order
        enb_min = ['fo','fspec','aspec'] # enabled widget for min. filt. order
        
        # common parameters for all man. / min. filter order response types:    
        par_man = ['N', 'f_S', 'F_sb', 'A_sb'] # enabled widget for man. filt. order
        par_min = ['f_S', 'A_pb', 'A_sb'] # enabled widget for min. filt. order

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types 
        # (common data comes first):
        self.com = {"man":{"enb":enb_man, "msg":msg_man, "par": par_man},
                    "min":{"enb":enb_min, "msg":msg_min, "par": par_min}}

        self.ft = 'IIR'
        self.rt = {
          "LP": {"man":{"par":[]},
                 "min":{"par":['F_pb','F_sb']}},
          "HP": {"man":{"par":[]},
                 "min":{"par":['F_sb','F_pb']}},
          "BP": {"man":{"par":['F_sb2']},
                 "min":{"par":['F_sb','F_pb','F_pb2','F_sb2']}},
          "BS": {"man":{"par":['F_sb2']},
                 "min":{"par":['F_pb','F_sb','F_sb2','F_pb2']}}
                 }

        self.info = "Chebychev Typ 2 Filter haben nur im Stopband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im SB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung zuerst\
        den spezifizierten Wert A_sb erreicht."
        
    def get_params(self,specs):
        """
        Translate parameters from the passed dictionary to instance
        parameters, scaling / transforming them if needed.
        """
        f_S = specs['f_S'] 
        self.N     = specs['N']
        self.F_pb  = specs['F_pb']/f_S * 2
        self.F_sb  = specs['F_sb']/f_S * 2
        self.F_pb2 = specs['F_pb2']/f_S * 2
        self.F_sb2 = specs['F_sb2']/f_S * 2 
        self.A_pb  = specs['A_pb']
        self.A_sb  = specs['A_sb']
        self.A_pb2 = specs['A_pb2']
        self.A_sb2 = specs['A_sb2']

    def save(self, specs, arg):
        """ 
        Convert poles / zeros / gain to filter coefficients (polynomes) and the
        other way round
        """
        if output == 'zpk': # arg = [z,p,k]
            self.coeffs = zpk2tf(arg[0], arg[1], arg[2])
            self.zpk = arg

        else: # arg = [b,a]
            self.zpk = tf2zpk(arg[0], arg[1])
            self.coeffs = arg
            
        specs['coeffs'] = self.coeffs
        specs['zpk'] = self.zpk
        try: # has the order been calculated by a "min" filter design?
            specs['N'] = self.N # yes, update filterbroker
        except AttributeError:
            pass

    def LPman(self, specs):
        self.get_params(specs)
        self.save(specs, cheby2(self.N, self.A_sb, self.F_sb,
                              btype='low', analog = False, output = output))
    # LP: F_pb < F_sb
    def LPmin(self, specs):
        self.get_params(specs)
        self.N, self.F_sbc = cheb2ord(self.F_pb, self.F_sb, self.A_pb, self.A_sb)
        self.save(specs, iirdesign(self.F_pb, self.F_sb, self.A_pb, self.A_sb,
                             analog=False, ftype='cheby2', output=output))
        print(self.N, self.F_sbc)

    def HPman(self, specs):
        self.get_params(specs)
        self.save(specs, cheby2(self.N, self.A_sb, self.F_sb, 
                             btype='highpass', analog = False, output = output))
        
    # HP: F_sb < F_pb                          
    def HPmin(self, specs):
        self.get_params(specs)
        self.N, self.F_sbc = cheb2ord(self.F_pb, self.F_sb, self.A_pb, self.A_sb)
        self.save(specs, iirdesign(self.F_pb, self.F_sb, self.A_pb, self.A_sb,
                             analog=False, ftype='cheby2', output=output))

    # For BP and BS, A_pb, A_sb, F_pb and F_sb have two elements each
    def BPman(self, specs):
        self.get_params(specs)
        self.save(specs, cheby2(self.N, self.A_sb, [self.F_sb, self.F_sb2], 
                            btype='bandpass', analog = False, output = output))
        
    # BP: F_sb[0] < F_pb[0], F_sb[1] > F_pb[1]    
    def BPmin(self, specs):
        self.get_params(specs)
        self.save(specs, iirdesign([self.F_pb,self.F_pb2], 
                [self.F_sb, self.F_sb2], self.A_pb, self.A_sb,
                             analog=False, ftype='cheby2', output=output))

    def BSman(self, specs):
        self.get_params(specs)
        self.save(specs, cheby2(self.N, self.A_sb,[self.F_sb, self.F_sb2],
                        btype='bandstop', analog = False, output = output))

    # BS: F_sb[0] > F_pb[0], F_sb[1] < F_pb[1]            
    def BSmin(self, specs):
        self.get_params(specs)
        self.save(specs, iirdesign([self.F_pb,self.F_pb2], 
                [self.F_sb, self.F_sb2], self.A_pb, self.A_sb,
                            analog=False, ftype='cheby2', output=output)) 