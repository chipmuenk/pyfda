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
Simple IIR Filter
=================
The following is a straight forward HDL description of a
direct-form-I (sos?!) IIR filter.  This module can be used to
generate synthesizable Verilog/VHDL.



:Author: Christopher Felton <chris.felton@gmail.com>
"""

import myhdl as hdl
from myhdl import Signal, intbv, always, always_comb, always_seq
from pyfda.filter_blocks.support import Samples


@hdl.block
def filter_iir(glbl, sigin, sigout, sos, shared_multiplier=False):
    """Basic IIR direct-form I filter.

    Ports:
        glbl (Global): global signals.
        sigin (SignalBus): input digital signal.
        sigout (SignalBus): output digitla signal.

    Args:
        b (tuple, list): numerator coefficents.
        a (tuple, list): denominator coefficents.

    Returns:
        inst (myhdl.Block, list):
    """
    assert isinstance(sigin, Samples)
    assert isinstance(sigout, Samples)
    assert isinstance(sos, tuple)
    #assert isinstance(b, tuple)

    # All the coefficients need to be an `int`, the
    # class (`???`) handles all the float to fixed-poit
    # conversions.
    ra = [isinstance(aa, int) for aa in sos]
    #rb = [isinstance(bb, int) for bb in b]
    assert all(ra)
    #assert all(rb)

    w = sigin.word_format
    ymax = 2**(w[0]-1)
    vmax = 2**(100*w[0])  # double width max and min
    vmin = -vmax

    # Quantized IIR coefficients
    b0, b1, b2, a0, a1, a2 = sos
    print(sos)
    print(b0,b1,b2,a0,a1,a2)
    q, qd = w[0]-1, 2*w[0]

    # Locally reference the interface signals
    clock, reset = glbl.clock, glbl.reset
    x, xdv = sigin.data, sigin.valid
    y, ydv = sigout.data, sigout.valid

    # Delay elements, list-of-signals (double length for all)
    ffd = [Signal(intbv(0, min=vmin, max=vmax)) for _ in range(2)]
    fbd = [Signal(intbv(0, min=vmin, max=vmax)) for _ in range(2)]
    yacc = Signal(intbv(0, min=vmin, max=vmax))
    dvd = Signal(bool(0))

    @always(clock.posedge)
    def beh_direct_form_one():
        if sigin.valid:
            ffd[1].next = ffd[0]
            ffd[0].next = x

            fbd[1].next = fbd[0]
            #fbd[0].next = yacc[qd:q].signed()
            fbd[0].next = yacc.signed()

    @always_comb
    def beh_acc():
        # double precision accumulator
        yacc.next = (b0 * x) + (b1 * ffd[0]) + (b2 * ffd[1]) \
                    - (a1 * fbd[0]) - (a2 * fbd[1])

    @always_seq(clock.posedge, reset=reset)
    def beh_output():
        dvd.next = xdv
        y.next = yacc[qd:q].signed()
        ydv.next = dvd

    # @todo add shared multiplier version ...

    return hdl.instances()


@hdl.block
def filter_iir_sos(glbl, x, y, sos, w):
    """IIR sum of sections ...
    """
    #assert len(b) == len(a)
    number_of_sections = len(sos)
    list_of_insts = [None for _ in range(number_of_sections)]

    xmax = x.imax
    xmin = x.imin

    xb = [Samples(min = xmin, max = xmax) for _ in range(number_of_sections+1)]
    xb[0] = x
    xb[number_of_sections] = y

    for ii in range(len(sos)):
        list_of_insts[ii] = filter_iir(
            glbl, xb[ii], xb[ii+1],
            sos=tuple(map(int, sos[ii]))
        )

    return list_of_insts

