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

import logging
logger = logging.getLogger(__name__)


# =============================================================================
class FIR_DF_pyfixp(object):
    """
    Construct fixed point object with parameter dict `p`

    Usage:
    ------
    filt = FIR_DF(p) # Instantiate fixpoint filter object with parameter dict

    Parameters
    ----------
    p : dict
        Dictionary with coefficients and quantizer settings with a.o.
        the following keys : values

        - 'b', value: array of coefficients as floats, scaled as `WI:WF`

        - 'QACC', value: dict with quantizer settings for the accumulator

        - 'q_mul', value: dict with quantizer settings for the partial products
           optional, 'quant' and 'sat' are both set to 'none' if there is none
    """
    def __init__(self, p):
        self.p = p

        logger.info("Instantiating filter")
        # create various quantizers and initialize / reset them
        self.Q_b = fx.Fixed(self.p['QCB'])  # transversal coeffs
        self.Q_mul = fx.Fixed(self.p['QACC'].copy())  # partial products
        self.Q_acc = fx.Fixed(self.p['QACC'])  # accumulator
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
        self.p = p  # parameter dictionary with coefficients etc.

        q_mul = p['QACC'].copy()

        # update the quantizers
        self.Q_b.set_qdict(self.p['QCB'])  # transversal coeffs.s
        self.Q_mul.set_qdict(q_mul)  # partial products
        self.Q_acc.set_qdict(self.p['QACC'])  # accumulator
        self.Q_O.set_qdict(self.p['QO'])  # output

        # Quantize coefficients and store them in local attributes
        # This also resets the overflow counters.
        self.b_q = quant_coeffs(fb.fil[0]['ba'][0], self.Q_b)

        self.L = len(self.b_q)  # filter length = number of taps

        self.reset() # reset overflow counters (except coeffs) and registers

        # Initialize filter memory with passed values zi and fill up with zeros
        # or truncate to filter length L
        if zi is not None:
            if len(zi) == self.L - 1:
                self.zi = zi
            elif len(zi) < self.L - 1:
                self.zi = np.concatenate((zi, np.zeros(self.L - 1 - len(zi))))
            else:
                self.zi = zi[:self.L - 1]

    # ---------------------------------------------------------
    def reset(self):
        """
        Reset register and overflow counters of quantizers
        (but don't reset coefficient quantizers)
        """
        self.Q_mul.resetN()
        self.Q_acc.resetN()
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
        if zi is not None:
            if len(zi) == self.L - 1:   # use zi as it is
                self.zi = zi
            elif len(zi) < self.L - 1:  # append zeros
                self.zi = np.concatenate((zi, np.zeros(self.L - 1 - len(zi))))
            else:                       # truncate zi
                self.zi = zi[:self.L - 1]
                logger.warning("len(zi) > len(b) - 1, zi was truncated")

        # initialize quantized partial products and output arrays
        y_q = xb_q = np.zeros(len(x))

        # Calculate response by:
        # - append new stimuli `x` to register state `self.zi`
        # - slide a window with length `len(b)` over `self.zi`, starting at position `k`
        #   and multiply it with the coefficients `b`, yielding the partial products x*b
        #   TODO: Doing this for the last len(x) terms should be enough
        # - quantize the partial products x*b, yielding xb_q
        # - accumulate the quantized partial products and quantize result, yielding y_q[k]

        self.zi = np.concatenate((self.zi, x))

        for k in range(len(x)):
            # partial products xb_q at time k, quantized with Q_mul:
            xb_q = self.Q_mul.fixp(self.zi[k:k + self.L] * self.b_q)
            # accumulate x_bq to get accu[k]
            y_q[k] = self.Q_acc.fixp(np.sum(xb_q))

        self.zi = self.zi[-(self.L-1):]  # store last L-1 inputs (i.e. the L-1 registers)

        # Overflows in Q_mul are added to overflows in Q_Acc, then Q_mul is reset
        if self.Q_acc.q_dict['N_over'] > 0 or self.Q_mul.q_dict['N_over'] > 0:
            logger.warning(f"Overflows: N_Acc = {self.Q_acc.q_dict['N_over']}, "
                           f"N_Mul = {self.Q_mul.q_dict['N_over']}")

        self.Q_acc.q_dict['N_over'] = self.Q_acc.q_dict['N_over'] + self.Q_mul.q_dict['N_over']
        self.Q_mul.resetN()

        return self.Q_O.fixp(y_q[:len(x)]), self.zi


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """
    Run widget standalone with
    `python -m pyfda.fixpoint_widgets.fir_df.fir_df_pyfixp`
    """

    p = {'b': [1, 2, 3, 2, 1], 'QACC': {'Q': '4.3', 'ovfl': 'wrap', 'quant': 'round'},
         'QI': {'Q': '2.3', 'ovfl': 'sat', 'quant': 'round'},
         'QO': {'Q': '5.3', 'ovfl': 'wrap', 'quant': 'round'}
         }
    dut = FIR_DF_pyfixp(p)
    x = np.ones(4)
    y = dut.fxfilter(x=x)
    print(y)
    y = dut.fxfilter(x=np.zeros(5))
    print(y)
