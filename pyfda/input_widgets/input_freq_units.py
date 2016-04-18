# -*- coding: utf-8 -*-
"""
Widget for entering frequency units

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import rt_label


class InputFreqUnits(QtGui.QWidget):
    """
    Build and update widget for entering the frequency units
    """

    # class variables (shared between instances if more than one exists)
    sigUnitChanged = pyqtSignal() # emitted when frequency unit has been changed
    sigSpecsChanged = pyqtSignal() # emitted when frequency specs have been changed
                                  # (e.g. when the sort button has been pushed)

    def __init__(self, parent, title = "Frequency Units"):

        super(InputFreqUnits, self).__init__(parent)
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

        self.lblUnits=QtGui.QLabel(self)
        self.lblUnits.setText("Freq. Unit:")
        self.lblUnits.setFont(bfont)

        self.f_S = fb.fil[0]["f_S"]
        self.ledF_S = QtGui.QLineEdit()
        self.ledF_S.setText(str(self.f_S))
        self.ledF_S.setObjectName("f_S")

        self.lblF_S = QtGui.QLabel(self)
        self.lblF_S.setText(rt_label("f_S"))

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
        self.butSort.setChecked(True)
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

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmbUnits.currentIndexChanged.connect(self.update_UI)
        self.ledF_S.editingFinished.connect(self.update_UI)
        self.cmbFRange.currentIndexChanged.connect(self._freq_range)
        self.butSort.clicked.connect(self._store_sort_flag)
        #----------------------------------------------------------------------


        self.update_UI() # first time initialization


#-------------------------------------------------------------
    def update_UI(self):
        """
        Transform the displayed frequency spec input fields according to the units
        setting. Spec entries are always stored normalized w.r.t. f_S in the
        dictionary; when f_S or the unit are changed, only the displayed values
        of the frequency entries are updated, not the dictionary!
        Signals are blocked before changing the value for f_S programmatically


        updateUI is called during init and when
        - the f_S lineedit field has been edited or the unit combobox is changed
        
        Finally, store freqSpecsRange and emit sigUnitChanged signal via _freq_range
        """
        idx = self.cmbUnits.currentIndex() # read index of units combobox
        f_unit = str(self.cmbUnits.currentText()) # and the label
        fb.fil[0].update({'freq_specs_unit':f_unit}) # and store it in dict
        
        self.f_S = float(self.ledF_S.text()) # read sampling frequency

        self.ledF_S.setVisible(f_unit not in {"f_S", "f_Ny"}) # only vis. when
        self.lblF_S.setVisible(f_unit not in {"f_S", "f_Ny"}) # not normalized

        # get ID of signal that triggered updateUI():
        if self.sender(): # origin of signal that triggered the slot
            senderName = self.sender().objectName()
            logger.debug(senderName + ' was triggered\n================')
        else: # no sender, updateUI has been called from initUI or another method
            senderName = ""

        if senderName == "f_S" and self.f_S != 0:
            # f_S has been edited -> update dictionary entry for f_S and
            # change display of frequency entries via sigSpecsChanged
            fb.fil[0]['f_S'] = self.f_S

        else: # cmbUnitBox
            if f_unit in {"f_S", "f_Ny"}: # normalized frequency
                if f_unit == "f_S": # normalized to f_S
                    self.f_S = 1.
                    f_label = r"$F = f/f_S = \Omega / 2 \pi \; \rightarrow$"
                else:   # idx == 1: normalized to f_nyq = f_S / 2
                    self.f_S = 2.
                    f_label = r"$F = 2f/f_S = \Omega / \pi \; \rightarrow$"
                t_label = r"$n \; \rightarrow$"
                
                self.ledF_S.setText(str(self.f_S)) # update field for f_S
                fb.fil[0]['f_S'] = self.f_S # store f_S in dictionary
            else: # Hz, kHz, ...
                f_label = r"$f$ in " + f_unit + r"$\; \rightarrow$"
                t_label = r"$t$ in " + self.t_units[idx] + r"$\; \rightarrow$"

            fb.fil[0].update({"plt_fLabel":f_label}) # label for freq. axis
            fb.fil[0].update({"plt_tLabel":t_label}) # label for time axis
            fb.fil[0].update({"plt_fUnit":f_unit}) # frequency unit as string
            fb.fil[0].update({"plt_tUnit":self.t_units[idx]}) # time unit as string


        self._freq_range() # update f_lim setting and emit sigUnitChanged signal
        
    #-------------------------------------------------------------
    def _freq_range(self):
        """
        Set frequency range for single-sided spectrum up to f_S/2 or f_S or
        for double-sided spectrum between -f_S/2 and f_S/2 and emit
        sigUnitChanged signal
        """
        # get ID of signal that triggered updateUI():
        if self.sender(): # origin of signal that triggered the slot
            senderName = self.sender().objectName()
            logger.debug(senderName + ' was triggered\n================')
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
            self.sigUnitChanged.emit() # -> input_widgets


    #-------------------------------------------------------------
    def load_entries(self):
        """
        Reload comboBox settings and textfields from filter dictionary
        Block signals during update of combobox / lineedit widgets
        """
        self.ledF_S.setText(str(fb.fil[0]['f_S']))

        self.cmbUnits.blockSignals(True)
        idx = self.cmbUnits.findText(fb.fil[0]['freq_specs_unit']) # get and set
        self.cmbUnits.setCurrentIndex(idx) # index for freq. unit combo box
        self.cmbUnits.blockSignals(False)

        self.cmbFRange.blockSignals(True)
        idx = self.cmbFRange.findData(fb.fil[0]['freqSpecsRangeType'])
        self.cmbFRange.setCurrentIndex(idx) # set frequency range
        self.cmbFRange.blockSignals(False)
        
        self.butSort.blockSignals(True)
        self.butSort.setChecked(fb.fil[0]['freq_specs_sort'])
        self.butSort.blockSignals(False)


#-------------------------------------------------------------
    def _store_sort_flag(self):
        """
        Store sort flag in filter dict and emit sigSpecsChanged
        when sort button is checked.
        """
        fb.fil[0]['freq_specs_sort'] = self.butSort.isChecked()
        if self.butSort.isChecked():
            self.sigSpecsChanged.emit() # -> input_widgets

 
#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputFreqUnits(None) #)

    form.update_UI()
#    form.updateUI(newLabels = ['F_PB','F_PB2'])

    form.show()

    app.exec_()
