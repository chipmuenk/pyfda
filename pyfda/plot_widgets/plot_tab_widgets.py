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
from __future__ import print_function, division, unicode_literals, absolute_import

import logging
logger = logging.getLogger(__name__)

import os, sys
import importlib
from ..compat import QTabWidget, QVBoxLayout, QEvent, QtCore, pyqtSignal

from pyfda.pyfda_rc import params
import pyfda.filterbroker as fb

#------------------------------------------------------------------------------
class PlotTabWidgets(QTabWidget):

    # incoming, connected to input_tab_widget.sig_tx in pyfdax
    sig_rx = pyqtSignal(object)
    # outgoing: emitted by process_sig_rx
    sig_tx = pyqtSignal(object)

    def __init__(self, parent):
        super(PlotTabWidgets, self).__init__(parent)
        self._construct_UI()

#---------------------------------------------- --------------------------------
    def _construct_UI(self):
        """
        Initialize UI with tabbed subwidgets and connect the signals of all
        subwidgets.
        This is done by dynamically instantiating each widget from the list
        `fb.plot_widget_list` in the module `wdg_dir`. Try to:

        - connect `sig_tx` and `sig_rx`

        - set the TabToolTip from the instance attribute `tool_tip`

        - set the tab label from the instance attribute `tab_label`
          for each widget.
        """
        tabWidget = QTabWidget(self)
        tabWidget.setObjectName("plot_tabs")

        n_wdg = 0 # number and ...
        inst_wdg_str = "" # ... full names of successfully instantiated plot widgets
        #
        # wdg = (class_name, args, dir)
        for wdg in fb.plot_widgets_list:
            if not wdg[1]:
                # use standard plot module
                pckg_name = 'pyfda.plot_widgets'
            else:
                # check and extract user directory
                if os.path.isdir(wdg[1]):
                    pckg_path = os.path.normpath(wdg[1])
                    # split the path into the dir containing the module and its name
                    user_dir_name, pckg_name = os.path.split(pckg_path)

                    if user_dir_name not in sys.path:
                        sys.path.append(user_dir_name)
                else:
                    logger.warning("Path {0:s} doesn't exist!".format(wdg[1]))
                    continue
            mod_name = pckg_name + '.' + wdg[0].lower()
            class_name = pckg_name + '.' + wdg[0]

            try:  # Try to import the module from the package ...
                mod = importlib.import_module(mod_name)
                # get the class belonging to wdg[0] ...
                wdg_class = getattr(mod, wdg[0])
                # and instantiate it
                inst = wdg_class(self)
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

                n_wdg += 1 # successfully instantiated one more widget
                inst_wdg_str += '\t' + class_name + '\n'

            except ImportError as e:
                logger.warning('Module "{0}" could not be imported.\n{1}'\
                               .format(mod_name, e))
                continue

            except AttributeError as e:
                logger.warning('Module "{0}" could not be imported from {1}.\n{2}'\
                               .format(wdg[0], pckg_name, e))
                continue

        if len(inst_wdg_str) == 0:
            logger.warning("No plotting widgets found!")
        else:
            logger.info("Imported {0:d} plotting classes:\n{1}".format(n_wdg, inst_wdg_str))
        #----------------------------------------------------------------------
        layVMain = QVBoxLayout()
        layVMain.addWidget(tabWidget)
        layVMain.setContentsMargins(*params['wdg_margins'])#(left, top, right, bottom)

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # self.sig_rx.connect(inst.sig_rx) # this happens in _construct_UI()
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.timer_id = QtCore.QTimer()
        self.timer_id.setSingleShot(True)
        # redraw current widget at timeout (timer was triggered by resize event):
        self.timer_id.timeout.connect(self.current_tab_redraw)

        self.sig_tx.connect(self.sig_rx) # loop back to local inputs

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
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'tab'})

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
        When the timer generates a timeout after 500 ms, ``current_tab_redraw()`` is
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