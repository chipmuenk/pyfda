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
                      QTableWidget, QTableWidgetItem, QAbstractItemView,
                      QVBoxLayout, QHBoxLayout, QSizePolicy)

import numpy as np
import numpy.ma as ma
from scipy.signal import freqz

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, safe_eval
from pyfda.pyfda_rc import params

# TODO: delete / insert individual cells instead of rows
# TODO: correct scaling after insertion / deletion of cells
# TODO: drag & drop doesn't work
# TODO: insert row above currently selected row instead of appending at the end
# TODO: eliminate trailing zeros for filter order calculation
# TODO: order P/Z depending on frequency or magnitude
# TODO: display SOS graphically

class FilterPZ(QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """

    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal()

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

        self.chkPZList = QCheckBox("Show Poles / Zeros", self)
        self.chkPZList.setChecked(True)
        self.chkPZList.setToolTip("Show filter Poles / Zeros as an editable list.")

        lblRound = QLabel("Digits = ", self)
        self.spnRound = QSpinBox(self)
        self.spnRound.setRange(0,9)
        self.spnRound.setValue(0)
        self.spnRound.setToolTip("Round to d digits.")

        self.cmbFilterType = QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip("FIR filters only have zeros (b coefficients).")
        self.cmbFilterType.addItems(["FIR","IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.chkNorm =  QCheckBox("Normalize", self)
        self.chkNorm.setChecked(False)
        self.chkNorm.setToolTip("Normalize max. (H(f)).")

        self.lblGain = QLabel("k = ", self)
        self.ledGain = QLineEdit(self)
        self.ledGain.setToolTip("Specify gain factor k.")
        self.ledGain.setText(str(1.))
        self.ledGain.setObjectName("ledGain")
        self.ledGain.installEventFilter(self)

        self.tblPZ = QTableWidget(self)
        self.tblPZ.setEditTriggers(QTableWidget.AllEditTriggers) # make everything editable
        self.tblPZ.setAlternatingRowColors(True) # alternating row colors
#        self.tblPZ.setDragEnabled(True)
#        self.tblPZ.setDragDropMode(QAbstractItemView.InternalMove)
#        self.tblPZ.SelectionMode.
        self.tblPZ.setSizePolicy(QSizePolicy.MinimumExpanding,
                                          QSizePolicy.Expanding)
        self.tblPZ.setObjectName("tblPZ")
        self.tblPZ.installEventFilter(self)


        butAddRow = QPushButton(butTexts[0], self)
        butAddRow.setToolTip("Add row to PZ table.\n"
                                "Select n existing rows to append n new rows.")

        ButLength = butAddRow.fontMetrics().boundingRect(longestText).width()+10
        butAddRow.setMaximumWidth(ButLength)

        butDelCell = QPushButton(butTexts[1], self)
        butDelCell.setToolTip("Delete selected cell(s) from the table.\n"
                "Multiple cells can be selected using <SHIFT> or <CTRL>."
                "If nothing is selected, delete last row.")
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
        butSetZero.setToolTip("Set P / Z = 0 with a magnitude < eps.")
        butSetZero.setMaximumWidth(ButLength)

        self.lblEps = QLabel("for P, Z <", self)
        self.ledSetEps = QLineEdit(self)
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        # ============== UI Layout =====================================
        layHChkBoxes = QHBoxLayout()
        layHChkBoxes.addWidget(self.chkPZList)
        layHChkBoxes.addStretch(1)
        layHChkBoxes.addWidget(self.cmbFilterType)
        layHChkBoxes.addStretch(1)
        layHChkBoxes.addWidget(lblRound)
        layHChkBoxes.addWidget(self.spnRound)

        layHGain = QHBoxLayout()
        layHGain.addWidget(self.lblGain)
        layHGain.addWidget(self.ledGain)
#        layHChkBoxes.addStretch(1)
        layHGain.addWidget(self.chkNorm)
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
        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        self.load_entries() # initialize table with default values from filterbroker
        self._update_entries()

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
#        self.tblPZ.itemEntered.connect(self.saveZPK) # nothing happens
#        self.tblPZ.itemActivated.connect(self.saveZPK) # nothing happens
#        self.tblPZ.itemChanged.connect(self.saveZPK) # works but fires multiple times
#        self.tblPZ.selectionModel().currentChanged.connect(self.saveZPK)
#        self.tblPZ.clicked.connect(self.saveZPK)
#        self.ledGain.editingFinished.connect(self.saveZPK)

        self.spnRound.editingFinished.connect(self.load_entries)
        self.cmbFilterType.currentIndexChanged.connect(self._set_filter_type)
        butLoad.clicked.connect(self.load_entries)
        self.chkPZList.clicked.connect(self.load_entries)

        butSave.clicked.connect(self._save_entries)

        butDelCell.clicked.connect(self._delete_cells)
        butAddRow.clicked.connect(self._add_rows)
        butClear.clicked.connect(self._clear_table)

        butSetZero.clicked.connect(self._zero_PZ)
        #----------------------------------------------------------------------

        # Every time a field is edited, call self._store_entry and
        # self.load_entries. This is achieved by dynamically installing and
        # removing event filters when creating / deleting subwidgets.
        # The event filter monitors the focus of the input fields.

#------------------------------------------------------------------------------

    def eventFilter(self, source, event):
        """
        Filter all events generated by the QLineEdit widgets. Source and type
        of all events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (QEvent.FocusIn`), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (QEvent.FocusOut`), store
          current value in linear format with full precision (only if
          `spec_edited`== True) and display the stored value in selected format
        """

        if isinstance(source, (QLineEdit, QTableWidget)):#, QTableWidgetItem)): # could be extended for other widgets
            if event.type() == QEvent.FocusIn:  # 8
                print(source.objectName(), "focus in")
                self.spec_edited = False
                self._update_entry(source)
#                if isinstance(source, QLineEdit):
#                    self._update_entry(source)
#                else:
#                    self._update_entries()
                return True # event processing stops here

            elif event.type() == QEvent.KeyPress:
                print(source.objectName(), "key")
                self.spec_edited = True # entry has been changed
                key = event.key() # key press: 6, key release: 7
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}: # store entry
                    self._store_entry(source)
                    return True
                elif key == QtCore.Qt.Key_Escape: # revert changes
                    self.spec_edited = False
                    self._update_entries()
                    return True

            elif event.type() == QEvent.FocusOut: # 9
                print(source.objectName(), "focus out")
                self._update_entry(source)
                self._store_entry(source)
                return True
                # 1: Timer event, 10/11: mouse enters/leaves widget, 12: paint,
                # 24/25: window is activated / deactivated
                # 110: Tooltip was requested
#            elif str(source.objectName()) == "tblPZ" and event.type() not in (1, 10, 11, 12, 110):
#                print(event.type())
#            else:
        # Call base class method to continue normal event processing:
 #               return super(FilterPZ, self).eventFilter(source, event)
#        else:
#            return super(FilterPZ, self).eventFilter(source, event)
        return super(FilterPZ, self).eventFilter(source, event)
#------------------------------------------------------------------------------
    def _store_entry(self, source):
        """
        When the textfield of `source` has been edited (flag `self.spec_edited` =  True),
        store it in the shadow dict. This is triggered by `QEvent.focusOut`.
        """
        if self.spec_edited:
            print("\n_store_entry:", str(source.objectName()))
            if isinstance(source, QLineEdit):
                value = safe_eval(source.text())
                self.zpk[2] = value
                self.spec_edited = False # reset flag
            else:
                row = self.tblPZ.currentRow()
                col = self.tblPZ.currentColumn()
                item = self.tblPZ.item(col, row).text()
                if item:
                    if item != "":
                        self.zpk[col][row] = safe_eval(str(item))# safe_eval(item)
                else:
                    self.zpk[col][row] = 0.

                print("current item:", item)

            self._update_entries()

#------------------------------------------------------------------------------
    def _set_filter_type(self):
        """
        Change between FIR and IIR filter setting
        """

        if self.cmbFilterType.currentText() == 'FIR':
            fb.fil[0]['ft'] = 'FIR'
        else:
            fb.fil[0]['ft'] = 'IIR'


#------------------------------------------------------------------------------
    def _update_entry(self, source = None):
        """
        (Re-)Create the diplayed table from the shadow table self.zpk with the
        desired number of digits and in the desired format.

        Recalculate gain and update QLineEdit

        Called by _store_entry()
        """
        print("\n_update_entry:")
        if self.chkPZList.isChecked():
            if isinstance(source, QLineEdit) or not source:

                self.ledGain.setVisible(self.chkPZList.isChecked())
                self.lblGain.setVisible(self.chkPZList.isChecked())

                n_digits = int(self.spnRound.text())

                if self.chkNorm.isChecked():
                    [w, H] = freqz(fb.fil[0]['ba'][0], fb.fil[0]['ba'][1]) # (bb, aa)
                    self.Hmax_last = max(abs(H)) # store current max. filter gain
                    if not np.isfinite(self.Hmax_last) or self.Hmax_last > 1e4:
                        self.Hmax_last = 1.

                    if not np.isfinite(self.zpk[2]):
                        self.zpk[2] = 1.

                if not self.ledGain.hasFocus():
                        # widget has no focus, round the display
                        print("led no focus")
                        self.ledGain.setText(str(params['FMT'].format(self.zpk[2])))
                else:
                        # widget has focus, show full precision
                        self.ledGain.setText(str(self.zpk[2]))
                        print("led focus")

            if isinstance(source, QTableWidget) or not source:

#                sel = self.tblPZ.selectedItems() # list with selected instances
#                print(sel)
#                if sel:
#                    col = sel[0].column()
#                    row = sel[0].row()

                row = self.tblPZ.currentRow()
                col = self.tblPZ.currentColumn()
                cur_idx = self.tblPZ.currentIndex()
                print("current table item:", col, row)
                print("current index:", cur_idx.column(),cur_idx.row())
                print("gc:", self._get_selected(self.tblPZ)['cur'])


                item = self.tblPZ.item(row, col)
                item_w = self.tblPZ.currentItem()
                # copy content of self.zpk to corresponding table field, rounding
                # as specified and removing the brackets of complex arguments
                if item: # does item exist?
                    if not item.isSelected():
#                        # widget has no focus, round the display
#                        print("item not selected:", col, row)
#                        print(item_w.isSelected())
#                        item.setText(str(params['FMT'].format(self.zpk[col][row])))
#                    else:
#                        # widget has focus, show full precision
                        item.setText(str(self.zpk[col][row]).strip('()'))
                        print("item selected:", col, row)
                else: # no, construct it:
                    self.tblPZ.setItem(row,col,QTableWidgetItem(
                          str(self.zpk[col][row]).strip('()')))




#------------------------------------------------------------------------------
    def _update_entries(self):
        """
        (Re-)Create the diplayed table from the shadow table self.zpk with the
        desired number of digits and in the desired format - all entries are
        assumed to be unselected.

        Called by _store_entry() and eventFilter
        """
        print("\n_update_entries:")
        self.ledGain.setVisible(self.chkPZList.isChecked())
        self.lblGain.setVisible(self.chkPZList.isChecked())
        self.tblPZ.setVisible(self.chkPZList.isChecked())

        if self.chkPZList.isChecked():

            if fb.fil[0]['ft'] == 'FIR':
                self.cmbFilterType.setCurrentIndex(0) # set comboBox to "FIR"
            else:
                self.cmbFilterType.setCurrentIndex(1) # set comboBox to "IIR"

            n_digits = int(self.spnRound.text())

            self.ledGain.setText(str(params['FMT'].format(self.zpk[2])))

            self.tblPZ.setRowCount(max(len(self.zpk[0]),len(self.zpk[1])))

            logger.debug("_update_entries - pz:\n"
                "Shape = %s\n"
                "Len   = %d\n"
                "NDim  = %d\n\n"
                "ZPK = %s"
                %(np.shape(self.zpk),len(self.zpk), np.ndim(self.zpk), pformat(self.zpk))
                  )

            self.tblPZ.setColumnCount(2)
            self.tblPZ.setHorizontalHeaderLabels(["Z", "P"])
            for col in range(2):
                for row in range(len(self.zpk[col])):
                    logger.debug("Len Row = %d" %len(self.zpk[col]))
                    item = self.tblPZ.item(row, col)
                    # copy content of self.zpk to corresponding table field, formatting
                    # as specified and removing the brackets of complex arguments
                    if item: # does item exist?
                        item.setText(str(params['FMT'].format(self.zpk[col][row]))) # .strip('()'))
                    else: # no, construct it:
                        self.tblPZ.setItem(row,col,QTableWidgetItem(
                              str(self.zpk[col][row]).strip('()')))

            self.tblPZ.resizeColumnsToContents()
            self.tblPZ.resizeRowsToContents()

#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Load all entries from filter dict fb.fil[0]['zpk'] into the shadow
        register self.zpk and update the display.
        """
        print("\nload_entries:")
        if fb.fil[0]['ft'] == 'FIR':
            self.cmbFilterType.setCurrentIndex(0) # set comboBox to "FIR"
        else:
            self.cmbFilterType.setCurrentIndex(1) # set comboBox to "IIR"

        self.zpk = fb.fil[0]['zpk']
        self._update_entries()

#------------------------------------------------------------------------------
    def _save_entries(self):
        """
        Save the values from the shadow dict to the filter PZ dict
        """

        logger.debug("=====================\nInputPZ._save_entries called")

        fb.fil[0]['N'] = max(len(self.zpk[0]), len(self.zpk[1]))
#        self.zpk = []
#
#        num_rows = self.tblPZ.rowCount()
#        logger.debug("nrows = %d" %num_rows)
#
#        #iterate over both columns
#        for col in range(2):
#            rows = []
#            for row in range(num_rows):
#                item = self.tblPZ.item(row, col)
#                if item:
#                    if item.text() != "":
#                        rows.append(safe_eval(item.text()))
#                else:
#                    rows.append(0.)
#
#            self.zpk.append(rows)
#
#        self.zpk.append(safe_eval(self.ledGain.text())) # append k factor to self.zpk
#
#        fb.fil[0]['N'] = num_rows
#
#        if np.any(self.zpk[1]):
#            fb.fil[0]['ft'] = 'IIR'
#            fb.fil[0]['fc'] = 'Manual_IIR'
#            self.cmbFilterType.setCurrentIndex(1) # set to "IIR"
#        else:
#            fb.fil[0]['ft'] = 'FIR'
#            fb.fil[0]['fc'] = 'Manual_FIR'
#            self.cmbFilterType.setCurrentIndex(0) # set to "FIR"
#
#        fil_save(fb.fil[0], self.zpk, 'zpk', __name__) # save & convert to 'ba'
#
#        if self.chkNorm.isChecked():
#            # set gain factor k (self.zpk[2]) in such a way that the max. filter
#            # gain remains unchanged
#            # TODO: Comparison against Hmax is not robust, need to find another anchor
#            [w, H] = freqz(fb.fil[0]['ba'][0], fb.fil[0]['ba'][1]) # (bb, aa)
#            Hmax = max(abs(H))
#            if not np.isfinite(Hmax) or Hmax > 1e4:
#                Hmax = 1.
#            self.zpk[2] = self.zpk[2] * self.Hmax_last / max(abs(H))
        fil_save(fb.fil[0], self.zpk, 'zpk', __name__) # save with new gain

        if __name__ == '__main__':
            self.load_entries() # only needed for stand-alone test

        self.sigFilterDesigned.emit() # -> filter_specs
        self.sigSpecsChanged.emit()
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
        cur_itm = table.currentItem()
        print("cur_index: ", cur_idx.column(), cur_idx.row())
        print("cur_item:", cur_itm.isSelected())
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
        """
        sel = self._get_selected(self.tblPZ)['idx'] # get all selected indices
        Z = [s[1] for s in sel if s[0] == 0] # all selected indices in 'Z' column
        P = [s[1] for s in sel if s[0] == 1] # all selected indices in 'P' column

        # Delete array entries with selected indices. If Z or P are empty,
        # arrays remain unchanged.
        self.zpk[0] = np.delete(self.zpk[0], Z)
        self.zpk[1] = np.delete(self.zpk[1], P)

        # test and correct if P and Z array have different lengths:
        D = len(self.zpk[0]) - len(self.zpk[1])
        if D > 0:
            self.zpk[1] = np.append(self.zpk[1], np.zeros(D))
        elif D < 0:
            self.zpk[0] = np.append(self.zpk[0], np.zeros(-D))

        self._update_entries()

#------------------------------------------------------------------------------
    def _add_rows(self):
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add one row.
        """
        print("\n_add_rows:")
        print(self.tblPZ.selectionModel().selectedRows(), "\n", self.tblPZ.currentRow())
        sel = len(self.tblPZ.selectionModel().selectedRows())
        row = self.tblPZ.currentRow()
        print(self._get_selected(self.tblPZ))
        print(sel, row)

        if sel == 0: # nothing selected
            sel = 1 # add at least one row
            row = min(len(self.zpk[0]), len(self.zpk[1]))

        self.zpk[0] = np.insert(self.zpk[0], row, 0)
        self.zpk[1] = np.insert(self.zpk[1], row, 0)

#        self.tblPZ.setRowCount(new_rows)
#
#        for col in range(2):
#            for row in range(old_rows, new_rows):
#                self.tblPZ.setItem(row,col,QTableWidgetItem("0.0"))
        self._update_entries()

#------------------------------------------------------------------------------
    def _zero_PZ(self):
        """
        Set all PZs = 0 with a magnitude less than eps
        """
        eps = float(self.ledSetEps.text())
        num_rows= self.tblPZ.rowCount()

        for col in range(2):
            for row in range(num_rows):
                item = self.tblPZ.item(row, col)
                if item:
                    if abs(safe_eval(item.text())) < eps:
                        item.setText(str(0.))
                else:
                    self.tblPZ.setItem(row,col,QTableWidgetItem("0.0"))

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FilterPZ(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())