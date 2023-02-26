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
from pyfda.libs.compat import QWidget, pyqtSignal, QVBoxLayout
import numpy as np
from numpy import ndarray, pi
from pyfda.libs.pyfda_qt_lib import qget_cmb_box
import scipy.signal as sig
from scipy.special import sinc, diric

import pyfda.filterbroker as fb
from pyfda.libs.pyfda_sig_lib import angle_zero
from pyfda.libs.pyfda_lib import (
    safe_eval, pprint_log, np_type, calc_ssb_spectrum,
    rect_bl, sawtooth_bl, triang_bl, comb_bl, safe_numexpr_eval)

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

    def __init__(self):
        super().__init__()
        self.ui = Plot_Tran_Stim_UI()  # create the UI part with buttons etc.

        # initial settings
        self.needs_calc = True   # flag whether plots need to be recalculated
        self.needs_redraw = [True] * 2  # flag which plot needs to be redrawn
        self.error = False
        self.x_file = None  # data mapped from file io

        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None) -> None:
        """
        Process signals coming from
        - the navigation toolbars (time and freq.)
        - local widgets (impz_ui) and
        - plot_tab_widgets() (global signals)
        """

        logger.warning("SIG_RX - needs_calc: {0} | vis: {1}\n{2}"
                       .format(self.needs_calc, self.isVisible(), pprint_log(dict_sig)))

    def _construct_UI(self) -> None:
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

    def init_labels_stim(self):
            '''intialize title string, y-axis label and some variables'''
            # use radians for angle internally
            self.H_str = r'$y[n]$'  # default
            self.title_str = ""
            if self.ui.stim == "none":
                self.title_str = r'Zero Input'
                self.H_str = r'$h_0[n]$'
            # ------------------------------------------------------------------
            elif self.ui.stim == "dirac":
                self.title_str = r'Impulse Response'
                self.H_str = r'$h[n]$'
            elif self.ui.stim == "sinc":
                self.title_str = r'Sinc Impulse'
            elif self.ui.stim == "gauss":
                self.title_str = r'Gaussian Impulse'
            elif self.ui.stim == "rect":
                self.title_str = r'Rect Impulse'
            # ------------------------------------------------------------------
            elif self.ui.stim == "step":
                if self.ui.chk_step_err.isChecked():
                    self.title_str = r'Settling Error $\epsilon$'
                    self.H_str = r'$h_{\epsilon, \infty} - h_{\epsilon}[n]$'
                else:
                    self.title_str = r'Step Response'
                    self.H_str = r'$h_{\epsilon}[n]$'
            # ------------------------------------------------------------------
            elif self.ui.stim == "cos":
                self.title_str = r'Cosine Stimulus'
            elif self.ui.stim == "sine":
                self.title_str = r'Sinusoidal Stimulus'
            elif self.ui.stim == "exp":
                self.title_str = r'Complex Exponential Stimulus'
            elif self.ui.stim == "diric":
                self.title_str = r'Periodic Sinc Stimulus'
            # ------------------------------------------------------------------
            elif self.ui.stim == "chirp":
                self.title_str = self.ui.chirp_type.capitalize() + ' Chirp Stimulus'
            # ------------------------------------------------------------------
            elif self.ui.stim == "triang":
                if self.ui.but_stim_bl.isChecked():
                    self.title_str = r'Bandlim. Triangular Stimulus'
                else:
                    self.title_str = r'Triangular Stimulus'
            elif self.ui.stim == "saw":
                if self.ui.but_stim_bl.isChecked():
                    self.title_str = r'Bandlim. Sawtooth Stimulus'
                else:
                    self.title_str = r'Sawtooth Stimulus'
            elif self.ui.stim == "square":
                if self.ui.but_stim_bl.isChecked():
                    self.title_str = r'Bandlimited Rect. Stimulus'
                else:
                    self.title_str = r'Rect. Stimulus'
            elif self.ui.stim == "comb":
                self.title_str = r'Bandlim. Comb Stimulus'
            # ------------------------------------------------------------------
            elif self.ui.stim == "am":
                self.title_str = (
                    r'AM Stimulus: $A_1 \sin(2 \pi n f_1 + \varphi_1)'
                    r'\cdot A_2 \sin(2 \pi n f_2 + \varphi_2)$')
            elif self.ui.stim == "pmfm":
                self.title_str = (
                    r'PM / FM Stimulus: $A_1 \sin(2 \pi n f_1'
                    r'+ \varphi_1 + A_2 \sin(2 \pi n f_2 + \varphi_2))$')
            elif self.ui.stim == "pwm":
                self.title_str = (
                    r'PWM Stimulus with Duty Cycle $\frac {1} {2}(1 + A_2\sin(2 \pi n f_2'
                    r'+ \varphi_2 ))$')

            # ------------------------------------------------------------------
            elif self.ui.stim == "formula":
                self.title_str = r'Formula Defined Stimulus'
            # ==================================================================
            if self.ui.noise == "gauss":
                self.title_str += r' + Gaussian Noise'
            elif self.ui.noise == "uniform":
                self.title_str += r' + Uniform Noise'
            elif self.ui.noise == "randint":
                self.title_str += r' + Random Int. Sequence'
            elif self.ui.noise == "mls":
                self.title_str += r' + Max. Length Sequence'
            elif self.ui.noise == "brownian":
                self.title_str += r' + Brownian Noise'
            # ==================================================================
            if self.ui.ledDC.isVisible and self.ui.DC != 0:
                self.title_str += r' + DC'
            # ==================================================================
            if qget_cmb_box(self.ui.cmb_file_io) == "add":
                self.title_str += r' + File Data'
            elif qget_cmb_box(self.ui.cmb_file_io) == "use":
                self.title_str = r'File Data'
        # ----------------------------------------------------------------------


# ------------------------------------------------------------------------------
    def calc_stimulus_frame(self, N_first: int = 0, N_frame: int = 10, N_end: int = 10,
                            init: bool = False) -> np.ndarray:
        """
        Calculate a data frame of stimulus `x` with a length of `N_frame` samples,
        starting with index `N_first`

        Parameters
        ----------
        N_first: int
            index of first data point of the frame

        N_frame: int
            frame length

        N_end: int
            last sample of total stimulus to be generated

        init: bool
            when init == True, initialize stimulus settings

        Returns
        -------
        x: ndarray
            an array with `N` stimulus data points
        """
        # -------------------------------------------
        def add_signal(stim: np.ndarray, sig: np.ndarray):
            """
            Add signal `sig` to stimulus `stim` (both need to have the same shape)
            and respect all combinations of real and complex-valued signals.
            If `sig` has the shape (N x 2), the two columns are added as real and
            imaginary values.
            """
            # logger.warning(f"stim: {pprint_log(stim)}\n\nsig: {pprint_log(sig)}")
            if np.ndim(sig) == 0:
                if sig is None or sig == 0:
                    return stim
                # else sig is a scalar, can be added to stim
            elif np.ndim(sig) > 1 or np.ndim(stim) != 1\
                    or len(stim) != np.shape(stim)[0]\
                        or np.ndim(sig) == 2 and np.shape(sig)[1] != 2:
                logger.error(
                    f"Cannot combine stimulus ({np.shape(stim)}) and additional "
                    f"signal ({np.shape(sig)}) due to different shapes!")
                return stim
            # special case of 2D-sig which is added to stimulus as a complex signal
            elif np.ndim(sig) == 2:
                stim = stim.astype(complex) + sig[:, 0] + 1j * sig[:, 1]
                return stim
            # ---
            # sig is complex, cast stim to complex as well before adding
            if np.iscomplexobj(sig):
                stim = stim.astype(complex) + sig
            # sig is real and stimulus is complex:
            # -> add sig to bothreal and imaginary part of stimulus
            elif np.iscomplexobj(self.xf):
                stim += sig + 1j * sig
            else:  # stim and sig are real-valued
                stim += sig
            return stim
        # -------------------------------------------

        if init or N_first == 0:
            self.init_labels_stim()
            self.rad_phi1 = self.ui.phi1 / 180 * pi
            self.rad_phi2 = self.ui.phi2 / 180 * pi
            self.xf_is_cmplx =\
                (self.ui.ledDC.isVisible and type(self.ui.DC) == complex)\
                    or (self.ui.ledAmp1.isVisible and type(self.ui.A1) == complex)\
                        or (self.ui.ledAmp2.isVisible and type(self.ui.A2) == complex)

        noi = 0  # initialize noise frame
        N_last = N_first + N_frame  # calculate last element index
        n = np.arange(N_first, N_last)  #  create frame index

        # calculate index for T1, only needed for dirac and step
        self.T1_idx = int(np.round(self.ui.T1))

        # - Initialize self.xf with N_frame zeros.
        # - Set dtype of ndarray to complex or float, depending on stimuli
        if self.xf_is_cmplx:
            self.xf = np.zeros(N_frame, dtype=complex)
        else:
            self.xf = np.zeros(N_frame, dtype=float)

        # #####################################################################
        #
        # calculate stimuli x[n]
        #
        # ######################################################################
        if self.ui.stim == "none":
            pass
        elif qget_cmb_box(self.ui.cmb_file_io) == "use":
            if self.x_file is None:
                logger.warning("No file loaded!")
            else:
                self.xf = self.x_file[N_first:N_last]
            return self.xf[:N_frame]
        # ----------------------------------------------------------------------
        elif self.ui.stim == "dirac":
            if N_first <= self.T1_idx < N_last:
                self.xf[self.T1_idx - N_first] = self.ui.A1
        # ----------------------------------------------------------------------
        elif self.ui.stim == "sinc":
            self.xf = self.ui.A1 * sinc(2 * (n - self.ui.T1) * self.ui.f1)\
                + self.ui.A2 * sinc(2 * (n - self.ui.T2) * self.ui.f2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "gauss":
            self.xf = self.ui.A1 * sig.gausspulse(
                    (n - self.ui.T1), fc=self.ui.f1, bw=self.ui.BW1) +\
                self.ui.A2 * sig.gausspulse(
                    (n - self.ui.T2), fc=self.ui.f2, bw=self.ui.BW2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "rect":
            n_rise = int(self.T1_idx - np.floor(self.ui.TW1/2))  # pos. of rising edge
            n_min = max(n_rise, 0)
            n_max = min(n_rise + self.ui.TW1, N_end)
            self.xf = self.ui.A1 * np.where((n >= n_min) & (n < n_max), 1, 0)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "step":
            if self.T1_idx < N_first:   # step before current frame
                self.xf.fill(self.ui.A1)
            if N_first <= self.T1_idx < N_last:  # step in current frame
                self.xf[0:self.T1_idx - N_first].fill(0)
                self.xf[self.T1_idx - N_first:N_last].fill(self.ui.A1)
            elif self.T1_idx >= N_last:  # step after current frame
                self.xf.fill(0)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "cos":
            self.xf =\
                self.ui.A1 * np.cos(2 * pi * n * self.ui.f1 + self.rad_phi1) +\
                self.ui.A2 * np.cos(2 * pi * n * self.ui.f2 + self.rad_phi2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "sine":
            self.xf =\
                self.ui.A1 * np.sin(2 * pi * n * self.ui.f1 + self.rad_phi1) +\
                self.ui.A2 * np.sin(2 * pi * n * self.ui.f2 + self.rad_phi2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "exp":
            self.xf =\
                self.ui.A1 * np.exp(1j * (2 * pi * n * self.ui.f1 + self.rad_phi1)) +\
                self.ui.A2 * np.exp(1j * (2 * pi * n * self.ui.f2 + self.rad_phi2))
        # ----------------------------------------------------------------------
        elif self.ui.stim == "diric":
            self.xf = self.ui.A1 * diric(
                (4 * pi * (n - self.ui.T1) * self.ui.f1 + self.rad_phi1 * 2)
                / self.ui.TW1, self.ui.TW1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "chirp":
            if self.ui.T2 == 0:  # sig.chirp is buggy, T_sim cannot be larger than T_end
                T_end = N_end  # frequency sweep over complete interval
            else:
                T_end = self.ui.T2  # frequency sweep till T2
            self.xf = self.ui.A1 * sig.chirp(
                n, self.ui.f1, T_end, self.ui.f2,
                method=self.ui.chirp_type, phi=self.rad_phi1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "triang":
            if self.ui.but_stim_bl.isChecked():
                self.xf = self.ui.A1 * triang_bl(2*pi * n * self.ui.f1 + self.rad_phi1)
            else:
                self.xf = self.ui.A1 * sig.sawtooth(
                    2*pi * n * self.ui.f1 + self.rad_phi1, width=0.5)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "saw":
            if self.ui.but_stim_bl.isChecked():
                self.xf = self.ui.A1 * sawtooth_bl(2*pi * n * self.ui.f1 + self.rad_phi1)
            else:
                self.xf = self.ui.A1 * sig.sawtooth(2*pi * n * self.ui.f1 + self.rad_phi1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "square":
            if self.ui.but_stim_bl.isChecked():
                self.xf = self.ui.A1 * rect_bl(
                    2 * pi * n * self.ui.f1 + self.rad_phi1, duty=self.ui.stim_par1)
            else:
                self.xf = self.ui.A1 * sig.square(
                    2 * pi * n * self.ui.f1 + self.rad_phi1, duty=self.ui.stim_par1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "comb":
            self.xf = self.ui.A1 * comb_bl(2 * pi * n * self.ui.f1 + self.rad_phi1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "am":
            self.xf = self.ui.A1 * np.sin(2*pi * n * self.ui.f1 + self.rad_phi1)\
                * self.ui.A2 * np.sin(2*pi * n * self.ui.f2 + self.rad_phi2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "pmfm":
            self.xf = self.ui.A1 * np.sin(
                2 * pi * n * self.ui.f1 + self.rad_phi1 +
                self.ui.A2 * np.sin(2*pi * n * self.ui.f2 + self.rad_phi2))
        # ----------------------------------------------------------------------
        elif self.ui.stim == "pwm":
            if self.ui.but_stim_bl.isChecked():
                self.xf = self.ui.A1 * rect_bl(
                    2 * np.pi * n * self.ui.f1 + self.rad_phi1,
                    duty=(1/2 + self.ui.A2 / 2 *
                          np.sin(2*pi * n * self.ui.f2 + self.rad_phi2)))
            else:
                self.xf = self.ui.A1 * sig.square(
                    2 * np.pi * n * self.ui.f1 + self.rad_phi1,
                    duty=(1/2 + self.ui.A2 / 2 *
                          np.sin(2*pi * n * self.ui.f2 + self.rad_phi2)))
        # ----------------------------------------------------------------------
        elif self.ui.stim == "formula":
            param_dict = {"A1": self.ui.A1, "A2": self.ui.A2,
                          "f1": self.ui.f1, "f2": self.ui.f2,
                          "phi1": self.ui.phi1, "phi2": self.ui.phi2,
                          "BW1": self.ui.BW1, "BW2": self.ui.BW2,
                          "f_S": fb.fil[0]['f_S'], "n": n, "j": 1j}

            self.xf = safe_numexpr_eval(self.ui.stim_formula, (N_frame,), param_dict)
        else:
            logger.error('Unknown stimulus format "{0}"'.format(self.ui.stim))
            return None
        # ----------------------------------------------------------------------
        # Calculate noise
        # ----------------------------------------------------------------------
        if self.ui.noise == "none":
            pass
        elif self.ui.noise == "gauss":
            # Gaussian noise is uncorrelated, no information from last frame needed
            if np.iscomplexobj(self.ui.noi):
                noi = self.ui.noi.real * np.random.randn(N_frame)\
                    + 1j * self.ui.noi.imag * np.random.randn(N_frame)
            else:
                noi = self.ui.noi * np.random.randn(N_frame)
        # ---
        elif self.ui.noise == "uniform":
            # Uniform noise is uncorrelated, no information from last frame needed
            if np.iscomplexobj(self.ui.noi):
                noi = self.ui.noi.real * (np.random.rand(N_frame) - 0.5)\
                    + 1j * self.ui.noi.imag * (np.random.rand(N_frame) - 0.5)
            else:
                noi = self.ui.noi * (np.random.rand(N_frame) - 0.5)
        # ---
        elif self.ui.noise == "randint":
            # Random integers are uncorrelated, no information from last frame needed
            if np.iscomplexobj(self.ui.noi):
                noi = np.random.randint(
                    np.int(np.abs(self.ui.noi.real)) + 1, size=N_frame) +\
                        1j * np.random.randint(
                            np.int(np.abs(self.ui.noi.imag)) + 1, size=N_frame)
            else:
                noi = np.random.randint(np.int(np.abs(self.ui.noi)) + 1, size=N_frame)
        # ---
        elif self.ui.noise == "mls":
            # Maximum Length Sequences have a fixed length of 2 ** self.ui.mls_b,
            # use seed of last sequence element to seed new sequence
            if N_first == 0:
                # initialize sequence(s) with fixed seeds, creating an identical
                # sequence at every run
                self.seed_r = [1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1, 1,
                        0, 1, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0][:self.ui.mls_b]
                self.seed_i = np.roll(self.seed_r, 1)

            noi_r, self.seed_r = sig.max_len_seq(
                self.ui.mls_b, length=N_frame, state=self.seed_r)
            if np.iscomplexobj(self.ui.noi):
                noi_i, self.seed_i = sig.max_len_seq(
                    self.ui.mls_b, length=N_frame, state=self.seed_i)
                noi = self.ui.noi.real * noi_r + 1j * self.ui.noi.imag * noi_i
            else:
                noi = noi_r * self.ui.noi.real
        # ---
        elif self.ui.noise == "brownian":  # brownian noise
            # Brownian noise in cumulative, add last value of last frame to
            # current frame
            if N_first == 0:
                self.noi_last = 0  # initialize for first frame
            if np.iscomplexobj(self.ui.noi):
                noi = np.cumsum(self.ui.noi.real * np.random.randn(N_frame))\
                    + 1j * np.cumsum(self.ui.noi.imag * np.random.randn(N_frame))
            else:
                noi = np.cumsum(self.ui.noi * np.random.randn(N_frame))
            noi += self.noi_last
            self.noi_last = noi[-1]
        else:
            logger.error('Unknown kind of noise "{}"'.format(self.ui.noise))

        # Add noise to stimulus:
        self.xf = add_signal(self.xf, noi)

        # Add DC to stimulus when visible / enabled
        if self.ui.ledDC.isVisible:
            self.xf = add_signal(self.xf, self.ui.DC)

        # Add file data
        if qget_cmb_box(self.ui.cmb_file_io) == "add":
            if self.x_file is None:
                logger.warning("No file loaded!")
            # file data is longer than frame, use only a part:
            elif len(self.x_file) >= N_last:
                self.xf = add_signal(self.xf, self.x_file[N_first:N_last, :])
            # file data is shorter than frame, pad with zeros
            elif len(self.x_file) > N_first:
                self.xf = add_signal(self.xf, np.concatenate(
                    (self.x_file[N_first:, :],
                     np.zeros(N_last - np.shape(self.x_file)[0], np.shape(self.x_file[1])))
                    ))
            # file data has been consumed, nothing left to be added
            else:
                pass

        return self.xf[:N_frame]
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
