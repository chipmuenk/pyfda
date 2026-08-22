# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for entering weight specifications
"""
import logging
import sys

from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.compat import (
    QtCore, QWidget, QLabel, QLineEdit, QFrame, QFont,
    QVBoxLayout, QHBoxLayout, QGridLayout, pyqtSignal, QEvent)
from pyfda.libs.pyfda_lib import to_html, safe_eval
from pyfda.libs.pyfda_qt_lib import qstyle_widget, emit
from pyfda.libs.pyfda_qt_classes import PushButton
from pyfda.pyfda_rc import params  # FMT string for QLineEdit fields, e.g. '{:.3g}'

logger = logging.getLogger(__name__)

class WeightSpecs(QWidget):
    """
    Build and update widget for entering the weight
    specifications like W_SB, W_PB etc.
    """
    sig_rx = pyqtSignal(object)  # receive signals from higher hierarchies
    sig_tx = pyqtSignal(object)  # outgoing signals

    def __init__(self, objectName: str = "") -> None:
        super().__init__()

        self.setObjectName(objectName)
        self.q_labels = []  # list with references to QLabel widgets
        self.q_line_edits = []  # list with references to QLineEdit widgets

        self.spec_edited = False  # flag whether QLineEdit field has been edited

        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig: dict) -> None:
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict = None) -> None:
        """
        Process signals coming in via subwidgets and sig_rx
        """
        # logger.warning(
        #     f"SIG RX: {first_item(dict_sig)}")
        if dict_sig['id'] == id(self):
            # logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
            return
        if 'data_changed' in dict_sig:
            if dict_sig['data_changed'] in {'filter_loaded', 'filter_designed'}:
                self.dict2ui()

    # ------------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Construct User Interface
        """
        self.lay_g_specs = QGridLayout()  # Sublayout for spec fields, populated
                        # dynamically in _show_entries()
        title = "Weight Specifications"
        bfont = QFont()
        bfont.setBold(True)

        lbl_title = QLabel(self)  # field for widget title
        lbl_title.setText(str(title))
        lbl_title.setFont(bfont)
        lbl_title.setWordWrap(True)

        self.but_reset = PushButton(self, text="Reset", checkable=False)
        # self.but_reset.setText("Reset")
        self.but_reset.setToolTip("Reset weights to 1")

        lay_h_title = QHBoxLayout()       # Layout for title and reset button
        lay_h_title.addWidget(lbl_title)
        lay_h_title.addWidget(self.but_reset)

        # set the title as the first (fixed) entry in grid layout. The other
        # fields are added and hidden dynamically in _show_entries and _hide_entries()
        self.lay_g_specs.addLayout(lay_h_title, 0, 0, 1, 2)

        # This is the top level widget, encompassing the other widgets
        frm_main = QFrame(self)
        frm_main.setLayout(self.lay_g_specs)

        self.lay_v_main = QVBoxLayout()   # Widget main vertical layout
        self.lay_v_main.addWidget(frm_main)
        self.lay_v_main.setContentsMargins(*params['wdg_margins'])

        self.setLayout(self.lay_v_main)

        # - Build a list from all entries in the filter dictionary starting
        #   with "W" (= weight specifications of the current filter)
        # - Pass the list to setEntries which recreates the widget
        self.n_cur_labels = 0  # number of currently visible labels / qlineedits
        new_labels = [str(lbl) for lbl in fb_get() if lbl[0] == 'W']
        self.update_ui(new_labels=new_labels)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs / EVENT FILTER
        # ----------------------------------------------------------------------
        self.but_reset.clicked.connect(self._reset_weights)
        #       ^ this also initializes the weight text fields
        # DYNAMIC EVENT MONITORING
        # Every time a field is edited, call self._store_entry and
        # self.dict2ui. This is achieved by dynamically installing and
        # removing event filters when creating / deleting subwidgets.
        # The event filter monitors the focus of the input fields.

    # ------------------------------------------------------------------------------
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
                if key in {QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter}:
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
        Called from filter_specs.update_ui()
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

        num_new_labels = len(new_labels)

        # less new labels/qlineedit fields than before
        if num_new_labels < self.n_cur_labels:
            self._hide_entries(num_new_labels)

        # more new labels than before, create / show new ones
        elif num_new_labels > self.n_cur_labels:
            self._show_entries(num_new_labels)

        for i in range(num_new_labels):
            # Update ALL labels and corresponding values
            self.q_labels[i].setText(to_html(new_labels[i], frmt='bi'))

            self.q_line_edits[i].setText(str(fb_get(new_labels[i])))
            self.q_line_edits[i].setObjectName(new_labels[i])  # update ID
            self.q_line_edits[i].setToolTip(
                "<span>Relative weight (importance) for approximating this band.</span>")
            qstyle_widget(self.q_line_edits[i], state)

        self.n_cur_labels = num_new_labels  # update number of currently visible labels
        self.dict2ui()  # display rounded filter dict entries

    # ------------------------------------------------------------------------------
    def dict2ui(self) -> None:
        """
        Reload textfields from filter dictionary to update changed settings
        """
        for qle in self.q_line_edits:
            weight_value = fb_get(str(qle.objectName()))

            if not qle.hasFocus():
                # widget has no focus, round the display
                qle.setText(params['FMT'].format(weight_value))
            else:
                # widget has focus, show full precision
                qle.setText(str(weight_value))

    # ------------------------------------------------------------------------------
    def _store_entry(self, widget: QtCore.QObject) -> None:
        """
        When the textfield of `widget` has been edited (`self.spec_edited` =  True),
        store the weight spec in filter dict. This is triggered by `QEvent.focusOut`
        """
        if self.spec_edited:
            w_label = str(widget.objectName())
            w_value = safe_eval(widget.text(), self.data_prev, sign='pos')
            w_value = max(w_value, 1)
            w_value = min(w_value, 1.e6)
            fb_set(w_label, w_value, new_key=w_label not in fb_get())
            self.emit({'specs_changed': 'w_specs'})
            self.spec_edited = False  # reset flag
        self.dict2ui()

    # -------------------------------------------------------------
    def _hide_entries(self, num_new_labels: int) -> None:
        """
        Hide subwidgets so that only `len_new_labels` subwidgets are visible
        """
        for i in range(num_new_labels, len(self.q_labels)):
            self.q_labels[i].hide()
            self.q_line_edits[i].hide()

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
        num_tot_labels = len(self.q_labels)  # number of existing labels / qlineedit fields

        if num_tot_labels < num_new_labels:  # new widgets need to be generated
            for i in range(num_tot_labels, num_new_labels):
                self.q_labels.append(QLabel(self))
                self.q_labels[i].setText(to_html("dummy", frmt='bi'))

                self.q_line_edits.append(QLineEdit(""))
                self.q_line_edits[i].setObjectName("dummy")
                self.q_line_edits[i].installEventFilter(self)  # filter events

                # first entry is title and reset button
                self.lay_g_specs.addWidget(self.q_labels[i], i+1, 0)
                self.lay_g_specs.addWidget(self.q_line_edits[i], i+1, 1)

        else:  # make the right number of widgets visible
            for i in range(self.n_cur_labels, num_new_labels):
                self.q_labels[i].show()
                self.q_line_edits[i].show()

    # ------------------------------------------------------------------------------
    def _reset_weights(self) -> None:
        """
        Reset all entries to "1.0" and store them in the filter dictionary
        """
        for qle in self.q_line_edits:
            qle.setText("1")

            w_label = str(qle.objectName())
            fb_set(w_label, 1.0)

        self.dict2ui()
        self.emit({'specs_changed': 'w_specs'})


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.weight_specs`

    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = WeightSpecs()

    mainw.update_ui(new_labels=['W_SB', 'W_SB2', 'W_PB', 'W_PB2'])
    mainw.update_ui(new_labels=['W_PB', 'W_PB2'])

    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
