# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for plotting impulse and general transient responses
"""
# import time
from pyfda.libs.compat import QWidget, pyqtSignal, QTabWidget, QVBoxLayout
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

from pyfda.plot_widgets.tran.plot_tran_stim_ui import Plot_Tran_Stim_UI

import logging
logger = logging.getLogger(__name__)


class Plot_Tran_Stim(QWidget):
    """
    Construct a widget for plotting impulse and general transient responses
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing, e.g. when stimulus has been calculated
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None):
        super(Plot_Tran_Stim, self).__init__(parent)

        self.ACTIVE_3D = False
        self.ui = Plot_Tran_Stim_UI(self)  # create the UI part with buttons etc.

        # initial settings
        self.needs_calc = True   # flag whether plots need to be recalculated
        self.needs_redraw = [True] * 2  # flag which plot needs to be redrawn
        self.error = False

        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from
        - the navigation toolbars (time and freq.)
        - local widgets (impz_ui) and
        - plot_tab_widgets() (global signals)
        """

        logger.warning("SIG_RX - needs_calc: {0} | vis: {1}\n{2}"
                       .format(self.needs_calc, self.isVisible(), pprint_log(dict_sig)))

    def _construct_UI(self):
        """
        Instantiate the UI of the widget.
        """
        self.main_wdg = QWidget()
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.ui.wdg_stim)
        layVMain.setContentsMargins(*params['mpl_margins'])

        self.ui.sig_tx.connect(self.sig_tx)  # relay UI events further up
        self.sig_rx.connect(self.ui.sig_rx)  # ... and the other way round

        self.setLayout(layVMain)

# ------------------------------------------------------------------------------
    def calc_stimulus_block(self, N_first: int, N_last: int) -> ndarray:
        """
        Calculate a data block of stimulus `x` with a length of `N_last - N_first`
        samples.
        
        Parameters
        ----------
        N_first: int
            number of first data point
            
        N_last: int
            number of last data point
            
        Returns
        -------
        x: ndarray
            an array with `N_last - N_first` stimulus data points
        """
        N = N_last - N_first
        n = N_first + np.arange(N)
        # use radians for angle internally
        phi1 = self.ui.phi1 / 180 * pi
        phi2 = self.ui.phi2 / 180 * pi
        # T_S = fb.fil[0]['T_S']
        # calculate index from T1 entry for creating stimulus vectors, shifted
        # by T1. Limit the value to N_last - 1.
        self.T1_int = min(int(np.round(self.ui.T1)), N_last-1)

        # calculate stimuli x[n] ==============================================
        self.H_str = ''
        self.title_str = ""

        if self.ui.stim == "none":
            x = np.zeros(N)
            self.title_str = r'Zero Input System Response'
            self.H_str = r'$h_0[n]$'  # default

        # ----------------------------------------------------------------------
        elif self.ui.stim == "dirac":
            if np_type(self.ui.A1) == complex:
                A_type = complex
            else:
                A_type = float

            x = np.zeros(N, dtype=A_type)
            x[self.T1_int] = self.ui.A1  # create dirac impulse as input signal
            self.title_str = r'Impulse Response'
            self.H_str = r'$h[n]$'  # default

        # ----------------------------------------------------------------------
        elif self.ui.stim == "sinc":
            x = self.ui.A1 * sinc(2 * (n - self.ui.T1) * self.ui.f1)\
                + self.ui.A2 * sinc(2 * (n - self.ui.T2) * self.ui.f2)
            self.title_str += r'Sinc Impulse '

        # ----------------------------------------------------------------------
        elif self.ui.stim == "gauss":
            x = self.ui.A1 * sig.gausspulse(
                    (n - self.ui.T1), fc=self.ui.f1, bw=self.ui.BW1) +\
                self.ui.A2 * sig.gausspulse(
                    (n - self.ui.T2), fc=self.ui.f2, bw=self.ui.BW2)
            self.title_str += r'Gaussian Impulse '

        # ----------------------------------------------------------------------
        elif self.ui.stim == "rect":
            n_start = int(np.floor((N - self.ui.TW1)/2 - self.ui.T1))
            n_min = max(n_start, 0)
            n_max = min(n_start + self.ui.TW1, N)
            self.title_str += r'Rect Impulse '
            x = self.ui.A1 * np.where((n > n_min) & (n <= n_max), 1, 0)

        # ----------------------------------------------------------------------
        elif self.ui.stim == "step":
            x = self.ui.A1 * np.ones(N)  # create step function
            x[0:self.T1_int].fill(0)
            if self.ui.chk_step_err.isChecked():
                self.title_str = r'Settling Error $\epsilon$'
                self.H_str = r'$h_{\epsilon, \infty} - h_{\epsilon}[n]$'
            else:
                self.title_str = r'Step Response'
                self.H_str = r'$h_{\epsilon}[n]$'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "cos":
            x = self.ui.A1 * np.cos(2*pi * n * self.ui.f1 + phi1) +\
                self.ui.A2 * np.cos(2*pi * n * self.ui.f2 + phi2)
            self.title_str += r'Cosine Stimulus'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "sine":
            x = self.ui.A1 * np.sin(2*pi * n * self.ui.f1 + phi1) +\
                self.ui.A2 * np.sin(2*pi * n * self.ui.f2 + phi2)
            self.title_str += r'Sinusoidal Stimulus '

        # ----------------------------------------------------------------------
        elif self.ui.stim == "exp":
            x = self.ui.A1 * np.exp(1j * (2 * pi * n * self.ui.f1 + phi1)) +\
                self.ui.A2 * np.exp(1j * (2 * pi * n * self.ui.f2 + phi2))
            self.title_str += r'Complex Exponential Stimulus '

        # ----------------------------------------------------------------------
        elif self.ui.stim == "diric":
            x = self.ui.A1 * diric(
                (4 * pi * (n-self.ui.T1) * self.ui.f1 + phi1*2)
                / self.ui.TW1, self.ui.TW1)
            self.title_str += r'Periodic Sinc Stimulus'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "chirp":
            if True:  # sig.chirp is buggy, T_sim cannot be larger than T_end
                T_end = N_last
            else:
                T_end = self.ui.T2
            x = self.ui.A1 * sig.chirp(n, self.ui.f1, T_end, self.ui.f2,
                                       method=self.ui.chirp_type, phi=phi1)
            self.title_str += self.ui.chirp_type.capitalize() + ' Chirp Stimulus'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "triang":
            if self.ui.but_stim_bl.isChecked():
                x = self.ui.A1 * triang_bl(2*pi * n * self.ui.f1 + phi1)
                self.title_str += r'Bandlim. Triangular Stimulus'
            else:
                x = self.ui.A1 * sig.sawtooth(
                    2*pi * n * self.ui.f1 + phi1, width=0.5)
                self.title_str += r'Triangular Stimulus'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "saw":
            if self.ui.but_stim_bl.isChecked():
                x = self.ui.A1 * sawtooth_bl(2*pi * n * self.ui.f1 + phi1)
                self.title_str += r'Bandlim. Sawtooth Stimulus'
            else:
                x = self.ui.A1 * sig.sawtooth(2*pi * n * self.ui.f1 + phi1)
                self.title_str += r'Sawtooth Stimulus'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "square":
            if self.ui.but_stim_bl.isChecked():
                x = self.ui.A1 * rect_bl(
                    2 * pi * n * self.ui.f1 + phi1, duty=self.ui.stim_par1)
                self.title_str += r'Bandlimited Rect. Stimulus'
            else:
                x = self.ui.A1 * sig.square(
                    2 * pi * n * self.ui.f1 + phi1, duty=self.ui.stim_par1)
                self.title_str += r'Rect. Stimulus'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "comb":
            x = self.ui.A1 * comb_bl(2 * pi * n * self.ui.f1 + phi1)
            self.title_str += r'Bandlim. Comb Stimulus'

        # ----------------------------------------------------------------------
        elif self.ui.stim == "am":
            x = self.ui.A1 * np.sin(2*pi * n * self.ui.f1 + phi1)\
                * self.ui.A2 * np.sin(2*pi * n * self.ui.f2 + phi2)
            self.title_str += (r'AM Stimulus: $A_1 \sin(2 \pi n f_1'
                               r'+ \varphi_1) \cdot A_2 \sin(2 \pi n f_2 + \varphi_2)$')

        # ----------------------------------------------------------------------
        elif self.ui.stim == "pmfm":
            x = self.ui.A1 * np.sin(
                2 * pi * n * self.ui.f1 + phi1 +
                self.ui.A2 * np.sin(2*pi * n * self.ui.f2 + phi2))
            self.title_str += (
                r'PM / FM Stimulus: $A_1 \sin(2 \pi n f_1'
                r'+ \varphi_1 + A_2 \sin(2 \pi n f_2 + \varphi_2))$')

        # ----------------------------------------------------------------------
        elif self.ui.stim == "formula":
            param_dict = {"A1": self.ui.A1, "A2": self.ui.A2,
                          "f1": self.ui.f1, "f2": self.ui.f2,
                          "phi1": self.ui.phi1, "phi2": self.ui.phi2,
                          "BW1": self.ui.BW1, "BW2": self.ui.BW2,
                          "f_S": fb.fil[0]['f_S'], "n": n}

            x = safe_numexpr_eval(self.ui.stim_formula, (N,), param_dict)
            self.title_str += r'Formula Defined Stimulus'
        else:
            logger.error('Unknown stimulus format "{0}"'.format(self.ui.stim))
            return None

        # ----------------------------------------------------------------------
        # Add noise to stimulus
        noi = 0
        if self.ui.noise == "none":
            pass
        elif self.ui.noise == "gauss":
            noi = self.ui.noi * np.random.randn(N)
            self.title_str += r' + Gaussian Noise'
        elif self.ui.noise == "uniform":
            noi = self.ui.noi * (np.random.rand(N)-0.5)
            self.title_str += r' + Uniform Noise'
        elif self.ui.noise == "prbs":
            noi = self.ui.noi * 2 * (np.random.randint(0, 2, N)-0.5)
            self.title_str += r' + PRBS Noise'
        elif self.ui.noise == "mls":
            # max_len_seq returns `sequence, state`. The state is not stored here,
            # hence, an identical sequence is created every time.
            noi = self.ui.noi * 2 * (sig.max_len_seq(int(np.ceil(np.log2(N))),
                                     length=N, state=None)[0] - 0.5)
            self.title_str += r' + max. length sequence'
        elif self.ui.noise == "brownian":
            # brownian noise
            noi = np.cumsum(self.ui.noi * np.random.randn(N))
            self.title_str += r' + Brownian Noise'
        else:
            logger.error('Unknown kind of noise "{}"'.format(self.ui.noise))
        if type(self.ui.noi) == complex:
            x = x.astype(complex) + noi
        else:
            x += noi
        # Add DC to stimulus when visible / enabled
        if self.ui.ledDC.isVisible:
            if type(self.ui.DC) == complex:
                x = x.astype(complex) + self.ui.DC
            else:
                x += self.ui.DC
            if self.ui.DC != 0:
                self.title_str += r' + DC'

        return x
# ------------------------------------------------------------------------------


if __name__ == "__main__":
    """ Run widget standalone with `python -m pyfda.plot_widgets.tran.plot_tran_stim` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Plot_Tran_Stim()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
