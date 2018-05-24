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
import sys
import logging
logger = logging.getLogger(__name__)

from ..compat import QTabWidget, QWidget, QVBoxLayout, QScrollArea, pyqtSignal

SCROLL = True

from pyfda.pyfda_rc import params
from pyfda.pyfda_lib import cmp_version

from pyfda.input_widgets import (filter_specs, file_io, input_coeffs,
                                filter_info, filter_pz)

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
        tabWidget.setObjectName("input_tabs")
        #
        self.filter_specs = filter_specs.FilterSpecs(self)
        self.filter_specs.sig_tx.connect(self.sig_rx)
        self.sig_tx.connect(self.filter_specs.sig_rx)   # comment out (infinite loop)
        tabWidget.addTab(self.filter_specs, 'Specs')
        tabWidget.setTabToolTip(0, "Enter and view filter specifications.")
        #
        self.filter_coeffs = filter_coeffs.Filter_Coeffs(self)
        self.filter_coeffs.sig_tx.connect(self.sig_rx)
        self.sig_tx.connect(self.filter_coeffs.sig_rx)
        tabWidget.addTab(self.filter_coeffs, 'b,a')
        tabWidget.setTabToolTip(1, "Display and edit filter coefficients.")
        #
        self.filter_pz = filter_pz.FilterPZ(self)
        self.filter_pz.sig_tx.connect(self.sig_rx)
        self.sig_tx.connect(self.filter_pz.sig_rx)
        tabWidget.addTab(self.filter_pz, 'P/Z')
        tabWidget.setTabToolTip(2, "Display and edit filter poles and zeros.")
        #
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
        elif 'specs_changed' in dict_sig:
            self.filter_specs.color_design_button("changed")
            if HAS_MYHDL:
                self.hdlSpecs.update_UI()

        elif 'data_changed' in dict_sig:
            if dict_sig['data_changed'] == 'filter_loaded':
                self.filter_specs.color_design_button("ok")
                """
                Called when a new filter has been LOADED:
                Pass new filter data from the global filter dict by
                specifically calling SelectFilter.load_dict()
                """
                self.filter_specs.sel_fil.load_dict() # update select_filter widget
            self.filter_specs.load_dict() # Pass new filter data from the global filter dict
        else:
            logger.debug("Dict {0} passed thru".format(dict_sig))

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
