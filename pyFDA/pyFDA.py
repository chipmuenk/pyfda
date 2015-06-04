# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Julia Beike, Christian Muenker and Michael Winkler

Mainwindow  for the pyFDA app, initializes UI
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
from PyQt4 import QtGui, QtCore

#import filterbroker as fb # importing filterbroker initializes all its globals
from input_widgets import input_all
from plot_widgets import plot_all

class pyFDA(QtGui.QMainWindow):
    """
    Create the main window consisting of a tabbed widget for entering filter
    specifications, poles / zeros etc. and another tabbed widget for plotting 
    various filter characteristics
    
    QMainWindow is a class that understands GUI elements like a toolbar, statusbar,
    central widget, docking areas. QWidget is just a raw widget.
    When you want to have a main window for you project, use QMainWindow.

    If you want to create a dialog box (modal dialog), use QWidget, or,
    more preferably, QDialog
    """
    
    def __init__(self):
        self.DEBUG = True
        super(pyFDA, self).__init__()
        # read directory with filterDesigns and construct filter tree from it
#        self.ffr = FilterFileReader('Init.txt', 'filterDesign',
#                                    commentChar = '#', DEBUG = DEBUG) #

        #self.em = QtGui.QFontMetricsF(QtGui.QLineEdit.font()).width('m')
        self.initUI()

    def initUI(self):
        """
        Intitialize the main GUI, consisting of:
        - Subwindow for parameter selection [-> ChooseParams.ChooseParams()]
        - Filter Design button [-> self.startDesignFilt()]
        - Plot Window [-> plotAll.plotAll()]
        """
        
        # Instantiate widget groups
        self.inputAll = input_all.InputAll() # input widgets        
        self.inputAll.setMaximumWidth(280) # comment out for splitter
        
        self.pltAll = plot_all.PlotAll() # plot widgets
        
        # ============== UI Layout =====================================
        _widget = QtGui.QWidget() # this widget contains all subwidget groups

        layHMain = QtGui.QHBoxLayout(_widget) # horizontal layout of all groups

        # comment out following 3 lines for splitter design
        layHMain.addWidget(self.inputAll)        
        layHMain.addWidget(self.pltAll)
        layHMain.setContentsMargins(0,0,0,0)#(left, top, right, bottom)


# variable size tabs (splitter)
#        layVInput = QtGui.QVBoxLayout()
#        layVInput.addWidget(self.inputAll)
#        layVPlt = QtGui.QVBoxLayout()
#        layVPlt.addWidget(self.pltAll)
#        
#        frmInput = QtGui.QFrame()
#        frmInput.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
#        frmInput.setLayout(layVInput)
#        frmInput.setSizePolicy(QtGui.QSizePolicy.Minimum,
#                                 QtGui.QSizePolicy.Minimum)
# 
#        frmPlt = QtGui.QFrame()
#        frmPlt.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
#        frmPlt.setLayout(layVPlt)
#        frmPlt.setSizePolicy(QtGui.QSizePolicy.Minimum,
#                                 QtGui.QSizePolicy.Minimum)
#                                 
#        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
#        splitter.addWidget(frmInput)
#        splitter.addWidget(frmPlt)
#        layHMain.addWidget(splitter)

        self.setWindowTitle('pyFDA - Python Filter Design and Analysis')
    
    
        # Create scroll area and "monitor" _widget whether scrollbars are needed
        scrollArea = QtGui.QScrollArea()
        scrollArea.setWidget(_widget) # splitter for var. size tabs?
        
        #============= Set behaviour of scroll area ======================
        # scroll bars appear when the scroll area shrinks below this size:
        scrollArea.setMinimumSize(QtCore.QSize(800, 500)) 
#        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded) #default
#        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded) # default                                
        scrollArea.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                 QtGui.QSizePolicy.MinimumExpanding)

        # Size of monitored widget is allowed to grow:
        scrollArea.setWidgetResizable(True)

        
        # CentralWidget (focus of GUI?) is now the ScrollArea
        self.setCentralWidget(scrollArea)


        #=============== Menubar =======================================

#        aboutAction = QtGui.QAction('&About', self)
#        aboutAction.setShortcut('Ctrl+A')
#        aboutAction.setStatusTip('Info about pyFDA')
#
#        menubar = self.menuBar()
#        fileMenu = menubar.addMenu('&About')
#        fileMenu.addAction(aboutAction)

        self.statusMessage("Application is initialized.")
       

        # ============== Signals & Slots ================================

        self.inputAll.sigFilterDesigned.connect(self.pltAll.updateAll)

        self.inputAll.sigSpecsChanged.connect(self.pltAll.updateSpecs)
        
#        aboutAction.triggered.connect(self.aboutWindow) # open pop-up window


    def aboutWindow(self):
        QtGui.QMessageBox.about(self, "About pyFDA",
        ("(c) 2013 - 15 Christian Münker\n\n"
        "A graphical tool for designing, analyzing and synthesizing digital filters")
        )

    def statusMessage(self, message):
        """
        Display a message in the statusbar.
        """
        self.statusBar().showMessage(message)

#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    
    _desktop = QtGui.QDesktopWidget()
    screen_h = _desktop.availableGeometry().height()
    screen_w = _desktop.availableGeometry().width()
    print(screen_h, screen_w)

    fontsize = 10    
    if screen_h < 800:
        delta = 50
    else:
        delta = 100


    myFont = QtGui.QFont("Tahoma", fontsize)

    app.setFont(myFont)
    main = pyFDA()
    app.setWindowIcon(QtGui.QIcon("images/icons/Logo_LST_4.svg"))
    main.setWindowIcon(QtGui.QIcon("images/icons/Logo_LST_4.svg"))
    
    
    # set position + size of main window on desktop
    main.setGeometry(20, 20, screen_w - delta, screen_h - delta) # ltop left / top right, deltax, delta y
    main.show()

    app.exec_()
