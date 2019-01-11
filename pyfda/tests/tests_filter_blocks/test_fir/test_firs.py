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

import numpy as np

import myhdl as hdl
from myhdl import Signal, intbv, delay

from pyfda.filter_blocks.support import Clock, Reset, Global, Samples
from pyfda.filter_blocks.testing.dds import DDSine

from pyfda.filter_blocks.fda.fir import FilterFIR

def notest_filters(args=None): # fails with FilterFIR.process() not implemented in filter_hw.py
    if args is None:
        ntaps, nbands, fs, imax = 86, 3, 1e5, 2**7
        nsmps = 3*ntaps
    # TODO: get the following from args

    clock = Clock(0, frequency=50e6)
    reset = Reset(0, active=0, async=True)
    glbl = Global(clock, reset)

    # Input to the filters
    xi = Samples(min=-imax, max=imax)
    xf = Samples(min=-1, max=1, dtype=float)

    # Output of the filters
    ym = Samples(min=-1, max=1, dtype=float)
    ylist = [Samples(min=-imax, max=imax) for _ in range(4)]
    ym, y1, y2, y3 = ylist
    # Record list, record each of these sample streams
    rlist = [ym] + [xi, xf] + ylist

    dibv = intbv(0, min=-imax, max=imax)
    dds1 = DDSine(1e3, fs, 0.8, 0, dibv)

    # TODO: get coefficients
    # bi, b = get_fir_coef()
    b = np.ones(ntaps) / ntaps
    bi = b * imax
    # h = tuple(bi)

    # Frequency sweep
    fsn = fs/2
    flist = np.linspace(0, fsn, nbands)

    @hdl.block
    def bench_fir():
        tbclk = clock.process()
        tbsin = dds1.process(clock, reset, xi, xf)

        # The collection of FIR filter implementations.
        # a simple model to compare to, each filter has a different
        # delay through the filter implementation
        model_inst = FilterFIR(b, [1]).process(glbl, xf, ym)

        # Create "records" for each sample stream.
        rec_insts = [None for _ in rlist]
        for ii, sc in enumerate(rlist):
            rec_insts[ii] = sc.process_record(clock, num_samples=nsmps)

        @hdl.instance
        def tbstim():
            yield reset.pulse(clock)
            yield clock.posedge

            for ff in flist:
                # Avoid the transitions
                dds1.set_frequency(ff)
                for _ in range(ntaps+7):
                    yield xi.valid.posedge
                dds1.set_zero(False)
                yield clock.posedge

                # Enable recording
                for sr in rlist:
                    sr.record = True

                # Collect a sample from each filter

                for sr in rlist:
                    sr.record = False
                    

            yield delay(1100)
            raise hdl.StopSimulation

        return hdl.instances()

    tb = bench_fir()
    tb.config_sim(trace=True)
    tb.run_sim()


if __name__ == '__main__':
    test_filters()



