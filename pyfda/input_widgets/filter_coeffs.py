# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Widget for displaying and modifying filter coefficients
"""

from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

import sys

from ..compat import (Qt, QtCore, QWidget, QLabel, QLineEdit, QComboBox, QApplication,
                      QPushButton, QFrame, QSpinBox, QCheckBox, QFont, QIcon, QSize,
                      QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
                      pyqtSignal, QEvent, QStyledItemDelegate, QColor, QBrush)

import numpy as np

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, safe_eval
from pyfda.pyfda_qt_lib import (qstyle_widget, qset_cmb_box, qget_cmb_box, qstr, 
                                qcopy_to_clipboard, qget_selected)
from pyfda.pyfda_rc import params
import pyfda.pyfda_fix_lib as fix

# TODO: Clipboard functionality: - always use table display
#                                - always return a vertical table
#                                - always return fractional data with full precision?
# TODO: Setting complex data (manually) crashes the app in setModelData():
#    model.setData(index, data) "Type Error: Can't convert complex to float"
#   -> need to implement a proper model-view architecture, QTableView instead of QTableWidget
#    somewhere downstream a "" string is created from this which causes an error 
#    in safe_eval
# TODO: Strip parentheses of complex argument @ setEditorData()

# TODO: detect overflows during quantization and color cells - 
#      add another array to fix to store over / underflows
# TODO: This ItemDelegate method displayText is called again and again when an 
#        item is selected?!

# TODO: FIR and IIR need to be treated separately in _add / _delete_cells?
# TODO: Need to refresh table after _load_q_settings?
# TODO: convert to a proper Model-View-Architecture using QTableView
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


#==============================================================================
#     def paint(self, painter, option, index):
#         """
#         Override painter
#         
#         painter: instance of QPainter
#         option:  instance of QStyleOptionViewItemV4
#         index:   instance of QModelIndex
#         
#         see http://www.mimec.org/node/305
#         """
#         index_role = index.data(Qt.AccessibleDescriptionRole).toString()
#         
#         if index_role == QtCore.QLatin1String("separator"):
#             print("separator!")
#             y = (option.rect.top() + option.rect.bottom()) / 2
#             #        painter.setPen(option.palette.color( QPalette.Active, QPalette.Dark ) )
#             painter.drawLine(option.rect.left(), y, option.rect.right(), y )
#         else:
#             # continue with the original `paint()` method
#             super(ItemDelegate, self).paint(painter, option, index)
# 
#==============================================================================

    def initStyleOption(self, option, index):
        """
        Initialize `option` with the values using the `index` index. When the 
        item (0,1) is processed, it is styled especially. All other items are 
        passed to the original `initStyleOption()` which then calls `displayText()`.
        """
        if index.row() == 0 and index.column() == 1: # a[0]: always 1
            option.text = "1" # QString object
            option.font.setBold(True) 
            option.displayAlignment = Qt.AlignRight | Qt.AlignCenter
            # see http://zetcode.com/gui/pyqt5/painting/ : 
            option.backgroundBrush = QBrush(Qt.BDiagPattern)#QColor(100, 200, 100, 200))
            option.backgroundBrush.setColor(QColor(100, 100, 100, 200))
            # option.state           
        else:
            # continue with the original `initStyleOption()`
            super(ItemDelegate, self).initStyleOption(option, index)
        
    def text(self, item):
        """
        Return item text as string transformed by self.displayText()
        """
        # return qstr(item.text()) # convert to "normal" string
        return  qstr(self.displayText(item.text(), QtCore.QLocale()))

    def displayText(self, text, locale):
        """
        Display `text` with selected fixpoint base and number of places

        text:   string / QVariant from QTableWidget to be rendered
        locale: locale for the text
        """ 
        string = qstr(text) # convert to "normal" string

        if self.parent.myQ.frmt == 'float':
            data = safe_eval(string)
            return "{0:.{1}g}".format(data, params['FMT_ba'])
        else:
            return "{0:>{1}}".format(self.parent.myQ.float2frmt(string), 
                                        self.parent.myQ.places)
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

    def updateEditorGeometry(self, editor, option, index):
        """
        Updates the editor for the item specified by index according to the option given
        """
        super(ItemDelegate, self).updateEditorGeometry(editor, option, index) # default
        # TODO: implement
        
    def setEditorData(self, editor, index):
        """
        Pass the data to be edited to the editor:
        - retrieve data with full accuracy from self.ba
        - store data in fb.data_old in fractional format
        - requantize data according to settings in fixpoint object
        - represent it in the selected format (int, hex, ...)

        editor: instance of e.g. QLineEdit
        index:  instance of QModelIndex
        """
#        data = qstr(index.data()) # get data from QTableWidget
        data = self.parent.ba[index.column()][index.row()] # data from self.ba
        fb.data_old = data # store old data in floating point format
        
        if self.parent.myQ.frmt == 'float':
            # fractional format: pass data with full resolution
            editor.setText(str(safe_eval(data))) 
        else:
            # integer format with base: pass requantized data with required number of places
            editor.setText("{0:>{1}}".format(self.parent.myQ.float2frmt(data),
                                               self.parent.myQ.places))

    def setModelData(self, editor, model, index):
        """
        When editor has finished, read the updated data from the editor,
        convert it back to floating point format and store it in the model 
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
        if self.parent.myQ.frmt == 'float':
            data = safe_eval(qstr(editor.text()), fb.data_old) # raw data without fixpoint formatting 
        else:
            data = self.parent.myQ.frmt2float(qstr(editor.text()),
                                    self.parent.myQ.frmt) # transform back to float

        model.setData(index, data)                          # store in QTableWidget 
        self.parent.ba[index.column()][index.row()] = data  # and in self.ba
        qstyle_widget(self.parent.butSave, 'changed')
        

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
        self.bfont = QFont()
        self.bfont.setBold(True) 
        self.bifont = QFont()
        self.bifont.setBold(True)
        self.bifont.setItalic(True)
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

        self.cmbFormat = QComboBox(self)
#        self.cmbFormat.addItem('Float')
        qFormat = ['Float', 'Dec', 'Hex', 'Bin', 'CSD']
        self.cmbFormat.addItems(qFormat)
        self.cmbFormat.insertSeparator(1)
        self.cmbFormat.setCurrentIndex(0) # 'float'
        self.cmbFormat.setToolTip('Set the display format.')
        self.cmbFormat.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lblRound = QLabel("Digits = ", self)
        self.spnRound = QSpinBox(self)
        self.spnRound.setRange(0,16)
        self.spnRound.setValue(params['FMT_ba'])
        self.spnRound.setToolTip("Display <i>d</i> digits.")
        
        self.chkRadixPoint = QCheckBox("Radix point", self)
        self.chkRadixPoint.setToolTip("<span>Show and use radix point (= decimal"
                    " point for base 10) for fixpoint formats (still disabled).</span>")
        self.chkRadixPoint.setChecked(False)
        self.chkRadixPoint.setCheckable(True)

        layHDisplay = QHBoxLayout()
        layHDisplay.setAlignment(Qt.AlignLeft)
        layHDisplay.addWidget(self.butEnable)
        layHDisplay.addWidget(self.cmbFormat)
        layHDisplay.addWidget(self.lblRound)
        layHDisplay.addWidget(self.spnRound)
        layHDisplay.addWidget(self.chkRadixPoint)
        layHDisplay.addStretch()

        # ---------------------------------------------
        # UI Elements for loading / storing
        # ---------------------------------------------
        self.cmbFilterType = QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip("Select between IIR and FIR filte for manual entry.")
        self.cmbFilterType.addItems(["FIR","IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setAlternatingRowColors(True)
        self.tblCoeff.horizontalHeader().setHighlightSections(True) # highlight when selected
        self.tblCoeff.horizontalHeader().setFont(self.bfont)

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
        butDelCells.setToolTip("<SPAN>Delete selected cell(s) from the table. "
                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
                "When nothing is selected, delete the last row.</SPAN>")
                
        butQuant = QPushButton(self)
        butQuant.setToolTip("<span>Quantize selected coefficients with specified settings. "
        "When nothing is selected, quantize the whole table.</span>")
#        butQuant.setText("Q!")
        butQuant.setIcon(QIcon(':/quantize.svg'))
        butQuant.setIconSize(q_icon_size)

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
        layHButtonsCoeffs1.addWidget(butQuant)
        layHButtonsCoeffs1.addWidget(butClear)
        layHButtonsCoeffs1.addWidget(self.butSave)
        layHButtonsCoeffs1.addWidget(butLoad)
        layHButtonsCoeffs1.addWidget(self.butClipboard)
        layHButtonsCoeffs1.addWidget(self.cmbFilterType)
        layHButtonsCoeffs1.addStretch()
#---------------------------------------------------------

        butSetZero = QPushButton("= 0", self)
        butSetZero.setToolTip("<span>Set selected coefficients = 0 with a magnitude &lt; &epsilon;. "
        "When nothing is selected, test the whole table.</span>")
        butSetZero.setIconSize(q_icon_size)

        self.lblEps = QLabel(self)
        self.lblEps.setText("for b, a <")

        self.ledSetEps = QLineEdit(self)
        self.ledSetEps.setToolTip("Specify eps value.")
        self.ledSetEps.setText(str(1e-6))

        self.lblWIWF  = QLabel("W = ")
        self.lblWIWF.setFont(self.bifont)
        self.lblQOvfl = QLabel("Ovfl.:")
        self.lblQuant = QLabel("Quant.:")

        self.ledW = QLineEdit(self)
        self.ledW.setToolTip("Specify wordlength.")
        self.ledW.setText("16")
        self.ledW.setMaxLength(2) # maximum of 2 digits
        self.ledW.setFixedWidth(30) # width of lineedit in points(?)

        self.ledWI = QLineEdit(self)
        self.ledWI.setToolTip("Specify number of integer bits.")
        self.ledWI.setText("0")
        self.ledWI.setMaxLength(2) # maximum of 2 digits
        self.ledWI.setFixedWidth(30) # width of lineedit in points(?)

        self.lblDot = QLabel(self)
        self.lblDot.setText(".")

        self.ledWF = QLineEdit(self)
        self.ledWF.setToolTip("Specify number of fractional bits.")
        self.ledWF.setText("15")
        self.ledWF.setMaxLength(2) # maximum of 2 digits
#        self.ledWF.setFixedWidth(30) # width of lineedit in points(?)
        self.ledWF.setMaximumWidth(30)
        
        self.lblScale = QLabel("Scale = ", self) 
        self.ledScale = QLineEdit(self)
        self.ledScale.setToolTip("Set the scale for converting float to fixpoint representation.") 
        self.ledScale.setText(str(1))        

        self.lblLSBtxt = QLabel(self)
        self.lblLSBtxt.setText("LSB =")
        self.lblLSBtxt.setFont(self.bifont)
        self.lblLSB = QLabel(self)

        self.lblMSBtxt = QLabel(self)
        self.lblMSBtxt.setText("MSB =")
        self.lblMSBtxt.setFont(self.bifont)
        self.lblMSB = QLabel(self)

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


        # ============== UI Layout =====================================


        layHButtonsCoeffs2 = QHBoxLayout()
        layHButtonsCoeffs2.addWidget(butSetZero)
        layHButtonsCoeffs2.addWidget(self.lblEps)
        layHButtonsCoeffs2.addWidget(self.ledSetEps)
        layHButtonsCoeffs2.addStretch()

        layHCoeffs_W = QHBoxLayout()
        layHCoeffs_W.addWidget(self.lblWIWF)
        layHCoeffs_W.addWidget(self.ledW)
        layHCoeffs_W.addWidget(self.ledWI)
        layHCoeffs_W.addWidget(self.lblDot)
        layHCoeffs_W.addWidget(self.ledWF)
        layHCoeffs_W.addWidget(self.lblScale)
        layHCoeffs_W.addWidget(self.ledScale)
    
        layHCoeffs_W.addStretch()

        layHCoeffsQOpt = QHBoxLayout()
        layHCoeffsQOpt.addWidget(self.lblQOvfl)
        layHCoeffsQOpt.addWidget(self.cmbQOvfl)
        layHCoeffsQOpt.addWidget(self.lblQuant)
        layHCoeffsQOpt.addWidget(self.cmbQQuant)
        layHCoeffsQOpt.addStretch()
        
        layHCoeffs_MSB_LSB = QHBoxLayout()

        layHCoeffs_MSB_LSB.addWidget(self.lblMSBtxt)
        layHCoeffs_MSB_LSB.addWidget(self.lblMSB)
        layHCoeffs_MSB_LSB.addStretch()
        layHCoeffs_MSB_LSB.addWidget(self.lblLSBtxt)
        layHCoeffs_MSB_LSB.addWidget(self.lblLSB)
        layHCoeffs_MSB_LSB.addStretch()
        
        layVButtonsQ = QVBoxLayout()
        layVButtonsQ.addLayout(layHCoeffs_W)
        layVButtonsQ.addLayout(layHCoeffsQOpt)
        layVButtonsQ.addLayout(layHCoeffs_MSB_LSB)        
        layVButtonsQ.setContentsMargins(0,5,0,0)

        # This frame encompasses the Quantization Settings
        self.frmQSettings = QFrame(self)
        self.frmQSettings.setLayout(layVButtonsQ)

        layVBtns = QVBoxLayout()
        layVBtns.addLayout(layHDisplay)
        layVBtns.addLayout(layHButtonsCoeffs1)
        layVBtns.addLayout(layHButtonsCoeffs2)
        layVBtns.addWidget(self.frmQSettings)

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

        # ============== Signals & Slots ================================
#        self.tblCoeff.itemActivated.connect(self.save_coeffs) # nothing happens
        # this works but fires multiple times _and_ fires every time cell is
        # changed by program as well!
#        self.tblCoeff.itemChanged.connect(self.save_coeffs)
#        self.tblCoeff.selectionModel().currentChanged.connect(self.save_coeffs)
        self.butEnable.clicked.connect(self._refresh_table)
        self.spnRound.editingFinished.connect(self._refresh_table)
        self.chkRadixPoint.clicked.connect(self._radix_point)
        self.butClipboard.clicked.connect(self._copy_to_clipboard)

        self.cmbFilterType.currentIndexChanged.connect(self._filter_type)

        butDelCells.clicked.connect(self._delete_cells)
        butAddCells.clicked.connect(self._add_cells)
        butLoad.clicked.connect(self.load_dict)
        self.butSave.clicked.connect(self._save_entries)
        butClear.clicked.connect(self._clear_table)
        butSetZero.clicked.connect(self._set_coeffs_zero)

        # refresh table after storing new settings
        self.cmbFormat.currentIndexChanged.connect(self._refresh_table)
        self.cmbQOvfl.currentIndexChanged.connect(self._refresh_table)
        self.cmbQQuant.currentIndexChanged.connect(self._refresh_table)
        self.ledWF.editingFinished.connect(self._WIWF_changed)
        self.ledWI.editingFinished.connect(self._WIWF_changed)
        self.ledW.editingFinished.connect(self._W_changed)
        
        self.ledScale.editingFinished.connect(self._refresh_table)

        butQuant.clicked.connect(self.quant_coeffs)
        
        self.myQ = fix.Fixed(fb.fil[0]["q_coeff"]) # initialize fixpoint object                        
        self.load_dict() # initialize + refresh table with default values from filter dict
        # TODO: this needs to be optimized - self._refresh is being called in both routines
        self._radix_point()


#------------------------------------------------------------------------------
    def _filter_type(self, fil_type=None):
        """
        Get / set 'FIR' and 'IIR' filter from cmbFilterType combobox and set filter
            dict and table properties accordingly.
        """

        if self.cmbFilterType.currentText() == 'IIR':
            fb.fil[0]['ft'] = 'IIR'
            self.col = 2
            qset_cmb_box(self.cmbFilterType, 'IIR')
            self.tblCoeff.setColumnCount(2)
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])

        else:
            fb.fil[0]['ft'] = 'FIR'
            self.col = 1
            qset_cmb_box(self.cmbFilterType, 'FIR')
            self.tblCoeff.setColumnCount(1)
            self.tblCoeff.setHorizontalHeaderLabels(["b"])

        self.tblCoeff.setColumnCount(self.col)

        self.load_dict()


#------------------------------------------------------------------------------
    def _WIWF_changed(self):
        """
        Set wordlength `W` when `WI` or `WF` have been changed
        """
        WI = abs(int(safe_eval(self.ledWI.text(), self.myQ.WI)))
        WF = abs(int(safe_eval(self.ledWF.text(), self.myQ.WF)))
        self.ledW.setText(str(WF + WI + 1))
        self._store_q_settings()
        self._refresh_table()

#------------------------------------------------------------------------------
    def _W_changed(self):
        """
        Set fractional and integer length `WF` and `WI` when wordlength Ẁ` has
        been changed. Try to preserve `WI`setting except when `WF`would become
        negative.
        """
        W = int(safe_eval(self.ledW.text(), self.myQ.W))
        if W < 2:
            self.ledW.setText(str(self.myQ.W))
        WF = W - self.myQ.WI - 1
        if WF < 0:
            self.ledWI.setText(str(W - 1))
            WF = 0
            
        self.ledWF.setText(str(WF))
        self._store_q_settings()
        
        self._refresh_table()

#------------------------------------------------------------------------------
    def _radix_point(self):
        """
        Set variables and widgets depending on radix point
        """
        self.ledWI.setVisible(self.chkRadixPoint.isChecked())
        self.lblDot.setVisible(self.chkRadixPoint.isChecked())
        self.ledWF.setVisible(self.chkRadixPoint.isChecked())
        self.ledW.setVisible(not self.chkRadixPoint.isChecked())

        self._refresh_table()
        
        #------------------------------------------------------------------------------
    def _set_scale(self):
        """
        Set scale for calculating floating point value from fixpoint representation
        and vice versa
        """
        self.scale = safe_eval(self.ledScale.text(), self.myQ.scale)
        self.ledScale.setText(str(self.scale))

#------------------------------------------------------------------------------
    def _refresh_table(self):
        """
        (Re-)Create the displayed table from self.ba with the
        desired number format.

        Called at the end of nearly every method.
        """

        self.num_rows = max(len(self.ba[1]), len(self.ba[0]))

        params['FMT_ba'] = int(self.spnRound.text())

        # When format is 'float', disable all fixpoint options
        is_float = (qget_cmb_box(self.cmbFormat, data=False).lower() == 'float')
        
        self.spnRound.setVisible(is_float) # number of digits can only be selected 
        self.lblRound.setVisible(is_float) # for format = 'float'
        self.ledScale.setEnabled(True)
        self.chkRadixPoint.setVisible(not is_float)

        if self.butEnable.isChecked():
            self.frmQSettings.setVisible(not is_float) # hide all q-settings for float
            self.butEnable.setIcon(QIcon(':/circle-check.svg'))
            self.tblCoeff.setVisible(True)

            self._store_q_settings() # store updated quantization / format settings

            # check whether filter is FIR and only needs one column
            if fb.fil[0]['ft'] == 'FIR':
                self.num_cols = 1
                self.tblCoeff.setColumnCount(1)
                self.tblCoeff.setHorizontalHeaderLabels(["b"])
                qset_cmb_box(self.cmbFilterType, 'FIR')
            else:
                self.num_cols = 2
                self.tblCoeff.setColumnCount(2)
                self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
                qset_cmb_box(self.cmbFilterType, 'IIR')

                self.ba[1][0] = 1.0 # restore fa[0] = 1 of denonimator polynome
                   
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
                    self.tblCoeff.item(row, col).setTextAlignment(Qt.AlignRight|Qt.AlignCenter)

            # make a[0] unselectable
            if fb.fil[0]['ft'] == 'IIR':
                item = self.tblCoeff.item(0,1)
                item.setFlags(Qt.ItemIsSelectable)#|  Qt.ItemIsEnabled )
                item.setFont(self.bfont)

            self.tblCoeff.blockSignals(False)

            self.tblCoeff.resizeColumnsToContents()
            self.tblCoeff.resizeRowsToContents()
            self.tblCoeff.clearSelection()

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
        otherwise the filter dict would be modified inadvertedly. 
        """

        self.ba = [0., 0.]
        self.ba[0] = np.array(fb.fil[0]['ba'][0])
        self.ba[1] = np.array(fb.fil[0]['ba'][1])

        # set comboBoxes from dictionary
        self._load_q_settings()

        self._refresh_table()
        qstyle_widget(self.butSave, 'normal')
        
    #------------------------------------------------------------------------------
    def _copy_to_clipboard(self, tab = "\t", cr = None):
        
        qcopy_to_clipboard(self.tblCoeff, self.ba, self.clipboard)

#------------------------------------------------------------------------------
    def _store_q_settings(self):
        """
        read out the settings of the quantization comboboxes and store them in
        filter dict. Update the fixpoint object.
        """
        fb.fil[0]['q_coeff'] = {
                'WI':abs(int(self.ledWI.text())),
                'WF':abs(int(self.ledWF.text())),
                'quant':self.cmbQQuant.currentText(),
                'ovfl':self.cmbQOvfl.currentText(),
                'frmt':self.cmbFormat.currentText(),
                'point':self.chkRadixPoint.isChecked()
                } 
        self.myQ.setQobj(fb.fil[0]['q_coeff'])
        
        self.lblLSB.setText("{0:.{1}g}".format(self.myQ.LSB, params['FMT_ba']))
        self.lblMSB.setText("{0:.{1}g}".format(self.myQ.MSB, params['FMT_ba']))
        
        self.scale = safe_eval(self.ledScale.text(), self.myQ.scale)
        self.ledScale.setText(str(self.scale))



#------------------------------------------------------------------------------
    def _load_q_settings(self):
        """
        load the quantization settings from the filter dict and set the widgets
        accordingly. Update the fixpoint object.
        """
        q_coeff = fb.fil[0]['q_coeff']
        self.ledWI.setText(str(q_coeff['WI']))
        self.ledWF.setText(str(q_coeff['WF']))
        qset_cmb_box(self.cmbQQuant, q_coeff['quant'])
        qset_cmb_box(self.cmbQOvfl,  q_coeff['ovfl'])
        qset_cmb_box(self.cmbFormat, q_coeff['frmt'])
        self.chkRadixPoint.setChecked(q_coeff['point'])

        self.lblLSB.setText("{0:.{1}g}".format(self.myQ.LSB, params['FMT_ba']))
        self.lblMSB.setText("{0:.{1}g}".format(self.myQ.MSB, params['FMT_ba']))
        
        self.scale = safe_eval(self.ledScale.text(), self.myQ.scale)
        self.ledScale.setText(str(self.scale))

        self.myQ.setQobj(fb.fil[0]['q_coeff'])

#------------------------------------------------------------------------------
    def _save_entries(self):
        """
        Save the values from self.ba to the filter ba dict.
        """

        logger.debug("_save_entries called")

        fb.fil[0]['N'] = max(len(self.ba[0]), len(self.ba[1])) - 1

        fb.fil[0]["q_coeff"] = {
                'WI':int(self.ledWI.text()),
                'WF':int(self.ledWF.text()),
                'quant':self.cmbQQuant.currentText(),
                'ovfl':self.cmbQOvfl.currentText(),
                'frmt':self.cmbFormat.currentText(),
                'point':self.chkRadixPoint.isChecked()
                }

        # save, check and convert coeffs, check filter type            
        fil_save(fb.fil[0], self.ba, 'ba', __name__) 
        
        if fb.fil[0]['ft'] == 'IIR':
            fb.fil[0]['fc'] = 'Manual_IIR'
        else:
            fb.fil[0]['fc'] = 'Manual_FIR'


        if __name__ == '__main__':
            self.load_dict() # only needed for stand-alone test

        self.sigFilterDesigned.emit() # -> filter_specs
        # -> input_tab_widgets -> pyfdax -> plt_tab_widgets.updateAll()

        qstyle_widget(self.butSave, 'normal')

#------------------------------------------------------------------------------
    def _clear_table(self):
        """
        Clear self.ba: Initialize coeff for a poles and a zero @ origin,
        a = b = [1; 0].

        Refresh QTableWidget
        """
        self.ba = np.array([[1, 0], [1, 0]])

        self._refresh_table()
        qstyle_widget(self.butSave, 'changed')


#------------------------------------------------------------------------------
    def _equalize_ba_length(self):
        """
        test and equalize if b and a subarray have different lengths:
        """
        D = len(self.ba[0]) - len(self.ba[1])

        if D > 0: # b is longer than a
            self.ba[1] = np.append(self.ba[1], np.zeros(D))
        elif D < 0: # a is longer than b
            if fb.fil[0]['ft'] == 'IIR':
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
        When nothing is selected, delete the last row.
        Finally, the QTableWidget is refreshed from self.ba.
        """
        sel = qget_selected(self.tblCoeff)['sel'] # get indices of all selected cells
        if not np.any(sel) and len(self.ba[0] > 0):
            self.ba[0] = np.delete(self.ba[0], -1)
            self.ba[1] = np.delete(self.ba[1], -1)
        else:
            self.ba[0] = np.delete(self.ba[0], sel[0])
            self.ba[1] = np.delete(self.ba[1], sel[1])

        # test and equalize if b and a array have different lengths:
        self._equalize_ba_length()
        if len(self.ba[0]) < 2:
            self._clear_table()
        else:
            self._refresh_table()
            qstyle_widget(self.butSave, 'changed')


#------------------------------------------------------------------------------
    def _add_cells(self):
        """
        Add the number of selected rows to self.ba and fill new cells with
        zeros from the bottom. If nothing is selected, add one row at the bottom.
        Refresh QTableWidget.
        """
        # get indices of all selected cells
        sel = qget_selected(self.tblCoeff)['sel']

        if not np.any(sel):
            sel[0] = [len(self.ba[0])]
            sel[1] = [len(self.ba[1])]

        self.ba[0] = np.insert(self.ba[0], sel[0], 0)
        self.ba[1] = np.insert(self.ba[1], sel[1], 0)

        # insert 'sel' contiguous rows  before 'row':
        # self.ba[0] = np.insert(self.ba[0], row, np.zeros(sel))

        self._equalize_ba_length()
        self._refresh_table()
        qstyle_widget(self.butSave, 'changed')

#------------------------------------------------------------------------------
    def _set_coeffs_zero(self):
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        eps = float(self.ledSetEps.text())
        idx = qget_selected(self.tblCoeff)['idx'] # get all selected indices

        test_val = 0. # value against which array is tested
        targ_val = 0. # value which is set when condition is true
        
        if not idx: # nothing selected, check whole table
            b_0 = np.isclose(self.ba[0], test_val, rtol=0, atol = eps)
            if np.any(b_0): # found at least one coeff where condition was true         
                self.ba[0] = self.ba[0] * np.logical_not(b_0)
                qstyle_widget(self.butSave, 'changed')
            
            if  fb.fil[0]['ft'] == 'IIR':
                a_0 = np.isclose(self.ba[1], test_val, rtol=0, atol = eps)
                if np.any(a_0):
                    self.ba[1] = self.ba[1] * np.logical_not(a_0)
                    qstyle_widget(self.butSave, 'changed')

        else: # only check selected cells
            changed = False
            for i in idx:
                if np.isclose(self.ba[i[0]][i[1]], test_val, rtol=0, atol = eps):
                    self.ba[i[0]][i[1]] = targ_val
                    changed = True
            if changed:
                # mark save button as changed
                qstyle_widget(self.butSave, 'changed')
        self._refresh_table()

#------------------------------------------------------------------------------
    def quant_coeffs(self):
        """
        Quantize selected / all coefficients in self.ba and refresh QTableWidget
        """

        self._store_q_settings() # read comboboxes and store setting in filter dict
        # always save quantized coefficients in fractional format
        # -> change output format to 'float' before quantizing and storing in self.ba
        self.myQ.frmt = 'float'

        idx = qget_selected(self.tblCoeff)['idx'] # get all selected indices
        if not idx: # nothing selected, quantize all elements
            self.ba = self.myQ.fix(self.ba, to_float=True)
        else:
            for i in idx:
                self.ba[i[0]][i[1]] = self.myQ.fix(self.ba[i[0]][i[1]], to_float=True)

        qstyle_widget(self.butSave, 'changed')
        self._refresh_table()

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainw = FilterCoeffs(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())