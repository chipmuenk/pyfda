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
import sys, os

import logging
import logging.config
logger = logging.getLogger(__name__)

import pyfda.libs.pyfda_dirs as dirs # initial import constructs file paths

import matplotlib
# specify matplotlib backend for systems that have both PyQt4 and PyQt5 installed
# to avoid
# "RuntimeError: the PyQt4.QtCore and PyQt5.QtCore modules both wrap the QObject class"
matplotlib.use("Qt5Agg")
# turn off matplotlib debug messages by elevating the level to "Warning"
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

from pyfda.libs.compat import (Qt, QtCore, QMainWindow, QApplication, QSplitter, QIcon,
                     QMessageBox, QPlainTextEdit, QMenu, pyqtSignal)

from pyfda.libs.pyfda_lib import to_html
from pyfda.libs.pyfda_lib import ANSIcolors as ACol

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

# =============================================================================
#         logging.addLevelName(logging.WARNING, ACol.YELLOW2 +
#                              logging.getLevelName(logging.WARNING) + ACol.CEND)
#         logging.addLevelName(logging.ERROR, ACol.RED2 +
#                              logging.getLevelName(logging.ERROR) + ACol.CEND)
#         logging.addLevelName(logging.CRITICAL, ACol.RED2 + ";" + ACol.CSELECTED +
#                              logging.getLevelName(logging.CRITICAL) + ACol.CEND)
# https://stackoverflow.com/questions/24469662/how-to-redirect-logger-output-into-pyqt-text-widget
# coloured logger: https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
# =============================================================================
class XStream(QtCore.QObject):
    """
    subclass for log messages on logger window
    Overrides stdout to print messages to textWidget
    """
    _stdout = None
    messageWritten = pyqtSignal(str) # pass str to slot

    def flush( self ):
        pass

    def fileno( self ):
        return -1

    def write(self, msg):
        if not self.signalsBlocked():
            msg = to_html(msg,frmt='log')

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
logging.config.fileConfig(dirs.USER_LOG_CONF_DIR_FILE)#, disable_existing_loggers=True)
#==============================================================================

from pyfda import pyfda_rc as rc
import pyfda.filterbroker as fb
from pyfda import qrc_resources # contains all icons
# edit pyfda.qrc, then
# create with   pyrcc4 pyfda.qrc -o qrc_resources.py -py3
#   or          pyrcc5 pyfda.qrc -o qrc_resources.py
# and manually replace "from from PyQt4/5 import QtCore"
#   by "from pyfda.libs.compat import QtCore" in qrc_resources.py
from pyfda.libs.tree_builder import Tree_Builder
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
    sig_rx = pyqtSignal(object) # incoming
    # sig_tx = pyqtSignal(object) # outgoing

    def __init__(self, parent=None):
        super(QMainWindow,self).__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # create clipboard instance that can be accessed from other modules
        fb.clipboard = QApplication.clipboard()

        # initialize the FilterTreeBuilder class:
        # read config file and construct filter tree from it
        _ = Tree_Builder() # TODO_ couldn't this be a function?
        self._construct_UI()

    def _construct_UI(self):
        """
        Construct the main GUI, consisting of:
            - Tabbed input widgets (left side)
            - Tabbed plot widgets (right side)
            - Logger window (right side, below plot tab)
        """

        # ============== UI Layout with H and V-Splitter =====================

        inputTabWidgets = input_tab_widgets.InputTabWidgets(self)  # input widgets
        pltTabWidgets = plot_tab_widgets.PlotTabWidgets(self)  # plot widgets
        self.loggerWin = QPlainTextEdit(self)  # logger window
        self.loggerWin.setReadOnly(True)
        # set custom right-button context menu policy
        self.loggerWin.setContextMenuPolicy(Qt.CustomContextMenu)
        self.loggerWin.customContextMenuRequested.connect(self.logger_win_context_menu)
        # create context menu and define actions and shortcuts
        self.popMenu = QMenu(self)
        self.popMenu.addAction('Select &All', self.loggerWin.selectAll, "Ctrl+A")
        self.popMenu.addAction('&Copy Selected', self.loggerWin.copy)
        self.popMenu.addSeparator()
        self.popMenu.addAction('Clear &Window', self.loggerWin.clear)

# =============================================================================

        # add logger window underneath plot Tab Widgets
        spltVPltLogger = QSplitter(QtCore.Qt.Vertical)
        spltVPltLogger.addWidget(pltTabWidgets)
        spltVPltLogger.addWidget(self.loggerWin)

        # create horizontal splitter that contains all subwidget groups
        spltHMain = QSplitter(QtCore.Qt.Horizontal)
        spltHMain.addWidget(inputTabWidgets)
        spltHMain.addWidget(spltVPltLogger)
        spltHMain.setStretchFactor(1, 4)  # relative initial sizes of subwidgets
        spltHMain.setContentsMargins(*rc.params['wdg_margins'])
        spltHMain.setFocus()
        # make spltHMain occupy the main area of QMainWindow and make QMainWindow its parent !!!
        self.setCentralWidget(spltHMain)
        spltVPltLoggerH = spltVPltLogger.size().height()
        spltVPltLogger.setSizes([int(spltVPltLoggerH*0.95), int(spltVPltLoggerH*0.05 - 8)])

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
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # Here, signals about spec and design changes from lower hierarchies
        # are distributed. At the moment, only changes in the input widgets are
        # routed to the plot widgets:
        inputTabWidgets.sig_tx.connect(pltTabWidgets.sig_rx)
        inputTabWidgets.sig_tx.connect(self.process_sig_rx)
        pltTabWidgets.sig_tx.connect(inputTabWidgets.sig_rx)
        # open pop-up "about" window
        #aboutAction.triggered.connect(self.aboutWindow)

        # trigger the close event in response to sigQuit generated in another subwidget:
        # inputTabWidgets.input_filter_specs.sigQuit.connect(self.close)

        # when a message has been written, pass it via signal-slot mechanism and
        # print it to logger window
        XStream.stdout().messageWritten.connect(self.loggerWin.appendHtml)

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx:
        - trigger close event in response to 'quit_program' emitted in another subwidget:

        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if 'quit_program' in dict_sig:
            self.close()

#==============================================================================
#     def statusMessage(self, message):
#         """
#         Display a message in the statusbar.
#         """
#         self.statusBar().showMessage(message)
#
#
#==============================================================================

    def logger_win_context_menu(self, point):
        """ Show right mouse button context  menu """
        self.popMenu.exec_(self.loggerWin.mapToGlobal(point))

# =============================================================================
    def closeEvent(self, event):
        """
        reimplement QMainWindow.closeEvent() to prompt the user
        """
        # test for a handle to another pop-up window (CSV options) and close it,
        # otherwise pyfda cannot be terminated and freezes
        if not dirs.csv_options_handle is None:
            dirs.csv_options_handle.close()

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
        style = "Using 'pyfda' style sheet."
    else:
        qstyle = QApplication.setStyle(rc.qss_rc) # no, this is just a name for a system stylesheet
        app = QApplication(sys.argv)
        if qstyle:
            style = 'Using system style "{0}".'.format(rc.qss_rc)
        else:
            style = 'Style "{0}" not found, falling back to default style.'.format(rc.qss_rc)

    mainw = pyFDA()
    logger.info("Logging to {0}".format(dirs.LOG_DIR_FILE))
    logger.info(style)

    if dirs.OS.lower() == "windows":
        # Windows taskbar is not for "Application Windows" but for "Application
        # User Models", grouping several instances of an application under one
        # common taskbar icon. Python apps are sometimes grouped under the icon
        # for Pythonw.exe, sometimes the icon is just blank. The following
        # instructions tell Windows that pythonw is merely hosting other applications.
        import ctypes
        myappid = u'chipmuenk.pyfda.v0.4'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # set taskbar icon
    app.setWindowIcon(QIcon(':/pyfda_icon.svg'))

    # Sets the active window to the active widget in response to a system event
    app.setActiveWindow(mainw)
    # Set default icon for window
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
    main()
