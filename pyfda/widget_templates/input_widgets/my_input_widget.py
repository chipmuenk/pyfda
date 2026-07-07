# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget template, demonstrating sig_rx / sig_tx mechanism and text output
"""
import sys
import pprint
import logging

from pyfda.libs.compat import (QWidget, QFont, QCheckBox, QFrame,
                      QTextBrowser, QVBoxLayout, QHBoxLayout, pyqtSignal)

import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params

logger = logging.getLogger(__name__)

class MyInputWidget(QWidget):
    """
    Template for user input widget
    """
    sig_rx = pyqtSignal(object) # incoming signals from input_tab_widgets
    sig_tx = pyqtSignal(object) # outgoing signals to input_tab_widgets

    def __init__(self):
        super().__init__()

        self.tab_label = 'MyWdg'
        self.tool_tip = "<span>This is my first pyFDA widget!</span>"

        self._construct_ui()
        self.dict2ui()

    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        logger.debug("Processing %s: %s", type(dict_sig).__name__, dict_sig)
        if 'data_changed' in dict_sig or 'view_changed' in dict_sig or 'specs_changed' in dict_sig:
            self.dict2ui()

    def _construct_ui(self):
        """
        Intitialize the widget, consisting of:
        - Checkboxes for selecting the info to be displayed
        - A large text window for displaying infos about the filter design
          algorithm
        """
        bfont = QFont()
        bfont.setBold(True)

        # ============== UI Layout =====================================
        # widget / subwindow for filter infos

        self.chk_filt_dict = QCheckBox("FiltDict", self)
        self.chk_filt_dict.setToolTip("Show filter dictionary for debugging.")

        self.lay_h_chk_boxes = QHBoxLayout()
        self.lay_h_chk_boxes.addWidget(self.chk_filt_dict)
        self.lay_h_chk_boxes.addStretch(1)
        self.frm_main = QFrame(self)
        self.frm_main.setLayout(self.lay_h_chk_boxes)

        self.txt_filt_dict = QTextBrowser(self)

        lay_v_main = QVBoxLayout()
        lay_v_main.addWidget(self.frm_main)
        lay_v_main.addWidget(self.txt_filt_dict)
        lay_v_main.setContentsMargins(*params['wdg_margins'])

        self.setLayout(lay_v_main)

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.chk_filt_dict.clicked.connect(self._show_filt_dict)

#------------------------------------------------------------------------------
    def dict2ui(self):
        """
        update docs and filter performance
        """
        self._show_filt_dict()

#------------------------------------------------------------------------------
    def _show_filt_dict(self):
        """
        Print filter dict for debugging
        """
        self.txt_filt_dict.setVisible(self.chk_filt_dict.isChecked())

        fb_sorted = [str(key) +' : '+ str(fb.fil[0][key]) for key in sorted(fb.fil[0].keys())]
        dictstr = pprint.pformat(fb_sorted)
        self.txt_filt_dict.setText(dictstr)


#------------------------------------------------------------------------------

if __name__ == '__main__':

    from pyfda.libs.compat import QApplication
    app = QApplication(sys.argv)
    mainw = MyInputWidget()

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
