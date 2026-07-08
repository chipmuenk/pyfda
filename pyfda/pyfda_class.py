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
import os
import logging
import logging.config
import sys

from pyfda import pyfda_rc
# edit pyfda.qrc, then
# create with  pyrcc5 pyfda.qrc -o qrc_resources.py
# and manually replace "from from PyQt5 import QtCore"
#   by "from pyfda.libs.compat import QtCore" in qrc_resources.py
from pyfda.config_file_parser import ConfigFileParser as CFP
from pyfda.libs.compat import (Qt, QtGui, QtCore, QMainWindow, QApplication, QSplitter,
                     QMessageBox, QPlainTextEdit, QMenu, pyqtSignal)
import pyfda.libs.pyfda_dirs as dirs # initial import constructs file paths
from pyfda.libs.pyfda_lib import to_html
from pyfda.tabbed_widget import TabbedWidget

logger = logging.getLogger(__name__)

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

    def flush( self ) -> None:
        """
        Flush the stream.

        Implemented to satisfy the file-like stream interface. This is a
        no-op because the XStream writes immediately via Qt signals.
        """

    def fileno( self ) -> int:
        """
        Return a file descriptor number.

        XStream does not correspond to a real OS file descriptor so it
        returns -1 to indicate an invalid descriptor (compatible with
        Python expectation for non-file-like streams).
        """
        return -1

    def write(self, msg: str) -> None:
        """
        Write a message to the stream.

        The message is converted to HTML for the logger widget and
        emitted via the `messageWritten` Qt signal unless signals are
        currently blocked.

        Parameters
        ----------
        msg : str
            The text message to write to the stream.
        """
        if not self.signalsBlocked():
            msg = to_html(msg, frmt='log')

            self.messageWritten.emit(msg)

    @staticmethod
    def stdout() -> 'XStream':
        """
        Return the singleton XStream instance used as `sys.stdout`.

        If no instance exists yet, create one and redirect `sys.stdout`
        to it so all standard output is routed through this stream.
        """
        if not XStream._stdout:
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

class QEditHandler(logging.Handler):
    """
    Subclass QEditHandler to also log messages to QPlainTextEdit in UI.
    Overrides stdout to print messages to textWidget (XStream)
    """
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        if msg:
            XStream.stdout().write(f'{msg}')

# "register" custom class DynFileHandler as an attribute for the logging module
# to use it inside the logging config file and pass file name / path and mode
# as parameters:
logging.DynFileHandler = DynFileHandler
logging.QEditHandler = QEditHandler
logging.config.fileConfig(dirs.USER_LOG_CONF_DIR_FILE)#, disable_existing_loggers=True)
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

    def __init__(self):
        super().__init__()
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # create clipboard instance that can be accessed from other modules
        dirs.clipboard = QApplication.clipboard()

        self._construct_ui()

    def _construct_ui(self) -> None:
        """
        Construct the main GUI, consisting of:
            - Tabbed input widgets (left side)
            - Tabbed plot widgets (right side)
            - Logger window (right side, below plot tab)
        """

        # ============== UI Layout with H and V-Splitter =====================
        # create tab widgets for input and plot widgets
        inputTabWidgets = TabbedWidget(wdg_classes_dict=CFP.INPUT_CLASSES_DICT, label='input',
                                       objectName='input_tab_widgets_inst', use_qscroll_area=True)
        pltTabWidgets = TabbedWidget(wdg_classes_dict=CFP.PLOT_CLASSES_DICT, label='plot',
                                     objectName='plot_tab_widgets_inst')

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
        spltHMain.setContentsMargins(*pyfda_rc.params['wdg_margins'])
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
        inputTabWidgets.sig_tx.connect(self.process_sig_rx)  # only for catching close event
        pltTabWidgets.sig_tx.connect(inputTabWidgets.sig_rx)
        # open pop-up "about" window
        #aboutAction.triggered.connect(self.aboutWindow)

        # when a message has been written, pass it via signal-slot mechanism and
        # print it to logger window
        XStream.stdout().messageWritten.connect(self.loggerWin.appendHtml)

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict=None) -> None:
        """
        Process signals coming from sig_rx:
            Trigger close event in response to 'close_event' emitted in another subwidget
        """
        if 'close_event' in dict_sig:
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

    def logger_win_context_menu(self, point: QtCore.QPoint) -> None:
        """ Show right mouse button context  menu """
        self.popMenu.exec_(self.loggerWin.mapToGlobal(point))

# =============================================================================
    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        reimplement QMainWindow.closeEvent() to prompt the user
        """
        # test for a handle to other pop-up windows and close them, otherwise
        # other pop-up windows can block the Messagebox (which has focus) and
        # pyfda cannot be terminated and freezes
        tran_freq_win_handle_vis = False
        fir_win_handle_vis = False
        if dirs.csv_options_handle is not None:
            dirs.csv_options_handle.close()
        if dirs.tran_freq_win_handle is not None and dirs.tran_freq_win_handle.isVisible():
            tran_freq_win_handle_vis = True
            dirs.tran_freq_win_handle.hide()
        if dirs.firwin_handle is not None and dirs.firwin_handle.isVisible():
            fir_win_handle_vis = True
            dirs.firwin_handle.hide()

        reply = QMessageBox.question(self, 'Message',
            "Quit pyFDA?", QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # Clear clipboard before exit to avoid error message on older Qt versions
            # "QClipboard: Unable to receive an event from the clipboard manager
            # in a reasonable time
            dirs.clipboard.clear()
            event.accept()
        else:  # restore hidden pop-up windows
            if fir_win_handle_vis:
                dirs.firwin_handle.show()
            if tran_freq_win_handle_vis:
                dirs.tran_freq_win_handle.show()
            event.ignore()
