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
from numpy.testing import assert_array_equal
from pyfda.libs import pyfda_fix_lib as fx
try:
    from migen import Cat, If, Replicate, Signal, Module, run_simulation
    from pyfda.fixpoint_widgets.fixpoint_helpers import requant
    HAS_MIGEN = True
except ImportError:
    HAS_MIGEN = False


class TestSequenceFunctions(unittest.TestCase):

    def setUp(self):
        self.q_in =  {'WI':0, 'WF':15, 'W':16, 'ovfl':'wrap', 'quant':'round'}
        self.q_out = {'WI':0, 'WF':15, 'W':16, 'ovfl':'wrap', 'quant':'round'}
        if HAS_MIGEN:
            self.dut = DUT(self.q_in, self.q_out)

        self.stim = np.array([0,1,15,64,32767,-1,-64,0]) # last zero isn't tested due to latency of 1

        # initialize a pyfda fixpoint quantizer
        q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'fx_base': 'dec', 'scale': 1}
        self.myQ = fx.Fixed(q_obj) # instantiate fixpoint object with settings above


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

        q_obj = {'WI':7, 'WF':3, 'ovfl':'none', 'quant':'fix', 'fx_base': 'hex', 'scale': 17}
        self.myQ.set_qdict(q_obj)

        # check whether option 'norm' sets the correct scale
        self.myQ.set_qdict({'scale':'norm'})
        self.assertEqual(2**(-self.myQ.q_dict['WI']), self.myQ.q_dict['scale'])
        # check whether option 'int' sets the correct scale
        self.myQ.set_qdict({'scale':'int'})
        self.assertEqual(1<<self.myQ.q_dict['WF']), self.myQ.q_dict['scale'])

    #==========================================================================
    # Test requant routine, this needs a migen class (DUT)
    #--------------------------------------------------------------------------
    # - The input to the run_sim method needs to be an iterable of integers, 
    #    the output is a list of integers
    # - migen moduls only use integer arithmetics, fractional arithmetics is 
    #    only provided by the requant method. It accepts quantization dicts in
    #    the same format as the pyfda quantization library
    # - Due to latency of one, strip last element of input and first of output
    # 

    # np.testing.assert_array_equal(yq_list, yq_list_goal) # compare arrays or lists
    # assert_array_almost_equal

    def test_fix_id(self):
        """
        test identity of input integer list and output list, passed thru migen 
        instance
        """
        response = self.run_sim(self.stim[:])
        assert_array_equal(self.stim[:-1], response[1:])

    def test_fix_round_wi(self):
        """
        Test rescaling for fixpoint integer representation when integer word 
        is shortened by 3 bits.
        """
        # Input quantization format, range: -512 ... 511:
        q_in =  {'WI':9, 'WF':0, 'W':10, 'ovfl':'wrap', 'quant':'round'}
        # Output quantization format, range: -64 ... 63:
        q_out = {'WI':6, 'WF':0, 'W':7, 'ovfl':'wrap', 'quant':'round'}
        targ_out = np.array([0,1,15,-64,-1,-1,-64,0])

        q_out_pyfda = q_out.copy()
        q_out_pyfda.update({'scale':'int'}) 
        self.myQ.set_qdict(q_out_pyfda)      

        self.dut = DUT(q_in, q_out) # pass quantization dicts
        response = self.run_sim(self.stim)

        # compare pyfda fixpoint quantization to migen fixpoint quantization:
        assert_array_equal(self.myQ.fixp(self.stim)[:-1],response[1:])
        # compare target list to migen fixpoint quantization:
        assert_array_equal(targ_out[:-1], response[1:])

    def test_fix_round_wf(self):
        """
        Test rescaling for fixpoint fractional representation when 3 fractional
        bits are thrown away.
        """
        q_in =  {'WI':0, 'WF':9, 'W':10, 'ovfl':'wrap', 'quant':'round'}
        q_out = {'WI':0, 'WF':6, 'W':7, 'ovfl':'wrap', 'quant':'round'}
        targ_out = np.array([0,0,2,8,0,0,-8,0])

        q_out_pyfda = q_out.copy()
        q_out_pyfda.update({'WI':6, 'WF':0, 'W':7}) # use integer representation
        self.myQ.set_qdict(q_out_pyfda)
      
        self.dut = DUT(q_in, q_out)
        response = self.run_sim(self.stim)
        
        # Throwing away 3 LSBs reduces fixpoint value by a factor of 8
        assert_array_equal(self.myQ.fixp(self.stim/8)[:-1],response[1:])
        # compare target list to migen fixpoint quantization:
        assert_array_equal(targ_out[:-1], response[1:])
        

###############################################################################
# migen class for testing requant operation
class DUT(Module):
    def __init__(self, par_in, par_out):

        # ------------- Define I/Os -------------------------------------------
        self.i = Signal((par_in['W'], True)) # input signal
        self.o = Signal((par_out['W'], True)) # output signal
        ###
        # requantize from input format to output format
        self.comb += self.o.eq(requant(self, self.i, par_in, par_out))

if __name__=='__main__':
    unittest.main()

# run tests with python -m pyfda.tests.test_fixpoint_helpers
