# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Subwidget for entering frequency units
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

from ..compat import (QtCore,
                      QWidget, QLabel, QLineEdit, QComboBox, QFrame, QFont, QToolButton,
                      QVBoxLayout, QHBoxLayout, QGridLayout,
                      pyqtSignal, QEvent)


import pyfda.filterbroker as fb
from pyfda.pyfda_lib import to_html, safe_eval
from pyfda.pyfda_qt_lib import qget_cmb_box
from pyfda.pyfda_rc import params # FMT string for QLineEdit fields, e.g. '{:.3g}'


class FreqUnits(QWidget):
    """
    Build and update widget for entering the frequency units
    """

    # class variables (shared between instances if more than one exists)
    sig_tx = pyqtSignal(object) # outgoing

    def __init__(self, parent, title = "Frequency Units"):

        super(FreqUnits, self).__init__(parent)
        self.title = title
        self.spec_edited = False # flag whether QLineEdit field has been edited

        self._construct_UI()

    def _construct_UI(self):
        """
        Construct the User Interface
        """
        self.layVMain = QVBoxLayout() # Widget main layout

        f_units = ['f_S', 'f_Ny', 'Hz', 'kHz', 'MHz', 'GHz']
        self.t_units = ['', '', 's', 'ms', r'$\mu$s', 'ns']

        bfont = QFont()
        bfont.setBold(True)

        self.lblUnits=QLabel(self)
        self.lblUnits.setText("Freq. Unit:")
        self.lblUnits.setFont(bfont)

        self.fs_old = fb.fil[0]['f_S'] # store current sampling frequency
        self.ledF_S = QLineEdit()
        self.ledF_S.setText(str(fb.fil[0]["f_S"]))
        self.ledF_S.setObjectName("f_S")
        self.ledF_S.installEventFilter(self)  # filter events

        self.lblF_S = QLabel(self)
        self.lblF_S.setText(to_html("f_S", frmt='bi'))

        self.cmbUnits = QComboBox(self)
        self.cmbUnits.setObjectName("cmbUnits")
        self.cmbUnits.addItems(f_units)
        self.cmbUnits.setToolTip(
        "Select whether frequencies are specified with respect to \n"
        "the sampling frequency f_S, to the Nyquist frequency \n"
        "f_Ny = f_S/2 or as absolute values.")
        self.cmbUnits.setCurrentIndex(0)
#        self.cmbUnits.setItemData(0, (0,QColor("#FF333D"),Qt.BackgroundColorRole))#
#        self.cmbUnits.setItemData(0, (QFont('Verdana', bold=True), Qt.FontRole)

        fRanges = [("0...½", "half"), ("0...1","whole"), ("-½...½", "sym")]
        self.cmbFRange = QComboBox(self)
        self.cmbFRange.setObjectName("cmbFRange")
        for f in fRanges:
            self.cmbFRange.addItem(f[0],f[1])
        self.cmbFRange.setToolTip("Select frequency range (whole or half).")
        self.cmbFRange.setCurrentIndex(0)

        # Combobox resizes with longest entry
        self.cmbUnits.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbFRange.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.butSort = QToolButton(self)
        self.butSort.setText("Sort")
        self.butSort.setCheckable(True)
        self.butSort.setChecked(True)
        self.butSort.setToolTip("Sort frequencies in ascending order when pushed.")
        self.butSort.setStyleSheet("QToolButton:checked {font-weight:bold}")

        self.layHUnits = QHBoxLayout()
        self.layHUnits.addWidget(self.cmbUnits)
        self.layHUnits.addWidget(self.cmbFRange)
        self.layHUnits.addWidget(self.butSort)

        # Create a gridLayout consisting of QLabel and QLineEdit fields
        # for setting f_S, the units and the actual frequency specs:
        self.layGSpecWdg = QGridLayout() # sublayout for spec fields
        self.layGSpecWdg.addWidget(self.lblF_S,1,0)
        self.layGSpecWdg.addWidget(self.ledF_S,1,1)
        self.layGSpecWdg.addWidget(self.lblUnits,0,0)
        self.layGSpecWdg.addLayout(self.layHUnits,0,1)

        frmMain = QFrame(self)
        frmMain.setLayout(self.layGSpecWdg)

        self.layVMain.addWidget(frmMain)
        self.layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(self.layVMain)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
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

        Finally, store freqSpecsRange and emit 'view_changed' signal via _freq_range
        """
        idx = self.cmbUnits.currentIndex() # read index of units combobox
        f_unit = str(self.cmbUnits.currentText()) # and the label

        self.ledF_S.setVisible(f_unit not in {"f_S", "f_Ny"}) # only vis. when
        self.lblF_S.setVisible(f_unit not in {"f_S", "f_Ny"}) # not normalized

        if f_unit in {"f_S", "f_Ny"}: # normalized frequency
            self.fs_old = fb.fil[0]['f_S'] # store current sampling frequency
            if f_unit == "f_S": # normalized to f_S
                fb.fil[0]['f_S'] = 1.
                f_label = r"$F = f\, /\, f_S = \Omega \, /\,  2 \mathrm{\pi} \; \rightarrow$"
            else:   # idx == 1: normalized to f_nyq = f_S / 2
                fb.fil[0]['f_S'] = 2.
                f_label = r"$F = 2f \, / \, f_S = \Omega \, / \, \mathrm{\pi} \; \rightarrow$"
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
          display the stored value in selected format. Emit 'view_changed':'f_S'
        """
        def _store_entry():
            """
            Update filter dictionary, set line edit entry with reduced precision
            again.
            """
            if self.spec_edited:
                fb.fil[0].update({'f_S':safe_eval(source.text(), fb.fil[0]['f_S'])})
                # TODO: ?!
                self._freq_range(emit_sig_range = False) # update plotting range 
                self.sig_tx.emit({'sender':__name__, 'view_changed':'f_S'})
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
        return super(FreqUnits, self).eventFilter(source, event)

    #-------------------------------------------------------------
    def _freq_range(self, emit_sig_range = True):
        """
        Set frequency plotting range for single-sided spectrum up to f_S/2 or f_S
        or for double-sided spectrum between -f_S/2 and f_S/2 and emit
        'view_changed':'f_range'.
        """
        rangeType = qget_cmb_box(self.cmbFRange)

        fb.fil[0].update({'freqSpecsRangeType':rangeType})
        if rangeType == 'whole':
            f_lim = [0, fb.fil[0]["f_S"]]
        elif rangeType == 'sym':
            f_lim = [-fb.fil[0]["f_S"]/2., fb.fil[0]["f_S"]/2.]
        else:
            f_lim = [0, fb.fil[0]["f_S"]/2.]

        fb.fil[0]['freqSpecsRange'] = f_lim # store settings in dict

        self.sig_tx.emit({'sender':__name__, 'view_changed':'f_range'})

    #-------------------------------------------------------------
    def load_dict(self):
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
        Store sort flag in filter dict and emit 'specs_changed':'f_sort'
        when sort button is checked.
        """
        fb.fil[0]['freq_specs_sort'] = self.butSort.isChecked()
        if self.butSort.isChecked():
            self.sig_tx.emit({'sender':__name__, 'specs_changed':'f_sort'})

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    form = FreqUnits(None)

    form.update_UI()
#    form.updateUI(newLabels = ['F_PB','F_PB2'])

    form.show()

    app.exec_()
