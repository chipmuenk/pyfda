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
import pyfda.libs.pyfda_fix_lib as fx
from pyfda.libs.pyfda_sig_lib import angle_zero
# from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

import logging
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
def calc_response_frame(self, x: ndarray, zi, N_first: int, init: bool = False) -> ndarray:
    """
    Calculate the response for a data frame of stimulus `x`,
    starting with index `N_first`

    Parameters
    ----------
    x: ndarray
        sequence of data to be filtered
        
    zi: ndarray
        filter memory

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

    # ------------------------------------------------------------------------------
    # def calc_sos_frame(self, N_first, N_last, zi):
    #     # calculate one frame with the response
    #     batch_size = N # Number of samples per batch
    #     # Array of initial conditions for the SOS filter.
    #     z = np.zeros((sos.shape[0], 2))
    #     # Preallocate space for the filtered signal.
    #     y = np.empty_like(x)
    #     start = 0
    #     while start < len(x):
    #         stop = min(start + batch_size, len(x))
    #         y, z = sig.sosfilt(sos, x, zi=z)
    #     return y, z
    
    bb = np.asarray(fb.fil[0]['ba'][0])
    aa = np.asarray(fb.fil[0]['ba'][1])

    logger.debug("Coefficient area = {0}".format(np.sum(np.abs(bb))))
    # has_sos = 'sos' in fb.fil[0]
    sos = np.asarray(fb.fil[0]['sos'])

    if len(sos) > 0:  # has second order sections
        # zi = sig.sosfilt_zi(sos)
        y, z = sig.sosfilt(sos, x, zi=zi)
        logger.warning(y.shape)
        logger.warning(z.shape)
#    elif antiCausal:
#        y = sig.filtfilt(self.bb, self.aa, x, -1, None)
    else:  # no second order sections or antiCausals for current filter
        # zi = sig.lfilter_zi(bb, aa)
        y, z = sig.lfilter(bb, aa, x, zi=zi)

    if self.stim_wdg.ui.stim == "step" and self.stim_wdg.ui.chk_step_err.isChecked():
        dc = sig.freqz(bb, aa, [0])  # DC response of the system
        # subtract DC (final) value from response
        y[max(N_first, self.ui.stim_wdg.T1_int):] = \
            y[max(N_first, self.stim_wdg.T1_int):] - abs(dc[1])

    y = np.real_if_close(y, tol=1e3)  # tol specified in multiples of machine eps

    return y, z


if __name__ == "__main__":
    """ Run standalone with `python -m pyfda.plot_widgets.tran.plot_tran_response` """
    import sys

    print(np.arange(100))
    sys.exit()
