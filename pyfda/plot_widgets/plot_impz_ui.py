# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create the UI for the PlotImz class
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

from ..compat import (QCheckBox, QWidget, QComboBox, QLineEdit, QLabel, QPushButton,
                      QHBoxLayout, QVBoxLayout, pyqtSignal)

import numpy as np
import scipy.signal as sig
from pyfda.pyfda_lib import to_html, safe_eval
import pyfda.filterbroker as fb
from pyfda.pyfda_qt_lib import qset_cmb_box, qget_cmb_box
from pyfda.pyfda_rc import params # FMT string for QLineEdit fields, e.g. '{:.3g}'

class PlotImpz_UI(QWidget):
    """
    Create the UI for the PlotImpz class
    """
    # incoming: from connector widget plot_tab_widgets to self.process_sig_rx() 
    sig_rx = pyqtSignal(object)
    # outgoing: from process_sig_rx() to PlotImpz
    sig_tx = pyqtSignal(object) 

    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (FilterCoeffs)
        """
        super(PlotImpz_UI, self).__init__(parent)

        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """

        # initial settings for lineedit widgets
        self.N_start = 0
        self.N_points = 0
        self.bottom_t = -80
        self.f1 = 0.02
        self.f2 = 0.03
        self.A1 = 1.0
        self.A2 = 0.0
        self.phi1 = self.phi2 = 0 # not used yet
        self.noi = 0.1
        self.noise = 'none'
        self.DC = 0.0

        self.bottom_f = -120
        self.param1 = None

        # initial settings for comboboxes
        self.plt_time_stim = "None"
        self.plt_time_resp = "Stem"
        self.plt_freq_stim = "None"
        self.plt_freq_resp = "Line"

        self.plt_freq = "None" # TODO: kann später weg!
        self.stim = "Pulse"
        self.noise = "None"
        self.window = "Hann"

        self._construct_UI()
        self._enable_stim_widgets()
        self.update_N() # also updates window function
        self._update_noi()

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar
        """
        logger.debug("Processing {0}".format(dict_sig))
        if 'data_changed' in dict_sig:
            self.update_N(dict_sig) # this passes dict_sig on to sig_tx as well
        else:
            self.sig_tx.emit(dict_sig)

    def _construct_UI(self):
        # ----------- ---------------------------------------------------
        # Run control widgets
        # ---------------------------------------------------------------
        self.lbl_sim_select = QLabel("<b>Simulate</b>", self)
        self.cmb_sim_select = QComboBox(self)
        self.cmb_sim_select.addItems(["Float","Fixpoint"])
        qset_cmb_box(self.cmb_sim_select, "Float")
        self.cmb_sim_select.setToolTip("<span>Simulate floating-point or fixpoint response."
                                 "</span>")

        self.lbl_N_points = QLabel(to_html("N", frmt='bi')  + " =", self)
        self.led_N_points = QLineEdit(self)
        self.led_N_points.setText(str(self.N_points))
        self.led_N_points.setToolTip("<span>Number of points to calculate and display. "
                                   "N = 0 tries to choose for you.</span>")

        self.lbl_N_start = QLabel(to_html("N_0", frmt='bi') + " =", self)
        self.led_N_start = QLineEdit(self)
        self.led_N_start.setText(str(self.N_start))
        self.led_N_start.setToolTip("<span>First point to plot.</span>")
        
        self.but_run = QPushButton("RUN", self)
        self.but_run.setToolTip("Run fixpoint simulation")

        self.chk_fx_scale = QCheckBox("Integer scale", self)
        self.chk_fx_scale.setObjectName("chk_fx_scale")
        self.chk_fx_scale.setToolTip("<span>Display data with integer (fixpoint) scale.</span>")
        self.chk_fx_scale.setChecked(False)
        
        self.chk_stim_options = QCheckBox("Stimulus Options", self)
        self.chk_stim_options.setObjectName("chk_stim_options")
        self.chk_stim_options.setToolTip("<span>Show options for stimulus signal.</span>")
        self.chk_stim_options.setChecked(True)


        layH_ctrl_run = QHBoxLayout()
        layH_ctrl_run.addWidget(self.lbl_sim_select)
        layH_ctrl_run.addWidget(self.cmb_sim_select)
        layH_ctrl_run.addStretch(1)        
        layH_ctrl_run.addWidget(self.lbl_N_start)
        layH_ctrl_run.addWidget(self.led_N_start)
        layH_ctrl_run.addStretch(1)
        layH_ctrl_run.addWidget(self.lbl_N_points)
        layH_ctrl_run.addWidget(self.led_N_points)
        layH_ctrl_run.addStretch(1)
        layH_ctrl_run.addWidget(self.but_run)
        layH_ctrl_run.addStretch(2)        
        layH_ctrl_run.addWidget(self.chk_fx_scale)
        layH_ctrl_run.addStretch(2)        
        layH_ctrl_run.addWidget(self.chk_stim_options)
        layH_ctrl_run.addStretch(10)

        #layH_ctrl_run.setContentsMargins(*params['wdg_margins'])

        self.wdg_ctrl_run = QWidget(self)
        self.wdg_ctrl_run.setLayout(layH_ctrl_run)
        # --- end of run control ----------------------------------------        

        # ----------- ---------------------------------------------------
        # Controls for time domain
        # ---------------------------------------------------------------

        lbl_plt_time_title = QLabel("<b>Time: Show</b>", self)
        self.lbl_plt_time_stim = QLabel("Stimulus", self)
        self.cmb_plt_time_stim = QComboBox(self)
        self.cmb_plt_time_stim.addItems(["None","Dots","Line","Stem", "Step"])       
        qset_cmb_box(self.cmb_plt_time_stim, self.plt_time_stim)
        self.cmb_plt_time_stim.setToolTip("<span>Choose stimulus plot style.</span>")

        self.chk_mrk_time_stim = QCheckBox("*", self)
        self.chk_mrk_time_stim.setChecked(False)
        self.chk_mrk_time_stim.setToolTip("Use plot markers")
        
        self.lbl_plt_time_resp = QLabel("Response", self)
        self.cmb_plt_time_resp = QComboBox(self)
        self.cmb_plt_time_resp.addItems(["None","Dots","Line","Stem", "Step"])       
        qset_cmb_box(self.cmb_plt_time_resp, self.plt_time_resp)
        self.cmb_plt_time_resp.setToolTip("<span>Choose response plot style.</span>")

        self.chk_mrk_time_resp = QCheckBox("*", self)
        self.chk_mrk_time_resp.setChecked(False)
        self.chk_mrk_time_resp.setToolTip("Use plot markers")

        self.chk_log_time = QCheckBox("dB", self)
        self.chk_log_time.setObjectName("chk_log_time")
        self.chk_log_time.setToolTip("<span>Logarithmic scale for y-axis.</span>")
        self.chk_log_time.setChecked(False)

        self.lbl_log_bottom_time = QLabel("Bottom = ", self)
        self.led_log_bottom_time = QLineEdit(self)
        self.led_log_bottom_time.setText(str(self.bottom_t))
        self.led_log_bottom_time.setToolTip("<span>Minimum display value for log. scale.</span>")
        self.lbl_dB_time = QLabel("dB", self)
        
        self.chk_win_time = QCheckBox("FFT Window", self)
        self.chk_win_time.setObjectName("chk_win_time")
        self.chk_win_time.setToolTip("<span>Show FFT windowing function.</span>")
        self.chk_win_time.setChecked(False)

        self.chk_fx_range = QCheckBox("Min/max.", self)
        self.chk_fx_range.setObjectName("chk_fx_range")
        self.chk_fx_range.setToolTip("<span>Display limits of fixpoint range.</span>")
        self.chk_fx_range.setChecked(False)

        layH_ctrl_time = QHBoxLayout()
        layH_ctrl_time.addWidget(lbl_plt_time_title)
        layH_ctrl_time.addStretch(1)
        layH_ctrl_time.addWidget(self.cmb_plt_time_resp)
        layH_ctrl_time.addWidget(self.chk_mrk_time_resp)        
        layH_ctrl_time.addStretch(1)
        layH_ctrl_time.addWidget(self.lbl_plt_time_stim)
        layH_ctrl_time.addWidget(self.cmb_plt_time_stim)
        layH_ctrl_time.addWidget(self.chk_mrk_time_stim) 
        layH_ctrl_time.addStretch(2)
        layH_ctrl_time.addWidget(self.chk_log_time)
        layH_ctrl_time.addStretch(1)
        layH_ctrl_time.addWidget(self.lbl_log_bottom_time)
        layH_ctrl_time.addWidget(self.led_log_bottom_time)
        layH_ctrl_time.addWidget(self.lbl_dB_time)
        layH_ctrl_time.addStretch(1)
        layH_ctrl_time.addWidget(self.chk_win_time)        
        layH_ctrl_time.addStretch(2)        
        layH_ctrl_time.addWidget(self.chk_fx_range)
        layH_ctrl_time.addStretch(10)
        
        #layH_ctrl_time.setContentsMargins(*params['wdg_margins'])
        
        self.wdg_ctrl_time = QWidget(self)
        self.wdg_ctrl_time.setLayout(layH_ctrl_time)
        # ---- end time domain ------------------

        # ---------------------------------------------------------------
        # Controls for frequency domain
        # ---------------------------------------------------------------
        lbl_plt_freq_title = QLabel("<b>Freq: Show</b>", self)
        
        self.lbl_plt_freq_stim = QLabel("Stimulus", self)
        self.cmb_plt_freq_stim = QComboBox(self)
        self.cmb_plt_freq_stim.addItems(["None","Dots","Line","Stem", "Step"])       
        qset_cmb_box(self.cmb_plt_freq_stim, self.plt_freq_stim)
        self.cmb_plt_freq_stim.setToolTip("<span>Choose stimulus plot style.</span>")

        self.chk_mrk_freq_stim = QCheckBox("*", self)
        self.chk_mrk_freq_stim.setChecked(False)
        self.chk_mrk_freq_stim.setToolTip("Use plot markers")
        
        self.lbl_plt_freq_resp = QLabel("Response", self)
        self.cmb_plt_freq_resp = QComboBox(self)
        self.cmb_plt_freq_resp.addItems(["None","Dots","Line","Stem", "Step"])       
        qset_cmb_box(self.cmb_plt_freq_resp, self.plt_freq_resp)
        self.cmb_plt_freq_resp.setToolTip("<span>Choose response plot style.</span>")

        self.chk_mrk_freq_resp = QCheckBox("*", self)
        self.chk_mrk_freq_resp.setChecked(False)
        self.chk_mrk_freq_resp.setToolTip("Use plot markers")

        self.chk_log_freq = QCheckBox("dB", self)
        self.chk_log_freq.setObjectName("chk_log_freq")
        self.chk_log_freq.setToolTip("<span>Logarithmic scale for y-axis.</span>")
        self.chk_log_freq.setChecked(True)

        self.lbl_log_bottom_freq = QLabel("Bottom = ", self)
        self.led_log_bottom_freq = QLineEdit(self)
        self.led_log_bottom_freq.setText(str(self.bottom_f))
        self.led_log_bottom_freq.setToolTip("<span>Minimum display value for log. scale.</span>")
        self.lbl_dB_freq = QLabel("dB", self)

        self.lbl_win_fft = QLabel("Window: ", self)
        self.cmb_win_fft = QComboBox(self)
        self.cmb_win_fft.addItems(["Rect","Triangular","Hann","Hamming","Kaiser", "Flattop", "Chebwin"])
        self.cmb_win_fft.setToolTip("Select window type.")
        qset_cmb_box(self.cmb_win_fft, self.window)

        self.lblWinPar1 = QLabel("Param1")
        self.ledWinPar1 = QLineEdit(self)
        self.ledWinPar1.setText("1")
        self.ledWinPar1.setObjectName("ledWinPar1")
        
        self.chk_win_freq = QCheckBox("Show", self)
        self.chk_win_freq.setObjectName("chk_win_freq")
        self.chk_win_freq.setToolTip("<span>Show FFT windowing function.</span>")
        self.chk_win_freq.setChecked(False)

        layH_ctrl_freq = QHBoxLayout()

        layH_ctrl_freq.addWidget(lbl_plt_freq_title)
        layH_ctrl_freq.addStretch(1)
        layH_ctrl_freq.addWidget(self.lbl_plt_freq_resp)
        layH_ctrl_freq.addWidget(self.cmb_plt_freq_resp)
        layH_ctrl_freq.addWidget(self.chk_mrk_freq_resp)        
        layH_ctrl_freq.addStretch(1)
        layH_ctrl_freq.addWidget(self.lbl_plt_freq_stim)
        layH_ctrl_freq.addWidget(self.cmb_plt_freq_stim)
        layH_ctrl_freq.addWidget(self.chk_mrk_freq_stim)

        layH_ctrl_freq.addWidget(self.chk_log_freq)
        layH_ctrl_freq.addWidget(self.led_log_bottom_freq)
        layH_ctrl_freq.addWidget(self.lbl_dB_freq)
        layH_ctrl_freq.addStretch(2)
        layH_ctrl_freq.addWidget(self.lbl_win_fft)
        layH_ctrl_freq.addWidget(self.cmb_win_fft)
        layH_ctrl_freq.addWidget(self.lblWinPar1)
        layH_ctrl_freq.addWidget(self.ledWinPar1)
        layH_ctrl_freq.addWidget(self.chk_win_freq)        
        layH_ctrl_freq.addStretch(10)

        #layH_ctrl_freq.setContentsMargins(*params['wdg_margins'])

        self.wdg_ctrl_freq = QWidget(self)
        self.wdg_ctrl_freq.setLayout(layH_ctrl_freq)
        # ---- end Frequency Domain ------------------

        # ---------------------------------------------------------------
        # Controls for stimuli
        # ---------------------------------------------------------------

        lbl_title_stim = QLabel("<b>Stimulus:</b>", self)
        
        self.lblStimulus = QLabel("Signal: ", self)
        self.cmbStimulus = QComboBox(self)
        self.cmbStimulus.addItems(["None","Pulse","Step","StepErr","Cos","Sine","Rect","Saw"])
        self.cmbStimulus.setToolTip("Select stimulus type.")
        qset_cmb_box(self.cmbStimulus, self.stim)

        self.lblNoise = QLabel("Noise: ", self)
        self.cmbNoise = QComboBox(self)
        self.cmbNoise.addItems(["None","Gauss","Uniform"])
        self.cmbNoise.setToolTip("Select added noise type.")
        qset_cmb_box(self.cmbNoise, self.noise)

        layVlblCmb = QVBoxLayout()
        layVlblCmb.addWidget(self.lblStimulus)
        layVlblCmb.addWidget(self.lblNoise)
        layVCmb = QVBoxLayout()
        layVCmb.addWidget(self.cmbStimulus)
        layVCmb.addWidget(self.cmbNoise)

        self.lblAmp1 = QLabel(to_html("A_1", frmt='bi') + " =", self)
        self.ledAmp1 = QLineEdit(self)
        self.ledAmp1.setText(str(self.A1))
        self.ledAmp1.setToolTip("Stimulus amplitude.")
        self.ledAmp1.setObjectName("stimAmp1")

        self.lblAmp2 = QLabel(to_html("A_2", frmt='bi') + " =", self)
        self.ledAmp2 = QLineEdit(self)
        self.ledAmp2.setText(str(self.A2))
        self.ledAmp2.setToolTip("Stimulus amplitude 2.")
        self.ledAmp2.setObjectName("stimAmp2")

        layVlblAmp = QVBoxLayout()
        layVlblAmp.addWidget(self.lblAmp1)
        layVlblAmp.addWidget(self.lblAmp2)

        layVledAmp = QVBoxLayout()
        layVledAmp.addWidget(self.ledAmp1)
        layVledAmp.addWidget(self.ledAmp2)

        self.lblFreq1 = QLabel(to_html("f_1", frmt='bi') + " =", self)
        self.ledFreq1 = QLineEdit(self)
        self.ledFreq1.setText(str(self.f1))
        self.ledFreq1.setToolTip("Stimulus frequency 1.")
        self.ledFreq1.setObjectName("stimFreq1")
        self.lblFreqUnit1 = QLabel("f_S", self)

        self.lblFreq2 = QLabel(to_html("f_2", frmt='bi') + " =", self)
        self.ledFreq2 = QLineEdit(self)
        self.ledFreq2.setText(str(self.f2))
        self.ledFreq2.setToolTip("Stimulus frequency 2.")
        self.ledFreq2.setObjectName("stimFreq2")
        self.lblFreqUnit2 = QLabel("f_S", self)
        layVlblfreq = QVBoxLayout()
        layVlblfreq.addWidget(self.lblFreq1)
        layVlblfreq.addWidget(self.lblFreq2)

        layVledfreq = QVBoxLayout()
        layVledfreq.addWidget(self.ledFreq1)
        layVledfreq.addWidget(self.ledFreq2)

        layVlblfreqU = QVBoxLayout()
        layVlblfreqU.addWidget(self.lblFreqUnit1)
        layVlblfreqU.addWidget(self.lblFreqUnit2)

        self.lblNoi = QLabel("not initialized", self)
        self.ledNoi = QLineEdit(self)
        self.ledNoi.setText(str(self.noi))
        self.ledNoi.setToolTip("not initialized")
        self.ledNoi.setObjectName("stimNoi")

        self.lblDC = QLabel(to_html("DC =", frmt='bi'), self)
        self.ledDC = QLineEdit(self)
        self.ledDC.setText(str(self.DC))
        self.ledDC.setToolTip("DC Level")
        self.ledDC.setObjectName("stimDC")

        layVlblNoiDC = QVBoxLayout()
        layVlblNoiDC.addWidget(self.lblNoi)
        layVlblNoiDC.addWidget(self.lblDC)
        layVledNoiDC = QVBoxLayout()
        layVledNoiDC.addWidget(self.ledNoi)
        layVledNoiDC.addWidget(self.ledDC)
        
        layH_ctrl_stim = QHBoxLayout()
        layH_ctrl_stim.addWidget(lbl_title_stim)
        layH_ctrl_stim.addStretch(1)
        layH_ctrl_stim.addLayout(layVlblCmb)
        layH_ctrl_stim.addLayout(layVCmb)
        layH_ctrl_stim.addStretch(1)
        layH_ctrl_stim.addLayout(layVlblAmp)
        layH_ctrl_stim.addLayout(layVledAmp)
        layH_ctrl_stim.addLayout(layVlblfreq)
        layH_ctrl_stim.addLayout(layVledfreq)
        layH_ctrl_stim.addLayout(layVlblfreqU)
        layH_ctrl_stim.addStretch(1)
        layH_ctrl_stim.addLayout(layVlblNoiDC)
        layH_ctrl_stim.addLayout(layVledNoiDC)
        layH_ctrl_stim.addStretch(10)
        
        self.wdg_ctrl_stim = QWidget(self)
        self.wdg_ctrl_stim.setLayout(layH_ctrl_stim)
        # --------- end stimuli ---------------------------------

 
        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # --- run control ---
        self.led_N_start.editingFinished.connect(self.update_N)
        self.led_N_points.editingFinished.connect(self.update_N)

        # --- frequency control ---
        #self.chkLogF.clicked.connect(self._log_mode_freq)
        #self.ledLogBottomF.editingFinished.connect(self._log_mode_freq)
        # careful! currentIndexChanged passes the current index to _update_win_fft
        self.cmb_win_fft.currentIndexChanged.connect(self._update_win_fft)
        self.ledWinPar1.editingFinished.connect(self._update_win_fft)

        # --- stimulus control ---
        self.cmbStimulus.currentIndexChanged.connect(self._enable_stim_widgets)
        self.cmbNoise.currentIndexChanged.connect(self._update_noi)
        self.ledNoi.editingFinished.connect(self._update_noi)
        self.ledAmp1.editingFinished.connect(self._update_amp1)
        self.ledAmp2.editingFinished.connect(self._update_amp2)
        self.ledDC.editingFinished.connect(self._update_DC)


    def _enable_stim_widgets(self):
        """ Enable / disable widgets depending on the selected stimulus"""
        self.stim = qget_cmb_box(self.cmbStimulus, data=False)
        f1_en = self.stim in {"Cos", "Sine", "Rect", "Saw"}
        f2_en = self.stim in {"Cos", "Sine"}
        a2_en = self.stim in {"Cos", "Sine"}
        dc_en = self.stim not in {"Step", "StepErr"}
        self.lblFreq1.setVisible(f1_en)
        self.ledFreq1.setVisible(f1_en)
        self.lblFreqUnit1.setVisible(f1_en)
        self.lblFreq2.setVisible(f2_en)
        self.ledFreq2.setVisible(f2_en)
        self.lblFreqUnit2.setVisible(f2_en)
        self.lblAmp2.setVisible(a2_en)
        self.ledAmp2.setVisible(a2_en)
        self.lblDC.setVisible(dc_en)
        self.ledDC.setVisible(dc_en)

        self.sig_tx.emit({'sender':__name__, 'data_changed':'stim'})

    def _update_amp1(self):
        """ Update value for self.A1 from QLineEditWidget"""
        self.A1 = safe_eval(self.ledAmp1.text(), self.A1, return_type='float')
        self.ledAmp1.setText(str(self.A1))
        self.sig_tx.emit({'sender':__name__, 'data_changed':'a1'})

    def _update_amp2(self):
        """ Update value for self.A2 from the QLineEditWidget"""
        self.A2 = safe_eval(self.ledAmp2.text(), self.A2, return_type='float')
        self.ledAmp2.setText(str(self.A2))
        self.sig_tx.emit({'sender':__name__, 'data_changed':'a2'})


    def _update_noi(self):
        """ Update type + value + label for self.noi for noise"""
        self.noise = qget_cmb_box(self.cmbNoise, data=False).lower()
        self.lblNoi.setVisible(self.noise!='none')
        self.ledNoi.setVisible(self.noise!='none')
        if self.noise!='none':
            self.noi = safe_eval(self.ledNoi.text(), 0, return_type='float', sign='pos')
            self.ledNoi.setText(str(self.noi))
            if self.noise == 'gauss':
                self.lblNoi.setText(to_html("&sigma; =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Standard deviation of statistical process,"
                                       "noise power is <i>P</i> = &sigma;<sup>2</sup></span>")
            elif self.noise == 'uniform':
                self.lblNoi.setText(to_html("&Delta; =", frmt='bi'))
                self.ledNoi.setToolTip("<span>Interval size for uniformly distributed process "
                                       "(e.g. quantization step size for quantization noise), "
                                       "centered around 0. Noise power is "
                                       "<i>P</i> = &Delta;<sup>2</sup>/12.</span>")
        self.sig_tx.emit({'sender':__name__, 'data_changed':'noi'})

    def _update_DC(self):
        """ Update value for self.DC from the QLineEditWidget"""
        self.DC = safe_eval(self.ledDC.text(), 0, return_type='float')
        self.ledDC.setText(str(self.DC))
        self.sig_tx.emit({'sender':__name__, 'data_changed':'dc'})
    # -------------------------------------------------------------------------

    def update_N(self, dict_sig=None):
        """
        Update values for self.N and self.N_start from the QLineEditWidget
        """
        self.N_start = safe_eval(self.led_N_start.text(), 0, return_type='int', sign='pos')
        self.led_N_start.setText(str(self.N_start))
        N_user = safe_eval(self.led_N_points.text(), 0, return_type='int', sign='pos')
        if N_user == 0: # automatic calculation
            self.N = self.calc_n_points(N_user) # widget remains set to 0
        else:
            self.N = N_user
            self.led_N_points.setText(str(self.N)) # update widget

        self.N_end = self.N + self.N_start # total number of points to be calculated: N + N_start

        self._update_win_fft(dict_sig)

    def _update_win_fft(self, dict_sig=None):
        """ Update window type for FFT """

        def _update_param1():
            self.ledWinPar1.setToolTip(tooltip)
            self.lblWinPar1.setText(to_html(txt_par1, frmt='bi'))

            self.param1 = safe_eval(self.ledWinPar1.text(), self.param1, return_type='float', sign='pos')
            self.ledWinPar1.setText(str(self.param1))
        #----------------------------------------------------------------------
        self.window_type = qget_cmb_box(self.cmb_win_fft, data=False)
#        self.param1 = None
        has_par1 = False
        txt_par1 = ""

        if self.window_type in {"Bartlett", "Triangular"}:
            window_name = "bartlett"
        elif self.window_type == "Flattop":
            window_name = "flattop"
        elif self.window_type == "Hamming":
            window_name = "hamming"
        elif self.window_type == "Hann":
            window_name = "hann"
        elif self.window_type == "Rect":
            window_name = "boxcar"
        elif self.window_type == "Kaiser":
            window_name = "kaiser"
            has_par1 = True
            txt_par1 = '&beta; ='

            tooltip = ("<span>Shape parameter; lower values reduce  main lobe width, "
                       "higher values reduce side lobe level, typ. value is 5.</span>")
            _update_param1()
            if not self.param1:
                self.param1 = 5

        elif self.window_type == "Chebwin":
            window_name = "chebwin"
            has_par1 = True
            txt_par1 = 'Attn ='
            tooltip = ("<span>Side lobe attenuation in dB (typ. 80 dB).</span>")
            _update_param1()
            if not self.param1:
                self.param1 = 80
            if self.param1 < 45:
                logger.warning("Attenuation needs to be larger than 45 dB!")

        else:
            logger.error("Unknown window type {0}".format(self.window_type))

        # get attribute window_name from submodule sig.windows and
        # returning the desired window function:
        win_fnct = getattr(sig.windows, window_name, None)
        if not win_fnct:
            logger.error("No window function {0} in scipy.signal.windows, using rectangular window instead!"\
                         .format(window_name))
            win_fnct = sig.windows.boxcar
            self.param1 = None

        self.lblWinPar1.setVisible(has_par1)
        self.ledWinPar1.setVisible(has_par1)
        if has_par1:
            self.win = win_fnct(self.N, self.param1) # use additional parameter
        else:
            self.win = win_fnct(self.N)

        self.nenbw = self.N * np.sum(np.square(self.win)) / (np.square(np.sum(self.win)))

        self.scale = self.N / np.sum(self.win)
        self.win *= self.scale # correct gain for periodic signals (coherent gain)

        if not dict_sig or type(dict_sig) != dict:
            self.sig_tx.emit({'sender':__name__, 'data_changed':'win'})
        else:
            self.sig_tx.emit(dict_sig)

#------------------------------------------------------------------------------
    def calc_n_points(self, N_user = 0):
        """
        Calculate number of points to be displayed, depending on type of filter
        (FIR, IIR) and user input. If the user selects 0 points, the number is
        calculated automatically.

        An improvement would be to calculate the dominant pole and the corresponding
        settling time.
        """

        if N_user == 0: # set number of data points automatically
            if fb.fil[0]['ft'] == 'IIR':
                N = 100
            else:
                N = min(len(fb.fil[0]['ba'][0]),100) # FIR: N = number of coefficients (max. 100)
        else:
            N = N_user

        return N

#------------------------------------------------------------------------------

def main():
    import sys
    from ..compat import QApplication

    app = QApplication(sys.argv)
    mainw = PlotImpz_UI(None)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
