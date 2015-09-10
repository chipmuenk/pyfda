# -*- coding: utf-8 -*-
"""
Tabbed container with all plot widgets

Author: Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
from PyQt4 import QtGui

from pyfda.plot_widgets import (plot_hf, plot_phi, plot_pz, plot_tau_g, plot_impz,
                          plot_3d)

from pyfda import user_settings

#------------------------------------------------------------------------------
class PlotWidgets(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
#        css = """
#QTabBar{
#font-weight:normal;
#}
#
#"""

#        self.setStyleSheet(css)
        self.pltHf = plot_hf.PlotHf()
        self.pltPhi = plot_phi.PlotPhi()
        self.pltPZ = plot_pz.PlotPZ()
        self.pltTauG = plot_tau_g.PlotTauG()
        self.pltImpz = plot_impz.PlotImpz()
        self.plt3D = plot_3d.Plot3D()

        self.initUI()


#------------------------------------------------------------------------------
    def initUI(self):
        """ Initialize UI with tabbed subplots """
        tabWidget = QtGui.QTabWidget()
        tabWidget.setStyleSheet(user_settings.css_rc['QTabBar'])
        tabWidget.addTab(self.pltHf, '|H(f)|')
        tabWidget.addTab(self.pltPhi, 'phi(f)')
        tabWidget.addTab(self.pltPZ, 'P/Z')
        tabWidget.addTab(self.pltTauG, 'tau_g')
        tabWidget.addTab(self.pltImpz, 'h[n]')
        tabWidget.addTab(self.plt3D, '3D')

        layVMain = QtGui.QVBoxLayout()
        layVMain.addWidget(tabWidget)
        layVMain.setContentsMargins(1,1,1,1)#(left, top, right, bottom)
#
        self.setLayout(layVMain)


#------------------------------------------------------------------------------
    def updateData(self):
        """ Update and redraw all subplots with new filter DATA"""
        self.pltHf.draw()
        self.pltPhi.draw()
        self.pltPZ.draw()
        self.pltTauG.draw()
        self.pltImpz.draw()
        self.plt3D.draw()
        
#------------------------------------------------------------------------------
    def updateSpecs(self):
        """ Update and redraw all subplots with new filter SPECS"""
        self.pltHf.draw()
        self.pltPhi.draw()
        self.pltTauG.draw()
        self.pltImpz.draw()

#------------------------------------------------------------------------

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    form = PlotWidgets()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
