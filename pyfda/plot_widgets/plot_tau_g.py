# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import


from ..compat import QCheckBox, QWidget, QFrame, QHBoxLayout

import numpy as np

import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
from pyfda.pyfda_lib import grpdelay
from pyfda.plot_widgets.plot_utils import MplWidget


class PlotTauG(QWidget):

    def __init__(self, parent):
        super(PlotTauG, self).__init__(parent)


        self.chkWarnings = QCheckBox("Enable Warnings", self)
        self.chkWarnings.setChecked(False)
        self.chkWarnings.setToolTip("Print warnings about singular group delay")

        layHControls = QHBoxLayout()
        layHControls.addStretch(10)
        layHControls.addWidget(self.chkWarnings)
        
        # This widget encompasses all control subwidgets:
        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)

        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.setLayout(self.mplwidget.layVMainMpl)
        
        self.ax = self.mplwidget.fig.add_subplot(111)
        
        self.draw() # initial drawing of tau_g

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.chkWarnings.clicked.connect(self.draw)
        
#------------------------------------------------------------------------------
    def draw(self):
        self.frmControls.setEnabled(self.mplwidget.mplToolbar.enabled)
        if self.mplwidget.mplToolbar.enabled:
            self.draw_taug()
            
#------------------------------------------------------------------------------
    def update_view(self):
        """
        Update frequency range etc. without recalculating group delay.
        """
        self.draw()

#------------------------------------------------------------------------------
    def draw_taug(self):
        """
        Draw group delay
        """
        self.ax.clear()
        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']

        [w, tau_g] = grpdelay(bb,aa, params['N_FFT'], whole = wholeF, 
            verbose = self.chkWarnings.isChecked())

        F = w / (2 * np.pi) * fb.fil[0]['f_S']

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            tau_g = np.fft.fftshift(tau_g)
            F = F - f_S / 2.
            
        if fb.fil[0]['freq_specs_unit'] in {'f_S', 'f_Ny'}:
            tau_str = r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $'
        else:
            tau_str = r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega})$'\
                + ' in ' + fb.fil[0]['plt_tUnit'] + r' $ \rightarrow $'
            tau_g = tau_g / fb.fil[0]['f_S']


        #---------------------------------------------------------
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
    mainw = PlotTauG(None)
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
