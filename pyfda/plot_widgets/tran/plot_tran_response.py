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
from numpy import ndarray
import scipy.signal as sig

import pyfda.filterbroker as fb
# from pyfda.libs.pyfda_sig_lib import angle_zero

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
def calc_response_frame(self, x: ndarray, zi, N_first: int, init: bool = False)\
        -> ndarray:
    """
    Calculate the response for a data frame of stimulus `x`,
    starting with index `N_first`

    Parameters
    ----------
    x: ndarray
        sequence of data to be filtered

    zi: ndarray
        filter state for initialization

    N_first: int
        index of first data point

    init: bool
        when True, initialize filter with zeros

    Returns
    -------
    y: ndarray
        an array with the same number of response data points as the stimulus
    """

# ------------------------------------------------------------------------------
    #     # Preallocate space for the filtered signal?
    #     y = np.empty_like(x)

    if len(self.sos) > 0:  # has second order sections
        y, z = sig.sosfilt(self.sos, x, zi=zi)
    else:  # no second order sections or antiCausals for current filter
        y, z = sig.lfilter(self.bb, self.aa, x, zi=zi)

    y = np.real_if_close(y, tol=1e3)  # tol specified in multiples of machine eps

    return y, z


if __name__ == "__main__":
    """ Run standalone with `python -m pyfda.plot_widgets.tran.plot_tran_response` """
    import sys

# TODO: just a dummy test right now
    print(np.arange(100))
    sys.exit()
