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
from pyfda.compat import (QWidget, QFont, QLabel, QComboBox,
                     QFrame, QCheckBox, 
                     QPushButton, QVBoxLayout, QHBoxLayout)

#------------------------------------------------------------------------------
class CSV_option_box(QWidget):
    def __init__(self, parent):
        super(CSV_option_box, self).__init__(parent)
        
        QWidget.__init__(self)
        
        self.parent = parent # instance of the parent (not the base) class

        lblDelimiter = QLabel("CSV-Delimiter:")
        delim = [('Auto','auto'), (',',','), (';', ';'), ('<TAB>', '\t'), ('<SPACE>', ' '), ('|', '|')]
        self.cmbDelimiter = QComboBox(self)
        for d in delim:
            self.cmbDelimiter.addItem(d[0],d[1])
        self.cmbDelimiter.setToolTip("Delimiter between data fields.")
        qset_cmb_box(self.cmbDelimiter, params['CSV']['delimiter'], data=True)

        lblTerminator = QLabel("Line Terminator:")
        terminators = [('Auto','auto'), ('CRLF (Win)', '\r\n'), ('CR (Mac)', '\r'), ('LF (Unix)', '\n')]
                
        self.cmbLineTerminator = QComboBox(self)
        self.cmbLineTerminator.setToolTip("<span>Terminator at the end of a data row."
                " This depends a.o. on the operating system.")
        for t in terminators:
            self.cmbLineTerminator.addItem(t[0], t[1])
        qset_cmb_box(self.cmbLineTerminator, params['CSV']['lineterminator'], data=True)        

        self.chkHorizontal = QCheckBox("Horizontal orientation", self)
        # self.chkHorizontal.setFont(self.bifont)
        self.chkHorizontal.setToolTip("<span>Set horizontal orientation of table"
                    " (transposed).</span>")
        self.chkHorizontal.setChecked(params['CSV']['horizontal'])

        butClose = QPushButton(self)
        butClose.setText("Close")
#        butClose.setDefault(self, True)  
        layDelimiter = QHBoxLayout()
        layDelimiter.addWidget(lblDelimiter)  
        layDelimiter.addWidget(self.cmbDelimiter)
        
        layLineTerminator = QHBoxLayout()
        layLineTerminator.addWidget(lblTerminator)
        layLineTerminator.addWidget(self.cmbLineTerminator)
        
        layVMain = QVBoxLayout()
        # layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addLayout(layDelimiter)
        layVMain.addLayout(layLineTerminator)
        layVMain.addWidget(self.chkHorizontal)
        layVMain.addWidget(butClose)
        layVMain.setContentsMargins(*params['wdg_margins'])
#        layVMain.addStretch(1)
        self.setLayout(layVMain) 

        # ============== Signals & Slots ================================
        butClose.clicked.connect(self.close)
        self.chkHorizontal.clicked.connect(self._store_settings)
        self.cmbDelimiter.currentIndexChanged.connect(self._store_settings)
        self.cmbLineTerminator.currentIndexChanged.connect(self._store_settings)
        self.cmbHeader.currentIndexChanged.connect(self._store_settings)
       

    def _store_settings(self):
        try:
            params['CSV']['horizontal'] =  self.chkHorizontal.isChecked()
            params['CSV']['delimiter'] = qget_cmb_box(self.cmbDelimiter, data=True)
            params['CSV']['lineterminator'] = qget_cmb_box(self.cmbLineTerminator, data=True)
            params['CSV']['header'] = qget_cmb_box(self.cmbHeader, data=True)
           
        except KeyError as e:
            logger.error(e)
            
        except KeyError as e:
            logger.error(e)

#==============================================================================


if __name__=='__main__':
    pass
