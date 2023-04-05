# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for plotting the group delay
"""
from matplotlib.ticker import AutoMinorLocator
from pyfda.plot_widgets.mpl_widget import MplWidget
from pyfda.pyfda_rc import params
import pyfda.filterbroker as fb
import numpy as np
from pyfda.libs.pyfda_qt_lib import qcmb_box_populate
from pyfda.libs.pyfda_sig_lib import group_delay
from pyfda.libs.compat import (QCheckBox, QWidget, QFrame, QComboBox,
                               QHBoxLayout, pyqtSignal)
import logging
logger = logging.getLogger(__name__)

# from scipy.signal import group_delay

# TODO: Anticausal filter have no group delay. But is a filter with
#       'baA' always anticausal or maybe just acausal?

# Dict containing class name : display name
classes = {'Plot_tau_g': 'tau_g'}


class Plot_tau_g(QWidget):
    """
    Widget for plotting the group delay
    """
    # incoming, connected in sender widget (locally connected to self.process_signals() )
    sig_rx = pyqtSignal(object)
#    sig_tx = pyqtSignal(object) # outgoing from process_signals

    def __init__(self):
        super().__init__()
        self.verbose = False  # suppress warnings
        self.algorithm = "auto"
        self.needs_calc = True   # flag whether plot needs to be recalculated
        self.tool_tip = self.tr("Group delay")
        self.tab_label = "\U0001D70F(f)"  # "tau_g" \u03C4

        self.cmb_algorithm_items =\
            ["<span>Select algorithm for calculating the group delay.</span>",
             ("auto", "Auto", "<span>Try to find best-suited algorithm.</span>"),
             ("scipy", "Scipy", "<span>Scipy algorithm.</span>"),
             ("jos", "JOS", "<span>J.O. Smith's algorithm.</span>"),
             ("shpak", "Shpak", "<span>Shpak's algorithm for SOS and other IIR"
              "filters.</span>"),
             ("diff", "Diff", "<span>Textbook-style, differentiate the phase."
              "</span>")
             ]

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """
        self.chkWarnings = QCheckBox(self.tr("Verbose"), self)
        self.chkWarnings.setChecked(self.verbose)
        self.chkWarnings.setToolTip(self.tr(
            "<span>Print messages about singular group delay and calculation times."
            "</span>"))

        self.cmbAlgorithm = QComboBox(self)
        qcmb_box_populate(self.cmbAlgorithm, self.cmb_algorithm_items, self.algorithm)

        layHControls = QHBoxLayout()
        layHControls.addStretch(10)
        layHControls.addWidget(self.chkWarnings)
        # layHControls.addWidget(self.chkScipy)
        layHControls.addWidget(self.cmbAlgorithm)

        # This widget encompasses all control subwidgets:
        self.frmControls = QFrame(self)
        self.frmControls.setObjectName("frmControls")
        self.frmControls.setLayout(layHControls)

        self.mplwidget = MplWidget(self)
        self.mplwidget.layVMainMpl.addWidget(self.frmControls)
        self.mplwidget.layVMainMpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget.mplToolbar.a_he.setEnabled(True)
        self.mplwidget.mplToolbar.a_he.info = "manual/plot_tau_g.html"
        self.mplwidget.mplToolbar.a_ui_num_levels = 2
        self.setLayout(self.mplwidget.layVMainMpl)

        self.init_axes()
        self.draw()  # initial drawing of tau_g

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.mplwidget.mplToolbar.sig_tx.connect(self.process_sig_rx)
        self.cmbAlgorithm.currentIndexChanged.connect(self.draw)

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig=None):
        """
        Process signals coming from the navigation toolbar and from sig_rx
        """
        # logger.debug("Processing {0} | needs_calc = {1}, visible = {2}"
        #              .format(dict_sig, self.needs_calc, self.isVisible()))
        if self.isVisible():
            if 'data_changed' in dict_sig or self.needs_calc\
                    or ('mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'home'):
                self.draw()
                self.needs_calc = False
            elif 'view_changed' in dict_sig:
                self.update_view()
            elif 'mpl_toolbar' in dict_sig and dict_sig['mpl_toolbar'] == 'ui_level':
                self.frmControls.setVisible(dict_sig['value'] == 0)

        else:
            if 'data_changed' in dict_sig or 'view_changed' in dict_sig:
                self.needs_calc = True

# ------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize the axes and set some stuff that is not cleared by
        `ax.clear()` later on.
        """
        self.ax = self.mplwidget.fig.subplots()
        self.ax.xaxis.tick_bottom()  # remove axis ticks on top
        self.ax.yaxis.tick_left()  # remove axis ticks right

# ------------------------------------------------------------------------------
    def calc_tau_g(self):
        """
        (Re-)Calculate the complex frequency response H(f)
        """
        bb = fb.fil[0]['ba'][0]
        aa = fb.fil[0]['ba'][1]

        # calculate H_cmplx(W) (complex) for W = 0 ... 2 pi:
        # scipy: self.W, self.tau_g = group_delay((bb, aa), w=params['N_FFT'],
        #                                           whole = True)

        if fb.fil[0]['creator'][0] == 'sos':  # one of 'sos', 'zpk', 'ba'
            self.W, self.tau_g = group_delay(fb.fil[0]['sos'], nfft=params['N_FFT'],
                                             sos=True, whole=True,
                                             verbose=self.chkWarnings.isChecked(),
                                             alg=self.cmbAlgorithm.currentData())
        else:
            self.W, self.tau_g = group_delay(bb, aa, nfft=params['N_FFT'], whole=True,
                                             verbose=self.chkWarnings.isChecked(),
                                             alg=self.cmbAlgorithm.currentData())
            #                                   self.chkWarnings.isChecked())

        # Zero phase filters have no group delay (Causal+AntiCausal)
        if 'baA' in fb.fil[0]:
            self.tau_g = np.zeros(self.tau_g.size)

# ------------------------------------------------------------------------------
    def draw(self):
        self.calc_tau_g()
        self.update_view()

# ------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """
        # ========= select frequency range to be displayed =====================
        # === shift, scale and select: W -> F, H_cplx -> H_c
        f_max_2 = fb.fil[0]['f_max'] / 2.
        F = self.W * f_max_2 / np.pi

        if fb.fil[0]['freqSpecsRangeType'] == 'sym':
            # shift tau_g and F by f_S/2
            tau_g = np.fft.fftshift(self.tau_g)
            F -= f_max_2
        elif fb.fil[0]['freqSpecsRangeType'] == 'half':
            # only use the first half of H and F
            tau_g = self.tau_g[0:params['N_FFT']//2]
            F = F[0:params['N_FFT']//2]
        else:  # fb.fil[0]['freqSpecsRangeType'] == 'whole'
            # use H and F as calculated
            tau_g = self.tau_g

        # ================ Main Plotting Routine =========================
        # ===  clear the axes and (re)draw the plot

        if fb.fil[0]['freq_specs_unit'] in {'f_S', 'f_Ny'}:
            tau_str = r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $'
        else:
            tau_str = r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega})$'\
                + ' in ' + fb.fil[0]['plt_tUnit'] + r' $ \rightarrow $'
            tau_g = tau_g / fb.fil[0]['f_S']

        # ---------------------------------------------------------
        self.ax.clear()  # need to clear, doesn't overwrite
        line_tau_g, = self.ax.plot(F, tau_g, label="Group Delay")
        # ---------------------------------------------------------

        self.ax.xaxis.set_minor_locator(
            AutoMinorLocator())  # enable minor ticks
        self.ax.yaxis.set_minor_locator(
            AutoMinorLocator())  # enable minor ticks
        self.ax.set_title(r'Group Delay $ \tau_g$')
        self.ax.set_xlabel(fb.fil[0]['plt_fLabel'])
        self.ax.set_ylabel(tau_str)
        # widen y-limits to suppress numerical inaccuracies when tau_g = constant
        self.ax.set_ylim(
            [max(np.nanmin(tau_g)-0.5, 0), np.nanmax(tau_g) + 0.5])
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
    """ Run widget standalone with `python -m pyfda.plot_widgets.plot_tau_g` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Plot_tau_g()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
