# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for displaying and modifying filter coefficients
"""

from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

import sys

from ..compat import (Qt, QtCore, QWidget, QLineEdit, QApplication,
                      QIcon, QSize, QTableWidget, QTableWidgetItem, QVBoxLayout,
                      pyqtSignal, QStyledItemDelegate, QColor, QBrush)

import numpy as np

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import qstr, fil_save, safe_eval
from pyfda.pyfda_qt_lib import qstyle_widget, qset_cmb_box, qget_cmb_box, qget_selected
from pyfda.pyfda_io_lib import CSV_option_box, qtable2text, qtext2table
 
from pyfda.pyfda_rc import params
import pyfda.pyfda_fix_lib as fix

from .input_coeffs_ui import Input_Coeffs_UI

# TODO: implement checking for complex-valued filters somewhere (pyfda_lib?),
#       h[n] detects complex data (although it isn't)
# TODO: Fixpoint coefficients do not properly convert complex -> float when saving
#       the filter?
# TODO: This ItemDelegate method displayText is called again and again when an
#        item is selected?!
# TODO: negative values for WI don't work correctly
#
# TODO: Filters need to be scaled properly, see e.g. http://radio.feld.cvut.cz/matlab/toolbox/filterdesign/normalize.html
#       http://www.ue.eti.pg.gda.pl/~wrona/lab_dsp/cw05/matlab/Help1.pdf

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
        Pass instance `parent` of parent class (Input_Coeffs)
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

        elif self.parent.myQ.frmt == 'dec' and self.parent.myQ.WF > 0:
            # decimal fixpoint representation with fractional part
            return "{0:.{1}g}".format(self.parent.myQ.float2frmt(data_str),
                                        params['FMT_ba'])
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
        # if the entry is complex, convert ba (list of arrays) to complex type
        if isinstance(data, complex):
            self.parent.ba[0] = self.parent.ba[0].astype(complex)
            self.parent.ba[1] = self.parent.ba[1].astype(complex)
        self.parent.ba[index.column()][index.row()] = data  # store in self.ba
        qstyle_widget(self.parent.ui.butSave, 'changed')
        self.parent._refresh_table_item(index.row(), index.column()) # refresh table entry


class Input_Coeffs(QWidget):
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
    sig_tx = pyqtSignal(object) # emitted when filter has been saved
    sig_rx = pyqtSignal(object) # incoming from input_tab_widgets

    def __init__(self, parent):
        super(Input_Coeffs, self).__init__(parent)

        self.opt_widget = None # handle for pop-up options widget
        self.tool_tip = "Display and edit filter coefficients."
        self.tab_label = "b,a"

        self.ui = Input_Coeffs_UI(self) # create the UI part with buttons etc.
        self._construct_UI()
        
#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if dict_sig['sender'] == __name__:
            logger.debug("Infinite Loop!")
        elif 'data_changed' in dict_sig:
            self.load_dict()
        elif  'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'csv':
            self.ui._set_load_save_icons()


    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """

        # handle to central clipboard instance
        self.clipboard = fb.clipboard

        # ---------------------------------------------------------------------
        #   Coefficient table widget
        # ---------------------------------------------------------------------
        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setAlternatingRowColors(True)
        self.tblCoeff.horizontalHeader().setHighlightSections(True) # highlight when selected
        self.tblCoeff.horizontalHeader().setFont(self.ui.bfont)

#        self.tblCoeff.QItemSelectionModel.Clear
        self.tblCoeff.setDragEnabled(True)
#        self.tblCoeff.setDragDropMode(QAbstractItemView.InternalMove) # doesn't work like intended
        self.tblCoeff.setItemDelegate(ItemDelegate(self))

        # ============== Main UI Layout =====================================
        layVMain = QVBoxLayout()
        layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addWidget(self.ui)
        layVMain.addWidget(self.tblCoeff)

        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        self.myQ = fix.Fixed(fb.fil[0]["q_coeff"]) # initialize fixpoint object
        self.load_dict() # initialize + refresh table with default values from filter dict
        # TODO: this needs to be optimized - self._refresh is being called in both routines
        self._set_number_format()
        
        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL (UI) SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # wdg.textChanged() is emitted when contents of widget changes
        # wdg.textEdited() is only emitted for user changes
        # wdg.editingFinished() is only emitted for user changes
        self.ui.butEnable.clicked.connect(self._refresh_table)
        self.ui.spnDigits.editingFinished.connect(self._refresh_table)

        self.ui.cmbQFrmt.currentIndexChanged.connect(self._set_number_format)
        self.ui.butFromTable.clicked.connect(self._copy_from_table)
        self.ui.butToTable.clicked.connect(self._copy_to_table)

        self.ui.cmbFilterType.currentIndexChanged.connect(self._filter_type)

        self.ui.butDelCells.clicked.connect(self._delete_cells)
        self.ui.butAddCells.clicked.connect(self._add_cells)
        self.ui.butLoad.clicked.connect(self.load_dict)
        self.ui.butSave.clicked.connect(self._save_dict)
        self.ui.butClear.clicked.connect(self._clear_table)
        self.ui.ledEps.editingFinished.connect(self._set_eps)
        self.ui.butSetZero.clicked.connect(self._set_coeffs_zero)

        # store new settings and refresh table
        self.ui.cmbFormat.currentIndexChanged.connect(self._store_q_settings)
        self.ui.cmbQOvfl.currentIndexChanged.connect(self._store_q_settings)
        self.ui.cmbQuant.currentIndexChanged.connect(self._store_q_settings)
        self.ui.ledWF.editingFinished.connect(self._store_q_settings)
        self.ui.ledWI.editingFinished.connect(self._store_q_settings)
        self.ui.ledW.editingFinished.connect(self._W_changed)

        self.ui.ledScale.editingFinished.connect(self._set_scale)

        self.ui.butQuant.clicked.connect(self.quant_coeffs)
        
        self.ui.sig_tx.connect(self.sig_tx)
        # =====================================================================

#------------------------------------------------------------------------------
    def _filter_type(self, ftype=None):
        """
        Get / set 'FIR' and 'IIR' filter from cmbFilterType combobox and set filter
            dict and table properties accordingly.

        When argument fil_type is not None, set the combobox accordingly.

        Reload from filter dict unless ftype is specified [does this make sense?!]
        """
        if ftype in {'FIR', 'IIR'}:
            ret=qset_cmb_box(self.ui.cmbFilterType, ftype)
            if ret == -1:
                logger.warning("Unknown filter type {0}".format(ftype))

        if self.ui.cmbFilterType.currentText() == 'IIR':
            fb.fil[0]['ft'] = 'IIR'
            self.col = 2
            self.tblCoeff.setColumnCount(2)
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
        else:
            fb.fil[0]['ft'] = 'FIR'
            self.col = 1
            self.tblCoeff.setColumnCount(1)
            self.tblCoeff.setHorizontalHeaderLabels(["b"])

        if not ftype:
            self._refresh_table()

#------------------------------------------------------------------------------
    def _W_changed(self):
        """
        Set fractional and integer length `WF` and `WI` when wordlength Ẁ` has
        been changed. Try to preserve `WI` or `WF` settings depending on the
        number format (integer or fractional).
        """
        W = safe_eval(self.ui.ledW.text(), self.myQ.W, return_type='int', sign='pos')

        if W < 2:
            logger.warn("W must be > 1, restoring previous value.")
            W = self.myQ.W # fall back to previous value
        self.ui.ledW.setText(str(W))

        if qget_cmb_box(self.ui.cmbQFrmt) == 'qint': # integer format, preserve WI bits
            WI = W - self.myQ.WF - 1
            self.ui.ledWI.setText(str(WI))
            self.ui.ledScale.setText(str(1 << (W-1)))
        else: # fractional format, preserve WF bit setting
            WF = W - self.myQ.WI - 1
            if WF < 0:
                self.ui.ledWI.setText(str(W - 1))
                WF = 0
            self.ui.ledWF.setText(str(WF))

        self._store_q_settings()

#------------------------------------------------------------------------------
    def _set_number_format(self):
        """
        Set one of three number formats: Integer, fractional, normalized fractional
        """

        qfrmt = qget_cmb_box(self.ui.cmbQFrmt)
        is_qfrac = False
        W = safe_eval(self.ui.ledW.text(), self.myQ.W, return_type='int', sign='pos')
        if qfrmt == 'qint':
            self.ui.ledWI.setText(str(W - 1))
            self.ui.ledWF.setText("0")
            self.ui.ledScale.setText(str(1 << (W-1)))
        elif qfrmt == 'qnfrac': # normalized fractional format
            self.ui.ledWI.setText("0")
            self.ui.ledWF.setText(str(W - 1))
            self.ui.ledScale.setText("1")
        else: # qfrmt == 'qfrac':
            is_qfrac = True

        self.ui.ledWI.setEnabled(is_qfrac)
        self.ui.lblDot.setEnabled(is_qfrac)
        self.ui.ledWF.setEnabled(is_qfrac)
        self.ui.ledW.setEnabled(not is_qfrac)
        self.ui.ledScale.setEnabled(is_qfrac)

        self._store_q_settings()

        #------------------------------------------------------------------------------
    def _set_scale(self):
        """
        Set scale for calculating floating point value from fixpoint representation
        and vice versa
        """
        # if self.ui.ledScale.isModified() ... self.ui.ledScale.setModified(False)
        scale = safe_eval(self.ui.ledScale.text(), self.myQ.scale, return_type='float', sign='pos')
        self.ui.ledScale.setText(str(scale))
        self._store_q_settings()

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
        # logger.debug("np.shape(ba) = {0}".format(np.shape(self.ba)))

        params['FMT_ba'] = int(self.ui.spnDigits.text())

        # When format is 'float', disable all fixpoint options
        is_float = (qget_cmb_box(self.ui.cmbFormat, data=False).lower() == 'float')

        self.ui.spnDigits.setVisible(is_float) # number of digits can only be selected
        self.ui.lblDigits.setVisible(is_float) # for format = 'float'
        self.ui.cmbQFrmt.setVisible(not is_float) # hide unneeded widgets for format = 'float'
        self.ui.lbl_W.setVisible(not is_float)
        self.ui.ledW.setVisible(not is_float)

        if self.ui.butEnable.isChecked():
            self.ui.frmQSettings.setVisible(not is_float) # hide all q-settings for float
            self.ui.butEnable.setIcon(QIcon(':/circle-x.svg'))
            self.tblCoeff.setVisible(True)

            # check whether filter is FIR and only needs one column
            if fb.fil[0]['ft'] == 'FIR':
                self.num_cols = 1
                self.tblCoeff.setColumnCount(1)
                self.tblCoeff.setHorizontalHeaderLabels(["b"])
                qset_cmb_box(self.ui.cmbFilterType, 'FIR')
            else:
                self.num_cols = 2
                self.tblCoeff.setColumnCount(2)
                self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
                qset_cmb_box(self.ui.cmbFilterType, 'IIR')

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
                item.setFont(self.ui.bfont)

            self.tblCoeff.blockSignals(False)

            self.tblCoeff.resizeColumnsToContents()
            self.tblCoeff.resizeRowsToContents()
            self.tblCoeff.clearSelection()

        else:
            self.ui.frmQSettings.setVisible(False)
            self.ui.butEnable.setIcon(QIcon(':/circle-check.svg'))
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
        qstyle_widget(self.ui.butSave, 'normal')

    #------------------------------------------------------------------------------
    def _copy_options(self):
        """
        Set options for copying to/from clipboard or file.
        """
        self.opt_widget = CSV_option_box(self) # important: Handle must be class attribute
        #self.opt_widget.show() # modeless dialog, i.e. non-blocking
        self.opt_widget.exec_() # modal dialog (blocking)

    #------------------------------------------------------------------------------
    def _copy_from_table(self):
        """
        Copy data from coefficient table `self.tblCoeff` to clipboard / file in
        CSV format.
        """
        qtable2text(self.tblCoeff, self.ba, self, 'ba', self.myQ.frmt)

    #------------------------------------------------------------------------------
    def _copy_to_table(self):
        """
        Read data from clipboard / file and copy it to `self.ba` as float / cmplx
        # TODO: More checks for swapped row <-> col, single values, wrong data type ...
        """
        data_str = qtext2table(self, 'ba', comment="filter coefficients ")
        if data_str == -1: # file operation has been aborted
            return

        logger.debug("importing data: dim - shape = {0} - {1} - {2}\n{3}"\
                       .format(type(data_str), np.ndim(data_str), np.shape(data_str), data_str))

        conv = self.myQ.frmt2float # frmt2float_vec?
        frmt = self.myQ.frmt

        if np.ndim(data_str) > 1:
            num_cols, num_rows = np.shape(data_str)
            orientation_horiz = num_cols > num_rows # need to transpose data
        elif np.ndim(data_str) == 1:
            num_rows = len(data_str)
            num_cols = 1
            orientation_horiz = False
        else:
            logger.error("Imported data is a single value or None.")
            return None
        logger.info("_copy_to_table: c x r = {0} x {1}".format(num_cols, num_rows))
        if orientation_horiz:
            self.ba = [[],[]]
            for c in range(num_cols):
                self.ba[0].append(conv(data_str[c][0], frmt))
                if num_rows > 1:
                    self.ba[1].append(conv(data_str[c][1], frmt))
            if num_rows > 1:
                self._filter_type(ftype='IIR')
            else:
                self._filter_type(ftype='FIR')
        else:
            self.ba[0] = [conv(s, frmt) for s in data_str[0]]
            if num_cols > 1:
                self.ba[1] = [conv(s, frmt) for s in data_str[1]]
                self._filter_type(ftype='IIR')
            else:
                self.ba[1] = [1]
                self._filter_type(ftype='FIR')

        self.ba[0] = np.asarray(self.ba[0])
        self.ba[1] = np.asarray(self.ba[1])

        self._equalize_ba_length()
        qstyle_widget(self.ui.butSave, 'changed')
        self._refresh_table()


#------------------------------------------------------------------------------
    def _load_q_settings(self):
        """
        load the quantization settings from the filter dict and set the widgets
        accordingly. Update the fixpoint object.
        """
        self.myQ.setQobj(fb.fil[0]['q_coeff'])
        q_coeff = self.myQ.q_obj

        self.ui.ledWI.setText(qstr(q_coeff['WI']))
        self.ui.ledWF.setText(qstr(q_coeff['WF']))
        qset_cmb_box(self.ui.cmbQuant, q_coeff['quant'])
        qset_cmb_box(self.ui.cmbQOvfl,  q_coeff['ovfl'])
        qset_cmb_box(self.ui.cmbFormat, q_coeff['frmt'])
        self.ui.ledScale.setText(qstr(q_coeff['scale']))

        self.ui.ledW.setText(qstr(self.myQ.W))
        self.ui.lblLSB.setText("{0:.{1}g}".format(self.myQ.LSB, params['FMT_ba']))
        self.ui.lblMSB.setText("{0:.{1}g}".format(self.myQ.MSB, params['FMT_ba']))
        self.ui.lblMAX.setText("{0}".format(self.myQ.float2frmt(self.myQ.MAX/self.myQ.scale)))

#------------------------------------------------------------------------------
    def _store_q_settings(self):
        """
        Read out the settings of the quantization comboboxes and store them in
        the filter dict. Update the fixpoint object and refresh table
        """
        fb.fil[0]['q_coeff'] = {
                'WI':safe_eval(self.ui.ledWI.text(), self.myQ.WI, return_type='int'),
                'WF':safe_eval(self.ui.ledWF.text(), self.myQ.WF, return_type='int', sign='pos'),
                'quant':qstr(self.ui.cmbQuant.currentText()),
                'ovfl':qstr(self.ui.cmbQOvfl.currentText()),
                'frmt':qstr(self.ui.cmbFormat.currentText()),
                'scale':qstr(self.ui.ledScale.text())
                }
        self.sig_tx.emit({'sender':__name__, 'view_changed':'q_coeff'})

        self._load_q_settings() # update widgets and the fixpoint object self.myQ
        self._refresh_table()

#------------------------------------------------------------------------------
    def _save_dict(self):
        """
        Save the coefficient register `self.ba` to the filter dict `fb.fil[0]['ba']`.
        """

        logger.debug("_save_dict called")

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

        self.sig_tx.emit({'sender':__name__, 'data_changed':'input_coeffs'})
        # -> input_tab_widgets

        qstyle_widget(self.ui.butSave, 'normal')

#------------------------------------------------------------------------------
    def _clear_table(self):
        """
        Clear self.ba: Initialize coeff for a poles and a zero @ origin,
        a = b = [1; 0].

        Refresh QTableWidget
        """
        self.ba = [np.asarray([1., 0.]), np.asarray([1., 0.])]

        self._refresh_table()
        qstyle_widget(self.ui.butSave, 'changed')


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
        # if length is less than 2, clear the table: this ain't no filter!
        if len(self.ba[0]) < 2:
            self._clear_table() # sets 'changed' attribute
        else:
            self._refresh_table()
            qstyle_widget(self.ui.butSave, 'changed')

#------------------------------------------------------------------------------
    def _add_cells(self):
        """
        Add the number of selected rows to self.ba and fill new cells with
        zeros from the bottom. If nothing is selected, add one row at the bottom.
        Refresh QTableWidget.
        """
        # get indices of all selected cells
        sel = qget_selected(self.tblCoeff)['sel']

        if not np.any(sel): # nothing selected, append zeros to table
            self.ba[0] = np.append(self.ba[0], 0)
            self.ba[1] = np.append(self.ba[1], 0)
        else:
            self.ba[0] = np.insert(self.ba[0], sel[0], 0)
            self.ba[1] = np.insert(self.ba[1], sel[1], 0)

        # insert 'sel' contiguous rows  before 'row':
        # self.ba[0] = np.insert(self.ba[0], row, np.zeros(sel))

        self._equalize_ba_length()
        self._refresh_table()
        # don't tag as 'changed' when only zeros have been added at the end
        if np.any(sel):
            qstyle_widget(self.ui.butSave, 'changed')

#------------------------------------------------------------------------------
    def _set_eps(self):
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        self.ui.eps = safe_eval(self.ui.ledEps.text(), return_type='float', sign='pos', alt_expr=self.ui.eps)
        self.ui.ledEps.setText(str(self.ui.eps))

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
            b_close = np.logical_and(np.isclose(self.ba[0], test_val, rtol=0, atol=self.ui.eps),
                                    (self.ba[0] != targ_val))
            if np.any(b_close): # found at least one coeff where condition was true
                self.ba[0] = np.where(b_close, targ_val, self.ba[0])
                changed = True

            if  fb.fil[0]['ft'] == 'IIR':
                a_close = np.logical_and(np.isclose(self.ba[1], test_val, rtol=0, atol=self.ui.eps),
                                    (self.ba[1] != targ_val))
                if np.any(a_close):
                    self.ba[1] = np.where(a_close, targ_val, self.ba[1])
                    changed = True

        else: # only check selected cells
            for i in idx:
                if np.logical_and(np.isclose(self.ba[i[0]][i[1]], test_val, rtol=0, atol=self.ui.eps),
                                  (self.ba[i[0]][i[1]] != targ_val)):
                    self.ba[i[0]][i[1]] = targ_val
                    changed = True
        if changed:
            qstyle_widget(self.ui.butSave, 'changed') # mark save button as changed

        self._refresh_table()

#------------------------------------------------------------------------------
    def quant_coeffs(self):
        """
        Quantize selected / all coefficients in self.ba and refresh QTableWidget
        """
        idx = qget_selected(self.tblCoeff)['idx'] # get all selected indices
        if not idx: # nothing selected, quantize all elements
            self.ba = self.myQ.fixp(self.ba, scaling='multdiv')
        else:
            for i in idx:
                self.ba[i[0]][i[1]] = self.myQ.fixp(self.ba[i[0]][i[1]], scaling = 'multdiv')

        qstyle_widget(self.ui.butSave, 'changed')
        self._refresh_table()

#------------------------------------------------------------------------------

if __name__ == '__main__':
    """ Test with python -m pyfda.input_widgets.input_coeffs """
    app = QApplication(sys.argv)
    mainw = Input_Coeffs(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
