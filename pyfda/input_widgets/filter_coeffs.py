# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Widget for displaying and modifying filter coefficients
"""





from __future__ import print_function, division, unicode_literals, absolute_import
import sys
from pprint import pformat
import logging
logger = logging.getLogger(__name__)

from ..compat import (Qt, QApplication, QWidget, QLabel, QLineEdit, QComboBox,
                      QFrame, QPushButton, QSpinBox, QFont, QIcon, QSize,
                      QAbstractItemView, QTableWidget, QTableWidgetItem,
                      QVBoxLayout, QHBoxLayout,
                      pyqtSignal, QEvent, QStyledItemDelegate)

import numpy as np

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, safe_eval, style_widget, set_cmb_box, qstr
from pyfda.pyfda_rc import params
import pyfda.pyfda_fix_lib as fix

# TODO: FIR / IIR - Filter detection: Save always switches to IIR -> _filter_type
# TODO: number of digits is limited to 12?!
# TODO: FIR / IIR chaos
# TODO: Edit coefficients in the selected output format
# TODO: Clipboard functionality
# TODO: enable / disable buttons, clean up UI
# TODO: what happens with complex / nearly real coefficients?
# TODO: Buttons with <Q> etc -> https://sarasoueidan.com/blog/icon-fonts-to-svg/
# TODO: Auto-Width (min. number of WI)
class ItemDelegate(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.

    `displayText()` displays the data stored in the table in various number formats
    

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" e.g. in a QTableWidgetItem and converted back when
    retrieved. In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    """
    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (FilterCoeffs)
        """
        super(ItemDelegate, self).__init__(parent)
        self.parent = parent # instance of the parent (not the base) class


    def displayText(self, text, locale):
        """
        Display `text` in the number format selected in the fixpoint object 

        text:   string / QVariant from QTableWidget to be rendered
        locale: locale for the text
        """ 
        data = qstr(text) # convert to "normal" string

        if self.parent.myQ.frmt == 'frac':
            return "{0:.{1}g}".format(safe_eval(data), params['FMT_ba'])
     #       return "{0:g}".format(safe_eval(data))
        else:
            return "{0:>{1}}".format(self.parent.myQ.repr_fix(data), self.parent.myQ.digits)
# see: http://stackoverflow.com/questions/30615090/pyqt-using-qtextedit-as-editor-in-a-qstyleditemdelegate

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
#        return QLineEdit(parent) # return object without instantiating      


    def setEditorData(self, editor, index):
        """
        Pass the data to be edited to the editor:
        - retrieve data with full accuracy from self.ba
        - requantize data according to settings in fixpoint object
        - represent it in the selected format (int, hex, ...)
        
        editor: instance of e.g. QLineEdit
        index:  instance of QModelIndex
        """
#        data = qstr(index.data()) # get data from QTableWidget
        data = self.parent.ba[index.column()][index.row()] # data from self.ba

        if self.parent.myQ.frmt == 'frac':
            editor.setText(str(safe_eval(data))) # no string formatting, pass full resolution
        else:
            editor.setText("{0:>{1}}".format(
                    self.parent.myQ.repr_fix(data), self.parent.myQ.digits))
#            print(self.parent.myQ.repr_fix(data), self.parent.myQ.digits)


    def setModelData(self, editor, model, index):
        """
        When editor has finished, read the updated data from the editor,
        convert it back to fractional format and store it in the model 
        (= QTableWidget) and in self.ba

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
        if self.parent.myQ.frmt == 'frac':
            data = safe_eval(qstr(editor.text())) # raw data without fixpoint formatting 
        else:
            data = self.parent.myQ.fix_base(qstr(editor.text())) # transform back to fractional
        model.setData(index, data)                          # store in QTableWidget 
        self.parent.ba[index.column()][index.row()] = data  # and in self.ba


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
#        q_icon_size = QSize(20, 20) # optional, size is derived from butEnable

#==============================================================================
#          #Which Button holds the longest Text?
#         MaxTextlen = 0
#         longestText = ""
#         ButLength = 0
#         butTexts = ["Add", "Delete", "Save", "Load", "Clear", "Set Zero", "< Q >"]
#
#         # Find the longest text + padding for subsequent bounding box calculation
#         for item in butTexts:
#             if len(item) > MaxTextlen:
#                 MaxTextlen = len(item)
#                 longestText = item + "mm" # this is the longest text + padding for
#
#         #Calculate the length for the buttons based on the longest ButtonText
#         #ButLength = butAddRow.fontMetrics().boundingRect(longestText).width()
#        butDelCell.setText(butTexts[1])
#        butDelCell.setMaximumWidth(ButLength)
#
#==============================================================================
        # ---------------------------------------------
        # UI Elements for controlling the display
        # ---------------------------------------------
        self.butEnable = QPushButton(self)
        self.butEnable.setIcon(QIcon(':/circle-check.svg'))
        q_icon_size = self.butEnable.iconSize() # <- uncomment this for manual sizing
        self.butEnable.setIconSize(q_icon_size)
        self.butEnable.setCheckable(True)
        self.butEnable.setChecked(True)
        self.butEnable.setToolTip("<span>Show filter coefficients as an editable table."
                "For high order systems, this might be slow.</span>")

        self.butQEnable = QPushButton(self)
        self.butQEnable.setIcon(QIcon(':/menu.svg'))
        self.butQEnable.setIconSize(q_icon_size)
        self.butQEnable.setCheckable(True)
        self.butQEnable.setChecked(True)
        self.butQEnable.setToolTip("<span>Show quantization options.</span>")

        self.cmbFormat = QComboBox(self)
        qFormat = ['Frac', 'Int', 'Hex', 'Bin', 'CSD']
        self.cmbFormat.addItems(qFormat)
        self.cmbFormat.setCurrentIndex(0) # 'frac'
        self.cmbFormat.setToolTip('Set the display format.')
        self.cmbFormat.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lblRound = QLabel("Digits = ", self)
        self.spnRound = QSpinBox(self)
        self.spnRound.setRange(0,16)
        self.spnRound.setValue(params['FMT_ba'])
        self.spnRound.setToolTip("Display <i>d</i> digits.")

        layHDisplay = QHBoxLayout()
        layHDisplay.setAlignment(Qt.AlignLeft)
        layHDisplay.addWidget(self.butEnable)
        layHDisplay.addWidget(self.butQEnable)
        layHDisplay.addWidget(self.cmbFormat)
        layHDisplay.addWidget(self.lblRound)
        layHDisplay.addWidget(self.spnRound)
        layHDisplay.addStretch()

        # ---------------------------------------------
        # UI Elements for loading / storing
        # ---------------------------------------------
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
        self.tblCoeff.setItemDelegate(ItemDelegate(self))


        butAddCells = QPushButton(self)
        butAddCells.setIcon(QIcon(':/plus.svg'))
        butAddCells.setIconSize(q_icon_size)
        butAddCells.setToolTip("<SPAN>Select cells to insert a new cell above each selected cell. "
                                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
                                "When nothing is selected, add a row at the end.</SPAN>")

        butDelCells = QPushButton(self)
        butDelCells.setIcon(QIcon(':/minus.svg'))
        butDelCells.setIconSize(q_icon_size)
        butDelCells.setToolTip("<span>Delete selected cell(s) from the table. "
                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells.</span>")

        self.butSave = QPushButton(self)
        self.butSave.setIcon(QIcon(':/upload.svg'))
        self.butSave.setIconSize(q_icon_size)
        self.butSave.setToolTip("<span>Save coefficients and update all plots. "
                                "No modifications are saved before!</span>")

        butLoad = QPushButton(self)
        butLoad.setIcon(QIcon(':/download.svg'))
        butLoad.setIconSize(q_icon_size)
        butLoad.setToolTip("Reload coefficients.")

        butClear = QPushButton(self)
        butClear.setIcon(QIcon(':/trash.svg'))
        butClear.setIconSize(q_icon_size)
        butClear.setToolTip("Clear all entries.")

        self.butClipboard = QPushButton(self)
        self.butClipboard.setIcon(QIcon(':/clipboard.svg'))
        self.butClipboard.setIconSize(q_icon_size)
        self.butClipboard.setToolTip("<span>Copy table to clipboard, selected items are copied as "
                            "displayed. When nothing is selected, the whole table "
                            "is copied with full precision in decimal format. </span>")

        layHButtonsCoeffs1 = QHBoxLayout()
        layHButtonsCoeffs1.addWidget(butAddCells)
        layHButtonsCoeffs1.addWidget(butDelCells)
        layHButtonsCoeffs1.addWidget(butClear)
        layHButtonsCoeffs1.addWidget(self.butSave)
        layHButtonsCoeffs1.addWidget(butLoad)
        layHButtonsCoeffs1.addWidget(self.butClipboard)
        layHButtonsCoeffs1.addWidget(self.cmbFilterType)
        layHButtonsCoeffs1.addStretch()
#---------------------------------------------------------

        butSetZero = QPushButton("= 0", self)
        butSetZero.setToolTip("<span>Set coefficients = 0 with a magnitude &lt; &epsilon;.</span>")
        butSetZero.setIconSize(q_icon_size)

        self.lblEps = QLabel(self)
        self.lblEps.setText("for b, a <")

        self.ledSetEps = QLineEdit(self)
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        butQuant = QPushButton(self)
        butQuant.setToolTip("Quantize coefficients with selected settings.")
        butQuant.setText("Q!")
        butQuant.setIconSize(q_icon_size)

        self.lblWIWF  = QLabel("WI.WF = ")
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

        self.clipboard = QApplication.clipboard()

        self.myQ = fix.Fixed(fb.fil[0]["q_coeff"]) # initialize fixpoint object


        # ============== UI Layout =====================================


        layHButtonsCoeffs2 = QHBoxLayout()
        layHButtonsCoeffs2.addWidget(butSetZero)
        layHButtonsCoeffs2.addWidget(self.lblEps)
        layHButtonsCoeffs2.addWidget(self.ledSetEps)
        layHButtonsCoeffs2.addStretch()

        layHButtonsCoeffs3 = QHBoxLayout()
        layHButtonsCoeffs3.addWidget(butQuant)
        layHButtonsCoeffs3.addWidget(self.lblWIWF)
        layHButtonsCoeffs3.addWidget(self.ledQuantI)
        layHButtonsCoeffs3.addWidget(self.lblDot)
        layHButtonsCoeffs3.addWidget(self.ledQuantF)
        layHButtonsCoeffs3.addStretch()

        layHButtonsCoeffs4 = QHBoxLayout()
        layHButtonsCoeffs4.addWidget(self.lblQOvfl)
        layHButtonsCoeffs4.addWidget(self.cmbQOvfl)
        layHButtonsCoeffs4.addWidget(self.lblQuant)
        layHButtonsCoeffs4.addWidget(self.cmbQQuant)
        layHButtonsCoeffs4.addStretch()

        layVButtonsQ = QVBoxLayout()
        layVButtonsQ.addLayout(layHButtonsCoeffs3)
        layVButtonsQ.addLayout(layHButtonsCoeffs4)

        self.frmQSettings = QFrame(self)
        self.frmQSettings.setLayout(layVButtonsQ)


        layVBtns = QVBoxLayout()
        layVBtns.addLayout(layHDisplay)
        layVBtns.addLayout(layHButtonsCoeffs1)
        layVBtns.addLayout(layHButtonsCoeffs2)
        layVBtns.addWidget(self.frmQSettings)
#        layVBtns.addLayout(layHButtonsCoeffs3)
#        layVBtns.addLayout(self.layHButtonsCoeffs4)

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
#        self.tblCoeff.selectionModel().currentChanged.connect(self.save_coeffs)
        self.butEnable.clicked.connect(self._refresh_table)
        self.spnRound.editingFinished.connect(self._refresh_table)
        self.butClipboard.clicked.connect(self._copy_to_clipboard)

        self.cmbFilterType.currentIndexChanged.connect(self._filter_type)

        butDelCells.clicked.connect(self._delete_cells)
        butAddCells.clicked.connect(self._add_cells)
        butLoad.clicked.connect(self.load_dict)
        self.butSave.clicked.connect(self._save_entries)
        butClear.clicked.connect(self._clear_table)
        butSetZero.clicked.connect(self._set_coeffs_zero)

        self.cmbFormat.currentIndexChanged.connect(self._store_q_settings)
        self.cmbQOvfl.currentIndexChanged.connect(self._store_q_settings)
        self.cmbQQuant.currentIndexChanged.connect(self._store_q_settings)
        self.ledQuantF.editingFinished.connect(self._store_q_settings)
        self.ledQuantI.editingFinished.connect(self._store_q_settings)

        butQuant.clicked.connect(self.quant_coeffs)

#        self.tblCoeff.cellChanged.connect(self._copy_item)
#        self.tblCoeff.dropEvent.connect(self._copy_item)

#------------------------------------------------------------------------------
    def _filter_type(self, fil_type=None):
        """
        Get / set 'FIR' and 'IIR' filter type:
            When type is not declared, read cmbFilterType combobox and set filter
            dict accordingly.

            When type is declared as 'auto', check whether all items of a = self.ba[1]
            are zero except for the first one. If true, it's an 'IIR', otherwise
            it's a 'FIR' filter.
            Set cmbFilterType combobox and filter dict accordingly.
        """
        if not fil_type: # no argument, read out combobox
            if self.cmbFilterType.currentText() == 'IIR':
                ft = 'IIR'
            else:
                ft = 'FIR'
        else:
            if fil_type == 'auto': # determine type of filter from coefficients
                if np.any(self.ba[1][0:]):
                    ft = 'IIR'
                else:
                    ft = 'FIR'

            if fil_type == 'IIR': # filter type has been specified
                ft = 'IIR'
            else:
                ft = 'IIR'

        if ft == 'IIR':
            self.col = 2
            set_cmb_box(self.cmbFilterType, 'IIR')
            self.tblCoeff.setColumnCount(2)
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
        else:
            self.col = 1
            set_cmb_box(self.cmbFilterType, 'FIR')
            self.tblCoeff.setColumnCount(1)
            self.tblCoeff.setHorizontalHeaderLabels(["b"])

        fb.fil[0]['ft'] = ft
        self.tblCoeff.setColumnCount(self.col)

        self.load_dict()

#------------------------------------------------------------------------------
    def _refresh_table(self):
        """
        (Re-)Create the displayed table from self.ba with the
        desired number format.

        Called at the end of nearly every method.
        """

        self.num_rows = max(len(self.ba[1]), len(self.ba[0]))

        params['FMT_ba'] = int(self.spnRound.text())

        self.spnRound.setEnabled(self.cmbFormat.currentIndex() == 0) # only enabled for
        self.lblRound.setEnabled(self.cmbFormat.currentIndex() == 0) # format = decimal

        if self.butEnable.isChecked():

            self.frmQSettings.setVisible(True)
            self.butEnable.setIcon(QIcon(':/circle-check.svg'))
            self.tblCoeff.setVisible(True)

            self._load_q_settings()

            # check whether filter is FIR and only needs one column
            if fb.fil[0]['ft'] == 'FIR':
                self.num_cols = 1
                self.tblCoeff.setColumnCount(1)
                self.tblCoeff.setHorizontalHeaderLabels(["b"])
                set_cmb_box(self.cmbFilterType, 'FIR')
            else:
                self.num_cols = 2
                self.tblCoeff.setColumnCount(2)
                self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
                set_cmb_box(self.cmbFilterType, 'IIR')

            self.tblCoeff.setRowCount(self.num_rows)
            self.tblCoeff.setColumnCount(self.num_cols)
            # Create strings for index column (vertical header), starting with "0"
            idx_str = [str(n) for n in range(self.num_rows)]
            self.tblCoeff.setVerticalHeaderLabels(idx_str)

            self.tblCoeff.blockSignals(True)
            for col in range(self.num_cols):
                for row in range(self.num_rows):
                    # set table item from self.ba and strip '()' of complex numbers
                    item = self.tblCoeff.item(row, col)
                    if item: # does item exist?
                        item.setText(str(self.ba[col][row]).strip('()'))
                    else: # no, construct it:
                        self.tblCoeff.setItem(row,col,QTableWidgetItem(
                              str(self.ba[col][row]).strip('()')))
                    self.tblCoeff.item(row, col).setTextAlignment(Qt.AlignRight)

            self.tblCoeff.blockSignals(False)

            self.tblCoeff.resizeColumnsToContents()
            self.tblCoeff.resizeRowsToContents()
            self.tblCoeff.clearSelection()

            self._copy_to_clipboard()

        else:
            self.frmQSettings.setVisible(False)
            self.butEnable.setIcon(QIcon(':/circle-x.svg'))
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
        self.ba[0] = np.array(fb.fil[0]['ba'][0], dtype = complex)
        self.ba[1] = np.array(fb.fil[0]['ba'][1], dtype = complex)

        # set comboBoxes from dictionary
        self._load_q_settings()

        self._refresh_table()
        style_widget(self.butSave, 'normal')

#------------------------------------------------------------------------------
    def _copy_item(self):
        """
        Copy the value from the current table item to self.ba
        This is triggered every time a table item is edited.
        When no item was selected, do nothing.

        Triggered by  `tblCoeff.cellChanged`

        """
        # multiple selection:
        #idx = self._get_selected(self.tblCoeff)['idx']
        #for x in idx:
        #    print(self.tblCoeff.item(x[0],x[1]).text())

        col = self.tblCoeff.currentIndex().column()
        row = self.tblCoeff.currentIndex().row()
        item = self.tblCoeff.item(row,col)


        if item:
            if item.text() != "":
                self.ba[col][row] = safe_eval(item.text())
            else:
                self.ba[col][row] = 0.

        style_widget(self.butSave, 'changed')

#------------------------------------------------------------------------------
    def _store_q_settings(self):
        """
        read out the settings of the quantization comboboxes and store them in
        filter dict. Update the fixpoint object.
        """
        fb.fil[0]['q_coeff'] = {
                'WI':int(self.ledQuantI.text()),
                'WF':int(self.ledQuantF.text()),
                'quant':self.cmbQQuant.currentText(),
                'ovfl':self.cmbQOvfl.currentText(),
                'frmt':self.cmbFormat.currentText()
                }
        self.myQ.setQobj(fb.fil[0]['q_coeff'])
        self._refresh_table()

#------------------------------------------------------------------------------
    def _load_q_settings(self):
        """
        load the quantization settings from the filter dict and set the widgets
        accordingly. Update the fixpoint object.
        """
        q_coeff = fb.fil[0]['q_coeff']
        self.ledQuantI.setText(str(q_coeff['WI']))
        self.ledQuantF.setText(str(q_coeff['WF']))
        set_cmb_box(self.cmbQQuant, q_coeff['quant'])
        set_cmb_box(self.cmbQOvfl,  q_coeff['ovfl'])
        set_cmb_box(self.cmbFormat, q_coeff['frmt'])

        self.myQ.setQobj(fb.fil[0]['q_coeff'])

#------------------------------------------------------------------------------
    def _save_entries(self):
        """
        Save the values from self.ba to the filter ba dict.
        """

        logger.debug("=====================\nFilterCoeff._save_entries called")

        fb.fil[0]['N'] = max(len(self.ba[0]), len(self.ba[1])) - 1
        # TODO: The following doesn't work, needs to check whether this is IIR / FIR
        if np.any(self.ba[1]): # any denominator coefficients?
            fb.fil[0]['fc'] = 'Manual_IIR'
        else:
            fb.fil[0]['fc'] = 'Manual_FIR'

        fb.fil[0]["q_coeff"] = {
                'WI':int(self.ledQuantI.text()),
                'WF':int(self.ledQuantF.text()),
                'quant':self.cmbQQuant.currentText(),
                'ovfl':self.cmbQOvfl.currentText(),
                'frmt':self.cmbFormat.currentText()
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
        style_widget(self.butSave, 'normal')

#------------------------------------------------------------------------------
    def _clear_table(self):
        """
        Clear self.ba: Initialize coeff for two poles and zeros @ origin,
        a = b = [1; 0; 0]. Initialize with dtype complex to avoid errors
        if the data type becomes complex later on.
        Refresh QTableWidget
        """
        self.ba = np.array([[1, 0, 0], [1, 0, 0]], dtype = np.complex)

        self._refresh_table()
        style_widget(self.butSave, 'changed')

#------------------------------------------------------------------------------
    def _copy_to_clipboard(self):
        """
        Copy table from self.ba to clipboard as CSV list
        """
        text = ""
        tab = "\t"  # tab character
        cr = "\n"   # newline character

        sel = self._get_selected(self.tblCoeff)['sel']   
        if not np.any(sel): # nothing selected
            for r in range(self.num_rows):
                for c in range(self.num_cols):
                    text += str(self.ba[c][r])
                    if c != self.num_cols:
                        text += tab
                if r != self.num_rows:
                    text += cr
        else:
            for r in sel[0]:
                text += str(self.ba[0][r])
            text += cr 
            for r in sel[1]:
                text += str(self.ba[1][r])
            

        self.clipboard.setText(text)

        #self.textLabel.setText(self.clipboard.text())


#==============================================================================
#         void MyTableWidget::keyPressEvent(QKeyEvent* event) {
#     // If Ctrl-C typed
#     // Or use event->matches(QKeySequence::Copy)
#     if (event->key() == Qt::Key_C && (event->modifiers() & Qt::ControlModifier))
#     {
#         QModelIndexList cells = selectedIndexes();
#         qSort(cells); // Necessary, otherwise they are in column order
#
#         QString text;
#         int currentRow = 0; // To determine when to insert newlines
#         foreach (const QModelIndex& cell, cells) {
#             if (text.length() == 0) {
#                 // First item
#             } else if (cell.row() != currentRow) {
#                 // New row
#                 text += '\n';
#             } else {
#                 // Next cell
#                 text += '\t';
#             }
#             currentRow = cell.row();
#             text += cell.data().toString();
#         }
#
#         QApplication::clipboard()->setText(text);
#     }
# }
#==============================================================================

#------------------------------------------------------------------------------
    def _get_selected(self, table):
        """
        get selected cells and return:
        - indices of selected cells
        - list of selected cells per column, sorted in reverse
        - current cell selection
        """
        idx = []
        for _ in table.selectedItems():
            idx.append([_.column(), _.row(), ])

        sel = [0, 0]
        sel[0] = sorted([i[1] for i in idx if i[0] == 0], reverse = True)
        sel[1] = sorted([i[1] for i in idx if i[0] == 1], reverse = True)

        # use set comprehension to eliminate multiple identical entries
        # cols = sorted(list({i[0] for i in idx}))
        # rows = sorted(list({i[1] for i in idx}))
        cur = (table.currentColumn(), table.currentRow())
        # cur_idx_row = table.currentIndex().row()
        return {'idx':idx, 'sel':sel, 'cur':cur}# 'rows':rows 'cols':cols, }

#------------------------------------------------------------------------------
    def _equalize_ba_length(self):
        """
        test and equalize if b and a subarray have different lengths:
        """
        D = len(self.ba[0]) - len(self.ba[1])

        if D > 0: # b is longer than a
            self.ba[1] = np.append(self.ba[1], np.zeros(D))
        elif D < 0: # a is longer than b
            if fb.fil[0] == 'IIR':
                self.ba[0] = np.append(self.ba[0], np.zeros(-D))
            else:
                self.ba[1] = self.ba[1][:D] # discard last D elements of a

#------------------------------------------------------------------------------
    def _delete_cells(self):
        """
        Delete all selected elements in self.ba by:
        - determining the indices of all selected cells in the P and Z arrays
        - deleting elements with those indices
        - equalizing the lengths of b and a array by appending the required
          number of zeros.
        Finally, the QTableWidget is refreshed from self.ba.
        """
        # TODO: FIR and IIR need to be treated separately
        sel = self._get_selected(self.tblCoeff)['sel'] # get indices of all selected cells

        self.ba[0] = np.delete(self.ba[0], sel[0])
#        if fb.fil[0]['ft'] == 'IIR': # not necessary?
        self.ba[1] = np.delete(self.ba[1], sel[1])

        # test and equalize if b and a array have different lengths:
        self._equalize_ba_length()
        self._refresh_table()
        style_widget(self.butSave, 'changed')


#------------------------------------------------------------------------------
    def _add_cells(self):
        """
        Add the number of selected rows to self.ba and fill new cells with
        zeros. If nothing is selected, add one row at the bottom.
        Refresh QTableWidget.
        """
        # get indices of all selected cells
        sel = self._get_selected(self.tblCoeff)['sel']

        if not np.any(sel):
            sel[0] = [len(self.ba[0])]
            sel[1] = [len(self.ba[1])]

        self.ba[0] = np.insert(self.ba[0], sel[0], 0)
        self.ba[1] = np.insert(self.ba[1], sel[1], 0)

        # insert 'sel' contiguous rows  before 'row':
        # self.ba[0] = np.insert(self.ba[0], row, np.zeros(sel))

        self._equalize_ba_length()
        self._refresh_table()
        style_widget(self.butSave, 'changed')

#------------------------------------------------------------------------------
    def _set_coeffs_zero(self):
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        eps = float(self.ledSetEps.text())
        sel = self._get_selected(self.tblCoeff)['idx'] # get all selected indices

        if not sel: # nothing selected, check whole table
            self.ba[0] = self.ba[0] * np.logical_not(
                                        np.isclose(self.ba[0], 0., rtol=0, atol = eps))
            self.ba[1] = self.ba[1] * np.logical_not(
                                        np.isclose(self.ba[1], 0., rtol=0, atol = eps))

        else: # only check selected cells
            for i in sel:
                self.ba[i[0]][i[1]] = self.ba[i[0]][i[1]] * np.logical_not(
                                         np.isclose(self.ba[i[0]][i[1]], 0., rtol=0, atol = eps))

        style_widget(self.butSave, 'changed')
        self._refresh_table()

#------------------------------------------------------------------------------
    def quant_coeffs(self):
        """
        Quantize all coefficients in self.ba and refresh QTableWidget
        """

        self._store_q_settings() # read comboboxes and store setting in filter dict
        # always save quantized coefficients in fractional format
        # -> change output format to 'frac' before quantizing and storing in self.ba
        self.myQ.frmt = 'frac'

#        for i in range(len(self.ba[0])):
#            self.ba[0][i] = self.myQ.fix(self.ba[0][i])
#            if i > 0: # don't quantize first "1" in denonimator polynome
#                self.ba[1][i] = self.myQ.fix(self.ba[1][i])
        self.ba = self.myQ.fix(self.ba)
        self.ba[1][0] = 1 # restore first "1" in denonimator polynome

        style_widget(self.butSave, 'changed')
        self._refresh_table()

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FilterCoeffs(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())