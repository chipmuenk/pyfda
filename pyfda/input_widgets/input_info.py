# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for displaying infos about filter and filter design method and debugging infos as well
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import pprint
import textwrap
import logging
logger = logging.getLogger(__name__)

from ..compat import (QtGui, QWidget, QFont, QCheckBox, QFrame,
                      QTableWidget, QTableWidgetItem, QTextBrowser, QTextCursor,
                      QVBoxLayout, QHBoxLayout, QSplitter, Qt, pyqtSignal)

import numpy as np
from numpy import pi, log10
import scipy.signal as sig

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.filter_factory as ff # importing filterbroker initializes all its globals
from pyfda.pyfda_lib import lin2unit, mod_version
from pyfda.pyfda_rc import params
# TODO: Passband and stopband info should show min / max values for each band

if mod_version('docutils') is not None:
    from docutils.core import publish_string
    HAS_DOCUTILS = True
else:
    HAS_DOCUTILS = False

class Input_Info(QWidget):
    """
    Create widget for displaying infos about filter specs and filter design method
    """
    sig_rx = pyqtSignal(object) # incoming signals from input_tab_widgets

    def __init__(self, parent):
        super(Input_Info, self).__init__(parent)
        
        self.tab_label = 'Info'
        self.tool_tip = ("<span>Display the achieved filter specifications"
                " and more info about the filter design algorithm.</span>")       
        
        self._construct_UI()
        self.load_dict()

    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if 'data_changed' in dict_sig or 'view_changed' in dict_sig or 'specs_changed' in dict_sig:
            self.load_dict()

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Checkboxes for selecting the info to be displayed
        - A large text window for displaying infos about the filter design
          algorithm
        """
        bfont = QFont()
        bfont.setBold(True)
        
        # ============== UI Layout =====================================
        # widget / subwindow for filter infos
        self.chkFiltPerf = QCheckBox("H(f)", self)
        self.chkFiltPerf.setChecked(True)
        self.chkFiltPerf.setToolTip("Display frequency response at test frequencies.")

        self.chkDocstring = QCheckBox("Doc$", self)
        self.chkDocstring.setChecked(False)
        self.chkDocstring.setToolTip("Display docstring from python filter method.")

        self.chkRichText = QCheckBox("RTF", self)
        self.chkRichText.setChecked(HAS_DOCUTILS)
        self.chkRichText.setEnabled(HAS_DOCUTILS)
        self.chkRichText.setToolTip("Render documentation in Rich Text Format.")
                                                  
        self.chkFiltDict = QCheckBox("FiltDict", self)
        self.chkFiltDict.setToolTip("Show filter dictionary for debugging.")   

        self.chkFiltTree = QCheckBox("FiltTree", self)
        self.chkFiltTree.setToolTip("Show filter tree for debugging.")

        self.layHChkBoxes = QHBoxLayout()
        self.layHChkBoxes.addWidget(self.chkFiltPerf)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.chkDocstring)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.chkRichText)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.chkFiltDict)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.chkFiltTree)
        self.frmMain = QFrame(self)
        self.frmMain.setLayout(self.layHChkBoxes)

        
        self.tblFiltPerf = QTableWidget(self)
        self.tblFiltPerf.setAlternatingRowColors(True)
#        self.tblFiltPerf.verticalHeader().setVisible(False)
        self.tblFiltPerf.horizontalHeader().setHighlightSections(False)
        self.tblFiltPerf.horizontalHeader().setFont(bfont)
        self.tblFiltPerf.verticalHeader().setHighlightSections(False)
        self.tblFiltPerf.verticalHeader().setFont(bfont)

        self.txtFiltInfoBox = QTextBrowser(self)
        self.txtFiltDict = QTextBrowser(self)
        self.txtFiltTree = QTextBrowser(self)

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmMain)

#        layVMain.addLayout(self.layHChkBoxes)
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(self.tblFiltPerf)
        splitter.addWidget(self.txtFiltInfoBox)
        splitter.addWidget(self.txtFiltDict)
        splitter.addWidget(self.txtFiltTree)
        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([3000,10000,1000,1000])
        layVMain.addWidget(splitter)

        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.chkFiltPerf.clicked.connect(self._show_filt_perf)
        self.chkFiltDict.clicked.connect(self._show_filt_dict)
        self.chkFiltTree.clicked.connect(self._show_filt_tree)
        self.chkDocstring.clicked.connect(self._show_doc)
        self.chkRichText.clicked.connect(self._show_doc)

#------------------------------------------------------------------------------
    def load_dict(self):
        """
        update docs and filter performance
        """
        self._show_doc()
        self._show_filt_perf()
        self._show_filt_dict()
        self._show_filt_tree()

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
                    self.txtFiltInfoBox.append(self._clean_doc(doc))

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
        
        antiC = False

        def _find_min_max(self, f_start, f_stop, unit = 'dB'):
            """
            Find minimum and maximum magnitude and the corresponding frequencies
            for the filter defined in the filter dict in a given frequency band
            [f_start, f_stop].
            """
            w = np.linspace(f_start, f_stop, params['N_FFT'])*2*np.pi
            [w, H] = sig.freqz(bb, aa, worN = w)

            # add antiCausals if we have them
            if (antiC):
               #
               # Evaluate transfer function of anticausal half on the same freq grid.
               #
               wa, ha = sig.freqz(bbA, aaA, worN = w)
               ha = ha.conjugate()
               #
               # Total transfer function is the product
               #
               H = H*ha

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
        #------------------------------------------------------------------

        self.tblFiltPerf.setVisible(self.chkFiltPerf.isChecked())
        if self.chkFiltPerf.isChecked():

            bb = fb.fil[0]['ba'][0]
            aa = fb.fil[0]['ba'][1]

            #'rpk' means nonCausal filter
            if 'rpk' in fb.fil[0]:
                antiC = True
                bbA = fb.fil[0]['baA'][0]
                aaA = fb.fil[0]['baA'][1]
                bbA = bbA.conjugate()
                aaA = aaA.conjugate()

            f_S  = fb.fil[0]['f_S']
    
            f_lbls = []
            f_vals = []
            a_lbls = []
            a_targs = []
            a_targs_dB = []
            a_test = []
            ft = fb.fil[0]['ft'] # get filter type ('IIR', 'FIR')
            unit = fb.fil[0]['amp_specs_unit']
            unit = 'dB' # fix this for the moment
            # construct pairs of corner frequency and corresponding amplitude
            # labels in ascending frequency for each response type        
            if fb.fil[0]['rt'] in {'LP', 'HP', 'BP', 'BS', 'HIL'}:
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
                elif fb.fil[0]['rt'] == 'HIL':
                    f_lbls = ['F_PB', 'F_PB2']
                    a_lbls = ['A_PB', 'A_PB']


            # Try to get lists of frequency / amplitude specs from the filter dict
            # that correspond to the f_lbls / a_lbls pairs defined above
            # When one of the labels doesn't exist in the filter dict, delete 
            # all corresponding amplitude and frequency entries.
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
    
                logger.debug("F_test_labels = %s" %f_lbls)
                               
                # Calculate frequency response at test frequencies
                [w_test, a_test] = sig.freqz(bb, aa, 2.0 * pi * f_vals.astype(np.float))
                # add antiCausals if we have them
                if (antiC):
                   wa, ha = sig.freqz(bbA, aaA, 2.0 * pi * f_vals.astype(np.float))
                   ha = ha.conjugate()
                   a_test = a_test*ha


            (F_min, H_min, F_max, H_max) = _find_min_max(self, 0, 1, unit = 'V')    
            # append frequencies and values for min. and max. filter reponse to 
            # test vector
            
            f_lbls += ['Min.','Max.']
            # QTableView does not support direct formatting, use QLabel

            f_vals = np.append(f_vals, [F_min, F_max])
            a_targs = np.append(a_targs, [np.nan, np.nan])
            a_targs_dB = np.append(a_targs_dB, [np.nan, np.nan])
            a_test = np.append(a_test, [H_min, H_max])
            # calculate response of test frequencies in dB
            a_test_dB = -20*log10(abs(a_test))
            
            ft = fb.fil[0]['ft'] # get filter type ('IIR', 'FIR') for dB <-> lin conversion
#            unit = fb.fil[0]['amp_specs_unit']
            unit = 'dB' # make this fixed for the moment
    
            # build a list with the corresponding target specs:
            a_targs_pass = []
            eps = 1e-3
            for i in range(len(f_lbls)):
                if 'PB' in f_lbls[i]:
                    a_targs_pass.append((a_test_dB[i] - a_targs_dB[i])< eps)
                    a_test[i] = 1 - abs(a_test[i])
                elif 'SB' in f_lbls[i]:
                    a_targs_pass.append(a_test_dB[i] >= a_targs_dB[i]) 
                else:
                    a_targs_pass.append(True)
    
            self.targs_spec_passed = np.all(a_targs_pass)
            
            logger.debug("H_targ = {0}\n" 
                "H_test = {1}\n"
                "H_test_dB = {2}\n"
                "F_test = {3}\n" 
                "H_targ_pass = {4}\n" 
                "passed: {5}\n".format(a_targs,  a_test,  a_test_dB, f_vals, a_targs_pass,self.targs_spec_passed)) 
    
            self.tblFiltPerf.setRowCount(len(a_test)) # number of table rows
            self.tblFiltPerf.setColumnCount(5) # number of table columns
    
            self.tblFiltPerf.setHorizontalHeaderLabels([
            'f/{0:s}'.format(fb.fil[0]['freq_specs_unit']),'Spec\n(dB)', '|H(f)|\n(dB)', 'Spec', '|H(f)|'] )
            self.tblFiltPerf.setVerticalHeaderLabels(f_lbls)
            for row in range(len(a_test)):
                self.tblFiltPerf.setItem(row,0,QTableWidgetItem(str('{0:.4g}'.format(f_vals[row]*f_S))))
                self.tblFiltPerf.setItem(row,1,QTableWidgetItem(str('%2.3g'%(-a_targs_dB[row]))))
                self.tblFiltPerf.setItem(row,2,QTableWidgetItem(str('%2.3f'%(-a_test_dB[row]))))
                if a_targs[row] < 0.01:
                    self.tblFiltPerf.setItem(row,3,QTableWidgetItem(str('%.3e'%(a_targs[row]))))
                else:
                    self.tblFiltPerf.setItem(row,3,QTableWidgetItem(str('%2.4f'%(a_targs[row]))))
                if a_test[row] < 0.01:    
                    self.tblFiltPerf.setItem(row,4,QTableWidgetItem(str('%.3e'%(abs(a_test[row])))))
                else:
                    self.tblFiltPerf.setItem(row,4,QTableWidgetItem(str('%.4f'%(abs(a_test[row])))))
                    
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
        

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = Input_Info(None)

    app.setActiveWindow(mainw) 
    mainw.show()

    sys.exit(app.exec_())
