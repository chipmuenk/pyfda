# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:13:41 2013

@author: beike
"""
import scipy.signal as sig
import numpy as np
class iir_cheby1():
    
    def __init__(self, params):
        self.N = params(0)
        self.fs = params(1)
        self.A = params(2)
        self.W = params(3) * 2 * np.pi
        if params(0) == 'min':
            N, wn = sig.cheb1ord(self.W, self.A)
        
    
    def LP(self, params):

        b,a = sig.cheby1(self.N, self.rp, self.wn, btype ='low', analog = False, output = 'ba')
        
        return b, a