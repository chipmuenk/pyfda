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
import sys
import logging

from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.compat import (
    QtCore, QWidget, QLabel, QLineEdit, QComboBox, QFrame, QFont, QSizePolicy,
    QIcon, QVBoxLayout, QHBoxLayout, QGridLayout, pyqtSignal, QEvent)
from pyfda.libs.pyfda_lib import to_html, safe_eval, first_item
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, qset_cmb_box, qcmb_box_populate, emit
from pyfda.libs.pyfda_qt_classes import PushButton
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

logger = logging.getLogger(__name__)

class FreqUnits(QWidget):
    """
    Build and update widget for entering frequency unit, frequency range and
    sampling frequency f_S

    The following key-value pairs of the `fil[0]` dict are modified:

        - `'freq_specs_unit'` : The unit ('f_S', 'f_Ny', 'Hz' etc.) as a string
        - `'freqSpecsRange'` : A list with two entries for minimum and maximum frequency
                               values for labelling the frequency axis
        - `'f_S'` : The sampling frequency for referring frequency values to as a float
        - `'f_max'` : maximum frequency for scaling frequency axis
        - `'plt_fUnit'`: frequency unit as string
        - `'plt_tUnit'`: time unit as string
        - `'plt_fLabel'`: label for frequency axis
        - `'plt_tLabel'`: label for time axis

    """
    # class variables (shared between instances if more than one exists)
    # incoming:
    sig_rx = pyqtSignal(object)
    # outgoing: from various and when normalized frequencies have been changed
    sig_tx = pyqtSignal(object)  # outgoing

    def __init__(self, title: str = "Frequency Units", objectName: str = ""):

        super().__init__()
        self.title = title
        self.setObjectName(objectName)
        self.spec_edited = False  # flag whether QLineEdit field has been edited

        # combobox tooltip + data / text / tooltip for frequency unit
        self.cmb_f_unit_items = [
            "<span>Select whether frequencies are specified w.r.t. the sampling "
            "frequency " + to_html("f_S", frmt = 'i') + ", to the Nyquist frequency "
            + to_html("f_Ny = f_S", frmt='i') + "/2 or as absolute values.",
            ("fs", "f_S", "Relative to sampling frequency, "
             + to_html("F = f / f_S", frmt='i')),
            ("fny", "f_Ny", "Relative to Nyquist frequency, "
             + to_html("F = f / f_Ny = 2f / f_S", frmt='i')),
            # ("k", "k", "Frequency index " + to_html("k = 0 ... N_FFT - 1", frmt='i')),
            ("mhz", "mHz", "Absolute sampling frequency in mHz"),
            ("hz", "Hz", "Absolute sampling frequency in Hz"),
            ("khz", "kHz", "Absolute sampling frequency in kHz"),
            ("meghz", "MHz", "Absolute sampling frequency in MHz"),
            ("ghz", "GHz", "Absolute sampling frequency in GHz")
        ]
        self.cmb_f_unit_init = "fs"

        self.cmb_f_range_items = [
            "Select one- or two-sided spectrum and symmetry around <i>f</i> = 0",
            ("half", "0...½", "One-sided spectrum"),
            ("whole", "0...1", "Two-sided spectrum, starting at <i>f</i> = 0"),
            ("sym", "-½...½", "Two-sided spectrum, symmetrical around <i>f</i> = 0")
            ]
        self.cmb_f_range_init = "half"

        # t_units and f_scale have the same index as the f_unit_items, i.e.
        # 'f_S', 'f_Ny', 'mHz', 'Hz', 'kHz', 'MHz', 'GHz'
        self.t_units = ['T_S', 'T_S', 'ks', 's', 'ms', r'$\mu$s', 'ns']
        self.f_scale = [1., 1., 1e-3, 1., 1e3, 1e6, 1e9]

        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig: dict) -> None:
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # --------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict) -> None:
        """
        Process signals coming from
        - FFT window widget
        - qfft_win_select
        """

        logger.debug("SIG_RX: %s", first_item(dict_sig))

        if 'id' in dict_sig and dict_sig['id'] == id(self):
            logger.debug("Stopped infinite loop")
            return
        if ('view_changed' in dict_sig and dict_sig['view_changed'] == 'f_S')\
            or 'data_changed' in dict_sig:
            self.update_UI(emit_signal=False)

# ------------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Construct the User Interface
        """
        self.layVMain = QVBoxLayout() # Widget main layout

        bfont = QFont()
        bfont.setBold(True)

        self.lbl_units = QLabel(self)
        self.lbl_units.setText("Freq. Unit")
        self.lbl_units.setFont(bfont)

        self.f_s_old = fb_get('f_S')  # store current sampling frequency
        self.T_s_old = fb_get('T_S')  # store current sampling period

        self.lbl_f_s = QLabel(self)
        self.lbl_f_s.setText(to_html("f_S =", frmt='bi'))

        self.led_f_s = QLineEdit(objectName='f_S')
        self.led_f_s.setText(str(fb_get('f_S')))
        self.led_f_s.installEventFilter(self)  # filter events

        self.butLock = PushButton(self, icon=QIcon(':/lock-unlocked.svg'))
        self.butLock.setToolTip(
            "<span><b>Unlocked:</b> When <i>f<sub>S</sub></i> is changed, all frequency "
            "related widgets are updated, normalized frequencies stay the same.<br />"
            "<b>Locked:</b> When <i>f<sub>S</sub></i> is changed, displayed absolute "
            "frequency values don't change but normalized frequencies do.</span>")

        lay_h_f_s = QHBoxLayout()
        lay_h_f_s.addWidget(self.led_f_s)
        lay_h_f_s.addWidget(self.butLock)

        self.cmb_f_units = QComboBox(self, objectName="cmb_f_units")
        qcmb_box_populate(self.cmb_f_units, self.cmb_f_unit_items, self.cmb_f_unit_init)
#        self.cmb_f_units.setItemData(0, (0,QColor("#FF333D"),Qt.BackgroundColorRole))#
#        self.cmb_f_units.setItemData(0, (QFont('Verdana', bold=True), Qt.FontRole)

        self.cmb_f_range = QComboBox(self, objectName="cmb_f_range")
        qcmb_box_populate(self.cmb_f_range, self.cmb_f_range_items,
                          self.cmb_f_range_init)

        # Combobox resizes with longest entry
        self.cmb_f_units.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmb_f_range.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.but_sort = PushButton(self, icon=QIcon(':/sort-ascending.svg'))
        self.but_sort.setChecked(True)
        self.but_sort.setToolTip("Sort frequencies in ascending order when activated.")
        self.but_sort.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.layHUnits = QHBoxLayout()
        self.layHUnits.addWidget(self.cmb_f_units)
        self.layHUnits.addWidget(self.cmb_f_range)
        self.layHUnits.addWidget(self.but_sort)

        # Create a gridLayout consisting of QLabel and QLineEdit fields
        # for setting f_S, the units and the actual frequency specs:
        self.layGSpecWdg = QGridLayout()  # sublayout for spec fields
        self.layGSpecWdg.addWidget(self.lbl_f_s, 1, 0)
        # self.layGSpecWdg.addWidget(self.led_f_s,1,1)
        self.layGSpecWdg.addLayout(lay_h_f_s, 1, 1)
        self.layGSpecWdg.addWidget(self.lbl_units, 0, 0)
        self.layGSpecWdg.addLayout(self.layHUnits, 0, 1)

        frm_main = QFrame(self)
        frm_main.setLayout(self.layGSpecWdg)

        self.layVMain.addWidget(frm_main)
        self.layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(self.layVMain)

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # swallow index passed by "IndexChanged":
        self.cmb_f_units.currentIndexChanged.connect(lambda: self.update_UI(self))
        self.butLock.clicked.connect(self._lock_freqs)
        self.cmb_f_range.currentIndexChanged.connect(self._freq_range)
        self.but_sort.clicked.connect(self._store_sort_flag)
        # ----------------------------------------------------------------------

        self.update_UI()  # first-time initialization

# -------------------------------------------------------------
    def _lock_freqs(self) -> None:
        """
        Lock / unlock frequency entries: The values of frequency related widgets
        are stored in normalized form (w.r.t. sampling frequency)`fil[0]['f_S']`.

        When the sampling frequency changes, absolute frequencies displayed in the
        widgets change their values. Most of the time, this is the desired behaviour,
        the properties of discrete time systems or signals are usually defined
        by the normalized frequencies.

        When the effect of varying the sampling frequency is to be analyzed, the
        displayed values in the widgets can be locked by pressing the Lock button.
        After changing the sampling frequency, normalized frequencies have to be
        rescaled like `f_a *= fil[0]['f_S_prev'] / fil[0]['f_S']` to maintain
        the displayed value `f_a * f_S`.

        This has to be accomplished by each frequency widget (currently, these are
        freq_specs and plot_tran_stim) when receiving the signal {'view_changed': 'f_S'}.

        The setting is stored as bool in the global dict entry `fil[0]['freq_locked']`.
        No signal is emitted because there is no immediate need for action, all the values
        remain unchanged.
        """

        if self.butLock.checked:
            # Lock has been activated, keep displayed frequencies locked
            fb_set('freq_locked', True)
            self.butLock.setIcon(QIcon(':/lock-locked.svg'))
        else:
            # Lock has been unlocked, scale displayed frequencies with f_S
            fb_set('freq_locked', False)
            self.butLock.setIcon(QIcon(':/lock-unlocked.svg'))

# -------------------------------------------------------------
    def update_UI(self, emit_signal: bool = True) -> None:
        """
        update_UI is called
        - during init (direct call)
        - when the unit combobox is changed (signal-slot)
        - when a signal {'view_changed': 'f_S'} or {'data_changed': ...} has been
          received. In this case, the UI is updated from the fil[0] dictionary
          and no signal is emitted (`emit_signal==False`).

        Set various scale factors and labels depending on the setting of the unit
        combobox.

        Update the freqSpecsRange and finally, emit 'view_changed':'f_S' signal
        """
        if not emit_signal:  # triggered by function call, not by a change of UI
            # Load f_S display from dict
            self.led_f_s.setText(str(fb_get('f_S')))
            # Load freq. unit setting from dict
            idx = qset_cmb_box(self.cmb_f_units, fb_get('freq_specs_unit'),
                               caseSensitive=True)
            if idx == -1:
                logger.warning(
                    "Unknown frequency unit %s, using 'f_S'.",
                    fb_get('freq_specs_unit')
                )
            # Load Frequency range type (0 ... f_S/2 etc.) from dict
            qset_cmb_box(self.cmb_f_range, fb_get('freqSpecsRangeType'),
                         data=True, fireSignals=True)

        f_unit = qget_cmb_box(self.cmb_f_units, data=False)  # selected frequency unit,
        idx = self.cmb_f_units.currentIndex()  # its index
        f_s_scale = self.f_scale[idx]  # and its scaling factor

        is_normalized_freq = f_unit in {"f_S", "f_Ny"}

        self.led_f_s.setVisible(not is_normalized_freq)  # only vis. when
        self.lbl_f_s.setVisible(not is_normalized_freq)  # not normalized
        self.butLock.setVisible(not is_normalized_freq)

        if is_normalized_freq:
            # store current sampling frequency to restore it when returning to
            # absolute (not normalized) frequencies
            if f_unit == "f_S":  # normalized to f_S
                fb_set('f_S', 1.)
                fb_set('f_max', 1.)
                f_label = r"$F = f\, /\, f_S = \Omega \, /\,  2 \mathrm{\pi} \; \rightarrow$"
            elif f_unit == "f_Ny":  # normalized to f_nyq = f_S / 2
                fb_set('f_S', 2.)
                fb_set('f_max', 2.)
                f_label = r"$F = 2f \, / \, f_S = \Omega \, / \, \mathrm{\pi} \; \rightarrow$"
            else: # frequency index k,
                logger.error("Unit k is no longer supported!")

            # always use T_S = 1 for normalized frequencies
            fb_set('T_S', 1.)
            t_label = r"$n = t\, /\, T_S \; \rightarrow$"

            # Don't lock frequency scaling with normalized frequencies
            fb_set('freq_locked', False)
            self.butLock.setIcon(QIcon(':/lock-unlocked.svg'))

        else:  # Hz, kHz, ...
            # Restore sampling frequency when selecting absolute instead of
            # normalized frequencies

            if fb_get('freq_specs_unit') in {"f_S", "f_Ny"}:  # previous setting normalized?
                fb_set('f_S', self.f_s_old)
                fb_set('f_max', self.f_s_old) # yes, restore prev. f_S
                fb_set('T_S', self.T_s_old)  # yes, restore prev. T_S

            # --- try to pick the most suitable unit for f_S --------------
            f_S = fb_get('f_S') * f_s_scale
            if f_S >= 1e9:
                f_unit = "GHz"
            elif f_S >= 1e6:
                f_unit = "MHz"
            elif f_S >= 1e3:
                f_unit = "kHz"
            elif f_S >= 1:
                f_unit = "Hz"
            else:
                f_unit = "mHz"

            new_idx = qset_cmb_box(self.cmb_f_units, f_unit, caseSensitive=True)
            if new_idx != idx:
                # sampling frequency unit has been changed, f_S and T_S need to be scaled
                idx = new_idx
                f_s_scale = self.f_scale[idx]
                fb_set('f_S', f_S / f_s_scale)
                fb_get('T_S', f_s_scale / f_S)
                emit_signal = True
            # -------------------------------------------------------------
            self.f_s_old = fb_get('f_S')
            self.T_s_old = fb_get('T_S')
            self.led_f_s.setText(params['FMT'].format(fb_get('f_S')))

            f_label = r"$f$ in " + f_unit + r"$\; \rightarrow$"
            t_label = r"$t$ in " + self.t_units[idx] + r"$\; \rightarrow$"

        # fb_set('f_s_scale', f_s_scale)  # scale factor for f_S (Hz, kHz, ...)
        # fb_set('freq_specs_unit', f_unit)  # frequency unit
        # # time and frequency unit as string e.g. for plot axis labeling
        # fb_set('plt_fUnit', f_unit)
        # fb_set('plt_tUnit', self.t_units[idx])
        # # complete plot axis labels including unit and arrow
        # fb_set('plt_fLabel', f_label)
        # fb_set('plt_tLabel', t_label)

        fb_set(
            {'f_s_scale': f_s_scale,  # scale factor for f_S (Hz, kHz, ...)
            'freq_specs_unit': f_unit,  # frequency unit
            'plt_fUnit': f_unit,  # time and frequency unit as string, e.g.
            'plt_tUnit': self.t_units[idx],  #  for plot axis labeling
            'plt_fLabel': f_label,  # plot axis labels including unit and arrow
            'plt_tLabel': t_label}
            )

        self._freq_range(emit_signal=False)  # update f_lim setting without emit_signalting signal
        if emit_signal:  # UI was updated by user or a rescaling of f_S
            self.emit({'view_changed': 'f_S'})

# ------------------------------------------------------------------------------
    def eventFilter(self, source: QtCore.QObject, event: QEvent) -> bool:

        """
        Filter all events generated by the QLineEdit `f_S` widget. Source and type
        of all events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (QEvent.FocusIn`), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (QEvent.FocusOut`), store
          current value with full precision (only if `spec_edited`== True) and
          display the stored value in selected format. Emit 'view_changed':'f_S'
        - When f_S has been changed, update `fil[0]['f_S']`,
          emit `{'view_changed': 'f_S'}` to update other widgets and only *then*
          update {'f_S_prev': fil[0]['f_S']} to allow correction of normalized
          frequency with the old value of f_S.
        """
        def _store_entry() -> None:
            """
            Update filter dictionary with sampling frequency and related parameters
            and emit `{'view_changed': 'f_S'}`.
            """
            if self.spec_edited:
                f_S_tmp = safe_eval(source.text(), fb_get('f_S'), sign='pos')
                fb_set('f_S', f_S_tmp)
                fb_set('T_S', 1./f_S_tmp)
                fb_set('f_max', f_S_tmp)

                self._freq_range(emit_signal=False)  # update plotting range
                self.emit({'view_changed': 'f_S'})
                # Now store current f_S as f_S_prev
                fb_set('f_S_prev', fb_get('f_S'))

                self.spec_edited = False  # reset flag, changed entry has been saved
        # ----------------------
        if source.objectName() == 'f_S':
            if event.type() == QEvent.FocusIn:
                self.spec_edited = False
                source.setText(str(fb_get('f_S')))  # full precision
            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True  # entry has been changed
                key = event.key()
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}:
                    _store_entry()
                elif key == QtCore.Qt.Key_Escape:  # revert changes
                    self.spec_edited = False
                    source.setText(str(fb_get('f_S')))  # full precision
            elif event.type() == QEvent.FocusOut:
                _store_entry()
                source.setText(params['FMT'].format(fb_get('f_S')))  # reduced prec.

            # Call base class method to continue normal event processing:
        return super().eventFilter(source, event)

    # -------------------------------------------------------------
    def _freq_range(self, emit_signal: bool = True) -> None:
        """
        Set frequency plotting range for single-sided spectrum up to f_S/2 or f_S
        or for double-sided spectrum between -f_S/2 and f_S/2

        Emit 'view_changed':'f_range' when `emit_signal=True`
        """
        if isinstance(emit_signal, int):  # signal was emitted by combobox
            emit_signal = True

        rangeType = qget_cmb_box(self.cmb_f_range)

        fb_set('freqSpecsRangeType', rangeType)
        f_max = fb_get('f_max')

        if rangeType == 'whole':
            f_lim = [0, f_max]
        elif rangeType == 'sym':
            f_lim = [-f_max/2., f_max/2.]
        else:
            f_lim = [0, f_max/2.]

        fb_set('freqSpecsRange', f_lim)  # store settings in dict

        if emit_signal:
            self.emit({'view_changed': 'f_range'})

    # -------------------------------------------------------------
    def dict2ui(self) -> None:
        """
        Reload comboBox settings and textfields from filter dictionary
        Block signals during update of combobox / lineedit widgets
        This is called via `input_specs.dict2ui()`
        """
        self.update_UI(emit_signal=False)
        # This updates the following widgets:
        # - `self.led_f_s` from `fb_get('f_S')`
        # - `self.cmb_f_units` with `fb_get('freq_specs_unit')`
        # - `self.cmb_f_range` from `fb_get('freqSpecsRangeType')``
        # The other widgets are updated automatically.

# -------------------------------------------------------------
    def _store_sort_flag(self) -> None:
        """
        Store sort flag in filter dict and emit 'specs_changed':'f_sort'
        when sort button is checked.
        """
        fb_set('freq_specs_sort', self.but_sort.checked)
        if self.but_sort.checked:
            self.emit({'specs_changed': 'f_sort'})

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.freq_units`
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.QSS_RC)
    mainw = FreqUnits()
    app.setActiveWindow(mainw)
    mainw.update_UI()
#    mainw.updateUI(newLabels = ['F_PB','F_PB2'])

    mainw.show()
    sys.exit(app.exec_())
