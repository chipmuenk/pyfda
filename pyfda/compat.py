

try:
    import PyQt5
    from PyQt5 import QtGui, QtCore, Qt
    from PyQt5.QtGui import QFont  
    from PyQt5.QtWidgets import QWidget, QComboBox, QLabel, QLineEdit, QFrame
    from PyQt5.QtWidgets import QPushButton, QCheckBox
    from PyQt5.QtWidgets import QFileDialog#, QInputDialog
    from PyQt5.QtWidgets import QSizePolicy
#    from PyQt5.QtWidgets import 
    from PyQt5.QtWidgets import QMainWindow, QTabWidget, QApplication
    from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout
except ImportError as err:
    print(err)
    import PyQt4
    from PyQt4 import QtGui, QtCore, Qt
    from PyQt4.QtGui import QWidget, QComboBox, QLabel, QLineEdit, QFrame
    from PyQt4.QtGui import QPushButton, QCheckBox, QFont
    from PyQt4.QtGui import QFileDialog#, QInputDialog
    from PyQt4.QtGui import QSizePolicy
    from PyQt4.QtGui import QMainWindow, QTabWidget, QApplication
    from PyQt4.QtGui import QHBoxLayout, QVBoxLayout, QGridLayout



