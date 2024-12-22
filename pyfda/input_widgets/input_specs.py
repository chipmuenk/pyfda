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
import sys
import copy

from pyfda.libs.compat import (
    Qt, QWidget, QLabel, QFrame, QPushButton, QComboBox, QLineEdit, pyqtSignal,
    QVBoxLayout, QHBoxLayout, QSizePolicy)

import pyfda.filterbroker as fb
import pyfda.filter_factory as ff
from pyfda.libs.pyfda_lib import pprint_log, to_html, first_item
from pyfda.libs.pyfda_qt_lib import qstyle_widget, qcmb_box_populate, qget_cmb_box, qget_selected
from pyfda.libs.pyfda_io_lib import load_filter, save_filter, save_all_filters
from pyfda.pyfda_rc import params

from pyfda.input_widgets import (select_filter, amplitude_specs,
                                 freq_specs, freq_units,
                                 weight_specs, target_specs)
import logging
logger = logging.getLogger(__name__)

classes = {'Input_Specs': 'Specs'}  #: Dict containing class name : display name


class Input_Specs(QWidget):
    """
    Build widget for entering all filter specs
    """
    # class variables (shared between instances if more than one exists)
    sig_rx_local = pyqtSignal(object)  # incoming from subwidgets -> process_sig_rx_local

    sig_rx = pyqtSignal(object)  # incoming from subwidgets -> process_sig_rx
    sig_tx = pyqtSignal(object)  # from process_sig_rx: propagate local signals
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None, objectName="input_specs_inst"):
        super(Input_Specs, self).__init__(parent)
        self.setObjectName(objectName)
        self.tab_label = "Specs"
        self.tool_tip = "Enter and view filter specifications."

        self.led_info_tool_tip = "Filter info:"

        filter_load_help_txt = "Load <- Mem {0}: " + fb.fil[0]['info']
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
            ("file", "File", "Save current filter to file."),
            ("file_all", "File (all)", "Save all filters to file.")
        ]
        self.cmb_filter_load_default = "0"

        filter_save_help_txt = "Copy -> Mem {0}: " + fb.fil[0]['info']
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

        self._construct_UI()

    def process_sig_rx_local(self, dict_sig=None):
        """
        Signals coming in from local subwidgets need to be propagated, so set
        `propagate=True` and proceed with processing in `process_sig_rx`.
        """
        self.process_sig_rx(dict_sig, propagate=True)

    def process_sig_rx(self, dict_sig, propagate=False):
        """
        Process signals coming in via subwidgets and sig_rx

        All signals terminate here unless the flag `propagate=True`.

        The sender name of signals coming in from local subwidgets is changed to
        its parent widget (`input_specs`) to prevent infinite loops.

        """
        if dict_sig['id'] == id(self):
            # logger.warning(f"Stopped infinite loop:\n\tPropagate = {propagate}\
            #               \n{first_item(dict_sig)}")
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
            # kind of input fields changes -> reload filter parameters and update_UI
            self.update_UI(dict_sig)
            self.sel_fil.load_dict()
            # Update state of "DESIGN FILTER" button
            # It is disabled for "Manual_IIR" and "Manual_FIR" filter classes
            self.color_design_button('changed')
        elif 'data_changed' in dict_sig and dict_sig['data_changed'] == 'filter_loaded':
                # Update info string from filter dict & set button = "ok"
                # This is only triggered from global signals
                self.load_dict()

        if propagate:
            # local signals are propagated with the class name and id of this widget,
            # global signals terminate here
            dict_sig.update({'class': self.__class__.__name__, 'id': id(self)})
            self.emit(dict_sig)

    def _construct_UI(self):
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
        lbl_info_1 = QLabel(to_html(">", frmt='b'))
        lbl_info_2 = QLabel(to_html(">", frmt='b'))
        self.led_info = QLineEdit(fb.fil[0]['info'])
        self.led_info.setToolTip(self.led_info_tool_tip)
        # self.led_info.home(True)  # move cursor to beginning of line
        lay_h_buttons_load_save_1 = QHBoxLayout()
        lay_h_buttons_load_save_1.addWidget(self.cmb_filter_load) # Load from mem or file
        lay_h_buttons_load_save_1.addWidget(lbl_info_1)
        lay_h_buttons_load_save_1.addWidget(self.led_info)
        lay_h_buttons_load_save_1.addWidget(lbl_info_2)
        lay_h_buttons_load_save_1.addWidget(self.cmb_filter_save)  # <Save Filter> combo
        lay_h_buttons_load_save_1.setContentsMargins(*params['wdg_margins_spc'])
        lay_v_buttons_load_save = QVBoxLayout()
        lay_v_buttons_load_save.addLayout(lay_h_buttons_load_save_1)
        self.frm_buttons_load_save = QFrame()
        self.frm_buttons_load_save.setLayout(lay_v_buttons_load_save)
        self.frm_buttons_load_save.setContentsMargins(*params['wdg_margins'])

        self.butDesignFilt = QPushButton("DESIGN FILTER", self)
        self.butDesignFilt.setToolTip("Design filter with chosen specs")
        self.butQuit = QPushButton("Quit", self)
        self.butQuit.setToolTip("Exit pyfda tool")
        layHButtons2 = QHBoxLayout()
        layHButtons2.addWidget(self.butDesignFilt)  # <Design Filter> button
        layHButtons2.addWidget(self.butQuit)        # <Quit> button
        layHButtons2.setContentsMargins(*params['wdg_margins'])

        # Subwidget for selecting filter with response type rt (LP, ...),
        #    filter type ft (IIR, ...) and filter class fc (cheby1, ...)
        self.sel_fil = select_filter.SelectFilter(self, objectName="select_filter_inst")

        # Subwidget for selecting the frequency unit and range
        self.f_units = freq_units.FreqUnits(self, objectName="freq_units_inst")

        # Changing the frequency unit requires re-display of frequency specs
        # but it does not influence the actual specs (no specsChanged )
        # Activating the "Sort" button emits 'view_changed'?specs_changed'?, requiring
        # sorting and storing the frequency entries

        # Changing filter parameters / specs requires reloading of parameters
        # in other hierarchy levels, e.g. in the plot tabs

        # Subwidget for Frequency Specs
        self.f_specs = freq_specs.FreqSpecs(self, objectName="freq_specs_corner")

        # Subwidget for Amplitude Specs
        self.a_specs = amplitude_specs.AmplitudeSpecs(self, objectName="amplitude_specs_general")

        # Subwidget for Weight Specs
        self.w_specs = weight_specs.WeightSpecs(self, objectName="weight_specs_inst")

        # Subwidget for target specs (frequency and amplitude)
        self.t_specs = target_specs.TargetSpecs(self, title="Target Specifications",
                                                objectName="target_specs_inst")
        self.t_specs.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)

        # Subwidget for displaying infos on the design method
        self.lblMsg = QLabel(self)
        self.lblMsg.setWordWrap(True)
        layVMsg = QVBoxLayout()
        layVMsg.addWidget(self.lblMsg)

        self.frmMsg = QFrame(self)
        self.frmMsg.setLayout(layVMsg)
        layVFrm = QVBoxLayout()
        layVFrm.addWidget(self.frmMsg)
        layVFrm.setContentsMargins(*params['wdg_margins'])

        # ----------------------------------------------------------------------
        # LAYOUT for input specifications and buttons
        # ----------------------------------------------------------------------
        layVMain = QVBoxLayout(self)
        layVMain.addWidget(self.frm_buttons_load_save)  # <Load> & <Save> buttons
        layVMain.addWidget(self.sel_fil)  # Design method (IIR - ellip, ...)
        layVMain.addLayout(layHButtons2)  # <Design> & <Quit> buttons
        layVMain.addWidget(self.f_units)  # Frequency units
        layVMain.addWidget(self.t_specs)  # Target specs
        layVMain.addWidget(self.f_specs)  # Freq. specifications
        layVMain.addWidget(self.a_specs)  # Amplitude specs
        layVMain.addWidget(self.w_specs)  # Weight specs
        layVMain.addLayout(layVFrm)       # Text message

        layVMain.addStretch()

        layVMain.setContentsMargins(*params['wdg_margins'])

        self.setLayout(layVMain)  # main layout of widget

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

        self.update_UI()  # first time initialization
        self.start_design_filt()  # design first filter using default values

# ------------------------------------------------------------------------------
    def _save_info2dict(self) -> None:
        """
        Update_filter dict and tooltip every time the info field is changed
        """
        fb.fil[0]['info'] = self.led_info.text()
        self.led_info.setToolTip("<span>" + self.led_info_tool_tip + "\n"
                                 + self.led_info.text() + "</span>")
        self.led_info.home(True)  # move cursor to beginning
        self.led_info.deselect()

# ------------------------------------------------------------------------------
    def update_UI(self, dict_sig={}) -> None:
        """
        update_UI is called every time the filter design method or order
        (min / man) has been changed as this usually requires a different set of
        frequency and amplitude specs.

        At this time, the actual filter object instance has been created from
        the name of the design method (e.g. 'cheby1') in select_filter.py.
        Its handle has been stored in fb.fil_inst.

        fb.fil[0] (currently selected filter) is read, then general information
        for the selected filter type and order (min/man) is gathered from
        the filter tree [fb.fil_tree], i.e. which parameters are needed, which
        widgets are visible and which message shall be displayed.

        Then, the UIs of all subwidgets are updated using their "update_UI" method.
        """
        rt = fb.fil[0]['rt']  # e.g. 'LP'
        ft = fb.fil[0]['ft']  # e.g. 'FIR'
        fc = fb.fil[0]['fc']  # e.g. 'equiripple'
        fo = fb.fil[0]['fo']  # e.g. 'man'

        # the keys of the all_widgets dict are the names of the subwidgets,
        # the values are a tuple with the corresponding parameters
        all_widgets = fb.fil_tree[rt][ft][fc][fo]

        # logger.debug("rt: {0} - ft: {1} - fc: {2} - fo: {3}".format(rt, ft, fc, fo))
        # logger.debug("fb.fil_tree[rt][ft][fc][fo]:\n{0}".format(fb.fil_tree[rt][ft][fc][fo]))

        # update filter order subwidget, called by select_filter:
        # self.sel_fil.load_filter_order()

        # TARGET SPECS: is widget in the dict and is it visible (marker != 'i')?
        if ('tspecs' in all_widgets and len(all_widgets['tspecs']) > 1 and
                all_widgets['tspecs'][0] != 'i'):
            self.t_specs.setVisible(True)
            # disable all subwidgets with marker 'd':
            self.t_specs.setEnabled(all_widgets['tspecs'][0] != 'd')
            self.t_specs.update_UI(new_labels=all_widgets['tspecs'][1])
        else:
            self.t_specs.hide()

        # FREQUENCY SPECS
        if ('fspecs' in all_widgets and len(all_widgets['fspecs']) > 1 and
                all_widgets['fspecs'][0] != 'i'):
            self.f_specs.setVisible(True)
            self.f_specs.setEnabled(all_widgets['fspecs'][0] != 'd')
            self.f_specs.update_UI(new_labels=all_widgets['fspecs'])
        else:
            self.f_specs.hide()

        # AMPLITUDE SPECS
        if ('aspecs' in all_widgets and len(all_widgets['aspecs']) > 1 and
                all_widgets['aspecs'][0] != 'i'):
            self.a_specs.setVisible(True)
            self.a_specs.setEnabled(all_widgets['aspecs'][0] != 'd')
            self.a_specs.update_UI(new_labels=all_widgets['aspecs'])
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
            self.frmMsg.setVisible(True)
            self.frmMsg.setEnabled(all_widgets['msg'][0] != 'd')
            self.lblMsg.setText(all_widgets['msg'][1:][0])
        else:
            self.frmMsg.hide()

        # Update state of "DESIGN FILTER" button
        # It is disabled for "Manual_IIR" and "Manual_FIR" filter classes
        self.color_design_button('changed')

# ------------------------------------------------------------------------------
    def _load_filter(self):
        """
        Load filter dict `fb.fil[0]` either from file or from memory and update the
        widgets via `load_dict()` and via sig_tx: {'data_changed':'filter_loaded'}.
        """
        sel = qget_cmb_box(self.cmb_filter_load)
        # 'File' selected, update fil[0] from file
        if sel == "file":
            ret = load_filter(self)
            if ret == 0:
                self.load_dict()
                self.emit({'data_changed': 'filter_loaded'})
            elif ret == -1:
                return  # aborted or error occurred -> do nothing
            else:
                logger.error(f'Unknown return code "{ret}"!')
                return
        # 'File (all)' selected, update fil[0] ... fil[9] from file
        elif sel == "file_all":
            ret = load_filter(self, all_filters=True)
            if ret == 0:
                self.load_dict()
                self.emit({'data_changed': 'filter_loaded'})
            elif ret == -1:
                return  # aborted or error occurred -> do nothing
            else:
                logger.error(f'Unknown return code "{ret}"!')
                return
        # 'Mem <i>', copy fil[i] to fil[0]
        else:
            fb.fil[0] = copy.deepcopy(fb.fil[int(sel)])
            self.load_dict()

        # update info string
        self.led_info.setText(str(fb.fil[0]['info']))
        self.cmb_filter_load.setCurrentIndex(0)
        self.emit({'data_changed': 'filter_loaded'})

# ------------------------------------------------------------------------------
    def _save_filter(self):
        """ Save current filter fb.fil[0] either to file or to one of the memories"""
        # sel contains the data field of the combo box which is either "file" / "file_all"
        # or the number of the memory location (e.g. "2" for "Mem 2"). This is larger by 1
        # than the combobox index
        sel = qget_cmb_box(self.cmb_filter_save)

        if sel == "file":
            # save current filter to file
            save_filter(self)
        elif sel == "file_all":
            # save all filters
            save_all_filters(self)
        elif sel == "0":
            # filter 0 selected, don't do anything
            return
        else:
            # save fil[0] to selected location
            fb.fil[int(sel)] = copy.deepcopy(fb.fil[0])
            # insert info string into new tool tip
            self.cmb_filter_save.setItemData(
                int(sel) + 1, f"Copy -> Mem {sel}: {self.led_info.text()}", Qt.ToolTipRole)
            self.cmb_filter_load.setItemData(
                int(sel) + 1, f"Load <- Mem {sel}: {self.led_info.text()}", Qt.ToolTipRole)
        self.cmb_filter_save.setCurrentIndex(0)

# ------------------------------------------------------------------------------
    def load_dict(self):
        """
        Reload info text from global dict `fb.fil[0]` and reset 'DESIGN' button
        """
        self.led_info.setText(str(fb.fil[0]['info']))
        for i in range(1,10):
            self.cmb_filter_save.setItemData(
                i + 1, f"Copy -> Mem {i}: {str(fb.fil[i]['info'])}", Qt.ToolTipRole)
            self.cmb_filter_load.setItemData(
                i + 1, f"Load <- Mem {i}: {str(fb.fil[i]['info'])}", Qt.ToolTipRole)
        self.color_design_button("ok")

# ------------------------------------------------------------------------------
    def start_design_filt(self):
        """
        Start the actual filter design process:

        - store the entries of all input widgets in the global filter dict.
        - call the design method, passing the whole dictionary as the
          argument: let the design method pick the needed specs
        - update the input widgets in case weights, corner frequencies etc.
          have been changed by the filter design method
        - the plots are updated via signal-slot connection
        """

        try:
            logger.info(
                "Start filter design using method\n\t'{0}.{1}{2}'"
                .format(str(fb.fil[0]['fc']), str(fb.fil[0]['rt']), str(fb.fil[0]['fo'])))

            # ----------------------------------------------------------------------
            # A globally accessible instance fb.fil_inst of selected filter class fc
            # has been instantiated in InputFilter.set_design_method, now
            # call the method specified in the filter dict fil[0].

            # The name of the instance method is constructed from the response
            # type (e.g. 'LP') and the filter order (e.g. 'man'), giving e.g. 'LPman'.
            # The filter is designed by passing the specs in fil[0] to the method,
            # resulting in e.g. cheby1.LPman(fb.fil[0]) and writing back coefficients,
            # P/Z etc. back to fil[0].

            err = ff.fil_factory.call_fil_method(
                fb.fil[0]['rt'] + fb.fil[0]['fo'], fb.fil[0])
            # this is the same as e.g.
            # from pyfda.filter_design import ellip
            # inst = ellip.ellip()
            # inst.LPmin(fb.fil[0])
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
                logger.info(
                    f"Designed filter with order = {str(fb.fil[0]['N'])}")

        except Exception as e:
            if ('__doc__' in str(e)):
                logger.warning(f"Filter design:\n {e.__doc__}\n{e}\n")
            else:
                logger.warning(f"{e}")
            self.color_design_button("error")

    def color_design_button(self, state):
        man = "manual" in fb.fil[0]['fc'].lower()
        self.butDesignFilt.setDisabled(man)
        if man:
            state = 'ok'
        fb.design_filt_state = state
        qstyle_widget(self.butDesignFilt, state)

# ------------------------------------------------------------------------------
    def quit_program(self):
        """
        When <QUIT> button is pressed, send 'close_event'
        """
        self.emit({'close_event': ''})


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.input_widgets.input_specs` """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Input_Specs(None)
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
