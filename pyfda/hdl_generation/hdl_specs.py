# -*- coding: utf-8 -*-
"""
Widget for simulating fixpoint filters and 
generating VHDL and Verilog Code 

Author: Christian Muenker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
import logging
logger = logging.getLogger(__name__)

from ..compat import (QWidget, QLabel, QLineEdit, QComboBox, QFont, QPushButton, QFD,
                      QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame)

import numpy as np

from myhdl import (toVerilog, toVHDL, Signal, always, always_comb, delay,
               instance, instances, intbv, traceSignals, 
               Simulation, StopSimulation)
    

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.filter_factory as ff
import pyfda.pyfda_fix_lib as fix
from pyfda.pyfda_lib import extract_file_ext
from pyfda.pyfda_rc import params

from pyfda.hdl_generation.filter_iir import FilterIIR # IIR filter object


# see C. Feltons "FPGA IIR Lowpass Direct Form I Filter Generator"
#                 @ http://www.dsprelated.com/showcode/211.php


#------------------------------------------------------------------------------

class HDLSpecs(QWidget):
    """
    Create the widget for entering exporting / importing / saving / loading data
    """
    
    sigFilterDesigned = pyqtSignal()

    def __init__(self, parent):
        super(HDLSpecs, self).__init__(parent)

        self.initUI()

    def initUI(self):
        """
        Intitialize the main GUI, consisting of:
        """
        
        # ============== UI Layout =====================================
        bfont = QFont()
#        font.setPointSize(11)
        bfont.setBold(True)
        
        bifont = QFont()
        bifont.setBold(True)
        bifont.setItalic(True)

        ifont = QFont()
        ifont.setItalic(True)

        lblMsg = QLabel("Warning! This feature is only experimental, "
        "only HDL code for second order IIR filters under the name siir_hdl.v "
        " resp. siir_hdl.vhd are created at the moment. Files are saved "
        " in the pyFDA root directory.", self)
        lblMsg.setWordWrap(True)
        layHMsg = QHBoxLayout()
        layHMsg.addWidget(lblMsg)   

        self.frmMsg = QFrame(self)
        self.frmMsg.setLayout(layHMsg)
        self.frmMsg.setContentsMargins(*params['wdg_margins'])

# =============================================================================
# UI for quantization
# =============================================================================
        
        lblHBtnsMsg = QLabel("Fixpoint signal / coeff. formats as WI.WF:", self)
        lblHBtnsMsg.setFont(bfont)
        self.layHBtnsMsg = QHBoxLayout()
        self.layHBtnsMsg.addWidget(lblHBtnsMsg)

        ledMaxWid = 30 # Max. Width of QLineEdit fields
        qQuant = ['none', 'round', 'fix', 'floor']
        qOvfl = ['none', 'wrap', 'sat']
        tipOvfl = "Select overflow behaviour."
        tipQuant = "Select the kind of quantization."
        tipWI = "Specify number of integer bits."
        tipWF = "Specify number of fractional bits."
        lblQ = "Quant.:"
        lblOv = "Ovfl.:"

# -------------------------------------------------------------------
# subUI -- self.layHButtonsHDL_i -- for input format 
# -------------------------------------------------------------------
        self.lblWInput = QLabel("Input Format:", self)
        self.lblWInput.setFont(bifont)
        self.ledWIInput = QLineEdit(self)
        self.ledWIInput.setToolTip(tipWI)
        self.ledWIInput.setText("0")
        self.ledWIInput.setMaxLength(2) # maximum of 2 digits
        self.ledWIInput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.lblDotInput = QLabel(".", self)
        
        self.ledWFInput = QLineEdit(self)
        self.ledWFInput.setToolTip(tipWF)
        self.ledWFInput.setText("15")
        self.ledWFInput.setMaxLength(2) # maximum of 2 digits
        self.ledWFInput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.layHButtonsHDL_i = QHBoxLayout()
        self.layHButtonsHDL_i.addWidget(self.lblWInput)
        self.layHButtonsHDL_i.addStretch()
        self.layHButtonsHDL_i.addWidget(self.ledWIInput)
        self.layHButtonsHDL_i.addWidget(self.lblDotInput)
        self.layHButtonsHDL_i.addWidget(self.ledWFInput)
        
# -----------------------------------------------------------------------------
# subUI -- self.layHButtonsHDL_cc -- for coefficient format 
# -----------------------------------------------------------------------------
        enb_coeff = False
        self.lblQCoeff = QLabel("Coeff. Format:", self)
        self.lblQCoeff.setFont(bifont)
        self.lblQCoeff.setEnabled(enb_coeff)
        self.ledWICoeff = QLineEdit(self)
        self.ledWICoeff.setToolTip(tipWI)
        self.ledWICoeff.setText("0")
        self.ledWICoeff.setMaxLength(2) # maximum of 2 digits
        self.ledWICoeff.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
        self.ledWICoeff.setEnabled(enb_coeff)

        self.lblDotCoeff = QLabel(".", self)
        
        self.ledWFCoeff = QLineEdit(self)
        self.ledWFCoeff.setToolTip(tipWF)
        self.ledWFCoeff.setText("15")
        self.ledWFCoeff.setMaxLength(2) # maximum of 2 digits
#        self.ledWFCoeff.setFixedWidth(30) # width of lineedit in points(?)
        self.ledWFCoeff.setMaximumWidth(ledMaxWid)
        self.ledWFCoeff.setEnabled(enb_coeff)

        self.layHButtonsHDL_c = QHBoxLayout()
        self.layHButtonsHDL_c.addWidget(self.lblQCoeff)
        self.layHButtonsHDL_c.addStretch()
        self.layHButtonsHDL_c.addWidget(self.ledWICoeff)
        self.layHButtonsHDL_c.addWidget(self.lblDotCoeff)
        self.layHButtonsHDL_c.addWidget(self.ledWFCoeff)
 

        self.lblQuant_c = QLabel(lblQ, self)
        self.lblQuant_c.setEnabled(enb_coeff)
        self.cmbQuant_c = QComboBox(self)
        self.cmbQuant_c.addItems(qQuant)
        self.cmbQuant_c.setToolTip(tipQuant)
        self.cmbQuant_c.setEnabled(enb_coeff)
        
        self.lblQOvfl_c = QLabel(lblOv, self)
        self.lblQOvfl_c.setEnabled(enb_coeff)   
        self.cmbOvfl_c = QComboBox(self)
        self.cmbOvfl_c.addItems(qOvfl)
        self.cmbOvfl_c.setToolTip(tipOvfl)
        self.cmbOvfl_c.setEnabled(enb_coeff)   

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant_c.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbOvfl_c.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.layHButtonsHDL_cc = QHBoxLayout()
        self.layHButtonsHDL_cc.addWidget(self.lblQOvfl_c)            
        self.layHButtonsHDL_cc.addWidget(self.cmbOvfl_c)
        self.layHButtonsHDL_cc.addStretch()
        self.layHButtonsHDL_cc.addWidget(self.lblQuant_c)
        self.layHButtonsHDL_cc.addWidget(self.cmbQuant_c)
        self.layHButtonsHDL_cc.setEnabled(False)
        
# -----------------------------------------------------------------------------
# subUI -- self.layHButtonsHDL_ac -- for accumulator format / overflow behaviour
# -----------------------------------------------------------------------------
        # ---------- Accumulator format --------------
        self.lblQAccu = QLabel("Accumulator Format:", self)
        self.lblQAccu.setFont(bifont)
        self.ledWIAccu = QLineEdit(self)
        self.ledWIAccu.setToolTip(tipWI)
        self.ledWIAccu.setText("0")
        self.ledWIAccu.setMaxLength(2) # maximum of 2 digits
        self.ledWIAccu.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.lblDotAccu = QLabel(".", self)
        
        self.ledWFAccu = QLineEdit(self)
        self.ledWFAccu.setToolTip(tipWF)
        self.ledWFAccu.setText("15")
        self.ledWFAccu.setMaxLength(2) # maximum of 2 digits
        self.ledWFAccu.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.layHButtonsHDL_a = QHBoxLayout()
        self.layHButtonsHDL_a.addWidget(self.lblQAccu)
        self.layHButtonsHDL_a.addStretch()
        self.layHButtonsHDL_a.addWidget(self.ledWIAccu)
        self.layHButtonsHDL_a.addWidget(self.lblDotAccu)
        self.layHButtonsHDL_a.addWidget(self.ledWFAccu)

        # ---------- Accumulator overflow --------------
        self.lblOvfl_a = QLabel(lblOv, self)
        self.cmbOvfl_a = QComboBox(self)
        self.cmbOvfl_a.addItems(qOvfl)
        self.cmbOvfl_a.setToolTip(tipOvfl)
        
        self.lblQuant_a = QLabel(lblQ, self)
        self.cmbQuant_a = QComboBox(self)
        self.cmbQuant_a.addItems(qQuant)
        self.cmbQuant_a.setToolTip(tipQuant)

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant_a.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbOvfl_a.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.layHButtonsHDL_ac = QHBoxLayout()
        self.layHButtonsHDL_ac.addWidget(self.lblOvfl_a)            
        self.layHButtonsHDL_ac.addWidget(self.cmbOvfl_a)
        self.layHButtonsHDL_ac.addStretch()
        self.layHButtonsHDL_ac.addWidget(self.lblQuant_a)
        self.layHButtonsHDL_ac.addWidget(self.cmbQuant_a)

# -----------------------------------------------------------------------------
# subUI -- self.layHButtonsHDL_o -- for output format and overflow behaviour
# -----------------------------------------------------------------------------

        enb_o_ui = False
        self.lblQOutput = QLabel("Output Format:", self)
        self.lblQOutput.setFont(bifont)
#        self.lblQOutput.setEnabled(enb_o_ui)
        self.ledWIOutput = QLineEdit(self)
        self.ledWIOutput.setToolTip(tipWI)
        self.ledWIOutput.setText("0")
        self.ledWIOutput.setMaxLength(2) # maximum of 2 digits
        self.ledWIOutput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
#        self.ledWIOutput.setEnabled(enb_o_ui)
        
        self.lblDot_o = QLabel(".", self)
#        self.lblDot_o.setEnabled(enb_o_ui)

        self.ledWFOutput = QLineEdit(self)
        self.ledWFOutput.setToolTip(tipWF)
        self.ledWFOutput.setText("15")
        self.ledWFOutput.setMaxLength(2) # maximum of 2 digits
        self.ledWFOutput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
#        self.ledWFOutput.setEnabled(enb_o_ui)

        self.layHButtonsHDL_o = QHBoxLayout()
        self.layHButtonsHDL_o.addWidget(self.lblQOutput)
        self.layHButtonsHDL_o.addStretch()
        self.layHButtonsHDL_o.addWidget(self.ledWIOutput)
        self.layHButtonsHDL_o.addWidget(self.lblDot_o)
        self.layHButtonsHDL_o.addWidget(self.ledWFOutput)
        # This doesn't work - need to set a parent widget like WFrame
        self.layHButtonsHDL_o.setEnabled(False)
        
        # ---------- Accumulator overflow --------------
        self.lblQOvfl_o = QLabel(lblOv, self)
        self.lblQOvfl_o.setEnabled(enb_o_ui)
        self.lblQuant_o = QLabel(lblQ, self)
        self.lblQuant_o.setEnabled(enb_o_ui)
        
        self.cmbQuant_o = QComboBox(self)
        self.cmbQuant_o.addItems(qQuant)
        self.cmbQuant_o.setToolTip(tipQuant)
        self.cmbQuant_o.setEnabled(enb_o_ui)
        
        self.cmbOvfl_o = QComboBox(self)
        self.cmbOvfl_o.addItems(qOvfl)
        self.cmbOvfl_o.setToolTip(tipOvfl)
        self.cmbOvfl_o.setEnabled(enb_o_ui)

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant_o.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbOvfl_o.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.layHButtonsHDL_oc = QHBoxLayout()
        self.layHButtonsHDL_oc.addWidget(self.lblQOvfl_o)            
        self.layHButtonsHDL_oc.addWidget(self.cmbOvfl_o)
        self.layHButtonsHDL_oc.addStretch()
        self.layHButtonsHDL_oc.addWidget(self.lblQuant_o)
        self.layHButtonsHDL_oc.addWidget(self.cmbQuant_o)

        self.butExportHDL = QPushButton(self)
        self.butExportHDL.setToolTip("Create VHDL and Verilog files.")
        self.butExportHDL.setText("Create HDL")
        
        self.butSimFixPoint = QPushButton(self)
        self.butSimFixPoint.setToolTip("Simulate filter with fixpoint effects.")
        self.butSimFixPoint.setText("Simulate")

        
        self.layHButtonsHDL_h = QHBoxLayout()
        self.layHButtonsHDL_h.addWidget(self.butSimFixPoint)            
        self.layHButtonsHDL_h.addWidget(self.butExportHDL)

# -------------------------------------------------------------------        

        layVBtns = QVBoxLayout()
        layVBtns.addLayout(self.layHBtnsMsg)
        layVBtns.addLayout(self.layHButtonsHDL_i)
        
        layVBtns.addLayout(self.layHButtonsHDL_c)
        layVBtns.addLayout(self.layHButtonsHDL_cc)
        
        layVBtns.addLayout(self.layHButtonsHDL_a)
        layVBtns.addLayout(self.layHButtonsHDL_ac)

        layVBtns.addLayout(self.layHButtonsHDL_o)
        layVBtns.addLayout(self.layHButtonsHDL_oc)
        
        layVBtns.addLayout(self.layHButtonsHDL_h)

        # -------------------------------------------------------------------
        # This frame encompasses all the buttons            
        frmBtns = QFrame(self)
        frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmBtns.setLayout(layVBtns)

    # -------------------------------------------------------------------
    # Top level layout
    # -------------------------------------------------------------------
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmMsg)
#        layVMain.addWidget(self.frmFixpoint)
        layVMain.addWidget(frmBtns)
        layVMain.setContentsMargins(*params['wdg_margins'])
        
        layVMain.addStretch()
            
        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.butExportHDL.clicked.connect(self.exportHDL)
        self.butSimFixPoint.clicked.connect(self.simFixPoint)
        #----------------------------------------------------------------------
        self.update_UI()
        
#------------------------------------------------------------------------------
    def update_UI(self):
        """
        Update the UI after changing the filter class
        """
        if hasattr(ff.fil_inst, 'hdl'):
            self.butExportHDL.setEnabled('iir_sos' in ff.fil_inst.hdl)
            self.butSimFixPoint.setEnabled('iir_sos' in ff.fil_inst.hdl)
        else:
            self.butExportHDL.setEnabled(False)
            self.butSimFixPoint.setEnabled(False)
            
#------------------------------------------------------------------------------
    def setupHDL(self, file_name = "", dir_name = ""):
        """
        Setup instance of myHDL object with word lengths and coefficients
        """
        qI_i = int(self.ledWIInput.text())
        qF_i = int(self.ledWFInput.text())
        
        qI_o = int(self.ledWIOutput.text())
        qF_o = int(self.ledWFOutput.text())
        
        qQuant_o = self.cmbQuant_o.currentText()
        qOvfl_o = self.cmbOvfl_o.currentText()
        
        q_obj_o =  {'WI':qI_o, 'WF': qF_o, 'quant': qQuant_o, 'ovfl': qOvfl_o}
        myQ_o = fix.Fixed(q_obj_o) # instantiate fixed-point object


        self.W = (qI_i + qF_i + 1, qF_i) # Matlab format: (W,WF)

        # @todo: always use sos?  The filter object is setup to always
        # @todo: generate a second order filter
        # get filter coefficients etc. from filter dict
        coeffs = fb.fil[0]['ba']
        zpk =  fb.fil[0]['zpk']
        sos = fb.fil[0]['sos']

        print("W = ", self.W)
        print('b =', coeffs[0][0:3])
        print('a =', coeffs[1][0:3])

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
                caption="Save HDL as", directory=fb.base_dir,
                filter=file_types)
        hdl_file = os.path.normpath(str(hdl_file))
        hdl_type = extract_file_ext(hdl_filter)[0] # return '.v' or '.vhd'

        hdl_dir_name = os.path.dirname(hdl_file) # extract the directory path
        if not os.path.isdir(hdl_dir_name): # create directory if it doesn't exist
            os.mkdir(hdl_dir_name)
        fb.base_dir = hdl_dir_name # make this directory the new default / base dir

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
                caption = "Save plots as", directory=fb.base_dir,
                filter = plt_types)
        plt_file = os.path.normpath(str(plt_file))
        plt_type = str(plt_type)
        
        logger.info('Using plot filename "%s"', plt_file)
        
        plt_dir_name = os.path.dirname(plt_file)  # extract the directory path
        if not os.path.isdir(plt_dir_name): # create directory if it doesn't exist
            os.mkdir(plt_dir_name)
        fb.base_dir = plt_dir_name # make this directory the new default / base dir
        
        # return the filename without suffix
        plt_file_name = os.path.splitext(os.path.basename(plt_file))[0]

        self.setupHDL(file_name = plt_file_name, dir_name = plt_dir_name)
        
        logger.info('Creating plot file "{0}"'.format(
                    os.path.join(plt_dir_name, plt_file_name)))

        logger.info("Fixpoint simulation setup")
        tb = self.flt.simulate_freqz(num_loops=3, Nfft=1024)
        clk = Signal(False)
        ts  = Signal(False)
        x   = Signal(intbv(0,min=-2**(self.W[0]-1), max=2**(self.W[0]-1)))
        y   = Signal(intbv(0,min=-2**(self.W[0]-1), max=2**(self.W[0]-1)))

        sim = Simulation(tb)
        logger.info("Fixpoint simulation started")
        sim.run()
        logger.info("Fixpoint plotting started")
        self.flt.plot_response()
        logger.info("Fixpoint plotting finished")

#------------------------------------------------------------------------------

if __name__ == '__main__':

	# imports from one level above when run as __main__ :
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))


    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = HDLSpecs(None)
    mainw.show()

    app.exec_()