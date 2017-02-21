# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying and modifying filter coefficients
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, six
from pprint import pformat
import logging
logger = logging.getLogger(__name__)

from ..compat import (Qt, QWidget, QLabel, QLineEdit, QComboBox, QFrame,
                      QPushButton, QSpinBox, QFont, QIcon, QSize,
                      QAbstractItemView, QTableWidget, QTableWidgetItem,
                      QVBoxLayout, QHBoxLayout,
                      pyqtSignal, QEvent, QStyledItemDelegate)

import numpy as np

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, safe_eval, style_widget, set_cmb_box
from pyfda.pyfda_rc import params
import pyfda.pyfda_fix_lib as fix


# TODO: eliminate trailing zeros for filter order calculation

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
    def __init__(self, parent, inst):
        """
        pass instance using this class as a parameter to access attributes here
        """
        super(ItemDelegate, self).__init__(parent)
        self.coeff_inst = inst


    def displayText(self, text, locale):

        def tohex(val, nbits):
            return hex((val + (1 << nbits)) % (1 << nbits))
            # np.set_printoptions(formatter={'int':hex})

        if not isinstance(text, six.text_type): #
            text = text.toString() # needed for Python 2, doesn't work with Py3
        idx = self.coeff_inst.cmbFormat.currentIndex()

        W = fb.fil[0]['q_coeff']['QI'] + fb.fil[0]['q_coeff']['QF'] + 1

        dec = int(safe_eval(text) * 2**W)
        dec_digits = int(np.ceil(np.log10(2 ** W))+2) # required number of digits for dec. repr.

        if idx == 0: # fractional format
            return "{:.{n_digits}g}".format(safe_eval(text), n_digits = params['FMT_ba'])
        elif idx == 1: # decimal format
            return "{0:>{1}}".format(dec, dec_digits)# , n_digits = int(np.ceil(np.log10(2 ** W))))
        elif idx == 2: # hex format
            return "{0}".format(tohex(dec, W))
        else:
            return "{0}".format(np.binary_repr(dec, width = W))


class FilterCoeffs(QWidget):
    """
    Create widget for viewing / editing / entering data
    """
    sigFilterDesigned = pyqtSignal()  # emitted when coeffs have been changed

    def __init__(self, parent):
        super(FilterCoeffs, self).__init__(parent)

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        bfont = QFont()
        bfont.setBold(True)
        q_icon_size = QSize(20, 20)

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

        #Calculate the length for the buttons based on the longest ButtonText
        #ButLength = butAddRow.fontMetrics().boundingRect(longestText).width()

        self.cmbFormat = QComboBox(self)
        qFormat = ['Frac', 'Dec', 'Hex', 'Bin']
        self.cmbFormat.addItems(qFormat)
        self.cmbFormat.setCurrentIndex(0) # 'frac'
        self.cmbFormat.setToolTip('Set the display and output format.')
        self.cmbFormat.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lblRound = QLabel("Digits = ", self)
        self.spnRound = QSpinBox(self)
        self.spnRound.setRange(0,9)
        self.spnRound.setValue(params['FMT_ba'])
        self.spnRound.setToolTip("Display <i>d</i> digits.")

        self.cmbFilterType = QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip("FIR filters only have zeros (b coefficients).")
        self.cmbFilterType.addItems(["FIR","IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)


        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setAlternatingRowColors(True)
        self.tblCoeff.horizontalHeader().setHighlightSections(True) # highlight when selected
        self.tblCoeff.horizontalHeader().setFont(bfont)

#        self.tblCoeff.QItemSelectionModel.Clear
        self.tblCoeff.setDragEnabled(True)
#        self.tblCoeff.setDragDropMode(QAbstractItemView.InternalMove) # doesn't work like intended
        self.tblCoeff.setItemDelegate(ItemDelegate(self, self))

        self.butEnable = QPushButton(self)
        self.butEnable.setIcon(QIcon(':/circle-check.svg'))
        self.butEnable.setIconSize(q_icon_size)
        self.butEnable.setCheckable(True)
        self.butEnable.setChecked(True)
        self.butEnable.setToolTip("<span>Show filter coefficients as an editable table."
                "For high order systems, this might be slow. </span>")

        butAddCells = QPushButton(self)
        butAddCells.setIcon(QIcon(':/plus.svg'))
        butAddCells.setIconSize(q_icon_size)
        # butAddRow.setText(butTexts[0])
        butAddCells.setToolTip("<SPAN>Select cells to insert a new cell above each selected cell. "
                                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
                                "When nothing is selected, add a row at the end.</SPAN>")
#        butAddRow.setMaximumWidth(ButLength)

        butDelCells = QPushButton(self)
        butDelCells.setIcon(QIcon(':/minus.svg'))
        butDelCells.setIconSize(q_icon_size)        
        butDelCells.setToolTip("<span>Delete selected cell(s) from the table. "
                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells.</span>")
#        butDelCell.setText(butTexts[1])
        #butDelCell.setMaximumWidth(ButLength)

        self.butSave = QPushButton(self)
        # butSave.setText(butTexts[2])
        self.butSave.setIcon(QIcon(':/upload.svg'))
        self.butSave.setIconSize(q_icon_size)
        self.butSave.setToolTip("<span>Save coefficients and update all plots. "
                                "No modifications are saved before!</span>")

        #butSave.setMaximumWidth(ButLength)

        butLoad = QPushButton(self)
        butLoad.setIcon(QIcon(':/download.svg'))
        butLoad.setIconSize(q_icon_size)
        # butLoad.setText(butTexts[3])
        butLoad.setToolTip("Reload coefficients.")
        #butLoad.setMaximumWidth(ButLength)

        butClear = QPushButton(self)
        butClear.setIcon(QIcon(':/trash.svg'))
        butClear.setIconSize(q_icon_size)
        # butClear.setText(butTexts[4])
        butClear.setToolTip("Clear all entries.")
        #butClear.setMaximumWidth(ButLength)

        butSetZero = QPushButton(butTexts[5], self)
        butSetZero.setToolTip("<span>Set coefficients = 0 with a magnitude &lt; &epsilon;.</span>")
        butSetZero.setIconSize(q_icon_size)
#        butSetZero.setMaximumWidth(ButLength)

        self.lblEps = QLabel(self)
        self.lblEps.setText("for b, a <")

        self.ledSetEps = QLineEdit(self)
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        butQuant = QPushButton(self)
        butQuant.setToolTip("Quantize coefficients with selected settings.")
        butQuant.setText("Q!")
        butQuant.setIconSize(q_icon_size)

#        butQuant.setText(butTexts[6])
#        butQuant.setMaximumWidth(ButLength)

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

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbQOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # ============== UI Layout =====================================
        layHChkBoxes = QHBoxLayout()
        layHChkBoxes.setAlignment(Qt.AlignLeft)
        layHChkBoxes.addWidget(self.butEnable)
        layHChkBoxes.addWidget(self.cmbFormat)
        layHChkBoxes.addWidget(self.lblRound)
        layHChkBoxes.addWidget(self.spnRound)
        layHChkBoxes.addStretch()        


        layHButtonsCoeffs1 = QHBoxLayout()
        layHButtonsCoeffs1.addWidget(butAddCells)
        layHButtonsCoeffs1.addWidget(butDelCells)
        layHButtonsCoeffs1.addWidget(butClear)

        layHButtonsCoeffs1.addWidget(self.butSave)
        layHButtonsCoeffs1.addWidget(butLoad)
        layHButtonsCoeffs1.addWidget(self.cmbFilterType)
        layHButtonsCoeffs1.addStretch()

        layHButtonsCoeffs2 = QHBoxLayout()
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
        self.frmQSettings = QFrame(self)
        self.frmQSettings.setLayout(layHButtonsCoeffs3)
        

        self.layHButtonsCoeffs4 = QHBoxLayout()
        self.layHButtonsCoeffs4.addWidget(self.lblQOvfl)
        self.layHButtonsCoeffs4.addWidget(self.cmbQOvfl)
        self.layHButtonsCoeffs4.addWidget(self.lblQuant)
        self.layHButtonsCoeffs4.addWidget(self.cmbQQuant)
        self.layHButtonsCoeffs4.addStretch()

        layVBtns = QVBoxLayout()
        layVBtns.addLayout(layHChkBoxes)  
        layVBtns.addLayout(layHButtonsCoeffs1)
        layVBtns.addLayout(layHButtonsCoeffs2)
        layVBtns.addWidget(self.frmQSettings)
#        layVBtns.addLayout(layHButtonsCoeffs3)
        
        layVBtns.addLayout(self.layHButtonsCoeffs4)

        # This frame encompasses all the buttons
        frmMain = QFrame(self)
        frmMain.setLayout(layVBtns)

        layVMain = QVBoxLayout()
        layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addWidget(frmMain)
        layVMain.addWidget(self.tblCoeff)
        layVMain.setContentsMargins(*params['wdg_margins'])
#        layVMain.addStretch(1)
        self.setLayout(layVMain)

        self.load_dict() # initialize table with default values from filter dict
        # TODO: needed?
        self._refresh_table()

        # ============== Signals & Slots ================================
#        self.tblCoeff.itemActivated.connect(self.save_coeffs) # nothing happens
        # this works but fires multiple times _and_ fires every time cell is
        # changed by program as well!
#        self.tblCoeff.itemChanged.connect(self.save_coeffs)
#        self.tblCoeff.clicked.connect(self.save_coeffs)
#        self.tblCoeff.selectionModel().currentChanged.connect(self.save_coeffs)
        self.spnRound.editingFinished.connect(self._refresh_table)

        butLoad.clicked.connect(self.load_dict)
        self.butEnable.clicked.connect(self.load_dict)

        butSave.clicked.connect(self._save_entries)

        self.cmbFilterType.currentIndexChanged.connect(self._set_filter_type)

        butDelCell.clicked.connect(self._delete_cells)
        butAddRow.clicked.connect(self._add_rows)

        butClear.clicked.connect(self._clear_table)
        butSetZero.clicked.connect(self._set_coeffs_zero)
        butQuant.clicked.connect(self.quant_coeffs)

        self.tblCoeff.cellChanged.connect(self._copy_item)

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
    def _refresh_table(self):
        """
        (Re-)Create the displayed table from self.ba with the
        desired number format.

        Called at the end of nearly every method.
        """

        params['FMT_ba'] = int(self.spnRound.text())

        if self.butEnable.isChecked():

            self.tblCoeff.setVisible(True)

            num_rows = max(len(self.ba[0]), len(self.ba[1]))

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
                %(np.shape(self.ba),len(self.ba), np.ndim(self.ba), pformat(self.ba))
                  )

            for col in range(num_cols):
                    for row in range(len(self.ba[col])):
                        # set table item from self.ba and strip '()' of complex numbers
                        item = self.tblCoeff.item(row, col)
                        if item: # does item exist?
                            item.setText(str(self.ba[col][row]).strip('()'))
                        else: # no, construct it:
                            self.tblCoeff.setItem(row,col,QTableWidgetItem(
                                  str(self.ba[col][row]).strip('()')))

            self.tblCoeff.resizeColumnsToContents()
            self.tblCoeff.resizeRowsToContents()
            self.tblCoeff.clearSelection()
            
        else:
            self.tblCoeff.setVisible(False)
            

#------------------------------------------------------------------------------
    def load_dict(self):
        """
        Load all entries from filter dict fb.fil[0]['ba'] into the shadow
        register self.ba and update the display.
        
        The shadow register is a list of two ndarrays to allow different
        lengths for b and a subarrays while adding / deleting items. 
        The explicit np.array( ... ) statement enforces a deep copy of fb.fil[0],
        otherwise the filter dict would be modified inadvertedly. Enforcing the 
        type np.complex is necessary, otherwise operations creating complex 
        coefficient values (or complex user entries) create errors.
        """
        
        self.ba = [0, 0]
        self.ba[0] = np.array(fb.fil[0]['ba'], dtype = complex)[0] # this enforces a deep copy
        self.ba[1] = np.array(fb.fil[0]['ba'], dtype = complex)[1]

        # set comboBoxes from dictionary
        self.ledQuantI.setText(str(fb.fil[0]['q_coeff']['QI']))
        self.ledQuantF.setText(str(fb.fil[0]['q_coeff']['QF']))
        set_cmb_box(self.cmbQQuant, fb.fil[0]['q_coeff']['quant']) 
        set_cmb_box(self.cmbQOvfl, fb.fil[0]['q_coeff']['ovfl'])
        set_cmb_box(self.cmbFormat, fb.fil[0]['q_coeff']['frmt']) 
                
        self._refresh_table()

#------------------------------------------------------------------------------
    def _copy_item(self):
        """
        Copy the value from the current table item to self.ba
        This is triggered every time a table item is edited.
        When no item was selected, do nothing.

        Triggered by  `tblCoeff.cellChanged`

        """
        col = self.tblCoeff.currentIndex().column()
        row = self.tblCoeff.currentIndex().row()
        item = self.tblCoeff.item(row,col)

        if item:
            if item.text() != "":
                self.ba[col][row] = safe_eval(item.text())
            else:
                self.ba[col][row] = 0.

#------------------------------------------------------------------------------
    def _save_entries(self):
        """
        Save the values from self.ba to the filter BA dict.
        """

        logger.debug("=====================\nFilterCoeff._save_entries called")

        fb.fil[0]['N'] = max(len(self.ba[0]), len(self.ba[1])) - 1
        # TODO: The following doesn't work, needs to check whether this is IIR / FIR
        if np.any(self.ba[1]): # any denominator coefficients?
            fb.fil[0]['fc'] = 'Manual_IIR'
        else:
            fb.fil[0]['fc'] = 'Manual_FIR'

        fb.fil[0]["q_coeff"] = {
                'QI':int(self.ledQuantI.text()),
                'QF':int(self.ledQuantF.text()),
                'quant':self.cmbQQuant.currentText(),
                'ovfl':self.cmbQOvfl.currentText(),
                'frmt':self.cmbQFormat.currentText()
                }

        fil_save(fb.fil[0], self.ba, 'ba', __name__) # save as coeffs

        if __name__ == '__main__':
            self.load_dict() # only needed for stand-alone test

        self.sigFilterDesigned.emit() # -> filter_specs
        # -> input_tab_widgets -> pyfdax -> plt_tab_widgets.updateAll()

        logger.debug("_save_entries - coeffients / zpk updated:\n"
            "b,a = %s\n\n"
            "zpk = %s\n"
            %(pformat(fb.fil[0]['ba']), pformat(fb.fil[0]['zpk'])
              ))

#------------------------------------------------------------------------------
    def _clear_table(self):
        """
        Clear table & initialize coeff for two poles and zeros @ origin,
        a = b = [1; 0; 0]
        """
        self.ba = np.array([[1, 0, 0], [1, 0, 0]], dtype = np.complex)

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
    def _equalize_ba_length(self):
        # test and equalize if b and a subarray have different lengths:
        D = len(self.ba[0]) - len(self.ba[1])
        if D > 0:
            self.ba[1] = np.append(self.ba[1], np.zeros(D))
        elif D < 0:
            self.ba[0] = np.append(self.ba[0], np.zeros(-D))

#------------------------------------------------------------------------------
    def _delete_cells(self):
        """
        Delete all selected elements by:
        - determining the indices of all selected cells in the P and Z arrays
        - deleting elements with those indices
        - equalizing the lengths of B and A array by appending the required
          number of zeros.
        Finally, the table is refreshed from self.ba.
        """
        # TODO: FIR and IIR need to be treated separately
        sel = self._get_selected(self.tblCoeff)['idx'] # get all selected indices
        B = [s[1] for s in sel if s[0] == 0] # all selected indices in 'Z' column
        A = [s[1] for s in sel if s[0] == 1] # all selected indices in 'P' column
        print(B,A)

        # Delete array entries with selected indices. If nothing is selected
        # (B and A are empty), delete the last row.
        if len(B) < 1 and len(A) < 1:
            B = [len(self.ba[0])-1]
            A = [len(self.ba[1])-1]
        self.ba[0] = np.delete(self.ba[0], B)
        self.ba[1] = np.delete(self.ba[1], A)

        # test and equalize if B and a array have different lengths:
        self._equalize_ba_length()
#        self._delete_PZ_pairs()
        self._refresh_table()
        
#------------------------------------------------------------------------------
    def _add_rows(self):
        """
        Add the number of selected rows to the table and fill new cells with
        zeros. If nothing is selected, add 1 row.
        """
        row = self.tblCoeff.currentRow()
        sel = len(self._get_selected(self.tblCoeff)['rows'])
        # TODO: evaluate and create non-contiguous selections as well?

        if sel == 0: # nothing selected ->
            sel = 1 # add at least one row ...
            row = min(len(self.ba[0]), len(self.ba[1])) # ... at the bottom

        self.ba[0] = np.insert(self.ba[0], row, np.zeros(sel))
        self.ba[1] = np.insert(self.ba[1], row, np.zeros(sel))

        self._equalize_ba_length()
        self._refresh_table()


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
        Quantize all coefficients and refresh table
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