# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Fixpoint class for calculating direct-form DF1 FIR filter using pyfixp routines
"""
import logging
logger = logging.getLogger(__name__)

import numpy as np
from numpy.lib.function_base import iterable
import pyfda.filterbroker as fb
# from pyfda.libs.pyfda_lib import pprint_log
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_fix_lib import quant_coeffs

from pyfda.libs.pyfda_fix_lib_amaranth import requant

from functools import reduce
from operator import add

from amaranth.back import verilog
from amaranth import Signal, signed, Elaboratable, Module
from amaranth.sim import Simulator, Tick  # , Delay, Settle


class FIR_DF_amaranth_mod(Elaboratable):
    """
    A synthesizable nMigen FIR filter in Direct Form.

    Construct fixed point object with parameter dict `p`

    Usage:
    ------
    filt = FIR_DF(p) # Instantiate fixpoint filter object with parameter dict

    Parameters
    ----------
    p : dict
        Dictionary with coefficients and quantizer settings with a.o.
        the following keys : values

        - 'QCB', value: array of coefficients as floats, scaled as `WI:WF`

        - 'QACC', value: dict with quantizer settings for the accumulator

        - 'q_mul', value: dict with quantizer settings for the partial products
           optional, 'quant' and 'sat' are both set to 'none' if there is none
    """
    def __init__(self, p):
        self.init(p)

    # ---------------------------------------------------------
    def init(self, p, zi: iterable = None) -> None:
        """
        Initialize filter with parameter dict `p` by initialising all registers
        and quantizers.
        This needs to be done every time quantizers or coefficients are updated.

        Parameters
        ----------
        p : dict
            dictionary with coefficients and quantizer settings (see docstring of
            `__init__()` for details)

        zi : array-like
            Initialize `L = len(b)` filter registers. Strictly speaking, `zi[0]` is
            not a register but the current input value.
            When `len(zi) != len(b)`, truncate or fill up with zeros.
            When `zi == None`, all registers are filled with zeros.

        Returns
        -------
        None.
        """
        logger.warning("Initializing filter")
        self.p = p  # parameter dictionary with coefficients etc.

        # update the quantizers from the dictionary
        self.b_q = p['ba']
        # logger.warning(f"b_q = {self.b_q}")
        self.L = len(self.b_q)  # filter length = number of coefficients / taps
        DW = int(np.ceil(np.log2(self.L)))  # word growth

        # Accumulator settings
        # self.Q_acc = fx.Fixed(p['QACC'])  # accumulator
        self.W_acc = self.p['QACC']['WI'] + self.p['QACC']['WF'] + 1  # total accu word length

        # Partial products: use accumulator settings and update word length
        # to sum of coefficient and input word lengths
        self.Q_mul = fx.Fixed(p['QACC'].copy())  # partial products
        self.Q_mul.set_qdict({'WI': self.p['QI']['WI'] + self.p['QCB']['WI'] + DW,
             'WF': self.p['QI']['WF'] + self.p['QCB']['WF']})
        self.W_mul = self.Q_mul.q_dict['WI'] + self.Q_mul.q_dict['WF'] + 1
        # self.W_mul = 1 + DW + self.p['QI']['WI'] + self.p['QCB']['WI']\
        #    + self.p['QI']['WF'] + self.p['QCB']['WF']

        # Input and output signal are quantized in FIR_DF_Amaranth()

        self.reset() # reset overflow counters (except coeffs) and registers

        # Initialize filter memory with passed values zi and fill up with zeros
        # or truncate to filter length
        ######  NOT IMPLEMENTED YET - Amaranth remembers state variables between sims?
        if zi is not None:
            if len(zi) == self.L - 1:
                self.zi = zi
            elif len(zi) < self.L - 1:
                self.zi = np.concatenate((zi, np.zeros(self.L - 1 - len(zi))))
            else:
                self.zi = zi[:self.L - 1]

        # ------------- Define I/Os for amaranth module ---------------------------
        self.WI = p['QI']['WI'] + p['QI']['WF'] + 1  # total input word length
        self.WO = p['QO']['WI'] + p['QO']['WF'] + 1  # total output word length
        self.i = Signal(signed(self.WI))  # input signal
        self.o = Signal(signed(self.WO))  # output signal

    # ---------------------------------------------------------
    def reset(self):
        """
        Reset register and overflow counters of quantizers
        (but don't reset coefficient quantizers)
        """
        self.Q_mul.resetN()
        # self.Q_acc.resetN()
        # self.Q_O.resetN()
        self.N_over_filt = 0
        self.zi = np.zeros(self.L - 1)

    # ---------------------------------------------------------
    def elaborate(self, platform) -> Module:
        """
        `platform` normally specifies FPGA platform, not needed here.
        """
        m = Module()  # instantiate a module
        ###
        muls = [0] * len(self.b_q)

        src = self.i  # first register is connected to input signal

        i = 0
        for b_q in self.b_q:
            sreg = Signal(signed(self.WI))  # create chain of registers
            m.d.sync += sreg.eq(src)        # with input word length
            src = sreg
            # TODO: keep old data sreg to allow frame based processing (requiring reset)?
            muls[i] = int(b_q)*sreg
            i += 1

        sum_full = Signal(signed(self.W_mul))  # sum of all multiplication products with
        m.d.sync += sum_full.eq(reduce(add, muls))  # full product wordlength

        # requantize from full partial product wordlength to accumulator format
        sum_accu = Signal(signed(self.W_acc))
        m.d.comb += sum_accu.eq(requant(m, sum_full, self.Q_mul.q_dict, self.p['QACC']))

        # requantize from accumulator format to output width
        m.d.comb += self.o.eq(requant(m, sum_accu, self.p['QACC'], self.p['QO']))

        return m   # return result as list of integers


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run widget standalone with
    `python -m pyfda.fixpoint_widgets.fir_df.fir_df_amaranth_mod`
    """
    fb.fil[0]['fx_sim'] = True  # enable fixpoint mode
    # fb.fil[0]['qfrmt'] = 'qint'

    p = {'QCB': {'WI': 2, 'WF': 5, 'w_a_m': 'a',
                'ovfl': 'wrap', 'quant': 'floor', 'N_over': 0},
         'QACC': {'WI': 6, 'WF': 3, 'ovfl': 'wrap', 'quant': 'round'},
         'QI': {'WI': 2, 'WF': 3, 'ovfl': 'sat', 'quant': 'round'},
         'QO': {'WI': 6, 'WF': 3, 'ovfl': 'wrap', 'quant': 'round'}
         }
    
    Q_b = fx.Fixed(p['QCB'])  # quantizer for transversal coeffs
    b_q = quant_coeffs([1, 2, 3, 2, 1], Q_b, out_frmt="qint")
    p.update({'ba': b_q})
    Q_I = fx.Fixed(p['QI'])
    Q_O = fx.Fixed(p['QO'])

    dut = FIR_DF_amaranth_mod(p)
    
    def process():
        # input = stimulus
        output = []
        for i in stimulus:
            yield dut.i.eq(int(i))
            yield Tick()
            output.append((yield dut.o))
        logger.warning(f"in: {stimulus}")
        logger.warning(f"out: {output}")

    sim = Simulator(dut)
    # with Simulator(m) as sim:
    sim.add_clock(1/48000)


    stimulus = Q_I.fixp(np.ones(20), out_frmt='qint')
    sim.add_process(process)
    sim.run()
    # This remembers sreg from last run!
    stimulus = np.zeros(20)
    sim.add_process(process)
    sim.run()