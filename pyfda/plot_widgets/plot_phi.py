# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)
"""
Widget for plotting phase frequency response phi(f)
"""
import logging

from matplotlib.ticker import AutoMinorLocator
import numpy as np
import scipy.signal as sig

from pyfda.config_file_parser import ConfigFileParser as CFP
from pyfda.filterbroker import fb_get, fb_set
from pyfda.libs.compat import (
    QWidget, QComboBox, QHBoxLayout, QFrame, pyqtSignal)
from pyfda.plot_widgets.mpl_widget import MplWidget
from pyfda.libs.pyfda_lib import pprint_log
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, emit
from pyfda.libs.pyfda_qt_classes import PushButton
from pyfda.pyfda_rc import params

logger = logging.getLogger(__name__)

classes = {'Plot_Phi': '\u03C6(f)'}  #: Dict containing class name : display name


class Plot_Phi(QWidget):
    """ Widget for plotting the phase frequency response phi(f) """
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)
    # outgoing, distributed via plot_tab_widget
    sig_tx = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.needs_calc = True  # recalculation of filter function necessary
        self.needs_draw = True  # plotting neccessary (e.g. log instead of  lin)
        self.tool_tip = "Phase frequency response"
        self.tab_label = "\u03C6(f)"  # phi(f)
        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        logger.debug("PROCESS_SIG_RX:\n%s \n\tneeds_calc = %s, visible = %s",
                     pprint_log(dict_sig), self.needs_calc, self.isVisible())

        if dict_sig['id'] == id(self):
            logger.debug("Stopped infinite loop:\n%s", pprint_log(dict_sig))
            return

        if self.isVisible():
            if 'data_changed' in dict_sig or self.needs_calc\
                    or ('mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'home'):
                self.draw()
                self.needs_calc = False
                self.needs_draw = False
            elif 'view_changed' in dict_sig or self.needs_draw:
                self.update_view()
                self.needs_draw = False
            elif 'mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'ui_level':
                self.frm_controls.setVisible(self.mplwidget.mpl_toolbar.a_ui_level == 0)

        else:
            if 'data_changed' in dict_sig:
                self.needs_calc = True
            elif 'view_changed' in dict_sig:
                self.needs_draw = True

    # --------------------------------------------------------------------------
    def _construct_ui(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """

        self.cmbUnitsPhi = QComboBox(self, objectName="cmbUnitsA")
        units = ["rad", "rad/pi",  "deg"]
        scales = [1.,   1. / np.pi, 180./np.pi]
        for unit, scale in zip(units, scales, strict=True):
            self.cmbUnitsPhi.addItem(unit, scale)
        self.cmbUnitsPhi.setToolTip("Set unit for phase.")
        self.cmbUnitsPhi.setCurrentIndex(0)
        self.cmbUnitsPhi.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.but_wrap = PushButton(self, "wrapped")
        self.but_wrap.setToolTip("Plot phase wrapped to +/- pi")

        lay_h_controls = QHBoxLayout()
        lay_h_controls.addWidget(self.cmbUnitsPhi)
        lay_h_controls.addWidget(self.but_wrap)
        lay_h_controls.addStretch(10)

        # ----------------------------------------------------------------------
        #               ### frm_controls ###
        #
        # This widget encompasses all control subwidgets
        # ----------------------------------------------------------------------
        self.frm_controls = QFrame(self, objectName="frm_controls")
        self.frm_controls.setLayout(lay_h_controls)

        # ----------------------------------------------------------------------
        #               ### mplwidget ###
        #
        # main widget, encompassing the other widgets
        # ----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)
        self.mplwidget.lay_v_main_mpl.addWidget(self.frm_controls)
        self.mplwidget.lay_v_main_mpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget.mpl_toolbar.a_he.setEnabled(True)
        self.mplwidget.mpl_toolbar.a_he.info = "manual/plot_phi.html"
        self.mplwidget.mpl_toolbar.a_ui_num_levels = 2
        self.setLayout(self.mplwidget.lay_v_main_mpl)

        self.init_axes()

        self.draw()  # initial drawing

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.but_wrap.clicked.connect(self.draw)
        self.cmbUnitsPhi.currentIndexChanged.connect(self.unit_changed)
        self.mplwidget.mpl_toolbar.sig_tx.connect(self.process_sig_rx)

    # --------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes - this is only called once
        """
        # add_subplot() always returns a single Axes. It is needed because otherwise self.ax
        # is None and self.ax.clear() in update_view() throws an error.
        # Pylint's static checker infers that self.ax = self.mplwidget.fig.subplots() may be a
        # numpy.ndarray because subplots() can return a single Axes object or an array of Axes
        self.ax = self.mplwidget.fig.add_subplot(1, 1, 1)
        self.ax.xaxis.tick_bottom()  # remove axis ticks on top
        self.ax.yaxis.tick_left()  # remove axis ticks right

    # -------------------------------------------------------------------------
    def unit_changed(self):
        """
        Unit for phase display has been changed, emit a 'view_changed' signal
        and continue with drawing.
        """
        self.emit({'view_changed': 'plot_phi'})
        self.draw()

    # --------------------------------------------------------------------------
    def calc_resp(self):
        """
        (Re-)Calculate the complex frequency response H(f)
        """
        # calculate H_cplx(W) (complex) for W = 0 ... 2 pi:
        self.W, self.H_cmplx = sig.freqz(
            fb_get('ba', 0), fb_get('ba', 1), worN=CFP.conf_settings['N_FFT'],
            whole=True, fs=2*np.pi)
        # replace nan and inf by finite values, otherwise np.unwrap yields
        # an array full of nans
        self.H_cmplx = np.nan_to_num(self.H_cmplx)

    # --------------------------------------------------------------------------
    def draw(self):
        r"""
        Main entry point:
        Re-calculate \|H(f)\| and draw the figure
        """
        self.calc_resp()
        self.update_view()

    # --------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """

        self.unitPhi = qget_cmb_box(self.cmbUnitsPhi, data=False)

        f_max_2 = fb_get('f_max') / 2.

        # ========= select frequency range to be displayed =====================
        # === shift, scale and select: W -> F, H_cplx -> H_c
        F = self.W * f_max_2 / np.pi

        if fb_get('freqSpecsRangeType') == 'sym':
            # shift H and F by f_S/2
            H = np.fft.fftshift(self.H_cmplx)
            F -= f_max_2
        elif fb_get('freqSpecsRangeType') == 'half':
            # only use the first half of H and F
            H = self.H_cmplx[0:CFP.conf_settings['N_FFT']//2]
            F = F[0:CFP.conf_settings['N_FFT']//2]
        else:  # fb_get('freqSpecsRangeType') == 'whole'
            # use H and F as calculated
            H = self.H_cmplx

        y_str = r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$ in '
        if self.unitPhi == 'rad':
            y_str += 'rad ' + r'$\rightarrow $'
            scale = 1.
        elif self.unitPhi == 'rad/pi':
            y_str += 'rad' + r'$ / \pi \;\rightarrow $'
            scale = 1. / np.pi
        else:
            y_str += 'deg ' + r'$\rightarrow $'
            scale = 180./np.pi
        fb_set('plt_phiLabel', y_str)
        fb_set('plt_phiUnit', self.unitPhi)

        if self.but_wrap.checked:
            phi_plt = np.angle(H) * scale
        else:
            phi_plt = np.unwrap(np.angle(H)) * scale

        # ---------------------------------------------------------
        self.ax.clear()  # need to clear, doesn't overwrite
        self.ax.plot(F, phi_plt, label=r'$\phi(F)$')
        # ---------------------------------------------------------

        self.ax.xaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
        self.ax.yaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
        self.ax.set_title(r'Phase Frequency Response')
        self.ax.set_xlabel(fb_get('plt_fLabel'))
        self.ax.set_ylabel(y_str)
        self.ax.set_xlim(fb_get('freqSpecsRange'))

        self.redraw()

    # --------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    # Run widget standalone with `python -m pyfda.plot_widgets.plot_phi`
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = Plot_Phi()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
