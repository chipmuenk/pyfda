# -*- coding: utf-8 -*-
"""
Mainwindow  for the pyFDA app, initializes UI 

Authors: Julia Beike, Christian Muenker and Michael Winkler
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
from PyQt4 import QtGui, QtCore

#import filterbroker as fb # importing filterbroker initializes all its globals
from .input_widgets import input_tab_widgets 
from .plot_widgets import plot_tab_widgets

class pyFDA(QtGui.QMainWindow):
    """
    Create the main window consisting of a tabbed widget for entering filter
    specifications, poles / zeros etc. and another tabbed widget for plotting 
    various filter characteristics
    
    QMainWindow is used here as it is a class that understands GUI elements like 
    toolbar, statusbar, central widget, docking areas etc.
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
        self.inputWidgets = input_tab_widgets.InputWidgets() # input widgets        
        self.inputWidgets.setMaximumWidth(320) # comment out for splitter
        
        self.pltWidgets = plot_tab_widgets.PlotWidgets() # plot widgets
        
        # ============== UI Layout =====================================
        _widget = QtGui.QWidget() # this widget contains all subwidget groups

        layHMain = QtGui.QHBoxLayout(_widget) # horizontal layout of all groups

        # comment out following 3 lines for splitter design
        layHMain.addWidget(self.inputWidgets)        
        layHMain.addWidget(self.pltWidgets)
        layHMain.setContentsMargins(0,0,0,0)#(left, top, right, bottom)


# variable size tabs (splitter)
#        layVInput = QtGui.QVBoxLayout()
#        layVInput.addWidget(self.inputWidgets)
#        layVPlt = QtGui.QVBoxLayout()
#        layVPlt.addWidget(self.pltWidgets)
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

#        self.statusMessage("Application is initialized.")
       

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # Here, signals about spec and design changes from lower hierarchies
        # are distributed. At the moment, only changes in the input widgets are
        # routed to the plot widgets:
        # 
        # sigSpecsChanged: signal indicating that filter SPECS have changed, 
        # requiring partial update of some plot widgets:
        self.inputWidgets.sigSpecsChanged.connect(self.pltWidgets.updateSpecs)
        #
        # sigFilterDesigned: signal indicating that filter has been DESIGNED,
        #  requiring full update of all plot widgets: 
        self.inputWidgets.sigFilterDesigned.connect(self.pltWidgets.updateData)

        
#        aboutAction.triggered.connect(self.aboutWindow) # open pop-up window


#------------------------------------------------------------------------------
    def aboutWindow(self):
        QtGui.QMessageBox.about(self, "About pyFDA",
        ("(c) 2013 - 15 Christian Münker\n\n"
        "A graphical tool for designing, analyzing and synthesizing digital filters")
        )

#------------------------------------------------------------------------------
    def statusMessage(self, message):
        """
        Display a message in the statusbar.
        """
        self.statusBar().showMessage(message)


#------------------------------------------------------------------------------
def main():
    """ entry point for the pyfda application """
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
    mainw = pyFDA()
    app.setWindowIcon(QtGui.QIcon("images/icons/Logo_LST_4.svg"))
    mainw.setWindowIcon(QtGui.QIcon("images/icons/Logo_LST_4.svg"))
    
    
    # set position + size of main window on desktop
    mainw.setGeometry(20, 20, screen_w - delta, screen_h - delta) # ltop left / top right, deltax, delta y
    mainw.show()

    app.exec_()
    
#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()