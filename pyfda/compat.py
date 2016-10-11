
try:
    import PyQt5
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtCore import pyqtSignal, Qt, QEvent
    from PyQt5.QtGui import QFont, QTextCursor, QIcon, QImage
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
    from PyQt4.QtCore import pyqtSignal, Qt, QEvent
    from PyQt4.QtGui import (QFont, QIcon, QImage,
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


class QFD(QFileDialog):
    """
    Subclass methods whose names changed between PyQt4 and PyQt5 and provide
    a common API.
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




