# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with classes and functions for file and text IO
"""
import logging
logger = logging.getLogger(__name__)

import numpy as np

#from pyfda.pyfda_lib import safe_eval
from pyfda.pyfda_qt_lib import qget_selected, qget_cmb_box, qset_cmb_box
from pyfda.pyfda_rc import params
from pyfda.plot_widgets.mpl_widget import MplWidget
#import pyfda.pyfda_dirs as dirs
import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

from pyfda.compat import (QWidget, QFrame, QLabel, pyqtSignal,
                     QCheckBox, QComboBox, QPushButton, QRadioButton,
                     QHBoxLayout, QVBoxLayout)
#------------------------------------------------------------------------------
class Plot_FFT_win(QWidget):
    """
    Create a pop-up widget for displaying time and frequency view of an FFT 
    window.
    """
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)


    def __init__(self, parent):
        super(Plot_FFT_win, self).__init__(parent)
        self._construct_UI()

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        logger.debug("Processing {0} | needs_calc = {1}, visible = {2}"\
                     .format(dict_sig, self.needs_calc, self.isVisible()))
        if self.isVisible():
            if 'data_changed' in dict_sig or 'home' in dict_sig or self.needs_calc:
                self.draw()
                self.needs_calc = False
                self.needs_draw = False               
            elif 'view_changed' in dict_sig or self.needs_draw:
                self.update_view()
                self.needs_draw = False                
            elif ('ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized')\
                or self.needs_redraw:
                self.redraw()
        else:
            if 'data_changed' in dict_sig:
                self.needs_calc = True
            elif 'view_changed' in dict_sig:
                self.needs_draw = True 
            elif 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized':
                self.needs_redraw = True

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """

        self.cmbUnitsPhi = QComboBox(self)
        units = ["rad", "rad/pi",  "deg"]
        scales = [1.,   1./ np.pi, 180./np.pi]
        for unit, scale in zip(units, scales):
            self.cmbUnitsPhi.addItem(unit, scale)
        self.cmbUnitsPhi.setObjectName("cmbUnitsA")
        self.cmbUnitsPhi.setToolTip("Set unit for phase.")
        self.cmbUnitsPhi.setCurrentIndex(0)
        self.cmbUnitsPhi.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.chkWrap = QCheckBox("Wrapped Phase", self)
        self.chkWrap.setChecked(False)
        self.chkWrap.setToolTip("Plot phase wrapped to +/- pi")

        layHControls = QHBoxLayout()
        layHControls.addWidget(self.cmbUnitsPhi)
        layHControls.addWidget(self.chkWrap)
        layHControls.addStretch(10)

        #----------------------------------------------------------------------
        #               ### frmControls ###
        #
        # This widget encompasses all control subwidgets
        #----------------------------------------------------------------------
        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)

        #----------------------------------------------------------------------
        #               ### mplwidget ###
        #
        # main widget, encompassing the other widgets
        #----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.setLayout(self.mplwidget.layVMainMpl)

        self.init_axes()

        self.draw() # initial drawing

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.chkWrap.clicked.connect(self.draw)
        self.cmbUnitsPhi.currentIndexChanged.connect(self.draw)
        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)

#------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes - this is only called once
        """
        if len(self.mplwidget.fig.get_axes()) == 0: # empty figure, no axes
            self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.get_xaxis().tick_bottom() # remove axis ticks on top
        self.ax.get_yaxis().tick_left() # remove axis ticks right

#------------------------------------------------------------------------------
    def calc_resp(self):
        """
        (Re-)Calculate the FFT window, only dummy data at the moment
        """
        # calculate H_cplx(W) (complex) for W = 0 ... 2 pi:
        self.W = np.arange(params['N_FFT'])
        self.H_cmplx = np.random.randn(params['N_FFT'])
        # replace nan and inf by finite values, otherwise np.unwrap yields
        # an array full of nans

#------------------------------------------------------------------------------
    def draw(self):
        """
        Main entry point:
        Re-calculate \|H(f)\| and draw the figure
        """
        self.calc_resp()
        self.update_view()

#------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """

        self.unitPhi = qget_cmb_box(self.cmbUnitsPhi, data=False)

        f_S2 = fb.fil[0]['f_S'] / 2.

        #========= select frequency range to be displayed =====================
        #=== shift, scale and select: W -> F, H_cplx -> H_c
        F = self.W * f_S2 / np.pi

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            # shift H and F by f_S/2
            H = np.fft.fftshift(self.H_cmplx)
            F -= f_S2
        elif fb.fil[0]['freqSpecsRangeType'] == 'half':
            # only use the first half of H and F
            H = self.H_cmplx[0:params['N_FFT']//2]
            F = F[0:params['N_FFT']//2]
        else: # fb.fil[0]['freqSpecsRangeType'] == 'whole'
            # use H and F as calculated
            H = self.H_cmplx

        y_str = r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$ in '
        if self.unitPhi == 'rad':
            y_str += 'rad ' + r'$\rightarrow $'
            scale = 1.
        elif self.unitPhi == 'rad/pi':
            y_str += 'rad' + r'$ / \pi \;\rightarrow $'
            scale = 1./ np.pi
        else:
            y_str += 'deg ' + r'$\rightarrow $'
            scale = 180./np.pi
        fb.fil[0]['plt_phiLabel'] = y_str
        fb.fil[0]['plt_phiUnit'] = self.unitPhi

        if self.chkWrap.isChecked():
            phi_plt = np.angle(H) * scale
        else:
            phi_plt = np.unwrap(np.angle(H)) * scale

        #---------------------------------------------------------
        self.ax.clear() # need to clear, doesn't overwrite
        line_phi, = self.ax.plot(F, phi_plt)
        #---------------------------------------------------------

        self.ax.set_title(r'Phase Frequency Response')
        self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax.set_ylabel(y_str)
        self.ax.set_xlim(fb.fil[0]['freqSpecsRange'])

        self.redraw()

#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

#==============================================================================

if __name__=='__main__':
    pass
