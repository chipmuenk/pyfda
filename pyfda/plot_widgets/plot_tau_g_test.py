# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from PyQt4 import QtGui, QtCore
import numpy as np

import pyfda.filterbroker as fb
import pyfda.pyfda_rc as rc
from pyfda.pyfda_lib import grpdelay
#from pyfda.plot_widgets.plot_utils import MplWidget

# from plot_utils
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

# http://matplotlib.org/examples/user_interfaces/embedding_in_qt4.html

#class MyMplCanvas(FigureCanvas):
#    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
#
#    def __init__(self, parent=None, width=5, height=4, dpi=100):
#        fig = Figure(figsize=(width, height), dpi=dpi)
#        self.axes = fig.add_subplot(111)
#        # We want the axes cleared every time plot() is called
#        self.axes.hold(False)
#
#        self.compute_initial_figure()
#
#        #
#        FigureCanvas.__init__(self, fig)
#        self.setParent(parent)
#
#        FigureCanvas.setSizePolicy(self,
#                                   QtGui.QSizePolicy.Expanding,
#                                   QtGui.QSizePolicy.Expanding)
#        FigureCanvas.updateGeometry(self)
#
#    def compute_initial_figure(self):
#        pass
#
#
#class MyStaticMplCanvas(MyMplCanvas):
#    """Simple canvas with a sine plot."""
#
#    def compute_initial_figure(self):
#        t = np.arange(0.0, 3.0, 0.01)
#        s = np.sin(2*np.pi*t)
#        self.axes.plot(t, s)
#
class PlotTauG(QtGui.QWidget):

    def __init__(self, parent):
        super(PlotTauG, self).__init__(parent)

################# GUI Elements ################################################
#        self.chkWarnings = QtGui.QCheckBox()
#        self.chkWarnings.setText("Enable Warnings")
#        self.chkWarnings.setChecked(False)
#        self.chkWarnings.setToolTip("Print warnings about singular group delay")
#
#        self.layHChkBoxes = QtGui.QHBoxLayout()
#        self.layHChkBoxes.addStretch(10)
#        self.layHChkBoxes.addWidget(self.chkWarnings)
###############################################################################
# from plot_utils  ----------------------------------------------------------- 
 #       plt_canvas-> mplwidget      
        self.fig = Figure() 

        self.mplwidget = FigureCanvas(self.fig)
        self.mplwidget.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)

        # Needed for mouse modifiers (x,y, <CTRL>, ...):
        #    Key press events in general are not processed unless you
        #    "activate the focus of Qt onto your mpl canvas"
        # http://stackoverflow.com/questions/22043549/matplotlib-and-qt-mouse-press-event-key-is-always-none
#        self.mplwidget.setFocusPolicy(QtCore.Qt.ClickFocus)
#        self.mplwidget.setFocus()

        self.mplwidget.updateGeometry() 
        
        self.setLayout(self.mplwidget.layVMainMpl)
        
        
############ combine UI elements ##############################################
        
#        _widget = QtGui.QWidget() # this widget contains all subwidget groups
#
#        layVMain = QtGui.QVBoxLayout(_widget) # horizontal layout of all groups
#
#        layVMain.addWidget(self.mplwidget)
#        layVMain.addLayout(self.layHChkBoxes)

###############################################################################

#        self.setLayout(layVMain)
#------------------------------------------------        


#        _widget.setSizePolicy(QtGui.QSizePolicy.Expanding,
#                                 QtGui.QSizePolicy.Expanding)
        
        self._init_axes()

        self.draw() # initial drawing of tau_g

#        #=============================================
#        # Signals & Slots
#        #=============================================
#        self.chkWarnings.clicked.connect(self.draw)


#------------------------------------------------------------------------------
    def _init_axes(self):
        """Initialize and clear the axes
        """
#        self.ax = self.mplwidget.ax
        self.ax = self.fig.add_subplot(111)
        self.ax.clear()
        self.ax.set_title(r'Group Delay $ \tau_g$')
        self.ax.hold(False)      
        
        #plt.gca().cla()
        #p.clf()
        
#------------------------------------------------------------------------------
    def draw(self):
##        if self.mplwidget.mplToolbar.enable_update:
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
        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']

        [w, tau_g] = grpdelay(bb,aa, rc.params['N_FFT'], whole = wholeF)#, 
#            verbose = self.chkWarnings.isChecked())

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
                   

        self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax.set_ylabel(tau_str)
        # widen y-limits to suppress numerical inaccuracies when tau_g = constant
        self.ax.set_ylim([max(min(tau_g)-0.5,0), max(tau_g) + 0.5])
        self.ax.set_xlim(fb.fil[0]['freqSpecsRange'])

#        self.mplwidget.redraw()
#------------------------------------------------------------------------------
#################################################################################
#class ApplicationWindow(QtGui.QMainWindow):
#    def __init__(self):
#        QtGui.QMainWindow.__init__(self)
#        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
#        self.setWindowTitle("application main window")
#
#
#        self.main_widget = QtGui.QWidget(self)
#
#        l = QtGui.QVBoxLayout(self.main_widget)
#        sc = MyStaticMplCanvas(self.main_widget, width=5, height=4, dpi=100)
##        dc = MyDynamicMplCanvas(self.main_widget, width=5, height=4, dpi=100)
##        mw = 
#        l.addWidget(sc)
##        l.addWidget(dc)
#
#        self.main_widget.setFocus()
#        self.setCentralWidget(self.main_widget)

#################################################################################

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    mainw = PlotTauG()

#    app = QtGui.QApplication(sys.argv)   
#    mainw = ApplicationWindow()

    app.setActiveWindow(mainw) 
    mainw.show()
#    app.exec_()
    sys.exit(app.exec_())
    

#    app = QtGui.QApplication(sys.argv)
#    
#    mainw = ApplicationWindow()
#    mainw.setWindowTitle("%s" % progname)
#    aw.show()
#    sys.exit(qApp.exec_())
#qApp.exec_()    

if __name__ == "__main__":
    main()
