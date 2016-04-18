# -*- coding: utf-8 -*-
"""
Widget for entering weight specifications

Author: Julia Beike, Christian Münker
"""
from __future__ import print_function, division, unicode_literals
import sys
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import rt_label
from pyfda.simpleeval import simple_eval

class InputWeightSpecs(QtGui.QWidget):
    """
    Build and update widget for entering the weight
    specifications like W_SB, W_PB etc.
    """
           
    sigSpecsChanged = pyqtSignal()

    def __init__(self, parent):

        super(InputWeightSpecs, self).__init__(parent)

        self.qlabels = [] # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self._init_UI()

#------------------------------------------------------------------------------
    def _init_UI(self):
        """
        Initialize UI
        """
        self.layVMain = QtGui.QVBoxLayout() # Widget vertical layout
        self.layGSpecs   = QtGui.QGridLayout() # sublayout for spec fields

        title = "Weight Specifications"
        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        self.lblTitle = QtGui.QLabel(self) # field for widget title
        self.lblTitle.setText(str(title))
        self.lblTitle.setFont(bfont)
        self.lblTitle.setWordWrap(True)
        self.layVMain.addWidget(self.lblTitle)

        self.butReset = QtGui.QPushButton("Reset", self)
        self.butReset.setToolTip("Reset weights to 1")

        self.layGSpecs.addWidget(self.butReset, 1, 1) # span two columns


        frmMain = QtGui.QFrame()
        frmMain.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        frmMain.setLayout(self.layGSpecs)

        self.layVMain.addWidget(frmMain)
#        self.layVMain.addLayout(self.layGSpecs)
        self.layVMain.setContentsMargins(1,1,1,1)

        self.setLayout(self.layVMain)
        
        # - Build a list from all entries in the fil_dict dictionary starting
        #   with "W" (= weight specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget
        # ATTENTION: Entries need to be converted from QString to str for Py 2
        new_labels = [str(l) for l in fb.fil[0] if l[0] == 'W']
        self.update_UI(new_labels = new_labels)


        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.butReset.clicked.connect(self._reset_weights)
        # DYNAMIC SIGNAL SLOT CONNECTION:
        # Every time a field is edited, call self._store_entries - this signal-
        # slot mechanism is constructed in self.add_entry/ destructed in 
        # self._del_entry each time the widget is updated, i.e. when a new 
        # filter design method is selected.
        #----------------------------------------------------------------------
        

#-------------------------------------------------------------
    def update_UI(self, new_labels = []):
        """
        Set labels and get corresponding values from filter dictionary.
        When number of elements changes, the layout of subwidget is rebuilt.
        
        Connect new QLineEdit fields to _store_entries so that the filter
        dictionary is updated automatically when a QLineEdit field has been
        edited.
        """
        # Check whether the number of entries has changed: 
        #  self.qlabels is a list with references to existing QLabel widgets,
        #  new_labels is a list of strings from the filter_dict for the current
        #    filter design

        delta_new_labels = len(new_labels) - len(self.qlabels)
        
        if delta_new_labels < 0: # less new labels, delete old ones
            self._del_entries(-delta_new_labels)

        elif delta_new_labels > 0: # more new labels, create new ones
            self._add_entries(delta_new_labels)
            
        for i in range(len(new_labels)):        
#            else:
                # when entry has changed, update signal-slot connection, 
                #  label and corresponding value
                if str(self.qlineedit[i].objectName()) != new_labels[i]:
                    try:
                        self.qlineedit[i].editingFinished.disconnect()
                    except TypeError:
                        pass
                    self.qlabels[i].setText(rt_label(new_labels[i]))
    
                    self.qlineedit[i].setText(
                        str(fb.fil[0][new_labels[i]] * fb.fil[0]['f_S']))
                    self.qlineedit[i].setObjectName(new_labels[i])  # update ID                      
                    self.qlineedit[i].editingFinished.connect(self._store_entries)
#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Reload textfields from filter dictionary to update changed settings
        """
        for i in range(len(self.qlineedit)):
            self.qlineedit[i].setText(
                str(fb.fil[0][str(self.qlineedit[i].objectName())]))

#------------------------------------------------------------------------------
    def _store_entries(self):
        """
        Store specification entries in filter dictionary
        """
        for i in range(len(self.qlineedit)):
            w_label = str(self.qlineedit[i].objectName())
            w_value = simple_eval(self.qlineedit[i].text())
            fb.fil[0].update({w_label:w_value})
                       
        self.sigSpecsChanged.emit() # -> input_specs
        
#-------------------------------------------------------------
    def _del_entries(self, num):
        """
        Delete num subwidgets (QLabel and QLineEdit) from layout and memory and
        disconnect the editingFinished signals from self._store_entries.
        """
        Nmax = len(self.qlabels)-1  # number of existing labels
        for i in range(Nmax, Nmax-num, -1):  # start with len, last element len - num
            
            self.qlineedit[i].editingFinished.disconnect()
    
            self.layGSpecs.removeWidget(self.qlabels[i])
            self.layGSpecs.removeWidget(self.qlineedit[i])
    
#            self.qlabels[i].deleteLater() # 
            self.qlabels[i].setParent(None) # alternative: change ownership back to python
            del self.qlabels[i]
#            self.qlineedit[i].deleteLater()
            self.qlineedit[i].setParent(None) # alternative: change ownership back to python
            del self.qlineedit[i]        
                
#------------------------------------------------------------------------
    def _add_entries(self, num):
        """
        Append num subwidgets (QLabel und QLineEdit) to memory and layout and 
        initialize them with dummy information.
        """
        Nmax = len(self.qlabels)-1 # number of existing labels
        # start with Nmax + 1, last element Nmax + num +1
        for i in range(Nmax+1, Nmax+num+1, 1): 
            self.qlabels.append(QtGui.QLabel(self))
            self.qlabels[i].setText(rt_label("dummy"))
    
            self.qlineedit.append(QtGui.QLineEdit(""))
            self.qlineedit[i].setObjectName("dummy")
    
            self.layGSpecs.addWidget(self.qlabels[i],(i+2),0)
            self.layGSpecs.addWidget(self.qlineedit[i],(i+2),1)   


#------------------------------------------------------------------------------
    def _reset_weights(self):
        """
        Reset all entries to "1.0" and store them in the filter dictionary
        """
        for i in range(len(self.qlineedit)):
            self.qlineedit[i].setText("1.0")
        self._store_entries()


#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    mainw = InputWeightSpecs(None)

    mainw.update_UI(new_labels = ['W_SB','W_SB2','W_PB','W_PB2'])
    mainw.update_UI(new_labels = ['W_PB','W_PB2'])

    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())
