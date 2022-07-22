# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Fixpoint class for calculating direct-form DF1 IIR filter using pyfixp routines
"""
import numpy as np
from numpy.lib.function_base import iterable
import pyfda.filterbroker as fb
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_fix_lib import quant_coeffs

import logging
logger = logging.getLogger(__name__)


# =============================================================================
class IIR_DF1_pyfixp(object):
    """
    Construct fixed point object with parameter dict `p`

    Usage:
    ------
    filt = IIR_DF1(p) # Instantiate fixpoint filter object with parameter dict

    Parameters
    ----------
    p : dict
        Dictionary with quantizer settings with a.o. the following key: value pairs:

        - 'QCB', value: dict with quantizer settings for transversal coefficients

        - 'QCA', value: dict with quantizer settings for recursive coefficients

        - 'QACC', value: dict with accumulator quantizer settings

        - 'q_mul', value: dict with partial product quantizer settings
            currently unused, created from a copy of the QACC dict
    """
    def __init__(self, p):
        self.p = p

        logger.info("Instantiating filter")
        # create various quantizers and initialize / reset them
        self.Q_b = fx.Fixed(self.p['QCB'])  # transversal coeffs.
        self.Q_a = fx.Fixed(self.p['QCA'])  # recursive coeffs
        self.Q_mul = fx.Fixed(self.p['QACC'].copy())  # partial products
        self.Q_acc = fx.Fixed(self.p['QACC'])  # accumulator
        self.Q_O = fx.Fixed(self.p['QO'])  # output

        self.init(p)

    # ---------------------------------------------------------
    def init(self, p, zi_b: iterable = None, zi_a: iterable = None) -> None:
        """
        Initialize filter with parameter dict `p` by initialising all registers
        and quantizers.
        This needs to be done every time quantizers or coefficients are updated.

        Parameters
        ----------
        p : dict
            dictionary with coefficients and quantizer settings (see docstring of
            `__init__()` for details)

        zi_b : array-like
            Initialize `L = len(b) = len(a)` filter registers. Strictly speaking,
             `zi_b[0]` is not a register but the current input value.
            When `len(zi_b) != len(b)`, truncate or fill up with zeros.
            When `zi_b == None`, all registers are filled with zeros.
            When `len(b) != len(a)` throw an error

        zi_a : array-like
            Initialize `L = len(b) - 1` filter registers. Strictly speaking,
             `zi_b[0]` is not a register but the current input value.
            When `len(zi_b) != len(b) - 1`, truncate or fill up with zeros.
            When `zi_b == None`, all registers are filled with zeros.
            When `len(b) != len(a)` throw an error

        Returns
        -------
        None.
        """
        self.p = p  # update parameter dictionary with coefficients etc.

        q_mul = p['QACC'].copy()

        # update the quantizers
        self.Q_b.set_qdict(self.p['QCB'])  # transversal coeffs.
        self.Q_a.set_qdict(self.p['QCA'])  # recursive coeffs
        self.Q_mul.set_qdict(q_mul)  # partial products
        self.Q_acc.set_qdict(self.p['QACC'])  # accumulator
        self.Q_O.set_qdict(self.p['QO'])  # output

        # Quantize coefficients and store them in local attributes
        # This also resets the overflow counters.
        self.a_q = quant_coeffs(fb.fil[0]['ba'][1], self.Q_a, recursive=True)
        self.b_q = quant_coeffs(fb.fil[0]['ba'][0], self.Q_b)

        self.L = max(len(self.b_q), len(self.a_q))  # filter length = number of taps

        self.reset() # reset overflow counters (except coeffs) and registers

        # Initialize filter memory with passed values zi_b, zi_a and fill up with zeros
        # or truncate to filter length L
        if zi_b is not None:
            if len(zi_b) == self.L - 1:
                self.zi_b = zi_b
            elif len(zi_b) < self.L - 1:
                self.zi_b = np.concatenate((zi_b, np.zeros(self.L - 1 - len(zi_b))))
            else:
                self.zi_b = zi_b[:self.L - 1]

        if zi_a is not None:
            if len(zi_a) == self.L - 1:   # use zi_a as it is
                self.zi_a = zi_a
            else:
                logger.warning(f"length of zi_a is {len(zi_a)} != {len(self.L)-1}")
                self.zi_a = np.zeros(self.L - 1)

    # ---------------------------------------------------------
    def reset(self):
        """
        Reset registers and overflow counters of quantizers
        (except for coefficient quant.)
        """
        self.Q_mul.resetN()
        self.Q_acc.resetN()
        self.Q_O.resetN()
        self.N_over_filt = 0
        self.zi_a = np.zeros(self.L - 1)
        self.zi_b = np.zeros(self.L - 1)

    # ---------------------------------------------------------
    def fxfilter(self, x: iterable = None,
                 zi_b: iterable = None, zi_a: iterable = None) -> np.ndarray:
        """
        Calculate quantized IIR filter (direct form 1) response via difference equation
        with quantized coefficient values `self.a_q` and `self.b_q` and quantized
        arithmetics.

        Registers can be initialized by passing `zi_a` and `zi_b`.

        Parameters
        ----------
        x : array of float or float or None
            input value(s) scaled and quantized according to the setting of `p['QI']`
            - When x is a scalar, calculate impulse response with the
                amplitude defined by the scalar.
            - When `x == None`, calculate impulse response with amplitude = 1.

        zi_b : array-like
             initial conditions for transversal registers; when `zi_b == None`,
             the register contents from the last run are used.

        zi_a : array-like
             initial conditions for recursive registers; when `zi_a == None`,
             the register contents from the last run are used.

        Returns
        -------
        yq : ndarray
            The quantized input value(s) as an ndarray of np.float64
            and the same shape as `x` resp. `b` or `a`(impulse response).
        """
        if zi_b is not None:
            if len(zi_b) == self.L - 1:   # use zi_b as it is
                self.zi_b = zi_b
            elif len(zi_b) < self.L - 1:  # append zeros
                self.zi_b = np.concatenate((zi_b, np.zeros(self.L - 1 - len(zi_b))))
            else:                         # truncate zi_b
                self.zi_b = zi_b[:self.L - 1]
                logger.warning("len(zi_b) > len(coeff) - 1, zi_b was truncated")

        if zi_a is not None:
            if len(zi_a) == self.L - 1:   # use zi_a as it is
                self.zi_a = zi_a
            elif len(zi_a) < self.L - 1:  # append zeros
                self.zi_a = np.concatenate((zi_a, np.zeros(self.L - 1 - len(zi_a))))
            else:                         # truncate zi_b
                self.zi_a = zi_a[:self.L - 1]
                logger.warning("len(zi_a) > len(coeff) - 1, zi_a was truncated")

        # initialize quantized partial products and output arrays
        y_q = xb_q = np.zeros(len(x))
        xa_q = np.zeros(self.L - 1)

        # Calculate response by:
        # - feed last output `y_q[k]`` into the recursive register `self.zi_a`
        # - append new stimuli `x` to transversal register state `self.zi_b`
        # - slide a window with length `len(b)` over `self.zi`, starting at position `k`
        #   and multiply it with the coefficients `b`, yielding the partial products x*b
        #   TODO: Doing this for the last len(x) terms should be enough
        # - quantize the partial products x*b and x*a, yielding xb_q and x_aq
        # - accumulate the quantized partial products and quantize result, yielding y_q[k]

        self.zi_b = np.concatenate((self.zi_b, x))

        for k in range(len(x)):
            # partial products xa_q and xb_q at time k, quantized with Q_mul:
            xb_q = self.Q_mul.fixp(self.zi_b[k:k + len(self.b_q)] * self.b_q)
            # append a zero to xa_q to equalize length of xb_q and xa_q
            xa_q = np.append(self.Q_mul.fixp(self.zi_a * self.a_q[1:]), 0)

            # accumulate partial products x_bq and x_aq and quantize them (Q_acc)
            # quantize individual accumulation steps - needed?!
            # y_q[k] = 0.0
            # for i in range(len(self.b_q)):
            #     y_q[k] += self.Q_acc.fixp(xb_q[i] - xa_q[i])

            y_q[k] = self.Q_acc.fixp(np.sum(xb_q) - np.sum(xa_q))
            self.zi_a[1:] = self.zi_a[:-1]  # shift right by one

            # and insert last output value quantized to output format
            self.zi_a[0] = self.Q_O.fixp(y_q[k])

            # logger.warning(f"zi_a = {self.zi_a}\n"
            #                f"zi_b = {self.zi_b}")

        self.zi_b = self.zi_b[-(self.L-1):]  # store last L-1 inputs (i.e. the L-1 registers)

        # Overflows in Q_mul are added to overflows in Q_Acc, then Q_mul is reset
        if self.Q_acc.q_dict['N_over'] > 0 or self.Q_mul.q_dict['N_over'] > 0:
            logger.warning(f"Overflows: N_Acc = {self.Q_acc.q_dict['N_over']}, "
                           f"N_Mul = {self.Q_mul.q_dict['N_over']}")
        self.Q_acc.q_dict['N_over'] += self.Q_mul.q_dict['N_over']
        self.Q_mul.resetN()

        return self.Q_O.fixp(y_q[:len(x)]), self.zi_b, self.zi_a


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run widget standalone with
    `python -m pyfda.fixpoint_widgets.iir_df1.iir_df1_pyfixp`
    """

    p = {'b': [-0.2, 0.2, 0], 'QACC': {'Q': '3.6', 'ovfl': 'wrap', 'quant': 'round'},
         'a': [1, 0, -0.81],
         'QI': {'Q': '1.3', 'ovfl': 'sat', 'quant': 'round'},
         'QO': {'Q': '3.3', 'ovfl': 'sat', 'quant': 'round'}
         }
    dut = IIR_DF1_pyfixp(p)
    x = np.zeros(5)
    x[0] = 1
    y = dut.fxfilter(x=x)
    print(y)
    y = dut.fxfilter(x=np.zeros(5))
    print(y)
