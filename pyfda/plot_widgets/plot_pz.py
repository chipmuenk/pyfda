# -*- coding: utf-8 -*-
"""
Widget for plotting poles and zeros

Author: Christian Muenker 2015
"""
from __future__ import print_function, division, unicode_literals, absolute_import

from PyQt4 import QtGui
import numpy as np

import pyfda.filterbroker as fb
import pyfda.pyfda_rc as rc

from pyfda.pyfda_lib import unique_roots

from pyfda.plot_widgets.plot_utils import MplWidget#, MplCanvas

from  matplotlib import patches # TODO: should not be imported here?!

class PlotPZ(QtGui.QWidget):

    def __init__(self, parent): 
        super(PlotPZ, self).__init__(parent)

        self.layHChkBoxes = QtGui.QHBoxLayout()
        self.layHChkBoxes.addStretch(10)

        #----------------------------------------------------------------------
        # mplwidget
        #----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)

        self.mplwidget.layVMainMpl.addLayout(self.layHChkBoxes)
        
        self.setLayout(self.mplwidget.layVMainMpl)

        # make this the central widget, taking all available space:
 #       self.setCentralWidget(self.mplwidget)
        
        self._init_axes()

        self.draw() # calculate and draw poles and zeros

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
#        self.btnWhatever.clicked.connect(self.draw)

#------------------------------------------------------------------------------
    def _init_axes(self):
        """Initialize and clear the axes
        """
#        self.ax = self.mplwidget.ax
        self.ax = self.mplwidget.fig.add_subplot(111)
        self.ax.clear()
        
#------------------------------------------------------------------------------
    def update_specs(self):
        """
        Draw the figure with new limits, scale etcs without recalculating H(f)
        -- not yet implemented, just use draw() for the moment
        """
        self.draw()

#------------------------------------------------------------------------------
    def draw(self):
        if self.mplwidget.mplToolbar.enable_update:
            self.draw_pz()
            
#------------------------------------------------------------------------------
    def draw_pz(self):
        """
        (re)draw P/Z plot
        """
        p_marker = rc.params['P_Marker']
        z_marker = rc.params['Z_Marker']
        
        zpk = fb.fil[0]['zpk']

        self.ax.clear()

        [z, p, k] = self.zplane(z = zpk[0], p = zpk[1], k = zpk[2], plt_ax = self.ax, verbose = False, 
            mps = p_marker[0], mpc = p_marker[1], mzs = z_marker[0], mzc = z_marker[1])

        self.ax.set_title(r'Pole / Zero Plot')
        self.ax.set_xlabel('Real axis')
        self.ax.set_ylabel('Imaginary axis')

        self.mplwidget.redraw()
        
        

    def zplane(self, b=None, a=1, z=None, p=None, k =1,  pn_eps=1e-3, analog=False, plt_ax = None,
              verbose=False, style='square', anaCircleRad=0, lw=2,
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
    
        pltLib :  string (default: 'matplotlib')
             Library for plotting the P/Z plane. Currently, only matplotlib is
             implemented. When pltLib = 'none' or when matplotlib is not
             available, only pass the poles / zeros and their multiplicity
    
        verbose : boolean (default: False)
            When verbose == True, print poles / zeros and their multiplicity.
    
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
        # - add keywords for size, color etc. of markers and circle -> **kwargs
        # - add option for multi-dimensional arrays and zpk data
    
        # make sure that all inputs are arrays
        b = np.atleast_1d(b) 
        a = np.atleast_1d(a)
        z = np.atleast_1d(z) # make sure that p, z  are arrays
        p = np.atleast_1d(p)
    
        if b.any(): # coefficients were specified
            zpk = False
            if len(b) < 2 and len(a) < 2:
                raise TypeError(
                'No proper filter coefficients: both b and a are scalars!')
            # The coefficients are less than 1, normalize the coeficients
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
        elif p.any() or z.any(): # P/Z were specified
            zpk = True
        else:
            raise TypeError(
            'No proper filter coefficients: Either b,a or z,p must be specified!')          
    
    
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
    #        t1 = plt.plot(z.real, z.imag, 'go', ms=10, label=label)
    #        plt.setp( t1, markersize=mzs, markeredgewidth=2.0,
    #                  markeredgecolor=mzc, markerfacecolor='none')
        # Plot the poles
        ax.scatter(p.real, p.imag, s=mps*mps, zorder=2, marker='x',
                   color=mpc, lw=lw, label=plabel)
    
         # Print multiplicity of poles / zeros
        for i in range(len(z)):
            if verbose == True: print('z', i, z[i], num_z[i])
            if num_z[i] > 1:
                ax.text(np.real(z[i]), np.imag(z[i]),'  (' + str(num_z[i]) +')',va = 'bottom')
    
        for i in range(len(p)):
            if verbose == True: print('p', i, p[i], num_p[i])
            if num_p[i] > 1:
                ax.text(np.real(p[i]), np.imag(p[i]), '  (' + str(num_p[i]) +')',va = 'bottom')
    
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
    #    print(ax.get_xlim(),ax.get_ylim())
    
    
        return z, p, k

#

#------------------------------------------------------------------------------

def main():
    import sys
    app = QtGui.QApplication(sys.argv)
    mainw = PlotPZ(None)
    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
