# -*- coding: utf-8 -*-
"""
Mainwindow  for the pyFDA app, initializes UI

Authors: Julia Beike, Christian Muenker and Michael Winkler
"""
from __future__ import print_function, division, unicode_literals, absolute_import
SPLITTER = True
SCROLL = False
import sys, os
#from sip import setdestroyonexit
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
#from pyfda.input_widgets import input_tab_widgets_test as input_tab_widgets

from pyfda.plot_widgets import plot_tab_widgets
#from pyfda.plot_widgets import plot_tab_widgets_test as plot_tab_widgets
#from pyfda.plot_widgets import plot_tab_widgets_empty as plot_tab_widgets


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
        rc.save_dir, home_dir)
    rc.save_dir = home_dir


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

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        
        # initialize the FilterTreeBuilder class with the filter directory and
        # the filter file as parameters:         
        # read directory with filterDesigns and construct filter tree from it
        self.ftb = FilterTreeBuilder('filter_design', 'filter_list.txt', comment_char='#')                                  
        self._construct_UI()

    def _construct_UI(self):
        """
        Construct the main GUI, consisting of:
        - Subwindow for parameter selection [-> ChooseParams.ChooseParams()]
        - Filter Design button [-> self.startDesignFilt()]
        - Plot Window [-> plotAll.plotAll()]
        """

        # ============== UI Layout =====================================
        self.main_widget = QtGui.QWidget(self) # this widget contains all subwidget groups

        layHMain = QtGui.QHBoxLayout(self.main_widget) # horizontal layout of all groups

        # Instantiate subwidget groups
        self.inputTabWidgets = input_tab_widgets.InputTabWidgets(self) # input widgets
        self.pltTabWidgets = plot_tab_widgets.PlotTabWidgets(self) # plot widgets
# Test        self.pltTabWidgets = plot_tab_widgets.MyStaticMplCanvas(self.main_widget, width=5, height=4, dpi=100)

        if SPLITTER: # use splitter design (variable ratio for input / plot subwidget sizes)
            layVInput = QtGui.QVBoxLayout()
            layVInput.addWidget(self.inputTabWidgets)
            layVPlt = QtGui.QVBoxLayout()
            layVPlt.addWidget(self.pltTabWidgets)
    
            frmInput = QtGui.QFrame()
            frmInput.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
            frmInput.setLayout(layVInput)
            frmInput.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                     QtGui.QSizePolicy.Minimum)
    
            frmPlt = QtGui.QFrame()
            frmPlt.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
            frmPlt.setLayout(layVPlt)
            frmPlt.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                     QtGui.QSizePolicy.Minimum)
    
            splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
            splitter.addWidget(frmInput)
            splitter.addWidget(frmPlt)
            splitter.setStretchFactor(1,4) # factors for the initial sizes of subwidgets
#            splitter.setSizes([200,600])

            layHMain.addWidget(splitter)

        else: # no splitter design, only use layHMain layout
            self.inputTabWidgets.setMaximumWidth(420) # comment out for splitter
            layHMain.addWidget(self.inputTabWidgets)
            layHMain.addWidget(self.pltTabWidgets)
            layHMain.setContentsMargins(0, 0, 0, 0)#(left, top, right, bottom)

        self.setWindowTitle('pyFDA - Python Filter Design and Analysis')

        if SCROLL:
            # Create scroll area and "monitor" _widget whether scrollbars are needed
            scrollArea = QtGui.QScrollArea()
            scrollArea.setWidget(self.main_widget) # make main widget "scrollable"
    
            #============= Set behaviour of scroll area ======================
            # scroll bars appear when the scroll area shrinks below this size:
            scrollArea.setMinimumSize(QtCore.QSize(800, 500))
    #        scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded) #default
    #        scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded) # default
            scrollArea.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                     QtGui.QSizePolicy.MinimumExpanding)
    
            # Size of monitored widget is allowed to grow:
            scrollArea.setWidgetResizable(True)
    
        self.main_widget.setFocus()
        # make main_widget occupy the main area of QMainWidget 
        #   and make QMainWindow its parent !!!
        self.setCentralWidget(self.main_widget)

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
        self.inputTabWidgets.file_io.sigReadFilters.connect(self.ftb.init_filters)

        # open pop-up "about" window
        #aboutAction.triggered.connect(self.aboutWindow) 

        # trigger the close event in response to sigQuit generated in another subwidget:
        self.inputTabWidgets.filter_specs.sigQuit.connect(self.close)


        logger.debug("Main routine initialized!")

#==============================================================================
# #------------------------------------------------------------------------------
#     def aboutWindow(self):
#         """
#         Display an "About" window
#         """
#         QtGui.QMessageBox.about(self, "About pyFDA",
#                                 ("(c) 2013 - 15 Christian Münker\n\n"
#         "A graphical tool for designing, analyzing and synthesizing digital filters")
#         )
# 
# #------------------------------------------------------------------------------
#     def statusMessage(self, message):
#         """
#         Display a message in the statusbar.
#         """
#         self.statusBar().showMessage(message)
# 
# #------------------------------------------------------------------------------       
#==============================================================================
    
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
    app.setWindowIcon(QtGui.QIcon(':/pyfda_icon.svg'))
    app.setStyleSheet(rc.css_rc) 

    mainw = pyFDA()

    # Sets the active window to the active widget in response to a system event.
    app.setActiveWindow(mainw) 
    mainw.setWindowIcon(QtGui.QIcon(':/pyfda_icon.svg'))

    screen_resolution = app.desktop().screenGeometry()
    screen_h, screen_w = screen_resolution.height(), screen_resolution.width()
    logger.info("Available screen resolution: %d x %d", screen_w, screen_h)

    fontsize = 10
    if screen_h < 800:
        delta = 50
    else:
        delta = 100
    # set position + size of main window on desktop
    mainw.setGeometry(20, 20, screen_w - delta, screen_h - delta) # top L / top R, dx, dy
    # Give the keyboard input focus to this widget if this widget 
    # or one of its parents is the active window:
#    mainw.setFocus() 
    mainw.show()

    #start the application's exec loop, return the exit code to the OS
    app.exec_() # sys.exit(app.exec_()) and app.exec_() have same behaviour

#------------------------------------------------------------------------------

if __name__ == '__main__':
#    setdestroyonexit(False) # don't call the C++ destructor of wrapped instances
    main()
