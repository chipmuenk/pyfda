# -*- coding: utf-8 -*-
#
# Copyright (c) 2011, 2015 Christopher L. Felton
#

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

# module documentation
"""
:Author: Christopher Felton <cfelton@ieee.org>
"""

from myhdl import (Signal, always_seq, always_comb, intbv, concat)

from .filter_intf import FilterInterface


def filter_iir_hdl(clock, reset, sigin, sigout, coefficients=(None, None,),
                   shared_multiplier=False):
    """ Hardware description of a direct-form type I IIR filter
    @todo: description

    Ports
    -----
      clock: system global synchronous clock
      reset: system global reset
      sigin: digital input signal
      sigout: digital output signal

    Parameters
    ----------
      coefficients:
      shared_multiplier:

      B: numerator coefficients, in fixed-point matching `W` format
      A: denominator coefficients, in fixed-point matchin `W` format
      W: fixed-point description tuple: (word-length, integer-word-length,
         fractional-word-length)
           W[0] = word length (wl)
           W[1] = integer word length (iwl)
           W[2] = franction world length (fwl)
           wl = iwl+fwl+1
    """
    b, a = coefficients

    # @todo: current limitation ... mismatch input output future enhancement
    assert sigin.word_format == sigout.word_format
    w = sigin.word_format
    assert isinstance(w, tuple), "Fixed-Point format (W) should be a 2-element tuple"
    assert len(w) == 2 or len(w) == 3, "Fixed-Point format (W) should be a 2-element tuple"

    assert isinstance(a, tuple), "Tuple of denominator coefficents length 3"
    assert len(a) == 3, "Tuple of denominator coefficients length 3"

    assert isinstance(b, tuple), "Tuple of numerator coefficients length 3"
    assert len(b) == 3, "Tuple of numerator coefficients length 3"

    # Make sure all coefficients are int, the class wrapper handles all float to
    # fixed-point conversion.
    ra = [isinstance(a[ii], int) for ii in range(len(a))]
    rb = [isinstance(b[ii], int) for ii in range(len(b))]

    assert False not in ra, "All A coefficients must be type int (fixed-point)"
    assert False not in rb, "All B coefficients must be type int (fixed-point)"

    # full width based on operations
    # @todo: add inner maximum gain calculations
    dmax = 2**(2*w[0])+3
    dmin = -1*dmax

    # Quantize IIR Coefficients
    b0, b1, b2 = b
    a0, a1, a2 = a

    # the input and output word lengths are the same size, these
    # are used to determine the slice of the full precision accumulator
    # should be used.
    ql, qu = w[0]-1, 2*w[0]

    # locally reference the interface signals
    x, xdv = sigin.data, sigin.data_valid
    y, ydv = sigout.data, sigout.data_valid

    # Delay elements, list of signals (double length for all)
    ffd = [Signal(intbv(0, min=dmin, max=dmax)) for _ in range(2)]
    fbd = [Signal(intbv(0, min=dmin, max=dmax)) for _ in range(2)]
    dvd = Signal(bool(0))
    # accumulator full precision
    yacc = Signal(intbv(0, min=dmin, max=dmax))

    @always_seq(clock.posedge, reset=reset)
    def rtl_input():
        if xdv:
            ffd[1].next = ffd[0]
            ffd[0].next = x

            fbd[1].next = fbd[0]
            fbd[0].next = yacc[qu:ql].signed()

    @always_comb
    def rtl_acc():
        # full precision accumulator - second order only
        yacc.next = ((b0*x) + (b1*ffd[0]) + (b2*ffd[1]) -
                     (a1*fbd[0]) - (a2*fbd[1]))

    @always_seq(clock.posedge, reset=reset)
    def rtl_output():
        dvd.next = xdv
        y.next = yacc[qu:ql].signed()
        ydv.next = dvd

    stage = Signal(intbv(0, min=0, max=8))
    product = Signal(intbv(0, min=dmin, max=dmax))
    m1, m2 = [Signal(intbv(0, min=dmin, max=dmax)) for _ in range(2)]

    @always_seq(clock.posedge, reset=reset)
    def rtl_acc_shared():
        ydv.next = False  # default
        if stage == 0 and xdv:
            stage.next = 1
            m1.next = b0
            m2.next = x
            yacc.next = 0
        elif stage == 1:
            stage.next = 2
            m1.next = b1
            m2.next = ffd[0]
            yacc.next = yacc + product  # accumulating b0*x
        elif stage == 2:
            stage.next = 3
            m1.next = b2
            m2.next = ffd[1]
            yacc.next = yacc + product  # accumulating b1*ffd[0]
        elif stage == 3:
            stage.next = 4
            m1.next = a1
            m2.next = fbd[0]
            yacc.next = yacc + product  # accumulating b2*ffd[1]
        elif stage == 4:
            stage.next = 5
            m1.next = a2
            m2.next = fbd[1]
            yacc.next = yacc - product  # accumulating a1*fbd[0]
        elif stage == 5:
            stage.next = 6
            m1.next = 0
            m2.next = 0
            yacc.next = yacc - product  # accumulating a1*fbd[0]
        elif stage == 6:
            stage.next = 0
            y.next = yacc[qu:ql].signed()
            ydv.next = True

    @always_comb
    def rtl_shared_mult():
        product.next = m1 * m2

    # determine the generators to return based on the parameters
    if shared_multiplier:
        gens = (rtl_input, rtl_acc_shared, rtl_shared_mult,)
    else:
        gens = (rtl_input, rtl_acc, rtl_output,)

    return gens

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def filter_iir_sos_hdl(clock, reset, sigin, sigout, coefficients=None,
                       shared_multiplier=False):
    """ Cascaded second-order IIR filters.

    Ports
    -----
    :param clock:
    :param reset:
    :param sigin:
    :param sigout:

    Parameters
    ----------
    :param coefficients:
    :param shared_multiplier:
    :return:
    """
    b, a = coefficients
    assert len(b) == len(a)
    num_sections = len(b)
    w = sigout.w
    list_of_iir = [None for _ in range(num_sections)]
    _x = [FilterInterface(word_format=sigout.word_format)
          for _ in range(num_sections+1)]
    _x[0] = sigin
    _x[num_sections] = sigout

    for ii in range(len(B)):
        list_of_iir[ii] = filter_iir_hdl(clock, reset, _x[ii], _x[ii+1],
                                         coefficients=(b[ii], a[ii]),
                                         shared_multiplier=shared_multiplier)
    return list_of_iir

