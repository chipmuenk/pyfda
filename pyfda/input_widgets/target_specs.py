
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
import sys

from pyfda.libs.compat import (
    QWidget, QLabel, QFont, QFrame, pyqtSignal, Qt, QHBoxLayout, QVBoxLayout)

import pyfda.filterbroker as fb
from pyfda.libs.pyfda_lib import pprint_log, first_item
from pyfda.input_widgets import amplitude_specs, freq_specs
from pyfda.pyfda_rc import params

import logging
logger = logging.getLogger(__name__)


class TargetSpecs(QWidget):
    """
    Build and update widget for entering the target specifications (frequencies
    and amplitudes) like F_SB, F_PB, A_SB, etc.
    """
    # class variables (shared between instances if more than one exists)
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing
    sig_tx_local = pyqtSignal(object)  # outgoing to lower hierarchies
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None, title="Target Specs", objectName=""):
        super(TargetSpecs, self).__init__(parent)

        self.title = title
        self.setObjectName(objectName)

        self._construct_UI()

# =============================================================================
#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming in via subwidgets and sig_rx
        """
        # logger.warning(f"SIG_RX: {first_item(dict_sig)}")
        if dict_sig['id'] == id(self):
          logger.warning("Stopped infinite loop.")
          return
        elif 'view_changed' in dict_sig and dict_sig['view_changed'] == 'f_S':
            # update target frequencies with new f_S
            self.emit(dict_sig, sig_name='sig_tx_local')
        elif 'data_changed' in dict_sig and dict_sig['data_changed'] == 'filter_loaded':
            self.emit(dict_sig, sig_name='sig_tx_local')
        else:
            return

# =============================================================================

    def _construct_UI(self):
        """
        Construct user interface
        """
        # subwidget for Frequency Specs
        self.f_specs = freq_specs.FreqSpecs(self, title="Frequency",
                                            objectName="freq_specs_targ")
        # subwidget for Amplitude Specs
        self.a_specs = amplitude_specs.AmplitudeSpecs(self, title="Ripple",
                                                      objectName="amplitude_specs_targ")
        self.a_specs.setVisible(True)
        """
        LAYOUT
        """
        bfont = QFont()
        bfont.setBold(True)
        lblTitle = QLabel(self)  # field for widget title
        lblTitle.setText(self.title)
        lblTitle.setFont(bfont)
#        lblTitle.setContentsMargins(2,2,2,2)

        layHTitle = QHBoxLayout()
        layHTitle.addWidget(lblTitle)
        layHTitle.setAlignment(Qt.AlignHCenter)
        layHSpecs = QHBoxLayout()
        layHSpecs.setAlignment(Qt.AlignTop)
        layHSpecs.addWidget(self.f_specs)  # frequency specs
        layHSpecs.addWidget(self.a_specs)  # ampltitude specs

        layVSpecs = QVBoxLayout()
        layVSpecs.addLayout(layHTitle)
        layVSpecs.addLayout(layHSpecs)
        layVSpecs.setContentsMargins(0, 6, 0, 0)  # (left, top, right, bottom)

        # This is the top level widget, encompassing the other widgets
        frmMain = QFrame(self)
        frmMain.setLayout(layVSpecs)

        self.layVMain = QVBoxLayout()  # Widget main layout
        self.layVMain.addWidget(frmMain)
        self.layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(self.layVMain)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # process incoming global signals
        self.sig_rx.connect(self.process_sig_rx)
        # connect signals from f_specs and a_specs subwidget to higher hierarchies
        self.f_specs.sig_tx.connect(self.sig_tx)
        self.a_specs.sig_tx.connect(self.sig_tx)
        # pass on prefiltered received signals
        self.sig_tx_local.connect(self.f_specs.sig_rx)
        self.sig_tx_local.connect(self.a_specs.sig_rx)

        self.update_UI()  # first time initialization

# ------------------------------------------------------------------------------
    def update_UI(self, new_labels=()):
        """
        Called when a new filter design algorithm has been selected
        - Pass new frequency and amplitude labels to the amplitude and frequency
          spec widgets. The first element of the 'amp' and the 'freq' tuple
          is the state with 'u' for 'unused' and 'd' for disabled

        - The `filt_changed` signal is emitted already by `select_filter.py`
        """

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

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.input_widgets.target_specs` """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)

    # Read freq / amp / weight labels for current filter design
    rt = fb.fil[0]['rt']
    ft = fb.fil[0]['ft']
    fc = fb.fil[0]['fc']

    if 'min' in fb.fil_tree[rt][ft][fc]:
        # extract target parameters from filter tree
        print(fb.fil_tree[rt][ft][fc]['min']['tspecs'])
        target_params = fb.fil_tree[rt][ft][fc]['min']['tspecs'][1]
    else:
        target_params = {}

    mainw = TargetSpecs(title="Test Specs")
    mainw.update_UI(target_params)

    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
