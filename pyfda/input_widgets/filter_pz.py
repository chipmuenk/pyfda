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

from ..compat import (QWidget, QLabel, QLineEdit, pyqtSignal,
                      QCheckBox, QPushButton, QSpinBox, QComboBox,
                      QTableWidget, QTableWidgetItem, QAbstractItemView,
                      QVBoxLayout, QHBoxLayout, QSizePolicy)

import numpy as np
from scipy.signal import freqz

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import cround, fil_save
from pyfda.simpleeval import simple_eval

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

        self.chkPZList = QCheckBox()
        self.chkPZList.setChecked(True)
        self.chkPZList.setToolTip("Show filter Poles / Zeros as an editable list.")
        self.chkPZList.setText("Show Poles / Zeros")

        self.lblRound = QLabel("Digits = ")
        self.spnRound = QSpinBox()
        self.spnRound.setRange(0,9)
        self.spnRound.setValue(0)
        self.spnRound.setToolTip("Round to d digits.")

        self.cmbFilterType = QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip("FIR filters only have zeros (b coefficients).")
        self.cmbFilterType.addItems(["FIR","IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lblGain = QLabel("k = ")
        
        self.chkNorm =  QCheckBox()
        self.chkNorm.setChecked(False)
        self.chkNorm.setToolTip("Normalize max. (H(f)).")
        self.chkNorm.setText("Normalize")

        self.ledGain = QLineEdit()
        self.ledGain.setToolTip("Specify gain factor k.")
        self.ledGain.setText(str(1.))

        self.tblPZ = QTableWidget()
        self.tblPZ.setEditTriggers(QTableWidget.AllEditTriggers)
        self.tblPZ.setAlternatingRowColors(True)
        self.tblPZ.setDragEnabled(True)
        self.tblPZ.setDragDropMode(QAbstractItemView.InternalMove)
        self.tblPZ.setSizePolicy(QSizePolicy.MinimumExpanding,
                                          QSizePolicy.Expanding)

        self.butAddRow = QPushButton()
        self.butAddRow.setToolTip("Add row to PZ table.\n"
                                "Select n existing rows to append n new rows.")
        self.butAddRow.setText(butTexts[0])
        
        ButLength = self.butAddRow.fontMetrics().boundingRect(longestText).width()+10
        self.butAddRow.setMaximumWidth(ButLength)

        self.butDelRow = QPushButton()
        self.butDelRow.setToolTip("Delete selected row(s) from the table.\n"
                "Multiple rows can be selected using <SHIFT> or <CTRL>."
                "If nothing is selected, delete last row.")
        self.butDelRow.setText(butTexts[1])
        self.butDelRow.setMaximumWidth(ButLength)

        self.butClear = QPushButton()
        self.butClear.setToolTip("Clear all entries.")
        self.butClear.setText(butTexts[4])
        self.butClear.setMaximumWidth(ButLength)              

        self.butSave = QPushButton()
        self.butSave.setToolTip("Save P/Z & update all plots.\n"
                                "No modifications are saved before!")
        self.butSave.setText(butTexts[2])
        self.butSave.setMaximumWidth(ButLength)

        self.butLoad = QPushButton()
        self.butLoad.setToolTip("Reload P / Z.")
        self.butLoad.setText(butTexts[3])
        self.butLoad.setMaximumWidth(ButLength)              

        self.butSetZero = QPushButton()
        self.butSetZero.setToolTip("Set P / Z = 0 with a magnitude < eps.")
        self.butSetZero.setText(butTexts[5])
        self.butSetZero.setMaximumWidth(ButLength)              

        self.lblEps = QLabel("for P, Z <")

        self.ledSetEps = QLineEdit()
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        # ============== UI Layout =====================================
        self.layHChkBoxes = QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkPZList)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.cmbFilterType)
        self.layHChkBoxes.addStretch(1)        
        self.layHChkBoxes.addWidget(self.lblRound)
        self.layHChkBoxes.addWidget(self.spnRound)

        self.layHGain = QHBoxLayout()
        self.layHGain.addWidget(self.lblGain)
        self.layHGain.addWidget(self.ledGain)
        self.layHChkBoxes.addStretch(1)
        self.layHGain.addWidget(self.chkNorm)
        self.layHGain.addStretch()

        self.layHButtonsPZs1 = QHBoxLayout()
        self.layHButtonsPZs1.addWidget(self.butAddRow)
        self.layHButtonsPZs1.addWidget(self.butDelRow)
        self.layHButtonsPZs1.addWidget(self.butSave)
        self.layHButtonsPZs1.addWidget(self.butLoad)
        self.layHButtonsPZs1.addStretch()

        self.layHButtonsPZs2 = QHBoxLayout()
        self.layHButtonsPZs2.addWidget(self.butClear)
        self.layHButtonsPZs2.addWidget(self.butSetZero)
        self.layHButtonsPZs2.addWidget(self.lblEps)
        self.layHButtonsPZs2.addWidget(self.ledSetEps)
        self.layHButtonsPZs2.addStretch()

        layVMain = QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addLayout(self.layHGain)
        layVMain.addLayout(self.layHButtonsPZs1)
        layVMain.addLayout(self.layHButtonsPZs2)
        layVMain.addWidget(self.tblPZ)
#        layVMain.addStretch(1)
        self.setLayout(layVMain)
        
        self.load_entries() # initialize table with default values from filterbroker

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
        self.butLoad.clicked.connect(self.load_entries)
        self.chkPZList.clicked.connect(self.load_entries)

        self.butSave.clicked.connect(self._save_entries)

        self.butDelRow.clicked.connect(self._delete_rows)
        self.butAddRow.clicked.connect(self._add_rows)
        self.butClear.clicked.connect(self._clear_table)

        self.butSetZero.clicked.connect(self._zero_PZ)
        #----------------------------------------------------------------------

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
    def load_entries(self):
        """
        Update all entries from filter dict,
        create table from filter zpk dict, overwriting all previous entries.
        """
        
        if fb.fil[0]['ft'] == 'FIR':
            self.cmbFilterType.setCurrentIndex(0) # set to "FIR"
        else:
            self.cmbFilterType.setCurrentIndex(1) # set to "IIR"

        zpk = fb.fil[0]['zpk']
        n_digits = int(self.spnRound.text())
        self.ledGain.setVisible(self.chkPZList.isChecked())
        self.lblGain.setVisible(self.chkPZList.isChecked())
        self.tblPZ.setVisible(self.chkPZList.isChecked())
        
        if self.chkNorm.isChecked():
            [w, H] = freqz(fb.fil[0]['ba'][0], fb.fil[0]['ba'][1]) # (bb, aa)
            self.Hmax_last = max(abs(H)) # store current max. filter gain
            if not np.isfinite(self.Hmax_last) or self.Hmax_last > 1e4:
                self.Hmax_last = 1.

        if not np.isfinite(zpk[2]):
            zpk[2] = 1.
        self.ledGain.setText(str(cround(zpk[2], n_digits)))

        self.tblPZ.setVisible(self.chkPZList.isChecked())
        self.tblPZ.setRowCount(max(len(zpk[0]),len(zpk[1])))

        logger.debug("load_entries - pz:\n"
            "Shape = %s\n"
            "Len   = %d\n"
            "NDim  = %d\n\n"
            "ZPK = %s"
            %(np.shape(zpk),len(zpk), np.ndim(zpk), pformat(zpk))
              )

        self.tblPZ.setColumnCount(2)
        self.tblPZ.setHorizontalHeaderLabels(["Z", "P"])
        for col in range(2):
            for row in range(len(zpk[col])):
                logger.debug("Len Row = %d" %len(zpk[col]))
                item = self.tblPZ.item(row, col)
                # copy content of zpk to corresponding table field, rounding 
                # as specified and removing the brackets of complex arguments
                if item: # does item exist?
                    item.setText(str(cround(zpk[col][row], n_digits)).strip('()'))
                else: # no construct it
                    self.tblPZ.setItem(row,col,QTableWidgetItem(
                          str(cround(zpk[col][row], n_digits)).strip('()')))

        self.tblPZ.resizeColumnsToContents()
        self.tblPZ.resizeRowsToContents()
        

#------------------------------------------------------------------------------
    def _save_entries(self):
        """
        Read table entries and save the values to the filter PZ dict
        """
            
        logger.debug("=====================\nInputPZ._save_entries called")
            
        zpk = [] 
        
        num_rows = self.tblPZ.rowCount()
        logger.debug("nrows = %d" %num_rows)

        #iterate over both columns
        for col in range(2):
            rows = []
            for row in range(num_rows):
                item = self.tblPZ.item(row, col)
                if item:
                    if item.text() != "":
                        rows.append(simple_eval(item.text()))
                else:
                    rows.append(0.)

            zpk.append(rows)

        zpk.append(simple_eval(self.ledGain.text())) # append k factor to zpk

        fb.fil[0]['N'] = num_rows
     
        if np.any(zpk[1]):
            fb.fil[0]['ft'] = 'IIR'
            fb.fil[0]['fc'] = 'Manual_IIR'
            self.cmbFilterType.setCurrentIndex(1) # set to "IIR"
        else:
            fb.fil[0]['ft'] = 'FIR'
            fb.fil[0]['fc'] = 'Manual_FIR'
            self.cmbFilterType.setCurrentIndex(0) # set to "FIR"

        fil_save(fb.fil[0], zpk, 'zpk', __name__) # save & convert to 'ba'

        if self.chkNorm.isChecked():
            # set gain factor k (zpk[2]) in such a way that the max. filter 
            # gain remains unchanged
            # TODO: Comparison against Hmax is not robust, need to find another anchor
            [w, H] = freqz(fb.fil[0]['ba'][0], fb.fil[0]['ba'][1]) # (bb, aa)
            Hmax = max(abs(H))
            if not np.isfinite(Hmax) or Hmax > 1e4:
                Hmax = 1.
            zpk[2] = zpk[2] * self.Hmax_last / max(abs(H))
            fil_save(fb.fil[0], zpk, 'zpk', __name__) # save with new gain

        if __name__ == '__main__':
            self.load_entries() # only needed for stand-alone test
         
        self.sigFilterDesigned.emit()

        logger.debug("_save_entries - coeffients / zpk updated:\n"
            "b,a = %s\n\n"
            "zpk = %s\n"
            %(pformat(fb.fil[0]['ba']), pformat(fb.fil[0]['zpk'])
              ))

#------------------------------------------------------------------------------
    def _clear_table(self):
        """
        Clear & initialize table for two poles and zeros @ origin,
        P = Z = [0; 0], k = 1
        """
        self.tblPZ.clear()
        self.tblPZ.setRowCount(2)
        self.tblPZ.setColumnCount(2)
        self.tblPZ.setHorizontalHeaderLabels(["Z", "P"])

        self.Hmax_last = 1.0
        self.ledGain.setText("1.0")

        num_cols = self.tblPZ.columnCount()
        for row in range(2):
            for col in range(num_cols):
                self.tblPZ.setItem(row,col,QTableWidgetItem("0.0"))


#------------------------------------------------------------------------------
    def _delete_rows(self):
        """
        Delete all selected rows by:
        - reading the indices of all selected cells
        - collecting the row numbers in a set (only unique elements)
        - sort the elements in a list in descending order
        - delete the rows starting at the bottom
        If nothing is selected, delete last row.
        """
        old_rows = self.tblPZ.rowCount()
        indices = self.tblPZ.selectionModel().selectedIndexes()
        rows = set()
        for index in indices:
            rows.add(index.row()) # collect all selected rows in a set
        if len(rows) == 0:
            rows = {old_rows-1}
        rows = sorted(list(rows), reverse = True)# sort rows in decending order
        for r in rows:
            self.tblPZ.removeRow(r)

        self.tblPZ.setRowCount(old_rows - len(rows))


#------------------------------------------------------------------------------
    def _add_rows(self):
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add one row.
        """
        old_rows = self.tblPZ.rowCount()
        new_rows = len(self.tblPZ.selectionModel().selectedRows()) + old_rows
        self.tblPZ.setRowCount(new_rows)

        if old_rows == new_rows: # nothing selected
            new_rows = old_rows + 1 # add at least one row

        self.tblPZ.setRowCount(new_rows)

        for col in range(2):
            for row in range(old_rows, new_rows):
                self.tblPZ.setItem(row,col,QTableWidgetItem("0.0"))

        self.tblPZ.resizeColumnsToContents()
        self.tblPZ.resizeRowsToContents()


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
                    if abs(simple_eval(item.text())) < eps:
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