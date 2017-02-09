# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter coefficients
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
from pprint import pformat
import logging
logger = logging.getLogger(__name__)

from ..compat import (QWidget, QLabel, QLineEdit, QComboBox, QFrame,
                      QCheckBox, QPushButton,
                      QAbstractItemView, QTableWidget, QTableWidgetItem,
                      QVBoxLayout, QHBoxLayout, QSizePolicy,
                      pyqtSignal, QEvent)

import numpy as np

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import cround, fil_save, safe_eval
from pyfda.pyfda_rc import params
import pyfda.pyfda_fix_lib as fix


# TODO: delete / insert individual cells instead of rows
# TODO: drag & drop doesn't work
# TODO: insert row above currently selected row instead of appending at the end
# TODO: eliminate trailing zeros for filter order calculation
# TODO: Fill combobox for Wrap / Quant settings
# TODO: Separate View and Storage of data for selecting number of displayed digits

class FilterCoeffs(QWidget):
    """
    Create widget for viewing / editing / entering data
    """
        # class variables (shared between instances if more than one exists)
    sigFilterDesigned = pyqtSignal()  # emitted when coeffs have been changed
                                    # manually
    def __init__(self, parent):
        super(FilterCoeffs, self).__init__(parent)

#        self.nrows = 0 # keep track of number of rows

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """

         #Which Button holds the longest Text?

        MaxTextlen = 0
        longestText = ""
        ButLength = 0
        butTexts = ["Add", "Delete", "Save", "Load", "Clear", "Set Zero", "< Q >"]

        # Find the longest text + padding for subsequent bounding box calculation 
        for item in butTexts:
            if len(item) > MaxTextlen:
                MaxTextlen = len(item)
                longestText = item + "mm" # this is the longest text + padding for  


        self.chkCoeffList =  QCheckBox(self)
        self.chkCoeffList.setChecked(True)
        self.chkCoeffList.setToolTip("Show filter coefficients as an editable list.")
        self.lblCoeffList = QLabel("Show Coefficients", self)
        
        self.cmbFilterType = QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip("FIR filters only have zeros (b coefficients).")
        self.cmbFilterType.addItems(["FIR","IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)


        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setEditTriggers(QTableWidget.AllEditTriggers)
        self.tblCoeff.setAlternatingRowColors(True)
#        self.tblCoeff.QItemSelectionModel.Clear
        self.tblCoeff.setDragEnabled(True)
        self.tblCoeff.setDragDropMode(QAbstractItemView.InternalMove)
        self.tblCoeff.setSizePolicy(QSizePolicy.MinimumExpanding,
                                          QSizePolicy.MinimumExpanding)

        butAddRow = QPushButton(self)
        butAddRow.setToolTip("Add row to coefficient table.\nSelect n existing rows to append n new rows.")
        butAddRow.setText(butTexts[0])
        #Calculate the length for the buttons based on the longest ButtonText
        ButLength = butAddRow.fontMetrics().boundingRect(longestText).width()
        butAddRow.setMaximumWidth(ButLength)

        butDelRow = QPushButton(self)
        butDelRow.setToolTip("Delete selected row(s) from the table.\n"
                "Multiple rows can be selected using <SHIFT> or <CTRL>.\n"
                "When noting is selected, delete last row.")
        butDelRow.setText(butTexts[1])
        butDelRow.setMaximumWidth(ButLength)

        butSave = QPushButton(self)
        butSave.setToolTip("Save coefficients & update filter plots.")
        butSave.setText(butTexts[2])
        butSave.setMaximumWidth(ButLength)

        butLoad = QPushButton(self)
        butLoad.setToolTip("Reload coefficients.")
        butLoad.setText(butTexts[3])
        butLoad.setMaximumWidth(ButLength)

        butClear = QPushButton(self)
        butClear.setToolTip("Clear all entries.")
        butClear.setText(butTexts[4])
        butClear.setMaximumWidth(ButLength)


        butSetZero = QPushButton(self)
        butSetZero.setToolTip("Set coefficients = 0 with a magnitude < eps.")
        butSetZero.setText(butTexts[5])
        butSetZero.setMaximumWidth(ButLength)

        self.lblEps = QLabel(self)
        self.lblEps.setText("for b, a <")

        self.ledSetEps = QLineEdit(self)
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        butQuant = QPushButton(self)
        butQuant.setToolTip("Quantize coefficients = 0 with a magnitude < eps.")
        butQuant.setText(butTexts[6])
        butQuant.setMaximumWidth(ButLength)

        self.lblQIQF  = QLabel("QI.QF = ")
        self.lblQOvfl = QLabel("Ovfl.:")
        self.lblQuant = QLabel("Quant.:")

        self.ledQuantI = QLineEdit(self)
        self.ledQuantI.setToolTip("Specify number of integer bits.")
        self.ledQuantI.setText("0")
        self.ledQuantI.setMaxLength(2) # maximum of 2 digits
        self.ledQuantI.setFixedWidth(30) # width of lineedit in points(?)

        self.lblDot = QLabel(self)
        self.lblDot.setText(".")

        self.ledQuantF = QLineEdit(self)
        self.ledQuantF.setToolTip("Specify number of fractional bits.")
        self.ledQuantF.setText("15")
        self.ledQuantF.setMaxLength(2) # maximum of 2 digits
#        self.ledQuantF.setFixedWidth(30) # width of lineedit in points(?)
        self.ledQuantF.setMaximumWidth(30)

        self.cmbQQuant = QComboBox(self)
        qQuant = ['none', 'round', 'fix', 'floor']
        self.cmbQQuant.addItems(qQuant)
        self.cmbQQuant.setCurrentIndex(1) # 'round'
        self.cmbQQuant.setToolTip("Select the kind of quantization.")
        
        self.cmbQOvfl = QComboBox(self)
        qOvfl = ['none', 'wrap', 'sat']
        self.cmbQOvfl.addItems(qOvfl)
        self.cmbQOvfl.setCurrentIndex(2) # 'sat'
        self.cmbQOvfl.setToolTip("Select overflow behaviour.")
        
        self.cmbQFormat = QComboBox(self)
        qFormat = ['Frac', 'Dec', 'Hex', 'Bin']
        self.cmbQFormat.addItems(qFormat)
        self.cmbQFormat.setCurrentIndex(0) # 'frac'
        self.cmbQFormat.setToolTip('Set the output format.')


        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbQOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbQFormat.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # ============== UI Layout =====================================
        layHChkBoxes = QHBoxLayout()
        layHChkBoxes.addWidget(self.chkCoeffList)
        layHChkBoxes.addWidget(self.lblCoeffList)
        layHChkBoxes.addStretch(1)

        layHButtonsCoeffs1 = QHBoxLayout()
        layHButtonsCoeffs1.addWidget(butAddRow)
        layHButtonsCoeffs1.addWidget(butDelRow)
        layHButtonsCoeffs1.addWidget(butSave)
        layHButtonsCoeffs1.addWidget(butLoad)
        layHButtonsCoeffs1.addWidget(self.cmbFilterType)
        layHButtonsCoeffs1.addStretch()

        layHButtonsCoeffs2 = QHBoxLayout()
        layHButtonsCoeffs2.addWidget(butClear)
        layHButtonsCoeffs2.addWidget(butSetZero)
        layHButtonsCoeffs2.addWidget(self.lblEps)
        layHButtonsCoeffs2.addWidget(self.ledSetEps)
        layHButtonsCoeffs2.addStretch()

        layHButtonsCoeffs3 = QHBoxLayout()
        layHButtonsCoeffs3.addWidget(butQuant)
        layHButtonsCoeffs3.addWidget(self.lblQIQF)
        layHButtonsCoeffs3.addWidget(self.ledQuantI)
        layHButtonsCoeffs3.addWidget(self.lblDot)
        layHButtonsCoeffs3.addWidget(self.ledQuantF)

        layHButtonsCoeffs3.addStretch()

        layHButtonsCoeffs4 = QHBoxLayout()

        layHButtonsCoeffs4.addWidget(self.lblQOvfl)
        layHButtonsCoeffs4.addWidget(self.cmbQOvfl)
        layHButtonsCoeffs4.addWidget(self.lblQuant)
        layHButtonsCoeffs4.addWidget(self.cmbQQuant)
        layHButtonsCoeffs4.addWidget(self.cmbQFormat)
        layHButtonsCoeffs4.addStretch()

        layVBtns = QVBoxLayout()
        layVBtns.addLayout(layHChkBoxes)
        layVBtns.addLayout(layHButtonsCoeffs1)
        layVBtns.addLayout(layHButtonsCoeffs2)
        layVBtns.addLayout(layHButtonsCoeffs3)
        layVBtns.addLayout(layHButtonsCoeffs4)

        # This frame encompasses all the buttons       
        frmMain = QFrame(self)
        frmMain.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmMain.setLayout(layVBtns)

        layVMain = QVBoxLayout()        
        layVMain.addWidget(frmMain)
        layVMain.addWidget(self.tblCoeff)
        layVMain.setContentsMargins(*params['wdg_margins'])
#        layVMain.addStretch(1)
        self.setLayout(layVMain)

        self.load_dict() # initialize table with default values from filter dict

        # ============== Signals & Slots ================================
#        self.tblCoeff.itemEntered.connect(self.save_coeffs) # nothing happens
#        self.tblCoeff.itemActivated.connect(self.save_coeffs) # nothing happens
        # this works but fires multiple times _and_ fires every time cell is
        # changed by program as well!
#        self.tblCoeff.itemChanged.connect(self.save_coeffs)
#        self.tblCoeff.clicked.connect(self.save_coeffs)
#        self.tblCoeff.selectionModel().currentChanged.connect(self.save_coeffs)

        self.chkCoeffList.clicked.connect(self.load_dict)
        self.cmbFilterType.currentIndexChanged.connect(self._set_filter_type)
        butLoad.clicked.connect(self.load_dict)

        butSave.clicked.connect(self.store_entries)

        butDelRow.clicked.connect(self.delete_rows)
        butAddRow.clicked.connect(self.add_rows)

        butClear.clicked.connect(self._clear_table)
        butSetZero.clicked.connect(self._set_coeffs_zero)
        butQuant.clicked.connect(self.quant_coeffs)

#------------------------------------------------------------------------------
    def _set_filter_type(self):
        """
        Change between FIR and IIR filter setting
        """
        
        if self.cmbFilterType.currentText() == 'FIR':
            fb.fil[0]['ft'] = 'FIR'            
        else:
            fb.fil[0]['ft'] = 'IIR'
            
        self.load_dict()

#------------------------------------------------------------------------------
    def store_entries(self):
        """
        Read out coefficients table and save the values to filter 'coeffs'
        and 'zpk' dicts. Is called when clicking the <Save> button, triggers
        a recalculation and replot of all plot widgets.
        """
        coeffs = []
        num_rows, num_cols = self.tblCoeff.rowCount(), self.tblCoeff.columnCount()
        logger.debug("store_entries: \n%s rows x  %s cols" %(num_rows, num_cols))

        if self.cmbFilterType.currentText() ==  'IIR':
            fb.fil[0]['ft'] = 'IIR'
            fb.fil[0]['fc'] = 'Manual_IIR'
            self.cmbFilterType.setCurrentIndex(1) # set to "IIR"
        else:
            fb.fil[0]['ft'] = 'FIR'
            fb.fil[0]['fc'] = 'Manual_FIR'
            self.cmbFilterType.setCurrentIndex(0) # set to "FIR"


#        if num_cols > 1: # IIR
        for col in range(num_cols):
            rows = []
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                if item:
                    if item.text() != "":
                        rows.append(safe_eval(item.text()))
                else:
                    rows.append(0.)
#                    rows.append(float(item.text()) if item else 0.)
            if num_cols == 1:
                coeffs = rows
            else:
                coeffs.append(rows) # type: list num_cols x num_rows

        fb.fil[0]["N"] = num_rows - 1
        fb.fil[0]["q_coeff"] = {
                'QI':int(self.ledQuantI.text()),
                'QF':int(self.ledQuantF.text()),
                'quant':self.cmbQQuant.currentText(),
                'ovfl':self.cmbQOvfl.currentText(),
                'frmt':self.cmbQFormat.currentText()
                }

        fil_save(fb.fil[0], coeffs, 'ba', __name__)

        logger.debug("store_entries - coeffients / zpk updated:\n"
            "b,a = %s\n\n"
            "zpk = %s\n"
            %(pformat(fb.fil[0]['ba']), pformat(fb.fil[0]['zpk'])
              ))

        self.sigFilterDesigned.emit()  # -> input_tab_widgets -> pyfdax -> plt_tab_widgets.updateAll()
        # TODO: this also needs to trigger filter_specs.updateUI to switch to 
        #       manual design when saving b,a

#------------------------------------------------------------------------------
    def load_dict(self):
        """
        Create table from filter coeff dict
        """
        coeffs = fb.fil[0]['ba']
        num_rows = max(np.shape(coeffs))
        
        q_coeff = fb.fil[0]['q_coeff']
        self.ledQuantI.setText(str(q_coeff['QI']))
        self.ledQuantF.setText(str(q_coeff['QF']))       
        self.cmbQQuant.setCurrentIndex(self.cmbQQuant.findText(q_coeff['quant']))
        self.cmbQOvfl.setCurrentIndex(self.cmbQOvfl.findText(q_coeff['ovfl']))
        
        # check whether filter is FIR and only needs one column 
        if fb.fil[0]['ft'] == 'FIR':# and np.all(fb.fil[0]['zpk'][1]) == 0:
            num_cols = 1
            self.tblCoeff.setColumnCount(1)
            self.tblCoeff.setHorizontalHeaderLabels(["b"])
            self.cmbFilterType.setCurrentIndex(0) # set to "FIR"     
            
        else:
            num_cols = 2
            self.tblCoeff.setColumnCount(2)
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
            self.cmbFilterType.setCurrentIndex(1) # set to "IIR"       

            
        self.tblCoeff.setVisible(self.chkCoeffList.isChecked())
        self.tblCoeff.setRowCount(num_rows)
        self.tblCoeff.setColumnCount(num_cols)
        # create index strings for column 0, starting with 0
        idx_str = [str(n) for n in range(num_rows)]
        self.tblCoeff.setVerticalHeaderLabels(idx_str)

        logger.debug("load_dict - coeffs:\n"
            "Shape = %s\n"
            "Len   = %d\n"
            "NDim  = %d\n\n"
            "Coeffs = %s"
            %(np.shape(coeffs),len(coeffs), np.ndim(coeffs), pformat(coeffs))
              )

        for col in range(num_cols):
            for row in range(np.shape(coeffs)[1]):
                item = self.tblCoeff.item(row, col)
                # copy content of zpk to corresponding table field, rounding 
                # as specified and removing the brackets of complex arguments
                if item:
                    item.setText(str(cround(coeffs[col][row])).strip('()'))
                else:
                    self.tblCoeff.setItem(row,col,QTableWidgetItem(
                                str(cround(coeffs[col][row])).strip('()')))
        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()

#------------------------------------------------------------------------------
    def delete_rows(self):
        """
        Delete all selected rows by:
        - reading the indices of all selected cells
        - collecting the row numbers in a set (only unique elements)
        - sort the elements in a list in descending order
        - delete the rows starting at the bottom
        If nothing is selected, delete last row.
        """
        # returns index to rows:
#        rows = self.tblCoeff.selectionModel().selectedRows()
        nrows = self.tblCoeff.rowCount()
        indices = self.tblCoeff.selectionModel().selectedIndexes()
        rows = set()
        for index in indices:
            rows.add(index.row()) # collect all selected rows in a set
        if len(rows) == 0: # nothing selected
            rows = {nrows-1} # -> select last row
        rows = sorted(list(rows), reverse = True)# sort rows in decending order
        for r in rows:
#            self.tblCoeff.removeRow(r.row())
            self.tblCoeff.removeRow(r)
        self.tblCoeff.setRowCount(nrows - len(rows))

#------------------------------------------------------------------------------
    def add_rows(self):
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add 1 row.
        """
        old_rows = self.tblCoeff.rowCount()
        new_rows = len(self.tblCoeff.selectionModel().selectedRows()) + old_rows
        self.tblCoeff.setRowCount(new_rows)

        if old_rows == new_rows: # nothing selected
            new_rows = old_rows + 1 # add at least one row

        self.tblCoeff.setRowCount(new_rows)

        for col in range(2):
            for row in range(old_rows, new_rows):
                self.tblCoeff.setItem(row,col,QTableWidgetItem("0.0"))

        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()

#------------------------------------------------------------------------------
    def _clear_table(self):
        """
        Clear table & initialize coeff, zpk for two poles and zeros @ origin,
        a = b = [1; 0; 0]
        """
        self.tblCoeff.clear()
        self.tblCoeff.setRowCount(3)

        num_cols = self.tblCoeff.columnCount()
        
        if num_cols < 2:
            self.tblCoeff.setHorizontalHeaderLabels(["b"])
        else:
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
        
        for row in range(3):
            for col in range(num_cols):
                if row == 0:
                    self.tblCoeff.setItem(row,col,QTableWidgetItem("1.0"))
                else:
                    self.tblCoeff.setItem(row,col,QTableWidgetItem("0.0"))

#------------------------------------------------------------------------------
    def _set_coeffs_zero(self):
        """
        Set all coefficients = 0 in table with a magnitude less than eps
        """
        eps = float(self.ledSetEps.text())
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        for col in range(num_cols):
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                if item:
                    if abs(safe_eval(item.text())) < eps:
                        item.setText(str(0.))
                else:
                    self.tblCoeff.setItem(row,col,QTableWidgetItem("0.0"))

#------------------------------------------------------------------------------
    def quant_coeffs(self):
        """
        Quantize all coefficients
        """
        # define + instantiate fixed-point object
        myQ = fix.Fixed({'QI':int(self.ledQuantI.text()),
                         'QF':int(self.ledQuantF.text()),
                         'quant': self.cmbQQuant.currentText(),
                         'ovfl':self.cmbQOvfl.currentText(),
                         'frmt':self.cmbQFormat.currentText()})
                         
        num_rows, num_cols = self.tblCoeff.rowCount(),\
                                        self.tblCoeff.columnCount()
        for col in range(num_cols):
            for row in range(num_rows):
                item = self.tblCoeff.item(row, col)
                if item:
                    item.setText(str(myQ.fix(safe_eval(item.text()))))
                else:
                    self.tblCoeff.setItem(row,col,QTableWidgetItem("0.0"))

        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FilterCoeffs(None)

    app.setActiveWindow(mainw) 
    mainw.show()

    sys.exit(app.exec_())