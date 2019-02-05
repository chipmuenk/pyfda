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
Define FIR filter 
"""

from math import log, ceil

import myhdl as hdl
from myhdl import Signal, intbv, always_seq

from pyfda.filter_blocks.support import Samples


@hdl.block
def filter_fir_parallel(clock, reset, x, y, h):
    """ A basic FIR filter description
    """
    assert isinstance(x, Samples)
    assert isinstance(y, Samples)

    xd = [Signal(intbv(0, min=x.data.min, max=x.data.max))
          for _ in range(len(h)-1)]

    # need to scale the outputs, the multiply will
    # create a number twice as big
    scale = int(len(x.data)-1)

    @always_seq(clock.posedge, reset=reset)
    def beh_sop():
        if x.vld:
            # tap update loop
            xd[0].next = x.sig
            for ii in range(1, len(h)-1):
                xd[ii].next = xd[ii-1]
                
            # sum-of-products loop
            c = h[0]
            sop = x.data * c
            for ii in range(len(h)-1):
                c = h[ii+1]
                sop = sop + (c * xd[ii])
            
            # scale the sum of products to the 
            # output range (truncate)
            y.data.next = sop >> scale
            y.valid.next = True
        else:
            y.valid.next = False

    return beh_sop
