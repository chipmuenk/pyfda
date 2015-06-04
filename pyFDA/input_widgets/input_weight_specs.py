# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

@author: Julia Beike, Christian Münker
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

# import from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb
from simpleeval import simple_eval

class InputWeightSpecs(QtGui.QWidget):
    """
    Build and update widget for entering the weight
    specifications like W_SB, W_PB etc.
    """
           
    sigSpecsChanged = pyqtSignal()

    def __init__(self, DEBUG = True):
        """
        Initialize; fil_dict is a dictionary containing _all_ the filter specs
        """

        super(InputWeightSpecs, self).__init__()
        self.DEBUG = DEBUG

        self.qlabels = [] # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()

    def initUI(self):
        self.layVMain = QtGui.QVBoxLayout() # Widget vertical layout
        self.layGSpecWdg   = QtGui.QGridLayout() # sublayout for spec fields

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

        self.layGSpecWdg.addWidget(self.butReset, 1, 1) # span two columns

        # - Build a list from all entries in the fil_dict dictionary starting
        #   with "W" (= weight specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget
        newLabels = [l for l in fb.fil[0] if l[0] == 'W']
        self.setEntries(newLabels = newLabels)

        frmMain = QtGui.QFrame()
        frmMain.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        frmMain.setLayout(self.layGSpecWdg)

        self.layVMain.addWidget(frmMain)
#        self.layVMain.addLayout(self.layGSpecWdg)
        self.layVMain.setContentsMargins(1,1,1,1)


        self.setLayout(self.layVMain)

        # =========== SIGNALS & SLOTS =======================================
        self.butReset.clicked.connect(self._resetWeights)
        # DYNAMIC SIGNAL SLOT CONNECTION:
        # Every time a field is edited, call self.storeEntries - this signal-
        # slot mechanism is constructed in self._addEntry/ destructed in 
        # self._delEntry each time the widget is updated, i.e. when a new 
        # filter design method is selected.

#-------------------------------------------------------------
    def rtLabel(self, label):
        """
        Rich text label: Format label with HTML tags, replacing '_' by
        HTML subscript tags
        """
        #"<b><i>{0}</i></b>".format(newLabels[i])) # update label
        if "_" in label:
            label = label.replace('_', '<sub>')
            label += "</sub>"
        htmlLabel = "<b><i>"+label+"</i></b>"
        return htmlLabel

#-------------------------------------------------------------
    def setEntries(self, newLabels = []):
        """
        Set labels and get corresponding values from filter dictionary.
        When number of elements changes, the layout of subwidget is rebuilt.
        """
        # Check whether the number of entries has changed
        for i in range(max(len(self.qlabels), len(newLabels))):
             # newLabels is shorter than qlabels -> delete the difference
            if (i > (len(newLabels)-1)):
                self._delEntry(len(newLabels))

            # newLabels is longer than existing qlabels -> create new ones!
            elif (i > (len(self.qlabels)-1)):
             self._addEntry(i,newLabels[i])

            else:
                # when entry has changed, update label and corresponding value
                if self.qlineedit[i].objectName() != newLabels[i]:
                    self.qlabels[i].setText(self.rtLabel(newLabels[i]))
                    self.qlineedit[i].setText(str(fb.fil[0][newLabels[i]]))
                    self.qlineedit[i].setObjectName(newLabels[i])  # update ID

    def _delEntry(self,i):
        """
        Delete entry number i from subwidget (QLabel and QLineEdit) and
        disconnect the lineedit field from self.storeEntries
        """
        self.qlineedit[i].editingFinished.disconnect(self.storeEntries)
        
        self.layGSpecWdg.removeWidget(self.qlabels[i])
        self.layGSpecWdg.removeWidget(self.qlineedit[i])

        self.qlabels[i].deleteLater()
        del self.qlabels[i]
        self.qlineedit[i].deleteLater()
        del self.qlineedit[i]


    def _addEntry(self, i, newLabel):
        """
        Append entry number i to subwidget (QLabel und QLineEdit) and
        connect QLineEdit widget to self.storeEntries. This way, the central filter
        dictionary is updated automatically when a QLineEdit field has been
        edited.
        """
        self.qlabels.append(QtGui.QLabel(self))
        self.qlabels[i].setText(self.rtLabel(newLabel))

        self.qlineedit.append(QtGui.QLineEdit(str(fb.fil[0][newLabel])))
        self.qlineedit[i].setObjectName(newLabel) # update ID
        
        self.qlineedit[i].editingFinished.connect(self.storeEntries)

        self.layGSpecWdg.addWidget(self.qlabels[i],(i+2),0)
        self.layGSpecWdg.addWidget(self.qlineedit[i],(i+2),1)

    def _resetWeights(self):
        for i in range(len(self.qlineedit)):
            self.qlineedit[i].setText("1.0")
        self.storeEntries()

    def loadEntries(self):
        """
        Reload textfields from filter dictionary to update changed settings
        """
        for i in range(len(self.qlineedit)):
            self.qlineedit[i].setText(
                str(fb.fil[0][self.qlineedit[i].objectName()]))

    def storeEntries(self):
        """
        Store specification entries in filter dictionary
        """
        for i in range(len(self.qlabels)):
            fb.fil[0].update(
                {self.qlineedit[i].objectName():float(self.qlineedit[i].text())})
                       
        self.sigSpecsChanged.emit() # -> input_all

#------------------------------------------------------------------------------

if __name__ == '__main__':

    import filterbroker as fb

    app = QtGui.QApplication(sys.argv)
    form = InputWeightSpecs(fil_dict = fb.fil[0])

    form.setEntries(newLabels = ['W_SB','W_SB2','W_PB','W_PB2'])
    form.setEntries(newLabels = ['W_PB','W_PB2'])

    form.show()

    app.exec_()
