# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for simulating fixpoint filters and
generating VHDL and Verilog Code
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import logging
logger = logging.getLogger(__name__)

from ..compat import (Qt, QWidget, QLabel, QSplitter,
                      QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, QPixmap)

from pyfda.hdl_generation.hdl_helpers import UI_WI_WF, UI_Q_Ovfl

from pyfda.pyfda_rc import params
#==============================================================================

class HDL_DF1(QWidget):
    """
    Create the widget for quantizing data and coef
    """
    sig_rx = pyqtSignal(object)
    
    def __init__(self, parent):
        super(HDL_DF1, self).__init__(parent)

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the main GUI, consisting of:
        """
        lblMsg = QLabel("<b>Direct-Form 1 (DF1) Filters</b><br />"
                        "Simple filters", self)
        lblMsg.setWordWrap(True)
        layHMsg = QHBoxLayout()
        layHMsg.addWidget(lblMsg)

        self.frmMsg = QFrame(self)
        self.frmMsg.setLayout(layHMsg)
        self.frmMsg.setContentsMargins(*params['wdg_margins'])

#------------------------------------------------------------------------------

        self.lbl_img_hdl = QLabel(self)
        file_path = os.path.dirname(os.path.realpath(__file__))
        img_file = os.path.join(file_path, "hdl-df1.png")
        img_hdl = QPixmap(img_file)
        img_hdl_scaled = img_hdl.scaled(self.lbl_img_hdl.size(), Qt.KeepAspectRatio)
        # self.lbl_img_hdl.setPixmap(QPixmap(img_hdl_scaled))
        self.lbl_img_hdl.setPixmap(QPixmap(img_hdl)) # fixed size

        layHImg = QHBoxLayout()
        layHImg.addWidget(self.lbl_img_hdl)
        self.frmImg = QFrame(self)
        self.frmImg.setLayout(layHImg)
        self.frmImg.setContentsMargins(*params['wdg_margins'])

#------------------------------------------------------------------------------

        lblHBtnsMsg = QLabel("<b>Fixpoint signal / coeff. formats as WI.WF:</b>", self)
        self.layHBtnsMsg = QHBoxLayout()
        self.layHBtnsMsg.addWidget(lblHBtnsMsg)

        self.wdg_wi_wf_input = UI_WI_WF(self, label='Input Format x[n]:')
        self.wdg_wi_wf_coeffs = UI_WI_WF(self, label='Coefficient Format:')
        self.wdg_q_ovfl_coeffs = UI_Q_Ovfl(self)
        self.wdg_wi_wf_accu = UI_WI_WF(self, label='Accumulator Format:', WF=30)
        self.wdg_q_ovfl_accu = UI_Q_Ovfl(self)
        self.wdg_wi_wf_output = UI_WI_WF(self, label='Output Format y[n]:')
        self.wdg_q_ovfl_output = UI_Q_Ovfl(self)

#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.addLayout(self.layHBtnsMsg)
        layVWdg.addWidget(self.wdg_wi_wf_input)
        layVWdg.addWidget(self.wdg_wi_wf_coeffs)
        self.wdg_wi_wf_coeffs.setEnabled(False)
        layVWdg.addWidget(self.wdg_q_ovfl_coeffs)
        self.wdg_q_ovfl_coeffs.setEnabled(False)

        layVWdg.addWidget(self.wdg_wi_wf_accu)
        layVWdg.addWidget(self.wdg_q_ovfl_accu)

        layVWdg.addWidget(self.wdg_wi_wf_output)
        layVWdg.addWidget(self.wdg_q_ovfl_output)

        layVWdg.addStretch()

        # -------------------------------------------------------------------
        # This frame encompasses all the subwidgets
        frmWdg = QFrame(self)
        frmWdg.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmWdg.setLayout(layVWdg)

    # -------------------------------------------------------------------
    # Top level layout
    # -------------------------------------------------------------------
       
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(self.frmMsg)
        splitter.addWidget(self.frmImg)
        splitter.addWidget(frmWdg)
        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([1000,3000,10000])

        layVMain = QVBoxLayout()
        layVMain.addWidget(splitter)
        #layVMain.addWidget(self.frmMsg)
        #layVMain.addWidget(self.frmImg)
        #layVMain.addWidget(frmBtns)
        #layVMain.addStretch()
        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = HDL_DF1(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.hdl_generation.hdl_df1"