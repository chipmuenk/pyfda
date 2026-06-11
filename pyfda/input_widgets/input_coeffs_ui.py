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
import logging

# load the icons resource file
from pyfda import qrc_resources  # noqa: F401  # pylint: disable=unused-import
from pyfda.filterbroker import fb_get
from pyfda.libs.compat import (
    pyqtSignal, Qt, QWidget, QLabel, QLineEdit, QComboBox, QPushButton, QFrame,
    QSpinBox, QFont, QIcon, QVBoxLayout, QHBoxLayout, QSizePolicy)
from pyfda.libs.csv_option_box import CSV_option_box
from pyfda.libs.pyfda_lib import to_html
from pyfda.libs.pyfda_qt_lib import qstyle_widget, qcmb_box_populate, emit
from pyfda.libs.pyfda_qt_classes import PushButton
from pyfda.libs.pyfda_lib import first_item
import pyfda.libs.pyfda_dirs as dirs
from pyfda.fixpoint_widgets.fx_ui_wq import FX_UI_WQ
from pyfda.pyfda_rc import params

logger = logging.getLogger(__name__)


class Input_Coeffs_UI(QWidget):
    """
    Create the UI for the Input_Coeffs() class
    """
    sig_rx = pyqtSignal(dict)  # incoming
    sig_tx = pyqtSignal(dict)  # outgoing

    def __init__(self):
        super().__init__()
        self.eps = 1.e-6  # initialize tolerance value

        self.cmb_qfrmt_items = [
            "<span>Quantization format for coefficients (only affects "
            "display, not stored values).</span>",
            ('float64', "Float64", "<span>Full precision floating point format</span>"),
            ('float32', "Float32", "<span>Single precision floating point format</span>"),
            ('qint', "Integer", "<span>Integer format with <i>WI</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 1)</span>"),
            ('qfrac', "Fractional",
             "<span>General fractional format with <i>WI</i> + <i>WF</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 2<sup>WF</sup>).</span>")
            ]
        self.cmb_qfrmt_default = 'float64'

        self.cmb_fx_base_items = [
            "<span>Select the coefficient fixpoint display format.</span>",
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

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict) -> None:
        """
        Process signals coming from the CSV pop-up window
        """
        # logger.warning("PROCESS_SIG_RX:\n{0}".format(pprint_log(dict_sig)))
        if dict_sig['id'] == id(self):
            # this should not happen as the rx slot is not connected globally
            logger.warning('Stopped infinite loop: "%s"', first_item(dict_sig))
            return

        if 'close_event' in dict_sig:
            self._close_csv_win()
            # send signal that pop-up box is closed
            self.emit({'ui_global_changed': 'csv'})
        elif 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed'] == 'csv':
            # signal change of CSV options to other widgets with current id
            self.emit({'ui_global_changed': 'csv'})

    # ------------------------------------------------------------------------------
    def _construct_UI(self) -> None:
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
        #
        # UI Elements for controlling the display
        # ---------------------------------------------
        lbl_display = QLabel(to_html("Display:", frmt='bi'), self)
        self.cmb_qfrmt = QComboBox(self)
        qcmb_box_populate(self.cmb_qfrmt, self.cmb_qfrmt_items,
                          self.cmb_qfrmt_default)
        self.cmb_qfrmt.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.cmb_fx_base = QComboBox(self)
        qcmb_box_populate(self.cmb_fx_base, self.cmb_fx_base_items,
                          self.cmb_fx_base_default)

        self.spn_digits = QSpinBox(self)
        self.spn_digits.setRange(0, 20)
        self.spn_digits.setValue(params['FMT_ba'])
        self.spn_digits.setToolTip("Number of digits to display.")
        self.lbl_digits = QLabel("Digits", self)
        self.lbl_digits.setFont(self.bifont)

        self.but_quant = QPushButton(self)
        self.but_quant.setToolTip(
            "<span>Quantize selected coefficients / whole table with specified "
            "settings and store in filter dict, affecting both view and data in memory."
            "</span>")
        self.but_quant.setIcon(QIcon(':/quantize.svg'))
        # self.but_quant.setIconSize(q_icon_size)
        q_icon_size = self.but_quant.iconSize()  # <- comment this for manual sizing
        self.but_quant.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # layH_q_frmt = QHBoxLayout()
        # layH_q_frmt.addWidget(self.cmb_qfrmt)
        # layH_q_frmt.addWidget(self.but_quant)
        # layH_q_frmt.setContentsMargins(5, 0, 0, 0)  # 5 pixels extra left space
        # self.frm_q_frmt = QFrame(self)
        # self.frm_q_frmt.setLayout(layH_q_frmt)

        lay_h_display = QHBoxLayout()
        lay_h_display.setContentsMargins(*params['wdg_margins'])
        lay_h_display.setAlignment(Qt.AlignLeft)
        lay_h_display.addWidget(lbl_display)
        lay_h_display.addWidget(self.cmb_qfrmt)
        lay_h_display.addWidget(self.spn_digits)
        lay_h_display.addWidget(self.lbl_digits)
        lay_h_display.addWidget(self.cmb_fx_base)
        lay_h_display.addWidget(self.but_quant)
        lay_h_display.addStretch()

        frm_display = QFrame(self)
        frm_display.setLayout(lay_h_display)

        #######################################################################
        # frm_buttons_coeffs
        #
        # This frame contains all buttons for manipulating coefficients
        # -----------------------------------------------------------------
        # lay_h_buttons_coeffs1
        #
        # UI Elements for loading / storing / manipulating cells and rows
        # -----------------------------------------------------------------
        self.cmb_filter_type = QComboBox(self, objectName="comboFilterType")
        self.cmb_filter_type.setToolTip(
            "<span>Select between IIR and FIR filter for manual entry. "
            "Changing the type reloads the filter from the filter dict.</span>")
        self.cmb_filter_type.addItems(["FIR", "IIR"])
        self.cmb_filter_type.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.but_add_cells = QPushButton(self)
        self.but_add_cells.setIcon(QIcon(':/row_insert_above.svg'))
        self.but_add_cells.setIconSize(q_icon_size)
        self.but_add_cells.setToolTip(
            "<span>Insert a row above each selected cell. "
            "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
            "When nothing is selected, append a row to the end.</span>")

        self.but_del_cells = QPushButton(self)
        self.but_del_cells.setIcon(QIcon(':/row_delete.svg'))
        self.but_del_cells.setIconSize(q_icon_size)
        self.but_del_cells.setToolTip(
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

        self.but_clear = QPushButton(self)
        self.but_clear.setIcon(QIcon(':/trash.svg'))
        self.but_clear.setIconSize(q_icon_size)
        self.but_clear.setToolTip("Clear all table entries.")

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
            "<span>Select CSV format options like separator and linebreaks.</span>")

        self.but_format = PushButton(self, icon=QIcon(':/star.svg'), checked=False)
        self.but_format.setToolTip(
            "<span><b>Formatted Data</b><br><br>"
            "When <b>inactive</b>: Import / export coefficients in float / complex "
            "format with full precision.<br><br>"
            "When <b>active</b>: Import / export coefficients in selected display "
            "format, i.e. with the selected number of digits in Hex, Binary etc.</span>"
            )
        self.but_format.setIconSize(q_icon_size)


        self.load_save_clipboard = not self.load_save_clipboard  # is inverted next step
        self._set_load_save_icons()  # initialize icon / button settings

        lay_h_buttons_coeffs1 = QHBoxLayout()
        lay_h_buttons_coeffs1.addWidget(self.cmb_filter_type)
        lay_h_buttons_coeffs1.addWidget(self.but_add_cells)
        lay_h_buttons_coeffs1.addWidget(self.but_del_cells)
        lay_h_buttons_coeffs1.addWidget(self.but_clear)
        lay_h_buttons_coeffs1.addWidget(self.but_undo)
        lay_h_buttons_coeffs1.addWidget(self.but_apply)
        lay_h_buttons_coeffs1.addWidget(self.but_file_clipboard)
        lay_h_buttons_coeffs1.addWidget(self.but_table_import)
        lay_h_buttons_coeffs1.addWidget(self.but_table_export)
        lay_h_buttons_coeffs1.addWidget(self.but_format)
        lay_h_buttons_coeffs1.addWidget(self.but_csv_options)
        lay_h_buttons_coeffs1.addStretch()

        # ----------------------------------------------------------------------
        # lay_h_buttons_coeffs2
        #
        # Eps / set zero settings
        # ---------------------------------------------------------------------
        self.but_set_zero = QPushButton("= 0", self)
        self.but_set_zero.setToolTip(
            "<span>Set selected coefficients = 0 with a magnitude &lt; &epsilon;. "
            "When nothing is selected, test the whole table.</span>")
        self.but_set_zero.setIconSize(q_icon_size)

        lbl_eps = QLabel(self)
        lbl_eps.setText("<b><i>for b, a</i> &lt;</b>")

        self.led_eps = QLineEdit(self)
        self.led_eps.setToolTip("Specify tolerance value.")

        lay_h_buttons_coeffs2 = QHBoxLayout()
        lay_h_buttons_coeffs2.addWidget(self.but_set_zero)
        lay_h_buttons_coeffs2.addWidget(lbl_eps)
        lay_h_buttons_coeffs2.addWidget(self.led_eps)
        lay_h_buttons_coeffs2.addStretch()

        # -------------------------------------------------------------------
        # Collect lay_h_buttons_coeffs in frm_buttons_coeffs
        # ---------------------------------------------------------------------
        lay_v_buttons_coeffs = QVBoxLayout()
        lay_v_buttons_coeffs.addLayout(lay_h_buttons_coeffs1)
        lay_v_buttons_coeffs.addLayout(lay_h_buttons_coeffs2)
        lay_v_buttons_coeffs.setContentsMargins(*params['wdg_margins'])  # 0, 5, 0, 0)
        # This frame encompasses all Quantization Settings
        self.frm_buttons_coeffs = QFrame(self)
        self.frm_buttons_coeffs.setLayout(lay_v_buttons_coeffs)
        #######################################################################

        # -------------------
        self.wdg_wq_coeffs_b = FX_UI_WQ(
            fb_get('fxq', 'QCB'), objectName='fx_ui_wq_coeffs_b',
            label='<b>Coeff. Quantization <i>b<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')
        # -------------------
        self.wdg_wq_coeffs_a = FX_UI_WQ(
            fb_get('fxq', 'QCA'), objectName='fx_ui_wq_coeffs_a',
            label='<b>Coeff. Quantization <i>a<sub>I.F&nbsp;</sub></i>:</b>',
            MSB_LSB_vis='max')

        #######################################################################
        # ########################  Main UI Layout ############################
        #######################################################################

        lay_v_main = QVBoxLayout()
        lay_v_main.setContentsMargins(*params['wdg_margins'])
        # the following affects only the first widget (intended here)
        lay_v_main.setAlignment(Qt.AlignTop)
        lay_v_main.addWidget(self.frm_buttons_coeffs)
        lay_v_main.addWidget(frm_display)
        lay_v_main.addWidget(self.wdg_wq_coeffs_b)
        lay_v_main.addWidget(self.wdg_wq_coeffs_a)
        self.setLayout(lay_v_main)
        #######################################################################

        # --- set initial values from dict ------------
        self.spn_digits.setValue(params['FMT_ba'])
        self.led_eps.setText(str(self.eps))

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.but_csv_options.clicked.connect(self._open_csv_win)
        self.but_file_clipboard.clicked.connect(self._set_load_save_icons)

    # --------------------------------------------------------------------------
    def _open_csv_win(self) -> None:
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
    def _close_csv_win(self) -> None:
        dirs.csv_options_handle = None
        self.but_csv_options.setChecked(False)
        qstyle_widget(self.but_csv_options, "normal")

    # ------------------------------------------------------------------------------
    def _set_load_save_icons(self) -> None:
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
    # Test with python -m pyfda.input_widgets.input_coeffs_ui
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.QSS_RC)
    mainw = Input_Coeffs_UI()

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
