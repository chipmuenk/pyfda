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
import sys, os
import logging
logger = logging.getLogger(__name__)

from ..compat import (Qt, QtCore, QWidget, QPushButton, QFD, QSplitter, QPixmap, QLabel,
                      QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, QEvent)
import numpy as np

#from myhdl import (toVerilog, toVHDL, Signal, always, always_comb, delay,
#               instance, instances, intbv, traceSignals,
#               Simulation, StopSimulation)
import myhdl
from pyfda.hdl_generation.hdl_df1 import HDL_DF1

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.pyfda_fix_lib as fix
import pyfda.pyfda_dirs as dirs
from pyfda.pyfda_io_lib import extract_file_ext
from pyfda.pyfda_qt_lib import qstr
from pyfda.pyfda_rc import params

from pyfda.hdl_generation.filter_iir import FilterIIR # IIR filter object


# see C. Feltons "FPGA IIR Lowpass Direct Form I Filter Generator"
#                 @ http://www.dsprelated.com/showcode/211.php

#------------------------------------------------------------------------------

class HDL_Specs(QWidget):
    """
    Create the widget for entering exporting / importing / saving / loading data
    """
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

#------------------------------------------------------------------------------        
        self.frmHDL = HDL_DF1(self)
#------------------------------------------------------------------------------
        lblTitle = QLabel(self.frmHDL.title, self)
        lblTitle.setWordWrap(True)
        layHTitle = QHBoxLayout()
        layHTitle.addWidget(lblTitle)

        self.frmTitle = QFrame(self)
        self.frmTitle.setLayout(layHTitle)
        self.frmTitle.setContentsMargins(*params['wdg_margins'])
#------------------------------------------------------------------------------        
        self.lbl_img_hdl = QLabel(self)
        file_path = os.path.dirname(os.path.realpath(__file__))
        img_file = os.path.join(file_path, self.frmHDL.img_name)
        self.img_hdl = QPixmap(img_file)
        #img_hdl_scaled = img_hdl.scaled(self.lbl_img_hdl.size(), Qt.KeepAspectRatio)
        # self.lbl_img_hdl.setPixmap(QPixmap(img_hdl_scaled))
        
        self.lbl_img_hdl.setPixmap(QPixmap(self.img_hdl)) # fixed size

        layHImg = QHBoxLayout()
        layHImg.addWidget(self.lbl_img_hdl)
        self.frmImg = QFrame(self)
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
        splitter.addWidget(self.frmHDL)
        splitter.addWidget(frmBtns)
        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([1000,1000, 3000,10000])


        layVMain = QVBoxLayout()
        layVMain.addWidget(splitter)
        #layVMain.addWidget(self.frmMsg)
        #layVMain.addWidget(self.frmImg)
        #layVMain.addWidget(frmBtns)
        #layVMain.addStretch()
        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.timer_id = QtCore.QTimer()
        self.timer_id.setSingleShot(True)
        # redraw current widget at timeout (timer was triggered by resize event):
        self.timer_id.timeout.connect(self.resize_img)

        splitter.installEventFilter(self)

        self.butExportHDL.clicked.connect(self.exportHDL)
        self.butSimFixPoint.clicked.connect(self.simFixPoint)
        #----------------------------------------------------------------------

        self.update_UI()
        
#------------------------------------------------------------------------------
    def eventFilter(self, source, event):
        """
        Filter all events generated by QSplitter. Source and type of all
         events generated by monitored objects are passed to this eventFilter,
        evaluated and passed on to the next hierarchy level.
        
        This filter stops and restarts a one-shot timer for every resize event.
        When the timer generates a timeout after 500 ms, current_tab_redraw is 
        called by the timer.
        """
        if isinstance(source, QSplitter):
            if event.type() == QEvent.Resize:
                self.timer_id.stop()
                self.timer_id.start(500)

        # Call base class method to continue normal event processing:
        return super(HDL_Specs, self).eventFilter(source, event)
#------------------------------------------------------------------------------

    def resize_img(self):
            img_scaled = self.img_hdl.scaled(self.lbl_img_hdl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_img_hdl.setPixmap(QPixmap(img_scaled))


#------------------------------------------------------------------------------
    def update_UI(self):
        """
        Update the UI after changing the filter class
        """
        pass
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