# -*- coding: utf-8 -*-
"""
Mainwindow  for the pyFDA app, initializes UI

Authors: Julia Beike, Christian Muenker and Michael Winkler
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import logging
import logging.config
logger = logging.getLogger(__name__)

from PyQt4 import QtGui, QtCore

import pyfda.filterbroker as fb
from pyfda import pyfda_rc as rc
from pyfda.filter_tree_builder import FilterTreeBuilder

from pyfda.input_widgets import input_tab_widgets
from pyfda.plot_widgets import plot_tab_widgets

__version__ = "0.1a5"

# get dir for this file, apppend 'pyfda' and store as base_dir in filterbroker
fb.base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyfda')

class DynFileHandler(logging.FileHandler):
    """
    subclass FileHandler with a customized handler for dynamic definition of
    the logging filepath and -name
    """
    def __init__(self, *args):
        filename, mode = args
        if not os.path.isabs(filename): # path to logging file given in config_file?
            filename = os.path.join(fb.base_dir, filename) # no, use basedir
        logging.FileHandler.__init__(self, filename, mode)

# "register" custom class DynFileHandler as an attribute for the logging module
# to use it inside the logging config file and pass file name / path and mode
# as parameters:
logging.DynFileHandler = DynFileHandler
logging.config.fileConfig(os.path.join(fb.base_dir, rc.log_config_file))#, disable_existing_loggers=True)


if not os.path.exists(rc.save_dir):
    logger.warning('Specified save_dir "%s" doesn\'t exist, using "%s" instead.\n',
        rc.save_dir, fb.base_dir)
    rc.save_dir = fb.base_dir


#class Whitelist(logging.Filter):
#    def __init__(self, **whitelist):
#        self.whitelist = [logging.Filter(name) for name in whitelist]
#        print("filter intialized with", whitelist)
#
#    def filter(self, record):
#        """filter logging record"""
#        arg = any(f.filter(record) for f in self.whitelist)
#        # record.levelno == logging.ERROR
#        # arg = self.param not in record.msg
#        # record.msg = 'changed: ' + record.msg
#        print("filter_arg", arg)
#        return arg


#logging.Filter()


class pyFDA(QtGui.QMainWindow):
    """
    Create the main window consisting of a tabbed widget for entering filter
    specifications, poles / zeros etc. and another tabbed widget for plotting
    various filter characteristics

    QMainWindow is used here as it is a class that understands GUI elements like
    toolbar, statusbar, central widget, docking areas etc.
    """

    def __init__(self):
        super(pyFDA, self).__init__()
        # initialize the FilterTreeBuilder class with the filter directory and
        # the filter file as parameters:         
        # read directory with filterDesigns and construct filter tree from it
        self.ftb = FilterTreeBuilder('filter_design', 'filter_list.txt', comment_char='#')                                  
        self.initUI()

    def initUI(self):
        """
        Intitialize the main GUI, consisting of:
        - Subwindow for parameter selection [-> ChooseParams.ChooseParams()]
        - Filter Design button [-> self.startDesignFilt()]
        - Plot Window [-> plotAll.plotAll()]
        """

        # Instantiate widget groups
        self.inputWidgets = input_tab_widgets.InputTabWidgets() # input widgets
        self.inputWidgets.setMaximumWidth(320) # comment out for splitter

        self.pltWidgets = plot_tab_widgets.PlotTabWidgets() # plot widgets

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
        self.inputWidgets.sigSpecsChanged.connect(self.pltWidgets.update_view)
        #
        # sigFilterDesigned: signal indicating that filter has been DESIGNED,
        #  requiring full update of all plot widgets:
        self.inputWidgets.sigFilterDesigned.connect(self.pltWidgets.update_data)
        #
        # sigReadFilters: button has been pressed to rebuild filter tree:
        self.inputWidgets.inputFiles.sigReadFilters.connect(self.ftb.init_filters)
#####        self.closeEvent.connect(self.aboutToQuit)
#        aboutAction.triggered.connect(self.aboutWindow) # open pop-up window
        logger.debug("Main routine initialized!")

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
    def quitEvent(self): # reimplement QMainWindow.closeEvent
        pass
    
    def closeEvent(self, event): # reimplement QMainWindow.closeEvent von !pyFDA!
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

#    combine with:
#    self.btnExit.clicked.connect(self.close)
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def main():
    """ 
    entry point for the pyfda application 
    see http://pyqt.sourceforge.net/Docs/PyQt4/qapplication.html :
    
    "For any GUI application using Qt, there is precisely *one* QApplication object,
    no matter whether the application has 0, 1, 2 or more windows at any given time.
    ...
    Since the QApplication object does so much initialization, it must be created 
    *before* any other objects related to the user interface are created."     
    """
    app = QtGui.QApplication(sys.argv) # instantiate QApplication object, passing ?
    app.setObjectName("TopApp")

    _desktop = QtGui.QDesktopWidget() # test the available desktop resolution
    screen_h = _desktop.availableGeometry().height()
    screen_w = _desktop.availableGeometry().width()
    logger.info("Available screen resolution: %d x %d", screen_w, screen_h)

    fontsize = 10
    if screen_h < 800:
        delta = 50
    else:
        delta = 100

    app.setStyleSheet(rc.css_rc) 

    mainw = pyFDA()
# http://stackoverflow.com/questions/18416201/core-dump-with-pyqt4
# http://stackoverflow.com/questions/11945183/what-are-good-practices-for-avoiding-crashes-hangs-in-pyqt
# http://stackoverflow.com/questions/5506781/pyqt4-application-on-windows-is-crashing-on-exit
# http://stackoverflow.com/questions/13827798/proper-way-to-cleanup-widgets-in-pyqt
# http://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt

    # Sets the active window to the active widget in response to a system event.
    app.setActiveWindow(mainw) #<---- That makes no difference!



    icon = os.path.join(fb.base_dir, 'images', 'icons', "Logo_LST_4.svg")

    app.setWindowIcon(QtGui.QIcon(icon))
    mainw.setWindowIcon(QtGui.QIcon(icon))

    # set position + size of main window on desktop
    mainw.setGeometry(20, 20, screen_w - delta, screen_h - delta) # top L / top R, dx, dy
    mainw.show()
#    app.show() # -> QApplication doesn't have an attribute "show"
    
       
 #   app.lastWindowClosed.connect(mainw.closeEvent())

    #start the application's exec loop, return the exit code to the OS
    sys.exit(app.exec_()) # same behavior as app.exec_()

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
