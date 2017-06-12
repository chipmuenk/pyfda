# -*- coding: utf-8 -*-
"""
Created 2012 - 2017

@author: Christian Muenker

Popup box for setting CSV-File and clipboard options
"""

from __future__ import division, print_function
import logging
logger = logging.getLogger(__name__)

#import csv

from pyfda.pyfda_rc import params
from pyfda.pyfda_qt_lib import qget_cmb_box, qset_cmb_box
from pyfda.compat import (Qt, pyqtSignal,
        QDialog, QFont, QLabel, QComboBox, QFrame, QCheckBox, 
                     QPushButton, QVBoxLayout, QHBoxLayout)

#------------------------------------------------------------------------------
class CSV_option_box(QDialog):

    def __init__(self, parent):
        super(CSV_option_box, self).__init__(parent)    
        self._init_UI()

    def _init_UI(self):
        """ initialize the User Interface """
        self.setWindowTitle("CSV Options")
        lblDelimiter = QLabel("CSV-Delimiter:", self)
        delim = [('Auto','auto'), ('< , >',','), ('< ; >', ';'), ('<TAB>', '\t'), ('<SPACE>', ' '), ('< | >', '|')]
        self.cmbDelimiter = QComboBox(self)
        for d in delim:
            self.cmbDelimiter.addItem(d[0],d[1])
        self.cmbDelimiter.setToolTip("Delimiter between data fields.")

        lblTerminator = QLabel("Line Terminator:", self)
        terminator = [('Auto','auto'), ('CRLF (Win)', '\r\n'), ('CR (Mac)', '\r'), ('LF (Unix)', '\n')]
        self.cmbLineTerminator = QComboBox(self)
        self.cmbLineTerminator.setToolTip("<span>Terminator at the end of a data row."
                " (depending on the operating system).")
        for t in terminator:
            self.cmbLineTerminator.addItem(t[0], t[1])

        butClose = QPushButton(self)
        butClose.setText("Close")
#        butClose.setDefault(self, True)  
        layHDelimiter = QHBoxLayout()
        layHDelimiter.addWidget(lblDelimiter)  
        layHDelimiter.addWidget(self.cmbDelimiter)
        
        layHLineTerminator = QHBoxLayout()
        layHLineTerminator.addWidget(lblTerminator)
        layHLineTerminator.addWidget(self.cmbLineTerminator)

        lblOrientation = QLabel("Table orientation", self)
        orientation = [('Auto/Vert.', 'auto'), ('Vertical', 'vert'), ('Horizontal', 'horiz')]
        self.cmbOrientation = QComboBox(self)
        self.cmbOrientation.setToolTip("<span>Select orientation of table.</span>")
        for o in orientation:
            self.cmbOrientation.addItem(o[0], o[1])
        
        layHOrientation = QHBoxLayout()
        layHOrientation.addWidget(lblOrientation)
        layHOrientation.addWidget(self.cmbOrientation)

                    
        lblHeader = QLabel("Enable header", self)
        header = [('Auto', 'auto'), ('On', 'on'), ('Off', 'off')]
        self.cmbHeader = QComboBox(self)
        self.cmbHeader.setToolTip("First row is a header.")
        for h in header:
            self.cmbHeader.addItem(h[0], h[1])
        layHHeader = QHBoxLayout()
        layHHeader.addWidget(lblHeader)
        layHHeader.addWidget(self.cmbHeader)
        
        layVMain = QVBoxLayout()
        # layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addLayout(layHDelimiter)
        layVMain.addLayout(layHLineTerminator)
        layVMain.addLayout(layHOrientation)
        layVMain.addLayout(layHHeader)
        layVMain.addWidget(butClose)
        layVMain.setContentsMargins(*params['wdg_margins'])
#        layVMain.addStretch(1)
        self.setLayout(layVMain)
        
        self._load_settings()

        # ============== Signals & Slots ================================
        butClose.clicked.connect(self.close)
        self.cmbOrientation.currentIndexChanged.connect(self._store_settings)
        self.cmbDelimiter.currentIndexChanged.connect(self._store_settings)
        self.cmbLineTerminator.currentIndexChanged.connect(self._store_settings)
        self.cmbHeader.currentIndexChanged.connect(self._store_settings)
       

    def _store_settings(self):
        try:
            params['CSV']['orientation'] =  qget_cmb_box(self.cmbOrientation, data=True)
            params['CSV']['delimiter'] = qget_cmb_box(self.cmbDelimiter, data=True)
            params['CSV']['lineterminator'] = qget_cmb_box(self.cmbLineTerminator, data=True)
            params['CSV']['header'] = qget_cmb_box(self.cmbHeader, data=True)

        except KeyError as e:
            logger.error(e)

    def _load_settings(self):
        """
        Load settings of all widgets from `pyfda_rc`.
        """
        try:
            qset_cmb_box(self.cmbDelimiter, params['CSV']['delimiter'], data=True)
            qset_cmb_box(self.cmbLineTerminator, params['CSV']['lineterminator'], data=True)
            qset_cmb_box(self.cmbHeader, params['CSV']['header'], data=True)
            qset_cmb_box(self.cmbOrientation, params['CSV']['orientation'], data=True)

        except KeyError as e:
            logger.error(e)
            

#==============================================================================


if __name__=='__main__':
    from ..compat import QApplication
    import sys
    app = QApplication(sys.argv)
    mainw = CSV_option_box(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
