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
from pyfda.libs.pyfda_lib import to_html

from pyfda.libs.pyfda_qt_lib import (
    qset_cmb_box, qstyle_widget, qcmb_box_populate, QHLine, PushButton)
from pyfda.libs.csv_option_box import CSV_option_box
from pyfda.libs.pyfda_lib import first_item
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

        self.cmb_q_frmt_items = [
            "<span>Quantization format for coefficients (affects only "
            "the display, not the stored values).</span>",
            ('float', "Float", "<span>Full precision floating point format</span>"),
            ('qint', "Integer", "<span>Integer format with <i>WI</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 1)</span>"),
            ('qfrac', "Fractional",
             "<span>General fractional format with <i>WI</i> + <i>WF</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 2<sup>WF</sup>).</span>")
            ]
        self.cmb_q_frmt_default = "float"

        self.cmb_fx_base_items = [
            "<span>Select the coefficient fixpoint display format.</span>",
            # ("float", "Float", "<span>Coefficients with full precision in floating "
            # "point format</span>"),
            ('dec', "Dec", "<span>Fixpoint coefficients in decimal format</span>"),
            ('hex', "Hex", "<span>Fixpoint coefficients in hexadecimal format</span>"),
            ('bin', "Bin", "<span>Fixpoint coefficients in binary format</span>"),
            ('oct', "Oct", "<span>Fixpoint coefficients in octal format</span>"),
            ('csd', "CSD", "<span>Fixpoint coefficients in Canonically Signed Digit "
             "(ternary logic) format</span>")
            ]
        self.cmb_fx_base_default = "dec"

        self.load_save_clipboard = False  # load / save to clipboard or file

        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the CSV pop-up window
        """
        # logger.warning("PROCESS_SIG_RX:\n{0}".format(pprint_log(dict_sig)))
        if dict_sig['id'] == id(self):
            # this should not happen as the rx slot is not connected globally
            logger.warning(
                f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return
        elif 'close_event' in dict_sig:
            self._close_csv_win()
            # send signal that pop-up box is closed
            self.emit({'ui_global_changed': 'csv'})
        elif 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed'] == 'csv':
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
#        q_icon_size = QSize(20, 20) # optional, size is derived from butEnable

        #######################################################################
        # frmMain
        #
        # This frame contains all the buttons
        #######################################################################
        # ---------------------------------------------
        #
        # UI Elements for controlling the display
        # ---------------------------------------------

        self.cmb_qfrmt = QComboBox(self)
        qcmb_box_populate(self.cmb_qfrmt, self.cmb_q_frmt_items,
                          self.cmb_q_frmt_default)
        self.cmb_qfrmt.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.cmb_fx_base = QComboBox(self)
        qcmb_box_populate(self.cmb_fx_base, self.cmb_fx_base_items,
                          self.cmb_fx_base_default)

        self.spnDigits = QSpinBox(self)
        self.spnDigits.setRange(0, 16)
        self.spnDigits.setValue(params['FMT_ba'])
        self.spnDigits.setToolTip("Number of digits to display.")
        self.lblDigits = QLabel("Digits", self)
        self.lblDigits.setFont(self.bifont)

        self.but_quant = QPushButton(self)
        self.but_quant.setToolTip(
            "<span>Quantize selected coefficients / whole table with specified "
            "settings and save to dict. This modifies the data, not only the view."
            "</span>")
        self.but_quant.setIcon(QIcon(':/quantize.svg'))
        # self.but_quant.setIconSize(q_icon_size)
        q_icon_size = self.but_quant.iconSize()  # <- comment this for manual sizing
        self.but_quant.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.but_format = PushButton(self, icon=QIcon(':/star.svg'), checked=False)
        self.but_format.setToolTip(
            "<span><b>Formatted Data</b><br><br>"
            "When <b>inactive</b>: Import / export coefficients in float / complex "
            "format with full precision.<br><br>"
            "When <b>active</b>: Import / export coefficients in selected display "
            "format, i.e. with the selected number of digits in Hex, Binary etc.</span>"
            )
        self.but_format.setIconSize(q_icon_size)

        # layH_q_frmt = QHBoxLayout()
        # layH_q_frmt.addWidget(self.cmb_qfrmt)
        # layH_q_frmt.addWidget(self.but_quant)
        # layH_q_frmt.setContentsMargins(5, 0, 0, 0)  # 5 pixels extra left space
        # self.frm_q_frmt = QFrame(self)
        # self.frm_q_frmt.setLayout(layH_q_frmt)

        layH_display = QHBoxLayout()
        layH_display.setContentsMargins(*params['wdg_margins'])
        layH_display.setAlignment(Qt.AlignLeft)
        layH_display.addWidget(self.cmb_qfrmt)
        layH_display.addWidget(self.spnDigits)
        layH_display.addWidget(self.lblDigits)
        layH_display.addWidget(self.cmb_fx_base)
        layH_display.addWidget(self.but_quant)
        layH_display.addWidget(self.but_format)
        layH_display.addStretch()

        self.frm_display = QFrame(self)
        self.frm_display.setLayout(layH_display)

        #######################################################################
        # frm_buttons_coeffs
        #
        # This frame contains all buttons for manipulating coefficients
        # -----------------------------------------------------------------
        # layH_buttons_coeffs1
        #
        # UI Elements for loading / storing / manipulating cells and rows
        # -----------------------------------------------------------------
        self.cmbFilterType = QComboBox(self, objectName="comboFilterType")
        self.cmbFilterType.setToolTip(
            "<span>Select between IIR and FIR filter for manual entry. "
            "Changing the type reloads the filter from the filter dict.</span>")
        self.cmbFilterType.addItems(["FIR", "IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.butAddCells = QPushButton(self)
        self.butAddCells.setIcon(QIcon(':/row_insert_above.svg'))
        self.butAddCells.setIconSize(q_icon_size)
        self.butAddCells.setToolTip(
            "<span>Insert a row above each selected cell. "
            "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
            "When nothing is selected, append a row to the end.</span>")

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

        self.but_undo = QPushButton(QIcon(':/action-undo.svg'), "", self)
        self.but_undo.setIconSize(q_icon_size)
        self.but_undo.setToolTip(
            "<span>Undo: Reload coefficient table from current filter.</span>")

        self.butClear = QPushButton(self)
        self.butClear.setIcon(QIcon(':/trash.svg'))
        self.butClear.setIconSize(q_icon_size)
        self.butClear.setToolTip("Clear all table entries.")

        self.but_file_clipboard = PushButton(self, icon=QIcon(':/clipboard.svg'), checked=False)
        self.but_file_clipboard.setIconSize(q_icon_size)
        self.but_file_clipboard.setToolTip("Select between file and clipboard import / export.")

        self.but_table_export = QPushButton(self)
        self.but_table_export.setIconSize(q_icon_size)
        self.but_table_export.setIcon(QIcon(':/table_export.svg'))
        self.but_table_export.setToolTip(
            "<span><b>Export coefficients</b> to clipboard or file<br><br>"
            "When the &lt;FORMATTED DATA&gt; button is inactive, use float / complex "
            "format with full precision.<br>"
            "Otherwise, export coefficients as displayed.</span>")
        self.but_table_import = QPushButton(self)
        self.but_table_import.setIconSize(q_icon_size)
        self.but_table_import.setIcon(QIcon(':/table_import.svg'))
        self.but_table_import.setToolTip(
            "<span><b>Import coefficients</b> from clipboard or file<br><br>"
            "When the &lt;FORMATTED DATA&gt; button is inactive, use float / complex "
            "format with full precision.<br>"
            "Otherwise, import coefficients in selected display format "
            "(e.g. 'Hex').</span>")

        self.but_csv_options = PushButton(self, icon=QIcon(':/csv_options.svg'))
        # self.but_csv_options.setIconSize(q_icon_size)
        self.but_csv_options.setToolTip(
            "<span>Select CSV format and whether "
            "to copy to/from clipboard or file.</span>")

        self.load_save_clipboard = not self.load_save_clipboard  # is inverted next step
        self._set_load_save_icons()  # initialize icon / button settings

        layH_buttons_coeffs1 = QHBoxLayout()
        layH_buttons_coeffs1.addWidget(self.cmbFilterType)
        layH_buttons_coeffs1.addWidget(self.butAddCells)
        layH_buttons_coeffs1.addWidget(self.butDelCells)
        layH_buttons_coeffs1.addWidget(self.butClear)
        layH_buttons_coeffs1.addWidget(self.but_undo)
        layH_buttons_coeffs1.addWidget(self.but_apply)
        layH_buttons_coeffs1.addWidget(self.but_file_clipboard)
        layH_buttons_coeffs1.addWidget(self.but_table_import)
        layH_buttons_coeffs1.addWidget(self.but_table_export)
        layH_buttons_coeffs1.addWidget(self.but_csv_options)
        layH_buttons_coeffs1.addStretch()

        # ----------------------------------------------------------------------
        # layH_buttons_coeffs2
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

        layH_buttons_coeffs2 = QHBoxLayout()
        layH_buttons_coeffs2.addWidget(self.butSetZero)
        layH_buttons_coeffs2.addWidget(lblEps)
        layH_buttons_coeffs2.addWidget(self.ledEps)
        layH_buttons_coeffs2.addStretch()

        # -------------------------------------------------------------------
        # Now put the _buttons_coeffs HBoxes into frm_buttons_coeffs
        # ---------------------------------------------------------------------
        layV_buttons_coeffs = QVBoxLayout()
        layV_buttons_coeffs.addLayout(layH_buttons_coeffs1)
        layV_buttons_coeffs.addLayout(layH_buttons_coeffs2)
        layV_buttons_coeffs.setContentsMargins(*params['wdg_margins'])  # 0, 5, 0, 0)
        # This frame encompasses all Quantization Settings
        self.frm_buttons_coeffs = QFrame(self)
        self.frm_buttons_coeffs.setLayout(layV_buttons_coeffs)
        #######################################################################

        # -------------------
        self.wdg_wq_coeffs_b = FX_UI_WQ(
            fb.fil[0]['fxq']['QCB'], objectName='fx_ui_wq_coeffs_b',
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')
        # -------------------
        self.wdg_wq_coeffs_a = FX_UI_WQ(
            fb.fil[0]['fxq']['QCA'], objectName='fx_ui_wq_coeffs_a',
            label='<b>Coeff. Quantization <i>a<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')

        #######################################################################
        # ########################  Main UI Layout ############################
        #######################################################################

        layVMain = QVBoxLayout()
        layVMain.setContentsMargins(*params['wdg_margins'])
        # the following affects only the first widget (intended here)
        layVMain.setAlignment(Qt.AlignTop)
        layVMain.addWidget(self.frm_display)
        layVMain.addWidget(self.frm_buttons_coeffs)
        layVMain.addWidget(self.wdg_wq_coeffs_b)
        layVMain.addWidget(self.wdg_wq_coeffs_a)
        self.setLayout(layVMain)
        #######################################################################

        # --- set initial values from dict ------------
        self.spnDigits.setValue(params['FMT_ba'])
        self.ledEps.setText(str(self.eps))

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.but_csv_options.clicked.connect(self._open_csv_win)
        self.but_file_clipboard.clicked.connect(self._set_load_save_icons)

    # --------------------------------------------------------------------------
    def _open_csv_win(self):
        """
        Pop-up window for CSV options
        """
        if dirs.csv_options_handle is None:
            # no handle to the window? Create a new instance
            if self.but_csv_options.checked:
                # Important: Handle to window must be class attribute, otherwise it
                # (and the attached window) is deleted immediately when it goes
                # out of scope
                dirs.csv_options_handle = CSV_option_box(self)
                dirs.csv_options_handle.sig_tx.connect(self.process_sig_rx)
                dirs.csv_options_handle.show()  # modeless i.e. non-blocking popup window
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
        Set icon for importing / exporting data to / from file or clipboard
        """
        self.load_save_clipboard = not self.load_save_clipboard
        if self.load_save_clipboard:
            self.but_file_clipboard.setIcon(QIcon(':/clipboard.svg'))
        else:
            self.but_file_clipboard.setIcon(QIcon(':/file.svg'))

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
