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
    QWidget, QComboBox, QLineEdit, QLabel, QPushButton, QPushButtonRT, QLineEdit, QFrame,
    QHBoxLayout, QVBoxLayout, QGridLayout, QIcon)

from pyfda.libs.pyfda_lib import to_html
from pyfda.libs.pyfda_qt_lib import (
    QVLine, PushButton, qget_cmb_box, qcmb_box_populate, qcmb_box_add_items,
    qcmb_box_del_item, qtext_width)
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

import logging
logger = logging.getLogger(__name__)


class Tran_IO_UI(QWidget):
    """
    Create the UI for the Tran_IO class
    """
    def __init__(self, parent=None):

        # combobox tooltip + data / text / tooltip for channel import
        self.cmb_chan_import_items = [
            "<span>Select channel(s) / column(s) for data import. '&Sigma;' "
            "sums up the columns.</span>",
            ("1", "1", "Use data from channel 1 (left, mono)"),
            ("2", "2", "Use data from channel 2 (right, mono)"),
            ("12", "1|2", "Use data from both channels (stereo)"),
            ("sum", "Σ", "Sum data from both channels (mono)")
        ]
        self.cmb_chan_import_init = "1"

        self.led_normalize_default = 1  # default setting for normalization

        self.cmb_file_format_items = [
            "<span>Select file format for data import and export.</span>",
            ("csv", "csv", "Comma / tab separated values text format"),
            ("wav", "wav", "Wave audio file format")
        ]
        self.cmb_file_format_init = "csv"

        self.cmb_data_format_items = [
            "<span>Data format for export</span>",
            ("uint8", "UInt8", "8 Bit Unsigned Integer (0 ... 255)"),
            ("int16", "Int16", "16 Bit signed integer (CD-quality), standard WAV-format"),
            ("int32", "Int32", "32 Bit signed integer for High-Res audio"),
            ("float32", "Float32", "Floating point single precision"),
            ("float64", "Float64", "Floating point double precision")
        ]
        self.cmb_data_format_init = "int16"

        # combobox tooltip + data / text / item tooltip for channel export (real data)
        # The data field needs to contain the exact name of the corresponding variable (`x`, `y`)
        self.cmb_chan_export_real_items = [
            "<span>Select signals for exporting data (one or two channels resp. L / R "
            "channel for WAV format).</span>",
            ("", "none", "no data"),
            ("x", "x", "Stimuli"),
            ("y", "y", "Response")
        ]

        # Additional data / text / item tooltip for channel export (real_fx data)
        # The data field needs to contain the exact name of the corresponding variable (`x_Q`)
        self.cmb_chan_export_real_fx_items = [
            ("x_q", "x_Q", "Quantized stimuli")
        ]

        # Additional data / text / item tooltip for channel export (complex_fx data)
        # The data field needs to contain the exact name of the corresponding variable (`x_Q`),
        # followed by `.re` resp. `.im` for real resp. imaginary component
        self.cmb_chan_export_complex_fx_items = [
            ("x_q.re", "x_re_Q", "Quantized stimuli (real part)"),
            ("x_q.im", "x_im_Q", "Quantized stimuli (imag. part)")
        ]

        # combobox tooltip + data / text / item tooltip for channel export (complex data)
        # The data field needs to contain the exact name of the corresponding variable (`x`, `y`),
        # followed by `.re` resp. `.im` for real resp. imaginary component
        self.cmb_chan_export_complex_items = [
            "<span>Select signals for data export. '&Sigma;' "
            "sums up all columns.</span>",
            ("", "none", "no data"),
            ("x.re", "x_re", "Stimuli (real part)"),
            ("x.im", "x_im", "Stimuli (imag. part)"),
            ("y.re", "y_re", "Response (real part)"),
            ("y.im", "y_im", "Response (imag. part)")
        ]
        self.cmb_chan_export_cur_item_l = "x"
        self.cmb_chan_export_cur_item_r = "y"

        self.led_nr_loops_default = 1

        super(Tran_IO_UI, self).__init__(parent)
        self._construct_UI()

    # -------------------------------------------------------------------------
    def _construct_UI(self):
        # =====================================================================
        # Controls
        # =====================================================================
        self.lbl_title_io_file = QLabel("File:", objectName="large")
        # ----------------------------------------------------------------------
        # Main Widget
        # ----------------------------------------------------------------------

        # ----------- LOAD ------------------------------------------------------------
        self.but_select = PushButton("Select", checkable=False, objectName="large")
        self.but_select.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)
        self.but_select.setToolTip(
            self.tr("<span>Select file, get its shape and size but don't load "
                    "it yet.</span>"))

        self.but_load = QPushButton("Load:", objectName="large")
        self.but_load.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)
        self.but_load.setToolTip(
            self.tr("<span>Load / unload selected file.</span>"))
        self.but_load.setEnabled(False)

        self.lbl_file = QLabel(to_html("Name:", frmt="b"))
        self.lbl_filename = QLabel("None")

        self.lbl_shape = QLabel(to_html("Shape:", frmt="b"))
        self.lbl_shape_actual = QLabel("None")

        lbl_f_s = QLabel(to_html("f_S =", frmt="bi"))
        self.lbl_f_s_value = QLabel("None")
        lbl_f_s_unit = QLabel("Hz")
        layH_f_s = QHBoxLayout()
        layH_f_s.addWidget(lbl_f_s)
        layH_f_s.addWidget(self.lbl_f_s_value)
        layH_f_s.addWidget(lbl_f_s_unit)
        layH_f_s.addStretch()
        layH_f_s.setContentsMargins(0, 0, 0, 0)
        self.frm_f_s = QFrame(self)
        self.frm_f_s.setLayout(layH_f_s)
        self.frm_f_s.setContentsMargins(0, 0, 0, 0)
        self.frm_f_s.setVisible(False)

        self.line0 = QVLine(width=1)
        self.line0.setVisible(False)
        self.lbl_chan_import = QLabel(to_html("Column", frmt="b"))
        self.lbl_chan_import.setVisible(False)
        self.cmb_chan_import = QComboBox(self)
        qcmb_box_populate(
            self.cmb_chan_import, self.cmb_chan_import_items,
            self.cmb_chan_import_init)
        self.cmb_chan_import.setVisible(False)

        line1 = QVLine(width=10)

        self.lbl_wordlength = QLabel(to_html("W =", frmt="bi"))
        self.lbl_wordlength_value = QLabel("None")

        self.but_scale_to = PushButton("Scale to")
        self.but_scale_to.setToolTip(
            self.tr("<span>When activated, scale maximum of data to the value below "
                    "before saving and after loading.</span>"))
        self.but_scale_to.setEnabled(True)
        self.but_scale_to.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)

        # ----------- FILE FORMAT -------------------------------------------
        self.cmb_file_format = QComboBox()
        qcmb_box_populate(self.cmb_file_format, self.cmb_file_format_items,
                          self.cmb_file_format_init)
        self.but_csv_options = PushButton(self, icon=QIcon(':/csv_options.svg'),
                                          checked=False)
        self.but_csv_options.setToolTip(
            "<span>Select CSV format and whether "
            "to copy to/from clipboard or file.</span>")

        self.but_scale_int = PushButton("Scale Int ", checked=True)
        self.but_scale_int.setToolTip(
            "<span>Autoscale integer data when importing and exporting so that "
            "1.0 represents the max. positive value.</span>")
        layH_file_fmt_options = QHBoxLayout()
        layH_file_fmt_options.addWidget(self.but_csv_options)
        layH_file_fmt_options.addWidget(self.but_scale_int)

        self.but_f_s_wav_auto = QPushButtonRT(self, "<b>Auto <i>f<sub>S</sub></i></b>", margin=5)
        self.but_f_s_wav_auto.setCheckable(True)
        self.but_f_s_wav_auto.setChecked(True)
        self.but_f_s_wav_auto.setToolTip(
            "<span>Copy pyfda sampling frequency to WAV file during export "
            "when selected.</span>")
        self.lbl_f_s_wav = QLabel(to_html("f_S =", frmt='bi'))
        self.led_f_s_wav = QLineEdit(self)
        self.led_f_s_wav.setMaximumWidth(qtext_width(N_x=8))
        self.led_f_s_wav.setToolTip(
            "<span>Manual f_S for import / export of WAV file (must be integer).</span>")

        layH_lbl_led_f_s_wav = QHBoxLayout()
        layH_lbl_led_f_s_wav.addWidget(self.lbl_f_s_wav)
        layH_lbl_led_f_s_wav.addWidget(self.led_f_s_wav)

        line2 = QVLine(width=1)
        # ----------- SCALE ------------------------------------------------------------
        self.led_scale_to = QLineEdit()
        self.led_scale_to.setToolTip(self.tr("Max. value after normalizing"))
        self.led_scale_to.setText(str(self.led_normalize_default))
        self.led_scale_to.setEnabled(True)
        self.led_scale_to.setMaximumWidth(qtext_width(N_x=8))
        # self.led_scale_to.setFixedWidth(self.but_scale_to.sizeHint().width())

        # ----------- SAVE ------------------------------------------------------------
        line3 = QVLine(width=5)
        self.but_save = QPushButton("Save:", objectName="large")
        self.but_save.setSizePolicy(QSizePolicy.Expanding,
                                      QSizePolicy.Expanding)
        self.but_save.setToolTip(
            self.tr("<span>Save selected signals to R/L file channels.</span>"))
        self.lbl_chan_export_l = QLabel(to_html("L:", frmt="b"))
        self.cmb_chan_export_l = QComboBox(self)
        self.lbl_chan_export_r = QLabel(to_html("R:", frmt="b"))
        self.cmb_chan_export_r = QComboBox(self)
        qcmb_box_populate(self.cmb_chan_export_l,
                            self.cmb_chan_export_real_items,
                            self.cmb_chan_export_cur_item_l)
        qcmb_box_populate(self.cmb_chan_export_r,
                            self.cmb_chan_export_real_items,
                            self.cmb_chan_export_cur_item_r)

        self.lbl_data_format = QLabel((to_html("Format", frmt="b")))
        self.cmb_data_format = QComboBox()
        qcmb_box_populate(self.cmb_data_format, self.cmb_data_format_items,
                          self.cmb_data_format_init)

        self.lbl_nr_loops = QLabel(to_html("Loops", frmt='b'))

        self.led_nr_loops = QLineEdit()
        self.led_nr_loops.setToolTip(self.tr(
            "<span>Select how many times the signal is looped when saving.</span>"))
        self.led_nr_loops.setText(str(self.led_nr_loops_default))
        self.led_nr_loops.setMaximumWidth(qtext_width(N_x=8))

        #-------------------------------
        layG_io_file = QGridLayout()
        i = 0
        # ---- LOAD FILE
        layG_io_file.addWidget(self.but_select, 0, i)
        layG_io_file.addWidget(self.but_load, 1, i)
        i += 1
        layG_io_file.addWidget(self.lbl_file, 0, i)
        layG_io_file.addWidget(self.lbl_shape, 1, i)
        i += 1
        layG_io_file.addWidget(self.lbl_filename, 0, i, 1, 2)
        layG_io_file.addWidget(self.lbl_shape_actual, 1, i)
        i += 1
        # row 0 is used by the file name
        layG_io_file.addWidget(self.frm_f_s, 1, i)
        i += 1
        layG_io_file.addWidget(self.line0, 0, i, 2, 1)
        i+=1
        layG_io_file.addWidget(self.lbl_chan_import, 0, i)
        layG_io_file.addWidget(self.cmb_chan_import, 1, i)
        i += 1
        layG_io_file.addWidget(line1, 0, i, 2, 1)
        # ---- FILE FORMAT
        i += 1
        layG_io_file.addWidget(self.cmb_file_format, 0, i)
        # layG_io_file.addWidget(self.but_csv_options, 1, i)
        layG_io_file.addLayout(layH_file_fmt_options, 1, i)
        i += 1
        layG_io_file.addWidget(self.but_f_s_wav_auto, 0, i)
        layG_io_file.addLayout(layH_lbl_led_f_s_wav, 1, i)
        # ---- SCALE TO
        i += 1
        layG_io_file.addWidget(line2, 0, i, 2, 1)
        i += 1
        layG_io_file.addWidget(self.but_scale_to, 0, i)
        layG_io_file.addWidget(self.led_scale_to, 1, i)
        # ---- SAVE FILE
        i += 1
        layG_io_file.addWidget(line3, 0, i, 2, 1)
        i += 1
        layG_io_file.addWidget(self.but_save, 0, i, 2, 1)
        i += 1
        layG_io_file.addWidget(self.lbl_chan_export_l, 0, i)
        layG_io_file.addWidget(self.lbl_chan_export_r, 1, i)
        i += 1
        layG_io_file.addWidget(self.cmb_chan_export_l, 0, i)
        layG_io_file.addWidget(self.cmb_chan_export_r, 1, i)
        i += 1
        layG_io_file.addWidget(self.lbl_data_format, 0, i)
        layG_io_file.addWidget(self.cmb_data_format, 1, i)
        i+= 1
        layG_io_file.addWidget(self.lbl_nr_loops, 0, i)
        layG_io_file.addWidget(self.led_nr_loops, 1, i)
        #
        layG_io_file.setColumnStretch(i+1, 1)
        # --------

        layH_title_io_file = QHBoxLayout()
        layH_title_io_file.addWidget(self.lbl_title_io_file)
        self.wdg_title_io_file = QWidget(self)
        self.wdg_title_io_file.setLayout(layH_title_io_file)
        self.wdg_title_io_file.setContentsMargins(0, 0, 0, 0)

        self.wdg_ctrl_io_file = QWidget(self)
        self.wdg_ctrl_io_file.setLayout(layG_io_file)
        self.wdg_ctrl_io_file.setContentsMargins(0, 0, 0, 0)

        layH_io = QHBoxLayout()
        layH_io.addWidget(self.wdg_title_io_file)
        layH_io.addWidget(self.wdg_ctrl_io_file)
        layH_io.setContentsMargins(0, 0, 0, 0)

        self.wdg_top = QWidget(self, objectName="transparent")
        self.wdg_top.setLayout(layH_io)
        self.wdg_top.setContentsMargins(0, 0, 0, 0)
        self.wdg_top.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        # ------ Local signal-slot-connections
        self.cmb_file_format.currentIndexChanged.connect(self.set_ui_visibility)
        self.cmb_data_format.currentIndexChanged.connect(self.set_ui_visibility)
        self.but_f_s_wav_auto.clicked.connect(self.set_ui_visibility)
        # inizialize data format dependent widgets
        self.set_ui_visibility()

    # -------------------------------------------------------------------------
    def set_ui_visibility(self):
        """
        Update visiblity and accessibility of some widgets, depending on the settings of
        other widgets.
        """
        is_csv_format = qget_cmb_box(self.cmb_file_format) == 'csv'
        self.but_csv_options.setVisible(is_csv_format)

        # int_data_format = qget_cmb_box(self.cmb_data_format)\
        #    in {'uint8', 'int16', 'int32'}
        self.but_f_s_wav_auto.setVisible(not is_csv_format)
        self.lbl_f_s_wav.setVisible(not is_csv_format)
        self.led_f_s_wav.setVisible(not is_csv_format)
        self.lbl_data_format.setVisible(not is_csv_format)
        self.cmb_data_format.setVisible(not is_csv_format)
        self.but_scale_int.setVisible(not is_csv_format)

        self.led_f_s_wav.setEnabled(not self.but_f_s_wav_auto.isChecked())

    # -------------------------------------------------------------------------
    def update_ui(self, cmplx=False, fx=False):
        """
        Update the combo boxes for file saving, depending on whether signals are
        complex and fixpoint simulation has been selected.
        """
        self.cmb_chan_export_cur_item_l = qget_cmb_box(self.cmb_chan_export_l)
        self.cmb_chan_export_cur_item_r = qget_cmb_box(self.cmb_chan_export_r)
        if cmplx:
            qcmb_box_populate(self.cmb_chan_export_l,
                            self.cmb_chan_export_complex_items,
                            self.cmb_chan_export_cur_item_l)
            qcmb_box_populate(self.cmb_chan_export_r,
                            self.cmb_chan_export_complex_items,
                            self.cmb_chan_export_cur_item_r)
            if fx:
                qcmb_box_add_items(self.cmb_chan_export_l,
                                   self.cmb_chan_export_complex_fx_items)
                qcmb_box_add_items(self.cmb_chan_export_r,
                                   self.cmb_chan_export_complex_fx_items)
        else:
            qcmb_box_populate(self.cmb_chan_export_l,
                            self.cmb_chan_export_real_items,
                            self.cmb_chan_export_cur_item_l)
            qcmb_box_populate(self.cmb_chan_export_r,
                            self.cmb_chan_export_real_items,
                            self.cmb_chan_export_cur_item_r)
            if fx:
                qcmb_box_add_items(self.cmb_chan_export_l,
                                   self.cmb_chan_export_real_fx_items)
                qcmb_box_add_items(self.cmb_chan_export_r,
                                   self.cmb_chan_export_real_fx_items)
            else:
                qcmb_box_del_item(self.cmb_chan_export_l, "x_Q")
                qcmb_box_del_item(self.cmb_chan_export_r, "x_Q")

# ================================================================================
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
