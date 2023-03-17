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
from pyfda.libs.compat import Qt, QWidget, pyqtSignal, QVBoxLayout
import numpy as np

import pyfda.libs.pyfda_io_lib as io

from pyfda.libs.pyfda_lib import safe_eval, pprint_log
from pyfda.libs.pyfda_qt_lib import emit, qstyle_widget, qget_cmb_box
from pyfda.libs.csv_option_box import CSV_option_box
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

        if 'id' in dict_sig and dict_sig['id'] == id(self):
            logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
        elif 'closeEvent' in dict_sig:
            self.close_csv_win()
            self.emit({'ui_local_changed': 'csv'})  # propagate one level up
        elif 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed'] == 'csv':
            # Set CSV options button according to state of CSV popup handle
            self.ui.but_csv_options.setChecked(not dirs.csv_options_handle is None)

    # ------------------------------------------------------------------------------
    def _construct_UI(self) -> None:
        """
        Instantiate the UI of the widget
        """
        self.main_wdg = QWidget()
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.ui.wdg_top)
        layVMain.setContentsMargins(*params['mpl_margins'])

        # ---------------------------------------------------------------------
        # UI SIGNALS & SLOTs
        # ---------------------------------------------------------------------
        self.ui.but_select.clicked.connect(self.select_file)
        self.ui.cmb_chan.currentIndexChanged.connect(self.select_chan_normalize)
        self.ui.but_load.clicked.connect(self.import_data)
        self.ui.but_normalize.clicked.connect(self.select_chan_normalize)
        self.ui.led_normalize.editingFinished.connect(self.select_chan_normalize)

        self.ui.but_csv_options.clicked.connect(self.open_csv_win)
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

        if self.nchans > 2:
            logger.warning(
                f"Unsuitable file format with {io.read_csv_info} > 2 channels.")
            return -1
        elif self.nchans == 1:
            self.ui.lbl_chan.setVisible(False)
            self.ui.cmb_chan.setVisible(False)
            self.ui.line_chan.setVisible(False)
        else:
            self.ui.lbl_chan.setVisible(True)
            self.ui.cmb_chan.setVisible(True)
            self.ui.line_chan.setVisible(True)

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
            self.ui.but_load.setEnabled(False)
            return -1

        self.data_raw = io.import_data(self.file_name, self.file_type)
        logger.warning(f"data_raw: {np.shape(self.data_raw)}")

        if self.data_raw is None:  # file operation cancelled
            err = True
        elif type(self.data_raw) != np.ndarray:
            logger.warning("Unsuitable file / data format")
            err = True

        if err:
            self.ui.but_load.setEnabled(False)
            return -1

        if self.data_raw.ndim == 1:
            nchans_actual = 1
            N_actual = len(self.data_raw)
            logger.warning(f"imported data: ndim = 1, len = {len(self.data_raw)}")
        elif self.data_raw.ndim == 2:
            N_actual, nchans_actual = np.shape(self.data_raw)
            logger.warning(f"imported data: ndim = 2, rows (N) x colums (chans) = {np.shape(self.data_raw)}")
        else:
            logger.warning("Unsuitable data shape with "
                           f"{self.data_raw.ndim} dimensions.")
            return -1

        # if (nchans_actual, N_actual) != (self.nchans, self.N):
        #     logger.warning(f"Actual data shape {(nchans_actual, N_actual)} is different "
        #                    f"from guestimated shape {(self.nchans, self.N)}, "
        #                    "using actual shape.")
        #     self.nchans, self.N = (nchans_actual, N_actual)

        self.select_chan_normalize()
        return 0

    # ------------------------------------------------------------------------------
    def select_chan_normalize(self):
        """
        - For two channel data, select one channel, average the channels or
          from `self.data_raw`

        - Scale `self.data` to the maximum specified by self.ui.led_normalize and
            assign normalized result to `self.x`
        """
        logger.info("select_chan_normalize")
        if not hasattr(self, 'data_raw') or self.data_raw is None:
            logger.warning("No data loaded yet.")
            return
        logger.warning(f"self.data_raw: rows x columns = {np.shape(self.data_raw)}")
        logger.warning(f"self.data_raw: {pprint_log(self.data_raw)}")

        if self.nchans == 1:
            data = self.data_raw
        else:
            item = qget_cmb_box(self.ui.cmb_chan)

            if item == "del":  # delete data
                self.x = self.data_raw = None
                self.emit({'data_changed': 'file_io'})
                qstyle_widget(self.ui.but_load, "normal")
                self.ui.but_load.setText("Load")
                return
            elif item == "1":  # use channel 1 (mono)
                data = self.data_raw[:, 0]
            elif item == "2":  # use channel 2 (mono)
                data = self.data_raw[:, 1]
            elif item == "12":  # use channel 1 and 2 as stereo signal
                data = np.array(
                    self.data_raw[:, 0] + 1j * self.data_raw[:, 1], dtype=complex)
            elif item == "sum":  # sum channel 1 and 2 as mono signal
                data = self.data_raw.sum(1)  # sum all channels along dim 1 (columns)
            else:
                logger.error(f'Unknown item "{item}"')
                return

        if self.ui.but_normalize.isChecked() == True:
            self.norm = safe_eval(self.ui.led_normalize.text(), self.norm, return_type="float")
            # logger.info(f"norm: {type(self.norm)}, data: {type(self.data)} / {self.data.dtype}")
            self.ui.led_normalize.setText(str(self.norm))
            # use data.ravel() to enforce ndim == 1 instead of (N, 1) which is ndim == 2
            # ravel() creates only a view on the array, not a new array.
            self.x = data.ravel() * self.norm / np.max(np.abs(data))
        else:
            self.x = data.ravel()

        qstyle_widget(self.ui.but_load, "ok")
        self.ui.but_load.setText("Loaded")
        self.ui.but_load.setEnabled(True)
        self.ui.but_normalize.setEnabled(True)

        logger.warning(f"normalized data: rows x columns = {np.shape(self.x)}, {self.x.dtype}")

        self.emit({'data_changed': 'file_io'})
        return

    # ------------------------------------------------------------------------------
    def open_csv_win(self):
        """
        Pop-up window for CSV options, triggered by clicking the options button
        """
        if dirs.csv_options_handle is None:
            # no handle to the window? Create a new instance!
            if self.ui.but_csv_options.isChecked():
                # Important: Handle to window must be class attribute otherwise it (and
                # the attached window) is deleted immediately when it goes out of scope
                dirs.csv_options_handle = CSV_option_box(self)
                dirs.csv_options_handle.sig_tx.connect(self.process_sig_rx)
                dirs.csv_options_handle.show()  # modeless i.e. non-blocking popup window
        else:  # close window, delete handle
            dirs.csv_options_handle.close()
            self.ui.but_csv_options.setChecked(False)

        # alert other widgets that csv options / visibility have changed
        self.emit({'ui_global_changed': 'csv'})

    # ------------------------------------------------------------------------------
    def close_csv_win(self):
        dirs.csv_options_handle = None
        self.ui.but_csv_options.setChecked(False)
