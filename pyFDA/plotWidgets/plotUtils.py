# -*- coding: utf-8 -*-
"""
Created on Wed Nov 26 15:48:44 2014

@author: Christian Muenker
http://matplotlib.1069221.n5.nabble.com/Figure-with-pyQt-td19095.html
"""
from PyQt4 import QtGui, QtCore

from PyQt4.QtGui import QSizePolicy
from PyQt4.QtCore import QSize


#import matplotlib as plt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from matplotlib import rcParams
rcParams['font.size'] = 12

import numpy as np
import scipy.signal as sig

N_FFT = 2048 # FFT length for freqz
 
DEBUG = True      


class MplWidget(QtGui.QWidget):
    """
    Construct a subwidget with matplotlib figure and some widgets
    """

    def __init__(self):
        super(MplWidget, self).__init__() # initialize QWidget Base Class
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.pltFig = Figure((5.0, 4.0), dpi=self.dpi)
        self.pltAxes = self.pltFig.add_subplot(111)
  
        
        self.pltCanv = FigureCanvas(self.pltFig)
#        self.pltCanv.setParent(self)
        
        
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.pltCanv, self)
        
        self.butDraw = QtGui.QPushButton("&Redraw")
#        self.butDraw.clicked.connect(lambda: self.update(self.coeffs))

        self.cboxGrid = QtGui.QCheckBox("Show &Grid")
        self.cboxGrid.setChecked(True)  
        # Attention: passes unwanted clicked bool argument:
#        self.cboxGrid.clicked.connect(self.redraw)

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
        # Widget layout with box sizers
        #=============================================
          
        self.hbox1 = QtGui.QHBoxLayout()            
        for w in [self.butDraw, self.cboxGrid, lblLw, self.sldLw]:
            self.hbox1.addWidget(w)
            self.hbox1.setAlignment(w, QtCore.Qt.AlignVCenter)
            
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.mpl_toolbar)
        self.vbox.addWidget(self.pltCanv)
        self.vbox.addLayout(self.hbox1)         
#        self.setLayout(vbox)
        
        
#    def redraw(self):
#        """
#        Redraw the figure with new properties (grid, linewidth)
#        """
#        self.pltAxes.grid(self.cboxGrid.isChecked())
#        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value()/5.)
#        self.pltFig.tight_layout()
#        self.pltCanv.draw()
        
class MplWidget2(QtGui.QWidget):
    """
    Construct a subwidget with matplotlib figure and some widgets
    """

    def __init__(self):
        super(MplWidget, self).__init__() # initialize QWidget Base Class
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
#        self.dpi = 100
#        self.pltFig = Figure((5.0, 4.0), dpi=self.dpi)
#        self.pltAxes = self.pltFig.add_subplot(111)
  
        
        self.pltCanv = MplWidget(self)#FigureCanvas(self.pltFig)
#        self.pltCanv.setParent(self)
        
        
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.pltCanv, self)
        
        self.butDraw = QtGui.QPushButton("&Redraw")
#        self.butDraw.clicked.connect(lambda: self.update(self.coeffs))

        self.cboxGrid = QtGui.QCheckBox("Show &Grid")
        self.cboxGrid.setChecked(True)  
        # Attention: passes unwanted clicked bool argument:
#        self.cboxGrid.clicked.connect(self.redraw)

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
        # Widget layout with box sizers
        #=============================================
          
        self.hbox1 = QtGui.QHBoxLayout()            
        for w in [self.butDraw, self.cboxGrid, lblLw, self.sldLw]:
            self.hbox1.addWidget(w)
            self.hbox1.setAlignment(w, QtCore.Qt.AlignVCenter)
            
        self.vbox = QtGui.QVBoxLayout()
        self.vbox.addWidget(self.mpl_toolbar)
        self.vbox.addWidget(self.pltCanv)
        self.vbox.addLayout(self.hbox1)         
#        self.setLayout(vbox)
        
        
#    def redraw(self):
#        """
#        Redraw the figure with new properties (grid, linewidth)
#        """
#        self.pltAxes.grid(self.cboxGrid.isChecked())
#        plt.artist.setp(self.pltPlt, linewidth = self.sldLw.value()/5.)
#        self.pltFig.tight_layout()
#        self.pltCanv.draw()        
        


class MplCanvas(FigureCanvas):
    """
    MatplotlibWidget inherits PyQt4.QtGui.QWidget
    and matplotlib.backend_bases.FigureCanvasBase

    """
    def __init__(self, parent=None):
 
        self.dpi = 100
        self.width = 4
        self.height = 3
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