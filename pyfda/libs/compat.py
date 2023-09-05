# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Was: Compatibility wrapper to obtain same syntax for both Qt4 and 5, PyQt4 has 
been removed
"""

# import PyQt5
from PyQt5 import QtGui, QtCore, QtTest, QtWidgets
from PyQt5.QtCore import (Qt, QEvent, QT_VERSION_STR, PYQT_VERSION_STR, QSize, QSysInfo,
                          QObject, QVariant, QPoint, pyqtSignal, pyqtSlot)
from PyQt5.QtGui import (QFont, QFontMetrics, QIcon, QImage, QTextCursor, QColor,
                         QBrush, QPalette, QPixmap, QPainter)
from PyQt5.QtWidgets import (QAction, QMenu,
                             QMainWindow, QTabWidget, QApplication, QRadioButton,
                             QScrollArea, QSplitter, QMessageBox, QDialog,
                             QWidget, QComboBox, QLabel, QLineEdit, QFrame,
                             QPushButton, QCheckBox, QToolButton, QSpinBox, QDial,
                             QFileDialog, QInputDialog, QPlainTextEdit, QProgressBar,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTextBrowser,
                             QSizePolicy, QAbstractItemView, QSpacerItem,
                             QHBoxLayout, QVBoxLayout, QGridLayout,
                             QStyledItemDelegate, QStyle, QStyleOption)
from PyQt5.QtTest import QTest, QSignalSpy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

# def windowStaysOnTopHint(self, b=True):
#    try:
#        import win32gui, win32con
#        flag = win32con.HWND_TOPMOST if b else win32con.HWND_NOTOPMOST
#        win32gui.SetWindowPos(self.winId(), flag, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
#    except ModuleNotFoundError:
#        pass
#    if b:
#        flag = self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
#    else:
#        flag = self.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint
#    self.setGeometry(self.geometry())  # `setWindowFlags` resets size if setGeometry is never called
#    self.setWindowFlags(flag)
#    self.show()

# except ImportError:
#    import PyQt4
#
#    from PyQt4 import QtGui, QtCore, QtTest
#    from PyQt4.QtCore import (Qt, QEvent, QT_VERSION_STR, QSize, QSysInfo,
#                              QObject, QVariant, pyqtSignal, pyqtSlot)
#    from PyQt4.QtGui import (QAction, QMenu, 
#                             QFont, QFontMetrics, QIcon, QImage, QColor, QBrush, QStyle,
#                             QPalette, QPixmap, 
#                             QMainWindow, QTabWidget, QApplication, QRadioButton,
#                             QScrollArea, QSplitter, QMessageBox, QDialog,
#                             QWidget, QComboBox, QLabel, QLineEdit, QFrame,
#                             QPushButton, QCheckBox, QToolButton, QSpinBox, QDial,
#                             QFileDialog, QInputDialog, QPlainTextEdit,
#                             QTableWidget, QTableWidgetItem, QTextBrowser, QTextCursor,
#                             QSizePolicy, QAbstractItemView,
#                             QHBoxLayout, QVBoxLayout, QGridLayout,
#                             QStyledItemDelegate)
#
#    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar  
# ==============================================================================


# class QFD(QFileDialog):
#     """
#     Subclass QFileDialog methods whose names changed between PyQt4 and PyQt5
#     to provide a common API.
#     """
#     def __init__(self, parent):
#         super(QFD, self).__init__(parent)

#     def getOpenFileName_(self, **kwarg):
#         return self.getOpenFileName(**kwarg)

#     def getOpenFileNames_(self, **kwarg):
#         return self.getOpenFileNames(**kwarg)

#     def getSaveFileName_(self, **kwarg):
#         return self.getSaveFileName(**kwarg)


class QPushButtonRT(QPushButton):
    """
    Subclass QPushButton to render rich text
    """
    def __init__(self, parent=None, text=None, margin=10):
        if parent is not None:
            super().__init__(parent)
        else:
            super().__init__()
        self.__lbl = QLabel(self)
        self.margin = margin
        if text is not None:
            self.__lbl.setText(text)
        self.__lyt = QHBoxLayout()
        self.__lyt.setContentsMargins(margin, 0, 0, 0)  # L, T, R, B
        self.__lyt.setSpacing(0)
        self.setLayout(self.__lyt)
        self.__lbl.setAttribute(Qt.WA_TranslucentBackground)
        self.__lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.__lbl.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )
        self.__lbl.setTextFormat(Qt.RichText)
        self.__lyt.addWidget(self.__lbl, Qt.AlignHCenter)
        return

    def setText(self, text):
        self.__lbl.setText(text)
        self.updateGeometry()
        return

    def sizeHint(self):
        s = QPushButton.sizeHint(self)
        w = self.__lbl.sizeHint()
        s.setWidth(w.width() + 2 * self.margin)
        # s.setHeight(w.height())
        return s

    # def clicked(self):
    #     if self.isChecked():
    #         self.__lbl.setText("chk!")
    #     self.updateGeometry()
    #     return

    # def paintEvent(self, pe):
    #     o = QStyleOption()
    #     o.initFrom(self)
    #     p = QPainter(self)
    #     self.style().drawPrimitive(QStyle.PE_Widget, o, p, self)


if __name__ == '__main__':
    pass
