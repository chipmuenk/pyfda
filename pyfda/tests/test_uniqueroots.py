#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#===========================================================================
#  unittest for unique_roots in pyfda_lib
#
# For comparison, select scipy.signal.unique_roots in function FuT (function
#  under test)
# (c) 2015 Christian Muenker
#===========================================================================
from __future__ import (division, print_function, unicode_literals,
                        absolute_import)
if __name__ == "__main__":
    import sys, os
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.join('..',os.path.dirname(__cwd__)))
    
import numpy as np
from numpy import ones, exp, pi

import scipy.signal as sig
from pyfda.pyfda_lib import unique_roots


import unittest
#import random



rtype = 'avg'
rdist = 'euclid'
magsort = False
N_eps = 6


def FuT(roots_in, *kwargs):
    """Select Function-Under-Test (FuT)"""
    return unique_roots(roots_in, tol=1e-3, magsort = magsort, rtype = rtype, rdist = rdist)
#    return sig.unique_roots(roots_in, rtype = rtype)

def nan_equal(a,b):
    """
    yield nan == nan, see
    http://stackoverflow.com/questions/10710328/
    comparing-numpy-arrays-containing-nan
    """
    try:
#        np.testing.assert_allclose()
#        np.testing.assert_equal(a,b)
        print("a:",a,"b:",b)
        np.testing.assert_array_almost_equal(a,b)
#        np.testing.assert_array_equal(a,b)
    except AssertionError:
        return False
    return True

def toSoT(list_in):
    """
    Convert a 2D-list into a set of tuples
    to compare lists with differing sequences"    
    """
    set_out = set({})
#    print("list_in:", list_in)
#    print(np.shape(list_in))
    for i in range(np.shape(list_in)[1]):
        set_out.add((np.round(list_in[0][i],N_eps), list_in[1][i]))
        
    return set_out


class TestSequenceFunctions(unittest.TestCase):
        
#    def setUp(self):
#        self.seq = range(10)
#
#    def test_shuffle(self):
#        # make sure the shuffled sequence does not lose any elements
#        random.shuffle(self.seq)
#        self.seq.sort()
#        self.assertEqual(self.seq, range(10))
#
#    def test_choice(self):
#        element = random.choice(self.seq)
#        self.assertTrue(element in self.seq)
#
#    def test_sample(self):
#        self.assertRaises(ValueError, random.sample, self.seq, 20)
#        for element in random.sample(self.seq, 5):
#            self.assertTrue(element in self.seq)

    def test_empty(self): # ret-value to be discussed
        """ empty input"""
        roots_in = []
        roots_goal = [],[]
        roots_out = FuT(roots_in)
        self.assertEqual(roots_out,roots_goal)


    def test_single_root(self):
        """ real and complex scalar roots"""
        
        def root_cmp(a):
            roots_out = FuT(a)
            roots_goal = list(np.atleast_1d(a)), [1]
            self.assertEqual(roots_out,roots_goal) 

        root_cmp(2+3j)
        root_cmp([2+3j])
        root_cmp(2)
        root_cmp([2])
        root_cmp(0)
        root_cmp([0])
        root_cmp(1j)
        root_cmp([1j])
        
    def test_nan(self):
        """
        roots containing nan's and / or real / complex roots
        """
        
        def root_cmp_nan(roots_in,roots_goal):
#            roots_out = np.round(FuT(roots_in), N_eps)
            roots_out = FuT(roots_in)           
#            print('NAN:', type(roots_out), roots_out, '\n', type(roots_goal),roots_goal)
            self.assertEqual(nan_equal(roots_out, roots_goal), True)
#((a == b) | (numpy.isnan(a) & numpy.isnan(b))).all()
            
        root_cmp_nan([np.nan], 
                     ([np.nan],[1]))
        root_cmp_nan([np.nan, np.nan, 2.3],
                     ([np.nan, np.nan, 2.3],[1,1,1]))
        root_cmp_nan([np.nan, 2.3, 2.3],
                     ([np.nan, 2.3],[1,2]))                     
        root_cmp_nan([np.nan, np.nan],
                     ([np.nan, np.nan],[1,1]))
        root_cmp_nan([np.nan, np.nan, (-2 - 3.1j)], 
                      ([np.nan, np.nan, (-2 - 3.1j)],[1,1,1]))
        root_cmp_nan([np.nan, np.nan, (-2 - 3.1j), (-3.1j -2)], 
                      ([np.nan, np.nan, (-2 - 3.1j)],[1,1,2]))

    def test_unique_roots(self):
        """
        List of unique roots - attention: the order of the entries
        returned by unique_roots may be different from the input order,
        that's why input and output roots are converted to sets first
        """

        def root_cmp(my_list):
            roots_in  = my_list 
            roots_goal = np.array(my_list), ones(len(my_list), dtype = 'int')
            roots_out = FuT(roots_in)
            print(roots_out)
            self.assertEqual(toSoT(roots_out), toSoT(roots_goal))
            
#        def root_cmp(a):
#            roots_in  = array(a)
#            roots_out = FuT(roots_in)
#            try: 
#                len_a = len(a) # is a a list?
#                if roots_in.shape[1] == 1:
#                    roots_goal = roots_in, ones(len_a, dtype = int)
#                else: 
#                    roots_goal = roots_in
#                self.assertEqual(toSoT(roots_out),toSoT(roots_goal))      
#            except (TypeError, IndexError):
#                roots_goal = roots_in, [1]
#                self.assertEqual(roots_out,roots_goal) 
            
#        root_cmp([(2+3j), (1+ 1j), (5 + 1j)])
#        root_cmp([5,-1.2, 0])
        
        roots_in = [(2+3j), (1+ 1j), (5 + 1j)]
        roots_goal = roots_in, ones(len(roots_in))
        roots_out = FuT(roots_in)
        print(roots_out)
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))
            


        
    def test_multi_roots_UC(self):
        """ multiple roots along the unit circle (UC, mag. = 1)"""
 
        # 5 roots distributed along the UC
        roots_in = np.roots(np.convolve(ones(5), ones(5))) 
        roots_goal = np.round([
                    (-1 + 0j)**0.4, (-1 + 0j)**-0.4,
                     -(-1 + 0j)**0.2, -(-1 + 0j)**(-0.2)], N_eps), [2, 2, 2, 2]
        roots_out = np.round(FuT(roots_in), N_eps)
#        print(roots_out)
#        print(roots_goal)
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))

        # 5 roots at z = 1
        roots_in = ones(5)
        roots_goal = [1], [5]
        roots_out = FuT(roots_in)
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))

        # 5 roots at z = 1j
        roots_in = 1j * ones(5)
        roots_goal = [1j], [5]
        roots_out = FuT(roots_in)
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))
        
    def test_multi_roots_order(self):
        """ multiple complex roots in different order """
        a = 2+3j
        b = 1+1j
        
        roots_in  = [a,a,b] 
        roots_goal = ([a,b], [2,1])
        roots_out = FuT(roots_in)
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))

        roots_in  = [b,a,a] 
        roots_goal = [b,a], [1,2]
        roots_out = FuT(roots_in)
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))

    def test_close_real_roots(self):
        """
        N real valued roots at close distance r0 (1 + i*eps),
        """
        
        r0 = 1
        N = 5
        eps = 1e-4
        roots_in = []
        for i in range(N):
            roots_in.append(r0 + eps*((N-1)/2-i))
        roots_out = FuT(roots_in)
        roots_goal = ([r0], [N])
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))
        
        for i in range(N):
            roots_in.append(r0 + eps*((N-1)/2-i))
        roots_out = FuT(roots_in)
        roots_goal = ([r0], [2*N])
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))

    def test_close_complex_roots(self):
        """
        N roots at close distance r0 (1 + eps),
        distributed radially (complex valued) around r0
        """
        
        r0 = 1
        N = 5
        eps = 1e-4
        roots_in = []
        
        for i in range(N):
            roots_in.append(r0 + eps* exp(i * 2*pi* 1j/N))
        roots_out = FuT(roots_in)
        roots_goal = ([r0], [N])
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))   
        
        for i in range(N):
            roots_in.append(r0 + eps* exp(i * 2*pi* 1j/N))
        roots_out = FuT(roots_in)
        roots_goal = ([r0], [2*N])
        self.assertEqual(toSoT(roots_out),toSoT(roots_goal))         

#=====================================00

if __name__ == '__main__':
   unittest.main()
