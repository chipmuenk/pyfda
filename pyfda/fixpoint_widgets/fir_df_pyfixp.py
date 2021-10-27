# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form DF1 FIR filter
"""
import typing
import numpy as np
from numpy.lib.function_base import iterable
# from pyfda.libs.pyfda_lib import set_dict_defaults, pprint_log

import pyfda.libs.pyfda_fix_lib as fx

################################

import logging
logger = logging.getLogger(__name__)

classes = {'FIR_DF_wdg': 'FIR_DF'}  #: Dict containing widget class name : display name


class FIR_DF_pyfixp(object):
    """
    This class describes a direct form FIR fixpoint filter implemented with the `pyfixp`
    fixpoint library.

    Usage
    =====
    > Q = FIR_DF(b, q_mul, q_acc) # Instantiate fixpoint filter object
    > x_bq = self.Q_mul.filt(x, bq)

    The fixpoint object has two different quantizers:
    - b is an array with coefficients
    - q_mul describes requanitization after coefficient multiplication
      ('quant' and 'sat' can both be set to 'none' if there is none)
    - q_acc describes requantization after each summation in the accumulator
            (resp. in the common summation point)
    """
    def __init__(self, b: iterable, q_acc: dict, q_mul: dict = None) -> None:
        """
        Initialize fixpoint object with coefficients and quantizer dict(s)

        Parameters
        ----------
        b : array-like
            filter coefficients

        q_acc : dict
                dictionary with quantizer settings for the accumulator

        q_mul : dict
                dictionary with quantizer settings for the partial products (optional)

        Returns
        -------
        None
        """
        if q_mul is None:
            q_mul = {'Q': '0.15', 'ovfl': 'none', 'quant': 'none'}
        self.Q_acc = fx.Fixed(q_acc)  # create quantizer for accumulator
        self.Q_mul = fx.Fixed(q_mul)  # create quantizer for partial product
        self.N_over_filt = 0          # total number of overflows

        self.b = b  # coefficients
        self.L = len(self.b)  # filter length
        self.xi = np.zeros(self.L)  # initialize the filter registers

    # --------------------------------------------------------------------------
    def reset(self) -> None:
        """
        Reset all overflow counters

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.Q_mul.resetN()  # reset overflow counter of Q_mul
        self.Q_acc.resetN()  # reset overflow counter of Q_acc
        self.N_over_filt = 0  # total number of overflows in filter

        return

    # --------------------------------------------------------------------------
    def update_filter(self, b: iterable) -> None:
        """
        Load filter with new set of coefficients

        Parameters
        ----------
        b : array-like
            filter coefficients. Length must be identical to the coefficient
            set used during initialization

        Returns
        -------
        None

        """
        if len(b) == len(self.b):
            self.b = b
        else:
            raise IndexError("Number of coefficients differs from initialization!")
        return

    # --------------------------------------------------------------------------
    def lfilter(self, b: iterable, x) -> np.ndarray:
        """
        Calculate FIR filter (direct form) response via difference equation with
        quantization. The filter is initialized with zeros.

        This method is equivalent to `scipy.signal.lfilter()`.
        """

        return self.lfilter_zi(b=b, x=x, zi=np.zeros(len(b)))[0]

    # --------------------------------------------------------------------------
    def lfilter_zi(self, b: iterable, x: iterable, zi: iterable = None)\
            -> typing.Tuple[np.ndarray, np.ndarray]:
        """
        TODO: When len(x) < len(b), only zeros are returned because the for loop
        is never executed

        Calculate FIR filter (direct form) response via difference equation with
        quantization. Registers can be initialized with `zi`.

        This method is equivalent to `scipy.signal.lfilter_zi()`.

        Parameters
        ----------
        x :  scalar or array-like
             input value(s)

        b :  array-like
             filter coefficients; when None, the old coefficients are left untouched

        zi : array-like
             initial conditions; when `zi == None`, instance attributes are reused

        Returns
        -------
        yq : ndarray
            The quantized input value(s) as a scalar or an ndarray with np.float64.
            and the same shape as x.

        zi : ndarray
            The final filter state, same length as `b`
        """

        if b is not None:  # update coefficients
            if len(b) == len(self.b):
                self.b = b
            else:
                raise IndexError("Number of coefficients differs from initialization!")

        if zi is not None:  # initialize filter memory and fill up with zeros
            if len(zi) == self.L:
                self.xi = zi
            elif len(zi) < self.L:
                self.xi = np.concatenate((zi, np.zeros(self.L - len(len(zi)))))
            else:
                self.xi = zi[:self.L]
                logger.warning("len(zi) > len(b) - 1, zi was truncated")

        # initialize quantized partial products and output arrays
        y_q = xb_q = np.zeros(len(x))

        # Calculate response by:
        # - append new stimuli `x` to register state `self.xi`
        # - slide a window with length `len(b)` over `self.xi`, starting at position `k`
        #   and multiply it with the coefficients `b`, yielding the partial products x*b
        #   TODO: Doing this for the last len(x) terms should be enough
        # - quantize the partial products x*b, yielding xb_q
        # - sum up the quantized partial products, yielding result y[k]
        # - quantize result, yielding y_q[k]

        self.xi = np.concatenate((self.xi, x))

        for k in range(len(x)):
            # weighted state-vector x at time k:
            xb_q = self.Q_mul.fixp(
                self.xi[k:k + len(self.b)] * self.b)
            # sum up x_bq to get accu[k]
            y_q[k] = self.Q_acc.fixp(np.sum(xb_q))

        self.xi = self.xi[-self.L:]  # store last L inputs (i.e. the L registers)
        self.N_over_filt = self.Q_acc.N_over + self.Q_mul.N_over

        return y_q[:len(x)], self.xi


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.fixpoint_widgets.fir_df_pyfixp` """

    dut = FIR_DF_pyfixp(b=[1, 1, 1, 1, 1],
                        q_acc={'Q': '5.0', 'ovfl': 'wrap', 'quant': 'round'})

    stim = np.arange(100)

    xq = dut.lfilter(b=None, x=stim[:10])
    print(xq)
