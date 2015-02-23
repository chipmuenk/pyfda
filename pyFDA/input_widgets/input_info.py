# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying infos about filter and filter design method
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui
#import scipy.io
import numpy as np

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb # importing filterbroker initializes all its globals


class InputInfo(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputInfo, self).__init__()

        self.initUI()
        self.showInfo()
        
    def initUI(self): 
        """
        Intitialize the widget, consisting of:
        - 
        - 
        """
        # widget / subwindow for parameter selection
        self.chkFilterInfo = QtGui.QCheckBox()
        self.chkFilterInfo.setChecked(True)
        self.chkFilterInfo.setToolTip("Display filter info from filter design file.")
        self.lblFilterInfo = QtGui.QLabel()
        self.lblFilterInfo.setText("Filter Info")

        
        self.lblFiltInfoBox = QtGui.QLabel()
        self.lblFiltInfoBox.setWordWrap(True)
        
        filtInfoLayout = QtGui.QVBoxLayout()
        filtInfoLayout.addWidget(self.lblFiltInfoBox)
        
        self.frmFiltInfoBox = QtGui.QFrame()
        self.frmFiltInfoBox.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        self.frmFiltInfoBox.setLayout(filtInfoLayout)
        self.frmFiltInfoBox.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                 QtGui.QSizePolicy.Minimum)


 
        # ============== UI Layout =====================================
        self.chkLayout = QtGui.QHBoxLayout()
        self.chkLayout.addWidget(self.chkFilterInfo) # filter export button
        self.chkLayout.addWidget(self.lblFilterInfo)
        self.chkLayout.addStretch(10)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(self.chkLayout)
        vbox.addWidget(self.frmFiltInfoBox)
        vbox.addStretch(10)
        self.setLayout(vbox)
        
        # ============== Signals & Slots ================================
        self.chkFilterInfo.clicked.connect(self.showInfo)     

        
    def showInfo(self):
        """
        Display info from filter design file
        """
        self.frmFiltInfoBox.setVisible(self.chkFilterInfo.isChecked())
        try:
            self.lblFiltInfoBox.setText(fb.filObj.info)
        except AttributeError as e:
            print(e)

#------------------------------------------------------------------------------
   
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputInfo()
    form.show()
   
    app.exec_()