# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for plotting poles and zeros
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

from ..compat import (QWidget, QLabel, QCheckBox, QFrame, QDial, QHBoxLayout,
                      pyqtSlot, pyqtSignal)

import numpy as np
import scipy.signal as sig

import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
from pyfda.pyfda_lib import unique_roots

from pyfda.plot_widgets.mpl_widget import MplWidget

from  matplotlib import patches


class Plot_PZ(QWidget):
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)

    def __init__(self, parent):
        super(Plot_PZ, self).__init__(parent)
        self.data_changed = True   # flag whether filter data has been changed
        self.size_changed = True # flag whether plot has been resized
        self.tool_tip = "Pole / zero plan"
        self.tab_label = "P / Z"

        self._construct_UI()

#------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        logger.debug("Processing {0} | needs_draw = {1}, visible = {2}"\
                     .format(dict_sig, self.data_changed, self.isVisible()))
        if self.isVisible():
            if 'data_changed' in dict_sig or 'home' in dict_sig or self.data_changed:
                self.draw()
                self.data_changed = False
                self.size_changed = False
                self.view_changed = False
            if 'view_changed' in dict_sig or self.view_changed:
                self.update_view()
                self.view_changed = False
                self.size_changed = False
            if 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized'\
                    or self.size_changed:
                self.redraw()
                self.size_changed = False
        else:
            if 'data_changed' in dict_sig:
                self.data_changed = True
            if 'view_changed' in dict_sig:
                self.view_changed = True
            if 'ui_changed' in dict_sig and dict_sig['ui_changed'] == 'resized':
                self.size_changed = True

#------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """
        self.chkHf = QCheckBox("Show |H(f)|", self)
        self.chkHf.setToolTip("<span>Display |H(f)| around unit circle.</span>")
        self.chkHf.setEnabled(True)

        self.chkHfLog = QCheckBox("Log. Scale", self)
        self.chkHfLog.setToolTip("<span>Log. scale for |H(f)|.</span>")
        self.chkHfLog.setEnabled(True)

        self.diaRad_Hf = QDial(self)
        self.diaRad_Hf.setRange(2., 10.)
        self.diaRad_Hf.setValue(2)
        self.diaRad_Hf.setTracking(False) # produce less events when turning
        self.diaRad_Hf.setFixedHeight(30)
        self.diaRad_Hf.setFixedWidth(30)
        self.diaRad_Hf.setWrapping(False)
        self.diaRad_Hf.setToolTip("<span>Set max. radius for |H(f)| plot.</span>")

        self.lblRad_Hf = QLabel("Radius", self)

        self.chkFIR_P = QCheckBox("Plot FIR Poles", self)
        self.chkFIR_P.setToolTip("<span>Show FIR poles at the origin.</span>")
        self.chkFIR_P.setChecked(True)


        layHControls = QHBoxLayout()
        layHControls.addWidget(self.chkHf)
        layHControls.addWidget(self.chkHfLog)
        layHControls.addWidget(self.diaRad_Hf)
        layHControls.addWidget(self.lblRad_Hf)
        layHControls.addStretch(10)
        layHControls.addWidget(self.chkFIR_P)

        #----------------------------------------------------------------------
        #               ### frmControls ###
        #
        # This widget encompasses all control subwidgets
        #----------------------------------------------------------------------
        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)

        #----------------------------------------------------------------------
        #               ### mplwidget ###
        #
        # main widget, encompassing the other widgets
        #----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.setLayout(self.mplwidget.layVMainMpl)

        self.init_axes()

        self.draw() # calculate and draw poles and zeros

        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)
        self.chkHf.clicked.connect(self.draw)
        self.chkHfLog.clicked.connect(self.draw)
        self.diaRad_Hf.valueChanged.connect(self.draw)
        self.chkFIR_P.clicked.connect(self.draw)

#------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes
        """
        if self.chkHf.isChecked():
            self.ax = self.mplwidget.fig.add_subplot(111)
        else:
            self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()
        self.ax.get_xaxis().tick_bottom() # remove axis ticks on top
        self.ax.get_yaxis().tick_left() # remove axis ticks right

#------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etcs without recalculating H(f)
        -- not yet implemented, just use draw() for the moment
        """
        self.draw()

#------------------------------------------------------------------------------
    def draw(self):
        self.chkFIR_P.setVisible(fb.fil[0]['ft']=='FIR')
        self.init_axes()
        self.draw_pz()

#------------------------------------------------------------------------------
    def draw_pz(self):
        """
        (re)draw P/Z plot
        """
        p_marker = params['P_Marker']
        z_marker = params['Z_Marker']

        zpk = fb.fil[0]['zpk']

        # add antiCausals if they exist (must take reciprocal to plot)
        if 'rpk' in fb.fil[0]:
            zA = fb.fil[0]['zpk'][0]
            zA = np.conj(1./zA)
            pA = fb.fil[0]['zpk'][1]
            pA = np.conj(1./pA)
            zC = np.append(zpk[0],zA)
            pC = np.append(zpk[1],pA)
            zpk[0] = zC
            zpk[1] = pC

        self.ax.clear()

        [z,p,k] = self.zplane(z = zpk[0], p = zpk[1], k = zpk[2], plt_ax = self.ax,
            plt_poles=self.chkFIR_P.isChecked() or fb.fil[0]['ft'] == 'IIR',
            mps = p_marker[0], mpc = p_marker[1], mzs = z_marker[0], mzc = z_marker[1])

        self.ax.set_title(r'Pole / Zero Plot')
        self.ax.set_xlabel('Real axis')
        self.ax.set_ylabel('Imaginary axis')

        self.draw_Hf(r = self.diaRad_Hf.value())

        self.redraw()

#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

#------------------------------------------------------------------------------
    def zplane(self, b=None, a=1, z=None, p=None, k=1,  pn_eps=1e-3, analog=False,
              plt_ax = None, plt_poles=True, style='square', anaCircleRad=0, lw=2,
              mps = 10, mzs = 10, mpc = 'r', mzc = 'b', plabel = '', zlabel = ''):
        """
        Plot the poles and zeros in the complex z-plane either from the
        coefficients (`b,`a) of a discrete transfer function `H`(`z`) (zpk = False)
        or directly from the zeros and poles (z,p) (zpk = True).

        When only b is given, an FIR filter with all poles at the origin is assumed.

        Parameters
        ----------
        b :  array_like
             Numerator coefficients (transversal part of filter)
             When b is not None, poles and zeros are determined from the coefficients
             b and a

        a :  array_like (optional, default = 1 for FIR-filter)
             Denominator coefficients (recursive part of filter)

        z :  array_like, default = None
             Zeros
             When b is None, poles and zeros are taken directly from z and p

        p :  array_like, default = None
             Poles

        analog : boolean (default: False)
            When True, create a P/Z plot suitable for the s-plane, i.e. suppress
            the unit circle (unless anaCircleRad > 0) and scale the plot for
            a good display of all poles and zeros.

        pn_eps : float (default : 1e-2)
             Tolerance for separating close poles or zeros

        plt_ax : handle to axes for plotting (default: None)
            When no axes is specified, the current axes is determined via plt.gca()

        plt_poles : Boolean (default : True)
            Plot poles. This can be used to suppress poles for FIR systems
            where all poles are at the origin.

        style : string (default: 'square')
            Style of the plot, for style == 'square' make scale of x- and y-
            axis equal.

        mps : integer  (default: 10)
            Size for pole marker

        mzs : integer (default: 10)
            Size for zero marker

        mpc : char (default: 'r')
            Pole marker colour

        mzc : char (default: 'b')
            Zero marker colour

        lw : integer (default:  2)
            Linewidth for unit circle

        plabel, zlabel : string (default: '')
            This string is passed to the plot command for poles and zeros and
            can be displayed by legend()


        Returns
        -------
        z, p, k : ndarray


        Notes
        -----
        """
        # TODO:
        # - polar option
        # - add keywords for color of circle -> **kwargs
        # - add option for multi-dimensional arrays and zpk data

        # make sure that all inputs are arrays
        b = np.atleast_1d(b)
        a = np.atleast_1d(a)
        z = np.atleast_1d(z) # make sure that p, z  are arrays
        p = np.atleast_1d(p)

        if b.any(): # coefficients were specified
            if len(b) < 2 and len(a) < 2:
                logger.error('No proper filter coefficients: both b and a are scalars!')
                return z, p, k

            # The coefficients are less than 1, normalize the coefficients
            if np.max(b) > 1:
                kn = np.max(b)
                b = b / float(kn)
            else:
                kn = 1.

            if np.max(a) > 1:
                kd = np.max(a)
                a = a / abs(kd)
            else:
                kd = 1.

            # Calculate the poles, zeros and scaling factor
            p = np.roots(a)
            z = np.roots(b)
            k = kn/kd
        elif not (len(p) or len(z)): # P/Z were specified
            logger.error('Either b,a or z,p must be specified!')
            return z, p, k

        # find multiple poles and zeros and their multiplicities
        if len(p) < 2: # single pole, [None] or [0]
            if not p or p == 0: # only zeros, create equal number of poles at origin
                p = np.array(0,ndmin=1) #
                num_p = np.atleast_1d(len(z))
            else:
                num_p = [1.] # single pole != 0
        else:
            #p, num_p = sig.signaltools.unique_roots(p, tol = pn_eps, rtype='avg')
            p, num_p = unique_roots(p, tol = pn_eps, rtype='avg')
    #        p = np.array(p); num_p = np.ones(len(p))
        if len(z) > 0:
            z, num_z = unique_roots(z, tol = pn_eps, rtype='avg')
    #        z = np.array(z); num_z = np.ones(len(z))
            #z, num_z = sig.signaltools.unique_roots(z, tol = pn_eps, rtype='avg')
        else:
            num_z = []

        ax = plt_ax#.subplot(111)
        if analog == False:
            # create the unit circle for the z-plane
            uc = patches.Circle((0,0), radius=1, fill=False,
                                color='grey', ls='solid', zorder=1)
            ax.add_patch(uc)
            if style == 'square':
                r = 1.1
                ax.axis([-r, r, -r, r], 'equal')
                ax.axis('equal')
        #    ax.spines['left'].set_position('center')
        #    ax.spines['bottom'].set_position('center')
        #    ax.spines['right'].set_visible(True)
        #    ax.spines['top'].set_visible(True)

        else: # s-plane
            if anaCircleRad > 0:
                # plot a circle with radius = anaCircleRad
                uc = patches.Circle((0,0), radius=anaCircleRad, fill=False,
                                    color='grey', ls='solid', zorder=1)
                ax.add_patch(uc)
            # plot real and imaginary axis
            ax.axhline(lw=2, color = 'k', zorder=1)
            ax.axvline(lw=2, color = 'k', zorder=1)

        # Plot the zeros
        ax.scatter(z.real, z.imag, s=mzs*mzs, zorder=2, marker = 'o',
                   facecolor = 'none', edgecolor = mzc, lw = lw, label=zlabel)
        # and print their multiplicity
        for i in range(len(z)):
            logger.debug('z: {0} | {1} | {2}'.format(i, z[i], num_z[i]))
            if num_z[i] > 1:
                ax.text(np.real(z[i]), np.imag(z[i]),'  (' + str(num_z[i]) +')',
                                va = 'top', color=mzc)
        if plt_poles:
            # Plot the poles
            ax.scatter(p.real, p.imag, s=mps*mps, zorder=2, marker='x',
                       color=mpc, lw=lw, label=plabel)
            # and print their multiplicity
            for i in range(len(p)):
                logger.debug('p:{0} | {1} | {2}'.format(i, p[i], num_p[i]))
                if num_p[i] > 1:
                    ax.text(np.real(p[i]), np.imag(p[i]), '  (' + str(num_p[i]) +')',
                                    va = 'bottom', color=mpc)

            # increase distance between ticks and labels
            # to give some room for poles and zeros
        for tick in ax.get_xaxis().get_major_ticks():
            tick.set_pad(12.)
            tick.label1 = tick._get_text1()
        for tick in ax.get_yaxis().get_major_ticks():
            tick.set_pad(12.)
            tick.label1 = tick._get_text1()

        xl = ax.get_xlim(); Dx = max(abs(xl[1]-xl[0]), 0.05)
        yl = ax.get_ylim(); Dy = max(abs(yl[1]-yl[0]), 0.05)
        ax.set_xlim((xl[0]-Dx*0.05, max(xl[1]+Dx*0.05,0)))
        ax.set_ylim((yl[0]-Dy*0.05, yl[1] + Dy*0.05))

        return z, p, k

#------------------------------------------------------------------------------

    def draw_Hf(self, r=2):
        """
        Draw the magnitude frequency response around the UC
        """
        self.chkHfLog.setVisible(self.chkHf.isChecked())
        self.diaRad_Hf.setVisible(self.chkHf.isChecked())
        self.lblRad_Hf.setVisible(self.chkHf.isChecked())
        if not self.chkHf.isChecked():
            return
        ba = fb.fil[0]['ba']
        w, H = sig.freqz(ba[0], ba[1], worN=params['N_FFT'], whole=True)
        H = np.abs(H)
        if self.chkHfLog.isChecked():
            H = np.clip(np.log10(H), -6, None) # clip to -120 dB
            H = H - np.max(H) # shift scale to H_min ... 0
            H = 1 + (r-1) * (1 + H / abs(np.min(H))) # scale to 1 ... r
        else:
            H = 1 + (r-1) * H / np.max(H)  #  map |H(f)| to a range 1 ... r
        y = H * np.sin(w)
        x = H * np.cos(w)

        self.ax.plot(x,y, label="|H(f)|")
        uc = patches.Circle((0,0), radius=r, fill=False,
                                    color='grey', ls='dashed', zorder=1)
        self.ax.add_patch(uc)

        xl = self.ax.get_xlim()
        xmax = max(abs(xl[0]), abs(xl[1]), r*1.05)
        yl = self.ax.get_ylim()
        ymax = max(abs(yl[0]), abs(yl[1]), r*1.05)
        self.ax.set_xlim((-xmax, xmax))
        self.ax.set_ylim((-ymax, ymax))

#------------------------------------------------------------------------------

def main():
    import sys
    from ..compat import QApplication

    app = QApplication(sys.argv)
    mainw = Plot_PZ(None)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
