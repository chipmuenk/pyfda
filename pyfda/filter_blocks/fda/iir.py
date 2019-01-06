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
Simulate and convert IIR fixpoint filter block using myHDL
"""
import numpy as np
import myhdl as hdl
from myhdl import Signal, intbv, StopSimulation

from .filter_hw import FilterHardware
from ..iir import iir_df1, iir_sos
from pyfda.filter_blocks.support import Clock, Reset, Global, Samples


class FilterIIR(FilterHardware):
    def __init__(self, b = None, a = None):
        """Contains IIR filter parameters. Parent Class : FilterHardware
            Args:
                b (list of int): list of numerator coefficients.
                a (list of int): list of denominator coefficients.
                word format (tuple of int): (W, WI, WF)
                filter_type:
                filter_form_type:
                response(list): list of filter output in int format.
            """
        super(FilterIIR, self).__init__(b, a)
        self.filter_type = 'direct_form'
        self.direct_form_type = 1
        self.response = []

    def get_response(self):
        """Return filter output.

        Returns:
            response(numpy int array) : returns filter output as
            numpy array
        """
        return self.response

    def run_sim(self):
        """Run filter simulation"""

        testfil = self.filter_block()
        #testfil.config_sim(trace=True)
        testfil.run_sim()

    def info(self):
        """Print filter info"""
        print("Filter type :", self.filter_type, "\n"
              "Filter order :", len(self.b), "\n"
              "Arithmatic :", "fixed", "\n"
              "Coefficient format :", self.coef_word_format ,"\n"
              "Input format :", self.input_word_format ,"\n"
              "Accumulator size :", "\n"
              "Output format :", self.output_word_format ,"\n"
              "Round mode :", "no rounding", "\n"
              "Overflow mode :" "saturate"
            )

    def convert(self, **kwargs):
        """Convert the HDL description to Verilog and VHDL.
        """
        w = self.input_word_format
        w_out = self.output_word_format
        omax = 2**(w_out[0]-1)
        imax = 2**(w[0]-1)

        # small top-level wrapper
        def filter_iir_top(hdl , clock, reset, x, xdv, y, ydv):
            sigin = Samples(x.min, x.max, self.input_word_format)
            sigin.data, sigin.data_valid = x, xdv
            sigout = Samples(y.min, y.max, self.output_word_format)
            sigout.data, sigout.data_valid = y, ydv
            clk = clock
            rst = reset
            glbl = Global(clk, rst)
            
            # choose appropriate filter
            iir_hdl = iir_df1.filter_iir

            iir = iir_hdl(
                glbl, sigin, sigout, self.b, self.a, self.coef_word_format,
                shared_multiplier=self._shared_multiplier
            )
            iir.convert(**kwargs)

        clock = Clock(0, frequency=50e6)
        reset = Reset(1, active=0, async=True)
        x = Signal(intbv(0, min=-imax, max=imax))
        y = Signal(intbv(0, min=-omax, max=omax))
        xdv, ydv = Signal(bool(0)), Signal(bool(0))
        

        if self.hdl_target.lower() == 'verilog':
            filter_iir_top(hdl, clock, reset, x, xdv, y, ydv)
 
        elif self.hdl_target.lower() == 'vhdl':
            filter_iir_top(hdl, clock, reset, x, xdv, y, ydv)
        else:
            raise ValueError('incorrect target HDL {}'.format(self.hdl_target))

    @hdl.block
    def filter_block(self):
        """ this elaboration code will select the different structure and implementations"""

        w = self.input_word_format
        w_out = self.output_word_format
        
        ymax = 2**(2*w[0]-1)
        vmax = 2**(2*w[0])
        omax = 2**(w_out[0]-1)
        xt = Samples(min=-ymax, max=ymax, word_format=self.input_word_format)
        yt = Samples(min=-omax, max=omax, word_format=self.output_word_format)
        xt.valid = bool(1)
        clock = Clock(0, frequency=50e6)
        reset = Reset(1, active=0, async=True)
        glbl = Global(clock, reset)
        tbclk = clock.process()
        numsample = 0
        
        # set numsample 
        numsample = len(self.sigin)
        # process to record output in buffer
        rec_insts = yt.process_record(clock, num_samples=numsample)

        if self.filter_type == 'direct_form':
            if self.direct_form_type == 1:
                # all filters will need the same interface ports, this should be do able
                dfilter = iir_df1.filter_iir

            if self.n_cascades > 0:
                # TODO: port the SOS iir into the latest set of interfaces
                #filter_insts = iir_sos.filter_iir_sos(
                #     glbl, xt, yt, self.sos, self.coef_word_format
                #)
                pass
            
            else:
                filter_insts = dfilter(
                    glbl, xt, yt, self.b, self.a, self.coef_word_format
                )

        @hdl.instance
        def stimulus():
            """record output in numpy array yt.sample_buffer"""
            for k in self.sigin:
                xt.data.next = int(k)
                xt.valid = bool(1)

                yt.record = True
                yt.valid = True
                yield clock.posedge
                # Collect a sample from each filter
                yt.record = False
                yt.valid = False

            self.response = yt.sample_buffer

            raise StopSimulation()

        return hdl.instances()
