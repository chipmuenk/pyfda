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
    Create the main window for entering the filter specifications
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
        self.inputAll.setMaximumWidth(280)
        self.pltAll = plot_all.PlotAll() # plot widgets

        

# variable size tabs
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
        
        # ============== UI Layout =====================================
        _widget = QtGui.QWidget() # this widget contains all subwidget groups
        hbox = QtGui.QHBoxLayout(_widget) # horizontal layout of all groups
        hbox.addWidget(self.inputAll)
        hbox.addWidget(self.pltAll)
#        hbox.addWidget(splitter)
        #self.setCentralWidget(_widget)

        self.setWindowTitle('pyFDA - Python Filter Design and Analysis')
    
    
        #Die Die Minimale Größe für das _wiidget liegt bei 800x600 Pixel
        _widget.setMinimumSize(QtCore.QSize(800,600))
        
        #Erstellen der ScrollArea
        scrollArea = QtGui.QScrollArea()
        
        #Das Widget, welches die ScrollArea "überwachen" soll ist _widget
        scrollArea.setWidget(_widget)
        
        #Die Größe des "überwachten" Widgets darf nach oben hin vergrößert werden
        scrollArea.setWidgetResizable(True)
        
        #Das CentralWidget (Focus der GUI?) ist nun die ScrollArea
        self.setCentralWidget(scrollArea)
        


        #=============== Menubar =======================================
        aboutAction = QtGui.QAction('&About', self)
        aboutAction.setShortcut('Ctrl+A')
        aboutAction.setStatusTip('Info about pyFDA')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&About')
        fileMenu.addAction(aboutAction)

        # ============== Signals & Slots ================================

        self.inputAll.inputSpecs.fspecs.specsChanged.connect(self.updateOutput)
        self.inputAll.inputSpecs.filterDesigned.connect(self.updateOutput)
        self.inputAll.inputCoeffs.butSave.clicked.connect(self.updateOutput)
        self.inputAll.inputPZ.butSave.clicked.connect(self.updateOutput)
#        self.inputAll.inputUpdated.connect(self.updateOutput)

        aboutAction.triggered.connect(self.aboutWindow)

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

    app = QtGui.QApplication(sys.argv)
    main = pyFDA()
    app.setWindowIcon(QtGui.QIcon("images/icons/Logo_LST_4.svg"))
    main.setWindowIcon(QtGui.QIcon("images/icons/Logo_LST_4.svg"))
    
    """
    Die Linkeecke des Fensters ist 100pixel in (X und Y) von der oberen linken
    Bildschirmecke entfernt.
    Die Standardgröße des pyFDA Fensters ist 1600x900
    """
    main.setGeometry(100, 100, 1600, 900)
    main.show()

    app.exec_()
