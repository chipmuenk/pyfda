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

from pyfda.libs.compat import (
    QWidget, QLabel, QFrame, QPushButton, pyqtSignal, QVBoxLayout, QHBoxLayout)

import pyfda.filterbroker as fb
import pyfda.filter_factory as ff
from pyfda.libs.pyfda_lib import pprint_log
from pyfda.libs.pyfda_qt_lib import qstyle_widget
from pyfda.libs.pyfda_io_lib import load_filter, save_filter
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

    def __init__(self, parent=None):
        super(Input_Specs, self).__init__(parent)
        self.tab_label = "Specs"
        self.tool_tip = "Enter and view filter specifications."

        self._construct_UI()

    def process_sig_rx_local(self, dict_sig=None):
        """
        Flag signals coming in from local subwidgets with `propagate=True` before
        proceeding with processing in `process_sig_rx`.
        """
        self.process_sig_rx(dict_sig, propagate=True)

    def process_sig_rx(self, dict_sig=None, propagate=False):
        """
        Process signals coming in via subwidgets and sig_rx

        All signals terminate here unless the flag `propagate=True`.

        The sender name of signals coming in from local subwidgets is changed to
        its parent widget (`input_specs`) to prevent infinite loops.

        """
        logger.info(f"SIG_RX: {pprint_log(dict_sig)}")
        if dict_sig['id'] == id(self):
            # logger.warning(f"Stopped infinite loop:\n\tPropagate = {propagate}\
            #               \n{pprint_log(dict_sig)}")
            return
        elif 'view_changed' in dict_sig:
            self.f_specs.load_dict()
            self.t_specs.load_dict()
        elif 'specs_changed' in dict_sig:
            self.f_specs.sort_dict_freqs()
            self.t_specs.f_specs.sort_dict_freqs()
            self.color_design_button("changed")
        elif 'filt_changed' in dict_sig:
            # Changing the filter design requires updating UI because number or
            # kind of input fields changes -> call update_UI
            self.update_UI(dict_sig)
        elif 'data_changed' in dict_sig:
            if dict_sig['data_changed'] == 'filter_loaded':
                """
                Called when a new filter has been LOADED:
                Pass new filter data from the global filter dict by
                specifically calling SelectFilter.load_dict()
                """
                self.sel_fil.load_dict()  # update select_filter widget
            # Pass new filter data from the global filter dict & set button = "ok"
            self.load_dict()

        if propagate:
            # local signals are propagated with the name of this widget,
            # global signals terminate here
            dict_sig.update({'class': self.__class__.__name__})
            self.emit(dict_sig)

    def _construct_UI(self):
        """
        Construct User Interface from all input subwidgets
        """
        self.butLoadFilt = QPushButton("LOAD FILTER", self)
        self.butLoadFilt.setToolTip("Load filter from disk")
        self.butSaveFilt = QPushButton("SAVE FILTER", self)
        self.butSaveFilt.setToolTip("Save filter todisk")
        layHButtons1 = QHBoxLayout()
        layHButtons1.addWidget(self.butLoadFilt)  # <Load Filter> button
        layHButtons1.addWidget(self.butSaveFilt)  # <Save Filter> button
        layHButtons1.setContentsMargins(*params['wdg_margins_spc'])

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
        self.sel_fil = select_filter.SelectFilter(self)
        self.sel_fil.setObjectName("select_filter")
        self.sel_fil.sig_tx.connect(self.sig_rx_local)

        # Subwidget for selecting the frequency unit and range
        self.f_units = freq_units.FreqUnits(self)
        self.f_units.setObjectName("freq_units")
        self.f_units.sig_tx.connect(self.sig_rx_local)

        # Changing the frequency unit requires re-display of frequency specs
        # but it does not influence the actual specs (no specsChanged )
        # Activating the "Sort" button emits 'view_changed'?specs_changed'?, requiring
        # sorting and storing the frequency entries

        # Changing filter parameters / specs requires reloading of parameters
        # in other hierarchy levels, e.g. in the plot tabs

        # Subwidget for Frequency Specs
        self.f_specs = freq_specs.FreqSpecs(self)
        self.f_specs.setObjectName("freq_specs")
        self.f_specs.sig_tx.connect(self.sig_rx_local)
        self.sig_tx.connect(self.f_specs.sig_rx)
        # Subwidget for Amplitude Specs
        self.a_specs = amplitude_specs.AmplitudeSpecs(self)
        self.a_specs.setObjectName("amplitude_specs")
        self.a_specs.sig_tx.connect(self.sig_rx_local)
        # Subwidget for Weight Specs
        self.w_specs = weight_specs.WeightSpecs(self)
        self.w_specs.setObjectName("weight_specs")
        self.w_specs.sig_tx.connect(self.sig_rx_local)
        # Subwidget for target specs (frequency and amplitude)
        self.t_specs = target_specs.TargetSpecs(self, title="Target Specifications")
        self.t_specs.setObjectName("target_specs")
        self.t_specs.sig_tx.connect(self.sig_rx_local)
        self.sig_tx.connect(self.t_specs.sig_rx)
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
        layVMain.addLayout(layHButtons1)  # <Load> & <Save> buttons
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
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx_local.connect(self.process_sig_rx_local)
        self.butLoadFilt.clicked.connect(self._load_filter)
        self.butSaveFilt.clicked.connect(lambda: save_filter(self))
        self.butDesignFilt.clicked.connect(self.start_design_filt)
        self.butQuit.clicked.connect(self.quit_program)  # emit 'quit_program'
        # ----------------------------------------------------------------------

        self.update_UI()  # first time initialization
        self.start_design_filt()  # design first filter using default values

# ------------------------------------------------------------------------------
    def update_UI(self, dict_sig={}):
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
        self.color_design_button("changed")

# ------------------------------------------------------------------------------
    def _load_filter(self):
        ret = load_filter(self)
        if ret == 0:
            self.load_dict()
            self.emit({'data_changed': 'filter_loaded'})
        elif ret == -1:
            return  # error occurred, do nothing
        else:
            logger.error(f'Unknown return code "{ret}"!')

# ------------------------------------------------------------------------------
    def load_dict(self):
        """
        Reload all specs/parameters entries from global dict fb.fil[0],
        using the "load_dict" methods of the individual classes
        """
        self.sel_fil.load_dict()  # select filter widget
        self.f_units.load_dict()  # frequency units widget
        self.f_specs.load_dict()  # frequency specification widget
        self.a_specs.load_dict()  # magnitude specs with unit
        self.w_specs.load_dict()  # weight specification
        self.t_specs.load_dict()  # target specs

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
                # Update filter order. weights and freq display in case they
                # have been changed by the design algorithm
                self.sel_fil.load_filter_order()
                self.w_specs.load_dict()
                self.f_specs.load_dict()
                self.color_design_button("ok")

                self.emit({'data_changed': 'filter_designed'})
                logger.info(
                    'Designed filter with order = {0}'.format(str(fb.fil[0]['N'])))
# =============================================================================
#                 logger.debug("Results:\n"
#                     "F_PB = %s, F_SB = %s "
#                     "Filter order N = %s\n"
#                     "NDim fil[0]['ba'] = %s\n\n"
#                     "b,a = %s\n\n"
#                     "zpk = %s\n",
#                     str(fb.fil[0]['F_PB']), str(fb.fil[0]['F_SB']), str(fb.fil[0]['N']),
#                     str(np.ndim(fb.fil[0]['ba'])), pformat(fb.fil[0]['ba']),
#                     pformat(fb.fil[0]['zpk']))
#
# =============================================================================
        except Exception as e:
            if ('__doc__' in str(e)):
                logger.warning("Filter design:\n %s\n %s\n", e.__doc__, e)
            else:
                logger.warning("{0}".format(e))
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
        When <QUIT> button is pressed, send 'quit_program'
        """
        self.emit({'quit_program': ''})


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
