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
Define a direct form FIR filter.
"""
import math
import myhdl as hdl
from myhdl import Signal, intbv, always_seq
from pyfda.filter_blocks.support import Samples, Signals


@hdl.block
def filter_fir(glbl, sigin, sigout, b, coef_w, shared_multiplier=False):
    """Basic FIR direct-form I filter.

    Ports:
        glbl (Global): global signals.
        sigin (Samples): input digital signal.
        sigout (Samples): output digitla signal.

    Args:
        b (tuple): numerator coefficents.

    Returns:
        inst (myhdl.Block, list):
    """
    assert isinstance(sigin, Samples)
    assert isinstance(sigout, Samples)
    assert isinstance(b, tuple)
    # All the coefficients need to be an `int`
    rb = [isinstance(bb, int) for bb in b]
    assert all(rb)

    w = sigin.word_format
    w_out = sigout.word_format
    ntaps = len(b)-1
    ymax = 2 ** (w[0]-1)
    sum_abs_b = (sum([abs(x) for x in b]))/2.**(coef_w[0]-1)
    acc_bits = w[0] + coef_w[0] + math.ceil(math.log(sum_abs_b, 2))
    amax = 2**(acc_bits-1)
    qd = acc_bits
    q = acc_bits-w_out[0]

    if q < 0:
        q = 0

    clock, reset = glbl.clock, glbl.reset
    xdv = sigin.valid
    y, ydv = sigout.data, sigout.valid
    x = Signal(intbv(0, min=-ymax, max=ymax))
    # Delay elements, list-of-signals
    ffd = Signals(intbv(0, min=-ymax, max=ymax), ntaps)
    yacc = Signal(intbv(0, min=-amax, max=amax))
    dvd = Signal(bool(0))

    @hdl.always(clock.posedge)
    def beh_direct_form_one():
        if sigin.valid:
            x.next = sigin.data

            for i in range(ntaps-1):
                ffd[i+1].next = ffd[i]

            ffd[0].next = x
            # sum-of-products loop
            c = b[0]
            sop = x * c

            for ii in range(ntaps):
                c = b[ii+1]
                sop = sop + (c * ffd[ii])
            yacc.next = sop

    @always_seq(clock.posedge, reset=reset)
    def beh_output():
        dvd.next = xdv
        y.next = yacc[qd:q].signed()
        ydv.next = dvd

    return beh_direct_form_one, beh_output
