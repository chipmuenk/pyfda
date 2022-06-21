# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Test suite for fir_df
"""

import unittest
import numpy as np
from pyfda.libs import pyfda_fix_lib as fx
from pyfda.fixpoint_widgets.fir_df import FIR_DF_wdg


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        q_dict = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'fx_base': 'dec', 'scale': 1}
        self.myQ = fx.Fixed(q_dict) # instantiate fixpoint object with settings above

        self.y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.9, 0.99, 1.0, 1.1]
        self.y_list_cmplx = [-1.1j + 0.1, -1.0 - 0.3j, -0.5-0.5j, 0j, 0.5j, 0.9, 0.99+0.3j, 1j, 1.1]
        # list with various invalid strings
        self.y_list_validate = ['1.1.1', 'xxx', '123', '1.23', '', 1.23j + 3.21, '3.21 + 1.23 j']
        
        self.dut = FIR_DF_wdg

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
        self.assertEqual(12, self.myQ.q_dict['WI'])
        self.assertEqual(0, self.myQ.q_dict['WF'])
        self.assertEqual('12.0', self.myQ.q_dict['Q'])


        # check whether option 'norm' sets the correct scale
        self.myQ.set_qdict({'scale':'norm'})
        self.assertEqual(2**(-self.myQ.q_dict['WI']), self.myQ.q_dict['scale'])
        # check whether option 'int' sets the correct scale
        self.myQ.set_qdict({'scale':'int'})
        self.assertEqual(1<<self.myQ.q_dict['WF'], self.myQ.q_dict['scale'])

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



if __name__=='__main__':
    unittest.main()

# run tests with python -m pyfda.tests.test_pyfda_fir_df
