# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Tabbed container widget containing several widgets
"""
import importlib
import logging
import sys

from pyfda.libs.compat import (
    QTabWidget, QWidget, QVBoxLayout, QScrollArea, pyqtSignal, QEvent, QtCore,
    QSizePolicy)
from pyfda.libs.pyfda_lib import pprint_log
from pyfda.libs.pyfda_qt_lib import emit
from pyfda.pyfda_rc import params

logger = logging.getLogger(__name__)

SCROLL = True  # enable scrolling


class TabbedWidget(QWidget):
    """
    Create a tabbed widget with all subwidgets from the passed dict ``wdg_classes_dict``,
    e.g. ``CFP.INPUT_CLASSES_DICT``. Usually, this dict is parsed from the config file
    at startup in :class:`pyfda.ConfigFileParser` and stored as a class variable.
    """
    # signals as class variables (shared between instances if more than one exists)
    # incoming, connected here to individual senders, passed on to process sigmals
    sig_rx = pyqtSignal(object)
    # outgoing, connected in receiver (pyfdax -> plot_tab_widgets)
    sig_tx = pyqtSignal(object)

    def __init__(self, wdg_classes_dict: dict, objectName: str = '', label: str = '',
                 use_timer: bool = False) -> None:
        super().__init__()
        self.setObjectName(objectName)
        self.wdg_classes_dict = wdg_classes_dict
        self.label = label
        self.use_timer = use_timer
        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig: dict) -> None:
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Initialize UI with tabbed subwidgets: Instantiate dynamically each widget
        from the dict `wdg_classes_dict`. The dict has entries like
        {
        'Plot_Hf': {'name': '|H(f)|', 'mod': 'pyfda.plot_widgets.plot_hf'},
        ...
        }
        defining the display name and the fully qualified name of the widget.

        Try to

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
        self.tab_widget = QTabWidget(self)

        self.n_wdg = 0  # number and ...
        inst_wdg_str = ""  # ... full names of successfully instantiated widgets

        for class_name, wdg_dict in self.wdg_classes_dict.items():
            try:
                # fully qualified module name:
                mod_fq_name = wdg_dict['mod']
                mod = importlib.import_module(mod_fq_name)  # dynamically import module
                wdg_class = getattr(mod, class_name)  # get widget class ...
                inst = wdg_class()  # ... and instantiate it
            except ImportError as e:
                logger.warning(
                    'Class "%s" could not be imported from %s:\n%s.',
                    class_name, mod_fq_name, e)
                continue  # unsuccessful, try next widget

            if hasattr(inst, "state") and inst.state == "deactivated":
                continue  # with next widget
            if hasattr(inst, 'tab_label'):
                self.tab_widget.addTab(inst, inst.tab_label)
            else:
                self.tab_widget.addTab(inst, "not set")
            if hasattr(inst, 'tool_tip'):
                self.tab_widget.setTabToolTip(self.n_wdg, inst.tool_tip)
            # collect all instance tx signals in self.sig_tx
            if hasattr(inst, 'sig_tx'):
                inst.sig_tx.connect(self.sig_tx)
            # distribute self.sig_rx signal to all instance rx signals
            if hasattr(inst, 'sig_rx'):
                self.sig_rx.connect(inst.sig_rx)

            self.n_wdg += 1  # successfully instantiated one more widget
            inst_wdg_str += '\t' + mod_fq_name + "." + class_name + '\n'

        if len(inst_wdg_str) == 0:
            logger.critical("No %s widgets found!", self.labels)
            sys.exit()
        else:
            logger.debug("Added %d %s widgets:\n%s", self.n_wdg, self.label, inst_wdg_str)

        # --------------------------------------
        # UI Layout
        #---------------------------------------
        lay_v_main = QVBoxLayout()
        # setContentsMargins -> number of pixels between frame window border
        lay_v_main.setContentsMargins(*params['wdg_margins'])  # (left, top, right, bottom)

        if self.use_timer:
            # add the tab_widget directly, is resized after waiting for timer
            lay_v_main.addWidget(self.tab_widget)
        else:
            # add the widget in a QScrollArea
            scroll = QScrollArea(self)
            scroll.setWidget(self.tab_widget)
            scroll.setWidgetResizable(True)  # Size of monitored widget is allowed to grow
            lay_v_main.addWidget(scroll)


        self.setLayout(lay_v_main)  # set the main layout of the window

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ---------------------------------------------------------------------
        # self.sig_rx.connect(inst.sig_rx) # this happens in _construct_ui()
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # connect collected tx signals to all local rx signal inputs
        self.sig_tx.connect(self.sig_rx)
        self.sig_rx.connect(self.log_rx) # enable for debugging
        # When user has selected a different tab, trigger a redraw of current tab
        # self.tab_widget.currentChanged.connect(lambda: self.emit({'ui_global_changed': 'tab'}))
        self.tab_widget.currentChanged.connect(self.current_tab_changed)
        # The following does not work: maybe current scope must be left?
        # tab_widget.currentChanged.connect(tab_widget.currentWidget().redraw)

        # ------------------------------------------------------------------------
        #            Resizing
        # ------------------------------------------------------------------------
        if self.use_timer:
            self.timer_id = QtCore.QTimer()
            self.timer_id.setSingleShot(True)
            # redraw current widget at timeout (timer is triggered by resize event in event filter):
            self.timer_id.timeout.connect(lambda: self.emit({'ui_global_changed': 'resized'}))
            self.tab_widget.installEventFilter(self)

    # ------------------------------------------------------------------------------
    def log_rx(self, dict_sig: dict = None) -> None:
        """
        Enable `self.sig_rx.connect(self.log_rx)` above for debugging.
        """
        logger.debug("SIG_RX\n%s", pprint_log(dict_sig))

    # ------------------------------------------------------------------------------
    def eventFilter(self, source: QtCore.QObject, event: QEvent) -> bool:
        """
        Filter all events generated by the QTabWidget. Source and type of all
        events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        This filter stops and restarts a one-shot timer for every resize event.
        When the timer generates a timeout after 500 ms, ``{'ui_global_changed': 'resized'}``
        is emitted by the timer.
        """
        if isinstance(source, QTabWidget):
            if event.type() == QEvent.Resize:
                self.timer_id.stop()
                self.timer_id.start(500)

        # Call base class method to continue with normal event processing:
        return super().eventFilter(source, event)

    # ------------------------------------------------------------------------------
    def current_tab_changed(self, idx) -> None:
        """
        Triggered by currentChanged signal which passes the index of the current tab.

        Ignore the size policy of all hidden tabs so that only the size of the current
        tab widget matters and determines the behaviour of QScrollArea.

        Emit the signal 'ui_global_changed':'tab' to notify other widgets that the
        current tab position has changed

        This is inspired by
        https://stackoverflow.com/questions/29128936/qtabwidget-size-depending-on-current-tab

        The QTabWidget won't select the biggest widget's size as its own size
        unless you use layout on the QTabWidget. Therefore, if you want to change
        the size of QTabWidget manually, remove the layout and call QTabWidget.resize()
        according to the currentChanged signal.
        """
        # logger.warning("current widget = %s", self.tab_widget.currentWidget().objectName())

        # Ignore the size of the unselected (not diplayed) widgets:
        for i in range(self.n_wdg):
            self.tab_widget.widget(i).setSizePolicy(QSizePolicy.Ignored,
                                                    QSizePolicy.Ignored)
        # Set the size policy of the current (displayed) widget to "preferred", allowing
        # it to shrink and grow from the hinted size:
        self.tab_widget.widget(idx).setSizePolicy(QSizePolicy.Preferred,
                                                  QSizePolicy.Preferred)

        # After that, call adjustSize() to update the sizes.
        # self.tab_widget.widget(idx).resize(self.tab_widget.widget(idx).minimumSizeHint())
        # self.tab_widget.widget(idx).adjustSize()

        self.emit({'ui_global_changed': 'tab'})

# ------------------------------------------------------------------------
if __name__ == "__main__":
    # Run widget standalone with `python -m pyfda.tabbed_widget`
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc
    from pyfda.config_file_parser import ConfigFileParser as CFP
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.QSS_RC)

    mainw = TabbedWidget(CFP.INPUT_CLASSES_DICT, objectName='tst_widget', label = 'test')
    app.setActiveWindow(mainw)
    mainw.show()
    mainw = TabbedWidget(CFP.PLOT_CLASSES_DICT, objectName='tst_widget', label = 'test')
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
