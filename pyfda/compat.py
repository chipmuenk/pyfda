
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

# use QFontMetrics to measure / set the width of widgets depending on the
# font properties and store it in filter broker
myfont = QFont("", 0)
QFMetric = QFontMetrics(myfont)
QFMetric.xxx = 13

# wdg_pix_width  = QFMetrics.width("Hallo")# calculate width in pixels
# wdg_pix_height = QFMetric.height()
# my_widget.setFixedSize(wdg_pix_width, wdg_pix_height) # set widget dimensions


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




