# -*- coding: utf-8 -*-
"""
Widget for entering frequency units

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import pyfda.filterbroker as fb    

# TODO: self.cmbFRange is not updated when file is loaded from disk although
#           fb.fil[0] is updated to correct setting?

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

        self._init_UI()

    def _init_UI(self):
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
        self.lblF_S.setText(self._rt_label("f_S"))

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
        self.cmbUnits.currentIndexChanged.connect(self.update_UI)
        self.ledF_S.editingFinished.connect(self.update_UI)
        self.cmbFRange.currentIndexChanged.connect(self._freq_range)
        self.butSort.clicked.connect(self._store_sort)

        self.update_UI() # first time initialization
               

#-------------------------------------------------------------
    def update_UI(self):
        """
        Transform the displayed frequency spec input fields according to the units
        setting. Spec entries are always stored normalized w.r.t. f_S in the
        dictionary; when f_S or the unit are changed, only the displayed values
        of the frequency entries are updated, not the dictionary!

        updateUI is called during init and when
        - the f_S lineedit field has been edited or the unit combobox is changed
        
        Finally, store freqSpecsRange and emit sigFilterChanged signal via _freq_range
        """
        idx = self.cmbUnits.currentIndex() # read index of units combobox
        unit = str(self.cmbUnits.currentText())
        self.f_S = float(self.ledF_S.text()) # read sampling frequency

        self.ledF_S.setVisible(unit not in {"f_S", "f_Ny"}) # only vis. when
        self.lblF_S.setVisible(unit not in {"f_S", "f_Ny"}) # not normalized

        # get ID of signal that triggered updateUI():
        if self.sender(): # origin of signal that triggered the slot
            senderName = self.sender().objectName()
            if self.DEBUG: print(senderName + ' was triggered\n================')
        else: # no sender, updateUI has been called from initUI or another method
            senderName = ""

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

        self._freq_range() # update f_lim setting and emit sigSpecsChanged signal
        
    #-------------------------------------------------------------
    def _freq_range(self):
        """
        Set frequency range for single-sided spectrum up to f_S/2 or f_S or
        for double-sided spectrum between -f_S/2 and f_S/2 and emit
        sigSpecsChanged signal
        """
        # get ID of signal that triggered updateUI():
        if self.sender(): # origin of signal that triggered the slot
            senderName = self.sender().objectName()
            if self.DEBUG: print(senderName + ' was triggered\n================')
        else: # no sender, updateUI has been called from initUI or another method
            senderName = ""

        rangeType = self.cmbFRange.itemData(self.cmbFRange.currentIndex())
        if not isinstance(rangeType, str):
            rangeType = str(rangeType.toString()) # needed for Python 2.x

        fb.fil[0].update({'freqSpecsRangeType':rangeType})
        if rangeType == 'whole':
            f_lim = [0, self.f_S]
        elif rangeType == 'sym':
            f_lim = [-self.f_S/2, self.f_S/2]
        else:
            f_lim = [0, self.f_S/2]

        fb.fil[0]['freqSpecsRange'] = f_lim
        
        # only emit signal when _freq_range has been triggered by combobox
        if len(senderName) > 2:          
            self.sigSpecsChanged.emit() # -> input_widgets


    #-------------------------------------------------------------
    def load_entries(self):
        """
        Reload settings and textfields from filter dictionary
        """
        self.f_S = fb.fil[0]['f_S']  # read sampling frequency
        self.ledF_S.setText(str(self.f_S))

        idx = self.cmbUnits.findText(fb.fil[0]['freq_specs_unit']) # get and set
        self.cmbUnits.setCurrentIndex(idx) # index for freq. unit combo box

        idx = self.cmbFRange.findData(fb.fil[0]['freqSpecsRangeType'])
        self.cmbFRange.setCurrentIndex(idx) # set frequency range
        
        self.butSort.setChecked(fb.fil[0]['freq_specs_sort'])


    #-------------------------------------------------------------
    def _store_entries(self):
# TODO: not needed?
        """
        - Store cmbBox etc. settings in dictionary
        - Emit sigFilterChanged signal
        """
        # simply call updateUI? 
        fb.fil[0].update({'freq_specs_unit':self.cmbUnits.currentText()})
        fb.fil[0]['f_S'] = self.f_S # store f_S in dictionary
        
#-------------------------------------------------------------
    def _rt_label(self, label):
        """
        Rich text label: Format label with italic + bold HTML tags and
         replace '_' by HTML subscript tags
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

    form.update_UI()
#    form.updateUI(newLabels = ['F_PB','F_PB2'])

    form.show()

    app.exec_()
