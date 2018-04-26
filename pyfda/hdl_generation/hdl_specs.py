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
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os, importlib
import logging
logger = logging.getLogger(__name__)

from ..compat import (Qt, QWidget, QPushButton, QComboBox, QFD, QSplitter, QLabel,
                      QPixmap, QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, 
                      QEvent, QSizePolicy)
import numpy as np

import myhdl
#from myhdl import (toVerilog, toVHDL, Signal, always, always_comb, delay,
#               instance, instances, intbv, traceSignals,
#               Simulation, StopSimulation)
hdl_wdg_list = ["HDL_DF1", "HDL_DF2"]
hdl_wdg_dir = "hdl_generation"

from pyfda.hdl_generation.hdl_df1 import HDL_DF1

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.pyfda_fix_lib as fix
import pyfda.pyfda_dirs as dirs
from pyfda.pyfda_io_lib import extract_file_ext
from pyfda.pyfda_qt_lib import qstr, qget_cmb_box
from pyfda.pyfda_rc import params

from pyfda.hdl_generation.filter_iir import FilterIIR 

# see C. Feltons "FPGA IIR Lowpass Direct Form I Filter Generator"
#                 @ http://www.dsprelated.com/showcode/211.php

#------------------------------------------------------------------------------

class HDL_Specs(QWidget):
    """
    Create the widget for entering exporting / importing / saving / loading data
    """
    sig_resize = pyqtSignal()
    def __init__(self, parent):
        super(HDL_Specs, self).__init__(parent)

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the main GUI, consisting of:
        - an image of the filter topology
        - the UI for the HDL filter settings
        - and the myHDL interface:
        """
        self.cmb_wdg_hdl = QComboBox(self)
        self.cmb_wdg_hdl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        for hdl_wdg in hdl_wdg_list:
            hdl_mod_name = 'pyfda.' + hdl_wdg_dir + '.' + hdl_wdg.lower()
            try:  # Try to import the module from the  package and get a handle:
                hdl_mod = importlib.import_module(hdl_mod_name)
                hdl_wdg_class = getattr(hdl_mod, hdl_wdg) # try to resolve the class       
                self.cmb_wdg_hdl.addItem(hdl_wdg, hdl_mod_name)
            except ImportError:
                logger.warning("Could not import {0}!".format(hdl_mod_name))
                continue
            except Exception as e:
                logger.warning("Unexpected error during module import:\n{0}".format(e))
                continue
        self.update_filt_wdg()
#------------------------------------------------------------------------------        
        # import and set self.hdl_wdg_inst
#------------------------------------------------------------------------------
        self.lblTitle = QLabel(self.hdl_wdg_inst.title, self)
        self.lblTitle.setWordWrap(True)
        self.lblTitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layHTitle = QHBoxLayout()
        layHTitle.addWidget(self.cmb_wdg_hdl)
        layHTitle.addWidget(self.lblTitle)

        self.frmTitle = QFrame(self)
        self.frmTitle.setLayout(layHTitle)
        self.frmTitle.setContentsMargins(*params['wdg_margins'])
#------------------------------------------------------------------------------        
        self.frmImg = QFrame(self)
        self.lbl_img_hdl = QLabel(self)
        self.img_dir = os.path.dirname(os.path.realpath(__file__))  
        self.img_file = os.path.join(self.img_dir, 'hdl_dummy.png')
        self.img_hdl = QPixmap(self.img_file)
        self.resize_img()
        layHImg = QHBoxLayout()
        layHImg.addWidget(self.lbl_img_hdl)
        self.frmImg.setLayout(layHImg)
        self.frmImg.setContentsMargins(*params['wdg_margins'])
#------------------------------------------------------------------------------        
        self.butExportHDL = QPushButton(self)
        self.butExportHDL.setToolTip("Create VHDL and Verilog files.")
        self.butExportHDL.setText("Create HDL")

        self.butSimFixPoint = QPushButton(self)
        self.butSimFixPoint.setToolTip("Simulate filter with fixpoint effects.")
        self.butSimFixPoint.setText("Simulate")

        self.layHBtns = QHBoxLayout()
        self.layHBtns.addWidget(self.butSimFixPoint)
        self.layHBtns.addWidget(self.butExportHDL)

        # This frame encompasses all the buttons
        frmBtns = QFrame(self)
        frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmBtns.setLayout(self.layHBtns)

    # -------------------------------------------------------------------
    # Top level layout
    # -------------------------------------------------------------------
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(self.frmTitle)
        splitter.addWidget(self.frmImg)
        splitter.addWidget(self.hdl_wdg_inst)
        splitter.addWidget(frmBtns)
        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([1000,3000, 5000,1000])

        layVMain = QVBoxLayout()
        layVMain.addWidget(splitter)
        layVMain.addStretch()
        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs & EVENTFILTERS
        #----------------------------------------------------------------------
        # monitor events and generate sig_resize event when resized
        self.lbl_img_hdl.installEventFilter(self)
        # ... then redraw image when resized
        self.sig_resize.connect(self.resize_img)

        self.cmb_wdg_hdl.currentIndexChanged.connect(self.update_all)
        self.butExportHDL.clicked.connect(self.exportHDL)
        self.butSimFixPoint.clicked.connect(self.simFixPoint)
        #----------------------------------------------------------------------

        self.update_UI()
        
#------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by monitored QLabel, only resize events are
        processed here, generating a `sig_resize` signal. Alll other events
        are passed on to the next hierarchy level.
        """
        if event.type() == QEvent.Resize:
            self.sig_resize.emit()

        # Call base class method to continue normal event processing:
        return super(HDL_Specs, self).eventFilter(source, event)
#------------------------------------------------------------------------------
    def resize_img(self):
            """ 
            Resize the image inside QLabel to completely fill the label while
            keeping the aspect ratio.
            """
            img_scaled = self.img_hdl.scaled(self.lbl_img_hdl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_img_hdl.setPixmap(QPixmap(img_scaled))

#------------------------------------------------------------------------------
    def update_all(self):
        """
        Import new module and update UI after changing the filter topology
        """
        self.update_filt_wdg()
        self.update_UI()

#------------------------------------------------------------------------------
    def update_filt_wdg(self):
        """
        Import new module after changing the filter topology
        """
        cmb_wdg_hdl_cur = qstr(self.cmb_wdg_hdl.currentText())

        if cmb_wdg_hdl_cur: # at least one valid hdl widget found
            self.hdl_wdg_found = True
            hdl_mod_name = qget_cmb_box(self.cmb_wdg_hdl, data=True)
            hdl_mod = importlib.import_module(hdl_mod_name)
            hdl_wdg_class = getattr(hdl_mod, cmb_wdg_hdl_cur)
            self.hdl_wdg_inst = hdl_wdg_class(self)
        else:
            self.hdl_wdg_found = False
 
#------------------------------------------------------------------------------
    def update_UI(self):
        """
        Update the UI after changing the filter class
        """
        if self.hdl_wdg_inst.img_name: # is filename defined?
            # check whether file exists
            file_path = os.path.dirname(os.path.realpath(__file__))  
            img_file = os.path.join(file_path, self.hdl_wdg_inst.img_name)
            if os.path.exists(img_file):
                self.img_hdl = QPixmap(img_file)
            else:
                logger.warning("Image file {0} doesn't exist.".format(img_file))
                img_file = os.path.join(file_path, "hdl_dummy.png")                
                self.img_hdl = QPixmap(img_file)
                
                #self.lbl_img_hdl.setPixmap(QPixmap(self.img_hdl)) # fixed size
            self.resize_img()
            
        self.lblTitle.setText(self.hdl_wdg_inst.title)
# =============================================================================
#             layHImg = QHBoxLayout()
#             layHImg.addWidget(self.lbl_img_hdl)
#             self.frmImg.setLayout(layHImg)
#             self.frmImg.setContentsMargins(*params['wdg_margins'])
# 
# =============================================================================

# =============================================================================
#         if hasattr(ff.fil_inst, 'hdl'):
#             self.butExportHDL.setEnabled('iir_sos' in ff.fil_inst.hdl)
#             self.butSimFixPoint.setEnabled('iir_sos' in ff.fil_inst.hdl)
#         else:
#             self.butExportHDL.setEnabled(False)
#             self.butSimFixPoint.setEnabled(False)
#
# =============================================================================
#------------------------------------------------------------------------------
    def setupHDL(self, file_name = "", dir_name = ""):
        """
        Setup instance of myHDL object with word lengths and coefficients
        """
        self.qI_i = self.wdg_wi_wf_input.WI
        self.qF_i = self.wdg_wi_wf_input.WF

        self.qI_o = self.wdg_wi_wf_output.WI
        self.qF_o = self.wdg_wi_wf_output.WF

        qQuant_o = self.wdg_q_ovfl_output.quant
        qOvfl_o = self.wdg_q_ovfl_output.ovfl

        q_obj_o =  {'WI':self.qI_o, 'WF': self.qF_o, 'quant': qQuant_o, 'ovfl': qOvfl_o}
        myQ_o = fix.Fixed(q_obj_o) # instantiate fixed-point object


        self.W = (self.qI_i + self.qF_i + 1, self.qF_i) # Matlab format: (W,WF)

        # @todo: always use sos?  The filter object is setup to always
        # @todo: generate a second order filter
        # get filter coefficients etc. from filter dict
        coeffs = fb.fil[0]['ba']
        zpk =  fb.fil[0]['zpk']
        sos = fb.fil[0]['sos']

        logger.info("W = {0}".format(self.W))
        logger.info('b = {0}'.format(coeffs[0][0:3]))
        logger.info('a = {0}'.format(coeffs[1][0:3]))

        # =============== adapted from C. Felton's SIIR example =============
        self.flt = FilterIIR(b=np.array(coeffs[0][0:3]),
                             a=np.array(coeffs[1][0:3]),
                             #sos = sos, doesn't work yet
                             word_format=(self.W[0], 0, self.W[1]))

        self.flt.hdl_name = file_name
        self.flt.hdl_directory = dir_name

#------------------------------------------------------------------------------
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

        if hdl_file != "": # "operation cancelled" gives back an empty string
            hdl_file = os.path.normpath(hdl_file)
            hdl_type = extract_file_ext(qstr(hdl_filter))[0] # return '.v' or '.vhd'

            hdl_dir_name = os.path.dirname(hdl_file) # extract the directory path
            if not os.path.isdir(hdl_dir_name): # create directory if it doesn't exist
                os.mkdir(hdl_dir_name)
            dirs.save_dir = hdl_dir_name # make this directory the new default / base dir

            # return the filename without suffix
            hdl_file_name = os.path.splitext(os.path.basename(hdl_file))[0]

            self.setupHDL(file_name = hdl_file_name, dir_name = hdl_dir_name)

            if str(hdl_type) == '.vhd':
                self.flt.hdl_target = 'vhdl'
                suffix = '.vhd'
            else:
                self.flt.hdl_target = 'verilog'
                suffix = '.v'


            logger.info('Creating hdl_file "{0}"'.format(
                        os.path.join(hdl_dir_name, hdl_file_name + suffix)))

            self.flt.convert()
            logger.info("HDL conversion finished!")

#------------------------------------------------------------------------------
    def simFixPoint(self):
        """
        Simulate filter in fix-point description
        """
        # Setup the Testbench and run

        dlg = QFD(self)  # instantiate file dialog object

        plt_types = "png (*.png);;svg (*.svg)"

        plt_file, plt_type = dlg.getSaveFileName_(
                caption = "Save plots as", directory=dirs.save_dir,
                filter = plt_types)
        plt_file = str(plt_file)

        if plt_file != "":
            plt_file = os.path.normpath(plt_file)
            plt_type = str(plt_type)

            logger.info('Using plot filename "%s"', plt_file)

            plt_dir_name = os.path.dirname(plt_file)  # extract the directory path
            if not os.path.isdir(plt_dir_name): # create directory if it doesn't exist
                os.mkdir(plt_dir_name)
            dirs.save_dir = plt_dir_name # make this directory the new default / base dir

#            plt_file_name = os.path.splitext(os.path.basename(plt_file))[0] # filename without suffix
            plt_file_name = os.path.basename(plt_file)

            logger.info('Creating plot file "{0}"'.format(
                        os.path.join(plt_dir_name, plt_file_name)))

            self.setupHDL(file_name = plt_file_name, dir_name = plt_dir_name)

            logger.info("Fixpoint simulation setup")
            tb = self.flt.simulate_freqz(num_loops=3, Nfft=1024)
            clk = myhdl.Signal(False)
            ts  = myhdl.Signal(False)
            x   = myhdl.Signal(myhdl.intbv(0,min=-2**(self.W[0]-1), max=2**(self.W[0]-1)))
            y   = myhdl.Signal(myhdl.intbv(0,min=-2**(self.W[0]-1), max=2**(self.W[0]-1)))

            try:
                sim = myhdl.Simulation(tb)
                logger.info("Fixpoint simulation started")
                sim.run()
                logger.info("Fixpoint plotting started")
                self.flt.plot_response()
                logger.info("Fixpoint plotting finished")
            except myhdl.SimulationError as e:
                logger.warning("Simulation failed:\n{0}".format(e))

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = HDL_Specs(None)
    mainw.show()

    app.exec_()
    
# test using "python -m pyfda.hdl_generation.hdl_specs"