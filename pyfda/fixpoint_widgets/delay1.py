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

#import numpy as np

import pyfda.filterbroker as fb
import pprint

from ..compat import QWidget, QLabel, QVBoxLayout, QHBoxLayout

from .fixpoint_helpers import UI_W, UI_W_coeffs, UI_Q, UI_Q_coeffs

# =============================================================================
# if cmp_version("myhdl", "0.10") >= 0:
#     import myhdl
#     HAS_MYHDL = True
# 
#     fil_blocks_path = os.path.abspath(os.path.join(dirs.INSTALL_DIR, '../../filter-blocks'))
#     if not os.path.exists(fil_blocks_path):
#         logger.error("Invalid path {0}".format(fil_blocks_path))
#     else:
#         if fil_blocks_path not in sys.path:
#             sys.path.append(fil_blocks_path)
#         from pyfda.filter_blocks.fda.fir import FilterFIR
#         from pyfda.filter_blocks.fda.iir import FilterIIR    
# else:
#     HAS_MYHDL = False
# =============================================================================
#from .filter_iir import FilterIIR 
#==============================================================================

class Delay1(QWidget):
    """
    Widget for entering word formats & quantization
    """
    def __init__(self, parent):
        super(Delay1, self).__init__(parent)

        self.title = ("<b>Unit Delay</b><br />"
                 "Just a delay with quantization for testing fixpoint quantization,"
                 "simulation and HDL generation.")
        self.img_name = "df1.png"

        self._construct_UI()

#------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the UI and instantiate hdl_filter class
        """
        
        lblHBtnsMsg = QLabel("<b>Fixpoint signal / coeff. formats as WI.WF:</b>", self)
        self.layHBtnsMsg = QHBoxLayout()
        self.layHBtnsMsg.addWidget(lblHBtnsMsg)

        self.wdg_w_input = UI_W(self, label='Input Format <i>Q<sub>X </sub></i>:')
        self.wdg_q_input = UI_Q(self)
        
#------------------------------------------------------------------------------

        layVWdg = QVBoxLayout()
        layVWdg.setContentsMargins(0,0,0,0)

        layVWdg.addLayout(self.layHBtnsMsg)

        layVWdg.addWidget(self.wdg_w_input)
        layVWdg.addWidget(self.wdg_q_input)
        
        layVWdg.addStretch()

        self.setLayout(layVWdg)

#------------------------------------------------------------------------------
    def update_UI(self):
        """
        Update all parts of the UI that need to be updated when specs have been
        changed outside this class, e.g. coefficients and coefficient wordlength).
            
        This is called from one level above by `Input_Fixpoint_Specs()`.
        """
        pass
#        self.wdg_w_coeffs.load_ui() # update coefficient wordlength
#        self.wdg_q_coeffs.load_ui() # update coefficient quantization settings

#==============================================================================
    def get_hdl_dict(self):
        """
        Build the dictionary for passing infos to the filter implementation
        """
        
        # parameters for input format
        hdl_dict= {'QI':{'WI':self.wdg_w_input.WI,
                               'WF':self.wdg_w_input.WF,
                               'W':self.wdg_w_input.W,
                               'ovfl': self.wdg_q_input.ovfl,
                               'quant': self.wdg_q_input.quant
                               }
                    }

        # TODO: remove this - a leftover from an earlier version, needed for old 
        #       implementation of exportHDL
#        self.flt = FilterIIR(b=np.array(fb.fil[0]['ba'][0][0:3]),
#                a=np.array(fb.fil[0]['ba'][1][0:3]),
#                #sos = sos, doesn't work yet
#                word_format=(hdl_dict['QI']['WI'] + hdl_dict['QI']['WF'], 0,
#                             hdl_dict['QI']['WF']))
        #-------------------------------------------------
    
        return hdl_dict

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = Delay1(None)
    mainw.show()

    app.exec_()
    
    # test using "python -m pyfda.fixpoint_filters.delay1"