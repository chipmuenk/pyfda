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
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os, importlib
import logging
logger = logging.getLogger(__name__)

from ..compat import (Qt, QWidget, QPushButton, QComboBox, QFD, QSplitter, QLabel,
                      QPixmap, QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, 
                      QEvent, QSizePolicy)

import numpy as np

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.pyfda_dirs as dirs
from pyfda.pyfda_lib import qstr, cmp_version
import pyfda.pyfda_fix_lib as fx
from pyfda.pyfda_io_lib import extract_file_ext
from pyfda.pyfda_qt_lib import qget_cmb_box, qstyle_widget
from pyfda.fixpoint_widgets.fixpoint_helpers import UI_W, UI_Q
from pyfda.pyfda_rc import params

if cmp_version("myhdl", "0.10") >= 0:
    import myhdl
    HAS_MYHDL = True
  
#    fil_blocks_path = os.path.abspath(os.path.join(dirs.INSTALL_DIR, '../../filter-blocks'))
#    if not os.path.exists(fil_blocks_path):
#        logger.error("Invalid path {0}".format(fil_blocks_path))
#    else:
#        if fil_blocks_path not in sys.path:
#            sys.path.append(fil_blocks_path)
#        from pyfda.filter_blocks.fda.fir import FilterFIR
#        from pyfda.filter_blocks.fda.iir import FilterIIR

else:
    HAS_MYHDL = False

# see C. Feltons "FPGA IIR Lowpass Direct Form I Filter Generator"
#                 @ http://www.dsprelated.com/showcode/211.php

#------------------------------------------------------------------------------

class Input_Fixpoint_Specs(QWidget):
    """
    Create the widget that holds the dynamically loaded fixpoint filter ui 
    """
    # emit a signal when the image has been resized
    sig_resize = pyqtSignal()
    # incoming, connected to input_tab_widget.sig_tx
    sig_rx = pyqtSignal(object)
    # outcgoing
    sig_tx = pyqtSignal(object)

    def __init__(self, parent):
        super(Input_Fixpoint_Specs, self).__init__(parent)

        self.tab_label = 'Fixpoint'
        self.tool_tip = ("<span>Select a fixpoint implementation for the filter,"
                " simulate it and generate a Verilog / VHDL netlist.</span>")
        self.parent = parent
        # initialize the dict with the filter quantization settings and coefficients
        self.fxqc_dict = {'QI':{}, 'QO':{}}
        

        if HAS_MYHDL:
            self._construct_UI()
        else:
            self.state = "deactivated" # "invisible", "disabled"

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming in via subwidgets and sig_rx
		
		Play PingPong with a stimulus & plot widget:
		
		(1. ``fx_sim_init()``: Initialize quantization dict ``hdl_dict`` with settings
			from fixpoint widget.) # currently not implemented
		2. ``fx_sim_hdl()``: Request stimulus by sending 'fx_sim':'get_stimulus'
		
		3. ``fx_sim_set_stimulus()``: Receive stimulus from widget in 'fx_sim':'set_stimulus'
			and pass it to HDL object for simulation
		   
		4. Send back HDL response to widget via 'fx_sim':'set_response'

        """
		
        logger.debug("Processing {0}: {1}".format(type(dict_sig).__name__, dict_sig))
        if dict_sig['sender'] == __name__:
            logger.debug("Infinite loop detected")
            return
        if 'data_changed' in dict_sig:
            # update hdl_dict when filter has been designed and set RUN button to "changed"
            # TODO: This needs to be changed
            self.wdg_dict2ui()
        if 'filt_changed' in dict_sig:
            # update list of available filter topologies here
            self._update_filter_cmb()
        if 'view_changed' in dict_sig and dict_sig['view_changed'] == 'q_coeff':
            # update fields in the filter topology widget - wordlength may have
            # been changed. Also set RUN button to "changed"
            self.wdg_dict2ui()
        if 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'init':
                self.fx_sim_init() # not implemented: what should it do?
        if 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'start':
                self.fx_sim_hdl()
        if 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'set_stimulus':
                self.fx_sim_set_stimulus(dict_sig)

                
#------------------------------------------------------------------------------

    def _construct_UI(self):
        """
        Intitialize the main GUI, consisting of:
            
        - A combo box to select the filter topology and an image of the filter topology
        
        - The input quantizer
        
        - The UI of the fixpoint filter widget
        
        - and the myHDL interface:
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
        lblHBtnsMsg1 = QLabel("<b>Fixpoint signal / coeff. formats:</b>", self)
        lblHBtnsMsg2 = QLabel("<b>WI.WF  </b>", self)
        layHBtnsMsg = QHBoxLayout()
        layHBtnsMsg.addWidget(lblHBtnsMsg1)
        layHBtnsMsg.addStretch(1)
        layHBtnsMsg.addWidget(lblHBtnsMsg2)

        self.wdg_w_input = UI_W(self, label='Input Format <i>Q<sub>X </sub></i>:')
        self.wdg_q_input = UI_Q(self)

        self.wdg_w_output = UI_W(self, label='Output Format <i>Q<sub>Y </sub></i>:')
        self.wdg_q_output = UI_Q(self)

        layVQioWdg = QVBoxLayout()
        layVQioWdg.addLayout(layHBtnsMsg)
        layVQioWdg.addWidget(self.wdg_w_input)
        layVQioWdg.addWidget(self.wdg_q_input)
        layVQioWdg.addWidget(self.wdg_w_output)
        layVQioWdg.addWidget(self.wdg_q_output)

        # This frame encompasses the HDL buttons sim and convert
        frmQioWdg = QFrame(self)
        #frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmQioWdg.setLayout(layVQioWdg)
        frmQioWdg.setContentsMargins(*params['wdg_margins'])
        
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
#       myhdl Buttons        
#------------------------------------------------------------------------------        
        self.butExportHDL = QPushButton(self)
        self.butExportHDL.setToolTip("Create VHDL and Verilog files.")
        self.butExportHDL.setText("Create HDL")

        self.butSimHDL = QPushButton(self)
        self.butSimHDL.setToolTip("Start fixpoint simulation with myHDL description.")
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
        splitter.addWidget(self.frmImg)

        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([3000, 5000])

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmTitle)
        layVMain.addWidget(frmQioWdg)
#        layVMain.addWidget(frmQoWdg)
        layVMain.addWidget(frmHdlBtns)
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
        self.butSimHDL.clicked.connect(self.fx_sim_hdl)
        self.butSimFxPy.clicked.connect(self.fx_sim_py)
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
        every time a new filter design is selected (not fully implemented yet,
        at the moment a list with *all* filter implementations is read). 
        
        Then try to import the fixpoint designs in the list and populate the 
        fixpoint implementation combo box ``self.cmb_wdg_fixp`` when successfull. 
        """
        inst_wdg_str = "" # full names of successfully instantiated widgets for logging

        self.cmb_wdg_fixp.clear()

        # wdg = (class_name, dir)
        for wdg in fb.fixpoint_widgets_list:
            if not wdg[1]:
                # use standard module
                pckg_name = 'pyfda'
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
            mod_name = pckg_name + '.fixpoint_widgets.' + wdg[0].lower()
            class_name = pckg_name + '.fixpoint_widgets.' + wdg[0]

            try:  # Try to import the module from the  package ...
                mod = importlib.import_module(mod_name)
                # get the class belonging to wdg[0] ...
                _ = getattr(mod, wdg[0]) # try to resolve the class       
                # everything worked fine, add it to the combo box:
                self.cmb_wdg_fixp.addItem(wdg[0], mod_name)
                
                inst_wdg_str += '\t' + class_name + '\n'

            except ImportError:
                logger.warning('Could not import module "{0}"!'.format(mod_name))
                continue
            except AttributeError:
                logger.warning('No attribute / class "{0}" in"{1}"'.format(wdg[0], mod_name))
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
    def update_all(self):
        """
        Import new module and update UI after changing the filter topology
        """
        self._construct_dyn_widget()
        self.update_UI()

#------------------------------------------------------------------------------
    def _update_fixp_widget(self):
        """
        This method is called at the initialization of the ``input_fixpoint_specs``
         widget and when  a new fixpoint filter implementation is selected 
        in the combo box:

        - Destruct old instance of fixpoint filter widget
        
        - Import and instantiate new fixpoint filter widget e.g. after changing the 
          filter topology
          
        - Try to load image for filter topology
        
        - Update the UI of the widget
        
        - Instantiate
          ``self.hdl_filter_inst = self.fx_wdg_inst.hdlfilter``
        """
        # destruct old fixpoint widget instance
        if hasattr(self, "fx_wdg_inst"): # is a fixpoint widget loaded?
            try:
                self.layHWdg.removeWidget(self.fx_wdg_inst) # remove widget from layout
                self.fx_wdg_inst.deleteLater() # delete QWidget when scope has been left
            except AttributeError as e:
                logger.error("Could not destruct_UI!\n{0}".format(e))

        # instantiate new fixpoint widget class as self.fx_wdg_inst
        # which instantiates filter class as self.fx_wdg_inst.hdlfilter
        cmb_wdg_fx_cur = qget_cmb_box(self.cmb_wdg_fixp, data=False)
        if cmb_wdg_fx_cur: # at least one valid fixpoint widget found
            self.fx_wdg_found = True
            fx_mod_name = qget_cmb_box(self.cmb_wdg_fixp, data=True) # module name and path
            fx_mod = importlib.import_module(fx_mod_name) # get module 
            fx_wdg_class = getattr(fx_mod, cmb_wdg_fx_cur) # get class
            self.fx_wdg_inst = fx_wdg_class(self) # instantiate the widget
            self.layHWdg.addWidget(self.fx_wdg_inst, stretch=1) # and add it to layout
            self.wdg_dict2ui() # initialize the fixpoint subwidgets from the fxqc_dict

            #---- connect signals to fx_wdg_inst ----
            if hasattr(self.fx_wdg_inst, "sig_rx"):
                self.sig_rx.connect(self.fx_wdg_inst.sig_rx)
            #if hasattr(self.fx_wdg_inst, "sig_tx"):
                #self.fx_wdg_inst.sig_tx.connect(self.sig_rx)

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
                img_file = os.path.join(file_path, "hdl_dummy.png")                
                self.img_fixp = QPixmap(img_file)
                #self.lbl_img_fixp.setPixmap(QPixmap(self.img_fixp)) # fixed size
            self.resize_img()
                
            self.lblTitle.setText(self.fx_wdg_inst.title)

            #--- try to reference Python fixpoint filter instance -----
            if hasattr(self.fx_wdg_inst,'fxpy_filter'):
                self.fxpy_filter_inst = self.fx_wdg_inst.fxpy_filter
                self.butSimFxPy.setEnabled(True)
            else:
                self.butSimFxPy.setEnabled(False)
                
            #--- try to reference HDL fixpoint filter instance -----
            if hasattr(self.fx_wdg_inst,'hdlfilter'):
                self.hdl_filter_inst = self.fx_wdg_inst.hdlfilter
                self.butExportHDL.setEnabled(hasattr(self.fx_wdg_inst.hdlfilter, "convert"))
                self.butSimHDL.setEnabled(hasattr(self.fx_wdg_inst.hdlfilter, "run_sim"))
                self.update_fxqc_dict()
                #self.fx_wdg_inst.update_hdl_filter()
            else:
                self.hdl_filter_inst = None
                self.butSimHDL.setEnabled(False)
                self.butExportHDL.setEnabled(False)

        else:
            self.fx_wdg_found = False
            self.butSimFxPy.setEnabled(False)
            self.butSimHDL.setEnabled(False)
            self.butExportHDL.setEnabled(False)

#------------------------------------------------------------------------------
    def wdg_dict2ui(self):
        """
        Trigger an update of the fixpoint widget UI when view (i.e. fixpoint 
        coefficient format) has been changed outside this class. Additionally,
        pass the fixpoint quantization widget to update / restore other subwidget
        settings.
        
        Set the RUN button to "changed".
        """
        if hasattr(self.fx_wdg_inst, "dict2ui"):
            self.fx_wdg_inst.dict2ui(self.fxqc_dict)

        qstyle_widget(self.butSimHDL, "changed")
#------------------------------------------------------------------------------
    def update_fxqc_dict(self):
        """
        Update the fxqc dictionary before simulation / HDL generation starts. It
        is NOT updated each time one of the relevant widgets changes ("lazy update").
         This avoids having to connect and disconnect all sorts of signals and slots.
        """
        if self.fx_wdg_found and self.hdl_filter_inst:
            # get a dict with the coefficients and fixpoint settings from fixpoint widget
            if hasattr(self.fx_wdg_inst, "ui2dict"):
                self.fxqc_dict.update(self.fx_wdg_inst.ui2dict())

            # update the fxqc_dict with the settings of the input quantizer  
            self.fxqc_dict.update({'QI':{'WI': self.wdg_w_input.WI,
                       'WF': self.wdg_w_input.WF,
                       'W':  self.wdg_w_input.W,
                       'ovfl': self.wdg_q_input.ovfl,
                       'quant': self.wdg_q_input.quant
                       }
                })
            # output quantization parameters
            self.fxqc_dict.update({'QO':{'WI':self.wdg_w_output.WI,
                               'WF':self.wdg_w_output.WF,
                               'W':self.wdg_w_output.W,
                               'ovfl': self.wdg_q_output.ovfl,
                               'quant': self.wdg_q_output.quant
                               }
                        })

            self.q_i = fx.Fixed(self.fxqc_dict['QI']) # setup quantizer for input quantization
            self.q_i.setQobj({'frmt':'dec'})#, 'scale':'int'}) # always use integer decimal format
            self.q_o = fx.Fixed(self.fxqc_dict['QO']) # setup quantizer for output quantization
        else:
            logger.error("No fixpoint widget or HDL filter instance found!")
#------------------------------------------------------------------------------           
    def info_hdl(self, hdl_dict):
        """
        Print filter info (not reallly implemented yet)
        """
        print("Filter type :", self.filter_type, "\n"
              "Filter order :", len(self.b), "\n"
              "Arithmatic :", "fixed", "\n"
              "Coefficient format :", self.coef_word_format ,"\n"
              "Input format :", self.input_word_format ,"\n"
              "Accumulator size :", "\n"
              "Output format :", self.output_word_format ,"\n"
              "Round mode :", "no rounding", "\n"
              "Overflow mode :" "no overflow"
            )

    def exportHDL(self):
        """
        Synthesize HDL description of filter using myHDL module
        """
        dlg = QFD(self) # instantiate file dialog object

        file_types = "Verilog (*.v);;VHDL (*.vhd)"

        hdl_file, hdl_filter = dlg.getSaveFileName_(
                caption="Save HDL as", directory=dirs.save_dir,
                filter=file_types)
        hdl_file = qstr(hdl_file)

        if hdl_file != "": # "operation cancelled" returns an empty string
            # return '.v' or '.vhd' depending on filetype selection:
            hdl_type = extract_file_ext(qstr(hdl_filter))[0]
            # sanitized dir + filename + suffix. The filename suffix is replaced
            # by `hdl_type` later.
            hdl_file = os.path.normpath(hdl_file)
            hdl_dir_name = os.path.dirname(hdl_file) # extract the directory path
            if not os.path.isdir(hdl_dir_name): # create directory if it doesn't exist
                os.mkdir(hdl_dir_name)
            dirs.save_dir = hdl_dir_name # make this directory the new default / base dir

            # remove the suffix from the filename:
            hdl_file_name = os.path.splitext(os.path.basename(hdl_file))[0]

            if hdl_type == '.vhd':
                hdl = 'VHDL'
            elif hdl_type == '.v':
                hdl = 'Verilog'
            else:
                logger.error('Unknown file extension "{0}", cancelling.'.format(hdl_type))
                return

            logger.info('Creating hdl_file "{0}"'.format(
                        os.path.join(hdl_dir_name, hdl_file_name + hdl_type)))
            try:
                self.update_fxqc_dict()
                self.hdl_filter_inst.setup(self.fxqc_dict)
                self.hdl_filter_inst.convert(hdl=hdl, name=hdl_file_name, path=hdl_dir_name)

                logger.info("HDL conversion finished!")
            except (IOError, TypeError) as e:
                logger.warning(e)

#------------------------------------------------------------------------------
    def fx_sim_py(self):
        """
        Start fix-point simulation: Send the ``fxqc_dict``
        containing all quantization information and request a stimulus signal
        """
        try:
            logger.info("Started myhdl fixpoint simulation")
            self.update_fxqc_dict()
            self.fxpyfilter.setup(self.fxqc_dict)   # setup filter instance         
            dict_sig = {'sender':__name__, 'fx_sim':'get_stimulus', 'hdl_dict':self.fxqc_dict}
            self.sig_tx.emit(dict_sig)
                        
        except AttributeError as e:
            logger.warning("Fixpoint stimulus generation failed:\n{0}".format(e))
        return

#------------------------------------------------------------------------------
    def fx_sim_hdl(self):
        """
        Start fix-point simulation: Send the ``fxqc_dict``
        containing all quantization information and request a stimulus signal
        """
        try:
            logger.info("Started myhdl fixpoint simulation")
            self.update_fxqc_dict()
            self.hdl_filter_inst.setup(self.fxqc_dict)   # setup filter instance         
            dict_sig = {'sender':__name__, 'fx_sim':'get_stimulus', 'hdl_dict':self.fxqc_dict}
            self.sig_tx.emit(dict_sig)
                        
        except myhdl.SimulationError as e:
            logger.warning("Fixpoint stimulus generation failed:\n{0}".format(e))
        return

#------------------------------------------------------------------------------
    def fx_sim_set_stimulus(self, dict_sig):
        """
        - Get fixpoint stimulus from ``dict_sig``
        
        - Quantize the stimulus with the selected input quantization settings
        
		- Scale it with the input word length, i.e. with 2**(W-1) (input) to obtain
          integer values
          
        - Pass it to the fixpoint filter and calculate the fixpoint response
        
        - Send the reponse to the plotting widget
        """
        try:
            self.stim = self.q_i.fixp(dict_sig['fx_stimulus']) * (1 << self.q_i.W-1)
            logger.info("\n\n stim W={0}|q={1}\nstim:{2}\nstimq:{3}\n".format(self.q_i.W, self.q_i.q_obj, 
                        dict_sig['fx_stimulus'][0:9], self.stim[0:9]))

            self.hdl_filter_inst.set_stimulus(self.stim)    # Set the simulation input
            self.hdl_filter_inst.run_sim()         # Run the simulation
            logger.info("Start fixpoint simulation with stimulus from {0}.".format(dict_sig['sender']))

            # Get the response from the simulation in integer
            self.fx_results = self.hdl_filter_inst.get_response()
            logger.info("\n\n resp {0}\n".format(self.fx_results[0:9]))
            #TODO: fixed point / integer to float conversion?
            #TODO: color push-button to show state of simulation
            #TODO: add QTimer single shot
#            self.timer_id = QtCore.QTimer()
#            self.timer_id.setSingleShot(True)
#            # kill simulation after some idle time, also add a button for this
#            self.timer_id.timeout.connect(self.kill_sim)

        except myhdl.SimulationError as e:
            logger.warning("Simulation failed:\n{0}".format(e))
            self.fx_results = None
            qstyle_widget(self.butSimHDL, "error")
            return
        except ValueError as e:
            logger.warning("Overflow error {0}".format(e))
            self.fx_results = None
            qstyle_widget(self.butSimHDL, "error")
            return

        logger.info("Fixpoint plotting started")
        dict_sig = {'sender':__name__, 'fx_sim':'set_results', 
                    'fx_results':self.fx_results }            
        self.sig_tx.emit(dict_sig)
        qstyle_widget(self.butSimHDL, "normal")
        
        logger.info("Fixpoint plotting finished")        
            
        return

###############################################################################

if __name__ == '__main__':
    from ..compat import QApplication
    logging.basicConfig() # setup a basic logger
    fb.fixpoint_widgets_list = [('DF1',''), ('DF2','')]
    app = QApplication(sys.argv)
    mainw = Input_Fixpoint_Specs(None)
    mainw.show()

    app.exec_()
    
# test using "python -m pyfda.input_widgets.input_fixpoint_specs"
