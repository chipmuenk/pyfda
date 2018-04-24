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

from ..compat import (Qt, QWidget, QLabel, QLineEdit, QComboBox, QFont,
                      QPushButton, QFD, QSplitter,
                      QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, QPixmap)
import numpy as np

#from myhdl import (toVerilog, toVHDL, Signal, always, always_comb, delay,
#               instance, instances, intbv, traceSignals,
#               Simulation, StopSimulation)
import myhdl


import pyfda.filterbroker as fb # importing filterbroker initializes all its globals
import pyfda.filter_factory as ff
import pyfda.pyfda_fix_lib as fix
import pyfda.pyfda_dirs as dirs
from pyfda.pyfda_io_lib import extract_file_ext
from pyfda.pyfda_qt_lib import qstr
from pyfda.pyfda_rc import params
from pyfda.pyfda_lib import safe_eval, to_html

from pyfda.hdl_generation.filter_iir import FilterIIR # IIR filter object


# see C. Feltons "FPGA IIR Lowpass Direct Form I Filter Generator"
#                 @ http://www.dsprelated.com/showcode/211.php


#------------------------------------------------------------------------------

class UI_WI_WF(QWidget):
    """
    Widget for entering integer and fractional bits. The result can be read out
    via the attributes `self.WI` and `self.WF`.
    """

    def __init__(self, parent, **kwargs):
        super(UI_WI_WF, self).__init__(parent)
        self._construct_UI(**kwargs)

    def _construct_UI(self, **kwargs):
        """ Construct widget """

        dict_ui = {'label':'WI.WF', 'max_led_width':30,
                   'WI':0, 'WI_len':2, 'tip_WI':'Number of integer bits',
                   'WF':15,'WF_len':2, 'tip_WF':'Number of fractional bits'
                   }
        for key, val in kwargs.items():
            dict_ui.update({key:val})
        # dict_ui.update(map(kwargs)) # same as above?
        self.WI = dict_ui['WI']
        self.WF = dict_ui['WF']

        lblW = QLabel(to_html(dict_ui['label'], frmt='bi'), self)
        self.ledWI = QLineEdit(self)
        self.ledWI.setToolTip(dict_ui['tip_WI'])
        self.ledWI.setText(qstr(dict_ui['WI']))
        self.ledWI.setMaxLength(dict_ui['WI_len']) # maximum of 2 digits
        self.ledWI.setFixedWidth(dict_ui['max_led_width']) # width of lineedit in points(?)

        lblDot = QLabel(".", self)

        self.ledWF = QLineEdit(self)
        self.ledWF.setToolTip(dict_ui['tip_WF'])
        self.ledWF.setText(qstr(dict_ui['WF']))
        self.ledWF.setMaxLength(dict_ui['WI_len']) # maximum of 2 digits
        self.ledWF.setFixedWidth(dict_ui['max_led_width']) # width of lineedit in points(?)

        layH = QHBoxLayout()
        layH.addWidget(lblW)
        layH.addStretch()
        layH.addWidget(self.ledWI)
        layH.addWidget(lblDot)
        layH.addWidget(self.ledWF)
        layH.setContentsMargins(0,0,0,0)

        frmMain = QFrame(self)
        frmMain.setLayout(layH)

        layVMain = QVBoxLayout() # Widget main layout
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(0,5,0,0)#*params['wdg_margins'])

        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.ledWI.editingFinished.connect(self._update_ui)
        self.ledWF.editingFinished.connect(self._update_ui)

    #--------------------------------------------------------------------------
    def _update_ui(self):
        """ Update the attributes `self.WI` and `self.WF` """
        self.WI = safe_eval(self.ledWI.text(), self.WI, return_type="int", sign='pos')
        self.ledWI.setText(qstr(self.WI))
        self.WF = safe_eval(self.ledWF.text(), self.WF, return_type="int", sign='pos')
        self.ledWF.setText(qstr(self.WF))

#==============================================================================

class UI_Q_Ovfl(QWidget):
    """
    Widget for selecting quantization / overflow options. The result can be read out
    via the attributes `self.x` and `self.y`.
    """

    def __init__(self, parent, **kwargs):
        super(UI_Q_Ovfl, self).__init__(parent)
        self._construct_UI(**kwargs)

    def _construct_UI(self, **kwargs):
        """ Construct widget """

        dict_ui = {'label_q':'Quant.', 'tip_q':'Select the kind of quantization.',
                   'cmb_q':['none', 'round', 'fix', 'floor'],
                   'label_ov':'Ovfl.', 'tip_ov':'Select overflow behaviour.',
                   'cmb_ov': ['none', 'wrap', 'sat']
                   }
        for key, val in kwargs.items():
            dict_ui.update({key:val})
        # dict_ui.update(map(kwargs)) # same as above?

        lblQuant = QLabel(dict_ui['label_q'], self)
        self.cmbQuant = QComboBox(self)
        self.cmbQuant.addItems(dict_ui['cmb_q'])
        self.cmbQuant.setToolTip(dict_ui['tip_q'])

        lblOvfl = QLabel(dict_ui['label_ov'], self)
        self.cmbOvfl = QComboBox(self)
        self.cmbOvfl.addItems(dict_ui['cmb_ov'])
        self.cmbOvfl.setToolTip(dict_ui['tip_ov'])

        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layH = QHBoxLayout()
        layH.addWidget(lblOvfl)
        layH.addWidget(self.cmbOvfl)
        layH.addStretch()
        layH.addWidget(lblQuant)
        layH.addWidget(self.cmbQuant)
        layH.setContentsMargins(0,0,0,0)

        frmMain = QFrame(self)
        frmMain.setLayout(layH)

        layVMain = QVBoxLayout() # Widget main layout
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(5,0,0,0)#*params['wdg_margins'])

        self.setLayout(layVMain)

        # initial settings:
        self.ovfl = self.cmbOvfl.currentText()
        self.quant = self.cmbQuant.currentText()

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.cmbOvfl.currentIndexChanged.connect(self._update_ui)
        self.cmbQuant.currentIndexChanged.connect(self._update_ui)

    #--------------------------------------------------------------------------
    def _update_ui(self):
        """ Update the attributes `self.ovfl` and `self.quant` """
        self.ovfl = self.cmbOvfl.currentText()
        self.quant = self.cmbQuant.currentText()

#==============================================================================


class HDLSpecs(QWidget):
    """
    Create the widget for entering exporting / importing / saving / loading data
    """
    def __init__(self, parent):
        super(HDLSpecs, self).__init__(parent)

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the main GUI, consisting of:
        """
        # ============== UI Layout =====================================
        bfont = QFont()
        bfont.setBold(True)

        bifont = QFont()
        bifont.setBold(True)
        bifont.setItalic(True)

        ifont = QFont()
        ifont.setItalic(True)

        lblMsg = QLabel("<b>Direct-Form 1 (DF1) Filters</b><br />"
                        "Simple filters", self)
        lblMsg.setWordWrap(True)
        layHMsg = QHBoxLayout()
        layHMsg.addWidget(lblMsg)

        self.frmMsg = QFrame(self)
        self.frmMsg.setLayout(layHMsg)
        self.frmMsg.setContentsMargins(*params['wdg_margins'])

        self.lbl_img_hdl = QLabel(self)
        file_path = os.path.dirname(os.path.realpath(__file__))
        img_file = os.path.join(file_path, "hdl-df1.png")
        img_hdl = QPixmap(img_file)
        img_hdl_scaled = img_hdl.scaled(self.lbl_img_hdl.size(), Qt.KeepAspectRatio)
        # self.lbl_img_hdl.setPixmap(QPixmap(img_hdl_scaled))
        self.lbl_img_hdl.setPixmap(QPixmap(img_hdl)) # fixed size

        layHImg = QHBoxLayout()
        layHImg.addWidget(self.lbl_img_hdl)
        self.frmImg = QFrame(self)
        self.frmImg.setLayout(layHImg)
        self.frmImg.setContentsMargins(*params['wdg_margins'])

# =============================================================================
# UI for quantization
# =============================================================================

        lblHBtnsMsg = QLabel("Fixpoint signal / coeff. formats as WI.WF:", self)
        lblHBtnsMsg.setFont(bfont)
        self.layHBtnsMsg = QHBoxLayout()
        self.layHBtnsMsg.addWidget(lblHBtnsMsg)

        self.wdg_wi_wf_input = UI_WI_WF(self, label='Input Format x[n]:')
        self.wdg_wi_wf_coeffs = UI_WI_WF(self, label='Coefficient Format:')
        self.wdg_q_ovfl_coeffs = UI_Q_Ovfl(self)
        self.wdg_wi_wf_accu = UI_WI_WF(self, label='Accumulator Format:', WF=30)
        self.wdg_q_ovfl_accu = UI_Q_Ovfl(self)
        self.wdg_wi_wf_output = UI_WI_WF(self, label='Output Format y[n]:')
        self.wdg_q_ovfl_output = UI_Q_Ovfl(self)

#------------------------------------------------------------------------------
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
        layVBtns.addWidget(self.wdg_wi_wf_input)
        layVBtns.addWidget(self.wdg_wi_wf_coeffs)
        self.wdg_wi_wf_coeffs.setEnabled(False)
        layVBtns.addWidget(self.wdg_q_ovfl_coeffs)
        self.wdg_q_ovfl_coeffs.setEnabled(False)

        layVBtns.addWidget(self.wdg_wi_wf_accu)
        layVBtns.addWidget(self.wdg_q_ovfl_accu)

        layVBtns.addWidget(self.wdg_wi_wf_output)
        layVBtns.addWidget(self.wdg_q_ovfl_output)

        layVBtns.addLayout(self.layHButtonsHDL_h)

        layVBtns.addStretch()

        # -------------------------------------------------------------------
        # This frame encompasses all the buttons
        frmBtns = QFrame(self)
        frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmBtns.setLayout(layVBtns)

    # -------------------------------------------------------------------
    # Top level layout
    # -------------------------------------------------------------------
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(self.frmMsg)
        splitter.addWidget(self.frmImg)
        splitter.addWidget(frmBtns)
        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([1000,3000,10000])


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
        self.butExportHDL.clicked.connect(self.exportHDL)
        self.butSimFixPoint.clicked.connect(self.simFixPoint)
        #----------------------------------------------------------------------
        self.update_UI()

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

	# imports from one level above when run as __main__ :
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))


    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = HDLSpecs(None)
    mainw.show()

    app.exec_()