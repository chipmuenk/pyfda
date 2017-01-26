# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 08:56:46 2017

@author: Christian Muenker
"""
#from PyQt4.QtGui
from PyQt5.QtWidgets import (QApplication, QWidget, QTableWidget, QTableWidgetItem,
                         QLabel, QVBoxLayout,QStyledItemDelegate)
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import QEvent
from numpy.random import randn
"""
http://stackoverflow.com/questions/36905614/how-to-set-text-to-qlineedit-when-it-is-used-as-qitemdelegate-with-qtableview
"""

class ItemDelegate(QStyledItemDelegate):
    def displayText(self, text, locale):
        return "{:.3g}".format(float(text))

class EventTable (QWidget):
    def __init__(self, parent = None):
        super(EventTable, self).__init__(parent)
        self.myTable = QTableWidget(self)
        self.myTable.setItemDelegate(ItemDelegate(self))
        myQVBoxLayout = QVBoxLayout()
        myQVBoxLayout.addWidget(self.myTable)
        self.setLayout(myQVBoxLayout)
        self.rows = 3; self.columns = 4 # table + data dimensions
        self.data = randn(self.rows, self.columns) # initial data
        self._update_table() # create table

    def _update_table(self):
        self.myTable.setRowCount(self.rows)
        self.myTable.setColumnCount(self.columns)
        for col in range(self.columns):
            for row in range(self.rows):
                item = QTableWidgetItem(str(self.data[row][col]))
                self.myTable.setItem(row, col, item)
        self.myTable.resizeColumnsToContents()
        self.myTable.resizeRowsToContents()
        
        for col in range(self.columns):
            for row in range(self.rows):
                print(self.myTable.item(row, col).text())

        
        

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    mainw = EventTable()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())