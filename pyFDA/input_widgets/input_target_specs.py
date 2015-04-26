# -*- coding: utf-8 -*-
"""
Created on Thu Nov 14 15:21:19 2013
Widget for entering filter specifications

@author: beike, Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import numpy as np
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb
#from filter_tree_builder import FilterTreeBuilder

from input_widgets import (input_filter, input_order, input_amp_specs,
                           input_freq_specs, input_weight_specs)
#from plot_widgets import plot_all


class InputTargetSpecs(QtGui.QWidget):
    """
    Build widget for entering all filter specs
    """
    # class variables (shared between instances if more than one exists)
    filterDesigned = pyqtSignal()  # emitted when filter has been designed
    filterChanged = pyqtSignal()

    def __init__(self, specs, DEBUG = False):
        super(InputTargetSpecs, self).__init__()
#        self.setStyleSheet("margin:5px; border:1px solid rgb(0, 0, 0); ")
#        self.setStyleSheet("background-color: rgb(255,0,0); margin:5px; border:1px solid rgb(0, 255, 0); ")


        self.DEBUG = DEBUG
#        self.ftb = FilterTreeBuilder('init.txt', 'filter_design',
#                                    commentChar = '#', DEBUG = DEBUG) #
        self.initUI()

    def initUI(self):
        """
        Create all widgets:

        fspecs : Frequency Specifications


        """

        # subwidget for Frequency Specs
        self.fspecs = input_freq_specs.InputFreqSpecs(specs = fb.fil[0],
                    DEBUG = False)
        # subwidget for Amplitude Specs
        self.aspecs = input_amp_specs.InputAmpSpecs(specs = fb.fil[0],
                    DEBUG = False)

        self.aspecs.setVisible(True)
        """
        LAYOUT
        """
        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        lblTitle = QtGui.QLabel(self) # field for widget title
        lblTitle.setText("Target Specifications")
        lblTitle.setFont(bfont)

        spcV = QtGui.QSpacerItem(0,0, QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Expanding)
        layGMain = QtGui.QGridLayout()
#        layGMain.addWidget(self.fspecs,0,0,1,2)
        
        layGMain.addWidget(lblTitle,0,0,1,2)
        layGMain.addWidget(self.fspecs,1,0)  # Freq. specifications
        layGMain.addWidget(self.aspecs,1,1)   # Amplitude specs
        layGMain.addItem(spcV,2,0)   # Amplitude specs

        layGMain.setContentsMargins(1,1,1,1)

        self.setLayout(layGMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        # Call chooseDesignMethod every time filter selection is changed:

        self.chooseDesignMethod() # first time initialization

    def chooseDesignMethod(self):
        """
        Reads:  fb.fil[0] (currently selected filter), extracting info
                from fb.filTree
        Writes:
        Depending on SelectFilter and frequency specs, the values of the
        widgets fo, fspecs are recreated. For widget ms, the visibility is changed
        as well.
        """

        # filter object instance is created from design method
        # (e.g. 'cheby1', 'min') in input_filter.py

        # Read freq / amp / weight labels for current filter design
        rt = fb.fil[0]['rt']
        ft = fb.fil[0]['ft']
        dm = fb.fil[0]['dm']
#        fo = fb.fil[0]['fo']
#        print(fb.filTree[rt][ft])
#TODO: The following fails when a design method has no minimum filter order 
#       algorithm! Solution: Provide generic parameters for LP / BP / ... as fallback        
        if 'min' in fb.filTree[rt][ft][dm]:
            myParams = fb.filTree[rt][ft][dm]['min']['par']
        else:
            myParams = {}
#        myEnbWdg = fb.filTree[rt][ft][dm][fo]['enb'] # enabled widgets

        # build separate parameter lists according to the first letter
        self.freqParams = [l for l in myParams if l[0] == 'F']
        self.ampParams = [l for l in myParams if l[0] == 'A']
        if self.DEBUG:
            print("=== InputParams.chooseDesignMethod ===")
            print("selFilter:", fb.fil[0])
            print('myLabels:', myParams)
            print('ampLabels:', self.ampParams)
            print('freqLabels:', self.freqParams)
            print('weightLabels:', self.weightParams)

        # pass new labels to widgets
        # set widgets invisible if param list is empty
        self.fspecs.setEntries(newLabels = self.freqParams) # update frequency spec labels
        self.aspecs.setVisible(self.ampParams != [])
        self.aspecs.setEntries(newLabels = self.ampParams)

        self.filterChanged.emit() # ->pyFDA -> pltAll.updateAll()

    def storeEntries(self):
        """
        Update global dict fb.fil[0] with currently selected filter
        parameters, using the update methods of the classes
        """
        # collect data from widgets and write to fb.fil[0]
        self.fspecs.storeEntries() # frequency specification widget
        self.aspecs.storeEntries() # magnitude specs with unit

        if self.DEBUG: print(fb.fil[0])


#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = InputTargetSpecs(specs = fb.fil[0])
    form.show()
    form.storeEntries()

    app.exec_()







