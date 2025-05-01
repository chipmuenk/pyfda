# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for displaying and modifying filter Poles and Zeros
"""
from pyfda.libs.compat import (
    QtCore, QLineEdit, QBrush, QColor, QSize, QStyledItemDelegate, Qt)
from pyfda.libs.pyfda_qt_lib import qstyle_widget
from pyfda.libs.pyfda_lib import frmt2cmplx
from pyfda.pyfda_rc import params

class ItemDelegatePZ(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.

    - `displayText()` displays the data stored in the table in various number formats
    - `createEditor()` creates a line edit instance for editing table entries
    - `setEditorData()` pass data with full precision and in selected format to editor
    - `setModelData()` pass edited data back to model (`self.zpk`)
    """
    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (Input_PZ)
        """
        super().__init__(parent)
        self.parent = parent  # instance of the parent (not the base) class

    # --------------------------------------------------------------------------
    def initStyleOption(self, option, index):
        """
        Initialize `option` with the values using the `index` index. All items are
        passed to the original `initStyleOption()` which then calls `displayText()`.

        Afterwards, check whether a pole (index.column() == 1 )is outside the
        UC and color item background accordingly (not implemented yet).
        """
        # continue with the original `initStyleOption()` and call displayText()
        super().initStyleOption(option, index)
        # test for poles with magnitude > 1
        if index.column() == 1 and False:
            # Color item backgrounds with poles outside the UC red
            option.backgroundBrush = QBrush(Qt.SolidPattern)
            option.backgroundBrush.setColor(QColor(100, 0, 0, 80))

    # --------------------------------------------------------------------------
    def text(self, item) -> str:
        """
        Return item text as string transformed by self.displayText()
        """
        return self.displayText(item.text(), QtCore.QLocale())

    # --------------------------------------------------------------------------
    def displayText(self, text: str, locale) -> str:
        """
        Display `text` with selected format (cartesian / polar)
        and number of places

        text:   string / QVariant from QTableWidget to be rendered
        locale: locale for the text
        """
        return self.parent.cmplx2frmt(text, places=params['FMT_pz'])

    # --------------------------------------------------------------------------
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

    # --------------------------------------------------------------------------
    def setEditorData(self, editor, index):
        """
        Pass the data to be edited to the editor:
        - retrieve data with full accuracy (`places=-1`) from `zpk` (in float format)
        - represent it in the selected format (Cartesian, polar, ...)

        editor: instance of e.g. QLineEdit
        index:  instance of QModelIndex
        """
        data = self.parent.zpk[index.column()][index.row()]
        data_str = self.parent.cmplx2frmt(data, places=-1)
        editor.setText(data_str)

    # --------------------------------------------------------------------------
    def setModelData(self, editor, model, index):
        """
        When editor has finished, read the updated data from the editor,
        convert it to complex format and store it in both the model
        (= QTableWidget) and in `zpk`. Finally, refresh the table item to
        display it in the selected format (via `to be defined`) and normalize
        the gain.

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

        # convert entered string to complex, pass the old value as default
        data = frmt2cmplx(editor.text(), self.parent.zpk[index.column()][index.row()])
        model.setData(index, data)                          # store in QTableWidget
        self.parent.zpk[index.column()][index.row()] = data  # and in self.ba
        qstyle_widget(self.parent.ui.but_apply, 'changed')
        qstyle_widget(self.parent.ui.but_undo, 'changed')

        self.parent._refresh_table_item(index.row(), index.column())  # refresh table entry
        self.parent._normalize_gain()  # recalculate gain

# ===================================================================================
