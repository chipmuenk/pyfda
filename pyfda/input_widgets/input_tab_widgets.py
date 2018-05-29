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
from pyfda.pyfda_lib import cmp_version
import pyfda.filterbroker as fb

from pyfda.input_widgets import (file_io, filter_info)

if cmp_version("myhdl", "0.10") >= 0:
    from pyfda.fixpoint_filters import hdl_specs
    HAS_MYHDL = True
else:
    HAS_MYHDL = False


class InputTabWidgets(QWidget):
    """
    Create a tabbed widget for various input subwidgets
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

        inst_wdg_list = "" # successfully instantiated plot widgets
        n_wdg = 0 # number of successfully instantiated plot widgets
        #
        for i, wdg in enumerate(fb.input_widgets_list):
            if not wdg[1]:
                # use standard input widgets package
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
                    logger.warning("Path {0:s} doesn't exist!".format(wdg[1]))
                    continue
            mod_name = pckg_name + '.' + wdg[0].lower()
            class_name = pckg_name + '.' + wdg[0]

            try:  # Try to import the module from the package and get a handle:
                input_mod = importlib.import_module(mod_name)
                input_class = getattr(input_mod, wdg[0])
                input_inst = input_class(self)
                if hasattr(input_inst, 'tab_label'):
                    tabWidget.addTab(input_inst, input_inst.tab_label)
                else:
                    tabWidget.addTab(input_inst, str(i))
                if hasattr(input_inst, 'tool_tip'):
                    tabWidget.setTabToolTip(i, input_inst.tool_tip)
                if hasattr(input_inst, 'sig_tx'):
                    input_inst.sig_tx.connect(self.sig_rx)
                if hasattr(input_inst, 'sig_rx'):
                    self.sig_tx.connect(input_inst.sig_rx)

                inst_wdg_list += '\t' + class_name + '\n'
                n_wdg += 1

            except ImportError as e:
                logger.warning('Module "{0}" could not be imported.\n{1}'\
                               .format(mod_name, e))
                continue
            except AttributeError as e:
                logger.warning('Module "{0}" could not be imported from {1}.\n{2}'\
                               .format(wdg[0], mod_name, e))
                continue

            #except Exception as e:
             #   logger.warning("Unexpected error during module import:\n{0}".format(e))
              #  continue

        if len(inst_wdg_list) == 0:
            logger.warning("No input widgets found!")
        else:
            logger.info("Imported {0:d} input classes:\n{1}".format(n_wdg, inst_wdg_list))

        #
        # TODO: document signal options
        self.file_io = file_io.File_IO(self)
        self.file_io.sig_tx.connect(self.sig_rx)
        tabWidget.addTab(self.file_io, 'Files')
        tabWidget.setTabToolTip(3, "Load and save filter designs.")
        #
        self.filter_info = filter_info.FilterInfo(self)
        self.sig_tx.connect(self.filter_info.sig_rx)
        tabWidget.addTab(self.filter_info, 'Info')
        tabWidget.setTabToolTip(4, "<span>Display the achieved filter specifications"
                                   " and more info about the filter design algorithm.</span>")        
        if HAS_MYHDL:
            self.hdlSpecs = hdl_specs.HDL_Specs(self)
            tabWidget.addTab(self.hdlSpecs, 'HDL')
            #self.sig_tx.connect(self.hdlSpecs.sig_rx)
  
        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------       
        self.sig_rx.connect(self.process_sig_rx)


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
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if dict_sig['sender'] == __name__:
            logger.warning("Prevented Infinite Loop!")
            return

        self.sig_tx.emit(dict_sig)

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
