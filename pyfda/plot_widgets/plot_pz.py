# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui

#import numpy as np

if __name__ == "__main__": # relative import if this file is run as __main__
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import pyfda.filterbroker as fb
import pyfda.pyfda_lib

from pyfda.plot_widgets.plot_utils import MplWidget#, MplCanvas

class PlotPZ(QtGui.QMainWindow):

    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window
        super(PlotPZ, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.DEBUG = DEBUG

        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)

        self.mplwidget = MplWidget()

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)

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

    def draw(self):
        if self.mplwidget.mplToolbar.enable_update:
            self.draw_pz()

    def draw_pz(self):
        """
        (re)draw P/Z plot
        """

        zpk = fb.fil[0]['zpk']

        self.ax.clear()

        [z, p, k] = pyfda_lib.zplane(self.ax, zpk, verbose = False)

        self.ax.set_title(r'Pole / Zero Plot')
        self.ax.set_xlabel('Real axis')
        self.ax.set_ylabel('Imaginary axis')

        self.ax.axis([-1.1, 1.1, -1.1, 1.1])

        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = PlotPZ()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
