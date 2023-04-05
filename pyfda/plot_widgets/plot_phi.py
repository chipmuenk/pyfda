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

from pyfda.libs.compat import (
    QCheckBox, QWidget, QComboBox, QHBoxLayout, QFrame, pyqtSignal)

import numpy as np
import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
from pyfda.plot_widgets.mpl_widget import MplWidget
from matplotlib.ticker import AutoMinorLocator
from pyfda.libs.pyfda_lib import calc_Hcomplex, pprint_log
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, PushButton

import logging
logger = logging.getLogger(__name__)

classes = {'Plot_Phi': '\u03C6(f)'}  #: Dict containing class name : display name


class Plot_Phi(QWidget):
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)
    # outgoing, distributed via plot_tab_widget
    sig_tx = pyqtSignal(object)
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self):
        super().__init__()
        self.needs_calc = True  # recalculation of filter function necessary
        self.needs_draw = True  # plotting neccessary (e.g. log instead of  lin)
        self.tool_tip = "Phase frequency response"
        self.tab_label = "\u03C6(f)"  # phi(f)
        self._construct_UI()

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        # logger.debug("Processing {0} | needs_calc = {1}, visible = {2}"
        #              .format(dict_sig, self.needs_calc, self.isVisible()))

        if dict_sig['id'] == id(self):
            logger.warning("Stopped infinite loop:\n{0}".format(pprint_log(dict_sig)))
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
                self.frmControls.setVisible(dict_sig['value'] == 0)

        else:
            if 'data_changed' in dict_sig:
                self.needs_calc = True
            elif 'view_changed' in dict_sig:
                self.needs_draw = True

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """

        self.cmbUnitsPhi = QComboBox(self)
        units = ["rad", "rad/pi",  "deg"]
        scales = [1.,   1. / np.pi, 180./np.pi]
        for unit, scale in zip(units, scales):
            self.cmbUnitsPhi.addItem(unit, scale)
        self.cmbUnitsPhi.setObjectName("cmbUnitsA")
        self.cmbUnitsPhi.setToolTip("Set unit for phase.")
        self.cmbUnitsPhi.setCurrentIndex(0)
        self.cmbUnitsPhi.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.but_wrap = PushButton("wrapped ", checked=False)
        self.but_wrap.setToolTip("Plot phase wrapped to +/- pi")

        layHControls = QHBoxLayout()
        layHControls.addWidget(self.cmbUnitsPhi)
        layHControls.addWidget(self.but_wrap)
        layHControls.addStretch(10)

        # ----------------------------------------------------------------------
        #               ### frmControls ###
        #
        # This widget encompasses all control subwidgets
        # ----------------------------------------------------------------------
        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)

        # ----------------------------------------------------------------------
        #               ### mplwidget ###
        #
        # main widget, encompassing the other widgets
        # ----------------------------------------------------------------------
        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget.mplToolbar.a_he.setEnabled(True)
        self.mplwidget.mplToolbar.a_he.info = "manual/plot_phi.html"
        self.mplwidget.mplToolbar.a_ui_num_levels = 2
        self.setLayout(self.mplwidget.layVMainMpl)

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
        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)

# ------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize and clear the axes - this is only called once
        """
        if len(self.mplwidget.fig.get_axes()) == 0:  # empty figure, no axes
            self.ax = self.mplwidget.fig.subplots()
        self.ax.xaxis.tick_bottom()  # remove axis ticks on top
        self.ax.yaxis.tick_left()  # remove axis ticks right

# ------------------------------------------------------------------------------
    def unit_changed(self):
        """
        Unit for phase display has been changed, emit a 'view_changed' signal
        and continue with drawing.
        """
        self.emit({'view_changed': 'plot_phi'})
        self.draw()

# ------------------------------------------------------------------------------
    def calc_resp(self):
        """
        (Re-)Calculate the complex frequency response H(f)
        """
        # calculate H_cplx(W) (complex) for W = 0 ... 2 pi:
        self.W, self.H_cmplx = calc_Hcomplex(fb.fil[0], params['N_FFT'], wholeF=True)
        # replace nan and inf by finite values, otherwise np.unwrap yields
        # an array full of nans
        self.H_cmplx = np.nan_to_num(self.H_cmplx)

# ------------------------------------------------------------------------------
    def draw(self):
        """
        Main entry point:
        Re-calculate \|H(f)\| and draw the figure
        """
        self.calc_resp()
        self.update_view()

# ------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """

        self.unitPhi = qget_cmb_box(self.cmbUnitsPhi, data=False)

        f_max_2 = fb.fil[0]['f_max'] / 2.

        # ========= select frequency range to be displayed =====================
        # === shift, scale and select: W -> F, H_cplx -> H_c
        F = self.W * f_max_2 / np.pi

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            # shift H and F by f_S/2
            H = np.fft.fftshift(self.H_cmplx)
            F -= f_max_2
        elif fb.fil[0]['freqSpecsRangeType'] == 'half':
            # only use the first half of H and F
            H = self.H_cmplx[0:params['N_FFT']//2]
            F = F[0:params['N_FFT']//2]
        else:  # fb.fil[0]['freqSpecsRangeType'] == 'whole'
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
        fb.fil[0]['plt_phiLabel'] = y_str
        fb.fil[0]['plt_phiUnit'] = self.unitPhi

        if self.but_wrap.isChecked():
            phi_plt = np.angle(H) * scale
        else:
            phi_plt = np.unwrap(np.angle(H)) * scale

        # ---------------------------------------------------------
        self.ax.clear()  # need to clear, doesn't overwrite
        line_phi, = self.ax.plot(F, phi_plt)
        # ---------------------------------------------------------

        self.ax.xaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
        self.ax.yaxis.set_minor_locator(AutoMinorLocator())  # enable minor ticks
        self.ax.set_title(r'Phase Frequency Response')
        self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax.set_ylabel(y_str)
        self.ax.set_xlim(fb.fil[0]['freqSpecsRange'])

        self.redraw()

# ------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    """ Run widget standalone with `python -m pyfda.plot_widgets.plot_phi` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Plot_Phi()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
