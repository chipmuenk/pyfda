# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Calculate transient response for one frame
"""
# import time
import numpy as np
from numpy import ndarray, pi
import scipy.signal as sig
from scipy.special import sinc, diric

import pyfda.filterbroker as fb
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_sig_lib import angle_zero
from pyfda.libs.pyfda_lib import (
    safe_eval, pprint_log, np_type, calc_ssb_spectrum,
    rect_bl, sawtooth_bl, triang_bl, comb_bl, calc_Hcomplex, safe_numexpr_eval)

from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

import logging
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
def calc_response_frame(self, x: ndarray, N_first: int, init: bool = False) -> ndarray:
    """
    Calculate a data frame of stimulus `x` with a length of `N` samples,
    starting with index `N_first`

    Parameters
    ----------
    x: ndarray
        sequence of data to be filtered

    N_first: int
        index of first data point

    init: bool
        when True, initialize filter with zeros

    Returns
    -------
    y: ndarray
        an array with the same number of response data points as the stimulus
    """
    

    return x
# ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    def calc_response_frame(self, N_first, N_last, zi):
        # calculate one frame with the response
        batch_size = N # Number of samples per batch
        # Array of initial conditions for the SOS filter.
        z = np.zeros((sos.shape[0], 2))
        # Preallocate space for the filtered signal.
        y = np.empty_like(x)
        start = 0
        while start < len(x):
            stop = min(start + batch_size, len(x))
            y[start:stop], z = sosfilt(sos, x[start:stop], zi=z)
            start = stop
        return y, z

if __name__ == "__main__":
    """ Run standalone with `python -m pyfda.plot_widgets.tran.plot_tran_response` """
    import sys

    print(np.arange(100))
    sys.exit()
