# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form 2 (DF2) filter
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

import numpy as np

from ..compat import QWidget, QLabel, QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame

from pyfda.hdl_generation.hdl_helpers import UI_WI_WF, UI_Q_Ovfl
from pyfda.hdl_generation.filter_iir import FilterIIR 
#==============================================================================

class HDL_DF2(QWidget):
    """
    Create the widget for quantizing data and coef
    """
    sig_rx = pyqtSignal(object)
    
    def __init__(self, parent):
        super(HDL_DF2, self).__init__(parent)

        self.title = ("<b>Direct-Form 2 (DF2) Filters</b><br />"
                 "Simple topology, only suitable for low-order filters.")
        self.img_name = "hdl_df2.png"
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
        #self.wdg_wi_wf_accu = UI_WI_WF(self, label='Accumulator Format:', WF=30)
        #self.wdg_q_ovfl_accu = UI_Q_Ovfl(self)
        self.wdg_wi_wf_output = UI_WI_WF(self, label='Output Format y[n]:')
        self.wdg_q_ovfl_output = UI_Q_Ovfl(self)

#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0,0,0,0)
        layVWdg.addLayout(self.layHBtnsMsg)
        layVWdg.addWidget(self.wdg_wi_wf_input)
        layVWdg.addWidget(self.wdg_wi_wf_coeffs)
        self.wdg_wi_wf_coeffs.setEnabled(False)
        layVWdg.addWidget(self.wdg_q_ovfl_coeffs)
        self.wdg_q_ovfl_coeffs.setEnabled(False)

        #layVWdg.addWidget(self.wdg_wi_wf_accu)
        #layVWdg.addWidget(self.wdg_q_ovfl_accu)

        layVWdg.addWidget(self.wdg_wi_wf_output)
        layVWdg.addWidget(self.wdg_q_ovfl_output)

        layVWdg.addStretch()

        self.setLayout(layVWdg)
        
#==============================================================================
    def setup_HDL(self, coeffs):
        """
        Instantiate the myHDL description and pass quantization parameters and
        coefficients.
        """
        self.qI_i = self.wdg_wi_wf_input.WI
        self.qF_i = self.wdg_wi_wf_input.WF

        self.qI_o = self.wdg_wi_wf_output.WI
        self.qF_o = self.wdg_wi_wf_output.WF

        qQuant_o = self.wdg_q_ovfl_output.quant
        qOvfl_o = self.wdg_q_ovfl_output.ovfl

        # a dict like this could be passed to the HDL description
        q_obj_o =  {'WI':self.qI_o, 'WF': self.qF_o, 'quant': qQuant_o, 'ovfl': qOvfl_o}

        self.W = (self.qI_i + self.qF_i + 1, self.qF_i) # Matlab format: (W,WF)
        
        logger.info("W = {0}".format(self.W))
        logger.info('b = {0}'.format(coeffs[0][0:3]))
        logger.info('a = {0}'.format(coeffs[1][0:3]))

        
        self.flt = FilterIIR(b=np.array(coeffs[0][0:3]),
                a=np.array(coeffs[1][0:3]),
                #sos = sos, doesn't work yet
                word_format=(self.W[0], 0, self.W[1]))

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = HDL_DF2(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.hdl_generation.hdl_df1"