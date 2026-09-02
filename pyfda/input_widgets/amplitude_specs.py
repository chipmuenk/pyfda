# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)
#####################################################
#
# Widget for entering amplitude specifications
#
# Author: Christian Münker
######################################################
"""
Subwidget for entering amplitude specifications
"""

import sys
import logging

from pyfda.libs.compat import (
    QtCore, Qt, QEvent, pyqtSignal, QWidget, QLabel, QLineEdit, QComboBox, QFrame,
    QFont, QVBoxLayout, QHBoxLayout, QGridLayout)

from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.pyfda_lib import to_html, safe_eval, pprint_log, first_item
from pyfda.libs.special_functions import lin2unit, unit2lin
from pyfda.libs.pyfda_qt_lib import qstyle_widget, qget_cmb_box, emit
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

logger = logging.getLogger(__name__)

class AmplitudeSpecs(QWidget):
    """
    Build and update widget for entering the amplitude
    specifications like a_sb, a_pb etc.
    """
    sig_rx = pyqtSignal(object)  # receive signals from higher hierarchies
    sig_tx = pyqtSignal(object)  # emitted when amplitude unit or spec has been changed

    def __init__(self, title="Amplitude Specs", objectName=""):
        """
        Initialize
        """
        super().__init__()
        self.title = title
        self.setObjectName(objectName)

        self.qlabels = []    # list with references to QLabel widgets
        self.qlineedit = []  # list with references to QLineEdit widgets

        self.spec_edited = False  # flag whether QLineEdit field has been edited
        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming in via subwidgets and sig_rx
        """
        logger.debug("SIG_RX: %s", first_item(dict_sig))
        if dict_sig['id'] == id(self):
            # this should never happen
            logger.warning("Stopped infinite loop:\n%s", pprint_log(dict_sig))
            return
        if 'data_changed' in dict_sig and dict_sig['data_changed'] == 'filter_loaded':
            self.dict2ui()

    # ------------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Construct User Interface
        """
        amp_units = ["dB", "V", "W"]

        bfont = QFont()
        bfont.setBold(True)
        lblTitle = QLabel(str(self.title), self)  # field for widget title
        lblTitle.setFont(bfont)
        lblTitle.setWordWrap(True)

        lbl_units = QLabel("in", self)

        self.cmbUnitsA = QComboBox(self, objectName="cmbUnitsA")
        self.cmbUnitsA.addItems(amp_units)
        self.cmbUnitsA.setToolTip(
            "<span>Unit for amplitude specifications:"
            " dB is attenuation (&gt; 0); levels in V and W have to be &lt; 1.</span>")

        # fit size dynamically to largest element:
        self.cmbUnitsA.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # find index for default unit from dictionary and set the unit
        amp_idx = self.cmbUnitsA.findData(fb_get('amp_specs_unit'))
        amp_idx = max(amp_idx, 0)
        self.cmbUnitsA.setCurrentIndex(amp_idx)  # initialize for dBs

        layHTitle = QHBoxLayout()  # layout for title and unit
        layHTitle.addWidget(lblTitle)
        layHTitle.addStretch(5)
        layHTitle.addWidget(lbl_units, Qt.AlignLeft)
        layHTitle.addWidget(self.cmbUnitsA, Qt.AlignLeft)

        self.layGSpecs = QGridLayout()  # sublayout for spec fields
        # set the title as the first (fixed) entry in grid layout. The other
        # fields are added and hidden dynamically in _show_entries and _hide_entries()
        self.layGSpecs.addLayout(layHTitle, 0, 0, 1, 2)
        self.layGSpecs.setAlignment(Qt.AlignLeft)
        self.layGSpecs.setAlignment(Qt.AlignTop)

        # This is the top level widget, encompassing the other widgets
        self.frm_main = QFrame(self)
        self.frm_main.setLayout(self.layGSpecs)

        self.lay_v_main = QVBoxLayout()  # Widget main layout
        self.lay_v_main.addWidget(self.frm_main)
        self.lay_v_main.setContentsMargins(*params['wdg_margins'])

        self.setLayout(self.lay_v_main)

        self.n_cur_labels = 0  # number of currently visible labels / qlineedits

        # - Build a list from all entries in the fil_dict dictionary starting
        #   with "a_" (= amplitude specifications of the current filter)
        # - Pass the list to update_ui which recreates the widget
        new_labels = [str(lbl) for lbl in fb_get() if lbl[0:2] == 'a_']
        self.update_ui(new_labels=new_labels)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs / EVENT MONITORING
        # ----------------------------------------------------------------------
        self.cmbUnitsA.currentIndexChanged.connect(self._set_amp_unit)
        #       ^ this also triggers the initial dict2ui
        # DYNAMIC EVENT MONITORING
        # Every time a field is edited, call self._store_entry and
        # self.dict2ui. This is achieved by dynamically installing and
        # removing event filters when creating / deleting subwidgets.
        # The event filter monitors the focus of the input fields.

    # --------------------------------------------------------------------------
    def eventFilter(self, source: QtCore.QObject, event: QEvent) -> bool:
        """
        Filter all events generated by the QLineEdit widgets. Source and type
        of all events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        - When a QLineEdit widget gains input focus (QEvent.FocusIn`), display
          the stored value from filter dict with full precision
        - When a key is pressed inside the text field, set the `spec_edited` flag
          to True.
        - When a QLineEdit widget loses input focus (QEvent.FocusOut`), store
          current value in linear format with full precision (only if
          `spec_edited`== True) and display the stored value in selected format
        """
        if isinstance(source, QLineEdit):  # could be extended for other widgets
            if event.type() == QEvent.FocusIn:
                self.spec_edited = False
                self.dict2ui()
                # store current entry in case new value can't be evaluated:
                self.data_prev = source.text()
            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True  # entry has been changed
                key = event.key()
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}:  # store entry
                    self._store_entry(source)
                elif key == QtCore.Qt.Key_Escape:  # revert changes
                    self.spec_edited = False
                    self.dict2ui()

            elif event.type() == QEvent.FocusOut:
                self._store_entry(source)
        # Call base class method to continue normal event processing:
        return super().eventFilter(source, event)

    # -------------------------------------------------------------
    def update_ui(self, new_labels: list[str]) -> None:
        """
        Called from input_specs.update_ui() and target_specs.update_ui().
        The first entry is the state of the widget, 'a', 'u', 'd'.
        Set labels and get corresponding values from filter dictionary.
        When number of entries has changed, the layout of subwidget is rebuilt,
        using

        - `new_labels`, a list of strings from the filter_dict for the current
          filter design
        - `self.qlabels`, a list with references to existing QLabel widgets,
        - `self.n_cur_labels`, the number of currently visible labels / qlineedit
          fields
        """
        state = new_labels[0]
        new_labels = new_labels[1:]

#        W_lbl = max([self.qfm.width(l) for l in new_labels]) # max. label width in pixel

        num_new_labels = len(new_labels)
        if num_new_labels < self.n_cur_labels:
            # less new labels/qlineedit fields than before
            self._hide_entries(num_new_labels)

        elif num_new_labels > self.n_cur_labels:
            # more new labels than before -> create / show new ones
            self._show_entries(num_new_labels)

        tool_tipp_sb = "Min. attenuation resp. maximum level in (this) stop band"
        for i in range(num_new_labels):
            # Update ALL labels and corresponding values and style them
            self.qlabels[i].setText(to_html(new_labels[i], frmt='bi'))
            qstyle_widget(self.qlabels[i], state)
            self.qlabels[i].setStyleSheet("QLabel {background-color :none;}")

            self.qlineedit[i].setText(str(fb_get(new_labels[i])))
            self.qlineedit[i].setObjectName(new_labels[i])  # update ID

            if "sb" in new_labels[i]:
                self.qlineedit[i].setToolTip(
                    "<span>" + tool_tipp_sb + " (&gt; 0).</span>")
            elif "pb" in new_labels[i]:
                self.qlineedit[i].setToolTip(
                    "<span>Maximum ripple (&gt; 0) in (this) pass band.<span/>")
            qstyle_widget(self.qlineedit[i], state)

        self.n_cur_labels = num_new_labels  # update number of currently visible labels
        self.dict2ui()  # display rounded filter dict entries in selected unit

    # -------------------------------------------------------------------------
    def dict2ui(self) -> None:
        """
        Reload and reformat the amplitude textfields from filter dict when a new filter
        design algorithm is selected or when the user has changed the unit  (V / W / dB):

        - Reload amplitude entries from filter dictionary and convert to selected
          to reflect changed settings unit.
        - Update the lineedit fields, rounded to specified format.
        """
        unit = fb_get('amp_specs_unit')

        filt_type = fb_get('ft')

        for qle in self.qlineedit:
            amp_label = str(qle.objectName())
            amp_value = lin2unit(fb_get(amp_label), filt_type, amp_label, unit=unit)

            if not qle.hasFocus():
                # widget has no focus, round the display
                qle.setText(params['FMT'].format(amp_value))
            else:
                # widget has focus, show full precision
                qle.setText(str(amp_value))

    # --------------------------------------------------------------------------
    def _set_amp_unit(self) -> None:
        """
        Store unit for amplitude in filter dictionary, reload amplitude spec
        entries via dict2ui and fire a sigUnitChanged signal
        """
        fb_set('amp_specs_unit', qget_cmb_box(self.cmbUnitsA, data=False))
        self.dict2ui()

        self.emit({'view_changed': 'a_unit'})

    # --------------------------------------------------------------------------
    def _store_entry(self, source: QtCore.QObject) -> None:
        """
        When the textfield of `source` has been edited (flag `self.spec_edited` =  True),
        transform the amplitude spec back to linear unit setting and store it
        in filter dict.
        This is triggered by `QEvent.focusOut`

        Spec entries are *always* stored in linear units; only the
        displayed values are adapted to the amplitude unit, not the dictionary!
        """
        if self.spec_edited:
            unit = str(self.cmbUnitsA.currentText())
            filt_type = fb_get('ft')
            amp_label = str(source.objectName())
            amp_value = safe_eval(source.text(), self.data_prev, sign='pos')
            is_new_key = amp_label not in fb_get()
            fb_set(amp_label, unit2lin(amp_value, filt_type, amp_label, unit), new_key=is_new_key)
            self.emit({'specs_changed': 'a_specs'})
            self.spec_edited = False  # reset flag
        self.dict2ui()

    # ------------------------------------------------------------------------
    def _hide_entries(self, num_new_labels: int) -> None:
        """
        Hide subwidgets so that only `num_new_labels` subwidgets are visible
        """
        for i in range(num_new_labels, len(self.qlabels)):
            self.qlabels[i].hide()
            self.qlineedit[i].hide()

    # ------------------------------------------------------------------------
    def _show_entries(self, num_new_labels: int) -> None:
        """
        - check whether enough subwidgets (QLabel und QLineEdit) exist for the
          the required number of `num_new_labels`:
              - create new ones if required
              - initialize them with dummy information
              - install eventFilter for new QLineEdit widgets so that the filter
                  dict is updated automatically when a QLineEdit field has been
                  edited.
        - if enough subwidgets exist already, make enough of them visible to
          show all spec fields
        """
        num_tot_labels = len(self.qlabels)  # number of existing labels (vis. + invis.)

        if num_tot_labels < num_new_labels:  # new widgets need to be generated
            for i in range(num_tot_labels, num_new_labels):
                self.qlabels.append(QLabel(self))
                self.qlabels[i].setText(to_html("dummy", frmt='bi'))

                self.qlineedit.append(QLineEdit(""))
                self.qlineedit[i].setObjectName("dummy")
                self.qlineedit[i].installEventFilter(self)  # filter events

                # first entry is title
                self.layGSpecs.addWidget(self.qlabels[i], i+1, 0)
                self.layGSpecs.addWidget(self.qlineedit[i], i+1, 1)

        else:  # make the right number of widgets visible
            for i in range(self.n_cur_labels, num_new_labels):
                self.qlabels[i].show()
                self.qlineedit[i].show()


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.amplitude_specs`
    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = AmplitudeSpecs()
    mainw.update_ui(new_labels=['a', 'a_sb', 'a_sb2', 'a_pb', 'a_pb2'])
    mainw.update_ui(new_labels=['u', 'a_pb', 'a_sb'])

    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
