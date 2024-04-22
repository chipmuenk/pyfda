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
import pyfda.filterbroker as fb
import pyfda.libs.pyfda_dirs as dirs

from pyfda.libs.pyfda_lib import safe_eval, pprint_log, np_shape
from pyfda.libs.pyfda_qt_lib import emit, qstyle_widget, qget_cmb_box, qset_cmb_box
from pyfda.libs.csv_option_box import CSV_option_box

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

    def __init__(self, parent):
        super().__init__()

        # initial settings
        self.file_name = None  # full name of loaded file
        self.file_type = None  # type of loaded file
        self.x_file = None     # data loaded from file

        self.ui = Tran_IO_UI()  # create the UI part with buttons etc.
        self.parent = parent    # handle to instantiating object

        self.norm = self.ui.led_normalize_default
        self.nr_loops = self.ui.led_nr_loops_default
        self.f_s_wav = self.f_s_file = fb.fil[0]['f_S']

        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None) -> None:
        """
        Process signals coming from
        - the navigation toolbars (time and freq.)
        - local widgets (impz_ui) and
        - plot_tab_widgets() (global signals)
        """
        # logger.warning("SIG_RX - vis: {0}\n{1}"
        #                .format(self.isVisible(), pprint_log(dict_sig)))

        if 'id' in dict_sig and dict_sig['id'] == id(self):
            logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
        elif 'close_event' in dict_sig:
            self.close_csv_win()
            self.emit({'ui_local_changed': 'csv'})  # propagate one level up
        elif 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed'] == 'csv':
            # Set CSV options button according to state of CSV popup handle
            self.ui.but_csv_options.setChecked(not dirs.csv_options_handle is None)
        elif 'view_changed' in dict_sig and dict_sig['view_changed'] == 'f_S':
            self.set_f_s_wav(fb.fil[0]['f_S'] * fb.fil[0]['f_s_scale'])

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
        self.ui.but_csv_options.clicked.connect(self.open_csv_win)
        self.ui.led_f_s_wav.editingFinished.connect(self.set_f_s_wav)

        self.ui.but_select.clicked.connect(self.load_data_raw)
        self.ui.cmb_chan_import.currentIndexChanged.connect(self.select_chan_normalize)
        self.ui.but_load.clicked.connect(self.load_button_clicked)
        self.ui.but_normalize.clicked.connect(self.select_chan_normalize)
        self.ui.led_normalize.editingFinished.connect(self.select_chan_normalize)

        self.ui.led_nr_loops.editingFinished.connect(self.save_nr_loops)
        self.ui.but_save.clicked.connect(self.save_data)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # connect rx global events to process_sig_rx() and to listening subwidgets
        self.sig_rx.connect(self.process_sig_rx)

        self.setLayout(layVMain)

        self.set_f_s_wav(fb.fil[0]['f_S'] * fb.fil[0]['f_s_scale'])

    # ------------------------------------------------------------------------------
    def set_f_s_wav(self, f_s_wav=None):
        """
        Set sampling frequency for wav files, either from LineEdit (button `Auto f_s`
        unchecked) or from argument `f_s_wav` (button `Auto f_s` checked), passed either
        from loaded wav file or from updated f_S some other place in the app.

        The sampling frequency needs to integer and at least 1.
        """
        if not self.ui.but_f_s_wav_auto.isChecked() or f_s_wav is None:
            f_s_wav = self.ui.led_f_s_wav.text()

        self.f_s_wav = max(safe_eval(f_s_wav, alt_expr=self.f_s_wav,
                                 return_type='int', sign='pos'), 1)
        self.ui.led_f_s_wav.setText(str(self.f_s_wav))

    # ------------------------------------------------------------------------------
    def unload_data(self):
        """
        Enable load button and set to normal mode, replace label "Loaded" by "Load",
        clear loaded data, disable normalize button and emit 'data_changed' signal
        """
        was_loaded = self.ui.but_load.property("state") == "ok"
        self.ui.but_load.setEnabled(True)
        qstyle_widget(self.ui.but_load, "normal")
        self.ui.but_load.setText("Load:")
        self.ui.but_normalize.setEnabled(False)
        self.ui.led_normalize.setEnabled(False)
        self.x_file = None

        if was_loaded:
            self.emit({'data_changed': 'file_io'})

    # ------------------------------------------------------------------------------
    def load_data_raw(self):
        """
        Select a file in a UI dialog (CSV or WAV) and load it into `self.data_raw`
        Try to find the dimensions and some other infos.

        When loading the file was successful, store the fully qualified file name
        and the file type in the attributes `self.file_name` and `self.file_type`
        and return 0.
        When an error occurred, return -1.

        """
        # TODO: "test_row_ba_IIR_header.csv" fails to read, data should be unloaded

        file_type = (qget_cmb_box(self.ui.cmb_file_format),)  # str -> tuple
        file_name_prev = self.file_name
        file_type_prev = self.file_type

        self.file_name, self.file_type = io.select_file(
            self, title="Select file for data import", mode="r",
            file_types=file_type)

        if self.file_name is None:  # operation cancelled
            self.file_name = file_name_prev
            self.file_type = file_type_prev
            qset_cmb_box(self.ui.cmb_file_format, self.file_type)
            return -1

        self.unload_data()  # reset load and normalize button

        self.N = None
        self.nchans = None
        self.WL = None

        info_str = ""

        if self.file_type == 'wav':
            ret = io.read_wav_info(self.file_name)
            if ret < 0:
                return -1
            self.data_raw = io.load_data_np(self.file_name, 'wav')
            if self.data_raw is None:  # an error occurred
                return -1
            self.N = io.read_wav_info.N
            self.nchans = io.read_wav_info.nchans
            self.f_s_file = io.read_wav_info.f_S
            self.WL = io.read_wav_info.WL
            # info_str = f" x {self.WL * 8} bits,"
            info_str = f" x {io.read_wav_info.sample_format},"
            self.ui.frm_f_s.setVisible(True)
            self.ui.lbl_f_s_value.setText(str(self.f_s_file))

        elif self.file_type == 'csv':
            self.ui.frm_f_s.setVisible(False)
            self.data_raw = io.load_data_np(self.file_name, 'csv')
            if self.data_raw is None:
                logger.error(f"Could not load '{self.file_name}'.")
                qstyle_widget(self.ui.but_load, "error")
                return -1

            # self.N, self.nchans = np_shape(self.data_raw)
            # if self.N in {None, 0}:  # data is scalar, None or multidim
            #     qstyle_widget(self.ui.but_load, "error")
            #     logger.warning("Unsuitable data format")
            #     return -1
            info_str = f" ({io.load_data_np.info_str})"
        else:
            logger.error(f"Unknown file format '{self.file_type}'")
            qstyle_widget(self.ui.but_load, "error")
            return -1

        if self.nchans > 2:
            logger.warning(
                f"Unsuitable file format with {self.nchans} > 2 channels.")
            qstyle_widget(self.ui.but_load, "error")
            return -1
        elif self.nchans == 1:
            self.ui.lbl_chan_import.setVisible(False)
            self.ui.cmb_chan_import.setVisible(False)
        else:
            self.ui.lbl_chan_import.setVisible(True)
            self.ui.cmb_chan_import.setVisible(True)

        if len(self.file_name) < 45:
            self.ui.lbl_filename.setText(self.file_name)
        else:
            self.ui.lbl_filename.setText(
                self.file_name[:10] + ' ... ' + self.file_name[-20:])

        self.ui.lbl_filename.setToolTip(self.file_name)
        self.ui.lbl_shape_actual.setText(
            f"{self.nchans} x {self.N}{info_str}")
        return 0

    # ------------------------------------------------------------------------------
    def load_button_clicked(self):
        """
        When load button was clicked, determine its state. When it was "ok" (loaded),
        unload data and reset button.

        Continue with select_chan_normalize() otherwise.
        """
        # ------------------------------------------------------------------------------
        if self.ui.but_load.property("state") == "ok":
            self.unload_data()
        else:
            self.select_chan_normalize()

    # ------------------------------------------------------------------------------
    def select_chan_normalize(self):
        """
        `select_chan_normalize()` is triggered by `load_data_np()` and by signal-slot
        connections
            * self.ui.cmb_chan_import.currentIndexChanged
            * self.ui.but_normalize.clicked
            * self.ui.led_normalize.editingFinished

        It processes `self.data_raw` and yields `self.x_file` as a result which
        is assigned as `self.stim_wdg.x_file = self.file_io_wdg.x_file` in the class
        `Plot_Impz()` when the signal `{'data_changed': 'file_io'}` is received.

        - For two channel `self.data_raw`, assign one channel or the sum of both channels
          to `data`. Alternatively, assign one channel of `self.data_raw` as real and the
          other as imaginary component of `data`.

        - Scale `data` to the maximum specified by `self.ui.led_normalize` and
            assign normalized result to `self.x_file`.
        """
        if not hasattr(self, 'data_raw') or self.data_raw is None:
            logger.warning("No data loaded yet.")
            return None

        logger.info(pprint_log(self.data_raw))

        if self.data_raw.ndim == 1:
            data = self.data_raw
        else:
            item = qget_cmb_box(self.ui.cmb_chan_import)

            if item == "1":  # use channel 1 (mono)
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
                self.unload_data()
                return None

        qstyle_widget(self.ui.but_load, "ok")
        self.ui.but_load.setText("Loaded")
        self.ui.but_load.setEnabled(True)
        self.ui.but_normalize.setEnabled(True)
        self.ui.led_normalize.setEnabled(True)

        if self.file_type == 'wav':
            self.set_f_s_wav(self.f_s_file)  # copy f_s read from wav file info to line edit
            scale_int = 1
            offset_int = 0

            if self.ui.but_scale_int.isChecked() == True:
                if io.read_wav_info.sample_format == "int16":
                    scale_int = (1 << 15) - 1
                elif io.read_wav_info.sample_format == "int24":
                    scale_int = (1 << 23) - 1
                elif io.read_wav_info.sample_format == "int32":
                    scale_int = (1 << 31) - 1
                elif io.read_wav_info.sample_format == "uint8":
                    scale_int = (1 << 7) - 1
                    offset_int = 128

            data = (data - offset_int) / scale_int

        if self.ui.but_normalize.isChecked() == True:
            self.norm = safe_eval(self.ui.led_normalize.text(), self.norm, return_type="float")
            self.ui.led_normalize.setText(str(self.norm))
            self.x_file = data * self.norm / np.max(np.abs(data))
        else:
            self.x_file = data

        self.emit({'data_changed': 'file_io'})
        if self.ui.but_f_s_wav_auto.isChecked():
            fb.fil[0]['f_S'] = self.f_s_file
            fb.fil[0]['freq_specs_unit'] = 'Hz'
            self.emit({'view_changed': 'f_S'})
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

    # ------------------------------------------------------------------------------
    def save_nr_loops(self):
        self.nr_loops = safe_eval(
            self.ui.led_nr_loops.text(), alt_expr=self.nr_loops,
            return_type='int', sign='pos')
        self.ui.led_nr_loops.setText(str(self.nr_loops))

    # ------------------------------------------------------------------------------
    def save_data(self) -> None:
        """
        Save a file with UI dialog (CSV or WAV), using the data for left and right
        channel, selected in the UI.

        WAV files can be exported in various int formats, the sampling frequency is
        read from the line edit field.

        TODO: uint8 export doesn't work
        """
        file_type = (qget_cmb_box(self.ui.cmb_file_format),)  # str -> tuple

        self.file_name, self.file_type = io.select_file(
            self, title="Select file for data export", mode="wb",
            file_types=file_type)

        if self.file_name is None:  # operation cancelled
            return -1
        # select which data is saved (stimulus, response, quantized stimulus)
        sel_r = qget_cmb_box(self.ui.cmb_chan_export_r)
        sel_l = qget_cmb_box(self.ui.cmb_chan_export_l)

        data = None
        if not sel_l and not sel_r:
            logger.warning("No signal selected for saving.")
            return

        if sel_l:
            if not '.' in sel_l:
                data = getattr(self.parent, sel_l)
            elif 'im' in sel_l:
                data = getattr(self.parent, sel_l.split('.')[0]).imag
            else:
                data = getattr(self.parent, sel_l.split('.')[0]).real
        if sel_r:
            if not '.' in sel_r:
                data_r = getattr(self.parent, sel_r)
            elif 'im' in sel_r:
                data_r = getattr(self.parent, sel_r.split('.')[0]).imag
            else:
                data_r = getattr(self.parent, sel_r.split('.')[0]).real

            if data is None:
                data = data_r
            else:
                # create 2D-array from 1D arrays and transpose them to row based form
                data = np.vstack((data, data_r))

        if self.file_type == 'wav':
            # convert to selected data format
            frmt = qget_cmb_box(self.ui.cmb_data_format)
            scale_int = self.ui.but_scale_int.isChecked()
            if frmt not in {'uint8', 'int16', 'int32', 'float32', 'float64'}:
                logger.error(f"Unsupported format {frmt} for data export.")
                return -1
            elif data.dtype not in {np.dtype('float32'), np.dtype('float64')}:
                logger.warning(f"Data has format '{data.dtype}', instead of 'float', "
                            "scaling may yield incorrect results.")
            if frmt == 'int16':
                if scale_int:
                    data = (data * ((1 << 15) - 1)).astype(np.int16)
                else:
                    data = data.astype(np.int16)
            elif frmt == 'int32':
                if scale_int:
                    data = (data * ((1 << 31) - 1)).astype(np.int32)
                else:
                    data = data.astype(np.int32)
            elif frmt == 'uint8':
                if scale_int:
                    data = (data * 127 + 128).astype(np.uint8)
                else:
                    data = data.astype(np.uint8)
            elif frmt == 'float32':
                data = data.astype(np.float32)
            else:
                data = data.astype(np.float64)

        # repeat selected signal(s) for specified number of cycles
        cycles = int(self.ui.led_nr_loops.text())
        data = np.tile(data, cycles).T

        try:
            io.save_data_np(self.file_name, self.file_type, data, self.f_s_wav)
        except IOError as e:
            logger.warning(f"File could not be saved:\n{e}")
