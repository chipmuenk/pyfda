# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter Poles and Zeros
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

import sys
from pprint import pformat

from ..compat import (QtCore, QWidget, QLineEdit, pyqtSignal, QEvent,
                      QBrush, QColor, QSize, QStyledItemDelegate, QApplication,
                      QTableWidget, QTableWidgetItem, Qt, QVBoxLayout)

from pyfda.pyfda_qt_lib import (qstr, qcopy_to_clipboard, qcopy_from_clipboard,
                                qget_cmb_box)

import numpy as np
from scipy.signal import freqz, zpk2tf

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, safe_eval

from pyfda.pyfda_rc import params

from .filter_pz_ui import FilterPZ_UI

# TODO: correct scaling after insertion / deletion of cells
# TODO: display P/Z in polar or cartesian format -> display text
# TODO: order P/Z depending on frequency or magnitude
# TODO: _equalize_PZ_length?
# TODO: store / load gain (k) from / to clipboard
# TODO: Option for mirroring P/Z (w/ and without copying) along the UC or the x-axis
# TODO: Option for limiting P/Z to a selectable magnitude
# TODO: display SOS graphically

class ItemDelegate(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.

    - `displayText()` displays the data stored in the table in various number formats

    - `createEditor()` creates a line edit instance for editing table entries

    - `setEditorData()` pass data with full precision and in selected format to editor

    - `setModelData()` pass edited data back to model (`self.ba`)
    """
    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (FilterPZ)
        """
        super(ItemDelegate, self).__init__(parent)
        self.parent = parent # instance of the parent (not the base) class
        

    def initStyleOption(self, option, index):
        """
        Initialize `option` with the values using the `index` index. All items are
        passed to the original `initStyleOption()` which then calls `displayText()`.

        Afterwards, check whether a pole (index.column() == 1 )is outside the
        UC and color item background accordingly (not implemented yet).
        """
        # continue with the original `initStyleOption()` and call displayText()
        super(ItemDelegate, self).initStyleOption(option, index)
        # test whether fixpoint conversion during displayText() created an overflow:
        if index.column() == 1 and False:
            # Color item backgrounds with pos. Overflows red
            option.backgroundBrush = QBrush(Qt.SolidPattern)
            option.backgroundBrush.setColor(QColor(100, 0, 0, 80))

    def text(self, item):
        """
        Return item text as string transformed by self.displayText()
        """
        # return qstr(item.text()) # convert to "normal" string
        return  qstr(self.displayText(item.text(), QtCore.QLocale()))

    def displayText(self, text, locale):
        """
        Display `text` with selected format (cartesian / polar - to be implemented)
        and number of places

        text:   string / QVariant from QTableWidget to be rendered
        locale: locale for the text

        """
        string = qstr(text) # convert to "normal" string

        if True:
            data = safe_eval(string, return_type='auto')
            return "{0:.{1}g}".format(data, params['FMT_pz'])
        else:
            pass

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
        line_edit.setMinimumSize(QSize(W, H)) #(160, 25));

        return line_edit


class ItemDelegateAnti(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.

    `displayText()` displays number with n_digits without sacrificing precision of
    the data stored in the table.
    """
    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (FilterPZ)
        """
        super(ItemDelegateAnti, self).__init__(parent)
        self.parent = parent # instance of the parent (not the base) class

    def displayText(self, text, locale):
        return "{:.{n_digits}g}".format(safe_eval(qstr(text), return_type='cmplx'), 
                n_digits = params['FMT_pz'])

class FilterPZ(QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """

    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal()

    def __init__(self, parent):
        super(FilterPZ, self).__init__(parent)

        self.Hmax_last = 1  # initial setting for maximum gain
        self.norm_last = "" # initial setting for previous combobox
        self.eps = 1.e-4 # tolerance value for setting P/Z to zero

        self.ui = FilterPZ_UI(self) # create the UI part with buttons etc.
        self._construct_UI() # construct the rest of the UI

    def _construct_UI(self):
        """
        Intitialize the widget
        """
        # Create clipboard instance
        self.clipboard = QApplication.clipboard()

        self.tblPZ = QTableWidget(self)
#        self.tblPZ.setEditTriggers(QTableWidget.AllEditTriggers) # make everything editable
        self.tblPZ.setAlternatingRowColors(True) # alternating row colors)
        self.tblPZ.setObjectName("tblPZ")

        self.tblPZ.horizontalHeader().setHighlightSections(True) # highlight when selected
        self.tblPZ.horizontalHeader().setFont(self.ui.bfont)

        self.tblPZ.verticalHeader().setHighlightSections(True)
        self.tblPZ.verticalHeader().setFont(self.ui.bfont)
        self.tblPZ.setColumnCount(2)
        self.tblPZ.setItemDelegate(ItemDelegate(self))

#       Table of antiCausal Zeros/Poles (for now not editable)
        self.anti   = False 
        self.tblPZA = QTableWidget(self)
        self.tblPZA.setAlternatingRowColors(True) # alternating row colors)
        self.tblPZA.setObjectName("tblPZA")

        self.tblPZA.horizontalHeader().setHighlightSections(True) # highlight when selected
        self.tblPZA.horizontalHeader().setFont(self.ui.bfont)

        self.tblPZA.verticalHeader().setHighlightSections(True)
        self.tblPZA.verticalHeader().setFont(self.ui.bfont)
        self.tblPZA.setColumnCount(2)
        self.tblPZA.setItemDelegate(ItemDelegateAnti(self))


        layVMain = QVBoxLayout()
        layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addWidget(self.ui)
        layVMain.addWidget(self.tblPZ)
        layVMain.addWidget(self.tblPZA)

        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        self.load_dict() # initialize table from filterbroker
        self._refresh_table()

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.ui.spnDigits.editingFinished.connect(self._refresh_table)
        self.ui.butLoad.clicked.connect(self.load_dict)
        self.ui.butEnable.clicked.connect(self.load_dict)

        self.ui.butSave.clicked.connect(self._save_entries)

        self.ui.butDelCells.clicked.connect(self._delete_cells)
        self.ui.butAddCells.clicked.connect(self._add_rows)
        self.ui.butClear.clicked.connect(self._clear_table)
        
        self.ui.butToClipboard.clicked.connect(self._copy_to_clipboard)
        self.ui.butFromClipboard.clicked.connect(self._copy_from_clipboard)


        self.ui.butSetZero.clicked.connect(self._zero_PZ)
        # signal itemChanged is also triggered programmatically,
        # itemSelectionChanged is only triggered when entering cell
        # self.tblPZ.itemSelectionChanged.connect(self._copy_item)

        self.tblPZ.cellChanged.connect(self._copy_item)
        self.ui.cmbNorm.activated.connect(self._copy_item)
        
        self.ui.ledGain.installEventFilter(self)
        self.ui.ledEps.editingFinished.connect(self._set_eps)
        #----------------------------------------------------------------------

        # Every time a table item is edited, call self._copy_item to copy the
        # item content to self.zpk. This is triggered by the itemChanged signal.
        # The event filter monitors the focus of the input fields.

#------------------------------------------------------------------------------

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
                return True # event processing stops here

            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True # entry has been changed
                key = event.key() # key press: 6, key release: 7
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}: # store entry
                    self._store_gain(source)
                    self._restore_gain(source) # display in desired format
                    return True

                elif key == QtCore.Qt.Key_Escape: # revert changes
                    self.spec_edited = False
                    self._restore_gain(source)
                    return True

            elif event.type() == QEvent.FocusOut: # 9
                self._store_gain(source)
                self._restore_gain(source) # display in desired format
                return True

        return super(FilterPZ, self).eventFilter(source, event)
#------------------------------------------------------------------------------

    def _store_gain(self, source):
        """
        When the textfield of `source` has been edited (flag `self.spec_edited` =  True),
        store it in the shadow dict. This is triggered by `QEvent.focusOut` or
        RETURN key.
        """
        if self.spec_edited:
            self.zpk[2] = safe_eval(source.text(), alt_expr = str(self.zpk[2]))
            self.spec_edited = False # reset flag

#------------------------------------------------------------------------------
    def _normalize_gain(self):
        """
        Normalize the gain factor so that the maximum of |H(f)| stays 1 or a
        previously stored maximum value of |H(f)|. Do this every time a P or Z
        has been changed.

        Called by _copy_item()
        """
        if not np.isfinite(self.zpk[2]):
            self.zpk[2] = 1.
        self.zpk[2] = np.real_if_close(self.zpk[2])
        if np.iscomplex(self.zpk[2]):
            logger.warning("Casting complex to real for gain k!")
            self.zpk[2] = np.abs(self.zpk[2])

        norm = self.ui.cmbNorm.currentText()
        if norm != "None":
            b, a = zpk2tf(self.zpk[0], self.zpk[1], self.zpk[2])
            [w, H] = freqz(b, a)
            Hmax = max(abs(H))
            if not np.isfinite(Hmax) or Hmax > 1e4 or Hmax < 1e-4:
                Hmax = 1.
            if norm == "1":
                self.zpk[2] = self.zpk[2] / Hmax # normalize to 1
            elif norm == "Max":
                if norm != self.norm_last: # setting has been changed -> 'Max'
                    self.Hmax_last = Hmax # use current design to set Hmax_last
                self.zpk[2] = self.zpk[2] / Hmax * self.Hmax_last
            self.norm_last = norm # store current setting of combobox

        self._restore_gain()

#------------------------------------------------------------------------------
    def _restore_gain(self, source = None):
        """
        Update QLineEdit with either full (has focus) or reduced precision (no focus)

        Called by eventFilter, _normalize_gain() and _refresh_table()
        """

        self.ui.ledGain.setVisible(self.ui.butEnable.isChecked())
        self.ui.lblGain.setVisible(self.ui.butEnable.isChecked())

        if self.ui.butEnable.isChecked():
            if len(self.zpk) == 3:
                pass
            elif len(self.zpk) == 2: # k is missing in zpk:
                self.zpk.append(1.) # use k = 1
            else:
                logger.error("P/Z list zpk has wrong length {0}".format(len(self.zpk)))
                
            if not self.ui.ledGain.hasFocus():  # no focus, round the gain
                self.ui.ledGain.setText(str(params['FMT'].format(self.zpk[2])))
            else: # widget has focus, show gain with full precision
                self.ui.ledGain.setText(str(self.zpk[2]))

#------------------------------------------------------------------------------
    def _refresh_table(self):
        """
        (Re-)Create the displayed table from self.zpk with the
        desired number format.

        TODO:
        Update zpk[2]?

        Called by _copy_item()
        """

        params['FMT_pz'] = int(self.ui.spnDigits.text())

        self.ui.ledGain.setVisible(self.ui.butEnable.isChecked())
        self.ui.lblGain.setVisible(self.ui.butEnable.isChecked())
        self.tblPZ.setVisible(self.ui.butEnable.isChecked())

        if self.ui.butEnable.isChecked():

            self._restore_gain()

            self.tblPZ.setHorizontalHeaderLabels(["Zeros", "Poles"])
            self.tblPZ.setRowCount(max(len(self.zpk[0]),len(self.zpk[1])))

            self.tblPZ.blockSignals(True)
            for col in range(2):
                for row in range(len(self.zpk[col])):
                    # set table item from self.zpk and strip '()' of complex numbers
                    item = self.tblPZ.item(row, col)
                    if item: # does item exist?
                        item.setText(str(self.zpk[col][row]).strip('()'))
                    else: # no, construct it:
                        self.tblPZ.setItem(row,col,QTableWidgetItem(
                              str(self.zpk[col][row]).strip('()')))
            self.tblPZ.blockSignals(False)

            self.tblPZ.resizeColumnsToContents()
            self.tblPZ.resizeRowsToContents()
            self.tblPZ.clearSelection()

            self.tblPZA.setVisible(self.anti) # only display anticausal P/Z when present
            #   Add antiCausals if they exist
            if self.anti:
                self.tblPZA.setHorizontalHeaderLabels(["AntiCausalZeros", "AntiCausalPoles"])
                self.tblPZA.setRowCount(max(len(self.zpkA[0]),len(self.zpkA[1])))

                self.tblPZA.blockSignals(True)
                for col in range(2):
                    for row in range(len(self.zpkA[col])):
                        # set table item from self.zpk and strip '()' of complex numbers
                        item = self.tblPZA.item(row, col)
                        if item: # does item exist?
                            item.setText(str(self.zpkA[col][row]).strip('()'))
                        else: # no, construct it:
                            self.tblPZA.setItem(row,col,QTableWidgetItem(
                                  str(self.zpkA[col][row]).strip('()')))
                self.tblPZA.blockSignals(False)

                self.tblPZA.resizeColumnsToContents()
                self.tblPZA.resizeRowsToContents()
                self.tblPZA.clearSelection()


#------------------------------------------------------------------------------
    def load_dict(self):
        """
        Load all entries from filter dict fb.fil[0]['zpk'] into the shadow
        register self.zpk and update the display.
        The explicit np.array( ... ) statement enforces a deep copy of fb.fil[0],
        otherwise the filter dict would be modified inadvertedly. Enforcing the 
        type np.complex is necessary, otherwise operations creating complex 
        coefficient values (or complex user entries) create errors.

        """
        self.zpk = np.array(fb.fil[0]['zpk'])# this enforces a deep copy

        if 'zpkA' in fb.fil[0]:

            # AntiCausals are not stored as reciprocals, compute them
            self.zpkA = np.array(fb.fil[0]['zpkA'])
            self.zpkA[0] = 1./self.zpkA[0]
            self.zpkA[1] = 1./self.zpkA[1]
            self.anti = True 
        else:
            self.anti = False
        self._refresh_table()

#------------------------------------------------------------------------------
    def _copy_item(self):
        """
        Copy the value from the current table item to self.zpk and normalize /
        update the gain. This is triggered every time a table item is edited.
        When no item was selected, only the gain is updated.

        Triggered by  `tblPZ.cellChanged` and `cmbNorm.activated`

        """
        col = self.tblPZ.currentIndex().column()
        row = self.tblPZ.currentIndex().row()
        item = self.tblPZ.item(row,col)

        if item:
            if item.text() != "":
                self.zpk[col][row] = safe_eval(item.text())
            else:
                self.zpk[col][row] = 0.
        self._normalize_gain()

#------------------------------------------------------------------------------
    def _save_entries(self):
        """
        Save the values from self.zpk to the filter PZ dict,
        the QLineEdit for setting the gain has to be treated separately.
        """

        logger.debug("_save_entries called")

        fb.fil[0]['N'] = len(self.zpk[0])
        if np.any(self.zpk[1]): # any non-zero poles?
            fb.fil[0]['fc'] = 'Manual_IIR'
        else:
            fb.fil[0]['fc'] = 'Manual_FIR'

        fil_save(fb.fil[0], self.zpk, 'zpk', __name__) # save with new gain

        if __name__ == '__main__':
            self.load_dict() # only needed for stand-alone test

        self.sigFilterDesigned.emit() # -> filter_specs
        # -> input_tab_widgets -> pyfdax -> plt_tab_widgets.updateAll()

        logger.debug("b,a = %s\n\n"
            "zpk = %s\n"
            %(pformat(fb.fil[0]['ba']), pformat(fb.fil[0]['zpk'])
              ))

#------------------------------------------------------------------------------
    def _clear_table(self):
        """
        Clear & initialize table and zpk for two poles and zeros @ origin,
        P = Z = [0; 0], k = 1
        """
        self.zpk = np.array([[0, 0], [0, 0], 1])
        self.Hmax_last = 1.0
        self.anti = False

        self._refresh_table()

#------------------------------------------------------------------------------
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
        #cur_idx_row = table.currentIndex().row()

        return {'idx':idx, 'cols':cols, 'rows':rows, 'cur':cur}

#------------------------------------------------------------------------------
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
        sel = self._get_selected(self.tblPZ)['idx'] # get all selected indices
        Z = [s[1] for s in sel if s[0] == 0] # all selected indices in 'Z' column
        P = [s[1] for s in sel if s[0] == 1] # all selected indices in 'P' column

        # Delete array entries with selected indices. If nothing is selected
        # (Z and P are empty), delete the last row.
        if len(Z) < 1 and len(P) < 1:
            Z = [len(self.zpk[0])-1]
            P = [len(self.zpk[1])-1]
        self.zpk[0] = np.delete(self.zpk[0], Z)
        self.zpk[1] = np.delete(self.zpk[1], P)

        # test and equalize if P and Z array have different lengths:
        D = len(self.zpk[0]) - len(self.zpk[1])
        if D > 0:
            self.zpk[1] = np.append(self.zpk[1], np.zeros(D))
        elif D < 0:
            self.zpk[0] = np.append(self.zpk[0], np.zeros(-D))

        self._delete_PZ_pairs()
        self._refresh_table()

#------------------------------------------------------------------------------
    def _add_rows(self):
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add one row.
        """
        row = self.tblPZ.currentRow()
        sel = len(self._get_selected(self.tblPZ)['rows'])
        # TODO: evaluate and create non-contiguous selections as well?

        if sel == 0: # nothing selected ->
            sel = 1 # add at least one row ...
            row = min(len(self.zpk[0]), len(self.zpk[1])) # ... at the bottom

        self.zpk[0] = np.insert(self.zpk[0], row, np.zeros(sel))
        self.zpk[1] = np.insert(self.zpk[1], row, np.zeros(sel))

        self._refresh_table()

#------------------------------------------------------------------------------
    def _set_eps(self):
        """
        Set tolerance value 
        """
        self.eps = safe_eval(self.ui.ledEps.text(), alt_expr=self.eps, sign='pos')
        self.ui.ledEps.setText(str(self.eps))
        
#------------------------------------------------------------------------------
    def _zero_PZ(self):
        """
        Set all P/Zs = 0 with a magnitude less than eps and delete P/Z pairs
        afterwards.
        """
        sel = self._get_selected(self.tblPZ)['idx'] # get all selected indices
        if not sel:
            self.zpk[0] = self.zpk[0] * np.logical_not(
                                        np.isclose(self.zpk[0], 0., rtol=0, atol = self.eps))
            self.zpk[1] = self.zpk[1] * np.logical_not(
                                        np.isclose(self.zpk[1], 0., rtol=0, atol = self.eps))
        else:
            for i in sel:
                self.zpk[i[0]][i[1]] = self.zpk[i[0]][i[1]] * np.logical_not(
                                         np.isclose(self.zpk[i[0]][i[1]], 0., rtol=0, atol = self.eps))
        self._delete_PZ_pairs()
        self._refresh_table()

#------------------------------------------------------------------------------
    def _delete_PZ_pairs(self, eps = 0):
        """
        Find and delete pairs of poles and zeros in self.zpk
        The filter dict and the table have to be updated afterwards.
        """
        for z in range(len(self.zpk[0])-1, -1, -1): # start at the bottom
            for p in range(len(self.zpk[1])-1, -1, -1):
                if np.isclose(self.zpk[0][z], self.zpk[1][p], rtol = eps, atol = 1e-08):
                    self.zpk[0] = np.delete(self.zpk[0], z)
                    self.zpk[1] = np.delete(self.zpk[1], p)
                    break

        if len(self.zpk[0]) < 1 : # no P / Z, add 1 row
            self.zpk[0] = np.append(self.zpk[0], 0.)
            self.zpk[1] = np.append(self.zpk[1], 0.)

    #------------------------------------------------------------------------------
    def _to_cartesian(self, string):
        """
        Convert input to cartesian format depending on the setting of cmbPZFrmt
        """
        if qget_cmb_box(self.ui.cmbPZFrmt) == 'Cartesian':
            return string
        else:
            return string

    #------------------------------------------------------------------------------
    def _copy_to_clipboard(self):
        """
        Copy data from coefficient table `self.tblCoeff` to clipboard in CSV format.
        """
        qcopy_to_clipboard(self.tblPZ, self.zpk, self.clipboard)

    #------------------------------------------------------------------------------
    def _copy_from_clipboard(self):
        """
        Read data from clipboard and copy it to `self.zpk` as array of strings
        # TODO: More checks for swapped row <-> col, single values, wrong data type ...
        """
        clp_str = qcopy_from_clipboard(self.clipboard)
        
        conv = self._to_cartesian # routine for converting to cartesian coordinates

        if np.ndim(clp_str) > 1:
            num_cols, num_rows = np.shape(clp_str)
            orientation_horiz = num_cols > num_rows # need to transpose data
        elif np.ndim(clp_str) == 1:
            num_rows = len(clp_str)
            num_cols = 1
            orientation_horiz = False
        else:
            logger.error("Data from clipboard is a single value or None.")
            return None
        logger.debug("_copy_from_clipboard: c x r:", num_cols, num_rows)
        if orientation_horiz:
            self.zpk = [[],[]]
            for c in range(num_cols):
                self.zpk[0].append(conv(clp_str[c][0]))
                if num_rows > 1:
                    self.zpk[1].append(conv(clp_str[c][1]))
        else:
            self.zpk[0] = [conv(s) for s in clp_str[0]]
            if num_cols > 1:
                self.zpk[1] = [conv(s) for s in clp_str[1]]
            else:
                self.zpk[1] = [1]

        self._equalize_columns()

        self._refresh_table()

#------------------------------------------------------------------------------
    def _equalize_columns(self):
        """
        test and equalize if P and Z subarray have different lengths:
        """
        try:
            p_len = len(self.zpk[1])
        except IndexError:
            p_len = 0

        try:
            z_len = len(self.zpk[0])
        except IndexError:
            z_len = 0

        D = z_len - p_len

        if D > 0: # more zeros than poles
            self.zpk[1] = np.append(self.zpk[1], np.zeros(D))
        elif D < 0: # more poles than zeros
            self.zpk[0] = np.append(self.zpk[0], np.zeros(-D))        
#            if fb.fil[0]['ft'] == 'IIR':
#                self.zpk[0] = np.append(self.zpk[0], np.zeros(-D))
#            else:
#                self.zpk[1] = self.zpk[1][:D] # discard last D elements of a

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainw = FilterPZ(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
