# -*- coding: utf-8 -*-
"""
Mainwindow  for the pyFDA app, initializes UI

Authors: Julia Beike, Christian Muenker and Michael Winkler
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from sip import setdestroyonexit
import logging
import logging.config
logger = logging.getLogger(__name__)

from PyQt4 import QtGui, QtCore

import pyfda.filterbroker as fb
from pyfda import pyfda_lib
from pyfda import pyfda_rc as rc
from pyfda import qrc_resources # contains all icons
# create with pyrcc4 pyfda.qrc -o qrc_resources.py -py3
from pyfda.filter_tree_builder import FilterTreeBuilder

from pyfda.input_widgets import input_tab_widgets
from pyfda.plot_widgets import plot_tab_widgets

# get dir for this file and store as base_dir in filterbroker
fb.base_dir = os.path.dirname(os.path.abspath(__file__))

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
    home_dir = pyfda_lib.get_home_dir()
    logger.warning('save_dir "%s" specified in pyfda_rc.py doesn\'t exist, using "%s" instead.\n',
        rc.save_dir, home_dir) #fb.base_dir
    rc.save_dir = home_dir #fb.base_dir


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
#        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
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
        self.inputTabWidgets = input_tab_widgets.InputTabWidgets(self) # input widgets
        self.inputTabWidgets.setMaximumWidth(420) # comment out for splitter

        self.pltTabWidgets = plot_tab_widgets.PlotTabWidgets(self) # plot widgets

        # ============== UI Layout =====================================
        _widget = QtGui.QWidget() # this widget contains all subwidget groups

        layHMain = QtGui.QHBoxLayout(_widget) # horizontal layout of all groups

        # comment out following 3 lines for splitter design
        layHMain.addWidget(self.inputTabWidgets)
        layHMain.addWidget(self.pltTabWidgets)
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


        # make ScrollArea occupy the main area of QMainWidget 
        #   and make QMainWindow its parent !!!
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
        self.inputTabWidgets.sigSpecsChanged.connect(self.pltTabWidgets.update_view)
        #
        # sigFilterDesigned: signal indicating that filter has been DESIGNED,
        #  requiring full update of all plot widgets:
        self.inputTabWidgets.sigFilterDesigned.connect(self.pltTabWidgets.update_data)
        #
        # sigReadFilters: button has been pressed to rebuild filter tree:
        self.inputTabWidgets.inputFiles.sigReadFilters.connect(self.ftb.init_filters)

#        aboutAction.triggered.connect(self.aboutWindow) # open pop-up window
        # trigger the close event in response to sigQuit generated in another subwidget:
        self.inputTabWidgets.inputSpecs.sigQuit.connect(self.close)


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
    
    def closeEvent(self, event): 
        """
        reimplement QMainWindow.closeEvent() to prompt the user "Are you sure ..."
        """
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
            
#------------------------------------------------------------------------------       
    def clean_up(self):
        """
        Clean up everything - may only be called when exiting application!!

        See http://stackoverflow.com/questions/18732894/crash-on-close-and-quit
        """
        for i in self.__dict__:
            item = self.__dict__[i]
            clean_item(item)

#------------------------------------------------------------------------------
def clean_item(item):
    """
    Clean up memory by closing and deleting item recursively if possible
    """
    if isinstance(item, list) or isinstance(item, dict):
        for _ in range(len(item)):
            clean_item(item.pop())
    else:
        try:
            item.close()
        except(RuntimeError, AttributeError): # deleted or no close method
            pass
        try:
            item.deleteLater()
        except(RuntimeError, AttributeError): # deleted or no deleteLater method
            pass


#==============================================================================
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
     # instantiate QApplication object, passing command line arguments
    app = QtGui.QApplication(sys.argv)
    app.setObjectName("TopApp")
    
#    icon = os.path.join(fb.base_dir, 'images', 'icons', "pyfda_icon.svg")

    app.setWindowIcon(QtGui.QIcon(':/pyfda_icon.svg'))
    app.setStyleSheet(rc.css_rc) 

    mainw = pyFDA()
# http://stackoverflow.com/questions/18416201/core-dump-with-pyqt4
# http://stackoverflow.com/questions/11945183/what-are-good-practices-for-avoiding-crashes-hangs-in-pyqt
# http://stackoverflow.com/questions/5506781/pyqt4-application-on-windows-is-crashing-on-exit
# http://stackoverflow.com/questions/13827798/proper-way-to-cleanup-widgets-in-pyqt
# http://stackoverflow.com/questions/4528347/clear-all-widgets-in-a-layout-in-pyqt

    # Sets the active window to the active widget in response to a system event.
    app.setActiveWindow(mainw) 
    mainw.setWindowIcon(QtGui.QIcon(':/pyfda_icon.svg'))

    desktop = QtGui.QDesktopWidget() # test the available desktop resolution
    # make pyFDA instance the parent for clean termination upon exit 
    #  - otherwise the whole application will crash upon exit!
    desktop.setParent(mainw) 
    screen_h = desktop.availableGeometry().height()
    screen_w = desktop.availableGeometry().width()
    logger.info("Available screen resolution: %d x %d", screen_w, screen_h)

    fontsize = 10
    if screen_h < 800:
        delta = 50
    else:
        delta = 100
    desktop.deleteLater() # without this instruction, the main app looses focus ?!

    # set position + size of main window on desktop
    mainw.setGeometry(20, 20, screen_w - delta, screen_h - delta) # top L / top R, dx, dy
    # Give the keyboard input focus to this widget if this widget 
    # or one of its parents is the active window:
    mainw.setFocus() 
    mainw.show()

    #start the application's exec loop, return the exit code to the OS
    app.exec_() # sys.exit(app.exec_()) and app.exec_() have same behaviour

#------------------------------------------------------------------------------

if __name__ == '__main__':
    setdestroyonexit(False) # don't call the C++ destructor of wrapped instances
    main()
