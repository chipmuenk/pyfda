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
from pyfda.libs.pyfda_qt_lib import QVLine, PushButton, qtext_width
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

import logging
logger = logging.getLogger(__name__)


class Tran_IO_UI(QWidget):
    """
    Create the UI for the PlotImpz class
    """
    def __init__(self, parent=None):
        """
        Pass instance `parent` of parent class (FilterCoeffs)
        """
        # combobox tooltip + data / text / tooltip for file I/O usage
        self.cmb_file_io_items = [
            ("<span>Select data from File I/O widget/span>"),
            ("off", "Off", "<span>Don't use file I/O data.</span>"),
            ("use", "Use", "<span><b>Use></b> file I/O data as stimuli.</span>"),
            ("add", "Add", "<span><b>Add</b> file I/O data to other stimuli")
            ]
        self.cmb_file_io_default = "none"

        self.led_normalize_default = 1  # default setting for normalization

        super(Tran_IO_UI, self).__init__(parent)
        self._construct_UI()

    def _construct_UI(self):
        # =====================================================================
        # Controls
        # =====================================================================

        # ----------------------------------------------------------------------
        # Main Widget
        # ----------------------------------------------------------------------
        self.but_csv_options = PushButton(self, icon=QIcon(':/settings.svg'),
                                          checked=False)
        self.but_csv_options.setToolTip(
            "<span>Select CSV format and whether "
            "to copy to/from clipboard or file.</span>")

        self.but_select = PushButton("Select", checkable=False)
        self.but_select.setToolTip(
            self.tr("<span>Select file, get its shape and size but don't load"
                   " it yet.</span>"))
        self.but_load = PushButton("Load", checkable=False)
        self.but_load.setToolTip(
            self.tr("<span>Load file to memory.</span>"))
        self.but_load.setEnabled(False)
        self.but_load.setFixedWidth(qtext_width("Loaded"))

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

        self.line_chan = QVLine()
        self.line_chan.setVisible(False)
        self.lbl_chan = QLabel(to_html("Col.", frmt="b"))
        self.lbl_chan.setVisible(False)
        self.cmb_chan = QComboBox(self)
        self.cmb_chan.setToolTip(
            "<span>Select channel / column for data import. '&Sigma;' "
            "</span> sums up all columns.")
        # populate combobox for correct width (is overwritten later)
        self.cmb_chan.addItems(["1", "2", "Σ", "1|2"])
        self.cmb_chan.setVisible(False)

        layV_chan = QVBoxLayout()
        layV_chan.addWidget(self.lbl_chan)
        layV_chan.addWidget(self.cmb_chan)

        self.lbl_wordlength = QLabel(to_html("W =", frmt="bi"))
        self.lbl_wordlength_value = QLabel("None")

        self.but_normalize = PushButton("Norm")
        self.but_normalize.setToolTip(
            self.tr("<span>Normalize data to the value below.</span>"))
        self.but_normalize.setEnabled(False)
        self.led_normalize = QLineEdit()
        self.led_normalize.setToolTip(self.tr("Max. value for normalization"))
        self.led_normalize.setText(str(self.led_normalize_default))

        line1 = QVLine()
        line2 = QVLine()
        #-------------------------------
        layG_io_file = QGridLayout()
        i = 0
        layG_io_file.addWidget(self.but_csv_options, 0, i)
        i += 1
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
        layG_io_file.addWidget(self.line_chan, 0, i, 2, 1)
        i+=1
        layG_io_file.addWidget(self.lbl_chan, 0, i)
        layG_io_file.addWidget(self.cmb_chan, 1, i)
        i+=1
        layG_io_file.addWidget(line1, 0, i, 2, 1)
        i += 1
        layG_io_file.addWidget(self.but_normalize, 0, i)
        layG_io_file.addWidget(self.led_normalize, 1, i)
        i += 1
        layG_io_file.addWidget(line2, 0, i, 2, 1)

        layV_io = QVBoxLayout()
        layV_io.addLayout(layG_io_file)

        layH_io = QHBoxLayout()
        layH_io.addLayout(layV_io)
        layH_io.addStretch(10)

        self.wdg_top = QWidget(self)
        self.wdg_top.setLayout(layH_io)
        self.wdg_top.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

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
