# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:13:41 2013

Design cheby1-Filters (LP, HP, BP, BS) with fixed or minimum order, return
the filter design in zeros, poles, gain (zpk) format

@author: Christian Muenker

Expected changes in scipy 0.16:
https://github.com/scipy/scipy/pull/3717
https://github.com/scipy/scipy/issues/2444
"""
from __future__ import print_function, division, unicode_literals
import scipy.signal as sig
#import numpy as np

#import filterbroker as fb

output = 'zpk' # set output format of filter design routines to 'zpk' or 'ba'

class cheby1(object):
    
    def __init__(self):
        self.name = {'cheby1':'Chebychev 1'}
        
        # common messages for all man. / min. filter order response types:            
        msg_man = ("Enter the filter order $N$, the maximum ripple $A_pb$ "
            "allowed below unity gain in the passband and the frequency or "
            "frequencies $F_pb$ where the gain first drops below $-A_pb$.")
        msg_min = ("Enter the desired pass band ripple and minimum stop "
            "band attenuation and the corresponding corner frequencies.")

        # enabled widgets for all man. / min. filter order response types:    
        enb_man = ['fo','fspec','aspec'] # enabled widget for man. filt. order
        enb_min = ['fo','fspec','aspec'] # enabled widget for min. filt. order
        
        # parameters for all man. / min. filter order response types:    
        par_man = ['N', 'f_S', 'F_pb', 'A_pb'] # enabled widget for man. filt. order
        par_min = ['f_S', 'A_pb', 'A_sb'] # enabled widget for min. filt. order

        # Common data for all man. / min. filter order response types:
        # This data is merged with the entries for individual response types 
        # (common data comes first):
        self.com = {"man":{"enb":enb_man, "msg":msg_man, "par":par_man},
                    "min":{"enb":enb_min, "msg":msg_min, "par":par_min}}

        self.ft = 'IIR'
        self.rt = {
          "LP": {"man":{"par":[]},
                 "min":{"par":['F_pb','F_sb']}},
          "HP": {"man":{"par":[]},
                 "min":{"par":['F_sb','F_pb']}},
          "BP": {"man":{"par":['F_pb2']},
                 "min":{"par":['F_sb','F_pb','F_pb2','F_sb2']}},
          "BS": {"man":{"par":['F_pb2']},
                 "min":{"par":['F_pb','F_sb','F_sb2','F_pb2']}}
                 }

        self.info = "Chebychev Typ 1 Filter haben nur im Passband Ripple. \
        Sie werden spezifiziert über die Ordnung, den zulässigen Ripple im PB \
        und über die kritische(n) Frequenz(en) bei denen die Verstärkung unter \
        den spezifizierten Wert fällt."

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
        Convert between poles / zeros / gain, filter coefficients (polynomes) 
        and second-order sections and store all available formats in the global
        database.
        """
        if output == 'zpk': # arg = [z,p,k]
            self.coeffs = sig.zpk2tf(arg[0], arg[1], arg[2])
            self.zpk = arg
        else: # arg = [b,a]
            self.zpk = sig.tf2zpk(arg[0], arg[1])
            self.coeffs = arg

        specs['coeffs'] = self.coeffs
        specs['zpk'] = self.zpk
        try: # has the order been calculated by a "min" filter design?
            specs['N'] = self.N # yes, update filterbroker
        except AttributeError:
            pass


    def LPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby1(self.N, self.A_pb, self.F_pb,
                            btype='low', analog = False, output = output))

    def HPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby1(self.N, self.A_pb, self.F_pb,
                            btype='highpass', analog = False, output = output))
        
    # For BP and BS, A_pb, F_pb and F_stop have two elements each
    def BPman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby1(self.N, self.A_pb,[self.F_pb,self.F_pb2],
                            btype='bandpass', analog = False, output = output))
        
    def BSman(self, specs):
        self.get_params(specs)
        self.save(specs, sig.cheby1(self.N, self.A_pb, [self.F_pb,self.F_pb2],
                            btype='bandstop', analog = False, output = output))

    # LP: F_pb < F_stop
    def LPmin(self, specs):
        self.get_params(specs)
        self.save(specs, sig.iirdesign(self.F_pb, self.F_sb, self.A_pb, self.A_sb,
                             analog=False, ftype='cheby1', output=output))
   
    # HP: F_stop < F_pb                          
    def HPmin(self, specs):
        self.get_params(specs)
        self.save(specs, sig.iirdesign(self.F_pb, self.F_sb, self.A_pb, self.A_sb,
                             analog=False, ftype='cheby1', output=output))
        
    # BP: F_stop[0] < F_pb[0], F_stop[1] > F_pb[1]    
    def BPmin(self, specs):
        self.get_params(specs)        
        self.save(specs, sig.iirdesign([self.F_pb,self.F_pb2], [self.F_sb,self.F_sb2],
            self.A_pb, self.A_sb, analog=False, ftype='cheby1', output=output))

    # BS: F_stop[0] > F_pb[0], F_stop[1] < F_pb[1]            
    def BSmin(self, specs):
        self.get_params(specs)
        self.save(specs, sig.iirdesign([self.F_pb,self.F_pb2], [self.F_sb,self.F_sb2],
            self.A_pb, self.A_sb, analog=False, ftype='cheby1', output=output))

