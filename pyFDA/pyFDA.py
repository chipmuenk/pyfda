# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Julia Beike, Christian Muenker

Main file for the pyFDA app, initializes UI
"""
from __future__ import print_function, division, unicode_literals
import sys
from PyQt4 import QtGui
import numpy as np

import databroker as db # importing databroker initializes all its globals
#from FilterFileReader import FilterFileReader
from inputWidgets import inputAll
from plotWidgets import plotAll


class pyFDA(QtGui.QWidget):
    PLT_SAME_WINDOW =  True
    """
    Create the main window for entering the filter specifications
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(pyFDA, self).__init__()
        # read directory with filterDesigns and construct filter tree from it
#        self.ffr = FilterFileReader('Init.txt', 'filterDesign', 
#                                    commentChar = '#', DEBUG = DEBUG) # 
        
        # initialize filter coefficients b, a :
        #self.em = QtGui.QFontMetricsF(QtGui.QLineEdit.font()).width('m')

        self.initUI()     
        
    def initUI(self): 
        """
        Intitialize the main GUI, consisting of:
        - Subwindow for parameter selection [-> ChooseParams.ChooseParams()]
        - Filter Design button [-> self.startDesignFilt()] 
        - Plot Window [-> plotAll.plotAll()]
        """
        # widget / subwindow for parameter selection
#        self.widgetInputParams = ChooseParams.ChooseParams() 

        self.inputAll = inputAll.inputAll()
        self.pltAll = plotAll.plotAll() # instantiate tabbed plot widgets  
#        self.inputAll.setMaximumWidth(280)

        # ============== UI Layout =====================================
#        self.grLayout = QtGui.QGridLayout()
#        self.grLayout.addWidget(self.widgetInputParams,0,0) # parameter select widget
#        self.grLayout.addWidget(self.butDesignFilt,1,0) # filter design button

        hbox = QtGui.QHBoxLayout()
#        hbox.addLayout(self.grLayout)
#        hbox.addWidget(self.pltAll)

        if self.PLT_SAME_WINDOW:
            # Plot window docked in same window:
            hbox.addWidget(self.inputAll)
            hbox.addWidget(self.pltAll)

        self.setLayout(hbox)
#        self.setLayout(self.layout1)
        
        # ============== Signals & Slots ================================
#        self.butDesignFilt.clicked.connect(self.startDesignFilt)
        self.inputAll.inputParams.butDesignFilt.clicked.connect(self.pltAll.update)

#    def startDesignFilt(self):
#        """
#        Design Filter
#        """
#        self.widgetInputParams.get() # -> db.gD["curSpecs"] 
#        if self.DEBUG:
#            print("--- pyFDA.py : startDesignFilter ---")
#            print('Specs:', db.gD["curSpecs"])#params)
#            print("db.gD['curFilter']['dm']", db.gD['curFilter']['dm']+"."+
#                  db.gD['curFilter']['rt']+db.gD['curFilter']['fo'])
#        # create filter object instance from design method (e.g. 'cheby1'):   
#        self.myFilter = self.ffr.objectWizzard(db.gD['curFilter']['dm'])
#        # Now construct the instance method from the response type (e.g.
#        # 'LP' -> cheby1.LP) and
#        # design the filter by passing current specs to the method:
#        getattr(self.myFilter, db.gD['curFilter']['rt']+db.gD['curFilter']['fo'])(db.gD["curSpecs"])
#        
#        # Read back filter coefficients and (zeroes, poles, k):
#        db.gD['zpk'] = self.myFilter.zpk # (zeroes, poles, k)
#        if np.ndim(self.myFilter.coeffs) == 1:  # FIR filter: only b coeffs
#            db.gD['coeffs'] = (self.myFilter.coeffs, [1]) # add dummy a = [1]
#            # This still has ndim == 1? 
#        else:                                   # IIR filter: [b, a] coeffs
#            db.gD['coeffs'] = self.myFilter.coeffs 
#        if self.DEBUG:
#            print("=== pyFDA.py : startDesignFilter ===")
#            print("zpk:" , db.gD['zpk'])
#            print('ndim gD:', np.ndim(db.gD['coeffs']))
#            print("b,a = ", db.gD['coeffs'])
#
#        if self.PLT_SAME_WINDOW:       
#            self.pltAll.update()
#        else:
#            # Separate window for plots:
#            self.pltAll.update()
#            self.pltAll.show()

#------------------------------------------------------------------------------
   
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = pyFDA()
    form.show()
   
    app.exec_()