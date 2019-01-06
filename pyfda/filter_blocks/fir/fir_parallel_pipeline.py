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
Define pipelined FIR filter (?)
"""

import myhdl as hdl
from myhdl import Signal, intbv, always_seq

from pyfda.filter_blocks.support import Samples


@hdl.block
def pipes(clock, reset, ti, to, vi, vo):
    assert isinstance(ti, list)
    assert isinstance(to, list)
    assert len(ti) == len(to)
    Ntaps = len(ti)

    @always_seq(clock.posedge, reset)
    def beh_pipes():
        for ii in range(Ntaps):
            to[ii].next = ti[ii]
        vo.next = vi

    return beh_pipes


@hdl.block
def filter_fir_parallel_pipeline(clock, reset, x, y, h, multpipe=3):
    assert isinstance(x, Samples)
    assert isinstance(y, Samples)

    ntaps = len(h)

    # The converter only knows how to deal with a list of signals,
    # need to extract the signals from my interface (bus object)
    xd = [Samples(min=x.data.min, max=x.data.max) for _ in range(ntaps)]
    xds = [ss.data for ss in xd]

    # Need enough valids for the complete pipeline, one for the
    # tap update, one for the multiplies, /gm/ for the multiply
    # pipeline stages.
    vld = [Signal(bool(0)) for _ in range(multpipe+2)]

    # Setup the configurable pipeline stage after the multiple.  In
    # some cases (synthesis guidelines) multiple registers are desired
    # after a  multiply to maximize hard MAC (DSP block) in the FPGA.
    # currently the converter does not handle 2D lists of signals,
    # need to break it out in elaboration.
    pmax = x.data.max * x.data.max
    pmat = [[Signal(intbv(0, min=-pmax, max=pmax))
             for _ in range(ntaps)] for _ in range(multpipe+1)]
    pris, pros = pmat[0], pmat[multpipe]
    pipe_insts = [None for _ in range(multpipe)]
    for ii in range(multpipe):
        pipe_insts[ii] = pipes(clock, reset, pmat[ii],
                               pmat[ii+1], vld[ii+1], vld[ii+2])
    
    # Extra pipeline after scaling
    ypipe = Samples(min=-pmax, max=pmax)

    # Need to scale the outputs, the multiply will
    # create a number twice as big
    scale = int(len(x.sig)-1)

    # when a new sample is ready (vld) it will kick off the 
    # pipelined compuation, if the sample stream is continuous 
    # the pipeline will remain full.
    @always_seq(clock.posedge, reset=reset)
    def beh_sop():
        
        # Tap update loop, if there is a new sample get it, if
        # a new sample is not right on the heels clear all vlds
        # only the first, xd[0], vld is used to feed the pipe.
        if x.vld:
            xds[0].next = x.sig
            vld[0].next = x.vld
            for ii in range(1,ntaps):
                xds[ii].next = xds[ii-1]
        else:
            vld[0].next = False
                
        # Output pipelines, adds to the overall delay
        # of the filter but does not change the response            
        # multiply loop, certain MAC IP require registers, the 
        # pipeline after the multiply can be set.
        for ii in range(ntaps):
            c = h[ii]
            pris[ii].next = c * xds[ii]
        vld[1].next = vld[0]
    
        # Multiply pipeline stages, instantiated above
        # vld[1]i, vld[2]oi, ..., vld[mp-1]o
        
        # sum-of-products loop
        sop = 0
        for ii in range(ntaps):
            sop = sop + pros[ii]
        
        ypipe.data.next = sop
        ypipe.valid.next = vld[multpipe+1]
        
        y.data.next = ypipe.data >> scale
        y.valid.next = ypipe.valid

    return hdl.instances()
