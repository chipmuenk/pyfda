# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create the UI for the Tran_IO class
"""
from PyQt5.QtWidgets import QSizePolicy
from pyfda.libs.compat import (
    QWidget, QComboBox, QLineEdit, QLabel, QPushButton,
    pyqtSignal, QEvent, Qt, QHBoxLayout, QVBoxLayout, QGridLayout, QIcon)

from pyfda.libs.pyfda_lib import to_html, safe_eval, pprint_log
import pyfda.filterbroker as fb
from pyfda.libs.pyfda_qt_lib import (
    qcmb_box_populate, qget_cmb_box, qset_cmb_box, qtext_width,
    PushButton)
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

import logging
logger = logging.getLogger(__name__)


class Tran_IO_UI(QWidget):
    """
    Create the UI for the PlotImpz class
    """
    # incoming:
    sig_rx = pyqtSignal(object)
    # outgoing: from various UI elements to PlotImpz ('ui_local':'xxx')
    sig_tx = pyqtSignal(object)

    from pyfda.libs.pyfda_qt_lib import emit

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from
        -
        -
        """

        logger.warning("PROCESS_SIG_RX - vis: {0}\n{1}"
                       .format(self.isVisible(), pprint_log(dict_sig)))

        if 'id' in dict_sig and dict_sig['id'] == id(self):
            logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
            return
        # elif 'view_changed' in dict_sig:
        #     if dict_sig['view_changed'] == 'f_S':
        #         self.recalc_freqs()

# ------------------------------------------------------------------------------
    def __init__(self, parent=None):
        """
        Pass instance `parent` of parent class (FilterCoeffs)
        """
        super(Tran_IO_UI, self).__init__(parent)
        self._construct_UI()

    def _construct_UI(self):
        # =====================================================================
        # Controls
        # =====================================================================

        self.butLoad = PushButton(self, icon=QIcon(':/file.svg'),
                                  checkable=False)
        # self.butLoad.setIconSize(q_icon_size)
        self.butLoad.setToolTip("Load data from file.")
        self.butLoad.setEnabled(True)

        self.lbl_info = QLabel(to_html("File:", frmt="b"))

        # ----------------------------------------------------------------------
        # Main Widget
        # ----------------------------------------------------------------------
        layH_io_par = QHBoxLayout()
        layH_io_par.addWidget(self.butLoad)
        layH_io_par.addWidget(self.lbl_info)

        layV_io = QVBoxLayout()
        layV_io.addLayout(layH_io_par)

        layH_io = QHBoxLayout()
        layH_io.addLayout(layV_io)
        layH_io.addStretch(10)

        self.wdg_top = QWidget(self)
        self.wdg_top.setLayout(layH_io)
        self.wdg_top.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)


# ------------------------------------------------------------------------------
# def main():
#     import sys
#     from pyfda.libs.compat import QApplication

#     app = QApplication(sys.argv)

#     mainw = Tran_IO_UI(None)
#     layVMain = QVBoxLayout()
#     layVMain.addWidget(mainw.wdg_stim)
#     layVMain.setContentsMargins(*params['wdg_margins'])  # (left, top, right, bottom)

#     mainw.setLayout(layVMain)

#     app.setActiveWindow(mainw)
#     mainw.show()
#     sys.exit(app.exec_())


if __name__ == "__main__":
    """ Run widget standalone with
        `python -m pyfda.plot_widgets.tran.tran_io_ui` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Tran_IO_UI()

    layVMain = QVBoxLayout()
    layVMain.addWidget(mainw.wdg_stim)

    mainw.setLayout(layVMain)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
