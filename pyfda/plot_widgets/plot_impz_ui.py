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

from pyfda.pyfda_lib import expand_lim, to_html, safe_eval
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
        self.f1 = 0.02
        self.f2 = 0.03
        self.A = 1.0
        self.A2 = 0.0
        self.bottom = -80
        self._construct_UI()
        self.enable_controls()
        self.enable_log_mode()

    def _construct_UI(self):
        self.lblNPoints = QLabel("<i>N</i>&nbsp; =", self)

        self.ledNPoints = QLineEdit(self)
        self.ledNPoints.setText("0")
        self.ledNPoints.setToolTip("<span>Number of points to calculate and display. "
                                   "N = 0 tries to choose for you.</span>")
        self.lblNStart = QLabel("<i>N</i><sub>0</sub>&nbsp; =", self)

        self.ledNStart = QLineEdit(self)
        self.ledNStart.setText("0")
        self.ledNStart.setToolTip("<span>First point to plot.</span>")
        
        layVlblNPoints = QVBoxLayout()
        layVlblNPoints.addWidget(self.lblNStart)
        layVlblNPoints.addWidget(self.lblNPoints)
        
        layVledNPoints = QVBoxLayout()
        layVledNPoints.addWidget(self.ledNStart)
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
        
        self.lblStimulus = QLabel("Type = ", self)
        self.cmbStimulus = QComboBox(self)
        self.cmbStimulus.addItems(["Pulse","Step","StepErr", "Cos", "Sine", "Rect", "Saw", "RandN", "RandU"])
        self.cmbStimulus.setToolTip("Select stimulus type.")

        self.lblAmp1 = QLabel("<i>A</i>&nbsp; =", self)
        self.ledAmp1 = QLineEdit(self)
        self.ledAmp1.setText(str(self.A))
        self.ledAmp1.setToolTip("Stimulus amplitude.")
        self.ledAmp1.setObjectName("stimAmp1")
        
        self.lblAmp2 = QLabel("<i>A</i><sub>2</sub>&nbsp; =", self)
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

        self.lblFreq1 = QLabel("<i>f</i><sub>1</sub>&nbsp; =", self)
        self.ledFreq1 = QLineEdit(self)
        self.ledFreq1.setText(str(self.f1))
        self.ledFreq1.setToolTip("Stimulus frequency 1.")
        self.ledFreq1.setObjectName("stimFreq1")
        self.lblFreqUnit1 = QLabel("f_S", self)

        self.lblFreq2 = QLabel("<i>f</i><sub>2</sub>&nbsp; =", self)
        self.lblFreq2.setEnabled(False)
        self.ledFreq2 = QLineEdit(self)
        self.ledFreq2.setText(str(self.f2))
        self.ledFreq2.setToolTip("Stimulus frequency 2.")
        self.ledFreq2.setObjectName("stimFreq2")
        self.ledFreq2.setEnabled(False)
        self.lblFreqUnit2 = QLabel("f_S", self)
        self.lblFreqUnit2.setEnabled(False)

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
        layHControls.addWidget(self.lblStimulus)
        layHControls.addWidget(self.cmbStimulus)
        layHControls.addStretch(2)
        layHControls.addLayout(layVlblAmp)
        layHControls.addLayout(layVledAmp)
        layHControls.addWidget(self.lblFreq1)
        layHControls.addWidget(self.ledFreq1)
        layHControls.addWidget(self.lblFreqUnit1)

        layHControls.addStretch(10)
        
        self.cmbStimulus.activated.connect(self.enable_controls)
        self.chkLog.clicked.connect(self.enable_log_mode)
        
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
