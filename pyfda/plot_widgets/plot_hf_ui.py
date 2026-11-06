# -*- coding: utf-8 -*-
#
# This file is part of the pyfda project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyfda Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create the UI for the PlotHf class
"""
import logging

from pyfda.libs.compat import (
    QCheckBox, QWidget, QComboBox, QLabel, QLineEdit, QFrame,
    QHBoxLayout, QVBoxLayout, QGridLayout)
from pyfda.libs.pyfda_text_lib import to_html
from pyfda.libs.pyfda_qt_lib import qtext_width, qcmb_box_populate
from pyfda.libs.pyfda_qt_classes import PushButton

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
CMB_UNITS_A_ITEMS = [
    "<span>Set unit for y-axis</span>",
    ("Auto", "Auto", "Use same setting as in Ripple specifications"),
    ("dB", "dB", "Attenuation in dB"),
    ("V", "V", "Linear gain"),
    ("W", "W", "Power gain")
]
CMB_UNITS_A_DEFAULT = "auto"


class PlotHfUI(QWidget):
    """
    Create the UI for the PlotHf class
    """
    def __init__(self) -> None:
        super().__init__()
        self.log_bottom = -80
        self.lin_neg_bottom = -10
        self.inset_idx = 0  # store previous index for comparison

        self._construct_ui()
        self._construct_layout()

    # --------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Define and construct the subwidgets
        """
        self.lbl_show_h_abs = QLabel(to_html('| H |', frmt='b'))
        self.chk_show_h_abs = QCheckBox(self)
        self.chk_show_h_abs.setChecked(True)
        self.chk_show_h_abs.setToolTip("Show magnitude of H(f)")
        self.lbl_show_h_re = QLabel(to_html('re{H}&nbsp;', frmt='b'))
        self.chk_show_h_re = QCheckBox(self)
        self.chk_show_h_re.setToolTip("Show real part of H(f)")
        self.lbl_show_h_im = QLabel(to_html('im{H}', frmt='b'))
        self.chk_show_h_im = QCheckBox(self)
        self.chk_show_h_im.setToolTip("Show imaginary part of H(f)")

        self.lbl_in = QLabel(to_html("Unit:", frmt="b"), self)

        self.cmb_units_a = QComboBox(self, objectName="cmb_units_a")
        qcmb_box_populate(self.cmb_units_a, CMB_UNITS_A_ITEMS, CMB_UNITS_A_DEFAULT)
        self.cmb_units_a.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lbl_log_bottom = QLabel(to_html("min =", 'bi'), self)
        self.led_log_bottom = QLineEdit(self)
        self.led_log_bottom.setText(str(self.log_bottom))
        self.led_log_bottom.setMaximumWidth(qtext_width(n_x=8))
        self.led_log_bottom.setToolTip(
            "<span>Minimum display value for dB. scale.</span>")
        self.lbl_log_unit = QLabel("dB", self)

        self.but_zerophase = PushButton(self)
        self.but_zerophase.setText("Zero Phase")
        self.but_zerophase.setToolTip(
            "<span>Subtract linear phase as calculated from filter order. "
            "Only available for FIR filters and for unit 'V', it "
            "only affects the display of phase and re / im components.</span>")

        self.lbl_inset = QLabel(to_html("Inset", "bi"), self)
        self.cmb_inset = QComboBox(self, objectName="cmb_inset")
        self.cmb_inset.addItems(['off', 'edit', 'fixed'])
        self.cmb_inset.setToolTip("Display/edit second inset plot")
        self.cmb_inset.setCurrentIndex(0)

        self.but_specs = PushButton(self, "Specs")
        self.but_specs.setToolTip("Display filter specs as hatched regions")

        self.but_phase = PushButton(self, "Phase")
        self.but_phase.setToolTip("Overlay phase")

        self.but_align = PushButton(self, "Align")
        self.but_align.setToolTip(
            "<span>Try to align gridlines for magnitude and phase "
            "(doesn't work in all cases).</span>")
        self.but_align.setVisible(self.but_phase.isChecked())

    # --------------------------------------------------------------------------
    def _construct_layout(self) -> None:
        """
        Construct the layout of the control subwidgets
        """
        lay_g_show_h = QGridLayout()
        lay_g_show_h.addWidget(self.lbl_show_h_abs, 0, 0)
        lay_g_show_h.addWidget(self.chk_show_h_abs, 0, 1)
        lay_g_show_h.addWidget(self.lbl_show_h_re, 1, 0)
        lay_g_show_h.addWidget(self.chk_show_h_re, 1, 1)
        lay_g_show_h.addWidget(self.lbl_show_h_im, 2, 0)
        lay_g_show_h.addWidget(self.chk_show_h_im, 2, 1)
        lay_g_show_h.setContentsMargins(0, 0, 10, 0)
        lay_g_show_h.setSpacing(0)

        # ----------------------------------------------------------------------
        #               ### frm_controls ###
        #
        # This widget encompasses all control subwidgets
        # ----------------------------------------------------------------------
        lay_h_controls = QHBoxLayout()
        lay_h_controls.addLayout(lay_g_show_h)
        lay_h_controls.addWidget(self.lbl_in)
        lay_h_controls.addWidget(self.cmb_units_a)
        lay_h_controls.addStretch(1)
        lay_h_controls.addWidget(self.lbl_log_bottom)
        lay_h_controls.addWidget(self.led_log_bottom)
        lay_h_controls.addWidget(self.lbl_log_unit)
        lay_h_controls.addStretch(1)
        lay_h_controls.addWidget(self.but_zerophase)
        lay_h_controls.addStretch(1)
        lay_h_controls.addWidget(self.lbl_inset)
        lay_h_controls.addWidget(self.cmb_inset)
        lay_h_controls.addStretch(1)
        lay_h_controls.addWidget(self.but_specs)
        lay_h_controls.addStretch(1)
        lay_h_controls.addWidget(self.but_phase)
        lay_h_controls.addWidget(self.but_align)
        lay_h_controls.addStretch(10)

        self.frm_controls = QFrame(self, objectName="frm_controls")
        self.frm_controls.setLayout(lay_h_controls)

        lay_v_main = QVBoxLayout()
        lay_v_main.addWidget(self.frm_controls)
        lay_v_main.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lay_v_main)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.plot_widgets.plot_hf_ui`
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = PlotHfUI()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())

