# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from PyQt4 import QtGui
import numpy as np

import pyfda.filterbroker as fb
import pyfda.pyfda_rc as rc
from pyfda.pyfda_lib import grpdelay
from pyfda.plot_widgets.plot_utils import MplWidget


class PlotTauG(QtGui.QMainWindow):

    def __init__(self, parent = None): # default parent = None -> top Window
        super(PlotTauG, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax
#
#        self.lblWrap = QtGui.QLabel("Wrapped Phase")
        self.chkWarnings = QtGui.QCheckBox()
        self.chkWarnings.setText("Enable Warnings")
        self.chkWarnings.setChecked(False)
        self.chkWarnings.setToolTip("Print warnings about singular group delay")
#        self.chkScipy = QtGui.QCheckBox()
#        self.chkScipy.setText("Scipy grpdelay")
#        self.chkScipy.setChecked(False)
#        self.chkScipy.setToolTip("Use group delay from scipy 0.16")
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)
        self.layHChkBoxes.addWidget(self.chkWarnings)
#        self.layHChkBoxes.addWidget(self.chkScipy)

        self.mplwidget = MplWidget()
#        self.mplwidget.setParent(self)
        
        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)

#        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)
        
        self.initAxes()

        self.draw() # calculate and draw phi(f)

#        #=============================================
#        # Signals & Slots
#        #=============================================
        self.chkWarnings.clicked.connect(self.draw)


    def initAxes(self):
        """Initialize and clear the axes
        """
#        self.ax = self.mplwidget.ax
        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()
        self.ax.set_title(r'Group Delay $ \tau_g$')
        self.ax.hold(False)
        
        
        #plt.gca().cla()
        #p.clf()
        
    def draw(self):
        if self.mplwidget.mplToolbar.enable_update:
            self.draw_taug()
            
    def update_specs(self):
        """
        Update frequency range etc. without recalculating group delay.
        """
        self.draw()

    def draw_taug(self):
        """
        Draw group delay
        """
        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']

        self.unitPhi = fb.fil[0]['plt_phiUnit']   
        y_str = r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$'
        if self.unitPhi == 'rad':
            y_str += ' in rad ' + r'$\rightarrow $'
            scale = 1.
        elif self.unitPhi == 'rad/pi':
            y_str += ' in rad' + r'$ / \pi \;\rightarrow $'
            scale = 1./ np.pi
        else:
            y_str += ' in deg ' + r'$\rightarrow $'
            scale = 180./np.pi
#        fb.fil[0]['plt_phiLabel'] = y_str


#        scale = self.cmbUnitsPhi.itemData(self.cmbUnitsPhi.currentIndex())

        [w, tau_g] = grpdelay(bb,aa, rc.params['N_FFT'], whole = wholeF, 
            verbose = self.chkWarnings.isChecked())

        F = w / (2 * np.pi) * fb.fil[0]['f_S']

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            tau_g = np.fft.fftshift(tau_g)
            F = F - f_S / 2.

        #---------------------------------------------------------
        line_tau_g, = self.ax.plot(F, tau_g, label = "Group Delay")
        #---------------------------------------------------------
        
        self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax.set_ylabel(r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $')
        # widen limits to suppress numerical inaccuracies when tau_g = constant
        self.ax.axis(fb.fil[0]['freqSpecsRange'] + [max(min(tau_g)-0.5,0), max(tau_g) + 0.5])

        self.mplwidget.redraw()
#------------------------------------------------------------------------------

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    form = PlotTauG()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
