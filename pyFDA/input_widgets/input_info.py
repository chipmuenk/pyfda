# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for displaying infos about filter and filter design method
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import textwrap
from PyQt4 import Qt, QtGui, QtWebKit
from docutils.core import publish_string #, publish_parts
import numpy as np
from numpy import pi, log10
import scipy.signal as sig
# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb # importing filterbroker initializes all its globals

# TODO: Setting the cursor position doesn't work yet
# TODO: Docstrings cannot be displayed with Py3:
#       Line 113: QTextEdit.append(str): argument 1 has unexpected type 'bytes'
class InputInfo(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = False):
        self.DEBUG = DEBUG
        super(InputInfo, self).__init__()

        self.initUI()
        self.showInfo()
        self.showFiltPerf()

    def initUI(self):
        """
        Intitialize the widget, consisting of:
        - Checkboxes for selecting the info to be displayed
        - A large text window for displaying infos about the filter design
          algorithm
        """
        self.chkFiltPerf = QtGui.QCheckBox()
        self.chkFiltPerf.setChecked(True)
        self.chkFiltPerf.setToolTip("Display filter performance at test frequencies.")
        self.lblFiltPerf = QtGui.QLabel("Performance")


        self.txtFiltPerf = QtGui.QTextBrowser()

        self.tblFiltPerf = QtGui.QTableWidget()
#        self.tblCoeff.setEditTriggers(QtGui.QTableWidget.AllEditTriggers)
        self.tblFiltPerf.setAlternatingRowColors(True)
        self.tblFiltPerf.verticalHeader().setVisible(False)
#        self.tblCoeff.QItemSelectionModel.Clear
#        self.tblCoeff.setDragEnabled(True)
#        self.tblCoeff.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.tblFiltPerf.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                          QtGui.QSizePolicy.MinimumExpanding)

#        self.tblFiltPerf = QtGui.QTextTable(self.txtFiltPerf)
#        QTextBrowser()
#        self.txtFiltPerf.setSizePolicy(QtGui.QSizePolicy.Minimum,
#                                          QtGui.QSizePolicy.Expanding)
        # widget / subwindow for filter infos
        self.chkDocstring = QtGui.QCheckBox()
        self.chkDocstring.setChecked(False)
        self.chkDocstring.setToolTip("Display docstring from python filter method.")

        self.lblDocstring = QtGui.QLabel()
        self.lblDocstring.setText("Docstring")

        self.chkRichText = QtGui.QCheckBox()
        self.chkRichText.setChecked(True)
        self.chkRichText.setToolTip("Render documentation in Rich Text Format.")

        self.lblRichText = QtGui.QLabel()
        self.lblRichText.setText("RTF")

        self.txtFiltInfoBox = QtGui.QTextBrowser()
        self.txtFiltInfoBox.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                          QtGui.QSizePolicy.Expanding)

        # ============== UI Layout =====================================
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkFiltPerf)
        self.layHChkBoxes.addWidget(self.lblFiltPerf)

        self.layHChkBoxes.addStretch(10)

        self.layHChkBoxes.addWidget(self.chkDocstring)
        self.layHChkBoxes.addWidget(self.lblDocstring)
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkRichText)
        self.layHChkBoxes.addWidget(self.lblRichText)

        self.layHChkBoxes.addStretch(10)

        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addWidget(self.tblFiltPerf)
        layVMain.addWidget(self.txtFiltInfoBox)
#        layVMain.addStretch(10)
        self.setLayout(layVMain)

        # ============== Signals & Slots ================================
        self.chkFiltPerf.clicked.connect(self.showFiltPerf)
        self.chkDocstring.clicked.connect(self.showDocs)
        self.chkRichText.clicked.connect(self.showDocs)

    def showInfo(self):
        """
        update docs and filter performance
        """
        self.showDocs()
        self.showFiltPerf()

    def showFiltPerf(self):
        """
        Print filter properties at frequencies of interest.
        """
        self.tblFiltPerf.setVisible(self.chkFiltPerf.isChecked())

        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        f_S  = fb.fil[0]['f_S']

        F_test_lbl = [l for l in fb.fil[0] if l[0] == 'F']
        F_test = np.array([fb.fil[0][l] for l in F_test_lbl]) * f_S

#        F_test = np.array([0, F_sig, 0.5]) # Vektor mit Testfrequenzen

        # Berechne Frequenzantwort bei Testfrequenzen und gebe sie aus:
        [w_test, H_test] = sig.freqz(bb, aa, F_test * 2.0 * pi)
        [w, H] = sig.freqz(bb, aa)

        f = w  * f_S / (2.0 * pi)
        H_abs = abs(H)
        H_max = max(H_abs);
        H_max_dB = 20*log10(H_max);
        F_max = f[np.argmax(H_abs)]
        #
        H_min = min(H_abs)
        H_min_dB = 20*log10(H_min)
        F_min = f[np.argmin(H_abs)]

        F_test_lbl += ['Minimum','Maximum']
        F_test = np.append(F_test, [F_min, F_max])
        H_test = np.append(H_test, [H_min, H_max])
        if self.DEBUG:
            print("input_info.showFiltPerf\n===================H_test", H_test)
            print("F_test", F_test)
#        min_dB = np.floor(max(PLT_min_dB, H_min_dB) / 10) * 10

        self.tblFiltPerf.setRowCount(len(H_test))
        self.tblFiltPerf.setColumnCount(4)

        self.tblFiltPerf.setHorizontalHeaderLabels(['Test Case', 'f(Hz)','|H(f)|','|H(f)| (dB)'])
        for row in range(len(H_test)):
            self.tblFiltPerf.setItem(row,0,QtGui.QTableWidgetItem(F_test_lbl[row]))
            self.tblFiltPerf.setItem(row,1,QtGui.QTableWidgetItem(str('{0:.4g}'.format(F_test[row]))))
            self.tblFiltPerf.setItem(row,2,QtGui.QTableWidgetItem(str('%.4g'%(abs(H_test[row])))))
            self.tblFiltPerf.setItem(row,3,QtGui.QTableWidgetItem(str('%2.3f'%(20*log10(abs(H_test[row]))))))

        self.tblFiltPerf.resizeColumnsToContents()
        self.tblFiltPerf.resizeRowsToContents()


        if self.DEBUG:
            print('============ Filter Characteristics ================\n'
                '  Test Case  |  f (Hz)    |   |H(f)|   | |H(f)| (dB)')
            print('----------------------------------------------------')
    
            for i in range(len(H_test)):
                print('{0:12} | {1:10.3f} | {2:10.6f} | {3:9.4f}'\
                    .format(F_test_lbl[i], f[i], abs(H_test[i]),
                            20*log10(abs(H_test[i]))))
            print('{0:12} | {1:10.3f} | {2:10.6f} | {3:9.4f} '\
                .format('Maximum', F_max, H_max, H_max_dB))
            print('{0:12} | {1:10.3f} | {2:10.6f} | {3:9.4f} '\
                .format('Minimum', F_min, H_min, H_min_dB))


    def showDocs(self):
        """
        Display info from filter design file and docstring
        """
        pos = self.txtFiltInfoBox.textCursor().position()
#        print(pos)

        if hasattr(fb.filObj,'info'):
            if self.chkRichText.isChecked():
                self.txtFiltInfoBox.setText(publish_string(
                    self.cleanDoc(fb.filObj.info), writer_name='html',
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
                     self.cleanDoc(doc), writer_name='html',
                        settings_overrides = {'output_encoding': 'unicode'}))
            else:
                self.txtFiltInfoBox.append('\nPython module docstring:\n')
                for doc in fb.filObj.info_doc:
                    self.txtFiltInfoBox.append(self.cleanDoc(doc))

#        self.txtFiltInfoBox.textCursor().setPosition(pos) # no effect
        self.txtFiltInfoBox.moveCursor(QtGui.QTextCursor.Start)

    def cleanDoc(self, doc):
        """
        Remove uniform number of leading blanks from docstrings for subsequent
        processing of rich text. The first line is treated differently, _all_
        leading blanks are removed (if any). This allows for different formats
        of docstrings.
        """
        lines = doc.splitlines()
        result = lines[0].lstrip() +\
         "\n" + textwrap.dedent("\n".join(lines[1:]))# + '\n'
        return result
        
        
#app = QtGui.QApplication([])
#view = QtWebKit.QWebView()
#
#class MyWebPage(QtWebKit.QWebPage):
#    def acceptNavigationRequest(self, frame, req, nav_type):
#        if nav_type == QtWebKit.QWebPage.NavigationTypeFormSubmitted:
#            text = "<br/>\n".join(["%s: %s" % pair for pair in req.url().queryItems()])
#            view.setHtml(text)
#            return False
#        else:
#            return super(MyWebPage, self).acceptNavigationRequest(frame, req, nav_type)
#
#view.setPage(MyWebPage())
#
#html = """
#<h1>Hello World!</h1>
#"""
#
#view.setHtml(html)
#
##view.setWindowFlags(Qt.FramelessWindowHint) # no title
##view.setWindowFlags(Qt.CustomizeWindowHint) # resizable frame
#
#view.show()
#app.exec_()

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputInfo()
    form.show()

    app.exec_()