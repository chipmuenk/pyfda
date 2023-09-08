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
import sys

import logging
import logging.config
logger = logging.getLogger(__name__)

import pyfda.libs.pyfda_dirs as dirs # initial import constructs file paths
import pyfda.pyfda_rc as rc

import matplotlib
# specify matplotlib backend for systems that have both PyQt4 and PyQt5 installed
# to avoid
# "RuntimeError: the PyQt4.QtCore and PyQt5.QtCore modules both wrap the QObject class"
matplotlib.use("Qt5Agg")
# turn off matplotlib debug messages by elevating the level to "Warning"
mpl_logger = logging.getLogger('matplotlib')
mpl_logger.setLevel(logging.WARNING)

from pyfda.libs.compat import (Qt, QtCore, QtGui, QMainWindow, QApplication, QSplitter, QIcon,
                     QMessageBox, QPlainTextEdit, QMenu, pyqtSignal, QtWidgets, QFont, QFontMetrics)

# from pyfda.libs.pyfda_lib import ANSIcolors as ACol
import numpy as np
from pyfda.pyfda_class import pyFDA

def main():
    """
    entry point for the pyfda application
    see http://pyqt.sourceforge.net/Docs/PyQt4/qapplication.html :

    "For any GUI application using Qt, there is precisely *one* QApplication object,
    no matter whether the application has 0, 1, 2 or more windows at any given time.
    ...
    Since the QApplication object does so much initialization, it must be created
    *before* any other objects related to the user interface are created."

    Environment variables controlling Qt behaviour need to be set even before initializing
    the QApplication object

    Scaling
    -------
    - DPI: The resolution number of dots per inch in a digital print
    - PPI: Pixel density of an electronic image device (e.g. computer monitor)
    - Point: 1/72 Inch = 0.3582 mm, physical measure in typography
    - em: Equal to font height. For e.g. a 12 pt font, 1 em = 12 pt

    - Physical DPI: The PPI that a physical screen actually provides.
    - Logical DPI: The PPI that software claims a screen provides. This can be thought
        of as the PPI provided by a virtual screen created by the operating system.
        Font sizes are specified in logical DPI
    - Screen scaling: High-Resolution screens have a very high physical DPI, resulting
        in very small characters. Screen scaling by e.g. 125 ... 200% increases the
        logical DPI and hence the character size by the same amount.

    MacOS
    ~~~~~
        Early displays had 72 PPI, equaling 72 Pt/Inch, i.e. 1 Pixel = 1 Point. Print-out
        size was equal to screen size.

    Windows
    ~~~~~~~
      A 72-point font is defined to be one logical inch = 96 pixels tall.
    12 pt = 12/72 = 1/6 logical inch = 96/6 pixels = 16 pixels @ 96 dpi



    # Enable automatic scaling based on the monitor's pixel density. This doesn't change the
    # size of point based fonts!
    # os.environ["QT_ENABLE_HIGHDPI_SCALING"]   = "1"
    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"  # replaced by QT_ENABLE_HIGHDPI_SCALING
    # Define global scale factor for the whole application, including point-sized fonts:
    # os.environ["QT_SCALE_FACTOR"]             = "1"
    """
    # Enable High DPI display with PyQt5
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        Qt.AA_EnableHighDpiScaling = True
    else:
        logger.warning("No Qt attribute 'AA_EnableHighDpiScaling'.")
    # Instantiate QApplication object, passing command line arguments
    if len(rc.qss_rc) > 20:
        app = QApplication(sys.argv)
        app.setStyleSheet(rc.qss_rc) # this is a proper style sheet
        style = "'pyfda' style sheet"
    else:
        qstyle = QApplication.setStyle(rc.qss_rc) # this is just a name for a system stylesheet
        app = QApplication(sys.argv)
        if qstyle:
            style = f"system style sheet '{rc.qss_rc}'"
        else:
            style = f"default style sheet ('{rc.qss_rc}' not found)"

    if dirs.OS.lower() == "darwin":  # Mac OS
        ref_dpi = 72
    else:
        ref_dpi = 96

    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    else:
        logger.warning("Qt attribute 'AA_UseHighDpiPixmaps' not available.")

    ldpi = app.primaryScreen().logicalDotsPerInch()
#    ldpix = app.primaryScreen().logicalDotsPerInchX()
#    ldpiy = app.primaryScreen().logicalDotsPerInchY()
    pdpi = app.primaryScreen().physicalDotsPerInch()
    pdpix = app.primaryScreen().physicalDotsPerInchX()
    pdpiy = app.primaryScreen().physicalDotsPerInchY()
    # scr_size = app.primaryScreen().size()  # pixel resolution, type QSize()
    screen_resolution = app.desktop().screenGeometry()
    avail_geometry = app.desktop().availableGeometry()
    # avail_size = app.desktop().availableSize()
    pixel_ratio = app.desktop().devicePixelRatio()
    height, width = screen_resolution.height(), screen_resolution.width()
    scaling = ldpi / ref_dpi

    # font = QFont()
    # font.setPointSize(yourPointSize)
    # fm = QFontMetrics(font)
    # try to find a good value for matplotlib font size depending on screen resolution

    fontsize = round(9.5 * np.sqrt(pdpiy / ref_dpi) * scaling)
    # fontsize = round(font.pointSizeF() * 1.5 * ldpi / 96)

    rc.mpl_rc['font.size'] = fontsize
    rc.params['screen'] = {'ref_dpi': ref_dpi, 'scaling': scaling,
                           'height': height, 'width': width}

    mainw = pyFDA()
    logger.info("Logging to {0}".format(dirs.LOG_DIR_FILE))
    logger.info(f"Starting pyfda with screen resolution {width} x {height}, "
                f"avail: {avail_geometry.width()}x{avail_geometry.height()}")
    logger.info(f"with {style} and matplotlib fontsize {fontsize}.")
    logger.info(f"lDPI = {ldpi:.2f}, pDPI = {pdpi:.2f} ({pdpix:.2f} x {pdpiy:.2f}), pix.ratio = {pixel_ratio}")

    # Available signals:
    # - logicalDotsPerInchChanged(qreal dpi)
    # - physicalDotsPerInchChanged(qreal dpi)
    # - geometryChanged(const QRect &geometry)
    # - availableGeometryChanged(const QRect &geometry)

    # logger.info(f"size = {font.pointSize()}, {font.pointSizeF()}, {font.pixelSize()},  height = {fm.height()}")
    if dirs.OS.lower() == "windows":
        # Windows taskbar is not for "Application Windows" but for "Application
        # User Models", grouping several instances of an application under one
        # common taskbar icon. Python apps are sometimes grouped under the icon
        # for Pythonw.exe, sometimes the icon is just blank. The following
        # instructions tell Windows that pythonw is merely hosting other applications.
        import ctypes
        myappid = u'chipmuenk.pyfda.v0.8'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # set taskbar icon
    app.setWindowIcon(QIcon(':/pyfda_icon.svg'))

    # Sets the active window to the active widget in response to a system event
    app.setActiveWindow(mainw)
    # Set default icon for window
    mainw.setWindowIcon(QIcon(':/pyfda_icon.svg'))
    # set main window on desktop to full size
    # mainw.setGeometry(0, 0, width, height) # top L / top R, dx, dy
    mainw.setGeometry(app.desktop().availableGeometry())
    # Give the keyboard input focus to this widget if this widget
    # or one of its parents is the active window:
#    mainw.setFocus()
    mainw.show()

    #start the application's exec loop, return the exit code to the OS
    app.exec_() # sys.exit(app.exec_()) and app.exec_() have same behaviour

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
