# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for simulating fixpoint filters and generating Verilog Code

"""
import importlib
import io
import logging
import os
import re
import sys

import numpy as np

from pyfda.libs.compat import (
    Qt, QWidget, QPushButton, QComboBox, QFileDialog, QLabel, QPixmap,
    QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, QSizePolicy)

from pyfda.filterbroker import get_fx, fb_get, fb_set
from pyfda.config_file_parser import ConfigFileParser as CFP

import pyfda.libs.pyfda_dirs as dirs
from pyfda.libs.pyfda_lib import pprint_log
from pyfda.libs.pyfda_qt_lib import (
    qget_cmb_box, qcmb_box_populate, qset_cmb_box, emit)
from pyfda.fixpoint_widgets.fx_ui_wq import FX_UI_WQ
from pyfda.pyfda_rc import params

# when deltasigma module is present, add a corresponding entry to the combobox
try:
    import deltasigma  # noqa: F401  # pylint: disable=unused-import
    HAS_DS = True
except ImportError:
    HAS_DS = False

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------

classes = {'Input_Fixpoint_Specs': 'Fixpoint'}  #: Dict with class name : display name

class Input_Fixpoint_Specs(QWidget):
    """
    Create the widget that holds the dynamically loaded fixpoint filter UI
    """
    sig_rx_local = pyqtSignal(object)  # incoming from subwidgets -> process_sig_rx_local
    sig_rx = pyqtSignal(object)  # incoming, connected to input_tab_widget.sig_rx
    sig_tx = pyqtSignal(object)  # outcgoing

    def __init__(self, objectName="input_fixpoint_spec_inst"):
        super().__init__()

        self.setObjectName(objectName)
        self.tab_label = 'Fixpoint'
        self.tool_tip = ("<span>Select a fixpoint implementation for the filter,"
                         " simulate it or generate a Verilog netlist.</span>")
        self.fx_specs_changed = False
        self.fx_filt_changed = False

        self.fx_path = os.path.realpath(
            os.path.join(dirs.INSTALL_DIR, 'fixpoint_widgets'))

        self.no_fx_filter_img = os.path.join(self.fx_path, "no_fx_filter.png")
        if not os.path.isfile(self.no_fx_filter_img):
            logger.error("Image %s not found!", self.no_fx_filter_img)

        self.default_fx_img = os.path.join(self.fx_path, "default_fx_img.png")
        if not os.path.isfile(self.default_fx_img):
            logger.error("Image %s not found!", self.default_fx_img)

        self.cmb_qfrmt_items = [
            "<span>Quantization format for coefficients (affects only "
            "the display, not the stored values).</span>",
            ('float64', "Float64", "<span>Full precision floating point format</span>"),
            ('float32', "Float32", "<span>Single precision floating point format</span>"),
            ('qint', "Integer", "<span>Integer format with <i>WI</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 1)</span>"),
            ('qfrac', "Fractional",
             "<span>General fractional format with <i>WI</i> + <i>WF</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 2<sup>WF</sup>).</span>")
            ]
        self.cmb_qfrmt_default = 'float64'

        self._construct_ui()
        inst_wdg_list = self._update_filter_cmb()
        if len(inst_wdg_list) == 0:
            logger.warning("No fixpoint filter found for this type of filter!")
        else:
            logger.debug("Imported %d fixpoint filters:\n%s",
                         len(inst_wdg_list.split("\n"))-1, inst_wdg_list)
        self._update_fixp_widget()
        self.dict2ui()  # update fixpoint widgets

    # -----------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

# ------------------------------------------------------------------------------
    def process_sig_rx_local(self, dict_sig: dict = None) -> None:
        """
        Process signals coming in from input and output quantizer subwidget and
        emit {'fx_sim': 'specs_changed'} in the end.
        """
        logger.debug(
           "SIG_RX_LOCAL(): vis = %s\n%s", self.isVisible(), pprint_log(dict_sig))
        if dict_sig['id'] == id(self):
            # logger.warning(
            #     f'RX_LOCAL - Stopped infinite loop: "{pprint_log(dict_sig)}"')
            return
        # ---------------------------------------------------------------------
        # Updated fixpoint specs in filter widget, update UI + emit with self id

        if 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui() # update fixpoint widgets
            dict_sig.update({'id': id(self)})  # propagate 'specs_changed' with self 'id'
            self.emit(dict_sig)
            return

        # ---- Process input and output quantizer settings ('ui_local_changed') --
        if 'ui_local_changed' in dict_sig:
            if 'sender_name' not in dict_sig:
                logger.warning(
                    "No key 'sender_name' in dict_sig:\n%s", pprint_log(dict_sig))
                return

            if dict_sig['ui_local_changed']\
                    not in {'WI', 'WF', 'ovfl', 'quant', 'cmbW', 'but_lock'}:
                logger.warning("Unknown value '%s' for key 'ui_local_changed'",
                               dict_sig['ui_local_changed'])
                return

            if dict_sig['sender_name'] == 'fx_ui_wq_input':
                # Input fixpoint format has been changed: Update filter dict with the
                # settings of the input quantizer dict. If I/O lock is active, copy
                # input fixpoint word format to output word format. Do the same
                # if but_lock has been activated.
                #
                fb_set('fxq', 'QI', self.wdg_wq_input.Q.q_dict)
                if dict_sig['ui_local_changed'] == 'but_lock'\
                        and not self.wdg_wq_input.but_lock.checked:
                    # but_lock was deactivitated, don't do anything
                    return
                if self.wdg_wq_input.but_lock.checked:
                    # button lock was activated or wordlength settings have been changed
                    # with active lock -> copy input settings to output
                    fb_set('fxq', 'QO', 'WI', fb_get('fxq', 'QI', 'WI'))
                    fb_set('fxq', 'QO', 'WF', fb_get('fxq', 'QI', 'WF'))

            elif dict_sig['sender_name'] == 'fx_ui_wq_output':
                # Output fixpoint format has been changed: Update filter dict with the
                # settings of the output quantizer dict. When I/O lock is active, copy
                # output fixpoint word format to input word format.
                #
                fb_set('fxq', 'QO', self.wdg_wq_output.Q.q_dict)

                if self.wdg_wq_input.but_lock.checked:
                    # button lock was activated or wordlength settings have been changed
                    # with active lock -> copy output settings to input
                    fb_set('fxq', 'QI', 'WI', fb_get('fxq', 'QO', 'WI'))
                    fb_set('fxq', 'QI', 'WF', fb_get('fxq', 'QO', 'WF'))

            else:
                logger.error("Unknown wdg_name / sender_name '%s' in dict_sig:\n%s",
                             dict_sig['sender_name'], pprint_log(dict_sig))
                return

            self.dict2ui() # update fixpoint widgets
            self.emit({'fx_sim': 'specs_changed'})  # propagate 'specs_changed'
        # --------------------------------------------------------------------------------

        else:
            logger.error("Unknown key/value in 'dict_sig':\n%s", pprint_log(dict_sig))
        return

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict = None) -> None:
        """
        Process signals coming in via `sig_rx` from other widgets.

        Trigger fx simulation:

        1. `'fx_sim': 'init'`: Start fixpoint simulation by sending
           `'fx_sim':'start_fx_response_calculation'`

        2. Store fixpoint response in `fb.fx_result` and return to initiating routine
        """

        logger.debug(
            "SIG_RX: vis = %s, fx_sim = %s\n%s",
            self.isVisible(), get_fx(), pprint_log(dict_sig))

        if dict_sig['id'] == id(self):
            # logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        # always update visibility of subwidgets and resize image, also when in float mode
        # or invisible (?)
        if 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui()
        elif 'data_changed' in dict_sig:
            if dict_sig['data_changed'] == 'filter_loaded':
                self.load_fx_filter()
                # TODO: should self._update_filter_cmb() be called here?
                return
            if dict_sig['data_changed'] == "filter_designed":
                # New filter has been designed, update list of available filter topologies
                self._update_filter_cmb()

        if get_fx():  # fixpoint mode active
            #  =================== UI_CHANGED =======================================
            if 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed']\
                    in {'resized', 'tab'} and self.isVisible():
                # Widget size has changed / "Fixpoint" tab has been selected -> resize image
                self.resize_img()

            # =================== DATA CHANGED =====================================
            elif 'data_changed' in dict_sig:
                # Filter data has changed (but not the filter type):
                # Update fixpoint widgets from dict
                self.dict2ui()

            # =================== FX SIM ============================================
            elif 'fx_sim' in dict_sig:
                # --------------- init -------------------
                if dict_sig['fx_sim'] == 'init':
                    # fixpoint simulation has been started externally, e.g. by
                    # `impz.impz_init()`
                    if not self.fx_wdg_found:
                        logger.error("No fixpoint widget found!")
                        # process this in PlotImpz()
                        self.emit({'fx_sim': 'error'})
                        return
                    # initialize fixpoint filter and check for error during initialization
                    err = self.fx_filt_init()
                    if err != 0:  # returned an error
                        # process this in PlotImpz()
                        self.emit({'fx_sim': 'error'})
                    else:
                        # Reset overflow counter for input and output quantizer
                        self.wdg_wq_input.Q.resetN()
                        self.wdg_wq_output.Q.resetN()
                        # Trigger fixpoint response calculation, passing a handle to the
                        # fixpoint filter function in the emitted dict via signal-slot
                        if hasattr(self.fx_filt_ui, 'fxfilter'):
                            self.emit({'fx_sim': 'start_fx_response_calculation',
                                    'fxfilter_func': self.fx_filt_ui.fxfilter})
                        else:
                            logger.error(
                                "Couldn't find fixpoint filter definition\n\t'%s.fxfilter'!",
                                 self.fx_filt_ui.__class__.__name__)
                            self.emit({'fx_sim': 'error'})

                        # next, start fx response calculation in `plot_impz()`
                        return

                # --------------- finish --------------
                elif dict_sig['fx_sim'] == 'finish':
                    # update I/O widgets and dynamically instantiated filter widget with
                    # number of overflows etc.
                    self.wdg_wq_input.update_ovfl_cnt()
                    self.wdg_wq_output.update_ovfl_cnt()
                    if hasattr(self, 'fx_filt_ui')\
                            and hasattr(self.fx_filt_ui, 'update_ovfl_cnt_all'):
                        self.fx_filt_ui.update_ovfl_cnt_all()
                    else:
                        logger.warning("No method 'fx_filt_ui.update_ovfl_cnt_all()'")

                # --------------- fx_sim : specs_changed ------------
                elif dict_sig['fx_sim'] == 'specs_changed' and self.isVisible():
                    self.dict2ui()  # update fixpoint widgets
                    self.fx_specs_changed = False
                elif dict_sig['fx_sim'] == 'specs_changed' and not self.isVisible():
                    self.fx_specs_changed = True
                else:
                    logger.error("Unknown 'fx_sim' command option '%s'\n\treceived from '%s'.",
                                 dict_sig['fx_sim'], dict_sig['class'])

            # the next part is reached when fx_sim is active but no fx_sim command
            # has been issued:
            # =================== Previous Changes ====================================
            # have fixpoint specs / filter been changed when widget was invisible
            # or in float mode? If yes, update fixpoint topologies and UI from dict,
            # set RUN button to 'changed' and resize fixpoint image.
            if self.fx_filt_changed:
                self.fx_filt_changed = False  # reset flag
                self.fx_specs_changed = False  # reset flag
                self._update_filter_cmb()

            elif self.fx_specs_changed:
                self.fx_specs_changed = False  # reset flag
                self.dict2ui()  # update fixpoint widgets

        # =============================================================================
        else:  # fixpoint mode is not active
            if 'data_changed' in dict_sig:
                # Filter data has changed (but not the filter type):
                # Reload UI from dict and
                self.fx_specs_changed = True

    # -----------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Intitialize the main UI, consisting of:

        - A combo box to select the filter topology and an image of the topology
        - The input quantizer
        - The UI of the fixpoint filter widget
        - Simulation and export buttons
        """
        margins = params['wdg_margins']
        # ------------------------------------------------------------------
        # Define frame and layout for the dynamically updated filter widget
        # The actual filter widget is instantiated / deleted in
        # `self._update_fixp_widget()` later on

        self.layH_fx_wdg = QHBoxLayout()
        # left and right: Zero margin, top and bottom: default margin
        self.layH_fx_wdg.setContentsMargins(0, margins[1], 0, margins[3])
        # self.layH_fx_wdg.setContentsMargins(*params['wdg_margins'])
        wdg_fx_dyn = QWidget(self)
        # The following has no effect?
        # wdg_fx_dyn.setStyleSheet(".QWidget { background-color:none; }")
        wdg_fx_dyn.setLayout(self.layH_fx_wdg)

        # ------------------------------------------------------------------
        #  Initialize fixpoint filter combobox, title and description
        # ------------------------------------------------------------------
        self.cmb_fx_wdg = QComboBox(self)
        self.cmb_fx_wdg.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lblTitle = QLabel("not set", self)
        self.lblTitle.setWordWrap(True)
        self.lblTitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.lbl_descr = QLabel("", self)
        self.lbl_descr.setWordWrap(True)

        layHTitle = QHBoxLayout()
        layHTitle.addWidget(self.cmb_fx_wdg)
        layHTitle.addWidget(self.lblTitle)

        layVTitle = QVBoxLayout()
        layVTitle.addLayout(layHTitle)
        layVTitle.addWidget(self.lbl_descr)

        self.frmTitle = QFrame(self)
        self.frmTitle.setLayout(layVTitle)
        self.frmTitle.setContentsMargins(*params['wdg_margins'])

        # -----------------------------------------------------------------
        #       Input and Output Quantizer
        # -----------------------------------------------------------------
        #       - instantiate widgets for input and output quantizer
        #       - pass the quantization dictionary to the constructor
        # -----------------------------------------------------------------

        self.wdg_wq_input = FX_UI_WQ(
            fb_get('fxq', 'QI'), objectName='fx_ui_wq_input',
            label='<b>Input Quantizer <i>Q<sub>I&nbsp;</sub></i>:</b>',
            lock_vis='on', cmb_w_vis='off')
        if HAS_DS:
            self.wdg_wq_input.cmbQuant.addItem('DSM', userData='dsm')
            self.wdg_wq_input.cmbQuant.setItemData(
                self.wdg_wq_input.cmbQuant.count() - 1,
                self.wdg_wq_input.cmbQuant.tr("Delta-Sigma Modulation"), Qt.ToolTipRole)
        self.wdg_wq_input.sig_tx.connect(self.sig_rx_local)

        self.wdg_wq_output = FX_UI_WQ(
            fb_get('fxq', 'QO'), objectName='fx_ui_wq_output',
            label='<b>Output Quantizer <i>Q<sub>O&nbsp;</sub></i>:</b>',
            cmb_w_vis='off')
        self.wdg_wq_output.sig_tx.connect(self.sig_rx_local)

        # --------------------------------------------------------------------
        # Dynamically updated image of filter topology (label as placeholder)
        # --------------------------------------------------------------------
        self.lbl_fixp_img = QLabel("img not set", self)
        # self.lbl_fixp_img.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.embed_fixp_img(self.no_fx_filter_img)
        lay_h_img = QHBoxLayout()
        lay_h_img.setContentsMargins(0, 0, 0, 0)
        lay_h_img.addWidget(self.lbl_fixp_img)  # , Qt.AlignCenter)
        # embedd image into transparent QFrame
        self.frmImg = QFrame(self)
        self.frmImg.setObjectName("transparent")
        self.frmImg.setLayout(lay_h_img)
        self.frmImg.setContentsMargins(*params['wdg_margins'])

        # -----------------------------------------------------------------
        #       Simulation and export Buttons
        # -----------------------------------------------------------------
        # choose float / fixpoint mode
        self.cmb_qfrmt = QComboBox(self)
        qcmb_box_populate(self.cmb_qfrmt, self.cmb_qfrmt_items,
                          self.cmb_qfrmt_default)
        self.cmb_qfrmt.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.but_export_code = QPushButton(self)
        self.but_export_code.setToolTip(
            "Create implementable code for fixpoint filter.")
        self.but_export_code.setText("-> Code")

        # Wrap qfrmt combobox and HDL buttons sim and convert in one layout
        lay_h_fx_btns = QHBoxLayout()
        lay_h_fx_btns.addWidget(self.cmb_qfrmt)
        lay_h_fx_btns.addWidget(self.but_export_code)

        frm_hdl_btns = QFrame(self)
        frm_hdl_btns.setLayout(lay_h_fx_btns)
        frm_hdl_btns.setContentsMargins(*params['wdg_margins'])

        # -------------------------------------------------------------
        #       Top level layout
        # -------------------------------------------------------------
        lay_v_main = QVBoxLayout()
        lay_v_main.addWidget(self.frmTitle)
        lay_v_main.addWidget(frm_hdl_btns)
        lay_v_main.addWidget(self.wdg_wq_input)
        lay_v_main.addWidget(wdg_fx_dyn)
        lay_v_main.addWidget(self.wdg_wq_output)
        lay_v_main.addWidget(self.frmImg)
        lay_v_main.addStretch()
        lay_v_main.setContentsMargins(*params['wdg_margins'])

        self.setLayout(lay_v_main)

        # -----------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # -----------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        self.sig_rx_local.connect(self.process_sig_rx_local)
        # dynamic connection in `self._update_fixp_widget()`:
        # -----
        # if hasattr(self.fx_filt_ui, "sig_rx"):
        #     self.sig_rx.connect(self.fx_filt_ui.sig_rx)
        # if hasattr(self.fx_filt_ui, "sig_tx"):
        #     self.fx_filt_ui.sig_tx.connect(self.sig_rx_local)
        # ----
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.cmb_fx_wdg.currentIndexChanged.connect(self._update_fixp_widget)
        self.but_export_code.clicked.connect(self.export_code)
        self.cmb_qfrmt.currentIndexChanged.connect(self.qfrmt2ui)

        # ----------------------------------------------------------------------
        # EVENT FILTER
        # ----------------------------------------------------------------------
        # # monitor events and generate sig_resize event when resized
        # self.lbl_fixp_img.installEventFilter(self)
        # # ... then redraw image when resized
        # self.sig_resize.connect(self.resize_img)

    # --------------------------------------------------------------------------
    def load_fx_filter(self) -> None:
        """
        A new filter has been loaded, create fixpoint filter from scratch.

        (Re-)Read list of available fixpoint filters for a given filter class
        every time a new filter has been designed or loaded.

        Then try to import the fixpoint designs in the list and populate the
        fixpoint implementation combo box `self.cmb_fx_wdg` with successfull
        imports.
        """
        self._update_filter_cmb(fx_wdg=fb_get('fx_mod_class_name'))

        self.dict2ui()  # update fixpoint widgets

    # --------------------------------------------------------------------------
    def _update_filter_cmb(self, fx_wdg: str = "") -> str:
        """
        (Re-)Read list of available fixpoint filters for a given filter class
        every time a new filter has been designed or loaded.

        Then try to import the fixpoint designs in the list and populate the
        fixpoint implementation combo box `self.cmb_fx_wdg` with successful
        imports.

        Try to set the combobox to the passed argument `fx_wdg` or (if empty), try
        to use the last combobox setting. If both fail, use the first entry of the
        combobox.

        Parameters
        ----------
        fx_wdg: str
          fully qualified name of fixpoint widget (optional)

        Returns
        -------
        inst_wdg_str: str
          string with all fixpoint widgets that have been instantiated successfully.
        """
        inst_wdg_str = ""  # full names of successfully instantiated widgets for logging
        # remember last fx widget setting:
        last_fx_wdg = qget_cmb_box(self.cmb_fx_wdg, data=False)
        self.cmb_fx_wdg.clear()  # clear combobox
        fc = fb_get('fc')  # get current filter class

        if 'fix' in CFP.FILTER_CLASSES_DICT[fc]:
            self.cmb_fx_wdg.blockSignals(True)
            for class_name in CFP.FILTER_CLASSES_DICT[fc]['fix']:  # get class name
                try:   # construct module + class name ...
                    mod_class_name = CFP.FIXPOINT_CLASSES_DICT[class_name]['mod'] + '.'\
                        + class_name
                    # ... and display name
                    disp_name = CFP.FIXPOINT_CLASSES_DICT[class_name]['name']
                    self.cmb_fx_wdg.addItem(disp_name, mod_class_name)
                    inst_wdg_str += '\t' + class_name + ' : ' + mod_class_name + '\n'
                except AttributeError as e:
                    logger.warning('Widget "%s":\n%s', class_name, e)
                    self.embed_fixp_img(self.no_fx_filter_img)
                    continue  # with next `class_name` in for loop
                except KeyError as e:
                    logger.warning("No fixpoint filter for filter type %s available.",e)
                    self.embed_fixp_img(self.no_fx_filter_img)
                    continue  # with next `class_name` in for loop

            # set passed fx_widget or restore last fx widget if possible
            if fx_wdg:
                idx = self.cmb_fx_wdg.findText(fx_wdg)
            else:
                idx = self.cmb_fx_wdg.findText(last_fx_wdg)
            # set to idx 0 if not found (returned -1)
            self.cmb_fx_wdg.setCurrentIndex(max(idx, 0))
            self.cmb_fx_wdg.blockSignals(False)
        else:  # no fixpoint widget
            self.embed_fixp_img(self.no_fx_filter_img)
        self._update_fixp_widget()
        return inst_wdg_str

# # ------------------------------------------------------------------------------
#     def eventFilter(self, source, event):
#         """
#         Filter all events generated by monitored QLabel, only resize events are
#         processed here, generating a `sig_resize` signal. All other events
#         are passed on to the next hierarchy level.
#         """
#         if event.type() == QEvent.Resize:
#             logger.warning("resize event!")
#             self.sig_resize.emit()

#         # Call base class method to continue normal event processing:
#         return super(Input_Fixpoint_Specs, self).eventFilter(source, event)

    # --------------------------------------------------------------------------
    def embed_fixp_img(self, img_file: str) -> QPixmap:
        """
        Embed `img_file` in png format as `self.img_fixp`

        Parameters
        ----------
        img_file: str
            path and file name to image file

        Returns
        -------
        self.img_fixp: QPixmap object
            pixmap containing the passed img_file
        """
        if not os.path.isfile(img_file):
            logger.warning("Image file '%s' doesn't exist.", img_file)
            img_file = self.default_fx_img

        _, file_extension = os.path.splitext(img_file)
        if file_extension != '.png':
            logger.error('Unknown file extension "%s"!', file_extension)
            img_file = self.default_fx_img

        self.img_fixp = QPixmap(img_file)
        return self.img_fixp

    # --------------------------------------------------------------------------
    def resize_img(self) -> None:
        """
        Triggered when `self` (the widget) is selected or resized. The method resizes
        the image inside QLabel to completely fill the label while keeping
        the aspect ratio.

        The parent `TabbedWidget` defines the available width (minus some offset
        due to margins etc.).

        TODO: `self.width()` is a bad measure as it expands with the parent but
        doesn't shrink. Maybe this is because the tab consists of multiple subwidgets
        with individual size policies? Maybe minimumSizeHints are not set properly?
        Changing the tab and back redraws everything nicely.
        """
        if __name__ == "__main__":
            # Module level test: Parent is QApplication which has no width:
            print("Setting fixed width = 300 ")
            wdg_w = 300  # set fixed size for module level test
        else:  # widget parent is TabbedWidget()
            wdg_w = self.width()
            # logger.warning("width = %d", wdg_w)

        # img_w, img_h = self.img_fixp.width(), self.img_fixp.height()
        # if img_w > 20:
        #     max_h = int(max(np.floor(img_h * scale) - 5, 20))
        # else:
        #     max_h = 200
        # logger.debug("img size: {0},{1}, frm size: {2},{3}, max_h: {4}"
        #              .format(img_w, img_h, par_w, par_h, max_h))

        # The following doesn't work because the width of the parent widget can
        # grow with the image size:
        # img_scaled = self.img_fixp.scaled(self.lbl_fixp_img.size(),
        # Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_scaled = self.img_fixp.scaledToWidth(wdg_w - 20, Qt.SmoothTransformation)

        self.lbl_fixp_img.setPixmap(img_scaled)

    # --------------------------------------------------------------------------
    def _update_fixp_widget(self):
        """
        This method is called at the initialization of the widget and when
        a new fixpoint filter implementation is selected from the combo box:

        - Destruct old instance of fixpoint filter widget `self.fx_filt_ui`
        - Import and instantiate new fixpoint filter widget e.g. after changing the
          filter topology as
        - Try to load image for filter topology
        - Update the UI of the widget
        - Try to instantiate fixpoint filter as `self.fx_filt_ui.fixp_filter` with
            dummy data
        - emit {'fx_sim': 'specs_changed'} when successful
        """
        def _disable_fx_wdg(self) -> None:
            if hasattr(self, "fx_filt_ui") and self.fx_filt_ui is not None:
                # is a fixpoint widget loaded?
                try:
                    # try to remove widget from layout
                    self.layH_fx_wdg.removeWidget(self.fx_filt_ui)
                    # delete QWidget when scope has been left
                    self.fx_filt_ui.deleteLater()
                except AttributeError as e:
                    logger.error("Destructing UI failed!\n%s", e)

            self.fx_wdg_found = False
            self.but_export_code.setVisible(False)
            self.img_fixp = self.embed_fixp_img(self.no_fx_filter_img)
            self.resize_img()
            self.lblTitle.setText("")

            self.fx_filt_ui = None
        # -----------------------------------------------------------
        _disable_fx_wdg(self)  # destruct old fixpoint widget instance:

        # instantiate new fixpoint widget class as self.fx_filt_ui
        cmb_wdg_fx_cur = qget_cmb_box(self.cmb_fx_wdg, data=False)
        if cmb_wdg_fx_cur:  # at least one valid fixpoint widget found
            self.fx_wdg_found = True
            self.cmb_qfrmt.setEnabled(True)
            # get list [module name and path, class name]
            fx_mod_class_name = qget_cmb_box(self.cmb_fx_wdg, data=True).rsplit('.', 1)
            fx_mod = importlib.import_module(fx_mod_class_name[0])  # get module
            fx_filt_ui_class = getattr(fx_mod, fx_mod_class_name[1])  # get class
            # logger.info("Instantiating new FX widget")
                        # f"\n\t{fx_mod.__name__}.{fx_filt_ui_class.__name__}")
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            self.fx_filt_ui = fx_filt_ui_class()  # instantiate the fixpoint widget
            self.fx_filt_ui.setObjectName('fx_filt_ui')
            # and add it to layout:
            self.layH_fx_wdg.addWidget(self.fx_filt_ui, stretch=1)
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            self.dict2ui()  # update fixpoint widgets from dictionary

            # ---- connect signals to fx_filt_ui ----
            if hasattr(self.fx_filt_ui, "sig_rx"):
                self.sig_rx.connect(self.fx_filt_ui.sig_rx)
            if hasattr(self.fx_filt_ui, "sig_tx"):
                self.fx_filt_ui.sig_tx.connect(self.sig_rx_local)

            # ---- get name of new fixpoint filter image ----
            if not (hasattr(self.fx_filt_ui, "img_name") and self.fx_filt_ui.img_name):
                # no image name defined, use default image
                img_file = self.default_fx_img
            else:
                # get path of imported fixpoint widget ...
                file_path = os.path.dirname(fx_mod.__file__)
                # ... and construct full image name from it
                img_file = os.path.join(file_path, self.fx_filt_ui.img_name)

            # ---- instantiate and scale graphic of filter topology ----
            self.embed_fixp_img(img_file)
            self.resize_img()

            # ---- set title and description for filter
            self.lblTitle.setText(self.fx_filt_ui.title)
            if hasattr(self.fx_filt_ui, "description"):
                self.lbl_descr.setVisible(True)
                self.lbl_descr.setText(self.fx_filt_ui.description)
            else:
                self.lbl_descr.setVisible(False)

            # store fully qualified name of current fixpoint class:
            fb_set('fx_mod_class_name', fx_mod_class_name[0])
            # Check which methods the fixpoint widget provides and enable
            # corresponding buttons:
            self.but_export_code.setVisible(
                hasattr(self.fx_filt_ui, "fx_filt") and
                hasattr(self.fx_filt_ui.fx_filt, "to_verilog"))

        else:  # no fixpoint widget found
            fb_set('fx_mod_class_name', "")
            self.fx_wdg_found = False
            self.lbl_descr.setVisible(False)
            self.cmb_qfrmt.setEnabled(False)

        self.emit({'fx_sim': 'specs_changed'})

    # --------------------------------------------------------------------------
    def qfrmt2ui(self):
        """
        Triggered by by a change of index of the combo box `self.cmb_qfrmt`.

        - Update UI (fixpoint format, visibility of fixpoint widgets) from combobox
          `self.cmb_qfrmt` to `fil[0]['qfrmt']`.
        - Update fixpoint widget settings via `self.dict2ui()`
        - Emit {'fx_sim': 'specs_changed'}.
          """
        fb_set('qfrmt', qget_cmb_box(self.cmb_qfrmt))

        self.dict2ui()

        self.emit({'fx_sim': 'specs_changed'})

    # --------------------------------------------------------------------------
    def dict2ui(self):
        """
        Called during `__init__()` and from `process_sig_rx()`.

        Update UI from `fil[0]['qfrmt']` and the fx filter dict `fil[0]['fxq']`.
        This affects the visibility and the fx settings of input, output and dyn.
        filter widget via their `dict2ui()` methods.
        The setting of the `self.cmb_qfrmt` combobox influencing float / fixpoint number
        format is updated as well.
        """
        if not fb_get('fx_mod_class_name'):  # no fixpoint filter available
            fb_set('qfrmt', 'float64')
        is_fixp = get_fx()

        # fixpoint widgets are only visible in fixpoint mode
        self.frmTitle.setVisible(is_fixp)
        self.wdg_wq_input.setVisible(is_fixp)
        self.wdg_wq_output.setVisible(is_fixp)
        self.frmImg.setVisible(is_fixp)
        if self.fx_wdg_found:
            self.fx_filt_ui.setVisible(is_fixp)

        # set combobox from dictionary
        qset_cmb_box(self.cmb_qfrmt, fb_get('qfrmt'), data=True)
        if is_fixp:
            # refresh image in case of switching from float to fix
            self.resize_img()
            # update fixpoint widgets from the global filter dict:
            # when loading a filter, a new instance of fil[0] is created, requiring
            # passing a hard update of the filter dict
            # TODO: FX - is this still correct?
            self.wdg_wq_input.dict2ui(fb_get('fxq', 'QI'))
            self.wdg_wq_output.dict2ui(fb_get('fxq', 'QO'))
            try:
                # this uses the global filter dict as well but it is reinstantiated
                # when loading a filter, using the new instance
                self.fx_filt_ui.dict2ui()
            except AttributeError as e:
                logger.error("Error using FX filter widget 'dict2ui()' method:\n%s", e)

    # --------------------------------------------------------------------------
    def export_code(self):
        """
        Generate implementable code for filter
        """
        dlg = QFileDialog(self)  # instantiate file dialog object

        file_types = "Verilog (*.v)"
        # needed for overwrite confirmation when name is entered without suffix:
        dlg.setDefaultSuffix('v')
        dlg.setWindowTitle('Export Fixpoint Filter Code')
        dlg.setNameFilter(file_types)
        dlg.setDirectory(dirs.last_file_dir)
        # set mode "save file" instead "open file":
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setOption(QFileDialog.DontConfirmOverwrite, False)
        if dlg.exec_() == QFileDialog.Accepted:
            code_file = str(dlg.selectedFiles()[0])
            # hdl_type = extract_file_ext(str(dlg.selectedNameFilter()))

            code_dir = os.path.dirname(code_file)  # extract the directory path
            if not os.path.isdir(code_dir):  # create directory if it doesn't exist
                os.mkdir(code_dir)
            # remove file extension if given and return only base name:
            code_file = os.path.splitext(os.path.basename(code_file))[0]
            # remove all non-alphanumeric chars and convert to lower case for "clean name"
            code_file_clean_name = re.sub(r'\W+', '', code_file).lower()

            code_dir_file = os.path.join(code_dir, code_file + ".v")
            dirs.last_file_name = code_dir_file
            dirs.last_file_dir = code_dir  # make this directory the new default / base dir

            logger.info('Creating file "%s"\n\twith top level module "%s"',
                        code_dir_file, code_file_clean_name)
            try:
                code = self.fx_filt_ui.fx_filt.to_verilog(name=code_file_clean_name)
                # logger.info(str(code)) # print generated code to console
                with io.open(code_dir_file, 'w', encoding="utf8") as f:
                    f.write(str(code))

                logger.info("Code generation finished!")
            except (IOError, TypeError) as e:
                logger.warning(e)

    # --------------------------------------------------------------------------
    def fx_filt_init(self):
        """
        Wrapper around `self.fx_filt_ui.init_filter()` to catch errors.
        Initialize fix-point filter, reset registers and overflow counters

        TODO: - Update the `'fxq'` dict entries containing all quantization information

        Returns
        -------
        error: int
            0 for sucessful fx widget construction, -1 for error
        """
        try:
            # initialize fixpoint filter instance with fixpoint quantizer
            self.fx_filt_ui.fx_filt.init(fb_get('fxq'))

            return 0
        except (ValueError, AttributeError) as e:
            logger.error(
                'Fixpoint filter reset or instantiation failed\nwith " %s "', e)
            return -1

    # --------------------------------------------------------------------------
    # def fx_sim_calc_response(self, dict_sig) -> None:
    #     """
    #     - Read fixpoint stimulus from `dict_sig` in integer format
    #     - Pass it to the fixpoint filter which calculates the fixpoint response
    #     - Store the result in `fx_results` and return. In case of an error,
    #       `fx_results == None`

    #     Returns
    #     -------
    #     None
    #     """
    #     try:
    #         # Run fixpoint simulation and store the results as integer values:
    #         fx_results = self.fx_filt_ui.fxfilter(dict_sig['fx_stimulus'])

    #         if len(fx_results) == 0:
    #             logger.error("Fixpoint simulation returned empty results!")

    #     except ValueError as e:
    #         logger.error("Simulator error %s", e)
    #         fx_results = None

    #     except AssertionError as e:
    #         logger.error(
    #             'Fixpoint simulation failed for dict\n%s\n\twith msg. " %s "' \
    #             '\n\tStimuli: Shape %s of type %s'
    #             '\n\tResponse: Shape %s of type "%s"',
    #             pprint_log(dict_sig), e,
    #             np.shape(dict_sig["fx_stimulus"]), dict_sig["fx_stimulus"].dtype,
    #             np.shape(fx_results), type(fx_results))
    #         fx_results = None


###############################################################################
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.input_fixpoint_specs`
    #
    # Resizing the image does not work standalone as the {'ui_global_changed': 'resized'}
    # signal is issued from somewhere else
    from pyfda.libs.compat import QApplication
    from pyfda.filter_tree_builder import FilterTreeBuilder
    from pyfda.pyfda_rc import QSS

    logging.basicConfig()  # setup a basic logger

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    # change initial settings to FIR
    # fb_set({'ft': 'FIR', 'fc': 'Equiripple'})
    fb_set('ft', 'IIR')
    fb_set('fc', 'Ellip')
    FilterTreeBuilder().build_fil_tree()
    mainw = Input_Fixpoint_Specs()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
