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

# import pyfda.filterbroker from one level above if this file is run as __main__
# for test purposes
#if __name__ == "__main__":
#    __cwd__ = os.path.dirname(os.path.abspath(__file__))
#    sys.path.append(os.path.dirname(__cwd__))

import pyfda.filterbroker as fb

from pyfda.input_widgets import (input_filter, input_order, input_amp_specs,
                                 input_freq_specs, input_freq_units,
                                 input_weight_specs, input_target_specs)


class InputSpecs(QtGui.QWidget):
    """
    Build widget for entering all filter specs
    """
    # class variables (shared between instances if more than one exists)
    sigFilterDesigned = pyqtSignal()  # emitted when filter has been designed
    sigSpecsChanged = pyqtSignal() # emitted when specs have been changed


    def __init__(self, DEBUG=True):
        super(InputSpecs, self).__init__()

        self.DEBUG = DEBUG
#        self.ftb = FilterTreeBuilder('init.txt', 'filter_design',
#                                    comment_char = '#', DEBUG = DEBUG) #
        self.initUI()

    def initUI(self):
        """
        Create all subwidgets
        """
        # Select filter with response type rt (LP, ...), filter type ft
        # (IIR, ...) and design method dm (cheby1, ...)
        self.sel_fil = input_filter.InputFilter(DEBUG=False)
        # subwidget for selecting filter order ['man' (numeric) or 'min']
        self.fil_ord = input_order.InputOrder(DEBUG=False)
        # subwidget for selecting the frequency unit and range
        self.f_units = input_freq_units.InputFreqUnits(DEBUG=False)
        self.f_units.setObjectName("freq_units")
        # subwidget for Frequency Specs
        self.f_specs = input_freq_specs.InputFreqSpecs(DEBUG=False)
        self.f_specs.setObjectName("freq_specs")
        # subwidget for Amplitude Specs
        self.a_specs = input_amp_specs.InputAmpSpecs(DEBUG=False)
        self.a_specs.setObjectName("amp_specs")
        # subwidget for Weight Specs
        self.w_specs = input_weight_specs.InputWeightSpecs(DEBUG=False)
        self.w_specs.setObjectName("weight_specs")
        # subwidget for target specs (frequency and amplitude)
        self.t_specs = input_target_specs.InputTargetSpecs(DEBUG=False,
                                            title="Target Specifications")
        self.t_specs.setObjectName("target_specs")
        # subwidget for displaying infos on the design method
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
        self.color_design_button("changed")
        self.butQuit = QtGui.QPushButton("Quit", self)

        #----------------------------------------------------------------------
        # LAYOUT for input specifications and buttons
        #----------------------------------------------------------------------
        spcV = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Minimum,
                                       QtGui.QSizePolicy.Expanding)
        layGMain = QtGui.QGridLayout()
        layGMain.addWidget(self.sel_fil, 0, 0, 1, 2)  # Design method (IIR - ellip, ...)
        layGMain.addWidget(self.fil_ord, 1, 0, 1, 2)  # Filter order
        layGMain.addWidget(self.f_units, 2, 0, 1, 2)  # Frequency units
        layGMain.addWidget(self.f_specs, 3, 0, 1, 2)  # Freq. specifications
        layGMain.addWidget(self.a_specs, 4, 0, 1, 2)  # Amplitude specs
        layGMain.addWidget(self.w_specs, 5, 0, 1, 2)  # Weight specs
        layGMain.addWidget(frmMsg, 6, 0, 1, 2)        # Text message
        layGMain.addWidget(self.t_specs, 7, 0, 1, 2)  # Target specs
        layGMain.addWidget(self.butDesignFilt, 8, 0)#, 1, 2)
        layGMain.addWidget(self.butQuit, 8, 1)#, 1, 2)
#        layGMain.addWidget(self.butReadFiltTree, 8,1)
        layGMain.addItem(spcV, 9, 0, 1, 2)
#        layGMain.addWidget(self.HLine(), 9,0,1,2) # create HLine
        layGMain.setContentsMargins(0, 0, 0, 0)


        self.setLayout(layGMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTS
        # Call updateUI every time filter (order) method is changed
        # updateUI emits sigFilterChanged when it's finished
        #
        # Changes requiring update of UI because number or kind of
        # input fields has changed:
        self.fil_ord.sigSpecsChanged.connect(self.updateAllUIs)
        self.sel_fil.sigSpecsChanged.connect(self.updateAllUIs)

        # Changes requiring recalculation of frequency specs
        self.f_units.sigSpecsChanged.connect(self.f_specs.loadEntries)
        self.f_units.sigSpecsChanged.connect(self.t_specs.loadEntries)

        # Connect sigSpecsChanged signal to next hierarchy level to propagate
        # changes requiring reload of parameters e.g. to the plot tabs
        self.f_units.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.f_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.t_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.a_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)
        self.w_specs.sigSpecsChanged.connect(self.sigSpecsChanged.emit)

        # Other signal-slot connections
        self.butDesignFilt.clicked.connect(self.startDesignFilt)
        self.butQuit.clicked.connect(QtGui.qApp.quit)
        #----------------------------------------------------------------------

        self.updateAllUIs() # first time initialization


#------------------------------------------------------------------------------
    def updateAllUIs(self):
        """
        This method is called every time filter design method or order
        (min / man) is changed. At this time, the actual filter object
        instance has been created from design method and order
        (e.g. 'cheby1', 'min') in input_filter.py. Its handle has been stored
        in fb.filobj.

        fb.fil[0] (currently selected filter) is read, then general information
        for the selected filter type and order (min/man) is gathered from
        the filter tree [fb.fil_tree], i.e. which parameters are needed, which
        widgets are visible and which message shall be displayed.

        Then, the UIs of all subwidgets are updated using their "updateUI" method,
        finally the signal 'sigSpecsChanged' is emitted.
        """

        # Read freq / amp / weight labels for current filter design
        rt = fb.fil[0]['rt']
        ft = fb.fil[0]['ft']
        dm = fb.fil[0]['dm']
        fo = fb.fil[0]['fo']
        all_params = fb.fil_tree[rt][ft][dm][fo]['par'] # all parameters e.g. 'F_SB'
        min_params = man_params = []
        if "min" in fb.fil_tree[rt][ft][dm]:
            min_params = fb.fil_tree[rt][ft][dm]['min']['par']
        if "man" in fb.fil_tree[rt][ft][dm]:
            man_params = fb.fil_tree[rt][ft][dm]['man']['par']

        vis_wdgs = fb.fil_tree[rt][ft][dm][fo]['vis'] # visible widgets
        dis_wdgs = fb.fil_tree[rt][ft][dm][fo]['dis'] # disabled widgets
        msg      = fb.fil_tree[rt][ft][dm][fo]['msg'] # message

        # build separate parameter lists according to the first letter
        self.f_params = [l for l in all_params if l[0] == 'F']
        self.f_min_params = [l for l in min_params if l[0] == 'F']
        self.f_man_params = [l for l in man_params if l[0] == 'F']

        self.a_params = [l for l in all_params if l[0] == 'A']
        self.weightParams = [l for l in all_params if l[0] == 'W']
        if self.DEBUG:
            print("=== InputParams.chooseDesignMethod ===")
            print("selFilter:", fb.fil[0])
            print('myLabels:', all_params)
            print('ampLabels:', self.a_params)
            print('freqLabels:', self.f_params)
            print('weightLabels:', self.weightParams)

        # pass new labels to widgets and recreate UI
        # set widgets invisible if param list is empty
        self.fil_ord.loadEntries()

        # always use parameters for manual filter order here,
        # frequency specs for minimum order are displayed in target specs
        self.f_specs.setVisible("fspecs" in vis_wdgs)
        self.f_specs.setEnabled("fspecs" not in dis_wdgs)
        self.f_specs.updateUI(newLabels=self.f_man_params)

#        self.a_specs.setVisible(self.a_params != [])
        self.a_specs.setVisible("aspecs" in vis_wdgs)
        self.a_specs.setEnabled("aspecs" not in dis_wdgs)
        self.a_specs.updateUI(newLabels=self.a_params)

        self.w_specs.setVisible("wspecs" in vis_wdgs)
        self.w_specs.setEnabled("wspecs" not in dis_wdgs)
        self.w_specs.updateUI(newLabels=self.weightParams)

        self.t_specs.setVisible("tspecs" in vis_wdgs)
        self.t_specs.setEnabled("tspecs" not in dis_wdgs)
        self.t_specs.updateUI(self.f_min_params, self.a_params)

        self.lblMsg.setText(msg)

        self.sigSpecsChanged.emit()


#------------------------------------------------------------------------------
    def storeAll(self):
        """
        Store all entries of current filter design in global dict fb.fil[0]
        parameters, using the "storeEntries" methods of the classes
        -- not used yet --
        """
        # collect data from widgets and write to fb.fil[0]
        # self.f_units.storeEntries() # frequency units widget - not working yet
        self.fil_ord.storeEntries() # filter order widget
        self.f_specs.storeEntries() # frequency specification widget
        self.f_units.storeEntries() # frequency specification widget
        self.a_specs.storeEntries() # magnitude specs with unit
        self.w_specs.storeEntries() # weight specification
        self.t_specs.storeEntries() # target specs

#------------------------------------------------------------------------------
    def loadAll(self):
        """
        Reload entries from global dict fb.fil[0]
        parameters, using the "loadEntries" methods of the classes
        """
        self.sel_fil.loadEntries() # select filter widget
        self.f_units.loadEntries() # frequency units widget
        self.fil_ord.loadEntries() # filter order widget
        self.f_specs.loadEntries() # frequency specification widget
        self.a_specs.loadEntries() # magnitude specs with unit
        self.w_specs.loadEntries() # weight specification
        self.t_specs.loadEntries() # target specs

        if self.DEBUG:
            print("=== input_specs.py : loadAll ===")
            print(fb.fil[0])


#------------------------------------------------------------------------------
    def startDesignFilt(self):
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

        try:
            getattr(fb.filObj, fb.fil[0]['rt'] + fb.fil[0]['fo'])(fb.fil[0])

            # The filter design routines write coeffs, poles/zeros etc. back to
            # the global filter dict

            # Update filter order. weights and freq display in case they
            # have been changed by the design algorithm
            self.fil_ord.loadEntries()
            self.w_specs.loadEntries()
            self.f_specs.loadEntries()

            self.sigFilterDesigned.emit() # emit signal -> input_widgets

        except Exception as e:
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
        Color the >> DESIGN FILTER << button:
        green:  filter has been designed, everything ok
        yellow: filter specs have been changed
        red:    an error has occurred during filter design
        orange: filter does not meet target specs
        """

  #      print("state", state)
        self.butDesignFilt.setProperty("state", str(state))
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
    form.storeAll()

    app.exec_()







