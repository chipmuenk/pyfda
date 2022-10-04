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
from pyfda.libs.pyfda_lib import qstr, pprint_log, first_item
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, qstyle_widget
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

    # sig_resize = pyqtSignal()  # emit a signal when the image has been resized
    sig_rx_local = pyqtSignal(object)  # incoming from subwidgets -> process_sig_rx_local
    sig_rx = pyqtSignal(object)  # incoming, connected to input_tab_widget.sig_rx
    sig_tx = pyqtSignal(object)  # outcgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None):
        super(Input_Fixpoint_Specs, self).__init__(parent)
    # def __init__(self) -> None:
    #    super().__init__()

        self.tab_label = 'Fixpoint'
        self.tool_tip = ("<span>Select a fixpoint implementation for the filter,"
                         " simulate it or generate a Verilog netlist.</span>")
        self.parent = parent
        self.fx_specs_changed = True  # fixpoint specs have been changed outside
        self.fx_path = os.path.realpath(
            os.path.join(dirs.INSTALL_DIR, 'fixpoint_widgets'))

        self.no_fx_filter_img = os.path.join(self.fx_path, "no_fx_filter.png")
        if not os.path.isfile(self.no_fx_filter_img):
            logger.error("Image {0:s} not found!".format(self.no_fx_filter_img))

        self.default_fx_img = os.path.join(self.fx_path, "default_fx_img.png")
        if not os.path.isfile(self.default_fx_img):
            logger.error("Image {0:s} not found!".format(self.default_fx_img))

        self._construct_UI()
        inst_wdg_list = self._update_filter_cmb()
        if len(inst_wdg_list) == 0:
            logger.warning("No fixpoint filter found for this type of filter!")
        else:
            logger.debug("Imported {0:d} fixpoint filters:\n{1}"
                         .format(len(inst_wdg_list.split("\n"))-1, inst_wdg_list))
        self._update_fixp_widget()

# ------------------------------------------------------------------------------
    def process_sig_rx_local(self, dict_sig: dict = None) -> None:
        """
        Process signals coming in from input and output quantizer subwidget and
        emit {'fx_sim': 'specs_changed'} in the end.
        """
        logger.debug(
            f"SIG_RX_LOCAL(): vis={self.isVisible()}\n{pprint_log(dict_sig)}")
        if dict_sig['id'] == id(self):
            logger.warning(
                f'RX_LOCAL - Stopped infinite loop: "{first_item(dict_sig)}"')
            return
        # ---------------------------------------------------------------------
        # Updated fixpoint specs in filter widget, update UI + emit with self id

        elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.wdg_dict2ui()  # update wordlengths in UI, set RUN button to 'changed'
            dict_sig.update({'id': id(self)})  # propagate 'specs_changed' with self 'id'
            self.emit(dict_sig)
            return

        # ---- Process input and output quantizer settings ('ui_local_changed') --
        elif 'ui_local_changed' in dict_sig:
            if 'wdg_name' not in dict_sig:
                logger.warning(f"No key 'wdg_name' in dict_sig:\n{pprint_log(dict_sig)}")
                return

            elif dict_sig['ui_local_changed']\
                    not in {'WI', 'WF', 'ovfl', 'quant', 'cmbW', 'butLock'}:
                logger.warning(
                    f"Unknown value '{dict_sig['ui_local_changed']}' "
                    "for key 'ui_local_changed'")
                return

            elif dict_sig['wdg_name'] == 'wq_input':
                """
                Input fixpoint format has been changed or butLock has been clicked.
                When I/O lock is active, copy input fixpoint word format to output
                word format.
                """
                if dict_sig['ui_local_changed'] == 'butLock'\
                        and not self.wdg_wq_input.butLock.isChecked():
                    # butLock was deactivitated, don't do anything
                    return
                elif self.wdg_wq_input.butLock.isChecked():
                    # button lock was activated or wordlength settings have been changed
                    fb.fil[0]['fxqc']['QO']['WI'] = fb.fil[0]['fxqc']['QI']['WI']
                    fb.fil[0]['fxqc']['QO']['WF'] = fb.fil[0]['fxqc']['QI']['WF']
                    fb.fil[0]['fxqc']['QO']['W'] = fb.fil[0]['fxqc']['QI']['W']

            elif dict_sig['wdg_name'] == 'wq_output':
                """
                Output fixpoint format has been changed. When I/O lock is active, copy
                output fixpoint word format to input word format.
                """
                if self.wdg_wq_input.butLock.isChecked():
                    fb.fil[0]['fxqc']['QI']['WI'] = fb.fil[0]['fxqc']['QO']['WI']
                    fb.fil[0]['fxqc']['QI']['WF'] = fb.fil[0]['fxqc']['QO']['WF']
                    fb.fil[0]['fxqc']['QI']['W'] = fb.fil[0]['fxqc']['QO']['W']
            else:
                logger.error("Unknown wdg_name '{0}' in dict_sig:\n{1}"
                             .format(dict_sig['wdg_name'], pprint_log(dict_sig)))
                return

            self.wdg_dict2ui()  # update wordlengths in UI and set RUN button to 'changed'
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

        1. ``fx_sim': 'init'``: Start fixpoint simulation by sending
           'fx_sim':'start_fx_response_calculation'

        2. Store fixpoint response in `fb.fx_result` and return to initiating routine
        """

        logger.debug(
            "SIG_RX(): vis={0}\n{1}".format(self.isVisible(), pprint_log(dict_sig)))
        # logger.debug(f'SIG_RX():  "{first_item(dict_sig)}"')

        if dict_sig['id'] == id(self):
            # logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        #  =================== UI_CHANGED =======================================
        elif 'ui_global_changed' in dict_sig and dict_sig['ui_global_changed']\
                in {'resized', 'tab'} and self.isVisible():
            # Widget size has changed / "Fixpoint" tab has been selected -> resize image
            self.resize_img()

        # =================== DATA CHANGED =====================================
        elif 'data_changed' in dict_sig and\
                dict_sig['data_changed'] == "filter_designed":
            # New filter has been designed, update list of available filter topologies
            self._update_filter_cmb()
            return

        elif 'data_changed' in dict_sig:
            # Filter data has changed (but not the filter type):
            # - reload UI from dict and set RUN button to "changed"
            self.wdg_dict2ui()

        # =================== FX SIM ============================================
        elif 'fx_sim' in dict_sig:

            # --------------- init -------------------
            if dict_sig['fx_sim'] == 'init':
                # fixpoint simulation has been started externally, e.g. by
                # `impz.impz_init()`, return a handle to the fixpoint filter function
                # via signal-slot connection
                if not self.fx_wdg_found:
                    logger.error("No fixpoint widget found!")
                    qstyle_widget(self.butSimFx, "error")
                    self.emit({'fx_sim': 'error'})
                    return
                # initialize fixpoint filter and check for error during initialization
                err = self.fx_filt_init()
                if err != 0:  # returned an error
                    qstyle_widget(self.butSimFx, "error")
                    self.emit({'fx_sim': 'error'})
                else:
                    # Reset overflow counter for input and output quantization,
                    self.wdg_wq_input.QObj.resetN()
                    self.wdg_wq_output.QObj.resetN()
                    # Trigger fixpoint response calculation, passing a handle to the
                    # fixpoint filter function in the emitted dict
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
                self.wdg_wq_input.update_disp()
                self.wdg_wq_output.update_disp()
                if hasattr(self, 'fx_filt_ui') and hasattr(self.fx_filt_ui, 'update'):
                    self.fx_filt_ui.update_disp()
                qstyle_widget(self.butSimFx, "normal")
            # fixpoint specifications / quantization settings have been changed
            # somewhere else, update UI and set run button to "changed" in wdg_dict2ui()

            # --------------- fx specs_changed ------------
            elif self.fx_specs_changed or\
                    (dict_sig['fx_sim'] == 'specs_changed' and self.isVisible()):
                # update wordlengths in UI and set RUN button to 'changed':
                self.wdg_dict2ui()
                self.fx_specs_changed = False
                # self.emit(dict_sig)  # TODO: ???
                return
            elif dict_sig['fx_sim'] == 'specs_changed' and not self.isVisible():
                self.fx_specs_changed = True

            else:
                logger.error('Unknown "fx_sim" command option "{0}"\n'
                             '\treceived from "{1}".'
                             .format(dict_sig['fx_sim'], dict_sig['class']))

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
        wdg_fx = QWidget(self)
        wdg_fx.setStyleSheet(".QWidget { background-color:none; }")
        wdg_fx.setLayout(self.layH_fx_wdg)

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
            fb.fil[0]['fxqc']['QI'], wdg_name='wq_input',
            label='<b>Input Quantizer <i>Q<sub>X&nbsp;</sub></i>:</b>',
            lock_vis='on')
        if HAS_DS:
            self.wdg_wq_input.cmbQuant.addItem('DSM', userData='dsm')
            self.wdg_wq_input.cmbQuant.setItemData(
                self.wdg_wq_input.cmbQuant.count() - 1,
                self.wdg_wq_input.cmbQuant.tr("Delta-Sigma Modulation"), Qt.ToolTipRole)
        self.wdg_wq_input.sig_tx.connect(self.sig_rx_local)

        self.wdg_wq_output = FX_UI_WQ(
            fb.fil[0]['fxqc']['QO'], wdg_name='wq_output',
            label='<b>Output Quantizer <i>Q<sub>Y&nbsp;</sub></i>:</b>')
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
        self.butExportHDL = QPushButton(self)
        self.butExportHDL.setToolTip(
            "Create Verilog or VHDL netlist for fixpoint filter.")
        self.butExportHDL.setText("Create HDL")

        self.butSimFx = QPushButton(self)
        self.butSimFx.setToolTip("Start fixpoint simulation.")
        self.butSimFx.setText("Sim. FX")

        self.layHHdlBtns = QHBoxLayout()
        self.layHHdlBtns.addWidget(self.butSimFx)
        self.layHHdlBtns.addWidget(self.butExportHDL)
        # This frame encompasses the HDL buttons sim and convert
        frmHdlBtns = QFrame(self)
        frmHdlBtns.setLayout(self.layHHdlBtns)
        frmHdlBtns.setContentsMargins(*params['wdg_margins'])

# -------------------------------------------------------------------
#       Top level layout
# -------------------------------------------------------------------
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmTitle)
        layVMain.addWidget(frmHdlBtns)
        layVMain.addWidget(self.wdg_wq_input)
        layVMain.addWidget(wdg_fx)
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
        self.butSimFx.clicked.connect(self._start_fx_sim)
        # ----------------------------------------------------------------------
        # EVENT FILTER
        # ----------------------------------------------------------------------
        # # monitor events and generate sig_resize event when resized
        # self.lbl_fixp_img.installEventFilter(self)
        # # ... then redraw image when resized
        # self.sig_resize.connect(self.resize_img)

# ------------------------------------------------------------------------------
    def _start_fx_sim(self) -> None:
        """
        Start fixpoint simulation by setting the global fixpoint flag
        `fb.fil[0]['fx_sim'] = True` and emitting `{'fx_sim': 'start_fx_sim'}`.
        """
        fb.fil[0]['fx_sim'] = True
        self.emit({'fx_sim': 'start_fx_sim'})

# ------------------------------------------------------------------------------
    def _update_filter_cmb(self) -> str:
        """
        (Re-)Read list of available fixpoint filters for a given filter design
        every time a new filter design is selected.

        Then try to import the fixpoint designs in the list and populate the
        fixpoint implementation combo box `self.cmb_fx_wdg` when successfull.

        Returns
        -------
        inst_wdg_str: str
          string with all fixpoint widgets that could be instantiated successfully
        """
        inst_wdg_str = ""  # full names of successfully instantiated widgets for logging
        # remember last fx widget setting:
        last_fx_wdg = qget_cmb_box(self.cmb_fx_wdg, data=False)
        self.cmb_fx_wdg.clear()
        fc = fb.fil[0]['fc']

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
                    continue  # with next `class_name` of for loop
                except KeyError as e:
                    logger.warning("No fixpoint filter for filter type {0} available."
                                   .format(e))
                    self.embed_fixp_img(self.no_fx_filter_img)
                    continue  # with next `class_name` of for loop

            # restore last fx widget if possible
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
            self.butSimFx.setEnabled(False)
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
            self.fx_filt_ui.setVisible(True)
            self.wdg_dict2ui()  # initialize the fixpoint subwidgets from the fxqc_dict

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

            # Check which methods the fixpoint widget provides and enable
            # corresponding buttons:
            self.butExportHDL.setVisible(hasattr(self.fx_filt_ui, "to_hdl"))
            self.butSimFx.setEnabled(hasattr(self.fx_filt_ui, "fxfilter"))
            self.emit({'fx_sim': 'specs_changed'})

# ------------------------------------------------------------------------------
    def wdg_dict2ui(self):
        """
        Trigger an update of the input, output and fixpoint widgets UI when view
        (i.e. fixpoint coefficient format) or data have been changed outside this
        class.

        Set the RUN button to "changed".
        """
        self.wdg_wq_input.dict2ui()
        self.wdg_wq_output.dict2ui()

#       The following should be connected via signal-slot
#         if self.fx_wdg_found and hasattr(self.fx_filt_ui, "dict2ui"):
#             self.fx_filt_ui.dict2ui()

        qstyle_widget(self.butSimFx, "changed")

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
            hdl_file = qstr(dlg.selectedFiles()[0])
            # hdl_type = extract_file_ext(qstr(dlg.selectedNameFilter()))[0]

# =============================================================================
#       # static method getSaveFileName_() is simple but unflexible
#         hdl_file, hdl_filter = dlg.getSaveFileName_(
#                 caption="Save Verilog netlist as (this also defines the module name)",
#                 directory=dirs.last_file_dir, filter=file_types)
#         hdl_file = qstr(hdl_file)
#         if hdl_file != "": # "operation cancelled" returns an empty string
#             # return '.v' or '.vhd' depending on filetype selection:
#             # hdl_type = extract_file_ext(qstr(hdl_filter))[0]
#             # sanitized dir + filename + suffix. The filename suffix is replaced
#             # by `v` later.
#             hdl_file = os.path.normpath(hdl_file) # complete path + file name
# =============================================================================
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
        try:
            # initialize fixpoint filter instance with fixpoint quantizer
            # self.fx_filt_ui.init_filter()
            self.fx_filt_ui.fx_filt.init(fb.fil[0]['fxqc'])

            return 0

        except (ValueError, AttributeError) as e:
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
            # logger.info(
            #     'Simulate fixpoint frame with "{0}" stimulus:\n\t{1}'.format(
            #         dict_sig['class'],
            #         pprint_log(dict_sig['fx_stimulus'], tab=" "),
            #         ))

            # Run fixpoint simulation and store the results as integer values:
            fb.fx_results = self.fx_filt_ui.fxfilter(dict_sig['fx_stimulus'])

            if len(fb.fx_results) == 0:
                logger.error("Fixpoint simulation returned empty results!")
            # else:
            #     # logger.debug("fx_results: {0}"\
            #     #            .format(pprint_log(fb.fx_results, tab= " ")))
            #     logger.info(
            #         f'Fixpoint simulation successful for dict\n{pprint_log(dict_sig)}'
            #         f'\tStimuli: Shape {np.shape(dict_sig["fx_stimulus"])}'
            #         f' of type "{dict_sig["fx_stimulus"].dtype}"'
            #         f'\n\tResponse: Shape {np.shape(fb.fx_results)}'
            #         f' of type "{type(fb.fx_results).__name__} "'
            #         f' ("{type(fb.fx_results[0]).__name__}")'
            #     )

        except ValueError as e:
            logger.error("Simulator error {0}".format(e))
            fb.fx_results = None

        except AssertionError as e:
            logger.error('Fixpoint simulation failed for dict\n{0}'
                         '\twith msg. "{1}"\n\tStimuli: Shape {2} of type "{3}"'
                         '\n\tResponse: Shape {4} of type "{5}"'.format(
                            pprint_log(dict_sig), e,
                            np.shape(dict_sig['fx_stimulus']),
                            dict_sig['fx_stimulus'].dtype,
                            np.shape(fb.fx_results),
                            type(fb.fx_results)
                                ))
            fb.fx_results = None

        if fb.fx_results is None:
            qstyle_widget(self.butSimFx, "error")
        else:
            pass  # everything ok, return
            # logger.debug("Sending fixpoint results")
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
    # change initial settings to FIR (no IIR fixpoint filters available yet)
    # fb.fil[0].update({'ft': 'FIR', 'fc': 'Equiripple'})
    # _ = Tree_Builder()  # TODO_ couldn't this be a function?
    fb.fil[0].update({'ft': 'IIR', 'fc': 'Ellip'})
    _ = Tree_Builder()  # TODO_ couldn't this be a function?
    mainw = Input_Fixpoint_Specs()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
