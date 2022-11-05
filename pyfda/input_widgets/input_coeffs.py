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
import sys

from pyfda.libs.compat import (
    Qt, QtCore, QWidget, QLineEdit, QApplication, QIcon, QSize, QTableWidget,
    QTableWidgetItem, QVBoxLayout, pyqtSignal, QStyledItemDelegate, QColor, QBrush)
import numpy as np

import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals
from pyfda.libs.pyfda_lib import fil_save, safe_eval, pprint_log
from pyfda.libs.pyfda_qt_lib import (
    qstyle_widget, qset_cmb_box, qget_cmb_box, qget_selected)
from pyfda.libs.pyfda_io_lib import qtable2text, qtext2table, export_csv_data
from pyfda.libs.csv_option_box import CSV_option_box

from pyfda.pyfda_rc import params

from .input_coeffs_ui import Input_Coeffs_UI

import logging
logger = logging.getLogger(__name__)

# TODO: implement checking for complex-valued filters somewhere (pyfda_lib?),
#       h[n] detects complex data (although it isn't)
# TODO: Fixpoint coefficients do not properly convert complex -> float when saving
#       the filter?
# TODO: This ItemDelegate method displayText is called again and again when an
#        item is selected?!
# TODO: negative values for WI don't work correctly
#
# TODO: Filters need to be scaled properly, see e.g.
#       http://radio.feld.cvut.cz/matlab/toolbox/filterdesign/normalize.html
#       http://www.ue.eti.pg.gda.pl/~wrona/lab_dsp/cw05/matlab/Help1.pdf
#       https://stackoverflow.com/questions/68206713/scipy-filter-force-minimal-value-of-sos-coefficient-to-prepare-integer-filter


classes = {'Input_Coeffs': 'b,a'}  #: Dict containing class name : display name


class ItemDelegate(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.

    - `displayText()` displays the data stored in the table in various number formats

    - `createEditor()` creates a line edit instance for editing table entries

    - `setEditorData()` pass data with full precision and in selected format to editor

    - `setModelData()` pass edited data back to model (`self.ba`)

    Editing the table triggers `setModelData()` but does not emit a signal outside
    this class, only the `ui.butSave` button is highlighted. When it is pressed,
    a signal with `'data_changed':'input_coeffs'` is produced in class `Input_Coeffs`.
    Additionally, a signal is emitted with `'fx_sim': 'specs_changed'`
    """

    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (Input_Coeffs)
        """
        super(ItemDelegate, self).__init__(parent)
        self.parent = parent  # instance of the parent (not the base) class
        # handles to quantization objects (fx.Fixed() instance) of coefficient widgets
        self.QObj = [self.parent.ui.wdg_wq_coeffs_b.QObj,
                     self.parent.ui.wdg_wq_coeffs_a.QObj]

# ==============================================================================
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
#             #     painter.setPen(option.palette.color( QPalette.Active, QPalette.Dark ))
#             painter.drawLine(option.rect.left(), y, option.rect.right(), y )
#         else:
#             # continue with the original `paint()` method
#             super(ItemDelegate, self).paint(painter, option, index)
#             #painter.restore()
# ----------------------------------
#         logger.debug("Ovr_flag:".format(self.parent.self.QObj[0].ovr_flag))
#         #option.backgroundBrush = QBrush(QColor(000, 100, 100, 200)) # lightGray
#             #option.backgroundBrush.setColor(QColor(000, 100, 100, 200))
#         # continue with the original `paint()` method
#         #option.palette.setColor(QPalette.Window, QColor(Qt.red))
#         #option.palette.setColor(QPalette.Base, QColor(Qt.green))
#         super(ItemDelegate, self).paint(painter, option, index)
#
#
# ==============================================================================

    def initStyleOption(self, option, index):
        """
        Initialize `option` with the values using the `index` index. When the
        item (0,1) is processed, it is styled especially. All other items are
        passed to the original `initStyleOption()` which then calls `displayText()`.
        Afterwards, check whether an fixpoint overflow has occured and color item
        background accordingly.
        """

        if index.row() == 0 and index.column() == 1:  # a[0]: always 1
            option.text = "1"  # QString object
            option.font.setBold(True)
            option.displayAlignment = Qt.AlignRight | Qt.AlignCenter
            # see http://zetcode.com/gui/pyqt5/painting/ :
            option.backgroundBrush = QBrush(Qt.BDiagPattern)
            option.backgroundBrush.setColor(QColor(100, 100, 100, 200))
            # don't continue with default initStyleOption... display routine ends here
        else:
            # continue with the original `initStyleOption()` and call displayText()
            super(ItemDelegate, self).initStyleOption(option, index)

    # -------------------------------------------------------------------------
    def text(self, item):
        """
        Return item text as string transformed by self.displayText()

        Used a.o. in `libs.pyfda_fix_lib` as `text += table.itemDelegate().text(item)`

        TODO: Still needed?
        """
        dtext = str(self.displayText(item.text(), QtCore.QLocale()))
        # logger.warning(f"dtext={dtext}")
        return dtext

    # -------------------------------------------------------------------------
    def displayText(self, text, locale):
        """
        Display `text` with selected fixpoint base and number of places

        text:   string / QVariant from QTableWidget to be rendered
        locale: locale for the text

        The instance parameter `QObj[c].ovr_flag` is set to +1 or -1 for
         positive / negative overflows, else it is 0.
        """

        if fb.fil[0]['fxqc']['QCB']['fx_base'] == 'float':
            data = safe_eval(text, return_type='auto')  # convert to float
            return "{0:.{1}g}".format(data, params['FMT_ba'])

        elif fb.fil[0]['fxqc']['QCB']['fx_base'] == 'dec':
            return "{0:>{1}}".format(text, self.QObj[0].q_dict['places'])

        else:
            return text
# see:
# http://stackoverflow.com/questions/30615090/pyqt-using-qtextedit-as-editor-in-a-qstyleditemdelegate

    # -------------------------------------------------------------------------
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
        line_edit.setMinimumSize(QSize(W, H))  # (160, 25));

        return line_edit

#    def updateEditorGeometry(self, editor, option, index):
#        """
#        Updates the editor for the item specified by index according to the option given
#        """
#        super(ItemDelegate, self).updateEditorGeometry(editor, option, index) # default

    # -------------------------------------------------------------------------
    def setEditorData(self, editor, index):
        """
        Pass the data to be edited to the editor:
        - retrieve data with full accuracy from self.ba (in float format)
        - requantize data according to settings in fixpoint object
        - represent it in the selected format (int, hex, ...)

        editor: instance of e.g. QLineEdit
        index:  instance of QModelIndex
        """
        data_str = str(safe_eval(self.parent.ba[index.column()][index.row()],
                                 return_type="auto"))
        if self.QObj[index.column()].q_dict['fx_base'] == 'float':
            # floating point format: pass data with full resolution
            editor.setText(data_str)
        else:
            # fixpoint format with base:
            # pass requantized data with required number of decimal places
            editor.setText(
                "{0:>{1}}".format(self.QObj[index.column()].float2frmt(data_str),
                                  self.QObj[index.column()].q_dict['places']))

    # -------------------------------------------------------------------------
    def setModelData(self, editor, model, index):
        """
        When editor has finished, read the updated data from the editor,
        convert it back to floating point format and store it in both the model
        (= QTableWidget) and in self.ba_q. Finally, refresh the table item to
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
        if self.QObj[index.column()].q_dict['fx_base'] == 'float':
            data = safe_eval(
                str(editor.text()), self.parent.ba[index.column()][index.row()],
                return_type='auto')  # raw data without fixpoint formatting
            data_q = data  # TODO: complex data
        else:   # transform to float
            data = self.QObj[index.column()].frmt2float(
                str(editor.text()), self.QObj[index.column()].q_dict['fx_base'])
            data_q = self.QObj[index.column()].float2frmt(data)

        # model.setData(index, data)                          # store in QTableWidget
        # if data is complex, convert whole ba (list of arrays) to complex type
        if isinstance(data, complex):
            self.parent.ba[index.column()] = self.parent.ba[index.column()].astype(complex)
            self.parent.ba_q[index.column()] = self.parent.ba_q[index.column()].astype(complex)

        # store new data in self.ba and ba_q
        self.parent.ba[index.column()][index.row()] = data
        self.parent.ba_q[index.column()][index.row()] = data_q
        qstyle_widget(self.parent.ui.butSave, 'changed')
        self.parent._refresh_table_item(index.row(), index.column())  # refresh table item

###############################################################################


class Input_Coeffs(QWidget):
    """
    Create widget with a (sort of) model-view architecture for viewing /
    editing / entering data contained in `self.ba` which is a list of two numpy
    arrays:

    - `self.ba[0]` contains the numerator coefficients ("b")
    - `self.ba[1]` contains the denominator coefficients ("a")

    The lists don't neccessarily have the same length but they are always defined.
    For FIR filters, `self.ba[1][0] = 1`, all other elements are zero.

    The length of both lists can be egalized with `self._equalize_ba_length()`.

    Views / formats are handled by the ItemDelegate() class.
    """
    sig_tx = pyqtSignal(object)  # emitted when filter has been saved
    sig_rx = pyqtSignal(object)  # incoming from input_tab_widgets
    from pyfda.libs.pyfda_qt_lib import emit

    # -------------------------------------------------------------------------
    def __init__(self, parent=None):
        super(Input_Coeffs, self).__init__(parent)

        self.opt_widget = None  # handle for pop-up options widget
        self.tool_tip = "Display and edit filter coefficients."
        self.tab_label = "b,a"

        self.data_changed = True  # initialize flag: filter data has been changed
        self.fx_specs_changed = True  # fixpoint specs have been changed outside

        self.ui = Input_Coeffs_UI(self)  # create the UI part with buttons etc.

        # handles to quantization objects (`fx.Fixed()` instances) of coefficient widgets
        self.QObj = [self.ui.wdg_wq_coeffs_b.QObj,
                     self.ui.wdg_wq_coeffs_a.QObj]

        self._construct_UI()

    # -------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        logger.debug("process_sig_rx(): vis={0}\n{1}"\
                     .format(self.isVisible(), pprint_log(dict_sig)))

        if dict_sig['id'] == id(self):
            # logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        if 'ui_global_changed' in dict_sig\
                and dict_sig['ui_global_changed'] == 'csv':
            # CSV options have been changed, update icons (file vs. clipboard)
            self.ui._set_load_save_icons()

        elif 'ui_local_changed' in dict_sig and 'wdg_name' in dict_sig and\
                dict_sig['wdg_name'] in {'wq_coeffs_a', 'wq_coeffs_b'}:
            # local events from UI, trigger requant and refresh table
            self.refresh_table()
            self.emit({'fx_sim': 'specs_changed'})
            return

        elif self.isVisible():
            if self.data_changed or 'data_changed' in dict_sig:
                self.load_dict()
                self.data_changed = False
            if self.fx_specs_changed or\
                    ('fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed'):
                # global event, update widget dicts and table
                self.qdict2ui()
                self.fx_specs_changed = False
        else:
            # TODO: draw wouldn't be necessary for 'view_changed', only update view
            # TODO: what is emitted when fixpoint formats are changed?
            if 'data_changed' in dict_sig:
                self.data_changed = True
            elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
                self.fx_specs_changed = True

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        # ---------------------------------------------------------------------
        #   Coefficient table widget
        # ---------------------------------------------------------------------
        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setAlternatingRowColors(True)
        # highlight section of header when a corresponding cell is selected
        self.tblCoeff.horizontalHeader().setHighlightSections(True)
        self.tblCoeff.horizontalHeader().setFont(self.ui.bfont)

#        self.tblCoeff.QItemSelectionModel.Clear
        self.tblCoeff.setDragEnabled(True)
#        self.tblCoeff.setDragDropMode(QAbstractItemView.InternalMove) # doesn't work
        self.tblCoeff.setItemDelegate(ItemDelegate(self))

        # ============== Main UI Layout =====================================
        layVMain = QVBoxLayout()
        layVMain.setAlignment(Qt.AlignTop)  # only affects the first widget (intended)
        layVMain.addWidget(self.ui)
        layVMain.addWidget(self.tblCoeff)
        layVMain.setContentsMargins(*params['wdg_margins'])
        self.setLayout(layVMain)

        # initialize, quantize + refresh table with default values from filter dict
        self.load_dict()

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL (UI) SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # wdg.textChanged() is emitted when contents of widget changes
        # wdg.textEdited() is only emitted for user changes
        # wdg.editingFinished() is only emitted for user changes
        self.ui.butEnable.clicked.connect(self.refresh_table)
        self.ui.spnDigits.editingFinished.connect(self.refresh_table)

        self.ui.butFromTable.clicked.connect(self._export)
        self.ui.butToTable.clicked.connect(self._import)

        self.ui.cmbFilterType.currentIndexChanged.connect(self._filter_type)

        self.ui.butDelCells.clicked.connect(self._delete_cells)
        self.ui.butAddCells.clicked.connect(self._add_cells)
        self.ui.butLoad.clicked.connect(self.load_dict)
        self.ui.butSave.clicked.connect(self._save_dict)
        self.ui.butClear.clicked.connect(self.clear_table)
        self.ui.ledEps.editingFinished.connect(self._set_eps)
        self.ui.butSetZero.clicked.connect(self._set_coeffs_zero)

        # store new settings and refresh table
        self.ui.cmb_fx_base.currentIndexChanged.connect(self.fx_base2qdict)
        self.ui.cmb_q_frmt.currentIndexChanged.connect(self.qfrmt2qdict)

        self.ui.wdg_wq_coeffs_a.sig_tx.connect(self.process_sig_rx)
        self.ui.wdg_wq_coeffs_b.sig_tx.connect(self.process_sig_rx)

        self.ui.but_quant.clicked.connect(self.quant_coeffs_save)

        self.ui.sig_tx.connect(self.sig_tx)

# ------------------------------------------------------------------------------
    def quant_coeffs_view(self):
        """
        This method only creates a view on the quantized coefficients and stores
        it in `self.ba_q`, the actual coefficients in `self.ba` remain unchanged!

        * Reset overflow counters

        * Quantize filter coefficients `self.ba` with quantizer objects
          `self.QObj[0]` and `self.QObj[1]` for `b` and `a` coefficients respectively
          and store them in the array `self.ba_q`. Depending on the number base
          (float, dec, hex, ...) the result can be of type float or string.

        *  Store pos. / neg. overflows in the 3rd and 4th column of `self.ba_q` as
           0 or +/- 1.
        """
        self.QObj[0].resetN()
        self.QObj[1].resetN()

        if np.isscalar(self.ba[0]) or np.isscalar(self.ba[1]):
            logger.error("No proper filter, coefficients are scalar!")
            return

        len_b = len(self.ba[0])
        len_a = len(self.ba[1])

        # Create a copy of the a coefficients without the "1" as this could create
        # false overflows during quantization. The "1" is always printed though
        # by the `ItemDelegate.initStyleOption()` method
        #
        # TODO: Replacing the first element by 0  doesn't work, a is always converted 
        # to integer for non-dec formats somehwhere - Why???

        # logger.error(f"ba[1]: {self.ba[1].dtype}")
        a = np.concatenate(([0.123], self.ba[1][1:]))
        # a = self.ba[1]
        # logger.error(f"a: {a.dtype}")

        if fb.fil[0]['fxqc']['QCB']['fx_base'] == 'float':
            self.ba_q = [self.ba[0],
                         self.ba[1],
                         np.zeros(len_b),
                         np.zeros(len_a),
                         ]
        elif fb.fil[0]['fxqc']['QCB']['fx_base'] == 'dec':
            self.ba_q = [
                ["{0:>{1}}".format(x, self.QObj[0].q_dict['places'])
                    for x in self.QObj[0].float2frmt(self.ba[0])],
                ["{0:>{1}}".format(x, self.QObj[0].q_dict['places'])
                    for x in self.QObj[1].float2frmt(a)],
                self.QObj[0].q_dict['ovr_flag'],
                self.QObj[1].q_dict['ovr_flag']
                        ]
        else:
            self.ba_q = [
                self.QObj[0].float2frmt(self.ba[0]),
                self.QObj[1].float2frmt(a),
                self.QObj[0].q_dict['ovr_flag'],
                self.QObj[1].q_dict['ovr_flag']
                        ]
        self.ui.wdg_wq_coeffs_b.update_disp()
        self.ui.wdg_wq_coeffs_a.update_disp()

# ------------------------------------------------------------------------------
    def quant_coeffs_save(self):
        """
        - Store selected / all quantized coefficients in `self.ba`
        - Refresh table (for the case that anything weird happens during quantization)
        - Reset Overflow flags `self.ba_q[2]` and `self.ba_q[3]`
        - Save quantized `self.ba` to filter dict (in `_save_dict()`). This emits
          {'data_changed': 'input_coeffs'}
        """
        idx = qget_selected(self.tblCoeff)['idx']  # get all selected indices
        # returns e.g. [[0, 0], [0, 6]]

        if not idx:  # nothing selected, quantize all elements
            self.ba[0] = self.QObj[0].frmt2float(self.ba_q[0])
            self.ba[1] = self.QObj[1].frmt2float(self.ba_q[1])
            self.ba_q[2] = np.zeros(len(self.ba_q[0]))
            self.ba_q[3] = np.zeros(len(self.ba_q[1]))
            # idx = [[j, i] for i in range(self.num_rows) for j in range(self.num_cols)]
        else:
            try:
                idx.remove([1, 0])  # don't process '1' of recursive filters
            except ValueError:
                pass
            for i in idx:
                self.ba[i[0]][i[1]] = self.QObj[i[0]].frmt2float(self.ba_q[i[0]][i[1]])
                self.ba_q[i[0] + 2][i[1]] = 0

        self.refresh_table()
        # qstyle_widget(self.ui.butSave, 'changed')
        self._save_dict()

    # --------------------------------------------------------------------------
    def _filter_type(self, ftype=None):
        """
        Get / set 'FIR' and 'IIR' filter from cmbFilterType combobox and set filter
            dict and table properties accordingly.

        When argument fil_type is not None, set the combobox accordingly.

        Reload from filter dict unless ftype is specified [does this make sense?!]
        """
        if ftype in {'FIR', 'IIR'}:
            ret = qset_cmb_box(self.ui.cmbFilterType, ftype)
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
            self.ba[1] = np.zeros_like(self.ba[1])  # enforce FIR filter
            self.ba[1][0] = 1.

        self._equalize_ba_length()
        self.refresh_table()
        qstyle_widget(self.ui.butSave, 'changed')

# ------------------------------------------------------------------------------
    def _refresh_table_item(self, row, col):
        """
        Refresh the table item with the index `row, col` from `self.ba_q`
        and color it according to overflow conditions
        """
        item = self.tblCoeff.item(row, col)

        if item:  # does item exist?
            item.setText(str(self.ba_q[col][row]).strip('()'))
        else:  # no, construct it:
            item = QTableWidgetItem(str(self.ba_q[col][row]).strip('()'))
            self.tblCoeff.setItem(row, col, item)

        brush = QBrush(Qt.SolidPattern)
        brush.setColor(QColor(255, 255, 255, 0))  # transparent white

        if self.ba_q[col + 2][row] > 0:
            # Color item backgrounds with pos. Overflows red
            brush.setColor(QColor(100, 0, 0, 80))

        elif self.ba_q[col + 2][row] < 0:
            # Color item backgrounds with neg. Overflows blue
            brush.setColor(QColor(0, 0, 100, 80))

        item.setTextAlignment(Qt.AlignRight | Qt.AlignCenter)
        item.setBackground(brush)

    # --------------------------------------------------------------------------
    def refresh_table(self):
        """
        Update `self.ba_q` from `self.ba` (list with 2 one-dimensional numpy arrays),
        i.e. requantize displayed values (not `self.ba`) and overflow counters.

        Refresh the table from it. Data is displayed via `ItemDelegate.displayText()` in
        the number format set by `self.q_dict['fx_base']`.

        - self.ba[0] -> b coefficients
        - self.ba[1] -> a coefficients

        The table dimensions are set according to the filter type set in
        `fb.fil[0]['ft']` which is either 'FIR' or 'IIR' and by the number of
        rows in `self.ba`.

        Called at the end of nearly every method.
        """
        params['FMT_ba'] = int(self.ui.spnDigits.text())
        # quantize coefficient display and update overflow counter
        self.quant_coeffs_view()
        if np.ndim(self.ba) == 1 or fb.fil[0]['ft'] == 'FIR':
            self.num_rows = len(self.ba[0])
        else:
            self.num_rows = max(len(self.ba[1]), len(self.ba[0]))

        # When format is 'float', disable all fixpoint options and widgets:
        is_float = (qget_cmb_box(self.ui.cmb_fx_base, data=False).lower() == 'float')
        self.ui.spnDigits.setVisible(is_float)  # select number of float digits
        self.ui.lblDigits.setVisible(is_float)
        self.ui.frm_q_frmt.setVisible(not is_float)  # hide quantization widgets

        # hide all q-settings for float
        self.ui.wdg_wq_coeffs_b.setVisible(not is_float)

        if self.ui.butEnable.isChecked():
            self.ui.butEnable.setIcon(QIcon(':/circle-check.svg'))
            self.ui.frm_buttons_coeffs.setVisible(True)
            self.tblCoeff.setVisible(True)

            # check whether filter is FIR and only needs one column
            if fb.fil[0]['ft'] == 'FIR':
                self.num_cols = 1
                self.tblCoeff.setColumnCount(1)
                self.tblCoeff.setHorizontalHeaderLabels(["b"])
                qset_cmb_box(self.ui.cmbFilterType, 'FIR')
                self.ui.wdg_wq_coeffs_a.setVisible(False)  # always hide a coeffs for FIR
            else:
                self.num_cols = 2
                self.tblCoeff.setColumnCount(2)
                self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
                qset_cmb_box(self.ui.cmbFilterType, 'IIR')
                # hide all q-settings for float:
                self.ui.wdg_wq_coeffs_a.setVisible(not is_float)

                self.ba[1][0] = 1.0  # restore a[0] = 1 of denominator polynome

            self.tblCoeff.setRowCount(self.num_rows)
            self.tblCoeff.setColumnCount(self.num_cols)
            # Create strings for index column (vertical header), starting with "0"
            idx_str = [str(n) for n in range(self.num_rows)]
            self.tblCoeff.setVerticalHeaderLabels(idx_str)
            # ----------------------------------
            self.tblCoeff.blockSignals(True)

            for col in range(self.num_cols):
                for row in range(self.num_rows):
                    self._refresh_table_item(row, col)

            # make a[0] selectable but not editable
            if fb.fil[0]['ft'] == 'IIR':
                item = self.tblCoeff.item(0, 1)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                item.setFont(self.ui.bfont)

            self.tblCoeff.blockSignals(False)
            # ---------------------------------
            self.tblCoeff.resizeColumnsToContents()
            self.tblCoeff.resizeRowsToContents()
            self.tblCoeff.clearSelection()

        else:
            self.ui.frm_buttons_coeffs.setVisible(False)
            self.ui.butEnable.setIcon(QIcon(':/circle-x.svg'))
            self.tblCoeff.setVisible(False)

    # --------------------------------------------------------------------------
    def load_dict(self):
        """
        Create a reference from filter dict `fb.fil[0]['ba']` to the coefficient list
        `self.ba` and update the display via `self.refresh_table()`.

        The filter dict is a "normal" 2D-numpy float array for the b and a coefficients
        while the coefficient list `self.ba` is a list of two float ndarrays to allow
        for different lengths of b and a subarrays while adding / deleting items.
        """
        self.ba = [fb.fil[0]['ba'][0], fb.fil[0]['ba'][1]]  # list of two arrays

        self.qdict2ui()  # set quantization UI from dictionary

        self.refresh_table()

        qstyle_widget(self.ui.butSave, 'normal')

    # --------------------------------------------------------------------------
    def _copy_options(self):
        """
        Set options for copying to/from clipboard or file.
        """
        self.opt_widget = CSV_option_box(self)  # Handle must be class attribute!
        # self.opt_widget.show() # modeless dialog, i.e. non-blocking
        self.opt_widget.exec_()  # modal dialog (blocking)

    # --------------------------------------------------------------------------
    def _export(self):
        """
        Export data from coefficient table `self.tblCoeff` to clipboard / file in
        CSV format.
        """
        if not params['CSV']['cmsis']:
            qtable2text(self.tblCoeff, self.ba, self, 'ba', self.QObj[0].q_dict['fx_base'],
                        title="Export Filter Coefficients")
        elif fb.fil[0]['ft'] != 'IIR':
            logger.warning("CMSIS SOS export is only possible for IIR filters!")
        else:
            # Get coefficients in SOS format and delete 4th column containing the
            # '1.0' of the recursive parts:
            sos_coeffs = np.delete(fb.fil[0]['sos'], 3, 1)
            # TODO: check `scipy.signal.zpk2sos` for details concerning sos paring

            delim = params['CSV']['delimiter'].lower()
            if delim == 'auto':  # 'auto' doesn't make sense when exporting
                delim = ","
            cr = params['CSV']['lineterminator']

            text = ""
            for r in range(np.shape(sos_coeffs)[0]):  # number of rows
                for c in range(5):  # always has 5 columns
                    text += str(safe_eval(sos_coeffs[r][c], return_type='auto')) + delim
                text = text.rstrip(delim) + cr
            text = text.rstrip(cr)  # delete last CR

            if params['CSV']['clipboard']:
                fb.clipboard.setText(text)
            else:
                export_csv_data(self, text, title="Export in CMSIS DSP SOS format",
                                file_types=('csv',))

    # --------------------------------------------------------------------------
    def _import(self):
        """
        Import data from clipboard / file and copy it to `self.ba` as float / cmplx.

        Quantize data to `self.ba_q` and refresh table.

        # TODO: More checks for swapped row <-> col, single values, wrong data type ...
        """
        # get data as ndarray of str
        data_str = qtext2table(self, 'ba', title="Import Filter Coefficients")
        if data_str is None:  # file operation has been aborted or some other error
            return

        logger.debug(
            "importing data: dim - shape = {0} - {1} - {2}\n{3}"
            .format(type(data_str), np.ndim(data_str), np.shape(data_str), data_str))

        frmt = self.QObj[0].q_dict['fx_base']

        if np.ndim(data_str) > 1:
            num_cols, num_rows = np.shape(data_str)
            orientation_horiz = num_cols > num_rows  # need to transpose data
        elif np.ndim(data_str) == 1:
            num_rows = len(data_str)
            num_cols = 1
            orientation_horiz = False
        else:
            logger.error("Imported data is a single value or None.")
            return None
        logger.info("_import: c x r = {0} x {1}".format(num_cols, num_rows))
        if orientation_horiz:
            self.ba = [[], []]
            for c in range(num_cols):
                self.ba[0].append(
                    self.QObj[0].frmt2float(data_str[c][0], frmt))
                if num_rows > 1:
                    self.ba[1].append(
                        self.QObj[1].frmt2float(data_str[c][1], frmt))
            if num_rows > 1:
                self._filter_type(ftype='IIR')
            else:
                self._filter_type(ftype='FIR')
        else:
            self.ba[0] =\
                [self.QObj[0].frmt2float(s, frmt) for s in data_str[0]]
            if num_cols > 1:
                self.ba[1] =\
                    [self.QObj[1].frmt2float(s, frmt) for s in data_str[1]]
                self._filter_type(ftype='IIR')
            else:
                self.ba[1] = [1]
                self._filter_type(ftype='FIR')

        self.ba[0] = np.asarray(self.ba[0])
        self.ba[1] = np.asarray(self.ba[1])

        self._equalize_ba_length()
        self.refresh_table()
        qstyle_widget(self.ui.butSave, 'changed')

    # --------------------------------------------------------------------------
    def qdict2ui(self):
        """
        Set the UI from the quantization dict and update the fixpoint quant. object.

        Triggered by:
        - `process_sig_rx()`: self.fx_specs_changed == True or
                                dict_sig['fx_sim'] == 'specs_changed'
        - `self.qfrmt2qdict()`
        - `self.fx_base2qdict()`

        """
        if self.ui.wdg_wq_coeffs_b.q_dict['WI'] != 0\
                and self.ui.wdg_wq_coeffs_b.q_dict['WF'] != 0:
            qset_cmb_box(self.ui.cmb_q_frmt, 'qfrac', data=True)

        # update quantizer objects and widgets
        self.ui.wdg_wq_coeffs_a.dict2ui()
        self.ui.wdg_wq_coeffs_b.dict2ui()

        # qset_cmb_box(self.ui.cmb_q_frmt, self.ui.wdg_wq_coeffs_b.q_dict['qfrmt'])
        # qset_cmb_box(self.ui.cmb_fx_base, self.ui.wdg_wq_coeffs_b.q_dict['fx_base'])

        self.refresh_table()

# ------------------------------------------------------------------------------
    def qfrmt2qdict(self):
        """
        Read out the UI settings of  `self.ui.cmb_q_frmt` (triggering this method)
        and store the old 'qfrmt' setting under the 'qfrmt_last' key.

        The coefficient quantization settings are copied to the quantization dicts
        fb.fil[0]['fxqc']['QCB']` and `...['QCA']` inside the quantization widget
        instances of `FX_UI_WQ` every time something is updated there. This information
        is also kept in the quantization objects `QObj` of the quantization widgets.

        Refresh the table and update quantization widgets, finally emit a signal
        `{'fx_sim': 'specs_changed'}`.
        """
        fb.fil[0]['fxqc']['QCB'].update(
            {'qfrmt_last': fb.fil[0]['fxqc']['QCB']['qfrmt'],
             'qfrmt': qget_cmb_box(self.ui.cmb_q_frmt)})
        fb.fil[0]['fxqc']['QCA'].update(
            {'qfrmt_last': fb.fil[0]['fxqc']['QCA']['qfrmt'],
             'qfrmt': qget_cmb_box(self.ui.cmb_q_frmt)})

        # update quant. widgets and table with the new `qfrmt` settings
        self.qdict2ui()
        self.emit({'fx_sim': 'specs_changed'})

# ------------------------------------------------------------------------------
    def fx_base2qdict(self):
        """
        Read out the UI settings of `self.ui.cmb_fx_base` (triggering this method)
        which specifies the number base (dec, bin, ...)

        The coefficient quantization settings are copied to the quantization dicts
        fb.fil[0]['fxqc']['QCB']` and `...['QCA']` inside the quantization widget
        instances of `FX_UI_WQ` every time something is updated there. This information
        is also kept in the quantization objects `QObj` of the quantization widgets.

        Refresh the table and update quantization widgets. Don't emit a signal
        because this only influences the view not the data itself.
        """
        fb.fil[0]['fxqc']['QCB'].update({'fx_base': qget_cmb_box(self.ui.cmb_fx_base)})
        fb.fil[0]['fxqc']['QCA'].update({'fx_base': qget_cmb_box(self.ui.cmb_fx_base)})

        # update quant. widgets and table with the new `fx_base` settings
        self.qdict2ui()

# ------------------------------------------------------------------------------
    def _save_dict(self):
        """
        Save the coefficient register `self.ba` to the filter dict `fb.fil[0]['ba']`.
        """
        logger.debug("_save_dict called")

        fb.fil[0]['N'] = max(len(self.ba[0]), len(self.ba[1])) - 1

        if fb.fil[0]['ft'] == 'IIR':
            fb.fil[0]['fc'] = 'Manual_IIR'
        else:
            fb.fil[0]['fc'] = 'Manual_FIR'

        # save, check and convert coeffs, check filter type
        try:
            fil_save(fb.fil[0], self.ba, 'ba', __name__)
        except Exception as e:
            # catch exception due to malformatted coefficients:
            logger.error("While saving the filter coefficients, "
                         "the following error occurred:\n{0}".format(e))

        if __name__ == '__main__':
            self.load_dict()  # only needed for stand-alone test

        self.emit({'data_changed': 'input_coeffs'})  # -> input_tab_widgets

        qstyle_widget(self.ui.butSave, 'normal')

# ------------------------------------------------------------------------------
    def clear_table(self):
        """
        Clear self.ba: Initialize coeff for a poles and a zero @ origin,
        a = b = [1; 0].

        Refresh QTableWidget
        """
        self.ba = [np.asarray([1., 0.]), np.asarray([1., 0.])]
        self.refresh_table()
        qstyle_widget(self.ui.butSave, 'changed')

# ------------------------------------------------------------------------------
    def _equalize_ba_length(self):
        """
        test and equalize if b and a subarray have different lengths and copy to
        `self.ba_q`:
        """
        try:
            a_len = len(self.ba[1])
        except IndexError:
            self.ba.append(np.array(1))
            a_len = 1

        D = len(self.ba[0]) - a_len

        if D > 0:  # b is longer than a
            self.ba[1] = np.append(self.ba[1], np.zeros(D))
            self.quant_coeffs_view()
        elif D < 0:  # a is longer than b
            if fb.fil[0]['ft'] == 'IIR':
                self.ba[0] = np.append(self.ba[0], np.zeros(-D))
            else:
                self.ba[1] = self.ba[1][:D]  # discard last D elements of a
            self.quant_coeffs_view()

# ------------------------------------------------------------------------------
    def _delete_cells(self):
        """
        Delete all selected elements in self.ba by:
        - determining the indices of all selected cells in the P and Z arrays
        - deleting elements with those indices
        - equalizing the lengths of b and a array by appending the required
          number of zeros.
        When nothing is selected, delete the last row.
        Finally, refresh the table
        """
        sel = qget_selected(self.tblCoeff)['sel']  # get indices of all selected cells

        if not any(sel) and len(self.ba[0]) > 0:  # nothing selected, delete last row
            self.ba = np.delete(self.ba, -1, axis=1)
        elif np.all(sel[0] == sel[1]) or fb.fil[0]['ft'] == 'FIR':
            # only complete rows selected or FIR -> delete row
            self.ba = np.delete(self.ba, sel[0], axis=1)
        else:
            self.ba[0][sel[0]] = 0
            self.ba[1][sel[1]] = 0
            # self.ba[0] = np.delete(self.ba[0], sel[0])
            # self.ba[1] = np.delete(self.ba[1], sel[1])
        # test and equalize if b and a array have different lengths:
        self._equalize_ba_length()
        self.refresh_table()
        # if length is less than 2, clear the table: this ain't no filter!
        if len(self.ba[0]) < 2:
            self.clear_table()  # sets 'changed' attribute

        qstyle_widget(self.ui.butSave, 'changed')

# ------------------------------------------------------------------------------
    def _add_cells(self):
        """
        Add the number of selected rows to self.ba and fill new cells with
        zeros from the bottom. If nothing is selected, add one row at the bottom.
        Refresh QTableWidget.
        """
        # get indices of all selected cells
        sel = qget_selected(self.tblCoeff)['sel']

        # merge selections in both columns, remove duplicates and sort
        sel_01 = sorted(list(set(sel[0]).union(set(sel[1]))))

        if not any(sel):  # nothing selected, append row of zeros after last row
            self.ba = np.insert(self.ba, len(self.ba[0]), 0, axis=1)
        # elif fb.fil[0]['ft'] == 'IIR':
        else:
            self.ba = np.insert(self.ba, sel_01, 0, axis=1)
        # else:
        # insert 'sel' contiguous rows  before 'row':
        # self.ba[0] = np.insert(self.ba[0], row, np.zeros(sel))

        self._equalize_ba_length()
        self.refresh_table()

        # don't tag as 'changed' when only zeros have been appended to end of table
        if any(sel_01):
            qstyle_widget(self.ui.butSave, 'changed')

# ------------------------------------------------------------------------------
    def _set_eps(self):
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        self.ui.eps = safe_eval(
            self.ui.ledEps.text(), return_type='float', sign='pos', alt_expr=self.ui.eps)
        self.ui.ledEps.setText(str(self.ui.eps))

# ------------------------------------------------------------------------------
    def _set_coeffs_zero(self):
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        self._set_eps()
        idx = qget_selected(self.tblCoeff)['idx']  # get all selected indices

        test_val = 0.  # value against which array is tested
        targ_val = 0.  # value which is set when condition is true
        changed = False

        if not idx:  # nothing selected, check whole table
            # When entry is close to zero (but not = 0), mark as "b_close"
            # and set all marked entries and the corresponding overflow flags = 0
            b_close = np.logical_and(
                np.isclose(self.ba[0], test_val, rtol=0, atol=self.ui.eps),
                (self.ba[0] != targ_val))
            if np.any(b_close):  # found at least one coeff where condition was true
                self.ba[0] = np.where(b_close, targ_val, self.ba[0])
                changed = True

            if fb.fil[0]['ft'] == 'IIR':
                a_close = np.logical_and(
                    np.isclose(self.ba[1], test_val, rtol=0, atol=self.ui.eps),
                    (self.ba[1] != targ_val))
                if np.any(a_close):
                    self.ba[1] = np.where(a_close, targ_val, self.ba[1])
                    changed = True

        else:  # only check selected cells
            for i in idx:
                if np.logical_and(
                    np.isclose(self.ba[i[0]][i[1]], test_val, rtol=0, atol=self.ui.eps),
                        (self.ba[i[0]][i[1]] != targ_val)):
                    self.ba[i[0]][i[1]] = targ_val
                    changed = True
        if changed:
            qstyle_widget(self.ui.butSave, 'changed')  # mark save button as changed

        self.refresh_table()


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.input_widgets.input_coeffs` """
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Input_Coeffs()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
