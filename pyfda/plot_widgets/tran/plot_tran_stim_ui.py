# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create the UI for the Plot_Tran_Impz class
"""
import collections

from PyQt5.QtWidgets import QSizePolicy
from pyfda.libs.compat import (
    QWidget, QComboBox, QLineEdit, QLabel, QPushButton,
    pyqtSignal, QEvent, Qt, QHBoxLayout, QVBoxLayout, QGridLayout)

from pyfda.libs.pyfda_lib import to_html, safe_eval, pprint_log
import pyfda.filterbroker as fb
from pyfda.libs.pyfda_qt_lib import (
    qcmb_box_populate, qget_cmb_box, qset_cmb_box, qtext_width,
    PushButton)
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

import logging
logger = logging.getLogger(__name__)


class Plot_Tran_Stim_UI(QWidget):
    """
    Create the UI for the PlotImpz class
    """
    # incoming:
    sig_rx = pyqtSignal(object)
    # outgoing: from various UI elements to PlotImpz ('ui_changed':'xxx')
    sig_tx = pyqtSignal(object)
    # outgoing: to fft related widgets (FFT window widget, qfft_win_select)
    sig_tx_fft = pyqtSignal(object)

    from pyfda.libs.pyfda_qt_lib import emit

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from
        - FFT window widget
        - qfft_win_select
        """

        # logger.warning("PROCESS_SIG_RX - vis: {0}\n{1}"
        #             .format(self.isVisible(), pprint_log(dict_sig)))

        if 'id' in dict_sig and dict_sig['id'] == id(self):
            logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
            return
        elif 'view_changed' in dict_sig:
            if dict_sig['view_changed'] == 'f_S':
                self.recalc_freqs()

# ------------------------------------------------------------------------------
    def __init__(self):
        super().__init__()

        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        # initial settings
        self.N_FFT = 0  # TODO: FFT value needs to be passed here somehow?

        # stimuli
        self.cmb_stim_item = "impulse"
        self.cmb_stim_periodic_item = 'square'
        self.cmb_stim_modulation_item = 'am'
        self.stim = "dirac"
        self.impulse_type = 'dirac'
        self.sinusoid_type = 'sine'

        self.chirp_type = 'linear'

        self.noise = "None"

        self.f1 = 0.02
        self.f2 = 0.03
        self.A1 = 1.0
        self.A2 = 0.0
        self.phi1 = self.phi2 = 0
        self.T1 = self.T2 = 0
        self.TW1 = self.TW2 = 1
        self.BW1 = self.BW2 = 0.5
        self.noi = 0.1
        self.noise = 'none'
        self.DC = 0.0
        self.stim_formula = "A1 * abs(sin(2 * pi * f1 * n))"
        self.stim_par1 = 0.5

        self.scale_impz = 1  # optional energy scaling for impulses

        # self.bottom_f = -120  # initial value for log. scale
        # self.param = None

        # dictionaries with widgets needed for the various stimuli
        self.stim_wdg_dict = collections.OrderedDict()
        self.stim_wdg_dict.update({
            "none":    {"dc", "noise"},
            "dirac":   {"dc", "a1", "T1", "norm", "noise"},
            "sinc":    {"dc", "a1", "a2", "T1", "T2", "f1", "f2", "norm", "noise"},
            "gauss":   {"dc", "a1", "a2", "T1", "T2", "f1", "f2", "BW1", "BW2",
                        "norm", "noise"},
            "rect":    {"dc", "a1", "T1", "TW1", "norm", "noise"},
            "step":    {"a1", "T1", "noise"},
            "cos":     {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
            "sine":    {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
            "exp":     {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
            "diric":   {"dc", "a1", "phi1", "T1", "TW1", "f1", "noise"},

            "chirp":   {"dc", "a1", "phi1", "f1", "f2", "T2", "noise"},
            "triang":  {"dc", "a1", "phi1", "f1", "noise", "bl"},
            "saw":     {"dc", "a1", "phi1", "f1", "noise", "bl"},
            "square":  {"dc", "a1", "phi1", "f1", "noise", "bl", "par1"},
            "comb":    {"dc", "a1", "phi1", "f1", "noise"},
            "am":      {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
            "pmfm":    {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
            "pwm":     {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise", "bl"},
            "formula": {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "BW1",
                        "BW2", "noise"}
         })

        # combobox tooltip + data / text / tooltip for stimulus category items
        self.cmb_stim_items = [
            ("<span>Stimulus category.</span>"),
            ("none", "None", "<span>Only noise and DC can be selected.</span>"),
            ("impulse", "Impulse", "<span>Different impulses</span>"),
            ("step", "Step", "<span>Calculate step response and its error.</span>"),
            ("sinusoid", "Sinusoid", "<span>Sinusoidal waveforms</span>"),
            ("chirp", "Chirp", "<span>Different frequency sweeps.</span>"),
            ("periodic", "Periodic", "<span>Periodic functions with discontinuities, "
             "either band-limited or with aliasing.</span>"),
            ("modulation", "Modulat.", "<span>Modulated waveforms.</span>"),
            ("formula", "Formula", "<span>Formula defined stimulus.</span>")
            ]

        # combobox tooltip + data / text / tooltip for periodic signals items
        self.cmb_stim_periodic_items = [
            "<span>Periodic functions with discontinuities.</span>",
            ("square", "Square", "<span>Square signal with duty cycle &alpha;</span>"),
            ("saw", "Saw", "Sawtooth signal"),
            ("triang", "Triang", "Triangular signal"),
            ("comb", "Comb", "Comb signal")
            ]

        # combobox tooltip + data / text / tooltip for chirp signals items
        self.cmb_stim_chirp_items = [
            "<span>Type of frequency sweep from <i>f</i><sub>1</sub> @ <i>t</i> = 0 to "
            "<i>f</i><sub>2</sub> @ t = <i>T</i><sub>2</sub>.</span>",
            ("linear", "Lin", "Linear frequency sweep"),
            ("quadratic", "Square", "Quadratic frequency sweep"),
            ("logarithmic", "Log", "Logarithmic frequency sweep"),
            ("hyperbolic", "Hyper",  "Hyperbolic frequency sweep")
            ]

        self.cmb_stim_impulse_items = [
            "<span>Different aperiodic impulse forms</span>",
            ("dirac", "Dirac",
             "<span>Discrete-time dirac impulse for simulating impulse and "
             "frequency response.</span>"),
            ("gauss", "Gauss",
             "<span>Gaussian pulse with bandpass spectrum and controllable "
             "relative -6 dB bandwidth.</span>"),
            ("sinc", "Sinc",
             "<span>Sinc pulse with rectangular baseband spectrum</span>"),
            ("rect", "Rect", "<span>Rectangular pulse with sinc-shaped spectrum</span>")
            ]

        self.cmb_stim_sinusoid_items = [
            "Sinusoidal or similar signals",
            ("sine", "Sine", "Sine signal"),
            ("cos", "Cos", "Cosine signal"),
            ("exp", "Exp", "Complex exponential"),
            ("diric", "Sinc", "<span>Periodic Sinc (Dirichlet function)</span>")
            ]

        self.cmb_stim_modulation_items = [
            "Modulated signals",
            ("am", "AM", "<span>Sinusoidal amplitude modulation of a sine</span>"),
            ("pmfm", "PM / FM", "<span>Sinusoidal phase or frequency modulation "
             "of a sine</span>"),
            ("pwm", "PWM", "sinusoidal pulse width modulation")
            ]

        # data / text / tooltip for noise stimulus combobox.
        self.cmb_stim_noise_items = [
            "Type of additive noise.",
            ("none", "None", ""),
            ("gauss", "Gauss",
             "<span>Normal- or Gauss-distributed process with std. deviation &sigma;."
             "</span>"),
            ("uniform", "Uniform",
             "<span>Uniformly distributed process in the range &plusmn; &Delta;/2."
             "</span>"),
            ("prbs", "PRBS",
             "<span>Pseudo-Random Binary Sequence with values &plusmn; A.</span>"),
            ("mls", "MLS",
             "<span>Maximum Length Sequence with values &plusmn; A. The sequence is "
             "always the same as the state is not stored for the next sequence start."
             "</span>"),
            ("brownian", "Brownian",
             "<span>Brownian (cumulated sum) process based on Gaussian noise with"
             " std. deviation &sigma;.</span>")
            ]

        self._construct_UI()
        self._enable_stim_widgets()
        self._update_noi()

    def _construct_UI(self):
        # =====================================================================
        # Controls for stimuli
        # =====================================================================
        self.cmbStimulus = QComboBox(self)
        qcmb_box_populate(self.cmbStimulus, self.cmb_stim_items, self.cmb_stim_item)

        self.lblStimPar1 = QLabel(to_html("&alpha; =", frmt='b'), self)
        self.ledStimPar1 = QLineEdit(self)
        self.ledStimPar1.setText("0.5")
        self.ledStimPar1.setToolTip("Duty Cycle, 0 ... 1")
        self.ledStimPar1.setObjectName("ledStimPar1")

        self.but_stim_bl = QPushButton(self)
        self.but_stim_bl.setText("BL")
        self.but_stim_bl.setToolTip(
            "<span>Bandlimit the signal to the Nyquist "
            "frequency to avoid aliasing. However, this is much slower "
            "to calculate especially for a large number of points.</span>")
        self.but_stim_bl.setMaximumWidth(qtext_width(text="BL "))
        self.but_stim_bl.setCheckable(True)
        self.but_stim_bl.setChecked(True)
        self.but_stim_bl.setObjectName("stim_bl")

        # -------------------------------------
        self.cmbChirpType = QComboBox(self)
        qcmb_box_populate(self.cmbChirpType, self.cmb_stim_chirp_items, self.chirp_type)

        self.cmbImpulseType = QComboBox(self)
        qcmb_box_populate(
            self.cmbImpulseType, self.cmb_stim_impulse_items, self.impulse_type)

        self.cmbSinusoidType = QComboBox(self)
        qcmb_box_populate(
            self.cmbSinusoidType, self.cmb_stim_sinusoid_items, self.sinusoid_type)

        self.cmbPeriodicType = QComboBox(self)
        qcmb_box_populate(self.cmbPeriodicType, self.cmb_stim_periodic_items,
                          self.cmb_stim_periodic_item)

        self.cmbModulationType = QComboBox(self)
        qcmb_box_populate(
            self.cmbModulationType, self.cmb_stim_modulation_items,
            self.cmb_stim_modulation_item)

        # -------------------------------------
        self.chk_step_err = QPushButton("Error", self)
        self.chk_step_err.setToolTip("<span>Display the step response error.</span>")
        self.chk_step_err.setMaximumWidth(qtext_width(text="Error "))
        self.chk_step_err.setCheckable(True)
        self.chk_step_err.setChecked(False)
        self.chk_step_err.setObjectName("stim_step_err")

        layHCmbStim = QHBoxLayout()
        layHCmbStim.addWidget(self.cmbStimulus)
        layHCmbStim.addWidget(self.cmbImpulseType)
        layHCmbStim.addWidget(self.cmbSinusoidType)
        layHCmbStim.addWidget(self.cmbChirpType)
        layHCmbStim.addWidget(self.cmbPeriodicType)
        layHCmbStim.addWidget(self.cmbModulationType)
        layHCmbStim.addWidget(self.but_stim_bl)
        layHCmbStim.addWidget(self.lblStimPar1)
        layHCmbStim.addWidget(self.ledStimPar1)
        layHCmbStim.addWidget(self.chk_step_err)

        self.lblDC = QLabel(to_html("DC =", frmt='bi'), self)
        self.ledDC = QLineEdit(self)
        self.ledDC.setText(str(self.DC))
        self.ledDC.setToolTip("DC Level")
        self.ledDC.setObjectName("stimDC")

        layHStimDC = QHBoxLayout()
        layHStimDC.addWidget(self.lblDC)
        layHStimDC.addWidget(self.ledDC)

        # ======================================================================
        self.lblAmp1 = QLabel(to_html("&nbsp;A_1", frmt='bi') + " =", self)
        self.ledAmp1 = QLineEdit(self)
        self.ledAmp1.setText(str(self.A1))
        self.ledAmp1.setToolTip(
            "Stimulus amplitude, complex values like 3j - 1 are allowed")
        self.ledAmp1.setObjectName("stimAmp1")

        self.lblAmp2 = QLabel(to_html("&nbsp;A_2", frmt='bi') + " =", self)
        self.ledAmp2 = QLineEdit(self)
        self.ledAmp2.setText(str(self.A2))
        self.ledAmp2.setToolTip(
            "Stimulus amplitude 2, complex values like 3j - 1 are allowed")
        self.ledAmp2.setObjectName("stimAmp2")
        # ----------------------------------------------
        self.lblPhi1 = QLabel(to_html("&nbsp;&phi;_1", frmt='bi') + " =", self)
        self.ledPhi1 = QLineEdit(self)
        self.ledPhi1.setText(str(self.phi1))
        self.ledPhi1.setToolTip("Stimulus phase")
        self.ledPhi1.setObjectName("stimPhi1")
        self.lblPhU1 = QLabel(to_html("&deg;", frmt='b'), self)

        self.lblPhi2 = QLabel(to_html("&nbsp;&phi;_2", frmt='bi') + " =", self)
        self.ledPhi2 = QLineEdit(self)
        self.ledPhi2.setText(str(self.phi2))
        self.ledPhi2.setToolTip("Stimulus phase 2")
        self.ledPhi2.setObjectName("stimPhi2")
        self.lblPhU2 = QLabel(to_html("&deg;", frmt='b'), self)
        # ----------------------------------------------
        self.lbl_T1 = QLabel(to_html("&nbsp;T_1", frmt='bi') + " =", self)
        self.led_T1 = QLineEdit(self)
        self.led_T1.setText(str(self.T1))
        self.led_T1.setToolTip("Time shift")
        self.led_T1.setObjectName("stimT1")
        self.lbl_TU1 = QLabel(to_html("T_S", frmt='b'), self)

        self.lbl_T2 = QLabel(to_html("&nbsp;T_2", frmt='bi') + " =", self)
        self.led_T2 = QLineEdit(self)
        self.led_T2.setText(str(self.T2))
        self.led_T2.setToolTip("Time shift 2")
        self.led_T2.setObjectName("stimT2")
        self.lbl_TU2 = QLabel(to_html("T_S", frmt='b'), self)
        # ---------------------------------------------
        self.lbl_TW1 = QLabel(to_html("&nbsp;&Delta;T_1", frmt='bi') + " =", self)
        self.led_TW1 = QLineEdit(self)
        self.led_TW1.setText(str(self.TW1))
        self.led_TW1.setToolTip("Time width")
        self.led_TW1.setObjectName("stimTW1")
        self.lbl_TWU1 = QLabel(to_html("T_S", frmt='b'), self)

        self.lbl_TW2 = QLabel(to_html("&nbsp;&Delta;T_2", frmt='bi') + " =", self)
        self.led_TW2 = QLineEdit(self)
        self.led_TW2.setText(str(self.TW2))
        self.led_TW2.setToolTip("Time width 2")
        self.led_TW2.setObjectName("stimTW2")
        self.lbl_TWU2 = QLabel(to_html("T_S", frmt='b'), self)
        # ----------------------------------------------
        self.txtFreq1_f = to_html("&nbsp;f_1", frmt='bi') + " ="
        self.txtFreq1_k = to_html("&nbsp;k_1", frmt='bi') + " ="
        self.lblFreq1 = QLabel(self.txtFreq1_f, self)
        self.ledFreq1 = QLineEdit(self)
        self.ledFreq1.setText(str(self.f1))
        self.ledFreq1.setToolTip("Stimulus frequency")
        self.ledFreq1.setObjectName("stimFreq1")
        self.lblFreqUnit1 = QLabel("f_S", self)

        self.txtFreq2_f = to_html("&nbsp;f_2", frmt='bi') + " ="
        self.txtFreq2_k = to_html("&nbsp;k_2", frmt='bi') + " ="
        self.lblFreq2 = QLabel(self.txtFreq2_f, self)
        self.ledFreq2 = QLineEdit(self)
        self.ledFreq2.setText(str(self.f2))
        self.ledFreq2.setToolTip("Stimulus frequency 2")
        self.ledFreq2.setObjectName("stimFreq2")
        self.lblFreqUnit2 = QLabel("f_S", self)
        # ----------------------------------------------
        self.lbl_BW1 = QLabel(to_html(self.tr("&nbsp;BW_1"), frmt='bi') + " =", self)
        self.led_BW1 = QLineEdit(self)
        self.led_BW1.setText(str(self.BW1))
        self.led_BW1.setToolTip(self.tr("Relative bandwidth"))
        self.led_BW1.setObjectName("stimBW1")

        self.lbl_BW2 = QLabel(to_html(self.tr("&nbsp;BW_2"), frmt='bi') + " =", self)
        self.led_BW2 = QLineEdit(self)
        self.led_BW2.setText(str(self.BW2))
        self.led_BW2.setToolTip(self.tr("Relative bandwidth 2"))
        self.led_BW2.setObjectName("stimBW2")
        # ----------------------------------------------
        self.lblNoise = QLabel(to_html("&nbsp;Noise", frmt='bi'), self)
        self.cmbNoise = QComboBox(self)
        qcmb_box_populate(self.cmbNoise, self.cmb_stim_noise_items, self.noise)

        self.lblNoi = QLabel("not initialized", self)
        self.ledNoi = QLineEdit(self)
        self.ledNoi.setText(str(self.noi))
        self.ledNoi.setToolTip("not initialized")
        self.ledNoi.setObjectName("stimNoi")

        layGStim = QGridLayout()

        layGStim.addLayout(layHCmbStim, 0, 1)
        layGStim.addLayout(layHStimDC, 1, 1)

        layGStim.addWidget(self.lblAmp1, 0, 2)
        layGStim.addWidget(self.lblAmp2, 1, 2)

        layGStim.addWidget(self.ledAmp1, 0, 3)
        layGStim.addWidget(self.ledAmp2, 1, 3)

        layGStim.addWidget(self.lblPhi1, 0, 4)
        layGStim.addWidget(self.lblPhi2, 1, 4)

        layGStim.addWidget(self.ledPhi1, 0, 5)
        layGStim.addWidget(self.ledPhi2, 1, 5)

        layGStim.addWidget(self.lblPhU1, 0, 6)
        layGStim.addWidget(self.lblPhU2, 1, 6)

        layGStim.addWidget(self.lbl_T1, 0, 7)
        layGStim.addWidget(self.lbl_T2, 1, 7)

        layGStim.addWidget(self.led_T1, 0, 8)
        layGStim.addWidget(self.led_T2, 1, 8)

        layGStim.addWidget(self.lbl_TU1, 0, 9)
        layGStim.addWidget(self.lbl_TU2, 1, 9)

        layGStim.addWidget(self.lbl_TW1, 0, 10)
        layGStim.addWidget(self.lbl_TW2, 1, 10)

        layGStim.addWidget(self.led_TW1, 0, 11)
        layGStim.addWidget(self.led_TW2, 1, 11)

        layGStim.addWidget(self.lbl_TWU1, 0, 12)
        layGStim.addWidget(self.lbl_TWU2, 1, 12)

        layGStim.addWidget(self.lblFreq1, 0, 13)
        layGStim.addWidget(self.lblFreq2, 1, 13)

        layGStim.addWidget(self.ledFreq1, 0, 14)
        layGStim.addWidget(self.ledFreq2, 1, 14)

        layGStim.addWidget(self.lblFreqUnit1, 0, 15)
        layGStim.addWidget(self.lblFreqUnit2, 1, 15)

        layGStim.addWidget(self.lbl_BW1, 0, 16)
        layGStim.addWidget(self.lbl_BW2, 1, 16)

        layGStim.addWidget(self.led_BW1, 0, 17)
        layGStim.addWidget(self.led_BW2, 1, 17)

        layGStim.addWidget(self.lblNoise, 0, 18)
        layGStim.addWidget(self.lblNoi, 1, 18)

        layGStim.addWidget(self.cmbNoise, 0, 19)
        layGStim.addWidget(self.ledNoi, 1, 19)

        # ----------------------------------------------
        self.lblStimFormula = QLabel(to_html("x =", frmt='bi'), self)
        self.ledStimFormula = QLineEdit(self)
        self.ledStimFormula.setText(str(self.stim_formula))
        self.ledStimFormula.setToolTip(
            "<span>Enter formula for stimulus in numexpr syntax.</span>")
        self.ledStimFormula.setObjectName("stimFormula")

        layH_stim_formula = QHBoxLayout()
        layH_stim_formula.addWidget(self.lblStimFormula)
        layH_stim_formula.addWidget(self.ledStimFormula, 10)

        # ----------------------------------------------------------------------
        # Main Widget
        # ----------------------------------------------------------------------
        layH_stim_par = QHBoxLayout()
        layH_stim_par.addLayout(layGStim)

        layV_stim = QVBoxLayout()
        layV_stim.addLayout(layH_stim_par)
        layV_stim.addLayout(layH_stim_formula)

        layH_stim = QHBoxLayout()
        layH_stim.addLayout(layV_stim)
        layH_stim.addStretch(10)

        self.wdg_stim = QWidget(self)
        self.wdg_stim.setLayout(layH_stim)
        self.wdg_stim.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        # ----------------------------------------------------------------------
        # Event Filter
        # ----------------------------------------------------------------------
        # frequency related widgets are scaled with f_s, requiring special handling
        self.ledFreq1.installEventFilter(self)
        self.ledFreq2.installEventFilter(self)
        self.led_T1.installEventFilter(self)
        self.led_T2.installEventFilter(self)
        self.led_TW1.installEventFilter(self)
        self.led_TW2.installEventFilter(self)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # --- stimulus control ---
        self.but_stim_bl.clicked.connect(self._enable_stim_widgets)
        self.chk_step_err.clicked.connect(self._enable_stim_widgets)
        self.cmbStimulus.currentIndexChanged.connect(self._enable_stim_widgets)

        self.cmbNoise.currentIndexChanged.connect(self._update_noi)
        self.ledNoi.editingFinished.connect(self._update_noi)
        self.ledAmp1.editingFinished.connect(self._update_amp1)
        self.ledAmp2.editingFinished.connect(self._update_amp2)
        self.ledPhi1.editingFinished.connect(self._update_phi1)
        self.ledPhi2.editingFinished.connect(self._update_phi2)
        self.led_BW1.editingFinished.connect(self._update_BW1)
        self.led_BW2.editingFinished.connect(self._update_BW2)

        self.cmbImpulseType.currentIndexChanged.connect(self._update_impulse_type)
        self.cmbSinusoidType.currentIndexChanged.connect(self._update_sinusoid_type)
        self.cmbChirpType.currentIndexChanged.connect(self._update_chirp_type)
        self.cmbPeriodicType.currentIndexChanged.connect(self._update_periodic_type)
        self.cmbModulationType.currentIndexChanged.connect(self._update_modulation_type)

        self.ledDC.editingFinished.connect(self._update_DC)
        self.ledStimFormula.editingFinished.connect(self._update_stim_formula)
        self.ledStimPar1.editingFinished.connect(self._update_stim_par1)

# ------------------------------------------------------------------------------
    def update_freq_units(self):
        """
        Update labels referrring to frequency specs
        """

        if fb.fil[0]['freq_specs_unit'] == 'k':
            f_unit = ''
            t_unit = ''
            self.lblFreq1.setText(self.txtFreq1_k)
            self.lblFreq2.setText(self.txtFreq2_k)
        else:
            f_unit = fb.fil[0]['plt_fUnit']
            t_unit = fb.fil[0]['plt_tUnit'].replace(r"$\mu$", "&mu;")
            self.lblFreq1.setText(self.txtFreq1_f)
            self.lblFreq2.setText(self.txtFreq2_f)

        if f_unit in {"f_S", "f_Ny"}:
            unit_frmt = "i"  # italic
        else:
            unit_frmt = None  # don't print units like kHz in italic

        self.lblFreqUnit1.setText(to_html(f_unit, frmt=unit_frmt))
        self.lblFreqUnit2.setText(to_html(f_unit, frmt=unit_frmt))
        self.lbl_TU1.setText(to_html(t_unit, frmt=unit_frmt))
        self.lbl_TU2.setText(to_html(t_unit, frmt=unit_frmt))

# ------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by the monitored widgets (ledFreq1 and 2 and T1 / T2).
        Source and type of all events generated by monitored objects are passed
         to this eventFilter, evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (``QEvent.FocusIn``), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (``QEvent.FocusOut``), store
          current value normalized to f_S with full precision (only if
          ``spec_edited == True``) and display the stored value in selected format

          Emit 'ui_changed':'stim'
        """
        def _reload_entry(source):
            """ Reload text entry for active line edit field in rounded format """
            if source.objectName() == "stimFreq1":
                source.setText(str(params['FMT'].format(self.f1 * self.f_scale)))
            elif source.objectName() == "stimFreq2":
                source.setText(str(params['FMT'].format(self.f2 * self.f_scale)))
            elif source.objectName() == "stimT1":
                source.setText(str(params['FMT'].format(self.T1 * self.t_scale)))
            elif source.objectName() == "stimT2":
                source.setText(str(params['FMT'].format(self.T2 * self.t_scale)))
            elif source.objectName() == "stimTW1":
                source.setText(str(params['FMT'].format(self.TW1 * self.t_scale)))
            elif source.objectName() == "stimTW2":
                source.setText(str(params['FMT'].format(self.TW2 * self.t_scale)))

        def _store_entry(source):
            if self.spec_edited:
                if source.objectName() == "stimFreq1":
                    self.f1 = safe_eval(
                       source.text(), self.f1 * self.f_scale,
                       return_type='float') / self.f_scale
                    source.setText(str(params['FMT'].format(self.f1 * self.f_scale)))

                elif source.objectName() == "stimFreq2":
                    self.f2 = safe_eval(
                        source.text(), self.f2 * self.f_scale,
                        return_type='float') / self.f_scale
                    source.setText(str(params['FMT'].format(self.f2 * self.f_scale)))

                elif source.objectName() == "stimT1":
                    self.T1 = safe_eval(
                        source.text(), self.T1 * self.t_scale,
                        return_type='float') / self.t_scale
                    source.setText(str(params['FMT'].format(self.T1 * self.t_scale)))

                elif source.objectName() == "stimT2":
                    self.T2 = safe_eval(
                        source.text(), self.T2 * self.t_scale,
                        return_type='float') / self.t_scale
                    source.setText(str(params['FMT'].format(self.T2 * self.t_scale)))

                elif source.objectName() == "stimTW1":
                    self.TW1 = safe_eval(
                        source.text(), self.TW1 * self.t_scale, sign='pos',
                        return_type='float') / self.t_scale
                    source.setText(str(params['FMT'].format(self.TW1 * self.t_scale)))

                elif source.objectName() == "stimTW2":
                    self.TW2 = safe_eval(
                        source.text(), self.TW2 * self.t_scale, sign='pos',
                        return_type='float') / self.t_scale
                    source.setText(str(params['FMT'].format(self.TW2 * self.t_scale)))

                self.spec_edited = False  # reset flag
                self._update_scale_impz()
                self.emit({'ui_changed': 'stim'})

            # nothing has changed, but display frequencies in rounded format anyway
            else:
                _reload_entry(source)
        # --------------------------------------------------------------------

#        if isinstance(source, QLineEdit):
#        if source.objectName() in {"stimFreq1","stimFreq2"}:
        if event.type() in {QEvent.FocusIn, QEvent.KeyPress, QEvent.FocusOut}:
            if event.type() == QEvent.FocusIn:
                self.spec_edited = False
                self.update_freqs()
            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True  # entry has been changed
                key = event.key()
                if key in {Qt.Key_Return, Qt.Key_Enter}:
                    _store_entry(source)
                elif key == Qt.Key_Escape:  # revert changes
                    self.spec_edited = False
                    _reload_entry(source)

            elif event.type() == QEvent.FocusOut:
                _store_entry(source)

        # Call base class method to continue normal event processing:
        return super(Plot_Tran_Stim_UI, self).eventFilter(source, event)

    # -------------------------------------------------------------
    def recalc_freqs(self):
        """
        Update normalized frequencies if required. This is called by via signal
        ['ui_changed':'f_S'] from plot_impz.process_sig_rx
        """
        if fb.fil[0]['freq_locked']:
            self.f1 *= fb.fil[0]['f_S_prev'] / fb.fil[0]['f_S']
            self.f2 *= fb.fil[0]['f_S_prev'] / fb.fil[0]['f_S']
            self.T1 *= fb.fil[0]['f_S'] / fb.fil[0]['f_S_prev']
            self.T2 *= fb.fil[0]['f_S'] / fb.fil[0]['f_S_prev']
            self.TW1 *= fb.fil[0]['f_S'] / fb.fil[0]['f_S_prev']
            self.TW2 *= fb.fil[0]['f_S'] / fb.fil[0]['f_S_prev']

        self._update_scale_impz()

        self.update_freqs()

        self.emit({'ui_changed': 'f1_f2'})

    # -------------------------------------------------------------
    def update_freqs(self):
        """
        `update_freqs()` is called:

        - when one of the stimulus frequencies has changed via eventFilter()
        - sampling frequency has been changed via signal ['ui_changed':'f_S']
          from plot_impz.process_sig_rx -> self.recalc_freqs

        The sampling frequency is loaded from filter dictionary and stored as
        `self.f_scale` (except when the frequency unit is k when `f_scale = self.N_FFT`).

        Frequency field entries are always stored normalized w.r.t. f_S in the
        dictionary: When the `f_S` lock button is unlocked, only the displayed
        values for frequency entries are updated with f_S, not the dictionary.

        When the `f_S` lock button is pressed, the absolute frequency values in
        the widget fields are kept constant, and the dictionary entries are updated.

        """

        # recalculate displayed freq spec values for (maybe) changed f_S
        if fb.fil[0]['freq_specs_unit'] == 'k':
            self.f_scale = self.N_FFT
        else:
            self.f_scale = fb.fil[0]['f_S']
        self.t_scale = fb.fil[0]['T_S']

        if self.ledFreq1.hasFocus():
            # widget has focus, show full precision
            self.ledFreq1.setText(str(self.f1 * self.f_scale))

        elif self.ledFreq2.hasFocus():
            self.ledFreq2.setText(str(self.f2 * self.f_scale))

        elif self.led_T1.hasFocus():
            self.led_T1.setText(str(self.T1 * self.t_scale))

        elif self.led_T2.hasFocus():
            self.led_T2.setText(str(self.T2 * self.t_scale))

        elif self.led_TW1.hasFocus():
            self.led_TW1.setText(str(self.TW1 * self.t_scale))

        elif self.led_TW2.hasFocus():
            self.led_TW2.setText(str(self.TW2 * self.t_scale))

        else:
            # widgets have no focus, round the display
            self.ledFreq1.setText(str(params['FMT'].format(self.f1 * self.f_scale)))
            self.ledFreq2.setText(str(params['FMT'].format(self.f2 * self.f_scale)))
            self.led_T1.setText(str(params['FMT'].format(self.T1 * self.t_scale)))
            self.led_T2.setText(str(params['FMT'].format(self.T2 * self.t_scale)))
            self.led_TW1.setText(str(params['FMT'].format(self.TW1 * self.t_scale)))
            self.led_TW2.setText(str(params['FMT'].format(self.TW2 * self.t_scale)))

        self.update_freq_units()  # TODO: should only be called at f_S / unit update

    # -------------------------------------------------------------
    def _enable_stim_widgets(self):
        """ Enable / disable widgets depending on the selected stimulus """
        self.cmb_stim = qget_cmb_box(self.cmbStimulus)
        if self.cmb_stim == "impulse":
            self.stim = qget_cmb_box(self.cmbImpulseType)
            # recalculate the energy scaling for impulse functions
            self._update_scale_impz()

        elif self.cmb_stim == "sinusoid":
            self.stim = qget_cmb_box(self.cmbSinusoidType)
        elif self.cmb_stim == "periodic":
            self.stim = qget_cmb_box(self.cmbPeriodicType)
        elif self.cmb_stim == "modulation":
            self.stim = qget_cmb_box(self.cmbModulationType)
        else:
            self.stim = self.cmb_stim

        # read out which stimulus widgets are enabled
        stim_wdg = self.stim_wdg_dict[self.stim]

        self.lblDC.setVisible("dc" in stim_wdg)
        self.ledDC.setVisible("dc" in stim_wdg)

        self.chk_step_err.setVisible(self.stim == "step")

        self.lblStimPar1.setVisible("par1" in stim_wdg)
        self.ledStimPar1.setVisible("par1" in stim_wdg)

        self.but_stim_bl.setVisible("bl" in stim_wdg)

        self.lblAmp1.setVisible("a1" in stim_wdg)
        self.ledAmp1.setVisible("a1" in stim_wdg)
        self.lblPhi1.setVisible("phi1" in stim_wdg)
        self.ledPhi1.setVisible("phi1" in stim_wdg)
        self.lblPhU1.setVisible("phi1" in stim_wdg)
        self.lbl_T1.setVisible("T1" in stim_wdg)
        self.led_T1.setVisible("T1" in stim_wdg)
        self.lbl_TU1.setVisible("T1" in stim_wdg)
        self.lbl_TW1.setVisible("TW1" in stim_wdg)
        self.led_TW1.setVisible("TW1" in stim_wdg)
        self.lbl_TWU1.setVisible("TW1" in stim_wdg)
        self.lblFreq1.setVisible("f1" in stim_wdg)
        self.ledFreq1.setVisible("f1" in stim_wdg)
        self.lblFreqUnit1.setVisible("f1" in stim_wdg)
        self.lbl_BW1.setVisible("BW1" in stim_wdg)
        self.led_BW1.setVisible("BW1" in stim_wdg)

        self.lblAmp2.setVisible("a2" in stim_wdg)
        self.ledAmp2.setVisible("a2" in stim_wdg)
        self.lblPhi2.setVisible("phi2" in stim_wdg)
        self.ledPhi2.setVisible("phi2" in stim_wdg)
        self.lblPhU2.setVisible("phi2" in stim_wdg)
        self.lbl_T2.setVisible("T2" in stim_wdg)
        self.led_T2.setVisible("T2" in stim_wdg)
        self.lbl_TU2.setVisible("T2" in stim_wdg)
        self.lbl_TW2.setVisible("TW2" in stim_wdg)
        self.led_TW2.setVisible("TW2" in stim_wdg)
        self.lbl_TWU2.setVisible("TW2" in stim_wdg)
        self.lblFreq2.setVisible("f2" in stim_wdg)
        self.ledFreq2.setVisible("f2" in stim_wdg)
        self.lblFreqUnit2.setVisible("f2" in stim_wdg)
        self.lbl_BW2.setVisible("BW2" in stim_wdg)
        self.led_BW2.setVisible("BW2" in stim_wdg)
        self.lblStimFormula.setVisible(self.stim == "formula")
        self.ledStimFormula.setVisible(self.stim == "formula")

        self.cmbImpulseType.setVisible(self.cmb_stim == 'impulse')
        self.cmbSinusoidType.setVisible(self.cmb_stim == 'sinusoid')
        self.cmbChirpType.setVisible(self.cmb_stim == 'chirp')
        self.cmbPeriodicType.setVisible(self.cmb_stim == 'periodic')
        self.cmbModulationType.setVisible(self.cmb_stim == 'modulation')

        self.emit({'ui_changed': 'stim'})

    # -------------------------------------------------------------
    def _update_amp1(self):
        """ Update value for self.A1 from QLineEditWidget"""
        self.A1 = safe_eval(self.ledAmp1.text(), self.A1, return_type='cmplx')
        self.ledAmp1.setText(str(self.A1))
        self.emit({'ui_changed': 'a1'})

    def _update_amp2(self):
        """ Update value for self.A2 from the QLineEditWidget"""
        self.A2 = safe_eval(self.ledAmp2.text(), self.A2, return_type='cmplx')
        self.ledAmp2.setText(str(self.A2))
        self.emit({'ui_changed': 'a2'})

    def _update_phi1(self):
        """ Update value for self.phi1 from QLineEditWidget"""
        self.phi1 = safe_eval(self.ledPhi1.text(), self.phi1, return_type='float')
        self.ledPhi1.setText(str(self.phi1))
        self.emit({'ui_changed': 'phi1'})

    def _update_BW1(self):
        """ Update value for self.BW1 from QLineEditWidget"""
        self.BW1 = safe_eval(
            self.led_BW1.text(), self.BW1, return_type='float', sign='pos')
        self.led_BW1.setText(str(self.BW1))
        self._update_scale_impz()
        self.emit({'ui_changed': 'BW1'})

    def _update_BW2(self):
        """ Update value for self.BW2 from QLineEditWidget"""
        self.BW2 = safe_eval(
            self.led_BW2.text(), self.BW2, return_type='float', sign='pos')
        self.led_BW2.setText(str(self.BW2))
        self.emit({'ui_changed': 'BW2'})

    def _update_scale_impz(self):
        """
        recalculate the energy scaling for impulse functions when impulse type or
        relevant frequency / bandwidth parameter have been updated
        """
        if self.stim == "dirac":
            self.scale_impz = 1.
        elif self.stim == "sinc":
            self.scale_impz = self.f1 * 2
        elif self.stim == "gauss":
            self.scale_impz = self.f1 * 2 * self.BW1
        elif self.stim == "rect":
            self.scale_impz = 1. / self.TW1

    def _update_phi2(self):
        """ Update value for self.phi2 from the QLineEditWidget"""
        self.phi2 = safe_eval(self.ledPhi2.text(), self.phi2, return_type='float')
        self.ledPhi2.setText(str(self.phi2))
        self.emit({'ui_changed': 'phi2'})

    def _update_chirp_type(self):
        """ Update value for self.chirp_type from data field of ComboBox"""
        self.chirp_type = qget_cmb_box(self.cmbChirpType)
        self.emit({'ui_changed': 'chirp_type'})

    def _update_impulse_type(self):
        """ Update value for self.impulse_type from data field of ComboBox"""
        self.impulse_type = qget_cmb_box(self.cmbImpulseType)
        self._enable_stim_widgets()

    def _update_sinusoid_type(self):
        """ Update value for self.sinusoid_type from data field of ComboBox"""
        self.sinusoid_type = qget_cmb_box(self.cmbSinusoidType)
        self._enable_stim_widgets()

    def _update_periodic_type(self):
        """ Update value for self.periodic_type from data field of ComboBox"""
        self.periodic_type = qget_cmb_box(self.cmbPeriodicType)
        self._enable_stim_widgets()

    def _update_modulation_type(self):
        """ Update value for self.modulation_type from from data field of ComboBox"""
        self.modulation_type = qget_cmb_box(self.cmbModulationType)
        self._enable_stim_widgets()

    # -------------------------------------------------------------
    def _update_noi(self):
        """ Update type + value + label for self.noi for noise"""
        self.noise = qget_cmb_box(self.cmbNoise)
        self.lblNoi.setVisible(self.noise != 'none')
        self.ledNoi.setVisible(self.noise != 'none')
        if self.noise != 'none':
            self.noi = safe_eval(self.ledNoi.text(), 0, return_type='cmplx')
            self.ledNoi.setText(str(self.noi))
            if self.noise == 'gauss':
                self.lblNoi.setText(to_html("&nbsp;&sigma; =", frmt='bi'))
                self.ledNoi.setToolTip(
                    "<span>Standard deviation of statistical process,"
                    "noise power is <i>P</i> = &sigma;<sup>2</sup></span>")
            elif self.noise == 'uniform':
                self.lblNoi.setText(to_html("&nbsp;&Delta; =", frmt='bi'))
                self.ledNoi.setToolTip(
                    "<span>Interval size for uniformly distributed process (e.g. "
                    "quantization step size for quantization noise), centered around 0. "
                    "Noise power is <i>P</i> = &Delta;<sup>2</sup>/12.</span>")
            elif self.noise == 'prbs':
                self.lblNoi.setText(to_html("&nbsp;A =", frmt='bi'))
                self.ledNoi.setToolTip(
                    "<span>Amplitude of bipolar Pseudorandom Binary Sequence. "
                    "Noise power is <i>P</i> = A<sup>2</sup>.</span>")

            elif self.noise == 'mls':
                self.lblNoi.setText(to_html("&nbsp;A =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Amplitude of Maximum Length Sequence. "
                                       "Noise power is <i>P</i> = A<sup>2</sup>.</span>")
            elif self.noise == 'brownian':
                self.lblNoi.setText(to_html("&nbsp;&sigma; =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Standard deviation of the Gaussian process "
                                       "that is cumulated.</span>")

        self.emit({'ui_changed': 'noi'})

    def _update_DC(self):
        """ Update value for self.DC from the QLineEditWidget"""
        self.DC = safe_eval(self.ledDC.text(), 0, return_type='cmplx')
        self.ledDC.setText(str(self.DC))
        self.emit({'ui_changed': 'dc'})

    def _update_stim_formula(self):
        """Update string with formula to be evaluated by numexpr"""
        self.stim_formula = self.ledStimFormula.text().strip()
        self.ledStimFormula.setText(str(self.stim_formula))
        self.emit({'ui_changed': 'stim_formula'})

    def _update_stim_par1(self):
        """ Update value for self.par1 from QLineEditWidget"""
        self.stim_par1 = safe_eval(self.ledStimPar1.text(), self.stim_par1,
                                   sign='pos', return_type='float')
        self.ledStimPar1.setText(str(self.stim_par1))
        self.emit({'ui_changed': 'stim_par1'})


# ------------------------------------------------------------------------------
def main():
    import sys
    from pyfda.libs.compat import QApplication

    app = QApplication(sys.argv)

    mainw = Plot_Tran_Stim_UI(None)
    layVMain = QVBoxLayout()
    layVMain.addWidget(mainw.wdg_stim)
    layVMain.setContentsMargins(*params['wdg_margins'])  # (left, top, right, bottom)

    mainw.setLayout(layVMain)

    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    """ Run widget standalone with
        `python -m pyfda.plot_widgets.tran.plot_tran_stim_ui` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Plot_Tran_Stim_UI()

    layVMain = QVBoxLayout()
    layVMain.addWidget(mainw.wdg_stim)

    mainw.setLayout(layVMain)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
