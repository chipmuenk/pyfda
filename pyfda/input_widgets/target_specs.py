# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget collecting subwidgets for the target filter specifications (currently
only amplitude and frequency specs.)
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

from ..compat import (QWidget, QLabel, QFont, QFrame, pyqtSignal, Qt,
                      QHBoxLayout, QVBoxLayout)

import pyfda.filterbroker as fb
from pyfda.input_widgets import amplitude_specs, freq_specs
from pyfda.pyfda_rc import params


class TargetSpecs(QWidget):
    """
    Build and update widget for entering the target specifications (frequencies
    and amplitudes) like F_SB, F_PB, A_SB, etc.
    """
    # class variables (shared between instances if more than one exists)
    # sig_rx = pyqtSignal(object) # incoming
    sig_tx = pyqtSignal(object) # outgoing

    def __init__(self, parent, title = "Target Specs"):
        super(TargetSpecs, self).__init__(parent)

        self.title = title
        
        self._construct_UI()

# =============================================================================
# #------------------------------------------------------------------------------
#     def process_sig_rx(self, dict_sig=None):
#         """
#         Process signals coming in via subwidgets and sig_rx
#         """
#         logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
#         if dict_sig['sender'] == __name__:
#             logger.warning("Infinite loop detected")
#             return
# #------------------------------------------------------------------------------
# =============================================================================
    def _construct_UI(self):
        """
        Construct user interface
        """
        # subwidget for Frequency Specs
        self.f_specs = freq_specs.FreqSpecs(self, title = "Frequency")
        self.f_specs.sig_tx.connect(self.sig_tx) # pass signal upwards
        #self.sig_tx.connect(self.f_specs.sig_rx)
        # subwidget for Amplitude Specs
        self.a_specs = amplitude_specs.AmplitudeSpecs(self, title = "Amplitude")
        self.a_specs.setVisible(True)
        self.a_specs.sig_tx.connect(self.sig_tx) # pass signal upwards
        """
        LAYOUT
        """
        bfont = QFont()
        bfont.setBold(True)
        lblTitle = QLabel(self) # field for widget title
        lblTitle.setText(self.title)
        lblTitle.setFont(bfont)
#        lblTitle.setContentsMargins(2,2,2,2)
        
        layHTitle = QHBoxLayout()
        layHTitle.addWidget(lblTitle)
        layHTitle.setAlignment(Qt.AlignHCenter)
        layHSpecs = QHBoxLayout()
        layHSpecs.setAlignment(Qt.AlignTop)
        layHSpecs.addWidget(self.f_specs) # frequency specs
        layHSpecs.addWidget(self.a_specs) # ampltitude specs

        layVSpecs = QVBoxLayout()
        layVSpecs.addLayout(layHTitle)
        layVSpecs.addLayout(layHSpecs)
        layVSpecs.setContentsMargins(0,6,0,0) # (left, top, right, bottom)

        # This is the top level widget, encompassing the other widgets        
        frmMain = QFrame(self)
        frmMain.setLayout(layVSpecs)

        self.layVMain = QVBoxLayout() # Widget main layout
        self.layVMain.addWidget(frmMain)
        self.layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(self.layVMain)
        
        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # self.sig_rx.connect(self.process_sig_rx)
        
        self.update_UI() # first time initialization

#------------------------------------------------------------------------------
    def update_UI(self, new_labels = ()):
        """
        Called when a new filter design algorithm has been selected
        Pass frequency and amplitude labels to the amplitude and frequency
        spec widgets
        The sigSpecsChanged signal is emitted already by select_filter.py
        """

        # pass new labels to widgets. The first element of the 'amp' and the
        # 'freq' tuple is the state, 'u' is for 'unused', 'd' is for disabled

        if ('frq' in new_labels and len(new_labels['frq']) > 1 and
                                              new_labels['frq'][0] != 'i'):
            self.f_specs.show()
            self.f_specs.setEnabled(new_labels['frq'][0] != 'd')
            self.f_specs.update_UI(new_labels=new_labels['frq'])
        else:
            self.f_specs.hide()
            
        if ('amp' in new_labels and len(new_labels['amp']) > 1 and
                                              new_labels['amp'][0] != 'i'):
            self.a_specs.show()
            self.a_specs.setEnabled(new_labels['amp'][0] != 'd')
            self.a_specs.update_UI(new_labels=new_labels['amp'])
        else:
            self.a_specs.hide()

        # self.sig_tx.emit({'sender':__name__, 'changed_specs':'target'})

#------------------------------------------------------------------------------
    def load_dict(self):
        """
        Update entries from global dict fb.fil[0]
        parameters, using the "load_dict" methods of the classes
        """
        self.a_specs.load_dict() # magnitude specs with unit
        self.f_specs.load_dict() # weight specification

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)

    # Read freq / amp / weight labels for current filter design
    rt = fb.fil[0]['rt']
    ft = fb.fil[0]['ft']
    fc = fb.fil[0]['fc']

    if 'min' in fb.fil_tree[rt][ft][fc]:
        my_params = fb.fil_tree[rt][ft][fc]['min']['par']
    else:
        my_params = {}

    # build separate parameter lists according to the first letter
    freq_params = [l for l in my_params if l[0] == 'F']
    amp_params = [l for l in my_params if l[0] == 'A']

    mainw = TargetSpecs(None, title = "Test Specs")
    mainw.update_UI(freq_params, amp_params)
    
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())
