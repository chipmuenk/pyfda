# -*- coding: utf-8 -*-
"""
Widget for entering amplitude specifications

Author: Christian Münker
"""

# TODO: Check specs IIR / FIR A_PB <-> delta_PB

from __future__ import print_function, division, unicode_literals
from numpy import log10
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, Qt

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import rt_label
from pyfda.simpleeval import simple_eval

class InputAmpSpecs(QtGui.QWidget): #QtGui.QWidget,
    """
    Build and update widget for entering the amplitude
    specifications like A_sb, A_pb etc.
    """
    
    sigSpecsChanged = pyqtSignal()
    
    def __init__(self, DEBUG = True,  title = "Amplitude Specs"):
        """
        Initialize
        """
        super(InputAmpSpecs, self).__init__()
        self.DEBUG = DEBUG
        self.title = title

        self.qlabels = [] # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self._init_UI()

    def _init_UI(self):
        """
        Initialize User Interface
        """
        self.layVMain = QtGui.QVBoxLayout() # Widget vertical layout

        units = ["dB", "V", "W"]
        self.idxOld = -1 # index of comboUnits before last change

        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        self.lblTitle = QtGui.QLabel(self) # field for widget title
        self.lblTitle.setText(str(self.title))
        self.lblTitle.setFont(bfont)
        self.lblTitle.setWordWrap(True)
        self.layVMain.addWidget(self.lblTitle)

        self.lblUnits = QtGui.QLabel(self)
        self.lblUnits.setText("Unit:")

        self.cmbUnitsA = QtGui.QComboBox(self)
        self.cmbUnitsA.addItems(units)
        self.cmbUnitsA.setObjectName("cmbUnitsA")
        self.cmbUnitsA.setToolTip("Set unit for amplitude specifications:\n"
        "dB is attenuation (positive values)\nV and W are less than 1.")

        self.cmbUnitsA.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        # fit size dynamically to largest element
        self.cmbUnitsA.setCurrentIndex(0)
        
        self.layGSpecs = QtGui.QGridLayout() # sublayout for spec fields
        self.layGSpecs.addWidget(self.lblUnits,0,0)
        self.layGSpecs.addWidget(self.cmbUnitsA,0,1, Qt.AlignLeft)

        # - Build a list from all entries in the fil_dict dictionary starting
        #   with "A" (= amplitude specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget
        # ATTENTION: Entries need to be converted to str first for Py 2 (???)
        newLabels = [str(l) for l in fb.fil[0] if l[0] == 'A'] 
        self.update_UI(newLabels = newLabels)

        frmMain = QtGui.QFrame()
        frmMain.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        frmMain.setLayout(self.layGSpecs)

        self.layVMain.addWidget(frmMain)
        self.layVMain.setContentsMargins(1,1,1,1)

        self.setLayout(self.layVMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmbUnitsA.currentIndexChanged.connect(self._amp_units)
        # DYNAMIC SIGNAL SLOT CONNECTION:
        # Every time a field is edited, call self._amp_units - this signal-slot
        # mechanism is constructed in self._add_entry/ destructed in 
        # self._del_entry each time the widget is updated, i.e. when a new 
        # filter design method is selected.
        #----------------------------------------------------------------------

        self._amp_units() # first time initialization


#------------------------------------------------------------------------------
    def _amp_units(self):
        """
        Transform the amplitude spec input fields according to the Units
        setting. Spec entries are always stored in dB, only the displayed
        values are adapted to the amplitude unit, not the dictionary!
        """
        idx = self.cmbUnitsA.currentIndex()  # read index of units combobox

        if self.sender(): # origin of signal that triggered the slot
            senderName = self.sender().objectName()
            if self.DEBUG:
                print(senderName + ' was triggered\n================')
        else: # no sender, _amp_units has been called from initUI
            senderName = "cmbUnitsA"

        if senderName == "cmbUnitsA" and idx != self.idxOld:
            # combo unit has changed -> change display of amplitude entries
            self.load_entries()

        else: # amplitude spec textfield has been changed
            self._store_entries()
            
        self.idxOld = idx
        

#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Reload textfields from filter dictionary to reflect settings that
        may have been changed by the filter design algorithm.
        """

        def dB2amp(amp_label, dB_pow=20):
            """
            Convert dB to amplitude or power ripple:
            - passband: delta_PB = 1 - 10 ** (-A_PB/10 resp. 20) [IIR]
                        delta_PB = (10 ** (A_PB / 20) - 1)/ (10 ** (A_PB / 20) + 1)[FIR]
            - stopband: delta_SB = -10 ** (-A_SB/10 resp. 20)
            """
            amp_value = fb.fil[0][amp_label]
            if "PB" in amp_label: # passband
                if fb.fil[0]['ft'] == 'IIR':
                    delta = round(1. - 10.**(-amp_value / dB_pow), 10)
                else: 
      #              delta = round(10.**(amp_value / (2 * dB_pow)) - 1, 10)
                    delta = round((10.**(amp_value / dB_pow) - 1)/
                                    (10.**(amp_value / dB_pow) + 1),10)
            else: # stopband
                delta = round(10.**(-amp_value / dB_pow), 10)
            return delta

        idx = self.cmbUnitsA.currentIndex()  # read index of units combobox
 
        for i in range(len(self.qlineedit)):
            amp_label = str(self.qlineedit[i].objectName())
            
            if idx == 0: # Entry is in dBs, same as in dictionary -> no conversion
                self.qlineedit[i].setText(str(fb.fil[0][amp_label]))
            elif idx == 1:  # Convert dBs to voltages
                self.qlineedit[i].setText(str(dB2amp(amp_label, dB_pow = 20)))         
            else:  # # Convert dBs to power
                self.qlineedit[i].setText(str(dB2amp(amp_label, dB_pow = 10)))

#------------------------------------------------------------------------------
    def _store_entries(self):
        """
        Store specification entries in filter dictionary
        Entries are always stored in dB (20 log10) !
        """
        
        def amp2dB(amp_label, amp_value, dB_pow=20):
            """
            Convert amplitude or power ripple to dB:
            - passband: A_PB = -10 resp. 20 * log10(1-ripple_PB) [IIR]
                        A_PB = 20 log10((1+ripple_PB)/(1-ripple_PB)) [FIR]
            - stopband: A_SB = -10 resp. 20 * log10(ripple_SB)
            """
            
            if "PB" in amp_label: # passband
                if fb.fil[0]['ft'] == 'IIR':
                    A_dB = round(-dB_pow * log10(1. - amp_value), 10)
                else:
                    A_dB = round(dB_pow * log10((1. + amp_value)/(1 - amp_value)), 10)
            else: # stopband
                A_dB = round(-dB_pow * log10(amp_value),10)
            return A_dB

        idx = self.cmbUnitsA.currentIndex()  # read index of units combobox    
        
        for i in range(len(self.qlineedit)):
            amp_label = str(self.qlineedit[i].objectName())
            amp_value = simple_eval(self.qlineedit[i].text())
            if idx == 0: # Entry is in dBs, same as in dictionary
                fb.fil[0].update({amp_label:amp_value})
            elif idx == 1:  # Entries are voltages, convert to dBs
                    fb.fil[0].update(
                       {amp_label:amp2dB(amp_label, amp_value, dB_pow=20)})          
            else:  # Entries are powers, convert to dBs
                    fb.fil[0].update(
                       {amp_label:amp2dB(amp_label, amp_value, dB_pow=10)}) 
                       
        self.sigSpecsChanged.emit() # -> input_specs


#------------------------------------------------------------------------------
    def update_UI(self, newLabels = []):
        """
        Set labels and get corresponding values from filter dictionary.
        When number of elements changes, the layout of subwidget is rebuilt in
        self.layGSpecs.
        """
        # Check whether the number of entries has changed
        for i in range(max(len(self.qlabels), len(newLabels))):
             # newLabels is shorter than qlabels -> delete the difference
            if (i > (len(newLabels)-1)):
                self._del_entry(len(newLabels))

            # newLabels is longer than existing qlabels -> create new ones!
            elif (i > (len(self.qlabels)-1)):
             self._add_entry(i,newLabels[i])

            else:
                # when entry has changed, update label and corresponding value
                if self.qlineedit[i].objectName() != newLabels[i]:
                    self.qlabels[i].setText(rt_label(newLabels[i]))
                    
                    self.qlineedit[i].setText(str(fb.fil[0][newLabels[i]]))
                    self.qlineedit[i].setObjectName(newLabels[i])  # update ID


#------------------------------------------------------------------------------
    def _del_entry(self,i):
        """
        Delete entry number i from subwidget (QLabel and QLineEdit) and
        disconnect the lineedit field from self._amp_units
        """
        self.qlineedit[i].editingFinished.disconnect(self._amp_units) # needed?
        
        self.layGSpecs.removeWidget(self.qlabels[i])
        self.layGSpecs.removeWidget(self.qlineedit[i])

        self.qlabels[i].deleteLater()
        del self.qlabels[i]
        self.qlineedit[i].deleteLater()
        del self.qlineedit[i]


#------------------------------------------------------------------------------
    def _add_entry(self, i, newLabel):
        """
        Append entry number i to subwidget (QLabel und QLineEdit) in self.layGSpecs
        and connect QLineEdit.editingFinished to self._amp_units. This way, the
        filter dictionary is updated automatically when a QLineEdit field has 
        been edited (i.e. looses focus or when a return is entered).
        """
        self.qlabels.append(QtGui.QLabel(self))
        self.qlabels[i].setText(rt_label(newLabel))

        self.qlineedit.append(QtGui.QLineEdit(str(fb.fil[0][newLabel])))
        self.qlineedit[i].setObjectName(newLabel) # update ID
        
        self.qlineedit[i].editingFinished.connect(self._amp_units)

        self.layGSpecs.addWidget(self.qlabels[i],(i+2),0)
        self.layGSpecs.addWidget(self.qlineedit[i],(i+2),1)

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputAmpSpecs()

    form.update_UI(newLabels = ['A_SB','A_SB2','A_PB','A_PB2'])
    form.update_UI(newLabels = ['A_PB','A_PB2'])

    form.show()

    app.exec_()
