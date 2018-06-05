# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for specifying the parameters of a direct-form 1 (DF1) filter
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

import numpy as np

import pyfda.filterbroker as fb
import pyfda.pyfda_fix_lib as fix
import pprint

from ..compat import QWidget, QLabel, QVBoxLayout, QHBoxLayout, pyqtSignal

from .fixpoint_helpers import UI_WI_WF, UI_W_coeffs, UI_Q_Ovfl, build_coeff_dict
from .filter_iir import FilterIIR 

#==============================================================================

class DF1(QWidget):
    """
    Create the widget for quantizing data and coef
    """
    sig_rx = pyqtSignal(object)
    
    def __init__(self, parent):
        super(DF1, self).__init__(parent)

        self.title = ("<b>Direct-Form 1 (DF1) Filters</b><br />"
                 "Simple topology, only suitable for low-order filters.")
        self.img_name = "hdl_df1.png"
        # construct coefficient fixpoint object with initial settings
        self.Q_coeff = fix.Fixed(fb.fil[0]["q_coeff"])
        self._construct_UI()

    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming in via subwidgets and sig_rx
        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if dict_sig['sender'] == __name__:
            return
        elif 'specs_changed' in dict_sig:
            self.update_UI()
    
    def _construct_UI(self):
        """
        Intitialize the UI and instantiate hdl_filter class
        """
#------------------------------------------------------------------------------
        
        lblHBtnsMsg = QLabel("<b>Fixpoint signal / coeff. formats as WI.WF:</b>", self)
        self.layHBtnsMsg = QHBoxLayout()
        self.layHBtnsMsg.addWidget(lblHBtnsMsg)

        self.wdg_w_input = UI_WI_WF(self, label='Input Format x[n]:')
        self.wdg_w_coeffs = UI_W_coeffs(self, label='Coefficient Format:', enabled=True)
        self.wdg_q_coeffs = UI_Q_Ovfl(self, enabled=False)
        self.wdg_w_accu = UI_WI_WF(self, label='Accumulator Format:', WF=30)
        self.wdg_q_accu = UI_Q_Ovfl(self)
        self.wdg_w_output = UI_WI_WF(self, label='Output Format y[n]:')
        self.wdg_q_output = UI_Q_Ovfl(self)        
#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0,0,0,0)

        layVWdg.addLayout(self.layHBtnsMsg)
        layVWdg.addWidget(self.wdg_w_input)
        layVWdg.addWidget(self.wdg_w_coeffs)
        layVWdg.addWidget(self.wdg_q_coeffs)

        layVWdg.addWidget(self.wdg_w_accu)
        layVWdg.addWidget(self.wdg_q_accu)

        layVWdg.addWidget(self.wdg_w_output)
        layVWdg.addWidget(self.wdg_q_output)

        layVWdg.addStretch()

        self.setLayout(layVWdg)
        
    def update_UI(self):
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class (e.g. coefficient wordlength).
        This is called from one level above.
        """
        self.wdg_w_coeffs.load_ui()


#==============================================================================
    def build_hdl_dict(self):
        """
        Build the dictionary for constructing the filter
        """
        hdl_dict = {'QC':build_coeff_dict()} # coefficients
        # parameters for input format
        hdl_dict.update({'QI':{'WI':self.wdg_w_input.WI,
                               'WF':self.wdg_w_input.WF
                               }
                        })
        # parameters for output format
        hdl_dict.update({'QO':{'WI':self.wdg_w_output.WI,
                               'WF':self.wdg_w_output.WF,
                               'OVFL': self.wdg_q_output.ovfl,
                               'QUANT': self.wdg_q_output.quant
                               }
                        })
  
        hdl_dict_sorted = [str(k) +' : '+ str(hdl_dict[k]) for k in sorted(hdl_dict.keys())]
        hdl_dict_str = pprint.pformat(hdl_dict_sorted)
        logger.info("exporting hdl_dict:\n{0:s}".format(hdl_dict_str))   

        return hdl_dict


#==============================================================================
    def setup_HDL(self, coeffs):
        """
        Instantiate the myHDL description and pass quantization parameters and
        coefficients.
        """
        WI_i = self.wdg_w_input.WI
        WF_i = self.wdg_w_input.WF

        WI_o = self.wdg_w_output.WI
        WF_o = self.wdg_w_output.WF

        quant_o = self.wdg_q_output.quant
        ovfl_o = self.wdg_q_output.ovfl
        
        self.build_hdl_dict()

        # a dict like this could be passed to the HDL description
        q_dict =  {'WI':WI_o, 'WF': WF_o, 'quant': quant_o, 'ovfl': ovfl_o}

        self.W = (WI_i + WF_i + 1, WF_i) # Matlab format: (W,WF)
        
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
    mainw = DF1(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.hdl_generation.hdl_df1"