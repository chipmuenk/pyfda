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
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import importlib
import logging
logger = logging.getLogger(__name__)

from ..compat import QTabWidget, QWidget, QVBoxLayout, QScrollArea, pyqtSignal

SCROLL = True

from pyfda.pyfda_rc import params
import pyfda.filterbroker as fb

class InputTabWidgets(QWidget):
    """
    Create a tabbed widget for all input subwidgets in the list ``fb.input_widgets_list``.
    This list is compiled at startup in :class:`pyfda.tree_builder.Tree_Builder`.
    """
    # signals as class variables (shared between instances if more than one exists)
    # incoming, connected here to individual senders, passed on to process sigmals
    sig_rx = pyqtSignal(object)
    # outgoing, connected in receiver (pyfdax -> plot_tab_widgets)
    sig_tx = pyqtSignal(object)


    def __init__(self, parent):
        
        super(InputTabWidgets, self).__init__(parent)
        self._construct_UI()

    def _construct_UI(self):
        """
        Initialize UI with tabbed subwidgets and connect the signals of all
        subwidgets.
        """
        tabWidget = QTabWidget(self)

        n_wdg = 0 # number and ... 
        inst_wdg_str = "" # ... full names of successfully instantiated widgets
        #
        # wdg = (class_name, dir)
        for wdg in fb.input_widgets_list:
            if not wdg[1]:
                # dir is empty, use standard input widgets package
                pckg_name = 'pyfda.input_widgets'
            else:
                # check and extract user directory
                if os.path.isdir(wdg[1]):
                    pckg_path = os.path.normpath(wdg[1])
                    # split the path into the dir containing the module and its name
                    user_dir_name, pckg_name = os.path.split(pckg_path)

                    if user_dir_name not in sys.path:
                        sys.path.append(user_dir_name)
                else:
                    logger.warning("Path {0:s} doesn't exist!".format(wdg[2]))
                    continue
            mod_name = pckg_name + '.' + wdg[0].lower()
            class_name = pckg_name + '.' + wdg[0]

            try:  # Try to import the module from the package ...
                mod = importlib.import_module(mod_name)
                # get the class belonging to wdg[0] ...
                wdg_class = getattr(mod, wdg[0])
                # and instantiate it
                inst = wdg_class(self)

                if hasattr(inst, "state") and inst.state == "deactivated":
                    continue # with next widget
                elif hasattr(inst, 'tab_label'):
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
            logger.warning("No input widgets found!")
        else:
            logger.info("Imported {0:d} input classes:\n{1}"
                        .format(n_wdg, inst_wdg_str))

        #
        # TODO: document signal options

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------       
        #self.sig_rx.connect(inst.sig_rx) # happens in _construct_UI()
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------       
        self.sig_tx.connect(self.sig_rx) # loop back to local inputs

        # When user has selected a different tab, trigger a redraw of current tab
        tabWidget.currentChanged.connect(self.current_tab_changed)
        # The following does not work: maybe current scope must be left?
        # tabWidget.currentChanged.connect(tabWidget.currentWidget().redraw)


        layVMain = QVBoxLayout()

        #setContentsMargins -> number of pixels between frame window border
        layVMain.setContentsMargins(*params['wdg_margins']) 

#--------------------------------------
        if SCROLL:
            scroll = QScrollArea(self)
            scroll.setWidget(tabWidget)
            scroll.setWidgetResizable(True) # Size of monitored widget is allowed to grow:

            layVMain.addWidget(scroll)
        else:
            layVMain.addWidget(tabWidget) # add the tabWidget directly

        self.setLayout(layVMain) # set the main layout of the window

#------------------------------------------------------------------------------
    def current_tab_changed(self):
        self.sig_tx.emit({'sender':__name__, 'ui_changed':'tab'})

#------------------------------------------------------------------------

def main():
    from pyfda import pyfda_rc as rc
    from ..compat import QApplication
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.css_rc)

    mainw = InputTabWidgets(None)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
