# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 15:48:44 2014

@author: Christian Muenker
http://matplotlib.1069221.n5.nabble.com/Figure-with-pyQt-td19095.html
"""
from PyQt4 import QtGui, QtCore

from PyQt4.QtGui import QSizePolicy
from PyQt4.QtCore import QSize


import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backend_bases import cursors as mplCursors
from matplotlib.figure import Figure

from matplotlib import rcParams
rcParams['font.size'] = 12

import os
#import numpy as np
# import scipy.signal as sig

N_FFT = 2048 # FFT length for freqz
 
DEBUG = True

#------------------------------------------------------------------------------
class MplWidgetBut(QtGui.QWidget):
    """
    Construct a subwidget with Matplotlib canvas, NavigationToolbar
    and some buttons
    """

    def __init__(self, parent = None):
        super(MplWidget, self).__init__() # initialize QWidget Base Class
        # Create the mpl figure and subplot (5x4 inches, 100 dots-per-inch).
        # Construct the canvas with the figure
        #
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi,facecolor = '#FFFFFF')
        self.ax = self.fig.add_subplot(111)
        
        self.pltCanv = FigureCanvas(self.fig)
        
        
        #self.pltCanv.setSizePolicy(QSizePolicy.Expanding, 
        #                           QSizePolicy.Expanding)
        #self.pltCanv.updateGeometry()
                
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.pltCanv, self)
        
        self.butDraw = QtGui.QPushButton("&Redraw")
        self.butDraw.clicked.connect(self.redraw)

        self.cboxGrid = QtGui.QCheckBox("Show &Grid")
        self.cboxGrid.setChecked(True)  
        # Attention: passes unwanted clicked bool argument:
        self.cboxGrid.clicked.connect(self.redraw)

        #=============================================
        # Slider for line width
        #=============================================          
        lblLw = QtGui.QLabel('Line width:')
        self.sldLw = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.sldLw.setRange(1, 10)
        self.sldLw.setValue(5)
        self.sldLw.setTracking(True)
        self.sldLw.setTickPosition(QtGui.QSlider.NoTicks)
#        self.sldLw.valueChanged.connect(self.redraw)  

        #=============================================
        # Widget layout with QHBox / QVBox
        #=============================================
          
        self.hbox1 = QtGui.QHBoxLayout()            
        for w in [self.butDraw, self.cboxGrid, lblLw, self.sldLw]:
            self.hbox1.addWidget(w)
            self.hbox1.setAlignment(w, QtCore.Qt.AlignVCenter)
            
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.mpl_toolbar)
        self.vbox.addWidget(self.pltCanv)
        self.vbox.addLayout(self.hbox1)         
        self.setLayout(self.vbox)
        
    def redraw(self):
        """
        Redraw the figure with new properties (grid, linewidth)
        """
        self.ax.grid(self.cboxGrid.isChecked())
#        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value()/5.)
        self.fig.tight_layout(pad = 0.5)
        self.pltCanv.draw()
        self.pltCanv.updateGeometry()
      

#------------------------------------------------------------------------------
class MplWidget(QtGui.QWidget):
    """
    Construct a subwidget with Matplotlib canvas and NavigationToolbar
    """

    def __init__(self, parent = None):
        super(MplWidget, self).__init__() # initialize QWidget Base Class
        # Create the mpl figure and subplot (5x4 inches, 100 dots-per-inch).
        # Construct the canvas with the figure
        #
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi,facecolor = '#FFFFFF')
        self.ax = self.fig.add_subplot(111)
        
        self.pltCanv = FigureCanvas(self.fig)
        
        
        #self.pltCanv.setSizePolicy(QSizePolicy.Expanding, 
        #                           QSizePolicy.Expanding)
        #self.pltCanv.updateGeometry()
                
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.pltCanv, self)
        
        self.butDraw = QtGui.QPushButton("&Redraw")
        self.butDraw.clicked.connect(self.redraw)

        self.cboxGrid = QtGui.QCheckBox("&Grid")
        self.cboxGrid.setChecked(True)  
        # Attention: passes unwanted clicked bool argument:
        self.cboxGrid.clicked.connect(self.redraw)

        #=============================================
        # Widget layout with QHBox / QVBox
        #=============================================
          
        self.hbox1 = QtGui.QHBoxLayout()
            
        for w in [self.mpl_toolbar, self.butDraw, self.cboxGrid]:
            self.hbox1.addWidget(w)
            self.hbox1.setAlignment(w, QtCore.Qt.AlignVCenter)
            
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addLayout(self.hbox1)  
        self.vbox.addWidget(self.pltCanv)
       
        self.setLayout(self.vbox)
        
    def redraw(self):
        """
        Redraw the figure with new properties (grid, linewidth)
        """
        self.ax.grid(self.cboxGrid.isChecked())
#        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value()/5.)
        self.fig.tight_layout(pad = 0.5)
        self.pltCanv.draw()
        self.pltCanv.updateGeometry()

#-----------------------------------------------------------------------------        

class MplCanvas(FigureCanvas):
    """
    Construct a canvas with a MatplotlibWidget, inheriting PyQt4.QtGui.QWidget
    and matplotlib.backend_bases.FigureCanvasBase
    
    Usage example: 
    
    class PlotHf(QtGui.QMainWindow):

    def __init__(self):        
        super(PlotHf, self).__init__() # initialize QWidget base class
        
        self.coeffs = ([1,1,1],[3,0,0]) # dummy definition
        self.mplCanv = MplCanvas() 
        self.mplCanv.setFocus()
        self.setCentralWidget(self.mplCanv)

        mpl = self.mplCanv.ax
        mpl.plot(...)
        self.mplCanv.figure.tight_layout()  
        self.mplCanv.draw()

    """
    def __init__(self, parent=None):
 
        self.dpi = 100
        self.width = 5
        self.height = 4
        # create figure and Axes object
        self.fig = Figure(figsize=(self.width, self.height), dpi=self.dpi)
        self.ax = self.fig.add_subplot(111)
        
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)


        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, 
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def sizeHint(self):
        w, h = self.get_width_height()
        return QSize(w, h)

    def minimumSizeHint(self):
        return QSize(10, 10) 
        
    def redrawPlt(self):
        FigureCanvas.draw(self)
        FigureCanvas.updateGeometry(self)
        
#------------------------------------------------------------------------------

     
    class MyMplToolbar(NavigationToolbar):
        """
        Custom Matplotlib Navigationtoolbar, derived (sublassed) from 
        Navigationtoolbar with the following changes:
        - new icons
        - removed buttons for configuring subplots and editing curves
        - added an x,y location widget and icon
        
        http://www.python-forum.de/viewtopic.php?f=24&t=26437
        """
        def __init__(self, *args, **kwargs):
            NavigationToolbar.__init__(*args, **kwargs)
     
     
        def _init_toolbar(self):
            self.basedir = os.path.join(mpl.rcParams[ 'datapath' ], 'images')
     
            a = self.addAction(QtGui.QIcon(':/images/icons/home.svg'), \
                               'Home', self.home)
            a.setToolTip('Reset original view')
            a = self.addAction(QtGui.QIcon(':/images/icons/previous.svg'), \
                               'Back', self.back)
            a.setToolTip('Back to previous view')
            a = self.addAction(QtGui.QIcon(':/images/icons/next.svg'), \
                               'Forward', self.forward)
            a.setToolTip('Forward to next view')
            self.addSeparator()
            a = self.addAction(QtGui.QIcon(':/images/icons/move.png'), \
                               'Pan', self.pan)
            a.setToolTip('Pan axes with left mouse, zoom with right')
            a = self.addAction(QtGui.QIcon(':/images/icons/zoom.png'), \
                               'Zoom', self.zoom)
            a.setToolTip('Zoom to rectangle')
            self.addSeparator()
            a = self.addAction(QtGui.QIcon(':/images/icons/saveImage.svg'), \
                               'Save', self.save_figure)
            a.setToolTip('Save the figure')
     
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
           
        def mouse_move(self, event):
            if not event.inaxes or not self._active:
                if self._lastCursor != mplCursors.POINTER:
                    self.set_cursor(mplCursors.POINTER)
                    self._lastCursor = mplCursors.POINTER
            else:
                if self._active == 'ZOOM':
                    if self._lastCursor != mplCursors.SELECT_REGION:
                        self.set_cursor(mplCursors.SELECT_REGION)
                        self._lastCursor = mplCursors.SELECT_REGION
                    if self._xypress:
                        x, y = event.x, event.y
                        lastx, lasty, _, _, _, _ = self._xypress[0]
                        self.draw_rubberband(event, x, y, lastx, lasty)
                elif (self._active == 'PAN' and
                      self._lastCursor != mplCursors.MOVE):
                    self.set_cursor(mplCursors.MOVE)
     
                    self._lastCursor = mplCursors.MOVE
     
            if event.inaxes and event.inaxes.get_navigate():
     
                try: s = event.inaxes.format_coord(event.xdata, event.ydata)
                except ValueError: pass
                except OverflowError: pass
                else:
                    if len(self.mode):
                        self.set_message('%s : %s' % (self.mode, s))
                    else:
                        self.set_message(s)
            else: self.set_message(self.mode)