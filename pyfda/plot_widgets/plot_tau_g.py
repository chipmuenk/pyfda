# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from PyQt4 import QtGui
import numpy as np

# add path to libraries one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    import sys, os
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import pyfda.filterbroker as fb
import pyfda.pyfda_lib
from pyfda.plot_widgets.plot_utils import MplWidget


class PlotTauG(QtGui.QMainWindow):

    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window
        super(PlotTauG, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.DEBUG = DEBUG
#
#        self.lblWrap = QtGui.QLabel("Wrapped Phase")
#        self.btnWrap = QtGui.QCheckBox()
#        self.btnWrap.setChecked(False)
#        self.btnWrap.setToolTip("Plot phase wrapped to +/- pi")
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)
#        self.layHChkBoxes.addWidget(self.cmbUnitsPhi)

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
#        self.btnWrap.clicked.connect(self.draw)
#        self.cmbUnitsPhi.currentIndexChanged.connect(self.draw)

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

    def draw_taug(self):
        """
        Draw group delay
        """
        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']

#        scale = self.cmbUnitsPhi.itemData(self.cmbUnitsPhi.currentIndex())

        [tau_g, w] = pyfda_lib.grpdelay(bb,aa, fb.gD['N_FFT'],
                        whole = wholeF)

        F = w / (2 * np.pi) * fb.fil[0]['f_S']
        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            tau_g = np.fft.fftshift(tau_g)
            F = F - f_S / 2.

        self.ax.plot(F, tau_g, lw = fb.gD['rc']['lw'], label = "Group Delay")

        self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax.set_ylabel(r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $')
        # widen limits to suppress numerical inaccuracies when tau_g = constant
        self.ax.axis(fb.fil[0]['freqSpecsRange'] + [max(min(tau_g)-0.5,0), max(tau_g) + 0.5])


        self.mplwidget.redraw()
#------------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotTauG()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
