# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for loading and storing stimulus data from / to transient plotting widget
"""
from pyfda.libs.compat import QWidget, pyqtSignal, QVBoxLayout
import numpy as np

import pyfda.filterbroker as fb
import pyfda.libs.pyfda_io_lib as io

from pyfda.libs.pyfda_lib import safe_eval, pprint_log, safe_numexpr_eval
from pyfda.libs.pyfda_qt_lib import emit, qstyle_widget
import pyfda.libs.pyfda_dirs as dirs

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
        self.x = None  # array for file data
        self.file_load_status = "none"  # status flag ("none" / "loaded" / "error")
        self._construct_UI()
        self.norm = self.ui.led_normalize_default

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
        self.ui.but_normalize.clicked.connect(self.normalize_data)
        self.ui.led_normalize.editingFinished.connect(self.normalize_data)

        self.setLayout(layVMain)

# ------------------------------------------------------------------------------
    def import_data(self):
        self.data = io.import_data(
            self, title="Import Data", file_types=('csv', 'wav'))
        if self.data is None:
            return  # file operation cancelled
        elif type(self.data) != np.ndarray:
            logger.warning("Unsuitable file format")
            return
        else:
            # logger.info(f"Type of x: {type(self.x)}")
            logger.info(f"Last file: {dirs.last_file_name}\nType: {dirs.last_file_type}")
            ret = io.read_wav_info(dirs.last_file_name)
            if ret != 0:
                return
            logger.info(io.read_wav_info.f_S)
            logger.info(io.read_wav_info.bits_per_sample)
            if len(self.data.shape) == 1:
                self.n_chan = 1
                self.N = len(self.data)
            elif len(self.data.shape) == 2:
                self.n_chan = self.data.shape[0]
                self.N = self.data.shape[1]
            else:
                logger.error(f"Unsuitable data with shape {self.data.shape}.")
                return
            qstyle_widget(self.ui.butLoad, "active")
            self.file_load_status = "loaded"

            self.ui.lbl_filename.setText(dirs.last_file_name)
            self.ui.lbl_shape_actual.setText(
                f"Channels = {self.n_chan}, Samples = {self.N}")
            self.ui.lbl_f_S = io.read_wav_info.f_S
            self.x = self.normalize_data()

# ------------------------------------------------------------------------------
    def normalize_data(self):
        """ 
        Scale `self.data` to the maximum specified by self.ui.led_normalize and
        assign normalized result to `self.x`
        """
        if self.ui.but_normalize.isChecked() == True:
            self.norm = int(safe_eval(self.ui.led_normalize.text(), self.norm, return_type="float",
                            sign='poszero'))
            self.ui.led_normalize.setText(str(self.norm))
            self.x = self.data * self.norm / np.max(np.abs(self.data))
        else:
            self.x = self.data
            
        self.emit({'data_changed': 'file_io'})
        return