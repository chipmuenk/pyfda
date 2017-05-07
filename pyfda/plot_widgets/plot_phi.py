# -*- coding: utf-8 -*-
"""
Widget for plotting phase frequency response phi(f)

Author: Christian Muenker 2015
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from ..compat import QCheckBox, QWidget, QComboBox, QHBoxLayout, QFrame


import numpy as np
import scipy.signal as sig

import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
from pyfda.plot_widgets.plot_utils import MplWidget


class PlotPhi(QWidget):

    def __init__(self, parent):
        super(PlotPhi, self).__init__(parent)

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
#        layHControls.addStretch(10)
        layHControls.addWidget(self.cmbUnitsPhi)
        layHControls.addWidget(self.chkWrap)
        layHControls.addStretch(10)
        
        # This widget encompasses all control subwidgets:
        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)


        #----------------------------------------------------------------------
        # mplwidget
        #----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.setLayout(self.mplwidget.layVMainMpl)
        
        self.ax = self.mplwidget.fig.add_subplot(111)

        self.draw() # initial drawing

#        #=============================================
#        # Signals & Slots
#        #=============================================
        self.chkWrap.clicked.connect(self.draw)
        self.cmbUnitsPhi.currentIndexChanged.connect(self.draw)
        
        
    def update_view(self):
        """
        place holder; should update only the limits without recalculating
        the phase
        """
        self.draw()

    def draw(self):
        """
        main entry point for drawing the phase
        """
        self.frmControls.setEnabled(self.mplwidget.mplToolbar.enabled)
        if self.mplwidget.mplToolbar.enabled:
            self.draw_phi()

    def draw_phi(self):
        """
        Re-calculate phi(f) and draw the figure
        """
        self.ax.clear()
        self.unitPhi = self.cmbUnitsPhi.currentText()

        self.bb = fb.fil[0]['ba'][0]
        self.aa = fb.fil[0]['ba'][1]

        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']

        [W,H] = sig.freqz(self.bb, self.aa, worN = params['N_FFT'],
                        whole = wholeF)

        F = W / (2 * np.pi) * f_S

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            H = np.fft.fftshift(H)
            F = F - f_S / 2.

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
        
        # replace nan and inf by finite values, otherwise np.unwrap yields
        # an array full of nans
        H = np.nan_to_num(H) 
        if self.chkWrap.isChecked():
            phi_plt = np.angle(H) * scale
        else:
            phi_plt = np.unwrap(np.angle(H)) * scale

        self.ax.clear() # need to clear, doesn't overwrite 
        #---------------------------------------------------------
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

#------------------------------------------------------------------------------

def main():
    import sys
    from ..compat import QApplication
    
    app = QApplication(sys.argv)
    mainw = PlotPhi(None)
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
