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
import sys
import re
from pprint import pformat

from pyfda.libs.compat import (
    QtCore, QWidget, QLineEdit, pyqtSignal, QEvent, QIcon,
    QBrush, QColor, QSize, QStyledItemDelegate, QApplication,
    QTableWidget, QTableWidgetItem, Qt, QVBoxLayout)

from pyfda.libs.pyfda_qt_lib import qget_cmb_box, qstyle_widget
from pyfda.libs.pyfda_io_lib import qtable2csv, data2array, export_fil_data
from pyfda.libs.pyfda_sig_lib import zeros_with_val, zpk2array

import numpy as np
from scipy.signal import freqz, zpk2tf

import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals
from pyfda.libs.pyfda_lib import qstr, fil_save, safe_eval, pprint_log
from pyfda.pyfda_rc import params
from pyfda.input_widgets.input_pz_ui import Input_PZ_UI

import logging
logger = logging.getLogger(__name__)

classes = {'Input_PZ': 'P/Z'}  #: Dict containing class name : display name


class ItemDelegate(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.

    - `displayText()` displays the data stored in the table in various number formats

    - `createEditor()` creates a line edit instance for editing table entries

    - `setEditorData()` pass data with full precision and in selected format to editor

    - `setModelData()` pass edited data back to model (`self.zpk`)
    """
    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (Input_PZ)
        """
        super(ItemDelegate, self).__init__(parent)
        self.parent = parent  # instance of the parent (not the base) class

    # --------------------------------------------------------------------------
    def initStyleOption(self, option, index):
        """
        Initialize `option` with the values using the `index` index. All items are
        passed to the original `initStyleOption()` which then calls `displayText()`.

        Afterwards, check whether a pole (index.column() == 1 )is outside the
        UC and color item background accordingly (not implemented yet).
        """
        # continue with the original `initStyleOption()` and call displayText()
        super(ItemDelegate, self).initStyleOption(option, index)
        # test for poles with magnitude > 1
        if index.column() == 1 and False:
            # Color item backgrounds with poles outside the UC red
            option.backgroundBrush = QBrush(Qt.SolidPattern)
            option.backgroundBrush.setColor(QColor(100, 0, 0, 80))

    # --------------------------------------------------------------------------
    def text(self, item):
        """
        Return item text as string transformed by self.displayText()
        """
        return qstr(self.displayText(item.text(), QtCore.QLocale()))

    # --------------------------------------------------------------------------
    def displayText(self, text, locale):
        """
        Display `text` with selected format (cartesian / polar)
        and number of places

        text:   string / QVariant from QTableWidget to be rendered
        locale: locale for the text
        """
        return self.parent.cmplx2frmt(text, places=params['FMT_pz'])

    # --------------------------------------------------------------------------
    def createEditor(self, parent, options, index):
        """
        Neet to set editor explicitly, otherwise QDoubleSpinBox instance is
        created when space is not sufficient?!
        editor:  instance of e.g. QLineEdit (default)
        index:   instance of QModelIndex
        options: instance of QStyleOptionViewItemV4
        """
        line_edit = QLineEdit(parent)
        H = int(round(line_edit.sizeHint().height()))
        W = int(round(line_edit.sizeHint().width()))
        line_edit.setMinimumSize(QSize(W, H))  # (160, 25));

        return line_edit

    # --------------------------------------------------------------------------
    def setEditorData(self, editor, index):
        """
        Pass the data to be edited to the editor:
        - retrieve data with full accuracy (`places=-1`) from `zpk` (in float format)
        - represent it in the selected format (Cartesian, polar, ...)

        editor: instance of e.g. QLineEdit
        index:  instance of QModelIndex
        """
        data = self.parent.zpk[index.column()][index.row()]
        data_str = self.parent.cmplx2frmt(data, places=-1)
        editor.setText(data_str)

    # --------------------------------------------------------------------------
    def setModelData(self, editor, model, index):
        """
        When editor has finished, read the updated data from the editor,
        convert it to complex format and store it in both the model
        (= QTableWidget) and in `zpk`. Finally, refresh the table item to
        display it in the selected format (via `to be defined`) and normalize
        the gain.

        editor: instance of e.g. QLineEdit
        model:  instance of QAbstractTableModel
        index:  instance of QModelIndex
        """

        # check for different editor environments if needed and provide a default:
#        if isinstance(editor, QtGui.QTextEdit):
#            model.setData(index, editor.toPlainText())
#        elif isinstance(editor, QComboBox):
#            model.setData(index, editor.currentText())
#        else:
#            super(ItemDelegate, self).setModelData(editor, model, index)

        # convert entered string to complex, pass the old value as default
        data = self.parent.frmt2cmplx(qstr(editor.text()),
                                      self.parent.zpk[index.column()][index.row()])
        model.setData(index, data)                          # store in QTableWidget
        self.parent.zpk[index.column()][index.row()] = data  # and in self.ba
        qstyle_widget(self.parent.ui.butSave, 'changed')
        self.parent._refresh_table_item(index.row(), index.column())  # refresh table entry
        self.parent._normalize_gain()  # recalculate gain

# ===================================================================================
class Input_PZ(QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    sig_rx = pyqtSignal(object)  # incoming from input_tab_widgets
    sig_tx = pyqtSignal(object)  # emitted when filter has been saved
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None):
        super(Input_PZ, self).__init__(parent)

        self.data_changed = True  # initialize flag: filter data has been changed

        self.Hmax_last = 1  # initial setting for maximum gain
        self.angle_char = "\u2220"
        self.pi_char = "pi" # "\u03C0" looks ugly

        self.tab_label = "P/Z"
        self.tool_tip = "Display and edit filter poles and zeros."

        self.ui = Input_PZ_UI(self)  # create the UI control part
        self.norm_last = qget_cmb_box(self.ui.cmbNorm, data=False)  # initial setting of cmbNorm
        self._construct_UI()  # construct the rest of the UI

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        # logger.debug(f"SIG_RX - data_changed = {self.data_changed}, vis = "
        #              f"{self.isVisible()}\n{pprint_log(dict_sig)}")

        if dict_sig['id'] == id(self):
            # logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
            return

        if 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed'] == 'csv':
            self.ui._set_load_save_icons()
            # self.emit(dict_sig)

        elif self.isVisible():
            if 'data_changed' in dict_sig or self.data_changed:
                self.load_dict()
                self.data_changed = False
        else:
            # TODO: draw wouldn't be necessary for 'view_changed', only update view
            if 'data_changed' in dict_sig:
                self.data_changed = True

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Construct the UI from the table widget and the control part (`self.ui`),
        initialize the widget and setup signal-slot connections and event filters
        """
        self.tblPZ = QTableWidget(self, objectName="tblPZ")
#        self.tblPZ.setEditTriggers(QTableWidget.AllEditTriggers) # make everything editable
        self.tblPZ.setAlternatingRowColors(True)  # alternating row colors)

        # highlight when selected:
        self.tblPZ.horizontalHeader().setHighlightSections(True)
        self.tblPZ.horizontalHeader().setFont(self.ui.bfont)

        self.tblPZ.verticalHeader().setHighlightSections(True)
        self.tblPZ.verticalHeader().setFont(self.ui.bfont)
        self.tblPZ.setColumnCount(2)
        self.tblPZ.setItemDelegate(ItemDelegate(self))

        layVMain = QVBoxLayout()
        # the following affects only the first widget (intended here)
        layVMain.setAlignment(Qt.AlignTop)
        layVMain.addWidget(self.ui)
        layVMain.addWidget(self.tblPZ)

        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

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
        self.ui.cmbPZFrmt.activated.connect(self._refresh_table)
        self.ui.spnDigits.editingFinished.connect(self._refresh_table)
        self.ui.butLoad.clicked.connect(self.load_dict)

        self.ui.butSave.clicked.connect(self._save_entries)
        self.ui.cmbNorm.activated.connect(self._normalize_gain)

        self.ui.butDelCells.clicked.connect(self._delete_cells)
        self.ui.butAddCells.clicked.connect(self._add_rows)
        self.ui.butClear.clicked.connect(self._clear_table)

        self.ui.butFromTable.clicked.connect(self.export_table)
        self.ui.butToTable.clicked.connect(self._import)

        self.ui.butSetZero.clicked.connect(self._zero_PZ)

        self.ui.ledGain.installEventFilter(self)
        self.ui.ledEps.editingFinished.connect(self._set_eps)

        # ----------------------------------------------------------------------
        # self.tblPZ.itemSelectionChanged.connect(self._copy_item)
        #
        # Every time a table item is edited, call self._copy_item to copy the
        # item content to self.zpk. This is triggered by the itemChanged signal.
        # The event filter monitors the focus of the input fields.

        # signal itemChanged is also triggered programmatically,
        # itemSelectionChanged is only triggered when entering cell

    # ------------------------------------------------------------------------------
    def eventFilter(self, source, event):
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
                self._restore_gain(source)
                return True  # event processing stops here

            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True  # entry has been changed
                key = event.key()  # key press: 6, key release: 7
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}:  # store entry
                    self._store_gain(source)
                    self._restore_gain(source)  # display in desired format
                    return True

                elif key == QtCore.Qt.Key_Escape:  # revert changes
                    self.spec_edited = False
                    self._restore_gain(source)
                    return True

            elif event.type() == QEvent.FocusOut:  # 9
                self._store_gain(source)
                self._restore_gain(source)  # display in desired format
                return True

        return super(Input_PZ, self).eventFilter(source, event)

    # ------------------------------------------------------------------------------
    def _store_gain(self, source):
        """
        When the textfield of `source` has been edited (flag `self.spec_edited` =  True),
        store it in the shadow dict. This is triggered by `QEvent.focusOut` or
        RETURN key.
        """
        if self.spec_edited:
            self.zpk[2][0] = safe_eval(source.text(), alt_expr=str(self.zpk[2][0]))
            qstyle_widget(self.ui.butSave, 'changed')
            self.spec_edited = False  # reset flag

# ------------------------------------------------------------------------------
    def _normalize_gain(self):
        """
        Normalize the gain factor so that the maximum of |H(f)| stays 1 or a
        previously stored maximum value of |H(f)|. Do this every time a P or Z
        has been changed.
        Called by setModelData() and when cmbNorm is activated

        """
        norm = qget_cmb_box(self.ui.cmbNorm, data=False)
        self.ui.ledGain.setEnabled(norm == 'None')
        if norm != self.norm_last:
            qstyle_widget(self.ui.butSave, 'changed')
        if not np.isfinite(self.zpk[2][0]):
            self.zpk[2][0] = 1.
        self.zpk[2][0] = np.real_if_close(self.zpk[2][0]).item()
        if np.iscomplex(self.zpk[2][0]):
            logger.warning("Casting complex to real for gain k!")
            self.zpk[2][0] = np.abs(self.zpk[2][0])

        if norm != "None":
            b, a = zpk2tf(self.zpk[0], self.zpk[1], self.zpk[2][0])
            [w, H] = freqz(b, a, whole=True)
            Hmax = max(abs(H))
            if not np.isfinite(Hmax) or Hmax > 1e4 or Hmax < 1e-4:
                Hmax = 1.
            if norm == "1":
                self.zpk[2][0] = self.zpk[2][0] / Hmax  # normalize to 1
            elif norm == "Max":
                if norm != self.norm_last:  # setting has been changed -> 'Max'
                    self.Hmax_last = Hmax  # use current design to set Hmax_last
                self.zpk[2][0] = self.zpk[2][0] / Hmax * self.Hmax_last
        self.norm_last = norm  # store current setting of combobox

        self._restore_gain()

    # ------------------------------------------------------------------------------
    def _restore_gain(self, source=None):
        """
        Update QLineEdit with either full (has focus) or reduced precision (no focus)

        Called by eventFilter, _normalize_gain() and _refresh_table()
        """

        # if self.ui.butEnable.isChecked():
        if len(self.zpk) == 3:  # number of rows
            pass
        elif len(self.zpk) == 2:  # k is missing in zpk:
            self.zpk.append(zeros_with_val(len(self.zpk[0])))  # add a row with k = 1
        else:
            logger.error(f"P/Z array 'self.zpk' has wrong number of rows = {len(self.zpk)}")
            logger.error(self.zpk)

        k = safe_eval(self.zpk[2][0], return_type='auto')

        if not self.ui.ledGain.hasFocus():  # no focus, round the gain
            self.ui.ledGain.setText(str(params['FMT'].format(k)))
        else:  # widget has focus, show gain with full precision
            self.ui.ledGain.setText(str(k))

    # ------------------------------------------------------------------------------
    def _refresh_table_item(self, row, col):
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
    def _refresh_table(self):
        """
        (Re-)Create the displayed table from self.zpk with the
        desired number format.

        TODO:
        - Update zpk[2][0]?
        - Remove butEnable part

        Called by: load_dict(), _clear_table(), _zero_PZ(), _delete_cells(),
                add_row(), _import()
        """

        params['FMT_pz'] = int(self.ui.spnDigits.text())

        # self.tblPZ.setVisible(self.ui.butEnable.isChecked())
        self.tblPZ.setVisible(True)

        if True: # self.ui.butEnable.isChecked():

            # self.ui.butEnable.setIcon(QIcon(':/circle-check.svg'))

            self._restore_gain()

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

        # else:  # disable widgets
        #     self.ui.butEnable.setIcon(QIcon(':/circle-x.svg'))

    # ------------------------------------------------------------------------------
    def load_dict(self):
        """
        Load all entries from filter dict fb.fil[0]['zpk'] into the Zero/Pole/Gain list
        self.zpk and update the display via `self._refresh_table()`.
        The explicit np.array( ... ) statement enforces a deep copy of fb.fil[0],
        otherwise the filter dict would be modified inadvertedly. `dtype=object`
        needs to be specified to create a numpy array from the nested lists with
        differing lengths without creating the deprecation warning

        "Creating an ndarray from ragged nested sequences (which is a list-or-tuple of
        lists-or-tuples-or ndarrays with different lengths or shapes) is deprecated."

        The filter dict fb.fil[0]['zpk'] is a list of numpy float ndarrays for z / p / k
        values `self.zpk` is an array of float ndarrays with different lengths of
        z / p / k subarrays to allow adding / deleting items.

        Format is: [array[zeros, ...], array[poles, ...], k]
        """
        if not type(fb.fil[0]['zpk']) is np.ndarray:
            logger.warning(f"fb.fil[0]['zpk'] is of type {type(fb.fil[0]['zpk'])} "
                           f"with len = {len(fb.fil[0]['zpk'])}")

        zpk = list(fb.fil[0]['zpk']).copy()

        if len(zpk) == 3:  # number of rows
            if np.isscalar(zpk[2]):
                logger.warning("Gain is scalar, converting to proper format!")
                zpk[2] = zeros_with_val(len(zpk[0]), zpk[2])  # add a row gain
            elif len(zpk[2]) != len(zpk[0]):
                zpk[2] = zeros_with_val(len(zpk[0]), zpk[2][0])
        elif len(zpk) == 2:  # k is missing in zpk:
            zpk.append(zeros_with_val(len(zpk[0])))  # add a row with k = 1
        else:
            logger.error("P/Z array 'fb.fil[0]['zpk']' has wrong number of "
                         f"rows = {len(zpk)}")
            logger.error(zpk)
            return

        if len(zpk[0]) != len(zpk[1]):
            logger.warning("fb.fil[0]['zpk'] has differing row lengths, "
                           f"{len(fb.fil[0]['zpk'][0])} != {len(fb.fil[0]['zpk'][1])}")
            return
        # logger.warning(f"New shape (zpk) = {np.shape(zpk)}")
        self.zpk = np.array(zpk)  # this enforces a deep copy
        qstyle_widget(self.ui.butSave, 'normal')
        self._refresh_table()

    # ------------------------------------------------------------------------------
    def _save_entries(self):
        """
        Save the values from self.zpk to the filter PZ dict,
        the QLineEdit for setting the gain has to be treated separately.
        """
        fb.fil[0]['N'] = len(self.zpk[0])
        if np.any(self.zpk[1]):  # any non-zero poles?
            fb.fil[0]['fc'] = 'Manual_IIR'
        else:
            fb.fil[0]['fc'] = 'Manual_FIR'

        try:
            fil_save(fb.fil[0], self.zpk, 'zpk', __name__)  # save with new gain
        except Exception as e:
            # catch exception due to malformatted P/Zs:
            logger.error("While saving the poles / zeros, "
                         "the following error occurred:\n{0}".format(e))

        if __name__ == '__main__':
            self.load_dict()  # only needed for stand-alone test

        self.emit({'data_changed': 'input_pz'})
        # -> input_tab_widgets

        qstyle_widget(self.ui.butSave, 'normal')

        logger.debug(f"b,a = {fb.fil[0]['ba']}\n\n"
                     f"zpk = {pformat(fb.fil[0]['zpk'])}\n")

    # ------------------------------------------------------------------------------
    def _clear_table(self):
        """
        Clear & initialize table and zpk for two poles and zeros @ origin,
        P = Z = [0; 0], k = 1
        """
        self.zpk = np.array([[0, 0], [0, 0], [1, 0]], dtype=complex)
        self.Hmax_last = 1.0

        qstyle_widget(self.ui.butSave, 'changed')
        self._refresh_table()

    # ------------------------------------------------------------------------------
    def _get_selected(self, table):
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
    def _delete_cells(self):
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
            qstyle_widget(self.ui.butSave, 'changed')
            self._refresh_table()

    # ------------------------------------------------------------------------------
    def _add_rows(self):
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
    def _set_eps(self):
        """
        Set tolerance value
        """
        self.ui.eps = safe_eval(self.ui.ledEps.text(), alt_expr=self.ui.eps, sign='pos')
        self.ui.ledEps.setText(str(self.ui.eps))

    # ------------------------------------------------------------------------------
    def _zero_PZ(self):
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
            qstyle_widget(self.ui.butSave, 'changed')  # mark save button as changed
        self._refresh_table()

    # ------------------------------------------------------------------------------
    def _delete_PZ_pairs(self):
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
            qstyle_widget(self.ui.butSave, 'changed')  # mark save button as changed

    # ------------------------------------------------------------------------------
    def cmplx2frmt(self, text, places=-1):
        """
        Convert number "text" (real or complex or string) to the format defined
        by cmbPZFrmt.

        Returns:
            string
        """
        # convert to "normal" string and prettify via safe_eval:
        data = safe_eval(text, return_type='auto')
        frmt = qget_cmb_box(self.ui.cmbPZFrmt)  # get selected format
        # logger.warning(f"{text} -> {data}")
        if places == -1:
            full_prec = True
        else:
            full_prec = False

        if frmt == 'cartesian' or not (type(data) == complex):
            if full_prec:
                return "{0}".format(data)
            else:
                return "{0:.{plcs}g}".format(data, plcs=places)

        elif frmt == 'polar_rad':
            r, phi = np.absolute(data), np.angle(data, deg=False)
            if full_prec:
                return f"{r} {self.angle_char}{phi} rad"
            else:
                return "{r:.{plcs}g} {angle_char}{p:.{plcs}g} rad"\
                    .format(r=r, p=phi, plcs=places, angle_char=self.angle_char)

        elif frmt == 'polar_deg':
            r, phi = np.absolute(data), np.angle(data, deg=True)
            if full_prec:
                return f"{r} {self.angle_char}{phi}°"
            else:
                return "{r:.{plcs}g} {angle_char}{p:.{plcs}g}°"\
                    .format(r=r, p=phi, plcs=places, angle_char=self.angle_char)

        elif frmt == 'polar_pi':
            r, phi = np.absolute(data), np.angle(data, deg=False) / np.pi
            if full_prec:
                return f"{r} {self.angle_char}{phi} {self.pi_char}"
            else:
                return "{r:.{plcs}g} {angle_char}{p:.{plcs}g} {pi_char}"\
                    .format(r=r, p=phi, plcs=places, angle_char=self.angle_char,
                            pi_char=self.pi_char)

        else:
            logger.error("Unknown format {0}.".format(frmt))

    # ------------------------------------------------------------------------------
    def frmt2cmplx(self, string: str, default: float = 0.) -> complex:
        """
        Convert string to real or complex, try to find out the format (cartesian,
        polar with various angle formats)
        """
        def str2angle_rad(string: str) -> float:
            """
            Try to convert `string` to a corresponding angle in rad
                Use the following regular expressions:
                - '$' : matches the end of the string
                - '|' : combine multiple matches with OR
            """
            if re.search('°$|o$', string):
                # "°" in polar_str[1] or "o" in polar_str[1]:
                scale = np.pi / 180.  # angle in degrees
                string = re.sub('o|°', '', string)
            elif re.search('π$|pi$|p$', string):
                scale = np.pi
                string = re.sub('π$|pi$|p$', '', string)
            else:
                # this case also works when angle is a pure number
                scale = 1.  # angle in rad
                string = re.sub('rad$|r$', '', string)

            phi = safe_eval(string) * scale
            return phi
        # -------------------------------------------

        string = str(string).replace(" ", "")  # remove all blanks
        if qget_cmb_box(self.ui.cmbPZFrmt) == 'cartesian':
            return safe_eval(string, default, return_type='auto')
        else:
            # convert angle character to "<" and try to split string at "*<"
            # When the "<" character is not found, this returns a list with 1 item!
            polar_str = string.replace(self.angle_char, '<').replace('*', '')
            polar_str = polar_str.split('<', 1)

            if len(polar_str) == 2 and polar_str[0] == "": # pure angle
                phi = str2angle_rad(polar_str[1])
                x = np.cos(phi)
                y = np.sin(phi)
            elif len(polar_str) == 1:  # no angle found; real / imag / cartesian complex
                r = safe_eval(string, default, return_type='auto')
                x = r.real
                y = r.imag
            else:  # r and angle found
                r = safe_eval(polar_str[0], sign='pos')
                phi = str2angle_rad(polar_str[1])

                x = r * np.cos(phi)
                y = r * np.sin(phi)

            if safe_eval.err > 0:
                x = default.real
                y = default.imag
                logger.warning(f"Expression {string} could not be evaluated.")
            return x + 1j * y

    # --------------------------------------------------------------------------
    def export_table(self):
        """
        Export data from coefficient table `self.tblCoeff` to clipboard in CSV format
        or to file using a selected format
        """
        text = qtable2csv(
            self.tblPZ, self.zpk, zpk=True, formatted=self.ui.but_format.isChecked())
        if params['CSV']['destination'] == 'clipboard':
            # clipboard is selected as export target
            fb.clipboard.setText(text)
        else:
            # pass csv formatted text, key for accessing data in ``*.npz`` file or
            # Matlab workspace (``*.mat``) and a title for the file export dialog
            export_fil_data(self, text, 'zpk', title="Export Poles / Zeros")
    # --------------------------------------------------------------------------
    def _import(self):
        """
        Import data from clipboard / file and copy it to `self.zpk` as array of complex
        # TODO: More checks for swapped row <-> col, single values, wrong data type ...
        """
        data_str = data2array(self, 'zpk', title="Import Poles / Zeros ",
                              as_str = self.ui.but_format.isChecked())
        if data_str is None:  # file operation has been aborted
            return

        conv = self.frmt2cmplx  # routine for converting to cartesian coordinates

        if np.ndim(data_str) > 1:
            num_cols, num_rows = np.shape(data_str)
            orientation_horiz = num_cols > num_rows  # need to transpose data
        elif np.ndim(data_str) == 1:
            num_rows = len(data_str)
            num_cols = 1
            orientation_horiz = False
        else:
            logger.error("Imported data is a single value or None.")
            return None
        logger.info(f"_import: c x r = {num_cols} x {num_rows}")
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
        if not type(zpk_arr) is np.ndarray:  # an error has ocurred, error string is returned
            logger.error(zpk_arr)
            qstyle_widget(self.ui.butSave, 'error')
            return
        else:
            logger.warning(pprint_log(zpk_arr))
            self.zpk = zpk_arr
            qstyle_widget(self.ui.butSave, 'changed')
            self._refresh_table()

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.input_widgets.input_pz` """
    from pyfda import pyfda_rc as rc
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Input_PZ()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
