# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Fixpoint class for calculating direct-form DF1 FIR filter using nMigen library
"""

import numpy as np
from numpy.lib.function_base import iterable
from pyfda.libs.pyfda_lib import pprint_log
from pyfda.fixpoint_widgets.fixpoint_helpers_nmigen import requant

from functools import reduce
from operator import add

# from nmigen import *
# from nmigen.back import verilog
from nmigen import Signal, signed, Elaboratable, Module
from nmigen.sim import Simulator, Tick  # , Delay, Settle
# from nmigen.build.plat import Platform
# from nmigen.hdl import ast, dsl, ir
# from nmigen.sim.core import Simulator, Tick, Delay
# from nmigen.build import Platform
# from nmigen.back.pysim import Simulator, Delay, Settle

import logging
logger = logging.getLogger(__name__)

################################

#  Dict containing {widget class name : display name}
classes = {'FIR_DF_nmigen_ui': 'FIR_DF (nmigen)'}


###############################################################################
class FIR_DF_nmigen(Elaboratable):
    """
    A synthesizable nMigen FIR filter in Direct Form.

    Parameters
    ----------
    p : dict
        Dictionary with coefficients and quantizer settings with a.o.
        the following keys:

        - 'b', values: array-like, coefficients as integers

        - 'QA' value: dict with quantizer settings for the accumulator

        - 'q_mul' : dict with quantizer settings for the partial products
           optional, 'quant' and 'sat' are both be set to 'none' if there is none
        Dictionary with quantizer settings

    Attributes
    ----------
    i : Signal, in
        Input to the filter with  width `self.p['QI']['W']`

    o : Signal, out
        Output from the filter with width self.p['QO']['W']`
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
        self.p = p  # fb.fil[0]['fxq']  # parameter dictionary with coefficients etc.
        # ------------- Define I/Os --------------------------------------
        self.WI = p['QI']['WI'] + p['QI']['WF'] + 1  # total input word length
        self.WO = p['QO']['WI'] + p['QO']['WF'] + 1  # total output word length
        self.i = Signal(signed(self.WI))  # input signal
        self.o = Signal(signed(self.WO))  # output signal

    # ---------------------------------------------------------
    def elaborate(self, platform) -> Module:
        """
        `platform` normally specifies FPGA platform, not needed here.
        """
        m = Module()  # instantiate a module
        ###
        muls = [0] * len(self.p['b'])
        WACC = p['QACC']['WI'] + p['QACC']['WF'] + 1  # total accu word length

        DW = int(np.ceil(np.log2(len(self.p['b']))))  # word growth
        # word format for sum of partial products b_i * x_i
        QP = {'WI': self.p['QI']['WI'] + self.p['QCB']['WI'] + DW,
              'WF': self.p['QI']['WF'] + self.p['QCB']['WF']}
        WP = QP['WI'] + QP['WF'] + 1
        # QP.update({'W': QP['WI'] + QP['WF'] + 1})

        src = self.i  # first register is connected to input signal

        i = 0
        for b in self.p['b']:
            sreg = Signal(signed(self.WI))  # create chain of registers
            m.d.sync += sreg.eq(src)        # with input word length
            src = sreg
            # TODO: keep old data sreg to allow frame based processing (requiring reset)
            muls[i] = int(b)*sreg
            i += 1

        # logger.debug(f"b = {pprint_log(self.p['b'])}\nW(b) = {self.p['QCB']['W']}")

        sum_full = Signal(signed(WP))  # sum of all multiplication products with
        m.d.sync += sum_full.eq(reduce(add, muls))  # full product wordlength

        # rescale from full product wordlength to accumulator format
        sum_accu = Signal(signed(WACC))
        m.d.comb += sum_accu.eq(requant(m, sum_full, QP, self.p['QA']))

        # rescale from accumulator format to output width
        m.d.comb += self.o.eq(requant(m, sum_accu, self.p['QA'], self.p['QO']))

        return m   # return result as list of integers


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run module standalone with
        `python -m pyfda.fixpoint_widgets.fir_df.fir_df_nmigen`
    """
    p = {'b': [1, 2, 3, 2, 1],
         'QA': {'WI': 8, 'WF': 3, 'W': 18, 'ovfl': 'wrap', 'quant': 'round'},
         'QI': {'WI': 2, 'WF': 3, 'ovfl': 'sat', 'quant': 'round', 'W': 6},
         'QO': {'WI': 5, 'WF': 3, 'ovfl': 'wrap', 'quant': 'round', 'W': 9},
         'QCB': {'WI': 5, 'WF': 3, 'ovfl': 'wrap', 'quant': 'round', 'W': 9}
         }
    dut = FIR_DF_nmigen(p)

    def process():
        # input = stimulus
        output = []
        for i in np.ones(20):
            yield dut.i.eq(int(i))
            yield Tick()
            output.append((yield dut.o))
        print(output)

    sim = Simulator(dut)
    # with Simulator(m) as sim:

    sim.add_clock(1/48000)
    sim.add_process(process)
    sim.run()
