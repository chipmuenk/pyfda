# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 11:57:19 2017

@author: Christian Muenker
"""


import unittest
import numpy as np
from pyfda import pyfda_fix_lib as fix_lib
# TODO: Add test case for complex numbers

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 1}
        self.myQ = fix_lib.Fixed(q_obj) # instantiate fixpoint object with settings above

        self.y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.9, 0.99, 1.0, 1.1]
        self.y_list_cmplx = [-1.1j + 0.1, -1.0 - 0.3j, -0.5-0.5j, 0j, 0.5j, 0.9, 0.99+0.3j, 1j, 1.1]
        # list with various invalid strings
        self.y_list_validate = ['1.1.1', 'xxx', '123', '1.23', '', 1.23j + 3.21, '3.21 + 1.23 j']

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
    def test_write_q_obj(self):
        """
        Check whether parameters are written correctly to the fixpoint instance
        """
        q_obj = {'WI':7, 'WF':3, 'ovfl':'none', 'quant':'fix', 'frmt': 'hex', 'scale': 17}
        self.myQ.setQobj(q_obj)
        self.assertEqual(q_obj, self.myQ.q_obj)
        # check whether Q : 7.3 is resolved correctly as WI:7, WF: 3
        q_obj2 = {'Q': '7.3', 'ovfl':'none', 'quant':'fix', 'frmt': 'hex', 'scale': 17}
        self.myQ.setQobj(q_obj2)
        self.assertEqual(q_obj, self.myQ.q_obj)

    def test_fix_no_ovfl(self):
        """
        Test the actual fixpoint quantization without saturation / wrap-around. The 'frmt'
        keyword is not regarded here.
        """
        # return fixpoint numbers as float (no saturation, no quantization)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
        # test handling of invalid inputs - scalar inputs
        yq_list = list(map(self.myQ.fix, self.y_list_validate))
        yq_list_goal = [0, 0, 123.0, 1.23, 0, 3.21, 3.21]
        self.assertEqual(yq_list, yq_list_goal)
        # same in vector format
        yq_list = list(self.myQ.fix(self.y_list_validate))
        yq_list_goal = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.assertListEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as float (no saturation, no quantization)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = self.y_list
        self.assertEqual(yq_list, yq_list_goal)

        # test scaling (multiply by scaling factor)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'frmt': 'dec', 'scale': 2}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list) / 2.)
        self.assertEqual(yq_list, yq_list_goal)

        # test scaling (divide by scaling factor)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'frmt': 'dec', 'scale': 2}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list, scaling='div') * 2.)
        self.assertEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as float (rounding)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'round', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-1.125, -1.0, -0.5, 0, 0.5, 0.875, 1.0, 1.0, 1.125]
        self.assertEqual(yq_list, yq_list_goal)

        # wrap around behaviour with 'fix' quantization; fractional representation
        q_obj = {'WI':5, 'WF':2, 'ovfl':'wrap', 'quant':'fix', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-8.75, -8.0, -4.0, 0.0, 4.0, 7.0, 7.75, 8.0, 8.75]
        self.assertEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as integer (rounding)
        q_obj = {'WI':3, 'WF':0, 'ovfl':'none', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-9, -8, -4, 0, 4, 7, 8, 8, 9]
        self.assertEqual(yq_list, yq_list_goal)

        # input list of strings
        q_obj = {'WI':3, 'WF':0, 'ovfl':'none', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        y_string = ['-1.1', '-1.0', '-0.5', '0', '0.5', '0.9', '0.99', '1.0', '1.1']
        yq_list = list(self.myQ.fix(y_string))
        yq_list_goal = [-9, -8, -4, 0, 4, 7, 8, 8, 9]
        self.assertEqual(yq_list, yq_list_goal)

    def test_fix_no_ovfl_cmplx(self):
        """
        Test the actual fixpoint quantization without saturation / wrap-around. The 'frmt'
        keyword is not regarded here.
        """

        # return fixpoint numbers as float (no saturation, no quantization)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
        # test handling of complex inputs - scalar inputs
        yq_list = list(map(self.myQ.fix, self.y_list_cmplx))
        yq_list_goal = [0.1, -1.0, -0.5, 0.0, 0.0, 0.9, 0.99, 0.0, 1.1]
        self.assertEqual(yq_list, yq_list_goal)
        # same in array format
        yq_list = list(self.myQ.fix(self.y_list_cmplx))
        self.assertListEqual(yq_list, yq_list_goal)
#==============================================================================
#         # same in scalar string format        
#         y_list = np.array(self.y_list_cmplx).astype(np.string_)
#         yq_list = list(map(self.myQ.fix, y_list))
#         self.assertEqual(yq_list, yq_list_goal)
#         # same in vector string format        
#         y_list = np.array(self.y_list_cmplx).astype(np.string_)
#         yq_list = list(self.myQ.fix(y_list))
#         self.assertEqual(yq_list, yq_list_goal)
# 
#==============================================================================
    def test_fix_saturation(self):
        """
        Test saturation
        """
        y_list_ovfl = [-np.inf, -3.2, -2.2, -1.2, -1.0, -0.5, 0, 0.5, 0.8, 1.0, 1.2, 2.2, 3.2, np.inf]

        # Integer representation, saturation
        q_obj = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(y_list_ovfl))
        yq_list_goal = [-8.0, -8.0, -8.0, -8.0, -8.0, -4.0, 0.0, 4.0, 6.0, 7.0, 7.0, 7.0, 7.0, 7.0]
        self.assertEqual(yq_list, yq_list_goal)

        # Fractional representation, saturation
        q_obj = {'WI':3, 'WF':1, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(y_list_ovfl))
        yq_list_goal = [-8, -8, -8, -8, -8, -4, 0, 4, 6.5, 7.5, 7.5, 7.5, 7.5, 7.5]
        self.assertEqual(yq_list, yq_list_goal)

        # normalized fractional representation, saturation
        q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-1, -1, -0.5, 0, 0.5, 0.875, 0.875, 0.875, 0.875]
        self.assertEqual(yq_list, yq_list_goal)
        
        # saturation, one extra int bit
        q_obj = {'WI':1, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-1.125, -1.0, -0.5, 0.0, 0.5, 0.875, 1.0, 1.0, 1.125]
        self.assertEqual(yq_list, yq_list_goal)


    def test_fix_wrap(self):
        """
        Test wrap around
        """
        y_list_ovfl = [-np.inf, -3.2, -2.2, -1.2, -1.0, -0.5, 0, 0.5, 0.8, 1.0, 1.2, 2.2, 3.2, np.inf]

        # Integer representation, wrap
        q_obj = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = self.myQ.fix(y_list_ovfl)
        yq_list_goal = [np.nan, 6.0, -2.0, 6.0, -8.0, -4.0, 0.0, 4.0, 6.0, -8.0, -6.0, 2.0, -6.0, np.nan]
        np.testing.assert_array_equal(yq_list, yq_list_goal)

        # wrap around behaviour / floor quantization
        q_obj = {'WI':3, 'WF':1, 'ovfl':'wrap', 'quant':'floor', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [7.0, -8.0, -4, 0, 4, 7, 7.5, -8, -7.5]
        self.assertEqual(yq_list, yq_list_goal)


    def test_float2frmt_bin(self):
        """
        Conversion from float to binary format
        """
        # Integer case: Q3.0, scale = 1, scalar parameter
        q_obj = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'frmt': 'bin', 'scale': 8}
        self.myQ.setQobj(q_obj)
        # test handling of invalid inputs - scalar inputs
        yq_list = list(map(self.myQ.float2frmt, self.y_list_validate))
        yq_list_goal = ["0000", "0000", "0111", "0001", "0000", "0011", "0011"]
        self.assertEqual(yq_list, yq_list_goal)
        # same in vector format
        yq_list = list(self.myQ.float2frmt(self.y_list_validate))
        yq_list_goal = ["0000", "0000", "0111", "0001", "0000", "0011", "0011"]
        self.assertListEqual(yq_list, yq_list_goal)

        # Integer case: Q3.0, scale = 8, scalar parameter
        q_obj = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'frmt': 'bin', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['0111', '1000', '1100', '0000', '0100', '0111', '1000', '1000', '1001']
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized function
        yq_arr = list(self.myQ.float2frmt(self.y_list))
        self.assertEqual(yq_arr, yq_list_goal)

        # same but with Q1.2 format and scale = 2
        q_obj = {'WI':1, 'WF':2, 'ovfl':'sat', 'quant':'round', 'frmt': 'bin', 'scale': 2}
        self.myQ.setQobj(q_obj)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['10.00', '10.00', '11.00', '00.00', '01.00', '01.11', '01.11', '01.11', '01.11']
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized function
        yq_list = list(self.myQ.float2frmt(self.y_list))
        self.assertEqual(yq_list, yq_list_goal)

    def test_frmt2float_bin(self):
        """
        Test conversion from binary format to float
        """
        # wrap around behaviour with 'round' quantization
        y_list = ['100.000', '11.000', '10.000', '1,000', '1,001', '1.100', '1.111', '0.000', '0.100', '0.111', '01.000']
        q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'bin', 'scale': 1}
        self.myQ.setQobj(q_obj)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [-1, -1, -1, -1, -0.875, -0.5,-0.125,  0, 0.5, 0.875, 0.875]
        # TODO: Test fails for overflows -1 -> 0, -2 -> 0, -3 -> -1 (ok), -4 -> -1
        self.assertEqual(yq_list, yq_list_goal)

        # same for integer case
        y_list = ['11000', '1000', '1001', '1100', '1111', '0000', '0100', '0111', '01000']
        q_obj = {'WI':3, 'WF':0, 'ovfl':'none', 'quant':'round', 'frmt': 'bin', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [-1, -1, -0.875, -0.5,-0.125,  0, 0.5, 0.875, 0.875]
        self.assertEqual(yq_list, yq_list_goal)



if __name__=='__main__':
    unittest.main()

# run tests with python -m pyfda.tests.test_pyfda_fix_lib
