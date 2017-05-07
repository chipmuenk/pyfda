# -*- coding: utf-8 -*-
"""
Widget stacking all subwidgets for filter specification and design

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
from pprint import pformat
import logging
logger = logging.getLogger(__name__)

import numpy as np

from ..compat import (QWidget, QLabel, QFrame, QPushButton, pyqtSignal, QtGui,
                      QVBoxLayout, QHBoxLayout, QSizePolicy)

import pyfda.filterbroker as fb
import pyfda.filter_factory as ff
from pyfda.pyfda_lib import style_widget #HLine
from pyfda.pyfda_rc import params

from pyfda.input_widgets import (select_filter, amplitude_specs,
                                 freq_specs, freq_units,
                                 weight_specs, target_specs)


class FilterSpecs(QWidget):
    """
    Build widget for entering all filter specs
    """
    # class variables (shared between instances if more than one exists)
    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal() # emitted when specs have been changed
    sigViewChanged = pyqtSignal() # emitted when view has changed
    sigQuit = pyqtSignal() # emitted when >QUIT< button is clicked

    def __init__(self, parent):
        super(FilterSpecs, self).__init__(parent)

        self._construct_UI()

    def _construct_UI(self):
        """
        Construct User Interface from all input subwidgets
        """
        # Subwidget for selecting filter with response type rt (LP, ...),
        #    filter type ft (IIR, ...) and filter class fc (cheby1, ...)
        self.sel_fil = select_filter.SelectFilter(self)
        self.sel_fil.setObjectName("select_filter")
        # Subwidget for selecting the frequency unit and range
        self.f_units = freq_units.FreqUnits(self)
        self.f_units.setObjectName("freq_units")
        # Subwidget for Frequency Specs
        self.f_specs = freq_specs.FreqSpecs(self)
        self.f_specs.setObjectName("freq_specs")
        # Subwidget for Amplitude Specs
        self.a_specs = amplitude_specs.AmplitudeSpecs(self)
        self.a_specs.setObjectName("amplitude_specs")
        # Subwidget for Weight Specs
        self.w_specs = weight_specs.WeightSpecs(self)
        self.w_specs.setObjectName("weight_specs")
        # Subwidget for target specs (frequency and amplitude)
        self.t_specs = target_specs.TargetSpecs(self, title="Target Specifications")
        self.t_specs.setObjectName("target_specs")
        # Subwidget for displaying infos on the design method
        self.lblMsg = QLabel(self)
        self.lblMsg.setWordWrap(True)
        layVMsg = QVBoxLayout()
        layVMsg.addWidget(self.lblMsg)

        self.frmMsg = QFrame(self)
        self.frmMsg.setLayout(layVMsg)
        layVFrm = QVBoxLayout()
        layVFrm.addWidget(self.frmMsg)
        layVFrm.setContentsMargins(*params['wdg_margins'])

        self.butDesignFilt = QPushButton("DESIGN FILTER", self)
        self.butQuit = QPushButton("Quit", self)
        layHButtons = QHBoxLayout()
        layHButtons.addWidget(self.butDesignFilt)  # <Design Filter> button
        layHButtons.addWidget(self.butQuit)        # <Quit> button
        layHButtons.setContentsMargins(*params['wdg_margins'])

        #----------------------------------------------------------------------
        # LAYOUT for input specifications and buttons
        #----------------------------------------------------------------------
        layVMain = QVBoxLayout(self)
        layVMain.addWidget(self.sel_fil)  # Design method (IIR - ellip, ...)         
        layVMain.addLayout(layHButtons)   # <Design> & <Quit> buttons
        layVMain.addWidget(self.f_units)  # Frequency units
        layVMain.addWidget(self.t_specs)  # Target specs
        layVMain.addWidget(self.f_specs)  # Freq. specifications
        layVMain.addWidget(self.a_specs)  # Amplitude specs
        layVMain.addWidget(self.w_specs)  # Weight specs
        layVMain.addLayout(layVFrm)       # Text message

        layVMain.addStretch()

        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain) # main layout of widget

        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        #
        # Changing the filter design requires updating UI because number or
        # kind of input fields changes -> Call update_all_UIs, emitting
        # sigFilterChanged when it's finished
        self.sel_fil.sigFiltChanged.connect(self.update_UI)

        # Changing the frequency unit requires re-display of frequency specs
        # but it does not influence the actual specs (no specsChanged )
        self.f_units.sigUnitChanged.connect(self.f_specs.load_dict)
        self.f_units.sigUnitChanged.connect(self.t_specs.load_dict)
        self.f_units.sigUnitChanged.connect(self.sigViewChanged)
        # Activating the "Sort" button triggers sigSpecsChanged, requiring
        # sorting and storing the frequency entries
        self.f_units.sigSpecsChanged.connect(self.f_specs.sort_dict_freqs)
        self.f_units.sigSpecsChanged.connect(self.t_specs.f_specs.sort_dict_freqs)


        # Changing filter parameters / specs requires reloading of parameters
        # in other hierarchy levels, e.g. in the plot tabs
        # bundle sigSpecsChanged signals and propagate to next hierarchy level
#        self.f_units.sigSpecsChanged.connect(self.sigSpecsChanged)
        self.f_specs.sigSpecsChanged.connect(self.sigSpecsChanged)
        self.t_specs.sigSpecsChanged.connect(self.sigSpecsChanged)
        self.a_specs.sigSpecsChanged.connect(self.sigSpecsChanged)
        self.a_specs.sigUnitChanged.connect(self.sigViewChanged)
        self.w_specs.sigSpecsChanged.connect(self.sigSpecsChanged)

        # Other signal-slot connections
        self.butDesignFilt.clicked.connect(self.start_design_filt)
        self.butQuit.clicked.connect(self.sigQuit) # pass on to main application
        #----------------------------------------------------------------------

        self.update_UI() # first time initialization
        self.start_design_filt() # design first filter using default values

#------------------------------------------------------------------------------
    def update_UI(self):
        """
        update_UI is called every time the filter design method or order
        (min / man) has been changed as this usually requires a different set of
        frequency and amplitude specs.

        At this time, the actual filter object instance has been created from
        the name of the design method (e.g. 'cheby1') in select_filter.py.
        Its handle has been stored in fb.fil_inst.

        fb.fil[0] (currently selected filter) is read, then general information
        for the selected filter type and order (min/man) is gathered from
        the filter tree [fb.fil_tree], i.e. which parameters are needed, which
        widgets are visible and which message shall be displayed.

        Then, the UIs of all subwidgets are updated using their "update_UI" method,
        finally the signal 'sigSpecsChanged' is emitted.
        """
        rt = fb.fil[0]['rt'] # e.g. 'LP'
        ft = fb.fil[0]['ft'] # e.g. 'FIR'
        fc = fb.fil[0]['fc'] # e.g. 'equiripple'
        fo = fb.fil[0]['fo'] # e.g. 'man'

        # the keys of the all_widgets dict are the names of the subwidgets,
        # the values are a tuple with the corresponding parameters
        all_widgets = fb.fil_tree[rt][ft][fc][fo]

        logger.debug("rt: {0} - ft: {1} - fc: {2} - fo: {3}".format(rt, ft, fc, fo))
        logger.debug("fb.fil_tree[rt][ft][fc][fo]:\n{0}".format(fb.fil_tree[rt][ft][fc][fo]))

        # self.sel_fil.load_filter_order() # update filter order subwidget, called by select_filter

        if ('tspecs' in all_widgets and len(all_widgets['tspecs']) > 1 and
                                              all_widgets['tspecs'][0] != 'i'):
            self.t_specs.setVisible(True)
            self.t_specs.setEnabled(all_widgets['tspecs'][0] != 'd')
            self.t_specs.update_UI(new_labels=all_widgets['tspecs'][1])
        else:
            self.t_specs.hide()

        if ('fspecs' in all_widgets and len(all_widgets['fspecs']) > 1 and
                                              all_widgets['fspecs'][0] != 'i'):
            self.f_specs.setVisible(True)
            self.f_specs.setEnabled(all_widgets['fspecs'][0] != 'd')
            self.f_specs.update_UI(new_labels=all_widgets['fspecs'])
        else:
            self.f_specs.hide()

        if ('aspecs' in all_widgets and len(all_widgets['aspecs']) > 1 and
                                              all_widgets['aspecs'][0] != 'i'):
            self.a_specs.setVisible(True)
            self.a_specs.setEnabled(all_widgets['aspecs'][0] != 'd')
            self.a_specs.update_UI(new_labels=all_widgets['aspecs'])
        else:
            self.a_specs.hide()

        if ('wspecs' in all_widgets and len(all_widgets['wspecs']) > 1 and
                                              all_widgets['wspecs'][0] != 'i'):
            self.w_specs.setVisible(True)
            self.w_specs.setEnabled(all_widgets['wspecs'][0] != 'd')
            self.w_specs.update_UI(new_labels=all_widgets['wspecs'])
        else:
            self.w_specs.hide()

        if ('msg' in all_widgets and len(all_widgets['msg']) > 1  and
                                              all_widgets['msg'][0] != 'i'):
            self.frmMsg.setVisible(True)
            self.frmMsg.setEnabled(all_widgets['msg'][0] != 'd')
            self.lblMsg.setText(all_widgets['msg'][1:][0])
        else:
            self.frmMsg.hide()

        logger.debug("emit sigSpecsChanged")
        self.sigSpecsChanged.emit()

#------------------------------------------------------------------------------
    def load_dict(self):
        """
        Reload all specs/parameters entries from global dict fb.fil[0],
        using the "load_dict" methods of the individual classes
        """
        self.sel_fil.load_dict() # select filter widget
        self.f_units.load_dict() # frequency units widget
        self.f_specs.load_dict() # frequency specification widget
        self.a_specs.load_dict() # magnitude specs with unit
        self.w_specs.load_dict() # weight specification
        self.t_specs.load_dict() # target specs
        
        fb.design_filt_state = "ok"            
        style_widget(self.butDesignFilt, "ok")

#------------------------------------------------------------------------------
    def start_design_filt(self):
        """
        Start the actual filter design process:
        - store the entries of all input widgets in the global filter dict.
        - call the design method, passing the whole dictionary as the
          argument: let the design method pick the needed specs
        - update the input widgets in case weights, corner frequencies etc.
          have been changed by the filter design method
        - the plots are updated via signal-slot connection
        """
        logger.debug("start_design_filt - Specs:\n"
            "fb.fil[0]: %s\n"
            "fb.fil[0]['fc'] %s.%s%s",
            pformat(fb.fil[0]), str(fb.fil[0]['fc']), str(fb.fil[0]['rt']),
                         str(fb.fil[0]['fo']))

        logger.info("startDesignFilt using: %s\nmethod: %s\n",
            str(type(ff.fil_inst)), str(fb.fil[0]['fc']))

        try:
            #----------------------------------------------------------------------
            # A globally accessible instance fb.fil_inst of selected filter class fc
            # has been instantiated in InputFilter.set_design_method, now
            # call the method specified in the filter dict fil[0].

            # The name of the instance method is constructed from the response
            # type (e.g. 'LP') and the filter order (e.g. 'man'), giving e.g. 'LPman'.
            # The filter is designed by passing the specs in fil[0] to the method,
            # resulting in e.g. cheby1.LPman(fb.fil[0]) and writing back coefficients,
            # P/Z etc. back to fil[0].

            err = ff.fil_factory.call_fil_method(fb.fil[0]['rt'] + fb.fil[0]['fo'], fb.fil[0])
            # this is the same as e.g.
            # from pyfda.filter_design import ellip
            # inst = ellip.ellip()
            # inst.LPmin(fb.fil[0])
            #-----------------------------------------------------------------------

            if err > 0:
                raise AttributeError("Unknown design method.")
                self.color_design_button("error")
            # Update filter order. weights and freq display in case they
            # have been changed by the design algorithm
            self.sel_fil.load_filter_order()
            self.w_specs.load_dict()
            self.f_specs.load_dict()

            self.color_design_button("ok")

            self.sigFilterDesigned.emit() # emit signal -> InputTabWidgets.update_all

        except Exception as e:
            logger.warning("start_design_filt:\n%s\n%s\n", e.__doc__, e)
            
            self.color_design_button("error")

        logger.debug("start_design_filt - Results:\n"
            "F_PB = %s, F_SB = %s\n"
            "Filter order N = %s\n"
            "NDim fil[0]['ba'] = %s\n\n"
            "b,a = %s\n\n"
            "zpk = %s\n",
            str(fb.fil[0]['F_PB']), str(fb.fil[0]['F_SB']), str(fb.fil[0]['N']),
            str(np.ndim(fb.fil[0]['ba'])), pformat(fb.fil[0]['ba']),
                pformat(fb.fil[0]['zpk'])
              )

    def color_design_button(self, state):
        fb.design_filt_state = state
        style_widget(self.butDesignFilt, state)


#------------------------------------------------------------------------------

if __name__ == '__main__':
    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = FilterSpecs(None)
    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
