# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with classes and functions for file and text IO
"""
# TODO: import data from files doesn't update FIR / IIR and data changed

from .pyfda_qt_lib import (qget_cmb_box, qset_cmb_box, qcmb_box_populate,
                           qwindow_stay_on_top)
from pyfda.pyfda_rc import params
from .compat import (QLabel, QComboBox, QDialog, QPushButton, QRadioButton,
                     QCheckBox, QVBoxLayout, QGridLayout, pyqtSignal)

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
class CSV_option_box(QDialog):
    """
    Create a pop-up widget for setting CSV options. This is needed when storing /
    reading Comma-Separated Value (CSV) files containing coefficients or poles
    and zeros.
    """
    sig_tx = pyqtSignal(object)  # outgoing  # was: (dict)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent, has_cmsis=True):
        super(CSV_option_box, self).__init__(parent)

        self.has_cmsis = has_cmsis
        self.cmb_delimiter_default = "auto"
        self.cmb_terminator_default = "auto"
        self.cmb_orientation_default = "auto"
        self.cmb_header_default = "auto"

        self._construct_UI()
        qwindow_stay_on_top(self, True)

# ------------------------------------------------------------------------------
    def closeEvent(self, event):
        """
        Override closeEvent (user has tried to close the window) and send a
        signal to parent where window closing is registered before actually
        closing the window.
        """
        self.emit({'closeEvent': ''})
        event.accept()

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """ initialize the User Interface """
        self.setWindowTitle("CSV Options")

        lbl_delimiter = QLabel("CSV delimiter", self)
        cmb_delimiter_items = ["<span>Select delimiter between data fields for im- and export."
                       "</span>",
            ("auto", "Auto / ','", "<span>Detect the delimiter automatically for import, "
             "use ',' for exporting data.</span>"),
            (',', '< , >', "<span>Use ',' as delimiter between data fields.</span>"),
            (';', '< ; >', "<span>Use ';' as delimiter between data fields.</span>"),
            ( '\t', '<TAB>', "<span>Use &lt;TAB&gt; as delimiter between data fields."
             "</span>"),
            ( ' ', '<SPACE>', "<span>Use &lt;SPACE&gt; as delimiter between data "
             "fields.</span>"),
            ( '|', '< | >',"<span>Use '|' as delimiter between data fields.</span>")
            ]
        self.cmb_delimiter = QComboBox(self)
        qcmb_box_populate(self.cmb_delimiter, cmb_delimiter_items,
                          self.cmb_delimiter_default)


        lbl_terminator = QLabel("Line terminator", self)
        cmb_terminator_items = [
            "<span>Terminator at the end of a data row, depending on the operating "
            "system. 'None' can be used for a single row of data with added line breaks.</span>",
            ('auto', 'Auto',
             "<span>Use operating system's default line terminator.</span>"),
            ('\r\n', 'CRLF (Win)', 'Use &lt;CRLF&gt; as line terminator (Windows '
             'convention)</span>'),
            ('\r', 'CR (Mac)', 'Use &lt;CR&gt; as line terminator (MacOS '
             'convention)</span>'),
            ('\n', 'LF (Unix)', 'Use &lt;LF&gt; as line terminator (Unix '
             'convention)</span>'),
            ('\a', 'None', '<span>No line terminator, use for single row data</span>')
            ]
        self.cmb_terminator = QComboBox(self)
        qcmb_box_populate(self.cmb_terminator, cmb_terminator_items,
                          self.cmb_terminator_default)

        butClose = QPushButton(self)
        butClose.setText("Close")

        lbl_orientation = QLabel("Table mode", self)
        cmb_orientation_items = [
            "<span>Select row / column mode of table.</span>",
            ('auto', 'Auto/Cols.', "<span>Detect table orientation automatically "
             "during import; use column format for exporting data.</span>"),
            ('cols', 'Columns', "<span>Import / export data in columns.</span>"),
            ('rows', 'Rows', "<span>Import / export data in rows.</span>")
            ]
        self.cmb_orientation = QComboBox(self)
        qcmb_box_populate(self.cmb_orientation, cmb_orientation_items,
                          self.cmb_orientation_default)

        lbl_header = QLabel("Use header", self)
        cmb_header_items = [
            "<span>Interpret first row resp. column as header.</span>",
            ('auto', 'Auto/Off', "<span>Detect header automatically during import; "
             "turn off header during export.</span>"),
            ('on', 'On', "<span>Turn on header.</span>"),
            ('off', 'Off', "<span>Turn off.</span>")
            ]
        self.cmb_header = QComboBox(self)
        qcmb_box_populate(self.cmb_header, cmb_header_items,
                          self.cmb_header_default)

        lbl_cmsis = QLabel("CMSIS SOS format", self)
        lbl_cmsis.setVisible(self.has_cmsis)
        self.chk_cmsis = QCheckBox()
        self.chk_cmsis.setChecked(False)
        self.chk_cmsis.setToolTip(
            "<span>Use CMSIS DSP second-order sections format "
            "(only for IIR coefficients).</span>")
        self.chk_cmsis.setVisible(self.has_cmsis)

        self.radClipboard = QRadioButton("Clipboard", self)
        self.radClipboard.setChecked(False)
        self.radFile = QRadioButton("File", self)
        # setting is read later on from params['CSV']['clipboard']
        self.radFile.setChecked(True)

        lay_grid = QGridLayout()
        lay_grid.addWidget(lbl_delimiter, 1, 1)
        lay_grid.addWidget(self.cmb_delimiter, 1, 2)
        lay_grid.addWidget(lbl_terminator, 2, 1)
        lay_grid.addWidget(self.cmb_terminator, 2, 2)
        lay_grid.addWidget(lbl_orientation, 3, 1)
        lay_grid.addWidget(self.cmb_orientation, 3, 2)
        lay_grid.addWidget(lbl_header, 4, 1)
        lay_grid.addWidget(self.cmb_header, 4, 2)
        lay_grid.addWidget(lbl_cmsis, 5, 1)
        lay_grid.addWidget(self.chk_cmsis, 5, 2)
        lay_grid.addWidget(self.radClipboard, 6, 1)
        lay_grid.addWidget(self.radFile, 6, 2)

        layVMain = QVBoxLayout()
        # layVMain.setAlignment(Qt.AlignTop) # only affects first widget (intended here)
        layVMain.addLayout(lay_grid)
        layVMain.addWidget(butClose)
        layVMain.setContentsMargins(*params['wdg_margins'])
        self.setLayout(layVMain)

        self.load_settings()

        # ============== Signals & Slots ================================
        butClose.clicked.connect(self.close)
        self.cmb_orientation.currentIndexChanged.connect(self.store_settings)
        self.cmb_delimiter.currentIndexChanged.connect(self.store_settings)
        self.cmb_terminator.currentIndexChanged.connect(self.store_settings)
        self.cmb_header.currentIndexChanged.connect(self.store_settings)
        self.chk_cmsis.clicked.connect(self.store_settings)
        self.radClipboard.clicked.connect(self.store_settings)
        self.radFile.clicked.connect(self.store_settings)

    def store_settings(self):
        """
        Store settings of CSV options widget in ``pyfda_rc.params``.
        """

        try:
            params['CSV']['orientation'] = qget_cmb_box(self.cmb_orientation, data=True)
            params['CSV']['delimiter'] = qget_cmb_box(self.cmb_delimiter, data=True)
            params['CSV']['lineterminator'] = qget_cmb_box(self.cmb_terminator,
                                                           data=True)
            params['CSV']['header'] = qget_cmb_box(self.cmb_header, data=True)
            params['CSV']['cmsis'] = self.chk_cmsis.isChecked()
            params['CSV']['clipboard'] = self.radClipboard.isChecked()

            self.emit({'ui_global_changed': 'csv'})

        except KeyError as e:
            logger.error(e)

    def load_settings(self):
        """
        Load settings of CSV options widget from ``pyfda_rc.params``.
        """
        try:
            qset_cmb_box(self.cmb_orientation, params['CSV']['orientation'], data=True)
            qset_cmb_box(self.cmb_delimiter, params['CSV']['delimiter'], data=True)
            qset_cmb_box(self.cmb_terminator, params['CSV']['lineterminator'],
                         data=True)
            qset_cmb_box(self.cmb_header, params['CSV']['header'], data=True)
            self.chk_cmsis.setChecked(params['CSV']['cmsis'])

            self.radClipboard.setChecked(params['CSV']['clipboard'])
            self.radFile.setChecked(not params['CSV']['clipboard'])

        except KeyError as e:
            logger.error(f"Unknown key {e}")


# ==============================================================================
if __name__ == '__main__':
    """
    Run a simple test with python -m pyfda.libs.csv_option_box
    """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = CSV_option_box(parent=None)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
