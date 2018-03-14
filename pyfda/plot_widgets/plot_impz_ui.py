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

from ..compat import (QCheckBox, QWidget, QComboBox, QLineEdit, QLabel,
                      QHBoxLayout, QVBoxLayout, QFrame, pyqtSlot, pyqtSignal)

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

    sig_rx = pyqtSignal(dict) # incoming
    sig_tx = pyqtSignal(dict) # outgoing

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
        self.bottom = -80
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
        self.plt_time = "Response"
        self.plt_freq = "None"
        self.stim = "Pulse"
        self.noise = "None"
        self.window = "Hann"
        
        self._construct_UI()
        self._enable_stim_widgets()
        self._update_time_freq()
        self._log_mode()
        self._update_N() # slso updates window
        self._update_noi()
        #self._update_window()

    def _construct_UI(self):
        self.lblN_points = QLabel(to_html("N", frmt='bi')  + " =", self)
        self.ledN_points = QLineEdit(self)
        self.ledN_points.setText(str(self.N_points))
        self.ledN_points.setToolTip("<span>Number of points to calculate and display. "
                                   "N = 0 tries to choose for you.</span>")
        
        self.lblN_start = QLabel(to_html("N_0", frmt='bi') + " =", self)
        self.ledN_start = QLineEdit(self)
        self.ledN_start.setText(str(self.N_start))
        self.ledN_start.setToolTip("<span>First point to plot.</span>")
        
        layVlblN = QVBoxLayout()
        layVlblN.addWidget(self.lblN_start)
        layVlblN.addWidget(self.lblN_points)
        
        layVledN = QVBoxLayout()
        layVledN.addWidget(self.ledN_start)
        layVledN.addWidget(self.ledN_points)
        
        self.chkLog = QCheckBox("Log. y-axis", self)
        self.chkLog.setObjectName("chkLog")
        self.chkLog.setToolTip("<span>Logarithmic scale for y-axis.</span>")
        self.chkLog.setChecked(False)
        
        self.chkMarker = QCheckBox("Markers", self)
        self.chkMarker.setObjectName("chkMarker")
        self.chkMarker.setToolTip("<span>Show plot markers.</span>")
        self.chkMarker.setChecked(True)
        
        layVchkLogMark = QVBoxLayout()
        layVchkLogMark.addWidget(self.chkLog)
        layVchkLogMark.addWidget(self.chkMarker)

        self.lblLogBottom = QLabel("Bottom = ", self)
        self.ledLogBottom = QLineEdit(self)
        self.ledLogBottom.setText(str(self.bottom))
        self.ledLogBottom.setToolTip("<span>Minimum display value for log. scale.</span>")
        self.lbldB = QLabel("dB", self)
        
        self.lblPltTime = QLabel("Time: ", self)
        self.cmbPltTime = QComboBox(self)
        self.cmbPltTime.addItems(["None","Stimulus","Response", "Both"])
        qset_cmb_box(self.cmbPltTime, self.plt_time)
        self.cmbPltTime.setToolTip("<span>Choose which signals to show in the time domain: "
                                 "The stimulus, the filter response or both.</span>")

        self.lblPltFreq = QLabel("Freq.: ", self)
        self.cmbPltFreq = QComboBox(self)
        self.cmbPltFreq.addItems(["None","Stimulus","Response", "Both"])
        qset_cmb_box(self.cmbPltFreq, self.plt_freq)
        self.cmbPltFreq.setToolTip("<span>Choose which signals to show in the frequency domain: "
                                 "The stimulus, the filter response or both.</span>")
        layVlblPlt = QVBoxLayout()
        layVlblPlt.addWidget(self.lblPltTime)
        layVlblPlt.addWidget(self.lblPltFreq)
        layVcmbPlt = QVBoxLayout()
        layVcmbPlt.addWidget(self.cmbPltTime)
        layVcmbPlt.addWidget(self.cmbPltFreq)
        
        self.lblStimulus = QLabel("Stimulus: ", self)
        self.cmbStimulus = QComboBox(self)
        self.cmbStimulus.addItems(["Pulse","Step","StepErr", "Cos", "Sine", "Rect", "Saw"])
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

        layHControls = QHBoxLayout()
        layHControls.addLayout(layVlblN)
        layHControls.addLayout(layVledN)
        layHControls.addStretch(2)
        layHControls.addLayout(layVchkLogMark)
        layHControls.addStretch(1)
        layHControls.addWidget(self.lblLogBottom)
        layHControls.addWidget(self.ledLogBottom)
        layHControls.addWidget(self.lbldB)
        layHControls.addStretch(2)
        layHControls.addLayout(layVlblPlt)
        layHControls.addLayout(layVcmbPlt)        
        layHControls.addStretch(1)
        layHControls.addLayout(layVlblCmb)
        layHControls.addLayout(layVCmb)
        layHControls.addStretch(1)
        layHControls.addLayout(layVlblAmp)
        layHControls.addLayout(layVledAmp)
        layHControls.addLayout(layVlblfreq)
        layHControls.addLayout(layVledfreq)
        layHControls.addLayout(layVlblfreqU)
        layHControls.addStretch(1)
        layHControls.addLayout(layVlblNoiDC)
        layHControls.addLayout(layVledNoiDC)
        layHControls.addStretch(10)
        
        layHControlsF = QHBoxLayout()
        self.chkLogF = QCheckBox("Log. scale", self)
        self.chkLogF.setObjectName("chkLogF")
        self.chkLogF.setToolTip("<span>Logarithmic scale for y-axis.</span>")
        self.chkLogF.setChecked(True)

        self.lblLogBottomF = QLabel("Bottom = ", self)
        self.ledLogBottomF = QLineEdit(self)
        self.ledLogBottomF.setText(str(self.bottom_f))
        self.ledLogBottomF.setToolTip("<span>Minimum display value for log. scale.</span>")
        self.lbldBF = QLabel("dB", self)
        
        self.lblWindow = QLabel("Window: ", self)
        self.cmbWindow = QComboBox(self)
        self.cmbWindow.addItems(["Rect","Triangular","Hann","Hamming","Kaiser", "Flattop", "Chebwin"])
        self.cmbWindow.setToolTip("Select window type.")
        qset_cmb_box(self.cmbWindow, self.window)
        
        self.lblWinPar1 = QLabel("Param1")
        self.ledWinPar1 = QLineEdit(self)
        self.ledWinPar1.setText("1")
        self.ledWinPar1.setObjectName("ledWinPar1")

        layHControlsF.addWidget(self.chkLogF)
        layHControlsF.addWidget(self.lblLogBottomF)
        layHControlsF.addWidget(self.ledLogBottomF)
        layHControlsF.addWidget(self.lbldBF)
        layHControls.addStretch(2)       
        layHControlsF.addWidget(self.lblWindow)  
        layHControlsF.addWidget(self.cmbWindow)
        layHControlsF.addWidget(self.lblWinPar1)
        layHControlsF.addWidget(self.ledWinPar1)
        layHControlsF.addStretch(10)
        
        self.wdgHControlsF = QWidget(self)
        self.wdgHControlsF.setLayout(layHControlsF)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.ledN_start.editingFinished.connect(self._update_N)
        self.ledN_points.editingFinished.connect(self._update_N)
        self.chkLog.clicked.connect(self._log_mode)
        self.ledLogBottom.editingFinished.connect(self._log_mode)

        self.cmbPltTime.currentIndexChanged.connect(self._update_time_freq)
        self.cmbPltFreq.currentIndexChanged.connect(self._update_time_freq)

        self.chkMarker.clicked.connect(self._update_chk_boxes)

        self.cmbStimulus.currentIndexChanged.connect(self._enable_stim_widgets)
        self.cmbNoise.currentIndexChanged.connect(self._update_noi)
        self.ledNoi.editingFinished.connect(self._update_noi)
        self.ledAmp1.editingFinished.connect(self._update_amp1)
        self.ledAmp2.editingFinished.connect(self._update_amp2)

        self.ledDC.editingFinished.connect(self._update_DC)
        
        self.chkLogF.clicked.connect(self._log_mode)
        self.ledLogBottomF.editingFinished.connect(self._log_mode)
        self.cmbWindow.currentIndexChanged.connect(self._update_window)
        self.ledWinPar1.editingFinished.connect(self._update_window)
       
        
        # ########################  Main UI Layout ############################
        # layout for frame (UI widget)
        layVMainF = QVBoxLayout()
        layVMainF.addLayout(layHControls)
        layVMainF.addWidget(self.wdgHControlsF)

        # This frame encompasses all UI elements
        self.frmControls = QFrame(self)
        self.frmControls.setLayout(layVMainF)

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmControls)
        layVMain.setContentsMargins(*params['wdg_margins'])
        self.setLayout(layVMain)
        
        
    def _update_N(self):
        """ Update value for self.N_start from the QLineEditWidget"""
        self.N_start = safe_eval(self.ledN_start.text(), 0, return_type='int', sign='pos')
        self.ledN_start.setText(str(self.N_start))
        N_user = safe_eval(self.ledN_points.text(), 0, return_type='int', sign='pos')
        if N_user == 0: # automatic calculation
            self.N = self.calc_n_points(N_user)
        else:
            self.N = N_user
        
        self.N_end = self.N + self.N_start # total number of points to be calculated: N + N_start
        
        self._update_window()

    def _update_chk_boxes(self):
        """ 
        Trigger update view when one of "show stimulus", "show response" or 
        "show markers" checkboxes is clicked
        """
        self.sig_tx.emit({'sender':__name__, 'update_view':''})
        
    def _update_time_freq(self):
        """ 
        Trigger 'draw' when one of the comboboxes PltTime or PltFreq is modified,
        enable frequency domain controls only when needed
        """
        self.plt_time = qget_cmb_box(self.cmbPltTime, data=False)
        self.plt_freq = qget_cmb_box(self.cmbPltFreq, data=False)
        self.wdgHControlsF.setVisible(self.plt_freq != "None")
        self.sig_tx.emit({'sender':__name__, 'draw':''})


    def _log_mode(self):
        """
        Select / deselect logarithmic mode for both time and frequency
        domain and update self.bottom / self.bottom_f
        """
        log = self.chkLog.isChecked()
        self.lblLogBottom.setVisible(log)
        self.ledLogBottom.setVisible(log)
        self.lbldB.setVisible(log)
        if log:
            self.bottom = safe_eval(self.ledLogBottom.text(), self.bottom, 
                                    return_type='float', sign='neg')
            self.ledLogBottom.setText(str(self.bottom))
            
        log_f = self.chkLogF.isChecked()
        self.lblLogBottomF.setVisible(log_f)
        self.ledLogBottomF.setVisible(log_f)
        self.lbldBF.setVisible(log_f)
        if log_f:
            self.bottom_f = safe_eval(self.ledLogBottomF.text(), self.bottom_f, 
                                    return_type='float', sign='neg')
            self.ledLogBottomF.setText(str(self.bottom_f))

        self.sig_tx.emit({'sender':__name__, 'update_view':''})
        
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
        
        self.sig_tx.emit({'sender':__name__, 'draw':''})

    def _update_amp1(self):
        """ Update value for self.A1 from QLineEditWidget"""        
        self.A1 = safe_eval(self.ledAmp1.text(), self.A1, return_type='float')
        self.ledAmp1.setText(str(self.A1))
        self.sig_tx.emit({'sender':__name__, 'draw':''})
        
    def _update_amp2(self):
        """ Update value for self.A2 from the QLineEditWidget"""
        self.A2 = safe_eval(self.ledAmp2.text(), self.A2, return_type='float')
        self.ledAmp2.setText(str(self.A2))
        self.sig_tx.emit({'sender':__name__, 'draw':''})

        
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
        self.sig_tx.emit({'sender':__name__, 'draw':''})

    def _update_DC(self):
        """ Update value for self.DC from the QLineEditWidget"""
        self.DC = safe_eval(self.ledDC.text(), 0, return_type='float')
        self.ledDC.setText(str(self.DC))
        self.sig_tx.emit({'sender':__name__, 'draw':''})
        
    def _update_window(self):
        """ Update window type for FFT """

        def _update_param1():
            self.ledWinPar1.setToolTip(tooltip)
            self.lblWinPar1.setText(to_html(txt_par1, frmt='bi'))

            self.param1 = safe_eval(self.ledWinPar1.text(), self.param1, return_type='float', sign='pos')
            self.ledWinPar1.setText(str(self.param1))   
        #----------------------------------------------------------------------            
        self.window_type = qget_cmb_box(self.cmbWindow, data=False)
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
         
        self.sig_tx.emit({'sender':__name__, 'draw':''})
        
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
                N = min(len(fb.fil[0]['ba'][0]),  100) # FIR: N = number of coefficients (max. 100)
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
