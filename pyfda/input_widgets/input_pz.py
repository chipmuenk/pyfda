# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for displaying and modifying filter Poles and Zeros
"""
import logging
from pprint import pformat
import sys

import numpy as np

from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.compat import (
    QtCore, QWidget, QLineEdit, pyqtSignal, QEvent, QApplication,
    QTableWidget, QTableWidgetItem, Qt, QVBoxLayout)
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, qstyle_widget, emit
from pyfda.libs.pyfda_io_lib import qtable2csv, file2array, export_fil_data, select_file
from pyfda.libs.pyfda_sig_lib import zeros_with_val, zpk2array, normalize_zpk_gain, fil_save
import pyfda.libs.pyfda_dirs as dirs
from pyfda.libs.pyfda_lib import safe_eval, frmt2cmplx, pprint_log
from pyfda.pyfda_rc import params

from pyfda.input_widgets.input_pz_ui import Input_PZ_UI
from pyfda.input_widgets.item_delegate_pz import ItemDelegatePZ

logger = logging.getLogger(__name__)

classes = {'Input_PZ': 'P/Z'}  #: Dict containing class name : display name

class Input_PZ(QWidget):
    """
    Widget for entering, exporting / importing and saving / loading filter data
    in pole / zero format (P/Z) with gain.
    """
    sig_rx = pyqtSignal(object)  # incoming from input_tab_widgets
    sig_tx = pyqtSignal(object)  # emitted when filter has been saved

    def __init__(self, parent=None):
        super().__init__()

        self.data_changed = True  # initialize flag: filter data has been changed

        self.h_max = 1  # initial setting for maximum gain
        self.angle_char = "\u2220"
        self.pi_char = "pi" # "\u03C0" looks ugly

        self.tab_label = "P/Z"
        self.tool_tip = "Display and edit filter poles and zeros."

        self.ui = Input_PZ_UI()  # create the UI control part
        self._construct_UI()  # construct the rest of the UI

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None) -> None:
        """
        Process signals coming from sig_rx
        """
        logger.debug("SIG_RX - data_changed = %s, vis = %s\n%s",
                     self.data_changed, self.isVisible(), pprint_log(dict_sig))

        if dict_sig['id'] == id(self):
            # logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
            return

        if 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed'] == 'csv':
            self.ui.but_csv_options.setChecked(dirs.csv_options_handle is not None)
            return

        if self.isVisible():
            if 'data_changed' in dict_sig or self.data_changed:
                self.load_dict()
                self.data_changed = False
        else:
            # TODO: draw wouldn't be necessary for 'view_changed', only update view
            if 'data_changed' in dict_sig:
                self.data_changed = True

    # ------------------------------------------------------------------------------
    def _construct_UI(self) -> None:
        """
        Construct the UI from the table widget and the control part (`self.ui`),
        initialize the widget and setup signal-slot connections and event filters
        """
        self.tblPZ = QTableWidget(self, objectName="tblPZ")
        # self.tblPZ.setEditTriggers(QTableWidget.AllEditTriggers) # make everything editable
        self.tblPZ.setAlternatingRowColors(True)  # alternating row colors)

        # highlight when selected:
        self.tblPZ.horizontalHeader().setHighlightSections(True)
        self.tblPZ.horizontalHeader().setFont(self.ui.bfont)

        self.tblPZ.verticalHeader().setHighlightSections(True)
        self.tblPZ.verticalHeader().setFont(self.ui.bfont)
        self.tblPZ.setColumnCount(2)
        self.tblPZ.setItemDelegate(ItemDelegatePZ(self))

        lay_v_main = QVBoxLayout()
        # the following affects only the first widget (intended here)
        lay_v_main.setAlignment(Qt.AlignTop)
        lay_v_main.addWidget(self.ui)
        lay_v_main.addWidget(self.tblPZ)

        lay_v_main.setContentsMargins(*params['wdg_margins'])

        self.setLayout(lay_v_main)

        self.load_dict()  # initialize table from filterbroker
        self._refresh_table()  # initialize table with values

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        self.ui.sig_tx.connect(self.sig_tx)

        # ----------------------------------------------------------------------
        # LOCAL (UI) SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.ui.cmb_pz_frmt.activated.connect(self._refresh_table)
        self.ui.spn_digits.editingFinished.connect(self._refresh_table)
        self.ui.but_undo.clicked.connect(self.load_dict)

        self.ui.but_apply.clicked.connect(self._save_entries)
        self.ui.chk_gain.toggled.connect(self._normalize_gain)

        self.ui.but_del_cells.clicked.connect(self._delete_cells)
        self.ui.but_add_cells.clicked.connect(self._add_rows)
        self.ui.but_clear.clicked.connect(self._clear_table)

        self.ui.but_table_export.clicked.connect(self.export_table)
        self.ui.but_table_import.clicked.connect(self._import)

        self.ui.but_set_zero.clicked.connect(self._zero_PZ)

        self.ui.led_gain.installEventFilter(self)
        self.ui.led_h_max.installEventFilter(self)
        self.ui.led_eps.editingFinished.connect(self._set_eps)

        # ----------------------------------------------------------------------
        # self.tblPZ.itemSelectionChanged.connect(self._copy_item)
        #
        # Every time a table item is edited, call self._copy_item to copy the
        # item content to self.zpk. This is triggered by the itemChanged signal.
        # The event filter monitors the focus of the input fields.

        # signal itemChanged is also triggered programmatically,
        # itemSelectionChanged is only triggered when entering cell

    # ------------------------------------------------------------------------------
    def eventFilter(self, source: QtCore.QObject, event: QEvent) -> bool:
        """
        Filter all events generated by the QLineEdit widgets. Source and type
        of all events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (`QEvent.FocusIn`), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (`QEvent.FocusOut`), store
          current value in linear format with full precision (only if
          `spec_edited == True`) and display the stored value in selected format
        """

        if isinstance(source, QLineEdit):
            if event.type() == QEvent.FocusIn:  # 8
                self.spec_edited = False
                self._reload_entry(source)
                return True  # event processing stops here

            if event.type() == QEvent.KeyPress:
                self.spec_edited = True  # entry has been changed
                key = event.key()  # key press: 6, key release: 7
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}:  # store entry
                    self._store_entry(source)
                    self._reload_entry(source)  # display in desired format
                    return True

                if key == QtCore.Qt.Key_Escape:  # revert changes
                    self.spec_edited = False
                    self._reload_entry(source)
                    return True

            elif event.type() == QEvent.FocusOut:  # 9
                self._store_entry(source)
                self._reload_entry(source)  # display in desired format
                return True

        return super().eventFilter(source, event)

    # ------------------------------------------------------------------------------
    def _store_entry(self, source: QtCore.QObject) -> None:
        """
        When the textfield of `source` has been edited (flag `self.spec_edited` =  True),
        store it in 'target'. This is triggered by `QEvent.focusOut` or
        RETURN key.
        """
        if self.spec_edited:
            if source.objectName() == "led_gain":
                # enforce gain > 0
                self.zpk[2][0] = safe_eval(source.text(), sign='pos',
                                           alt_expr=str(self.zpk[2][0]))
            else:
                self.h_max = safe_eval(source.text(), alt_expr=str(self.h_max))

            qstyle_widget(self.ui.but_apply, 'changed')
            qstyle_widget(self.ui.but_undo, 'changed')

            self._normalize_gain()

            self.spec_edited = False  # reset flag

    # ------------------------------------------------------------------------------
    def _reload_entry(self, source: QtCore.QObject) -> None:
        """
        Reload QLineEdit with either full (has focus) or reduced precision (no focus)

        Called by eventFilter, _normalize_gain() and _refresh_table()
        """

        if len(self.zpk) == 3:  # number of rows
            pass
        elif len(self.zpk) == 2:  # k is missing in zpk:
            self.zpk.append(zeros_with_val(len(self.zpk[0])))  # add a row with k = 1
        else:
            logger.error("P/Z array 'self.zpk' has wrong number of rows = %s", len(self.zpk))
            logger.error(self.zpk)

        if source.objectName() == "led_gain":
            data = safe_eval(self.zpk[2][0], return_type='auto')
        else:
            data = self.h_max
        if not source.hasFocus():  # no focus, round the data
            source.setText(str(params['FMT'].format(data)))
        else:  # widget has focus, show data with full precision
            source.setText(str(data))

# ------------------------------------------------------------------------------
    def _normalize_gain(self) -> None:
        """
        Normalize the gain factor to either reach the selected maximum of |H(f)| or
        Do this every time a P or Z has been changed.
        Called by setModelData() and when gain / h_max radio buttons are toggled
        """
        use_gain = self.ui.chk_gain.isChecked()
        self.ui.led_gain.setEnabled(use_gain)
        self.ui.led_h_max.setEnabled(not use_gain)

        if not np.isfinite(self.zpk[2][0]):
            self.zpk[2][0] = 1.
        self.zpk[2][0] = np.real_if_close(self.zpk[2][0]).item()
        if np.iscomplex(self.zpk[2][0]):
            logger.warning("Casting complex to real for gain k!")
            self.zpk[2][0] = np.abs(self.zpk[2][0])

        if not use_gain:  # calculate necessary gain to achieve H_max
            self.h_max = safe_eval(self.ui.led_h_max.text(), alt_expr=self.h_max, sign='pos')
            self.zpk = normalize_zpk_gain(self.zpk, self.h_max)

        self._reload_entry(source=self.ui.led_gain)
        self._reload_entry(source=self.ui.led_h_max)

    # ------------------------------------------------------------------------------
    def _refresh_table_item(self, row: int, col: int) -> None:
        """
        Refresh the table item with the index `row, col` from self.zpk
        """
        item = self.tblPZ.item(row, col)
        if item:  # does item exist?
            item.setText(str(self.zpk[col][row]).strip('()'))
        else:  # no, construct it:
            self.tblPZ.setItem(row, col, QTableWidgetItem(
                  str(self.zpk[col][row]).strip('()')))
        self.tblPZ.item(row, col).setTextAlignment(Qt.AlignRight | Qt.AlignCenter)

    # ------------------------------------------------------------------------------
    def _refresh_table(self) -> None:
        """
        (Re-)Create the displayed table from self.zpk with the
        desired number format.

        TODO:
        - Update zpk[2][0]?

        Called by: load_dict(), _clear_table(), _zero_PZ(), _delete_cells(),
                add_row(), _import()
        """

        params['FMT_pz'] = int(self.ui.spn_digits.text())

        self.tblPZ.setVisible(True)

        self.ui.led_gain.setText(
            str(params['FMT'].format(safe_eval(self.zpk[2][0], return_type='auto'))))

        self.tblPZ.setHorizontalHeaderLabels(["Zeros", "Poles"])
        self.tblPZ.setRowCount(len(self.zpk[0]))

        self.tblPZ.blockSignals(True)
        for col in range(2):
            for row in range(len(self.zpk[col])):
                self._refresh_table_item(row, col)
        self.tblPZ.blockSignals(False)

        self.tblPZ.resizeColumnsToContents()
        self.tblPZ.resizeRowsToContents()
        self.tblPZ.clearSelection()

    # ------------------------------------------------------------------------------
    def load_dict(self) -> None:
        """
        Load all entries from filter dict fil[0]['zpk'] into the Zero/Pole/Gain list
        self.zpk and update the display via `self._refresh_table()`.
        The explicit np.array( ... ) statement enforces a deep copy of fil[0],
        otherwise the filter dict would be modified inadvertedly. `dtype=object`
        needs to be specified to create a numpy array from the nested lists with
        differing lengths without creating the deprecation warning

        "Creating an ndarray from ragged nested sequences (which is a list-or-tuple of
        lists-or-tuples-or ndarrays with different lengths or shapes) is deprecated."

        The filter dict fil[0]['zpk'] is a list of numpy float ndarrays for z / p / k
        values `self.zpk` is an array of float ndarrays with different lengths of
        z / p / k subarrays to allow adding / deleting items.

        Format is: [array[zeros, ...], array[poles, ...], k]
        """
        if not isinstance(fb_get('zpk'), np.ndarray):
            logger.warning("fil[0]['zpk'] is of type %s with len = %s",
                           type(fb_get('zpk')).__name__, len(fb_get('zpk')))

        zpk = list(fb_get('zpk'))

        if len(zpk) == 3:  # number of rows
            if np.isscalar(zpk[2]):
                logger.warning("Gain is scalar, converting to proper format!")
                zpk[2] = zeros_with_val(len(zpk[0]), zpk[2])  # add a row gain
            elif len(zpk[2]) != len(zpk[0]):
                zpk[2] = zeros_with_val(len(zpk[0]), zpk[2][0])
        elif len(zpk) == 2:  # k is missing in zpk:
            zpk.append(zeros_with_val(len(zpk[0])))  # add a row with k = 1
        else:
            logger.error("P/Z array 'fil[0]['zpk']' has wrong number of rows = %s", len(zpk))
            return

        if len(zpk[0]) != len(zpk[1]):
            logger.warning("fil[0]['zpk'] has differing row lengths, %s != %s",
                           len(zpk[0]), len(zpk[1]))
            return

        self.zpk = np.array(zpk)  # this enforces a deep copy and converts back to ndarray
        qstyle_widget(self.ui.but_apply, 'normal')
        qstyle_widget(self.ui.but_undo, 'normal')
        self._refresh_table()

    # ------------------------------------------------------------------------------
    def _save_entries(self) -> None:
        """
        Save the values from self.zpk to the filter PZ dict,
        the QLineEdit for setting the gain has to be treated separately.
        """
        fb_set('N', len(self.zpk[0]))
        # Switch to manual filter order and 'Manual_IIR' resp. 'Manual_FIR' filter class
        fb_set('fo', 'man')
        if np.any(self.zpk[1]):  # any non-zero poles?
            fb_set('fc', 'Manual_IIR')
        else:
            fb_set('fc', 'Manual_FIR')

        try:
            fil_save(self.zpk, 'zpk', __name__)  # save with new gain
        except (ValueError, TypeError)as e:
            # catch exception due to malformatted P/Zs:
            logger.error(
                "While saving the poles / zeros, the following error occurred:\n%s", e)

        if __name__ == '__main__':
            self.load_dict()  # only needed for stand-alone test

        # Change filter type to "Manual" and update UI in Input_Specs() ...
        self.emit({'filt_changed': 'input_coeffs'})
        # ... and update filter data and widgets
        self.emit({'data_changed': 'filter_designed'})

        qstyle_widget(self.ui.but_apply, 'normal')
        qstyle_widget(self.ui.but_undo, 'normal')

        logger.debug("b,a = %s\n\nzpk = %s\n", fb_get('ba'), pformat(fb_get('zpk')))

    # ------------------------------------------------------------------------------
    def _clear_table(self) -> None:
        """
        Clear & initialize table and zpk for two poles and zeros @ origin,
        P = Z = [0; 0], k = 1
        """
        self.zpk = np.array([[0, 0], [0, 0], [1, 0]], dtype=complex)
        self.h_max = 1.0

        qstyle_widget(self.ui.but_apply, 'changed')
        qstyle_widget(self.ui.but_undo, 'changed')
        self._refresh_table()

    # ------------------------------------------------------------------------------
    def _get_selected(self, table: QTableWidget) -> dict:
        """
        get selected cells and return:
        - indices of selected cells
        - selected colums
        - selected rows
        - current cell
        """
        idx = []
        for _ in table.selectedItems():
            idx.append([_.column(), _.row(), ])
        cols = sorted(list({i[0] for i in idx}))
        rows = sorted(list({i[1] for i in idx}))
        cur = (table.currentColumn(), table.currentRow())
        # cur_idx_row = table.currentIndex().row()

        return {'idx': idx, 'cols': cols, 'rows': rows, 'cur': cur}

    # ------------------------------------------------------------------------------
    def _delete_cells(self) -> None:
        """
        Delete all selected elements by:
        - determining the indices of all selected cells in the P and Z arrays
        - deleting elements with those indices
        - equalizing the lengths of P and Z array by appending the required
          number of zeros.
        - deleting all P/Z pairs
        Finally, the table is refreshed from self.zpk.
        """
        sel = self._get_selected(self.tblPZ)['idx']  # get selected indices as 2D list
        sel_z = [s[1] for s in sel if s[0] == 0]  # list with sel. indices in 'Z' column
        sel_p = [s[1] for s in sel if s[0] == 1]  # list with sel. indices in 'P' column

        k = self.zpk[2][0]

        # Delete array entries with selected indices. If nothing is selected
        # (sel_z and sel_p are empty), delete the last row.
        if len(sel_z) < 1 and len(sel_p) < 1:
            sel_z = [len(self.zpk[0])-1]
            sel_p = [len(self.zpk[1])-1]
        zeros = np.delete(self.zpk[0], sel_z)
        poles = np.delete(self.zpk[1], sel_p)

        # If resulting poles and zeros are empty, re-initialize using
        # `self._clear_table()`. This also refreshes the table and marks
        # the "Save" button as changed.
        if len(zeros) == 0 and len(poles) == 0:
            self._clear_table()
        else:
            # test and equalize if P and Z array have different lengths:
            D = len(zeros) - len(poles)
            if D > 0:
                poles = np.append(poles, np.zeros(D))
            elif D < 0:
                zeros = np.append(zeros, np.zeros(-D))

            gain = zeros_with_val(max(len(poles), len(zeros)), k)

            # reconstruct array with new number of rows
            self.zpk = np.array([zeros, poles, gain])

            self._delete_PZ_pairs()
            self._normalize_gain()
            qstyle_widget(self.ui.but_apply, 'changed')
            qstyle_widget(self.ui.but_undo, 'changed')
            self._refresh_table()

    # ------------------------------------------------------------------------------
    def _add_rows(self) -> None:
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add one row.
        """
        row = self.tblPZ.currentRow()
        sel = len(self._get_selected(self.tblPZ)['rows'])

        if sel == 0:  # nothing selected ->
            sel = 1  # add at least one row ...
            row = len(self.zpk[0]) # ... at the bottom

        self.zpk = np.insert(self.zpk, row, np.zeros((sel, 1)), axis=1)

        self._refresh_table()

    # ------------------------------------------------------------------------------
    def _set_eps(self) -> None:
        """
        Set tolerance value
        """
        self.ui.eps = safe_eval(self.ui.led_eps.text(), alt_expr=self.ui.eps, sign='pos')
        self.ui.led_eps.setText(str(self.ui.eps))

    # ------------------------------------------------------------------------------
    def _zero_PZ(self) -> None:
        """
        Set all P/Zs = 0 with a magnitude less than eps and delete P/Z pairs
        afterwards.
        """
        changed = False
        targ_val = 0.
        test_val = 0
        sel = self._get_selected(self.tblPZ)['idx']  # get all selected indices

        if not sel:  # nothing selected, check all cells
            z_close = np.logical_and(
                np.isclose(self.zpk[0], test_val, rtol=0, atol=self.ui.eps),
                (self.zpk[0] != targ_val))
            p_close = np.logical_and(
                np.isclose(self.zpk[1], test_val, rtol=0, atol=self.ui.eps),
                (self.zpk[1] != targ_val))
            if z_close.any():
                self.zpk[0] = np.where(z_close, targ_val, self.zpk[0])
                changed = True
            if p_close.any():
                self.zpk[1] = np.where(p_close, targ_val, self.zpk[1])
                changed = True
        else:
            for i in sel:  # check only selected cells
                if np.logical_and(
                    np.isclose(self.zpk[i[0]][i[1]], test_val, rtol=0, atol=self.ui.eps),
                        (self.zpk[i[0]][i[1]] != targ_val)):
                    self.zpk[i[0]][i[1]] = targ_val
                    changed = True

        self._delete_PZ_pairs()
        self._normalize_gain()
        if changed:
            qstyle_widget(self.ui.but_apply, 'changed')  # mark apply and undo
            qstyle_widget(self.ui.but_undo, 'changed')   # buttons as changed
        self._refresh_table()

    # ------------------------------------------------------------------------------
    def _delete_PZ_pairs(self) -> None:
        """
        Find and delete pairs of poles and zeros in self.zpk
        The filter dict and the table have to be updated afterwards.
        """
        zeros = self.zpk[0]
        poles = self.zpk[1]
        gain = self.zpk[2]
        changed = False
        for z in range(len(zeros)-1, -1, -1):  # start at the bottom
            for p in range(len(poles)-1, -1, -1):
                if np.isclose(zeros[z], poles[p], rtol=0, atol=self.ui.eps):
                    # zeros / poles to be deleted have values != 0, mark as changed
                    if zeros[z] != 0 and poles[p] != 0:
                        changed = True
                    zeros = np.delete(zeros, z)
                    poles = np.delete(poles, p)
                    gain = np.delete(gain, -1)  # delete last element (= 0)
                    break  # ... out of loop

        if len(zeros) < 1:  # no P / Z, add 1 row
            zeros = [0]
            poles = [0]
            gain = [1]

        self.zpk = np.array((zeros, poles, gain))

        if changed:
            qstyle_widget(self.ui.but_apply, 'changed')  # mark apply and undo
            qstyle_widget(self.ui.but_undo, 'changed')   # buttons as changed

    # ------------------------------------------------------------------------------
    def cmplx2frmt(self, text: str, places: int = -1) -> str:
        """
        Convert number "text" (real or complex or string) to a string with the format
        defined by cmb_pz_frmt.

        Returns:
            str
        """
        # convert to numeric value via safe_eval:
        data = safe_eval(text, return_type='auto')
        frmt = qget_cmb_box(self.ui.cmb_pz_frmt)  # get selected format

        if places == -1:
            full_prec = True
        else:
            full_prec = False

        if frmt == 'cartesian' or not isinstance(data, complex):
            if full_prec:
                return str(data)
            return f"{data:.{places}g}"

        if frmt == 'polar_rad':
            r, phi = np.absolute(data), np.angle(data, deg=False)
            if full_prec:
                return f"{r} {self.angle_char}{phi} rad"
            return f"{r:.{places}g} {self.angle_char}{phi:.{places}g} rad"

        if frmt == 'polar_deg':
            r, phi = np.absolute(data), np.angle(data, deg=True)
            if full_prec:
                return f"{r} {self.angle_char}{phi}°"
            return f"{r:.{places}g} {self.angle_char}{phi:.{places}g}°"

        if frmt == 'polar_pi':
            r, phi = np.absolute(data), np.angle(data, deg=False) / np.pi
            if full_prec:
                return f"{r} {self.angle_char}{phi} {self.pi_char}"

            return f"{r:.{places}g} {self.angle_char}{phi:.{places}g} {self.pi_char}"

        logger.error("Unknown format %s.", frmt)
        return str(data)

    # --------------------------------------------------------------------------
    def export_table(self) -> None:
        """
        Export data from coefficient table `self.tblCoeff` to clipboard in CSV format
        or to file using a selected format
        """
        text = qtable2csv(
            self.tblPZ, self.zpk, zpk=True, formatted=self.ui.but_format.checked)
        if self.ui.load_save_clipboard:  # data to clipboard:
            dirs.clipboard.setText(text)
        else:
            # pass csv formatted text, key for accessing data in ``*.npz`` file or
            # Matlab workspace (``*.mat``) and a title for the file export dialog
            export_fil_data(self, text, 'zpk', title="Export Poles / Zeros",
                            formatted=self.ui.but_format.checked)
    # --------------------------------------------------------------------------
    def _import(self) -> None:
        """
        Import data from clipboard / file and copy it to `self.zpk` as array of complex
        # TODO: More checks for swapped row <-> col, single values, wrong data type ...
        """
        # Get data as ndarray of str:

        if self.ui.load_save_clipboard:  # data from clipboard
            data_str = file2array(
                "", "", 'zpk', from_clipboard=True,
                as_str = self.ui.but_format.checked)
        else:  # data from file
            file_name, file_type = select_file(self, title="Import Poles / Zeros", mode="r",
                                    file_types=('csv', 'mat', 'npy', 'npz'))
            if file_name is None:  # operation cancelled or error
                return
            # file types 'csv', 'mat', 'npy', 'npz'
            data_str = file2array(
                file_name, file_type, 'zpk',
                from_clipboard=False,
                as_str = self.ui.but_format.checked)

        if data_str is None:  # file operation has been aborted
            return

        conv = frmt2cmplx  # routine for converting to cartesian coordinates

        if np.ndim(data_str) > 1:
            num_cols, num_rows = np.shape(data_str)
            orientation_horiz = num_cols > num_rows  # need to transpose data
        elif np.ndim(data_str) == 1:
            num_rows = len(data_str)
            num_cols = 1
            orientation_horiz = False
        else:
            logger.error("Imported data is a single value or None.")
            return
        logger.info("_import: c x r = %d x %d", num_cols, num_rows)
        zpk = [[], [], []]

        if orientation_horiz:
            for c in range(num_cols):
                zpk[0].append(conv(data_str[c][0]))
                if num_rows > 1:
                    zpk[1].append(conv(data_str[c][1]))
                if num_rows > 2:
                    zpk[2].append(conv(data_str[c][2]))
        else:
            zpk[0] = [conv(s) for s in data_str[0]]
            if num_cols == 1:
                zpk[1] = [1]
            elif num_cols > 1:
                zpk[1] = [conv(s) for s in data_str[1]]
            if num_cols > 2:
                zpk[2] = [conv(s) for s in data_str[2]]

        # sanitize zpk; test and equalize if P and Z lists have different lengths,
        # convert gain to a vector wth same length as zpk[0]
        zpk_arr = zpk2array(zpk)
        if type(zpk_arr) is not np.ndarray:  # an error has ocurred, error string is returned
            logger.error(zpk_arr)
            qstyle_widget(self.ui.but_apply, 'error')
            qstyle_widget(self.ui.but_undo, 'changed')  #
        else:
            self.zpk = zpk_arr
            qstyle_widget(self.ui.but_apply, 'changed')
            qstyle_widget(self.ui.but_undo, 'changed')  #
            self._refresh_table()

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.input_pz`
    from pyfda import pyfda_rc as rc
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.QSS_RC)
    mainw = Input_PZ()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
