# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Tabbed container with all plot widgets
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import logging
logger = logging.getLogger(__name__)

import importlib
from ..compat import QTabWidget, QVBoxLayout, QEvent, QtCore, pyqtSignal

from pyfda.pyfda_rc import params
import pyfda.filterbroker as fb

plot_wdg_dir = 'plot_widgets'

#------------------------------------------------------------------------------
class PlotTabWidgets(QTabWidget):

    # incoming, connected to input_tab_widget.sig_tx in pyfdax
    sig_rx = pyqtSignal(object)
    # outgoing: emitted by process_sig_rx
    sig_tx = pyqtSignal(object)

    def __init__(self, parent):
        super(PlotTabWidgets, self).__init__(parent)
        self._construct_UI()

#------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Initialize UI with tabbed subwidgets and connect the signals of all
        subwidgets.
        This is done by dynamically instantiating each widget from the list
        `fb.plot_widget_list` in the module `plot_wdg_dir`. Try to:
        - connect `sig_tx` and `sig_rx`
        - set the TabToolTip from the instance attribute `tool_tip`
        - set the tab label from the instance attribute `tab_label`
        for each widget.
        """
        tabWidget = QTabWidget(self)
        tabWidget.setObjectName("plot_tabs")
        inst_wdg_list = "" # successfully instantiated plot widgets
        #
        for i, plot_wdg in enumerate(fb.plot_widget_list):
            plot_mod_name = 'pyfda.' + plot_wdg_dir + '.' + plot_wdg.lower()
            try:  # Try to import the module from the package and get a handle:
                plot_mod = importlib.import_module(plot_mod_name)
                plot_class = getattr(plot_mod, plot_wdg, None)
                plot_inst = plot_class(self)
                if hasattr(plot_inst, 'tab_label'):
                    tabWidget.addTab(plot_inst, plot_inst.tab_label)
                else:
                    tabWidget.addTab(plot_inst, str(i))
                if hasattr(plot_inst, 'tool_tip'):
                    tabWidget.setTabToolTip(i, plot_inst.tool_tip)
                if hasattr(plot_inst, 'sig_tx'):
                    plot_inst.sig_tx.connect(self.sig_rx)
                if hasattr(plot_inst, 'sig_rx'):
                    self.sig_tx.connect(plot_inst.sig_rx)

                inst_wdg_list += '\t' + 'pyfda.' + plot_wdg_dir + '.' + plot_wdg + '\n'

            except ImportError as e:
                logger.warning('Plotting module "{0}" could not be imported.\n{1}'\
                               .format(plot_mod_name, e))
                continue
            except Exception as e:
                logger.warning("Unexpected error during module import:\n{0}".format(e))
                continue

        if len(inst_wdg_list) == 0:
            logger.warning("No plotting widgets found!")
        else:
            logger.info("Imported the following plotting classes:\n{0}".format(inst_wdg_list))
        #----------------------------------------------------------------------
        layVMain = QVBoxLayout()
        layVMain.addWidget(tabWidget)
        layVMain.setContentsMargins(*params['wdg_margins'])#(left, top, right, bottom)

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.timer_id = QtCore.QTimer()
        self.timer_id.setSingleShot(True)
        # redraw current widget at timeout (timer was triggered by resize event):
        self.timer_id.timeout.connect(self.current_tab_redraw)

        # When user has selected a different tab, trigger a redraw of current tab
        tabWidget.currentChanged.connect(self.current_tab_changed)
        # The following does not work: maybe current scope must be left?
        # tabWidget.currentChanged.connect(tabWidget.currentWidget().redraw)

        tabWidget.installEventFilter(self)


    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming in via sig_rx
        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if type(dict_sig) != dict:
            dict_sig = {'sender':__name__}
        self.sig_tx.emit(dict_sig)

        """
        https://stackoverflow.com/questions/29128936/qtabwidget-size-depending-on-current-tab

        The QTabWidget won't select the biggest widget's height as its own height
        unless you use layout on the QTabWidget. Therefore, if you want to change
        the size of QTabWidget manually, remove the layout and call QTabWidget::resize
        according to the currentChanged signal.

        You can set the size policy of the widget that is displayed to QSizePolicy::Preferred
        and the other ones to QSizePolicy::Ignored. After that call adjustSize to update the sizes.

        void MainWindow::updateSizes(int index)
        {
        for(int i=0;i<ui->tabWidget->count();i++)
            if(i!=index)
                ui->tabWidget->widget(i)->setSizePolicy(QSizePolicy::Ignored, QSizePolicy::Ignored);

        ui->tabWidget->widget(index)->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Preferred);
        ui->tabWidget->widget(index)->resize(ui->tabWidget->widget(index)->minimumSizeHint());
        ui->tabWidget->widget(index)->adjustSize();
        resize(minimumSizeHint());
        adjustSize();
        }

        adjustSize(): The last two lines resize the main window itself. You might want to avoid it,
        depending on your application. For example, if you set the rest of the widgets
        to expand into the space just made available, it's not so nice if the window
        resizes itself instead.
        """

#------------------------------------------------------------------------------
    def current_tab_changed(self):
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'changed'})

#------------------------------------------------------------------------------
    def current_tab_redraw(self):
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'resized'})

#------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by the QTabWidget. Source and type of all
         events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.

        This filter stops and restarts a one-shot timer for every resize event.
        When the timer generates a timeout after 500 ms, current_tab_redraw is
        called by the timer.
        """
        if isinstance(source, QTabWidget):
            if event.type() == QEvent.Resize:
                self.timer_id.stop()
                self.timer_id.start(500)

        # Call base class method to continue normal event processing:
        return super(PlotTabWidgets, self).eventFilter(source, event)

#------------------------------------------------------------------------

def main():
    import sys
    from pyfda import pyfda_rc as rc
    from ..compat import QApplication

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)

    mainw = PlotTabWidgets(None)
    mainw.resize(300,400)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
# test with: python -m  pyfda.plot_widgets.plot_tab_widgets