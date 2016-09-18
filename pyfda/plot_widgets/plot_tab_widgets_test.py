# -*- coding: utf-8 -*-
"""
Tabbed container with all plot widgets

Author: Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
from PyQt4 import QtGui

from pyfda.pyfda_lib import grpdelay
#from pyfda.plot_widgets import plot_tau_g_test as plot_tau_g
#from pyfda.plot_widgets import plot_tau_g
import pyfda.filterbroker as fb
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#------------------------------------------------------------------------------
class PlotTabWidgets(QtGui.QWidget):
    def __init__(self, parent):
        super(PlotTabWidgets, self).__init__(parent)

        self.pltTauG = PlotTauG(self)
        
        
        """ Initialize UI with tabbed subplots """
#        tabWidget = QtGui.QTabWidget()

#        tabWidget.addTab(self.pltTauG, 'tau_g')

        layVMain = QtGui.QVBoxLayout()
        layVMain.addWidget(self.pltTauG)        
#        layVMain.addWidget(tabWidget)
        layVMain.setContentsMargins(1,1,1,1)#(left, top, right, bottom)
#
        self.setLayout(layVMain)

#------------------------------------------------------------------------------
    def update_data(self):
        """ Calculate subplots with new filter DATA and redraw them """
#        self.pltHf.draw()
#        self.pltPhi.draw()
#        self.pltPZ.draw()

        self.pltTauG.draw_taug()

#        self.pltImpz.draw()
#        self.plt3D.draw()
        pass

#------------------------------------------------------------------------------
    def update_view(self):
        """ Update plot limits with new filter SPECS and redraw all subplots """
#        self.pltHf.update_view()
#        self.pltPhi.update_view()
        self.pltTauG.draw_taug()
#        self.pltImpz.update_view()

#        self.pltPZ.draw()
#        self.plt3D.draw()
        pass

#    def draw_tau(self):
#        bb = fb.fil[0]['ba'][0]
#        aa = fb.fil[0]['ba'][1]
#        
#        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'
#
#        [w, tau_g] = grpdelay(bb,aa, 2048, whole = wholeF)#, 
#
#        F = w * fb.fil[0]['f_S']
#
#        self.ax = self.figure.add_subplot(111)
#        self.ax.hold(False)
#        self.ax.plot(F, tau_g)
#        self.canvas.draw()
    

class PlotTauG(QtGui.QWidget):

    def __init__(self, parent=None):
        super(PlotTauG, self).__init__(parent)

        self.figure = Figure(figsize=(10,5))
        self.resize(800,480)
        self.canvas = FigureCanvas(self.figure)

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.draw_taug()

    def draw_taug(self):
        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        [w, tau_g] = grpdelay(bb,aa, 2048, whole = True)#, 
#            verbose = self.chkWarnings.isChecked())

        F = w * fb.fil[0]['f_S']

        self.ax = self.figure.add_subplot(111)
        self.ax.hold(False)
        self.ax.plot(F, tau_g)
        self.canvas.draw()

#------------------------------------------------------------------------

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    form = PlotTabWidgets(None)
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
