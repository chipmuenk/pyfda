
try:
    import PyQt5
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QT_VERSION_STR
    from PyQt5.QtGui import QFont, QFontMetrics, QTextCursor, QIcon, QImage
    from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QApplication,
                                 QScrollArea, QSplitter, QMessageBox,
                                 QWidget, QComboBox, QLabel, QLineEdit, QFrame,
                                 QPushButton, QCheckBox, QToolButton, QSpinBox, QDial,
                                 QFileDialog, QInputDialog,
                                 QTableWidget, QTableWidgetItem, QTextBrowser, 
                                 QSizePolicy, QAbstractItemView,
                                 QHBoxLayout, QVBoxLayout, QGridLayout)
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    HAS_QT5 = True

except ImportError:
    import PyQt4

    from PyQt4 import QtGui, QtCore
    from PyQt4.QtCore import pyqtSignal, Qt, QEvent, QT_VERSION_STR
    from PyQt4.QtGui import (QFont, QFontMetrics, QIcon, QImage,
                             QMainWindow, QTabWidget, QApplication,
                             QScrollArea, QSplitter, QMessageBox,
                             QWidget, QComboBox, QLabel, QLineEdit, QFrame,
                             QPushButton, QCheckBox, QToolButton, QSpinBox, QDial,
                             QFileDialog, QInputDialog,
                             QTableWidget, QTableWidgetItem, QTextBrowser, QTextCursor,
                             QSizePolicy, QAbstractItemView,
                             QHBoxLayout, QVBoxLayout, QGridLayout)

    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
    HAS_QT5 = False


class QFMetric(object):
    """
    Use QFontMetrics to measure / set the width of widgets depending on the
    font properties and make properties accessible via class attributes:

    wdg_pix_width  = QFMetrics.width("Hallo")#  calculate width in pixels
    wdg_pix_height = QFMetric.H

    # set widget (.e.g. QLineEdit) dimensions:
    my_widget.setFixedSize(wdg_pix_width, wdg_pix_height)

    """

    def __init__(self, parent):
#        super(QFMetric, self).__init__(parent)
        myfont = QFont("", 0)
        self.qfm = QFontMetrics(myfont)
        self.W0 = self.qfm.width("0")
        self.H = self.qfm.height()

        print(self.W0, self.H)
        print(self.qfm.size(0, "0"))

    def width(self, mystring):
        return self.qfm.width(mystring)


class QFD(QFileDialog):
    """
    Subclass QFileDialog methods whose names changed between PyQt4 and PyQt5 
    to provide a common API.
    """
    def __init__(self, parent):
        super(QFD, self).__init__(parent)
    
    def getOpenFileName_(self, **kwarg):
        if HAS_QT5:
            return self.getOpenFileName(**kwarg)
        else:
            return self.getOpenFileNameAndFilter(**kwarg)
            
    def getOpenFileNames_(self, **kwarg):
        if HAS_QT5:
            return self.getOpenFileNames(**kwarg)
        else:
            return self.getOpenFileNamesAndFilter(**kwarg)

    def getSaveFileName_(self, **kwarg):
        if HAS_QT5:
            return self.getSaveFileName(**kwarg)
        else:
            return self.getSaveFileNameAndFilter(**kwarg)



import sys

class QCustomTableWidget (QTableWidget):
    def __init__ (self, parent = None):
        super(QCustomTableWidget, self).__init__(parent)
        # Setup row & column data
        listsVerticalHeaderItem = ['Device 1', 'Device 2', 'Device 3', 'Device 4', 'Device 5']
        self.setRowCount(len(listsVerticalHeaderItem))
        for index in range(self.rowCount()):
            self.setVerticalHeaderItem(index, QtGui.QTableWidgetItem(listsVerticalHeaderItem[index]))
#        listsVerticalHeaderItem = ['Device 1', 'Device 2', 'Device 3', 'Device 4']
        self.setColumnCount(5)
        listsHorizontalHeaderItem = ['Option 1', 'Option 2']
        self.setColumnCount(len(listsHorizontalHeaderItem))
        for index in range(self.columnCount()):
            self.setHorizontalHeaderItem(index, QtGui.QTableWidgetItem(listsHorizontalHeaderItem[index]))

    def dataChanged (self, topLeftQModelIndex, bottomRightQModelIndex):
        row                  = topLeftQModelIndex.row()
        column               = topLeftQModelIndex.column()
        dataQTableWidgetItem = self.item(row, column)
        print('###### Data Changed  ######')
        print('row    :', row + 1)
        print('column :', column + 1)
        print('data   :', dataQTableWidgetItem.text())
        self.emit(QtCore.SIGNAL('dataChanged'), row, column, dataQTableWidgetItem)
        QtGui.QTableWidget.dataChanged(self, topLeftQModelIndex, bottomRightQModelIndex)

class QCustomWidget (QtGui.QWidget):
    def __init__(self, parent = None):
        super(QCustomWidget, self).__init__(parent)
        self.myQCustomTableWidget = QCustomTableWidget(self)
        self.myQLabel = QtGui.QLabel('Track edited data', self)
        myQVBoxLayout = QtGui.QVBoxLayout()
        myQVBoxLayout.addWidget(self.myQLabel)
        myQVBoxLayout.addWidget(self.myQCustomTableWidget)
        self.setLayout(myQVBoxLayout)
        self.connect(self.myQCustomTableWidget, QtCore.SIGNAL('dataChanged'), self.setTrackData)

    def setTrackData (self, row, column, dataQTableWidgetItem):
        self.myQLabel.setText('Last updated\nRow : %d, Column : %d, Data : %s' % (row + 1, column + 1, str(dataQTableWidgetItem.text())))

if __name__ == '__main__':
    myQApplication = QApplication(sys.argv)
    myQCustomWidget = QCustomWidget()
    myQCustomWidget.show()
    sys.exit(myQApplication.exec_())

