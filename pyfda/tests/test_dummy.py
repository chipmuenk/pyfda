# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 11:57:19 2017

@author: Christian Muenker
"""

import unittest

   
class TestSequenceFunctions(unittest.TestCase):
        
    def setUp(self):
        """
        This is called first
        """
        self.y_list = [-1.1, -1.0, -0.5, 0, 0.5, 0.99, 1.0]

    def test_dummy_pass(self):
        """
        This test passes       
        """
        self.assertEqual(self.y_list, self.y_list)

#    def test_dummy_fail(self):
#        """
#        This test fails      
#        """        
#        self.assertEqual(self.y_list, [])


if __name__=='__main__':
    unittest.main(argv=['first-argument-is-ignored', '-v']) # '-v' for more verbose output
    
# run tests with python -m pyfda.tests.test_dummy