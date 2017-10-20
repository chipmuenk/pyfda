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

from ..compat import (Qt, QtCore, QtGui, QWidget, QLabel, QLineEdit, QComboBox, QApplication,
                      QPushButton, QFrame, QSpinBox, QFont, QIcon, QSize,
                      QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QGridLayout,
                      pyqtSignal, QStyledItemDelegate, QColor, QBrush, QSizePolicy)

import numpy as np

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import fil_save, safe_eval
from pyfda.pyfda_qt_lib import (qstyle_widget, qset_cmb_box, qget_cmb_box, qstr, CSV_option_box,
                                qcopy_to_clipboard, qcopy_from_clipboard, qget_selected)
 
from pyfda.pyfda_rc import params
import pyfda.pyfda_fix_lib as fix

# TODO: implement checking for complex-valued filters somewhere (pyfda_lib?),
#       h[n] detects complex data (although it isn't)
# TODO: Fixpoint coefficients do not properly convert complex -> float when saving
#       the filter?
# TODO: This ItemDelegate method displayText is called again and again when an
#        item is selected?!
# TODO: negative values for WI don't work correctly
# TODO: Quantizing coefficients with setting "integer" produces zero values

# TODO: convert to a proper Model-View-Architecture using QTableView?

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
        Afterwards, check whether an fixpoint overflow has occured and color item
        background accordingly.
        """
        if index.row() == 0 and index.column() == 1: # a[0]: always 1
            option.text = "1" # QString object
            option.font.setBold(True)
            option.displayAlignment = Qt.AlignRight | Qt.AlignCenter
            # see http://zetcode.com/gui/pyqt5/painting/ :
            option.backgroundBrush = QBrush(Qt.BDiagPattern)#QColor(100, 200, 100, 200))
            option.backgroundBrush.setColor(QColor(100, 100, 100, 200))
            # don't continue with default initStyleOption... display routine ends here
        else:
            # continue with the original `initStyleOption()` and call displayText()
            super(ItemDelegate, self).initStyleOption(option, index)
            # test whether fixpoint conversion during displayText() created an overflow:
            if self.parent.myQ.ovr_flag > 0:
                # Color item backgrounds with pos. Overflows red
                option.backgroundBrush = QBrush(Qt.SolidPattern)
                option.backgroundBrush.setColor(QColor(100, 0, 0, 80))
            elif self.parent.myQ.ovr_flag < 0:
                # Color item backgrounds with neg. Overflows blue
                option.backgroundBrush = QBrush(Qt.SolidPattern)
                option.backgroundBrush.setColor(QColor(0, 0, 100, 80))


#==============================================================================
#     def paint(self, painter, option, index):
#
#         """
#         painter: instance of QPainter (default)
#         option:  instance of QStyleOptionViewItemV4
#         index:   instance of QModelIndex
#         """
#         logger.debug("Ovr_flag:".format(self.parent.myQ.ovr_flag))
#         print("paint_ovr:{0}.{1}:{2}".format(index.row(), index.column(), self.parent.myQ.ovr_flag))
#         #option.backgroundBrush = QBrush(QColor(000, 100, 100, 200)) # lightGray
#             #option.backgroundBrush.setColor(QColor(000, 100, 100, 200))
#         # continue with the original `paint()` method
#         #option.palette.setColor(QPalette.Window, QColor(Qt.red))
#         #option.palette.setColor(QPalette.Base, QColor(Qt.green))
#         super(ItemDelegate, self).paint(painter, option, index)
#         #painter.restore()
#
#==============================================================================

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

        The instance parameter myQ.ovr_flag is set to +1 or -1 for positive /
        negative overflows, else it is 0.
        """
        data_str = qstr(text) # convert to "normal" string

        if self.parent.myQ.frmt == 'float':
            data = safe_eval(data_str, return_type='auto') # convert to float
            return "{0:.{1}g}".format(data, params['FMT_ba'])
        else:
            return "{0:>{1}}".format(self.parent.myQ.float2frmt(data_str),
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

#    def updateEditorGeometry(self, editor, option, index):
#        """
#        Updates the editor for the item specified by index according to the option given
#        """
#        super(ItemDelegate, self).updateEditorGeometry(editor, option, index) # default

    def setEditorData(self, editor, index):
        """
        Pass the data to be edited to the editor:
        - retrieve data with full accuracy from self.ba (in float format)
        - requantize data according to settings in fixpoint object
        - represent it in the selected format (int, hex, ...)

        editor: instance of e.g. QLineEdit
        index:  instance of QModelIndex
        """
#        data = qstr(index.data()) # get data from QTableWidget
        data_str = qstr(safe_eval(self.parent.ba[index.column()][index.row()], return_type="auto"))

        if self.parent.myQ.frmt == 'float':
            # floating point format: pass data with full resolution
            editor.setText(data_str)
        else:
            # fixpoint format with base: pass requantized data with required number of places
            editor.setText("{0:>{1}}".format(self.parent.myQ.float2frmt(data_str),
                                               self.parent.myQ.places))

    def setModelData(self, editor, model, index):
        """
        When editor has finished, read the updated data from the editor,
        convert it back to floating point format and store it in both the model
        (= QTableWidget) and in self.ba. Finally, refresh the table item to 
        display it in the selected format (via `float2frmt()`).

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
            data = safe_eval(qstr(editor.text()), 
                             self.parent.ba[index.column()][index.row()], return_type='auto') # raw data without fixpoint formatting
        else:
            data = self.parent.myQ.frmt2float(qstr(editor.text()),
                                    self.parent.myQ.frmt) # transform back to float

        model.setData(index, data)                          # store in QTableWidget
        self.parent.ba[index.column()][index.row()] = data  # and in self.ba
        qstyle_widget(self.parent.butSave, 'changed')
        self.parent._refresh_table_item(index.row(), index.column()) # refresh table entry


class FilterCoeffs(QWidget):
    """
    Create widget with a (sort of) model-view architecture for viewing /
    editing / entering data contained in `self.ba` which is a list of two numpy
    arrays:

    - `self.ba[0]` contains the numerator coefficients ("b")
    - `self.ba[1]` contains the denominator coefficients ("a")

    The list don't neccessarily have the same length but they are always defined.
    For FIR filters, `self.ba[1][0] = 1`, all other elements are zero.

    The length of both lists can be egalized with `self._equalize_ba_length()`.

    Views / formats are handled by the ItemDelegate() class.
    """
    sigFilterDesigned = pyqtSignal()  # emitted when coeffs have been changed

    def __init__(self, parent):
        super(FilterCoeffs, self).__init__(parent)

        self.eps = 1.e-6 # initialize toleracce attribute
        self.opt_widget = None # handle for pop-up options widget
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

        # ---------------------------------------------
        # UI Elements for controlling the display
        # ---------------------------------------------
        self.butEnable = QPushButton(self)
        self.butEnable.setIcon(QIcon(':/circle-x.svg'))
        q_icon_size = self.butEnable.iconSize() # <- uncomment this for manual sizing
        self.butEnable.setIconSize(q_icon_size)
        self.butEnable.setCheckable(True)
        self.butEnable.setChecked(True)
        self.butEnable.setToolTip("<span>Show / hide filter coefficients as an editable table."
                "For high order systems, table display might be slow.</span>")

        fix_formats = ['Dec', 'Hex', 'Bin', 'CSD']
        self.cmbFormat = QComboBox(self)
        model = self.cmbFormat.model()
        item = QtGui.QStandardItem('Float')
        item.setData('child', Qt.AccessibleDescriptionRole)
        model.appendRow(item)

        item = QtGui.QStandardItem('Fixp.:')
        item.setData('parent', Qt.AccessibleDescriptionRole)
        item.setData(0, QtGui.QFont.Bold)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)# | Qt.ItemIsSelectable))
        model.appendRow(item)

        for idx in range(len(fix_formats)):
            item = QtGui.QStandardItem(fix_formats[idx])
#            item.setForeground(QtGui.QColor('red'))
            model.appendRow(item)

        self.cmbFormat.insertSeparator(1)
        qset_cmb_box(self.cmbFormat, 'float')
        self.cmbFormat.setToolTip('Set the display format.')
        self.cmbFormat.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.spnDigits = QSpinBox(self)
        self.spnDigits.setRange(0,16)
        self.spnDigits.setValue(params['FMT_ba'])
        self.spnDigits.setToolTip("Number of digits to display.")
        self.lblDigits = QLabel("Digits", self)
        self.lblDigits.setFont(self.bifont)

        self.cmbQFrmt = QComboBox(self)
        q_formats = [('Integer', 'qint' ), ('Norm. Frac.', 'qnfrac'), ('Fractional', 'qfrac')]
        for q in q_formats:
            self.cmbQFrmt.addItem(*q)

        self.lbl_W  = QLabel("W = ", self)
        self.lbl_W.setFont(self.bifont)

        self.ledW = QLineEdit(self)
        self.ledW.setToolTip("Specify total wordlength.")
        self.ledW.setText("16")
        self.ledW.setMaxLength(2) # maximum of 2 digits
        self.ledW.setFixedWidth(30) # width of lineedit in points(?)

        layHDisplay = QHBoxLayout()
        layHDisplay.setAlignment(Qt.AlignLeft)
        layHDisplay.addWidget(self.butEnable)
        layHDisplay.addWidget(self.cmbFormat)
        layHDisplay.addWidget(self.spnDigits)
        layHDisplay.addWidget(self.lblDigits)
        layHDisplay.addWidget(self.cmbQFrmt)
        layHDisplay.addWidget(self.lbl_W)
        layHDisplay.addWidget(self.ledW)
        layHDisplay.addStretch()

        # ---------------------------------------------
        # UI Elements for loading / storing / manipulating cells and rows
        # ---------------------------------------------

        self.cmbFilterType = QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip("<span>Select between IIR and FIR filter for manual entry."
                                      "Changing the type reloads the filter from the filter dict.</span>")
        self.cmbFilterType.addItems(["FIR","IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)


        butAddCells = QPushButton(self)
        butAddCells.setIcon(QIcon(':/row_insert_above.svg'))
        butAddCells.setIconSize(q_icon_size)
        butAddCells.setToolTip("<SPAN>Select cells to insert a new cell above each selected cell. "
                                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
                                "When nothing is selected, add a row at the end.</SPAN>")

        butDelCells = QPushButton(self)
        butDelCells.setIcon(QIcon(':/row_delete.svg'))
        butDelCells.setIconSize(q_icon_size)
        butDelCells.setToolTip("<SPAN>Delete selected cell(s) from the table. "
                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
                "When nothing is selected, delete the last row.</SPAN>")

        self.butSave = QPushButton(self)
        self.butSave.setIcon(QIcon(':/upload.svg'))
        self.butSave.setIconSize(q_icon_size)
        self.butSave.setToolTip("<span>Save coefficients and update all plots. "
                                "No modifications are saved before!</span>")

        butLoad = QPushButton(self)
        butLoad.setIcon(QIcon(':/download.svg'))
        butLoad.setIconSize(q_icon_size)
        butLoad.setToolTip("Reload coefficients.")

        self.butClear = QPushButton(self)
        self.butClear.setIcon(QIcon(':/trash.svg'))
        self.butClear.setIconSize(q_icon_size)
        self.butClear.setToolTip("Clear all entries.")

        butToClipboard = QPushButton(self)
        butToClipboard.setIcon(QIcon(':/to_clipboard.svg'))
        butToClipboard.setIconSize(q_icon_size)
        butToClipboard.setToolTip("<span>Copy table to clipboard, SELECTED items are copied as "
                            "displayed. When nothing is selected, the whole table "
                            "is copied with full precision in decimal format. </span>")

        butFromClipboard = QPushButton(self)
        butFromClipboard.setIcon(QIcon(':/from_clipboard.svg'))
        butFromClipboard.setIconSize(q_icon_size)
        butFromClipboard.setToolTip("<span>Copy clipboard to table.</span>")

        butSettingsClipboard = QPushButton(self)
        butSettingsClipboard.setIcon(QIcon(':/settings.svg'))
        butSettingsClipboard.setIconSize(q_icon_size)
        butSettingsClipboard.setToolTip("<span>Adjust settings for CSV format and whether "
                                "to copy to/from clipboard or file.</span>")

        layHButtonsCoeffs1 = QHBoxLayout()
        layHButtonsCoeffs1.addWidget(self.cmbFilterType)
        layHButtonsCoeffs1.addWidget(butAddCells)
        layHButtonsCoeffs1.addWidget(butDelCells)
        layHButtonsCoeffs1.addWidget(self.butClear)
        layHButtonsCoeffs1.addWidget(self.butSave)
        layHButtonsCoeffs1.addWidget(butLoad)
        layHButtonsCoeffs1.addWidget(butToClipboard)
        layHButtonsCoeffs1.addWidget(butFromClipboard)
        layHButtonsCoeffs1.addWidget(butSettingsClipboard)
        layHButtonsCoeffs1.addStretch()

        #-------------------------------------------------------------------
        #   Eps / set zero settings
        # ---------------------------------------------------------------------

        self.butSetZero = QPushButton("= 0", self)
        self.butSetZero.setToolTip("<span>Set selected coefficients = 0 with a magnitude &lt; &epsilon;. "
        "When nothing is selected, test the whole table.</span>")
        self.butSetZero.setIconSize(q_icon_size)

        lblEps = QLabel(self)
        lblEps.setText("<b><i>for b, a</i> &lt;</b>")

        self.ledEps = QLineEdit(self)
        self.ledEps.setToolTip("Specify tolerance value.")
        self.ledEps.setText(str(self.eps))

        layHButtonsCoeffs2 = QHBoxLayout()
        layHButtonsCoeffs2.addWidget(self.butSetZero)
        layHButtonsCoeffs2.addWidget(lblEps)
        layHButtonsCoeffs2.addWidget(self.ledEps)
        layHButtonsCoeffs2.addStretch()

        #-------------------------------------------------------------------
        #   QFormat and scale settings
        # ---------------------------------------------------------------------
        lbl_Q = QLabel("Q =", self)
        lbl_Q.setFont(self.bifont)

        self.ledWI = QLineEdit(self)
        self.ledWI.setToolTip("Specify number of integer bits.")
        self.ledWI.setText("0")
        self.ledWI.setMaxLength(2) # maximum of 2 digits
        self.ledWI.setFixedWidth(30) # width of lineedit in points(?)

        self.lblDot = QLabel(".", self) # class attribute, visibility is toggled
        self.lblDot.setFont(self.bfont)

        self.ledWF = QLineEdit(self)
        self.ledWF.setToolTip("Specify number of fractional bits.")
        self.ledWF.setText("15")
        self.ledWF.setMaxLength(2) # maximum of 2 digits
#        self.ledWF.setFixedWidth(30) # width of lineedit in points(?)
        self.ledWF.setMaximumWidth(30)

        self.lblScale = QLabel("<b><i>Scale</i> =</b>", self)
        self.ledScale = QLineEdit(self)
        self.ledScale.setToolTip("Set the scale for converting float to fixpoint representation.")
        self.ledScale.setText(str(1))

        layHWI_WF = QHBoxLayout()
        layHWI_WF.addWidget(lbl_Q)
        layHWI_WF.addWidget(self.ledWI)
        layHWI_WF.addWidget(self.lblDot)
        layHWI_WF.addWidget(self.ledWF)
        layHWI_WF.addStretch()

        layHScale = QHBoxLayout()
        layHScale.addWidget(self.lblScale)
        layHScale.addWidget(self.ledScale)
        layHScale.addStretch()

        layHW_Scale = QHBoxLayout()
        layHW_Scale.addLayout(layHWI_WF)
        layHW_Scale.addLayout(layHScale)

        #-------------------------------------------------------------------
        #   Quantization / Overflow / MSB / LSB settings
        # ---------------------------------------------------------------------

        lblQOvfl = QLabel("Ovfl.:", self)
        lblQOvfl.setFont(self.bifont)
        lblQuant = QLabel("Quant.:", self)
        lblQuant.setFont(self.bifont)

        self.cmbQOvfl = QComboBox(self)
        qOvfl = ['wrap', 'sat']
        self.cmbQOvfl.addItems(qOvfl)
        qset_cmb_box(self.cmbQOvfl, 'sat')
        self.cmbQOvfl.setToolTip("Select overflow behaviour.")
        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layHQOvflOpt = QHBoxLayout()
        layHQOvflOpt.addWidget(lblQOvfl)
        layHQOvflOpt.addWidget(self.cmbQOvfl)
        layHQOvflOpt.addStretch()

        self.cmbQuant = QComboBox(self)
        qQuant = ['none', 'round', 'fix', 'floor']
        self.cmbQuant.addItems(qQuant)
        qset_cmb_box(self.cmbQuant, 'round')
        self.cmbQuant.setToolTip("Select the kind of quantization.")
        self.cmbQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layHQuantOpt = QHBoxLayout()
        layHQuantOpt.addWidget(lblQuant)
        layHQuantOpt.addWidget(self.cmbQuant)
        layHQuantOpt.addStretch()

        self.butQuant = QPushButton(self)
        self.butQuant.setToolTip("<span>Quantize selected coefficients / "
        "whole table with specified settings.</span>")
        self.butQuant.setIcon(QIcon(':/quantize.svg'))
        self.butQuant.setIconSize(q_icon_size)
        self.butQuant.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        lblMSBtxt = QLabel(self)
        lblMSBtxt.setText("<b><i>MSB</i><sub>10</sub> =</b>")
        self.lblMSB = QLabel(self)
        layHMSB = QHBoxLayout()
        layHMSB.addWidget(lblMSBtxt)
        layHMSB.addWidget(self.lblMSB)
        layHMSB.addStretch()

        lblLSBtxt = QLabel(self)
        lblLSBtxt.setText("<b><i>LSB</i><sub>10</sub> =</b>")
        self.lblLSB = QLabel(self) #
        layHLSB = QHBoxLayout()
        layHLSB.addWidget(lblLSBtxt)
        layHLSB.addWidget(self.lblLSB)
        layHLSB.addStretch()

        layGQOpt = QGridLayout()
        layGQOpt.addLayout(layHQOvflOpt,0,0)
        layGQOpt.addLayout(layHQuantOpt, 0,1)
        layGQOpt.addWidget(self.butQuant, 0, 2, Qt.AlignCenter)
        layGQOpt.addLayout(layHMSB,1,0)
        layGQOpt.addLayout(layHLSB,1,1)

        #-------------------------------------------------------------------
        #   Display MAX
        # ---------------------------------------------------------------------

        lblMAXtxt = QLabel(self)
        lblMAXtxt.setText("<b><i>Max =</i></b>")
        self.lblMAX = QLabel(self)

        layHCoeffs_MAX = QHBoxLayout()
        layHCoeffs_MAX.addWidget(lblMAXtxt)
        layHCoeffs_MAX.addWidget(self.lblMAX)
        layHCoeffs_MAX.addStretch()

        # ---------------------------------------------------------------------
        #   Coefficient table widget
        # ---------------------------------------------------------------------
        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setAlternatingRowColors(True)
        self.tblCoeff.horizontalHeader().setHighlightSections(True) # highlight when selected
        self.tblCoeff.horizontalHeader().setFont(self.bfont)

#        self.tblCoeff.QItemSelectionModel.Clear
        self.tblCoeff.setDragEnabled(True)
#        self.tblCoeff.setDragDropMode(QAbstractItemView.InternalMove) # doesn't work like intended
        self.tblCoeff.setItemDelegate(ItemDelegate(self))

        # Create clipboard instance
        self.clipboard = QApplication.clipboard()

        # ============== Main UI Layout =====================================

        layVButtonsQ = QVBoxLayout()
        layVButtonsQ.addLayout(layHW_Scale)
        layVButtonsQ.addLayout(layGQOpt)
        layVButtonsQ.addLayout(layHCoeffs_MAX)
        layVButtonsQ.setContentsMargins(0,5,0,0)

        # This frame encompasses all Quantization Settings
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
        # wdg.textChanged() is emitted when contents of widget changes
        # wdg.textEdited() is only emitted for user changes
        # wdg.editingFinished() is only emitted for user changes
        self.butEnable.clicked.connect(self._refresh_table)
        self.spnDigits.editingFinished.connect(self._refresh_table)

        self.cmbQFrmt.currentIndexChanged.connect(self._set_number_format)
        butSettingsClipboard.clicked.connect(self._copy_options)
        butToClipboard.clicked.connect(self._copy_to_clipboard)
        butFromClipboard.clicked.connect(self._copy_from_clipboard)

        self.cmbFilterType.currentIndexChanged.connect(self._filter_type)

        butDelCells.clicked.connect(self._delete_cells)
        butAddCells.clicked.connect(self._add_cells)
        butLoad.clicked.connect(self.load_dict)
        self.butSave.clicked.connect(self._save_dict)
        self.butClear.clicked.connect(self._clear_table)
        self.ledEps.editingFinished.connect(self._set_eps)
        self.butSetZero.clicked.connect(self._set_coeffs_zero)

        # refresh table after storing new settings
        self.cmbFormat.currentIndexChanged.connect(self._refresh_table)
        self.cmbQOvfl.currentIndexChanged.connect(self._refresh_table)
        self.cmbQuant.currentIndexChanged.connect(self._refresh_table)
        self.ledWF.editingFinished.connect(self._WIWF_changed)
        self.ledWI.editingFinished.connect(self._WIWF_changed)
        self.ledW.editingFinished.connect(self._W_changed)

        self.ledScale.editingFinished.connect(self._set_scale)

        self.butQuant.clicked.connect(self.quant_coeffs)

        self.myQ = fix.Fixed(fb.fil[0]["q_coeff"]) # initialize fixpoint object
        self.load_dict() # initialize + refresh table with default values from filter dict
        # TODO: this needs to be optimized - self._refresh is being called in both routines
        self._set_number_format()


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
        Store values for 'WI' and 'WF' when either has been changed, 
        update wordlength `W` accordingly and update table
        """
        self._store_q_settings()
        self._refresh_table()

#------------------------------------------------------------------------------
    def _W_changed(self):
        """
        Set fractional and integer length `WF` and `WI` when wordlength Ẁ` has
        been changed. Try to preserve `WI` or `WF` settings depending on the
        number format (integer or fractional).
        """
        
        # if self.ledW.isModified() ... self.ledW.setModified(False)
        W = safe_eval(self.ledW.text(), self.myQ.W, return_type='int', sign='pos')

        if W < 2:
            logger.warn("W must be > 1, restoring previous value.")
            W = self.myQ.W # fall back to previous value
        self.ledW.setText(str(W))

        if qget_cmb_box(self.cmbQFrmt) == 'qint': # integer format, preserve WI bits
            WI = W - self.myQ.WF - 1
            self.ledWI.setText(str(WI))
            self.ledScale.setText(str(1 << (W-1)))
        else: # fractional format, preserve WF bit setting
            WF = W - self.myQ.WI - 1
            if WF < 0:
                self.ledWI.setText(str(W - 1))
                WF = 0
            self.ledWF.setText(str(WF))

        self._store_q_settings()
        self._refresh_table()

#------------------------------------------------------------------------------
    def _set_number_format(self):
        """
        Set one of three number formats: Integer, fractional, normalized fractional
        """

        qfrmt = qget_cmb_box(self.cmbQFrmt)
        is_qfrac = False
        W = safe_eval(self.ledW.text(), self.myQ.W, return_type='int', sign='pos')
        if qfrmt == 'qint':
            self.ledWI.setText(str(W - 1))
            self.ledWF.setText("0")
            self.ledScale.setText(str(1 << (W-1)))
        elif qfrmt == 'qnfrac': # normalized fractional format
            self.ledWI.setText("0")
            self.ledWF.setText(str(W - 1))
            self.ledScale.setText("1")
        else: # qfrmt == 'qfrac':
            is_qfrac = True

        self.ledWI.setEnabled(is_qfrac)
        self.lblDot.setEnabled(is_qfrac)
        self.ledWF.setEnabled(is_qfrac)
        self.ledW.setEnabled(not is_qfrac)
        self.ledScale.setEnabled(is_qfrac)

        self._store_q_settings()
        self._refresh_table()

        #------------------------------------------------------------------------------
    def _set_scale(self):
        """
        Set scale for calculating floating point value from fixpoint representation
        and vice versa
        """
        # if self.ledScale.isModified() ... self.ledScale.setModified(False)
        scale = safe_eval(self.ledScale.text(), self.myQ.scale, return_type='float', sign='pos')
        self.ledScale.setText(str(scale))
        self._store_q_settings()
        self._refresh_table()

#------------------------------------------------------------------------------
    def _refresh_table_item(self, row, col):
        """
        Refresh the table item with the index `row, col` from self.ba
        """
        item = self.tblCoeff.item(row, col)
        if item: # does item exist?
            item.setText(str(self.ba[col][row]).strip('()'))
        else: # no, construct it:
            self.tblCoeff.setItem(row,col,QTableWidgetItem(
                  str(self.ba[col][row]).strip('()')))
        self.tblCoeff.item(row, col).setTextAlignment(Qt.AlignRight|Qt.AlignCenter)

#------------------------------------------------------------------------------
    def _refresh_table(self):
        """
        (Re-)Create the displayed table from `self.ba` (list with 2 columns of
        float scalars). Data is displayed via `ItemDelegate.displayText()` in
        the number format set by `self.frmt`.

        The table dimensions are set according to the dimensions of `self.ba`:
        - self.ba[0] -> b coefficients
        - self.ba[1] -> a coefficients

        Called at the end of nearly every method.
        """
        try:
            self.num_rows = max(len(self.ba[1]), len(self.ba[0]))
        except IndexError:
            self.num_rows = len(self.ba[0])
        logger.debug("np.shape(ba) = {0}".format(np.shape(self.ba)))

        params['FMT_ba'] = int(self.spnDigits.text())

        # When format is 'float', disable all fixpoint options
        is_float = (qget_cmb_box(self.cmbFormat, data=False).lower() == 'float')

        self.spnDigits.setVisible(is_float) # number of digits can only be selected
        self.lblDigits.setVisible(is_float) # for format = 'float'
        self.cmbQFrmt.setVisible(not is_float) # hide unneeded widgets for format = 'float'
        self.lbl_W.setVisible(not is_float)
        self.ledW.setVisible(not is_float)

        if self.butEnable.isChecked():
            self.frmQSettings.setVisible(not is_float) # hide all q-settings for float
            self.butEnable.setIcon(QIcon(':/circle-x.svg'))
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
                    self._refresh_table_item(row, col)

            # make a[0] selectable but not editable
            if fb.fil[0]['ft'] == 'IIR':
                item = self.tblCoeff.item(0,1)
                item.setFlags(Qt.ItemIsSelectable| Qt.ItemIsEnabled)
                item.setFont(self.bfont)

            self.tblCoeff.blockSignals(False)

            self.tblCoeff.resizeColumnsToContents()
            self.tblCoeff.resizeRowsToContents()
            self.tblCoeff.clearSelection()

        else:
            self.frmQSettings.setVisible(False)
            self.butEnable.setIcon(QIcon(':/circle-check.svg'))
            self.tblCoeff.setVisible(False)

#------------------------------------------------------------------------------
    def load_dict(self):
        """
        Load all entries from filter dict `fb.fil[0]['ba']` into the coefficient
        list `self.ba` and update the display via `self._refresh_table()`.

        The filter dict is a "normal" 2D-numpy float array for the b and a coefficients
        while the coefficient register `self.ba` is a list of two float ndarrays to allow
        for different lengths of b and a subarrays while adding / deleting items.
        """

        self.ba = [0., 0.] # initial list with two elements
        self.ba[0] = np.array(fb.fil[0]['ba'][0]) # deep copy from filter dict to
        self.ba[1] = np.array(fb.fil[0]['ba'][1]) # coefficient register

        # set comboBoxes from dictionary
        self._load_q_settings()

        self._refresh_table()
        qstyle_widget(self.butSave, 'normal')

    #------------------------------------------------------------------------------
    def _copy_options(self):
        """
        Set options for copying to/from clipboard or file.
        """
        self.opt_widget = CSV_option_box(self) # important: Handle must be class attribute
        #self.opt_widget.show() # modeless dialog, i.e. non-blocking
        self.opt_widget.exec_() # modal dialog (blocking)

    #------------------------------------------------------------------------------
    def _copy_to_clipboard(self):
        """
        Copy data from coefficient table `self.tblCoeff` to clipboard in CSV format.
        """
        qcopy_to_clipboard(self.tblCoeff, self.ba, self.clipboard, self.myQ.frmt)

    #------------------------------------------------------------------------------
    def _copy_from_clipboard(self):
        """
        Read data from clipboard and copy it to `self.ba` as array of strings
        # TODO: More checks for swapped row <-> col, single values, wrong data type ...
        """
        ba_str = qcopy_from_clipboard(self.clipboard)

        conv = self.myQ.frmt2float # frmt2float_vec?
        frmt = self.myQ.frmt

        if np.ndim(ba_str) > 1:
            num_cols, num_rows = np.shape(ba_str)
            orientation_horiz = num_cols > num_rows # need to transpose data
        elif np.ndim(ba_str) == 1:
            num_rows = len(ba_str)
            num_cols = 1
            orientation_horiz = False
        else:
            logger.error("Data from clipboard is a single value or None.")
            return None
        logger.debug("_copy_from_clipboard: c x r:", num_cols, num_rows)
        if orientation_horiz:
            self.ba = [[],[]]
            for c in range(num_cols):
                self.ba[0].append(conv(ba_str[c][0], frmt))
                if num_rows > 1:
                    self.ba[1].append(conv(ba_str[c][1], frmt))
        else:
            self.ba[0] = [conv(s, frmt) for s in ba_str[0]]
            if num_cols > 1:
                self.ba[1] = [conv(s, frmt) for s in ba_str[1]]
            else:
                self.ba[1] = [1]

        self._equalize_ba_length()
        qstyle_widget(self.butSave, 'changed')
        self._refresh_table()


#------------------------------------------------------------------------------
    def _load_q_settings(self):
        """
        load the quantization settings from the filter dict and set the widgets
        accordingly. Update the fixpoint object.
        """
        q_coeff = fb.fil[0]['q_coeff']
        self.ledWI.setText(str(q_coeff['WI']))
        self.ledWF.setText(str(q_coeff['WF']))
        qset_cmb_box(self.cmbQuant, q_coeff['quant'])
        qset_cmb_box(self.cmbQOvfl,  q_coeff['ovfl'])
        qset_cmb_box(self.cmbFormat, q_coeff['frmt'])
        self.ledScale.setText(str(q_coeff['scale']))

        self.myQ.setQobj(fb.fil[0]['q_coeff'])

        self.ledW.setText(str(self.myQ.W))
        self.lblLSB.setText("{0:.{1}g}".format(self.myQ.LSB, params['FMT_ba']))
        self.lblMSB.setText("{0:.{1}g}".format(self.myQ.MSB, params['FMT_ba']))
        self.lblMAX.setText("{0}".format(self.myQ.float2frmt(self.myQ.MAX, scaling='none')))

#------------------------------------------------------------------------------
    def _store_q_settings(self):
        """
        Read out the settings of the quantization comboboxes and store them in
        the filter dict. Update the fixpoint object.
        """
        fb.fil[0]['q_coeff'] = {
                'WI':safe_eval(self.ledWI.text(), self.myQ.WI, return_type='int'),
                'WF':safe_eval(self.ledWF.text(), self.myQ.WF, return_type='int', sign='pos'),
                'quant':self.cmbQuant.currentText(),
                'ovfl':self.cmbQOvfl.currentText(),
                'frmt':self.cmbFormat.currentText(),
                'scale':self.ledScale.text()
                }
        self._load_q_settings() # update widgets and the fixpoint object self.myQ

#------------------------------------------------------------------------------
    def _save_dict(self):
        """
        Save the coefficient register `self.ba` to the filter dict `fb.fil[0]['ba']`.
        """

        logger.debug("_save_entries called")

        fb.fil[0]['N'] = max(len(self.ba[0]), len(self.ba[1])) - 1

        self._store_q_settings()

        if fb.fil[0]['ft'] == 'IIR':
            fb.fil[0]['fc'] = 'Manual_IIR'
        else:
            fb.fil[0]['fc'] = 'Manual_FIR'

        # save, check and convert coeffs, check filter type
        fil_save(fb.fil[0], self.ba, 'ba', __name__)

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
        self.ba = [[1, 0], [1, 0]]

        self._refresh_table()
        qstyle_widget(self.butSave, 'changed')


#------------------------------------------------------------------------------
    def _equalize_ba_length(self):
        """
        test and equalize if b and a subarray have different lengths:
        """
        try:
            a_len = len(self.ba[1])
        except IndexError:
            self.ba.append(np.array(1))
            a_len = 1

        D = len(self.ba[0]) - a_len

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

        if not np.any(sel) and len(self.ba[0]) > 0:
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

#------------------------------------------------------------------------------
    def _set_eps(self):
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        self.eps = safe_eval(self.ledEps.text(), return_type='float', sign='pos', alt_expr=self.eps)
        self.ledEps.setText(str(self.eps))

#------------------------------------------------------------------------------
    def _set_coeffs_zero(self):
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        self._set_eps()
        idx = qget_selected(self.tblCoeff)['idx'] # get all selected indices

        test_val = 0. # value against which array is tested
        targ_val = 0. # value which is set when condition is true
        changed = False

        if not idx: # nothing selected, check whole table
            b_close = np.logical_and(np.isclose(self.ba[0], test_val, rtol=0, atol=self.eps),
                                    (self.ba[0] != targ_val))
            if np.any(b_close): # found at least one coeff where condition was true
                self.ba[0] = np.where(b_close, targ_val, self.ba[0])
                changed = True

            if  fb.fil[0]['ft'] == 'IIR':
                a_close = np.logical_and(np.isclose(self.ba[1], test_val, rtol=0, atol=self.eps),
                                    (self.ba[1] != targ_val))
                if np.any(a_close):
                    self.ba[1] = np.where(a_close, targ_val, self.ba[1])
                    changed = True

        else: # only check selected cells
            for i in idx:
                if np.logical_and(np.isclose(self.ba[i[0]][i[1]], test_val, rtol=0, atol=self.eps),
                                  (self.ba[i[0]][i[1]] != targ_val)):
                    self.ba[i[0]][i[1]] = targ_val
                    changed = True
        if changed:
            qstyle_widget(self.butSave, 'changed') # mark save button as changed

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
            self.ba = self.myQ.fixp(self.ba, scaling='div')
        else:
            for i in idx:
                self.ba[i[0]][i[1]] = self.myQ.fixp(self.ba[i[0]][i[1]], scaling = 'div')

        qstyle_widget(self.butSave, 'changed')
        self._refresh_table()

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QApplication(sys.argv)
    mainw = FilterCoeffs(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
