# -*- coding: utf-8 -*-
"""

Edited by Christian Münker, 2013
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)
from PyQt4 import QtGui #, QtCore
import numpy as np
from numpy import pi, ones, zeros, sin, cos, log10
import scipy.signal as sig


import pyfda.filterbroker as fb
import pyfda.pyfda_rc as rc
from pyfda.pyfda_lib import H_mag
from pyfda.plot_widgets.plot_utils import MplWidget

from mpl_toolkits.mplot3d.axes3d import Axes3D
from matplotlib import cm # Colormap
from matplotlib.colors import LightSource

try:
    from mayavi import mlab
    MLAB = True
    logger.info("Module mayavi loaded, fast 3D-plots available.")
except ImportError:
    MLAB = False
    logger.info("Module mayavi not found.")



class Plot3D(QtGui.QMainWindow):
    """
    Class for various 3D-plots:
    - lin / log line plot of H(f)
    - lin / log surf plot of H(z)
    - optional display of poles / zeros
    """

    def __init__(self, parent=None): # default parent = None -> top Window
        super(Plot3D, self).__init__(parent) # initialize QWidget base class
#        QtGui.QMainWindow.__init__(self) # alternative syntax

        self.zmin = 0
        self.zmax = 4
        self.zmin_dB = -80
        self._init_UI()

    def _init_UI(self):
        self.chkLog = QtGui.QCheckBox(self)
        self.chkLog.setText("Log.")
        self.chkLog.setObjectName("chkLog")
        self.chkLog.setToolTip("Logarithmic scale")
        self.chkLog.setChecked(False)

        self.chkPolar = QtGui.QCheckBox(self)
        self.chkPolar.setText("Polar")
        self.chkPolar.setObjectName("chkPolar")
        self.chkPolar.setToolTip("Polar coordinates")
        self.chkPolar.setChecked(False)


        self.lblBottom = QtGui.QLabel("Bottom =")
        self.ledBottom = QtGui.QLineEdit(self)
        self.ledBottom.setObjectName("ledBottom")
        self.ledBottom.setText(str(self.zmin))
        self.ledBottom.setToolTip("Minimum display value.")

        self.lblTop = QtGui.QLabel("Top:")
        self.ledTop = QtGui.QLineEdit(self)
        self.ledTop.setObjectName("ledTop")
        self.ledTop.setText(str(self.zmax))
        self.ledTop.setToolTip("Maximum display value.")
#        self.ledTop.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)

        self.chkUC = QtGui.QCheckBox(self)
        self.chkUC.setText("UC")
        self.chkUC.setObjectName("chkUC")
        self.chkUC.setToolTip("Plot unit circle")
        self.chkUC.setChecked(True)

        self.chkPZ = QtGui.QCheckBox(self)
        self.chkPZ.setText("P/Z")
        self.chkPZ.setObjectName("chkPZ")
        self.chkPZ.setToolTip("Plot poles and zeros")
        self.chkPZ.setChecked(True)

        self.chkHf = QtGui.QCheckBox(self)
        self.chkHf.setText("H(f)")
        self.chkHf.setObjectName("chkHf")
        self.chkHf.setToolTip("Plot H(f) along the unit circle")
        self.chkHf.setChecked(True)

        modes = ['None', 'Mesh', 'Surf', 'Contour']
        self.cmbMode3D = QtGui.QComboBox(self)
        self.cmbMode3D.addItems(modes)
        self.cmbMode3D.setObjectName("cmbShow3D")
        self.cmbMode3D.setToolTip("Select 3D-plot mode.")
        self.cmbMode3D.setCurrentIndex(0)
        self.cmbMode3D.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

        self.chkColormap_r = QtGui.QCheckBox(self)
        self.chkColormap_r.setText("reverse")
        self.chkColormap_r.setToolTip("reverse colormap")
        self.chkColormap_r.setChecked(True)

        self.cmbColormap = QtGui.QComboBox(self)
        self._init_cmb_colormap()
        self.cmbColormap.setToolTip("Select colormap")

        self.chkColBar = QtGui.QCheckBox(self)
        self.chkColBar.setText("Colorbar")
        self.chkColBar.setObjectName("chkColBar")
        self.chkColBar.setToolTip("Show colorbar")
        self.chkColBar.setChecked(False)

        self.chkLighting = QtGui.QCheckBox(self)
        self.chkLighting.setText("Lighting")
        self.chkLighting.setObjectName("chkLighting")
        self.chkLighting.setToolTip("Enable light source")
        self.chkLighting.setChecked(False)

        self.lblAlpha = QtGui.QLabel("Alpha")
        self.diaAlpha = QtGui.QDial(self)
        self.diaAlpha.setRange(0., 10.)
        self.diaAlpha.setValue(8)
        self.diaAlpha.setTracking(False) # produce less events when turning
        self.diaAlpha.setFixedHeight(30)
        self.diaAlpha.setFixedWidth(30)
        self.diaAlpha.setWrapping(False)
        self.diaAlpha.setToolTip("Set transparency for surf and contour plot.")

        self.lblHatch = QtGui.QLabel("Stride")
        self.diaHatch = QtGui.QDial(self)
        self.diaHatch.setRange(0., 9.)
        self.diaHatch.setValue(7)
        self.diaHatch.setTracking(False) # produce less events when turning
        self.diaHatch.setFixedHeight(30)
        self.diaHatch.setFixedWidth(30)
        self.diaHatch.setWrapping(False)
        self.diaHatch.setToolTip("Set hatching for H(jw).")

        self.chkContour2D = QtGui.QCheckBox(self)
        self.chkContour2D.setText("Contour2D")
        self.chkContour2D.setObjectName("chkContour2D")
        self.chkContour2D.setToolTip("Plot 2D-contours for real and imaginary part")
        self.chkContour2D.setChecked(False)

        #----------------------------------------------------------------------
        # LAYOUT for UI widgets
        #----------------------------------------------------------------------
        spc = QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.Expanding,
                                       QtGui.QSizePolicy.Minimum)
        self.layGSelect = QtGui.QGridLayout()
        self.layGSelect.setObjectName('plotSpecSelect')
        self.layGSelect.addWidget(self.chkLog, 0, 0)
        self.layGSelect.addWidget(self.chkPolar, 1, 0)
        self.layGSelect.addWidget(self.lblTop, 0, 2)
        self.layGSelect.addWidget(self.lblBottom, 1, 2)
        self.layGSelect.addWidget(self.ledTop, 0, 4)
        self.layGSelect.addWidget(self.ledBottom, 1, 4)
        self.layGSelect.addItem(spc, 0,5)

        self.layGSelect.addWidget(self.chkUC, 0, 6)
        self.layGSelect.addWidget(self.chkHf, 1, 6)
        self.layGSelect.addWidget(self.chkPZ, 0, 8)
        self.layGSelect.addWidget(self.cmbColormap, 0,10,1,1)
        self.layGSelect.addWidget(self.chkColormap_r, 1,10)
        self.layGSelect.addWidget(self.cmbMode3D, 0, 12)
        self.layGSelect.addWidget(self.chkContour2D, 1, 12)
        self.layGSelect.addWidget(self.chkLighting, 0, 14)
        self.layGSelect.addWidget(self.chkColBar, 1, 14)

        self.layGSelect.addWidget(self.diaAlpha, 0, 16)
        self.layGSelect.addWidget(self.lblAlpha, 0, 15)
        self.layGSelect.addWidget(self.diaHatch, 1, 16)
        self.layGSelect.addWidget(self.lblHatch, 1, 15)


#        self.layHChkBoxes.addStretch(1)

        self.mplwidget = MplWidget()

#        self.mplwidget.layVMainMpl.addStretch(1)
        self.mplwidget.layVMainMpl.addLayout(self.layGSelect)

#        self.mplwidget.setFocus()
        # make this the central widget, taking all available space:
        self.setCentralWidget(self.mplwidget)
        
        self._init_axes()

        self._init_grid() # initialize grid and do initial plot

#        self.draw()

        #=============================================
        # Signals & Slots
        #=============================================
        self.chkLog.clicked.connect(self.logClicked)
        self.ledBottom.editingFinished.connect(self.logClicked)
        self.ledTop.editingFinished.connect(self.logClicked)

        self.chkPolar.clicked.connect(self._init_grid)
        self.chkUC.clicked.connect(self.draw)
        self.chkHf.clicked.connect(self.draw)
        self.chkPZ.clicked.connect(self.draw)
        self.cmbMode3D.currentIndexChanged.connect(self.draw)
        self.chkColBar.clicked.connect(self.draw)

        self.cmbColormap.currentIndexChanged.connect(self.draw)
        self.chkColormap_r.clicked.connect(self._init_cmb_colormap)

        self.chkLighting.clicked.connect(self.draw)
        self.diaAlpha.valueChanged.connect(self.draw)
        self.diaHatch.valueChanged.connect(self.draw)
        self.chkContour2D.clicked.connect(self.draw)

        logger.debug("UI initialized")


#------------------------------------------------------------------------------
    def _init_cmb_colormap(self):
        """ (Re-)Load combobox with available colormaps"""
        if self.chkColormap_r.isChecked():
            cmap_list = [m for m in cm.datad if m.endswith("_r")]
        else:
            cmap_list = [m for m in cm.datad if not m.endswith("_r")]
        # *_r colormaps reverse the color order
        cmap_list.sort()
        self.cmbColormap.blockSignals(True) # don't send signal "indexChanged"
        self.cmbColormap.clear()
        self.cmbColormap.addItems(cmap_list)
        self.cmbColormap.blockSignals(False)
        self.cmbColormap.setCurrentIndex(0)
        # Colormaps: 'hsv', 'jet', 'jet_r', 'bone', 'prism' 'gray', 'prism',
        # 'coolwarm', 'RdYlBu'        #cmap = cm.RdYlBu_r


#------------------------------------------------------------------------------
    def _init_grid(self):
        """ Initialize (x,y,z) coordinate grid + (re)draw plot."""
        phi_UC = np.linspace(0, 2*pi, 400, endpoint=True) # angles for unit circle
        self.xy_UC = np.exp(1j * phi_UC) # x,y coordinates of unity circle

        steps = 100              # number of steps for x, y, r, phi
        rmin = 0;    rmax = 1.2  # polar range limits
        #
        self.xmin = -1.5; self.xmax = 1.5  # cartesian range limits
        self.ymin = -1.5; self.ymax = 1.5
        #
        zmax_rel = 5 # Max. displayed z - value relative to max|H(f)|

        # Calculate grids for 3D-Plots
        dr = rmax / steps * 2 # grid size for polar range
        dx = (self.xmax - self.xmin) / steps
        dy = (self.ymax - self.ymin) / steps # grid size cartesian range

        if self.chkPolar.isChecked(): # # Plot circular range in 3D-Plot
            [r, phi] = np.meshgrid(np.arange(rmin, rmax, dr),
                            np.linspace(0, 2 * pi, steps, endpoint=True))
            self.x = r * cos(phi)
            self.y = r * sin(phi)
        else: # cartesian grid
            [self.x, self.y] = np.meshgrid(np.arange(self.xmin, self.xmax, dx),
                                            np.arange(self.ymin, self.ymax, dy))

        self.z = self.x + 1j*self.y # create coordinate grid for complex plan

        self.draw()

#------------------------------------------------------------------------------
    def _init_axes(self):
        """Initialize and clear the axes
        see http://stackoverflow.com/questions/4575588/matplotlib-3d-plot-with-pyqt4-in-qtabwidget-mplwidget
        """
        self.mplwidget.fig.clf() # needed to get rid of colormap
        self.ax3d = self.mplwidget.fig.add_subplot(111, projection='3d')


#------------------------------------------------------------------------------
    def logClicked(self):
        """ Change scale and settings to log / lin """
        self.log = self.chkLog.isChecked()
        if self.sender().objectName() == 'chkLog': # origin of signal that triggered the slot
            if self.log:

                self.ledBottom.setText(str(self.zmin_dB))
                self.zmax_dB = np.round(20 * log10(self.zmax), 2)
                self.ledTop.setText(str(self.zmax_dB))
            else:
                self.ledBottom.setText(str(self.zmin))
                self.zmax = np.round(10**(self.zmax_dB / 20), 2)
                self.ledTop.setText(str(self.zmax))
        else:
            if self.log:
                self.zmin_dB = float(self.ledBottom.text())
                self.zmax_dB = float(self.ledTop.text())
            else:
                self.zmin = float(self.ledBottom.text())
                self.zmax = float(self.ledTop.text())

        self.draw()


#------------------------------------------------------------------------------
    def draw(self):
        """
        Main drawing entry point: Check whether updating is enabled in the
        toolbar and then perform the actual plot
        """
        if self.mplwidget.mplToolbar.enable_update:
            self.draw_3d()


#------------------------------------------------------------------------------
    def draw_3d(self):
        """
        Draw various 3D plots
        """
        self._init_axes() # needed to get rid of colormap


        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        zz = np.array(fb.fil[0]['zpk'][0])
        pp = np.array(fb.fil[0]['zpk'][1])

        wholeF = fb.fil[0]['freqSpecsRangeType'] != 'half'
        f_S = fb.fil[0]['f_S']
        N_FFT = rc.params['N_FFT']
        alpha = self.diaAlpha.value()/10.
        cmap = cm.get_cmap(str(self.cmbColormap.currentText()))

        #cNorm  = colors.Normalize(vmin=0, vmax=values[-1])
        #scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

        #-----------------------------------------------------------------------------
        # Define 3D-Plotting Options
        #-----------------------------------------------------------------------------
        OPT_3D_FORCE_ZMAX = True # Enforce absolute limit for 3D-Plot
        OPT_3D_MSTRIDE = 2 # step size for mesh and cont


        [w, H] = sig.freqz(bb, aa, N_FFT, wholeF) # calculate H(w) along the
                                                # upper half of unity circle
                                                # w runs from 0 ... pi, length = N_FFT
        f = w / (2 * pi) * f_S                  # translate w to absolute frequencies

        H_abs = abs(H)
        H_max = max(H_abs)
        H_max_dB = 20*log10(H_max)
        F_max = f[np.argmax(H_abs)]


        H_min = min(H_abs)
        H_min_dB = 20*log10(H_min)
        F_min = f[np.argmin(H_abs)]

        plevel_rel = 1.05 # height of plotted pole position relative to zmax
        zlevel_rel = 0.1 # height of plotted zero position relative to zmax


        # calculate H(jw)| along the unity circle and |H(z)|, each clipped
        # between bottom and top
        if self.chkLog.isChecked():
            bottom = np.floor(max(self.zmin_dB, H_min_dB) / 10) * 10
            top = self.zmax_dB
            zlevel = bottom - (top - bottom) * (zlevel_rel)
            H_UC = H_mag(bb, aa, self.xy_UC, top, H_min=bottom, log=True)
            Hmag = H_mag(bb, aa, self.z, top, H_min=bottom, log=True)

            if self.cmbMode3D.currentText() == 'None': # "Poleposition" for H(f) plot only
                plevel_top = 2 * bottom - zlevel # height of displayed pole position
                plevel_btm = bottom
            else:
                plevel_top = top + (top - bottom) * (plevel_rel - 1)
                plevel_btm = top

        else:
            bottom = max(self.zmin, H_min)
            top = self.zmax
        #   top = zmax_rel * H_max # calculate display top from max. of H(f)
            H_UC = H_mag(bb, aa, self.xy_UC, top, H_min=bottom)
            Hmag = H_mag(bb, aa, self.z, top, H_min=bottom)

            zlevel = zlevel_rel * top # height of displayed zero position

            if self.cmbMode3D.currentText() == 'None': # "Poleposition" for H(f) plot only
                plevel_top = H_max * 0.3 # height of displayed pole position
                plevel_btm = bottom
            else:
                plevel_top = plevel_rel * top
                plevel_btm = top

        #===============================================================
        ## plot unit circle
        #===============================================================
        if self.chkUC.isChecked():
        # Plot unit circle and marker at (1,0):
            self.ax3d.plot(self.xy_UC.real, self.xy_UC.imag,
                           ones(len(self.xy_UC)) * bottom, lw=2, color='k')
            self.ax3d.plot([0.97, 1.03], [0, 0], [bottom, bottom], lw=2, color='k')

        #===============================================================
        ## plot ||H(f)| along unit circle as 3D-lineplot
        #===============================================================
        if self.chkHf.isChecked():
            self.ax3d.plot(self.xy_UC.real, self.xy_UC.imag, H_UC, alpha = 0.5)
            # draw once more as dashed white line to improve visibility
            self.ax3d.plot(self.xy_UC.real, self.xy_UC.imag, H_UC, 'w--')


            NL = 10 - self.diaHatch.value() # plot line every NL points on the UC
            if NL < 10:
                for k in range(len(self.xy_UC[::NL])):
                    self.ax3d.plot([self.xy_UC.real[::NL][k], self.xy_UC.real[::NL][k]],
                        [self.xy_UC.imag[::NL][k], self.xy_UC.imag[::NL][k]],
                        [np.ones(len(self.xy_UC[::NL]))[k]*bottom, H_UC[::NL][k]],
                         linewidth=1, color=(0.5, 0.5, 0.5))
        #===============================================================
        ## plot Poles and Zeros
        #===============================================================
        if self.chkPZ.isChecked():

            PN_SIZE = 8 # size of P/N symbols

            # Plot zero markers at |H(z_i)| = zlevel with "stems":
            self.ax3d.plot(zz.real, zz.imag, ones(len(zz)) * zlevel, 'o',
               markersize=PN_SIZE, markeredgecolor='blue', markeredgewidth=2.0,
                markerfacecolor='none')
            for k in range(len(zz)): # plot zero "stems"
                self.ax3d.plot([zz[k].real, zz[k].real], [zz[k].imag, zz[k].imag],
                            [bottom, zlevel], linewidth=1, color='b')

            # Plot the poles at |H(z_p)| = plevel with "stems":
            self.ax3d.plot(np.real(pp), np.imag(pp), plevel_top,
              'x', markersize=PN_SIZE, markeredgewidth=2.0, markeredgecolor='red')
            for k in range(len(pp)): # plot pole "stems"
                self.ax3d.plot([pp[k].real, pp[k].real], [pp[k].imag, pp[k].imag],
                            [plevel_btm, plevel_top], linewidth=1, color='r')

        #===============================================================
        ## 3D-Plots of |H(z)| clipped between |H(z)| = top
        #===============================================================

        m_cb = cm.ScalarMappable(cmap=cmap)    # proxy object that is mappable
        m_cb.set_array(Hmag)                   # for colorbar

        #---------------------------------------------------------------
        ## 3D-mesh plot
        #---------------------------------------------------------------
        if self.cmbMode3D.currentText() == 'Mesh':
        #    fig_mlab = mlab.figure(fgcolor=(0., 0., 0.), bgcolor=(1, 1, 1))
        #    self.ax3d.set_zlim(0,2)
            self.ax3d.plot_wireframe(self.x, self.y, Hmag, rstride=5,
                    cstride=NL, linewidth=1, color='gray')

        #---------------------------------------------------------------
        ## 3D-surface plot
        #---------------------------------------------------------------
        # http://stackoverflow.com/questions/28232879/phong-shading-for-shiny-python-3d-surface-plots
        elif self.cmbMode3D.currentText() == 'Surf':
            if MLAB:
                ## Mayavi
                surf = mlab.surf(self.x, self.y, H_mag, colormap='RdYlBu', warp_scale='auto')
                # Change the visualization parameters.
                surf.actor.property.interpolation = 'phong'
                surf.actor.property.specular = 0.1
                surf.actor.property.specular_power = 5
                mlab.show()
            else:
                # TODO: normalize for log. values and lighting = False
                if self.chkLighting.isChecked():
                    ls = LightSource(azdeg=0, altdeg=65) # Create light source object
                    rgb = ls.shade(Hmag, cmap=cmap) # Shade data, creating an rgb array
                    cmap_surf = None
                else:
                    rgb = cmap(Hmag)
                    cmap_surf = None

    #            s = self.ax3d.plot_surface(self.x, self.y, Hmag,
    #                    alpha=OPT_3D_ALPHA, rstride=1, cstride=1, cmap=cmap,
    #                    linewidth=0, antialiased=False, shade=True, facecolors = rgb)
    #            s.set_edgecolor('gray')
                s = self.ax3d.plot_surface(self.x, self.y, Hmag,
                        alpha=alpha, rstride=1, cstride=1,
                        linewidth=0, antialiased=True, facecolors = rgb)
                s.set_edgecolor(None)
        #---------------------------------------------------------------
        ## 3D-Contour plot
        #---------------------------------------------------------------
        elif self.cmbMode3D.currentText() == 'Contour':
            s = self.ax3d.contourf3D(self.x, self.y, Hmag, 20, alpha=alpha, cmap=cmap)

        #---------------------------------------------------------------
        ## 2D-Contour plot
        # TODO: 2D contour plots do not plot correctly together with 3D plots in
        #       current matplotlib 1.4.3 -> disable them for now
        # TODO: zdir = x / y delivers unexpected results -> rather plot max(H)
        #       along the other axis?
        # TODO: colormap is created depending on the zdir = 'z' contour plot
        #       -> set limits of (all) other plots manually?
        if self.chkContour2D.isChecked():
#            self.ax3d.contourf(x, y, Hmag, 20, zdir='x', offset=xmin,
#                         cmap=cmap, alpha = alpha)#, vmin = bottom)#, vmax = top, vmin = bottom)
#            self.ax3d.contourf(x, y, Hmag, 20, zdir='y', offset=ymax,
#                         cmap=cmap, alpha = alpha)#, vmin = bottom)#, vmax = top, vmin = bottom)
            s = self.ax3d.contourf(self.x, self.y, Hmag, 20, zdir='z',
                               offset=bottom - (top - bottom) * 0.05,
                                cmap=cmap, alpha=alpha)
            
        # plot colorbar for suitable plot modes
        if self.chkColBar.isChecked() and (self.chkContour2D.isChecked() or
                str(self.cmbMode3D.currentText()) in {'Contour', 'Surf'}):
                            self.colb = self.mplwidget.fig.colorbar(m_cb,
                                ax=self.ax3d, shrink=0.8, aspect=20,
                                pad=0.02, fraction=0.08)


        self.ax3d.set_xlim3d(self.xmin, self.xmax)
        self.ax3d.set_ylim3d(self.ymin, self.ymax)
        self.ax3d.set_zlim3d(bottom, top)

        self.ax3d.set_xlabel('Re')#(fb.fil[0]['plt_fLabel'])
        self.ax3d.set_ylabel('Im') #(r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $')
#        self.ax3d.set_zlabel(r'$|H(z)|\; \rightarrow $')
        self.ax3d.set_title(r'3D-Plot of $|H(\mathrm{e}^{\mathrm{j} \Omega})|$ and $|H(z)|$')

        self.mplwidget.redraw()

#------------------------------------------------------------------------------

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    form = Plot3D()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()
