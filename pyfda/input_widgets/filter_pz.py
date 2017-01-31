# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter Poles and Zeros
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
from pprint import pformat
import logging
logger = logging.getLogger(__name__)

from ..compat import (QtCore, QWidget, QLabel, QLineEdit, pyqtSignal, QFrame, QEvent,
                      QCheckBox, QPushButton, QSpinBox, QComboBox,
                      QTableWidget, QTableWidgetItem,
                      QVBoxLayout, QHBoxLayout, QStyledItemDelegate)

import numpy as np
from scipy.signal import freqz, zpk2tf

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, safe_eval, rt_label
from pyfda.pyfda_rc import params

# TODO: correct scaling after insertion / deletion of cellsn
# TODO: order P/Z depending on frequency or magnitude
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
        return "{:.{n_digits}g}".format(safe_eval(text), n_digits = FilterPZ.n_digits)

class FilterPZ(QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """

    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal()
    n_digits = 3 # class attribute, initial setting for number of displayed digits

    def __init__(self, parent):
        super(FilterPZ, self).__init__(parent)

        self.Hmax_last = 1

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        """
        # Find which button holds the longest text:
        MaxTextlen = 0
        longestText = ""
        ButLength = 0
        butTexts = ["Add", "Delete", "Save", "Load", "Clear", "Set Zero"]

        for item in butTexts:
            if len(item) > MaxTextlen:
                MaxTextlen = len(item)
                longestText = item

        self.chkPZList = QCheckBox("Show table", self)
        self.chkPZList.setChecked(True)
        self.chkPZList.setToolTip("Show filter Poles / Zeros as an editable table.")

        lblRound = QLabel("Digits = ", self)
        self.spnRound = QSpinBox(self)
        self.spnRound.setRange(0,9)
        self.spnRound.setValue(FilterPZ.n_digits)
        self.spnRound.setToolTip("Display d digits.")

        self.chkNorm =  QCheckBox("Normalize", self)
        self.chkNorm.setChecked(False)
        self.chkNorm.setToolTip("Normalize max. (H(f)).")
        self.cmbNorm = QComboBox(self)
        self.cmbNorm.addItems(["None", "1", "Max"])

        self.lblGain = QLabel(rt_label("k = "), self)
        self.ledGain = QLineEdit(self)
        self.ledGain.setToolTip("Specify gain factor k.")
        self.ledGain.setText(str(1.))
        self.ledGain.setObjectName("ledGain")
        self.ledGain.installEventFilter(self)

        self.tblPZ = QTableWidget(self)
#        self.tblPZ.setEditTriggers(QTableWidget.AllEditTriggers) # make everything editable
        self.tblPZ.setAlternatingRowColors(True) # alternating row colors)
        self.tblPZ.setObjectName("tblPZ")
        self.tblPZ.setItemDelegate(ItemDelegate(self))

        butAddRow = QPushButton(butTexts[0], self)
        butAddRow.setToolTip("<SPAN>Select <i>N</i> existing rows "
                             "to insert <i>N</i> new rows above last selected cell. "
                             "When nothing is selected, add a row at the end.</SPAN>")

        ButLength = butAddRow.fontMetrics().boundingRect(longestText).width()+10
        butAddRow.setMaximumWidth(ButLength)

        butDelCell = QPushButton(butTexts[1], self)
        butDelCell.setToolTip("Delete selected cell(s) from the table.\n"
                "Use <SHIFT> or <CTRL> to select multiple cells.")
        butDelCell.setMaximumWidth(ButLength)

        butClear = QPushButton(butTexts[4], self)
        butClear.setToolTip("Clear all entries.")
        butClear.setMaximumWidth(ButLength)

        butSave = QPushButton(butTexts[2], self)
        butSave.setToolTip("Save P/Z & update all plots.\n"
                                "No modifications are saved before!")
        butSave.setMaximumWidth(ButLength)

        butLoad = QPushButton(butTexts[3], self)
        butLoad.setToolTip("Reload P / Z.")
        butLoad.setMaximumWidth(ButLength)

        butSetZero = QPushButton(butTexts[5], self)
        butSetZero.setToolTip("<SPAN>Set P / Z = 0 when magnitude &lt; &epsilon;.</SPAN>")
        butSetZero.setMaximumWidth(ButLength)

        self.lblEps = QLabel("for " + rt_label("&epsilon; &lt;"), self)
#        self.lblEps.setTextFormat(Qt.RichText)
        self.ledSetEps = QLineEdit(self)
        self.ledSetEps.setToolTip("<SPAN>Specify tolerance.</SPAN>")
        self.ledSetEps.setText(str(1e-6))

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
        layHGain.addWidget(self.chkNorm)
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
        frmMain.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmMain.setLayout(layVBtns)

        layVMain = QVBoxLayout()
        layVMain.addWidget(frmMain)
        layVMain.addWidget(self.tblPZ)
#        layVMain.addStretch(1)
        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        self.load_entries() # initialize table with default values from filterbroker
        self._update_entries()

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.spnRound.editingFinished.connect(self.load_entries)
        butLoad.clicked.connect(self.load_entries)
        self.chkPZList.clicked.connect(self.load_entries)

        butSave.clicked.connect(self._save_entries)

        butDelCell.clicked.connect(self._delete_cells)
        butAddRow.clicked.connect(self._add_rows)
        butClear.clicked.connect(self._clear_table)

        butSetZero.clicked.connect(self._zero_PZ)
        self.tblPZ.itemChanged.connect(self._copy_entry)
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
                print(source.objectName(), "focus in")
                self.spec_edited = False
                self._update_gain(source)
                return True # event processing stops here

            elif event.type() == QEvent.KeyPress:
                print(source.objectName(), "key")
                self.spec_edited = True # entry has been changed
                key = event.key() # key press: 6, key release: 7
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}: # store entry
                    self._store_gain(source)
                    return True
                elif key == QtCore.Qt.Key_Escape: # revert changes
                    self.spec_edited = False
                    self._update_gain(source)
                    return True

            elif event.type() == QEvent.FocusOut: # 9
                print(source.objectName(), "focus out")
                self._update_gain(source)
                self._store_gain(source)
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
            print("\n_store_entry:", str(source.objectName()))
            value = safe_eval(source.text())
            self.zpk[2] = value
            self.spec_edited = False # reset flag

            self._update_gain()

    def _normalize_gain(self):
        """
        Normalize the gain factor so that the maximum of |H(f)| stays 1 or a 
        previously stored maximum value of |H(f)|
        """
        if not np.isfinite(self.zpk[2]):
            self.zpk[2] = 1.

        if self.cmbNorm.currentText() != "None":        
            b, a = zpk2tf(self.zpk[0], self.zpk[1], self.zpk[2]) 
            [w, H] = freqz(b, a) 
            Hmax = max(abs(H)) 
            if not np.isfinite(Hmax) or Hmax > 1e4 or Hmax < 1e-4:
                Hmax = 1.
            if self.cmbNorm.currentText() == "1":
                self.zpk[2] = self.zpk[2] / Hmax
            elif self.cmbNorm.currentText() == "Max":
                self.zpk[2] = self.zpk[2] / Hmax * self.Hmax_last
            self.Hmax_last = Hmax # store current max. filter gain

#------------------------------------------------------------------------------
    def _update_gain(self, source = None):
        """
        Recalculate gain and update QLineEdit

        Called by _store_entry()
        """
        print("\n_update_gain:")
        
        self.ledGain.setVisible(self.chkPZList.isChecked())
        self.lblGain.setVisible(self.chkPZList.isChecked())
        
        if self.chkPZList.isChecked():
            if isinstance(source, QLineEdit):

                self._normalize_gain()
                
                if not self.ledGain.hasFocus():  # no focus, round the gain
                    self.ledGain.setText(str(params['FMT'].format(self.zpk[2])))
                else: # widget has focus, show gain with full precision
                    self.ledGain.setText(str(self.zpk[2]))


#------------------------------------------------------------------------------
    def _update_entries(self):
        """
        (Re-)Create the displayed table from self.zpk with the
        desired number format.

        TODO:        
        Update zpk[2]?

        Called by _store_entry()
        """
        print("\n_refresh_table:")

        FilterPZ.n_digits = int(self.spnRound.text())
        
        self.ledGain.setVisible(self.chkPZList.isChecked())
        self.lblGain.setVisible(self.chkPZList.isChecked())
        self.tblPZ.setVisible(self.chkPZList.isChecked())

        if self.chkPZList.isChecked():

            self.ledGain.setText(str(params['FMT'].format(self.zpk[2])))

            self.tblPZ.setRowCount(max(len(self.zpk[0]),len(self.zpk[1])))
            self.tblPZ.setColumnCount(2)
            self.tblPZ.setHorizontalHeaderLabels(["Zeros", "Poles"])
            for col in range(2):
                for row in range(len(self.zpk[col])):
                    # set table item from self.zpk and strip '()' of complex numbers
                    item = self.tblPZ.item(row, col)
                    if item: # does item exist?
                        item.setText(str(self.zpk[col][row]).strip('()'))             
                    else: # no, construct it:
                        self.tblPZ.setItem(row,col,QTableWidgetItem(
                              str(self.zpk[col][row]).strip('()')))

            self.tblPZ.resizeColumnsToContents()
            self.tblPZ.resizeRowsToContents()
            self.tblPZ.clearSelection()

#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Load all entries from filter dict fb.fil[0]['zpk'] into the shadow
        register self.zpk and update the display.
        """
        print("\nload_entries:")

        self.zpk = fb.fil[0]['zpk']
        self._update_entries()

#------------------------------------------------------------------------------
    def _copy_entry(self):
        """
        Copy the values from the current table item to self.zpk 
        """  
        col = self.tblPZ.currentIndex().column()
        row = self.tblPZ.currentIndex().row()
        item = self.tblPZ.item(row,col)

        if item:
            if item.text() != "":
                self.zpk[col][row] = safe_eval(item.text())
            else:
                self.zpk[col][row] = 0.

#------------------------------------------------------------------------------
#    def _copy_entries(self):
#        """
#        Copy the values from the table to self.zpk 
#        """  
#        print(self.tblPZ.currentIndex().column(), self.tblPZ.currentIndex().row())
#        self.zpk[0] = self.zpk[1] = []
#        # self.zpk[2] is not modified here! 
#        num_rows, num_cols = self.tblPZ.rowCount(), self.tblPZ.columnCount()
#                       
#        for col in range(num_cols):
#            rows = []
#            for row in range(num_rows):
#                item = self.tblPZ.item(row, col)
#                if item:
#                    if item.text() != "":
#                        rows.append(safe_eval(item.text()))
#                else:
#                    rows.append(0.)
#
#            self.zpk[col] = rows # type: list num_cols x num_rows

#------------------------------------------------------------------------------
    def _save_entries(self):
        """
        Save the values from self.zpk to the filter PZ dict,
        the QLineEdit for setting the gain has to be treated separately.
        """

        logger.debug("=====================\nFilterPZ._save_entries called")
        
        self._copy_entries()
        fb.fil[0]['N'] = len(self.zpk[0])
        if np.any(self.zpk[1]): # any non-zero poles?
            fb.fil[0]['fc'] = 'Manual_IIR'
        else:
            fb.fil[0]['fc'] = 'Manual_FIR'

        fil_save(fb.fil[0], self.zpk, 'zpk', __name__) # save with new gain

        if __name__ == '__main__':
            self.load_entries() # only needed for stand-alone test

        self.sigFilterDesigned.emit() # -> filter_specs
        # -> input_tab_widgets -> pyfdax -> plt_tab_widgets.updateAll()
        # TODO: this also needs to trigger filter_specs.updateUI to switch to
        #       manual design when saving P/Z

        logger.debug("_save_entries - coeffients / zpk updated:\n"
            "b,a = %s\n\n"
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

        self._update_entries()

#------------------------------------------------------------------------------
    def _get_selected(self, table):
        """
        get selected cells and return:
        - indices of selected cells
        - selected colums
        - selected rows
        - current cell
        """
        print("get_selected")
        idx = []
        for _ in table.selectedItems():
            idx.append([_.column(), _.row(), ])
        cols = sorted(list({i[0] for i in idx}))
        rows = sorted(list({i[1] for i in idx}))
        cur = (table.currentColumn(), table.currentRow())


        cur_idx = table.currentIndex()
        print("cur_index: ", cur_idx.column(), cur_idx.row())
        print("cur_r_c:", cur)

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
        Finally, the table is updated from self.zpk.
        """
        sel = self._get_selected(self.tblPZ)['idx'] # get all selected indices
        Z = [s[1] for s in sel if s[0] == 0] # all selected indices in 'Z' column
        P = [s[1] for s in sel if s[0] == 1] # all selected indices in 'P' column

        # Delete array entries with selected indices. If Z or P are empty,
        # arrays remain unchanged.
        self.zpk[0] = np.delete(self.zpk[0], Z)
        self.zpk[1] = np.delete(self.zpk[1], P)

        # test and equalize if P and Z array have different lengths:
        D = len(self.zpk[0]) - len(self.zpk[1])
        if D > 0:
            self.zpk[1] = np.append(self.zpk[1], np.zeros(D))
        elif D < 0:
            self.zpk[0] = np.append(self.zpk[0], np.zeros(-D))

        self._delete_PZ_pairs()
        self._update_entries()

#------------------------------------------------------------------------------
    def _add_rows(self):
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add one row.
        """
        print("\n_add_rows:")
        row = self.tblPZ.currentRow()
        sel = len(self._get_selected(self.tblPZ)['rows'])
        # TODO: evaluate non-contiguous selection as well?
        print(sel, row)

        if sel == 0: # nothing selected
            sel = 1 # add at least one row ...
            row = min(len(self.zpk[0]), len(self.zpk[1])) # ... at the bottom

        self.zpk[0] = np.insert(self.zpk[0], row, np.zeros(sel))
        self.zpk[1] = np.insert(self.zpk[1], row, np.zeros(sel))

        self._update_entries()

#------------------------------------------------------------------------------
    def _zero_PZ(self):
        """
        Set all PZs = 0 with a magnitude less than eps and delete P/Z pairs
        afterwards.
        """
        eps = abs(safe_eval(self.ledSetEps.text()))
        
        remove_me = np.isclose(self.zpk[0:2], 0, rtol=0, atol = eps)
        self.zpk[0:2] = self.zpk[0:2] * np.logical_not(remove_me)
        

#        for col in range(2):
#            for row in range(len(self.zpk[col])):
#                # set table item from self.zpk and strip '()' of complex numbers
#                item = self.tblPZ.item(row, col)
#                if np.isclose(safe_eval(item.text()), 0, rtol=0, atol=eps):
#                        item.setText(str(0.))
        self._delete_PZ_pairs()
        self._update_entries()
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