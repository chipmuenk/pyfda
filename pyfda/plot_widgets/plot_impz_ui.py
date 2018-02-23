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

from pyfda.pyfda_lib import to_html, safe_eval
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

        # initial settings for line edit widgets
        self.N_start = 0
        self.bottom = -80
        self.f1 = 0.02
        self.f2 = 0.03
        self.A1 = 1.0
        self.A2 = 0.0
        self.noi = 0.0
        self.noise = 'none'
        self.DC = 0.0
        self._construct_UI()
        self.enable_controls()
        self.enable_log_mode()
        self.update_noi()

    def _construct_UI(self):
        self.lblNPoints = QLabel(to_html("N =", frmt='bi'), self)

        self.ledNPoints = QLineEdit(self)
        self.ledNPoints.setText("0")
        self.ledNPoints.setToolTip("<span>Number of points to calculate and display. "
                                   "N = 0 tries to choose for you.</span>")
        
        self.lblN_start = QLabel(to_html("N_0", frmt='bi') + " =", self)
        self.ledN_start = QLineEdit(self)
        self.ledN_start.setText("0")
        self.ledN_start.setToolTip("<span>First point to plot.</span>")
        
        layVlblNPoints = QVBoxLayout()
        layVlblNPoints.addWidget(self.lblN_start)
        layVlblNPoints.addWidget(self.lblNPoints)
        
        layVledNPoints = QVBoxLayout()
        layVledNPoints.addWidget(self.ledN_start)
        layVledNPoints.addWidget(self.ledNPoints)

        
        self.chkLog = QCheckBox("Log. y-axis", self)
        self.chkLog.setObjectName("chkLog")
        self.chkLog.setToolTip("<span>Logarithmic scale for y-axis.</span>")
        self.chkLog.setChecked(False)
        
        self.chkMarker = QCheckBox("Show markers", self)
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
        
        self.chkPltStim = QCheckBox("Show Stimulus", self)
        self.chkPltStim.setChecked(False)
        self.chkPltStim.setToolTip("Show stimulus signal.")
        
        self.chkPltResp = QCheckBox("Show Response", self)
        self.chkPltResp.setChecked(True)
        self.chkPltResp.setToolTip("Show filter response.")
        layVchkPlt = QVBoxLayout()
        layVchkPlt.addWidget(self.chkPltStim)
        layVchkPlt.addWidget(self.chkPltResp)
        
        self.lblStimulus = QLabel("Type: ", self)
        self.cmbStimulus = QComboBox(self)
        self.cmbStimulus.addItems(["Pulse","Step","StepErr", "Cos", "Sine", "Rect", "Saw"])
        self.cmbStimulus.setToolTip("Select stimulus type.")

        self.lblNoise = QLabel("Noise: ", self)
        self.cmbNoise = QComboBox(self)
        self.cmbNoise.addItems(["None","Gauss","Uniform"])
        self.cmbNoise.setToolTip("Select added noise type.")
        
        layVlblCmb = QVBoxLayout()
        layVlblCmb.addWidget(self.lblStimulus)
        layVlblCmb.addWidget(self.lblNoise)
        layVCmb = QVBoxLayout()
        layVCmb.addWidget(self.cmbStimulus)
        layVCmb.addWidget(self.cmbNoise)

        self.lblAmp1 = QLabel(to_html("A_1", frmt='b') + " =", self)
        self.ledAmp1 = QLineEdit(self)
        self.ledAmp1.setText(str(self.A1))
        self.ledAmp1.setToolTip("Stimulus amplitude.")
        self.ledAmp1.setObjectName("stimAmp1")
        
        self.lblAmp2 = QLabel(to_html("A_2", frmt='b') + " =", self)
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
        self.ledNoi.setText(str(self.f1))
        self.ledNoi.setToolTip("Noise Level")
        self.ledNoi.setObjectName("stimNoi")

        self.lblDC = QLabel(to_html("DC =", frmt='b'), self)
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
        
        layHControls.addLayout(layVlblNPoints)
        layHControls.addLayout(layVledNPoints)
        layHControls.addStretch(2)
        layHControls.addLayout(layVchkLogMark)
        layHControls.addStretch(1)
        layHControls.addWidget(self.lblLogBottom)
        layHControls.addWidget(self.ledLogBottom)
        layHControls.addWidget(self.lbldB)
        layHControls.addStretch(2)
        layHControls.addLayout(layVchkPlt)
        layHControls.addStretch(1)
        layHControls.addLayout(layVlblCmb)
        layHControls.addLayout(layVCmb)
        layHControls.addStretch(2)
        layHControls.addLayout(layVlblAmp)
        layHControls.addLayout(layVledAmp)
        layHControls.addLayout(layVlblfreq)
        layHControls.addLayout(layVledfreq)
        layHControls.addLayout(layVlblfreqU)
        layHControls.addStretch(1)
        layHControls.addLayout(layVlblNoiDC)
        layHControls.addLayout(layVledNoiDC)

        layHControls.addStretch(10)
        
        self.ledN_start.editingFinished.connect(self.update_N_start)
        self.cmbStimulus.activated.connect(self.enable_controls)
        self.cmbNoise.activated.connect(self.update_noi)
        self.chkLog.clicked.connect(self.enable_log_mode)
        self.ledAmp1.editingFinished.connect(self.update_amp1)
        self.ledAmp2.editingFinished.connect(self.update_amp2)
        self.ledNoi.editingFinished.connect(self.update_noi)
        self.ledDC.editingFinished.connect(self.update_DC)
        
        # ########################  Main UI Layout ############################
        # layout for frame (UI widget)
        layVMainF = QVBoxLayout()
        layVMainF.addLayout(layHControls)

        # This frame encompasses all UI elements
        self.frmControls = QFrame(self)
        self.frmControls.setLayout(layVMainF)

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmControls)
        layVMain.setContentsMargins(*params['wdg_margins'])
        self.setLayout(layVMain)
        

    def enable_controls(self):
        """ Enable / disable widget depending on the selected stimulus"""
        stim = str(self.cmbStimulus.currentText())
        f1_en = stim in {"Cos", "Sine", "Rect", "Saw"}
        f2_en = stim in {"Cos", "Sine", "Rect", "Saw"}
        a2_en = stim in {"Cos", "Sine"}
        self.lblFreq1.setVisible(f1_en)
        self.ledFreq1.setVisible(f1_en)
        self.lblFreqUnit1.setVisible(f1_en)
        self.lblFreq2.setVisible(f2_en)
        self.ledFreq2.setVisible(f2_en)
        self.lblFreqUnit2.setVisible(f2_en)
        self.lblAmp2.setVisible(a2_en)
        self.ledAmp2.setVisible(a2_en)
        
    def enable_log_mode(self):
        log = self.chkLog.isChecked()
        self.lblLogBottom.setVisible(log)
        self.ledLogBottom.setVisible(log)
        self.lbldB.setVisible(log)
        
    def update_amp1(self):
        """ Update value for self.A1 from QLineEditWidget"""        
        self.A1 = safe_eval(self.ledAmp1.text(), self.A1, return_type='float')
        self.ledAmp1.setText(str(self.A1))
        
    def update_amp2(self):
        """ Update value for self.A2 from the QLineEditWidget"""
        self.A2 = safe_eval(self.ledAmp2.text(), self.A2, return_type='float')
        self.ledAmp2.setText(str(self.A2))

    def update_N_start(self):
        """ Update value for self.N_start from the QLineEditWidget"""
        self.N_start = safe_eval(self.ledN_start.text(), 0, return_type='int', sign='pos')
        self.ledN_start.setText(str(self.N_start))
        
    def update_noi(self):
        """ Update value for self.noi from the QLineEditWidget"""
        self.noise = self.cmbNoise.currentText().lower()
        print(self.noise)
        self.lblNoi.setVisible(self.noise!='none')
        self.ledNoi.setVisible(self.noise!='none')
        if self.noise!='none':
            self.noi = safe_eval(self.ledNoi.text(), 0, return_type='float', sign='pos')
            self.ledNoi.setText(str(self.noi))
            if self.noise == 'gauss':
                self.lblNoi.setText(to_html("&sigma; =", frmt='b'))
            elif self.noise == 'uniform':
                self.lblNoi.setText(to_html("&Delta; =", frmt='b'))

    def update_DC(self):
        """ Update value for self.DC from the QLineEditWidget"""
        self.DC = safe_eval(self.ledDC.text(), 0, return_type='float')
        self.ledDC.setText(str(self.DC))

        

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
