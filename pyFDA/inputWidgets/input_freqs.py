# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

input_utils.py

@author: Christian Münker
Created on 23.1.2015
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from collections import OrderedDict
from PyQt4 import QtGui, QtCore

# add main directory from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')
    
# TODO: When changing between response types / minMax with different number of
# frequency spec entries and f_S != 1 , the frequency values (only display?)
# become jumbled, i.e. are scaled with different factors - check f_S scaling in loadEntries !
    
class InputFreqs(QtGui.QWidget):
    """
    Build and update widget for entering the frequency 
    specifications like F_sb, F_pb etc.
    """
    
    def __init__(self, specs, DEBUG = True):
        
        """
        Initialize
        specs: A dictionary containing all the specs
        labels: Names of the frequency spec labels
        """
        super(InputFreqs, self).__init__()   
        self.DEBUG = DEBUG
        self.specs = specs  # dictionary containing _all_ specifications of the
                            # currently selected filter
        self.qlabels = []    # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()     
        
    def initUI(self): 
        self.WVLayout = QtGui.QVBoxLayout() # Widget vertical layout  

        title = "Frequency Specifications"      
        self.unitsf = OrderedDict([
        ('Normalized to f_S', 1),
        ('Normalized to f_S/2', 2),
        ('Hz', 1.),
        ('kHz', 1000.),
        ('MHz', 1.e6),
        ('GHz', 1.e9)
        ])
        
        self.idxOld = -1 # index of comboUnits before last change

        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        self.qtitle = QtGui.QLabel(self) # field for widget title
        self.qtitle.setText(str(title))
        self.qtitle.setFont(bfont)
        self.qtitle.setWordWrap(True)
        self.WVLayout.addWidget(self.qtitle)    

        self.labelUnits=QtGui.QLabel(self)
        self.labelUnits.setText("Units")
        
        self.f_S = self.specs["f_S"]            
        self.editF_S = QtGui.QLineEdit()
        self.editF_S.setText(str(self.f_S))
        self.editF_S.setObjectName("f_S")

        self.labelF_S = QtGui.QLabel(self)
        self.labelF_S.setText(self.rtLabel("f<sub>S</sub>"))

        self.comboUnits = QtGui.QComboBox(self)
        self.comboUnits.setObjectName("comboUnits")
        self.comboUnits.addItems(self.unitsf.keys())
        self.comboUnits.setCurrentIndex(0)
        
        self.butSort = QtGui.QPushButton(self)
        self.butSort.setText("Sort")
        self.butSort.setToolTip("Sort frequencies in ascending order.")       
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.comboUnits)
        self.hbox.addWidget(self.butSort)

        # Create a gridLayout consisting of QLabel and QLineEdit fields
        # for setting f_S, the units and the actual frequency specs:
        self.layout = QtGui.QGridLayout() # sublayout for spec fields
        # addWidget(widget,row,col,rowSpan=1, colSpan=1, QtCore.Qt.Alignxxx)
        self.layout.addWidget(self.labelUnits,0,0)
        self.layout.addLayout(self.hbox,0,1)
        self.layout.addWidget(self.labelF_S,1,0)
        self.layout.addWidget(self.editF_S,1,1)

        # - Build a list from all entries in the specs dictionary starting 
        #   with "F" (= frequency specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget        
        newLabels = [l for l in self.specs if l[0] == 'F']
        self.setEntries(newLabels = newLabels)
        
        sfFrame = QtGui.QFrame()
        sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        sfFrame.setLayout(self.layout)
        
        self.WVLayout.addWidget(sfFrame)
        self.setLayout(self.WVLayout)
        
#        self.WVLayout.addLayout(self.layout) # no frame        
#        mainLayout = QtGui.QHBoxLayout()
#        mainLayout.addWidget(sfFrame)
#        self.setLayout(mainLayout)
        
        # SIGNALS & SLOTS
        # Every time a field is edited, call self.freqUnits - the signal is
        #   constructed in _addEntry
        self.comboUnits.currentIndexChanged.connect(self.freqUnits)
        self.editF_S.editingFinished.connect(self.freqUnits)
        self.butSort.clicked.connect(self._sortEntries)
        
        self.freqUnits()

    def mousePressEvent(self, event):
        """
        Do something every time a mouse event happens inside this widget - but 
        only if the event isn't swallowed by a child widget!!
        """
        print ("InputFreqs Mouse Press")
        super(InputFreqs, self).mousePressEvent(event)        

#-------------------------------------------------------------        
    def freqUnits(self):
        """
        Transform the frequency spec input fields according to the Units 
        setting. Spec entries are always stored normalized w.r.t. f_S in the 
        dictionary; when f_S or the unit are changed, only the displayed values
        of the frequency entries are updated, not the dictionary!

        freqUnits is called during init and every time a widget sends a signal.
        """        
        idx = self.comboUnits.currentIndex()  # read index of units combobox
        self.f_S = float(self.editF_S.text()) # read sampling frequency

        if self.sender(): # origin of signal that triggered the slot
            senderName = self.sender().objectName() 
            print(senderName + ' was triggered\n================')
        else: # no sender, freqUnits has been called from initUI
            senderName = "comboUnits"

        if senderName == "f_S" and self.f_S != 0:
            # f_S has been edited -> change display of frequency entries and
            # dictionary entry for f_S
            self.specs['f_S'] = self.f_S
            for i in range(len(self.qlabels)):
                f = self.specs[self.qlineedit[i].objectName()]
                self.qlineedit[i].setText(str(f * self.f_S))

        elif senderName == "comboUnits" and idx != self.idxOld:
            # combo unit has changed -> change display of frequency entries
            self.editF_S.setVisible(idx > 1)  # only visible when 
            self.labelF_S.setVisible(idx > 1) # not normalized
            
            if self.idxOld == 1: # was: normalized to f_S/2,
                # remove scaling factor 2 from spec entries
                for i in range(len(self.qlabels)):
                    f = self.specs[self.qlineedit[i].objectName()]
                    self.qlineedit[i].setText(str(f))
                self.f_S = 1.

            if idx < 2: # normalized frequency
                if idx == 0: # normalized to f_S
                    self.f_S = 1.
                    fLabel = r"$F = f/f_S \; \rightarrow$"
                else:   # idx == 1: normalized to f_S / 2
                    self.f_S = 2. 
                    fLabel = r"$F = 2f/f_S \; \rightarrow$"

                self.editF_S.setText(str(self.f_S)) # update textedit
                
                # recalculate displayed freq spec values but do not store them:
                for i in range(len(self.qlabels)):
                    f = self.specs[self.qlineedit[i].objectName()]
                    self.qlineedit[i].setText(str(f * self.f_S))
            else: # Hz, kHz, ...
                unit = str(self.comboUnits.itemText(idx))
                fLabel = r"$f$ in " + unit + r"$\; \rightarrow$"

            self.specs.update({"plt_fLabel":fLabel}) # label for freq. axis
            self.specs['f_S'] = self.f_S # store f_S in dictionary
            self.editF_S.setText(str(self.f_S))

        else: # freq. spec textfield has been changed
            self.storeEntries()

#        print(idx, self.f_S, self.qlineedit[0].text(), self.specs["F_pb"])
        self.idxOld = idx # remember setting of comboBox
        self.f_S_old = self.f_S # and f_S (not used yet)
        
    
    def rtLabel(self, label):
        """
        Richt text labels: Format labels with HTML tags
        """
        htmlLabel = "<b><i>"+label+"</i></b>"
        return htmlLabel
    
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
                    self.qlabels[i].setText(self.rtLabel(newLabels[i]))#"<b><i>{0}</i></b>".format(newLabels[i])) # update label
#                    self.qlabels[i].setText(newLabels[i]) # update label
                    
                    self.qlineedit[i].setText(str(self.specs[newLabels[i]]*self.f_S))
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
#        self.qlabels[i].setText(newLabel)
        
        self.qlineedit.append(QtGui.QLineEdit(str(self.specs[newLabel])))
        self.qlineedit[i].editingFinished.connect(self.freqUnits)
        self.qlineedit[i].setObjectName(newLabel) # update ID

        self.layout.addWidget(self.qlabels[i],(i+2),0)
        self.layout.addWidget(self.qlineedit[i],(i+2),1)
        
    def _sortEntries(self): 
        """
        Sort spec entries with ascending frequency and store in filter dict.
        """
        fSpecs = []
        for i in range(len(self.qlineedit)):
            fSpecs.append(self.qlineedit[i].text())
#        fSpecs = [f for f in self.qlineedit.text()]        
        
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
                str(self.specs[self.qlineedit[i].objectName()] * self.f_S))#text()]))

    def storeEntries(self):
        """
        Store specification entries in filter dictionary
        Entries are normalized with sampling frequency self.f_S !
        The scale factor (khz, ...) is contained neither in f_S nor the specs
        hence, it cancels out.
        """
        for i in range(len(self.qlabels)): 
            self.specs.update(
                {self.qlineedit[i].objectName():float(self.qlineedit[i].text())/self.f_S})

    
#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    import filterbroker as fb
    app = QtGui.QApplication(sys.argv)
    form = InputFreqs(specs = fb.gD["selFilter"])#, spec="TEST")

    form.setEntries(newLabels = ['F_sb','F_sb2','F_pb','F_pb2'])
    form.setEntries(newLabels = ['F_pb','F_pb2'])

    form.show()
   
    app.exec_()
