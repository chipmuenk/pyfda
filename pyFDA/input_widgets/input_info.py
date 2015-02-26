# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying infos about filter and filter design method
"""
from __future__ import print_function, division, unicode_literals
import sys, os
import textwrap
from PyQt4 import QtGui
#import scipy.io
from scipy.signal import remez
#import numpy as np
from docutils.core import publish_string, publish_parts
# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb # importing filterbroker initializes all its globals

# TODO: Setting the cursor position doesn't work yet
class InputInfo(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputInfo, self).__init__()

        self.initUI()
        self.showInfo()
        
    def initUI(self): 
        """
        Intitialize the widget, consisting of:
        - Checkboxes for selecting the info to be displayed
        - A large text window for displaying infos about the filter design 
          algorithm
        """
        # widget / subwindow for filter infos
        self.chkDocstring = QtGui.QCheckBox()
        self.chkDocstring.setChecked(False)
        self.chkDocstring.setToolTip("Display docstring from python filter method.")

        self.lblDocstring = QtGui.QLabel()
        self.lblDocstring.setText("Show Docstring")
        
        self.chkRichText = QtGui.QCheckBox()
        self.chkRichText.setChecked(True)
        self.chkRichText.setToolTip("Render documentation as Rich Text.")

        self.lblRichText = QtGui.QLabel()
        self.lblRichText.setText("Rich text")
        
        self.txtFiltInfoBox = QtGui.QTextBrowser()
        self.txtFiltInfoBox.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                          QtGui.QSizePolicy.Expanding)
        
        # ============== UI Layout =====================================
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkDocstring)
        self.layHChkBoxes.addWidget(self.lblDocstring)
        self.layHChkBoxes.addStretch(10)        
        self.layHChkBoxes.addWidget(self.chkRichText)
        self.layHChkBoxes.addWidget(self.lblRichText)

        self.layHChkBoxes.addStretch(10)

        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addWidget(self.txtFiltInfoBox)
#        layVMain.addStretch(10)
        self.setLayout(layVMain)
        
        # ============== Signals & Slots ================================
        self.chkDocstring.clicked.connect(self.showInfo)     
        self.chkRichText.clicked.connect(self.showInfo)     

        
    def showInfo(self):
        """
        Display info from filter design file and docstring
        """
        
        pos = self.txtFiltInfoBox.textCursor().position()
#        print(pos)
        
        if hasattr(fb.filObj,'info'):
            if self.chkRichText.isChecked():
                self.txtFiltInfoBox.setText(publish_string(
                    textwrap.dedent(fb.filObj.info), writer_name='html', 
                    settings_overrides={'output_encoding': 'unicode'}))
            else:
                self.txtFiltInfoBox.setText(textwrap.dedent(fb.filObj.info))

                
        else:
            self.txtFiltInfoBox.setText("")

            
        if self.chkDocstring.isChecked() and hasattr(fb.filObj,'info_doc'):
            if self.chkRichText.isChecked():
                self.txtFiltInfoBox.append(
                '<hr /><b>Python module docstring:</b>\n')
                for doc in fb.filObj.info_doc:
                    self.txtFiltInfoBox.append(publish_string(
                     self.cleanDoc(doc), writer_name='html'))
            else:
                self.txtFiltInfoBox.append('\nPython module docstring:\n')
                for doc in fb.filObj.info_doc:
                    self.txtFiltInfoBox.append(self.cleanDoc(doc))

#                self.txtFiltInfoBox.append(textwrap.dedent(fb.filObj.info_doc))

#
#                self.txtFiltInfoBox.append(publish_string(
#                    textwrap.dedent(fb.filObj.info_doc), writer_name='html'))

#        self.txtFiltInfoBox.textCursor().setPosition(pos) # no effect
        self.txtFiltInfoBox.moveCursor(QtGui.QTextCursor.Start)
        
    def cleanDoc(self, doc):
        lines = doc.splitlines()
        result = lines[0].lstrip() +\
         "\n" + textwrap.dedent("\n".join(lines[1:]))# + '\n'
        return result

#------------------------------------------------------------------------------
   
if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputInfo()
    form.show()
   
    app.exec_()