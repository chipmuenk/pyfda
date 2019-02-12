# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for plotting the group delay
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

from ..compat import QCheckBox, QWidget, QFrame, QHBoxLayout, pyqtSignal, pyqtSlot

import numpy as np

import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
from scipy.signal import group_delay
#from pyfda.pyfda_lib import group_delay
from pyfda.plot_widgets.mpl_widget import MplWidget

# TODO: Anticausal filter have no group delay. But is a filter with
#       'baA' always anticausal or maybe just acausal?

class Plot_Tau_G(QWidget):
    """
    Widget for plotting the group delay
    """
    # incoming, connected in sender widget (locally connected to self.process_signals() )
    sig_rx = pyqtSignal(object)
#    sig_tx = pyqtSignal(object) # outgoing from process_signals


    def __init__(self, parent):
        super(Plot_Tau_G, self).__init__(parent)
        self.verbose = True # suppress warnings
        self.needs_draw = True   # flag whether plot needs to be updated
        self.needs_redraw = True # flag whether plot needs to be redrawn
        self.tool_tip = "Group delay"
        self.tab_label = "tau_g"
        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements (currently commented out)
        """

# =============================================================================
# #### not needed at the moment ###
#        self.chkWarnings = QCheckBox("Enable Warnings", self)
#        self.chkWarnings.setChecked(False)
#        self.chkWarnings.setToolTip("Print warnings about singular group delay")
#
#        self.chkScipy = QCheckBox("Scipy", self)
#        self.chkScipy.setChecked(False)
#        self.chkScipy.setToolTip("Use scipy group delay routine")
#    
#        layHControls = QHBoxLayout()
#        layHControls.addStretch(10)
#        layHControls.addWidget(self.chkWarnings)
#        layHControls.addWidget(self.chkScipy)
#    
#        # This widget encompasses all control subwidgets:
#        self.frmControls = QFrame(self)
#        self.frmControls.setObjectName("frmControls")
#        self.frmControls.setLayout(layHControls)
# =============================================================================
        self.mplwidget = MplWidget(self)
        #self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.setLayout(self.mplwidget.layVMainMpl)

        self.init_axes()
        self.draw() # initial drawing of tau_g

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_signals)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.mplwidget.mplToolbar.sig_tx.connect(self.process_signals)

#------------------------------------------------------------------------------
    def process_signals(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        logger.debug("Processing {0} | needs_draw = {1}, visible = {2}"\
                     .format(dict_sig, self.needs_draw, self.isVisible()))
        if self.isVisible():
            if 'data_changed' in dict_sig or 'home' in dict_sig or self.needs_draw:
                self.draw()
                self.needs_draw = False
                self.needs_redraw = False
            elif 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized'\
                    or self.needs_redraw:
                self.redraw()
                self.needs_redraw = False
            elif 'view_changed' in dict_sig:
                self.update_view()
        else:
            if 'data_changed' in dict_sig or 'view_changed' in dict_sig:
                self.needs_draw = True
            elif 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized':
                self.needs_redraw = True

#------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes
        """
        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()
        self.ax.get_xaxis().tick_bottom() # remove axis ticks on top
        self.ax.get_yaxis().tick_left() # remove axis ticks right

#------------------------------------------------------------------------------
    def calc_tau_g(self):
        """
        (Re-)Calculate the complex frequency response H(f)
        """
        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        # calculate H_cmplx(W) (complex) for W = 0 ... 2 pi:
        self.W, self.tau_g = group_delay((bb, aa), w=params['N_FFT'], whole = True)
            #verbose = self.verbose) # self.chkWarnings.isChecked())

        # Zero phase filters have no group delay (Causal+AntiCausal)
        if 'baA' in fb.fil[0]:
           self.tau_g = np.zeros(self.tau_g.size)


#------------------------------------------------------------------------------
    def draw(self):
        self.calc_tau_g()
        self.update_view()

#------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """
        #========= select frequency range to be displayed =====================
        #=== shift, scale and select: W -> F, H_cplx -> H_c
        f_S2 = fb.fil[0]['f_S'] / 2.
        F = self.W * f_S2 / np.pi

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            # shift tau_g and F by f_S/2
            tau_g = np.fft.fftshift(self.tau_g)
            F -= f_S2
        elif fb.fil[0]['freqSpecsRangeType'] == 'half':
            # only use the first half of H and F
            tau_g = self.tau_g[0:params['N_FFT']//2]
            F = F[0:params['N_FFT']//2]
        else: # fb.fil[0]['freqSpecsRangeType'] == 'whole'
            # use H and F as calculated
            tau_g = self.tau_g

        #================ Main Plotting Routine =========================
        #===  clear the axes and (re)draw the plot

        if fb.fil[0]['freq_specs_unit'] in {'f_S', 'f_Ny'}:
            tau_str = r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $'
        else:
            tau_str = r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega})$'\
                + ' in ' + fb.fil[0]['plt_tUnit'] + r' $ \rightarrow $'
            tau_g = tau_g / fb.fil[0]['f_S']

        #---------------------------------------------------------
        self.ax.clear() # need to clear, doesn't overwrite
        line_tau_g, = self.ax.plot(F, tau_g, label = "Group Delay")
        #---------------------------------------------------------

        self.ax.set_title(r'Group Delay $ \tau_g$')
        self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax.set_ylabel(tau_str)
        # widen y-limits to suppress numerical inaccuracies when tau_g = constant
        self.ax.set_ylim([max(min(tau_g)-0.5,0), max(tau_g) + 0.5])
        self.ax.set_xlim(fb.fil[0]['freqSpecsRange'])

        self.redraw()

#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    import sys
    from ..compat import QApplication
    app = QApplication(sys.argv)
    mainw = Plot_Tau_G(None)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
