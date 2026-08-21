# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget stacking all subwidgets for filter specification and design. The actual
filter design is started here as well.
"""
import copy
import io
import json
import logging
import os
import pickle
import sys

import numpy as np

import pyfda.filterbroker as fb
from pyfda.filterbroker import fb_get, fb_set, backup_fil, restore_fil
from pyfda.filter_factory import call_fil_method
from pyfda.filter_tree_builder import FilterTreeBuilder as FTB
from pyfda.input_widgets import (
    select_filter, amplitude_specs, freq_specs, freq_units, weight_specs, target_specs)
from pyfda.libs.compat import (
    Qt, QWidget, QLabel, QFrame, QPushButton, QComboBox, QLineEdit, pyqtSignal,
    QVBoxLayout, QHBoxLayout, QSizePolicy)

import pyfda.libs.pyfda_dirs as dirs
from pyfda.libs.pyfda_lib import to_html, first_item, iter2ndarray, compare_dictionaries
from pyfda.libs.pyfda_qt_lib import (
    popup_warning, qstyle_widget, qcmb_box_populate, qget_cmb_box, emit)
from pyfda.libs.pyfda_io_lib import select_file
from pyfda.pyfda_rc import params

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# Include this version number as `'_id': ('pyfda', FILTER_FILE_VERSION)` when saving
# filter files and test for the version when loading filter files.
FILTER_FILE_VERSION = '2'

classes = {'Input_Specs': 'Specs'}  #: Dict containing class name : display name
# This is read by `tree_builder._build_widget_class_dicts()` into the dict
#  `filterbroker.INPUT_CLASSES_DICT` and used to create the widgets in input_tab_widgets.

# TODO: a lot of methods from other classes are called here, this is very intransparent
class Input_Specs(QWidget):
    """
    Build widget for entering all filter specs
    """
    # class variables (shared between instances if more than one exists)
    sig_rx_local = pyqtSignal(object)  # incoming from subwidgets -> process_sig_rx_local

    sig_rx = pyqtSignal(object)  # incoming from subwidgets -> process_sig_rx
    sig_tx = pyqtSignal(object)  # from process_sig_rx: propagate local signals

    def __init__(self, objectName: str = "input_specs_inst"):
        super().__init__()
        self.setObjectName(objectName)
        self.tab_label = "Specs"
        self.tool_tip = "Enter and view filter specifications."

        self.led_info_tool_tip = "Filter info:"

        filter_load_help_txt = "Load <- Mem {0}: " + fb_get('info')
        self.cmb_filter_load_items = [
            "<span>Load current filter(s) from memory location or file.</span>",
            ("0", "LOAD", "Current filter, no action."),
            ("1", "Mem 1", filter_load_help_txt.format("1")),
            ("2", "Mem 2", filter_load_help_txt.format("2")),
            ("3", "Mem 3", filter_load_help_txt.format("3")),
            ("4", "Mem 4", filter_load_help_txt.format("4")),
            ("5", "Mem 5", filter_load_help_txt.format("5")),
            ("6", "Mem 6", filter_load_help_txt.format("6")),
            ("7", "Mem 7", filter_load_help_txt.format("7")),
            ("8", "Mem 8", filter_load_help_txt.format("8")),
            ("9", "Mem 9", filter_load_help_txt.format("9")),
            ("def", "Default", "Load default filter."),
            ("def_all", "Default (all)", "Copy default filter to all memory locations."),
            ("file", "File", "Load filter from file."),
            ("file_all", "File (all)", "Load all filters from file.")
        ]
        self.cmb_filter_load_default = "0"

        filter_save_help_txt = "Copy -> Mem {0}: " + fb_get('info')
        self.cmb_filter_save_items = [
            "<span>Copy / save current filter(s) to memory location or file.</span>",
            ("0", "SAVE", "Current filter, no action."),
            ("1", "Mem 1", filter_save_help_txt.format("1")),
            ("2", "Mem 2", filter_save_help_txt.format("2")),
            ("3", "Mem 3", filter_save_help_txt.format("3")),
            ("4", "Mem 4", filter_save_help_txt.format("4")),
            ("5", "Mem 5", filter_save_help_txt.format("5")),
            ("6", "Mem 6", filter_save_help_txt.format("6")),
            ("7", "Mem 7", filter_save_help_txt.format("7")),
            ("8", "Mem 8", filter_save_help_txt.format("8")),
            ("9", "Mem 9", filter_save_help_txt.format("9")),
            ("file", "File", "Save current filter to file."),
            ("file_all", "File (all)", "Save all filters to file.")
        ]
        self.cmb_filter_save_default = "0"

        self._construct_ui()
        self._create_layout()
        self._update_ui()  # first time initialization
        self.start_design_filt()  # design first filter using default values

    # -------------------------------------------------------------------------
    def emit(self, dict_sig: dict) -> None:
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -------------------------------------------------------------------------
    def process_sig_rx_local(self, dict_sig: dict | None = None) -> None:
        """
        Signals coming in from local subwidgets need to be propagated, so set
        `propagate=True` and proceed with processing in `process_sig_rx`.
        """
        self.process_sig_rx(dict_sig, propagate=True)

    # -------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict, propagate: bool = False) -> None:
        """
        Process signals coming in via subwidgets and sig_rx

        All signals terminate here unless the flag `propagate=True`.

        The sender name of signals coming in from local subwidgets is changed to
        its parent widget (`input_specs`) to prevent infinite loops.

        """
        if dict_sig['id'] == id(self):
            logger.debug("Stopped infinite loop (propagate = %s)\n:\n\t%s",
                         propagate, first_item(dict_sig))
            return

        # logger.warning(f"SIG_RX: {first_item(dict_sig)}")

        if 'specs_changed' in dict_sig:
            if dict_sig['specs_changed'] == 'f_sort':
                # sort and update the frequency widgets
                self.f_specs.sort_dict_freqs()
                self.t_specs.f_specs.sort_dict_freqs()
            self.color_design_button('changed')
        elif 'filt_changed' in dict_sig:
            # Changing the filter design requires updating UI because number or
            # kind of input fields changes -> reload filter parameters and _update_ui
            self._update_ui()
            self.sel_fil.dict2ui()
            # Update state of "DESIGN FILTER" button
            # It is disabled for "Manual_IIR" and "Manual_FIR" filter classes
            self.color_design_button('changed')
        elif 'data_changed' in dict_sig and dict_sig['data_changed'] == 'filter_loaded':
            # Update info string from filter dict & set button = "ok"
            # This is only triggered from global signals
            self._load_info_text()

        if propagate:
            # local signals are propagated with the class name and id of this widget,
            # global signals terminate here
            dict_sig.update({'class': self.__class__.__name__, 'id': id(self)})
            self.emit(dict_sig)

    # -------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Construct User Interface from all input subwidgets
        """
        self.cmb_filter_load = QComboBox(self)
        qcmb_box_populate(self.cmb_filter_load, self.cmb_filter_load_items,
                          self.cmb_filter_load_default)
        self.cmb_filter_load.insertSeparator(1)
        self.cmb_filter_load.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cmb_filter_save = QComboBox(self)
        qcmb_box_populate(self.cmb_filter_save, self.cmb_filter_save_items,
                          self.cmb_filter_save_default)
        self.cmb_filter_save.insertSeparator(1)
        self.cmb_filter_save.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_info_1 = QLabel(to_html(">", frmt='b'))
        self.lbl_info_2 = QLabel(to_html(">", frmt='b'))
        self.led_info = QLineEdit(fb_get('info'))
        self.led_info.setToolTip(self.led_info_tool_tip)
        # self.led_info.home(True)  # move cursor to beginning of line

        self.butDesignFilt = QPushButton("DESIGN FILTER", self)
        self.butDesignFilt.setToolTip("Design filter with chosen specs")
        self.butQuit = QPushButton("Quit", self)
        self.butQuit.setToolTip("Exit pyfda tool")

        # Subwidget for selecting filter with response type rt (LP, ...),
        #    filter type ft (IIR, ...) and filter class fc (cheby1, ...)
        self.sel_fil = select_filter.SelectFilter(objectName="select_filter_inst")

        # Subwidget for selecting the frequency unit and range
        self.f_units = freq_units.FreqUnits(objectName="freq_units_inst")

        # Changing the frequency unit requires re-display of frequency specs
        # but it does not influence the actual specs (no specsChanged )
        # Activating the "Sort" button emits 'view_changed'?specs_changed'?, requiring
        # sorting and storing the frequency entries

        # Changing filter parameters / specs requires reloading of parameters
        # in other hierarchy levels, e.g. in the plot tabs

        # Subwidget for Frequency Specs
        self.f_specs = freq_specs.FreqSpecs(objectName="freq_specs_corner")

        # Subwidget for Amplitude Specs
        self.a_specs = amplitude_specs.AmplitudeSpecs(objectName="amplitude_specs_general")

        # Subwidget for Weight Specs
        self.w_specs = weight_specs.WeightSpecs(objectName="weight_specs_inst")

        # Subwidget for target specs (frequency and amplitude)
        self.t_specs = target_specs.TargetSpecs(title="Target Specifications",
                                                objectName="target_specs_inst")

        # Subwidget for displaying infos on the design method
        self.lblMsg = QLabel(self)
        self.lblMsg.setWordWrap(True)

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # connect incoming signals to process_sig_rx and other widgets?!
        self.sig_rx.connect(self.process_sig_rx)
        # self.sig_rx.connect(self.f_units.sig_rx)
        self.sig_rx_local.connect(self.process_sig_rx_local)

        # connect outgoing signal to receive slots of various subwidgets
        self.sig_tx.connect(self.sel_fil.sig_rx)
        self.sig_tx.connect(self.f_specs.sig_rx)
        self.sig_tx.connect(self.t_specs.sig_rx)
        self.sig_tx.connect(self.w_specs.sig_rx)
        self.sig_tx.connect(self.f_units.sig_rx)

        self.sel_fil.sig_tx.connect(self.sig_rx_local)
        self.f_specs.sig_tx.connect(self.sig_rx_local)
        self.a_specs.sig_tx.connect(self.sig_rx_local)
        self.t_specs.sig_tx.connect(self.sig_rx_local)
        self.w_specs.sig_tx.connect(self.sig_rx_local)
        self.f_units.sig_tx.connect(self.sig_rx_local)

        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.cmb_filter_load.currentIndexChanged.connect(self._load_filter)
        self.cmb_filter_save.currentIndexChanged.connect(self._save_filter)
        self.led_info.editingFinished.connect(self._save_info2dict)
        self.butDesignFilt.clicked.connect(self.start_design_filt)
        self.butQuit.clicked.connect(self.quit_program)  # emit 'close_event'
        # ----------------------------------------------------------------------

    # --------------------------------------------------------------------------
    def _create_layout(self) -> None:
        """
        Create the layout for the widget.
        """
        # ----------------------------------------------------------------------
        # LAYOUT for loading and saving filters
        # ----------------------------------------------------------------------
        lay_h_buttons_load_save = QHBoxLayout()
        lay_h_buttons_load_save.addWidget(self.cmb_filter_load) # Load from mem or file
        lay_h_buttons_load_save.addWidget(self.lbl_info_1)
        lay_h_buttons_load_save.addWidget(self.led_info)
        lay_h_buttons_load_save.addWidget(self.lbl_info_2)
        lay_h_buttons_load_save.addWidget(self.cmb_filter_save)  # <Save Filter> combo
        lay_h_buttons_load_save.setContentsMargins(*params['wdg_margins_spc'])
        lay_v_buttons_load_save = QVBoxLayout()
        lay_v_buttons_load_save.addLayout(lay_h_buttons_load_save)
        self.frm_buttons_load_save = QFrame()
        self.frm_buttons_load_save.setLayout(lay_v_buttons_load_save)
        self.frm_buttons_load_save.setContentsMargins(*params['wdg_margins'])

        # ----------------------------------------------------------------------
        # LAYOUT for Design and Quit buttons
        # ----------------------------------------------------------------------
        lay_h_buttons_action = QHBoxLayout()
        lay_h_buttons_action.addWidget(self.butDesignFilt)  # <Design Filter> button
        lay_h_buttons_action.addWidget(self.butQuit)        # <Quit> button
        lay_h_buttons_action.setContentsMargins(*params['wdg_margins'])

        lay_v_msg = QVBoxLayout()
        lay_v_msg.addWidget(self.lblMsg)

        self.frm_msg = QFrame(self)
        self.frm_msg.setLayout(lay_v_msg)
        lay_v_frm = QVBoxLayout()
        lay_v_frm.addWidget(self.frm_msg)
        lay_v_frm.setContentsMargins(*params['wdg_margins'])

       # ----------------------------------------------------------------------
        # Main LAYOUT
        # ----------------------------------------------------------------------
        lay_v_main = QVBoxLayout(self)
        lay_v_main.addWidget(self.frm_buttons_load_save)  # <Load> & <Save> buttons
        lay_v_main.addWidget(self.sel_fil)  # Design method (IIR - ellip, ...)
        lay_v_main.addLayout(lay_h_buttons_action)  # <Design> & <Quit> buttons
        lay_v_main.addWidget(self.f_units)  # Frequency units
        lay_v_main.addWidget(self.t_specs)  # Target specs
        lay_v_main.addWidget(self.f_specs)  # Freq. specifications
        lay_v_main.addWidget(self.a_specs)  # Amplitude specs
        lay_v_main.addWidget(self.w_specs)  # Weight specs
        lay_v_main.addLayout(lay_v_frm)       # Text message
        lay_v_main.addStretch()
        lay_v_main.setContentsMargins(*params['wdg_margins'])

        self.setLayout(lay_v_main)  # main layout of widget
        # Required to prevent shrinking of subwidgets
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    # --------------------------------------------------------------------------
    def _save_info2dict(self) -> None:
        """
        Update_filter dict and tooltip every time the info field is changed
        """
        fb_set('info', self.led_info.text())
        self.led_info.setToolTip("<span>" + self.led_info_tool_tip + "\n"
                                 + self.led_info.text() + "</span>")
        self.led_info.home(True)  # move cursor to beginning
        self.led_info.deselect()

    # --------------------------------------------------------------------------
    def _update_ui(self) -> None:
        """
        _update_ui is called every time the filter design method or order
        (min / man) has been changed as this usually requires a different set of
        frequency and amplitude specs.

        At this time, the actual filter object instance has been created from
        the name of the design method (e.g. 'cheby1') in select_filter.py.
        Its handle has been stored in `fb.fil_inst`.

        The dict fil[0] with the current filter info is read, then general information
        for the selected filter type and order (min/man) is gathered from
        the filter tree [FTB.fil_tree], i.e. which parameters are needed, which
        widgets are visible and which message shall be displayed.

        Then, the UIs of all subwidgets are updated using their `update_UI()` methods.
        """
        rt = fb_get('rt')  # e.g. 'LP'
        ft = fb_get('ft')  # e.g. 'FIR'
        fc = fb_get('fc')  # e.g. 'equiripple'
        fo = fb_get('fo')  # e.g. 'man'

        # the keys of the all_widgets dict are the names of the subwidgets,
        # the values are a tuple with the corresponding parameters
        all_widgets = FTB.fil_tree[rt][ft][fc][fo]

        # logger.debug("rt: '%s' - ft: '%s' - fc: '%s' - fo: '%s'", rt, ft, fc, fo)
        # logger.debug("fil_tree[rt][ft][fc][fo]:\n\t%s", FTB.fil_tree[rt][ft][fc][fo])

        # update filter order subwidget, called by select_filter:
        # self.sel_fil.load_filter_order()

        # TARGET SPECS: is widget in the dict and is it visible (marker != 'i')?
        if ('tspecs' in all_widgets and len(all_widgets['tspecs']) > 1 and
                all_widgets['tspecs'][0] != 'i'):
            self.t_specs.setVisible(True)
            # disable all subwidgets with marker 'd':
            self.t_specs.setEnabled(all_widgets['tspecs'][0] != 'd')
            self.t_specs.update_ui(new_labels=all_widgets['tspecs'][1])
        else:
            self.t_specs.hide()

        # FREQUENCY SPECS
        if ('fspecs' in all_widgets and len(all_widgets['fspecs']) > 1 and
                all_widgets['fspecs'][0] != 'i'):
            self.f_specs.setVisible(True)
            self.f_specs.setEnabled(all_widgets['fspecs'][0] != 'd')
            self.f_specs.update_ui(new_labels=all_widgets['fspecs'])
        else:
            self.f_specs.hide()

        # AMPLITUDE SPECS
        if ('aspecs' in all_widgets and len(all_widgets['aspecs']) > 1 and
                all_widgets['aspecs'][0] != 'i'):
            self.a_specs.setVisible(True)
            self.a_specs.setEnabled(all_widgets['aspecs'][0] != 'd')
            self.a_specs.update_ui(new_labels=all_widgets['aspecs'])
        else:
            self.a_specs.hide()

        # WEIGHT SPECS
        if ('wspecs' in all_widgets and len(all_widgets['wspecs']) > 1 and
                all_widgets['wspecs'][0] != 'i'):
            self.w_specs.setVisible(True)
            self.w_specs.setEnabled(all_widgets['wspecs'][0] != 'd')
            self.w_specs.update_UI(new_labels=all_widgets['wspecs'])
        else:
            self.w_specs.hide()

        # MESSAGE PANE
        if ('msg' in all_widgets and len(all_widgets['msg']) > 1 and
                all_widgets['msg'][0] != 'i'):
            self.frm_msg.setVisible(True)
            self.frm_msg.setEnabled(all_widgets['msg'][0] != 'd')
            self.lblMsg.setText(all_widgets['msg'][1:][0])
        else:
            self.frm_msg.hide()

        # Update state of "DESIGN FILTER" button
        # It is disabled for "Manual_IIR" and "Manual_FIR" filter classes
        self.color_design_button('changed')

    # --------------------------------------------------------------------------
    def _load_filter(self) -> None:
        """
        Load filter dict `fil[0]` either from file or from memory and update the info text
        via `_load_info_text()` and the widgets via sig_tx: {'data_changed':'filter_loaded'}.
        """
        src = qget_cmb_box(self.cmb_filter_load)
        # 'File' or 'File (all)' selected, update fil[0] resp. fil[0] ... fil[9] from file
        if src in {"file", "file_all"}:
            ret = load_filter(self, all_filters=src == "file_all")
            if ret == -1:
                return  # aborted or error occurred -> do nothing
            if ret != 0:
                logger.error('Unknown return code "%s"!', ret)
                return

        elif src == "def":  # restore default filter
            fb.fil[0] = copy.deepcopy(fb.fil_ref)

        elif src == "def_all":  # Copy defaults to all memories
            for i in range(1, 10):
                fb.fil[i] = copy.deepcopy(fb.fil_ref)

        # 'Mem <i>', copy fil[i] to fil[0]
        else:
            fb.fil[0] = copy.deepcopy(fb.fil[int(src)])

        # update info string
        self._load_info_text()
        self.led_info.setText(str(fb_get('info')))
        self.cmb_filter_load.setCurrentIndex(0)
        self.emit({'data_changed': 'filter_loaded'})

    # --------------------------------------------------------------------------
    def _save_filter(self) -> None:
        """
        Save current filter fb.fil[0] either to file or to one of the memories
        """
        # `dest`` contains the data field of the combo box which is either "file" / "file_all"
        # or the number of the memory location (e.g. "2" for "Mem 2"). This is larger by 1
        # than the combobox index
        dest = qget_cmb_box(self.cmb_filter_save)

        if dest == "file":
            # save current filter to file
            save_filter(self)
        elif dest == "file_all":
            # save all filters
            save_all_filters(self)
        elif dest == "0":
            # filter 0 selected, don't do anything
            return
        else:
            # save fil[0] to selected location
            fb.fil[int(dest)] = copy.deepcopy(fb.fil[0])
            # insert info string into new tool tip
            self.cmb_filter_save.setItemData(
                int(dest) + 1, f"Copy -> Mem {dest}: {self.led_info.text()}", Qt.ToolTipRole)
            self.cmb_filter_load.setItemData(
                int(dest) + 1, f"Load <- Mem {dest}: {self.led_info.text()}", Qt.ToolTipRole)
        self.cmb_filter_save.setCurrentIndex(0)

    # --------------------------------------------------------------------------
    def _load_info_text(self) -> None:
        """
        Reload info text from global dict `fb.fil[0]` and reset 'DESIGN' button
        """
        self.led_info.setText(str(fb_get('info')))
        for i in range(1,10):
            self.cmb_filter_save.setItemData(
                i + 1, f"Copy -> Mem {i}: {str(fb.fil[i]['info'])}", Qt.ToolTipRole)
            self.cmb_filter_load.setItemData(
                i + 1, f"Load <- Mem {i}: {str(fb.fil[i]['info'])}", Qt.ToolTipRole)
        self.color_design_button("ok")

    # --------------------------------------------------------------------------
    def start_design_filt(self) -> None:
        """
        Start the actual filter design process:

        - store the entries of all input widgets in the global filter dict.
        - call the design method, passing the whole dictionary as the
          argument: let the design method pick the needed specs
        - update the input widgets in case weights, corner frequencies etc.
          have been changed by the filter design method
        - the plots are updated via signal-slot connection
        """

        logger.info(
            "Start filter design using method\n\t'%s.%s%s'",
            fb_get('fc'), fb_get('rt'), fb_get('fo'))

        # ----------------------------------------------------------------------
        # A globally accessible instance of selected filter class fc
        # has been instantiated in filter_factory.set_design_method, now
        # call the method specified in the filter dict fil[0].

        # The name of the instance method is constructed from the response
        # type (e.g. 'LP') and the filter order (e.g. 'man'), giving e.g. 'LPman'.
        # The filter is designed by passing the specs in fil[0] to the method,
        # resulting in e.g. cheby1.LPman(fb.fil[0]) and writing back coefficients,
        # P/Z etc. back to fil[0].

        err = call_fil_method(fb_get('rt') + fb_get('fo'), fc=fb_get('fc'))
        # this is the same as e.g.
        # from pyfda.filter_design import ellip
        # inst = ellip.ellip()
        # inst.LPmin()
        # -----------------------------------------------------------------------

        if err > 0:
            self.color_design_button("error")
        elif err == -1:  # filter design cancelled by user
            return
        else:
            # Update filter order in case it has been changed by the
            # design algorithm and emit {'data_changed': 'filter_designed'}
            self.sel_fil.load_filter_order()
            self.color_design_button("ok")

            self.emit({'data_changed': 'filter_designed'})
            logger.info("Designed filter with order = %s", str(fb_get('N')))


    def color_design_button(self, state: str) -> None:
        """
        Color the >> DESIGN FILTER << button according to the filter design state
        using `qstyle_widget()` and the states defined in pyfda_rc.py, e.g.:
        - "ok": filter designed and up to date with specs
        - "changed": specs have been changed and filter needs to be re-designed
        - "error": filter design failed with current specs
        """
        man = "manual" in fb_get('fc').lower()
        self.butDesignFilt.setDisabled(man)
        if man:
            state = 'ok'
        fb.design_filt_state = state
        qstyle_widget(self.butDesignFilt, state)

    # --------------------------------------------------------------------------
    def quit_program(self) -> None:
        """
        When <QUIT> button is pressed, send 'close_event'
        """
        self.emit({'close_event': ''})

# ==============================================================================
def load_filter(self, all_filters: bool = False) -> int:
    """
    Load filter from JSON, zipped binary numpy array or (c)pickled object to
    filter dictionary

    Parameters
    ----------
    all_filters: bool
        If True, load all 10 memory locations, otherwise only the first one.

    Returns
    -------
    0 for success, -1 for file cancel or error
    """
    file_name, file_type = select_file(
        self, title="Load Filter", mode="rb", file_types = ("json", "npz", "pkl"))

    if file_name is None:
        return -1  # operation cancelled or some other error

    if file_type in {"npz", "pkl"}:
        try:
            with io.open(file_name, 'rb') as f:  # open in binary mode for npy and pkl
                if file_type == 'npz':
                    fb_temp = {}
                    # array containing dict, dtype 'object':
                    arr = np.load(f, allow_pickle=True)
                    if not isinstance(arr, np.lib.npyio.NpzFile):
                        logger.error("Tried to load file with 'npz' format, but file type is %s.",
                                       type(arr).__name__)
                        raise IOError("Not a valid npz file!")

                    # convert arrays to lists and extract scalar objects
                    for key in sorted(arr):
                        if np.ndim(arr[key]) == 0:
                            # scalar objects may be extracted with the item() method
                            fb_temp.update({key: arr[key].item()})
                        else:
                            # array objects are converted to list first
                            fb_temp.update({key: arr[key].tolist()})
                else:  # file_type == 'pkl':
                    fb_temp = pickle.load(f)

        except IOError as e:
            logger.error("Failed opening %s!\n%s", file_name, e)
            return -1

    elif file_type == 'json':
        try:
            with io.open(file_name, 'r', encoding='utf-8') as f:  # open in text mode (json files)
                fb_temp = json.load(f)

        except (IOError, json.JSONDecodeError) as e:
            logger.error("Failed loading / opening\n\t%s!\n%s", file_name, e)
            return -1

    else:
        logger.error('Unknown file type "%s"', file_type)
        return -1

    # --- Test loaded file content for correct type and shape ------------------
    if isinstance(fb_temp, list):
        if len(fb_temp) != 10:
            logger.error(
                "File contains a list with wrong length = %d != 10 "
                "which cannot be loaded!", len(fb_temp))
            return -1
        if all_filters:
            pass  # file content is well-formed for loading all filters
        else:
            msg = ("This file contains all 10 memory locations! "
                "Load the first one as current design (Yes) or abort (No)?")
            err = not popup_warning(None, message=msg)
            if not err:
                fb_temp = fb_temp[0]  # only process first filter
            else:
                return -1

    elif type(fb_temp) is dict:
        if not all_filters:
            pass  # file contains a single filter -> o.k.
        else:
            msg = ("This file contains only one filter! "
                "Load as current design (Yes) or abort (No)?")
            err = not popup_warning(None, message=msg)
            if not err:
                all_filters = False  # process as single filter
            else:
                return -1

    else:
        logger.error(
            "Wrong data type '%s' or shape, cannot load file.", type(fb_temp))
        return -1

    # --- Test for correct id and version number ------------------------------
    err = False
    if all_filters:
        fb_id = fb_temp[0]  # test first slice of all filters for correct id
    else:
        fb_id = fb_temp

    if '_id' not in fb_id or len(fb_id['_id']) != 2 or fb_id['_id'][0] != 'pyfda':
        msg = "This is no pyfda filter or an outdated file format! Load anyway?"
        err = not popup_warning(None, message=msg)
    elif str(fb_id['_id'][1]) != FILTER_FILE_VERSION:
        msg = (
            f"The filter file has version {fb_id['_id'][1]} instead of "
            f"required version {FILTER_FILE_VERSION}! Load anyway?")
        err = not popup_warning(None, message=msg)

    # Handle errors occurring during id test
    if err:
        return -1
    if all_filters:
        fb.fil = fb_temp  # assign all filters
    else:
        fb.fil[0] = fb_temp  # only assign one slice

    # --- Sanitize keys by comparing to reference dict -----------------------
    backup_fil()  # backup current filter fb.fil[0]
    try:
        key_errs = compare_dictionaries(fb.fil_ref, fb.fil[0])
        key_errs[0].sort()  # keys missing in the loaded dict
        key_errs[1].sort()  # unsupported keys; keys not in reference dict

        err_str = ""
        if key_errs[0]:
            # '\n'.join(...) converts list to multi-line string
            err_str += (
                f"\n\tThe following {len(key_errs[0])} key(s) have not been found in "
                "the loaded dict,\n"\
                "\tthey are copied with their default values from the reference dict:\n\t\t"
                    + "\n\t\t".join(key_errs[0])
                )
        if key_errs[1]:
            err_str += (
                f"\n\tThe following {len(key_errs[1])} key(s) are not part of the "
                "reference dict and have been ignored:\n\t\t"
                + "\n\t\t".join(key_errs[1])
            )
        if err_str != "":
            logger.warning(err_str)

    # --- Sanitize *values* in filter dictionary, keys are ok by now
        for k in fb.fil[0]:
            # Bytes need to be decoded for py3 to be used as keys later on
            if isinstance(fb.fil[0][k], bytes):
                fb.fil[0][k] = fb.fil[0][k].decode('utf-8')
            if fb.fil[0][k] is None:
                logger.warning("Entry fb.fil[0][%s] is empty!", k)

        if 'ba' not in fb.fil[0]:
            logger.error(
                "Missing key 'ba, cancelling file operation.")
            restore_fil()
            return -1
        if isinstance(fb_get('ba'), np.ndarray):
            pass
        elif isinstance(fb_get('ba'), (list, tuple)):
            fb_set('ba', iter2ndarray(fb_get('ba')))
        else:
            logger.error("Unsuitable 'ba' data type '%s', cancelling file operation.",
                         type(fb_get('ba')).__name__)
        if np.ndim(fb_get('ba')) != 2 or len(fb_get('ba')[0]) < 3:
            logger.error(
                "Unsuitable shape %s of 'ba' data, cancelling file operation.",
                np.shape(fb_get('ba')))
            restore_fil()
            return -1

        if 'zpk' not in fb.fil[0]:
            logger.error("Missing key 'zpk', cancelling file operation.")
            restore_fil()
            return -1
        if isinstance(fb_get('zpk'), np.ndarray):
            pass
        elif isinstance(fb_get('zpk'), (list, tuple)):
            fb_set('zpk', iter2ndarray(fb_get('zpk')))
        else:
            logger.error("Unsuitable 'zpk' data type '%s', cancelling file operation.",
                         type(fb_get('zpk')).__name__)
        if np.ndim(fb_get('zpk')) != 2 or np.shape(fb_get('zpk'))[0] != 3:
            logger.error(
                "Unsuitable shape %s of 'zpk' data, cancelling file operation.",
                np.shape(fb_get('zpk')))
            restore_fil()
            return -1

        if 'sos' not in fb.fil[0]:
            logger.error("Missing key 'sos', creating key and empty list.")
            fb_set('sos', [])
        elif isinstance(fb_get('sos'), (list, tuple)):
            fb_set('sos', iter2ndarray(fb_get('sos')))
        elif not isinstance(fb_get('sos'), np.ndarray):
            logger.error("Unsuitable 'sos' data type '%s', creating empty list.",
                         type(fb_get('sos')).__name__)
            fb_set('sos', [])
        elif np.ndim(fb_get('sos')) != 2 or np.shape(fb_get('sos'))[1] != 6:
            logger.warning("Unsuitable shape %s of 'sos' data, storing empty list.",
                np.shape(fb_get('sos')))
            fb_set('sos', [])
        # TODO: create an extra function, checking whether the sos data can be converted
        # to the correct shape instead of deleting it

        logger.info('Successfully loaded filter\n\t"%s"', file_name)
        dirs.last_file_name = file_name
        dirs.last_file_dir = os.path.dirname(file_name)  # update default working dir
        dirs.last_file_type = file_type  # save new default file type
        return 0

    except Exception as e:
        logger.error("Unexpected error:\n%s", e)
        restore_fil()
        return -1


# ------------------------------------------------------------------------------
def save_filter(self) -> int:
    """
    Save filter `fb.fil[0]` as JSON formatted textfile, zipped binary numpy array
    or pickle object

    Returns
    -------
    0 for success, -1 for file cancel or error
    """
    # provide an identifier with version number for pyfda files
    fb.fil[0].update({'_id': ['pyfda', FILTER_FILE_VERSION]})

    file_name, file_type = select_file(
        self, title="Save Filter", mode='w', file_types = ("json", "npz", "pkl"))

    if not file_name:
        return -1  # operation cancelled or other error

    err = False
    # create a copy of the filter to be saved that only contains keys of the
    # reference filter dict and warn of unsupported keys:
    keys_unsupported = [k for k in fb.fil[0] if k not in fb.fil_ref]
    if keys_unsupported:
        fil_clean = {k:v for k, v in fb.fil[0].items() if k in fb.fil_ref}
        logger.warning(
            "The following keys are ignored because they are not part of the\n"
            "\tfilter reference dict:\n\t%s", keys_unsupported)
    else:
        fil_clean = fb.fil[0]

    if file_type in {"npz", "pkl"}:
        try:
            with io.open(file_name, 'wb') as f:  # open in binary mode
                if file_type == 'npz':
                    np.savez(f, **fil_clean)
                else:  # file_type == 'pkl':
                    pickle.dump(fil_clean, f)  # save in default pickle version

        except IOError as e:
            err = True
            logger.error('Failed saving "%s"!\n%s', file_name, e)

    elif file_type == 'json':
        try:
            with io.open(file_name, 'w', encoding='utf-8') as f:  # open in text mode
                # first, convert dict containing numpy arrays to a pure json string
                fb_fil_clean_json = json.dumps(fil_clean, cls=NumpyEncoder, indent=2,
                                        ensure_ascii=False, sort_keys=True )
                # next, dump the string to a file
                f.write(fb_fil_clean_json)

        except IOError as e:
            err = True
            logger.error('Failed saving "%s"!\n%s', file_name, e)
    else:
        err = True
        logger.error('Unknown file type "%s"', file_type)

    if not err:
        logger.info('Filter saved as\n\t"%s"', file_name)
        dirs.last_file_name = file_name
        dirs.last_file_dir = os.path.dirname(file_name)  # save new default dir
        dirs.last_file_type = file_type  # save new default file type
        return 0
    return -1

# ------------------------------------------------------------------------------
def save_all_filters(self) -> int:
    """
    Save all filters `fb.fil` as JSON formatted textfile, zipped binary numpy array
    or pickle object
    """

    file_name, file_type = select_file(
        self, title="Save All Filters", mode='w', file_types = ("json", "npz", "pkl"))

    if not file_name:
        return -1  # operation cancelled or other error

    err = False
    # create a copy of the filters to be saved that only contains keys of the
    # reference filter dict and warn of unsupported keys:
    fil_clean = [None] * 10
    for i in range(10):
        # provide an identifier with version number for pyfda files
        fb.fil[i].update({'_id': ['pyfda', FILTER_FILE_VERSION]})
        keys_unsupported = [k for k in fb.fil[i] if k not in fb.fil_ref]
        if keys_unsupported != []:
            fil_clean[i] = {k:v for k, v in fb.fil[i].items() if k in fb.fil_ref}
            logger.warning(
                "The following keys are ignored because they are not part of the\n"
                "\tfilter reference dict:\n\t%s", keys_unsupported)
        else:
            fil_clean[i] = fb.fil[i]

    if file_type in {"npz", "pkl"}:
        try:
            with io.open(file_name, 'wb') as f:  # open in binary mode
                if file_type == 'npz':
                    np.savez(f, **fil_clean) # TODO: Doesn't work, this needs to be a mapping
                else:  # file_type == 'pkl':
                    pickle.dump(fil_clean, f)  # save in default pickle version
                    # TODO: Does this work?

        except IOError as e:
            err = True
            logger.error('Failed saving "%s"!\n%s', file_name, e)

    elif file_type == 'json':
        try:
            with io.open(file_name, 'w') as f:  # open in text mode
                # first, convert dict containing numpy arrays to a pure json string
                fb_fil_0_json = json.dumps(fil_clean, cls=NumpyEncoder, indent=2,
                                        ensure_ascii=False, sort_keys=True )
                # next, dump the string to a file
                f.write(fb_fil_0_json)

        except IOError as e:
            err = True
            logger.error('Failed saving "%s"!\n%s', file_name, e)
    else:
        err = True
        logger.error('Unknown file type "%s"', file_type)

    if not err:
        logger.info('Filter saved as\n\t"%s"', file_name)
        dirs.last_file_name = file_name
        dirs.last_file_dir = os.path.dirname(file_name)  # save new default dir
        dirs.last_file_type = file_type  # save new default file type
        return 0
    return -1


# ------------------------------------------------------------------------------
class NumpyEncoder(json.JSONEncoder):
    """
    Special json encoder for numpy and other non-supported types, building upon
    https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, complex):
            if obj.imag < 0:
                return str(obj.real) + str(obj.imag) + "j"
            return str(obj.real) + "+" + str(obj.imag) + "j"
        if callable(obj):
            logger.warning("Object '%s' not JSON serializable as it is a function.", obj)
            return ""

        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError as e:
            logger.warning(
                "Object of type '%s' is not JSON serializable.\n%s", type(obj), e)
            return ""



# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.input_specs`
    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = Input_Specs()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
