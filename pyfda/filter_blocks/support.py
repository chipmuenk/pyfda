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
Helper classes and functions for the generation of myhdl signals
"""
import numpy as np

import myhdl as hdl
from myhdl import Signal, SignalType, ResetSignal, intbv, delay


class Clock(SignalType):
    """ 
    Generate a clock instance
    
    Example
    -------
    Generate a clock with a frequency of 50 MHz, starting with '0'
    
    >>> clock = Clock(0, frequency=50e6)
    
    """
    def __init__(self, val=bool(0), frequency=1):
        self.frequency = frequency
        super(Clock, self).__init__(bool(val))

    @hdl.block
    def process(self, hticks=None):
        if hticks is None:
            nts = 1e-9
            period = 1 / self.frequency
            hticks = self._hticks = int(round((period / nts) / 2))

        @hdl.instance
        def beh_clock():
            self.next = False
            while True:
                yield delay(hticks)
                self.next = not self.val

        return beh_clock


class Reset(ResetSignal):
    """ 
    Generate a reset signal 

    Example
    -------
    Generate a reset signal with a frequency of 50 MHz, starting with '0'

    >>> reset = Reset(1, active=0, async=True)
    
    """
    def __init__(self, val=0, active=0, async=True):
        super(Reset, self).__init__(val, active, async)

    def pulse(self, clock=None, pulse_width=77):
        yield delay(10)
        self.next = self.active
        yield delay(pulse_width)
        if clock is not None:
            yield clock.posedge
        self.next = not self.active
        yield delay(10)


class Global(object):
    """ Generate global signals clock, reset, enable """
    def __init__(self, clock, reset):
        self.clock = clock
        self.reset = reset
        self.enable = Signal(bool(0))


class Samples(object):
    def __init__(self, min, max, word_format = (24, 23, 0), res=0, dtype=intbv, sample_rate=1):
        """
        Sample streams, input and output to filters.

        """
        # @todo: fixed-point support ...
        #word_format = (24, 23, 0)
        # The fixed-point word format is described by a tuple, the
        # tuple defines the number of integer bits and fractional bits:
        # (word, int, frac) where: word = int + frac + 1
        self.word_format = check_word_format(word_format)
        wl, iwl, fwl = word_format
        # imax = 2**(wl-1)

        # The sample integer range
        self.imax = imax = max
        self.imin = imin = min

        # @todo: use the dtype
        if dtype == intbv:
            val = intbv(0, min=imin, max=imax)
        else:
            val = dtype(0)
        self.data = Signal(val)
        self.valid = Signal(bool(0))

        self.sample_rate = sample_rate
        self.clock = None

        self.record = False
        self.sample_buffer = []
        self.sample_count = 0

    @hdl.block
    def process_record(self, clock, num_samples=10):
        self.clock = clock
        self.sample_buffer = np.zeros(num_samples)
        self.sample_count = 0

        @hdl.instance
        def beh_record():
            sb = self.sample_buffer
            sc = self.sample_count
            while True:
                yield clock.posedge

                if self.record:
                    if self.valid:
                        sb[sc] = int(self.data.val)
                        sc += 1

        return beh_record


def check_word_format(w):
    """
    Check whether specified word format is either ``(W, WI, WF)`` or ``(W, WI)``
    
    Arguments
    ---------
    w : tuple
      ``(W, WI, WF)`` or ``(W, WI)``, items need to be integer
      
    Returns
    -------
    Tuple
        ``(W, WI, WF)``    
    """
    if len(w) == 2:
        fwl = w[0] - w[1] - 1
        assert fwl >= 0
        wf = (w[0], w[1], )
    elif len(w) == 3:
        wf = w
    else:
        raise Exception("Invalid word format")
    return wf


def Signals(sigtype, num_sigs):
    """ 
    Create a list of myhdl signals, building upon myhdls ``Signal`` (singular)

    Arguments
    ---------
    sigtype : bool, intbv 
        The type to create a Signal from.
    
    num_sigs : int
        The number of signals to create in the list

    Returns
    -------
    sigs: list
        a list of signals, all of type ``sigtype``

    Creating multiple signals of the same type is a common requirement.
    This function facilitates the creation of multiple signals of
    the same type.
    
    Example
    -------

    The following example creates two signals of type bool
        >>> enable, timeout = Signals(bool(0), 2)

    The following creates a list of 256 signals, each of 8-bit type
        >>> mem = Signals(intbv(0)[8:], 256)
    """
    assert isinstance(sigtype, (bool, intbv))
    sigs = [Signal(sigtype) for _ in range(num_sigs)]
    return sigs

