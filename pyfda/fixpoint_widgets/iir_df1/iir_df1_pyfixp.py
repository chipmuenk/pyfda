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
import pyfda.libs.pyfda_fix_lib as fx

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
        Dictionary with coefficients and quantizer settings with a.o.
        the following keys : values

        - 'b', value: array of transversal coefficients as floats, scaled as `WI:WF`

        - 'a', value: array of recursive coefficients as floats, scaled as `WI:WF`

        - 'QA', value: dict with quantizer settings for the accumulator

        - 'q_mul', value: dict with quantizer settings for the partial products
           optional, 'quant' and 'sat' are both be set to 'none' if there is none
    """
    def __init__(self, p):
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
        self.p = p  # parameter dictionary with coefficients etc.

        # When p'[q_mul'] is undefined, use accumulator quantization settings:
        if 'q_mul' not in self.p or self.p['q_mul'] is None:
            q_mul = p['QA'].copy()
        else:
            q_mul = p['q_mul']

        self.b = self.p['b']  # transversal coefficients
        self.a = self.p['a']  # recursive coefficients
        self.L = max(len(self.b), len(self.a))  # filter length = number of taps
        # create various quantizers
        self.Q_mul = fx.Fixed(q_mul)  # partial products
        self.Q_acc = fx.Fixed(self.p['QA'])  # accumulator
        self.Q_O = fx.Fixed(self.p['QO'])  # output
        self.N_over_filt = 0  # initialize overflow counter TODO: not used yet?

        if zi_b is None:
            self.zi_b = np.zeros(self.L - 1)
        # initialize filter memory and fill up with zeros (except for first element
        # which is the input)
        else:
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
        else:
            self.zi_a = np.zeros(self.L - 1)

    # ---------------------------------------------------------
    def reset(self):
        """ reset overflow counters of quantizers """
        self.Q_mul.resetN()
        self.Q_acc.resetN()
        self.Q_O.resetN()
        self.N_over_filt = 0

    # ---------------------------------------------------------
    def fxfilter(self, x: iterable = None, b: iterable = None, a: iterable = None,
                 zi_b: iterable = None, zi_a: iterable = None) -> np.ndarray:
        """
        Calculate IIR filter (direct form 1) response via difference equation with
        quantization. Registers can be initialized with `zi`.

        Parameters
        ----------
        x : array of float or float or None
            input value(s) scaled and quantized according to the setting of `p['QI']`
            - When x is a scalar, calculate impulse response with the
                amplitude defined by the scalar.
            - When `x == None`, calculate impulse response with amplitude = 1.

        b :  array-like
             transversal filter coefficients as quantized floats scaled as `WI.WF`
             When `b == None`, the old coefficients are left untouched

        a :  array-like
             recursive filter coefficients as quantized floats scaled as `WI.WF`
             When `a == None`, the old coefficients are left untouched

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
        coeff_changed = False

        if b is not None and np.any(b != self.b):  # update transversal coefficients
            self.p['b'] = self.b = b
            coeff_changed = True

        if a is not None and np.any(a != self.a):  # update recursive coefficients
            self.p['a'] = self.a = a
            coeff_changed = True

        if coeff_changed:
            self.init(self.p)  # reset filter

        # When `zi_b` is specified, initialize filter memory with it and pad with zeros
        # When `zi_b == None`, use register contents from last run
        if zi_b is not None:
            if len(zi_b) == self.L - 1:   # use zi_b as it is
                self.zi_b = zi_b
            elif len(zi_b) < self.L - 1:  # append zeros
                self.zi_b = np.concatenate((zi_b, np.zeros(self.L - 1 - len(zi_b))))
            else:                       # truncate zi_b
                self.zi_b = zi_b[:self.L - 1]
                logger.warning("len(zi_b) > len(coeff) - 1, zi_b was truncated")

        if zi_a is not None:
            if len(zi_a) == self.L - 1:   # use zi_a as it is
                self.zi_a = zi_a

        if np.isscalar(x):
            A = x
            x = np.zeros(len(self.b))
            x[0] = A
        elif x is None:  # calculate impulse response
            x = np.zeros(len(self.b))
            x[0] = 1
        # else:  # don't change x, it is integer anyway
        #    x = x

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
            # weighted state-vector x at time k:
            xb_q = self.Q_mul.fixp(self.zi_b[k:k + len(self.b)] * self.b)
            xa_q = self.Q_mul.fixp(self.zi_a * self.a[1:])
            # sum up x_bq and x_aq to get accu[k]
            y_q[k] = self.Q_acc.fixp(np.sum(xb_q) - np.sum(xa_q))
            self.zi_a[1:] = self.zi_a[:-1]  # shift right by one
            self.zi_a[0] = y_q[k] # and insert last output value

        self.zi_b = self.zi_b[-(self.L-1):]  # store last L-1 inputs (i.e. the L-1 registers)
        # Overflows in Q_mul are added to overflows in QA
        logger.warning(f"{self.Q_acc.q_dict['N_over']} - {self.Q_mul.q_dict['N_over']}")
        self.Q_acc.q_dict['N_over'] += self.Q_mul.q_dict['N_over']
        self.Q_mul.resetN()

        return self.Q_O.fixp(y_q[:len(x)]), self.zi_b, self.zi_a


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run widget standalone with
    `python -m pyfda.fixpoint_widgets.iir_df1.iir_df1_pyfixp`
    """

    p = {'b': [-0.2, 0.2, 0], 'QA': {'Q': '3.6', 'ovfl': 'wrap', 'quant': 'round'},
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
