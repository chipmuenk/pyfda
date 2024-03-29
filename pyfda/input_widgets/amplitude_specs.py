# -*- coding: utf-8 -*-
"""
Widget for entering amplitude specifications

Author: Christian Münker
"""

import sys

from pyfda.libs.compat import (
    QtCore, Qt, QEvent, pyqtSignal, QWidget, QLabel, QLineEdit, QComboBox, QFrame,
    QFont, QVBoxLayout, QHBoxLayout, QGridLayout)

import pyfda.filterbroker as fb
from pyfda.libs.pyfda_lib import(
    to_html, lin2unit, unit2lin, safe_eval, pprint_log, first_item)
from pyfda.libs.pyfda_qt_lib import qstyle_widget, qget_cmb_box
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

import logging
logger = logging.getLogger(__name__)


class AmplitudeSpecs(QWidget):
    """
    Build and update widget for entering the amplitude
    specifications like A_SB, A_PB etc.
    """
    sig_rx = pyqtSignal(object)  # receive signals from higher hierarchies
    sig_tx = pyqtSignal(object)  # emitted when amplitude unit or spec has been changed

    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None, title="Amplitude Specs", objectName=""):
        """
        Initialize
        """
        super(AmplitudeSpecs, self).__init__(parent)
        self.title = title
        self.setObjectName(objectName)

        self.qlabels = []    # list with references to QLabel widgets
        self.qlineedit = []  # list with references to QLineEdit widgets

        self.spec_edited = False  # flag whether QLineEdit field has been edited
        self._construct_UI()

# -------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming in via subwidgets and sig_rx
        """
        # logger.warning(
        #    f"SIG_RX: {first_item(dict_sig)}")
        if dict_sig['id'] == id(self):
            # this should never happen
            logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
            return
        elif 'data_changed' in dict_sig and dict_sig['data_changed'] == 'filter_loaded':
            self.load_dict()

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Construct User Interface
        """
        amp_units = ["dB", "V", "W"]

        bfont = QFont()
        bfont.setBold(True)
        lblTitle = QLabel(str(self.title), self)  # field for widget title
        lblTitle.setFont(bfont)
        lblTitle.setWordWrap(True)

        lblUnits = QLabel("in", self)

        self.cmbUnitsA = QComboBox(self, objectName="cmbUnitsA")
        self.cmbUnitsA.addItems(amp_units)
        self.cmbUnitsA.setToolTip(
            "<span>Unit for amplitude specifications:"
            " dB is attenuation (&gt; 0); levels in V and W have to be &lt; 1.</span>")

        # fit size dynamically to largest element:
        self.cmbUnitsA.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # find index for default unit from dictionary and set the unit
        amp_idx = self.cmbUnitsA.findData(fb.fil[0]['amp_specs_unit'])
        if amp_idx < 0:
            amp_idx = 0
        self.cmbUnitsA.setCurrentIndex(amp_idx)  # initialize for dBs

        layHTitle = QHBoxLayout()  # layout for title and unit
        layHTitle.addWidget(lblTitle)
        layHTitle.addWidget(lblUnits, Qt.AlignLeft)
        layHTitle.addWidget(self.cmbUnitsA, Qt.AlignLeft)
        layHTitle.addStretch(1)

        self.layGSpecs = QGridLayout()  # sublayout for spec fields
        # set the title as the first (fixed) entry in grid layout. The other
        # fields are added and hidden dynamically in _show_entries and _hide_entries()
        self.layGSpecs.addLayout(layHTitle, 0, 0, 1, 2)
        self.layGSpecs.setAlignment(Qt.AlignLeft)

        # This is the top level widget, encompassing the other widgets
        self.frmMain = QFrame(self)
        self.frmMain.setLayout(self.layGSpecs)

        self.layVMain = QVBoxLayout()  # Widget main layout
        self.layVMain.addWidget(self.frmMain)
        self.layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(self.layVMain)

        self.n_cur_labels = 0  # number of currently visible labels / qlineedits

        # - Build a list from all entries in the fil_dict dictionary starting
        #   with "A" (= amplitude specifications of the current filter)
        # - Pass the list to update_UI which recreates the widget
        # ATTENTION: Entries need to be converted from QString to str for Py 2
        new_labels = [str(l) for l in fb.fil[0] if l[0] == 'A']
        self.update_UI(new_labels=new_labels)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs / EVENT MONITORING
        # ----------------------------------------------------------------------
        self.cmbUnitsA.currentIndexChanged.connect(self._set_amp_unit)
        #       ^ this also triggers the initial load_dict
        # DYNAMIC EVENT MONITORING
        # Every time a field is edited, call self._store_entry and
        # self.load_dict. This is achieved by dynamically installing and
        # removing event filters when creating / deleting subwidgets.
        # The event filter monitors the focus of the input fields.

# ------------------------------------------------------------------------------
    def eventFilter(self, source, event):
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
                self.load_dict()
                # store current entry in case new value can't be evaluated:
                self.data_prev = source.text()
            elif event.type() == QEvent.KeyPress:
                self.spec_edited = True  # entry has been changed
                key = event.key()
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}:  # store entry
                    self._store_entry(source)
                elif key == QtCore.Qt.Key_Escape:  # revert changes
                    self.spec_edited = False
                    self.load_dict()

            elif event.type() == QEvent.FocusOut:
                self._store_entry(source)
        # Call base class method to continue normal event processing:
        return super(AmplitudeSpecs, self).eventFilter(source, event)

# -------------------------------------------------------------
    def update_UI(self, new_labels=()):
        """
        Called from filter_specs.update_UI() and target_specs.update_UI().
        Set labels and get corresponding values from filter dictionary.
        When number of entries has changed, the layout of subwidget is rebuilt,
        using

        - `self.qlabels`, a list with references to existing QLabel widgets,
        - `new_labels`, a list of strings from the filter_dict for the current
          filter design
        - 'num_new_labels`, their number
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
            # Update ALL labels and corresponding values
            self.qlabels[i].setText(to_html(new_labels[i], frmt='bi'))

            self.qlineedit[i].setText(str(fb.fil[0][new_labels[i]]))
            self.qlineedit[i].setObjectName(new_labels[i])  # update ID

            if "sb" in new_labels[i].lower():
                self.qlineedit[i].setToolTip(
                    "<span>" + tool_tipp_sb + " (&gt; 0).</span>")
            elif "pb" in new_labels[i].lower():
                self.qlineedit[i].setToolTip(
                    "<span>Maximum ripple (&gt; 0) in (this) pass band.<span/>")
            qstyle_widget(self.qlineedit[i], state)

        self.n_cur_labels = num_new_labels  # update number of currently visible labels
        self.load_dict()  # display rounded filter dict entries in selected unit

# ------------------------------------------------------------------------------
    def load_dict(self):
        """
        Reload and reformat the amplitude textfields from filter dict when a new filter
        design algorithm is selected or when the user has changed the unit  (V / W / dB):

        - Reload amplitude entries from filter dictionary and convert to selected
          to reflect changed settings unit.
        - Update the lineedit fields, rounded to specified format.
        """
        unit = fb.fil[0]['amp_specs_unit']

        filt_type = fb.fil[0]['ft']

        for i in range(len(self.qlineedit)):
            amp_label = str(self.qlineedit[i].objectName())
            amp_value = lin2unit(fb.fil[0][amp_label], filt_type, amp_label, unit=unit)

            if not self.qlineedit[i].hasFocus():
                # widget has no focus, round the display
                self.qlineedit[i].setText(params['FMT'].format(amp_value))
            else:
                # widget has focus, show full precision
                self.qlineedit[i].setText(str(amp_value))

# ------------------------------------------------------------------------------
    def _set_amp_unit(self, source):
        """
        Store unit for amplitude in filter dictionary, reload amplitude spec
        entries via load_dict and fire a sigUnitChanged signal
        """
        fb.fil[0]['amp_specs_unit'] = qget_cmb_box(self.cmbUnitsA, data=False)
        self.load_dict()

        self.emit({'view_changed': 'a_unit'})

# ------------------------------------------------------------------------------
    def _store_entry(self, source):
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
            filt_type = fb.fil[0]['ft']
            amp_label = str(source.objectName())
            amp_value = safe_eval(source.text(), self.data_prev, sign='pos')
            fb.fil[0].update({amp_label: unit2lin(amp_value, filt_type, amp_label, unit)})
            self.emit({'specs_changed': 'a_specs'})
            self.spec_edited = False  # reset flag
        self.load_dict()

# -------------------------------------------------------------
    def _hide_entries(self, num_new_labels):
        """
        Hide subwidgets so that only `num_new_labels` subwidgets are visible
        """
        for i in range(num_new_labels, len(self.qlabels)):
            self.qlabels[i].hide()
            self.qlineedit[i].hide()

# ------------------------------------------------------------------------
    def _show_entries(self, num_new_labels):
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
    """ Run widget standalone with `python -m pyfda.input_widgets.amplitude_specs` """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = AmplitudeSpecs()
    mainw.update_UI(new_labels=['a', 'A_SB', 'A_SB2', 'A_PB', 'A_PB2'])
    mainw.update_UI(new_labels=['u', 'A_PB', 'A_SB'])

    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
