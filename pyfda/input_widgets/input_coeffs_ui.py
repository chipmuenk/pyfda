# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create the UI for the FilterCoeffs class
"""

from pyfda.libs.compat import (
    pyqtSignal, Qt, QtGui, QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QFrame,
    QSpinBox, QFont, QIcon, QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy)

from pyfda.libs.pyfda_qt_lib import (
    qset_cmb_box, qstyle_widget, qcmb_box_populate, QHLine, PushButton)
from pyfda.libs.csv_option_box import CSV_option_box
# from pyfda.libs.pyfda_lib import pprint_log
import pyfda.libs.pyfda_dirs as dirs
from pyfda.fixpoint_widgets.fx_ui_wq import FX_UI_WQ
from pyfda.pyfda_rc import params
import pyfda.filterbroker as fb

import logging
logger = logging.getLogger(__name__)


class Input_Coeffs_UI(QWidget):
    """
    Create the UI for the FilterCoeffs class
    """
    sig_rx = pyqtSignal(dict)  # incoming
    sig_tx = pyqtSignal(dict)  # outgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None):
        super(Input_Coeffs_UI, self).__init__(parent)
        self.eps = 1.e-6  # initialize tolerance value
        self.cmb_time_spgr_items = [
            "<span>Show Spectrogram for selected signal.</span>",
            ("none", "None", ""),
            ("xn", "x[n]", "input"),
            ("xqn", "x_q[n]", "quantized input"),
            ("yn", "y[n]", "output")
            ]

        self.cmb_q_frmt_items = [
            "<span>Number format for displaying signed fixpoint coefficients.</span>",
            ("qint", "Integer", "<span>Integer format with <i>WI</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 1)</span>"),
            ("qfrac", "Fractional",
             "<span>General fractional format with <i>WI</i> + <i>WF</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 2<sup>WF</sup>).</span>"),
            ("qnfrac", "Norm. Frac.",
             "<span>Normalized fractional format with <i>WF</i> + 1 bits "
             "(range -1 ... +1 - 2<sup>WF</sup>).</span>"),
            ("q31", "Q31", "<span>Normalized fractional format with 32 bits "
             "(31 fractional bits).</span>")
            ]
        self.cmb_q_frmt_default = 'qfrac'
        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the CSV pop-up window
        """
        # logger.debug("PROCESS_SIG_RX:\n{0}".format(pprint_log(dict_sig)))

        if 'closeEvent' in dict_sig:
            self._close_csv_win()
            self.emit({'ui_changed': 'csv'})
            return
        elif 'ui_changed' in dict_sig:
            self._set_load_save_icons()  # update icons file <-> clipboard
            # inform e.g. the p/z input widget about changes in CSV options
            self.emit({'ui_changed': 'csv'})

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        self.bfont = QFont()
        self.bfont.setBold(True)
        self.bifont = QFont()
        self.bifont.setBold(True)
        self.bifont.setItalic(True)
#        q_icon_size = QSize(20, 20) # optional, size is derived from butEnable

        #######################################################################
        # frmMain
        #
        # This frame contains all the buttons
        #######################################################################
        # ---------------------------------------------
        # layHDisplay
        #
        # UI Elements for controlling the display
        # ---------------------------------------------
        self.butEnable = PushButton(self, icon=QIcon(':/circle-check.svg'), checked=True)
        q_icon_size = self.butEnable.iconSize()  # <- uncomment this for manual sizing
        self.butEnable.setToolTip(
            "<span>Show / hide filter coefficients in an editable table."
            " For high order systems, table display might be slow.</span>")

        fix_formats = ['Dec', 'Hex', 'Bin', 'CSD']
        self.cmbFormat = QComboBox(self)
        model = self.cmbFormat.model()
        item = QtGui.QStandardItem('Float')
        item.setData('child', Qt.AccessibleDescriptionRole)
        model.appendRow(item)

        item = QtGui.QStandardItem('Fixp.:')
        item.setData('parent', Qt.AccessibleDescriptionRole)
        item.setData(0, QtGui.QFont.Bold)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)  # | Qt.ItemIsSelectable))
        model.appendRow(item)

        for idx in range(len(fix_formats)):
            item = QtGui.QStandardItem(fix_formats[idx])
#            item.setForeground(QtGui.QColor('red'))
            model.appendRow(item)

        self.cmbFormat.insertSeparator(1)
        qset_cmb_box(self.cmbFormat, 'float')
        self.cmbFormat.setToolTip('Set the display format.')
        self.cmbFormat.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.spnDigits = QSpinBox(self)
        self.spnDigits.setRange(0, 16)
        self.spnDigits.setValue(params['FMT_ba'])
        self.spnDigits.setToolTip("Number of digits to display.")
        self.lblDigits = QLabel("Digits", self)
        self.lblDigits.setFont(self.bifont)

        self.cmb_q_frmt = QComboBox(self)
        qcmb_box_populate(self.cmb_q_frmt, self.cmb_q_frmt_items,
                          self.cmb_q_frmt_default)

        self.butQuant = QPushButton(self)
        self.butQuant.setToolTip(
            "<span>Quantize selected coefficients / "
            "whole table with specified settings.</span>")
        self.butQuant.setIcon(QIcon(':/quantize.svg'))
        self.butQuant.setIconSize(q_icon_size)
        self.butQuant.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layHDisplay = QHBoxLayout()
        layHDisplay.setAlignment(Qt.AlignLeft)
        layHDisplay.addWidget(self.butEnable)
        layHDisplay.addWidget(self.cmbFormat)
        layHDisplay.addWidget(self.spnDigits)
        layHDisplay.addWidget(self.lblDigits)
        layHDisplay.addWidget(self.cmb_q_frmt)
        layHDisplay.addWidget(self.butQuant)
        layHDisplay.addStretch()

        #######################################################################
        # frmButtonsCoeffs
        #
        # This frame contains all buttons for manipulating coefficients
        #######################################################################
        # -----------------------------------------------------------------
        # layHButtonsCoeffs1
        #
        # UI Elements for loading / storing / manipulating cells and rows
        # -----------------------------------------------------------------
        self.cmbFilterType = QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip(
            "<span>Select between IIR and FIR filter for manual entry. "
            "Changing the type reloads the filter from the filter dict.</span>")
        self.cmbFilterType.addItems(["FIR", "IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.butAddCells = QPushButton(self)
        self.butAddCells.setIcon(QIcon(':/row_insert_above.svg'))
        self.butAddCells.setIconSize(q_icon_size)
        self.butAddCells.setToolTip(
            "<span>Select cells to insert a new cell above each selected cell. "
            "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
            "When nothing is selected, add a row at the end.</span>")

        self.butDelCells = QPushButton(self)
        self.butDelCells.setIcon(QIcon(':/row_delete.svg'))
        self.butDelCells.setIconSize(q_icon_size)
        self.butDelCells.setToolTip(
            "<span>Delete selected cell(s) from the table. "
            "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
            "When nothing is selected, delete the last row.</span>")

        self.butSave = QPushButton(self)
        self.butSave.setIcon(QIcon(':/upload.svg'))
        self.butSave.setIconSize(q_icon_size)
        self.butSave.setToolTip(
            "<span>Copy coefficient table to filter dict and update all plots "
            "and widgets.</span>")

        self.butLoad = QPushButton(self)
        self.butLoad.setIcon(QIcon(':/download.svg'))
        self.butLoad.setIconSize(q_icon_size)
        self.butLoad.setToolTip("<span>Reload coefficient table from filter dict.</span>")

        self.butClear = QPushButton(self)
        self.butClear.setIcon(QIcon(':/trash.svg'))
        self.butClear.setIconSize(q_icon_size)
        self.butClear.setToolTip("Clear all table entries.")

        self.butFromTable = QPushButton(self)
        self.butFromTable.setIconSize(q_icon_size)

        self.butToTable = QPushButton(self)
        self.butToTable.setIconSize(q_icon_size)

        self.but_csv_options = PushButton(self, icon=QIcon(':/settings.svg'),
                                          checked=False)
        self.but_csv_options.setIconSize(q_icon_size)
        self.but_csv_options.setToolTip(
            "<span>Select CSV format and whether "
            "to copy to/from clipboard or file.</span>")

        self._set_load_save_icons()  # initialize icon / button settings

        layHButtonsCoeffs1 = QHBoxLayout()
        layHButtonsCoeffs1.addWidget(self.cmbFilterType)
        layHButtonsCoeffs1.addWidget(self.butAddCells)
        layHButtonsCoeffs1.addWidget(self.butDelCells)
        layHButtonsCoeffs1.addWidget(self.butClear)
        layHButtonsCoeffs1.addWidget(self.butSave)
        layHButtonsCoeffs1.addWidget(self.butLoad)
        layHButtonsCoeffs1.addWidget(self.butFromTable)
        layHButtonsCoeffs1.addWidget(self.butToTable)
        layHButtonsCoeffs1.addWidget(self.but_csv_options)
        layHButtonsCoeffs1.addStretch()

        # ----------------------------------------------------------------------
        # layHButtonsCoeffs2
        #
        # Eps / set zero settings
        # ---------------------------------------------------------------------
        self.butSetZero = QPushButton("= 0", self)
        self.butSetZero.setToolTip(
            "<span>Set selected coefficients = 0 with a magnitude &lt; &epsilon;. "
            "When nothing is selected, test the whole table.</span>")
        self.butSetZero.setIconSize(q_icon_size)

        lblEps = QLabel(self)
        lblEps.setText("<b><i>for b, a</i> &lt;</b>")

        self.ledEps = QLineEdit(self)
        self.ledEps.setToolTip("Specify tolerance value.")

        layHButtonsCoeffs2 = QHBoxLayout()
        layHButtonsCoeffs2.addWidget(self.butSetZero)
        layHButtonsCoeffs2.addWidget(lblEps)
        layHButtonsCoeffs2.addWidget(self.ledEps)
        layHButtonsCoeffs2.addStretch()

        # -------------------------------------------------------------------
        # Now put the ButtonsCoeffs HBoxes into frmButtonsCoeffs
        # ---------------------------------------------------------------------
        layVButtonsCoeffs = QVBoxLayout()
        layVButtonsCoeffs.addLayout(layHButtonsCoeffs1)
        layVButtonsCoeffs.addLayout(layHButtonsCoeffs2)
        layVButtonsCoeffs.setContentsMargins(0, 5, 0, 0)
        # This frame encompasses all Quantization Settings
        self.frmButtonsCoeffs = QFrame(self)
        self.frmButtonsCoeffs.setLayout(layVButtonsCoeffs)

        # -------------------
        self.wdg_wq_coeffs_b = FX_UI_WQ(
            fb.fil[0]['fxqc']['QCB'], wdg_name='wq_coeffs_b',
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')
        # -------------------
        self.wdg_wq_coeffs_a = FX_UI_WQ(
            fb.fil[0]['fxqc']['QCA'], wdg_name='wq_coeffs_a',
            label='<b>Coeff. Quantization <i>a<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')

        #######################################################################
        # ########################  Main UI Layout ############################
        #######################################################################
        # Layout and frame for a coefficients quantization
        # Layout and frame for output quantization
        layVQbWdg = QVBoxLayout()
        layVQbWdg.addWidget(self.wdg_wq_coeffs_b)
        self.frm_wq_coeffs_b = QFrame(self)
        self.frm_wq_coeffs_b.setLayout(layVQbWdg)
        self.frm_wq_coeffs_b.setContentsMargins(*params['wdg_margins'])

        layVQaWdg = QVBoxLayout()
        layVQaWdg.addWidget(self.wdg_wq_coeffs_a)
        self.frm_wq_coeffs_a = QFrame(self)
        self.frm_wq_coeffs_a.setLayout(layVQaWdg)
        self.frm_wq_coeffs_a.setContentsMargins(*params['wdg_margins'])

        # layout for frame (UI widget)
        layVMainF = QVBoxLayout()
        layVMainF.addLayout(layHDisplay)
        layVMainF.addWidget(self.frmButtonsCoeffs)

        # This frame encompasses all UI elements
        frmMain = QFrame(self)
        frmMain.setLayout(layVMainF)

        layVMain = QVBoxLayout()
        # the following affects only the first widget (intended here)
        layVMain.setAlignment(Qt.AlignTop)
        layVMain.addWidget(frmMain)
        layVMain.addWidget(self.frm_wq_coeffs_b)
        layVMain.addWidget(self.frm_wq_coeffs_a)
        layVMain.setContentsMargins(*params['wdg_margins'])
        self.setLayout(layVMain)
        #######################################################################

        # --- set initial values from dict ------------
        self.spnDigits.setValue(params['FMT_ba'])
        self.ledEps.setText(str(self.eps))

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.but_csv_options.clicked.connect(self._open_csv_win)

    # --------------------------------------------------------------------------
    def _open_csv_win(self):
        """
        Pop-up window for CSV options
        """
        if self.but_csv_options.isChecked():
            qstyle_widget(self.but_csv_options, "changed")
        else:
            qstyle_widget(self.but_csv_options, "normal")

        if dirs.csv_options_handle is None:
            # no handle to the window? Create a new instance
            if self.but_csv_options.isChecked():
                # Important: Handle to window must be class attribute, otherwise it
                # (and the attached window) is deleted immediately when it goes
                # out of scope
                dirs.csv_options_handle = CSV_option_box(self)
                dirs.csv_options_handle.sig_tx.connect(self.process_sig_rx)
                dirs.csv_options_handle.show()  # modeless i.e. non-blocking popup window
        else:
            if not self.but_csv_options.isChecked():  # this should not happen
                if dirs.csv_options_handle is None:
                    logger.warning("CSV options window is already closed!")
                else:
                    dirs.csv_options_handle.close()

        self.emit({'ui_changed': 'csv'})

    # ------------------------------------------------------------------------------
    def _close_csv_win(self):
        dirs.csv_options_handle = None
        self.but_csv_options.setChecked(False)
        qstyle_widget(self.but_csv_options, "normal")

    # ------------------------------------------------------------------------------
    def _set_load_save_icons(self):
        """
        Set icons / tooltipps for loading and saving data to / from file or
        clipboard depending on selected options.
        """
        if params['CSV']['clipboard']:
            self.butFromTable.setIcon(QIcon(':/to_clipboard.svg'))
            self.butFromTable.setToolTip(
                "<span>Copy table to clipboard.<br>For float format, SELECTED items "
                "are copied as displayed. When nothing is selected, the whole table "
                "is copied with full precision.</span>")

            self.butToTable.setIcon(QIcon(':/from_clipboard.svg'))
            self.butToTable.setToolTip(
                "<span>Copy clipboard to table. Table data format (e.g. 'Hex') has to "
                "match the clipboard data format, otherwise data may be imported "
                "incorrectly without warning.</span>")
        else:
            self.butFromTable.setIcon(QIcon(':/save.svg'))
            self.butFromTable.setToolTip(
                "<span>"
                "Save table to file.<br>"
                "For float format,  SELECTED items are copied as "
                "displayed. When nothing is selected, the whole table "
                "is copied with full precision.</span>")

            self.butToTable.setIcon(QIcon(':/file.svg'))
            self.butToTable.setToolTip(
                "<span>Load table from file. Table data format (e.g. 'Hex') has to "
                "match the data format in the file, otherwise data may be imported "
                "incorrectly without warning.</span>")

        if dirs.csv_options_handle is None:
            qstyle_widget(self.but_csv_options, "normal")
            self.but_csv_options.setChecked(False)
        else:
            qstyle_widget(self.but_csv_options, "changed")
            self.but_csv_options.setChecked(True)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Test with python -m pyfda.input_widgets.input_coeffs_ui """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Input_Coeffs_UI()

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
