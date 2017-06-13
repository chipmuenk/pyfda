#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#===========================================================================
# Speed comparison for unique_roots from scipy.signal against
# new implementation 
#
# (c) 2015 Christian Muenker
#===========================================================================
from __future__ import division, print_function, unicode_literals # v3line15

import numpy as np
import numpy.random as rnd

import scipy.signal as sig

import time
if __name__ == "__main__":
    import sys, os
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join('..',os.path.dirname(__cwd__)))

import pyfda.pyfda_lib as dsp
#import my_dsp_lib_v6a as dsp

## scalar inputs - IndexError with scipy implementation
#vals = 1 # real root
#vals = 1j # imag. root
#vals = 1j + 1  # complex root

## multiple & single real roots 
#vals = np.convolve(ones(13),ones(13)) # 12 double, one single real root
#vals = np.convolve(ones(1000),ones(1000))
#vals = [1,2,-1] # different unique real roots

## multiple & single imag. roots on the unit circle
vals =[1j, 1j]
vals = rnd.randn(1000)
vals = rnd.randn(100) + 1j * rnd.randn(100)
#vals = ones(5) * 1j # root at j with multiplicity 5
#vals = np.append(vals, ones(5))
#vals = ones(5)
#np.sort_complex()
#vals = np.roots(np.convolve(ones(5),ones(5))) # 4 double complex roots
#vals = np.roots(np.convolve(ones(500),ones(100))) # 100 double and 400 single complex roots,
#vals = np.roots(np.convolve(ones(500),ones(500))) # 500 double complex roots

#vals = np.roots(np.convolve(ones(5),ones(7))) # 4 double complex roots

## tests with nans 
#vals = list(ones(5) * 1j); vals.append(np.nan); vals.append(np.nan)
#vals = []
#print(vals)

Navg = 1000
rtype = 'min'
print('============ dsp.unique_roots() ================================')
t1 = time.clock()
for i in range(Navg):
    roots, mult = dsp.unique_roots(vals, rtype = rtype, rdist='manhattan')
t2 = time.clock()
T_dsp = (t2 - t1)/Navg
print (mult)

print('============ signal.unique_roots() =============================')
t1 = time.clock()
for i in range(Navg):
    roots, mult = sig.unique_roots(vals, rtype = rtype)
t2 = time.clock()
T_sig = (t2 - t1)/Navg
print (mult)

print("T_dsp = ",T_dsp, " s")
print("T_sig = ",T_sig, " s")
print("T_dsp / T_sig = ", T_dsp / T_sig)
