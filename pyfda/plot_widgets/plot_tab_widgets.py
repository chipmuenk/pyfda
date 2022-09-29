# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create a tabbed widget for all plot subwidgets in the list ``fb.plot_widgets_list``.
This list is compiled at startup in :class:`pyfda.tree_builder.Tree_Builder`, it is
kept as a module variable in :mod:`pyfda.filterbroker`.
"""
import importlib
from pyfda.libs.compat import QTabWidget, QVBoxLayout, QEvent, QtCore, pyqtSignal

from pyfda.libs.pyfda_lib import pprint_log
from pyfda.pyfda_rc import params
import pyfda.filterbroker as fb

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
class PlotTabWidgets(QTabWidget):

    # incoming, connected to input_tab_widget.sig_tx in pyfdax
    sig_rx = pyqtSignal(object)
    # outgoing: emitted by process_sig_rx
    sig_tx = pyqtSignal(object)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None):
        super(PlotTabWidgets, self).__init__(parent)
        self._construct_UI()

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Initialize UI with tabbed subwidgets: Instantiate dynamically each widget
        from the dict `fb.plot_classes` and try to

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
        tabWidget = QTabWidget(self)
        tabWidget.setObjectName("plot_tabs")

        n_wdg = 0  # number and ...
        inst_wdg_str = ""  # ... full names of successfully instantiated plot widgets
        #
        for plot_class in fb.plot_classes:
            try:
                mod_fq_name = fb.plot_classes[plot_class]['mod']  # FQN
                mod = importlib.import_module(mod_fq_name)  # import plot widget module
                wdg_class = getattr(mod, plot_class)  # get plot widget class ...
                # and instantiate it
                inst = wdg_class()
            except ImportError as e:
                logger.warning('Class "{0}" could not be imported from {1}:\n{2}.'
                               .format(plot_class, mod_fq_name, e))
                continue  # unsuccessful, try next widget

            if hasattr(inst, 'tab_label'):
                tabWidget.addTab(inst, inst.tab_label)
            else:
                tabWidget.addTab(inst, "not set")
            if hasattr(inst, 'tool_tip'):
                tabWidget.setTabToolTip(n_wdg, inst.tool_tip)
            if hasattr(inst, 'sig_tx'):
                inst.sig_tx.connect(self.sig_tx)
            if hasattr(inst, 'sig_rx'):
                self.sig_rx.connect(inst.sig_rx)

            n_wdg += 1  # successfully instantiated one more widget
            inst_wdg_str += '\t' + mod_fq_name + "." + plot_class + '\n'

        if len(inst_wdg_str) == 0:
            logger.warning("No plotting widgets found!")
        else:
            logger.debug(
                "Imported {0:d} plotting classes:\n{1}".format(n_wdg, inst_wdg_str))
        # ----------------------------------------------------------------------
        layVMain = QVBoxLayout()
        layVMain.addWidget(tabWidget)
        layVMain.setContentsMargins(*params['wdg_margins'])  # (left, top, right, bottom)

        self.setLayout(layVMain)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ---------------------------------------------------------------------
        # self.sig_rx.connect(inst.sig_rx) # this happens in _construct_UI()
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.timer_id = QtCore.QTimer()
        self.timer_id.setSingleShot(True)
        # redraw current widget at timeout (timer was triggered by resize event):
        self.timer_id.timeout.connect(self.current_tab_redraw)

        self.sig_tx.connect(self.sig_rx)  # loop back to local inputs
        # self.sig_rx.connect(self.log_rx) # enable for debugging

        # When user has selected a different tab, trigger a redraw of current tab
        tabWidget.currentChanged.connect(self.current_tab_changed)
        # The following does not work: maybe current scope must be left?
        # tabWidget.currentChanged.connect(tabWidget.currentWidget().redraw)

        tabWidget.installEventFilter(self)

        """
        https://stackoverflow.com/questions/29128936/qtabwidget-size-depending-on-current-tab

        The QTabWidget won't select the biggest widget's height as its own height
        unless you use layout on the QTabWidget. Therefore, if you want to change
        the size of QTabWidget manually, remove the layout and call QTabWidget::resize
        according to the currentChanged signal.

        You can set the size policy of the widget that is displayed to
        QSizePolicy::Preferred
        and the other ones to
        QSizePolicy::Ignored. After that call adjustSize to update the sizes.

        void MainWindow::updateSizes(int index)
        {
        for(int i=0;i<ui->tabWidget->count();i++)
            if(i!=index)
                ui->tabWidget->widget(i)->setSizePolicy(
                                            QSizePolicy::Ignored, QSizePolicy::Ignored);

        ui->tabWidget->widget(index)->setSizePolicy(
                                        QSizePolicy::Preferred, QSizePolicy::Preferred);
        ui->tabWidget->widget(index)->resize(
                                        ui->tabWidget->widget(index)->minimumSizeHint());
        ui->tabWidget->widget(index)->adjustSize();
        resize(minimumSizeHint());
        adjustSize();
        }

        adjustSize(): The last two lines resize the main window itself. You might want
        to avoid it, depending on your application.
        For example, if you set the rest of the widgets to expand into the space just
        made available, it's not so nice if the window resizes itself instead.
        """

# ------------------------------------------------------------------------------
    def log_rx(self, dict_sig=None):
        """
        Enable `self.sig_rx.connect(self.log_rx)` above for debugging.
        """
        if type(dict_sig) == dict:
            logger.warning("SIG_RX\n{0}".format(pprint_log(dict_sig)))
        else:
            logger.warning("empty dict")

# ------------------------------------------------------------------------------
    def current_tab_changed(self):
        self.emit({'ui_global_changed': 'tab'})

# ------------------------------------------------------------------------------
    def current_tab_redraw(self):
        self.emit({'ui_global_changed': 'resized'})

# ------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by the QTabWidget. Source and type of all
        events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        This filter stops and restarts a one-shot timer for every resize event.
        When the timer generates a timeout after 500 ms, ``current_tab_redraw()`` is
        called by the timer.
        """
        if isinstance(source, QTabWidget):
            if event.type() == QEvent.Resize:
                self.timer_id.stop()
                self.timer_id.start(500)

        # Call base class method to continue with normal event processing:
        return super(PlotTabWidgets, self).eventFilter(source, event)


# ==============================================================================
if __name__ == "__main__":
    """ Run widget standalone with `python -m pyfda.plot_widgets.plot_tab_widgets` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = PlotTabWidgets()
    mainw.resize(300, 400)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
