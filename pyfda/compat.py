

try:
    import PyQt5
    from PyQt5 import QtGui, QtCore
    from PyQt5.QtCore import pyqtSignal, Qt, QEvent
    from PyQt5.QtGui import QFont, QTextCursor
    from PyQt5.QtWidgets import (QWidget, QComboBox, QLabel, QLineEdit, QFrame,
                                 QPushButton, QCheckBox, QToolButton, QSpinBox,
                                 QFileDialog, QInputDialog,
                                 QTableWidget, QTableWidgetItem, QTextBrowser, 
                                 QSizePolicy, QAbstractItemView,
                                 QMainWindow, QTabWidget, QApplication,
                                 QHBoxLayout, QVBoxLayout, QGridLayout)
except ImportError as err:
    print(err)
    import PyQt4

    from PyQt4 import QtGui, QtCore
    from PyQt4.QtCore import pyqtSignal, Qt, QEvent
    from PyQt4.QtGui import (QFont,
                             QWidget, QComboBox, QLabel, QLineEdit, QFrame,
                             QPushButton, QCheckBox, QToolButton, QSpinBox,
                             QFileDialog, QInputDialog,
                             QTableWidget, QTableWidgetItem, QTextBrowser, QTextCursor,
                             QSizePolicy, QAbstractItemView,
                             QMainWindow, QTabWidget, QApplication,
                             QHBoxLayout, QVBoxLayout, QGridLayout)




