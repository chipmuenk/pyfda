# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Tabbed container for all input widgets
"""
import importlib
import logging
import sys

from pyfda.libs.compat import QTabWidget, QWidget, QVBoxLayout, QScrollArea, pyqtSignal
from pyfda.libs.pyfda_lib import pprint_log
from pyfda.libs.pyfda_qt_lib import emit
from pyfda.pyfda_rc import params
from pyfda.config_file_parser import ConfigFileParser as CFP

logger = logging.getLogger(__name__)

SCROLL = True  # enable scrolling


class InputTabWidgets(QWidget):
    """
    Create a tabbed widget for all input subwidgets in ``CFP.INPUT_CLASSES_DICT``. This dict
    is parsed from the config file at startup in :class:`pyfda.ConfigFileParser` and
    stored as a class variable.
    """
    # signals as class variables (shared between instances if more than one exists)
    # incoming, connected here to individual senders, passed on to process sigmals
    sig_rx = pyqtSignal(object)
    # outgoing, connected in receiver (pyfdax -> plot_tab_widgets)
    sig_tx = pyqtSignal(object)

    def __init__(self, parent=None, objectName='input_tab_widgets_inst'):
        super().__init__(parent)
        self.setObjectName(objectName)
        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -------------------------------------------------------------------------
    def _construct_ui(self):
        """
        Initialize UI with tabbed subwidgets: Instantiate dynamically each widget
        from the dict `CFP.INPUT_CLASSES_DICT` and try to

        - set the TabToolTip from the instance attribute `tool_tip`

        - set the tab label from the instance attribute `tab_label`
          for each widget.

        - connect the available signals of all subwidgets (not all widgets have
          both `sig_rx` and `sig_tx` signals).

            - `self.sig_rx` is distributed to all `inst.sig_rx` signals

            - all `inst.sig_tx` signals are collected in `self.sig_tx`

            - `self.sig_tx.connect(self.sig_rx)` distributes incoming signals (via
               pyfdax or coming from the input widgets) among all input widgets.

           In order to prevent infinite loops, every widget needs to block in-
           coming signals with its own name!
        """
        tab_widget = QTabWidget(self)

        n_wdg = 0  # number and ...
        inst_wdg_str = ""  # ... full names of successfully instantiated widgets

        for input_class in CFP.INPUT_CLASSES_DICT:
            try:
                # fully qualified module name:
                mod_fq_name = CFP.INPUT_CLASSES_DICT[input_class]['mod']
                mod = importlib.import_module(mod_fq_name)
                wdg_class = getattr(mod, input_class)
                # and instantiate it
                inst = wdg_class(self)
            except ImportError as e:
                logger.warning(
                    'Class "%s" could not be imported from %s:\n%s.', input_class, mod_fq_name, e)
                continue  # unsuccessful, try next widget

            if hasattr(inst, "state") and inst.state == "deactivated":
                continue  # with next widget
            if hasattr(inst, 'tab_label'):
                tab_widget.addTab(inst, inst.tab_label)
            else:
                tab_widget.addTab(inst, "not set")
            if hasattr(inst, 'tool_tip'):
                tab_widget.setTabToolTip(n_wdg, inst.tool_tip)
            # collect all instance tx signals in self.sig_tx
            if hasattr(inst, 'sig_tx'):
                inst.sig_tx.connect(self.sig_tx)
            # distribute self.sig_rx signal to all instance rx signals
            if hasattr(inst, 'sig_rx'):
                self.sig_rx.connect(inst.sig_rx)

            n_wdg += 1  # successfully instantiated one more widget
            inst_wdg_str += '\t' + mod_fq_name + "." + input_class + '\n'

        if len(inst_wdg_str) == 0:
            logger.critical("No input widgets found!")
            sys.exit()
        else:
            logger.debug("Imported %d input classes:\n%s", n_wdg, inst_wdg_str)

        #
        # TODO: document signal options

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # self.sig_rx.connect(inst.sig_rx) # happens in _construct_ui()
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # connect collected tx signals to all rx signal inputs
        self.sig_tx.connect(self.sig_rx)
        # self.sig_rx.connect(self.log_rx) # enable for debugging
        # When user has selected a different tab, trigger a redraw of current tab
        tab_widget.currentChanged.connect(lambda: self.emit({'ui_global_changed': 'tab'})
)
        # The following does not work: maybe current scope must be left?
        # tab_widget.currentChanged.connect(tab_widget.currentWidget().redraw)

        lay_v_main = QVBoxLayout()

        # setContentsMargins -> number of pixels between frame window border
        lay_v_main.setContentsMargins(*params['wdg_margins'])

        # --------------------------------------
        if SCROLL:
            scroll = QScrollArea(self)
            scroll.setWidget(tab_widget)
            scroll.setWidgetResizable(True)  # Size of monitored widget is allowed to grow

            lay_v_main.addWidget(scroll)
        else:
            lay_v_main.addWidget(tab_widget)  # add the tab_widget directly

        self.setLayout(lay_v_main)  # set the main layout of the window

    # ------------------------------------------------------------------------------
    def log_rx(self, dict_sig=None):
        """
        Enable `self.sig_rx.connect(self.log_rx)` above for debugging.
        """
        if isinstance(dict_sig, dict):
            logger.warning("SIG_RX\n%s", pprint_log(dict_sig))
        else:
            logger.warning("empty dict")


# ------------------------------------------------------------------------
if __name__ == "__main__":
    # Run widget standalone with `python -m pyfda.input_widgets.input_tab_widgets`
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.QSS_RC)

    mainw = InputTabWidgets()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
