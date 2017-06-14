# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 11:57:19 2017

@author: Christian Muenker
"""


import unittest
from pyfda import pyfda_fix_lib as fix_lib

   
class TestSequenceFunctions(unittest.TestCase):
        
    def setUp(self):
        q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'point': False}
        self.myQ = fix_lib.Fixed(q_obj) # instantiate fixpoint object with settings above
    
        self.y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.9, 0.99, 1.0, 1.1]
        
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

    def test_fix(self):
        """
        Test the actual fixpoint quantization and saturation routine. The 'frmt'
        keyword is not regarded here.
        """
        # return fixpoint numbers as float (no saturation, no quantization)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'none', 'frmt': 'dec', 'point': False}        
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list, to_float=True))
        yq_list_goal = self.y_list
        self.assertEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as float (no saturation, rounding)
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'round', 'frmt': 'dec', 'point': False}        
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list, to_float=True))
        yq_list_goal = [-1.125, -1.0, -0.5, 0, 0.5, 0.875, 1.0, 1.0, 1.125]
        self.assertEqual(yq_list, yq_list_goal)

        # return fixpoint numbers as float w/ saturation + rounding
        q_obj = {'WI':0, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'point': False}        
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list, to_float=True))
        yq_list_goal = [-1, -1, -0.5, 0, 0.5, 0.875, 0.875, 0.875, 0.875]
        self.assertEqual(yq_list, yq_list_goal)
        
        # saturation behaviour
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-8, -8, -4, 0, 4, 7, 7, 7, 7]
        self.assertEqual(yq_list, yq_list_goal)
        
        # saturation, one extra int bit
        q_obj = {'WI':1, 'WF':3, 'ovfl':'sat', 'quant':'round', 'frmt': 'dec', 'point': False}        
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-16, -16, -8, 0, 8, 14, 15, 15, 15]
        self.assertEqual(yq_list, yq_list_goal)
        
        # no saturation behaviour
        q_obj = {'WI':0, 'WF':3, 'ovfl':'none', 'quant':'round', 'frmt': 'dec', 'point': False}        
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-9, -8, -4, 0, 4, 7, 8, 8, 9]
        self.assertEqual(yq_list, yq_list_goal)

        # wrap around behaviour
        q_obj = {'WI':0, 'WF':3, 'ovfl':'wrap', 'quant':'round', 'frmt': 'dec', 'point': False}        
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [7, -8, -4, 0, 4, 7, -8, -8, -7]
        self.assertEqual(yq_list, yq_list_goal)
        
        # wrap around behaviour with 'fix' quantization
        q_obj = {'WI':0, 'WF':3, 'ovfl':'wrap', 'quant':'fix', 'frmt': 'dec', 'point': False}        
        self.myQ.setQobj(q_obj)
        yq_list = list(self.myQ.fix(self.y_list))
        yq_list_goal = [-8, -8, -4, 0, 4, 7, 7, -8, -8]
        self.assertEqual(yq_list, yq_list_goal)       

    def test_frmt(self):
        """
        Test conversion to number formats
        """
        # wrap around behaviour with 'round' quantization
        q_obj = {'WI':0, 'WF':3, 'ovfl':'wrap', 'quant':'round', 'frmt': 'bin', 'point': False}        
        self.myQ.setQobj(q_obj)
        yq_list = list(map(self.myQ.float2frmt, self.y_list))
        yq_list_goal = ['0111', '1000', '1100', '0000', '0100', '0111', '1000', '1000', '1001']
        self.assertEqual(yq_list, yq_list_goal)       


if __name__=='__main__':
    unittest.main()
    
# run tests with python -m pyfda.tests.test_pyfda_fix_lib