# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)


"""
Create the UI for the FilterPZ class
"""
from pyfda.libs.compat import (
    pyqtSignal, Qt, QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QFrame, QSpinBox, QFont, QIcon, QVBoxLayout, QHBoxLayout)

from pyfda.libs.pyfda_qt_lib import qstyle_widget, qcmb_box_populate, PushButton
from pyfda.libs.csv_option_box import CSV_option_box
from pyfda.libs.pyfda_lib import to_html
import pyfda.libs.pyfda_dirs as dirs
from pyfda.pyfda_rc import params

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
class Input_PZ_UI(QWidget):
    """
    Create the UI for the InputPZ class
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None):
        """
        Pass instance `parent` of parent class (FilterCoeffs)
        """
        super(Input_PZ_UI, self).__init__(parent)
#        self.parent = parent # instance of the parent (not the base) class
        self.eps = 1.e-4  # tolerance value for e.g. setting P/Z to zero

        # Items for PZ-format combobox (data, display text, tool tip):
        self.cmb_pz_frmt_list = [
            """<span>Set display format for poles and zeros to
            either cartesian (x + jy) or polar (r * &ang; &Omega;).
            Type 'o' for '&deg;', '&lt;' for '&ang;' and 'pi' for '&pi;'.
            Typing just the angle '&lt;45 o' creates a pole or zero on the
            unit circle.</span>""",
            #
            ('cartesian', 'Cartesian'), ('polar_rad', 'Polar (rad)'),
            ('polar_pi', 'Polar (pi)'), ('polar_deg', 'Polar (°)')]
        # π: u'3C0, °: u'B0, ∠: u'2220
        self.cmb_pz_frmt_init = 'polar_deg'  # initial setting

        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the CSV pop-up window
        """
        # logger.debug("PROCESS_SIG_RX\n{0}".format(pprint_log(dict_sig)))

        if 'closeEvent' in dict_sig:
            self._close_csv_win()
            self.emit({'ui_global_changed': 'csv'})
            return  # probably not needed
        elif 'ui_global_changed' in dict_sig:
            self._set_load_save_icons()  # update icons file <-> clipboard
            # inform e.g. the p/z input widget about changes in CSV options
            self.emit({'ui_global_changed': 'csv'})

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

        # ---------------------------------------------
        # UI Elements for controlling the display
        # ---------------------------------------------
        self.butEnable = PushButton(self, icon=QIcon(':/circle-check.svg'), checked=True)
        q_icon_size = self.butEnable.iconSize()  # <- set this for manual icon sizing
        # self.butEnable.setIconSize(q_icon_size)  # and set the size
        self.butEnable.setToolTip(
            "<span>Show / hide poles and zeros in an editable table."
            " For high order systems, the table display might be slow.</span>")

        self.cmbPZFrmt = QComboBox(self)
        qcmb_box_populate(
            self.cmbPZFrmt, self.cmb_pz_frmt_list, self.cmb_pz_frmt_init)

        self.spnDigits = QSpinBox(self)
        self.spnDigits.setRange(0, 16)
        self.spnDigits.setToolTip("Number of digits to display.")
        self.lblDigits = QLabel("Digits", self)
        self.lblDigits.setFont(self.bifont)

        # self.cmbCausal = QComboBox(self)
        # causal_types = ['Causal', 'Acausal', 'Anticausal']
        # for cs in causal_types:
        #     self.cmbCausal.addItem(cs)

        # qset_cmb_box(self.cmbCausal, 'Causal')
        # self.cmbCausal.setToolTip(
        #     '<span>Set the system type. Not implemented yet.</span>')
        # self.cmbCausal.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        # self.cmbCausal.setEnabled(False)

        layHDisplay = QHBoxLayout()
        layHDisplay.setAlignment(Qt.AlignLeft)
        layHDisplay.addWidget(self.butEnable)
        layHDisplay.addWidget(self.cmbPZFrmt)
        layHDisplay.addWidget(self.spnDigits)
        layHDisplay.addWidget(self.lblDigits)
        # layHDisplay.addWidget(self.cmbCausal)
        layHDisplay.addStretch()

        # ---------------------------------------------
        # UI Elements for setting the gain
        # ---------------------------------------------
        self.lblNorm = QLabel(to_html("Normalize:", frmt='bi'), self)
        self.cmbNorm = QComboBox(self)
        self.cmbNorm.addItems(["None", "1", "Max"])
        self.cmbNorm.setToolTip(
            "<span>Set the gain <i>k</i> so that H(f)<sub>max</sub> is "
            "either 1 or the max. of the previous system.</span>")

        self.lblGain = QLabel(to_html("k =", frmt='bi'), self)
        self.ledGain = QLineEdit(self)
        self.ledGain.setToolTip(
            "<span>Specify gain factor <i>k</i>"
            " (only possible for Normalize = 'None').</span>")
        self.ledGain.setText(str(1.))
        self.ledGain.setObjectName("ledGain")

        layHGain = QHBoxLayout()
        layHGain.addWidget(self.lblNorm)
        layHGain.addWidget(self.cmbNorm)
        layHGain.addWidget(self.lblGain)
        layHGain.addWidget(self.ledGain)
        layHGain.addStretch()

        # ---------------------------------------------
        # UI Elements for loading / storing / manipulating cells and rows
        # ---------------------------------------------
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
            "<span>Copy P/Z table to filter dict and update all plots and widgets."
            "</span>")

        self.butLoad = QPushButton(self)
        self.butLoad.setIcon(QIcon(':/download.svg'))
        self.butLoad.setIconSize(q_icon_size)
        self.butLoad.setToolTip("Reload P/Z table from filter dict.")

        self.butClear = QPushButton(self)
        self.butClear.setIcon(QIcon(':/trash.svg'))
        self.butClear.setIconSize(q_icon_size)
        self.butClear.setToolTip("Clear all table entries.")

        self.butFromTable = QPushButton(self)
        self.butFromTable.setIconSize(q_icon_size)

        self.butToTable = QPushButton(self)
        self.butToTable.setIconSize(q_icon_size)

        self.but_csv_options = QPushButton(self)
        self.but_csv_options.setIcon(QIcon(':/settings.svg'))
        self.but_csv_options.setIconSize(q_icon_size)
        self.but_csv_options.setToolTip(
            "<span>Select CSV format and whether "
            "to copy to/from clipboard or file.</span>")
        self.but_csv_options.setCheckable(True)
        self.but_csv_options.setChecked(False)

        self._set_load_save_icons()  # initialize icon / button settings

        layHButtonsCoeffs1 = QHBoxLayout()
#        layHButtonsCoeffs1.addWidget(self.cmbFilterType)
        layHButtonsCoeffs1.addWidget(self.butAddCells)
        layHButtonsCoeffs1.addWidget(self.butDelCells)
        layHButtonsCoeffs1.addWidget(self.butClear)
        layHButtonsCoeffs1.addWidget(self.butSave)
        layHButtonsCoeffs1.addWidget(self.butLoad)
        layHButtonsCoeffs1.addWidget(self.butFromTable)
        layHButtonsCoeffs1.addWidget(self.butToTable)
        layHButtonsCoeffs1.addWidget(self.but_csv_options)
        layHButtonsCoeffs1.addStretch()

        # -------------------------------------------------------------------
        #   Eps / set zero settings
        # ---------------------------------------------------------------------
        self.butSetZero = QPushButton("= 0", self)
        self.butSetZero.setToolTip(
            "<span>Set selected poles / zeros = 0 with a magnitude &lt; &epsilon;. "
            "When nothing is selected, test the whole table.</span>")
        self.butSetZero.setIconSize(q_icon_size)

        lblEps = QLabel(self)
        lblEps.setText("<b><i>for &epsilon;</i> &lt;</b>")

        self.ledEps = QLineEdit(self)
        self.ledEps.setToolTip("Specify tolerance value.")

        layHButtonsCoeffs2 = QHBoxLayout()
        layHButtonsCoeffs2.addWidget(self.butSetZero)
        layHButtonsCoeffs2.addWidget(lblEps)
        layHButtonsCoeffs2.addWidget(self.ledEps)
        layHButtonsCoeffs2.addStretch()

        # ########################  Main UI Layout ############################
        # layout for frame (UI widget)
        layVMainF = QVBoxLayout()
        layVMainF.addLayout(layHDisplay)
        layVMainF.addLayout(layHGain)
        layVMainF.addLayout(layHButtonsCoeffs1)
        layVMainF.addLayout(layHButtonsCoeffs2)
        # This frame encompasses all UI elements
        frmMain = QFrame(self)
        frmMain.setLayout(layVMainF)

        layVMain = QVBoxLayout()
        layVMain.setAlignment(Qt.AlignTop)  # affects only the first widget (intended)
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(*params['wdg_margins'])
        self.setLayout(layVMain)

        # --- set initial values from dict ------------
        self.spnDigits.setValue(params['FMT_pz'])
        self.ledEps.setText(str(self.eps))
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.but_csv_options.clicked.connect(self._open_csv_win)

    # ------------------------------------------------------------------------------
    def _open_csv_win(self):
        """
        Pop-up window for CSV options
        """
        if self.but_csv_options.isChecked():
            qstyle_widget(self.but_csv_options, "changed")
        else:
            qstyle_widget(self.but_csv_options, "normal")

        if dirs.csv_options_handle is None:
            # no handle to the window? Create a new instance!
            if self.but_csv_options.isChecked():
                # Important: Handle to window must be class attribute otherwise it (and
                # the attached window) is deleted immediately when it goes out of scope
                dirs.csv_options_handle = CSV_option_box(self)
                dirs.csv_options_handle.sig_tx.connect(self.process_sig_rx)
                dirs.csv_options_handle.show()  # modeless i.e. non-blocking popup window
        else:
            if not self.but_csv_options.isChecked():  # this should not happen
                if dirs.csv_options_handle is None:
                    logger.warning("CSV options window is already closed!")
                else:
                    dirs.csv_options_handle.close()

        self.emit({'ui_global_changed': 'csv'})

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
                "<span>Copy table to clipboard, SELECTED items are copied as "
                "displayed. When nothing is selected, the whole table "
                "is copied with full precision in decimal format.</span>")

            self.butToTable.setIcon(QIcon(':/from_clipboard.svg'))
            self.butToTable.setToolTip("<span>Copy clipboard to table.</span>")
        else:
            self.butFromTable.setIcon(QIcon(':/save.svg'))
            self.butFromTable.setToolTip(
                "<span>Save table to file, SELECTED items are copied as "
                "displayed. When nothing is selected, the whole table "
                "is copied with full precision in decimal format.</span>")

            self.butToTable.setIcon(QIcon(':/file.svg'))
            self.butToTable.setToolTip("<span>Load table from file.</span>")

        if dirs.csv_options_handle is None:
            qstyle_widget(self.but_csv_options, "normal")
            self.but_csv_options.setChecked(False)
        else:
            qstyle_widget(self.but_csv_options, "changed")
            self.but_csv_options.setChecked(True)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.input_widgets.input_pz_ui` """

    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Input_PZ_UI()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
