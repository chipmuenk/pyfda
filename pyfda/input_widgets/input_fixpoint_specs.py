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
import sys, os, io
import re
import importlib

from pyfda.libs.compat import (
    Qt, QWidget, QPushButton, QComboBox, QFileDialog, QLabel, QPixmap,
    QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, QSizePolicy)

import numpy as np

import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals
import pyfda.libs.pyfda_dirs as dirs
from pyfda.libs.pyfda_lib import pprint_log, first_item
from pyfda.libs.pyfda_qt_lib import (
    qget_cmb_box, qstyle_widget, qcmb_box_populate, qset_cmb_box)
from pyfda.fixpoint_widgets.fx_ui_wq import FX_UI_WQ
from pyfda.pyfda_rc import params

# when deltasigma module is present, add a corresponding entry to the combobox
try:
    import deltasigma
    HAS_DS = True
except ImportError:
    HAS_DS = False

import logging
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
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None, objectName="input_fixpoint_spec_inst"):
        super(Input_Fixpoint_Specs, self).__init__(parent)
    # def __init__(self) -> None:
    #    super().__init__()

        self.setObjectName(objectName)
        self.tab_label = 'Fixpoint'
        self.tool_tip = ("<span>Select a fixpoint implementation for the filter,"
                         " simulate it or generate a Verilog netlist.</span>")
        self.parent = parent
        self.fx_specs_changed = False
        self.fx_filt_changed = False

        self.fx_path = os.path.realpath(
            os.path.join(dirs.INSTALL_DIR, 'fixpoint_widgets'))

        self.no_fx_filter_img = os.path.join(self.fx_path, "no_fx_filter.png")
        if not os.path.isfile(self.no_fx_filter_img):
            logger.error("Image {0:s} not found!".format(self.no_fx_filter_img))

        self.default_fx_img = os.path.join(self.fx_path, "default_fx_img.png")
        if not os.path.isfile(self.default_fx_img):
            logger.error("Image {0:s} not found!".format(self.default_fx_img))

        self.cmb_qfrmt_items = [
            "<span>Quantization format for coefficients (affects only "
            "the display, not the stored values).</span>",
            ('float', "Float", "<span>Full precision floating point format</span>"),
            ('qint', "Integer", "<span>Integer format with <i>WI</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 1)</span>"),
            ('qfrac', "Fractional",
             "<span>General fractional format with <i>WI</i> + <i>WF</i> + 1 bits "
             "(range -2<sup>WI</sup> ... 2<sup>WI</sup> - 2<sup>WF</sup>).</span>")
            ]
        self.cmb_qfrmt_default = "float"

        self._construct_UI()
        inst_wdg_list = self._update_filter_cmb()
        if len(inst_wdg_list) == 0:
            logger.warning("No fixpoint filter found for this type of filter!")
        else:
            logger.debug("Imported {0:d} fixpoint filters:\n{1}"
                         .format(len(inst_wdg_list.split("\n"))-1, inst_wdg_list))
        self._update_fixp_widget()
        self.dict2ui()  # update fixpoint widgets

# ------------------------------------------------------------------------------
    def process_sig_rx_local(self, dict_sig: dict = None) -> None:
        """
        Process signals coming in from input and output quantizer subwidget and
        emit {'fx_sim': 'specs_changed'} in the end.
        """
        # logger.warning(
        #     f"SIG_RX_LOCAL(): vis={self.isVisible()}\n{pprint_log(dict_sig)}")
        # logger.warning(
        #    f"SIG_RX_LOCAL: vis={self.isVisible()}, fx_sim={fb.fil[0]['fx_sim']}\n{first_item(dict_sig)}")
        if dict_sig['id'] == id(self):
            # logger.warning(
            #     f'RX_LOCAL - Stopped infinite loop: "{pprint_log(dict_sig)}"')
            return
        # ---------------------------------------------------------------------
        # Updated fixpoint specs in filter widget, update UI + emit with self id

        elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.dict2ui() # update fixpoint widgets
            dict_sig.update({'id': id(self)})  # propagate 'specs_changed' with self 'id'
            self.emit(dict_sig)
            return

        # ---- Process input and output quantizer settings ('ui_local_changed') --
        elif 'ui_local_changed' in dict_sig:
            if 'sender_name' not in dict_sig:
                logger.warning(f"No key 'sender_name' in dict_sig:\n{pprint_log(dict_sig)}")
                return

            elif dict_sig['ui_local_changed']\
                    not in {'WI', 'WF', 'ovfl', 'quant', 'cmbW', 'butLock'}:
                logger.warning(
                    f"Unknown value '{dict_sig['ui_local_changed']}' "
                    "for key 'ui_local_changed'")
                return

            elif dict_sig['sender_name'] == 'fx_ui_wq_input':
                """
                Input fixpoint format has been changed: Update filter dict with the
                settings of the input quantizer dict. If I/O lock is active, copy
                input fixpoint word format to output word format. Do the same
                if butLock has been activated.
                """
                fb.fil[0]['fxq']['QI'].update(self.wdg_wq_input.Q.q_dict)
                if dict_sig['ui_local_changed'] == 'butLock'\
                        and not self.wdg_wq_input.butLock.isChecked():
                    # butLock was deactivitated, don't do anything
                    return
                elif self.wdg_wq_input.butLock.isChecked():
                    # button lock was activated or wordlength settings have been changed
                    # with active lock -> copy input settings to output
                    fb.fil[0]['fxq']['QO']['WI'] = fb.fil[0]['fxq']['QI']['WI']
                    fb.fil[0]['fxq']['QO']['WF'] = fb.fil[0]['fxq']['QI']['WF']

            elif dict_sig['sender_name'] == 'fx_ui_wq_output':
                """
                Output fixpoint format has been changed: Update filter dict with the
                settings of the output quantizer dict. When I/O lock is active, copy
                output fixpoint word format to input word format.
                """
                fb.fil[0]['fxq']['QO'].update(self.wdg_wq_output.Q.q_dict)

                if self.wdg_wq_input.butLock.isChecked():
                    fb.fil[0]['fxq']['QI']['WI'] = fb.fil[0]['fxq']['QO']['WI']
                    fb.fil[0]['fxq']['QI']['WF'] = fb.fil[0]['fxq']['QO']['WF']
            else:
                logger.error("Unknown wdg_name / sender_name '{0}' in dict_sig:\n{1}"
                             .format(dict_sig['sender_name'], pprint_log(dict_sig)))
                return

            self.dict2ui() # update fixpoint widgets
            self.emit({'fx_sim': 'specs_changed'})  # propagate 'specs_changed'
        # --------------------------------------------------------------------------------

        else:
            logger.error(f"Unknown key/value in 'dict_sig':\n{pprint_log(dict_sig)}")
        return

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict = None) -> None:
        """
        Process signals coming in via `sig_rx` from other widgets.

        Trigger fx simulation:

        1. `fx_sim': 'init'`: Start fixpoint simulation by sending
           `'fx_sim':'start_fx_response_calculation'`

        2. Store fixpoint response in `fb.fx_result` and return to initiating routine
        """

        # logger.warning(
        #     "SIG_RX(): vis={0}\n{1}".format(self.isVisible(), pprint_log(dict_sig)))
        # logger.warning(
        #     f"SIG_RX: vis={self.isVisible()}, fx_sim={fb.fil[0]['fx_sim']}\n{pprint_log(dict_sig)}")
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
            elif dict_sig['data_changed'] == "filter_designed":
                # New filter has been designed, update list of available filter topologies
                self._update_filter_cmb()

        if fb.fil[0]['fx_sim']:  # fixpoint mode active
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
                                "Couldn't find fixpoint filter definition\n"
                                f"\t'{self.fx_filt_ui.__class__.__name__}.fxfilter'!")
                            self.emit({'fx_sim': 'error'})

                        # next, start fx response calculation in `plot_impz()`
                        return

                # --------------- finish --------------
                elif dict_sig['fx_sim'] == 'finish':
                    # update I/O widgets and dynamically instantiated filter widget with
                    # number of overflows etc.
                    self.wdg_wq_input.update_ovfl_cnt()
                    self.wdg_wq_output.update_ovfl_cnt()
                    if hasattr(self, 'fx_filt_ui') and hasattr(self.fx_filt_ui, 'update_ovfl_cnt_all'):
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
                    logger.error('Unknown "fx_sim" command option "{0}"\n'
                                '\treceived from "{1}".'
                                .format(dict_sig['fx_sim'], dict_sig['class']))

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


# ------------------------------------------------------------------------------
    def _construct_UI(self) -> None:
        """
        Intitialize the main UI, consisting of:

        - A combo box to select the filter topology and an image of the topology
        - The input quantizer
        - The UI of the fixpoint filter widget
        - Simulation and export buttons
        """
        margins = params['wdg_margins']
# ------------------------------------------------------------------------------
        # Define frame and layout for the dynamically updated filter widget
        # The actual filter widget is instantiated / deleted in
        # `self._update_fixp_widget()` later on

        self.layH_fx_wdg = QHBoxLayout()
        # left and right: Zero margin, top and bottom: default margin
        self.layH_fx_wdg.setContentsMargins(0, margins[1], 0, margins[3])
        # self.layH_fx_wdg.setContentsMargins(*params['wdg_margins'])
        wdg_fx_dyn = QWidget(self)
        wdg_fx_dyn.setStyleSheet(".QWidget { background-color:none; }")
        wdg_fx_dyn.setLayout(self.layH_fx_wdg)

# ------------------------------------------------------------------------------
#       Initialize fixpoint filter combobox, title and description
# ------------------------------------------------------------------------------
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

# ------------------------------------------------------------------------------
#       Input and Output Quantizer
# ------------------------------------------------------------------------------
#       - instantiate widgets for input and output quantizer
#       - pass the quantization dictionary to the constructor
# ------------------------------------------------------------------------------

        self.wdg_wq_input = FX_UI_WQ(
            fb.fil[0]['fxq']['QI'], objectName='fx_ui_wq_input',
            label='<b>Input Quantizer <i>Q<sub>I&nbsp;</sub></i>:</b>',
            lock_vis='on', cmb_w_vis='off')
        if HAS_DS:
            self.wdg_wq_input.cmbQuant.addItem('DSM', userData='dsm')
            self.wdg_wq_input.cmbQuant.setItemData(
                self.wdg_wq_input.cmbQuant.count() - 1,
                self.wdg_wq_input.cmbQuant.tr("Delta-Sigma Modulation"), Qt.ToolTipRole)
        self.wdg_wq_input.sig_tx.connect(self.sig_rx_local)

        self.wdg_wq_output = FX_UI_WQ(
            fb.fil[0]['fxq']['QO'], objectName='fx_ui_wq_output',
            label='<b>Output Quantizer <i>Q<sub>O&nbsp;</sub></i>:</b>',
            cmb_w_vis='off')
        self.wdg_wq_output.sig_tx.connect(self.sig_rx_local)

# ------------------------------------------------------------------------------
#       Dynamically updated image of filter topology (label as placeholder)
# ------------------------------------------------------------------------------
        # allow setting background color
        # lbl_fixp_img_palette = QPalette()
        # lbl_fixp_img_palette.setColor(QPalette(window, Qt: white))
        # lbl_fixp_img_palette.setBrush(self.backgroundRole(), QColor(150, 0, 0))
        # lbl_fixp_img_palette.setColor(QPalette: WindowText, Qt: blue)

        self.lbl_fixp_img = QLabel("img not set", self)
        self.lbl_fixp_img.setAutoFillBackground(True)
        # self.lbl_fixp_img.setPalette(lbl_fixp_img_palette)
        # self.lbl_fixp_img.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.embed_fixp_img(self.no_fx_filter_img)
        layHImg = QHBoxLayout()
        layHImg.setContentsMargins(0, 0, 0, 0)
        layHImg.addWidget(self.lbl_fixp_img)  # , Qt.AlignCenter)
        self.frmImg = QFrame(self)
        self.frmImg.setLayout(layHImg)
        self.frmImg.setContentsMargins(*params['wdg_margins'])

# ------------------------------------------------------------------------------
#       Simulation and export Buttons
# ------------------------------------------------------------------------------
        # choose float / fixpoint mode
        self.cmb_qfrmt = QComboBox(self)
        qcmb_box_populate(self.cmb_qfrmt, self.cmb_qfrmt_items,
                          self.cmb_qfrmt_default)
        self.cmb_qfrmt.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.butExportHDL = QPushButton(self)
        self.butExportHDL.setToolTip(
            "Create Verilog or VHDL netlist for fixpoint filter.")
        self.butExportHDL.setText("Create HDL")

        # Wrap qfrmt combobox and HDL buttons sim and convert in one layout
        layH_fx_btns = QHBoxLayout()
        layH_fx_btns.addWidget(self.cmb_qfrmt)
        layH_fx_btns.addWidget(self.butExportHDL)

        frmHdlBtns = QFrame(self)
        frmHdlBtns.setLayout(layH_fx_btns)
        frmHdlBtns.setContentsMargins(*params['wdg_margins'])

# -------------------------------------------------------------------
#       Top level layout
# -------------------------------------------------------------------
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmTitle)
        layVMain.addWidget(frmHdlBtns)
        layVMain.addWidget(self.wdg_wq_input)
        layVMain.addWidget(wdg_fx_dyn)
        layVMain.addWidget(self.wdg_wq_output)
        layVMain.addWidget(self.frmImg)
        layVMain.addStretch()
        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
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
        self.butExportHDL.clicked.connect(self.exportHDL)
        self.cmb_qfrmt.currentIndexChanged.connect(self.qfrmt2ui)

        # ----------------------------------------------------------------------
        # EVENT FILTER
        # ----------------------------------------------------------------------
        # # monitor events and generate sig_resize event when resized
        # self.lbl_fixp_img.installEventFilter(self)
        # # ... then redraw image when resized
        # self.sig_resize.connect(self.resize_img)

# ------------------------------------------------------------------------------
    def load_fx_filter(self) -> None:
        """
        A new filter has been loaded, create fixpoint filter from scratch.

        (Re-)Read list of available fixpoint filters for a given filter class
        every time a new filter has been designed or loaded.

        Then try to import the fixpoint designs in the list and populate the
        fixpoint implementation combo box `self.cmb_fx_wdg` with successfull
        imports.
        """
        self._update_filter_cmb(fx_wdg=fb.fil[0]['fx_mod_class_name'])

        self.dict2ui()  # update fixpoint widgets

# ------------------------------------------------------------------------------
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
        fc = fb.fil[0]['fc']  # get current filter class

        if 'fix' in fb.filter_classes[fc]:
            self.cmb_fx_wdg.blockSignals(True)
            for class_name in fb.filter_classes[fc]['fix']:  # get class name
                try:   # construct module + class name ...
                    mod_class_name = fb.fixpoint_classes[class_name]['mod'] + '.'\
                        + class_name
                    # ... and display name
                    disp_name = fb.fixpoint_classes[class_name]['name']
                    self.cmb_fx_wdg.addItem(disp_name, mod_class_name)
                    inst_wdg_str += '\t' + class_name + ' : ' + mod_class_name + '\n'
                except AttributeError as e:
                    logger.warning('Widget "{0}":\n{1}'.format(class_name, e))
                    self.embed_fixp_img(self.no_fx_filter_img)
                    continue  # with next `class_name` in for loop
                except KeyError as e:
                    logger.warning("No fixpoint filter for filter type {0} available."
                                   .format(e))
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

# ------------------------------------------------------------------------------
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
            logger.warning("Image file {0} doesn't exist.".format(img_file))
            img_file = self.default_fx_img

        _, file_extension = os.path.splitext(img_file)
        if file_extension != '.png':
            logger.error('Unknown file extension "{0}"!'.format(file_extension))
            img_file = self.default_fx_img

        self.img_fixp = QPixmap(img_file)
        return self.img_fixp

# ------------------------------------------------------------------------------
    def resize_img(self) -> None:
        """
        Triggered when `self` (the widget) is selected or resized. The method resizes
        the image inside QLabel to completely fill the label while keeping
        the aspect ratio.

        The parent `InputTabWidget` defines the available width (minus some offset
        due to margins etc.), unfortunately `self.width()` cannot be used as a measure
        as it expands with the parent but doesn't shrink.
        """
        # Module level test: Parent is QApplication which has no width:
        if self.parent is None:
            wdg_w = 300  # set fixed size for module level test
        else:  # widget parent is InputTabWidget()
            wdg_w = self.parent.width()

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

# ------------------------------------------------------------------------------
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
                    logger.error("Destructing UI failed!\n{0}".format(e))

            self.fx_wdg_found = False
            self.butExportHDL.setVisible(False)
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
            logger.info("Instantiating new FX widget\n\t"
                        f"{fx_mod.__name__}.{fx_filt_ui_class.__name__}")
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            self.fx_filt_ui = fx_filt_ui_class()  # instantiate the fixpoint widget
            # set lightblue background with transparency for fixpoint widget
            self.fx_filt_ui.setStyleSheet(
               ".QFrame { background-color: rgba(173, 216, 230, 25%)}")
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            # and add it to layout:
            self.layH_fx_wdg.addWidget(self.fx_filt_ui, stretch=1)
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
            fb.fil[0]['fx_mod_class_name'] = fx_mod_class_name[0]
            # Check which methods the fixpoint widget provides and enable
            # corresponding buttons:
            self.butExportHDL.setVisible(hasattr(self.fx_filt_ui, "to_hdl"))

        else:  # no fixpoint widget found
            fb.fil[0]['fx_mod_class_name'] = ""
            self.fx_wdg_found = False
            # fb.fil[0]['fx_sim'] = False
            self.lbl_descr.setVisible(False)
            self.cmb_qfrmt.setEnabled(False)

        self.emit({'fx_sim': 'specs_changed'})

# ------------------------------------------------------------------------------
    def qfrmt2ui(self):
        """
        Triggered by by a change of index of the combo box `self.cmb_qfrmt`.

        - Update UI (fixpoint format, visibility of fixpoint widgets) from combobox
          `self.cmb_qfrmt` to `fb.fil[0]['fx_sim']` and `fb.fil[0]['qfrmt']`.

        - Update fixpoint widget settings via `self.dict2ui()`

        - Emit {'fx_sim': 'specs_changed'}.
          """
        fb.fil[0]['fx_sim'] = (qget_cmb_box(self.cmb_qfrmt) != 'float')
        if fb.fil[0]['fx_sim']:
            fb.fil[0]['qfrmt'] = qget_cmb_box(self.cmb_qfrmt)

        self.dict2ui()

        self.emit({'fx_sim': 'specs_changed'})

# ------------------------------------------------------------------------------
    def dict2ui(self):
        """
        Called during `__init__()` and from `process_sig_rx()`.

        Update UI from `fb.fil[0]['fx_sim']`, `fb.fil[0]['qfrmt']` and the fx filter
        dict `fb.fil[0]['fxq']`. This affects the visibility and the fx settings of
        input, output and dyn. filter widget via their `dict2ui()` methods.
        The setting of the `self.cmb_qfrmt` combobox influencing float / fixpoint number
        format is updated as well.
        """
        if not fb.fil[0]['fx_mod_class_name']:  # no fixpoint filter available
            fb.fil[0]['fx_sim'] = False
        is_fixp = fb.fil[0]['fx_sim']

        # fixpoint widgets are only visible in fixpoint mode
        self.frmTitle.setVisible(is_fixp)
        self.wdg_wq_input.setVisible(is_fixp)
        self.wdg_wq_output.setVisible(is_fixp)
        self.frmImg.setVisible(is_fixp)
        if self.fx_wdg_found:
           self.fx_filt_ui.setVisible(is_fixp)

        if is_fixp:
            # set combobox from dictionary
            qset_cmb_box(self.cmb_qfrmt, fb.fil[0]['qfrmt'], data=True)
            # refresh image in case of switching from float to fix
            self.resize_img()
            # update fixpoint widgets from the global filter dict:
            # when loading a filter, a new instance of fb.fil[0] is created, requiring
            # passing a hard update of the filter dict
            self.wdg_wq_input.dict2ui(fb.fil[0]['fxq']['QI'])
            self.wdg_wq_output.dict2ui(fb.fil[0]['fxq']['QO'])
            try:
                # this uses the global filter dict as well but it is reinstantiated
                # when loading a filter, using the new instance
                self.fx_filt_ui.dict2ui()
            except AttributeError as e:
                logger.error(f"Error using FX filter widget 'dict2ui()' method:\n{e}")
        elif not fb.fil[0]['fx_sim']:
            qset_cmb_box(self.cmb_qfrmt, 'float', data=True)

# ------------------------------------------------------------------------------
    def exportHDL(self):
        """
        Synthesize HDL description of filter
        """
        dlg = QFileDialog(self)  # instantiate file dialog object

        file_types = "Verilog (*.v)"
        # needed for overwrite confirmation when name is entered without suffix:
        dlg.setDefaultSuffix('v')
        dlg.setWindowTitle('Export Verilog')
        dlg.setNameFilter(file_types)
        dlg.setDirectory(dirs.last_file_dir)
        # set mode "save file" instead "open file":
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        dlg.setOption(QFileDialog.DontConfirmOverwrite, False)
        if dlg.exec_() == QFileDialog.Accepted:
            hdl_file = str(dlg.selectedFiles()[0])
            # hdl_type = extract_file_ext(qstr(dlg.selectedNameFilter()))

            hdl_dir_name = os.path.dirname(hdl_file)  # extract the directory path
            if not os.path.isdir(hdl_dir_name):  # create directory if it doesn't exist
                os.mkdir(hdl_dir_name)
            hdl_file_name = os.path.splitext(os.path.basename(hdl_file))[0]
            hdl_full_name = os.path.join(hdl_dir_name, hdl_file_name + ".v")
            dirs.last_file_name = hdl_full_name
            dirs.last_file_dir = hdl_dir_name  # make this directory the new default / base dir
            # dirs.file
            # remove all non-alphanumeric chars:
            vlog_mod_name = re.sub(r'\W+', '', hdl_file_name).lower()

            logger.info('Creating hdl_file "{0}"\n\twith top level module "{1}"'
                        .format(hdl_full_name, vlog_mod_name))
            try:
                self.fx_filt_ui.construct_fixp_filter()
                code = self.fx_filt_ui.to_hdl(name=vlog_mod_name)
                # logger.info(str(code)) # print verilog code to console
                with io.open(hdl_full_name, 'w', encoding="utf8") as f:
                    f.write(str(code))

                logger.info("HDL conversion finished!")
            except (IOError, TypeError) as e:
                logger.warning(e)

    # --------------------------------------------------------------------------
    def fx_filt_init(self):
        """
        Wrapper around `self.fx_filt_ui.init_filter()` to catch errors.
        Initialize fix-point filter, reset registers and overflow counters

        TODO: - Update the `fxqc_dict` containing all quantization information

        Returns
        -------
        error: int
            0 for sucessful fx widget construction, -1 for error
        """
        if True:
        # try:
            # initialize fixpoint filter instance with fixpoint quantizer
            self.fx_filt_ui.fx_filt.init(fb.fil[0]['fxq'])

            return 0
        else:
        # except (ValueError, AttributeError) as e:
            logger.error('Fixpoint filter reset or instantiation failed.'
                         '\nwith "{0} "'.format(e))
        return -1

# ------------------------------------------------------------------------------
    def fx_sim_calc_response(self, dict_sig) -> None:
        """
        - Read fixpoint stimulus from `dict_sig` in integer format
        - Pass it to the fixpoint filter which calculates the fixpoint response
        - Store the result in `fb.fx_results` and return. In case of an error,
          `fb.fx_results == None`

        Returns
        -------
        None
        """
        try:
            # Run fixpoint simulation and store the results as integer values:
            fb.fx_results = self.fx_filt_ui.fxfilter(dict_sig['fx_stimulus'])

            if len(fb.fx_results) == 0:
                logger.error("Fixpoint simulation returned empty results!")

        except ValueError as e:
            logger.error("Simulator error {0}".format(e))
            fb.fx_results = None

        except AssertionError as e:
            logger.error(
                f'Fixpoint simulation failed for dict\n{pprint_log(dict_sig)}'
                f'\twith msg. "{e}"\n\tStimuli: Shape {np.shape(dict_sig["fx_stimulus"])} '
                f'of type {dict_sig["fx_stimulus"].dtype}'
                f'\n\tResponse: Shape {np.shape(fb.fx_results)} of type '
                f'"{type(fb.fx_results)}"')
            fb.fx_results = None

        return


###############################################################################
if __name__ == '__main__':
    """
    Run widget standalone with `python -m pyfda.input_widgets.input_fixpoint_specs`

    Resizing the image does not work standalone as the {'ui_global_changed': 'resized'}
    signal is issued from somewhere else
    """
    from pyfda.libs.tree_builder import Tree_Builder
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    logging.basicConfig()  # setup a basic logger

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    # change initial settings to FIR
    # fb.fil[0].update({'ft': 'FIR', 'fc': 'Equiripple'})
    # _ = Tree_Builder()  # TODO_ couldn't this be a function?
    fb.fil[0].update({'ft': 'IIR', 'fc': 'Ellip'})
    _ = Tree_Builder()  # TODO_ couldn't this be a function?
    mainw = Input_Fixpoint_Specs()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
