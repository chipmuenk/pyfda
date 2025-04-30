# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
This class controls the view of QTableWidget items in a Model-View-Delegate
architecture of the `Input_Coeffs()` widget. Coefficients of a digital filter
can be viewed and edited in various fixpoint and float formats.

Globally, coefficients are stored in the 2D float list `fb.fil[0]['ba']` 
where the numerator b is the first and the denominator a the second column.
A local copy is created as `self.parent.ba` of `Input_Coeffs()`where edits are
stored via `setModelData()`. Changes are only passed back to the original
`fb.fil[0]['ba']` list by `self.parent._save_dict()` when the user presses
the `Apply` button in the `Input_Coeffs_UI()`.

Coefficients are displayed and stored in a QTableWidget as string objects
number of rows. The first column contains the numerator b coefficients, the
second column the denominator a coefficients. The number of rows is set by
Quantized data is stored in 2D float array `self.parent.ba_q` where again 
the numerator b is the first and the denominator a the second column.

The coefficients are displayed as floats or in a fixed-point format with
user-defined number base and number of bits. 

The quantizer is an instance of the `fx.Fixed()` class, it is used to
convert the coefficients to fixed-point format and to display the coefficients 
in the selected format (int, hex, ...). The quantizer is created in the 
`Input_Coeffs` class and passed to this class via the `parent` parameter as
`self.Q = [self.parent.ui.wdg_wq_coeffs_b.Q, self.parent.ui.wdg_wq_coeffs_a.Q]`
"""
import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals

from pyfda.libs.compat import Qt, QtCore, QLineEdit, QSize, QStyledItemDelegate, QColor, QBrush
from pyfda.libs.pyfda_lib import safe_eval
from pyfda.libs.pyfda_qt_lib import qstyle_widget
from pyfda.pyfda_rc import params

# TODO: Fixpoint coefficients do not properly convert complex -> float when saving
#       the filter?
# TODO: This ItemDelegate method displayText is called again and again when an
#        item is selected?!
# TODO: negative values for WI don't work correctly

class ItemDelegateCoeffs(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.

    - `displayText()` displays the data stored in the table in various number formats

    - `createEditor()` creates a line edit instance for editing table entries

    - `setEditorData()` pass data with full precision and in selected format to editor

    - `setModelData()` pass edited data back to model (`self.ba`)

    Editing the table triggers `setModelData()` but does not emit a signal outside
    this class, only the `ui.but_apply` and `ui.but_undo` buttons are highlighted.
    When it is pressed, a signal with `'data_changed':'input_coeffs'` is produced in
    class `Input_Coeffs`. Additionally, a signal is emitted with `'fx_sim': 'specs_changed'`
    """

    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (Input_Coeffs)
        """
        super().__init__()
        self.parent = parent  # instance of the parent (not the base) class
        # handles to quantization objects (fx.Fixed() instance) of coefficient widgets
        self.Q = [self.parent.ui.wdg_wq_coeffs_b.Q, self.parent.ui.wdg_wq_coeffs_a.Q]

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
#         logger.debug("Ovr_flag:".format(self.parent.self.Q[0].ovr_flag))
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
            super().initStyleOption(option, index)

    # -------------------------------------------------------------------------
    def text(self, item) -> str:
        """
        Return item text as string transformed by self.displayText()

        This is used a.o. by `pyfda_io_lib.qtable2csv()` and  `libs.pyfda_fix_lib`
        to read out a table in text mode, e.g. `text = table.itemDelegate().text(item)`
        """
        return str(self.displayText(item.text(), QtCore.QLocale()))

    # -------------------------------------------------------------------------
    def displayText(self, text, locale) -> str:
        """
        Display `text` with selected fixpoint base and number of places

        text:   string / QVariant from QTableWidget to be rendered
        locale: locale for the text

        The instance parameter `Q[c].ovr_flag` is set to +1 or -1 for
         positive / negative overflows, else it is 0.
        """

        if not fb.fil[0]['fx_sim']:
            # convert to float and return as string with number of digits defined
            # in `params['FMT_ba']` (default: 6)
            data = safe_eval(text, return_type='auto')  # convert to float
            return f"{data:#.{params['FMT_ba']}g}"

        if fb.fil[0]['fx_base'] == 'dec':
            # text is decimal format, return with number of decimal places calculated
            # from the total number of bits
            return f"{text:>{self.Q[0].places}}"

        return text  # else: return text as rendered in the table
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
        data = safe_eval(self.parent.ba[index.column()][index.row()],
                         return_type="auto")

        if fb.fil[0]['fx_sim']:
            # fixpoint format with base:
            # pass requantized data with required number of decimal places
            editor.setText(
                "{0:>{1}}".format(self.Q[index.column()].float2frmt(data),
                                  self.Q[index.column()].places))
        else:
            # floating point format: pass data with full resolution
            editor.setText(str(data))

    # -------------------------------------------------------------------------
    def setModelData(self, editor, model, index) -> None:
        """
        When editing has finished, read the updated data from the editor (= QTableWidget),
        and store it in `self.ba` as float / complex for `fb.fil[0]['fx_sim'] == False`.

        For all other formats, convert data back to floating point format via
        `frmt2float()` and store it in `self.ba` as float / complex. Next, use
        `float2frmt()` to quantize data and store it in `parent.ba_q`.
        Finally, refresh the whole table - this might be needed to adapt the table
        to a longer number format. Alternatively, one could use `_refresh_table_item()`
        for a single item. 

        Parameters
        ----------
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
        if not fb.fil[0]['fx_sim']:
            data = safe_eval(
                str(editor.text()), self.parent.ba[index.column()][index.row()],
                return_type='auto')  # raw float data without fixpoint formatting
            data_q = data
        else:
            # fixpoint format: read editor string and transform to float (`data`)
            # convert `data` to fixpoint format as `data_q`
            data = self.Q[index.column()].frmt2float(str(editor.text()))
            data_q = self.Q[index.column()].float2frmt(data)

        if isinstance(data, complex):
            # if data is complex, convert whole column (b or a array) to complex
            self.parent.ba[index.column()] = self.parent.ba[index.column()].astype(complex)
        if isinstance(data_q, complex):
            # if data_q is complex, convert whole column (b or a array) to complex
            self.parent.ba_q[index.column()] = self.parent.ba_q[index.column()].astype(complex)
        # store new data in `self.parent.ba` and `ba_q``
        self.parent.ba[index.column()][index.row()] = data
        self.parent.ba_q[index.column()][index.row()] = data_q

        qstyle_widget(self.parent.ui.but_apply, 'changed')
        qstyle_widget(self.parent.ui.but_undo, 'changed')
        # this is needed to adapt text width to e.g. complex number representation
        self.parent.refresh_table()
        # self.parent._refresh_table_item(index.row(), index.column())  # refresh table item
