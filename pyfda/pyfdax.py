# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Mainwindow for the pyFDA app
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os

#from sip import setdestroyonexit
import logging
import logging.config
logger = logging.getLogger(__name__)

import pyfda.pyfda_dirs as dirs # initial import constructs file paths

import matplotlib
# specify matplotlib backend for systems that have both PyQt4 and PyQt5 installed
# to avoid 
# "RuntimeError: the PyQt4.QtCore and PyQt5.QtCore modules both wrap the QObject class"
try:
    import PyQt5
    matplotlib.use("Qt5Agg")
except ImportError:
    matplotlib.use("Qt4Agg")

from .compat import (QtCore, QMainWindow, QApplication, QFontMetrics, QSizePolicy,
                     QSplitter, QIcon, QMessageBox, QWidget, QHBoxLayout, QPlainTextEdit)

from pyfda.pyfda_lib import to_html

#========================= Setup the loggers ==================================
class DynFileHandler(logging.FileHandler):
    """
    subclass FileHandler with a customized handler for dynamic definition of
    the logging filepath and -name
    """
    def __init__(self, *args):
        filename, mode, encoding = args
        if filename == '':
            filename = dirs.LOG_FILE # use name including data and time
        if not os.path.isabs(filename): # path to logging file given in config_file?
            dirs.LOG_DIR_FILE = os.path.join(dirs.LOG_DIR, filename) # no, use default dir
        logging.FileHandler.__init__(self, dirs.LOG_DIR_FILE, mode, encoding)

class XStream(QtCore.QObject):
    """
    subclass for log messages on logger window
    Overrides stdout to print messages to textWidget 
    """
    _stdout = None
    messageWritten = QtCore.pyqtSignal(str) # pass str to slot

    def flush( self ):
        pass

    def fileno( self ):
        return -1

    def write(self, msg):
        if not self.signalsBlocked():
            msg = to_html(msg)

            self.messageWritten.emit(msg)

    @staticmethod
    def stdout():
        if not XStream._stdout:
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

class QEditHandler(logging.Handler):
    """
    subclass Handler to also log messages to textWidget on main display
    Overrides stdout to print messages to textWidget (XStream)
    """
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        if msg: 
            XStream.stdout().write('%s'%msg)

# "register" custom class DynFileHandler as an attribute for the logging module
# to use it inside the logging config file and pass file name / path and mode
# as parameters:
logging.DynFileHandler = DynFileHandler
logging.QEditHandler = QEditHandler
logging.config.fileConfig(dirs.USER_LOG_CONF_FILE)#, disable_existing_loggers=True)
#==============================================================================

from pyfda import pyfda_rc as rc
import pyfda.filterbroker as fb
from pyfda import qrc_resources # contains all icons
# edit pyfda.qrc, then
# create with   pyrcc4 pyfda.qrc -o qrc_resources.py -py3
#   or          pyrcc5 pyfda.qrc -o qrc_resources.py
# and manually replace "from from PyQt4/5 import QtCore"
#   by "from .compat import QtCore" in qrc_resources.py
from pyfda.filter_tree_builder import FilterTreeBuilder
from pyfda.input_widgets import input_tab_widgets
from pyfda.plot_widgets import plot_tab_widgets

#==============================================================================

class pyFDA(QMainWindow):
    """
    Create the main window consisting of a tabbed widget for entering filter
    specifications, poles / zeros etc. and another tabbed widget for plotting
    various filter characteristics

    QMainWindow is used here as it is a class that understands GUI elements like
    toolbar, statusbar, central widget, docking areas etc.
    """

    def __init__(self, parent=None):
        super(QMainWindow,self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # create clipboard instance that can be accessed from other modules
        fb.clipboard = QApplication.clipboard()

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

        # ============== UI Layout with H and V-Splitter =====================

        inputTabWidgets = input_tab_widgets.InputTabWidgets(self) # input widgets
        pltTabWidgets = plot_tab_widgets.PlotTabWidgets(self) # plot widgets
        loggerWin     = QPlainTextEdit(self)  # status window
        loggerWin.setReadOnly(True)        
        # only needed for logging window height measured in lines
        # mSize = QFontMetrics(loggerWin.font())
        # row4_height = mSize.lineSpacing() * 4

        # add logger window underneath plot Tab Widgets
        spltVPltLogger = QSplitter(QtCore.Qt.Vertical)
        spltVPltLogger.addWidget(pltTabWidgets)
        spltVPltLogger.addWidget(loggerWin)

        # create horizontal splitter that contains all subwidget groups
        spltHMain = QSplitter(QtCore.Qt.Horizontal)
        spltHMain.addWidget(inputTabWidgets)
        spltHMain.addWidget(spltVPltLogger)
        spltHMain.setStretchFactor(1,4) # relative initial sizes of subwidgets
        spltHMain.setContentsMargins(*rc.params['wdg_margins'])
        spltHMain.setFocus()
        # make spltHMain occupy the main area of QMainWindow and make QMainWindow its parent !!!
        self.setCentralWidget(spltHMain)
        spltVPltLoggerH = spltVPltLogger.size().height()
        spltVPltLogger.setSizes([spltVPltLoggerH*0.95, spltVPltLoggerH*0.05 - 8])

        self.setWindowTitle('pyFDA - Python Filter Design and Analysis')

        #=============== Menubar =======================================

#        aboutAction = QAction('&About', self)
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
        # sigViewChanged: signal indicating that filter VIEW has changed,
        # requiring partial update of some plot widgets:
        inputTabWidgets.sigViewChanged.connect(pltTabWidgets.update_view)
        #
        # sigSpecsChanged: signal indicating that filter SPECS have changed,
        # requiring partial update of some plot widgets:
        inputTabWidgets.sigSpecsChanged.connect(pltTabWidgets.update_view)

        #
        # sigFilterDesigned: signal indicating that filter has been DESIGNED,
        #  requiring full update of all plot widgets:
        inputTabWidgets.sigFilterDesigned.connect(pltTabWidgets.update_data)

        # open pop-up "about" window
        #aboutAction.triggered.connect(self.aboutWindow) 

        # trigger the close event in response to sigQuit generated in another subwidget:
        inputTabWidgets.filter_specs.sigQuit.connect(self.close)

        # when a message has been written, pass it via signal-slot mechanism and
        # print it to logger window
        XStream.stdout().messageWritten.connect(loggerWin.appendHtml)

#==============================================================================
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
        reimplement QMainWindow.closeEvent() to prompt the user
        """
        reply = QMessageBox.question(self, 'Message',
            "Quit pyFDA?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Clear clipboard before exit to avoid error message on older Qt versions
            # "QClipboard: Unable to receive an event from the clipboard manager 
            # in a reasonable time
            fb.clipboard.clear()
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

    if len(rc.qss_rc) > 20:
        app = QApplication(sys.argv)
        app.setStyleSheet(rc.qss_rc) # this is a proper style sheet
    else:
        qstyle = QApplication.setStyle(rc.qss_rc) # no, this is just a name for a system stylesheet
        if qstyle:
            logger.info('Using system style "{0}".'.format(rc.qss_rc))
            print(qstyle, "found")
        else:
            logger.warning('Style "{0}" not found, falling back to default style.'.format(rc.qss_rc))
            print("not found")
        app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(':/pyfda_icon.svg'))

    mainw = pyFDA()

    # Sets the active window to the active widget in response to a system event.
    app.setActiveWindow(mainw) 
    mainw.setWindowIcon(QIcon(':/pyfda_icon.svg'))

    screen_resolution = app.desktop().screenGeometry()
    screen_h, screen_w = screen_resolution.height(), screen_resolution.width()
    logger.info("Starting pyfda with screen resolution: %d x %d", screen_w, screen_h)

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
