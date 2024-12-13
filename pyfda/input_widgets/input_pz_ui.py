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
from pyfda.libs.pyfda_lib import to_html, first_item
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
        self.cmb_pz_frmt_items = [
            """<span>Set display format for poles and zeros to
            either cartesian (x + jy) or polar (r * &ang; &Omega;).
            Type 'o' for '&deg;', '&lt;' for '&ang;' and 'pi' for '&pi;'.
            Typing just the angle '&lt;45 o' creates a pole or zero on the
            unit circle (<i>r = 1</i>).</span>""",
            #
            ("cartesian", "Cartesian", "Cartesian coordinates (x + jy)"),
            ("polar_rad", "Polar (rad)",
             "<span>Polar coordinates (r * &ang; &Omega;) with &ang; in rad.</span>"),
            ('polar_pi', 'Polar (pi)',
             "<span>Polar coordinates (r * &ang; &Omega;) with &ang; in multiples "
             "of &pi;, type 'pi' instead of &pi;.</span>"),
            ('polar_deg', 'Polar (°)',
            "<span>Polar coordinates (r * &ang; &Omega;) with &ang; in degrees, "
            "use 'o' or '°' as the degree sign.</span>"),]
        # π: u'3C0, °: u'B0, ∠: u'2220
        self.cmb_pz_frmt_init = 'cartesian'  # initial setting

        self.load_save_clipboard = False  # load / save to clipboard or file

        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the CSV pop-up window
        """
        # logger.debug("PROCESS_SIG_RX\n{0}".format(pprint_log(dict_sig)))
        if dict_sig['id'] == id(self):
            logger.warning(
                # this should not happen as the rx slot is not connected globally
                f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return
        elif 'close_event' in dict_sig:
            self._close_csv_win()
            # send signal that pop-up box is closed
            self.emit({'ui_global_changed': 'csv'})
        elif 'ui_global_changed' in dict_sig:
            self._set_load_save_icons()  # update icons file <-> clipboard
            # signal change of CSV options to other widgets with current id
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
#        q_icon_size = QSize(20, 20) # optional, size is derived from butAddCells

        # ---------------------------------------------
        # UI Elements for controlling the display
        # ---------------------------------------------
        self.cmbPZFrmt = QComboBox(self)
        qcmb_box_populate(
            self.cmbPZFrmt, self.cmb_pz_frmt_items, self.cmb_pz_frmt_init)

        self.spnDigits = QSpinBox(self)
        self.spnDigits.setRange(0, 16)
        self.spnDigits.setToolTip("Number of digits to display.")
        self.lblDigits = QLabel("Digits", self)
        self.lblDigits.setFont(self.bifont)

        self.but_format = PushButton(self, icon=QIcon(':/star.svg'), checked=False)
        self.but_format.setToolTip(
            "<span><b>Formatted Data</b><br><br>"
            "When <b>inactive</b>: Import / export poles, zeros and gain <i>k</i> "
            "in float / complex format with full precision.<br><br>"
            "When <b>active</b>: Import / export in selected display format, e.g. in polar "
            "coordinates with the selected number of digits etc.</span>"
            )
        q_icon_size = self.but_format.iconSize()

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
        layHDisplay.addWidget(self.cmbPZFrmt)
        layHDisplay.addWidget(self.spnDigits)
        layHDisplay.addWidget(self.lblDigits)
        # layHDisplay.addWidget(self.cmbCausal)
        layHDisplay.addWidget(self.but_format)
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
        self.ledGain = QLineEdit(self, objectName="ledGain")
        self.ledGain.setToolTip(
            "<span>Specify gain factor <i>k</i> "
            "(only possible for Normalize = 'None').</span>")
        self.ledGain.setText(str(1.))

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
        self.butAddCells.setToolTip(
            "<span>Select cells to insert a new cell above each selected cell. "
            "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
            "When nothing is selected, add a row at the end.</span>")
        self.butAddCells.setIconSize(q_icon_size)
        # q_icon_size = self.butAddCells.iconSize()

        self.butDelCells = QPushButton(self)
        self.butDelCells.setIcon(QIcon(':/row_delete.svg'))
        self.butDelCells.setIconSize(q_icon_size)
        self.butDelCells.setToolTip(
            "<span>Delete selected cell(s) from the table. "
            "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
            "When nothing is selected, delete the last row.</span>")

        self.but_apply = QPushButton(self)
        self.but_apply.setIcon(QIcon(':/check.svg'))
        self.but_apply.setIconSize(q_icon_size)
        self.but_apply.setToolTip(
            "<span>Apply changes and update all plots and widgets.</span>")

        self.but_undo = QPushButton(self)
        self.but_undo.setIcon(QIcon(':/action-undo.svg'))
        self.but_undo.setIconSize(q_icon_size)
        self.but_undo.setToolTip("<span>Undo: (Re)Load P/Z table from current filter.</span>")

        self.butClear = QPushButton(self)
        self.butClear.setIcon(QIcon(':/trash.svg'))
        self.butClear.setIconSize(q_icon_size)
        self.butClear.setToolTip("Clear all table entries.")

        self.but_file_clipboard = PushButton(self, icon=QIcon(':/clipboard.svg'), checked=False)
        self.but_file_clipboard.setIconSize(q_icon_size)
        self.but_file_clipboard.setToolTip("Select between file and clipboard import / export.")

        self.but_table_import = QPushButton(self)
        self.but_table_import.setIconSize(q_icon_size)
        self.but_table_import.setIcon(QIcon(':/table_import.svg'))
        self.but_table_import.setToolTip(
            "<span><b>Import poles / zeros / gain</b> from file or clipboard<br><br>"
            "When the &lt;FORMATTED DATA&gt; button is inactive, use float / complex "
            "format with full precision.<br>"
            "Otherwise, import in display format.</span>")
        
        self.but_table_export = QPushButton(self)
        self.but_table_export.setIconSize(q_icon_size)
        self.but_table_export.setIcon(QIcon(':/table_export.svg'))
        self.but_table_export.setToolTip(
            "<span><b> Export poles / zeros / gain</b> to file or clipboard<br><br>" 
            "When the &lt;FORMATTED DATA&gt; button is inactive, use float / complex "
            "forma with full precision.<br>"
            "Otherwise, export as displayed.</span>")

        self.but_csv_options = PushButton(self, icon=QIcon(':/csv_options.svg'), checked=False)
        # self.but_csv_options.setIcon(QIcon(':/csv_options.svg'))
        self.but_csv_options.setIconSize(q_icon_size)
        self.but_csv_options.setToolTip(
            "<span>Select CSV format and whether "
            "to copy to/from clipboard or file.</span>")

        self.load_save_clipboard = not self.load_save_clipboard  # is inverted next step
        self._set_load_save_icons()  # initialize icon / button settings

        layHButtonsCoeffs1 = QHBoxLayout()
        layHButtonsCoeffs1.addWidget(self.butAddCells)
        layHButtonsCoeffs1.addWidget(self.butDelCells)
        layHButtonsCoeffs1.addWidget(self.butClear)
        layHButtonsCoeffs1.addWidget(self.but_undo)
        layHButtonsCoeffs1.addWidget(self.but_apply)
        layHButtonsCoeffs1.addWidget(self.but_file_clipboard)
        layHButtonsCoeffs1.addWidget(self.but_table_import)
        layHButtonsCoeffs1.addWidget(self.but_table_export)
        layHButtonsCoeffs1.addWidget(self.but_csv_options)
        layHButtonsCoeffs1.addStretch()

        # -------------------------------------------------------------------
        #   Eps / set zero settings
        # ---------------------------------------------------------------------
        self.butSetZero = QPushButton("= 0", self)
        self.butSetZero.setToolTip(
            "<span>Check whether selected poles / zeros are equal or zero with a "
            "tolerance oe &lt; &epsilon;. "
            "When nothing is selected, test the whole table.</span>")
        self.butSetZero.setIconSize(q_icon_size)

        lblEps = QLabel(self)
        lblEps.setText("<b><i>for &epsilon;</i> &lt;</b>")

        self.ledEps = QLineEdit(self)
        self.ledEps.setToolTip("Specify absolute tolerance value.")

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
        self.but_file_clipboard.clicked.connect(self._set_load_save_icons)

    # ------------------------------------------------------------------------------
    def _open_csv_win(self):
        """
        Pop-up window for CSV options
        """
        if dirs.csv_options_handle is None:
            # no handle to the window? Create a new instance!
            if self.but_csv_options.checked:
                # Important: Handle to window must be class attribute otherwise it (and
                # the attached window) is deleted immediately when it goes out of scope
                dirs.csv_options_handle = CSV_option_box(self)
                dirs.csv_options_handle.sig_tx.connect(self.process_sig_rx)
                dirs.csv_options_handle.show()  # modeless i.e. non-blocking popup window
                # alert other widgets that csv options / visibility have changed
                self.emit({'ui_global_changed': 'csv'})

        else:  # close window, delete handle
            dirs.csv_options_handle.close()
            self.but_csv_options.setChecked(False)
            # 'ui_global_changed': 'csv' is emitted by closing pop-up box

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
        self.load_save_clipboard = not self.load_save_clipboard
        if self.load_save_clipboard:
            self.but_file_clipboard.setIcon(QIcon(':/clipboard.svg'))
        else:
            self.but_file_clipboard.setIcon(QIcon(':/file.svg'))


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
