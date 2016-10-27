# -*- coding: utf-8 -*-
"""
Widget for displaying infos about filter and filter design method

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import pprint
import textwrap
import logging
logger = logging.getLogger(__name__)

from ..compat import (QtCore, QtGui,
                      QWidget, QLabel, QLineEdit, QComboBox, QFrame, QFont, QCheckBox,
                      QTableWidget, QTableWidgetItem, QTextBrowser, QTextCursor,
                      QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy,
                      pyqtSignal, Qt, QEvent)

try:
    from docutils.core import publish_string 
    HAS_DOCUTILS = True
except ImportError:
    HAS_DOCUTILS = False

import numpy as np
from numpy import pi, log10
import scipy.signal as sig

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.filter_factory as ff # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import lin2unit# , rt_label
# TODO: Passband and stopband info should show min / max values for each band

class FilterInfo(QWidget):
    """
    Create widget for displaying infos about filter and filter design method
    """
    def __init__(self, parent):
        super(FilterInfo, self).__init__(parent)
        
        self._construct_UI()
        self.load_entries()

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Checkboxes for selecting the info to be displayed
        - A large text window for displaying infos about the filter design
          algorithm
        """
        self.chkFiltPerf = QCheckBox("H(f)")
        self.chkFiltPerf.setChecked(True)
        self.chkFiltPerf.setToolTip("Display frequency response at test frequencies.")

        self.txtFiltPerf = QTextBrowser()
        self.txtFiltDict = QTextBrowser()

        bfont = QFont()
        bfont.setBold(True)
        self.tblFiltPerf = QTableWidget()
        self.tblFiltPerf.setAlternatingRowColors(True)
#        self.tblFiltPerf.verticalHeader().setVisible(False)
        self.tblFiltPerf.horizontalHeader().setHighlightSections(False)
        self.tblFiltPerf.horizontalHeader().setFont(bfont)
        self.tblFiltPerf.verticalHeader().setHighlightSections(False)
        self.tblFiltPerf.verticalHeader().setFont(bfont)
        
#        self.tblCoeff.QItemSelectionModel.Clear
#        self.tblCoeff.setDragEnabled(True)
#        self.tblCoeff.setDragDropMode(QAbstractItemView.InternalMove)
        self.tblFiltPerf.setSizePolicy(QSizePolicy.MinimumExpanding,
                                          QSizePolicy.MinimumExpanding)

#        self.tblFiltPerf = QTextTable(self.txtFiltPerf)
#        QTextBrowser()
#        self.txtFiltPerf.setSizePolicy(QSizePolicy.Minimum,
#                                          QSizePolicy.Expanding)
        # widget / subwindow for filter infos
        self.chkDocstring = QCheckBox("Doc$")
        self.chkDocstring.setChecked(False)
        self.chkDocstring.setToolTip("Display docstring from python filter method.")

        self.chkRichText = QCheckBox("RTF")
        self.chkRichText.setChecked(HAS_DOCUTILS)
        self.chkRichText.setEnabled(HAS_DOCUTILS)
        self.chkRichText.setToolTip("Render documentation in Rich Text Format.")

        self.txtFiltInfoBox = QTextBrowser()
        self.txtFiltInfoBox.setSizePolicy(QSizePolicy.MinimumExpanding,
                                          QSizePolicy.Expanding)
                                          
        self.chkFiltDict = QCheckBox("FiltDict")
        self.chkFiltDict.setToolTip("Show filter dictionary for debugging.")

        self.txtFiltDict = QTextBrowser()
        self.txtFiltDict.setSizePolicy(QSizePolicy.Minimum,
                                          QSizePolicy.Expanding)

        self.chkFiltTree = QCheckBox("FiltTree")
        self.chkFiltTree.setToolTip("Show filter tree for debugging.")

        self.txtFiltTree = QTextBrowser()
        self.txtFiltTree.setSizePolicy(QSizePolicy.Minimum,
                                          QSizePolicy.Expanding)


        # ============== UI Layout =====================================
        self.layHChkBoxes = QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkFiltPerf)
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkDocstring)
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkRichText)
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkFiltDict)
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkFiltTree)

        layVMain = QVBoxLayout()
        layVMain.addLayout(self.layHChkBoxes)
        layVMain.addWidget(self.tblFiltPerf)
        layVMain.addWidget(self.txtFiltInfoBox)
        layVMain.addWidget(self.txtFiltDict)
        layVMain.addWidget(self.txtFiltTree)
#        layVMain.addStretch(10)
        self.setLayout(layVMain)

        # ============== Signals & Slots ================================
        self.chkFiltPerf.clicked.connect(self._show_filt_perf)
        self.chkFiltDict.clicked.connect(self._show_filt_dict)
        self.chkFiltTree.clicked.connect(self._show_filt_tree)
        self.chkDocstring.clicked.connect(self._show_doc)
        self.chkRichText.clicked.connect(self._show_doc)

#------------------------------------------------------------------------------
    def load_entries(self):
        """
        update docs and filter performance
        """
        self._show_doc()
        self._show_filt_perf()
        self._show_filt_dict()

#------------------------------------------------------------------------------
    def _show_doc(self):
        """
        Display info from filter design file and docstring
        """
        if hasattr(ff.fil_inst,'info'):
            if self.chkRichText.isChecked():
                self.txtFiltInfoBox.setText(publish_string(
                    self._clean_doc(ff.fil_inst.info), writer_name='html',
                    settings_overrides={'output_encoding': 'unicode'}))
            else:
                self.txtFiltInfoBox.setText(textwrap.dedent(ff.fil_inst.info))
        else:
            self.txtFiltInfoBox.setText("")

        if self.chkDocstring.isChecked() and hasattr(ff.fil_inst,'info_doc'):
            if self.chkRichText.isChecked():
                self.txtFiltInfoBox.append(
                '<hr /><b>Python module docstring:</b>\n')
                for doc in ff.fil_inst.info_doc:
                    self.txtFiltInfoBox.append(publish_string(
                     self._clean_doc(doc), writer_name='html',
                        settings_overrides = {'output_encoding': 'unicode'}))
            else:
                self.txtFiltInfoBox.append('\nPython module docstring:\n')
                for doc in ff.fil_inst.info_doc:
                    self.txtFiltInfoBox.append(self.cleanDoc(doc))

        self.txtFiltInfoBox.moveCursor(QTextCursor.Start)

    def _clean_doc(self, doc):
        """
        Remove uniform number of leading blanks from docstrings for subsequent
        processing of rich text. The first line is treated differently, _all_
        leading blanks are removed (if any). This allows for different formats
        of docstrings.
        """
        lines = doc.splitlines()
        result = lines[0].lstrip() + "\n" + textwrap.dedent("\n".join(lines[1:]))
        return result

#------------------------------------------------------------------------------
    def _show_filt_perf(self):
        """
        Print filter properties in a table at frequencies of interest. When
        specs are violated, colour the table entry in red.
        """
        
        def _find_min_max(self, f_start, f_stop, unit = 'dB'):
            """
            Find minimum and maximum magnitude and the corresponding frequencies
            for the filter defined in the filter dict in a given frequency band
            [f_start, f_stop].
            """
            w = np.linspace(f_start, f_stop, 2048)*2*np.pi            
            [w, H] = sig.freqz(bb, aa)
            f = w / (2.0 * pi) # frequency normalized to f_S
            H_abs = abs(H)
            H_max = max(H_abs)
            H_min = min(H_abs)
            F_max = f[np.argmax(H_abs)] # find the frequency where H_abs 
            F_min = f[np.argmin(H_abs)] # becomes max resp. min
            if unit == 'dB':
                H_max = 20*log10(H_max)
                H_min = 20*log10(H_min)
            return F_min, H_min, F_max, H_max

            
            
        self.tblFiltPerf.setVisible(self.chkFiltPerf.isChecked())
        if self.chkFiltPerf.isChecked():

            bb = fb.fil[0]['ba'][0]
            aa = fb.fil[0]['ba'][1]
    
            f_S  = fb.fil[0]['f_S']
    
            # Build a list with all frequency related labels:
            #--------------------------------------------------------------------
            # First, extract the dicts for min / man filter order of the selected
            # filter class from filter tree:
            fil_dict = fb.fil_tree[fb.fil[0]['rt']][fb.fil[0]['ft']][fb.fil[0]['fc']]
            # Now, extract the parameter lists (key 'par'), yielding a nested list:
            fil_list = [fil_dict[k]['par'] for k in fil_dict.keys()]
            # Finally, flatten the list of lists and convert it into a set to 
            # eliminate double entries:
            fil_set = set([item for sublist in fil_list for item in sublist])
            # extract all labels starting with 'F':
    #        F_test_lbls = [lbl for lbl in fil_set if lbl[0] == 'F']
            # construct a list of lists [frequency, label], sorted by frequency:
    #        F_test = sorted([[fb.fil[0][lbl]*f_S, lbl] for lbl in F_test_lbls])
    
            # construct a list of lists consisting of [label, frequency]:
            # F_test = [[lbl, fb.fil[0][lbl]*f_S] for lbl in F_test_lbls]
            ## sort list of tuples using the LAST element of the tuple (= frequency)
            # F_test = sorted(F_test, key=lambda t: t[::-1])
    
    
            f_lbls = []
            f_vals = []
            a_lbls = []
            a_targs = []
            a_targs_dB = []
            ft = fb.fil[0]['ft'] # get filter type ('IIR', 'FIR')
            unit = fb.fil[0]['amp_specs_unit']
            unit = 'dB' # fix this for the moment
            # read specifications from filter dict and sort them depending on the response type        
            if fb.fil[0]['rt'] in {'LP', 'HP', 'BP', 'BS'}:
                if fb.fil[0]['rt'] == 'LP':
                    f_lbls = ['F_PB', 'F_SB'] 
                    a_lbls = ['A_PB', 'A_SB']
                elif fb.fil[0]['rt'] == 'HP':
                    f_lbls = ['F_SB', 'F_PB']
                    a_lbls = ['A_SB', 'A_PB']
                elif fb.fil[0]['rt'] == 'BP':
                    f_lbls = ['F_SB', 'F_PB', 'F_PB2', 'F_SB2']
                    a_lbls = ['A_SB', 'A_PB', 'A_PB', 'A_SB2']
                elif fb.fil[0]['rt'] == 'BS':
                    f_lbls = ['F_PB', 'F_SB', 'F_SB2', 'F_PB2']
                    a_lbls = ['A_PB', 'A_SB', 'A_SB', 'A_PB2']

            # Try to construct lists of frequency / amplitude labels and specs
            # When one of the labels doesn't exist in the filter dict, delete 
            # all corresponding amplitude and frequency entries
                err = [False] * len(f_lbls) # initialize error list  
                f_vals = []
                a_targs = []
                for i in range(len(f_lbls)):
                    try:
                        f = fb.fil[0][f_lbls[i]]
                        f_vals.append(f)
                    except KeyError as e:
                        f_vals.append('')
                        err[i] = True
                        logger.debug(e)
                    try:
                        a = fb.fil[0][a_lbls[i]]
                        a_dB = lin2unit(fb.fil[0][a_lbls[i]], ft, a_lbls[i], unit)
                        a_targs.append(a)
                        a_targs_dB.append(a_dB)
                    except KeyError as e:
                        a_targs.append('')
                        a_targs_dB.append('')
                        err[i] = True
                        logger.debug(e)

                for i in range(len(f_lbls)):
                    if err[i]:
                        del f_lbls[i]
                        del f_vals[i]
                        del a_lbls[i]
                        del a_targs[i]
                        del a_targs_dB[i]
    
                f_vals = np.asarray(f_vals) # convert to numpy array
    
                logger.debug("input_info.showFiltPerf\nF_test = %s" %f_lbls)
                               
                # Calculate frequency response at test frequencies
                [w_test, a_test] = sig.freqz(bb, aa, 2.0 * pi * f_vals.astype(np.float))
                
            
            (F_min, H_min, F_max, H_max) = _find_min_max(self, 0, 1, unit = 'V')    
            # append frequencies and values for min. and max. filter reponse to 
            # test vector
            f_lbls += ['Min.','Max.']
            # QTableView does not support direct formatting, use QLabel
            # f_lbls = [rt_label(l) for l in f_lbls] 
            f_vals = np.append(f_vals, [F_min, F_max])
            a_targs = np.append(a_targs, [np.nan, np.nan])
            a_targs_dB = np.append(a_targs_dB, [np.nan, np.nan])
            a_test = np.append(a_test, [H_min, H_max])
            # calculate response of test frequencies in dB
            a_test_dB = -20*log10(abs(a_test))
            
            
            ft = fb.fil[0]['ft'] # get filter type ('IIR', 'FIR') for dB <-> lin conversion
#            unit = fb.fil[0]['amp_specs_unit']
            unit = 'dB' # fix this for the moment
    
            # build a list with the corresponding target specs:
            a_targs_pass = []
            eps = 1e-3
            for i in range(len(f_lbls)):
                if 'PB' in f_lbls[i]:
                    a_targs_pass.append((a_test_dB[i] - a_targs_dB[i])< eps)
                elif 'SB' in f_lbls[i]:
                    a_targs_pass.append(a_test_dB[i] >= a_targs_dB[i]) 
                else:
                    a_targs_pass.append(True)
    
            self.targs_spec_passed = np.all(a_targs_pass)
            
            logger.debug("H_targ = %s\n", a_targs,
                "H_test = %s\n", a_test,
                "H_test_dB = %s\n", a_test_dB,
                "F_test = %s\n", f_vals,
                "H_targ_pass = %s\n", a_targs_pass,
                "passed: %s\n", self.targs_spec_passed)
    
            self.tblFiltPerf.setRowCount(len(a_test)) # number of table rows
            self.tblFiltPerf.setColumnCount(5) # number of table columns
    
            self.tblFiltPerf.setHorizontalHeaderLabels([
            'f/{0:s}'.format(fb.fil[0]['freq_specs_unit']),'|H(f)| (dB)', 'Spec (dB)', '|H(f)|','Spec'] )
            self.tblFiltPerf.setVerticalHeaderLabels(f_lbls)
            for row in range(len(a_test)):
                self.tblFiltPerf.setItem(row,0,QTableWidgetItem(str('{0:.4g}'.format(f_vals[row]*f_S))))
                self.tblFiltPerf.setItem(row,1,QTableWidgetItem(str('%2.3f'%(a_test_dB[row]))))
                self.tblFiltPerf.setItem(row,2,QTableWidgetItem(str('%2.3g'%(a_targs_dB[row]))))
                self.tblFiltPerf.setItem(row,3,QTableWidgetItem(str('%.3g'%(abs(a_test[row])))))
                self.tblFiltPerf.setItem(row,4,QTableWidgetItem(str('%2.3f'%(a_targs[row]))))
                if not a_targs_pass[row]:
                    self.tblFiltPerf.item(row,1).setBackground(QtGui.QColor('red'))
                    self.tblFiltPerf.item(row,3).setBackground(QtGui.QColor('red'))
    
            self.tblFiltPerf.resizeColumnsToContents()
            self.tblFiltPerf.resizeRowsToContents()

#------------------------------------------------------------------------------
    def _show_filt_dict(self):
        """
        Print filter dict for debugging
        """
        self.txtFiltDict.setVisible(self.chkFiltDict.isChecked())

        fb_sorted = [str(key) +' : '+ str(fb.fil[0][key]) for key in sorted(fb.fil[0].keys())]
        dictstr = pprint.pformat(fb_sorted)
#        dictstr = pprint.pformat(fb.fil[0])
        self.txtFiltDict.setText(dictstr)

#------------------------------------------------------------------------------
    def _show_filt_tree(self):
        """
        Print filter tree for debugging
        """
        self.txtFiltTree.setVisible(self.chkFiltTree.isChecked())

        ftree_sorted = ['<b>' + str(key) +' : '+ '</b>' + str(fb.fil_tree[key]) for key in sorted(fb.fil_tree.keys())]
        dictstr = pprint.pformat(ftree_sorted, indent = 4)
#        dictstr = pprint.pformat(fb.fil[0])
        self.txtFiltTree.setText(dictstr)
        
        
#app = QApplication([])
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

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FilterInfo(None)

    app.setActiveWindow(mainw) 
    mainw.show()

    sys.exit(app.exec_())