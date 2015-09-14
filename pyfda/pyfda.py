# -*- coding: utf-8 -*-
"""
Mainwindow  for the pyFDA app, initializes UI

Authors: Julia Beike, Christian Muenker and Michael Winkler
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui, QtCore

from pyfda import pyfda_rc
from .input_widgets import input_tab_widgets
from .plot_widgets import plot_tab_widgets

__version__ = "0.1a1"

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
#                                    comment_char = '#', DEBUG = DEBUG) #

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
        layHMain.setContentsMargins(0, 0, 0, 0)#(left, top, right, bottom)


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
        """
        Display an "About" window
        """
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
    app.setObjectName("TopApp")

    _desktop = QtGui.QDesktopWidget()
    screen_h = _desktop.availableGeometry().height()
    screen_w = _desktop.availableGeometry().width()
    print("Available screen resolution:", screen_w, "x", screen_h)

    fontsize = 10
    if screen_h < 800:
        delta = 50
    else:
        delta = 100

    myFont = QtGui.QFont("Tahoma", fontsize)

#    app.setFont(myFont)
    app.setStyleSheet(pyfda_rc.css_rc['TopWidget']) 
#                      pyfda_rc.css_rc['LineEdit'] +
 #                     pyfda_rc.css_rc['TabBar'])
    mainw = pyFDA()

    icon = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'images', 'icons', "Logo_LST_4.svg")

    app.setWindowIcon(QtGui.QIcon(icon))
    mainw.setWindowIcon(QtGui.QIcon(icon))

    # set position + size of main window on desktop
    mainw.setGeometry(20, 20, screen_w - delta, screen_h - delta) # top L / top R, dx, dy
    mainw.show()

#    def fdaQuit():
#        if blabla:
#        app.quit()
#        
#    app.lastWindowClosed.connect(fdaQuit)

    app.exec_()

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
