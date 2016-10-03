# -*- coding: utf-8 -*-
"""
input_filter.py
---------------
Subwidget for selecting the filter, consisting of combo boxes for:
- Response Type (LP, HP, Hilbert, ...)
- Filter Type (IIR, FIR, CIC ...)
- Design Method (Butterworth, ...)

@author: Julia Beike, Christian Münker, Michael Winkler
Datum: 4.12.2014
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import pyfda.filterbroker as fb
import pyfda.filter_factory as ff
import pyfda.pyfda_rc as rc
from pyfda.pyfda_lib import HLine


class SelectFilter(QtGui.QWidget):
    """
    Construct and read combo boxes for selecting the filter, consisting of the 
    following hierarchy:
      1. Response Type rt (LP, HP, Hilbert, ...)
      2. Filter Type ft (IIR, FIR, CIC ...)
      3. Filter Class (Butterworth, ...)
      
      Every time a combo box is changed manually, the filter tree for the selected
      response resp. filter type is read and the combo box(es) further down in
      the hierarchy are populated according to the available combinations.
      
      The signal sigFiltChanged is triggered and propagated to input_specs.py 
      where it triggers the recreation of all subwidgets.
    """

    sigFiltChanged = pyqtSignal()

    def __init__(self, parent):
        super(SelectFilter, self).__init__(parent)

        self.fc_last = '' # previous filter class

        self._construct_UI()

        self._set_response_type() # first time initialization

    def _construct_UI(self):
        """
        Construct UI with comboboxes for selecting filter:
        
        - cmbResponseType for selecting response type rt (LP, HP, ...)
        
        - cmbFilterType for selection of filter type (IIR, FIR, ...)
        
        - cmbFilterClass for selection of design design class (Chebychev, ...)
        
        and populate them from the "filterTree" dict during the initial run.
        Later, calling _set_response_type() updates the three combo boxes.
        
        See filterbroker.py for structure and content of "filterTree" dict        

        """

        bfont = QtGui.QFont()
        ifont = QtGui.QFont()
        bfont.setBold(True)
        bfont.setWeight(75)
        ifont.setItalic(True)

        #----------------------------------------------------------------------
        # Combo boxes for filter selection
        #----------------------------------------------------------------------
        self.cmbResponseType = QtGui.QComboBox(self)
        self.cmbResponseType.setObjectName("comboResponseType")
        self.cmbResponseType.setToolTip("Select filter response type.")
        self.cmbFilterType = QtGui.QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip("Select the kind of filter (recursive, transversal, ...).")
        self.cmbFilterClass = QtGui.QComboBox(self)
        self.cmbFilterClass.setObjectName("comboFilterClass")
        self.cmbFilterClass.setToolTip("Select the filter design class.")

        # Adapt comboboxes size dynamically to largest element
        self.cmbResponseType.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbFilterType.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbFilterClass.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        #----------------------------------------------------------------------
        # Populate combo box with initial settings from fb.fil_tree
        #----------------------------------------------------------------------
        # Translate short response type ("LP") to displayed names ("Lowpass")
        # (correspondence is defined in pyfda_rc.py) and populate rt combo box
        #
        # In Python 3, python objects are automatically converted to QVariant
        # when stored as "data" e.g. in a QComboBox and converted back when
        # retrieving. In Python 2, QVariant is returned when itemData is retrieved.
        # This is first converted from the QVariant container format to a
        # QString, next to a "normal" non-unicode string
        rt_list = sorted(list(fb.fil_tree.keys()))
        for rt in rt_list:
            self.cmbResponseType.addItem(rc.rt_names[rt], rt)
        idx = self.cmbResponseType.findData('LP') # find index for 'LP'

        if idx == -1: # Key 'LP' does not exist, use first entry instead
            idx = 0

        self.cmbResponseType.setCurrentIndex(idx) # set initial index
        rt = self.cmbResponseType.itemData(idx)
        if not isinstance(rt, str):
            rt = str(rt.toString()) # needed for Python 2.x

        for ft in fb.fil_tree[rt]:
            self.cmbFilterType.addItem(rc.ft_names[ft], ft)
        self.cmbFilterType.setCurrentIndex(0) # set initial index
        ft = self.cmbFilterType.itemData(0)
        if not isinstance(ft, str):
            ft = str(ft.toString()) # needed for Python 2.x
            
        for fc in fb.fil_tree[rt][ft]:
            self.cmbFilterClass.addItem(fb.fc_names[fc], fc)
        self.cmbFilterClass.setCurrentIndex(0) # set initial index

        #----------------------------------------------------------------------
        # Layout for Filter Type Subwidgets
        #----------------------------------------------------------------------
 
#        spacer = QtGui.QSpacerItem(1, 0, QtGui.QSizePolicy.Expanding,
#                                         QtGui.QSizePolicy.Fixed)

        layHFilWdg = QtGui.QHBoxLayout() # container for filter subwidgets
        layHFilWdg.addWidget(self.cmbResponseType)# QtCore.Qt.AlignLeft)
#        layHFilWdg.addItem(spacer)
        layHFilWdg.addWidget(self.cmbFilterType)
#        layHFilWdg.addItem(spacer)
        layHFilWdg.addWidget(self.cmbFilterClass)

        #----------------------------------------------------------------------
        # Layout for dynamic filter subwidgets (empty frame)
        #----------------------------------------------------------------------
        # see Summerfield p. 278
        self.layHDynWdg = QtGui.QHBoxLayout() # for additional dynamic subwidgets
        self.frmDynWdg = QtGui.QFrame() # collect subwidgets in frame (no border)
        self.frmDynWdg.setObjectName("wdg_frmDynWdg")
        self.frmDynWdg.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, 
                                     QtGui.QSizePolicy.Minimum)

        #Debugging: enable next line to show border of frmDnyWdg
        #self.frmDynWdg.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Raised)
        self.frmDynWdg.setLayout(self.layHDynWdg)

        #----------------------------------------------------------------------
        # Filter Order Subwidgets
        #----------------------------------------------------------------------
        self.lblOrder =  QtGui.QLabel("Order:")
        self.lblOrder.setFont(bfont)
        self.chkMinOrder = QtGui.QCheckBox("Minimum", self)
#        spacer1 = QtGui.QSpacerItem(20,0,
#                        QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.lblOrderN = QtGui.QLabel("N = ")
        self.lblOrderN.setFont(ifont)
        self.ledOrderN = QtGui.QLineEdit(str(fb.fil[0]['N']),self)

        #--------------------------------------------------
        #  Layout for filter order subwidgets
        layHOrdWdg = QtGui.QHBoxLayout()
        layHOrdWdg.addWidget(self.lblOrder)
        layHOrdWdg.addWidget(self.chkMinOrder)
#        layHOrdWdg.addItem(spacer1)
        layHOrdWdg.addWidget(self.lblOrderN)
        layHOrdWdg.addWidget(self.ledOrderN)

        #----------------------------------------------------------------------
        # OVERALL LAYOUT (stack standard + dynamic subwidgets vertically)
        #----------------------------------------------------------------------

        layVAllWdg = QtGui.QVBoxLayout()
        layVAllWdg.addLayout(layHFilWdg)
        layVAllWdg.addWidget(self.frmDynWdg)
        layVAllWdg.addWidget(HLine(QtGui, self))
        layVAllWdg.addLayout(layHOrdWdg)

#==============================================================================
#         frmMain = QtGui.QFrame()
#         frmMain.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
#         frmMain.setLayout(layVAllWdg)
# 
#         layHMain = QtGui.QHBoxLayout()
#         layHMain.addWidget(frmMain)
#         layHMain.setContentsMargins(0, 0, 0, 0)
# 
#         self.setLayout(layHMain)
# #        layHMain.setSizeConstraint(QtGui.QLayout.SetFixedSize)
# 
#==============================================================================
        self.setLayout(layVAllWdg)

        #------------------------------------------------------------
        # SIGNALS & SLOTS
        #------------------------------------------------------------
        # Connect comboBoxes and setters, propgate change events hierarchically
        #  through all widget methods and generate the signal sigFiltChanged
        #  in the end.
        self.cmbResponseType.currentIndexChanged.connect(
                lambda: self._set_response_type(enb_signal=True))# 'LP'
        self.cmbFilterType.currentIndexChanged.connect(
                lambda: self._set_filter_type(enb_signal=True))  #'IIR'
        self.cmbFilterClass.currentIndexChanged.connect(
                lambda: self._set_design_method(enb_signal=True))#'cheby1'
        self.chkMinOrder.clicked.connect(
                lambda: self._set_filter_order(enb_signal=True)) # Min. Order
        self.ledOrderN.editingFinished.connect(
                lambda:self._set_filter_order(enb_signal=True))  # Manual Order
        #------------------------------------------------------------


#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Reload comboboxes from filter dictionary to update changed settings
        after loading a filter design from disk.
        `load_entries` uses the automatism of _set_response_type etc. 
        of checking whether the previously selected filter design method is 
        also available for the new combination. 
        """
        rt_idx = self.cmbResponseType.findData(fb.fil[0]['rt']) # find index for response type
        self.cmbResponseType.setCurrentIndex(rt_idx)
        self._set_response_type()


#------------------------------------------------------------------------------
    def _read_cmb_box(self, cmb_box, tag):
        """
        Read out current setting of comboBox, convert to string (see 
        _construct_UI for details) and store in fb.fil[0][tag]
        
        Returns:
        
        The current setting of combobox as string
        """
        idx = cmb_box.currentIndex()
        cmb_data = cmb_box.itemData(idx)

        if not isinstance(cmb_data, str):
            cmb_data = str(cmb_data.toString()) # needed for Python 2
        fb.fil[0][tag] = cmb_data # copy selected rt setting to filter dict

        return cmb_data

#------------------------------------------------------------------------------
    def _set_response_type(self, enb_signal=False):
        """
        Triggered when cmbResponseType (LP, HP, ...) is changed:
        Copy selection to self.rt and fb.fil[0] and reconstruct filter type combo

        If previous filter type (FIR, IIR, ...) exists for new rt, set the
        filter type combo box to the old setting
        """
        # Read out current setting of comboBox and convert to string
        self.rt = self._read_cmb_box(self.cmbResponseType, 'rt')

        # Get list of available filter types for new rt
        ft_list = list(fb.fil_tree[self.rt].keys()) # explicit list() needed for Py3
        #---------------------------------------------------------------
        # Rebuild filter type combobox entries for new rt setting
        self.cmbFilterType.blockSignals(True) # don't fire when changed programmatically
        self.cmbFilterType.clear()
        for ft in fb.fil_tree[self.rt]:
            self.cmbFilterType.addItem(rc.ft_names[ft], ft)

        # Is current filter type (e.g. IIR) in list for new rt?
        if fb.fil[0]['ft'] in ft_list:
            ft_idx = self.cmbFilterType.findText(fb.fil[0]['ft'])
            self.cmbFilterType.setCurrentIndex(ft_idx) # yes, set same ft as before
        else:
            self.cmbFilterType.setCurrentIndex(0)     # no, set index 0
            
        self.cmbFilterType.blockSignals(False)
        #---------------------------------------------------------------

        self._set_filter_type(enb_signal)

#------------------------------------------------------------------------------
    def _set_filter_type(self, enb_signal=False):
        """"
        Triggered when cmbFilterType (IIR, FIR, ...) is changed:
        - read filter type ft and copy it to fb.fil[0]['ft'] and self.ft
        - (re)construct design method combo, adding
          displayed text (e.g. "Chebychev 1") and hidden data (e.g. "cheby1")
        """
        # Read out current setting of comboBox and convert to string
        self.ft = self._read_cmb_box(self.cmbFilterType, 'ft')
#
        logger.debug("InputFilter.set_filter_type triggered: {0}".format(self.ft))

        #---------------------------------------------------------------
        # Get all available design methods for new ft from fil_tree and
        # - Collect them in fc_list
        # - Rebuild design method combobox entries for new ft setting:
        #    The combobox is populated with the "long name",
        #    the internal name is stored in comboBox.itemData
        self.cmbFilterClass.blockSignals(True)
        self.cmbFilterClass.clear()
        fc_list = []

        for fc in sorted(fb.fil_tree[self.rt][self.ft]):
            self.cmbFilterClass.addItem(fb.fc_names[fc], fc)
            fc_list.append(fc)

        logger.debug("fc_list: {0}\n{1}".format(fc_list, fb.fil[0]['fc']))

        # Does new ft also provide the previous design method (e.g. ellip)?
        # Has filter been instantiated?
        if fb.fil[0]['fc'] in fc_list and ff.fil_inst:
            # yes, set same fc as before
            fc_idx = self.cmbFilterClass.findText(fb.fc_names[fb.fil[0]['fc']])
            logger.debug("fc_idx : %s", fc_idx)
            self.cmbFilterClass.setCurrentIndex(fc_idx)
        else:
            self.cmbFilterClass.setCurrentIndex(0)     # no, set index 0

        self.cmbFilterClass.blockSignals(False)

        self._set_design_method(enb_signal)


#------------------------------------------------------------------------------
    def _set_design_method(self, enb_signal=False):
        """
        Triggered when cmbFilterClass (cheby1, ...) is changed:
        - read design method fc and copy it to fb.fil[0]
        - create / update global filter instance fb.fil_inst of fc class
        - update dynamic widgets (if fc has changed and if there are any)
        - call load filter order
        """        
        fc = self._read_cmb_box(self.cmbFilterClass, 'fc')
        
        if fc != self.fc_last: # fc has changed:

            # when old filter instance has a dyn. subwidget, try to destroy it
            if hasattr(ff.fil_inst, 'wdg') and self.fc_last:      
                self._destruct_dyn_widgets() 

            #==================================================================
            """
            Create new instance of the selected filter class, accessible via
            its handle fb.fil_inst
            """
            err = ff.fil_factory.create_fil_inst(fc)
            logger.debug("InputFilter.set_design_method triggered: %s\n"
                        "Returned error code %d" %(fc, err))
            #==================================================================

    
            # Check whether new design method also provides the old filter order
            # method. If yes, don't change it, else set first available
            # filter order method
            if fb.fil[0]['fo'] not in fb.fil_tree[self.rt][self.ft][fc].keys():
                fb.fil[0].update({'fo':{}})
                # explicit list(dict.keys()) needed for Python 3
                fb.fil[0]['fo'] = list(fb.fil_tree[self.rt][self.ft][fc].keys())[0]
    
            logger.debug("selFilter = %s"
                   "filterTree[fc] = %s"
                   "filterTree[fc].keys() = %s"
                  %(fb.fil[0], fb.fil_tree[self.rt][self.ft][fc],\
                    fb.fil_tree[self.rt][self.ft][fc].keys()
                    ))

            if hasattr(ff.fil_inst, 'wdg'): # construct dyn. subwidgets if available
                self._construct_dyn_widgets()
            else:
                self.frmDynWdg.setVisible(False) # no subwidget, hide empty frame

            self.fc_last = fb.fil[0]['fc']

        self.load_filter_order(enb_signal)
        
#------------------------------------------------------------------------------
    def load_filter_order(self, enb_signal=False):
        """
        Called by set_design_method or from InputSpecs (with enb_signal = False),
          load filter order setting from fb.fil[0] and update widgets

        """                
        # read list of available filter order [fo] methods for  
        # current design method [fc] from fil_tree:
        foList = fb.fil_tree[fb.fil[0]['rt']]\
            [fb.fil[0]['ft']][fb.fil[0]['fc']].keys()

        # is currently selected fo setting available for (new) fc ?
        if fb.fil[0]['fo'] in foList:
            self.fo = fb.fil[0]['fo'] # keep current setting
        else:
            self.fo = foList[0] # use first list entry from filterTree
            fb.fil[0]['fo'] = self.fo # and update fo method

        # Determine which subwidgets are __visible__
        self.lblOrderN.setVisible('man' in foList)
        self.ledOrderN.setVisible('man' in foList)
        self.chkMinOrder.setVisible('min' in foList)

        # Determine which subwidgets are __enabled__
        self.chkMinOrder.setChecked(fb.fil[0]['fo'] == 'min')
        self.ledOrderN.setText(str(fb.fil[0]['N']))
        self.ledOrderN.setEnabled(not self.chkMinOrder.isChecked())
        self.lblOrderN.setEnabled(not self.chkMinOrder.isChecked())
        
        if enb_signal:
            self.sigFiltChanged.emit() # -> input_specs

#------------------------------------------------------------------------------    
    def _set_filter_order(self, enb_signal=False):
        """
        Triggered when either ledOrderN or chkMinOrder are edited:
        - copy settings to fb.fil[0]
        - emit sigFiltChanged if enb_signal is True
        """
        # Determine which subwidgets are _enabled_
        if self.chkMinOrder.isVisible():
            self.ledOrderN.setEnabled(not self.chkMinOrder.isChecked())
            self.lblOrderN.setEnabled(not self.chkMinOrder.isChecked())
            
            if self.chkMinOrder.isChecked() == True:
                # update in case N has been changed outside this class
                self.ledOrderN.setText(str(fb.fil[0]['N']))
                fb.fil[0].update({'fo' : 'min'})
                
            else:
                fb.fil[0].update({'fo' : 'man'})
                
        else:
            self.lblOrderN.setEnabled(self.fo == 'man')
            self.ledOrderN.setEnabled(self.fo == 'man')

        # read manual filter order, convert to positive integer and store it 
        # in filter dictionary.
        ordn = int(abs(float(self.ledOrderN.text())))
        self.ledOrderN.setText(str(ordn))
        fb.fil[0].update({'N' : ordn})

        if enb_signal:
            self.sigFiltChanged.emit() # -> input_specs
            
#------------------------------------------------------------------------------
    def _destruct_dyn_widgets(self):
        """
        Delete the dynamically created filter design subwidget (if there is one)
        
        see http://stackoverflow.com/questions/13827798/proper-way-to-cleanup-widgets-in-pyqt

        This does NOT work when the subwidgets to be deleted and created are
        identical, as the deletion is only performed when the current scope has
        been left (?)! Hence, it is necessary to skip this method when the new
        design method is the same as the old one.
        """
  
        try:
            ff.fil_inst.sigFiltChanged.disconnect() # disconnect signal
        except TypeError as e:
            print("Could not disconnect signal!\n", e)
            
        try:
            ff.fil_inst.destruct_UI() # local operations like disconnecting signals
            self.layHDynWdg.removeWidget(self.dyn_wdg_fil) # remove widget from layout
            self.dyn_wdg_fil.deleteLater() # delete UI widget when scope has been left

        except AttributeError as e:
            print("Could not destruct_UI!\n", e)
            
        ff.fil_inst.deleteLater() # delete QWidget when scope has been left
            

#------------------------------------------------------------------------------
    def _construct_dyn_widgets(self):
        """
        Create filter widget UI dynamically (if the filter routine has one) and 
        connect its sigFiltChanged signal to the signal with the same name 
        in this scope.
        """

        ff.fil_inst.construct_UI()            

        try:
            if ff.fil_inst.wdg:
                self.dyn_wdg_fil = getattr(ff.fil_inst, 'wdg_fil')
                self.layHDynWdg.addWidget(self.dyn_wdg_fil, stretch=1)
                self.layHDynWdg.setContentsMargins(0, 0, 0, 0)
                self.frmDynWdg.setVisible(self.dyn_wdg_fil != None)

                ff.fil_inst.sigFiltChanged.connect(self.sigFiltChanged)

        except AttributeError as e:
            print("input_filter._construct_dyn_widgets:", e)

#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainw = SelectFilter(None)

    app.setActiveWindow(mainw) 
    mainw.show()


    sys.exit(app.exec_())

