# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Julia Beike, Christian Muenker und Michael Winkler

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
        
        #War früher 280px, aber dann gibt es in den Input Widgets Probleme mit der gesamten Darstellung
        self.inputAll.setMaximumWidth(280) # comment out for splitter
        self.pltAll = plot_all.PlotAll() # plot widgets
        
        # ============== UI Layout =====================================
        _widget = QtGui.QWidget() # this widget contains all subwidget groups

        _desktop = QtGui.QDesktopWidget()
        screen_h = _desktop.availableGeometry().height()
        screen_w = _desktop.availableGeometry().width()

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
#        self.setCentralWidget(_widget)

        self.setWindowTitle('pyFDA - Python Filter Design and Analysis')
    
        # set minimum _widget size of central widget (matplotlib canvas) before scrollbars appear
        # print(_widget.height())
    
        # Create scroll area and "monitor" _widget whether scrollbars are needed
        scrollArea = QtGui.QScrollArea()
        scrollArea.setWidget(_widget)
        
        _widget.setMinimumSize(QtCore.QSize(800,500))
#        scrollArea.setMinimumSize(QtCore.QSize(screen_w - 200,screen_h - 200))
        
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
#        

        # ============== Signals & Slots ================================

        self.inputAll.inputSpecs.fspecs.specsChanged.connect(self.updateOutput)
        self.inputAll.inputSpecs.filterDesigned.connect(self.updateOutput)
        self.inputAll.inputCoeffs.butSave.clicked.connect(self.updateOutput)
        self.inputAll.inputPZ.butSave.clicked.connect(self.updateOutput)
#        self.inputAll.inputUpdated.connect(self.updateOutput)

#        aboutAction.triggered.connect(self.aboutWindow)

        self.statusMessage("Application is initialized.")

    def updateOutput(self):
        self.inputAll.updateAll() # input widgets re-read 'coeffs' / 'zpk'
        self.pltAll.updateAll()
#        self.frmInput.adjustSize()
#        self.pltAll.adjustSize()

    def aboutWindow(self):
        QtGui.QMessageBox.about(self, "About pyFDA",
        ("(c) 2013 - 15 Christian Münker\n\n"
        "A graphical tool for designing, analyzing and synthesizing digital filters")
        )

    def statusMessage(self, message):
        self.statusBar().showMessage(message)
        


#------------------------------------------------------------------------------

if __name__ == '__main__':
    myFont = QtGui.QFont("Tahoma", 10)
    app = QtGui.QApplication(sys.argv)
    app.setFont(myFont)
    main = pyFDA()
    app.setWindowIcon(QtGui.QIcon("images/icons/Logo_LST_4.svg"))
    main.setWindowIcon(QtGui.QIcon("images/icons/Logo_LST_4.svg"))
    
    """
    Die Linkeecke des Fensters ist 20 pixel in (X und Y) von der oberen linken
    Bildschirmecke entfernt.
    """
    main.setGeometry(20, 20, 1200, 700) # ltop left / top right, deltax, delta y
    main.show()

    app.exec_()
