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
import numpy as np
from numpy.lib.function_base import iterable
import pyfda.filterbroker as fb
# from pyfda.libs.pyfda_lib import pprint_log
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_fix_lib import quant_coeffs

from pyfda.libs.pyfda_fix_lib_amaranth import requant

from functools import reduce
from operator import add

# from amaranth import *
from amaranth.back import verilog
from amaranth import Signal, signed, Elaboratable, Module
from amaranth.sim import Simulator, Tick  # , Delay, Settle

import pyfda.fixpoint_widgets.fir_df.fir_df_amaranth_mod as mod

import logging
logger = logging.getLogger(__name__)


# =============================================================================
class FIR_DF_amaranth(object):
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
        the following key : value pairs:

        - 'QCB', value: array of coefficients as floats, scaled as `WI:WF`

        - 'QACC', value: dict with quantizer settings for the accumulator

        - 'q_mul', value: dict with quantizer settings for the partial products
           optional, 'quant' and 'sat' are both set to 'none' if there is none
    """
    def __init__(self, p):

        logger.info("Instantiating filter")
        self.p = p  # parameter dictionary with coefficients etc.
        self.Q_b = fx.Fixed(self.p['QCB'])  # transversal coeffs
        # self.Q_mul = fx.Fixed(self.p['QACC'].copy())  # partial products
        # self.Q_acc = fx.Fixed(self.p['QACC'])  # accumulator
        self.Q_O = fx.Fixed(self.p['QO'])  # output
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
        # Do not initialize filter unless fixpoint mode is active
        if not fb.fil[0]['fx_sim']:
            return

        b_q = quant_coeffs(fb.fil[0]['ba'][0], self.Q_b, out_frmt="qint")
        self.L = len(b_q)

        self.reset()

        # Unpack p and coeff. dict in new dict without modifying p
        d = {**p, **{'ba': b_q}}  # unpack p and coeff. dict in new dict without
        # d = p | {'ba': b_q}  # python 3.9+ only
        self.mod = mod.FIR_DF_amaranth_mod(d)

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

        self.sim = Simulator(self.mod)
        # with Simulator(m) as sim:
        self.sim.add_clock(1/48000)

    # ---------------------------------------------------------
    def process(self):
        """
        Amaranth process, apply stimuli via input `mod.i` from list `self.input`
        and collect filter outputs from `mod.o` in list `self.output`
        """
        self.output = []
        for i in self.input:
            yield self.mod.i.eq(int(i))
            yield Tick()
            self.output.append((yield self.mod.o))

    # ---------------------------------------------------------
    def reset(self):
        """
        Reset register and overflow counters of quantizers
        (but don't reset coefficient quantizers)
        """
        self.Q_O.resetN()
        self.N_over_filt = 0
        self.zi = np.zeros(self.L - 1)

    # ---------------------------------------------------------
    def fxfilter(self, x: iterable = None, zi: iterable = None) -> np.ndarray:
        """
        Calculate FIR filter (direct form) response via difference equation with
        quantization. Registers can be initialized with `zi`.

        Parameters
        ----------
        x : array of float or float or None
            input value(s) scaled and quantized according to the setting of `p['QI']`
            and fb.fil[0]['qfrmt']
            - When x is a scalar, calculate impulse response with the
                amplitude defined by the scalar.
            - When `x == None`, calculate impulse response with amplitude = 1.

        zi : array-like
             initial conditions for filter memory; when `zi == None`, register contents
             from last run are used.

        Returns
        -------
        yq : ndarray
            The quantized input value(s) as an ndarray of np.float64
            and the same shape as `x` resp. `b` (impulse response).
        """

        # -------------------------
        if zi is not None:
            if len(zi) == self.L - 1:   # use zi as it is
                self.zi = zi
            elif len(zi) < self.L - 1:  # append zeros
                self.zi = np.concatenate((zi, np.zeros(self.L - 1 - len(zi))))
            else:                       # truncate zi
                self.zi = zi[:self.L - 1]
                logger.warning("len(zi) > len(b) - 1, zi was truncated")

        # store last L-1 inputs (i.e. the L-1 registers)
        self.zi = np.concatenate((self.zi, x))[-(self.L-1):]

        # Calculate response by:
        # - append new stimuli `x` to register state `self.zi`
        # - slide a window with length `len(b)` over `self.zi`, starting at position `k`
        #   and multiply it with the coefficients `b`, yielding the partial products x*b
        #   TODO: Doing this for the last len(x) terms should be enough
        # - quantize the partial products x*b, yielding xb_q
        # - accumulate the quantized partial products and quantize result, yielding y_q[k]

        # convert stimulus to integer
        if fb.fil[0]['qfrmt'] == 'qfrac':
            self.input = x * (1 << self.p['QI']['WF'])
        else:
            self.input = x
        # logger.warning(f"stim = {self.input}")
        self.sim.add_process(self.process)
        self.sim.run()

        # Currently doesn't work, output signal is quantized afterwards, resetting 'N_over'
        # fb.fil[0]['fxq']['QO']['N_over'] = 13  # doesn't work, output signal is quantized

        # TODO: Pass Quantizer instead of quantizer dict to requant etc. to update overflow counter
        # logger.warning(f"y = {self.Q_O.fixp(self.output, in_frmt='qint', out_frmt=fb.fil[0]['qfrmt'])}")

        return self.Q_O.fixp(self.output, in_frmt='qint', out_frmt=fb.fil[0]['qfrmt']), self.zi


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run widget standalone with
    `python -m pyfda.fixpoint_widgets.fir_df.fir_df_amaranth`
    `python -m pyfda.fixpoint_widgets.fir_df.fir_df_amaranth.FIR_DF_amaranth_mod`
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
    Q_I = fx.Fixed(p['QI'])
    Q_O = fx.Fixed(p['QO'])

    p.update({'ba': b_q})

    dut = FIR_DF_amaranth(p)
    print(dut.fxfilter(Q_I.fixp(np.ones(20), out_frmt='qint')))
    print(dut.fxfilter(Q_I.fixp(np.zeros(20), out_frmt='qint')))

