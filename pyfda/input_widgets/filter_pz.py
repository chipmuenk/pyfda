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
import six
from pprint import pformat

from ..compat import (QtCore, QWidget, QLabel, QLineEdit, pyqtSignal, QFrame, QEvent,
                      QCheckBox, QPushButton, QSpinBox, QComboBox, QFont, QStyledItemDelegate,
                      QTableWidget, QTableWidgetItem, Qt, QVBoxLayout, QHBoxLayout)

import numpy as np
from scipy.signal import freqz, zpk2tf

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, safe_eval, rt_label
from pyfda.pyfda_rc import params

# TODO: correct scaling after insertion / deletion of cellsn
# TODO: display P/Z in polar or cartesian format
# TODO: order P/Z depending on frequency or magnitude
# TODO: Option for mirroring P/Z (w/ and without copying) along the UC or the x-axis
# TODO: Option for limiting P/Z to a selectable magnitude
# TODO: display SOS graphically

class ItemDelegate(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.

    `displayText()` displays number with n_digits without sacrificing precision of
    the data stored in the table.

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" e.g. in a QTableWidgetItem and converted back when
    retrieved. In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    """
    def displayText(self, text, locale):
        if not isinstance(text, six.text_type): #
            text = text.toString() # needed for Python 2, doesn't work with Py3
        return "{:.{n_digits}g}".format(safe_eval(text), n_digits = params['FMT_pz'])

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

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        """
        bfont = QFont()
        bfont.setBold(True)

        # Find which button holds the longest text:
        MaxTextlen = 0
        longestText = ""
        ButLength = 0
        butTexts = ["Add", "Delete", "Save", "Load", "Clear", "Set 0"]

        for item in butTexts:
            if len(item) > MaxTextlen:
                MaxTextlen = len(item)
                longestText = item + "mm"

        butAddRow = QPushButton(butTexts[0], self)
        ButLength = butAddRow.fontMetrics().boundingRect(longestText).width()

        self.chkPZList = QCheckBox("Show table", self)
        self.chkPZList.setChecked(True)
        self.chkPZList.setToolTip("<span>Show filter Poles / Zeros as an editable table. "
                                  "For high order systems, this might be slow. </span>")

        lblRound = QLabel("Digits = ", self)
        self.spnRound = QSpinBox(self)
        self.spnRound.setRange(0,9)
        self.spnRound.setValue(params['FMT_pz'])
        self.spnRound.setToolTip("Display d digits.")

        self.lblNorm = QLabel("Normalize", self)
        self.cmbNorm = QComboBox(self)
        self.cmbNorm.addItems(["None", "1", "Max"])
        self.cmbNorm.setToolTip("<span>Set the gain <i>k</i> so that H(f)<sub>max</sub> is "
                                "either 1 or the max. of the previous system.</span>")

        self.lblGain = QLabel(rt_label("k = "), self)
        self.ledGain = QLineEdit(self)
        self.ledGain.setToolTip("Specify gain factor <i>k</i>.")
        self.ledGain.setText(str(1.))
        self.ledGain.setObjectName("ledGain")
#        self.ledGain.setFixedSize(W8, H)
        self.ledGain.installEventFilter(self)

        self.tblPZ = QTableWidget(self)
#        self.tblPZ.setEditTriggers(QTableWidget.AllEditTriggers) # make everything editable
        self.tblPZ.setAlternatingRowColors(True) # alternating row colors)
        self.tblPZ.setObjectName("tblPZ")

        self.tblPZ.horizontalHeader().setHighlightSections(True) # highlight when selected
        self.tblPZ.horizontalHeader().setFont(bfont)

        self.tblPZ.verticalHeader().setHighlightSections(True)
        self.tblPZ.verticalHeader().setFont(bfont)
        self.tblPZ.setColumnCount(2)
        self.tblPZ.setItemDelegate(ItemDelegate(self))


        butAddRow.setToolTip("<SPAN>Select <i>N</i> existing rows "
                             "to insert <i>N</i> new rows above last selected cell. "
                             "When nothing is selected, add a row at the end.</SPAN>")
        butAddRow.setMaximumWidth(ButLength)

        butDelCell = QPushButton(butTexts[1], self)
        butDelCell.setToolTip("<span>Delete selected cell(s) from the table. "
                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
                "If nothing is selected, delete the last row.</span>")
        butDelCell.setMaximumWidth(ButLength)

        butClear = QPushButton(butTexts[4], self)
        butClear.setToolTip("Clear all entries.")
        butClear.setMaximumWidth(ButLength)

        butSave = QPushButton(butTexts[2], self)
        butSave.setToolTip("<span>Save P/Z and update all plots. "
                                "No modifications are saved before!</span>")
        butSave.setMaximumWidth(ButLength)

        butLoad = QPushButton(butTexts[3], self)
        butLoad.setToolTip("Reload P / Z.")
        butLoad.setMaximumWidth(ButLength)

        butSetZero = QPushButton(butTexts[5], self)
        butSetZero.setToolTip("<SPAN>Set selected cells = 0 when magnitude "
                            "&lt; &epsilon;. When nothing is selected, apply to "
                            "all cells.</SPAN>")
        butSetZero.setMaximumWidth(ButLength)

        self.lblEps = QLabel("for " + rt_label("&epsilon; &lt;"), self)
        self.ledSetEps = QLineEdit(self)
        self.ledSetEps.setToolTip("<SPAN>Specify tolerance.</SPAN>")
        self.ledSetEps.setText(str(1e-6))
#        self.ledSetEps.setFixedSize(W8, H)

        # ============== UI Layout =====================================
        layHChkBoxes = QHBoxLayout()
        layHChkBoxes.addWidget(self.chkPZList)
        layHChkBoxes.addStretch(1)
        layHChkBoxes.addWidget(lblRound)
        layHChkBoxes.addWidget(self.spnRound)

        layHGain = QHBoxLayout()
        layHGain.addWidget(self.lblGain)
        layHGain.addWidget(self.ledGain)
#        layHChkBoxes.addStretch(1)
        layHGain.addWidget(self.lblNorm)
        layHGain.addWidget(self.cmbNorm)
        layHGain.addStretch()

        layHButtonsPZs1 = QHBoxLayout()
        layHButtonsPZs1.addWidget(butAddRow)
        layHButtonsPZs1.addWidget(butDelCell)
        layHButtonsPZs1.addWidget(butSave)
        layHButtonsPZs1.addWidget(butLoad)
        layHButtonsPZs1.addStretch()

        layHButtonsPZs2 = QHBoxLayout()
        layHButtonsPZs2.addWidget(butClear)
        layHButtonsPZs2.addWidget(butSetZero)
        layHButtonsPZs2.addWidget(self.lblEps)
        layHButtonsPZs2.addWidget(self.ledSetEps)
        layHButtonsPZs2.addStretch()

        layVBtns = QVBoxLayout()
        layVBtns.addLayout(layHChkBoxes)
        layVBtns.addLayout(layHGain)
        layVBtns.addLayout(layHButtonsPZs1)
        layVBtns.addLayout(layHButtonsPZs2)

        # This frame encompasses all the buttons
        frmMain = QFrame(self)
        frmMain.setLayout(layVBtns)

        layVMain = QVBoxLayout()
        layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addWidget(frmMain)
        layVMain.addWidget(self.tblPZ)

        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        self.load_dict() # initialize table from filterbroker
        self._refresh_table()

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.spnRound.editingFinished.connect(self._refresh_table)
        butLoad.clicked.connect(self.load_dict)
        self.chkPZList.clicked.connect(self.load_dict)

        butSave.clicked.connect(self._save_entries)

        butDelCell.clicked.connect(self._delete_cells)
        butAddRow.clicked.connect(self._add_rows)
        butClear.clicked.connect(self._clear_table)

        butSetZero.clicked.connect(self._zero_PZ)
        # signal itemChanged is also triggered programmatically,
        # itemSelectionChanged is only triggered when entering cell
        # self.tblPZ.itemSelectionChanged.connect(self._copy_item)

        self.tblPZ.cellChanged.connect(self._copy_item)
        self.cmbNorm.activated.connect(self._copy_item)
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
            self.zpk[2] = safe_eval(source.text())
            self.spec_edited = False # reset flag

#------------------------------------------------------------------------------
    def _normalize_gain(self):
        """
        Normalize the gain factor so that the maximum of |H(f)| stays 1 or a
        previously stored maximum value of |H(f)|. Do this every time a P or Z
        has been change.

        Called by _copy_item()
        """
        if not np.isfinite(self.zpk[2]):
            self.zpk[2] = 1.

        norm = self.cmbNorm.currentText()
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

        self.ledGain.setVisible(self.chkPZList.isChecked())
        self.lblGain.setVisible(self.chkPZList.isChecked())

        if self.chkPZList.isChecked():
            if not self.ledGain.hasFocus():  # no focus, round the gain
                self.ledGain.setText(str(params['FMT'].format(self.zpk[2])))
            else: # widget has focus, show gain with full precision
                self.ledGain.setText(str(self.zpk[2]))


#------------------------------------------------------------------------------
    def _refresh_table(self):
        """
        (Re-)Create the displayed table from self.zpk with the
        desired number format.

        TODO:
        Update zpk[2]?

        Called by _copy_item()
        """

        params['FMT_pz'] = int(self.spnRound.text())

        self.ledGain.setVisible(self.chkPZList.isChecked())
        self.lblGain.setVisible(self.chkPZList.isChecked())
        self.tblPZ.setVisible(self.chkPZList.isChecked())

        if self.chkPZList.isChecked():

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
        # TODO: dtype=complex needs to be set for all subarrays
        self.zpk = np.array(fb.fil[0]['zpk'])# this enforces a deep copy
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
    def _zero_PZ(self):
        """
        Set all P/Zs = 0 with a magnitude less than eps and delete P/Z pairs
        afterwards.
        """
        eps = abs(safe_eval(self.ledSetEps.text()))
        sel = self._get_selected(self.tblPZ)['idx'] # get all selected indices
        if not sel:
            self.zpk[0] = self.zpk[0] * np.logical_not(
                                        np.isclose(self.zpk[0], 0., rtol=0, atol = eps))
            self.zpk[1] = self.zpk[1] * np.logical_not(
                                        np.isclose(self.zpk[1], 0., rtol=0, atol = eps))
        else:
            for i in sel:
                self.zpk[i[0]][i[1]] = self.zpk[i[0]][i[1]] * np.logical_not(
                                         np.isclose(self.zpk[i[0]][i[1]], 0., rtol=0, atol = eps))
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

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FilterPZ(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())