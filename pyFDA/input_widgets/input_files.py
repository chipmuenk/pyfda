# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for exporting / importing and saving / loading data
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui
#from PyQt4.QtCore import SIGNAL
import scipy.io
import numpy as np

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb # importing filterbroker initializes all its globals


class InputFiles(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputFiles, self).__init__()

        self.initUI()     
        
    def initUI(self): 
        """
        Intitialize the main GUI, consisting of:
        - Buttons for Exporting and Saving
        - 
        """
        # widget / subwindow for parameter selection
        self.butExportML = QtGui.QPushButton("Export -> ML", self)
        self.butExportCSV = QtGui.QPushButton("Export -> CSV", self)
        
        # ============== UI Layout =====================================
        self.grLayout = QtGui.QGridLayout()
        self.grLayout.addWidget(self.butExportML,1,0) # filter export button
        self.grLayout.addWidget(self.butExportCSV,2,0) # filter export button
        

        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(self.grLayout)
        self.setLayout(hbox)
        
        # ============== Signals & Slots ================================
        self.butExportML.clicked.connect(self.exportML)
        self.butExportCSV.clicked.connect(self.exportCSV)        

        
    def exportML(self):
        """
        Export filter coefficients to a file that can be imported into 
        Matlab workspace - see also Summerfield p. 192 ff
        """
#        myMLfile = QtGui.QFileDialog.setNameFilter('.mat')
#        myMLfile.getOpenFileName()
        formats = ["*.mat", "*.csv"]
        dlg=QtGui.QFileDialog( self )


        myMLfile = dlg.getSaveFileName(filter="Workspace / csv (*.mat *.csv)\nAll files(*.*)", directory="D:/Daten", 
                caption = "Save filter coefficients as")
       
        scipy.io.savemat(myMLfile, 
                         mdict={'filt_coeffs': fb.gD['coeffs']})
        print("exportML: Matlab workspace exported to %s!" %myMLfile)
        
    def exportCSV(self):
        """
        Export filter coefficients to a CSV-file 
        """
        
        np.savetxt('d:/Daten/filt_coeffs.csv', fb.gD['coeffs'])
        print("exportCSV: CSV - File exported!")
        

"""
File save format: use cPickle?

Alternative: Use the shelve module


import shelve

### write to database:
s = shelve.open('test_shelf.fb')
try:
    s['key1'] = { 'int': 10, 'float':9.5, 'string':'Sample data' }
finally:
    s.close()

### read from database:   
s = shelve.open('test_shelf.fb')
# s = shelve.open('test_shelf.fb', flag='r') # read-only
try:
    existing = s['key1']
finally:
    s.close()

print(existing)

### catch changes to objects, store in in-memory cache and write-back upon close
s = shelve.open('test_shelf.fb', writeback=True)
try:
    print s['key1']
    s['key1']['new_value'] = 'this was not here before'
    print s['key1']
finally:
    s.close()
    
"""
#------------------------------------------------------------------------------
   
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputFiles()
    form.show()
   
    app.exec_()