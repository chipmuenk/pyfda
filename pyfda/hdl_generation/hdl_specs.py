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
from pyfda.pyfda_lib import HLine, extract_file_ext
#import pyfda.pyfda_rc as rc

from pyfda.hdl_generation.filter_iir import FilterIIR #  second order IIR filter object
#from pyfda.hdl_generation.filter_iir import SIIR #  second order IIR filter object


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

        self.lblMyhdl1 = QLabel("Warning! This feature is only experimental, "
        "only HDL code for second order IIR filters under the name siir_hdl.v "
        " resp. siir_hdl.vhd are created at the moment. Files are saved "
        " in the pyFDA root directory.", self)
        self.lblMyhdl1.setWordWrap(True)
#        self.lblMyhdl1.setFont(bfont)
        self.lblMyhdl2 = QLabel("Enter fixpoint signal formats as QI.QF:", self)

        ledMaxWid = 30 # Max. Width of QLineEdit fields
        qQuant = ['none', 'round', 'fix', 'floor']
        qOvfl = ['none', 'wrap', 'sat']
        tipOvfl = "Select overflow behaviour."
        tipQuant = "Select the kind of quantization."
        tipQI = "Specify number of integer bits."
        tipQF = "Specify number of fractional bits."
        lblQ = "Quant.:"
        lblOv = "Ovfl.:"

# -------------------------------------------------------------------
# UI for input format 
# -------------------------------------------------------------------
        self.lblQInput = QLabel("Input Format:", self)
        self.lblQInput.setFont(bifont)
        self.ledQIInput = QLineEdit(self)
        self.ledQIInput.setToolTip(tipQI)
        self.ledQIInput.setText("0")
        self.ledQIInput.setMaxLength(2) # maximum of 2 digits
        self.ledQIInput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.lblDotInput = QLabel(".", self)
        
        self.ledQFInput = QLineEdit(self)
        self.ledQFInput.setToolTip(tipQF)
        self.ledQFInput.setText("15")
        self.ledQFInput.setMaxLength(2) # maximum of 2 digits
        self.ledQFInput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.layHButtonsHDL_i = QHBoxLayout()
        self.layHButtonsHDL_i.addWidget(self.lblQInput)
        self.layHButtonsHDL_i.addStretch()
        self.layHButtonsHDL_i.addWidget(self.ledQIInput)
        self.layHButtonsHDL_i.addWidget(self.lblDotInput)
        self.layHButtonsHDL_i.addWidget(self.ledQFInput)
        
# -------------------------------------------------------------------
# UI for coefficient format 
# -------------------------------------------------------------------
        enb_coeff = False
        self.lblQCoeff = QLabel("Coeff. Format:", self)
        self.lblQCoeff.setFont(bifont)
        self.lblQCoeff.setEnabled(enb_coeff)
        self.ledQICoeff = QLineEdit(self)
        self.ledQICoeff.setToolTip(tipQI)
        self.ledQICoeff.setText("0")
        self.ledQICoeff.setMaxLength(2) # maximum of 2 digits
        self.ledQICoeff.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
        self.ledQICoeff.setEnabled(enb_coeff)

        self.lblDotCoeff = QLabel(".", self)
        
        self.ledQFCoeff = QLineEdit(self)
        self.ledQFCoeff.setToolTip(tipQF)
        self.ledQFCoeff.setText("15")
        self.ledQFCoeff.setMaxLength(2) # maximum of 2 digits
#        self.ledQFCoeff.setFixedWidth(30) # width of lineedit in points(?)
        self.ledQFCoeff.setMaximumWidth(ledMaxWid)
        self.ledQFCoeff.setEnabled(enb_coeff)

        self.layHButtonsHDL_c = QHBoxLayout()
        self.layHButtonsHDL_c.addWidget(self.lblQCoeff)
        self.layHButtonsHDL_c.addStretch()
        self.layHButtonsHDL_c.addWidget(self.ledQICoeff)
        self.layHButtonsHDL_c.addWidget(self.lblDotCoeff)
        self.layHButtonsHDL_c.addWidget(self.ledQFCoeff)
 

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
        
# -------------------------------------------------------------------
# UI for accumulator format / overflow behaviour
# -------------------------------------------------------------------
        # ---------- Accumulator format --------------
        self.lblQAccu = QLabel("Accumulator Format:", self)
        self.lblQAccu.setFont(bifont)
        self.ledQIAccu = QLineEdit(self)
        self.ledQIAccu.setToolTip(tipQI)
        self.ledQIAccu.setText("0")
        self.ledQIAccu.setMaxLength(2) # maximum of 2 digits
        self.ledQIAccu.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.lblDotAccu = QLabel(".", self)
        
        self.ledQFAccu = QLineEdit(self)
        self.ledQFAccu.setToolTip(tipQF)
        self.ledQFAccu.setText("15")
        self.ledQFAccu.setMaxLength(2) # maximum of 2 digits
        self.ledQFAccu.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

        self.layHButtonsHDL_a = QHBoxLayout()
        self.layHButtonsHDL_a.addWidget(self.lblQAccu)
        self.layHButtonsHDL_a.addStretch()
        self.layHButtonsHDL_a.addWidget(self.ledQIAccu)
        self.layHButtonsHDL_a.addWidget(self.lblDotAccu)
        self.layHButtonsHDL_a.addWidget(self.ledQFAccu)

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

# -------------------------------------------------------------------
# UI for output format and overflow behaviour
# -------------------------------------------------------------------
        # ---------- Output format --------------
        enb_o_ui = False
        self.lblQOutput = QLabel("Output Format:", self)
        self.lblQOutput.setFont(bifont)
#        self.lblQOutput.setEnabled(enb_o_ui)
        self.ledQIOutput = QLineEdit(self)
        self.ledQIOutput.setToolTip(tipQI)
        self.ledQIOutput.setText("0")
        self.ledQIOutput.setMaxLength(2) # maximum of 2 digits
        self.ledQIOutput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
#        self.ledQIOutput.setEnabled(enb_o_ui)
        
        self.lblDot_o = QLabel(".", self)
#        self.lblDot_o.setEnabled(enb_o_ui)

        self.ledQFOutput = QLineEdit(self)
        self.ledQFOutput.setToolTip(tipQF)
        self.ledQFOutput.setText("15")
        self.ledQFOutput.setMaxLength(2) # maximum of 2 digits
        self.ledQFOutput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
#        self.ledQFOutput.setEnabled(enb_o_ui)

        self.layHButtonsHDL_o = QHBoxLayout()
        self.layHButtonsHDL_o.addWidget(self.lblQOutput)
        self.layHButtonsHDL_o.addStretch()
        self.layHButtonsHDL_o.addWidget(self.ledQIOutput)
        self.layHButtonsHDL_o.addWidget(self.lblDot_o)
        self.layHButtonsHDL_o.addWidget(self.ledQFOutput)
        # This doesn't work - need to set a parent widget like QFrame
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

        layVMain = QVBoxLayout()
        
        layVMain.addWidget(self.lblMyhdl1)
        layVMain.addWidget(HLine(QFrame, self))
        layVMain.addWidget(self.lblMyhdl2)
        layVMain.addWidget(HLine(QFrame, self))
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

        qI_i = int(self.ledQIInput.text())
        qF_i = int(self.ledQFInput.text())
        
        qI_o = int(self.ledQIOutput.text())
        qF_o = int(self.ledQFOutput.text())
        
        qQuant_o = self.cmbQuant_o.currentText()
        qOvfl_o = self.cmbOvfl_o.currentText()
        
        q_obj_o =  {'QI':qI_o, 'QF': qF_o, 'quant': qQuant_o, 'ovfl': qOvfl_o}
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
                             word_format=(self.W[0], 0, self.W[1]))

        self.flt.hdl_name = file_name
        self.flt.hdl_directory = dir_name
        
#------------------------------------------------------------------------------
    def exportHDL(self):
        """
        Synthesize HDL description of filter using myHDL module
        """
        # Passing the file name doesn't work yet, itis currently fixed to 
        # "siir_hdl" via the function with the same name
        dlg = QFD(self)
        
        file_types = "Verilog (*.v);;VHDL (*.vhd)"

        hdl_file, hdl_filter = dlg.getSaveFileName_(
                caption = "Save HDL as", directory="D:",
                filter = file_types)
        hdl_file = str(hdl_file)
        
        if not os.path.isdir(hdl_dir_name): # create directory if it doesn't exist
            os.mkdir(hdl_dir_name)
        # return the filename without suffix
        hdl_file_name = os.path.splitext(os.path.basename(hdl_file))[0]
        hdl_dir_name = os.path.splitext(hdl_file)[0]
        logger.info('Using hdl_filename "%s"', hdl_file_name)
        logger.info('Using hdl_dirname "%s"', hdl_dir_name)

        self.setupHDL(file_name = hdl_file_name, dir_name = hdl_dir_name)
        
        print('target:', self.flt.hdl_target)
        if str(hdl_filter) == '.vhd':
            self.flt.hdl_target = 'vhdl'
        else:
            self.flt.hdl_target = 'verilog'
            
        logger.info('Creating hdl_file "{0}" of type "{1}"'.format(hdl_file, self.flt.hdl_target))

        self.flt.convert() # was Convert()
        logger.info("HDL conversion finished!")

#------------------------------------------------------------------------------
    def simFixPoint(self):
        """
        Simulate filter in fix-point description
        """
        # Setup the Testbench and run

        # Passing the file name doesn't work yet, itis currently fixed to 
        # "siir_hdl" via the function with the same name
        dlg = QFD(self)
        
        plt_types = "png (*.png);;svg (*.svg)"

        plt_file, plt_type = dlg.getSaveFileName_(
                caption = "Save plots as", directory="D:",
                filter = plt_types)
        plt_file = str(plt_file)
        plt_type = str(plt_type)
        logger.info('Using plot filename "%s"', plt_file)
        plot_file_name = os.path.splitext(os.path.basename(plt_file))[0]
        plot_dir_name = os.path.splitext(plt_file)[0]
        logger.info('Using plot filename "%s"', plot_file_name)
        logger.info('Using plot directory "%s"', plot_dir_name)

#        self.flt.plt_type = plt_type
#        self.flt.plt_file = plt_file

        self.setupHDL(file_name = plot_file_name, dir_name = plot_dir_name)
        if not os.path.isdir(plt_dir_name): # create directory if it doesn't exist
            os.mkdir(plt_dir_name)        
        logger.info('Using plot filename "%s"', plt_file_name)

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