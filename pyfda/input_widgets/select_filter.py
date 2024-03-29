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
import sys
from pyfda.libs.compat import (
    QWidget, QLabel, QLineEdit, QComboBox, QFrame,
    QCheckBox, QVBoxLayout, QHBoxLayout, pyqtSignal)

import pyfda.filterbroker as fb
import pyfda.filter_factory as ff
from pyfda.libs.pyfda_lib import safe_eval, first_item
import pyfda.pyfda_rc as rc
from pyfda.libs.pyfda_qt_lib import qget_cmb_box

import logging
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
    from pyfda.libs.pyfda_qt_lib import emit

    def __init__(self, parent=None, objectName="select_filter_inst"):
        super(SelectFilter, self).__init__(parent)

        self.setObjectName(objectName)
        self.fc_last = ''  # previous filter class
        self._construct_UI()
        self._set_response_type()  # first time initialization

    def process_sig_rx(self, dict_sig):
        """
        Process signals coming in via sig_rx

        All signals terminate here.

        The sender name of signals coming in from local subwidgets is changed to
        its parent widget to prevent infinite loops.

        """
        # logger.warning(f"SIG_RX: {first_item(dict_sig)}")
        if dict_sig['id'] == id(self):
            # logger.warning(f"Stopped infinite loop:\n\tPropagate = {propagate}\
            #               \n{first_item(dict_sig)}")
            return

        elif 'data_changed' in dict_sig:
            if dict_sig['data_changed'] == 'filter_loaded':
                """
                Called when a new filter has been LOADED,
                pass new filter data from the global filter dict to load_dict()
                """
            self.load_dict()


    def _construct_UI(self):
        """
        Construct UI with comboboxes for selecting filter:

        - cmbResponseType for selecting response type rt (LP, HP, ...)

        - cmbFilterType for selection of filter type (IIR, FIR, ...)

        - cmbFilterClass for selection of design design class (Chebyshev, ...)

        and populate them from the "filterTree" dict during the initial run.
        Later, calling _set_response_type() updates the three combo boxes.

        See filterbroker.py for structure and content of "filterTree" dict

        """
        # ----------------------------------------------------------------------
        # Combo boxes for filter selection
        # ----------------------------------------------------------------------
        self.cmbResponseType = QComboBox(self, objectName="comboResponseType")
        self.cmbResponseType.setToolTip("Select filter response type.")
        self.cmbFilterType = QComboBox(self, objectName="comboFilterType")
        self.cmbFilterType.setToolTip(
          "<span>Choose filter type, either recursive (Infinite Impulse Response) "
          "or transversal (Finite Impulse Response).</span>")
        self.cmbFilterClass = QComboBox(self, objectName="comboFilterClass")
        self.cmbFilterClass.setToolTip("Select the filter design class.")

        # Adapt comboboxes size dynamically to largest element
        self.cmbResponseType.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmbFilterClass.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        # ----------------------------------------------------------------------
        # Populate combo box with initial settings from fb.fil_tree
        # ----------------------------------------------------------------------
        # Translate short response type ("LP") to displayed names ("Lowpass")
        # (correspondence is defined in pyfda_rc.py) and populate rt combo box
        #
        rt_list = sorted(list(fb.fil_tree.keys()))

        for rt in rt_list:
            try:
                self.cmbResponseType.addItem(rc.rt_names[rt], rt)
            except KeyError as e:
                logger.warning(
                  f"KeyError: {e} has no corresponding full name in rc.rt_names.")
        idx = self.cmbResponseType.findData('LP')  # find index for 'LP'

        if idx == -1:  # Key 'LP' does not exist, use first entry instead
            idx = 0

        self.cmbResponseType.setCurrentIndex(idx)  # set initial index
        rt = qget_cmb_box(self.cmbResponseType)

        for ft in fb.fil_tree[rt]:
            self.cmbFilterType.addItem(rc.ft_names[ft], ft)
        self.cmbFilterType.setCurrentIndex(0)  # set initial index
        ft = qget_cmb_box(self.cmbFilterType)

        for fc in fb.fil_tree[rt][ft]:
            self.cmbFilterClass.addItem(fb.filter_classes[fc]['name'], fc)
        self.cmbFilterClass.setCurrentIndex(0)  # set initial index

        # ----------------------------------------------------------------------
        # Layout for Filter Type Subwidgets
        # ----------------------------------------------------------------------

        layHFilWdg = QHBoxLayout()  # container for filter subwidgets
        layHFilWdg.addWidget(self.cmbResponseType)  # LP, HP, BP, etc.
        layHFilWdg.addStretch()
        layHFilWdg.addWidget(self.cmbFilterType)   # FIR, IIR
        layHFilWdg.addStretch()
        layHFilWdg.addWidget(self.cmbFilterClass)  # bessel, elliptic, etc.

        # ----------------------------------------------------------------------
        # Layout for dynamic filter subwidgets (empty frame)
        # ----------------------------------------------------------------------
        # see Summerfield p. 278
        self.layHDynWdg = QHBoxLayout()  # for additional dynamic subwidgets

        # ----------------------------------------------------------------------
        # Filter Order Subwidgets
        # ----------------------------------------------------------------------
        self.lblOrder = QLabel("<b>Order:</b>")
        self.chkMinOrder = QCheckBox("Minimum", self)
        self.chkMinOrder.setToolTip(
            "<span>Minimum filter order / # of taps is determined automatically.</span>")
        self.lblOrderN = QLabel("<b><i>N =</i></b>")
        self.ledOrderN = QLineEdit(str(fb.fil[0]['N']), self)
        self.ledOrderN.setToolTip("Filter order (# of taps - 1).")

        # --------------------------------------------------
        #  Layout for filter order subwidgets
        # --------------------------------------------------
        layHOrdWdg = QHBoxLayout()
        layHOrdWdg.addWidget(self.lblOrder)
        layHOrdWdg.addWidget(self.chkMinOrder)
        layHOrdWdg.addStretch()
        layHOrdWdg.addWidget(self.lblOrderN)
        layHOrdWdg.addWidget(self.ledOrderN)

        # ----------------------------------------------------------------------
        # OVERALL LAYOUT (stack standard + dynamic subwidgets vertically)
        # ----------------------------------------------------------------------
        self.layVAllWdg = QVBoxLayout()
        self.layVAllWdg.addLayout(layHFilWdg)
        self.layVAllWdg.addLayout(self.layHDynWdg)
        self.layVAllWdg.addLayout(layHOrdWdg)

# ==============================================================================
        frmMain = QFrame(self)
        frmMain.setLayout(self.layVAllWdg)

        layHMain = QHBoxLayout()
        layHMain.addWidget(frmMain)
        layHMain.setContentsMargins(*rc.params['wdg_margins'])

        self.setLayout(layHMain)

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
        self.cmbResponseType.currentIndexChanged.connect(
                lambda: self._set_response_type(enb_signal=True))  # 'LP'
        self.cmbFilterType.currentIndexChanged.connect(
                lambda: self._set_filter_type(enb_signal=True))  # 'IIR'
        self.cmbFilterClass.currentIndexChanged.connect(
                lambda: self._set_design_method(enb_signal=True))  # 'cheby1'
        self.chkMinOrder.clicked.connect(
                lambda: self._set_filter_order(enb_signal=True))  # Min. Order
        self.ledOrderN.editingFinished.connect(
                lambda: self._set_filter_order(enb_signal=True))  # Manual Order
        # ------------------------------------------------------------

# ------------------------------------------------------------------------------
    def load_dict(self):
        """
        Reload comboboxes from filter dictionary to update changed settings
        after loading a filter design from disk.
        `load_dict` uses the automatism of _set_response_type etc.
        of checking whether the previously selected filter design method is
        also available for the new combination.
        """
        # find index for response type:
        rt_idx = self.cmbResponseType.findData(fb.fil[0]['rt'])
        self.cmbResponseType.setCurrentIndex(rt_idx)
        self._set_response_type()

# ------------------------------------------------------------------------------
    def _set_response_type(self, enb_signal=False):
        """
        Triggered when cmbResponseType (LP, HP, ...) is changed:
        Copy selection to self.rt and fb.fil[0] and reconstruct filter type combo

        If previous filter type (FIR, IIR, ...) exists for new rt, set the
        filter type combo box to the old setting
        """
        # Read current setting of comboBox as string and store it in the filter dict
        fb.fil[0]['rt'] = self.rt = qget_cmb_box(self.cmbResponseType)

        # Get list of available filter types for new rt
        ft_list = list(fb.fil_tree[self.rt].keys())  # explicit list() needed for Py3
        # ---------------------------------------------------------------
        # Rebuild filter type combobox entries for new rt setting
        self.cmbFilterType.blockSignals(True)  # don't fire when changed programmatically
        self.cmbFilterType.clear()
        for ft in fb.fil_tree[self.rt]:
            self.cmbFilterType.addItem(rc.ft_names[ft], ft)

        # Is current filter type (e.g. IIR) in list for new rt?
        if fb.fil[0]['ft'] in ft_list:
            ft_idx = self.cmbFilterType.findText(fb.fil[0]['ft'])
            self.cmbFilterType.setCurrentIndex(ft_idx)  # yes, set same ft as before
        else:
            self.cmbFilterType.setCurrentIndex(0)     # no, set index 0

        self.cmbFilterType.blockSignals(False)
        # ---------------------------------------------------------------

        self._set_filter_type(enb_signal)

# ------------------------------------------------------------------------------
    def _set_filter_type(self, enb_signal=False):
        """"
        Triggered when cmbFilterType (IIR, FIR, ...) is changed:
        - read filter type ft and copy it to fb.fil[0]['ft'] and self.ft
        - (re)construct design method combo, adding
          displayed text (e.g. "Chebyshev 1") and hidden data (e.g. "cheby1")
        """
        # Read out current setting of comboBox and convert to string
        fb.fil[0]['ft'] = self.ft = qget_cmb_box(self.cmbFilterType)
#
        logger.debug("InputFilter.set_filter_type triggered: {0}".format(self.ft))

        # ---------------------------------------------------------------
        # Get all available design methods for new ft from fil_tree and
        # - Collect them in fc_list
        # - Rebuild design method combobox entries for new ft setting:
        #    The combobox is populated with the "long name",
        #    the internal name is stored in comboBox.itemData
        self.cmbFilterClass.blockSignals(True)
        self.cmbFilterClass.clear()
        fc_list = []

        for fc in sorted(fb.fil_tree[self.rt][self.ft]):
            self.cmbFilterClass.addItem(fb.filter_classes[fc]['name'], fc)
            fc_list.append(fc)

        logger.debug("fc_list: {0}\n{1}".format(fc_list, fb.fil[0]['fc']))

        # Does new ft also provide the previous design method (e.g. ellip)?
        # Has filter been instantiated?
        if fb.fil[0]['fc'] in fc_list and ff.fil_inst:
            # yes, set same fc as before
            fc_idx = self.cmbFilterClass.findText(
                fb.filter_classes[fb.fil[0]['fc']]['name'])
            logger.debug("fc_idx : %s", fc_idx)
            self.cmbFilterClass.setCurrentIndex(fc_idx)
        else:
            self.cmbFilterClass.setCurrentIndex(0)     # no, set index 0

        self.cmbFilterClass.blockSignals(False)

        self._set_design_method(enb_signal)

# ------------------------------------------------------------------------------
    def _set_design_method(self, enb_signal=False):
        """
        Triggered when cmbFilterClass (cheby1, ...) is changed:
        - read design method fc and copy it to fb.fil[0]
        - create / update global filter instance fb.fil_inst of fc class
        - update dynamic widgets (if fc has changed and if there are any)
        - call load filter order
        """
        fb.fil[0]['fc'] = fc = qget_cmb_box(self.cmbFilterClass)

        if fc != self.fc_last:  # fc has changed:

            # when filter has been changed, try to destroy dynamic widgets of last fc:
            if self.fc_last:
                self._destruct_dyn_widgets()

            # ==================================================================
            """
            Create new instance of the selected filter class, accessible via
            its handle fb.fil_inst
            """
            err = ff.fil_factory.create_fil_inst(fc)
            logger.debug(f"InputFilter.set_design_method triggered: {fc}\n"
                         f"Returned error code {err}")
            # ==================================================================

            # Check whether new design method also provides the old filter order
            # method. If yes, don't change it, else set first available
            # filter order method
            if fb.fil[0]['fo'] not in fb.fil_tree[self.rt][self.ft][fc].keys():
                fb.fil[0].update({'fo': {}})
                # explicit list(dict.keys()) needed for Python 3
                fb.fil[0]['fo'] = list(fb.fil_tree[self.rt][self.ft][fc].keys())[0]

# =============================================================================
#             logger.debug("selFilter = %s"
#                    "filterTree[fc] = %s"
#                    "filterTree[fc].keys() = %s"
#                   %(fb.fil[0], fb.fil_tree[self.rt][self.ft][fc],\
#                     fb.fil_tree[self.rt][self.ft][fc].keys()
#                     ))
#
# =============================================================================
            # construct dyn. subwidgets if available
            if hasattr(ff.fil_inst, 'construct_UI'):
                self._construct_dyn_widgets()

            self.fc_last = fb.fil[0]['fc']

        self.load_filter_order(enb_signal)

# ------------------------------------------------------------------------------
    def load_filter_order(self, enb_signal=False):

        """
        Called by set_design_method or from InputSpecs (with enb_signal = False),
          load filter order setting from fb.fil[0] and update widgets

        """
        # collect dict_keys of available filter order [fo] methods for selected
        # design method [fc] from fil_tree (explicit list() needed for Python 3)
        fo_dict = fb.fil_tree[fb.fil[0]['rt']][fb.fil[0]['ft']][fb.fil[0]['fc']]
        fo_list = list(fo_dict.keys())

        # is currently selected fo setting available for (new) fc ?
        if fb.fil[0]['fo'] in fo_list:
            self.fo = fb.fil[0]['fo']  # keep current setting
        else:
            self.fo = fo_list[0]  # use first list entry from filterTree
            fb.fil[0]['fo'] = self.fo  # and update fo method

        # check whether fo widget is active, disabled or invisible
        if 'fo' in fo_dict[self.fo] and len(fo_dict[self.fo]['fo']) > 1:
            status = fo_dict[self.fo]['fo'][0]
        else:
            status = 'i'

        # Determine which subwidgets are __visible__
        self.chkMinOrder.setVisible('min' in fo_list)
        self.ledOrderN.setVisible(status in {'a', 'd'})
        self.lblOrderN.setVisible(status in {'a', 'd'})

        # Determine which subwidgets are __enabled__
        self.chkMinOrder.setChecked(fb.fil[0]['fo'] == 'min')
        self.ledOrderN.setText(str(fb.fil[0]['N']))
        self.ledOrderN.setEnabled(not self.chkMinOrder.isChecked() and status == 'a')
        self.lblOrderN.setEnabled(not self.chkMinOrder.isChecked() and status == 'a')

        if enb_signal:
            logger.debug("Emit 'filt_changed'")
            self.emit({'filt_changed': 'filter_type'})

# ------------------------------------------------------------------------------
    def _set_filter_order(self, enb_signal=False):
        """
        Triggered when either ledOrderN or chkMinOrder are edited:
        - copy settings to fb.fil[0]
        - emit 'filt_changed' if enb_signal is True
        """
        # Determine which subwidgets are _enabled_
        if self.chkMinOrder.isVisible():
            self.ledOrderN.setEnabled(not self.chkMinOrder.isChecked())
            self.lblOrderN.setEnabled(not self.chkMinOrder.isChecked())

            if self.chkMinOrder.isChecked() is True:
                # update in case N has been changed outside this class
                self.ledOrderN.setText(str(fb.fil[0]['N']))
                fb.fil[0].update({'fo': 'min'})

            else:
                fb.fil[0].update({'fo': 'man'})

        else:
            self.lblOrderN.setEnabled(self.fo == 'man')
            self.ledOrderN.setEnabled(self.fo == 'man')

        # read manual filter order, convert to positive integer and store it
        # in filter dictionary.
        ordn = safe_eval(
            self.ledOrderN.text(), fb.fil[0]['N'], return_type='int', sign='pos')
        ordn = ordn if ordn > 0 else 1
        self.ledOrderN.setText(str(ordn))
        fb.fil[0].update({'N': ordn})

        if enb_signal:
            logger.debug("Emit 'filt_changed'")
            self.emit({'filt_changed': 'filter_order_widget'})

# ------------------------------------------------------------------------------
    def _destruct_dyn_widgets(self):
        """
        Delete the dynamically created filter design subwidget (if there is one)

        see http://stackoverflow.com/questions/13827798/proper-way-to-cleanup-
        widgets-in-pyqt

        This does NOT work when the subwidgets to be deleted and created are
        identical, as the deletion is only performed when the current scope has
        been left (?)! Hence, it is necessary to skip this method when the new
        design method is the same as the old one.
        """

        if hasattr(ff.fil_inst, 'wdg_fil'):
            # not needed, connection is destroyed automatically
            # ff.fil_inst.sig_tx.disconnect()
            try:
                # remove widget from layout
                self.layHDynWdg.removeWidget(self.dyn_wdg_fil)
                # delete UI widget when scope has been left
                self.dyn_wdg_fil.deleteLater()

            except AttributeError as e:
                logger.error("Could not destruct_UI!\n{0}".format(e))

            ff.fil_inst.deleteLater()  # delete QWidget when scope has been left

# ------------------------------------------------------------------------------
    def _construct_dyn_widgets(self):
        """
        Create filter widget UI dynamically (if the filter routine has one) and
        connect its sig_tx signal to sig_tx in this scope.
        """
        ff.fil_inst.construct_UI()
        if hasattr(ff.fil_inst, 'wdg_fil'):
            try:
                self.dyn_wdg_fil = getattr(ff.fil_inst, 'wdg_fil')
                self.layHDynWdg.addWidget(self.dyn_wdg_fil, stretch=1)
            except AttributeError as e:
                logger.warning(e)

        if hasattr(ff.fil_inst, 'sig_tx'):
            ff.fil_inst.sig_tx.connect(self.sig_tx)


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.input_widgets.select_filter` """
    from pyfda.libs.compat import QApplication

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = SelectFilter()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
