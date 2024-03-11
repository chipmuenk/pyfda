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
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, qstyle_widget
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
    Construct a widget for defining transient signals
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing, e.g. when stimulus has been calculated
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        super().__init__()
        # create the UI part with buttons etc.
        self.ui = Plot_Tran_Stim_UI(objectName='plot_tran_stim_ui_inst')

        # initial settings
        self.needs_calc = True   # flag whether plots need to be recalculated
        self.needs_redraw = [True] * 2  # flag which plot needs to be redrawn
        self.error = False
        self.x_file = None  # data mapped from file io in Plot_Impz.file_io()

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
            elif self.ui.stim == "rect_per":
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
            if self.ui.cmb_file_io.isEnabled():  # File is loaded, data is available
                if qget_cmb_box(self.ui.cmb_file_io) == "add":
                    self.title_str += r' + File Data'
                elif qget_cmb_box(self.ui.cmb_file_io) == "use":
                    self.title_str = r'File Data'
        # ----------------------------------------------------------------------


# ------------------------------------------------------------------------------
    def calc_stimulus_frame(self, x: np.ndarray = np.random.randn(10), N_first: int = 0,
                            N_frame: int = 10, N_end: int = 10) -> np.ndarray:
        """
        Calculate a data frame of stimulus `x` with a length of `N_frame` samples,
        starting with index `N_first`

        Parameters
        ----------
        x: ndarray of float or complex
            empty array that is filled in place frame by frame

        N_first: int
            index of first data point of the current frame

        N_frame: int
            current frame length; the last frame can be shorter than the rest

        N_end: int
            last sample of total stimulus to be generated (needed for scaling for some stimuli)

        Returns
        -------
        None
            x is filled with data in place

        """
        # -------------------------------------------
        def add_signal(stim: np.ndarray, add_sig: np.ndarray):
            """
            Add signal `add_sig` to stimulus `stim` (both need to have the same shape)
            and respect all combinations of real and complex-valued signals.
            If `add_sig` has the shape (N x 2), the two columns are added as real and
            imaginary values.
            """
            if np.ndim(add_sig) == 0:
                if add_sig is None or add_sig == 0:
                    return stim
                # else add_sig is a scalar, can be added to stim
            elif np.ndim(stim) != 1 or np.ndim(add_sig) > 2\
                or np.ndim(add_sig) == 2 and np.shape(add_sig)[1] != 2:
                logger.error(
                    f"Cannot combine stimulus ({np.shape(stim)}) and additional "
                    f"signal ({np.shape(add_sig)}) due to unsuitable dimensions!")
                return stim
            elif len(stim) != np.shape(add_sig)[0]:
                logger.error(
                    f"Cannot combine stimulus (len = {np.shape(stim)}) and additional "
                    f"signal (len = {np.shape(add_sig)}) due to different lenghts!")
                return stim
            # add_sig is 2D, add it to stimulus as a complex signal
            elif np.ndim(add_sig) == 2:
                logger.info("add_sig has two channels, casting to complex")
                stim = stim.astype(complex) + add_sig[:, 0] + 1j * add_sig[:, 1]
                return stim

            # ---
            # add_sig contains complex items (the array is always complex),
            # cast stim to complex as well before adding
            if np.any(np.iscomplex(add_sig)):
                logger.info("add_sig is complex")
                stim = stim.astype(complex) + add_sig
            # add_sig is real and stimulus is complex:
            # -> add add_sig to both real and imaginary part of stimulus
            elif np.any(np.iscomplex(stim)):
                logger.info("stim is complex")
                stim = stim + add_sig + 1j * add_sig
            else:  # stim and add_sig are real-valued
                stim = stim + add_sig
            return stim

        # ====================================================================
        # Initialization for all frames
        # -------------------------------------------------------------------
        if N_first == 0:
            # calculate index for T1, only needed for dirac, step and rect
            self.T1_idx = int(np.round(self.ui.T1))
            self.rad_phi1 = self.ui.phi1 / 180 * pi
            self.rad_phi2 = self.ui.phi2 / 180 * pi
        # -------------------------------------------------------------------
        # Initialization for current frame
        # -------------------------------------------------------------------
        N_last = N_first + N_frame  # calculate last element index
        frm_slc = slice(N_first, N_last)  # current slice
        n = np.arange(N_first, N_last)  #  create frame index vector
        t = n * fb.fil[0]['T_S']  # create time vector
        noi = 0  # fallback when no noise is selected
        # ====================================================================

        # #####################################################################
        #
        # calculate stimuli x[n]
        #
        # ######################################################################
        if self.ui.cmb_file_io.isEnabled() and qget_cmb_box(self.ui.cmb_file_io) == "use":
            if self.x_file is None:
                logger.warning("No file loaded!")
            # file data is longer than frame, use only a part:
            elif len(self.x_file) >= N_last:
                x[frm_slc] = self.x_file[frm_slc]
            # file data is shorter than frame, pad with zeros
            elif len(self.x_file) > N_first:
                x[frm_slc] = np.concatenate(
                    (self.x_file[N_first:], np.zeros(N_last - len(self.x_file))))
            else:
                # file data has been consumed, nothing left to be added
                pass
            return
        # ----------------------------------------------------------------------
        elif self.ui.stim == "none":
            pass
        # ----------------------------------------------------------------------
        elif self.ui.stim == "dirac":
            if N_first <= self.T1_idx < N_last:
                x[self.T1_idx - N_first] = self.ui.A1
        # ----------------------------------------------------------------------
        elif self.ui.stim == "sinc":
            x[frm_slc] = self.ui.A1 * sinc(2 * (n - self.ui.T1) * self.ui.f1)\
                + self.ui.A2 * sinc(2 * (n - self.ui.T2) * self.ui.f2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "gauss":
            x[frm_slc] = self.ui.A1 * sig.gausspulse(
                    (n - self.ui.T1), fc=self.ui.f1, bw=self.ui.BW1) +\
                self.ui.A2 * sig.gausspulse(
                    (n - self.ui.T2), fc=self.ui.f2, bw=self.ui.BW2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "rect":
            n_rise = int(self.T1_idx - np.floor(self.ui.TW1/2))  # pos. of rising edge
            n_min = max(n_rise, 0)
            n_max = min(n_rise + self.ui.TW1, N_end)
            x[frm_slc] = self.ui.A1 * np.where((n >= n_min) & (n < n_max), 1, 0)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "step":
            if self.T1_idx < N_first:   # step before current frame
                x[frm_slc].fill(self.ui.A1)
            if N_first <= self.T1_idx < N_last:  # step in current frame
                x[frm_slc][0:self.T1_idx - N_first].fill(0)
                x[frm_slc][self.T1_idx - N_first:N_last].fill(self.ui.A1)
            elif self.T1_idx >= N_last:  # step after current frame
                x[frm_slc].fill(0)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "cos":
            x[frm_slc] =\
                self.ui.A1 * np.cos(2 * pi * n * self.ui.f1 + self.rad_phi1) +\
                self.ui.A2 * np.cos(2 * pi * n * self.ui.f2 + self.rad_phi2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "sine":
            x[frm_slc] =\
                self.ui.A1 * np.sin(2 * pi * n * self.ui.f1 + self.rad_phi1) +\
                self.ui.A2 * np.sin(2 * pi * n * self.ui.f2 + self.rad_phi2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "exp":
            x[frm_slc] =\
                self.ui.A1 * np.exp(1j * (2 * pi * n * self.ui.f1 + self.rad_phi1)) +\
                self.ui.A2 * np.exp(1j * (2 * pi * n * self.ui.f2 + self.rad_phi2))
        # ----------------------------------------------------------------------
        elif self.ui.stim == "diric":
            # scipy:  diric(x, N) = sin(Nx/2) / N*sin(x/2)
            # we use: x = 2 pi t = 2 pi f_1 n
            # diric(x, N) = sin(Nx/2) / N*sin(x/2) with x = 2 pi f_1 n
            x[frm_slc] = self.ui.A1 * diric(
                (2 * pi * (n - self.ui.T1) * self.ui.f1),
                self.ui.N1)

        # ----------------------------------------------------------------------
        elif self.ui.stim == "chirp":
            if self.ui.T2 == 0:  # sig.chirp is buggy, T_sim cannot be larger than T_end
                T_end = N_end  # frequency sweep over complete interval
            else:
                T_end = self.ui.T2  # frequency sweep till T2
            x[frm_slc] = self.ui.A1 * sig.chirp(
                n, self.ui.f1, T_end, self.ui.f2,
                method=self.ui.chirp_type, phi=self.rad_phi1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "triang":
            if self.ui.but_stim_bl.isChecked():
                x[frm_slc] = self.ui.A1 * triang_bl(2*pi * n * self.ui.f1 + self.rad_phi1)
            else:
                x[frm_slc] = self.ui.A1 * sig.sawtooth(
                    2*pi * n * self.ui.f1 + self.rad_phi1, width=0.5)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "saw":
            if self.ui.but_stim_bl.isChecked():
                x[frm_slc] = self.ui.A1 * sawtooth_bl(2*pi * n * self.ui.f1 + self.rad_phi1)
            else:
                x[frm_slc] = self.ui.A1 * sig.sawtooth(2*pi * n * self.ui.f1 + self.rad_phi1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "rect_per":
            if self.ui.but_stim_bl.isChecked():
                x[frm_slc] = self.ui.A1 * rect_bl(
                    2 * pi * n * self.ui.f1 + self.rad_phi1, duty=self.ui.stim_par1)
            else:
                x[frm_slc] = self.ui.A1 * sig.square(
                    2 * pi * n * self.ui.f1 + self.rad_phi1, duty=self.ui.stim_par1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "comb":
            x[frm_slc] = self.ui.A1 * comb_bl(2 * pi * n * self.ui.f1 + self.rad_phi1)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "am":
            x[frm_slc] = self.ui.A1 * np.sin(2*pi * n * self.ui.f1 + self.rad_phi1)\
                * self.ui.A2 * np.sin(2*pi * n * self.ui.f2 + self.rad_phi2)
        # ----------------------------------------------------------------------
        elif self.ui.stim == "pmfm":
            x[frm_slc] = self.ui.A1 * np.sin(
                2 * pi * n * self.ui.f1 + self.rad_phi1 +
                self.ui.A2 * np.sin(2*pi * n * self.ui.f2 + self.rad_phi2))
        # ----------------------------------------------------------------------
        elif self.ui.stim == "pwm":
            if self.ui.but_stim_bl.isChecked():
                x[frm_slc] = self.ui.A1 * rect_bl(
                    2 * np.pi * n * self.ui.f1 + self.rad_phi1,
                    duty=(1/2 + self.ui.A2 / 2 *
                          np.sin(2*pi * n * self.ui.f2 + self.rad_phi2)))
            else:
                x[frm_slc] = self.ui.A1 * sig.square(
                    2 * np.pi * n * self.ui.f1 + self.rad_phi1,
                    duty=(1/2 + self.ui.A2 / 2 *
                          np.sin(2*pi * n * self.ui.f2 + self.rad_phi2)))
        # ----------------------------------------------------------------------
        elif self.ui.stim == "formula":
            param_dict = {
                "A1": self.ui.A1, "A2": self.ui.A2, "f1": self.ui.f1, "f2": self.ui.f2,
                "phi1": self.ui.phi1, "phi2": self.ui.phi2,
                "T1": self.ui.T1, "T2": self.ui.T2, "N1": self.ui.N1, "N2": self.ui.N2,
                "BW1": self.ui.BW1, "BW2": self.ui.BW2, "f_S": fb.fil[0]['f_S'],
                "n": n, "t": t, "j": 1j}

            x[frm_slc] = safe_numexpr_eval(self.ui.stim_formula, (N_frame,), param_dict)
            if safe_numexpr_eval.err > 0:
                qstyle_widget(self.ui.ledStimFormula, 'failed')
            else:
                qstyle_widget(self.ui.ledStimFormula, 'normal')
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
                    int(np.abs(self.ui.noi.real)) + 1, size=N_frame) +\
                        1j * np.random.randint(
                            int(np.abs(self.ui.noi.imag)) + 1, size=N_frame)
            else:
                noi = np.random.randint(int(np.abs(self.ui.noi)) + 1, size=N_frame)
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
                noi = noi_r * self.ui.noi
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


        # #####################################################################
        #
        # Add noise / DC / file data to stimulus x[n]
        #
        # ######################################################################

        # Add noise to stimulus when enabled:
        if qget_cmb_box(self.ui.cmb_stim_noise) != "none":
            x[frm_slc] = add_signal(x[frm_slc], noi)

        # Add DC to stimulus when visible / enabled
        if self.ui.ledDC.isVisible and self.ui.DC != 0:
            x[frm_slc] = add_signal(x[frm_slc], self.ui.DC)

        # Add file data to stimulus for combobox setting "add"
        if self.ui.cmb_file_io.isEnabled() and qget_cmb_box(self.ui.cmb_file_io) == "add":
            if self.x_file is None:
                logger.warning("No file loaded!")
            # file data is longer than frame, use only a part:
            elif len(self.x_file) >= N_last:
                x[frm_slc] = add_signal(x[frm_slc], self.x_file[frm_slc])
            # file data is shorter than frame, pad with zeros
            elif len(self.x_file) > N_first:
                x[frm_slc] = add_signal(x[frm_slc], np.concatenate(
                    (self.x_file[N_first:], np.zeros(N_last - len(self.x_file)))))
            # file data has been consumed, nothing left to be added
            else:
                return

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
