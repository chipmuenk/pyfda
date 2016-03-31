# -*- coding: utf-8 -*-
"""
Widget for plotting phase frequency response phi(f)

Author: Christian Muenker 2015
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from PyQt4 import QtGui
import numpy as np
import scipy.signal as sig

import pyfda.filterbroker as fb
import pyfda.pyfda_rc as rc
from pyfda.plot_widgets.plot_utils import MplWidget


class PlotPhi(QtGui.QWidget):

    def __init__(self, parent):
        super(PlotPhi, self).__init__(parent)

        self.cmbUnitsPhi = QtGui.QComboBox(self)
        units = ["rad", "rad/pi",  "deg"]
        scales = [1.,   1./ np.pi, 180./np.pi]
        for unit, scale in zip(units, scales):
            self.cmbUnitsPhi.addItem(unit, scale)
        self.cmbUnitsPhi.setObjectName("cmbUnitsA")
        self.cmbUnitsPhi.setToolTip("Set unit for phase.")
        self.cmbUnitsPhi.setCurrentIndex(0)
        self.cmbUnitsPhi.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.lblWrap = QtGui.QLabel("Wrapped Phase")
        self.btnWrap = QtGui.QCheckBox()
        self.btnWrap.setChecked(False)
        self.btnWrap.setToolTip("Plot phase wrapped to +/- pi")
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.cmbUnitsPhi)
        self.layHChkBoxes.addWidget(self.lblWrap)
        self.layHChkBoxes.addWidget(self.btnWrap)
        self.layHChkBoxes.addStretch(10)

        #----------------------------------------------------------------------
        # mplwidget
        #----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)
        
        self.setLayout(self.mplwidget.layVMainMpl)


#        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
#        self.setCentralWidget(self.mplwidget)
        
        self._init_axes()

        self.draw() # initial drawing

#        #=============================================
#        # Signals & Slots
#        #=============================================
        self.btnWrap.clicked.connect(self.draw)
        self.cmbUnitsPhi.currentIndexChanged.connect(self.draw)
        
    def _init_axes(self):
        """Initialize and clear the axes
        """
#        self.ax = self.mplwidget.ax
        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()
        self.ax.hold(False)
        
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
        if self.mplwidget.mplToolbar.enable_update:
            self.draw_phi()

    def draw_phi(self):
        """
        Re-calculate phi(f) and draw the figure
        """

        self.unitPhi = self.cmbUnitsPhi.currentText()

        self.bb = fb.fil[0]['ba'][0]
        self.aa = fb.fil[0]['ba'][1]

        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']

        [W,H] = sig.freqz(self.bb, self.aa, worN = rc.params['N_FFT'],
                        whole = wholeF)

        F = W / (2 * np.pi) * f_S

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            H = np.fft.fftshift(H)
            F = F - f_S / 2.

#        scale = self.cmbUnitsPhi.itemData(self.cmbUnitsPhi.currentIndex())
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
        if self.btnWrap.isChecked():
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

        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    mainw = PlotPhi()
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
