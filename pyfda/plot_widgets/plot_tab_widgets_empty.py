# -*- coding: utf-8 -*-
"""
This normally contains all tabbed plot subwidgets, for test purposes it is 
completely empty here WITHOUT Matplotlib canvas / figure

Author: Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
from PyQt4 import QtGui

from pyfda.pyfda_lib import grpdelay
import pyfda.filterbroker as fb
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#------------------------------------------------------------------------------
class PlotTabWidgets(QtGui.QWidget):
    def __init__(self, parent):
        super(PlotTabWidgets, self).__init__(parent)

#        self.pltTauG = PlotTauG(self) # instantiating this causes a crash upon exit
        
        
        """ Initialize UI with tabbed subplots """
#        tabWidget = QtGui.QTabWidget()

#        tabWidget.addTab(self.pltTauG, 'tau_g')

        layVMain = QtGui.QVBoxLayout()
#        layVMain.addWidget(self.pltTauG)        
#        layVMain.addWidget(tabWidget)
        layVMain.setContentsMargins(1,1,1,1)
#
        self.setLayout(layVMain)

#------------------------------------------------------------------------------
    def update_data(self):
        """ Calculate subplots with new filter DATA and redraw them """

#        self.pltTauG.draw_taug()
        pass

#------------------------------------------------------------------------------
    def update_view(self):
        """ Update plot limits with new filter SPECS and redraw all subplots """

#        self.pltTauG.draw_taug()
        pass
    

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

        [w, tau_g] = grpdelay(bb,aa, 2048, whole = True)

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
