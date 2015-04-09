# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui #, QtCore
import numpy as np
from numpy import pi, ones, zeros, sin, cos, log10
import scipy.signal as sig

if __name__ == "__main__": # relative import if this file is run as __main__
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb
import pyfda_lib

from plot_widgets.plot_utils import MplWidget#, MplCanvas
from mpl_toolkits.mplot3d.axes3d import Axes3D
from matplotlib import cm # Colormap

class Plot3D(QtGui.QMainWindow):
    
    """
    Class for various 3D-plots:
    - lin / log line plot of H(f)
    - lin / log surf plot of H(z)
    - optional display of poles / zeros
    """

    def __init__(self, parent = None, DEBUG = False): # default parent = None -> top Window
        super(Plot3D, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.DEBUG = DEBUG
        
        self.lblLog = QtGui.QLabel(self)
        self.lblLog.setText("Log.")
        self.chkLog = QtGui.QCheckBox(self)
        self.chkLog.setObjectName("chkLog")
        self.chkLog.setToolTip("Logarithmic scale")
        self.chkLog.setChecked(False)
        
        self.lblLogBottom = QtGui.QLabel("Log. bottom:")

        self.ledLogBottom = QtGui.QLineEdit(self)
        self.ledLogBottom.setText("-80")
        self.ledLogBottom.setToolTip("Minimum display value for log. scale.")

        self.lblUC = QtGui.QLabel(self)
        self.lblUC.setText("UC")
        self.chkUC = QtGui.QCheckBox(self)
        self.chkUC.setObjectName("chkUC")
        self.chkUC.setToolTip("Plot unit circle")
        self.chkUC.setChecked(True)
        
        self.lblPZ = QtGui.QLabel(self)
        self.lblPZ.setText("P/Z")
        self.chkPZ = QtGui.QCheckBox(self)
        self.chkPZ.setObjectName("chkPZ")
        self.chkPZ.setToolTip("Plot poles and zeros")
        self.chkPZ.setChecked(True)
        
        self.lblHf = QtGui.QLabel(self)
        self.lblHf.setText("H(f)")
        self.chkHf = QtGui.QCheckBox(self)
        self.chkHf.setObjectName("chkHf")
        self.chkHf.setToolTip("Plot H(f) along the unit circle")
        self.chkHf.setChecked(True)
        
        modes = ['None', 'Mesh', 'Surf', 'Contour']
        self.cmbMode3D = QtGui.QComboBox(self)
        self.cmbMode3D.addItems(modes)
        self.cmbMode3D.setObjectName("cmbShow3D")
        self.cmbMode3D.setToolTip("Select 3D-plot mode.")
        self.cmbMode3D.setCurrentIndex(0)
        
        self.lblColBar = QtGui.QLabel(self)
        self.lblColBar.setText("Colorbar")
        self.chkColBar = QtGui.QCheckBox(self)
        self.chkColBar.setObjectName("chkColBar")
        self.chkColBar.setToolTip("Show colorbar")
        self.chkColBar.setChecked(False)
        
        self.lblContour2D = QtGui.QLabel(self)
        self.lblContour2D.setText("Contour2D")
        self.chkContour2D = QtGui.QCheckBox(self)
        self.chkContour2D.setObjectName("chkContour2D")
        self.chkContour2D.setToolTip("Plot 2D-contours for real and imaginary part")
        self.chkContour2D.setChecked(True)
        
        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)

        self.layHChkBoxes.addWidget(self.lblLog)
        self.layHChkBoxes.addWidget(self.chkLog)
        self.layHChkBoxes.addWidget(self.lblLogBottom)
        self.layHChkBoxes.addWidget(self.ledLogBottom)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblUC)
        self.layHChkBoxes.addWidget(self.chkUC)  
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblPZ)
        self.layHChkBoxes.addWidget(self.chkPZ)                   
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblHf)
        self.layHChkBoxes.addWidget(self.chkHf)        
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.cmbMode3D)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblColBar)
        self.layHChkBoxes.addWidget(self.chkColBar)
        self.layHChkBoxes.addStretch(1)
        self.layHChkBoxes.addWidget(self.lblContour2D)
        self.layHChkBoxes.addWidget(self.chkContour2D) 

        self.layHChkBoxes.addStretch(1)        


        self.mplwidget = MplWidget()
#        self.mplwidget.setParent(self)

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)

        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)
        
        self.initAxes()

        self.draw() # calculate and draw phi(f)

#        #=============================================
#        # Signals & Slots
#        #=============================================
        self.chkLog.clicked.connect(self.draw)
        self.ledLogBottom.editingFinished.connect(self.draw)
        self.chkUC.clicked.connect(self.draw)
        self.chkHf.clicked.connect(self.draw)
        self.chkPZ.clicked.connect(self.draw)
        self.cmbMode3D.currentIndexChanged.connect(self.draw)
        self.chkColBar.clicked.connect(self.draw)
        self.chkContour2D.clicked.connect(self.draw)

    def initAxes(self):
        """Initialize and clear the axes
        see http://stackoverflow.com/questions/4575588/matplotlib-3d-plot-with-pyqt4-in-qtabwidget-mplwidget
        """
        
#        self.ax = self.mplwidget.ax
#        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax = Axes3D(self.mplwidget.fig)
#        self.ax = self.mplwidget.fig.gca(projection='3d')
        self.ax.clear()
        
        self.phi_EK = np.linspace(0, 2*pi, 400) # 400 points from 0 ... 2 pi
        self.xy_UC = np.exp(1j * self.phi_EK) # x,y coordinates of unity circle
        #plt.gca().cla()
        #p.clf()

    def draw(self):
        """
        Draw group delay
        """
        bb = fb.fil[0]['coeffs'][0]
        aa = fb.fil[0]['coeffs'][1]
        
        zz = np.array(fb.fil[0]['zpk'][0])
        pp = np.array(fb.fil[0]['zpk'][1])

        wholeF = fb.rcFDA['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']
        N_FFT = fb.gD['N_FFT']
        
        #-----------------------------------------------------------------------------
        # Define 3D-Plotting Options
        #-----------------------------------------------------------------------------
        PLT_min_dB = float(self.ledLogBottom.text())
        
        OPT_3D_POLAR_SPEC = False # Plot circular range in 3D-Plot
        OPT_3D_FORCE_ZMAX = True # Enforce absolute limit for 3D-Plot
        OPT_3D_MSTRIDE = 1 # Schrittweite für MESH und CONT3D
        OPT_3D_ALPHA = 1 # Transparency for surface plot
        #
        steps = 80               # number of steps for x, y, r, phi
        rmin = 0;    rmax = 1.0  # polar range definition
        #
        xmin = -1.5; xmax = 1.5  # cartesian range definition
        ymin = -1.5; ymax = 1.5
        #
        zmin =  -1.0; zmax = 4.0 # zmax only used when OPT_3D_FORCE_ZMAX = True
        zmax_rel = 5 # Max. displayed z - value relative to max|H(f)|
        
        # Calculate limits etc. for 3D-Plots
        dr = rmax / steps * 2 
        dphi = pi / steps # grid size for polar range
        dx = (xmax - xmin) / steps  
        dy = (ymax - ymin) / steps # grid size cartesian range
        if OPT_3D_POLAR_SPEC == True: # polar grid
            [r, phi] = np.meshgrid(np.arange(rmin, rmax, dr), np.arange(0,2*pi,dphi)) 
        #    [x, y] = np.pol2cart(phi,r) # 
            x = r * cos(phi)
            y = r * sin(phi)
        else: # cartesian grid
            [x, y] = np.meshgrid(np.arange(xmin,xmax,dx), np.arange(ymin,ymax,dy)) 
        
        z = x + 1j*y # create coordinate grid for complex plane

        [w, H] = sig.freqz(bb, aa, N_FFT, wholeF) # calculate H(w) along the 
                                                # upper half of unity circle
                                                # w runs from 0 ... pi, length = N_FFT
        f = w / (2 * pi) * f_S                  # translate w to absolute frequencies

        H_abs = abs(H)
        H_max = max(H_abs)
        H_max_dB = 20*log10(H_max)
        F_max = f[np.argmax(H_abs)]
        
        if OPT_3D_FORCE_ZMAX == True:
            thresh = zmax
        else:
            thresh = zmax_rel * H_max # calculate display thresh. from max. of H(f)
 
        #
        H_min = min(H_abs); H_min_dB = 20*log10(H_min); F_min = f[np.argmin(H_abs)]
        min_dB = np.floor(max(PLT_min_dB, H_min_dB) / 10) * 10   
    
        # calculate H(jw)| along the unity circle and |H(z)|, each clipped to thresh
        if self.chkLog.isChecked():
            zmin = min_dB
            thresh = 20 * log10(thresh)
            H_UC = 20 * log10(pyfda_lib.H_mag(bb, aa, self.xy_UC, thresh)) 
            H_UC = np.maximum(H_UC, min_dB)
            Hmag = 20 * log10(pyfda_lib.H_mag(bb, aa, z, thresh))

        else:  
            H_UC = pyfda_lib.H_mag(bb, aa, self.xy_UC, thresh) 
            Hmag = pyfda_lib.H_mag(bb, aa, z, thresh)
            zmin = -1
        
        self.ax.cla()
        self.ax.hold(True)

        #===============================================================
        ## plot unit circle
        #===============================================================       
        if self.chkUC.isChecked():        
        # Plot unit circle:
            self.ax.plot(self.xy_UC.real, self.xy_UC.imag, zeros(len(self.xy_UC)), 
                     linewidth=2, color = 'k')
                     
        #===============================================================
        ## plot ||H(f)| along unit circle as 3D-lineplot
        #===============================================================        
        if self.chkHf.isChecked():
            self.ax.plot(self.xy_UC.real, self.xy_UC.imag, H_UC, lw = fb.gD['rc']['lw'])
            NL = 2 # plot line every NL points on the UC
            for k in range(len(self.xy_UC[::NL])):
                self.ax.plot([self.xy_UC.real[::NL][k], self.xy_UC.real[::NL][k]],
                    [self.xy_UC.imag[::NL][k], self.xy_UC.imag[::NL][k]],
                    [np.zeros(len(self.xy_UC[::NL]))[k], H_UC[::NL][k]],
                     linewidth=1, color=(0.5, 0.5, 0.5))
        #===============================================================
        ## plot Poles and Zeros
        #===============================================================        
        if self.chkPZ.isChecked():
            plevel_rel = 1.05 # height of plotted pole position relative to zmax
            zlevel_rel = 0.1 # height of plotted zero position relative to zmax
            PN_SIZE = 8 # size of P/N symbols
            
            if self.cmbMode3D.currentText() == 'None':
                zlevel = plevel = 0 # plevel = H_max * 0.1 / zlevel = 0.1
            else:
                plevel = plevel_rel * thresh # height of displayed pole position
                zlevel = zlevel_rel * thresh # height of displayed zero position                
            # Plot zero markers at |H(z_i)| = zlevel with "stems":     
            self.ax.plot(zz.real, zz.imag, ones(len(zz)) * H_max * zlevel, 'o',
               markersize = PN_SIZE, markeredgecolor='blue', markeredgewidth=2.0,
                markerfacecolor = 'none') 
            for k in range(len(zz)): # plot zero "stems"
                self.ax.plot([zz[k].real, zz[k].real], [zz[k].imag, zz[k].imag],
                            [0, zlevel], linewidth=1, color='b')
                            
            # Plot the poles at |H(z_p)| = plevel with "stems":
            self.ax.plot(np.real(pp), np.imag(pp), plevel,
              'x', markersize = PN_SIZE, markeredgewidth=2.0, markeredgecolor='red') 
            for k in range(len(pp)): # plot pole "stems"
                self.ax.plot([pp[k].real, pp[k].real], [pp[k].imag, pp[k].imag],
                            [0, plevel], linewidth=1, color='r')

        #===============================================================
        ## 3D-Surface Plots
        #===============================================================    
        if self.cmbMode3D.currentText() == 'Mesh':
        #    fig_mlab = mlab.figure(fgcolor=(0., 0., 0.), bgcolor=(1, 1, 1))
        #    self.ax.set_zlim(0,2)
        
            self.ax.plot_wireframe(x, y, Hmag, rstride=5,
                                  cstride=OPT_3D_MSTRIDE, linewidth = 1, color = 'gray') 

    #        [xplane, yplane, zplane] = np.ogrid[-5:5:100 , -5:5:100 , -5:5:100]
        elif self.cmbMode3D.currentText() == 'Surf':
            #plot 3D-surface of |H(z)|; clipped at |H(z)| = thresh
            s = self.ax.plot_surface(x,y,Hmag, 
                    alpha = OPT_3D_ALPHA, rstride=1, cstride=1, cmap = cm.jet,
                    linewidth=0, antialiased=False, edgecolor = 'grey', shade = True)
                    # Colormaps: 'hsv', 'jet', 'bone', 'prism' 'gray' 'colorcube', 'prism'
    #       ax.setp(g,'EdgeColor', 'r')#(.4, .4, .4)) # medium gray color for mesh
            if self.chkColBar.isChecked():
                self.colb = self.mplwidget.fig.colorbar(s, shrink=0.5, aspect=10)
        elif self.cmbMode3D.currentText() == 'Contour': # Contour plot
            s = self.ax.contourf3D(x,y,Hmag,
                            rstride=OPT_3D_MSTRIDE, cstride=OPT_3D_MSTRIDE)
            if self.chkColBar.isChecked():
                self.colb = self.mplwidget.fig.colorbar(s, shrink=0.5, aspect=10)
                            
        if self.chkContour2D.isChecked():
            self.ax.contourf(x, y, Hmag, zdir='x', offset=xmin, 
                                 vmin = zmin, vmax = thresh, cmap=cm.coolwarm)
            self.ax.contourf(x, y, Hmag, zdir='y', offset=ymax, cmap=cm.coolwarm)

        self.ax.set_zlim3d(zmin, thresh)
        self.ax.set_xlabel('Re')#(fb.rcFDA['plt_fLabel'])
        self.ax.set_ylabel('Im') #(r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $')
        self.ax.set_title(r'3D-Plot of $|H(j\Omega)|$ and $H|(z)|$')
        self.ax.hold(False)
#        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    app = QtGui.QApplication(sys.argv)
    form = Plot3D()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
