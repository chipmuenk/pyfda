# -*- coding: utf-8 -*-
"""
Widget for displaying infos about filter and filter design method

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import textwrap
from PyQt4 import Qt, QtGui, QtWebKit
from docutils.core import publish_string #, publish_parts
import pprint
import numpy as np
from numpy import pi, log10
import scipy.signal as sig
# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

# TODO: Docstrings cannot be displayed with Py3:
#       Line 113: QTextEdit.append(str): argument 1 has unexpected type 'bytes'
# TODO: Passband and stopband info should show min / max values for each band
class InputInfo(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = False):
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
        self.chkFiltPerf = QtGui.QCheckBox("H(f)")
        self.chkFiltPerf.setChecked(True)
        self.chkFiltPerf.setToolTip("Display frequency response at test frequencies.")

        self.txtFiltPerf = QtGui.QTextBrowser()
        self.txtFiltDict = QtGui.QTextBrowser()

        bfont = QtGui.QFont()
        bfont.setBold(True)
        self.tblFiltPerf = QtGui.QTableWidget()
        self.tblFiltPerf.setColumnCount(4)
        self.tblFiltPerf.setAlternatingRowColors(True)
#        self.tblFiltPerf.verticalHeader().setVisible(False)
        self.tblFiltPerf.horizontalHeader().setHighlightSections(False)
        self.tblFiltPerf.horizontalHeader().setFont(bfont)
        self.tblFiltPerf.verticalHeader().setHighlightSections(False)
        self.tblFiltPerf.verticalHeader().setFont(bfont)
        
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
        self.chkDocstring = QtGui.QCheckBox("Doc$")
        self.chkDocstring.setChecked(False)
        self.chkDocstring.setToolTip("Display docstring from python filter method.")

        self.chkRichText = QtGui.QCheckBox("RTF")
        self.chkRichText.setChecked(True)
        self.chkRichText.setToolTip("Render documentation in Rich Text Format.")

        self.txtFiltInfoBox = QtGui.QTextBrowser()
        self.txtFiltInfoBox.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,
                                          QtGui.QSizePolicy.Expanding)
                                          
        self.chkFiltDict = QtGui.QCheckBox("FiltDict")
        self.chkFiltDict.setToolTip("Show filter dictionary for debugging.")

        self.txtFiltDict = QtGui.QTextBrowser()
        self.txtFiltDict.setSizePolicy(QtGui.QSizePolicy.Minimum,
                                          QtGui.QSizePolicy.Expanding)


        # ============== UI Layout =====================================
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkFiltPerf)
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkDocstring)
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkRichText)
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkFiltDict)

        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addWidget(self.tblFiltPerf)
        layVMain.addWidget(self.txtFiltInfoBox)
        layVMain.addWidget(self.txtFiltDict)
#        layVMain.addStretch(10)
        self.setLayout(layVMain)

        # ============== Signals & Slots ================================
        self.chkFiltPerf.clicked.connect(self.showFiltPerf)
        self.chkFiltDict.clicked.connect(self.showFiltDict)
        self.chkDocstring.clicked.connect(self.showDocs)
        self.chkRichText.clicked.connect(self.showDocs)

    def showInfo(self):
        """
        update docs and filter performance
        """
        self.showDocs()
        self.showFiltPerf()
        self.showFiltDict()

    def showFiltPerf(self):
        """
        Print filter properties at frequencies of interest.
        """
        self.tblFiltPerf.setVisible(self.chkFiltPerf.isChecked())

        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        f_S  = fb.fil[0]['f_S']

        # Build a list with all frequency related labels:
        #--------------------------------------------------------------------
        # First, extract the dicts for min / man filter order of the selected
        # design method from filter tree:
        fil_dict = fb.filTree[fb.fil[0]['rt']][fb.fil[0]['ft']][fb.fil[0]['dm']]
        # Now, extract the parameter lists (key 'par'), yielding a nested list:
        fil_list = [fil_dict[k]['par'] for k in fil_dict.keys()]
        # Finally, flatten the list of lists and convert it into a set to 
        # eliminate double entries:
        fil_set = set([item for sublist in fil_list for item in sublist])
        # extract all labels starting with 'F':
        F_test_lbls = [lbl for lbl in fil_set if lbl[0] == 'F']
        # construct a list of lists [frequency, label], sorted by frequency:
        F_test = sorted([[fb.fil[0][lbl]*f_S, lbl] for lbl in F_test_lbls])

        # construct a list of lists consisting of [label, frequency]:
        # F_test = [[lbl, fb.fil[0][lbl]*f_S] for lbl in F_test_lbls]
        ## sort list of tuples using the LAST element of the tuple (= frequency)
        # F_test = sorted(F_test, key=lambda t: t[::-1])

        if self.DEBUG: print("input_info.showFiltPerf\nF_test = ", F_test)


        # Vector with test frequencies of the labels above    
        F_test_vals = np.array([item[0] for item in F_test]) / f_S
        F_test_lbls = [item[1] for item in F_test]
        
        # Calculate frequency response at test frequencies and over the whole range:
        [w_test, H_test] = sig.freqz(bb, aa, F_test_vals * 2.0 * pi)
        [w, H] = sig.freqz(bb, aa)

        f = w / (2.0 * pi) # frequency normalized to f_S
        H_abs = abs(H)
        H_max = max(H_abs);
        H_max_dB = 20*log10(H_max);
        F_max = f[np.argmax(H_abs)]
        #
        H_min = min(H_abs)
        H_min_dB = 20*log10(H_min)
        F_min = f[np.argmin(H_abs)]
        
#        f = f * f_S 

        F_test_lbls += ['Min.','Max.']
        F_test_vals = np.append(F_test_vals, [F_min, F_max])
        H_test = np.append(H_test, [H_min, H_max])
        # calculate response of test frequencies and round to 5 digits to 
        # suppress fails due to numerical inaccuracies:
        H_test_dB = np.round(-20*log10(abs(H_test)),5)
        
        # build a list with the corresponding target specs:
        H_targ = []
        H_targ_pass = []
        
        for i in range(len(F_test_lbls)):
            lbl = F_test_lbls[i]
            if lbl   == 'F_PB': 
                H_targ.append(fb.fil[0]['A_PB'])
                H_targ_pass.append(H_test_dB[i] <= H_targ[i])
            elif lbl == 'F_SB': 
                H_targ.append(fb.fil[0]['A_SB'])
                H_targ_pass.append(H_test_dB[i] >= H_targ[i])
            elif lbl == 'F_PB2':
                H_targ.append(fb.fil[0]['A_PB2'])
                H_targ_pass.append( H_test_dB[i] <= H_targ[i])
            elif lbl == 'F_SB2':
                H_targ.append(fb.fil[0]['A_SB2'])
                H_targ_pass.append( H_test_dB[i] >= H_targ[i])
            else: 
                H_targ.append(np.nan)
                H_targ_pass.append(True)

        self.targ_spec_passed = np.all(H_targ_pass)
#            
        if self.DEBUG:
            print("input_info.showFiltPerf\n===================")
            print("H_targ", H_targ)
            print("H_test", H_test)
            print("H_test_dB", H_test_dB)
            print("F_test", F_test_vals)
            print("H_targ_pass",H_targ_pass)
            print("passed:", self.targ_spec_passed)

#        min_dB = np.floor(max(PLT_min_dB, H_min_dB) / 10) * 10

        self.tblFiltPerf.setRowCount(len(H_test))
        self.target_spec_passed = False

        self.tblFiltPerf.setHorizontalHeaderLabels([
        'f/{0:s}'.format(fb.fil[0]['freq_specs_unit']),'|H(f)|','|H(f)| (dB)', 'Spec'] )
        self.tblFiltPerf.setVerticalHeaderLabels(F_test_lbls)
        for row in range(len(H_test)):
#            self.tblFiltPerf.setItem(row,0,QtGui.QTableWidgetItem(F_test_lbls[row]))
            self.tblFiltPerf.setItem(row,0,QtGui.QTableWidgetItem(str('{0:.4g}'.format(F_test_vals[row]*f_S))))
            self.tblFiltPerf.setItem(row,1,QtGui.QTableWidgetItem(str('%.4g'%(abs(H_test[row])))))
            self.tblFiltPerf.setItem(row,2,QtGui.QTableWidgetItem(str('%2.3f'%(H_test_dB[row]))))
            if not H_targ_pass[row]:
                self.tblFiltPerf.item(row,1).setBackgroundColor(Qt.QColor('red'))
                self.tblFiltPerf.item(row,2).setBackgroundColor(Qt.QColor('red'))
            self.tblFiltPerf.setItem(row,3,QtGui.QTableWidgetItem(str('%2.3f'%(H_targ[row]))))


    #    self.tblFiltPerf.item(1,1).setBackgroundColor(Qt.QColor('red'))
        self.tblFiltPerf.resizeColumnsToContents()
        self.tblFiltPerf.resizeRowsToContents()


    def showDocs(self):
        """
        Display info from filter design file and docstring
        """

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
         "\n" + textwrap.dedent("\n".join(lines[1:]))
        return result

    def showFiltDict(self):
        """
        Print filter dict for debugging
        """
        self.txtFiltDict.setVisible(self.chkFiltDict.isChecked())

        fb_sorted = [str(key) +' : '+ str(fb.fil[0][key]) for key in sorted(fb.fil[0].keys())]
        dictstr = pprint.pformat(fb_sorted)
#        dictstr = pprint.pformat(fb.fil[0])
        self.txtFiltDict.setText(dictstr)

#        pprint.pprint(fb.fil[0])
        
        
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