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

        if 'closeEvent' in dict_sig:
            self.ui.but_csv_options.setChecked(False)
        elif 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed'] == 'csv'\
            and self.ui.but_csv_options.isChecked():
                self.ui.wdg_csv_options.load_settings()

# ------------------------------------------------------------------------------
    def _construct_UI(self) -> None:
        """
        Instantiate the UI of the widget
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
        self.ui.cmb_chan.currentIndexChanged.connect(self.select_chan_normalize)
        self.ui.but_load.clicked.connect(self.import_data)
        self.ui.but_normalize.clicked.connect(self.select_chan_normalize)
        self.ui.led_normalize.editingFinished.connect(self.select_chan_normalize)

        self.ui.wdg_csv_options.sig_tx.connect(self.process_sig_rx)

        self.setLayout(layVMain)

# ------------------------------------------------------------------------------
    def select_file(self):
        """
        Select a file in a UI dialog and peek into it to find the dimensions
        and some other infos (depending on the file type).

        When the selection was successful, store the fully qualified file name
        and the file type in the attributes `self.file_name` and `self.file_type`,
        delete previous data `self.x` from memory and return 0.
        When an error occurred, return -1.

        """
        file_name_prev = self.file_name
        file_type_prev = self.file_type

        self.file_name, self.file_type = io.select_file(
            self, title="Import Data", mode="r", file_types=('csv', 'wav'))

        if self.file_name is None:  # operation cancelled
            self.file_name = file_name_prev
            self.file_type = file_type_prev
            return -1

        self.N = None
        self.nchans = None
        self.f_S = None
        self.WL = None

        del self.x
        self.x = None

        if self.file_type == 'wav':
            ret = io.read_wav_info(self.file_name)
            if ret < 0:
                return -1
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
                return -1
            self.ui.frm_f_s.setVisible(False)
            self.N = io.read_csv_info.N
            self.nchans = io.read_csv_info.nchans
            info_str = f" ({io.read_csv_info.info})"
        else:
            logger.error(f"Unknown file format '{self.file_type}'")
            return -1

        if self.nchans > 9:
            logger.warning(
                f"Unsuitable file format with {io.read_csv_info} > 9 columns.")
            return -1
        elif self.nchans == 1:
            self.ui.lbl_chan.setVisible(False)
            self.ui.cmb_chan.setVisible(False)
            self.ui.line_chan.setVisible(False)
        else:
            self.ui.lbl_chan.setVisible(True)
            self.ui.cmb_chan.setVisible(True)
            self.ui.line_chan.setVisible(True)
            self.ui.cmb_chan.clear()
            # create a list with the numbers of the channels and the
            # sum sign and populate the combo box with it
            # don't emit a signal while re-initializing the combo box
            self.ui.cmb_chan.blockSignals(True)
            self.ui.cmb_chan.addItems(
                [str(k + 1) for k in range(self.nchans)] + ["Σ"]
                )
            self.ui.cmb_chan.blockSignals(False)

        if len(self.file_name) < 45:
            self.ui.lbl_filename.setText(self.file_name)
        else:
            self.ui.lbl_filename.setText(
                self.file_name[:10] + ' ... ' + self.file_name[-20:])

        self.ui.but_load.setEnabled(True)
        self.ui.but_load.setText("Load")
        qstyle_widget(self.ui.but_load, "normal")
        self.ui.but_normalize.setEnabled(False)

        self.ui.lbl_filename.setToolTip(self.file_name)
        self.ui.lbl_shape_actual.setText(
            f"{self.nchans} x {self.N}{info_str}")
        return 0

# ------------------------------------------------------------------------------
    def import_data(self):
        logger.info("import data")
        err = False
        if self.file_name is None:
            logger.warning("No valid file has been selected yet!")
            err = True

        self.data_raw = io.import_data(self.file_name, self.file_type)

        if self.data_raw is None:  # file operation cancelled
            err = True
        elif type(self.data_raw) != np.ndarray:
            logger.warning("Unsuitable file format")
            err = True

        if err:
            self.ui.but_load.setEnabled(False)
            return -1

        if self.data_raw.ndim == 1:
            nchans_actual = 1
            N_actual = len(self.data_raw)
        elif self.data_raw.ndim == 2:
            nchans_actual, N_actual = np.shape(self.data_raw)
        else:
            logger.warning("Unsuitable data shape with "
                           f"{self.data_raw.ndim} dimensions.")
            return -1

        if (nchans_actual, N_actual) != (self.nchans, self.N):
            logger.warning(f"Actual data shape {(nchans_actual, N_actual)} is different "
                           f"from guestimated shape {(self.nchans, self.N)}, "
                           "using actual shape.")
            self.nchans, self.N = (nchans_actual, N_actual)

        qstyle_widget(self.ui.but_load, "ok")
        self.ui.but_load.setText("Loaded")
        self.ui.but_load.setEnabled(True)
        self.ui.but_normalize.setEnabled(True)

        self.select_chan_normalize()
        return 0

# ------------------------------------------------------------------------------
    def select_chan_normalize(self):
        """
        - For multi-channel data, select one channel resp. average all channels
          from `self.data_raw`

        - Scale `self.data` to the maximum specified by self.ui.led_normalize and
            assign normalized result to `self.x`
        """
        logger.info("select_chan_normalize")
        if not hasattr(self, 'data_raw') or self.data_raw is None:
            logger.warning("No data loaded yet.")
            return
        logger.warning(f"idx = {self.ui.cmb_chan.currentIndex()}")
        logger.warning(f"self.data_raw: {np.shape(self.data_raw)}")
        logger.warning(f"self.data_raw: {pprint_log(self.data_raw)}")

        if self.nchans == 1:
            data = self.data_raw
        elif self.ui.cmb_chan.currentIndex() == self.nchans:  # last item (sum) selected
            data = self.data_raw.sum(0)  # sum all slices along dim 0
        else:
            data = self.data_raw[self.ui.cmb_chan.currentIndex()]

        if self.ui.but_normalize.isChecked() == True:
            self.norm = safe_eval(self.ui.led_normalize.text(), self.norm, return_type="float")
            # logger.info(f"norm: {type(self.norm)}, data: {type(self.data)} / {self.data.dtype}")
            self.ui.led_normalize.setText(str(self.norm))
            self.x = data * self.norm / np.max(np.abs(data))
        else:
            self.x = data
        logger.warning(f"self.x: {np.shape(self.x)}")
        logger.warning(f"self.x: {pprint_log(self.x)}")

        self.emit({'data_changed': 'file_io'})
        return