# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:13:41 2013

@author: Christian Muenker
"""
from __future__ import print_function, division
import scipy.signal as sig
import numpy as np

# a: ['HP', 'Equiripple', 10, ['Hz', ['Fs', 'Fpass', 'Fstop'], [48000, 9600, 12000]], [['Wpass', 'Wstop'], [1, 1]]]
# ['LP', 'Elliptic', 10, ['Hz', ['Fs', 'Fpass'], [48000, 14400]], ['DB', ['Apass', 'Astop'], [1, 80]]]
def iir_basic(a):
  
        filt_type = a["Response Type"]
        
        print('filt_type', filt_type)
        design_method = a["Design_Methode"]
        if design_method == 'Elliptic':
            ftype = 'ellip'
        elif design_method == 'Chebychev 1':
            ftype = 'cheby1'
        elif design_method == 'Chebychev 2':
            ftype = 'cheby2'
        elif design_method == 'Butterworth':
            ftype = 'butter'
#        else: raise_exception
            
        print('design_method', design_method)
        N = a['Order']
        print('order',N)
        fs = a["Fs"]
        F_pass = 2 * a["Fpass"]/fs
#        F_stop = 2 * a[3][2][2]/fs
        F_stop = 0.8
        print('fs','fpass','fstop',fs, F_pass, F_stop)
        A_pass = a["Apass"]
        A_stop = a["Astop"]
#        A_stop = a[4][2][2]
        print('A_pass', 'A_stop', A_pass, A_stop)
#        W = a[5]
#        print('W',W)
        
        if N == 'min':
            b,a = sig.iirdesign(F_pass, F_stop, A_pass, A_stop, analog = False, 
                                ftype = ftype, output = 'ba')            
        else:
            if ftype == 'ellip':
                b,a = sig.ellip(N, A_pass, A_stop, [F_pass, F_stop], btype ='low' )
            elif ftype == 'cheby1':
                b,a = sig.cheby1(N, A_pass, [F_pass, F_stop], btype ='low' )
            elif ftype == 'cheby2':
                b,a = sig.cheby2(N, A_stop, [F_pass, F_stop], btype ='low' )
            elif ftype == 'butter':
                b,a = sig.butter(N, (2 * a["Fc"]/fs), btype ='low' )
        return b, a
