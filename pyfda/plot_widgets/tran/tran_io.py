# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for plotting impulse and general transient responses
"""
from pyfda.libs.compat import QWidget, pyqtSignal, QVBoxLayout
#import numpy as np
#from numpy import ndarray, pi

import pyfda.filterbroker as fb
import pyfda.libs.pyfda_io_lib as io

from pyfda.libs.pyfda_lib import (
    safe_eval, pprint_log, np_type, calc_ssb_spectrum,
    rect_bl, sawtooth_bl, triang_bl, comb_bl, safe_numexpr_eval)

from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'
from pyfda.plot_widgets.tran.tran_io_ui import Tran_IO_UI

import logging
logger = logging.getLogger(__name__)


class Tran_IO(QWidget):
    """
    Construct a widget for reading data from file
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing, e.g. when stimulus has been calculated
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        super().__init__()
        self.ui = Tran_IO_UI()  # create the UI part with buttons etc.

        # initial settings

        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None) -> None:
        """
        Process signals coming from
        - the navigation toolbars (time and freq.)
        - local widgets (impz_ui) and
        - plot_tab_widgets() (global signals)
        """

        logger.warning("SIG_RX - vis: {0}\n{1}"
                       .format(self.isVisible(), pprint_log(dict_sig)))

# ------------------------------------------------------------------------------
    def _construct_UI(self) -> None:
        """
        Instantiate the UI of the widget.
        """
        self.main_wdg = QWidget()
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.ui.wdg_top)
        layVMain.setContentsMargins(*params['mpl_margins'])

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.ui.sig_tx.connect(self.sig_tx)  # relay UI events further up
        self.sig_rx.connect(self.ui.sig_rx)  # ... and the other way round

        # ---------------------------------------------------------------------
        # UI SIGNALS & SLOTs
        # ---------------------------------------------------------------------
        self.ui.butLoad.clicked.connect(self.import_data)

        self.setLayout(layVMain)

# ------------------------------------------------------------------------------
    def import_data(self):
        self.x = io.import_data(
            self, title="Import Data", file_types=('csv', 'wav'))
