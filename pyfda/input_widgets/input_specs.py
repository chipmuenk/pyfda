# -*- coding: utf-8 -*-
"""
Widget stacking all subwidgets for filter specification and design

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import numpy as np
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import pyfda.filterbroker as fb

from pyfda.input_widgets import (input_filter, input_amp_specs,
                                 input_freq_specs, input_freq_units,
                                 input_weight_specs, input_target_specs)


class InputSpecs(QtGui.QWidget):
    """
    Build widget for entering all filter specs
    """
    # class variables (shared between instances if more than one exists)
    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal() # emitted when specs have been changed
    sigViewChanged = pyqtSignal() # emitted when view has changed
    

    def __init__(self, DEBUG=True):
        super(InputSpecs, self).__init__()

        self.DEBUG = DEBUG
        self._init_UI()

    def _init_UI(self):
        """
        Create all subwidgets
        """
        # Subwidget for selecting filter with response type rt (LP, ...), 
        #    filter type ft (IIR, ...) and design method dm (cheby1, ...)
        self.sel_fil = input_filter.InputFilter(DEBUG=False)
        self.sel_fil.setObjectName("select_filter")
        # Subwidget for selecting the frequency unit and range
        self.f_units = input_freq_units.InputFreqUnits(DEBUG=False)
        self.f_units.setObjectName("freq_units")
        # Subwidget for Frequency Specs
        self.f_specs = input_freq_specs.InputFreqSpecs(DEBUG=False)
        self.f_specs.setObjectName("freq_specs")
        # Subwidget for Amplitude Specs
        self.a_specs = input_amp_specs.InputAmpSpecs(DEBUG=False)
        self.a_specs.setObjectName("amp_specs")
        # Subwidget for Weight Specs
        self.w_specs = input_weight_specs.InputWeightSpecs(DEBUG=False)
        self.w_specs.setObjectName("weight_specs")
        # Subwidget for target specs (frequency and amplitude)
        self.t_specs = input_target_specs.InputTargetSpecs(DEBUG=False,
                                            title="Target Specifications")
        self.t_specs.setObjectName("target_specs")
        # Subwidget for displaying infos on the design method
        self.lblMsg = QtGui.QLabel(self)
        self.lblMsg.setWordWrap(True)
#        self.lblMsg.setFrameShape(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)

        layVMsg = QtGui.QVBoxLayout()
        layVMsg.addWidget(self.lblMsg)

        frmMsg = QtGui.QFrame()
        frmMsg.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        frmMsg.setLayout(layVMsg)
        frmMsg.setSizePolicy(QtGui.QSizePolicy.Minimum,
                             QtGui.QSizePolicy.Minimum)

        self.butDesignFilt = QtGui.QPushButton("DESIGN FILTER", self)
        self.butQuit = QtGui.QPushButton("Quit", self)

        #----------------------------------------------------------------------
        # LAYOUT for input specifications and buttons
        #----------------------------------------------------------------------
        spcV = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum,
                                       QtGui.QSizePolicy.Expanding)
        layGMain = QtGui.QGridLayout()
        layGMain.addWidget(self.sel_fil, 0, 0, 1, 2)  # Design method (IIR - ellip, ...)
        layGMain.addWidget(self.f_units, 2, 0, 1, 2)  # Frequency units
        layGMain.addWidget(self.f_specs, 3, 0, 1, 2)  # Freq. specifications
        layGMain.addWidget(self.a_specs, 4, 0, 1, 2)  # Amplitude specs
        layGMain.addWidget(self.w_specs, 5, 0, 1, 2)  # Weight specs
        layGMain.addWidget(frmMsg, 6, 0, 1, 2)        # Text message
        layGMain.addWidget(self.t_specs, 7, 0, 1, 2)  # Target specs
        layGMain.addWidget(self.butDesignFilt, 8, 0)  # <Design Filter> button
        layGMain.addWidget(self.butQuit, 8, 1)        # <Quit> button
        layGMain.addItem(spcV, 9, 0, 1, 2)
#        layGMain.addWidget(self.HLine(), 9,0,1,2) # create HLine
        layGMain.setContentsMargins(0, 0, 0, 0)


        self.setLayout(layGMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        #
        # Changing the filter design requires updating UI because number or 
        # kind of input fields changes -> Call update_all_UIs, emitting 
        # sigFilterChanged when it's finished
        self.sel_fil.sigFiltChanged.connect(self.update_all_UIs)

        # Changing the frequency unit requires re-display of frequency specs
        # but it not influence the actual specs (no specsChanged )
        self.f_units.sigSpecsChanged.connect(self.f_specs.load_entries)
        self.f_units.sigSpecsChanged.connect(self.t_specs.load_entries)
        self.f_units.sigSpecsChanged.connect(self.sigViewChanged.emit)

        # Changing filter parameters / specs requires reloading of parameters
        # in other hierarchy levels, e.g. in the plot tabs
        # bundle sigSpecsChanged signals and propagate to next hierarchy level
        self.f_units.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.f_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.t_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.a_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.w_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)

        # Other signal-slot connections
        self.butDesignFilt.clicked.connect(self.start_design_filt)
        self.butQuit.clicked.connect(QtGui.qApp.quit) # which qApp is this??
        #----------------------------------------------------------------------

        self.update_all_UIs() # first time initialization
        self.start_design_filt() # design first filter using default values

#------------------------------------------------------------------------------
    def update_all_UIs(self):
        """
        update_all_UIs is called every time the filter design method or order
        (min / man) has been changed. This usually requires a different set of
        frequency and amplitude specs.
        
        At this time, the actual filter object instance has been created from 
        the name of the design method (e.g. 'cheby1') in input_filter.py. 
        Its handle has been stored in fb.fil_inst.

        fb.fil[0] (currently selected filter) is read, then general information
        for the selected filter type and order (min/man) is gathered from
        the filter tree [fb.fil_tree], i.e. which parameters are needed, which
        widgets are visible and which message shall be displayed.

        Then, the UIs of all subwidgets are updated using their "updateUI" method,
        finally the signal 'sigSpecsChanged' is emitted.
        """

        rt = fb.fil[0]['rt'] # e.g. 'LP'
        ft = fb.fil[0]['ft'] # e.g. 'FIR'
        dm = fb.fil[0]['dm'] # e.g. 'equiripple'
        fo = fb.fil[0]['fo'] # e.g. 'man'
        # read all parameters for selected filter type, e.g. 'F_SB':
        all_params = fb.fil_tree[rt][ft][dm][fo]['par']

        vis_wdgs = fb.fil_tree[rt][ft][dm][fo]['vis'] # visible widgets
        dis_wdgs = fb.fil_tree[rt][ft][dm][fo]['dis'] # disabled widgets
        msg      = fb.fil_tree[rt][ft][dm][fo]['msg'] # message

        # Read freq / amp / weight labels for current filter design, building
        # separate parameter lists according to the first letter
        self.f_params = [l for l in all_params if l[0] == 'F'] # curr. not used
        self.a_params = [l for l in all_params if l[0] == 'A']
        self.weightParams = [l for l in all_params if l[0] == 'W']
        if self.DEBUG:
            print("=== InputParams.chooseDesignMethod ===")
            print("selFilter:", fb.fil[0])
            print('myLabels:', all_params)
            print('ampLabels:', self.a_params)
            print('freqLabels:', self.f_params)
            print('weightLabels:', self.weightParams)

        self.sel_fil.load_filter_order() # update filter order from dict

        # build separate parameter lists for min. and man. filter order        
        min_params = man_params = []
        
        if "min" in fb.fil_tree[rt][ft][dm]:
            min_params = fb.fil_tree[rt][ft][dm]['min']['par']
            
        if "man" in fb.fil_tree[rt][ft][dm]:
            man_params = fb.fil_tree[rt][ft][dm]['man']['par']

        # always use parameters for MANUAL filter order for f_specs widget,
        # frequency specs for minimum order are displayed in target specs
        self.f_man_params = [l for l in man_params if l[0] == 'F']
        self.f_specs.setVisible("fspecs" in vis_wdgs)
        self.f_specs.setEnabled("fspecs" not in dis_wdgs)
        self.f_specs.update_UI(newLabels=self.f_man_params)

        # always use parameters for MINIMUM filter order for target frequency
        # spec widget
        self.f_min_params = [l for l in min_params if l[0] == 'F']
        self.t_specs.setVisible("tspecs" in vis_wdgs)
        self.t_specs.setEnabled("tspecs" not in dis_wdgs)
        self.t_specs.update_UI(self.f_min_params, self.a_params)
        
        # self.a_specs.setVisible(self.a_params != [])
        self.a_specs.setVisible("aspecs" in vis_wdgs)
        self.a_specs.setEnabled("aspecs" not in dis_wdgs)
        self.a_specs.update_UI(newLabels=self.a_params)

        self.w_specs.setVisible("wspecs" in vis_wdgs)
        self.w_specs.setEnabled("wspecs" not in dis_wdgs)
        self.w_specs.update_UI(newLabels=self.weightParams)

        self.lblMsg.setText(msg)

        self.sigSpecsChanged.emit()


#------------------------------------------------------------------------------
#    def store_all_specs(self):
#        """
#        Store all entries of current filter design in global dict fb.fil[0]
#        parameters, using the "storeEntries" methods of the classes
#        -- not used yet & shouldn't be used as all UI changes are copied to 
#        the filter dict immediately.
#        """
#        # collect data from widgets and write to fb.fil[0]
##        self.sel_fil.store_entries() # filter order widget
#        self.f_specs.store_entries() # frequency specification widget
#        self.f_units.storeEntries() # frequency specification widget
#        self.a_specs.store_entries() # magnitude specs with unit
#        self.w_specs.storeEntries() # weight specification
#        self.t_specs.store_entries() # target specs

#------------------------------------------------------------------------------
    def load_all_specs(self):
        """
        Reload all specs/parameters from global dict fb.fil[0],
        using the "loadEntries" methods of the classes
        """
        self.sel_fil.load_entries() # select filter widget
        self.f_units.load_entries() # frequency units widget
        self.f_specs.load_entries() # frequency specification widget
        self.a_specs.load_entries() # magnitude specs with unit
        self.w_specs.load_entries() # weight specification
        self.t_specs.load_entries() # target specs

        if self.DEBUG:
            print("=== input_specs.py : loadAll ===")
            print(fb.fil[0])


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
#        self.storeAll() # store entries of all input widgets -> fb.fil[0]
#       this is not needed as individual subwidgets store results automatically
        if self.DEBUG:
            print("--- pyFDA.py : startDesignFilter: Specs ---")
            print('Specs:', fb.fil[0])#params)
            print("fb.fil[0]['dm']", fb.fil[0]['dm']+"."+
                  fb.fil[0]['rt']+fb.fil[0]['fo'])

        # Now construct the instance method from the response type (e.g.
        # 'LP'+'man' -> cheby1.LPman) and
        # design the filter by passing current specs to the method, yielding
        # e.g. cheby1.LPman(fb.fil[0])

        # Create / update global instance fb.fil_inst of selected filter class dm 
        # instantiated in InputFilter.set_design_method
        # call the method specified as a string in the argument of the
        # filter instance defined previously in InputFilter.set_response_type

        print("\n---- InputSpecs.startDesignFilt ----")
        print(type(fb.fil_inst))

        try:
    
            err = fb.fil_factory.call_fil_method(fb.fil[0]['rt'] + fb.fil[0]['fo'])
            # The called method writes coeffs, poles/zeros etc. back to
            # the global filter dict fb.fil[0]
            
            if err > 0:
                raise AttributeError("Unknown design method.")
                self.color_design_button("error")
    
            # Update filter order. weights and freq display in case they
            # have been changed by the design algorithm
            self.sel_fil.load_entries()
            self.w_specs.load_entries()
            self.f_specs.load_entries()
            self.color_design_button("ok")
    
            self.sigFilterDesigned.emit() # emit signal -> InputTabWidgets.update_all

        except Exception as e:
            print("\n---- InputSpecs.startDesignFilt ----")
            print(e)
            print(e.__doc__)
            self.color_design_button("error")


        if self.DEBUG:
            print("=== pyFDA.py : startDesignFilter: Results ===")
            print("zpk:", fb.fil[0]['zpk'])
            print('ndim coeffs:', np.ndim(fb.fil[0]['ba']))
            print("b,a = ", fb.fil[0]['ba'])
            print("N = ", fb.fil[0]['N'])
            print("F_PB, F_SB = ", fb.fil[0]['F_PB'], fb.fil[0]['F_SB'])


#------------------------------------------------------------------------------
    def color_design_button(self, state):
        """
        Color the >> DESIGN FILTER << button according to the filter design state:
        
        "ok":  green, filter has been designed, everything ok

        "changed": yellow, filter specs have been changed

        "error" : red, an error has occurred during filter design

        "failed" : orange, filter fails to meet target specs

        The actual colors are defined in pyfda_rc.py
        """
        self.butDesignFilt.setProperty("state", str(state))
        fb.design_filt_state = state
        self.butDesignFilt.style().unpolish(self.butDesignFilt)
        self.butDesignFilt.style().polish(self.butDesignFilt)
        self.butDesignFilt.update()

#------------------------------------------------------------------------------
    def HLine(self):
        # http://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
        # solution
        """
        Create a horizontal line
        """
        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        return line
#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = InputSpecs()
    form.show()
    form.store_all_specs()

    app.exec_()







