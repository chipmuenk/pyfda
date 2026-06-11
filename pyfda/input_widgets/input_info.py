# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for displaying infos about filter and filter design method and debugging infos
"""
import logging
import pprint
import sys
import textwrap

import numpy as np
from numpy import pi, log10
import scipy.signal as sig

from pyfda.config_file_parser import ConfigFileParser as CFP
from pyfda.filterbroker import fb_get
import pyfda.filter_factory as ff
from pyfda.tree_builder import Tree_Builder as TB
from pyfda.input_widgets.input_info_about import AboutWindow
from pyfda.libs.compat import (
    QtGui, QWidget, QFont, QFrame, QLabel, QTableWidget, QTableWidgetItem,
    QTextBrowser, QTextCursor, QLineEdit, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSplitter, Qt, pyqtSignal)
from pyfda.libs.pyfda_lib import lin2unit, mod_version, to_html, safe_eval
from pyfda.libs.pyfda_qt_lib import emit
from pyfda.libs.pyfda_qt_classes import PushButton
from pyfda.pyfda_rc import params

logger = logging.getLogger(__name__)

# TODO: Passband and stopband info should show min / max values for each band

if mod_version('docutils') is not None:
    from docutils.core import publish_string
    HAS_DOCUTILS = True
else:
    HAS_DOCUTILS = False

classes = {'Input_Info': 'Info'}  #: Dict containing class name : display name

# ------------------------------------------------------------------------------
class Input_Info(QWidget):
    """
    Create widget for displaying infos about filter specs and filter design method
    """
    sig_rx = pyqtSignal(object)  # incoming signals from input_tab_widgets
    sig_tx = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__()

        self.tab_label = 'Info'
        self.tool_tip = (
            "<span>Display the achieved filter specifications"
            " and more info about the filter design algorithm.</span>")

        self._construct_UI()
        self.load_dict()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        # logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if 'data_changed' in dict_sig or 'view_changed' in dict_sig\
                or 'specs_changed' in dict_sig:
            self.load_dict()

    # -------------------------------------------------------------------------
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
        self.butFiltPerf = PushButton(self, text="H(f)", checked=True)
        self.butFiltPerf.setToolTip("Display frequency response at test frequencies.")

        self.butDebug = PushButton(self, "Debug", checked=False)
        self.butDebug.setToolTip("Show debugging options.")

        self.butAbout = PushButton(self, "About", checkable=False)  # pop-up "About" window
        self.butAbout.setToolTip(
            "<span>Show included modules and their versions.</span>")

        self.butSettings = PushButton(self, "Settings", checked=False)
        self.butSettings.setToolTip("Display and set some settings")

        layHControls1 = QHBoxLayout()
        layHControls1.addWidget(self.butFiltPerf)
        layHControls1.addWidget(self.butAbout)
        layHControls1.addWidget(self.butSettings)
        layHControls1.addWidget(self.butDebug)

        self.butDocstring = PushButton(self, "Doc$", checked=False)
        self.butDocstring.setToolTip("Display docstring from python filter method.")

        self.butRichText = PushButton(
            self, "RTF", checkable=HAS_DOCUTILS, checked=HAS_DOCUTILS)
        self.butRichText.setEnabled(HAS_DOCUTILS)
        self.butRichText.setToolTip("Render documentation in Rich Text Format.")

        self.butFiltDict = PushButton(self, "FiltDict", checked=False)
        self.butFiltDict.setToolTip("Show filter dictionary for debugging.")

        self.butFiltTree = PushButton(self, "FiltTree", checked=False)
        self.butFiltTree.setToolTip("Show filter tree for debugging.")

        lay_h_debug_1 = QHBoxLayout()
        lay_h_debug_1.addWidget(self.butDocstring)
        lay_h_debug_1.addWidget(self.butRichText)
        lay_h_debug_1.addWidget(self.butFiltDict)
        lay_h_debug_1.addWidget(self.butFiltTree)

        lay_v_debug = QVBoxLayout()
        lay_v_debug.addLayout(lay_h_debug_1)
        lay_v_debug.setContentsMargins(0, 0, 0, 0)

        self.frm_debug = QFrame(self)
        self.frm_debug.setLayout(lay_v_debug)
        self.frm_debug.setVisible(self.butDebug.checked)
        self.frm_debug.setContentsMargins(0, 0, 0, 0)

        lbl_settings_NFFT = QLabel(to_html("N_FFT =", frmt='bi'), self)
        self.led_settings_NFFT = QLineEdit(self)
        self.led_settings_NFFT.setText(str(CFP.conf_settings['N_FFT']))
        self.led_settings_NFFT.setToolTip("<span>Number of FFT points for frequency "
                                          "domain widgets.</span>")
        lbl_exception_handling = QLabel(to_html("Exception Level =", frmt='b'), self)
        self.led_exception_handling = QLineEdit(self)
        self.led_exception_handling.setText(str(CFP.conf_settings['EXCEPTION_LEVEL']))
        self.led_exception_handling.setToolTip(
            "<span>Set level for handling exceptions: "
            "0: quiet, 1: print error stack, 2: end pyfda.</span>")

        layGSettings = QGridLayout()
        layGSettings.addWidget(lbl_settings_NFFT, 1, 0)
        layGSettings.addWidget(self.led_settings_NFFT, 1, 1)
        layGSettings.addWidget(lbl_exception_handling, 2, 0)
        layGSettings.addWidget(self.led_exception_handling, 2, 1)

        self.frmSettings = QFrame(self)
        self.frmSettings.setLayout(layGSettings)
        self.frmSettings.setVisible(self.butSettings.checked)
        self.frmSettings.setContentsMargins(0, 0, 0, 0)

        lay_v_controls = QVBoxLayout()
        lay_v_controls.addLayout(layHControls1)
        lay_v_controls.addWidget(self.frm_debug)
        lay_v_controls.addWidget(self.frmSettings)

        self.frmMain = QFrame(self)
        self.frmMain.setLayout(lay_v_controls)

        self.tbl_filt_perf = QTableWidget(self)
        self.tbl_filt_perf.setAlternatingRowColors(True)
#        self.tbl_filt_perf.verticalHeader().setVisible(False)
        self.tbl_filt_perf.horizontalHeader().setHighlightSections(False)
        self.tbl_filt_perf.horizontalHeader().setFont(bfont)
        self.tbl_filt_perf.verticalHeader().setHighlightSections(False)
        self.tbl_filt_perf.verticalHeader().setFont(bfont)

        self.txt_filt_info_box = QTextBrowser(self)
        self.txt_filt_dict = QTextBrowser(self)
        self.txt_filt_tree = QTextBrowser(self)

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmMain)

#        layVMain.addLayout(self.layHControls)
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(self.tbl_filt_perf)
        splitter.addWidget(self.txt_filt_info_box)
        splitter.addWidget(self.txt_filt_dict)
        splitter.addWidget(self.txt_filt_tree)
        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([3000, 10000, 1000, 1000])
        layVMain.addWidget(splitter)

        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.butFiltPerf.clicked.connect(self._show_filt_perf)
        self.butAbout.clicked.connect(self._about_window)
        self.butSettings.clicked.connect(self._show_settings)
        self.led_settings_NFFT.editingFinished.connect(self._update_settings_nfft)
        self.led_exception_handling.editingFinished.connect(self._set_exception_handling)

        self.butDebug.clicked.connect(self._show_debug)

        self.butFiltDict.clicked.connect(self._show_filt_dict)
        self.butFiltTree.clicked.connect(self._show_filt_tree)
        self.butDocstring.clicked.connect(self._show_doc)
        self.butRichText.clicked.connect(self._show_doc)

    # -------------------------------------------------------------------------
    def _about_window(self):
        self.about_widget = AboutWindow(self)  # important: Handle must be class attribute
        # self.opt_widget.show() # modeless dialog, i.e. non-blocking
        self.about_widget.exec_()  # modal dialog (blocking)

    # ------------------------------------------------------------------------
    def _show_debug(self):
        """
        Show / hide debug options depending on the state of the debug button
        """
        self.frm_debug.setVisible(self.butDebug.checked)

    # ------------------------------------------------------------------------
    def _show_settings(self):
        """
        Show / hide settings options depending on the state of the settings button
        """
        self.frmSettings.setVisible(self.butSettings.checked)

    # -------------------------------------------------------------------------
    def _update_settings_nfft(self):
        """ Update value for self.par1 from QLineEdit Widget"""
        CFP.conf_settings['N_FFT'] = safe_eval(
            self.led_settings_NFFT.text(), CFP.conf_settings['N_FFT'],
            sign='pos', return_type='int')
        self.led_settings_NFFT.setText(str(CFP.conf_settings['N_FFT']))
        self.emit({'data_changed': 'n_fft'})

    # -------------------------------------------------------------------------
    def _set_exception_handling(self):
        """ Update value for exception handling from QLineEdit Widget"""
        CFP.conf_settings['EXCEPTION_LEVEL'] = safe_eval(
            self.led_exception_handling.text(), CFP.conf_settings['EXCEPTION_LEVEL'],
            sign='poszero', return_type='int')
        self.led_exception_handling.setText(str(CFP.conf_settings['EXCEPTION_LEVEL']))

    # --------------------------------------------------------------------------
    def load_dict(self):
        """
        update docs and filter performance
        """
        self._show_doc()
        self._show_filt_perf()
        self._show_filt_dict()
        self._show_filt_tree()

    # --------------------------------------------------------------------------
    def _show_doc(self):
        """
        Display info from filter design file and docstring
        """
        if hasattr(ff.fil_inst, 'info'):
            if self.butRichText.checked:
                self.txt_filt_info_box.setText(publish_string(
                    self._clean_doc(ff.fil_inst.info), writer_name='html',
                    settings_overrides={'output_encoding': 'unicode'}))
            else:
                self.txt_filt_info_box.setText(textwrap.dedent(ff.fil_inst.info))
        else:
            self.txt_filt_info_box.setText("")

        if self.butDocstring.checked and hasattr(ff.fil_inst, 'info_doc'):
            if self.butRichText.checked:
                self.txt_filt_info_box.append(
                    '<hr /><b>Python module docstring:</b>\n')
                for doc in ff.fil_inst.info_doc:
                    self.txt_filt_info_box.append(publish_string(
                     self._clean_doc(doc), writer_name='html',
                     settings_overrides={'output_encoding': 'unicode'}))
            else:
                self.txt_filt_info_box.append('\nPython module docstring:\n')
                for doc in ff.fil_inst.info_doc:
                    self.txt_filt_info_box.append(self._clean_doc(doc))

        self.txt_filt_info_box.moveCursor(QTextCursor.Start)

    # -------------------------------------------------------------------------
    def _clean_doc(self, doc: str) -> str:
        """
        Split doc into list of lines, filter out any lines containing '.. versionadded::'
        as this statment cannot be parsed anymore (?).

        Remove uniform number of leading blanks from docstrings for subsequent
        processing of rich text. The first line is treated differently, _all_
        leading blanks are removed (if any). This allows for different formats
        of docstrings.

        Finally, join lines and linebreaks to a new string.
        """
        lines = [ln for ln in doc.splitlines() if ".. versionadded::" not in ln]
        return "\n" + lines[0].lstrip() + "\n" + textwrap.dedent("\n".join(lines[1:]))

    # --------------------------------------------------------------------------
    def _show_filt_perf(self):
        """
        Print filter properties in a table at frequencies of interest. When
        specs are violated, colour the table entry in red.
        """

        def _find_min_max(self, f_start, f_stop, unit='dB'):
            """
            Find minimum and maximum magnitude and the corresponding frequencies
            for the filter defined in the filter dict in a given frequency band
            [f_start, f_stop].
            """
            w = np.linspace(f_start, f_stop, CFP.conf_settings['N_FFT'])*2*np.pi
            [w, H] = sig.freqz(bb, aa, worN=w)

            f = w / (2.0 * pi)  # frequency normalized to f_S
            H_abs = abs(H)
            H_max = max(H_abs)
            H_min = min(H_abs)
            F_max = f[np.argmax(H_abs)]  # find the frequency where H_abs
            F_min = f[np.argmin(H_abs)]  # becomes max resp. min
            if unit == 'dB':
                H_max = 20*log10(H_max)
                H_min = 20*log10(H_min)
            return F_min, H_min, F_max, H_max
        # ------------------------------------------------------------------

        self.tbl_filt_perf.setVisible(self.butFiltPerf.checked)
        if self.butFiltPerf.checked:

            bb = fb_get('ba', 0)
            aa = fb_get('ba')[1]

            f_S = fb_get('f_S')

            f_lbls = []
            f_vals = []
            a_lbls = []
            a_targs = []
            a_targs_dB = []
            a_test = []
            ft = fb_get('ft')  # get filter type ('IIR', 'FIR')
            unit = fb_get('amp_specs_unit')
            unit = 'dB'  # fix this for the moment
            # construct pairs of corner frequency and corresponding amplitude
            # labels in ascending frequency for each response type
            _rt = fb_get('rt')
            if _rt in {'LP', 'HP', 'BP', 'BS', 'HIL'}:
                if _rt == 'LP':
                    f_lbls = ['F_PB', 'F_SB']
                    a_lbls = ['A_PB', 'A_SB']
                elif _rt == 'HP':
                    f_lbls = ['F_SB', 'F_PB']
                    a_lbls = ['A_SB', 'A_PB']
                elif _rt == 'BP':
                    f_lbls = ['F_SB', 'F_PB', 'F_PB2', 'F_SB2']
                    a_lbls = ['A_SB', 'A_PB', 'A_PB', 'A_SB2']
                elif _rt == 'BS':
                    f_lbls = ['F_PB', 'F_SB', 'F_SB2', 'F_PB2']
                    a_lbls = ['A_PB', 'A_SB', 'A_SB', 'A_PB2']
                elif _rt == 'HIL':
                    f_lbls = ['F_PB', 'F_PB2']
                    a_lbls = ['A_PB', 'A_PB']

            # Try to get lists of frequency / amplitude specs from the filter dict
            # that correspond to the f_lbls / a_lbls pairs defined above
            # When one of the labels doesn't exist in the filter dict, delete
            # all corresponding amplitude and frequency entries.
                err = [False] * len(f_lbls)  # initialize error list
                f_vals = []
                a_targs = []
                for i in range(len(f_lbls)):
                    try:
                        f = fb_get(f_lbls[i])
                        f_vals.append(f)
                    except KeyError as e:
                        f_vals.append('')
                        err[i] = True
                        logger.debug(e)
                    try:
                        a = fb_get(a_lbls[i])
                        a_dB = lin2unit(fb_get(a_lbls[i]), ft, a_lbls[i], unit)
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

                f_vals = np.asarray(f_vals)  # convert to numpy array

                logger.debug("F_test_labels = %s", f_lbls)

                # Calculate frequency response at test frequencies
                [w_test, a_test] = sig.freqz(bb, aa, 2.0 * pi * f_vals.astype(float))

            (F_min, H_min, F_max, H_max) = _find_min_max(self, 0, 1, unit='V')
            # append frequencies and values for min. and max. filter reponse to
            # test vector

            f_lbls += ['Min.', 'Max.']
            # QTableView does not support direct formatting, use QLabel

            f_vals = np.append(f_vals, [F_min, F_max])
            a_targs = np.append(a_targs, [np.nan, np.nan])
            a_targs_dB = np.append(a_targs_dB, [np.nan, np.nan])
            a_test = np.append(a_test, [H_min, H_max])
            # calculate response of test frequencies in dB
            a_test_dB = -20*log10(abs(a_test))

            # get filter type ('IIR', 'FIR') for dB <-> lin conversion
            ft = fb_get('ft')
            # unit = fb_get('amp_specs_unit')
            unit = 'dB'  # make this fixed for the moment

            # build a list with the corresponding target specs:
            a_targs_pass = []
            eps = 1e-3
            for i in range(len(f_lbls)):
                if 'PB' in f_lbls[i]:
                    a_targs_pass.append((a_test_dB[i] - a_targs_dB[i]) < eps)
                    a_test[i] = 1 - abs(a_test[i])
                elif 'SB' in f_lbls[i]:
                    a_targs_pass.append(a_test_dB[i] >= a_targs_dB[i])
                else:
                    a_targs_pass.append(True)

            self.targs_spec_passed = np.all(a_targs_pass)

            logger.debug(
                "H_targ = %s\n"
                "H_test = %s\n"
                "H_test_dB = %s\n"
                "F_test = %s\n"
                "H_targ_pass = %s\n"
                "passed: %s\n", a_targs,  a_test,  a_test_dB, f_vals,
                    a_targs_pass, self.targs_spec_passed)

            self.tbl_filt_perf.setRowCount(len(a_test))  # number of table rows
            self.tbl_filt_perf.setColumnCount(5)  # number of table columns

            self.tbl_filt_perf.setHorizontalHeaderLabels([
                'f/{0:s}'.format(fb_get('freq_specs_unit')), 'Spec\n(dB)',
                '|H(f)|\n(dB)', 'Spec', '|H(f)|'])
            self.tbl_filt_perf.setVerticalHeaderLabels(f_lbls)
            for row in range(len(a_test)):
                self.tbl_filt_perf.setItem(
                    row, 0, QTableWidgetItem(str(f'{(f_vals[row]*f_S):.4g}')))
                self.tbl_filt_perf.setItem(
                    row, 1, QTableWidgetItem(str(f'{-a_targs_dB[row]:2.3g}')))
                self.tbl_filt_perf.setItem(
                    row, 2, QTableWidgetItem(str(f'{-a_test_dB[row]:2.3f}')))
                if a_targs[row] < 0.01:
                    self.tbl_filt_perf.setItem(
                        row, 3, QTableWidgetItem(str(f'{a_targs[row]:.3e}')))
                else:
                    self.tbl_filt_perf.setItem(
                        row, 3, QTableWidgetItem(str(f'{a_targs[row]:2.4f}')))
                if a_test[row] < 0.01:
                    self.tbl_filt_perf.setItem(
                        row, 4, QTableWidgetItem(str(f'{abs(a_test[row]):.3e}')))
                else:
                    self.tbl_filt_perf.setItem(
                        row, 4, QTableWidgetItem(str(f'{abs(a_test[row]):.4f}')))

                if not a_targs_pass[row]:
                    self.tbl_filt_perf.item(row, 1).setBackground(QtGui.QColor('red'))
                    self.tbl_filt_perf.item(row, 3).setBackground(QtGui.QColor('red'))

            self.tbl_filt_perf.resizeColumnsToContents()
            self.tbl_filt_perf.resizeRowsToContents()

    # --------------------------------------------------------------------------
    def _show_filt_dict(self):
        """
        Print filter dict for debugging
        """
        self.txt_filt_dict.setVisible(self.butFiltDict.checked)

        fb_sorted = [str(key) + ' : ' + str(fb_get(key))
                     for key in sorted(fb_get().keys())]
        dictstr = pprint.pformat(fb_sorted)
        # dictstr = pprint.pformat(fb_get())
        self.txt_filt_dict.setText(dictstr)

    # --------------------------------------------------------------------------
    def _show_filt_tree(self):
        """
        Print filter tree for debugging
        """
        self.txt_filt_tree.setVisible(self.butFiltTree.checked)

        ftree_sorted = ['<b>' + str(key) + ' : ' + '</b>' + str(TB.fil_tree[key])
                        for key in sorted(TB.fil_tree.keys())]
        dictstr = pprint.pformat(ftree_sorted, indent=4)
#        dictstr = pprint.pformat(fb_get())
        self.txt_filt_tree.setText(dictstr)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.input_info`
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.QSS_RC)
    mainw = Input_Info()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
