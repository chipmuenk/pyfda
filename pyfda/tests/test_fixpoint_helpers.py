# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Test suite for fixpoint_helpers.py
"""

import unittest
import numpy as np
from pyfda import pyfda_fix_lib as fix_lib
try:
    from migen import Cat, If, Replicate, Signal, Module, run_simulation
    from pyfda.fixpoint_widgets.fixpoint_helpers import rescale
    HAS_MIGEN = True
except ImportError:
    HAS_MIGEN = False


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.p_in =  {'WI':0, 'WF':15, 'W':16, 'ovfl':'wrap', 'quant':'round'}
        self.p_out = {'WI':0, 'WF':15, 'W':16, 'ovfl':'wrap', 'quant':'round'}
        if HAS_MIGEN:
            self.dut = DUT(self.p_in, self.p_out)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 1}
        self.myQ = fix_lib.Fixed(q_obj) # instantiate fixpoint object with settings above

        self.y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.9, 0.99, 1.0, 1.1]
        self.y_list_cmplx = [-1.1j + 0.1, -1.0 - 0.3j, -0.5-0.5j, 0j, 0.5j, 0.9, 0.99+0.3j, 1j, 1.1]
        # list with various invalid strings
        self.y_list_validate = ['1.1.1', 'xxx', '123', '1.23', '', 1.23j + 3.21, '3.21 + 1.23 j']

        self.fix_in = [0,1,15,32767,-1,-64,0] # last zero isn't tested due to latency of 1
        self.fix_out = [0,1,15,32768,-1,-64]

    def tb_dut(self, stimulus, inputs, outputs):
        """ use stimulus list from widget as input to filter """
        for x in stimulus:
            yield self.dut.i.eq(int(x)) # pass one stimulus value to filter
            inputs.append(x) # and append it to input list
            outputs.append((yield self.dut.o)) # append filter output to output list
            yield # ??

#------------------------------------------------------------------------------
    def run_sim(self, stimulus):
        """
        Pass stimuli and run filter simulation, see
        https://reconfig.io/2018/05/hello_world_migen
        https://github.com/m-labs/migen/blob/master/examples/sim/fir.py
        """
        inputs = []
        response = []

        testbench = self.tb_dut(stimulus, inputs, response)

        run_simulation(self.dut, testbench)

        return response

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

        # check whether option 'norm' sets the correct scale
        self.myQ.setQobj({'scale':'norm'})
        self.assertEqual(2**(-self.myQ.WI), self.myQ.scale)
        # check whether option 'int' sets the correct scale
        self.myQ.setQobj({'scale':'int'})
        self.assertEqual(1<<self.myQ.WF, self.myQ.scale)

    def test_fix_no_ovfl(self):
        """
        Test the actual fixpoint quantization without saturation / wrap-around. The 'frmt'
        keyword is not regarded here.
        """
        # return fixpoint numbers as float (no saturation, no quantization)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
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
        q_obj = {'scale': 2}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(self.y_list) / 2.)
        self.assertEqual(yq_list, yq_list_goal)

        # test scaling (divide by scaling factor)
        yq_list = list(self.myQ.fixp(self.y_list, scaling='div') * 2.)
        self.assertEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as float (rounding)
        q_obj = {'quant':'round', 'scale': 1}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-1.125, -1.0, -0.5, 0, 0.5, 0.875, 1.0, 1.0, 1.125]
        self.assertEqual(yq_list, yq_list_goal)

        # wrap around behaviour with 'fix' quantization; fractional representation
        q_obj = {'WI':5, 'WF':2, 'ovfl':'wrap', 'quant':'fix', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-8.75, -8.0, -4.0, 0.0, 4.0, 7.0, 7.75, 8.0, 8.75]
        self.assertEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as integer (rounding), overflow 'none'
        q_obj = {'WI':3, 'WF':0, 'ovfl':'none', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-9, -8, -4, 0, 4, 7, 8, 8, 9]
        self.assertEqual(yq_list, yq_list_goal)

        # input list of strings
        y_string = ['-1.1', '-1.0', '-0.5', '0', '0.5', '0.9', '0.99', '1.0', '1.1']
        yq_list = list(self.myQ.fixp(y_string))
        yq_list_goal = [-9, -8, -4, 0, 4, 7, 8, 8, 9]
        self.assertEqual(yq_list, yq_list_goal)

        # frmt float
        q_obj = {'frmt': 'float'}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(y_string))
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
        yq_list = list(map(self.myQ.fixp, self.y_list_cmplx))
        yq_list_goal = [0.1, -1.0, -0.5, 0.0, 0.0, 0.9, 0.99, 0.0, 1.1]
        self.assertEqual(yq_list, yq_list_goal)
        # same in array format
        yq_list = list(self.myQ.fixp(self.y_list_cmplx))
        self.assertListEqual(yq_list, yq_list_goal)
#==============================================================================
    def test_fix_saturation(self):
        """
        Test saturation
        """
        y_list_ovfl = [-np.inf, -3.2, -2.2, -1.2, -1.0, -0.5, 0, 0.5, 0.8, 1.0, 1.2, 2.2, 3.2, np.inf]

        # Integer representation, saturation
        q_obj = {'WI':3, 'WF':0, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(y_list_ovfl))
        yq_list_goal = [-8.0, -8.0, -8.0, -8.0, -8.0, -4.0, 0.0, 4.0, 6.0, 7.0, 7.0, 7.0, 7.0, 7.0]
        self.assertEqual(yq_list, yq_list_goal)

        # Fractional representation, saturation
        q_obj = {'WI':3, 'WF':1, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(y_list_ovfl))
        yq_list_goal = [-8, -8, -8, -8, -8, -4, 0, 4, 6.5, 7.5, 7.5, 7.5, 7.5, 7.5]
        self.assertEqual(yq_list, yq_list_goal)

        # normalized fractional representation, saturation
        q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-1, -1, -0.5, 0, 0.5, 0.875, 0.875, 0.875, 0.875]
        self.assertEqual(yq_list, yq_list_goal)

        # saturation, one extra int bit
        q_obj = {'WI':1, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'scale': 1}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(self.y_list))
        yq_list_goal = [-1.125, -1.0, -0.5, 0.0, 0.5, 0.875, 1.0, 1.0, 1.125]
        self.assertEqual(yq_list, yq_list_goal)


    def test_fix_wrap(self):
        """
        Test wrap around -np.inf, , np.inf ,np.nan, , np.nan
        """
        y_list_ovfl = [-3.2, -2.2, -1.2, -1.0, -0.5, 0, 0.5, 0.8, 1.0, 1.2, 2.2, 3.2]

        # Integer representation, wrap
        q_obj = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = self.myQ.fixp(y_list_ovfl)
        yq_list_goal = [6.0, -2.0, 6.0, -8.0, -4.0, 0.0, 4.0, 6.0, -8.0, -6.0, 2.0, -6.0]
        np.testing.assert_array_equal(yq_list, yq_list_goal)

        # wrap around behaviour / floor quantization
        q_obj = {'WI':3, 'WF':1, 'ovfl':'wrap', 'quant':'floor', 'frmt': 'dec', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fixp(self.y_list))
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
        yq_list_goal = ["0000", "0000", "0111", "0111", "0000", "0111", "0111"]
        self.assertEqual(yq_list, yq_list_goal)
        # same in vector format
        yq_list = list(self.myQ.float2frmt(self.y_list_validate))
        # input       ['1.1.1', 'xxx', '123', '1.23',    '', 1.23j + 3.21, '3.21 + 1.23 j']
        self.assertListEqual(yq_list, yq_list_goal)

        # Integer case: Q3.0, scale = 8, wrap, scalar inputs
        q_obj = {'WI':3, 'WF':0, 'ovfl':'wrap', 'quant':'round', 'frmt': 'bin', 'scale': 8}
        self.myQ.setQobj(q_obj)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['0111', '1000', '1100', '0000', '0100', '0111', '1000', '1000', '1001']
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized function
        yq_arr = list(self.myQ.float2frmt(self.y_list))
        self.assertEqual(yq_arr, yq_list_goal)

        # Q1.2 format and scale = 2, saturation, scalar inputs
        q_obj = {'WI':1, 'WF':2, 'ovfl':'sat', 'quant':'round', 'frmt': 'bin', 'scale': 2}
        self.myQ.setQobj(q_obj)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['10.00', '10.00', '11.00', '00.00', '01.00', '01.11', '01.11', '01.11', '01.11']
        self.assertEqual(yq_list, yq_list_goal)
        # same but vectorized function
        yq_list = list(self.myQ.float2frmt(self.y_list))
        self.assertEqual(yq_list, yq_list_goal)

    #==============================================================================
    #   Test rescale routine, this needs a migen class (DUT)
    #   The input to the run_sim methods needs to be an iterable, output is a list of integer
    # due to latency of one, strip last element of input and first of output


    def test_fix_id(self):
        """
        test identity of input integer list and output list, passed thru migen 
        instance
        """
        response = self.run_sim(self.fix_in[:])
        self.assertEqual(self.fix_in[:-1], response[1:])

    def test_fix_round_wf(self):
        """
        Test rescaling when fractional word is shortened by 4 bits
        """
        self.p_in =  {'WI':0, 'WF':9, 'W':10, 'ovfl':'wrap', 'quant':'round'}
        self.p_out = {'WI':0, 'WF':5, 'W':6, 'ovfl':'wrap', 'quant':'round'}
        q_out = self.p_out.copy()
        q_out.update({'WI':9, 'WF':0, 'W':10, 'scale':1/16})
        self.dut = DUT(self.p_in, self.p_out)

        # Integer representation, wrap
        self.myQ.setQobj(q_out)
        fixq_in = list(self.myQ.fixp(self.fix_in))

        response = self.run_sim(self.fix_in[:])
        #self.assertEqual(self.fix_in[:-1], response[1:])
        self.assertEqual(fixq_in[:-1], response[1:])
        self.assertEqual(fixq_in[:-1], response[1:])
        self.assertEqual(fix_out[:-1], response[1:])
        

###############################################################################
# migen class for testing rescale operation
class DUT(Module):
    def __init__(self, par_in, par_out):

        # ------------- Define I/Os -------------------------------------------
        self.i = Signal((par_in['W'], True)) # input signal
        self.o = Signal((par_out['W'], True)) # output signal
        ###
        # rescale from input format to output format
        self.comb += self.o.eq(rescale(self, self.i, par_in, par_out))

if __name__=='__main__':
    unittest.main()

# run tests with python -m pyfda.tests.test_pyfda_fixpoint_helpers
