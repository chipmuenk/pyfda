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

from pyfda.libs.pyfda_lib import safe_eval, pprint_log, safe_numexpr_eval, to_html
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
        self.file_name = None  # full name of loaded file
        self.file_type = None  # type of loaded file
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
        self.ui.but_select.clicked.connect(self.select_file)
        self.ui.but_load.clicked.connect(self.import_data)
        self.ui.but_normalize.clicked.connect(self.normalize_data)
        self.ui.led_normalize.editingFinished.connect(self.normalize_data)

        self.setLayout(layVMain)

# ------------------------------------------------------------------------------
    def select_file(self):
        """
        Select a file and peek into it to find the dimensions and some
        other infos (depending on the file type).

        Unload previous file from memory
        """
        self.file_name, self.file_type = io.select_file(
            self, title="Import Data", mode="r", file_types=('csv', 'wav'))

        self.N = None
        self.nchans = None
        self.f_S = None
        self.WL = None

        if self.file_name is None:
            return  # operation cancelled
        elif self.file_type == 'wav':
            ret = io.read_wav_info(self.file_name)
            if ret < 0:
                return
            self.N = io.read_wav_info.N
            self.nchans = io.read_wav_info.nchans
            self.f_S = io.read_wav_info.f_S
            self.WL = io.read_wav_info.WL
            info_str = f" x {self.WL * 8} bits,"
            self.ui.frm_f_s.setVisible(True)
            self.ui.lbl_f_s_value.setText(str(self.f_S))

        elif self.file_type == 'csv':
            ret = io.read_csv_info(self.file_name)
            if ret < 0:
                return
            self.ui.frm_f_s.setVisible(False)
            self.N = io.read_csv_info.N
            self.nchans = io.read_csv_info.nchans
            info_str = f" ({io.read_csv_info.info})"
        else:
            logger.error(f"Unknown file format '{self.file_type}'")

        if len(self.file_name) < 45:
            self.ui.lbl_filename.setText(self.file_name)
        else:
            self.ui.lbl_filename.setText(
                self.file_name[:10] + ' ... ' + self.file_name[-20:])

        del self.x
        self.x = None
        self.ui.but_load.setText("Load")
        qstyle_widget(self.ui.but_load, "normal")

        self.ui.lbl_filename.setToolTip(self.file_name)
        self.ui.lbl_shape_actual.setText(
            f"{self.nchans} x {self.N}{info_str}")

# ------------------------------------------------------------------------------
    def import_data(self):
        if self.file_name is None:
            logger.warning("No valid file has been selected yet!")
            return -1
        self.data = io.import_data(self.file_name, self.file_type)
        if self.data is None:
            return -1  # file operation cancelled
        elif type(self.data) != np.ndarray:
            logger.warning("Unsuitable file format")
            return -1

        # if len(self.data.shape) == 1:
        #     self.n_chan = 1
        #     self.N = len(self.data)
        # elif len(self.data.shape) == 2:
        #     self.n_chan = self.data.shape[1]
        #     self.N = self.data.shape[0]
        # else:
        #     logger.error(f"Unsuitable data with shape {self.data.shape}.")
        #     self.n_chan = -1
        #     self.N = -1
        #     return

        qstyle_widget(self.ui.but_load, "ok")
        self.ui.but_load.setText("Loaded")
        self.file_load_status = "loaded"

        self.x = self.normalize_data()

        return 0

# ------------------------------------------------------------------------------
    def normalize_data(self):
        """
        Scale `self.data` to the maximum specified by self.ui.led_normalize and
        assign normalized result to `self.x`
        """
        if not hasattr(self, 'data') or self.data is None:
            logger.error("No data loaded yet.")
            return
        if self.ui.but_normalize.isChecked() == True:
            self.norm = int(safe_eval(self.ui.led_normalize.text(), self.norm, return_type="float",
                            sign='poszero'))
            self.ui.led_normalize.setText(str(self.norm))
            self.x = self.data * self.norm / np.max(np.abs(self.data))
        else:
            self.x = self.data

        self.emit({'data_changed': 'file_io'})
        return