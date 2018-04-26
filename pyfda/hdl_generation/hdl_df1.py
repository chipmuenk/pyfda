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
import sys
import logging
logger = logging.getLogger(__name__)

from ..compat import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame)

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

        self.title = ("<b>Direct-Form 1 (DF1) Filters</b><br />"
                 "Simple topology, only suitable for low-order filters.")
        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the UI
        """
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
       
        layVMain = QVBoxLayout()
        layVMain.addWidget(frmWdg)

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