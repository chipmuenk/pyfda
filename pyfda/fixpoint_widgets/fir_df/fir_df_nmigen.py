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
        Dictionary with quantizer settings

    Attributes
    ----------
    i : Signal, in
        Input to the filter with  width `self.p['QI']['W']`

    o : Signal, out
        Output from the filter with width self.p['QO']['W']`
    """
    def __init__(self, p):
        self.p = p  # fb.fil[0]['fxqc']  # parameter dictionary with coefficients etc.
        # ------------- Define I/Os as signed --------------------------------------
        self.i = Signal(signed(self.p['QI']['W']))  # input signal
        self.o = Signal(signed(self.p['QO']['W']))  # output signal
        pass

    # def ports(self):
    #     return [self.i, self.o]

    def elaborate(self, platform) -> Module:
        """
        `platform` normally specifies FPGA platform, not needed here.
        """
        m = Module()  # instantiate a module
        ###
        muls = []    # list for partial products b_i * x_i
        DW = int(np.ceil(np.log2(len(self.p['b']))))  # word growth
        # word format for sum of partial products b_i * x_i
        QP = {'WI': self.p['QI']['WI'] + self.p['QCB']['WI'] + DW,
              'WF': self.p['QI']['WF'] + self.p['QCB']['WF']}
        QP.update({'W': QP['WI'] + QP['WF'] + 1})

        src = self.i  # first register is connected to input signal

        for b in self.p['b']:
            sreg = Signal(signed(self.p['QI']['W']))  # create chain of registers
            m.d.sync += sreg.eq(src)            # with input word length
            src = sreg
            muls.append(int(b)*sreg)

        logger.debug("b = {0}\nW(b) = {1}".format(
            pprint_log(self.p['b']), self.p['QCB']['W']))

        # saturation logic doesn't make much sense with a FIR filter, this is
        # just for demonstration
        sum_full = Signal(signed(QP['W']))
        m.d.sync += sum_full.eq(reduce(add, muls))  # sum of multiplication products

        # rescale from full product format to accumulator format
        sum_accu = Signal(signed(self.p['QA']['W']))
        m.d.comb += sum_accu.eq(requant(m, sum_full, QP, self.p['QA']))

        # rescale from accumulator format to output width
        m.d.comb += self.o.eq(requant(m, sum_accu, self.p['QA'], self.p['QO']))

        return m


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
