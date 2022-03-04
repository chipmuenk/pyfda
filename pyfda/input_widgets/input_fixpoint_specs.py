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
    Qt, QWidget, QPushButton, QComboBox, QFileDialog, QSplitter, QLabel, QPixmap,
    QVBoxLayout, QHBoxLayout, pyqtSignal, QFrame, QSizePolicy)

import numpy as np

import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals
import pyfda.libs.pyfda_dirs as dirs
from pyfda.libs.pyfda_lib import qstr, cmp_version, pprint_log, first_item
# import pyfda.libs.pyfda_fix_lib as fx
# from pyfda.libs.pyfda_io_lib import extract_file_ext
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, qstyle_widget
from pyfda.fixpoint_widgets.fixpoint_helpers import UI_W, UI_Q
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
    Create the widget that holds the dynamically loaded fixpoint filter ui
    """

    # sig_resize = pyqtSignal()  # emit a signal when the image has been resized
    sig_rx_local = pyqtSignal(object)  # incoming from subwidgets -> process_sig_rx_local
    sig_rx = pyqtSignal(object)  # incoming, connected to input_tab_widget.sig_rx
    sig_tx = pyqtSignal(object)  # outcgoing
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None):
        super(Input_Fixpoint_Specs, self).__init__(parent)

        self.tab_label = 'Fixpoint'
        self.tool_tip = ("<span>Select a fixpoint implementation for the filter,"
                         " simulate it or generate a Verilog netlist.</span>")
        self.parent = parent
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
        Process signals coming in from input and output quantizer subwidget and the
        dynamically instantiated subwidget and emit {'fx_sim': 'specs_changed'} in
        the end.
        """
        if dict_sig['id'] == id(self):
            logger.warning(f'RX_LOCAL - Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
            self.wdg_dict2ui()  # update wordlengths in UI and set RUN button to 'changed'
            dict_sig.update({'id': id(self)})  # propagate 'specs_changed' with self 'id'
            self.emit(dict_sig)
            return

        # ---- Process input and output quantizer settings ('ui' in dict_sig) --
        elif 'ui' in dict_sig:
            if 'wdg_name' not in dict_sig:
                logger.warning(f"No key 'wdg_name' in dict_sig:\n{pprint_log(dict_sig)}")
                return

            elif dict_sig['wdg_name'] == 'w_input':
                """
                Input fixpoint format has been changed or butLock has been clicked.
                When I/O lock is active, copy input fixpoint word format to output
                word format.
                """
                if dict_sig['ui'] == 'butLock'\
                        and not self.wdg_w_input.butLock.isChecked():
                    # butLock was deactivitated, don't do anything
                    return
                elif self.wdg_w_input.butLock.isChecked():
                    # but lock was activated or wordlength setting have been changed
                    fb.fil[0]['fxqc']['QO']['WI'] = fb.fil[0]['fxqc']['QI']['WI']
                    fb.fil[0]['fxqc']['QO']['WF'] = fb.fil[0]['fxqc']['QI']['WF']
                    fb.fil[0]['fxqc']['QO']['W'] = fb.fil[0]['fxqc']['QI']['W']

            elif dict_sig['wdg_name'] == 'w_output':
                """
                Output fixpoint format has been changed. When I/O lock is active, copy
                output fixpoint word format to input word format.
                """
                if self.wdg_w_input.butLock.isChecked():
                    fb.fil[0]['fxqc']['QI']['WI'] = fb.fil[0]['fxqc']['QO']['WI']
                    fb.fil[0]['fxqc']['QI']['WF'] = fb.fil[0]['fxqc']['QO']['WF']
                    fb.fil[0]['fxqc']['QI']['W'] = fb.fil[0]['fxqc']['QO']['W']

            elif dict_sig['wdg_name'] in {'q_output', 'q_input'}:
                pass
            else:
                logger.error("Unknown wdg_name '{0}' in dict_sig:\n{1}"
                             .format(dict_sig['wdg_name'], pprint_log(dict_sig)))
                return

            if dict_sig['ui'] not in {'WI', 'WF', 'ovfl', 'quant', 'cmbW', 'butLock'}:
                logger.warning("Unknown value '{0}' for key 'ui'".format(dict_sig['ui']))

            self.wdg_dict2ui()  # update wordlengths in UI and set RUN button to 'changed'
            self.emit({'fx_sim': 'specs_changed'})  # propagate 'specs_changed'

        else:
            logger.error(f"Unknown key/value in 'dict_sig':\n{pprint_log(dict_sig)}")

# ------------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict = None) -> None:
        """
        Process signals coming in via `sig_rx` from other widgets.

        Trigger fx simulation:

        1. ``fx_sim': 'init'``: Start fixpoint simulation by sending
           'fx_sim':'start_fx_response_calculation'

        2. ``fx_sim_calc_response()``: Receive stimulus from widget in
            'fx_sim':'calc_frame_fx_response' and pass it to fixpoint simulation method

        3. Store fixpoint response in `fb.fx_result` and return to initiating routine
        """

        # logger.info(
        #     "SIG_RX(): vis={0}\n{1}".format(self.isVisible(), pprint_log(dict_sig)))
        # logger.debug(f'SIG_RX():  "{first_item(dict_sig)}"')

        if dict_sig['id'] == id(self):
            # logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        elif 'data_changed' in dict_sig and dict_sig['data_changed'] == "filter_designed":
            # New filter has been designed, update list of available filter topologies
            self._update_filter_cmb()
            return

        elif 'data_changed' in dict_sig or\
             ('view_changed' in dict_sig and dict_sig['view_changed'] == 'q_coeff'):
            # Filter data has changed (but not the filter type) or the coefficient
            # format / wordlength have been changed in `input_coeffs`. The latter means
            # the view / display has been changed (wordlength) but not the actual
            # coefficients in the `input_coeffs` widget. However, the wordlength setting
            # is copied to the fxqc dict and from there to the fixpoint widget.
            # - update fields in the fixpoint filter widget - wordlength may have
            #   been changed.
            # - Set RUN button to "changed" in wdg_dict2ui()
            self.wdg_dict2ui()

        # --------------- FX Simulation -------------------------------------------
        elif 'fx_sim' in dict_sig:
            if dict_sig['fx_sim'] == 'init':
                # fixpoint simulation has been started externally, e.g. by
                # `impz.impz_init()`, return a handle to the fixpoint filter function
                # via signal-slot connection
                if not self.fx_wdg_found:
                    logger.error("No fixpoint widget found!")
                    qstyle_widget(self.butSimFx, "error")
                    self.emit({'fx_sim': 'error'})
                elif self.fx_sim_init() != 0:  # returned an error
                    qstyle_widget(self.butSimFx, "error")
                    self.emit({'fx_sim': 'error'})
                else:
                    self.emit({'fx_sim': 'start_fx_response_calculation',
                               'fxfilter_func': self.fx_filt_ui.fxfilter})

            elif dict_sig['fx_sim'] == 'calc_frame_fx_response':
                self.fx_sim_calc_response(dict_sig)
                # return to the routine collecting the response frame by frame
                return

            elif dict_sig['fx_sim'] == 'specs_changed':
                # fixpoint specification have been changed somewhere, update ui
                # and set run button to "changed" in wdg_dict2ui()
                self.wdg_dict2ui()
            elif dict_sig['fx_sim'] == 'finish':
                qstyle_widget(self.butSimFx, "normal")
            else:
                logger.error('Unknown "fx_sim" command option "{0}"\n'
                             '\treceived from "{1}".'
                             .format(dict_sig['fx_sim'], dict_sig['class']))

        # ---- resize image when "Fixpoint" tab is selected or widget size is changed:
        elif 'ui_changed' in dict_sig and dict_sig['ui_changed'] in {'resized', 'tab'}\
                and self.isVisible():
            self.resize_img()

# ------------------------------------------------------------------------------
    def _construct_UI(self) -> None:
        """
        Intitialize the main GUI, consisting of:

        - A combo box to select the filter topology and an image of the topology

        - The input quantizer

        - The UI of the fixpoint filter widget

        - Simulation and export buttons
        """
# ------------------------------------------------------------------------------
        # Define frame and layout for the dynamically updated filter widget
        # The actual filter widget is instantiated in self.set_fixp_widget() later on

        self.layH_fx_wdg = QHBoxLayout()
        # self.layH_fx_wdg.setContentsMargins(*params['wdg_margins'])
        frmHDL_wdg = QFrame(self)
        frmHDL_wdg.setLayout(self.layH_fx_wdg)
        # frmHDL_wdg.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

# ------------------------------------------------------------------------------
#       Initialize fixpoint filter combobox, title and description
# ------------------------------------------------------------------------------
        self.cmb_fx_wdg = QComboBox(self)
        self.cmb_fx_wdg.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.lblTitle = QLabel("not set", self)
        self.lblTitle.setWordWrap(True)
        self.lblTitle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layHTitle = QHBoxLayout()
        layHTitle.addWidget(self.cmb_fx_wdg)
        layHTitle.addWidget(self.lblTitle)

        self.frmTitle = QFrame(self)
        self.frmTitle.setLayout(layHTitle)
        self.frmTitle.setContentsMargins(*params['wdg_margins'])

# ------------------------------------------------------------------------------
#       Input and Output Quantizer
# ------------------------------------------------------------------------------
#       - instantiate widgets for input and output quantizer
#       - pass the quantization (sub-?) dictionary to the constructor
# ------------------------------------------------------------------------------

        self.wdg_w_input = UI_W(q_dict=fb.fil[0]['fxqc']['QI'],
                                wdg_name='w_input', label='', lock_visible=True)
        self.wdg_w_input.sig_tx.connect(self.process_sig_rx_local)

        cmb_q = ['round', 'floor', 'fix']

        self.wdg_w_output = UI_W(q_dict=fb.fil[0]['fxqc']['QO'],
                                 wdg_name='w_output', label='')
        self.wdg_w_output.sig_tx.connect(self.process_sig_rx_local)

        self.wdg_q_output = UI_Q(self, q_dict=fb.fil[0]['fxqc']['QO'],
                                 wdg_name='q_output',
                                 label='Output Format <i>Q<sub>Y&nbsp;</sub></i>:',
                                 cmb_q=cmb_q, cmb_ov=['wrap', 'sat'])
        self.wdg_q_output.sig_tx.connect(self.sig_rx_local)

        if HAS_DS:
            cmb_q.append('dsm')
        self.wdg_q_input = UI_Q(self, q_dict=fb.fil[0]['fxqc']['QI'],
                                wdg_name='q_input',
                                label='Input Format <i>Q<sub>X&nbsp;</sub></i>:',
                                cmb_q=cmb_q)
        self.wdg_q_input.sig_tx.connect(self.sig_rx_local)

        # Layout and frame for input quantization
        layVQiWdg = QVBoxLayout()
        layVQiWdg.addWidget(self.wdg_q_input)
        layVQiWdg.addWidget(self.wdg_w_input)
        frmQiWdg = QFrame(self)
        # frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmQiWdg.setLayout(layVQiWdg)
        frmQiWdg.setContentsMargins(*params['wdg_margins'])

        # Layout and frame for output quantization
        layVQoWdg = QVBoxLayout()
        layVQoWdg.addWidget(self.wdg_q_output)
        layVQoWdg.addWidget(self.wdg_w_output)
        frmQoWdg = QFrame(self)
        # frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmQoWdg.setLayout(layVQoWdg)
        frmQoWdg.setContentsMargins(*params['wdg_margins'])

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
        # frmBtns.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        frmHdlBtns.setLayout(self.layHHdlBtns)
        frmHdlBtns.setContentsMargins(*params['wdg_margins'])

# -------------------------------------------------------------------
#       Top level layout
# -------------------------------------------------------------------
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)
        splitter.addWidget(frmHDL_wdg)
        splitter.addWidget(frmQoWdg)
        splitter.addWidget(self.frmImg)

        # setSizes uses absolute pixel values, but can be "misused" by specifying values
        # that are way too large: in this case, the space is distributed according
        # to the _ratio_ of the values:
        splitter.setSizes([3000, 3000, 5000])

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.frmTitle)
        layVMain.addWidget(frmHdlBtns)
        layVMain.addWidget(frmQiWdg)
        layVMain.addWidget(splitter)
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
        self.butSimFx.clicked.connect(lambda x: self.emit({'fx_sim': 'start'}))
        # ----------------------------------------------------------------------
        # EVENT FILTER
        # ----------------------------------------------------------------------
        # # monitor events and generate sig_resize event when resized
        # self.lbl_fixp_img.installEventFilter(self)
        # # ... then redraw image when resized
        # self.sig_resize.connect(self.resize_img)

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
        # logger.warning(f"img_fixp = {img_file}")
        # logger.warning(f"_embed_fixp_img(): {self.img_fixp.__class__.__name__}")
        return self.img_fixp

# ------------------------------------------------------------------------------
    def resize_img(self) -> None:
        """
        Triggered when `self` (the widget) is selected or resized. The method resizes
        the image inside QLabel to completely fill the label while keeping
        the aspect ratio. An offset of some pixels is needed, otherwise the image
        is clipped.
        """
        # logger.warning(f"resize_img(): img_fixp = {self.img_fixp.__class__.__name__}")

        if self.parent is None:  # parent is QApplication, has no width or height
            par_w, par_h = 300, 700  # fixed size for module level test
        else:  # widget parent is InputTabWidget()
            par_w, par_h = self.parent.width(), self.parent.height()

        img_w, img_h = self.img_fixp.width(), self.img_fixp.height()

        if img_w > 10:
            max_h = int(max(np.floor(img_h * par_w/img_w) - 5, 20))
        else:
            max_h = 200
        logger.debug("img size: {0},{1}, frm size: {2},{3}, max_h: {4}"
                     .format(img_w, img_h, par_w, par_h, max_h))

        # The following doesn't work because the width of the parent widget can grow
        # with the image size
        # img_scaled = self.img_fixp.scaled(self.lbl_fixp_img.size(),
        # Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_scaled = self.img_fixp.scaledToHeight(max_h, Qt.SmoothTransformation)

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
        - Try to instantiate HDL filter as `self.fx_filt_ui.fixp_filter` with
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
            # self.layH_fx_wdg.setVisible(False)
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

            # Check which methods the fixpoint widget provides and enable
            # corresponding buttons:
            self.butExportHDL.setVisible(hasattr(self.fx_filt_ui, "to_hdl"))
            self.butSimFx.setEnabled(hasattr(self.fx_filt_ui, "fxfilter"))
            self.update_fxqc_dict()
            self.emit({'fx_sim': 'specs_changed'})

# ------------------------------------------------------------------------------
    def wdg_dict2ui(self):
        """
        Trigger an update of the fixpoint widget UI when view (i.e. fixpoint
        coefficient format) or data have been changed outside this class. Additionally,
        pass the fixpoint quantization widget to update / restore other subwidget
        settings.

        Set the RUN button to "changed".
        """
#        fb.fil[0]['fxqc']['QCB'].update({'scale':(1 << fb.fil[0]['fxqc']['QCB']['W'])})
        self.wdg_q_input.dict2ui(fb.fil[0]['fxqc']['QI'])
        self.wdg_q_output.dict2ui(fb.fil[0]['fxqc']['QO'])
        self.wdg_w_input.dict2ui(fb.fil[0]['fxqc']['QI'])
        self.wdg_w_output.dict2ui(fb.fil[0]['fxqc']['QO'])
        if self.fx_wdg_found and hasattr(self.fx_filt_ui, "dict2ui"):
            self.fx_filt_ui.dict2ui()
#            dict_sig = {'fx_sim':'specs_changed'}
#            self.emit(dict_sig)

        qstyle_widget(self.butSimFx, "changed")

# ------------------------------------------------------------------------------
    def update_fxqc_dict(self):
        """
        Update the fxqc dictionary before simulation / HDL generation starts.
        """
        if self.fx_wdg_found:
            # get a dict with the coefficients and fixpoint settings from fixpoint widget
            if hasattr(self.fx_filt_ui, "ui2dict"):
                fb.fil[0]['fxqc'].update(self.fx_filt_ui.ui2dict())
                logger.debug("update fxqc: \n{0}".format(pprint_log(fb.fil[0]['fxqc'])))
        else:
            logger.error("No fixpoint widget found!")

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
        dlg.setDirectory(dirs.save_dir)
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
#                 directory=dirs.save_dir, filter=file_types)
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
            dirs.save_dir = hdl_dir_name  # make this directory the new default / base dir
            hdl_file_name = os.path.splitext(os.path.basename(hdl_file))[0]
            hdl_full_name = os.path.join(hdl_dir_name, hdl_file_name + ".v")
            # remove all non-alphanumeric chars:
            vlog_mod_name = re.sub(r'\W+', '', hdl_file_name).lower()

            logger.info('Creating hdl_file "{0}"\n\twith top level module "{1}"'
                        .format(hdl_full_name, vlog_mod_name))
            try:
                self.update_fxqc_dict()
                self.fx_filt_ui.construct_fixp_filter()
                code = self.fx_filt_ui.to_hdl(name=vlog_mod_name)
                # logger.info(str(code)) # print verilog code to console
                with io.open(hdl_full_name, 'w', encoding="utf8") as f:
                    f.write(str(code))

                logger.info("HDL conversion finished!")
            except (IOError, TypeError) as e:
                logger.warning(e)

    # --------------------------------------------------------------------------
    def fx_sim_init(self):
        """
        Initialize fix-point simulation:

        - Update the `fxqc_dict` containing all quantization information
        - Setup a filter instance for fixpoint simulation
        - Request a stimulus signal

        Returns
        -------
        error: int
            0 for sucessful fx widget construction, -1 for error
        """
        try:
            self.update_fxqc_dict()
            self.fx_filt_ui.init_filter()   # setup filter instance
            return 0

        except ValueError as e:
            logger.error('Fixpoint stimulus generation failed during "init"'
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
            pass # everything ok, return 
            # logger.debug("Sending fixpoint results")
        return


###############################################################################
if __name__ == '__main__':
    """
    Run widget standalone with `python -m pyfda.input_widgets.input_fixpoint_specs`

    Resizing the image does not work standalone as the 'ui_changed: resized' signal is
    issued from somewhere else
    """
    from pyfda.libs.tree_builder import Tree_Builder
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    logging.basicConfig()  # setup a basic logger

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    # change initial settings to FIR (no IIR fixpoint filters available yet)
    fb.fil[0].update({'ft': 'FIR', 'fc': 'Equiripple'})
    _ = Tree_Builder()  # TODO_ couldn't this be a function?
    mainw = Input_Fixpoint_Specs()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
