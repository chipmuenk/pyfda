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
    QWidget, QComboBox, QLineEdit, QLabel, QPushButton, QLineEdit, QFrame,
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
        self.cmb_data_format_init = "float32"

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
        self.lbl_title_io_file = QLabel("File:")
        self.lbl_title_io_file.setObjectName("large")
        # ----------------------------------------------------------------------
        # Main Widget
        # ----------------------------------------------------------------------
        self.but_load = QPushButton("Load:")
        self.but_load.setObjectName("large")
        self.but_load.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)
        self.but_load.setToolTip(
            self.tr("<span>Load / unload selected file.</span>"))
        self.but_load.setEnabled(False)

        self.but_select = PushButton("Select", checkable=False)
        self.but_select.setObjectName("large")
        self.but_select.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)
        self.but_select.setToolTip(
            self.tr("<span>Select file, get its shape and size but don't load"
                   " it yet.</span>"))

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

        self.lbl_chan_import = QLabel(to_html("Column", frmt="b"))
        self.lbl_chan_import.setVisible(False)
        self.cmb_chan_import = QComboBox(self)
        qcmb_box_populate(
            self.cmb_chan_import, self.cmb_chan_import_items,
            self.cmb_chan_import_init)
        self.cmb_chan_import.setVisible(False)

        layV_chan = QVBoxLayout()
        layV_chan.addWidget(self.lbl_chan_import)
        layV_chan.addWidget(self.cmb_chan_import)

        self.lbl_wordlength = QLabel(to_html("W =", frmt="bi"))
        self.lbl_wordlength_value = QLabel("None")

        line1 = QVLine()

        self.but_normalize = PushButton("Norm")
        self.but_normalize.setToolTip(
            self.tr("<span>Normalize data to the value below.</span>"))
        self.but_normalize.setEnabled(False)
        self.but_normalize.setSizePolicy(QSizePolicy.Expanding,
                                    QSizePolicy.Expanding)

        self.led_normalize = QLineEdit()
        self.led_normalize.setToolTip(self.tr("Max. value for normalization"))
        self.led_normalize.setText(str(self.led_normalize_default))
        self.led_normalize.setEnabled(False)
        self.led_normalize.setMaximumWidth(qtext_width(N_x=8))
        # self.led_normalize.setFixedWidth(self.but_normalize.sizeHint().width())

        line2 = QVLine(width=5)

        self.cmb_file_format = QComboBox()
        qcmb_box_populate(self.cmb_file_format, self.cmb_file_format_items,
                          self.cmb_file_format_init)
        self.but_csv_options = PushButton(self, icon=QIcon(':/settings.svg'),
                                          checked=False)
        self.but_csv_options.setToolTip(
            "<span>Select CSV format and whether "
            "to copy to/from clipboard or file.</span>")

        self.but_scale_int = PushButton("Scale Int ", checked=True)
        self.but_scale_int.setToolTip(
            "<span>Autoscale integer data formats with the max. number "
            "when importing and exporting.</span>")
        layH_file_fmt_options = QHBoxLayout()
        layH_file_fmt_options.addWidget(self.but_csv_options)
        layH_file_fmt_options.addWidget(self.but_scale_int)

        self.lbl_data_format = QLabel((to_html("Format", frmt="b")))
        self.cmb_data_format = QComboBox()
        qcmb_box_populate(self.cmb_data_format, self.cmb_data_format_items,
                          self.cmb_data_format_init)

        line3 = QVLine(width=5)

        self.but_save = QPushButton("Save:")
        self.but_save.setObjectName("large")
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

        self.lbl_nr_loops = QLabel(to_html("Loops", frmt='b'))

        self.led_nr_loops = QLineEdit()
        self.led_nr_loops.setToolTip(self.tr(
            "<span>Select how many times the signal is looped when saving.</span>"))
        self.led_nr_loops.setText(str(self.led_nr_loops_default))
        self.led_nr_loops.setMaximumWidth(qtext_width(N_x=8))

        #-------------------------------
        layG_io_file = QGridLayout()
        i = 0
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
        i+=1
        layG_io_file.addWidget(self.lbl_chan_import, 0, i)
        layG_io_file.addWidget(self.cmb_chan_import, 1, i)
        i+=1
        layG_io_file.addWidget(line1, 0, i, 2, 1)
        i += 1
        layG_io_file.addWidget(self.but_normalize, 0, i)
        layG_io_file.addWidget(self.led_normalize, 1, i)
        i += 1
        layG_io_file.addWidget(line2, 0, i, 2, 1)
        i += 1
        layG_io_file.addWidget(self.cmb_file_format, 0, i)
        # layG_io_file.addWidget(self.but_csv_options, 1, i)
        layG_io_file.addLayout(layH_file_fmt_options, 1, i)
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

        self.wdg_top = QWidget(self)
        self.wdg_top.setObjectName("transparent")
        self.wdg_top.setLayout(layH_io)
        self.wdg_top.setContentsMargins(0, 0, 0, 0)
        self.wdg_top.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        # ------ Local signal-slot-connections
        self.cmb_file_format.currentIndexChanged.connect(self.set_ui_visibility)
        self.cmb_data_format.currentIndexChanged.connect(self.set_ui_visibility)
        # inizialize data format dependent widgets
        self.set_ui_visibility()

    # -------------------------------------------------------------------------
    def set_ui_visibility(self):
        is_csv_format = qget_cmb_box(self.cmb_file_format) == 'csv'
        self.but_csv_options.setVisible(is_csv_format)

        int_data_format = qget_cmb_box(self.cmb_data_format)\
            in {'uint8', 'int16', 'int32'}
        self.lbl_data_format.setVisible(not is_csv_format)
        self.cmb_data_format.setVisible(not is_csv_format)
        self.but_scale_int.setVisible(not is_csv_format and int_data_format)

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
