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
logger = logging.getLogger(__name__)

from pyfda.compat import (QtGui, QWidget, QFont, QCheckBox, QFrame,
                      QTableWidget, QTableWidgetItem, QTextBrowser, QTextCursor,
                      QVBoxLayout, QHBoxLayout, QSplitter, Qt, pyqtSignal)


import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_rc import params


class My_Input_Widget(QWidget):
    """
    Template for user widget
    """
    sig_rx = pyqtSignal(object) # incoming signals from input_tab_widgets
    sig_tx = pyqtSignal(object) # outgoing signals to input_tab_widgets

    def __init__(self, parent):
        super(My_Input_Widget, self).__init__(parent)
        
        self.tab_label = 'MyWdg'
        self.tool_tip = ("<span>This is my first pyFDA widget!</span>")       
        
        self._construct_UI()
        self.load_dict()

    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if 'data_changed' in dict_sig or 'view_changed' in dict_sig or 'specs_changed' in dict_sig:
            self.load_dict()

    def _construct_UI(self):
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
                                                  
        self.chkFiltDict = QCheckBox("FiltDict", self)
        self.chkFiltDict.setToolTip("Show filter dictionary for debugging.")   

        self.layHChkBoxes = QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkFiltDict)
        self.layHChkBoxes.addStretch(1)
        self.frmMain = QFrame(self)
        self.frmMain.setLayout(self.layHChkBoxes)

        self.txtFiltDict = QTextBrowser(self)

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmMain)
        layVMain.addWidget(self.txtFiltDict)
        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.chkFiltDict.clicked.connect(self._show_filt_dict)

#------------------------------------------------------------------------------
    def load_dict(self):
        """
        update docs and filter performance
        """
        self._show_filt_dict()

#------------------------------------------------------------------------------
    def _show_filt_dict(self):
        """
        Print filter dict for debugging
        """
        self.txtFiltDict.setVisible(self.chkFiltDict.isChecked())

        fb_sorted = [str(key) +' : '+ str(fb.fil[0][key]) for key in sorted(fb.fil[0].keys())]
        dictstr = pprint.pformat(fb_sorted)
        self.txtFiltDict.setText(dictstr)

        
#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = My_Input_Widget(None)

    app.setActiveWindow(mainw) 
    mainw.show()

    sys.exit(app.exec_())
