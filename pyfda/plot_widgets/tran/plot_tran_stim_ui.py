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

from pyfda.libs.compat import (
    QWidget, QComboBox, QLineEdit, QLabel, QPushButton,
    pyqtSignal, QEvent, Qt, QHBoxLayout, QVBoxLayout, QGridLayout)

from pyfda.libs.pyfda_lib import to_html, safe_eval, pprint_log
import pyfda.filterbroker as fb
from pyfda.libs.pyfda_qt_lib import (
    qcmb_box_populate, qget_cmb_box, qtext_width, qstyle_widget, QVLine, PushButton)
# FMT string for QLineEdit fields, e.g. '{:.3g}'
from pyfda.pyfda_rc import params

import logging
logger = logging.getLogger(__name__)


class Plot_Tran_Stim_UI(QWidget):
    """
    Create the UI for the PlotImpz class
    """
    # incoming:
    sig_rx = pyqtSignal(object)
    # outgoing: from various UI elements to PlotImpz ('ui_local_changed':'xxx')
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
            logger.warning("Stopped infinite loop:\n{0}".format(
                pprint_log(dict_sig)))
            return
        elif 'view_changed' in dict_sig:
            if dict_sig['view_changed'] == 'f_S':
                self.normalize_freqs()

# ------------------------------------------------------------------------------
    def __init__(self, objectName='plot_tran_stim_ui_inst'):
        super().__init__()

        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        # initial settings
        self.setObjectName(objectName)
        self.N_FFT = 0  # TODO: FFT value needs to be passed here somehow?

        # stimuli
        self.cmb_stim_item = "impulse"
        self.cmb_stim_periodic_item = "rect_per"
        self.cmb_stim_modulation_item = "am"
        self.stim = "dirac"
        self.impulse_type = "dirac"
        self.sinusoid_type = "sine"

        self.chirp_type = "linear"
        self.cmb_file_io_default = "use"

        self.f1 = 0.02
        self.f2 = 0.03
        self.A1 = 1.0
        self.A2 = 0.0
        self.phi1 = self.phi2 = 0
        self.T1 = self.T2 = 0
        self.TW1 = self.TW2 = 10
        self.BW1 = self.BW2 = 0.5
        self.N1 = self.N2 = 5
        self.noi = 0.1
        self.noise = "none"
        self.mls_b = 8
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
            "diric":   {"dc", "a1", "T1", "N1", "f1", "noise"},

            "chirp":   {"dc", "a1", "phi1", "f1", "f2", "T2", "noise"},
            "triang":  {"dc", "a1", "phi1", "f1", "noise", "bl"},
            "saw":     {"dc", "a1", "phi1", "f1", "noise", "bl"},
            "rect_per": {"dc", "a1", "phi1", "f1", "noise", "bl", "par1"},
            "comb":    {"dc", "a1", "phi1", "f1", "noise"},
            "am":      {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
            "pmfm":    {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise"},
            "pwm":     {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "noise", "bl"},
            "formula": {"dc", "a1", "a2", "phi1", "phi2", "f1", "f2", "N1", "N2",
                        "T1", "T2", "BW1", "BW2", "noise"}
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

        # combobox tooltip + data / text / tooltip for file I/O usage
        self.cmb_file_io_items = [
            ("<span>Select data from File I/O widget</span>"),
            ("use", "Use", "<span><b>Use</b> file I/O data as stimuli.</span>"),
            ("add", "Add", "<span><b>Add</b> file I/O data to other stimuli</span>")
        ]

        # combobox tooltip + data / text / tooltip for periodic signals items
        self.cmb_stim_periodic_items = [
            "<span>Periodic functions with discontinuities.</span>",
            ("rect_per", "Rect", "<span>Rectangular signal with duty cycle &alpha;</span>"),
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
            ("diric", "Diric", "<span>Periodic sinc (Dirichlet) function, "
             "diric(x, N) = sin(Nx/2) / N*sin(x/2) with x = 2 pi f_1 n</span>")
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
            ("randint", "RandInt",
             "<span>Random integer sequence in the interval [0, <i>I</i>]</span>"),
            ("mls", "MLS",
             "<span>Maximum Length Sequence with amplitude <i>A</i> and maximum length "
             "2<sup><i>b</i></sup> - 1 after which the sequence is repeated.</span>"),
            ("brownian", "Brownian",
             "<span>Brownian (cumulated sum) process based on Gaussian noise with"
             " std. deviation &sigma;.</span>")
        ]

        # Dict with objectNames as keys and tuples with normalized variables
        # and scaling factors as values, e.g. {'led_f1': (self.f1, self.f_scale)}
        self.dict_filtered_widgets = {
            'led_f1': ('f1', 'f_scale'),
            'led_f2': ('f2', 'f_scale'),
            'led_T1': ('T1', 't_scale'),
            'led_T2': ('T2', 't_scale'),
            'led_TW1': ('TW1', 't_scale'),
            'led_TW2': ('TW2', 't_scale')
        }

        self._construct_UI()
        self._enable_stim_widgets()
        self._update_noi()

    def _construct_UI(self):
        # =====================================================================
        # Controls for stimuli
        # =====================================================================

        self.lbl_title_stim = QLabel("Stim:", objectName="large")
        #
        self.cmbStimulus = QComboBox(self)
        qcmb_box_populate(self.cmbStimulus,
                          self.cmb_stim_items, self.cmb_stim_item)

        self.lblStimPar1 = QLabel(to_html("&alpha; =", frmt='b'), self)
        self.ledStimPar1 = QLineEdit(self, objectName="ledStimPar1")
        self.ledStimPar1.setText("0.5")
        self.ledStimPar1.setToolTip("Duty Cycle, 0 ... 1")

        self.but_stim_bl = QPushButton(self, objectName="stim_bl")
        self.but_stim_bl.setText("BL")
        self.but_stim_bl.setToolTip(
            "<span>Bandlimit the signal to the Nyquist "
            "frequency to avoid aliasing. However, this is much slower "
            "to calculate especially for a large number of points.</span>")
        self.but_stim_bl.setMaximumWidth(qtext_width(text="BL "))
        self.but_stim_bl.setCheckable(True)
        self.but_stim_bl.setChecked(True)

        # -------------------------------------
        self.cmbChirpType = QComboBox(self)
        qcmb_box_populate(self.cmbChirpType,
                          self.cmb_stim_chirp_items, self.chirp_type)

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
        self.chk_step_err = QPushButton("Error", objectName="stim_step_err")
        self.chk_step_err.setToolTip(
            "<span>Display the step response error.</span>")
        self.chk_step_err.setMaximumWidth(qtext_width(text="Error "))
        self.chk_step_err.setCheckable(True)
        self.chk_step_err.setChecked(False)
        #
        self.but_file_io = PushButton("<", checkable=False)
        self.but_file_io.setToolTip(
            "<span>Use file length as number of data points.</span>")
        self.lbl_file_io = QLabel(to_html("&nbsp;File IO", frmt='bi'))
        self.cmb_file_io = QComboBox(self, objectName="cmb_file_io")
        qcmb_box_populate(
            self.cmb_file_io, self.cmb_file_io_items, self.cmb_file_io_default)

        # TODO: layH_file_io is instantiated in plot_impz, this is very hacky
        self.layH_file_io = QHBoxLayout()
        self.layH_file_io.addWidget(self.but_file_io)
        self.layH_file_io.addWidget(self.lbl_file_io)
        self.layH_file_io.addWidget(self.cmb_file_io)
        self.layH_file_io.setContentsMargins(0, 0, 0, 0)
        # -------------------------------------

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
        self.ledDC = QLineEdit(self, objectName="stimDC")
        self.ledDC.setText(str(self.DC))
        self.ledDC.setToolTip("DC Level")

        layHStimDC = QHBoxLayout()
        layHStimDC.addWidget(self.lblDC)
        layHStimDC.addWidget(self.ledDC)

        # ======================================================================
        self.lblAmp1 = QLabel(to_html("&nbsp;A_1", frmt='bi') + " =", self)
        self.ledAmp1 = QLineEdit(self, objectName="stimAmp1")
        self.ledAmp1.setText(str(self.A1))
        self.ledAmp1.setToolTip(
            "Stimulus amplitude; complex values like 3j - 1 are allowed")

        self.lblAmp2 = QLabel(to_html("&nbsp;A_2", frmt='bi') + " =", self)
        self.ledAmp2 = QLineEdit(self, objectName="stimAmp2")
        self.ledAmp2.setText(str(self.A2))
        self.ledAmp2.setToolTip(
            "Stimulus amplitude 2; complex values like 3j - 1 are allowed")
        # ----------------------------------------------
        self.lblPhi1 = QLabel(to_html("&nbsp;&phi;_1", frmt='bi') + " =", self)
        self.ledPhi1 = QLineEdit(self, objectName="stimPhi1")
        self.ledPhi1.setText(str(self.phi1))
        self.ledPhi1.setToolTip("Stimulus phase 1 in degrees")
        self.lblPhU1 = QLabel(to_html("&deg;", frmt='i'), self)

        self.lblPhi2 = QLabel(to_html("&nbsp;&phi;_2", frmt='bi') + " =", self)
        self.ledPhi2 = QLineEdit(self, objectName="stimPhi2")
        self.ledPhi2.setText(str(self.phi2))
        self.ledPhi2.setToolTip("Stimulus phase 2 in degrees")
        self.lblPhU2 = QLabel(to_html("&deg;", frmt='i'), self)
        # ----------------------------------------------
        self.lbl_T1 = QLabel(to_html("&nbsp;T_1", frmt='bi') + " =", self)
        self.led_T1 = QLineEdit(self, objectName="led_T1")
        self.led_T1.setText(str(self.T1))
        self.led_T1.setToolTip("Time shift 1")
        self.lbl_TU1 = QLabel(to_html("T_S", frmt='i'), self)

        self.lbl_T2 = QLabel(to_html("&nbsp;T_2", frmt='bi') + " =", self)
        self.led_T2 = QLineEdit(self, objectName="led_T2")
        self.led_T2.setText(str(self.T2))
        self.led_T2.setToolTip("Time shift 2")
        self.lbl_TU2 = QLabel(to_html("T_S", frmt='i'), self)

        # ----------------------------------------------
        self.lbl_N1 = QLabel(to_html("&nbsp;N_1", frmt='bi') + " =", self)
        self.led_N1 = QLineEdit(self, objectName="stimN1")
        self.led_N1.setText(str(self.N1))
        self.led_N1.setToolTip("Parameter N1")

        self.lbl_N2 = QLabel(to_html("&nbsp;N_2", frmt='bi') + " =", self)
        self.led_N2 = QLineEdit(self, objectName="stimN2")
        self.led_N2.setText(str(self.N2))
        self.led_N2.setToolTip("Parameter N2")
        # ---------------------------------------------
        self.lbl_TW1 = QLabel(
            to_html("&nbsp;&Delta;T_1", frmt='bi') + " =", self)
        self.led_TW1 = QLineEdit(self, objectName="led_TW1")
        self.led_TW1.setText(str(self.TW1))
        self.led_TW1.setToolTip("Time width")
        self.lbl_TWU1 = QLabel(to_html("T_S", frmt='i'), self)

        self.lbl_TW2 = QLabel(
            to_html("&nbsp;&Delta;T_2", frmt='bi') + " =", self)
        self.led_TW2 = QLineEdit(self, objectName="led_TW2")
        self.led_TW2.setText(str(self.TW2))
        self.led_TW2.setToolTip("Time width 2")
        self.lbl_TWU2 = QLabel(to_html("T_S", frmt='i'), self)
        # ----------------------------------------------
        self.txtFreq1_f = to_html("&nbsp;f_1", frmt='bi') + " ="
        self.txtFreq1_F = to_html("&nbsp;F_1", frmt='bi') + " ="
        self.txtFreq1_k = to_html("&nbsp;k_1", frmt='bi') + " ="
        self.lblFreq1 = QLabel(self.txtFreq1_f, self)
        self.led_f1 = QLineEdit(self, objectName="led_f1")
        self.led_f1.setText(str(self.f1))
        self.led_f1.setToolTip("Stimulus frequency")
        self.lblFreqUnit1 = QLabel(to_html("f_S", frmt='i'), self)

        self.txtFreq2_f = to_html("&nbsp;f_2", frmt='bi') + " ="
        self.txtFreq2_F = to_html("&nbsp;F_2", frmt='bi') + " ="
        self.txtFreq2_k = to_html("&nbsp;k_2", frmt='bi') + " ="
        self.lblFreq2 = QLabel(self.txtFreq2_f, self)
        self.led_f2 = QLineEdit(self, objectName="led_f2")
        self.led_f2.setText(str(self.f2))
        self.led_f2.setToolTip("Stimulus frequency 2")
        self.lblFreqUnit2 = QLabel(to_html("f_S", frmt='i'), self)
        # ----------------------------------------------
        self.lbl_BW1 = QLabel(
            to_html(self.tr("&nbsp;BW_1"), frmt='bi') + " =", self)
        self.led_BW1 = QLineEdit(self, objectName="stimBW1")
        self.led_BW1.setText(str(self.BW1))
        self.led_BW1.setToolTip(self.tr("Relative bandwidth"))

        self.lbl_BW2 = QLabel(
            to_html(self.tr("&nbsp;BW_2"), frmt='bi') + " =", self)
        self.led_BW2 = QLineEdit(self, objectName="stimBW2")
        self.led_BW2.setText(str(self.BW2))
        self.led_BW2.setToolTip(self.tr("Relative bandwidth 2"))
        # ----------------------------------------------
        self.lblNoise = QLabel(to_html("&nbsp;Noise", frmt='bi'), self)
        self.cmb_stim_noise = QComboBox(self)
        qcmb_box_populate(self.cmb_stim_noise, self.cmb_stim_noise_items, self.noise)

        line2 = QVLine()
        self.lblNoi = QLabel("not initialized", self)
        self.ledNoi = QLineEdit(self, objectName="stimNoi")
        self.ledNoi.setMaximumWidth(self.cmb_stim_noise.width())
        self.ledNoi.setText(str(self.noi))
        self.ledNoi.setToolTip("not initialized")
        self.lblNoi_par = QLabel("not initialized", self)
        self.ledNoi_par = QLineEdit(self)
        self.ledNoi_par.setMaximumWidth(qtext_width(N_x=4))
        layH_noi_params = QHBoxLayout()
        layH_noi_params.addWidget(self.ledNoi)
        layH_noi_params.addWidget(self.lblNoi_par)
        layH_noi_params.addWidget(self.ledNoi_par)

        # ----------------------------------------------
        # Widget and Layout containing formula editor
        self.lblStimFormula = QLabel(to_html("x =", frmt='bi'), self)
        self.ledStimFormula = QLineEdit(self, objectName="stimFormula")
        self.ledStimFormula.setText(str(self.stim_formula))
        self.ledStimFormula.setToolTip(
            "<span>Enter formula for stimulus in numexpr syntax, using the index "
            "<i>n</i> or the time vector <i>t</i> and the following UI settings: "
            + to_html("A_1, A_2, phi_1, phi_2, f_1, f_2, T_1, T_2, BW_1, BW_2",
                      frmt='i') + ".</span>")

        layH_formula_stim = QHBoxLayout()
        layH_formula_stim.addWidget(self.lblStimFormula)
        layH_formula_stim.addWidget(self.ledStimFormula)
        layH_formula_stim.setContentsMargins(0, 0, 0, 0)
        self.wdg_formula_stim = QWidget(self)
        self.wdg_formula_stim.setLayout(layH_formula_stim)
        self.wdg_formula_stim.setContentsMargins(0, 0, 0, 0)

        # Main grid layout for all control elements
        layG_ctrl_stim = QGridLayout()
        i = 0
        layG_ctrl_stim.addLayout(layHCmbStim, 0, i)
        layG_ctrl_stim.addLayout(layHStimDC, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lblAmp1, 0, i)
        layG_ctrl_stim.addWidget(self.lblAmp2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.ledAmp1, 0, i)
        layG_ctrl_stim.addWidget(self.ledAmp2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lblFreq1, 0, i)
        layG_ctrl_stim.addWidget(self.lblFreq2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.led_f1, 0, i)
        layG_ctrl_stim.addWidget(self.led_f2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lblFreqUnit1, 0, i)
        layG_ctrl_stim.addWidget(self.lblFreqUnit2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lblPhi1, 0, i)
        layG_ctrl_stim.addWidget(self.lblPhi2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.ledPhi1, 0, i)
        layG_ctrl_stim.addWidget(self.ledPhi2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lblPhU1, 0, i)
        layG_ctrl_stim.addWidget(self.lblPhU2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lbl_BW1, 0, i)
        layG_ctrl_stim.addWidget(self.lbl_BW2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.led_BW1, 0, i)
        layG_ctrl_stim.addWidget(self.led_BW2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lbl_T1, 0, i)
        layG_ctrl_stim.addWidget(self.lbl_T2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.led_T1, 0, i)
        layG_ctrl_stim.addWidget(self.led_T2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lbl_TU1, 0, i)
        layG_ctrl_stim.addWidget(self.lbl_TU2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lbl_N1, 0, i)
        layG_ctrl_stim.addWidget(self.lbl_N2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.led_N1, 0, i)
        layG_ctrl_stim.addWidget(self.led_N2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lbl_TW1, 0, i)
        layG_ctrl_stim.addWidget(self.lbl_TW2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.led_TW1, 0, i)
        layG_ctrl_stim.addWidget(self.led_TW2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.lbl_TWU1, 0, i)
        layG_ctrl_stim.addWidget(self.lbl_TWU2, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(line2, 0, i, 2, 1)
        i += 1
        layG_ctrl_stim.addWidget(self.lblNoise, 0, i)
        layG_ctrl_stim.addWidget(self.lblNoi, 1, i)
        i += 1
        layG_ctrl_stim.addWidget(self.cmb_stim_noise, 0, i)
        layG_ctrl_stim.addLayout(layH_noi_params, 1, i)
        i += 1
        layG_ctrl_stim.setColumnStretch(i, 1)
        i += 1
        # place formula widget in row 2, stretching over i columns
        layG_ctrl_stim.addWidget(self.wdg_formula_stim, 2, 0, 1, i)

        # ----------------------------------------------------------------------
        # Main Widget
        # ----------------------------------------------------------------------

        # Widget with the text block "Stim:"
        layH_title_stim = QHBoxLayout()
        layH_title_stim.addWidget(self.lbl_title_stim)
        self.wdg_title_stim = QWidget(self)
        self.wdg_title_stim.setLayout(layH_title_stim)
        self.wdg_title_stim.setContentsMargins(0, 0, 0, 0)

        # Widget containing all control elements for stimuli
        self.wdg_ctrl_stim = QWidget(self)
        self.wdg_ctrl_stim.setLayout(layG_ctrl_stim)

        layH_stim = QHBoxLayout()
        layH_stim.addWidget(self.wdg_title_stim)
        layH_stim.addWidget(self.wdg_ctrl_stim)
        layH_stim.setContentsMargins(0, 0, 0, 0)

        self.wdg_stim = QWidget(self, objectName="transparent")
        self.wdg_stim.setLayout(layH_stim)
        self.wdg_stim.setContentsMargins(0, 0, 0, 0)

        # ----------------------------------------------------------------------
        # Initialization
        # ----------------------------------------------------------------------
        self.normalize_freqs()  # set f_scale and t_scale factors

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

        self.cmb_stim_noise.currentIndexChanged.connect(self._update_noi)
        self.ledNoi.editingFinished.connect(self._update_noi)
        self.ledNoi_par.editingFinished.connect(self._update_noi)
        self.ledAmp1.editingFinished.connect(self._update_amp1)
        self.ledAmp2.editingFinished.connect(self._update_amp2)
        self.ledPhi1.editingFinished.connect(self._update_phi1)
        self.ledPhi2.editingFinished.connect(self._update_phi2)
        self.led_BW1.editingFinished.connect(self._update_BW1)
        self.led_BW2.editingFinished.connect(self._update_BW2)
        self.led_N1.editingFinished.connect(self._update_N1)
        self.led_N2.editingFinished.connect(self._update_N2)

        self.cmb_file_io.currentIndexChanged.connect(self._enable_stim_widgets)
        self.cmbImpulseType.currentIndexChanged.connect(
            self._update_impulse_type)
        self.cmbSinusoidType.currentIndexChanged.connect(
            self._update_sinusoid_type)
        self.cmbChirpType.currentIndexChanged.connect(self._update_chirp_type)
        self.cmbPeriodicType.currentIndexChanged.connect(
            self._update_periodic_type)
        self.cmbModulationType.currentIndexChanged.connect(
            self._update_modulation_type)

        self.ledDC.editingFinished.connect(self._update_DC)
        self.ledStimFormula.editingFinished.connect(self._update_stim_formula)
        self.ledStimPar1.editingFinished.connect(self._update_stim_par1)

        # ----------------------------------------------------------------------
        # Event Filter
        # ----------------------------------------------------------------------
        # time / frequency related widgets have to be scaled with f_s, this
        # special handling is performed in an EventFilter (hence no regular
        # signal-slot connection).
        self.led_f1.installEventFilter(self)
        self.led_f2.installEventFilter(self)
        self.led_T1.installEventFilter(self)
        self.led_T2.installEventFilter(self)
        self.led_TW1.installEventFilter(self)
        self.led_TW2.installEventFilter(self)

# ------------------------------------------------------------------------------
    def update_freq_units(self):
        """
        Update labels for time / frequency related specs
        """
        if fb.fil[0]['freq_specs_unit'] == 'k':
            f_unit = ''
            t_unit = ''
            self.lblFreq1.setText(self.txtFreq1_k)
            self.lblFreq2.setText(self.txtFreq2_k)
        else:
            f_unit = fb.fil[0]['plt_fUnit']
            t_unit = fb.fil[0]['plt_tUnit'].replace(r"$\mu$", "&mu;")
            if fb.fil[0]['freq_specs_unit'] in {'f_S', 'f_Ny'}:
                # Normalized frequency labels with capital F
                self.lblFreq1.setText(self.txtFreq1_F)
                self.lblFreq2.setText(self.txtFreq2_F)
                unit_frmt = "i"  # print 'f_S' and 'f_Ny' in italic
            else:
                # absolute frequencies with lower case f
                self.lblFreq1.setText(self.txtFreq1_f)
                self.lblFreq2.setText(self.txtFreq2_f)
                unit_frmt = None  # don't print units like kHz in italic

        self.lblFreqUnit1.setText(to_html(f_unit, frmt=unit_frmt))
        self.lblFreqUnit2.setText(to_html(f_unit, frmt=unit_frmt))
        self.lbl_TU1.setText(to_html(t_unit, frmt=unit_frmt))
        self.lbl_TU2.setText(to_html(t_unit, frmt=unit_frmt))

# ------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by the monitored frequency / time related widgets
        led_f1 and 2, T1 / T2 and TW1 / TW2.
        Source and type of all events generated by monitored objects are passed
         to this eventFilter, evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (``QEvent.FocusIn``), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (``QEvent.FocusOut``) or when
          the Return key is pressed, store current value normalized to f_S with
          full precision and display the denormalized value in selected format
          or full precision when `spec_edited == True`. Emit 'ui_local_changed':'stim'.
        """
        def _reload_entry(source, full_prec=False):
            """
            Reload text entry for active line edit field in denormalized format,
            either with full precision (`full_prec == True`) or rounded.
            """
            try:
                var_name, param_name = self.dict_filtered_widgets[source.objectName()]
                var = getattr(self, var_name)
                scale = getattr(self, param_name)
                if full_prec:
                    source.setText(str(var * scale))
                else:
                    source.setText(str(params['FMT'].format(var * scale)))
            except KeyError:
                logger.warning(f"Unknown objectName {source.objectName}!")
        #------------------------------------------------------------

        def _store_entry(source):
            """ Store transformed frequency / time values """
            if self.spec_edited:
                try:
                    var_name, param_name = self.dict_filtered_widgets[source.objectName()]
                    scale = getattr(self, param_name)  # get scale value
                    var_old = getattr(self, var_name)  # get old var value
                    # assign var with either content of text field or fallback value:
                    if var_name in {'T1', 'T2'}:
                        var = safe_eval(source.text(), var_old * scale,
                                    return_type='float') / scale
                    else:
                        var = safe_eval(source.text(), var_old * scale,
                                        sign='pos', return_type='float') / scale
                    # assign evaluated text field to variable
                    setattr(self, var_name, var)
                    # set textfield with scaled value of `var_name`:
                    source.setText(str(params['FMT'].format(var * scale)))
                    # highlight lineedit field in red when normalized frequency is > 0.5
                    if var >= 0.5 and "_f" in source.objectName():  # only test this for 'led_f1' and 'led_f2'
                        qstyle_widget(source, 'failed')
                    else:
                        qstyle_widget(source, 'normal')
                except KeyError:
                    pass

                self.spec_edited = False  # reset flag
                self._update_energy_scaling_impz()
                self.emit({'ui_local_changed': 'stim'})

            # nothing has changed, but display frequencies in rounded format anyway
            else:
                _reload_entry(source)
        # --------------------------------------------------------------------
        # ------ EventFilter main part ---------------------------------------
        if event.type() in {QEvent.FocusIn, QEvent.KeyPress, QEvent.FocusOut}:
            if event.type() == QEvent.FocusIn:
                self.spec_edited = False
                _reload_entry(source, full_prec=True)
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
    def normalize_freqs(self):
        # TODO: move this to plot_tran_stim and update N_FFT
        """
        Update normalized frequencies and periods if required.

        `normalize_freqs()` is called when sampling frequency has been changed
        via signal ['view_changed':'f_S'] from plot_impz.process_sig_rx

        Frequency and time related entries are always stored normalized w.r.t. f_S
        which is loaded from filter dictionary and stored as  `self.f_scale`
        (except when the frequency unit is k when `f_scale = self.N_FFT`).

        - When the `f_S` lock button is unchecked, only the displayed
          values for frequency entries are updated with f_S, not the normalized freqs.

        - When the `f_S` lock button is checked, the absolute frequency values in
          the widget fields are kept constant, and the normalized freqs are updated.
        """

        f_corr = 1
        if fb.fil[0]['freq_locked']:
            f_corr = fb.fil[0]['f_S_prev'] / fb.fil[0]['f_S']
            self.f1 *= f_corr
            self.f2 *= f_corr
            self.T1 /= f_corr
            self.T2 /= f_corr
            self.TW1 /= f_corr
            self.TW2 /= f_corr

        self._update_energy_scaling_impz()

        # recalculate displayed freq spec values for (maybe) changed f_S
        if fb.fil[0]['freq_specs_unit'] == 'k':
            self.f_scale = self.N_FFT
        else:
            self.f_scale = fb.fil[0]['f_S']
        self.t_scale = fb.fil[0]['T_S']

        # logger.warning(f"f_S = {fb.fil[0]['f_S']}, prev = {fb.fil[0]['f_S_prev']}\n"
        #                f"f_scale = {self.f_scale}, f_1 = {self.f1}, f_corr = {f_corr}")

        # update and round the display
        for w in self.dict_filtered_widgets:
            var_name, param_name = self.dict_filtered_widgets[w]
            # read value and scale of normalized frequency / time value
            var = getattr(self, var_name)
            scale = getattr(self, param_name)
            # access lineedit object
            led = getattr(self, w)
            # logger.warning(f"{w} - {var} - {getattr(self, w).text()}")
            # update the text with the denormalized frequency / time variable
            led.setText(str(params['FMT'].format(var * scale)))
            # self.led_f1.setText(str(params['FMT'].format(self.f1 * self.f_scale)))

            # highlight lineedit field in red when normalized frequency is > 0.5
            if var >= 0.5 and "_f" in w:  # only test this for 'led_f1' and 'led_f2'
                qstyle_widget(led, 'failed')
            else:
                qstyle_widget(led, 'normal')

        self.update_freq_units()

        # emit a signal if normalized frequencies have changed due to an update
        # of f_S
        if fb.fil[0]['freq_locked']:
            self.emit({'ui_local_changed': 'f1_f2'})

    # -------------------------------------------------------------
    def _enable_stim_widgets(self):
        """ Enable / disable widgets depending on the selected stimulus """

        self.cmb_stim = qget_cmb_box(self.cmbStimulus)

        self.wdg_formula_stim.setVisible(self.cmb_stim == "formula")

        if self.cmb_stim == "impulse":
            self.stim = qget_cmb_box(self.cmbImpulseType)
            # recalculate the energy scaling for impulse functions
            self._update_energy_scaling_impz()

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
        self.lbl_N1.setVisible("N1" in stim_wdg)
        self.led_N1.setVisible("N1" in stim_wdg)
        self.lbl_TW1.setVisible("TW1" in stim_wdg)
        self.led_TW1.setVisible("TW1" in stim_wdg)
        self.lbl_TWU1.setVisible("TW1" in stim_wdg)
        self.lblFreq1.setVisible("f1" in stim_wdg)
        self.led_f1.setVisible("f1" in stim_wdg)
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
        self.lbl_N2.setVisible("N2" in stim_wdg)
        self.led_N2.setVisible("N2" in stim_wdg)
        self.lbl_TW2.setVisible("TW2" in stim_wdg)
        self.led_TW2.setVisible("TW2" in stim_wdg)
        self.lbl_TWU2.setVisible("TW2" in stim_wdg)
        self.lblFreq2.setVisible("f2" in stim_wdg)
        self.led_f2.setVisible("f2" in stim_wdg)
        self.lblFreqUnit2.setVisible("f2" in stim_wdg)
        self.lbl_BW2.setVisible("BW2" in stim_wdg)
        self.led_BW2.setVisible("BW2" in stim_wdg)

        self.cmbImpulseType.setVisible(self.cmb_stim == 'impulse')
        self.cmbSinusoidType.setVisible(self.cmb_stim == 'sinusoid')
        self.cmbChirpType.setVisible(self.cmb_stim == 'chirp')
        self.cmbPeriodicType.setVisible(self.cmb_stim == 'periodic')
        self.cmbModulationType.setVisible(self.cmb_stim == 'modulation')

        self.emit({'ui_local_changed': 'stim'})

    # -------------------------------------------------------------
    def _update_amp1(self):
        """ Update value for self.A1 from QLineEditWidget"""
        self.A1 = safe_eval(self.ledAmp1.text(), self.A1, return_type='cmplx')
        self.ledAmp1.setText(str(self.A1))
        self.emit({'ui_local_changed': 'a1'})

    def _update_amp2(self):
        """ Update value for self.A2 from the QLineEditWidget"""
        self.A2 = safe_eval(self.ledAmp2.text(), self.A2, return_type='cmplx')
        self.ledAmp2.setText(str(self.A2))
        self.emit({'ui_local_changed': 'a2'})

    def _update_phi1(self):
        """ Update value for self.phi1 from QLineEditWidget"""
        self.phi1 = safe_eval(self.ledPhi1.text(),
                              self.phi1, return_type='float')
        self.ledPhi1.setText(str(self.phi1))
        self.emit({'ui_local_changed': 'phi1'})

    def _update_N1(self):
        """ Update value for self.N1 from `self.led_N1`"""
        self.N1 = safe_eval(self.led_N1.text(), self.N1, return_type='int', sign='pos')
        self.led_N1.setText(str(self.N1))
        self.emit({'ui_local_changed': 'N1'})

    def _update_N2(self):
        """ Update value for self.N2 from `self.led_N2`"""
        self.N2 = safe_eval(self.led_N2.text(), self.N2, return_type='int', sign='pos')
        self.led_N2.setText(str(self.N2))
        self.emit({'ui_local_changed': 'N2'})

    def _update_BW1(self):
        """ Update value for self.BW1 from QLineEditWidget"""
        self.BW1 = safe_eval(
            self.led_BW1.text(), self.BW1, return_type='float', sign='pos')
        self.led_BW1.setText(str(self.BW1))
        self._update_energy_scaling_impz()
        self.emit({'ui_local_changed': 'BW1'})

    def _update_BW2(self):
        """ Update value for self.BW2 from QLineEditWidget"""
        self.BW2 = safe_eval(
            self.led_BW2.text(), self.BW2, return_type='float', sign='pos')
        self.led_BW2.setText(str(self.BW2))
        self.emit({'ui_local_changed': 'BW2'})

    def _update_energy_scaling_impz(self):
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
        self.phi2 = safe_eval(self.ledPhi2.text(),
                              self.phi2, return_type='float')
        self.ledPhi2.setText(str(self.phi2))
        self.emit({'ui_local_changed': 'phi2'})

    def _update_chirp_type(self):
        """ Update value for self.chirp_type from data field of ComboBox"""
        self.chirp_type = qget_cmb_box(self.cmbChirpType)
        self.emit({'ui_local_changed': 'chirp_type'})

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
        self.noise = qget_cmb_box(self.cmb_stim_noise)
        self.lblNoi.setVisible(self.noise != 'none')
        self.ledNoi.setVisible(self.noise != 'none')
        self.lblNoi_par.setVisible(self.noise == 'mls')
        self.ledNoi_par.setVisible(self.noise == 'mls')
        if self.noise != 'none':
            self.noi = safe_eval(self.ledNoi.text(), 0, return_type='cmplx')
            self.ledNoi.setText(str(self.noi))
            if self.noise == 'gauss':
                self.lblNoi.setText(to_html("&nbsp;&sigma; =", frmt='bi'))
                self.ledNoi.setToolTip(
                    "<span>Standard deviation, "
                    "noise power is <i>P</i> = &sigma;<sup>2</sup></span>")
            elif self.noise == 'uniform':
                self.lblNoi.setText(to_html("&nbsp;&Delta; =", frmt='bi'))
                self.ledNoi.setToolTip(
                    "<span>Interval size for uniformly distributed process (e.g. "
                    "quantization step size for quantization noise), centered around 0. "
                    "Noise power is <i>P</i> = &Delta;<sup>2</sup>/12.</span>")
            elif self.noise == 'randint':
                self.lblNoi.setText(to_html("&nbsp;I =", frmt='bi'))
                self.ledNoi.setToolTip(
                    "<span>Max. integer value <i>I</i> of random integer process."
                    "</span>")
            elif self.noise == 'mls':
                self.lblNoi.setText(to_html("&nbsp;A =", frmt='bi'))
                self.ledNoi.setToolTip(
                    "<span>Amplitude of Maximum Length Sequence. "
                    "Noise power is <i>P</i> = A<sup>2</sup>/2.</span>")
                self.lblNoi_par.setText(to_html("&nbsp;b =", frmt='bi'))
                self.mls_b = safe_eval(
                    self.ledNoi_par.text(), self.mls_b, return_type='int', sign='pos')
                if self.mls_b < 2:
                    self.mls_b = 2
                if self.mls_b > 32:
                    self.mls_b = 32
                self.ledNoi_par.setText(str(self.mls_b))
                self.ledNoi_par.setToolTip("<span>Length of sequence will be "
                                           "2<sup><i>b</i></sup> - 1 with <i>b</i> "
                                           "in the range 2 ... 32./span>")
            elif self.noise == 'brownian':
                self.lblNoi.setText(to_html("&nbsp;&sigma; =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Standard deviation of the Gaussian process "
                                       "that is cumulated.</span>")

        self.emit({'ui_local_changed': 'noi'})

    def _update_DC(self):
        """ Update value for self.DC from the QLineEditWidget"""
        self.DC = safe_eval(self.ledDC.text(), 0, return_type='cmplx')
        self.ledDC.setText(str(self.DC))
        self.emit({'ui_local_changed': 'dc'})

    def _update_stim_formula(self):
        """Update string with formula to be evaluated by numexpr"""
        self.stim_formula = self.ledStimFormula.text().strip()
        self.ledStimFormula.setText(str(self.stim_formula))
        self.emit({'ui_local_changed': 'stim_formula'})

    def _update_stim_par1(self):
        """ Update value for self.par1 from QLineEditWidget"""
        self.stim_par1 = safe_eval(self.ledStimPar1.text(), self.stim_par1,
                                   sign='pos', return_type='float')
        self.ledStimPar1.setText(str(self.stim_par1))
        self.emit({'ui_local_changed': 'stim_par1'})


# ------------------------------------------------------------------------------
def main():
    import sys
    from pyfda.libs.compat import QApplication

    app = QApplication(sys.argv)

    mainw = Plot_Tran_Stim_UI(None)
    layVMain = QVBoxLayout()
    layVMain.addWidget(mainw.wdg_stim)
    # (left, top, right, bottom)
    layVMain.setContentsMargins(*params['wdg_margins'])

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
