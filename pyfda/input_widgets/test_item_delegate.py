# -*- coding: utf-8 -*-
from __future__ import print_function, division, unicode_literals, absolute_import
#from PyQt4.QtGui import  ...
from PyQt5.QtWidgets import (QWidget, QApplication, QTableWidget, 
                             QTableWidgetItem, QVBoxLayout, QStyledItemDelegate)
from PyQt5.QtWidgets import QStyle  
from PyQt5.QtGui import QFont
#from PyQt4.QtGui import QStyle, QFont
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
        if index.row() == 0 and index.column() == 1: # always 1 at index (0,0)
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
        data = text # .toString() # Python 2: need to convert to "normal" string
        return "{0:>{1}}".format(data, 4)
                

class TestTable(QWidget):
    """ Create widget for viewing / editing / entering data """
    def __init__(self, parent):
        super(TestTable, self).__init__(parent)

        self.bfont = QFont()
        self.bfont.setBold(True)

        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setItemDelegate(ItemDelegate(self))

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tblCoeff)
        self.setLayout(layVMain)

        self.ba = np.random.randn(3,4) # test data
        self._refresh_table()

#------------------------------------------------------------------------------
    def _refresh_table(self):
        """ (Re-)Create the displayed table from self.ba """
        num_cols = 3
        num_rows = 4
               
        self.tblCoeff.setRowCount(num_rows)
        self.tblCoeff.setColumnCount(num_cols)

        for col in range(num_cols):
            for row in range(num_rows):
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