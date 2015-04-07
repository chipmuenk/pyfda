# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 15:48:44 2014

@author: Christian Muenker
http://matplotlib.1069221.n5.nabble.com/Figure-with-pyQt-td19095.html
"""
from __future__ import print_function, division, unicode_literals

from PyQt4 import QtGui, QtCore

from PyQt4.QtGui import QSizePolicy
from PyQt4.QtCore import QSize


#import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backend_bases import cursors as mplCursors
from matplotlib.figure import Figure

from matplotlib import rcParams
rcParams['font.size'] = 12

import os
#import numpy as np
# import scipy.signal as sig

DEBUG = True

#------------------------------------------------------------------------------
#class MplWidgetBut(QtGui.QWidget):
#    """
#    Construct a subwidget with Matplotlib canvas, NavigationToolbar
#    and some buttons
#    """
#
#    def __init__(self, parent = None):
#        super(MplWidget, self).__init__() # initialize QWidget Base Class
#        # Create the mpl figure and subplot (5x4 inches, 100 dots-per-inch).
#        # Construct the canvas with the figure
#        #
#        self.dpi = 100
#        self.fig = Figure(dpi=self.dpi,facecolor = '#FFFFFF')
#        self.ax = self.fig.add_subplot(111)
#
#        self.pltCanv = FigureCanvas(self.fig)
#
#
#        self.pltCanv.setSizePolicy(QSizePolicy.Expanding,
#                                   QSizePolicy.Expanding)
#        self.pltCanv.updateGeometry()
#
#        # Create the navigation toolbar, tied to the canvas
#        #
#        self.mpl_toolbar = self.MyMplToolbar(self.pltCanv, self)
#
#        self.butDraw = QtGui.QPushButton("&Redraw")
#        self.butDraw.clicked.connect(self.redraw)
#
#        self.cboxGrid = QtGui.QCheckBox("Show &Grid")
#        self.cboxGrid.setChecked(True)
#        # Attention: passes unwanted clicked bool argument:
#        self.cboxGrid.clicked.connect(self.redraw)
#
#        #=============================================
#        # Slider for line width
#        #=============================================
#        lblLw = QtGui.QLabel('Line width:')
#        self.sldLw = QtGui.QSlider(QtCore.Qt.Horizontal)
#        self.sldLw.setRange(1, 10)
#        self.sldLw.setValue(5)
#        self.sldLw.setTracking(True)
#        self.sldLw.setTickPosition(QtGui.QSlider.NoTicks)
##        self.sldLw.valueChanged.connect(self.redraw)
#
#        #=============================================
#        # Widget layout with QHBox / QVBox
#        #=============================================
#
#        self.hbox1 = QtGui.QHBoxLayout()
#        for w in [self.butDraw, self.cboxGrid, lblLw, self.sldLw]:
#            self.hbox1.addWidget(w)
#            self.hbox1.setAlignment(w, QtCore.Qt.AlignVCenter)
#
#        self.layVMainMpl = QtGui.QVBoxLayout()
#        self.layVMainMpl.addWidget(self.mpl_toolbar)
#        self.layVMainMpl.addWidget(self.pltCanv)
#        self.layVMainMpl.addLayout(self.hbox1)
#        self.setLayout(self.layVMainMpl)
#
#    def redraw(self):
#        """
#        Redraw the figure with new properties (grid, linewidth)
#        """
#        self.ax.grid(self.cboxGrid.isChecked())
##        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value()/5.)
#        self.fig.tight_layout(pad = 0.5)
#        self.pltCanv.draw()
#        self.pltCanv.updateGeometry()


#------------------------------------------------------------------------------
class MplWidget(QtGui.QWidget):
    """
    Construct a subwidget with Matplotlib canvas and NavigationToolbar
    """

    def __init__(self, parent = None):
        super(MplWidget, self).__init__() # initialize QWidget Base Class
        # Create the mpl figure and subplot (white bg, 100 dots-per-inch).
        # Construct the canvas with the figure
        #
        self.plt_lim = [] # x,y plot limits
        self.dpi = 100
        self.fig = Figure(dpi=self.dpi,facecolor = '#FFFFFF')
#        self.mpl = self.fig.add_subplot(111) # self.fig.add_axes([.1,.1,.9,.9])#
#        self.mpl21 = self.fig.add_subplot(211)

        self.pltCanv = FigureCanvas(self.fig)
        self.pltCanv.setSizePolicy(QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        self.pltCanv.updateGeometry()

        # Create the custom navigation toolbar, tied to the canvas
        #
        # self.mpl_toolbar = NavigationToolbar(self.pltCanv, self) # original
        self.mplToolbar = MyMplToolbar(self.pltCanv, self)
        self.mplToolbar.grid = True

        #=============================================
        # Widget layout with QHBox / QVBox
        #=============================================

#        self.hbox = QtGui.QHBoxLayout()
#
#        for w in [self.mpl_toolbar, self.butDraw, self.cboxGrid]:
#            self.hbox.addWidget(w)
#            self.hbox.setAlignment(w, QtCore.Qt.AlignVCenter)
#        self.hbox.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        self.layVMainMpl = QtGui.QVBoxLayout()
#        self.layVMainMpl.addLayout(self.hbox)
        self.layVMainMpl.addWidget(self.mplToolbar)
        self.layVMainMpl.addWidget(self.pltCanv)


        self.setLayout(self.layVMainMpl)

    def redraw(self):
        """
        Redraw the figure with new properties (grid, linewidth)
        """
#        self.ax.grid(self.mplToolbar.grid)
        for ax in self.fig.axes:
            ax.grid(self.mplToolbar.grid) # collect axes objects and toggle grid
#        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value()/5.)
        self.fig.tight_layout(pad = 0.5)
        self.pltCanv.draw()
        self.pltCanv.updateGeometry()

    def pltFullView(self):
        """
        Full zoom
        """
        for ax in self.fig.axes:
            ax.autoscale()
        self.redraw()

#-----------------------------------------------------------------------------

#class MplCanvas(FigureCanvas):
#    """
#    Construct a canvas with a MatplotlibWidget, inheriting PyQt4.QtGui.QWidget
#    and matplotlib.backend_bases.FigureCanvasBase
#
#    Usage example:
#
#    class PlotHf(QtGui.QMainWindow):
#
#    def __init__(self):
#        super(PlotHf, self).__init__() # initialize QWidget base class
#
#        self.coeffs = ([1,1,1],[3,0,0]) # dummy definition
#        self.mplCanv = MplCanvas()
#        self.mplCanv.setFocus()
#        self.setCentralWidget(self.mplCanv)
#
#        mpl = self.mplCanv.ax
#        mpl.plot(...)
#        self.mplCanv.figure.tight_layout()
#        self.mplCanv.draw()
#
#    """
#    def __init__(self, parent=None):
#
#        self.dpi = 100
#        self.width = 5
#        self.height = 4
#        # create figure and Axes object
#        self.fig = Figure(figsize=(self.width, self.height), dpi=self.dpi)
#        self.ax = self.fig.add_subplot(111)
#
#        FigureCanvas.__init__(self, self.fig)
#        self.setParent(parent)
#
#
#        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding,
#                                   QSizePolicy.Expanding)
#        FigureCanvas.updateGeometry(self)
#
#    def sizeHint(self):
#        w, h = self.get_width_height()
#        return QSize(w, h)
#
#    def minimumSizeHint(self):
#        return QSize(10, 10)
#
#    def redrawPlt(self):
#        FigureCanvas.draw(self)
#        FigureCanvas.updateGeometry(self)

#------------------------------------------------------------------------------


class MyMplToolbar(NavigationToolbar):
    """
    Custom Matplotlib Navigationtoolbar, derived (sublassed) from
    Navigationtoolbar with the following changes:
    - new icon set
    - new functions and icons grid, full view
    - removed buttons for configuring subplots and editing curves
    - added an x,y location widget and icon


    derived from http://www.python-forum.de/viewtopic.php?f=24&t=26437
    """
# subclass NavigationToolbar, passing through arguments:
    #def __init__(self, canvas, parent, coordinates=True):
    def __init__(self, *args, **kwargs):
        NavigationToolbar.__init__(self, *args, **kwargs)


    def _init_toolbar(self):
#        self.basedir = os.path.join(rcParams[ 'datapath' ], 'images/icons')
        iconDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
           '..','images','icons', '')

# Icons taken from https://useiconic.com/open/

# TODO: clicking pan or zoom gives the following error:
#    self._actions['pan'].setChecked(self._active == 'PAN')
# KeyError: u'pan'
# dict _actions is set in
#    backend_qt5.NavigationToolbar2QT._init_toolbar, using self.toolitems,

# subclassed from matplotlib.backend_bases.NavigationToolbar2:

    # list of toolitems to add to the toolbar, format is:
    # (
    #   text, # the text of the button (often not visible to users)
    #   tooltip_text, # the tooltip shown on hover (where possible)
    #   image_file, # name of the image for the button (without the extension)
    #   name_of_method, # name of the method in NavigationToolbar2 to call
    # )
#    toolitems = (
#        ('Home', 'Reset original view', 'home', 'home'),
#        ('Back', 'Back to  previous view', 'back', 'back'),
#        ('Forward', 'Forward to next view', 'forward', 'forward'),
#        (None, None, None, None),
#        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
#        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
#        (None, None, None, None),
#        ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
#        ('Save', 'Save the figure', 'filesave', 'save_figure'),
#      )

#        print (self.toolitems)

        # HOME:
        a = self.addAction(QtGui.QIcon(iconDir + 'home.svg'), \
                           'Home', self.home)
        a.setToolTip('Reset original view')
        # BACK:
        a = self.addAction(QtGui.QIcon(iconDir + 'action-undo.svg'), \
                           'Back', self.back)
        a.setToolTip('Back to previous view')
        # FORWARD:
        a = self.addAction(QtGui.QIcon(iconDir + 'action-redo.svg'), \
                           'Forward', self.forward)
        a.setToolTip('Forward to next view')

        self.addSeparator() #---------------------------------------------

        # PAN:
        a = self.addAction(QtGui.QIcon(iconDir + 'move.svg'), \
                           'Pan', self.pan)
#                           'Pan', self.pan('self.move','self.pan')) # nearly works ...
        a.setToolTip('Pan axes with left mouse button, zoom with right')
        # ZOOM RECTANGLE:
        a = self.addAction(QtGui.QIcon(iconDir + 'magnifying-glass.svg'), \
                           'Zoom', self.zoom)
        a.setToolTip('Zoom in / out to rectangle with left / right mouse button.')
        # Full View:
        a = self.addAction(QtGui.QIcon(iconDir + 'fullscreen-enter.svg'), \
            'Full View', self.parent.pltFullView)
        a.setToolTip('Full view')

        self.addSeparator() #---------------------------------------------

        # SAVE:
        a = self.addAction(QtGui.QIcon(iconDir + 'file.svg'), \
                           'Save', self.save_figure)
        a.setToolTip('Save the figure')

        # GRID:
        self.addSeparator()
        a = self.addAction(QtGui.QIcon(iconDir + 'grid-four-up.svg'), \
                           'Grid', self.toggle_grid)
        a.setToolTip('Toggle Grid')
        # REDRAW:
        a = self.addAction(QtGui.QIcon(iconDir + 'brush.svg'), \
                           'Redraw', self.parent.redraw)
        a.setToolTip('Redraw Plot')

        self.buttons = {}

        # Add the x,y location widget at the right side of the toolbar
        # The stretch factor is 1 which means any resizing of the toolbar
        # will resize this label instead of the buttons.
        if self.coordinates:
            self.locLabel = QtGui.QLabel("", self)
            self.locLabel.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
            self.locLabel.setSizePolicy(
                QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,
                                  QtGui.QSizePolicy.Ignored))
            labelAction = self.addWidget(self.locLabel)
            labelAction.setVisible(True)

        # reference holder for subplots_adjust window
        self.adj_window = None

    def toggle_grid(self):
        self.grid = not self.grid
        self.parent.redraw()

#    def mouse_move(self, event):
#        if not event.inaxes or not self._active:
#            if self._lastCursor != mplCursors.POINTER:
#                self.set_cursor(mplCursors.POINTER)
#                self._lastCursor = mplCursors.POINTER
#        else:
#            if self._active == 'ZOOM':
#                if self._lastCursor != mplCursors.SELECT_REGION:
#                    self.set_cursor(mplCursors.SELECT_REGION)
#                    self._lastCursor = mplCursors.SELECT_REGION
#                if self._xypress:
#                    x, y = event.x, event.y
#                    lastx, lasty, _, _, _, _ = self._xypress[0]
#                    self.draw_rubberband(event, x, y, lastx, lasty)
#            elif (self._active == 'PAN' and
#                  self._lastCursor != mplCursors.MOVE):
#                self.set_cursor(mplCursors.MOVE)
#
#                self._lastCursor = mplCursors.MOVE
#
#        if event.inaxes and event.inaxes.get_navigate():
#
#            try: s = event.inaxes.format_coord(event.xdata, event.ydata)
#            except ValueError: pass
#            except OverflowError: pass
#            else:
#                if len(self.mode):
#                    self.set_message('%s : %s' % (self.mode, s))
#                else:
#                    self.set_message(s)
#        else: self.set_message(self.mode)