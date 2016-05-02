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
import pyfda.pyfda_rc as rc

# TODO: make more attributes local: self.my_attribute -> attribute

class InputFilter(QtGui.QWidget):
    """
    Construct and read combo boxes for selecting the filter, consisting of the 
    following hierarchy:
      1. Response Type rt (LP, HP, Hilbert, ...)
      2. Filter Type ft (IIR, FIR, CIC ...)
      3. Design Method dm (Butterworth, ...)
      
      Every time a combo box is changed manually, the filter tree for the selected
      response resp. filter type is read and the combo box(es) further down in
      the hierarchy are populated according to the available combinations.
      
      The signal sigFiltChanged is triggered and propagated to input_specs.py 
      where it triggers the recreation of all subwidgets.
    """

    sigFiltChanged = pyqtSignal()

    def __init__(self, parent):
        super(InputFilter, self).__init__(parent)

        self.dm_last = '' # design method from last call

        self._init_UI()

        self.set_response_type() # first time initialization

    def _init_UI(self):
        """
        Initialize UI with comboboxes for selecting filter
        """
#-----------------------------------------------------------------------------
#        see filterbroker.py for structure and content of "filterTree" dict
#-----------------------------------------------------------------------------

        #----------------------------------------------------------------------
        # Create combo boxes
        # - cmbResponseType for selecting response type rt (LP, HP, ...)
		# - cmbFilterType for selection of filter type (IIR, FIR, ...)
		# - cmbDesignMethod for selection of design method (Chebychev, ...)
		# and populate them from the "filterTree" dict either directly or by
		# calling set_response_type() :

        bfont = QtGui.QFont()
        ifont = QtGui.QFont()
  #      font.setPointSize(11)
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
        self.cmbDesignMethod = QtGui.QComboBox(self)
        self.cmbDesignMethod.setObjectName("comboDesignMethod")
        self.cmbDesignMethod.setToolTip("Select the actual filter design method.")

        # Adapt comboboxes size dynamically to largest element
        self.cmbResponseType.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbFilterType.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbDesignMethod.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

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
            
        for dm in fb.fil_tree[rt][ft]:
            self.cmbDesignMethod.addItem(fb.dm_names[dm], dm)
        self.cmbDesignMethod.setCurrentIndex(0) # set initial index

        #----------------------------------------------------------------------
        # LAYOUT
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

        layHFilWdg = QtGui.QHBoxLayout() # container for standard subwidgets
        spacer = QtGui.QSpacerItem(1, 0, QtGui.QSizePolicy.Expanding,
                                         QtGui.QSizePolicy.Fixed)
        layHFilWdg.addWidget(self.cmbResponseType)# QtCore.Qt.AlignLeft)
        layHFilWdg.addItem(spacer)
        layHFilWdg.addWidget(self.cmbFilterType)
        layHFilWdg.addItem(spacer)
        layHFilWdg.addWidget(self.cmbDesignMethod)

        #----------------------------------------------------------------------
        # Filter Order
        #----------------------------------------------------------------------
        self.lblOrder =  QtGui.QLabel("Order:")
        self.lblOrder.setFont(bfont)
        self.chkMinOrder = QtGui.QRadioButton("Minimum",self)
        self.spacer = QtGui.QSpacerItem(20,0,
                        QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Minimum)
        self.lblOrderN = QtGui.QLabel("N = ")
        self.lblOrderN.setFont(ifont)
        self.ledOrderN = QtGui.QLineEdit(str(fb.fil[0]['N']),self)

        #  All subwidgets, including dynamically created ones
        self.layHOrdWdg = QtGui.QHBoxLayout()
        self.layHOrdWdg.addWidget(self.lblOrder)
        self.layHOrdWdg.addWidget(self.chkMinOrder)
        self.layHOrdWdg.addItem(self.spacer)
        self.layHOrdWdg.addWidget(self.lblOrderN)
        self.layHOrdWdg.addWidget(self.ledOrderN)

        # stack standard + dynamic subwidgets vertically:
        layVAllWdg = QtGui.QVBoxLayout()

        layVAllWdg.addLayout(layHFilWdg)
        layVAllWdg.addWidget(self.frmDynWdg)
        layVAllWdg.addWidget(self.HLine())
        layVAllWdg.addLayout(self.layHOrdWdg)


        self.frmMain = QtGui.QFrame()
        self.frmMain.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        self.frmMain.setLayout(layVAllWdg)

        layHMain = QtGui.QHBoxLayout()
        layHMain.addWidget(self.frmMain)
        layHMain.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layHMain)
#        layHMain.setSizeConstraint(QtGui.QLayout.SetFixedSize)

        #------------------------------------------------------------
        # SIGNALS & SLOTS
        #------------------------------------------------------------
        # Connect comboBoxes and setters, propgate change events hierarchically
        #  through all widget methods and generate the signal sigFiltChanged
        #  in the end.
        self.cmbResponseType.currentIndexChanged.connect(
                lambda: self.set_response_type(enb_signal=True)) # 'LP'
        self.cmbFilterType.currentIndexChanged.connect(
                lambda: self.set_filter_type(enb_signal=True)) #'IIR'
        self.cmbDesignMethod.currentIndexChanged.connect(
                lambda: self.set_design_method(enb_signal=True)) #'cheby1'
        self.chkMinOrder.clicked.connect(
                lambda: self.set_filter_order(enb_signal=True))
        self.ledOrderN.editingFinished.connect(
                lambda:self.set_filter_order(enb_signal=True))
        #------------------------------------------------------------


#------------------------------------------------------------------------------
    def load_entries(self):
        """
        Reload comboboxes from filter dictionary to update changed settings
        after loading a filter design from disk.
        `load_entries` is based on the automatism of set_response_type etc. 
        of checking whether the previously selected filter design method is 
        also available for the new combination. 
        """
        rt_idx = self.cmbResponseType.findData(fb.fil[0]['rt']) # find index for 'LP'
        self.cmbResponseType.setCurrentIndex(rt_idx)
        self.set_response_type()


#------------------------------------------------------------------------------
    def set_response_type(self, enb_signal=False):
        """
        Triggered when cmbResponseType (LP, HP, ...) is changed:
        Copy selection to self.rt and fb.fil[0] and reconstruct filter type combo

        If previous filter type (FIR, IIR, ...) exists for new rt, set the
        filter type combo box to the old setting
        """
#        sender_name = ""
#        if self.sender(): # origin of signal that triggered the slot
#            sender_name = self.sender().objectName()
#            logging.debug(senderName + " was triggered\n================\n"
#               "InputFilter.set_response_type triggered by %s " %sender_name)
        # Read out current setting of comboBox and convert to string (see init_UI)
        rt_idx = self.cmbResponseType.currentIndex()
        self.rt = self.cmbResponseType.itemData(rt_idx)

        if not isinstance(self.rt, str):
            self.rt = str(self.rt.toString()) # needed for Python 2
        fb.fil[0]['rt'] = self.rt # copy selected rt setting to filter dict

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

        self.set_filter_type(enb_signal)

#------------------------------------------------------------------------------
    def set_filter_type(self, enb_signal=False):
        """"
        Triggered when cmbFilterType (IIR, FIR, ...) is changed:
        - read filter type ft and copy it to fb.fil[0]['ft'] and self.ft
        - (re)construct design method combo, adding
          displayed text (e.g. "Chebychev 1") and hidden data (e.g. "cheby1")
        """
        # Read out current setting of comboBox and convert to string (see init_UI)
        ft_idx = self.cmbFilterType.currentIndex()
        self.ft = self.cmbFilterType.itemData(ft_idx)
        
        if not isinstance(self.ft, str):
            self.ft = str(self.ft.toString()) # needed for Python 2.x
        fb.fil[0]['ft'] = self.ft # copy selected ft setting to filter dict

        logger.debug("InputFilter.set_filter_type triggered: {0}".format(self.ft))

        #---------------------------------------------------------------
        # Get all available design methods for new ft from fil_tree and
        # - Collect them in list dm_list
        # - Rebuild design method combobox entries for new ft setting:
        #    The combobox is populated with the "long name",
        #    the internal name is stored in comboBox.itemData
        self.cmbDesignMethod.blockSignals(True)
        self.cmbDesignMethod.clear()
        dm_list = []

        for dm in sorted(fb.fil_tree[self.rt][self.ft]):
            self.cmbDesignMethod.addItem(fb.dm_names[dm], dm)
            dm_list.append(dm)

        logger.debug("dm_list: {0}\n{1}".format(dm_list, fb.fil[0]['dm']))

        # Does new ft also provide the previous design method (e.g. ellip)?
        # Has filter been instantiated?
        if fb.fil[0]['dm'] in dm_list and fb.fil_inst:
            # yes, set same dm as before
            dm_idx = self.cmbDesignMethod.findText(fb.dm_names[fb.fil[0]['dm']])
            logger.debug("dm_idx : %s", dm_idx)
            self.cmbDesignMethod.setCurrentIndex(dm_idx)
        else:
            self.cmbDesignMethod.setCurrentIndex(0)     # no, set index 0

        self.cmbDesignMethod.blockSignals(False)

        self.set_design_method(enb_signal)


#------------------------------------------------------------------------------
    def set_design_method(self, enb_signal=False):
        """
        Triggered when cmbDesignMethod (cheby1, ...) is changed:
        - read design method dm and copy it to fb.fil[0]
        - create / update global filter instance fb.fil_inst of dm class
        - update dynamic widgets (if dm has changed and if there are any)
        - call load filter order
        """
        dm_idx = self.cmbDesignMethod.currentIndex()
        dm = self.cmbDesignMethod.itemData(dm_idx)
        if not isinstance(dm, str):
            dm = str(dm.toString()) # needed for Python 2.x (see init_UI)
        fb.fil[0]['dm'] = dm
        if dm != self.dm_last: # dm has changed, create new instance
            #-----
            try:
                pass
#                fb.fil_inst.destruct_UI() # disconnect signals from dyn. widget
            except AttributeError:
                pass
                
            err = fb.fil_factory.create_fil_inst(dm)
            #-----
            logger.debug("InputFilter.set_design_method triggered: %s" %dm)
    
            # Check whether new design method also provides the old filter order
            # method. If yes, don't change it, else set first available
            # filter order method
            if fb.fil[0]['fo'] not in fb.fil_tree[self.rt][self.ft][dm].keys():
                fb.fil[0].update({'fo':{}})
                # explicit list(dict.keys()) needed for Python 3
                fb.fil[0]['fo'] = list(fb.fil_tree[self.rt][self.ft][dm].keys())[0]
    
            logger.debug("selFilter = %s"
                   "filterTree[dm] = %s"
                   "filterTree[dm].keys() = %s"
                  %(fb.fil[0], fb.fil_tree[self.rt][self.ft][dm],\
                    fb.fil_tree[self.rt][self.ft][dm].keys()
                    ))
    
            self._update_dyn_widgets() # check for new subwidgets and update if needed

        self.load_filter_order(enb_signal)
        
#------------------------------------------------------------------------------
    def load_filter_order(self, enb_signal=False):
        """
        Called by set_design_method or from InputSpecs (with enb_signal = False),
          load filter order setting from fb.fil[0] and update widgets

        """                
        # read list of available filter order [fo] methods for  
        # current design method [dm] from fil_tree:
        foList = fb.fil_tree[fb.fil[0]['rt']]\
            [fb.fil[0]['ft']][fb.fil[0]['dm']].keys()

        # is currently selected fo setting available for (new) dm ?
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
    def set_filter_order(self, enb_signal=False):
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
    def _update_dyn_widgets(self):
        """
        Delete dynamically (i.e. within filter design routine) created subwidgets
        and create new ones, depending on requirements of filter design algorithm


        This does NOT work when the subwidgets to be deleted and created are
        identical, as the deletion is only performed when the current scope has
        been left (?)! Hence, it is necessary to skip this method when the new
        design method is the same as the old one.
        """
# TODO: see https://www.commandprompt.com/community/pyqt/x3410.htm


        # Find "old" dyn. subwidgets and delete them:
        widgetList = self.frmDynWdg.findChildren(
            (QtGui.QComboBox, QtGui.QLineEdit, QtGui.QLabel, QtGui.QWidget))
#       widgetListNames = [w.objectName() for w in widgetList]

        for w in widgetList:
            self.layHDynWdg.removeWidget(w)   # remove widget from layout
            w.deleteLater()             # tell Qt to delete object when the
                                        # method has completed
#                del w                       # not really needed?

        # Try to create "new" dyn. subwidgets:
        if hasattr(fb.fil_inst, 'wdg'):
            try:
                if 'sf' in fb.fil_inst.wdg:
                    a = getattr(fb.fil_inst, fb.fil_inst.wdg['sf'])
                    self.layHDynWdg.addWidget(a, stretch=1)
                    self.layHDynWdg.setContentsMargins(0, 0, 0, 0)
                    self.frmDynWdg.setVisible(a != None)

            except AttributeError as e:
                print("sf.updateWidgets:", e)
                self.frmDynWdg.setVisible(False)
        else:
            self.frmDynWdg.setVisible(False)

        self.dm_last = fb.fil[0]['dm']

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

#    def closeEvent(self, event):
#        exit()
#------------------------------------------------------------------------------

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainw = InputFilter(None)

    app.setActiveWindow(mainw) 
    mainw.show()


    sys.exit(app.exec_())

