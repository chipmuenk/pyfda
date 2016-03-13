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

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import numpy as np

from myhdl import (toVerilog, toVHDL, Signal, always, always_comb, delay,
               instance, instances, intbv, traceSignals, 
               Simulation, StopSimulation)
    

import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.pyfda_fix_lib as fix
import pyfda.pyfda_rc as rc

from pyfda.hdl_generation.filter_iir import SIIR #  second order IIR filter object


# see C. Feltons "FPGA IIR Lowpass Direct Form I Filter Generator"
#                 @ http://www.dsprelated.com/showcode/211.php

#------------------------------------------------------------------------------
class HDLSpecs(QtGui.QWidget):
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
        bfont = QtGui.QFont()
#        font.setPointSize(11)
        bfont.setBold(True)
        
        bifont = QtGui.QFont()
        bifont.setBold(True)
        bifont.setItalic(True)

        ifont = QtGui.QFont()
        ifont.setItalic(True)

        self.lblMyhdl1 = QtGui.QLabel("Warning! This feature is only experimental, "
        "only HDL code for second order IIR filters under the name siir_hdl.v "
        " resp. siir_hdl.vhd are created at the moment. Files are saved "
        " in the pyFDA root directory.")
        self.lblMyhdl1.setWordWrap(True)
#        self.lblMyhdl1.setFont(bfont)
        self.lblMyhdl2 = QtGui.QLabel("Enter fixpoint signal formats as QI.QF:")

        
        ledMaxWid = 30 # Max. Width of QLineEdit fields
        qQuant = ['none', 'round', 'fix', 'floor']
        qOvfl = ['none', 'wrap', 'sat']
        tipOvfl = "Select overflow behaviour."
        tipQuant = "Select the kind of quantization."
        tipQI = "Specify number of integer bits."
        tipQF = "Specify number of fractional bits."
        lblQ = "Quant.:"
        lblOv = "Ovfl.:"
        

        layVMain = QtGui.QVBoxLayout()


        self.lblQIQF  = QtGui.QLabel("QI.QF = ")
        self.lblDot_c = QtGui.QLabel(".")
#        self.lblDot_c.setEnabled(enb_coeff)

        self.lblDot_i = QtGui.QLabel(".")

        self.lblDot_a = QtGui.QLabel(".")
        self.lblQuant_a = QtGui.QLabel(lblQ)
        self.lblQOvfl_a = QtGui.QLabel(lblOv)


# -------------------------------------------------------------------
# UI for input format 
# -------------------------------------------------------------------
        self.lblQInput = QtGui.QLabel("Input Format:")
        self.lblQInput.setFont(bifont)
        self.ledQIInput = QtGui.QLineEdit()
        self.ledQIInput.setToolTip(tipQI)
        self.ledQIInput.setText("0")
        self.ledQIInput.setMaxLength(2) # maximum of 2 digits
        self.ledQIInput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.ledQFInput = QtGui.QLineEdit()
        self.ledQFInput.setToolTip(tipQF)
        self.ledQFInput.setText("15")
        self.ledQFInput.setMaxLength(2) # maximum of 2 digits
        self.ledQFInput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.layHButtonsHDL_i = QtGui.QHBoxLayout()
        self.layHButtonsHDL_i.addWidget(self.lblQInput)
        self.layHButtonsHDL_i.addStretch()
        self.layHButtonsHDL_i.addWidget(self.ledQIInput)
        self.layHButtonsHDL_i.addWidget(self.lblDot_i)
        self.layHButtonsHDL_i.addWidget(self.ledQFInput)
# -------------------------------------------------------------------
# UI for output format 
# -------------------------------------------------------------------
        enb_coeff = False
        self.lblQCoeff = QtGui.QLabel("Coeff. Format:")
        self.lblQCoeff.setFont(bifont)
        self.lblQCoeff.setEnabled(enb_coeff)
        self.ledQICoeff = QtGui.QLineEdit()
        self.ledQICoeff.setToolTip(tipQI)
        self.ledQICoeff.setText("0")
        self.ledQICoeff.setMaxLength(2) # maximum of 2 digits
        self.ledQICoeff.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
        self.ledQICoeff.setEnabled(enb_coeff)

        self.ledQFCoeff = QtGui.QLineEdit()
        self.ledQFCoeff.setToolTip(tipQF)
        self.ledQFCoeff.setText("15")
        self.ledQFCoeff.setMaxLength(2) # maximum of 2 digits
#        self.ledQFCoeff.setFixedWidth(30) # width of lineedit in points(?)
        self.ledQFCoeff.setMaximumWidth(ledMaxWid)
        self.ledQFCoeff.setEnabled(enb_coeff)

        self.layHButtonsHDL_c = QtGui.QHBoxLayout()
        self.layHButtonsHDL_c.addWidget(self.lblQCoeff)
        self.layHButtonsHDL_c.addStretch()
        self.layHButtonsHDL_c.addWidget(self.ledQICoeff)
        self.layHButtonsHDL_c.addWidget(self.lblDot_c)
        self.layHButtonsHDL_c.addWidget(self.ledQFCoeff)
 

        self.lblQuant_c = QtGui.QLabel(lblQ)
        self.lblQuant_c.setEnabled(enb_coeff)
        self.cmbQuant_c = QtGui.QComboBox()
        self.cmbQuant_c.addItems(qQuant)
        self.cmbQuant_c.setToolTip(tipQuant)
        self.cmbQuant_c.setEnabled(enb_coeff)
        
        self.lblQOvfl_c = QtGui.QLabel(lblOv)
        self.lblQOvfl_c.setEnabled(enb_coeff)   
        self.cmbOvfl_c = QtGui.QComboBox()
        self.cmbOvfl_c.addItems(qOvfl)
        self.cmbOvfl_c.setToolTip(tipOvfl)
        self.cmbOvfl_c.setEnabled(enb_coeff)   

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant_c.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbOvfl_c.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.layHButtonsHDL_cc = QtGui.QHBoxLayout()
        self.layHButtonsHDL_cc.addWidget(self.lblQOvfl_c)            
        self.layHButtonsHDL_cc.addWidget(self.cmbOvfl_c)
        self.layHButtonsHDL_cc.addStretch()
        self.layHButtonsHDL_cc.addWidget(self.lblQuant_c)
        self.layHButtonsHDL_cc.addWidget(self.cmbQuant_c)
        self.layHButtonsHDL_cc.setEnabled(False)
# -----------------------------------------------------------------------------
        self.lblQAccu = QtGui.QLabel("Accumulator Format:")
        self.lblQAccu.setFont(bifont)
        self.ledQIAccu = QtGui.QLineEdit()
        self.ledQIAccu.setToolTip(tipQI)
        self.ledQIAccu.setText("0")
        self.ledQIAccu.setMaxLength(2) # maximum of 2 digits
        self.ledQIAccu.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.ledQFAccu = QtGui.QLineEdit()
        self.ledQFAccu.setToolTip(tipQF)
        self.ledQFAccu.setText("15")
        self.ledQFAccu.setMaxLength(2) # maximum of 2 digits
        self.ledQFAccu.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.layHButtonsHDL_a = QtGui.QHBoxLayout()
        self.layHButtonsHDL_a.addWidget(self.lblQAccu)
        self.layHButtonsHDL_a.addStretch()
        self.layHButtonsHDL_a.addWidget(self.ledQIAccu)
        self.layHButtonsHDL_a.addWidget(self.lblDot_a)
        self.layHButtonsHDL_a.addWidget(self.ledQFAccu)
# -------------------------------------------------------------------
        self.cmbQuant_a = QtGui.QComboBox()
        self.cmbQuant_a.addItems(qQuant)
        self.cmbQuant_a.setToolTip(tipQuant)
        self.cmbOvfl_a = QtGui.QComboBox()
        self.cmbOvfl_a.addItems(qOvfl)
        self.cmbOvfl_a.setToolTip(tipOvfl)

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant_a.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbOvfl_a.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.layHButtonsHDL_ac = QtGui.QHBoxLayout()
        self.layHButtonsHDL_ac.addWidget(self.lblQOvfl_a)            
        self.layHButtonsHDL_ac.addWidget(self.cmbOvfl_a)
        self.layHButtonsHDL_ac.addStretch()
        self.layHButtonsHDL_ac.addWidget(self.lblQuant_a)
        self.layHButtonsHDL_ac.addWidget(self.cmbQuant_a)

# -------------------------------------------------------------------

        enb_o_ui = False
        self.lblQOutput = QtGui.QLabel("Output Format:")
        self.lblQOutput.setFont(bifont)
        self.lblQOutput.setEnabled(enb_o_ui)
        self.ledQIOutput = QtGui.QLineEdit()
        self.ledQIOutput.setToolTip(tipQI)
        self.ledQIOutput.setText("0")
        self.ledQIOutput.setMaxLength(2) # maximum of 2 digits
        self.ledQIOutput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
        self.ledQIOutput.setEnabled(enb_o_ui)
        
        self.lblDot_o = QtGui.QLabel(".")
        self.lblDot_o.setEnabled(enb_o_ui)

        self.ledQFOutput = QtGui.QLineEdit()
        self.ledQFOutput.setToolTip(tipQF)
        self.ledQFOutput.setText("15")
        self.ledQFOutput.setMaxLength(2) # maximum of 2 digits
        self.ledQFOutput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
        self.ledQFOutput.setEnabled(enb_o_ui)

        self.layHButtonsHDL_o = QtGui.QHBoxLayout()
        self.layHButtonsHDL_o.addWidget(self.lblQOutput)
        self.layHButtonsHDL_o.addStretch()
        self.layHButtonsHDL_o.addWidget(self.ledQIOutput)
        self.layHButtonsHDL_o.addWidget(self.lblDot_o)
        self.layHButtonsHDL_o.addWidget(self.ledQFOutput)
# -------------------------------------------------------------------

        self.lblQOvfl_o = QtGui.QLabel(lblOv)
        self.lblQOvfl_o.setEnabled(enb_o_ui)
        self.lblQuant_o = QtGui.QLabel(lblQ)
        self.lblQuant_o.setEnabled(enb_o_ui)
        
        self.cmbQuant_o = QtGui.QComboBox()
        self.cmbQuant_o.addItems(qQuant)
        self.cmbQuant_o.setToolTip(tipQuant)
        self.cmbQuant_o.setEnabled(enb_o_ui)
        
        self.cmbOvfl_o = QtGui.QComboBox()
        self.cmbOvfl_o.addItems(qOvfl)
        self.cmbOvfl_o.setToolTip(tipOvfl)
        self.cmbOvfl_o.setEnabled(enb_o_ui)


        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant_o.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.cmbOvfl_o.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.layHButtonsHDL_oc = QtGui.QHBoxLayout()
        self.layHButtonsHDL_oc.addWidget(self.lblQOvfl_o)            
        self.layHButtonsHDL_oc.addWidget(self.cmbOvfl_o)
        self.layHButtonsHDL_oc.addStretch()
        self.layHButtonsHDL_oc.addWidget(self.lblQuant_o)
        self.layHButtonsHDL_oc.addWidget(self.cmbQuant_o)

        self.cmbHDL = QtGui.QComboBox()
        self.cmbHDL.addItems(['Verilog','VHDL'])
        self.cmbHDL.setToolTip("Select type of HDL for filter synthesis.")

        self.butExportHDL = QtGui.QPushButton()
        self.butExportHDL.setToolTip("Create VHDL and Verilog files.")
        self.butExportHDL.setText("Create HDL")
        
        self.butSimFixPoint = QtGui.QPushButton()
        self.butSimFixPoint.setToolTip("Simulate filter with fixpoint effects.")
        self.butSimFixPoint.setText("Simulate")

        
        self.layHButtonsHDL_h = QtGui.QHBoxLayout()
        self.layHButtonsHDL_h.addWidget(self.butSimFixPoint)            
        self.layHButtonsHDL_h.addWidget(self.butExportHDL)
# -------------------------------------------------------------------


        layVMain.addWidget(self.lblMyhdl1)
        layVMain.addWidget(self.HLine())
        layVMain.addWidget(self.lblMyhdl2)
        layVMain.addWidget(self.HLine())
        layVMain.addLayout(self.layHButtonsHDL_i)
        
        layVMain.addLayout(self.layHButtonsHDL_c)
        layVMain.addLayout(self.layHButtonsHDL_cc)
        
        layVMain.addLayout(self.layHButtonsHDL_a)
        layVMain.addLayout(self.layHButtonsHDL_ac)

        layVMain.addLayout(self.layHButtonsHDL_o)
        layVMain.addLayout(self.layHButtonsHDL_oc)
        
        layVMain.addLayout(self.layHButtonsHDL_h)
        
        layVMain.addStretch()
        

# -------------------------------------------------------------------
            
        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.butExportHDL.clicked.connect(self.exportHDL)
        self.butSimFixPoint.clicked.connect(self.simFixPoint)
        #----------------------------------------------------------------------


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
    def setupHDL(self):
        """
        Setup instance of myHDL object with word lengths and coefficients
        """

        qI_i = int(self.ledQIInput.text())
        qF_i = int(self.ledQFInput.text())
        
        qI_o = int(self.ledQIOutput.text())
        qF_o = int(self.ledQFOutput.text())
        
        qQuant_o = self.cmbQuant_o.currentText()
        qOvfl_o = self.cmbOvfl_o.currentText()
        
        q_obj_o =  {'QI':qI_o, 'QF': qF_o, 'quant': qQuant_o, 'ovfl': qOvfl_o}
        myQ_o = fix.Fixed(q_obj_o) # instantiate fixed-point object


        self.W = (qI_i + qF_i + 1, 0) # Matlab format: (W,WF)
        
        #       get filter coefficients etc. from filter dict    
        coeffs = fb.fil[0]['ba']
        zpk =  fb.fil[0]['zpk']
        sos = fb.fil[0]['sos']

        # =============== adapted from C. Feltons SIIR example =============
        self.flt = SIIR(W = self.W, b = np.array(coeffs[0][0:3]), 
                          a = np.array(coeffs[1][0:3]))

        
#------------------------------------------------------------------------------
    def exportHDL(self):
        """
        Synthesize HDL description of filter using myHDL module
        """
        # This does not work yet: file name is currently fixed to "siir_hdl" via the 
        # function with the same name
        dlg=QtGui.QFileDialog( self )
        
        file_types = "Verilog (*.v);;VHDL (*.vhd)"

        hdl_file, hdl_filter = dlg.getSaveFileNameAndFilter(self,
                caption = "Save HDL as", directory="D:",
                filter = file_types)
        hdl_file = str(hdl_file)
        hdl_filter = str(hdl_filter)
        logger.info('Creating hdl_file "%s"', hdl_file)
        hdl_filename = os.path.splitext(os.path.basename(hdl_file))[0]
        hdl_dirname = os.path.splitext(hdl_file)[0]
        logger.info('Using hdl_filename "%s"', hdl_filename)
        logger.info('Using hdl_dirname "%s"', hdl_dirname)

        self.setupHDL()
        self.flt.hdl_name = hdl_filename
        self.flt.hdl_directory = hdl_dirname
        self.flt.hdl_target = 'verilog' # or 'vhdl'
        self.flt.Convert()
        logger.info("HDL conversion finished!")

#------------------------------------------------------------------------------
    def simFixPoint(self):
        """
        Simulate filter in fix-point description
        """
        # Setup the Testbench and run
        self.setupHDL()
        logger.info("Fixpoint simulation called")
        tb = self.flt.TestFreqResponse(Nloops=3, Nfft=1024)
        clk = Signal(False)
        ts  = Signal(False)
        x   = Signal(intbv(0,min=-2**(self.W[0]-1), max=2**(self.W[0]-1)))
        y   = Signal(intbv(0,min=-2**(self.W[0]-1), max=2**(self.W[0]-1)))

        sim = Simulation(tb)
        logger.info("Fixpoint simulation started")
        sim.run()
        logger.info("Fixpoint plotting started")
        self.flt.PlotResponse()
        logger.info("Fixpoint plotting finished")

#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = HDLSpecs()
    form.show()

    app.exec_()