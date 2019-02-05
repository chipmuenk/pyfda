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
Define parallel IIR filter 
"""


import myhdl as hdl
from myhdl import Signal, intbv
from pyfda.filter_blocks.support import Samples, Signals


@hdl.block
def filter_iir(glbl, sigin, sigout, b, a, shared_multiplier=False):
    """Parallel IIR filter.

    Ports:
        glbl (Global): global signals.
        sigin (Samples): input digital signal.
        sigout (SignalBus): output digitla signal.

    Args:
        b (tuple, list): numerator coefficents.

    Returns:
        inst (myhdl.Block, list):
    """
    assert isinstance(sigin, Samples)
    assert isinstance(sigout, Samples)
    assert isinstance(b, tuple)
    assert isinstance(a, tuple)

    rb = [isinstance(bb, int) for bb in b]
    ra = [isinstance(aa, int) for aa in a]
    assert all(ra)
    assert all(rb)

    w = sigin.word_format
    ymax = 2**(w[0]-1)
    vmax = 2**(2*w[0])  # double width max and min
    vmin = -vmax
    N = len(b)-1
    # Quantized IIR coefficients
    b0, b1, b2 = b
    a1, a2 = a
    q, qd = w[0]-1, 2*w[0]

    # Locally reference the interface signals
    clock, reset = glbl.clock, glbl.reset
    xdv = sigin.valid
    ydv = sigout.valid
    y = sigout.data
    x = Signal(intbv(0, min=vmin, max=vmax))

    # Delay elements, list-of-signals (double length for all)
    ffd = Signals(intbv(0, min=vmin, max=vmax), N)
    fbd = Signals(intbv(0, min=vmin, max=vmax), N)
    yacc = Signal(intbv(0, min=vmin, max=vmax))
    dvd = Signal(bool(0))

    @hdl.always(clock.posedge)
    def beh_direct_form_one():
        if sigin.valid:
            x.next = sigin.data
            ffd[1].next = ffd[0]
            ffd[0].next = x

            fbd[1].next = fbd[0]
            fbd[0].next = yacc.signed()
            #print(fbd[0])

    @hdl.always_comb
    def beh_acc():
        # double precision accumulator
        yacc.next = (b0 * x) + (b1 * ffd[0]) + (b2 * ffd[1]) \
                    - (a1 * fbd[0]) - (a2 * fbd[1])

    @hdl.always_seq(clock.posedge, reset=reset)
    def beh_output():
        dvd.next = xdv
        y.next = yacc.signed()
        ydv.next = dvd

    return beh_direct_form_one, beh_acc, beh_output


@hdl.block
def parallel_sum(glbl, b, yin, yout):

    """sum of all the individial parallel outputs ...
    """
    clock, reset = glbl.clock, glbl.reset
    k = Signal(intbv(0)[8:])
    yout = Samples(k.min, k.max)
    list_of_data = [ds.data for ds in yin]
    list_of_valid = [ds.valid for ds in yin]

    @hdl.always_seq(clock.posedge, reset=reset)
    def output():
        yout.data = 0
        for ii in range(len(b)):
            yout.data = yout.data+list_of_data[ii]

        print(yout.data)

    return output


@hdl.block
def filter_iir_parallel(glbl, x, y, b, a, w):
    """structural model of parallel filters ...
    """
    assert len(b) == len(a)
    number_of_sections = len(b)
    list_of_insts = [None for _ in range(number_of_sections)]

    w = x.word_format
    ymax = 2**(w[0]-1)
    vmax = 2**(2*w[0])  # double width max and min
    vmin = -vmax

    y_i = [Samples(vmin, vmax) for _ in range(number_of_sections)]

    for ii in range(len(b)):
        list_of_insts[ii] = filter_iir(
            glbl, x, y_i[ii],
            b=tuple(map(int, b[ii])), a=tuple(map(int, a[ii])))

    insts = parallel_sum(glbl, b, y_i, y)

    return list_of_insts, insts
