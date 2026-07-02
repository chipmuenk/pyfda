# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Subwidget for selecting the filter, consisting of combo boxes for:
- Response Type (LP, HP, Hilbert, ...)
- Filter Type (IIR, FIR, CIC ...)
- Filter Class (Butterworth, ...)
"""
import logging
import sys

from pyfda.libs.compat import (
    QWidget, QLabel, QLineEdit, QComboBox, QFrame,
    QCheckBox, QVBoxLayout, QHBoxLayout, pyqtSignal)

from pyfda.filterbroker import fb_get, fb_set
from pyfda.filter_factory import create_fil_inst, get_fil_inst
from pyfda.tree_builder import Tree_Builder as TB
from pyfda.config_file_parser import ConfigFileParser as CFP
from pyfda.libs.pyfda_lib import safe_eval
from pyfda.libs.pyfda_qt_lib import qget_cmb_box, emit
import pyfda.pyfda_rc as rc

logger = logging.getLogger(__name__)


class SelectFilter(QWidget):
    """
    Construct and read combo boxes for selecting the filter, consisting of the
    following hierarchy:

    1. Response Type rt (LP, HP, Hilbert, ...)
    2. Filter Type ft (IIR, FIR, CIC ...)
    3. Filter Class (Butterworth, ...)

    Every time a combo box is changed manually, the filter tree for the selected
    response resp. filter type is read and the combo box(es) further down in
    the hierarchy are populated according to the available combinations.

    sig_tx({'filt_changed'}) is emitted and propagated to input_filter_specs.py
    where it triggers the recreation of all subwidgets.
    """
    # class variables (shared between instances if more than one exists)
    sig_rx = pyqtSignal(object)  # incoming -> process_sig_rx
    sig_tx = pyqtSignal(object)  # outgoing

    def __init__(self, objectName="select_filter_inst"):
        super().__init__()

        self.setObjectName(objectName)
        self.fc_last = ''  # previous filter class
        self._construct_ui()
        self._create_layout()
        self._set_response_type()  # first time initialization

    # -------------------------------------------------------------------------
    def emit(self, dict_sig):
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig):
        """
        Process signals coming in via sig_rx

        All signals terminate here.

        The sender name of signals coming in from local subwidgets is changed to
        its parent widget to prevent infinite loops.

        """
        # logger.warning("SIG_RX: \n%s", pprint_log(dict_sig))
        if dict_sig['id'] == id(self):
            # logger.warning(f"Stopped infinite loop:\n\tPropagate = {propagate}\
            #               \n{first_item(dict_sig)}")
            return

        if 'data_changed' in dict_sig and dict_sig['data_changed'] == 'filter_loaded':
            # Called when a new filter has been LOADED,
            # updating UI and settings via load_dict()
            self.load_dict()

    # -------------------------------------------------------------------------
    def _construct_ui(self):
        """
        Construct UI with comboboxes for selecting filter:

        - cmb_response_type for selecting response type rt (LP, HP, ...)

        - cmb_filter_type for selection of filter type (IIR, FIR, ...)

        - cmb_filter_class for selection of design design class (Chebyshev, ...)

        and populate them from the "filterTree" dict during the initial run.
        Later, calling _set_response_type() updates the three combo boxes.

        See filterbroker.py for structure and content of "filterTree" dict

        """
        # ----------------------------------------------------------------------
        # Combo boxes for filter selection
        # ----------------------------------------------------------------------
        self.cmb_response_type = QComboBox(self, objectName="comboResponseType")
        self.cmb_response_type.setToolTip("Select filter response type.")
        self.cmb_filter_type = QComboBox(self, objectName="comboFilterType")
        self.cmb_filter_type.setToolTip(
          "<span>Choose filter type, either recursive (Infinite Impulse Response) "
          "or transversal (Finite Impulse Response).</span>")
        self.cmb_filter_class = QComboBox(self, objectName="comboFilterClass")
        self.cmb_filter_class.setToolTip("Select the filter design class.")

        # Adapt comboboxes size dynamically to largest element
        self.cmb_response_type.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmb_filter_type.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmb_filter_class.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # ----------------------------------------------------------------------
        # Populate combo boxes from TB.fil_tree (has been filled by now)
        # ----------------------------------------------------------------------
        # start with response types (LP, HP, ...) and sort them alphabetically
        rt_list = sorted(TB.fil_tree.keys())

        # Translate short response type ("LP") from fil_tree to displayed names ("Lowpass",
        # correspondence is defined in pyfda_rc.py) and populate rt combo box
        for rt in rt_list:
            try:
                self.cmb_response_type.addItem(rc.rt_names[rt], rt)
            except KeyError as e:
                logger.warning(
                  "KeyError: %s has no corresponding full name in rc.rt_names:\n%s", rt, e)
        idx = self.cmb_response_type.findData('LP')  # find index for 'LP'

        if idx == -1:  # Key 'LP' does not exist, use first entry instead
            idx = 0

        self.cmb_response_type.setCurrentIndex(idx)  # set initial index
        rt = qget_cmb_box(self.cmb_response_type)

        # next, populate the filter type combo (IIr, FIR)
        for ft in TB.fil_tree[rt]:
            self.cmb_filter_type.addItem(rc.ft_names[ft], ft)
        self.cmb_filter_type.setCurrentIndex(0)  # set initial index
        ft = qget_cmb_box(self.cmb_filter_type)

        # Finally, populate the filter class combo (Butterworth, Chebyshev, ...)
        for fc in TB.fil_tree[rt][ft]:
            self.cmb_filter_class.addItem(CFP.FILTER_CLASSES_DICT[fc]['name'], fc)
        self.cmb_filter_class.setCurrentIndex(0)  # set initial index

       # ----------------------------------------------------------------------
        # Filter Order Subwidgets
        # ----------------------------------------------------------------------
        self.lbl_order = QLabel("<b>Order:</b>")
        self._chk_min_order = QCheckBox("Minimum", self)
        self._chk_min_order.setToolTip(
            "<span>Minimum filter order / # of taps is determined automatically.</span>")
        self._lbl_order_n = QLabel("<b><i>N =</i></b>")
        self._led_order_n = QLineEdit(str(fb_get('N')), self)
        self._led_order_n.setToolTip("Filter order (# of taps - 1).")

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # connect incoming signals to process_sig_rx and other widgets?!
        self.sig_rx.connect(self.process_sig_rx)

        # ------------------------------------------------------------
        # LOCAL SIGNALS & SLOTS
        # ------------------------------------------------------------
        # Connect comboBoxes and setters, propgate change events hierarchically
        #  through all widget methods and emit 'filt_changed' in the end.
        self.cmb_response_type.currentIndexChanged.connect(
                lambda: self._set_response_type(enb_signal=True))  # 'LP'
        self.cmb_filter_type.currentIndexChanged.connect(
                lambda: self._set_filter_type(enb_signal=True))  # 'IIR'
        self.cmb_filter_class.currentIndexChanged.connect(
                lambda: self._set_design_method(enb_signal=True))  # 'cheby1'
        self._chk_min_order.clicked.connect(
                lambda: self._set_filter_order(enb_signal=True))  # Min. Order
        self._led_order_n.editingFinished.connect(
                lambda: self._set_filter_order(enb_signal=True))  # Manual Order

    # --------------------------------------------------------------------------
    def _create_layout(self) -> None:
        """
        Create the layout for the widget.
        """
        # ----------------------------------------------------------------------
        # Layout for Filter Type Subwidgets
        # ----------------------------------------------------------------------
        lay_h_fil_wdg = QHBoxLayout()  # container for filter subwidgets
        lay_h_fil_wdg.addWidget(self.cmb_response_type)  # LP, HP, BP, etc.
        lay_h_fil_wdg.addStretch()
        lay_h_fil_wdg.addWidget(self.cmb_filter_type)   # FIR, IIR
        lay_h_fil_wdg.addStretch()
        lay_h_fil_wdg.addWidget(self.cmb_filter_class)  # bessel, elliptic, etc.

        # ----------------------------------------------------------------------
        # Layout for dynamic filter subwidgets (empty frame)
        # ----------------------------------------------------------------------
        # see Summerfield p. 278
        self.lay_h_dyn_wdg = QHBoxLayout()  # for additional dynamic subwidgets

        # --------------------------------------------------
        #  Layout for filter order subwidgets
        # --------------------------------------------------
        lay_h_ord_wdg = QHBoxLayout()
        lay_h_ord_wdg.addWidget(self.lbl_order)
        lay_h_ord_wdg.addWidget(self._chk_min_order)
        lay_h_ord_wdg.addStretch()
        lay_h_ord_wdg.addWidget(self._lbl_order_n)
        lay_h_ord_wdg.addWidget(self._led_order_n)

        # ----------------------------------------------------------------------
        # OVERALL LAYOUT (stack standard + dynamic subwidgets vertically)
        # ----------------------------------------------------------------------
        self.lay_v_all_wdg = QVBoxLayout()
        self.lay_v_all_wdg.addLayout(lay_h_fil_wdg)
        self.lay_v_all_wdg.addLayout(self.lay_h_dyn_wdg)
        self.lay_v_all_wdg.addLayout(lay_h_ord_wdg)

        # =======================================================================
        frm_main = QFrame(self)
        frm_main.setLayout(self.lay_v_all_wdg)

        lay_h_main = QHBoxLayout()
        lay_h_main.addWidget(frm_main)
        lay_h_main.setContentsMargins(*rc.params['wdg_margins'])

        self.setLayout(lay_h_main)

    # --------------------------------------------------------------------------
    def load_dict(self):
        """
        Reload comboboxes from filter dictionary to update changed settings
        after loading a filter design from disk.
        `load_dict` uses the automatism of _set_response_type etc.
        of checking whether the previously selected filter design method is
        also available for the new combination.
        """
        # find index for response type:
        rt_idx = self.cmb_response_type.findData(fb_get('rt'))
        self.cmb_response_type.setCurrentIndex(rt_idx)
        self._set_response_type()

    # --------------------------------------------------------------------------
    def _set_response_type(self, enb_signal=False):
        """
        Triggered when cmb_response_type (LP, HP, ...) is changed:
        Copy selection to self.rt and fil[0] and reconstruct filter type combo

        If previous filter type (FIR, IIR, ...) exists for new rt, set the
        filter type combo box to the old setting
        """
        # Read current setting of comboBox as string and store it in the filter dict
        self.rt = qget_cmb_box(self.cmb_response_type)
        fb_set('rt', self.rt)

        # Get list of available filter types for new rt
        ft_list = list(TB.fil_tree[self.rt].keys())  # conversion to list needed for Py3
        # ---------------------------------------------------------------
        # Rebuild filter type combobox entries for new rt setting
        self.cmb_filter_type.blockSignals(True)  # don't fire when changed programmatically
        self.cmb_filter_type.clear()
        for ft in TB.fil_tree[self.rt]:
            self.cmb_filter_type.addItem(rc.ft_names[ft], ft)

        # Is current filter type (e.g. IIR) in list for new rt?
        if fb_get('ft') in ft_list:
            ft_idx = self.cmb_filter_type.findText(fb_get('ft'))
            self.cmb_filter_type.setCurrentIndex(ft_idx)  # yes, set same ft as before
        else:
            self.cmb_filter_type.setCurrentIndex(0)     # no, set index 0

        self.cmb_filter_type.blockSignals(False)
        # ---------------------------------------------------------------

        self._set_filter_type(enb_signal)

    # --------------------------------------------------------------------------
    def _set_filter_type(self, enb_signal=False):
        """"
        Triggered when cmb_filter_type (IIR, FIR, ...) is changed:
        - read filter type ft and copy it to fil[0]['ft'] and self.ft
        - (re)construct design method combo, adding
          displayed text (e.g. "Chebyshev 1") and hidden data (e.g. "cheby1")
        """
        # Read out current setting of comboBox and convert to string
        self.ft = qget_cmb_box(self.cmb_filter_type)
        fb_set('ft', self.ft)

        logger.debug("SelectFilter.set_filter_type triggered: %s", self.ft)

        # ---------------------------------------------------------------
        # Get all available design methods for new ft from fil_tree and
        # - Collect them in fc_list
        # - Rebuild design method combobox entries for new ft setting:
        #    The combobox is populated with the "long name",
        #    the internal name is stored in comboBox.itemData
        self.cmb_filter_class.blockSignals(True)
        self.cmb_filter_class.clear()
        fc_list = []

        for fc in sorted(TB.fil_tree[self.rt][self.ft]):
            self.cmb_filter_class.addItem(CFP.FILTER_CLASSES_DICT[fc]['name'], fc)
            fc_list.append(fc)

        logger.debug("fc_list: %s\n%s", fc_list, fb_get('fc'))

        # Does new ft also provide the previous design method (e.g. ellip)?
        # Has filter been instantiated?
        if fb_get('fc') in fc_list and get_fil_inst():
            # yes, set same fc as before
            fc_idx = self.cmb_filter_class.findText(
                CFP.FILTER_CLASSES_DICT[fb_get('fc')]['name'])
            logger.debug("fc_idx : %s", fc_idx)
            self.cmb_filter_class.setCurrentIndex(fc_idx)
        else:
            self.cmb_filter_class.setCurrentIndex(0)     # no, set index 0

        self.cmb_filter_class.blockSignals(False)

        self._set_design_method(enb_signal)

    # --------------------------------------------------------------------------
    def _set_design_method(self, enb_signal=False):
        """
        Triggered when cmb_filter_class (cheby1, ...) is changed:
        - read design method fc and copy it to fil[0]
        - create / update filter instance fil_inst of fc class
        - update dynamic widgets (if fc has changed and if there are any)
        - call load filter order
        """
        fc = qget_cmb_box(self.cmb_filter_class)
        fb_set('fc', fc)

        if fc != self.fc_last:  # fc has changed:

            # when filter has been changed, try to destroy dynamic widgets of last fc:
            if self.fc_last:
                self._destruct_dyn_widgets()

            # ==================================================================
            # Create new instance of the selected filter class, accessible via
            # its handle fil_inst
            err = create_fil_inst(fc)
            logger.debug(
                "create_fil_inst triggered: %s\n\tReturned error code %s", fc, err)
            # ==================================================================

            # Check whether new design method also provides the old filter order method.
            # If yes, don't change it, else set first available filter order method.
            if fb_get('fo') not in TB.fil_tree[self.rt][self.ft][fc].keys():
                # explicit list(dict.keys()) needed for Python 3
                fb_set('fo', list(TB.fil_tree[self.rt][self.ft][fc].keys())[0])

            # ===================================================================
            # logger.debug("selFilter = %s"
            #        "filterTree[fc] = %s"
            #        "filterTree[fc].keys() = %s"
            #       %(fil[0], TB.fil_tree[self.rt][self.ft][fc],\
            #         TB.fil_tree[self.rt][self.ft][fc].keys()
            #         ))
            # ===================================================================
            # construct dyn. subwidgets if available
            if hasattr(get_fil_inst(), 'has_ui') and get_fil_inst().has_ui:
                self._construct_dyn_widgets()

            self.fc_last = fb_get('fc')  # store current fc as last fc

        self.load_filter_order(enb_signal)

    # --------------------------------------------------------------------------
    def load_filter_order(self, enb_signal=False):
        """
        Called by set_design_method or from InputSpecs (with enb_signal = False),
          load filter order setting from fil[0] and update widgets
        """
        # collect dict_keys of available filter order [fo] methods for selected
        # design method [fc] from fil_tree (explicit list() needed for Python 3)
        fo_dict = TB.fil_tree[fb_get('rt')][fb_get('ft')][fb_get('fc')]
        fo_list = list(fo_dict.keys())

        # is currently selected fo setting available for (new) fc ?
        if fb_get('fo') in fo_list:
            self.fo = fb_get('fo')  # keep current setting
        else:
            self.fo = fo_list[0]  # use first list entry from filterTree
            fb_set('fo', self.fo)  # and update fo method

        # check whether fo widget is active, disabled or invisible
        if 'fo' in fo_dict[self.fo] and len(fo_dict[self.fo]['fo']) > 1:
            status = fo_dict[self.fo]['fo'][0]
        else:
            status = 'i'

        # Determine which subwidgets are __visible__
        self._chk_min_order.setVisible('min' in fo_list)
        self._led_order_n.setVisible(status in {'a', 'd'})
        self._lbl_order_n.setVisible(status in {'a', 'd'})

        # Determine which subwidgets are __enabled__
        self._chk_min_order.setChecked(fb_get('fo') == 'min')
        self._led_order_n.setText(str(fb_get('N')))
        self._led_order_n.setEnabled(not self._chk_min_order.isChecked() and status == 'a')
        self._lbl_order_n.setEnabled(not self._chk_min_order.isChecked() and status == 'a')

        if enb_signal:
            self.emit({'filt_changed': 'filter_type'})

    # ------------------------------------------------------------------------------
    def _set_filter_order(self, enb_signal=False):
        """
        Triggered when either _led_order_n or _chk_min_order are edited:
        - copy settings to fil[0]
        - emit 'filt_changed' if enb_signal is True
        """
        # Determine which subwidgets are _enabled_
        if self._chk_min_order.isVisible():
            self._led_order_n.setEnabled(not self._chk_min_order.isChecked())
            self._lbl_order_n.setEnabled(not self._chk_min_order.isChecked())

            if self._chk_min_order.isChecked() is True:
                # update in case N has been changed outside this class
                self._led_order_n.setText(str(fb_get('N')))
                fb_set('fo', 'min')

            else:
                fb_set('fo', 'man')

        else:
            self._lbl_order_n.setEnabled(self.fo == 'man')
            self._led_order_n.setEnabled(self.fo == 'man')

        # read manual filter order, convert to positive integer and store it
        # in filter dictionary.
        ordn = safe_eval(
            self._led_order_n.text(), fb_get('N'), return_type='int', sign='pos')
        ordn = ordn if ordn > 0 else 1
        self._led_order_n.setText(str(ordn))
        fb_set('N', ordn)

        if enb_signal:
            logger.debug("Emit 'filt_changed'")
            self.emit({'filt_changed': 'filter_order_widget'})

    # ------------------------------------------------------------------------------
    def _destruct_dyn_widgets(self):
        """
        Delete the dynamically instantiated filter design subwidget 'wdg_fil'
        (if there is one).

        see http://stackoverflow.com/questions/13827798/proper-way-to-cleanup-
        widgets-in-pyqt

        This does NOT work when the subwidgets to be deleted and created are
        identical, as the deletion is only performed after the current scope has
        been left (?)! Hence, it is necessary to skip this method when the new
        design method is the same as the old one.
        """

        if hasattr(get_fil_inst(), 'wdg_fil'):
            # not needed, connection is destroyed automatically
            # get_fil_inst().sig_tx.disconnect()
            if hasattr(self, 'dyn_wdg_fil'):
                try:
                    # remove widget from layout
                    self.lay_h_dyn_wdg.removeWidget(self.dyn_wdg_fil)
                    # delete UI widget when scope has been left
                    self.dyn_wdg_fil.deleteLater()

                except AttributeError as e:
                    logger.error("Could not destruct_ui!\n\t%s}", e)
            else:
                logger.error("Dynamic filter instance 'wdg_fil' does not exist, "
                             "you should not see this message!")

            get_fil_inst().deleteLater()  # delete QWidget when scope has been left

            # try:
            #     get_fil_inst().deleteLater()  # delete QWidget when scope has been left
            # except RuntimeError as e:
            #     logger.error(e)
            # else:
            #     logger.error("Dynamic filter instance 'fil_inst' does not exist, "
            #                  "you should not see this message!")

    # ------------------------------------------------------------------------------
    def _construct_dyn_widgets(self):
        """
        Create filter widget UI dynamically and
        connect its sig_tx signal to sig_tx in this scope.
        """
        if hasattr(get_fil_inst(), 'wdg_fil'):
            try:
                self.dyn_wdg_fil = get_fil_inst().wdg_fil
                self.lay_h_dyn_wdg.addWidget(self.dyn_wdg_fil, stretch=1)
            except AttributeError as e:
                logger.warning(e)

        if hasattr(get_fil_inst(), 'sig_tx'):
            get_fil_inst().sig_tx.connect(self.sig_tx)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.select_filter`
    from pyfda.libs.compat import QApplication

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.QSS_RC)
    mainw = SelectFilter()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
