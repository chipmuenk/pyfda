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
import logging

from matplotlib.ticker import AutoMinorLocator
import numpy as np

from pyfda.plot_widgets.mpl_widget import MplWidget
from pyfda.pyfda_rc import params
from pyfda.config_file_parser import ConfigFileParser as CFP
from pyfda.filterbroker import fb_get
from pyfda.libs.pyfda_qt_lib import qcmb_box_populate
from pyfda.libs.pyfda_sig_lib import group_delay
from pyfda.libs.compat import (QCheckBox, QWidget, QFrame, QComboBox,
                               QHBoxLayout, pyqtSignal)

logger = logging.getLogger(__name__)

# Dict containing class name : display name
classes = {'PlotTauG': 'tau_g'}

CMB_ALGORITHM_ITEMS =\
    ["<span>Select algorithm for calculating the group delay.</span>",
        ("auto", "Auto", "<span>Try to find best-suited algorithm.</span>"),
        ("scipy", "Scipy", "<span>Scipy algorithm.</span>"),
        ("jos", "JOS", "<span>J.O. Smith's algorithm.</span>"),
        ("shpak", "Shpak", "<span>Shpak's algorithm for SOS and other IIR"
        "filters.</span>"),
        ("diff", "Diff", "<span>Textbook-style, differentiate the phase."
        "</span>")
        ]

class PlotTauG(QWidget):
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

        self._construct_ui()

    def _construct_ui(self):
        """
        Intitialize the widget, consisting of:
        - Matplotlib widget with NavigationToolbar
        - Frame with control elements
        """
        self.chk_warnings = QCheckBox(self.tr("Verbose"), self)
        self.chk_warnings.setChecked(self.verbose)
        self.chk_warnings.setToolTip(self.tr(
            "<span>Print messages about singular group delay and calculation times."
            "</span>"))

        self.cmb_algorithm = QComboBox(self)
        qcmb_box_populate(self.cmb_algorithm, CMB_ALGORITHM_ITEMS, self.algorithm)

        lay_h_controls = QHBoxLayout()
        lay_h_controls.addStretch(10)
        lay_h_controls.addWidget(self.chk_warnings)
        # lay_h_controls.addWidget(self.chkScipy)
        lay_h_controls.addWidget(self.cmb_algorithm)

        # This widget encompasses all control subwidgets:
        self.frm_controls = QFrame(self, objectName="frm_controls")
        self.frm_controls.setLayout(lay_h_controls)

        self.mplwidget = MplWidget(self)
        self.mplwidget.lay_v_main_mpl.addWidget(self.frm_controls)
        self.mplwidget.lay_v_main_mpl.setContentsMargins(*params['mpl_margins'])
        self.mplwidget.mpl_toolbar.a_he.setEnabled(True)
        self.mplwidget.mpl_toolbar.a_he.info = "manual/plot_tau_g.html"
        self.mplwidget.mpl_toolbar.a_ui_num_levels = 2
        self.setLayout(self.mplwidget.lay_v_main_mpl)

        self.init_axes()
        self.draw()  # initial drawing of tau_g

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.mplwidget.mpl_toolbar.sig_tx.connect(self.process_sig_rx)
        self.cmb_algorithm.currentIndexChanged.connect(self.draw)

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
                self.frm_controls.setVisible(self.mplwidget.mpl_toolbar.a_ui_level == 0)

        else:
            if 'data_changed' in dict_sig or 'view_changed' in dict_sig:
                self.needs_calc = True

# ------------------------------------------------------------------------------
    def init_axes(self):
        """
        Initialize the axes and set some stuff that is not cleared by
        `ax.clear()` later on.
        """
        # add_subplot() always returns a single Axes. It is needed because otherwise self.ax
        # is None and self.ax.clear() in update_view() throws an error.
        # Pylint's static checker infers that self.ax = self.mplwidget.fig.subplots() may be a
        # numpy.ndarray because subplots() can return a single Axes object or an array of Axes

        self.ax = self.mplwidget.fig.add_subplot(1, 1, 1)
        self.ax.xaxis.tick_bottom()  # remove axis ticks on top
        self.ax.yaxis.tick_left()  # remove axis ticks right

# ------------------------------------------------------------------------------
    def calc_tau_g(self):
        """
        (Re-)Calculate the complex frequency response H(f)
        """
        bb = fb_get('ba', 0)
        aa = fb_get('ba', 1)

        # calculate H_cmplx(w) (complex) for w = 0 ... 2 pi:
        # scipy: self.w, self.tau_g = group_delay((bb, aa), w=CFP.conf_settings['N_FFT'],
        #                                           whole = True)

        if fb_get('creator', 0) == 'sos':  # one of 'sos', 'zpk', 'ba'
            self.w, self.tau_g = group_delay(
                fb_get('sos'), nfft=CFP.conf_settings['N_FFT'],
                sos=True, whole=True, verbose=self.chk_warnings.isChecked(),
                alg=self.cmb_algorithm.currentData())
        else:
            self.w, self.tau_g = group_delay(
                bb, aa, nfft=CFP.conf_settings['N_FFT'], whole=True,
                verbose=self.chk_warnings.isChecked(),
                alg=self.cmb_algorithm.currentData())
            #                                   self.chk_warnings.isChecked())

# ------------------------------------------------------------------------------
    def draw(self):
        """
        Calculate the group delay and then draw it
        """
        self.calc_tau_g()
        self.update_view()

# ------------------------------------------------------------------------------
    def update_view(self):
        """
        Draw the figure with new limits, scale etc without recalculating H(f)
        """
        # ========= select frequency range to be displayed =====================
        # === shift, scale and select: w -> f, H_cplx -> H_c
        f_max_2 = fb_get('f_max') / 2.
        f = self.w * f_max_2 / np.pi

        if fb_get('freq_specs_range_type') == 'sym':
            # shift tau_g and f by f_S/2
            tau_g = np.fft.fftshift(self.tau_g)
            f -= f_max_2
        elif fb_get('freq_specs_range_type') == 'half':
            # only use the first half of H and f
            tau_g = self.tau_g[0:CFP.conf_settings['N_FFT']//2]
            f = f[0:CFP.conf_settings['N_FFT']//2]
        else:  # fb_get('freq_specs_range_type') == 'whole'
            # use H and f as calculated
            tau_g = self.tau_g

        # ================ Main Plotting Routine =========================
        # ===  clear the axes and (re)draw the plot

        if fb_get('freq_specs_unit') in {'f_S', 'f_Ny'}:
            tau_str = r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega}) / T_S \; \rightarrow $'
        else:
            tau_str = r'$ \tau_g(\mathrm{e}^{\mathrm{j} \Omega})$'\
                + ' in ' + fb_get('plt_t_unit') + r' $ \rightarrow $'
            tau_g = tau_g / fb_get('f_S')

        # ---------------------------------------------------------
        self.ax.clear()  # need to clear, doesn't overwrite
        self.ax.plot(f, tau_g, label=r"$\tau_g$")
        # ---------------------------------------------------------

        self.ax.xaxis.set_minor_locator(
            AutoMinorLocator())  # enable minor ticks
        self.ax.yaxis.set_minor_locator(
            AutoMinorLocator())  # enable minor ticks
        self.ax.set_title(r'Group Delay $ \tau_g$')
        self.ax.set_xlabel(fb_get('plt_f_label'))
        self.ax.set_ylabel(tau_str)
        # widen y-limits to suppress numerical inaccuracies when tau_g = constant
        self.ax.set_ylim(
            [max(np.nanmin(tau_g)-0.5, 0), np.nanmax(tau_g) + 0.5])
        self.ax.set_xlim(fb_get('freq_specs_range'))

        self.redraw()

# ------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the canvas when e.g. the canvas size has changed
        """
        self.mplwidget.redraw()

# ------------------------------------------------------------------------------


if __name__ == "__main__":
    # Run widget standalone with `python -m pyfda.plot_widgets.plot_tau_g`
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = PlotTauG()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
