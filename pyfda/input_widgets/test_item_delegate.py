# -*- coding: utf-8 -*-
"""
Widget for displaying and modifying filter coefficients
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from PyQt4.QtGui import (QWidget, QLineEdit, QApplication, QFont,
                      QTableWidget, QTableWidgetItem, QVBoxLayout,
                      QStyledItemDelegate)
from PyQt4.QtGui import QStyle
from PyQt4 import Qt
import numpy as np

class ItemDelegate(QStyledItemDelegate):
    """
    The following methods are subclassed to replace display and editor of the
    QTableWidget.
    """
    def __init__(self, parent):
        """
        Pass instance `parent` of parent class (TestTable)
        """
        super(ItemDelegate, self).__init__(parent)
        self.parent = parent # instance of the parent (not the base) class

        
    def paint(self, painter, option, index):
        """
        painter:  instance of QPainter
        option: instance of QStyleOptionViewItem(V4?)
        index:   instance of QModelIndex
        """
        style_option = option
        # read text to be shown:
        if index.row() == 0 and index.column() == 1: # a[0]: always 1
            style_option.text = "1!" # QString object
            style_option.font.setBold(True)
            # now paint the cell
            self.parent.style().drawControl(QStyle.CE_ItemViewItem, style_option, painter)
        else:
            super(ItemDelegate, self).paint(painter, option, index) # default painter

    def displayText(self, text, locale):
        """
        Display `text` in the selected with the selected number
        of digits

        text:   string / QVariant from QTableWidget to be rendered
        locale: locale for the text
        """ 
        data = text.toString() # convert to "normal" string

        return "{0:>{1}}".format(data, 4)
        
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
        editor.setText("{0:>{1}}".format(data, 8))


    def setModelData(self, editor, model, index):
        """
        When editor has finished, read the updated data from the editor,
        convert it back to fractional format and store it in the model 
        (= QTableWidget) and in self.ba

        editor: instance of e.g. QLineEdit
        model:  instance of QAbstractTableModel
        index:  instance of QModelIndex
        """
        data = str(editor.text())# 
        model.setData(index, data)                          # store in QTableWidget 
        self.parent.ba[index.column()][index.row()] = data  # and in self.ba
        

class TestTable(QWidget):
    """
    Create widget for viewing / editing / entering data
    """
    def __init__(self, parent):
        super(TestTable, self).__init__(parent)

        self._construct_UI()

    def _construct_UI(self):
        self.bfont = QFont()
        self.bfont.setBold(True)

        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setItemDelegate(ItemDelegate(self))

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tblCoeff)
        self.setLayout(layVMain)

        self.ba = np.random.randn(3,4)
        self._refresh_table()

#------------------------------------------------------------------------------
    def _refresh_table(self):
        """
        (Re-)Create the displayed table from self.ba with the
        desired number format.
        """
        num_cols = 3
        self.num_rows = 4

        self.ba[1][0] = 1.0 # restore fa[0] = 1 of denonimator polynome
               
        self.tblCoeff.setRowCount(self.num_rows)
        self.tblCoeff.setColumnCount(num_cols)
        # Create strings for index column (vertical header), starting with "0"
        idx_str = [str(n) for n in range(self.num_rows)]
        self.tblCoeff.setVerticalHeaderLabels(idx_str)

        self.tblCoeff.blockSignals(True)
        for col in range(num_cols):
            for row in range(self.num_rows):
                # set table item from self.ba 
                item = self.tblCoeff.item(row, col)
                if item: # does item exist?
                    item.setText(str(self.ba[col][row]))
                else: # no, construct it:
                    self.tblCoeff.setItem(row,col,QTableWidgetItem(
                          str(self.ba[col][row])))

        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()

#------------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    mainw = TestTable(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())