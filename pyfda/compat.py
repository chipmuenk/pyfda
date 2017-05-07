
try:
    import PyQt5
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QT_VERSION_STR, QSize, QSysInfo
    from PyQt5.QtGui import QFont, QFontMetrics, QIcon, QImage, QTextCursor, QColor, QBrush
    from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QApplication,
                                 QScrollArea, QSplitter, QMessageBox,
                                 QWidget, QComboBox, QLabel, QLineEdit, QFrame,
                                 QPushButton, QCheckBox, QToolButton, QSpinBox, QDial,
                                 QFileDialog, QInputDialog,
                                 QTableWidget, QTableWidgetItem, QTextBrowser,
                                 QSizePolicy, QAbstractItemView,
                                 QHBoxLayout, QVBoxLayout, QGridLayout,
                                 QStyledItemDelegate, QStyle)
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    HAS_QT5 = True

except ImportError:
    import PyQt4

    from PyQt4 import QtGui, QtCore
    from PyQt4.QtCore import pyqtSignal, Qt, QEvent, QT_VERSION_STR, QSize, QSysInfo
    from PyQt4.QtGui import (QFont, QFontMetrics, QIcon, QImage, QColor, QBrush, QStyle,
                             QMainWindow, QTabWidget, QApplication,
                             QScrollArea, QSplitter, QMessageBox,
                             QWidget, QComboBox, QLabel, QLineEdit, QFrame,
                             QPushButton, QCheckBox, QToolButton, QSpinBox, QDial,
                             QFileDialog, QInputDialog,
                             QTableWidget, QTableWidgetItem, QTextBrowser, QTextCursor,
                             QSizePolicy, QAbstractItemView,
                             QHBoxLayout, QVBoxLayout, QGridLayout,
                             QStyledItemDelegate)

    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
    HAS_QT5 = False
    

#==============================================================================
# class QFMetric(object):
#     """
#     Use QFontMetrics to measure / set the width of widgets depending on the
#     font properties and make properties accessible via class attributes:
# 
#     wdg_pix_width  = QFMetrics.width("Hallo")#  calculate width in pixels
#     wdg_pix_height = QFMetric.H
# 
#     # set widget (.e.g. QLineEdit) dimensions:
#     my_widget.setFixedSize(wdg_pix_width, wdg_pix_height)
# 
#     # Alternative without importing QFontMetric explicitly: 
#     my_widget.setFont(QFont("", 0)) # without this, returned dimensions are smaller?!
#     W6 = my_widget.fontMetrics().boundingRect("000000").width()
#     H = my_widget.sizeHint().height()
#     """
# 
#     def __init__(self, parent):
# #        super(QFMetric, self).__init__(parent)
#         myfont = QFont("", 0)
#         self.qfm = QFontMetrics(myfont)
#         self.W0 = self.qfm.width("0") # width of "0" in pixels
#         self.H = self.qfm.height() # height of "0" in pixels (too tight on some systems)
# 
#         # define class attributes
#         test_label = QLabel("0")
#         test_edit = QLineEdit()
#         #QFMetric.H = round(test_edit.sizeHint().height())
#         #QFMetric.W0 = round(test_label.sizeHint().width())
#         # print("LabelW, LabelH, EditH:", QFMetric.W0, round(test_label.sizeHint().height()), QFMetric.H)
# 
#     def width(self, mystring):
#         return self.qfm.width(mystring)
# 
#==============================================================================

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


if __name__ == '__main__':
    pass