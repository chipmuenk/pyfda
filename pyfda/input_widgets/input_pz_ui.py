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
import logging

from pyfda.libs.compat import (
    pyqtSignal, Qt, QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QRadioButton, QFrame, QSpinBox, QFont, QIcon, QVBoxLayout, QHBoxLayout)
from pyfda.libs.pyfda_qt_lib import qstyle_widget, qcmb_box_populate, emit
from pyfda.libs.pyfda_qt_classes import PushButton
from pyfda.libs.csv_option_box import CSV_option_box
from pyfda.libs.pyfda_lib import to_html, first_item
import pyfda.libs.pyfda_dirs as dirs
from pyfda.pyfda_rc import params

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
class Input_PZ_UI(QWidget):
    """
    Create the UI for the InputPZ class
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing

    def __init__(self):
        super().__init__()
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

        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig: dict) -> None:
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
        # logger.debug("PROCESS_SIG_RX\n{0}".format(pprint_log(dict_sig)))
        if dict_sig['id'] == id(self):
            logger.warning(
                # this should not happen as the rx slot is not connected globally
                'Stopped infinite loop: "%s"', first_item(dict_sig))
            return

        if 'close_event' in dict_sig:
            self._close_csv_win()
            # send signal that pop-up box is closed
            self.emit({'ui_global_changed': 'csv'})
        elif 'ui_global_changed' in dict_sig:
            self._set_load_save_icons()  # update icons file <-> clipboard
            # signal change of CSV options to other widgets with current id
            self.emit({'ui_global_changed': 'csv'})

    # ------------------------------------------------------------------------------
    def _construct_ui(self) -> None:
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
        # q_icon_size = QSize(20, 20) # optional, size is derived from but_add_cells

        # ---------------------------------------------
        # UI Elements for controlling the display
        # ---------------------------------------------

        lbl_display = QLabel(to_html("Display:", frmt='bi'), self)
        self.cmb_pz_frmt = QComboBox(self)
        qcmb_box_populate(
            self.cmb_pz_frmt, self.cmb_pz_frmt_items, self.cmb_pz_frmt_init)

        self.spn_digits = QSpinBox(self)
        self.spn_digits.setRange(0, 16)
        self.spn_digits.setToolTip("Number of digits to display.")
        self.lbl_digits = QLabel("Digits", self)
        self.lbl_digits.setFont(self.bifont)

        lay_h_display = QHBoxLayout()
        lay_h_display.setContentsMargins(*params['wdg_margins'])
        lay_h_display.setAlignment(Qt.AlignLeft)
        lay_h_display.addWidget(lbl_display)
        lay_h_display.addWidget(self.cmb_pz_frmt)
        lay_h_display.addWidget(self.spn_digits)
        lay_h_display.addWidget(self.lbl_digits)
        lay_h_display.addStretch()
        frm_display = QFrame(self)
        frm_display.setLayout(lay_h_display)

        # ---------------------------------------------
        # UI Elements for setting the gain
        # ---------------------------------------------
        self.chk_gain = QRadioButton(self, checked=True)
        lbl_gain = QLabel(to_html("k =", frmt='bi'), self)
        self.led_gain = QLineEdit(self, objectName="led_gain")
        self.led_gain.setToolTip(
            "<span>Specify gain factor <i>k</i></span>")
        self.led_gain.setText(str(1.))
        self.led_gain.setEnabled(self.chk_gain.isChecked())

        self.chk_h_max = QRadioButton(self)
        lbl_h_max = QLabel(to_html("|<i>H</i><sub>max</sub>(<i>f</i>)| =", frmt='b'), self)
        self.led_h_max = QLineEdit(self, objectName="led_h_max")
        self.led_h_max.setToolTip(
            "<span>Specify maximum of magnitude response.</span>")
        self.led_h_max.setText(str(1.))
        self.led_h_max.setEnabled(self.chk_h_max.isChecked())

        lay_h_gain = QHBoxLayout()
        lay_h_gain.setContentsMargins(*params['wdg_margins'])

        lay_h_gain.addWidget(self.chk_gain)
        lay_h_gain.addWidget(lbl_gain)
        lay_h_gain.addWidget(self.led_gain)
        lay_h_gain.addWidget(self.chk_h_max)
        lay_h_gain.addWidget(lbl_h_max)
        lay_h_gain.addWidget(self.led_h_max)
        lay_h_gain.addStretch()
        frm_gain = QFrame(self)
        frm_gain.setLayout(lay_h_gain)

        # ---------------------------------------------
        # UI Elements for loading / storing / manipulating cells and rows
        # ---------------------------------------------
        self.but_format = PushButton(self, icon=QIcon(':/star.svg'), checked=False)
        self.but_format.setToolTip(
            "<span><b>Formatted Data</b><br><br>"
            "When <b>inactive</b>: Import / export poles, zeros and gain <i>k</i> "
            "in float / complex format with full precision.<br><br>"
            "When <b>active</b>: Import / export in selected display format, e.g. in polar "
            "coordinates with the selected number of digits etc.</span>"
            )
        q_icon_size = self.but_format.iconSize()

        self.but_add_cells = QPushButton(self)
        self.but_add_cells.setIcon(QIcon(':/row_insert_above.svg'))
        self.but_add_cells.setToolTip(
            "<span>Select cells to insert a new cell above each selected cell. "
            "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
            "When nothing is selected, add a row at the end.</span>")
        self.but_add_cells.setIconSize(q_icon_size)
        # q_icon_size = self.but_add_cells.iconSize()

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

        self.but_undo = QPushButton(self)
        self.but_undo.setIcon(QIcon(':/action-undo.svg'))
        self.but_undo.setIconSize(q_icon_size)
        self.but_undo.setToolTip("<span>Undo: (Re)Load P/Z table from current filter.</span>")

        self.but_clear = QPushButton(self)
        self.but_clear.setIcon(QIcon(':/trash.svg'))
        self.but_clear.setIconSize(q_icon_size)
        self.but_clear.setToolTip("Clear all table entries.")

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
            "<span>Select CSV format like separator and line break.</span>")

        self.load_save_clipboard = not self.load_save_clipboard  # is inverted next step
        self._set_load_save_icons()  # initialize icon / button settings

        lay_h_buttons_pz1 = QHBoxLayout()
        lay_h_buttons_pz1.addWidget(self.but_add_cells)
        lay_h_buttons_pz1.addWidget(self.but_del_cells)
        lay_h_buttons_pz1.addWidget(self.but_clear)
        lay_h_buttons_pz1.addWidget(self.but_undo)
        lay_h_buttons_pz1.addWidget(self.but_apply)
        lay_h_buttons_pz1.addWidget(self.but_file_clipboard)
        lay_h_buttons_pz1.addWidget(self.but_table_import)
        lay_h_buttons_pz1.addWidget(self.but_table_export)
        lay_h_buttons_pz1.addWidget(self.but_format)
        lay_h_buttons_pz1.addWidget(self.but_csv_options)
        lay_h_buttons_pz1.addStretch()

        # -------------------------------------------------------------------
        #   Eps / set zero settings
        # ---------------------------------------------------------------------
        self.but_set_zero = QPushButton("= 0", self)
        self.but_set_zero.setToolTip(
            "<span>Check whether selected poles / zeros are equal or zero with a "
            "tolerance of &lt; &epsilon;. "
            "When nothing is selected, test the whole table.</span>")
        self.but_set_zero.setIconSize(q_icon_size)

        lbl_eps = QLabel(self)
        lbl_eps.setText("<b><i>for &epsilon;</i> &lt;</b>")

        self.led_eps = QLineEdit(self)
        self.led_eps.setToolTip("Specify absolute tolerance value.")

        lay_h_buttons_pz2 = QHBoxLayout()
        lay_h_buttons_pz2.addWidget(self.but_set_zero)
        lay_h_buttons_pz2.addWidget(lbl_eps)
        lay_h_buttons_pz2.addWidget(self.led_eps)
        lay_h_buttons_pz2.addStretch()

        # -------------------------------------------------------------------
        # Now put the _buttons_pz HBoxes into frm_buttons_pz
        # ---------------------------------------------------------------------
        lay_v_buttons_pz = QVBoxLayout()
        lay_v_buttons_pz.addLayout(lay_h_buttons_pz1)
        lay_v_buttons_pz.addLayout(lay_h_buttons_pz2)
        lay_v_buttons_pz.setContentsMargins(*params['wdg_margins'])

        frm_buttons_pz = QFrame(self)
        frm_buttons_pz.setLayout(lay_v_buttons_pz)

        # ########################  Main UI Layout ############################

        lay_v_main = QVBoxLayout()
        lay_v_main.setContentsMargins(*params['wdg_margins'])
        # the following affects only the first widget (intended here)
        lay_v_main.setAlignment(Qt.AlignTop)
        lay_v_main.addWidget(frm_gain)
        lay_v_main.addWidget(frm_buttons_pz)
        lay_v_main.addWidget(frm_display)
        self.setLayout(lay_v_main)

        # --- set initial values from dict ------------
        self.spn_digits.setValue(params['FMT_pz'])
        self.led_eps.setText(str(self.eps))
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.but_csv_options.clicked.connect(self._open_csv_win)
        self.but_file_clipboard.clicked.connect(self._set_load_save_icons)

    # ------------------------------------------------------------------------------
    def _open_csv_win(self) -> None:
        """
        Pop-up window for CSV options
        """
        if dirs.csv_options_handle is None:
            # no handle to the window? Create a new instance!
            if self.but_csv_options.checked:
                # Important: Handle to window must be class attribute otherwise it (and
                # the attached window) is deleted immediately when it goes out of scope
                dirs.csv_options_handle = CSV_option_box()
                dirs.csv_options_handle.sig_tx.connect(self.process_sig_rx)
                dirs.csv_options_handle.show()  # modeless i.e. non-blocking popup window
                # alert other widgets that csv options / visibility have changed
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
    # Run widget standalone with `python -m pyfda.input_widgets.input_pz_ui`

    import sys
    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = Input_PZ_UI()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
