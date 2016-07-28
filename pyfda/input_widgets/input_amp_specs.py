# -*- coding: utf-8 -*-
"""
Widget for entering amplitude specifications

Author: Christian Münker
"""

# TODO: Check specs IIR / FIR A_PB <-> delta_PB

from __future__ import print_function, division, unicode_literals
import sys
import logging
logger = logging.getLogger(__name__)
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, Qt, QEvent

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import rt_label, lin2unit, unit2lin
from pyfda.simpleeval import simple_eval

class InputAmpSpecs(QtGui.QWidget):
    """
    Build and update widget for entering the amplitude
    specifications like A_SB, A_PB etc.
    """
    
    sigSpecsChanged = pyqtSignal()
    
    def __init__(self, parent, title = "Amplitude Specs"):
        """
        Initialize
        """
        super(InputAmpSpecs, self).__init__(parent)
        self.title = title

        self.qlabels = [] # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self.FMT = '{:.3g}' # rounding format for QLineEdit fields
        self.spec_edited = False # flag whether QLineEdit field has been edited
        self._init_UI()

    def _init_UI(self):
        """
        Initialize User Interface
        """
        self.layVMain = QtGui.QVBoxLayout() # Widget vertical layout

        amp_units = ["dB", "V", "W"]

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
        self.cmbUnitsA.addItems(amp_units)
        self.cmbUnitsA.setObjectName("cmbUnitsA")
        self.cmbUnitsA.setToolTip("Set unit for amplitude specifications:\n"
        "dB is attenuation (positive values)\nV and W are less than 1.")

        self.cmbUnitsA.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        # fit size dynamically to largest element

        # find index for default unit from dictionary and set the unit     
        amp_idx = self.cmbUnitsA.findData(fb.fil[0]['amp_specs_unit'])
        if amp_idx < 0:
            amp_idx = 0
        self.cmbUnitsA.setCurrentIndex(amp_idx) # initialize for dBsg
        
        self.layGSpecs = QtGui.QGridLayout() # sublayout for spec fields
        self.layGSpecs.addWidget(self.lblUnits,0,0)
        self.layGSpecs.addWidget(self.cmbUnitsA,0,1, Qt.AlignLeft)

        frmMain = QtGui.QFrame()
        frmMain.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        frmMain.setLayout(self.layGSpecs)

        self.layVMain.addWidget(frmMain)
        self.layVMain.setContentsMargins(1,1,1,1)

        self.setLayout(self.layVMain)
        
        # - Build a list from all entries in the fil_dict dictionary starting
        #   with "A" (= amplitude specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget
        # ATTENTION: Entries need to be converted from QString to str for Py 2
        new_labels = [str(l) for l in fb.fil[0] if l[0] == 'A'] 
        self.update_UI(new_labels = new_labels)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmbUnitsA.currentIndexChanged.connect(self.load_entries)
        #       ^ this also triggers the initial load_entries
        # DYNAMIC SIGNAL SLOT CONNECTION:
        # Every time a field is edited, call self._store_entry and 
        # self.load_entries - this achieved with an event filter that monitors
        # the focus of the input fields. 
        #----------------------------------------------------------------------

#-------------------------------------------------------------
    def update_UI(self, new_labels = []):
        """
        Set labels and get corresponding values from filter dictionary.
        When number of entries has changed, the layout of subwidget is rebuilt,
        using

        - `self.qlabels`, a list with references to existing QLabel widgets,
        - `new_labels`, a list of strings from the filter_dict for the current
          filter design

        Install eventFilter for new QLineEdit widgets so that the filter dictionary 
        is updated automatically when a QLineEdit field has been edited.
        """

        delta_new_labels = len(new_labels) - len(self.qlabels)
        
        if delta_new_labels < 0: # less new labels, delete old ones
            self._del_entries(-delta_new_labels)

        elif delta_new_labels > 0: # more new labels, create new ones
            self._add_entries(delta_new_labels)
        
        for i in range(len(new_labels)):        
            # when entry has changed, update signal-slot connections, 
            #  label and corresponding value
                if str(self.qlineedit[i].objectName()) != new_labels[i]:
                    try:
                        self.qlineedit[i].removeEventFilter(self)
                    except TypeError:
                        pass
                    
                    self.qlabels[i].setText(rt_label(new_labels[i]))

                    self.qlineedit[i].setText(str(fb.fil[0][new_labels[i]]))
                    self.qlineedit[i].setObjectName(new_labels[i])  # update ID                    
                    self.qlineedit[i].installEventFilter(self)  # filter events 

        self.load_entries() # display filter dict entries in selected unit
        
#------------------------------------------------------------------------------

    def eventFilter(self, source, event):
        """ 
        When the focus on a QLineEdit widget changes, do the following:

        - When a QLineEdit widget gains input focus (QEvent.FocusIn`), display 
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (QEvent.FocusOut`), store 
          current value in linear format with full precision (only if 
          `spec_edited`== True) and display the stored value in selected format
   
    """
        if isinstance(source, QtGui.QLineEdit):
            if event.type() == QEvent.FocusIn:
                self.spec_edited = False
                self.load_entries()
            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True
            elif event.type() == QEvent.FocusOut:      
                self._store_entry(source)                
                
        return super(InputAmpSpecs, self).eventFilter(source, event)

        
#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Reload and reformat the amplitude textfields from filter dict when a new filter 
        design algorithm is selected or when the user has changed the unit  (V / W / dB):
        - Store the unit in the filter dictionary.
        - Reload amplitude entries from filter dictionary and convert to selected to reflect changed settings
          unit. 
        - Update the lineedit fields, rounded to specified format.          
        """
        unit = str(self.cmbUnitsA.currentText())
        fb.fil[0]['amp_specs_unit'] = unit
        
        filt_type = fb.fil[0]['ft']

        for i in range(len(self.qlineedit)):
            amp_label = str(self.qlineedit[i].objectName())
            amp_value = lin2unit(fb.fil[0][amp_label], filt_type, amp_label, unit = unit)
            
            if not self.qlineedit[i].hasFocus():
                # widget has no focus, round the display
                self.qlineedit[i].setText(self.FMT.format(amp_value))
            else:
                # widget has focus, show full precision
                self.qlineedit[i].setText(str(amp_value))
#------------------------------------------------------------------------------
    def _store_entry(self, source):
        """
        When the textfield of `source` has been edited (flag `self.spec_edited` =  True),
        transform the amplitude spec back to linear unit setting and store it 
        in filter dict. 
        This is triggered by `QEvent.focusOut`
        
        Spec entries are *always* stored in linear units; only the 
        displayed values are adapted to the amplitude unit, not the dictionary!
        """
        if self.spec_edited:
            unit = str(self.cmbUnitsA.currentText())
            filt_type = fb.fil[0]['ft']      
            amp_label = str(source.objectName())
            amp_value = simple_eval(source.text())
            fb.fil[0].update({amp_label:unit2lin(amp_value, filt_type, amp_label, unit)})                                 
            self.sigSpecsChanged.emit() # -> input_specs
        self.load_entries() 

#-------------------------------------------------------------
    def _del_entries(self, num):
        """
        Delete num subwidgets (QLabel and QLineEdit) from layout and memory
        """
        Nmax = len(self.qlabels)-1  # number of existing labels

        for i in range(Nmax, Nmax-num, -1):  # start with len, last element len - num
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

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    mainw = InputAmpSpecs(None)

    mainw.update_UI(new_labels = ['A_SB','A_SB2','A_PB','A_PB2'])
    mainw.update_UI(new_labels = ['A_PB','A_SB'])

    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())