# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

xxx

@author: Julia Beike, Christian Münker
Created on 18.11.2013
Updated on Thur Dec 11 2014
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui, QtCore

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')


class InputAmpSpecs(QtGui.QWidget): #QtGui.QWidget, 
    
    def __init__(self, specs, labels=[], DEBUG = True):
        
        """
        Initialisierung
        units: sind die Einheiten die in der Combobox stehen sollen
        lab: Namen der Labels in einer Liste
        """
        super(InputAmpSpecs, self).__init__()   
        self.DEBUG = DEBUG
        self.specs = specs  # dictionary containing _all_ specifications of the
                            # currently selected filter

        self.labels = labels # list with labels for combobox
        
        self.qlabels = [] # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()     
        
    def initUI(self): 
        self.WVLayout = QtGui.QVBoxLayout() # Widget vertical layout  
        self.layout   = QtGui.QGridLayout() # sublayout for spec fields
        title = "Amplitude Specifications"
        units = ["dB", "Squared"] 
       
        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        self.qtitle = QtGui.QLabel(self) # field for widget title
        self.qtitle.setText(str(title))
        self.qtitle.setFont(bfont)
        self.qtitle.setWordWrap(True)
        self.WVLayout.addWidget(self.qtitle)
        

        self.lab_units=QtGui.QLabel(self)
        self.lab_units.setText("Units")

        self.combo_units=QtGui.QComboBox(self)
        self.combo_units.addItems(units)

        self.layout.addWidget(self.lab_units,0,0)
        self.layout.addWidget(self.combo_units,0,1, QtCore.Qt.AlignLeft)

        #self.layout.addWidget(self.qtitle, 0, 0, 2, 1) # span two columns

        # Create a gridLayout consisting of Labels and LineEdit fields
        # The number of created lines depends on the number of labels
        # qlabels is a list with references to the QLabel widgets, 
        # qlineedit contains references to the QLineEdit widgets

        # iterate over number of labels and fill in values        
        for i in range(len(self.labels)):        
           
            self.qlabels.append(QtGui.QLabel(self))
            self.qlabels[i].setText(self.labels[i])
            self.qlineedit.append(QtGui.QLineEdit(str(
                                        self.specs[self.labels[i]])))

            self.layout.addWidget(self.qlabels[i],(i+1),0)
            self.layout.addWidget(self.qlineedit[i],(i+1),1)
        
        sfFrame = QtGui.QFrame()
        sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        sfFrame.setLayout(self.layout)
        
        self.WVLayout.addWidget(sfFrame)
#        self.WVLayout.addLayout(self.layout)

        self.setLayout(self.WVLayout)
#        
#        mainLayout = QtGui.QHBoxLayout()
#        mainLayout.addWidget(sfFrame)
#        self.setLayout(mainLayout)
        
        # SIGNALS & SLOTS
        # Every time a field is edited, call self.freqUnits - the signal is
        #   constructed in _addEntry
        self.combo_units.currentIndexChanged.connect(self.ampUnits)

    def ampUnits(self):
        """
        Transform the amplitude spec input fields according to the Units 
        setting.
        """
        pass
    
    def rtLabel(self, label):
        """
        Rich text labels: Format labels with HTML tags, replacing '_' by 
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
                    self.qlineedit[i].setText(str(self.specs[newLabels[i]]))
                    self.qlineedit[i].setObjectName(newLabels[i])  # update ID     
                     
    def _delEntry(self,i):
        """
        Delete entry number i from subwidget (QLabel and QLineEdit)
        """
        self.layout.removeWidget(self.qlabels[i])
        self.layout.removeWidget(self.qlineedit[i])

        self.qlabels[i].deleteLater()
        del self.qlabels[i]
        self.qlineedit[i].deleteLater()
        del self.qlineedit[i]  
        

    def _addEntry(self, i, newLabel): 
        """
        Append entry number i to subwidget (QLabel und QLineEdit)
        """
        self.qlabels.append(QtGui.QLabel(self))
        self.qlabels[i].setText(self.rtLabel(newLabel))
        
        self.qlineedit.append(QtGui.QLineEdit(str(self.specs[newLabel])))
        self.qlineedit[i].editingFinished.connect(self.ampUnits)
        self.qlineedit[i].setObjectName(newLabel) # update ID

        self.layout.addWidget(self.qlabels[i],(i+2),0)
        self.layout.addWidget(self.qlineedit[i],(i+2),1)
        
    def _sortEntries(self): 
        """
        Sort spec entries with ascending frequency and store in filter dict.
        """ 
        fSpecs = [self.qlineedit[i].text() for i in range(len(self.qlineedit))]
        
        fSpecs.sort()
        
        for i in range(len(self.qlineedit)):
            self.qlineedit[i].setText(fSpecs[i])
            
        self.storeEntries()
      
    def loadEntries(self):
        """
        Reload textfields from filter dictionary to update changed settings 
        """
        for i in range(len(self.qlineedit)): 
            self.qlineedit[i].setText(
                str(self.specs[self.qlineedit[i].objectName()]))#text()]))

    def storeEntries(self):
        """
        Store specification entries in filter dictionary
        Entries are normalized with sampling frequency self.f_S !
        The scale factor (khz, ...) is contained neither in f_S nor the specs
        hence, it cancels out.
        """
        for i in range(len(self.qlabels)): 
            self.specs.update(
                {self.qlineedit[i].objectName():float(self.qlineedit[i].text())})
    
#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    import filterbroker as fb
   
    app = QtGui.QApplication(sys.argv)
    form = InputAmpSpecs(specs = fb.gD["selFilter"])

    form.setEntries(newLabels = ['W_SB','W_SB2','W_PB','W_PB2'])
    form.setEntries(newLabels = ['W_PB','W_PB2'])

    form.show()
   
    app.exec_()
