# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Test suite for the pyfda_fix_lib classes and methods
"""

import unittest
import numpy as np
from pyfda.libs import pyfda_fix_lib as fix_lib
from pyfda.libs.pyfda_fix_lib import bin2hex, dec2csd, csd2dec
# TODO: Add test case for complex numbers
# TODO: test csd2dec, csd2dec_vec

class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        q_dict = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'fx_base': 'dec', 'scale': 1}
        self.myQ = fix_lib.Fixed(q_dict) # instantiate fixpoint object with settings above

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
    def test_write_q_dict(self):
        """
        Check whether parameters are written correctly to the fixpoint instance
        """
        q_dict = {'WI':7, 'WF':3, 'ovfl':'none', 'quant':'fix', 'fx_base': 'hex', 'scale': 17}
        self.myQ.set_qdict(q_dict)
        # self.assertEqual(q_dict, self.myQ.q_obj)
        # check whether Q : 7.3 is resolved correctly as WI:7, WF: 3
        q_dict2 = {'Q': '6.2'}
        self.myQ.set_qdict(q_dict2)
        # self.assertEqual(q_dict2, self.myQ.q_obj)

        self.myQ.set_qdict({'W': 13})
        self.assertEqual(12, self.myQ.WI)
        self.assertEqual(0, self.myQ.WF)
        self.assertEqual('12.0', self.myQ.Q)


        # check whether option 'norm' sets the correct scale
        self.myQ.set_qdict({'scale':'norm'})
        self.assertEqual(2**(-self.myQ.WI), self.myQ.scale)
        # check whether option 'int' sets the correct scale
        self.myQ.set_qdict({'scale':'int'})
        self.assertEqual(1<<self.myQ.WF, self.myQ.scale)

    def test_fix_no_ovfl(self):
        """
        Test the actual fixpoint quantization without saturation / wrap-around. The 'fx_base'
        keyword is not regarded here.
        """
        # return fixpoint numbers as float (no saturation, no quantization)
        q_dict = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'fx_base': 'dec', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        # test handling of invalid inputs - scalar inputs
        yq_list = list(map(self.myQ.fixp, self.y_list_validate))
        yq_list_goal = [0, 0, 123.0, 1.23, 0, 3.21, 3.21]
        self.assertEqual(yq_list, yq_list_goal)
        # same in vector format
        yq_list = list(self.myQ.fixp(self.y_list_validate))
        yq_list_goal = [0, 0, 123.0, 1.23, 0, 3.21, 3.21]
        self.assertListEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as float (no saturation, no quantization)
        # use global list
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = self.y_list
        self.assertEqual(yq_list, yq_list_goal)

        # test scaling (multiply by scaling factor)
        q_dict = {'scale': 2}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(self.y_list) / 2.)
        self.assertEqual(yq_list, yq_list_goal)

        # test scaling (divide by scaling factor)
        yq_list = list(self.myQ.fixp(self.y_list, scaling='div') * 2.)
        self.assertEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as float (rounding)
        q_dict = {'quant':'round', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-1.125, -1.0, -0.5, 0, 0.5, 0.875, 1.0, 1.0, 1.125]
        self.assertEqual(yq_list, yq_list_goal)

        # wrap around behaviour with 'fix' quantization; fractional representation
        q_dict = {'WI':5, 'WF':2, 'ovfl':'wrap', 'quant':'fix', 'fx_base': 'dec', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-8.75, -8.0, -4.0, 0.0, 4.0, 7.0, 7.75, 8.0, 8.75]
        self.assertEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as integer (rounding), overflow 'none'
        q_dict = {'WI':3, 'WF':0, 'ovfl':'none', 'quant':'round', 'fx_base': 'dec', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-9, -8, -4, 0, 4, 7, 8, 8, 9]
        self.assertEqual(yq_list, yq_list_goal)

        # input list of strings
        y_string = ['-1.1', '-1.0', '-0.5', '0', '0.5', '0.9', '0.99', '1.0', '1.1']
        yq_list = list(self.myQ.fixp(y_string))
        yq_list_goal = [-9, -8, -4, 0, 4, 7, 8, 8, 9]
        self.assertEqual(yq_list, yq_list_goal)

        # frmt float
        q_dict = {'fx_base': 'float'}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(y_string))
        self.assertEqual(yq_list, yq_list_goal)

    def test_fix_no_ovfl_cmplx(self):
        """
        Test the actual fixpoint quantization without saturation / wrap-around. The 'fx_base'
        keyword is not regarded here.
        """
        # return fixpoint numbers as float (no saturation, no quantization)
        q_dict = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'fx_base': 'dec', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        # test handling of complex inputs - scalar inputs
        yq_list = list(map(self.myQ.fixp, self.y_list_cmplx))
        yq_list_goal = [0.1, -1.0, -0.5, 0.0, 0.0, 0.9, 0.99, 0.0, 1.1]
        self.assertEqual(yq_list, yq_list_goal)
        # same in array format
        yq_list = list(self.myQ.fixp(self.y_list_cmplx))
        self.assertListEqual(yq_list, yq_list_goal)
#==============================================================================
#         # same in scalar string format
#         y_list = np.array(self.y_list_cmplx).astype(np.string_)
#         yq_list = list(map(self.myQ.fixp, y_list))
#         self.assertEqual(yq_list, yq_list_goal)
#         # same in vector string format
#         y_list = np.array(self.y_list_cmplx).astype(np.string_)
#         yq_list = list(self.myQ.fixp(y_list))
#         self.assertEqual(yq_list, yq_list_goal)
#
#==============================================================================
    def test_fix_saturation(self):
        """
        Test saturation
        """
        y_list_ovfl = [-np.inf, -3.2, -2.2, -1.2, -1.0, -0.5, 0, 0.5, 0.8, 1.0, 1.2, 2.2, 3.2, np.inf]

        # Integer representation, saturation
        q_dict = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'dec', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(y_list_ovfl))
        yq_list_goal = [-8.0, -8.0, -8.0, -8.0, -8.0, -4.0, 0.0, 4.0, 6.0, 7.0, 7.0, 7.0, 7.0, 7.0]
        self.assertEqual(yq_list, yq_list_goal)

        # Fractional representation, saturation
        q_dict = {'WI':3, 'WF':1, 'ovfl':'sat', 'quant':'round', 'fx_base': 'dec', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(y_list_ovfl))
        yq_list_goal = [-8, -8, -8, -8, -8, -4, 0, 4, 6.5, 7.5, 7.5, 7.5, 7.5, 7.5]
        self.assertEqual(yq_list, yq_list_goal)

        # normalized fractional representation, saturation
        q_dict = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'fx_base': 'dec', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-1, -1, -0.5, 0, 0.5, 0.875, 0.875, 0.875, 0.875]
        self.assertEqual(yq_list, yq_list_goal)

        # saturation, one extra int bit
        q_dict = {'WI':1, 'WF':3, 'ovfl':'sat', 'quant':'round', 'fx_base': 'dec', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-1.125, -1.0, -0.5, 0.0, 0.5, 0.875, 1.0, 1.0, 1.125]
        self.assertEqual(yq_list, yq_list_goal)


    def test_fix_wrap(self):
        """
        Test wrap around
        """
        y_list_ovfl = [-3.2, -2.2, -1.2, -1.0, -0.5, 0, 0.5, 0.8, 1.0, 1.2, 2.2, 3.2]

        # Integer representation, wrap
        q_dict = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'fx_base': 'dec', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = self.myQ.fixp(y_list_ovfl)
        yq_list_goal = [ 6.0, -2.0, 6.0, -8.0, -4.0, 0.0, 4.0, 6.0, -8.0, -6.0, 2.0, -6.0]
        np.testing.assert_array_equal(yq_list, yq_list_goal)

        # wrap around behaviour / floor quantization
        q_dict = {'WI':3, 'WF':1, 'ovfl':'wrap', 'quant':'floor', 'fx_base': 'dec', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [7.0, -8.0, -4, 0, 4, 7, 7.5, -8, -7.5]
        self.assertEqual(yq_list, yq_list_goal)


    def test_float2frmt_bin(self):
        """
        Conversion from float to binary format
        """
        # Integer case: Q3.0, scale = 1, scalar parameter
        q_dict = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'bin', 'scale': 8}
        self.myQ.set_qdict(q_dict)

        # test handling of invalid inputs - scalar inputs
        yq_list = list(map(self.myQ.float2frmt, self.y_list_validate))
        yq_list_goal = ["0000", "0000", "0111", "0111", "0000", "0111", "0111"]
        self.assertEqual(yq_list, yq_list_goal)
        # same in vector format
        yq_list = list(self.myQ.float2frmt(self.y_list_validate))
        # input       ['1.1.1', 'xxx', '123', '1.23',    '', 1.23j + 3.21, '3.21 + 1.23 j']
        self.assertListEqual(yq_list, yq_list_goal)

        # Integer case: Q3.0, scale = 8, wrap, scalar inputs
        q_dict = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'fx_base': 'bin', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['0111', '1000', '1100', '0000', '0100', '0111', '1000', '1000', '1001']
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized function
        yq_arr = list(self.myQ.float2frmt(self.y_list))
        self.assertEqual(yq_arr, yq_list_goal)

        # Q1.2 format and scale = 2, saturation, scalar inputs
        q_dict = {'WI':1, 'WF':2, 'ovfl':'sat', 'quant':'round', 'fx_base': 'bin', 'scale': 2}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['10.00', '10.00', '11.00', '00.00', '01.00', '01.11', '01.11', '01.11', '01.11']
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized function
        yq_list = list(self.myQ.float2frmt(self.y_list))
        self.assertEqual(yq_list, yq_list_goal)

    def test_float2frmt_hex(self):
        """
        Conversion from float to hex format
        """
        # Integer case: Q3.0, scale = 1, scalar parameter
        q_dict = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'hex', 'scale': 1}
        self.myQ.set_qdict(q_dict)

        # test handling of invalid inputs - scalar inputs
        yq_list = list(map(self.myQ.float2frmt, self.y_list_validate))
        yq_list_goal = ["0", "0", "7", "1", "0", "3", "3"]
        # input       ['1.1.1', 'xxx', '123', '1.23', '', 1.23j + 3.21, '3.21 + 1.23 j']
        self.assertEqual(yq_list, yq_list_goal)
        # same in vector format
        yq_list = list(self.myQ.float2frmt(self.y_list_validate))
        self.assertListEqual(yq_list, yq_list_goal)

        # Integer case: Q6.0, scale = 1, scalar parameter, test bin2hex (Q-params are not used)
        q_dict = {'WI':6, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'hex', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        y_list = [-64, -63, -31, -1, 0, 1, 31, 32, 63]
        yb_list = map(lambda x: np.binary_repr(x, width=7), y_list) # converted to binary
        yq_list_goal = ['40', '41', '61', '7F', '00', '01', '1F', '20', '3F']
        yq_list_b2h = list(map(lambda x: bin2hex(x, WI = 6), yb_list))
        self.assertEqual(yq_list_b2h, yq_list_goal)
        # same with float2frmt (scalar)
        yq_list = list(map(self.myQ.float2frmt, y_list))
        self.assertEqual(yq_list, yq_list_goal)
        # same, vectorized
        yq_list = list(self.myQ.float2frmt(y_list))
        self.assertEqual(yq_list, yq_list_goal)

        # Fractional case: Q0.6,
        self.myQ.set_qdict({'Q':'0.6', 'scale':1./64})
        yq_list = list(map(self.myQ.float2frmt, y_list))
        yq_list_goal = ['1.00', '1.04', '1.84', '1.FC', '0.00', '0.04', '0.7C', '0.80', '0.FC']
        self.assertEqual(yq_list, yq_list_goal)

        # Integer case: Q3.0, scale = 8, scalar parameter, test float2frmt
        q_dict = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'fx_base': 'hex', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['7', '8',   'C', '0', '4', '7', '8', '8', '9']
        #self.y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.9, 0.99, 1.0, 1.1]
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized function
        yq_arr = list(self.myQ.float2frmt(self.y_list))
        self.assertEqual(yq_arr, yq_list_goal)

    def test_float2frmt_csd(self):
        """
        Conversion from float and dec to CSD format
        """
        # Integer case: Q3.0, scale = 1, scalar parameter
        q_dict = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'csd', 'scale': 1}
        self.myQ.set_qdict(q_dict)

        # test handling of invalid inputs - scalar inputs
        yq_list = list(map(self.myQ.float2frmt, self.y_list_validate))
        yq_list_goal = ["0", "0", "+00-", "+", "0", "+0-", "+0-"]
        # input:  ['1.1.1', 'xxx', '123', '1.23', '', 1.23j + 3.21, '3.21 + 1.23 j']
        self.assertEqual(yq_list, yq_list_goal)
        # same in vector format
        yq_list = list(self.myQ.float2frmt(self.y_list_validate))
        self.assertListEqual(yq_list, yq_list_goal)

        # Integer case: Q6.0, scale = 1, scalar parameter, test bin2hex (Q-params are not used)
        q_dict = {'WI':6, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'csd', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        y_list = [-64, -63, -31, -1, 0, 1, 31, 32, 63]
        yq_list_goal = ['-000000', '-00000+', '-0000+', '-', '0', '+', '+0000-', '+00000', '+00000-']
        yq_list_d2c = list(map(lambda x: dec2csd(x, WF = 0), y_list))
        self.assertEqual(yq_list_d2c, yq_list_goal)
        # same with float2frmt (scalar)
        yq_list = list(map(self.myQ.float2frmt, y_list))
        self.assertEqual(yq_list, yq_list_goal)
        # same, vectorized
        yq_list = list(self.myQ.float2frmt(y_list))
        self.assertEqual(yq_list, yq_list_goal)

        # Fractional case: Q0.6, scalar, test float2frmt
        self.myQ.set_qdict({'Q':'0.6', 'scale':1./64})
        yq_list = list(map(self.myQ.float2frmt, y_list))
        yq_list_goal = ['-.000000',  '-.00000+', '-.0+0+0+', '0.00000-', '0', '0.00000+', '+.0-0-0-', '+.0-0-0-', '+.00000-']
# TODO: 3rd argument should be: '-.0000+', 7th argument should be '+.0000-', 8th argument should be '+.00000'
        self.assertEqual(yq_list, yq_list_goal)

        # Integer case: Q3.0, scale = 8, scalar parameter, test float2frmt
        q_dict = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'fx_base': 'csd', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['+00-', '-000', '-00', '0', '+00', '+00-', '-000', '-000', '-00+']
        #['7', '8',   'C', '0', '4', '7', '8', '8', '9']
        #self.y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.9, 0.99, 1.0, 1.1]
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized function
        yq_arr = list(self.myQ.float2frmt(self.y_list))
        self.assertEqual(yq_arr, yq_list_goal)

#================== FRMT -> FLOAT ===============================================

    def test_frmt2float_float(self):
        """
        Test conversion from float format to float
        """
        # return floats as float, no quantization options are regarded here
        q_dict = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'fx_base': 'float', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        # scalar format
        yq_list = list(map(self.myQ.frmt2float, self.y_list))
        yq_list_goal = self.y_list
        self.assertEqual(yq_list, yq_list_goal)
        # vector format
        yq_list = list(self.myQ.frmt2float(self.y_list))
        self.assertEqual(yq_list, yq_list_goal)

        # input list of strings, otherwise same - scalar
        y_string = ['-1.1', '-1.0', '-0.5', '0', '0.5', '0.9', '0.99', '1.0', '1.1']
        yq_list = list(map(self.myQ.frmt2float, y_string))
        self.assertEqual(yq_list, yq_list_goal)
        # vector doesn't work yet
        yq_list = list(self.myQ.frmt2float(y_string))
        self.assertEqual(yq_list, yq_list_goal)


    def test_frmt2float_bin(self):
        """
        Test conversion from binary format to float
        """
        # saturation behaviour with 'round' quantization
        y_list = ['100.000', '11.000', '10.000', '01,000', '1,001', '1.100', '1.111', '0.000', '0.100', '0.111', '01.000', '010.0', '010.010']
        q_dict = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'fx_base': 'bin', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [0, -1, 0, -1, -0.875, -0.5,-0.125,  0, 0.5, 0.875, -1, 0, 0.25]
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized
        #yq_list = self.myQ.frmt2float(y_list)
        #self.assertEqual(yq_list, yq_list_goal)

        # same for integer case
        y_list = ['11000', '1000', '-0111', '1001', '1100', '1111', '0000', '0100', '0111', '01000']
        q_dict = {'WI':3, 'WF':0, 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [-1, -1, -0.875, -0.875, -0.5, -0.125,  0, 0.5, 0.875, -1]
        self.assertEqual(yq_list, yq_list_goal)

        # same for integer case without scaling
        q_dict = {'scale': 1}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [-8, -8, -7, -7, -4, -1,  0, 4, 7, -8]
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized
        #yq_list = list(self.myQ.frmt2float(y_list))
        #self.assertEqual(yq_list, yq_list_goal)

    def test_frmt2float_hex(self):
        """
        Test conversion from hex format to float
        """
        # saturation behaviour with 'round' quantization for integer case
        y_list = ['100', '-F', '10', '3F', '1E', '1F', '0', '00', '', '-1F', '1', '2', 'A', 'A.0', 'F', '020.01']
        q_dict = {'WI':4, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'hex', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [0, -15, -16, -1, -2, -1, 0, 0, 0, 1, 1, 2, 10, 10, 15, 0]
        self.assertEqual(yq_list, yq_list_goal)

        # same for Q5.0 quantization
        y_list = ['0100', '100', 'F0', '3F', '1F', '1E', '0', '', '1', '2', 'A', '2A', '3A.0', '070.01']
        q_dict = {'WI':5, 'WF':0}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [0, 0, -16, -1, 31, 30, 0, 0, 1, 2, 10, -22, -6, -16]
        self.assertEqual(yq_list, yq_list_goal)

        # same with Q0.3
        y_list = ['100.000', '1,000', '1,1', '1.5', '1.E', '1.F', '0.000', '0.100', '0.7', '0.8','3.0', '2.0', '07.00', '070.01']
        q_dict = {'WI':0, 'WF':3}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [0, -1, -1, -0.75, -0.125, 0.0, 0.0, 0, 0.5, 0.5, -1, 0, -1, 0]
        self.assertEqual(yq_list, yq_list_goal)

        # same but vectorized
        # yq_list = self.myQ.frmt2float(y_list)
        # self.assertEqual(yq_list, yq_list_goal)

        # same for integer case
        y_list = ['100000', '1,000', '1,1', '1.5', '1.E', '1.F', '0.000', '1', '2', '8','', '2.0', '07.00', '070.01']
        q_dict = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'hex', 'scale': 8}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [0, 0.125, 0.125, 0.125, 0.25, 0.25, 0.0, 0.125, 0.25, -1, 0, 0.25, 0.875, 0]
        self.assertEqual(yq_list, yq_list_goal)

    def test_frmt2float_csd(self):
        """
        Test conversion from csd format to float and dec
        """
        # saturation behaviour with 'round' quantization for integer case
        y_list = ['-00000+', '-0000', '-0.0-', '-', '0', '00', '', '.+', '+', '+0', '+0+0', '+0+0.0-', '+000-','+0000', '020.01']

        q_dict = {'WI':4, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'csd', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [-16, -16, -2, -1, 0, 0, 0, 0, 1, 2, 10, 10, 15, 15, 0]
        self.assertEqual(yq_list, yq_list_goal)

        # same with scale=2
        q_dict = {'WI':4, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'csd', 'scale': 2}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [-8, -8, -1, -0.5, 0, 0, 0, 0, 0.5, 1, 5, 5, 7.5, 7.5, 0]
        self.assertEqual(yq_list, yq_list_goal)

        # same with Q5.2 quantization
        q_dict = {'WI':5, 'WF':2, 'ovfl':'sat', 'quant':'round', 'fx_base': 'csd', 'scale': 1}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [-32, -16, -2.25, -1, 0, 0, 0, 0.5, 1, 2, 10, 9.75, 15, 16, 0]
        self.assertEqual(yq_list, yq_list_goal)

        # same with Q5.2 quantization
        q_dict = {'WI':5, 'WF':2, 'ovfl':'sat', 'quant':'round', 'fx_base': 'csd', 'scale': 0.25}
        self.myQ.set_qdict(q_dict)
        yq_list = list(map(self.myQ.frmt2float, y_list))
        yq_list_goal = [-128, -64, -9, -4, 0, 0, 0, 2, 4, 8, 40, 39, 60, 64, 0]
        self.assertEqual(yq_list, yq_list_goal)

        # same but vectorized
        # yq_list = self.myQ.frmt2float(y_list)
        # self.assertEqual(yq_list, yq_list_goal)


# TODO: test csd2dec, csd2dec_vec

#==============================================================================
#         # same for Q5.0 quantization
#         y_list = ['0100', '100', 'F0', '3F', '1F', '1E', '0', '', '1', '2', 'A', '2A', '3A.0', '070.01']
#         q_dict = {'WI':5, 'WF':0}
#         self.myQ.set_qdict(q_dict)
#         yq_list = list(map(self.myQ.frmt2float, y_list))
#         yq_list_goal = [0, 0, -16, -1, 31, 30, 0, 0, 1, 2, 10, -22, -6, -16]
#         self.assertEqual(yq_list, yq_list_goal)
#
#         # same with Q0.3
#         y_list = ['100.000', '1,000', '1,1', '1.5', '1.E', '1.F', '0.000', '0.100', '0.7', '0.8','3.0', '2.0', '07.00', '070.01']
#         q_dict = {'WI':0, 'WF':3}
#         self.myQ.set_qdict(q_dict)
#         yq_list = list(map(self.myQ.frmt2float, y_list))
#         yq_list_goal = [0, -1, -1, -0.75, -0.125, 0.0, 0.0, 0, 0.5, 0.5, -1, 0, -1, 0]
#         self.assertEqual(yq_list, yq_list_goal)
#
#         # same but vectorized
#         #yq_list = self.myQ.frmt2float(y_list)
#         #self.assertEqual(yq_list, yq_list_goal)
#
#         # same for integer case
#         y_list = ['100000', '1,000', '1,1', '1.5', '1.E', '1.F', '0.000', '1', '2', '8','', '2.0', '07.00', '070.01']
#         q_dict = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'fx_base': 'hex', 'scale': 8}
#         self.myQ.set_qdict(q_dict)
#         yq_list = list(map(self.myQ.frmt2float, y_list))
#         yq_list_goal = [0, 0.125, 0.125, 0.125, 0.25, 0.25, 0.0, 0.125, 0.25, -1, 0, 0.25, 0.875, 0]
#         self.assertEqual(yq_list, yq_list_goal)
#
#==============================================================================


if __name__=='__main__':
    unittest.main()

# run tests with python -m pyfda.tests.test_pyfda_fix_lib
