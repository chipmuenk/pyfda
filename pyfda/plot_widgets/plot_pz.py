# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

# TODO: Make P/Z draggable -> Bercher, Journey in Signal Processing with Jupyter, 2018.
# TODO: Highlight P/Z selected in P/Z editor

"""
Widget for plotting poles and zeros
"""
from pyfda.libs.compat import (
    QWidget, QLabel, QFrame, QDial, QHBoxLayout, pyqtSignal, QComboBox, QLineEdit)
import numpy as np
import scipy.signal as sig

import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
from pyfda.libs.pyfda_lib import unique_roots, H_mag, to_html, safe_eval
from pyfda.libs.pyfda_qt_lib import (
    PushButton, qcmb_box_populate, qget_cmb_box, qtext_width)

from pyfda.plot_widgets.mpl_widget import MplWidget
from matplotlib.ticker import AutoMinorLocator

from matplotlib import patches, cm

import logging
logger = logging.getLogger(__name__)

classes = {'Plot_PZ': 'P / Z'}  #: Dict containing class name : display name


class Plot_PZ(QWidget):
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.needs_calc = True   # flag whether filter data has been changed
        self.needs_draw = False  # flag whether whether figure needs to be drawn
                                 # with new limits etc. (not implemented yet)
        self.tool_tip = "Pole / zero plan"
        self.tab_label = "P / Z"

        self.cmb_overlay_items = [
            "<span>Add various overlays to P/Z diagram.</span>",
            ("none", "None", ""),
            ("h(f)", "|H(f)|",
             "<span>Show |H(f)| wrapped around the unit circle between 0 resp. -120 dB "
             "and max(H(f)).</span>"),
            ("contour", "Contour", "<span>Show contour lines for |H(z)|</span>"),
            ("contourf", "Contourf", "<span>Show filled contours for |H(z)|</span>"),
            ]
        self.cmb_overlay_default = "none"  # default setting
        self.cmap = "viridis"  # colormap

        self.zmin = 0
        self.zmax = 2
        self.zmin_dB = -80
        self.zmax_dB = np.round(20 * np.log10(self.zmax), 2)
        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict = None) -> None:
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        # logger.info("Processing {0} | needs_draw = {1}, visible = {2}"\
        #              .format(dict_sig, self.needs_calc, self.isVisible()))
        if self.isVisible():
            if 'data_changed' in dict_sig or self.needs_calc\
                    or ('mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'home'):
                self.draw()
                self.needs_calc = False
                self.needs_draw = False
            elif 'view_changed' in dict_sig or self.needs_draw:
                self.update_view()
                self.needs_draw = False
            elif 'ui_global_changed' in dict_sig\
                    and dict_sig['ui_global_changed'] == 'resized':
                self.draw()
            elif 'mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'ui_level':
                self.frmControls.setVisible(self.mplwidget.mplToolbar.a_ui_level == 0)

        else:
            if 'data_changed' in dict_sig:
                self.needs_calc = True
            elif 'view_changed' in dict_sig:
                self.needs_draw = True
            elif 'ui_global_changed' in dict_sig\
                    and dict_sig['ui_global_changed'] == 'resized':
                self.needs_draw = True

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """
        self.lbl_overlay = QLabel(to_html("Overlay:", frmt='bi'), self)
        self.cmb_overlay = QComboBox(self)
        qcmb_box_populate(
            self.cmb_overlay, self.cmb_overlay_items, self.cmb_overlay_default)

        self.but_log = PushButton(" Log.", checked=True, objectName="but_log")
        self.but_log.setToolTip("<span>Log. scale for overlays.</span>")

        self.diaRad_Hf = QDial(self)
        self.diaRad_Hf.setRange(2, 10)
        self.diaRad_Hf.setValue(2)
        self.diaRad_Hf.setTracking(False)  # produce less events when turning
        self.diaRad_Hf.setFixedHeight(30)
        self.diaRad_Hf.setFixedWidth(30)
        self.diaRad_Hf.setWrapping(False)
        self.diaRad_Hf.setToolTip("<span>Set max. radius for |H(f)| plot.</span>")

        self.lblRad_Hf = QLabel("Radius", self)

        self.lblBottom = QLabel(to_html("Bottom =", frmt='bi'), self)
        self.ledBottom = QLineEdit(self, objectName="ledBottom")
        self.ledBottom.setText(str(self.zmin))
        self.ledBottom.setMaximumWidth(qtext_width(N_x=8))
        self.ledBottom.setToolTip("Minimum display value.")
        self.lblBottomdB = QLabel("dB", self)
        self.lblBottomdB.setVisible(self.but_log.isChecked())

        self.lblTop = QLabel(to_html("Top =", frmt='bi'), self)
        self.ledTop = QLineEdit(self, objectName="ledTop")
        self.ledTop.setText(str(self.zmax))
        self.ledTop.setToolTip("Maximum display value.")
        self.ledTop.setMaximumWidth(qtext_width(N_x=8))
        self.lblTopdB = QLabel("dB", self)
        self.lblTopdB.setVisible(self.but_log.isChecked())

        self.but_fir_poles = PushButton(" FIR Poles ", checked=True)
        self.but_fir_poles.setToolTip("<span>Show FIR poles at the origin.</span>")

        layHControls = QHBoxLayout()
        layHControls.addWidget(self.lbl_overlay)
        layHControls.addWidget(self.cmb_overlay)
        layHControls.addWidget(self.but_log)
        layHControls.addWidget(self.diaRad_Hf)
        layHControls.addWidget(self.lblRad_Hf)
        layHControls.addWidget(self.lblTop)
        layHControls.addWidget(self.ledTop)
        layHControls.addWidget(self.lblTopdB)
        layHControls.addWidget(self.lblBottom)
        layHControls.addWidget(self.ledBottom)
        layHControls.addWidget(self.lblBottomdB)
        layHControls.addStretch(10)
        layHControls.addWidget(self.but_fir_poles)

        # ----------------------------------------------------------------------
        #               ### frmControls ###
        #
        # This widget encompasses all control subwidgets
        # ----------------------------------------------------------------------
        self.frmControls = QFrame(self, objectName="frmControls")
        self.frmControls.setLayout(layHControls)

        # ----------------------------------------------------------------------
        #               ### mplwidget ###
        #
        # main widget, encompassing the other widgets
        # ----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['wdg_margins'])
        self.mplwidget.mplToolbar.a_he.setEnabled(True)
        self.mplwidget.mplToolbar.a_he.info = "manual/plot_pz.html"
        self.mplwidget.mplToolbar.a_ui_num_levels = 2
        self.setLayout(self.mplwidget.layVMainMpl)

        self.init_axes()

        self._log_clicked()  # calculate and draw poles and zeros

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)
        self.cmb_overlay.currentIndexChanged.connect(self.draw)
        self.but_log.clicked.connect(self._log_clicked)
        self.ledBottom.editingFinished.connect(self._log_clicked)
        self.ledTop.editingFinished.connect(self._log_clicked)
        self.diaRad_Hf.valueChanged.connect(self.draw)
        self.but_fir_poles.clicked.connect(self.draw)

    # --------------------------------------------------------------------------
    def _log_clicked(self):
        """
        Change scale and settings to log / lin when log setting is changed
        Update min / max settings when lineEdits have been edited
        """
        # clicking but_log triggered the slot or initialization
        if self.sender() is None or self.sender().objectName() == 'but_log':
            if self.but_log.isChecked():
                self.ledBottom.setText(str(self.zmin_dB))
                self.zmax_dB = np.round(20 * np.log10(self.zmax), 2)
                self.ledTop.setText(str(self.zmax_dB))
            else:
                self.ledBottom.setText(str(self.zmin))
                self.zmax = np.round(10**(self.zmax_dB / 20), 2)
                self.ledTop.setText(str(self.zmax))

        else:  # finishing a lineEdit field triggered the slot
            if self.but_log.isChecked():
                self.zmin_dB = safe_eval(
                    self.ledBottom.text(), self.zmin_dB, return_type='float')
                self.ledBottom.setText(str(self.zmin_dB))
                self.zmax_dB = safe_eval(
                    self.ledTop.text(), self.zmax_dB, return_type='float')
                self.ledTop.setText(str(self.zmax_dB))
            else:
                self.zmin = safe_eval(
                    self.ledBottom.text(), self.zmin, return_type='float')
                self.ledBottom.setText(str(self.zmin))
                self.zmax = safe_eval(self.ledTop.text(), self.zmax, return_type='float')
                self.ledTop.setText(str(self.zmax))

        self.draw()

    # --------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes (this is only run once)
        """
        self.mplwidget.fig.clf()  # needed to get rid of colorbar
        if len(self.mplwidget.fig.get_axes()) == 0:  # empty figure, no axes
            self.ax = self.mplwidget.fig.subplots()  # .add_subplot(111)
        self.ax.xaxis.tick_bottom()  # remove axis ticks on top
        self.ax.yaxis.tick_left()  # remove axis ticks right

    # --------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etcs without recalculating H(f)
        -- not yet implemented, just use draw() for the moment
        """
        self.draw()

    # --------------------------------------------------------------------------
    def draw(self):
        self.but_fir_poles.setVisible(fb.fil[0]['ft'] == 'FIR')
        contour = qget_cmb_box(self.cmb_overlay) in {"contour", "contourf"}
        self.ledBottom.setVisible(contour)
        self.lblBottom.setVisible(contour)
        self.lblBottomdB.setVisible(contour and self.but_log.isChecked())
        self.ledTop.setVisible(contour)
        self.lblTop.setVisible(contour)
        self.lblTopdB.setVisible(contour and self.but_log.isChecked())

        if True:
            self.init_axes()
        self.draw_pz()

    # --------------------------------------------------------------------------
    def draw_pz(self):
        """
        (re)draw P/Z plot
        """
        p_marker = params['P_Marker']
        z_marker = params['Z_Marker']

        zpk = fb.fil[0]['zpk']

        self.ax.clear()

        [z, p, k] = self.zplane(
            z=zpk[0], p=zpk[1], k=zpk[2], plt_ax=self.ax,
            plt_poles=self.but_fir_poles.isChecked() or fb.fil[0]['ft'] == 'IIR',
            mps=p_marker[0], mpc=p_marker[1], mzs=z_marker[0], mzc=z_marker[1])

        self.ax.xaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
        self.ax.yaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
        self.ax.set_title(r'Pole / Zero Plot')
        self.ax.set_xlabel('Real axis')
        self.ax.set_ylabel('Imaginary axis')

        overlay = qget_cmb_box(self.cmb_overlay)
        self.but_log.setVisible(overlay != "none")

        self.draw_Hf(r=self.diaRad_Hf.value(), Hf_visible=(overlay == "h(f)"))

        self.draw_contours(overlay)

        self.redraw()

    # --------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

    # --------------------------------------------------------------------------
    def zplane(self, b=None, a=1, z=None, p=None, k=1,  pn_eps=1e-3, analog=False,
               plt_ax=None, plt_poles=True, style='equal', anaCircleRad=0, lw=2,
               mps=10, mzs=10, mpc='r', mzc='b', plabel='', zlabel=''):
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

        style : string (default: 'scaled')
            Style of the plot, for `style == 'scaled'` make scale of x- and y-
            axis equal, `style == 'equal'` forces x- and y-axes to be equal. This
            is passed as an argument to the matplotlib `ax.axis(style)`

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

        # make sure that all inputs are (at least 1D) arrays
        b = np.atleast_1d(b)
        a = np.atleast_1d(a)
        z = np.atleast_1d(z)
        p = np.atleast_1d(p)

        if b.any():  # coefficients were specified
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
        elif not (len(p) or len(z)):  # P/Z were specified
            logger.error('Either b,a or z,p must be specified!')
            return z, p, k

        # find multiple poles and zeros and their multiplicities
        if len(p) < 2:  # single pole, [None] or [0]
            if not p or p == 0:  # only zeros, create equal number of poles at origin
                p = np.array(0, ndmin=1)
                num_p = np.atleast_1d(len(z))
            else:
                num_p = [1.]  # single pole != 0
        else:
            # p, num_p = sig.signaltools.unique_roots(p, tol = pn_eps, rtype='avg')
            p, num_p = unique_roots(p, tol=pn_eps, rtype='avg')
    #        p = np.array(p); num_p = np.ones(len(p))
        if len(z) > 0:
            z, num_z = unique_roots(z, tol=pn_eps, rtype='avg')
    #        z = np.array(z); num_z = np.ones(len(z))
            # z, num_z = sig.signaltools.unique_roots(z, tol = pn_eps, rtype='avg')
        else:
            num_z = []

        if analog is False:
            # create the unit circle for the z-plane
            uc = patches.Circle((0, 0), radius=1, fill=False,
                                color='grey', ls='solid', zorder=1)
            plt_ax.add_patch(uc)
            plt_ax.axis(style)
        #    ax.spines['left'].set_position('center')
        #    ax.spines['bottom'].set_position('center')
        #    ax.spines['right'].set_visible(True)
        #    ax.spines['top'].set_visible(True)

        else:  # s-plane
            if anaCircleRad > 0:
                # plot a circle with radius = anaCircleRad
                uc = patches.Circle((0, 0), radius=anaCircleRad, fill=False,
                                    color='grey', ls='solid', zorder=1)
                plt_ax.add_patch(uc)
            # plot real and imaginary axis
            plt_ax.axhline(lw=2, color='k', zorder=1)
            plt_ax.axvline(lw=2, color='k', zorder=1)

        # Plot the zeros
        plt_ax.scatter(z.real, z.imag, s=mzs*mzs, zorder=2, marker='o',
                       facecolor='none', edgecolor=mzc, lw=lw, label=zlabel)
        # and print their multiplicity
        for i in range(len(z)):
            logger.debug('z: {0} | {1} | {2}'.format(i, z[i], num_z[i]))
            if num_z[i] > 1:
                plt_ax.text(np.real(z[i]), np.imag(z[i]), '  (' + str(num_z[i]) + ')',
                            va='top', color=mzc)
        if plt_poles:
            # Plot the poles
            plt_ax.scatter(p.real, p.imag, s=mps*mps, zorder=2, marker='x',
                           color=mpc, lw=lw, label=plabel)
            # and print their multiplicity
            for i in range(len(p)):
                logger.debug('p:{0} | {1} | {2}'.format(i, p[i], num_p[i]))
                if num_p[i] > 1:
                    plt_ax.text(np.real(p[i]), np.imag(p[i]), '  (' + str(num_p[i]) + ')',
                                va='bottom', color=mpc)

# =============================================================================
#            # increase distance between ticks and labels
#            # to give some room for poles and zeros
#         for tick in ax.get_xaxis().get_major_ticks():
#             tick.set_pad(12.)
#             tick.label1 = tick._get_text1()
#         for tick in ax.get_yaxis().get_major_ticks():
#             tick.set_pad(12.)
#             tick.label1 = tick._get_text1()
#
# =============================================================================
        xl = plt_ax.get_xlim()
        Dx = max(abs(xl[1]-xl[0]), 0.05)
        yl = plt_ax.get_ylim()
        Dy = max(abs(yl[1]-yl[0]), 0.05)

        plt_ax.set_xlim((xl[0]-Dx*0.02, max(xl[1]+Dx*0.02, 0)))
        plt_ax.set_ylim((yl[0]-Dy*0.02, yl[1] + Dy*0.02))

        return z, p, k

    # --------------------------------------------------------------------------
    def draw_contours(self, overlay):
        if overlay not in {"contour", "contourf"}:
            return
        self.ax.apply_aspect()  # normally, the correct aspect is only set when plotting
        xl = self.ax.get_xlim()
        yl = self.ax.get_ylim()
        # logger.warning(xl)
        # logger.warning(yl)

        [x, y] = np.meshgrid(
            np.arange(xl[0], xl[1], 0.01),
            np.arange(yl[0], yl[1], 0.01))
        z = x + 1j*y  # create coordinate grid for complex plane

        if self.but_log.isChecked():
            H_max = self.zmax_dB
            H_min = self.zmin_dB
        else:
            H_max = self.zmax
            H_min = self.zmin
        Hmag = H_mag(fb.fil[0]['ba'][0], fb.fil[0]['ba'][1], z, H_max, H_min=H_min,
                     log=self.but_log.isChecked())

        if overlay == "contour":
            self.ax.contour(x, y, Hmag, 20, alpha=0.5, cmap=self.cmap)
        else:
            self.ax.contourf(x, y, Hmag, 20, alpha=0.5, cmap=self.cmap)

        m_cb = cm.ScalarMappable(cmap=self.cmap)    # normalized proxy object that is
        m_cb.set_array(Hmag)                        # mappable for colorbar (?)
        self.col_bar = self.mplwidget.fig.colorbar(
            m_cb, ax=self.ax, shrink=1.0, aspect=40, pad=0.01, fraction=0.08)

        # Contour plots and color bar somehow mess up the coordinates:
        # restore to previous settings
        self.ax.set_xlim(xl)
        self.ax.set_xlim(yl)

    # --------------------------------------------------------------------------
    def draw_Hf(self, r=2, Hf_visible=True):
        """
        Draw the magnitude frequency response around the UC
        """
        self.diaRad_Hf.setVisible(Hf_visible)
        self.lblRad_Hf.setVisible(Hf_visible)
        if not Hf_visible:
            return

        # suppress "divide by zero in log10" warnings
        old_settings_seterr = np.seterr()
        np.seterr(divide='ignore')
        ba = fb.fil[0]['ba']
        w, H = sig.freqz(ba[0], ba[1], worN=params['N_FFT'], whole=True)
        H = np.abs(H)
        if self.but_log.isChecked():
            H = np.clip(np.log10(H), -6, None)  # clip to -120 dB
            H = H - np.max(H)  # shift scale to H_min ... 0
            H = 1 + (r-1) * (1 + H / abs(np.min(H)))  # scale to 1 ... r
        else:
            H = 1 + (r-1) * H / np.max(H)  # map |H(f)| to a range 1 ... r
        y = H * np.sin(w)
        x = H * np.cos(w)

        self.ax.plot(x, y, label="|H(f)|")
        uc = patches.Circle((0, 0), radius=r, fill=False,
                            color='grey', ls='dashed', zorder=1)
        self.ax.add_patch(uc)

        xl = self.ax.get_xlim()
        xmax = max(abs(xl[0]), abs(xl[1]), r*1.05)
        yl = self.ax.get_ylim()
        ymax = max(abs(yl[0]), abs(yl[1]), r*1.05)
        self.ax.set_xlim((-xmax, xmax))
        self.ax.set_ylim((-ymax, ymax))

        np.seterr(**old_settings_seterr)


# ------------------------------------------------------------------------------
if __name__ == "__main__":
    """ Run widget standalone with `python -m pyfda.plot_widgets.plot_pz` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Plot_PZ()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
