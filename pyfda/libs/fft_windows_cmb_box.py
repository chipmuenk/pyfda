# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

import importlib
import copy
import numpy as np
import scipy.signal as sig
import scipy

import pyfda.filterbroker as fb
from .pyfda_qt_lib import qcmb_box_populate, qset_cmb_box, qget_cmb_box
from .pyfda_lib import to_html, safe_eval, pprint_log
from pyfda.pyfda_rc import params
from .compat import (QWidget, QLabel, QComboBox, QLineEdit,
                     QHBoxLayout, pyqtSignal)

from pyfda.libs.pyfda_fft_windows_lib import all_wins_dict_ref

import logging
logger = logging.getLogger(__name__)

# =============================================================================
class QFFTWinSelector(QWidget):
    """
    When no dict is passed to the constructor, build a combo box with window types from
    a deep copy of the `all_wins_dict_ref`, restricted to suitable types for `app`
    applications.

    When a dict is passed to the constructor, work with this dictionary and build the
    combo box from all the dict entries.
    """
    sig_rx = pyqtSignal(object)  # incoming
    sig_tx = pyqtSignal(object)  # outgoing

    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, cur_win_dict: dict, app: str = 'spec', all_wins_dict: dict = {},
                 objectName: str = ""):
        super().__init__()

        self.setObjectName(objectName)
        # key for storing / retrieving filter data from `fb.fil[0]['filter_widgets']`
        self.cur_win_dict = cur_win_dict
        self.err = False  # error flag for window calculation

        if all_wins_dict == {}:
            # construct combobox data from all_wins_dict_ref and app type,
            # remove unneeded key:value pairs
            self.all_wins_dict = copy.deepcopy(all_wins_dict_ref)
            self.cmb_win_fft_items = ["<span>Select window type</span>"]
            for k, v in all_wins_dict_ref.items():
                if app in v['app']:
                    self.cmb_win_fft_items.append((k, v['disp_name'], v['info']))
        else:
            # construct combobox data from passed dict
            self.all_wins_dict = all_wins_dict
            self.cmb_win_fft_items = ["<span>Select window type</span>"]
            for k, v in all_wins_dict.items():
                if 'disp_name' in v and 'info' in v:
                    self.cmb_win_fft_items.append((k, v['disp_name'], v['info']))

        self.win_fnct = None  # handle to windows function

        self._construct_UI()
        self.set_window_name()  # initialize win_dict
        self.ui2win_dict()

    # --------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the widget one hierarchy higher to update
        the widgets from the dictionary

        """
        # logger.debug("SIG_RX:\n{0}".format(pprint_log(dict_sig)))

        if dict_sig['id'] == id(self):
            return  # signal has been emitted from same instance

        elif 'view_changed' in dict_sig:
            if dict_sig['view_changed'] == 'fft_win_par':
                self.dict2ui_params()
            elif dict_sig['view_changed'] == 'fft_win_type':
                self.dict2ui()

    # --------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Create the FFT window selection widget, consisting of:
        - combobox for windows
        - 0 or more parameter fields
        """
        # Construct FFT window type combobox
        self.cmb_win_fft = QComboBox(self)
        qcmb_box_populate(self.cmb_win_fft, self.cmb_win_fft_items,
                          self.cur_win_dict['id'])

        # Variant of FFT window type (not implemented yet)
        self.cmb_win_fft_variant = QComboBox(self)
        self.cmb_win_fft_variant.setToolTip("FFT window variant.")
        self.cmb_win_fft_variant.setVisible(False)

        # First numeric parameter for FFT window
        self.lbl_win_par_0 = QLabel("Param1")
        self.led_win_par_0 = QLineEdit(self, objectName="ledWinPar1")
        self.led_win_par_0.setText("1")
        self.cmb_win_par_0 = QComboBox(self)

        # Second numeric parameter for FFT window
        self.lbl_win_par_1 = QLabel("Param2")
        self.led_win_par_1 = QLineEdit(self, objectName="ledWinPar2")
        self.led_win_par_1.setText("2")
        self.cmb_win_par_1 = QComboBox(self)

        layH_main = QHBoxLayout(self)
        layH_main.addWidget(self.cmb_win_fft)
        layH_main.addWidget(self.cmb_win_fft_variant)
        layH_main.addWidget(self.lbl_win_par_0)
        layH_main.addWidget(self.led_win_par_0)
        layH_main.addWidget(self.cmb_win_par_0)
        layH_main.addWidget(self.lbl_win_par_1)
        layH_main.addWidget(self.led_win_par_1)
        layH_main.addWidget(self.cmb_win_par_1)

        layH_main.setContentsMargins(*params['wdg_margins'])  # (left, top, right, bottom)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # careful! currentIndexChanged passes an integer (the current index)
        # to update_win
        self.cmb_win_fft.currentIndexChanged.connect(self.ui2win_dict_emit)
        self.led_win_par_0.editingFinished.connect(self.ui2dict_params)
        self.led_win_par_1.editingFinished.connect(self.ui2dict_params)
        self.cmb_win_par_0.currentIndexChanged.connect(self.ui2dict_params)
        self.cmb_win_par_1.currentIndexChanged.connect(self.ui2dict_params)

# ------------------------------------------------------------------------------
    def set_window_name(self, win_id: str = "") -> bool:
        """
        Select and set a window function object from its string `win_id` and update the
        `cur_win_dict` dictionary correspondingly.

        Additionally, the following class attributes are updated / reset:

        self.win_fnct = win_fnct            # handle to windows functionn

        Also, update the keys 'par' and 'id' of `fb.fil[0][self.key_fil]`

        The above is only updated when the window type has been changed compared to
        `self.cur_win_dict['id']` !

        Parameters
        ----------
        win_id : str
            Id of the window, which will be looked up in `self.all_wins_dict`. If empty,
            use `self.cur_win_dict['id']` instead.

        Returns
        -------
        win_err : bool
            Error flag; `True` when `win_id` could not be resolved
        """
        if win_id == "":
            cur_win_id = self.cur_win_dict['id']

        elif win_id not in self.all_wins_dict:
            logger.warning(
                f'Unknown window id "{win_id}", using rectangular window instead.')
            cur_win_id = "rectangular"
        else:
            cur_win_id = win_id

        fn_name = self.all_wins_dict[cur_win_id]['fn_name']

        # --------------------------------------
        # get attribute fn_name from submodule (default: sig.windows) and
        # return the desired window function:
        win_err = False
        mod_fnct = fn_name.split('.')  # try to split fully qualified name at "."
        fnct = mod_fnct[-1]  # last / rightmost part = function name
        if len(mod_fnct) == 1:
            # only one element, no module name given -> use scipy.signal.windows
            win_fnct = getattr(sig.windows, fnct, None)
            if not win_fnct:
                logger.error(f'No window function "{fn_name}" in scipy.signal.windows, '
                            'using rectangular window instead!')
                win_err = True
        else:
            # extract module name from fully qualified name, starting with first /
            # leftmost part of string to the last '.'
            mod_name = fn_name[:fn_name.rfind(".")]
            try:
                mod = importlib.import_module(mod_name)
                win_fnct = getattr(mod, fnct, None)
            except ImportError:  # no valid module
                logger.error(f'Found no valid module "{mod_name}", '
                            'using rectangular window instead!')
                win_err = True
            except NameError:
                logger.error(f'Found no valid window function "{fn_name}", '
                            'using rectangular window instead!')
                win_err = True

        if win_err:
            # an eror occurred, fall back to rectangular window
            win_fnct = getattr(sig.windows, 'boxcar', None)
            self.cur_win_dict['id'] = "rectangular"
            self.cur_win_dict['disp_name'] = "Rectangular"
            self.cur_win_dict['par'] = []
        else:
            # self.all_wins_dict.update({'cur_win_name': cur_win_id})
            self.win_fnct = win_fnct  # handle to windows function
            self.cur_win_dict['id'] = cur_win_id
            self.cur_win_dict['disp_name'] = self.all_wins_dict[cur_win_id]['disp_name']
            self.cur_win_dict['par'] = self.all_wins_dict[cur_win_id]['par']

        return win_err  # error flag, UI (window combo box) needs to be updated

# ------------------------------------------------------------------------------
    def get_window(self, N: int, win_id: str = None, sym: bool = False) -> np.array:
        """
        Calculate the selected window function with `N` points.

        Parameters
        ----------
        N : int
            Number of data points

        win_id : str, optional
            Id of the window. If specified (default is None), this will be used to
            obtain the window function, its parameters and tool tips etc. via
            `set_window_name()`. If not, the previous setting are used.

            If some kind of error occurs during calculation of the window, a rectangular
            window is used as a fallback and the class attribute `self.err` is
            set to `True`.

        sym : bool, optional
            When True, generate a symmetric window for filter design.
            When False (default), generate a periodic window for spectral analysis.

        Returns
        -------
        win_fnct : ndarray
            The window function with `N` data points (should be normalized to 1).
            Additionally, the normalized equivalent noise bandwidth is calculated and
            stored as `self.all_wins_dict['nenbw']` as well as the 
            correlated gain `self.all_wins_dict['cgain']`.
        """
        self.err = False
        logger.warning("get window")

        # window name is empty, use window function from filter dict
        if win_id is None:
            win_id = self.cur_win_dict['id']

        fn_name = self.all_wins_dict[win_id]['fn_name']
        n_par = len(self.all_wins_dict[win_id]['par'])

        try:
            if fn_name == 'dpss':
                w = scipy.signal.windows.dpss(N, self.all_wins_dict[win_id]['par'][0]['val'],
                                              sym=sym)
            elif n_par == 0:
                w = self.win_fnct(N, sym=sym)
            elif n_par == 1:
                w = self.win_fnct(N, self.all_wins_dict[win_id]['par'][0]['val'], sym=sym)
            elif n_par == 2:
                w = self.win_fnct(N, self.all_wins_dict[win_id]['par'][0]['val'],
                             self.all_wins_dict[win_id]['par'][1]['val'], sym=sym)
            else:
                logger.error(
                    "{0:d} parameters are not supported for windows at the moment!"
                    .format(n_par))
                w = None
        except Exception as e:
            logger.error('An error occurred calculating the window function "{0}":\n{1}'
                         .format(fn_name, e))
            w = None
        if w is None:  # Fall back to rectangular window
            self.err = True
            logger.warning('Falling back to rectangular window.')
            self.set_window_name("rectangular")
            w = np.ones(N)

        nenbw = N * np.sum(np.square(w)) / (np.square(np.sum(w)))
        cgain = np.sum(w) / N  # coherent gain / DC average

        self.all_wins_dict.update({'nenbw': nenbw, 'cgain': cgain})

        return w

# ------------------------------------------------------------------------------
    def dict2ui(self):
        """
        The `win_dict` dictionary has been updated somewhere else, now update the window
        selection widget and make corresponding parameter widgets visible if
        `self.cur_win_dict['id']` is different from current combo box entry:

        - set FFT window type combobox from `self.cur_win_dict['id']`
        - use `ui2win_dict()` to update parameter widgets for new window type
          from `self.all_wins_dict` without emitting a signal
        """
        if qget_cmb_box(self.cmb_win_fft, data=True) == self.cur_win_dict['id']:
            return
        else:
            qset_cmb_box(self.cmb_win_fft, self.cur_win_dict['id'], data=True)
            self.ui2win_dict()

# ------------------------------------------------------------------------------
    def dict2ui_params(self):
        """
        Set parameter values from `win_dict`

        TODO: take params from self.cur_win_dict?
        """
        cur_win_id = qget_cmb_box(self.cmb_win_fft, data=True)
        n_par = len(self.all_wins_dict[cur_win_id]['par'])

        if n_par > 0:
            if 'list' in self.all_wins_dict[cur_win_id]['par'][0]:
                qset_cmb_box(self.cmb_win_par_0, str(self.all_wins_dict[cur_win_id]['par'][0]['val']))
            else:
                self.led_win_par_0.setText(str(self.all_wins_dict[cur_win_id]['par'][0]['val']))

        if n_par > 1:
            if 'list' in self.all_wins_dict[cur_win_id]['par'][1]:
                qset_cmb_box(self.cmb_win_par_1, str(self.all_wins_dict[cur_win_id]['par'][1]['val']))
            else:
                self.led_win_par_1.setText(str(self.all_wins_dict[cur_win_id]['par'][1]['val']))

# ------------------------------------------------------------------------------
    def ui2dict_params(self):
        """
        Read out window parameter widget(s) when editing is finished and
        update self.cur_win_dict and self.all_wins_dict with the parameter values.

        Emit 'view_changed': 'fft_win_par'
        """
        cur_win_id = qget_cmb_box(self.cmb_win_fft, data=True)  # current window id / key

        if len(self.all_wins_dict[cur_win_id]['par']) > 1:
            if 'list' in self.all_wins_dict[cur_win_id]['par'][1]:
                param = qget_cmb_box(self.cmb_win_par_1, data=False)
            else:
                param = safe_eval(self.led_win_par_1.text(),
                                  self.all_wins_dict[cur_win_id]['par'][1]['val'],
                                  return_type='float')
                if param < self.all_wins_dict[cur_win_id]['par'][1]['min']:
                    param = self.all_wins_dict[cur_win_id]['par'][1]['min']
                elif param > self.all_wins_dict[cur_win_id]['par'][1]['max']:
                    param = self.all_wins_dict[cur_win_id]['par'][1]['max']
                self.led_win_par_1.setText(str(param))
            self.all_wins_dict[cur_win_id]['par'][1]['val'] = param
            self.cur_win_dict['par'][1]['val'] = param

        if len(self.all_wins_dict[cur_win_id]['par']) > 0:
            if 'list' in self.all_wins_dict[cur_win_id]['par'][0]:
                param = qget_cmb_box(self.cmb_win_par_0, data=False)
            else:
                param = safe_eval(self.led_win_par_0.text(),
                                  self.all_wins_dict[cur_win_id]['par'][0]['val'],
                                  return_type='float')
                if param < self.all_wins_dict[cur_win_id]['par'][0]['min']:
                    param = self.all_wins_dict[cur_win_id]['par'][0]['min']
                elif param > self.all_wins_dict[cur_win_id]['par'][0]['max']:
                    param = self.all_wins_dict[cur_win_id]['par'][0]['max']
                self.led_win_par_0.setText(str(param))
            self.all_wins_dict[cur_win_id]['par'][0]['val'] = param
            self.cur_win_dict['par'][0]['val'] = param

        self.emit({'view_changed': 'fft_win_par'})

# ------------------------------------------------------------------------------
    def ui2win_dict_emit(self, arg=None) -> None:
        """
        Triggered during initialization and by the window type combo box
        - read FFT window type combo box and update win_dict using `set_window_name()`,
          update parameter widgets accordingly
        - emit 'view_changed': 'fft_win_type'
        """
        self.ui2win_dict()
        self.emit({'view_changed': 'fft_win_type'})

# ------------------------------------------------------------------------------
    def ui2win_dict(self) -> None:
        """
        - read FFT window type combo box and update win_dict using `set_window_name()`
        - determine number of parameters and make lineedit or combobox fields visible
        - set tooltipps and parameter values from dict
        - update `cur_win_dict` and `all_wins_dict`
        """
        cur_win_id = qget_cmb_box(self.cmb_win_fft, data=True)
        err = self.set_window_name(cur_win_id)
        logger.warning(f"{self.objectName()}: cmb_win_fft = {cur_win_id}")
        logger.warning(f"cur_win_id = {self.cur_win_dict['id']}")
        # if selected window does not exist (`err = True`) or produces errors, fall back
        # to 'cur_win_id'
        if err:
            cur_win_id = self.cur_win_dict['id']
            qset_cmb_box(self.cmb_win_fft, cur_win_id, data=True)

        # update visibility and values of parameter widgets:
        n_par = len(self.all_wins_dict[cur_win_id]['par'])

        self.lbl_win_par_0.setVisible(n_par > 0)
        self.led_win_par_0.setVisible(False)
        self.cmb_win_par_0.setVisible(False)

        self.lbl_win_par_1.setVisible(n_par > 1)
        self.led_win_par_1.setVisible(False)
        self.cmb_win_par_1.setVisible(False)

        if n_par > 0:
            self.lbl_win_par_0.setText(
                to_html(self.all_wins_dict[cur_win_id]['par'][0]['name'] + " =", frmt='bi'))
            if 'list' in self.all_wins_dict[cur_win_id]['par'][0]:
                self.led_win_par_0.setVisible(False)
                self.cmb_win_par_0.setVisible(True)
                self.cmb_win_par_0.blockSignals(True)
                self.cmb_win_par_0.clear()
                self.cmb_win_par_0.addItems(self.all_wins_dict[cur_win_id]['par'][0]['list'])
                qset_cmb_box(self.cmb_win_par_0, str(self.all_wins_dict[cur_win_id]['par'][0]['val']))
                self.cmb_win_par_0.setToolTip(
                    self.all_wins_dict[cur_win_id]['par'][0]['tooltip'])
                self.cmb_win_par_0.blockSignals(False)
            else:
                self.led_win_par_0.setVisible(True)
                self.cmb_win_par_0.setVisible(False)
                self.led_win_par_0.setText(
                    str(self.all_wins_dict[cur_win_id]['par'][0]['val']))
                self.led_win_par_0.setToolTip(
                    self.all_wins_dict[cur_win_id]['par'][0]['tooltip'])

        if n_par > 1:
            self.lbl_win_par_1.setText(
                to_html(self.all_wins_dict[cur_win_id]['par'][1]['name'] + " =", frmt='bi'))
            if 'list' in self.all_wins_dict[cur_win_id]['par'][1]:
                self.led_win_par_1.setVisible(False)
                self.cmb_win_par_1.setVisible(True)
                self.cmb_win_par_1.blockSignals(True)
                self.cmb_win_par_1.clear()
                self.cmb_win_par_1.addItems(self.all_wins_dict[cur_win_id]['par'][1]['list'])
                qset_cmb_box(self.cmb_win_par_1, str(self.all_wins_dict[cur_win_id]['par'][1]['val']))
                self.cmb_win_par_1.setToolTip(self.all_wins_dict[cur_win_id]['par'][1]['tooltip'])
                self.cmb_win_par_1.blockSignals(False)
            else:
                self.led_win_par_1.setVisible(True)
                self.cmb_win_par_1.setVisible(False)
                self.led_win_par_1.setText(str(self.all_wins_dict[cur_win_id]['par'][1]['val']))
                self.led_win_par_1.setToolTip(self.all_wins_dict[cur_win_id]['par'][1]['tooltip'])

        self.cur_win_dict['id'] = cur_win_id
        self.cur_win_dict['disp_name'] = self.all_wins_dict[cur_win_id]['disp_name']
        self.cur_win_dict['par'] = self.all_wins_dict[cur_win_id]['par']

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    """ Run widget standalone with `python -m pyfda.libs.fft_windows_cmb_box` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = QFFTWinSelector(app='spec', objectName='TestName')
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
