# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)
#
# Taken from https://github.com/sriyash25/filter-blocks
# (c) Christopher Felton and Sriyash Caculo

"""
Top level class for fixpoint filter simulation and conversion?
"""
import numpy as np

import logging
logger = logging.getLogger(__name__)


class FilterHardware(object):
    def __init__(self, b=None, a=None):
        """
        Helper class with common attributes and methods for all filters
        
        Arguments
        ---------
        b (list of int): list of numerator coefficients.
        a (list of int): list of denominator coefficients.

        Attributes
        ----------
        coef_word_format (tuple of int): word format (W,WI,WF).
        n_cascades (int):
        sigin (numpy int array):
        nfft (int):
        hdl_name (str):
        hdl_directory (str):
        hdl_target (str):
        """
        # numerator coefficient
        if b is not None:
            self.b = tuple(b)

        # denominator coefficients
        if a is not None:
            self.a = tuple(a)

        # TODO: need a default word format, the coefficient
        #       can be determined from the coefficients if passed
        #       use an arbitrary value of the input and output
        self.coef_word_format = (24, 0, 23)
        self.input_word_format = (16, 0, 15)
        self.output_word_format = (16, 0, 15)

        self.n_cascades = 0
        self.sigin = np.array([])
        self._shared_multiplier = False
        self._sample_rate = 1
        self._clock_frequency = 1

        self.nfft = 1024

        self.hdl_name = 'name'
        self.hdl_directory = 'directory'
        self.hdl_target = 'verilog'

        # A reference to the HDL block
        self.hardware = None
        
    def setup(self, fx_dict):
        """
        Setup coefficients, word lengths etc.

        Returns
        -------
        None

        Arguments
        ---------
        fx_dict (dict): dictionary with filter parameters:
            
            - coef_w (tuple of int): word format (W, WI, WF)
            
            - input_w (tuple of int): word format (W, WI, WF)
            
            - output_w (tuple of int): word format (W, WI, WF)
        """
        self.coef_word_format  = (fx_dict['QC']['W'], fx_dict['QC']['WI'], fx_dict['QC']['WF'])
        self.input_word_format = (fx_dict['QI']['W'], fx_dict['QI']['WI'], fx_dict['QI']['WF'])
        self.output_word_format = (fx_dict['QO']['W'], fx_dict['QO']['WI'], fx_dict['QO']['WF'])
        
        self.b = tuple(fx_dict['QC']['b'])
        self.a = tuple(fx_dict['QC']['a'])
        if 'sos' in fx_dict['QC']:
            self.sos =  tuple(fx_dict['QC']['sos'])


    def set_coefficients(self, coeff_b = None, coeff_a = None, sos = None):
        """Set filter coefficients.

        Args:
            coeff_b (list): list of numerator filter coefficients
            coeff_a (list): list of denominator filter coefficients
        """
        if coeff_b is not None:
            self.b = tuple(coeff_b)

        if coeff_a is not None:
            self.a = tuple(coeff_a)

        if sos is not None:
            self.sos = sos

    def set_stimulus(self, sigin):
        """Set filter stimulus

        Args:
            sigin (np array int): numpy array of filter stimulus 
            bits (int) : no of bits
        """
        self.sigin = sigin.tolist()
        logger.warning("set_stimulus : {0}".format(self.sigin))

    def set_cascade(self, n_cascades):
        """Set number of filter cascades

        Args:
            n_cascades (int): no of filter sections connected together
        """
        self.n_cascades = n_cascades
