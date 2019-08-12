# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for simulating fixpoint filters and
generating VHDL and Verilog Code

see https://bitbucket.org/cfelton/examples
"""
import sys, os, io, importlib
import logging
logger = logging.getLogger(__name__)

from ..compat import (Qt, QWidget, QPushButton, QComboBox, QFD, QSplitter, QLabel,
                      QPixmap, QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, 
                      QEvent, QSizePolicy)

import numpy as np

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.pyfda_dirs as dirs
from pyfda.pyfda_lib import qstr, cmp_version, pprint_log
import pyfda.pyfda_fix_lib as fx
from pyfda.pyfda_io_lib import extract_file_ext
from pyfda.pyfda_qt_lib import qget_cmb_box, qset_cmb_box, qstyle_widget
from pyfda.fixpoint_widgets.fixpoint_helpers import UI_W, UI_Q
from pyfda.pyfda_rc import params

# when migen is present, instantiate the fixpoint widget
if cmp_version("migen", "0.1") >= -1: # currently, version cannot be determined
    import migen
    HAS_MIGEN = True
else:
    HAS_MIGEN = False

# when deltasigma module is present, add a corresponding entry to the combobox
try:
    import deltasigma
    HAS_DS = True
except ImportError:
    HAS_DS = False
#------------------------------------------------------------------------------

classes = {'Input_Fixpoint_Specs':'Fixpoint'} #: Dict containing class name : display name

class Input_Fixpoint_Specs(QWidget):
    """
    Create the widget that holds the dynamically loaded fixpoint filter ui 
    """
    # emit a signal when the image has been resized
    sig_resize = pyqtSignal()
    # incoming from subwidgets -> process_sig_rx_local
    sig_rx_local = pyqtSignal(object) 
    # incoming, connected to input_tab_widget.sig_rx
    sig_rx = pyqtSignal(object)
    # outcgoing
    sig_tx = pyqtSignal(object)

    def __init__(self, parent):
        super(Input_Fixpoint_Specs, self).__init__(parent)

        self.tab_label = 'Fixpoint'
        self.tool_tip = ("<span>Select a fixpoint implementation for the filter,"
                " simulate it or generate a Verilog netlist.</span>")
        self.parent = parent
        
        if HAS_MIGEN:
            self._construct_UI()
        else:
            self.state = "deactivated" # "invisible", "disabled"

#------------------------------------------------------------------------------
    def process_sig_rx_w_i(self, dict_sig=None):
        """
        Input fixpoint format has been changed. When I/O lock is active, copy
        input fixpoint word format to output word format.
        
        Flag with `propagate=True` before proceeding in `process_sig_rx` to allow
        for signal propagation.
        """
        if self.wdg_w_input.butLock.isChecked():
            fb.fil[0]['fxqc']['QO']['WI'] = fb.fil[0]['fxqc']['QI']['WI']
            fb.fil[0]['fxqc']['QO']['WF'] = fb.fil[0]['fxqc']['QI']['WF']
            fb.fil[0]['fxqc']['QO']['W'] = fb.fil[0]['fxqc']['QI']['W']

        self.process_sig_rx(dict_sig, propagate=True)

#------------------------------------------------------------------------------
    def process_sig_rx_w_o(self, dict_sig=None):
        """
        Output fixpoint format has been changed. When I/O lock is active, copy
        output fixpoint word format to input word format.
        
        Flag with `propagate=True` before proceeding in `process_sig_rx` to allow
        for signal propagation.
        """
        if self.wdg_w_input.butLock.isChecked():
            fb.fil[0]['fxqc']['QI']['WI'] = fb.fil[0]['fxqc']['QO']['WI']
            fb.fil[0]['fxqc']['QI']['WF'] = fb.fil[0]['fxqc']['QO']['WF']
            fb.fil[0]['fxqc']['QI']['W'] = fb.fil[0]['fxqc']['QO']['W']

        self.process_sig_rx(dict_sig, propagate=True)

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None, propagate=False):
        """
        Process signals coming in via subwidgets and sig_rx
		
		Play PingPong with a stimulus & plot widget:
        
		2. ``fx_sim_init()``: Request stimulus by sending 'fx_sim':'get_stimulus'
		
		3. ``fx_sim_set_stimulus()``: Receive stimulus from widget in 'fx_sim':'set_stimulus'
			and pass it to HDL object for simulation
		   
		4. Send back HDL response to widget via 'fx_sim':'set_response'

        """
		
        logger.info("SIG_RX - vis: {0} | prop: {1}\n{2}"\
                    .format(self.isVisible(), propagate, pprint_log(dict_sig)))
        if dict_sig['sender'] == __name__:
            logger.debug("Infinite loop detected")
            return
        elif 'filt_changed' in dict_sig:
            # update list of available filter topologies here
            self._update_filter_cmb()
        elif 'data_changed' in dict_sig or\
            ('view_changed' in dict_sig and dict_sig['view_changed'] == 'q_coeff'):
            # update fields in the filter topology widget - wordlength may have
            # been changed. Also set RUN button to "changed" in wdg_dict2ui() and 
            # enable propagate so that 
            self.wdg_dict2ui()
            #self.sig_tx.emit({'sender':__name__, 'fx_sim':'specs_changed'})
        elif 'fx_sim' in dict_sig:
            if dict_sig['fx_sim'] == 'init':
                if self.fx_wdg_found:
                    self.fx_sim_init()
                else:
                    logger.error("No fixpoint widget found!")
                    qstyle_widget(self.butSimHDL, "error")  
                    self.sig_tx.emit({'sender':__name__, 'fx_sim':'error'})
                    
            elif dict_sig['fx_sim'] == 'set_stimulus':
                self.fx_sim_set_stimulus(dict_sig)
            elif dict_sig['fx_sim'] == 'specs_changed':
                # fixpoint specification have been changed somewhere, update ui
                # and set run button to "changed" in wdg_dict2ui()
                self.wdg_dict2ui()
            elif dict_sig['fx_sim'] == 'finish':
                qstyle_widget(self.butSimHDL, "normal") 
            else:
                logger.error('Unknown "fx_sim" command option "{0}"\n'
                             '\treceived from "{1}".'.format(dict_sig['fx_sim'],dict_sig['sender']))
        # ---- Process local widget signals 
        elif 'ui' in dict_sig:
            if dict_sig['ui'] == 'butLock':
                if self.wdg_w_input.butLock.isChecked():
                    fb.fil[0]['fxqc']['QO']['WI'] = fb.fil[0]['fxqc']['QI']['WI']
                    fb.fil[0]['fxqc']['QO']['WF'] = fb.fil[0]['fxqc']['QI']['WF']
                    fb.fil[0]['fxqc']['QO']['W'] = fb.fil[0]['fxqc']['QI']['W']
                else:
                    return
            elif dict_sig['ui'] in {'WI', 'WF', 'ovfl', 'quant', 'cmbW'}:
                pass
            else:
                logger.warning("Unknown value '{0}' for key 'ui'".format(dict_sig['ui']))
            self.wdg_dict2ui()
            self.sig_tx.emit({'sender':__name__, 'fx_sim':'specs_changed'})

        if propagate:
            # signals of local subwidgets are propagated,
            # global signals terminate here.
            # The next event in the queue is only handled when control returns
            # from this one
            #dict_sig.update({'sender':__name__})
            self.sig_tx.emit(dict_sig)
            return

#------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the main GUI, consisting of:
            
        - A combo box to select the filter topology with an image of the filter topology
        
        - The input quantizer
        
        - The UI of the fixpoint filter widget
        
        - Simulation and export buttons
        """
        self.cmb_wdg_fixp = QComboBox(self)
        self.cmb_wdg_fixp.setSizeAdjustPolicy(QComboBox.AdjustToContents)
                
#------------------------------------------------------------------------------        
        # Define frame and layout for the dynamically updated filter widget
        # The actual filter widget is instantiated in self.set_fixp_widget() later on
       
        self.layHWdg = QHBoxLayout()
        #self.layHWdg.setContentsMargins(*params['wdg_margins'])
        frmHDL_wdg = QFrame(self)
        frmHDL_wdg.setLayout(self.layHWdg)
        #frmHDL_wdg.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

#------------------------------------------------------------------------------
        self.lblTitle = QLabel("not set", self)
        self.lblTitle.setWordWrap(True)
        self.lblTitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layHTitle = QHBoxLayout()
        layHTitle.addWidget(self.cmb_wdg_fixp)
        layHTitle.addWidget(self.lblTitle)

        self.frmTitle = QFrame(self)
        self.frmTitle.setLayout(layHTitle)
        self.frmTitle.setContentsMargins(*params['wdg_margins'])

#------------------------------------------------------------------------------
#       Input and Output Quantizer
#------------------------------------------------------------------------------
#       - instantiate widgets for input and output quantizer
#       - pass the quantization (sub-?) dictionary to the constructor     
#------------------------------------------------------------------------------

        self.wdg_w_input = UI_W(self, q_dict = fb.fil[0]['fxqc']['QI'],
                                label='<i>Input Format X<sub>I.F&nbsp;</sub></i>:',
                                lock_visible=True)
        self.wdg_w_input.sig_tx.connect(self.process_sig_rx_w_i)
        
        cmb_q = ['round','floor','fix']

        self.wdg_w_output = UI_W(self, q_dict = fb.fil[0]['fxqc']['QO'],
                                 label='Output Format <i>Y<sub>I.F&nbsp;</sub></i>:')
        self.wdg_w_output.sig_tx.connect(self.process_sig_rx_w_o)
        self.wdg_q_output = UI_Q(self, q_dict = fb.fil[0]['fxqc']['QO'],\
                                 cmb_q=cmb_q, cmb_ov=['wrap','sat'], visible=True)
        self.wdg_q_output.sig_tx.connect(self.sig_rx)

        if HAS_DS:
            cmb_q.append('dsm')
        self.wdg_q_input = UI_Q(self, q_dict = fb.fil[0]['fxqc']['QI'], cmb_q=cmb_q)
        self.wdg_q_input.sig_tx.connect(self.sig_rx)
        
        # Layout and frame for input quantization 
        layVQioWdg = QVBoxLayout()
        layVQioWdg.addWidget(self.wdg_w_input)
        layVQioWdg.addWidget(self.wdg_q_input)
        frmQioWdg = QFrame(self)
        #frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmQioWdg.setLayout(layVQioWdg)
        frmQioWdg.setContentsMargins(*params['wdg_margins'])
        
        # Layout and frame for output quantization
        layVQoWdg = QVBoxLayout()        
        layVQoWdg.addWidget(self.wdg_w_output)
        layVQoWdg.addWidget(self.wdg_q_output)        
        frmQoWdg = QFrame(self)
        #frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmQoWdg.setLayout(layVQoWdg)
        frmQoWdg.setContentsMargins(*params['wdg_margins'])        
  
#------------------------------------------------------------------------------        
#       Dynamically updated image of filter topology
#------------------------------------------------------------------------------        
        self.lbl_img_fixp = QLabel("a", self)
        #self.lbl_img_fixp.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.img_dir = os.path.dirname(os.path.realpath(__file__))  
        self.img_file = os.path.join(self.img_dir, 'hdl_dummy.png')
        self.img_fixp = QPixmap(self.img_file)

        layHImg = QHBoxLayout()
        layHImg.setContentsMargins(0,0,0,0)
        layHImg.addWidget(self.lbl_img_fixp)#, Qt.AlignCenter)
        self.frmImg = QFrame(self)
        self.frmImg.setLayout(layHImg)
        self.frmImg.setContentsMargins(*params['wdg_margins'])
        self.resize_img()
#------------------------------------------------------------------------------
#       Simulation and export Buttons        
#------------------------------------------------------------------------------        
        self.butExportHDL = QPushButton(self)
        self.butExportHDL.setToolTip("Export fixpoint filter in Verilog format.")
        self.butExportHDL.setText("Create HDL")

        self.butSimHDL = QPushButton(self)
        self.butSimHDL.setToolTip("Start migen fixpoint simulation.")
        self.butSimHDL.setText("Sim. HDL")
        
        self.butSimFxPy = QPushButton(self)
        self.butSimFxPy.setToolTip("Simulate filter with fixpoint effects.")
        self.butSimFxPy.setText("Sim. FixPy")

        self.layHHdlBtns = QHBoxLayout()
        self.layHHdlBtns.addWidget(self.butSimFxPy)
        self.layHHdlBtns.addWidget(self.butSimHDL)
        self.layHHdlBtns.addWidget(self.butExportHDL)
        # This frame encompasses the HDL buttons sim and convert
        frmHdlBtns = QFrame(self)
        #frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmHdlBtns.setLayout(self.layHHdlBtns)
        frmHdlBtns.setContentsMargins(*params['wdg_margins'])

# -------------------------------------------------------------------
#       Top level layout
# -------------------------------------------------------------------
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(frmHDL_wdg)
        splitter.addWidget(frmQoWdg)
        splitter.addWidget(self.frmImg)

        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([3000, 3000, 5000])

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmTitle)
        layVMain.addWidget(frmHdlBtns)        
        layVMain.addWidget(frmQioWdg)
        layVMain.addWidget(splitter)
        layVMain.addStretch()
        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs & EVENTFILTERS
        #----------------------------------------------------------------------
        # monitor events and generate sig_resize event when resized
        self.lbl_img_fixp.installEventFilter(self)
        # ... then redraw image when resized
        self.sig_resize.connect(self.resize_img)

        self.cmb_wdg_fixp.currentIndexChanged.connect(self._update_fixp_widget)

        self.butExportHDL.clicked.connect(self.exportHDL)
        self.butSimHDL.clicked.connect(self.fx_sim_init)
        #----------------------------------------------------------------------
        inst_wdg_list = self._update_filter_cmb()
        if len(inst_wdg_list) == 0:
            logger.warning("No fixpoint filters found!")
        else:
            logger.info("Imported {0:d} fixpoint filters:\n{1}"
                        .format(len(inst_wdg_list.split("\n"))-1, inst_wdg_list))

        self._update_fixp_widget()

#------------------------------------------------------------------------------
    def _update_filter_cmb(self):
        """
        (Re-)Read list of available fixpoint filters for a given filter design 
        every time a new filter design is selected. 
        
        Then try to import the fixpoint designs in the list and populate the 
        fixpoint implementation combo box `self.cmb_wdg_fixp` when successfull. 
        """
        inst_wdg_str = "" # full names of successfully instantiated widgets for logging
        last_fx_wdg = qget_cmb_box(self.cmb_wdg_fixp, data=False) # remember last fx widget setting
        self.cmb_wdg_fixp.clear()
        fc = fb.fil[0]['fc']
        if 'fix' in fb.filter_classes[fc]:
            for class_name in fb.filter_classes[fc]['fix']: # get class name
                try:
                    # construct module + class name
                    mod_class_name = fb.fixpoint_classes[class_name]['mod'] + '.' + class_name
                    disp_name = fb.fixpoint_classes[class_name]['name'] # # and display name
                    self.cmb_wdg_fixp.addItem(disp_name, mod_class_name)
                    inst_wdg_str += '\t' + class_name + ' : ' + mod_class_name + '\n'
                except AttributeError as e:
                    logger.warning('Widget "{0}":\n{1}'.format(class_name,e))
                    continue
                except Exception as e:
                    logger.warning(e)
                    continue

           # restore last fxp widget if possible
            idx = self.cmb_wdg_fixp.findText(last_fx_wdg)
            # set to idx 0 if not found (returned -1)
            self.cmb_wdg_fixp.setCurrentIndex(max(idx,0))
        return inst_wdg_str
        
#------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by monitored QLabel, only resize events are
        processed here, generating a `sig_resize` signal. All other events
        are passed on to the next hierarchy level.
        """
        if event.type() == QEvent.Resize:
            self.sig_resize.emit()

        # Call base class method to continue normal event processing:
        return super(Input_Fixpoint_Specs, self).eventFilter(source, event)
#------------------------------------------------------------------------------
    def resize_img(self):
        """ 
        Triggered when self (the widget) is resized, consequently the image
        inside QLabel is resized to completely fill the label while keeping 
        the aspect ratio.
        
        This doesn't really work at the moment.
        """

        if hasattr(self.parent, "width"): # needed for module test
            par_w, par_h = self.parent.width(), self.parent.height()
        else:
            par_w, par_h = 300, 700
        lbl_w, lbl_h = self.lbl_img_fixp.width(), self.lbl_img_fixp.height()
        img_w, img_h = self.img_fixp.width(), self.img_fixp.height()

        if img_w > 10:        
            max_h = int(max(np.floor(img_h * par_w/img_w) - 15, 20))
        else:
            max_h = 200
        logger.debug("img size: {0},{1}, frm size: {2},{3}, max_h: {4}".format(img_w, img_h, par_w, par_h, max_h))        
        #return
        #img_scaled = self.img_fixp.scaled(self.lbl_img_fixp.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        #img_scaled = self.img_fixp.scaledToHeight(max_h, Qt.SmoothTransformation)
        img_scaled = self.img_fixp.scaledToHeight(max_h, Qt.SmoothTransformation)

        self.lbl_img_fixp.setPixmap(QPixmap(img_scaled))

#------------------------------------------------------------------------------
    def _update_fixp_widget(self):
        """
        This method is called at the initialization of the widget and when
        a new fixpoint filter implementation is selected from the combo box:

        - Destruct old instance of fixpoint filter widget `self.fx_wdg_inst`

        - Import and instantiate new fixpoint filter widget e.g. after changing the 
          filter topology as 

        - Try to load image for filter topology

        - Update the UI of the widget

        - Try to instantiate HDL filter as `self.fx_wdg_inst.fixp_filter` with 
            dummy data
        """

        def _disable_fx_wdg(self):

            if hasattr(self, "fx_wdg_inst") and self.fx_wdg_inst is not None: # is a fixpoint widget loaded?
                try:
                    self.layHWdg.removeWidget(self.fx_wdg_inst) # remove widget from layout
                    self.fx_wdg_inst.deleteLater() # delete QWidget when scope has been left
                except AttributeError as e:
                    logger.error("Destructing UI failed!\n{0}".format(e))

            self.fx_wdg_found = False
            self.butSimFxPy.setVisible(False)
            self.butSimHDL.setEnabled(False)
            self.butExportHDL.setEnabled(False)
            self.img_fixp = QPixmap("no_fx_filter.png")
            self.resize_img()
            self.lblTitle.setText("")

            self.fx_wdg_inst = None
            
        # destruct old fixpoint widget instance
        _disable_fx_wdg(self)

        # instantiate new fixpoint widget class as self.fx_wdg_inst
        cmb_wdg_fx_cur = qget_cmb_box(self.cmb_wdg_fixp, data=False)
        if cmb_wdg_fx_cur: # at least one valid fixpoint widget found
            self.fx_wdg_found = True
            # get list [module name and path, class name]
            fx_mod_class_name = qget_cmb_box(self.cmb_wdg_fixp, data=True).rsplit('.',1)
            fx_mod = importlib.import_module(fx_mod_class_name[0]) # get module 
            fx_wdg_class = getattr(fx_mod, fx_mod_class_name[1]) # get class
            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            self.fx_wdg_inst = fx_wdg_class(self) # instantiate the fixpoint widget
            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            self.layHWdg.addWidget(self.fx_wdg_inst, stretch=1) # and add it to layout

# Doesn't work at the moment, combo box becomes inaccessible        
#            try:
#                self.fx_wdg_inst = fx_wdg_class(self) # instantiate the widget
#                self.layHWdg.addWidget(self.fx_wdg_inst, stretch=1) # and add it to layout
#            except KeyError as e:
#                logger.warning('Key Error {0} in fixpoint filter \n{1}'\
#                               .format(e, fx_mod_name + "." + cmb_wdg_fx_cur))
#                _disable_fx_wdg(self)
#                return
            
            self.wdg_dict2ui() # initialize the fixpoint subwidgets from the fxqc_dict

            #---- connect signals to fx_wdg_inst ----
            if hasattr(self.fx_wdg_inst, "sig_rx"):
                self.sig_rx.connect(self.fx_wdg_inst.sig_rx)
            if hasattr(self.fx_wdg_inst, "sig_tx"):
                self.fx_wdg_inst.sig_tx.connect(self.sig_rx)

            #---- instantiate and scale graphic of filter topology ----        
            if not (hasattr(self.fx_wdg_inst, "img_name") and self.fx_wdg_inst.img_name): # is an image name defined?
                self.fx_wdg_inst.img_name = "no_img.png"
                # check whether file exists
            file_path = os.path.dirname(fx_mod.__file__) # get path of imported fixpoint widget and 
            img_file = os.path.join(file_path, self.fx_wdg_inst.img_name) # construct full image name from it
            # _, file_extension = os.path.splitext(self.fx_wdg_inst.img_name)
            if os.path.exists(img_file):
                self.img_fixp = QPixmap(img_file)
#                if file_extension == '.png':
#                    self.img_fixp = QPixmap(img_file)
#                elif file_extension == '.svg':
#                    self.img_fixp = QtSvg.QSvgWidget(img_file)
            else:
                logger.warning("Image file {0} doesn't exist.".format(img_file))
                img_file = os.path.join(file_path, "no_img.png")                
                self.img_fixp = QPixmap(img_file)
                #self.lbl_img_fixp.setPixmap(QPixmap(self.img_fixp)) # fixed size
            self.resize_img()

            #---- set title and description for filter                      
            self.lblTitle.setText(self.fx_wdg_inst.title)

            #--- try to reference Python fixpoint filter instance -----
#            if hasattr(self.fx_wdg_inst,'fxpy_filter'):
#                self.fxpy_filter_inst = self.fx_wdg_inst.fxpy_filter
#                self.butSimFxPy.setEnabled(True)
#            else:
#                self.butSimFxPy.setVisible(False)
                
            #--- Check whether fixpoint widget contains HDL filters -----
            if hasattr(self.fx_wdg_inst,'fixp_filter'):
                self.butExportHDL.setEnabled(hasattr(self.fx_wdg_inst, "to_verilog"))
                self.butSimHDL.setEnabled(hasattr(self.fx_wdg_inst, "run_sim"))
                self.update_fxqc_dict()
                self.sig_tx.emit({'sender':__name__, 'fx_sim':'specs_changed'})
            else:
                self.butSimHDL.setEnabled(False)
                self.butExportHDL.setEnabled(False)

        else:
            _disable_fx_wdg(self)

#------------------------------------------------------------------------------
    def wdg_dict2ui(self):
        """
        Trigger an update of the fixpoint widget UI when view (i.e. fixpoint 
        coefficient format) or data have been changed outside this class. Additionally,
        pass the fixpoint quantization widget to update / restore other subwidget
        settings.
        
        Set the RUN button to "changed".
        """
#        fb.fil[0]['fxqc']['QCB'].update({'scale':(1 << fb.fil[0]['fxqc']['QCB']['W'])})
        self.wdg_q_input.dict2ui(fb.fil[0]['fxqc']['QI'])
        self.wdg_q_output.dict2ui(fb.fil[0]['fxqc']['QO'])
        self.wdg_w_input.dict2ui(fb.fil[0]['fxqc']['QI'])
        self.wdg_w_output.dict2ui(fb.fil[0]['fxqc']['QO'])
        if self.fx_wdg_found and hasattr(self.fx_wdg_inst, "dict2ui"):
            self.fx_wdg_inst.dict2ui()
#            dict_sig = {'sender':__name__, 'fx_sim':'specs_changed'}
#            self.sig_tx.emit(dict_sig)

        qstyle_widget(self.butSimHDL, "changed")
#------------------------------------------------------------------------------
    def update_fxqc_dict(self):
        """
        Update the fxqc dictionary before simulation / HDL generation starts.
        """
        if self.fx_wdg_found:
            # get a dict with the coefficients and fixpoint settings from fixpoint widget
            if hasattr(self.fx_wdg_inst, "ui2dict"):
                fb.fil[0]['fxqc'].update(self.fx_wdg_inst.ui2dict())
                logger.warning("update fxqc: \n{0}".format(pprint_log(fb.fil[0]['fxqc'])))
        else:
            logger.error("No fixpoint widget found!")
#------------------------------------------------------------------------------           
            
    def exportHDL(self):
        """
        Synthesize HDL description of filter
        """
        if not hasattr(self.fx_wdg_inst, 'construct_fixp_filter'):
            logger.warning('Fixpoint widget has no method "construct_fixp_filter", aborting.')
            return
        
        dlg = QFD(self) # instantiate file dialog object

        file_types = "Verilog (*.v)"

        hdl_file, hdl_filter = dlg.getSaveFileName_(
                caption="Save HDL as", directory=dirs.save_dir,
                filter=file_types)
        hdl_file = qstr(hdl_file)

        if hdl_file != "": # "operation cancelled" returns an empty string
            # return '.v' or '.vhd' depending on filetype selection:
            hdl_type = extract_file_ext(qstr(hdl_filter))[0]
            # sanitized dir + filename + suffix. The filename suffix is replaced
            # by `v` later.
            hdl_file = os.path.normpath(hdl_file)
            hdl_dir_name = os.path.dirname(hdl_file) # extract the directory path
            if not os.path.isdir(hdl_dir_name): # create directory if it doesn't exist
                os.mkdir(hdl_dir_name)
            dirs.save_dir = hdl_dir_name # make this directory the new default / base dir
            hdl_file_name = os.path.join(hdl_dir_name, 
                                os.path.splitext(os.path.basename(hdl_file))[0]+ ".v")

# =============================================================================
#             # remove the suffix from the filename:
# 
#             if hdl_type == '.vhd':
#                 hdl = 'VHDL'
#             elif hdl_type == '.v':
#                 hdl = 'Verilog'
#             else:
#                 logger.error('Unknown file extension "{0}", cancelling.'.format(hdl_type))
#                 return
# 
# =============================================================================
            logger.info('Creating hdl_file "{0}"'.format(
                        os.path.join(hdl_dir_name, hdl_file_name)))
            try:
                self.update_fxqc_dict()
                self.fx_wdg_inst.construct_fixp_filter()
                code = self.fx_wdg_inst.to_verilog()
                
                logger.info(str(code))
                
                with io.open(hdl_file_name, 'w', encoding="utf8") as f:
                    f.write(str(code))

                logger.info("HDL conversion finished!")
            except (IOError, TypeError) as e:
                logger.warning(e)

##------------------------------------------------------------------------------
#    def fx_sim_py(self):
#        """
#        Start fix-point simulation: Send the ``fxqc_dict``
#        containing all quantization information and request a stimulus signal
#        Not implemented yet
#        """
#        try:
#            logger.info("Started python fixpoint simulation")
#            self.update_fxqc_dict()
#            self.fxpyfilter.setup(fb.fil[0]['fxqc'])   # setup filter instance         
#            dict_sig = {'sender':__name__, 'fx_sim':'get_stimulus'}
#            self.sig_tx.emit(dict_sig)
#                        
#        except AttributeError as e:
#            logger.warning("Fixpoint stimulus generation failed:\n{0}".format(e))
#        return

#------------------------------------------------------------------------------
    def fx_sim_init(self):
        """
        Initialize fix-point simulation: 
            
        - Update the `fxqc_dict` containing all quantization information
        
        - Setup a filter instance for migen simulation
        
        - Request a stimulus signal
        """
        if not hasattr(self.fx_wdg_inst, 'construct_fixp_filter'):
            logger.error('Fixpoint widget has no method "construct_fixp_filter", aborting.')
            self.sig_tx.emit({'sender':__name__, 'fx_sim':'error'})
            return

        try:
            logger.info("Started HDL fixpoint simulation")
            self.update_fxqc_dict()
            self.fx_wdg_inst.construct_fixp_filter()   # setup filter instance         

            dict_sig = {'sender':__name__, 'fx_sim':'get_stimulus'}
            self.sig_tx.emit(dict_sig)
                        
        except  ValueError as e: # exception
            logger.error('Fixpoint stimulus generation failed for dict\n{0}'
                           '\nwith "{1} "'.format(pprint_log(dict_sig), e))
        return

#------------------------------------------------------------------------------
    def fx_sim_set_stimulus(self, dict_sig):
        """
        - Get fixpoint stimulus from `dict_sig` in integer format
          
        - Pass it to the fixpoint filter and calculate the fixpoint response
        
        - Send the reponse to the plotting widget
        """
        try:
            logger.info('Starting fixpoint simulation with stimulus from "{0}":\n\tfx_stimulus:{1}'
                        '\n\tStimuli: Shape {2} of type "{3}"'
                        .format( 
                            dict_sig['sender'],
                            pprint_log(dict_sig['fx_stimulus'], tab=" "),
                            np.shape(dict_sig['fx_stimulus']),
                            dict_sig['fx_stimulus'].dtype,
                            ))

            # Run fixpoint simulation and return the results as integer values:
            self.fx_results=self.fx_wdg_inst.run_sim(dict_sig['fx_stimulus'])         # Run the simulation

            if len(self.fx_results) == 0:
                logger.warning("Fixpoint simulation returned empty results!")
            else:
                logger.info("fx_results: {0}"\
                            .format(pprint_log(self.fx_results, tab= " ")))
            #TODO: fixed point / integer to float conversion?
            #TODO: color push-button to show state of simulation
            #TODO: add QTimer single shot
#            self.timer_id = QtCore.QTimer()
#            self.timer_id.setSingleShot(True)
#            # kill simulation after some idle time, also add a button for this
#            self.timer_id.timeout.connect(self.kill_sim)

        except ValueError as e:
            logger.error("Simulator error {0}".format(e))
            self.fx_results = None
            qstyle_widget(self.butSimHDL, "error")
            self.sig_tx.emit({'sender':__name__, 'fx_sim':'error'})
            return
        except AssertionError as e:
            logger.error('Fixpoint simulation failed for dict\n{0}'
                         '\twith msg. "{1}"\n\tStimuli: Shape {2} of type "{3}"'
                         '\n\tResponse: Shape {4} of type "{5}"'\
                           .format(pprint_log(dict_sig), e, 
                                   np.shape(dict_sig['fx_stimulus']),
                                   dict_sig['fx_stimulus'].dtype,
                                   np.shape(self.fx_results),
                                   type(self.fx_results)
                                    ))

            self.fx_results = None
            qstyle_widget(self.butSimHDL, "error")
            self.sig_tx.emit({'sender':__name__, 'fx_sim':'error'})
            return

        logger.debug("Sending fixpoint results")
        dict_sig = {'sender':__name__, 'fx_sim':'set_results', 
                    'fx_results':self.fx_results }            
        self.sig_tx.emit(dict_sig)
        qstyle_widget(self.butSimHDL, "normal")
        
        logger.debug("Fixpoint plotting finished")        
            
        return

###############################################################################

if __name__ == '__main__':
    from ..compat import QApplication
    logging.basicConfig() # setup a basic logger
    fb.fixpoint_classes = {{'DF1':''}, {'DF2':''}}
    fb.filter_classes = {'Bessel':{}, 'Equiripple':{'fix':'DF1'}}
    app = QApplication(sys.argv)
    mainw = Input_Fixpoint_Specs(None)
    mainw.show()

    app.exec_()
    
# test using "python -m pyfda.input_widgets.input_fixpoint_specs"
