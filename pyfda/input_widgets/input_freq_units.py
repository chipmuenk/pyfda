# -*- coding: utf-8 -*-
"""
Widget for entering frequency units

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSignal, QEvent

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import rt_label
from pyfda.pyfda_rc import params # FMT string for QLineEdit fields, e.g. '{:.3g}'
from pyfda.simpleeval import simple_eval


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
        self.spec_edited = False # flag whether QLineEdit field has been edited

        self._construct_UI()

    def _construct_UI(self):
        """
        Construct the User Interface
        """
        self.layVMain = QtGui.QVBoxLayout() # Widget main layout

        f_units = ['f_S', 'f_Ny', 'Hz', 'kHz', 'MHz', 'GHz']
        self.t_units = ['', '', 's', 'ms', r'$\mu$s', 'ns']

        bfont = QtGui.QFont()
        bfont.setBold(True)

        self.lblUnits=QtGui.QLabel(self)
        self.lblUnits.setText("Freq. Unit:")
        self.lblUnits.setFont(bfont)

        self.fs_old = fb.fil[0]['f_S'] # store current sampling frequency
        self.ledF_S = QtGui.QLineEdit()
        self.ledF_S.setText(str(fb.fil[0]["f_S"]))
        self.ledF_S.setObjectName("f_S")
        self.ledF_S.installEventFilter(self)  # filter events

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
        self.cmbFRange.currentIndexChanged.connect(self._freq_range)
        self.butSort.clicked.connect(self._store_sort_flag)
        #----------------------------------------------------------------------

        self.update_UI() # first-time initialization


#-------------------------------------------------------------
    def update_UI(self):
        """
        Transform the displayed frequency spec input fields according to the units
        setting. Spec entries are always stored normalized w.r.t. f_S in the
        dictionary; when f_S or the unit are changed, only the displayed values
        of the frequency entries are updated, not the dictionary!
        Signals are blocked before changing the value for f_S programmatically

        update_UI is called
        - during init
        - when the unit combobox is changed

        Finally, store freqSpecsRange and emit sigUnitChanged signal via _freq_range
        """
        idx = self.cmbUnits.currentIndex() # read index of units combobox
        f_unit = str(self.cmbUnits.currentText()) # and the label

        self.ledF_S.setVisible(f_unit not in {"f_S", "f_Ny"}) # only vis. when
        self.lblF_S.setVisible(f_unit not in {"f_S", "f_Ny"}) # not normalized

        if f_unit in {"f_S", "f_Ny"}: # normalized frequency
            self.fs_old = fb.fil[0]['f_S'] # store current sampling frequency
            if f_unit == "f_S": # normalized to f_S
                fb.fil[0]['f_S'] = 1.
                f_label = r"$F = f/f_S = \Omega / 2 \pi \; \rightarrow$"
            else:   # idx == 1: normalized to f_nyq = f_S / 2
                fb.fil[0]['f_S'] = 2.
                f_label = r"$F = 2f/f_S = \Omega / \pi \; \rightarrow$"
            t_label = r"$n \; \rightarrow$"

            self.ledF_S.setText(params['FMT'].format(fb.fil[0]['f_S']))

        else: # Hz, kHz, ...
            if fb.fil[0]['freq_specs_unit'] in {"f_S", "f_Ny"}: # previous setting
                fb.fil[0]['f_S'] = self.fs_old # restore prev. sampling frequency
                self.ledF_S.setText(params['FMT'].format(fb.fil[0]['f_S']))

            f_label = r"$f$ in " + f_unit + r"$\; \rightarrow$"
            t_label = r"$t$ in " + self.t_units[idx] + r"$\; \rightarrow$"

        fb.fil[0].update({'freq_specs_unit':f_unit}) # frequency unit
        fb.fil[0].update({"plt_fLabel":f_label}) # label for freq. axis
        fb.fil[0].update({"plt_tLabel":t_label}) # label for time axis
        fb.fil[0].update({"plt_fUnit":f_unit}) # frequency unit as string
        fb.fil[0].update({"plt_tUnit":self.t_units[idx]}) # time unit as string

        self._freq_range() # update f_lim setting and emit sigUnitChanged signal

#------------------------------------------------------------------------------

    def eventFilter(self, source, event):
        
        """
        Filter all events generated by the QLineEdit widgets. Source and type
        of all events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (QEvent.FocusIn`), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (QEvent.FocusOut`), store
          current value with full precision (only if `spec_edited`== True) and
          display the stored value in selected format. Emit sigSpecsChanged
          signal and a sigUnitsChanged signals
        """
        def _store_entry():
            """
            Update filter dictionary, set line edit entry with reduced precision
            again.
            """
            if self.spec_edited:
                fb.fil[0].update({'f_S':simple_eval(source.text())})
                self._freq_range(emit_sig_range = False) # update plotting range
                self.sigSpecsChanged.emit() # -> input_widgets
                self.spec_edited = False # reset flag, changed entry has been saved

        if source.objectName() == 'f_S':
            if event.type() == QEvent.FocusIn:
                self.spec_edited = False
                source.setText(str(fb.fil[0]['f_S'])) # full precision
            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True # entry has been changed
                key = event.key()
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}:
                    _store_entry()
                elif key == QtCore.Qt.Key_Escape: # revert changes
                    self.spec_edited = False                    
                    source.setText(str(fb.fil[0]['f_S'])) # full precision

            elif event.type() == QEvent.FocusOut:
                _store_entry()
                source.setText(params['FMT'].format(fb.fil[0]['f_S'])) # reduced precision
        # Call base class method to continue normal event processing:
        return super(InputFreqUnits, self).eventFilter(source, event)


    #-------------------------------------------------------------
    def _freq_range(self, emit_sig_range = True):
        """
        Set frequency plotting range for single-sided spectrum up to f_S/2 or f_S
        or for double-sided spectrum between -f_S/2 and f_S/2 and emit
        sigUnitChanged signal
        """

        rangeType = self.cmbFRange.itemData(self.cmbFRange.currentIndex())
        if not isinstance(rangeType, str):
            rangeType = str(rangeType.toString()) # needed for Python 2.x

        fb.fil[0].update({'freqSpecsRangeType':rangeType})
        if rangeType == 'whole':
            f_lim = [0, fb.fil[0]["f_S"]]
        elif rangeType == 'sym':
            f_lim = [-fb.fil[0]["f_S"]/2., fb.fil[0]["f_S"]/2.]
        else:
            f_lim = [0, fb.fil[0]["f_S"]/2.]

        fb.fil[0]['freqSpecsRange'] = f_lim # store settings in dict

        self.sigUnitChanged.emit() # -> input_widgets


    #-------------------------------------------------------------
    def load_entries(self):
        """
        Reload comboBox settings and textfields from filter dictionary
        Block signals during update of combobox / lineedit widgets
        """
        self.ledF_S.setText(params['FMT'].format(fb.fil[0]['f_S']))

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
