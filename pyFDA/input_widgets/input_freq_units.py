# -*- coding: utf-8 -*-
"""
Widget for entering frequency units

Author: Christian Muenker
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

import filterbroker as fb    
from simpleeval import simple_eval

class InputFreqUnits(QtGui.QWidget):
    """
    Build and update widget for entering the frequency units
    """

    # class variables (shared between instances if more than one exists)
    sigSpecsChanged = pyqtSignal() # emitted when filter has been changed

    def __init__(self, DEBUG = True, title = "Frequency Units"):

        super(InputFreqUnits, self).__init__()
        self.DEBUG = DEBUG
        self.title = title

        self.initUI()

    def initUI(self):
        """
        Initialize the User Interface
        """
        self.layVMain = QtGui.QVBoxLayout() # Widget main layout

        f_units = ['f_S', 'f_Ny', 'Hz', 'kHz', 'MHz', 'GHz']
        self.t_units = ['', '', 's', 'ms', r'$\mu$s', 'ns']

        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
#        self.lblTitle = QtGui.QLabel(self) # field for widget title
#        self.lblTitle.setText(str(self.title))
#        self.lblTitle.setFont(bfont)
#        self.lblTitle.setWordWrap(True)
#        self.layVMain.addWidget(self.lblTitle)

        self.lblUnits=QtGui.QLabel(self)
        self.lblUnits.setText("Freq. Unit:")
        self.lblUnits.setFont(bfont)

        self.f_S = fb.fil[0]["f_S"]
        self.ledF_S = QtGui.QLineEdit()
        self.ledF_S.setText(str(self.f_S))
        self.ledF_S.setObjectName("f_S")

        self.lblF_S = QtGui.QLabel(self)
        self.lblF_S.setText(self._rtLabel("f_S"))

        self.cmbUnits = QtGui.QComboBox(self)
        self.cmbUnits.setObjectName("cmbUnits")
        self.cmbUnits.addItems(f_units)
        self.cmbUnits.setToolTip(
        "Select whether frequencies are specified with respect to \n"
        "the sampling frequency f_S, to the Nyquist frequency \n"
        "f_Ny = f_S/2 or as absolute values.")
        self.cmbUnits.setCurrentIndex(0)
#        self.cmbUnits.setItemData(0, (0,QtGui.QColor("#FF333D"),Qt.BackgroundColorRole))#
#        self.cmbUnits.setItemData(0, (QtGui.QFont('Verdana', bold=True), Qt.FontRole)

        fRanges = [("0...½", "half"), ("0...1","whole"), ("-½...½", "sym")]
        self.cmbFRange = QtGui.QComboBox(self)
        self.cmbFRange.setObjectName("cmbFRange")
        for f in fRanges:
            self.cmbFRange.addItem(f[0],f[1])
        self.cmbFRange.setToolTip("Select frequency range (whole or half).")
        self.cmbFRange.setCurrentIndex(0)


        # Combobox resizes with longest entry
        self.cmbUnits.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbFRange.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.butSort = QtGui.QToolButton(self)
        self.butSort.setText("Sort")
        self.butSort.setCheckable(True)
        self.butSort.setToolTip("Sort frequencies in ascending order when pushed.")
        self.butSort.setStyleSheet("QToolButton:checked {font-weight:bold}")

        self.layHUnits = QtGui.QHBoxLayout()
        self.layHUnits.addWidget(self.cmbUnits)
        self.layHUnits.addWidget(self.cmbFRange)
        self.layHUnits.addWidget(self.butSort)

        # Create a gridLayout consisting of QLabel and QLineEdit fields
        # for setting f_S, the units and the actual frequency specs:
        self.layGSpecWdg = QtGui.QGridLayout() # sublayout for spec fields
        self.layGSpecWdg.addWidget(self.lblF_S,1,0)
        self.layGSpecWdg.addWidget(self.ledF_S,1,1)
        self.layGSpecWdg.addWidget(self.lblUnits,0,0)
        self.layGSpecWdg.addLayout(self.layHUnits,0,1)

        sfFrame = QtGui.QFrame()
        sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        sfFrame.setLayout(self.layGSpecWdg)

        self.layVMain.addWidget(sfFrame)
        self.layVMain.setContentsMargins(1,1,1,1)

        self.setLayout(self.layVMain)

        # =========== SIGNALS & SLOTS =======================================
        self.cmbUnits.currentIndexChanged.connect(self.updateUI)
        self.ledF_S.editingFinished.connect(self.updateUI)
        self.cmbFRange.currentIndexChanged.connect(self.freqRange)
        self.butSort.clicked.connect(self._store_sort)

        self.updateUI() # first time initialization
               

#-------------------------------------------------------------
    def updateUI(self):
        """
        Transform the displayed frequency spec input fields according to the units
        setting. Spec entries are always stored normalized w.r.t. f_S in the
        dictionary; when f_S or the unit are changed, only the displayed values
        of the frequency entries are updated, not the dictionary!

        updateUI is called during init and when
        - the f_S lineedit field has been edited or the unit combobox is changed
        
        Finally, store freqSpecsRange and emit sigFilterChanged signal via freqRange
        """
        idx = self.cmbUnits.currentIndex() # read index of units combobox
        unit = self.cmbUnits.currentText()
        self.f_S = float(self.ledF_S.text()) # read sampling frequency

        self.ledF_S.setVisible(unit not in {"f_S", "f_Ny"}) # only vis. when
        self.lblF_S.setVisible(unit not in {"f_S", "f_Ny"}) # not normalized

        # get ID of signal that triggered updateUI():
        if self.sender(): # origin of signal that triggered the slot
            senderName = self.sender().objectName()
            if self.DEBUG: print(senderName + ' was triggered\n================')
        else: # no sender, updateUI has been called from initUI
            senderName = "cmbUnits"

        if senderName == "f_S" and self.f_S != 0:
            # f_S has been edited -> update dictionary entry for f_S and
            # change display of frequency entries via sigSpecsChanged
            fb.fil[0]['f_S'] = self.f_S

        else: # cmbUnitBox
            if unit in {"f_S", "f_Ny"}: # normalized frequency
                if unit == "f_S": # normalized to f_S
                    self.f_S = 1.
                    f_label = r"$F = f/f_S = \Omega / 2 \pi \; \rightarrow$"
                else:   # idx == 1: normalized to f_nyq = f_S / 2
                    self.f_S = 2.
                    f_label = r"$F = 2f/f_S = \Omega / \pi \; \rightarrow$"
                t_label = r"$n \; \rightarrow$"
                self.ledF_S.setText(str(self.f_S)) # update field for f_S

            else: # Hz, kHz, ...
                f_label = r"$f$ in " + unit + r"$\; \rightarrow$"
                t_label = r"$t$ in " + self.t_units[idx] + r"$\; \rightarrow$"

            fb.fil[0].update({"plt_fLabel":f_label}) # label for freq. axis
            fb.fil[0].update({"plt_tLabel":t_label}) # label for time axis
            fb.fil[0].update({'freq_specs_unit':unit})
            fb.fil[0]['f_S'] = self.f_S # store f_S in dictionary
            self.ledF_S.setText(str(self.f_S))

        self.freqRange() # update f_lim setting and emit sigSpecsChanged signal
        
    #-------------------------------------------------------------
    def freqRange(self):
        """
        Set frequency range for single-sided spectrum up to f_S/2 or f_S or
        for double-sided spectrum between -f_S/2 and f_S/2 and emit
        sigSpecsChanged signal
        """
        rangeType = self.cmbFRange.itemData(self.cmbFRange.currentIndex())
        fb.fil[0].update({'freqSpecsRangeType':rangeType})
        if rangeType == 'whole':
            f_lim = [0, self.f_S]
        elif rangeType == 'sym':
            f_lim = [-self.f_S/2, self.f_S/2]
        else:
            f_lim = [0, self.f_S/2]

        fb.fil[0]['freqSpecsRange'] = f_lim
        
        self.sigSpecsChanged.emit() # -> input_widgets


    #-------------------------------------------------------------
    def loadEntries(self):
        """
        Reload settings and textfields from filter dictionary
        """
        self.ledF_S.setText(str(fb.fil[0]['f_S'])) # read sampling frequency

        idx = self.cmbUnits.findText(fb.fil[0]['freq_specs_unit']) # find index
        self.cmbUnits.setCurrentIndex(idx)

        idx = self.cmbFRange.findData(fb.fil[0]['freqSpecsRangeType'])
        self.cmbFRange.setCurrentIndex(idx)
        
        self.butSort.setChecked(fb.fil[0]['freq_specs_sort'])


    #-------------------------------------------------------------
    def storeEntries(self):
        """
        - Store cmbBox etc. settings in dictionary
        - Emit sigFilterChanged signal
        """
        # simply call updateUI? 
        fb.fil[0].update({"plt_fLabel":f_label}) # label for freq. axis
        fb.fil[0].update({"plt_tLabel":t_label}) # label for time axis
        fb.fil[0].update({'freq_specs_unit':self.cmbUnits.currentText()})
        fb.fil[0]['f_S'] = self.f_S # store f_S in dictionary
        
#-------------------------------------------------------------
    def _rtLabel(self, label):
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
    def _store_sort(self):
        """
        Store sort flag in filter dict and emit sigSpecsChanged
        """
        fb.fil[0]['freq_specs_sort'] = self.butSort.isChecked()
        self.sigSpecsChanged.emit() # -> input_widgets

 
#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputFreqUnits() #)

    form.updateUI(newLabels = ['F_SB','F_SB2','F_PB','F_PB2'])
    form.updateUI(newLabels = ['F_PB','F_PB2'])

    form.show()

    app.exec_()
