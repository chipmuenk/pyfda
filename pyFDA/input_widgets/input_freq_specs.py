# -*- coding: utf-8 -*-
"""
Created on Mon Nov 18 13:36:39 2013

@author: Christian Münker
"""
from __future__ import print_function, division, unicode_literals
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

# add main directory from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

class InputFreqSpecs(QtGui.QWidget):
    """
    Build and update widget for entering the frequency
    specifications like F_sb, F_pb etc.
    """

    # class variables (shared between instances if more than one exists)
    specsChanged = pyqtSignal() # emitted when filter has been designed

    def __init__(self, specs, DEBUG = True):

        """
        Initialize; specs is a dictionary containing _all_ the filter specs
        """
        super(InputFreqSpecs, self).__init__()
        self.DEBUG = DEBUG
        self.specs = specs  # dictionary containing _all_ specifications of the
                            # currently selected filter
        self.qlabels = []    # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.initUI()

    def initUI(self):
        self.layVMain = QtGui.QVBoxLayout() # Widget main layout

        title = "Frequency Specifications"

        f_units = ['f_S', 'f_Nyq', 'Hz', 'kHz', 'MHz', 'GHz']
        self.t_units = ['', '', 's', 'ms', r'us', 'ns']
        fRanges = [("0...½", "half"), ("0...1","whole"), ("-½...½", "sym")]

        self.idxOld = -1 # index of cmbUnits before last change

        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        self.lblTitle = QtGui.QLabel(self) # field for widget title
        self.lblTitle.setText(str(title))
        self.lblTitle.setFont(bfont)
        self.lblTitle.setWordWrap(True)
        self.layVMain.addWidget(self.lblTitle)

        self.lblUnits=QtGui.QLabel(self)
        self.lblUnits.setText("Unit:")

        self.f_S = self.specs.fil[0]["f_S"]
        self.ledF_S = QtGui.QLineEdit()
        self.ledF_S.setText(str(self.f_S))
        self.ledF_S.setObjectName("f_S")

        self.lblF_S = QtGui.QLabel(self)
        self.lblF_S.setText(self.rtLabel("f_S"))

        self.cmbUnits = QtGui.QComboBox(self)
        self.cmbUnits.setObjectName("cmbUnits")
        self.cmbUnits.addItems(f_units)
        self.cmbUnits.setCurrentIndex(0)


        self.cmbFRange = QtGui.QComboBox(self)
        self.cmbFRange.setObjectName("cmbFRange")
        for f in fRanges:
            self.cmbFRange.addItem(f[0],f[1])
#        self.cmbFRange.addItems(["0...½","0...1", "-½...½"])
        self.cmbFRange.setToolTip("Select frequency range (whole or half).")
        self.cmbFRange.setCurrentIndex(0)
        
        """EDIT WinMic"""
        #Die ComboBox passt Ihre größe dynamisch dem längsten element an.
        self.cmbUnits.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbFRange.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        """END"""


        self.butSort = QtGui.QPushButton(self)
        self.butSort.setText("Sort")
        self.butSort.setToolTip("Sort frequencies in ascending order.")

        self.layHUnits = QtGui.QHBoxLayout()
        self.layHUnits.addWidget(self.cmbUnits)
        self.layHUnits.addWidget(self.cmbFRange)
        self.layHUnits.addWidget(self.butSort)

        # Create a gridLayout consisting of QLabel and QLineEdit fields
        # for setting f_S, the units and the actual frequency specs:
        self.layGSpecWdg = QtGui.QGridLayout() # sublayout for spec fields
        # addWidget(widget,row,col,rowSpan=1, colSpan=1, QtCore.Qt.Alignxxx)
        self.layGSpecWdg.addWidget(self.lblUnits,0,0)
        self.layGSpecWdg.addLayout(self.layHUnits,0,1)
        self.layGSpecWdg.addWidget(self.lblF_S,1,0)
        self.layGSpecWdg.addWidget(self.ledF_S,1,1)

        # - Build a list from all entries in the specs dictionary starting
        #   with "F" (= frequency specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget
        newLabels = [l for l in self.specs.fil[0] if l[0] == 'F']
        self.setEntries(newLabels = newLabels)

        sfFrame = QtGui.QFrame()
        sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        sfFrame.setLayout(self.layGSpecWdg)

        self.layVMain.addWidget(sfFrame)
        self.layVMain.setContentsMargins(1,1,1,1)

        self.setLayout(self.layVMain)

#        self.layVMain.addLayout(self.layGSpecWdg) # no frame
#        mainLayout = QtGui.QHBoxLayout()
#        mainLayout.addWidget(sfFrame)
#        self.setLayout(mainLayout)

        # SIGNALS & SLOTS =====================================================

        self.cmbUnits.currentIndexChanged.connect(self.freqUnits)
        self.cmbFRange.currentIndexChanged.connect(self.freqRange)
        self.ledF_S.editingFinished.connect(self.freqUnits)
        self.butSort.clicked.connect(self._sortEntries)
        # Every time a textfield is edited, call self.freqUnits - the signal is
        #   constructed in _addEntry

        self.freqUnits()

#    def mousePressEvent(self, event):
#        """
#        Do something every time a mouse event happens inside this widget - but
#        only if the event isn't swallowed by a child widget!!
#        (not needed or used at the moment)
#        """
#        print ("InputFreqs Mouse Press")
#        super(InputFreqSpecs, self).mousePressEvent(event)

#-------------------------------------------------------------
    def freqRange(self):
        """
        Set frequency range for single-sided spectrum up to f_S/2 or f_S or
        for double-sided spectrum between -f_S/2 and f_S/2
        """
#        rangeIdx = self.cmbFRange.currentIndex#.item(self.cmbFRange.currentIndex())
        rangeType = self.cmbFRange.itemData(self.cmbFRange.currentIndex())
        self.specs.rcFDA.update({'freqSpecsRangeType':rangeType})
        if rangeType == 'whole':
            f_lim = [0, self.f_S]
        elif rangeType == 'sym':
            f_lim = [-self.f_S/2, self.f_S/2]
        else:
            f_lim = [0, self.f_S/2]

        self.specs.rcFDA['freqSpecsRange'] = f_lim
        self.specsChanged.emit() # ->pyFDA -> pltAll.updateAll()


#-------------------------------------------------------------
    def freqUnits(self):
        """
        Transform the frequency spec input fields according to the Units
        setting. Spec entries are always stored normalized w.r.t. f_S in the
        dictionary; when f_S or the unit are changed, only the displayed values
        of the frequency entries are updated, not the dictionary!

        freqUnits is called during init and every time a widget emits a signal.
        """
        idx = self.cmbUnits.currentIndex()  # read index of units combobox
        self.f_S = float(self.ledF_S.text()) # read sampling frequency

        # get ID of signal that triggered freqUnits():
        if self.sender(): # origin of signal that triggered the slot
            senderName = self.sender().objectName()
            print(senderName + ' was triggered\n================')
        else: # no sender, freqUnits has been called from initUI
            senderName = "cmbUnits"

        if senderName == "f_S" and self.f_S != 0:
            # f_S has been edited -> change display of frequency entries and
            # update dictionary entry for f_S
            self.specs.fil[0]['f_S'] = self.f_S
            for i in range(len(self.qlineedit)):
                f = self.specs.fil[0][self.qlineedit[i].objectName()]
                self.qlineedit[i].setText(str(f * self.f_S))

        elif senderName == "cmbUnits" and idx != self.idxOld:

            # combo unit has changed -> change display of frequency entries
            self.ledF_S.setVisible(idx > 1)  # only visible when
            self.lblF_S.setVisible(idx > 1) # not normalized

            # Handle special case when last setting was normalized to f_nyq:
            #  Restore spec entries (remove scaling factor 2 )
            if self.idxOld == 1: # was: normalized to f_nyq = f_S/2,
                for i in range(len(self.qlineedit)):
                    f = self.specs.fil[0][self.qlineedit[i].objectName()]
                    self.qlineedit[i].setText(str(f))
                self.f_S = 1.

            # Now check the new settings: -------------------------------------
            if idx < 2: # normalized frequency
                if idx == 0: # normalized to f_S
                    self.f_S = 1.
                    fLabel = r"$F = f/f_S = \Omega / 2 \pi \; \rightarrow$"
                else:   # idx == 1: normalized to f_nyq = f_S / 2
                    self.f_S = 2.
                    fLabel = r"$F = 2f/f_S = \Omega / \pi \; \rightarrow$"
                tLabel = r"$n \; \rightarrow$"
                self.ledF_S.setText(str(self.f_S)) # update field for f_S

                # recalculate displayed freq spec values but do not store them:
                for i in range(len(self.qlineedit)):
                    f = self.specs.fil[0][self.qlineedit[i].objectName()]
                    self.qlineedit[i].setText(str(f * self.f_S))
            else: # Hz, kHz, ...
                    
                unit = str(self.cmbUnits.itemText(idx))
                fLabel = r"$f$ in " + unit + r"$\; \rightarrow$"
                tLabel = r"$t$ in " + self.t_units[idx] + r"$\; \rightarrow$"

            self.specs.rcFDA.update({"plt_fLabel":fLabel}) # label for freq. axis
            self.specs.rcFDA.update({"plt_tLabel":tLabel}) # label for freq. axis
            self.specs.fil[0]['f_S'] = self.f_S # store f_S in dictionary
            self.ledF_S.setText(str(self.f_S))

        else: # freq. spec textfield has been changed -> change dict
            self.storeEntries()

        self.idxOld = idx # remember setting of comboBox
        self.f_S_old = self.f_S # and f_S (not used yet)
        self.freqRange() # update f_lim setting and send redraw signal
#        self.specsChanged.emit() # ->pyFDA -> pltAll.updateAll()
#        print("PING!!!")


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
                    self.qlineedit[i].setText(str(self.specs.fil[0][newLabels[i]]*self.f_S))
                    self.qlineedit[i].setObjectName(newLabels[i])  # update ID

    def _delEntry(self,i):
        """
        Delete entry number i from subwidget (QLabel and QLineEdit)
        """
        self.layGSpecWdg.removeWidget(self.qlabels[i])
        self.layGSpecWdg.removeWidget(self.qlineedit[i])

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

        self.qlineedit.append(QtGui.QLineEdit(str(self.specs.fil[0][newLabel]*self.f_S)))
        self.qlineedit[i].editingFinished.connect(self.freqUnits)
        self.qlineedit[i].setObjectName(newLabel) # update ID

        self.layGSpecWdg.addWidget(self.qlabels[i],(i+2),0)
        self.layGSpecWdg.addWidget(self.qlineedit[i],(i+2),1)

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
                str(self.specs.fil[0][self.qlineedit[i].objectName()] * self.f_S))

    def storeEntries(self):
        """
        Store specification entries in filter dictionary
        Entries are normalized with sampling frequency self.f_S !
        The scale factor (khz, ...) is contained neither in f_S nor the specs
        hence, it cancels out.
        """
        for i in range(len(self.qlineedit)):
            self.specs.fil[0].update(
                {self.qlineedit[i].objectName():
                    float(self.qlineedit[i].text())/self.f_S})

#------------------------------------------------------------------------------

if __name__ == '__main__':
    import filterbroker as fb
    app = QtGui.QApplication(sys.argv)
    form = InputFreqSpecs(specs = fb) #.fil[0])

    form.setEntries(newLabels = ['F_SB','F_SB2','F_PB','F_PB2'])
    form.setEntries(newLabels = ['F_PB','F_PB2'])

    form.show()

    app.exec_()
