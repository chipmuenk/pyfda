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

from ..compat import QTabWidget, QWidget, QVBoxLayout, QScrollArea, pyqtSignal, pyqtSlot

SCROLL = True

from pyfda.pyfda_rc import params
from pyfda.pyfda_lib import mod_version

from pyfda.input_widgets import (filter_specs, file_io, filter_coeffs,
                                filter_info, filter_pz)

if mod_version("myhdl"):
    from pyfda.hdl_generation import hdl_specs
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
        tabWidget.addTab(self.filter_specs, 'Specs')
        tabWidget.setTabToolTip(0, "Enter and view filter specifications.")
        #
        self.filter_coeffs = filter_coeffs.FilterCoeffs(self)
        self.filter_coeffs.sig_tx.connect(self.sig_rx)
        tabWidget.addTab(self.filter_coeffs, 'b,a')
        tabWidget.setTabToolTip(1, "Display and edit filter coefficients.")
        #
        self.filter_pz = filter_pz.FilterPZ(self)
        self.filter_pz.sig_tx.connect(self.sig_rx)
        tabWidget.addTab(self.filter_pz, 'P/Z')
        tabWidget.setTabToolTip(2, "Display and edit filter poles and zeros.")
        #
        self.file_io = file_io.File_IO(self)
        self.file_io.sig_tx.connect(self.sig_rx)
        tabWidget.addTab(self.file_io, 'Files')
        tabWidget.setTabToolTip(3, "Import and export filter designs and coefficients.")
        #
        self.filter_info = filter_info.FilterInfo(self)
        tabWidget.addTab(self.filter_info, 'Info')
        tabWidget.setTabToolTip(4, "<span>Display the achieved filter specifications"
                                   " and more info about the filter design algorithm.</span>")        
        if HAS_MYHDL:
            self.hdlSpecs = hdl_specs.HDLSpecs(self)
            tabWidget.addTab(self.hdlSpecs, 'HDL')

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


        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # Collect "specs changed" / "filter designed" signals from all input
        # widgets and route them to plot / input widgets that need to be updated
        #
        # Check:
        #http://www.pythoncentral.io/pysidepyqt-tutorial-creating-your-own-signals-and-slots/#custom-tab-2-pyqt
        #
        # sigSpecsChanged: signal indicating that filter SPECS have changed,
        #       requiring update of some plot widgets and input widgets:
        self.filter_specs.sigSpecsChanged.connect(self.update_specs)
        # sigViewChanged: signal indicating that PLOT VIEW has changed,
        #       requiring update of some plot widgets only:
        self.filter_specs.sigViewChanged.connect(self.update_view)
        #
        # sigFilterDesigned: signal indicating that filter has been DESIGNED,
        #       requiring update of all plot and some input widgets:
        self.filter_specs.sigFilterDesigned.connect(self.update_data)

        # The following widgets require a reloading of the select_filter
        # widget to update the filter selection:
        self.filter_coeffs.ui.sig_tx.connect(self.filter_pz.ui.sig_rx)
        self.filter_pz.ui.sig_tx.connect(self.filter_coeffs.ui.sig_rx)
        
        self.sig_rx.connect(self.process_signals)
        #----------------------------------------------------------------------

#------------------------------------------------------------------------------
    @pyqtSlot(object)
    def process_signals(self, dict_sig=None):
        """
        Process signals coming from sig_rx
        """
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if 'load_dict' in dict_sig:
            self.load_dict(dict_sig)
        elif 'view_changed' in dict_sig:
            self.update_view(dict_sig)
        elif 'specs_changed' in dict_sig:
            self.update_specs(dict_sig)
        elif 'data_changed' in dict_sig:
            if dict_sig['data_changed'] == 'filter_loaded':
                self.update_filter_data(dict_sig)
            else:
                self.update_data(dict_sig)
        else:
            logger.debug("Dict {0} passed thru".format(dict_sig))


    def update_view(self, dict_sig=None):
        """
        Slot for InputSpecs.sigViewChanged

        Propagate new PLOT VIEW (e.g. log scale, single/double sided) to
        plot widgets via pyfda.py

        Update plot widgets via sigSpecsChanged signal that need new
            specs, e.g. plotHf widget for the filter regions
        """
        if type(dict_sig) != dict:
            dict_sig = {'sender':__name__,'view_changed':True}
        self.filter_info.load_dict() # update frequency unit of info widget

        self.sig_tx.emit(dict_sig)


    def update_specs(self, dict_sig=None):
        """
        Slot for FilterSpecs.sigSpecsChanged

        Propagate new filter SPECS from filter dict to other input widgets and
        to plot widgets via pyfda.py

        - Update input widgets that can / need to display specs (except inputSpecs
             - the origin of the signal !!)
        - Update plot widgets via sigSpecsChanged signal that need new
            specs, e.g. plotHf widget for the filter regions
        """

        self.filter_specs.color_design_button("changed")

        if type(dict_sig) != dict:
            dict_sig = {'sender':__name__,'specs_changed':True}
        self.filter_info.load_dict()
        if HAS_MYHDL:
            self.hdlSpecs.update_UI()

        self.sig_tx.emit(dict_sig)

    def update_filter_data(self, dict_sig=None):
        """
        Called when a new filter has been LOADED:
        Pass new filter data from the global filter dict
        - Specifically call SelectFilter.load_dict
        - Update the input widgets that can / need to display filter data
          and all plot widgets via `update_data()`.
        """
        if type(dict_sig) != dict:
            dict_sig = {'sender':__name__,'data_changed':True}
        self.filter_specs.sel_fil.load_dict() # update select_filter widget
        self.update_data(dict_sig)

    def update_data(self, dict_sig=None):
        """
        Slot for sigFilterDesigned from InputSpecs, FilterCoeffs, FilterPZ

        Called when a new filter has been DESIGNED:
        - Pass new filter data from the global filter dict
        - Update the input widgets that can / need to display filter data
        - Update all plot widgets by emitting sig_tx = 'data_changed':True

        """
        self.filter_specs.color_design_button("ok")
        if type(dict_sig) != dict:
            dict_sig = {'sender':__name__,'data_changed':True}

        self.filter_specs.load_dict()
        self.filter_info.load_dict()
        self.filter_coeffs.load_dict()
        self.filter_pz.load_dict()

        logger.debug("Emit sig_tx = 'filter_designed'")
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
