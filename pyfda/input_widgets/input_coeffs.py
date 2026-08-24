# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for displaying and modifying filter coefficients
"""
import copy
import logging
import sys

import numpy as np

from pyfda.filterbroker import fb_get, fb_set, get_fx

from pyfda.libs.compat import (
    Qt, QWidget, QApplication, QTableWidget, QTableWidgetItem, QVBoxLayout, pyqtSignal,
    QColor, QBrush)
import pyfda.libs.pyfda_dirs as dirs
from pyfda.libs.pyfda_lib import safe_eval, pprint_log
from pyfda.libs.pyfda_qt_lib import (
    emit, qstyle_widget, qset_cmb_box, qget_cmb_box, qget_selected)
from pyfda.libs.pyfda_io_lib import qtable2csv, export_fil_data, select_file, file2array
from pyfda.libs.pyfda_sig_lib import zeros_with_val, fil_save
from pyfda.pyfda_rc import params

from pyfda.input_widgets.item_delegate_coeffs import ItemDelegateCoeffs
from pyfda.input_widgets.input_coeffs_ui import Input_Coeffs_UI

logger = logging.getLogger(__name__)

# TODO: Fixpoint coefficients do not properly convert complex -> float when saving
#       the filter?
# TODO: This ItemDelegate method displayText is called again and again when an
#        item is selected?!
# TODO: negative values for WI don't work correctly
#
# TODO: Filters need to be scaled properly, see e.g.
#       http://radio.feld.cvut.cz/matlab/toolbox/filterdesign/normalize.html
#       http://www.ue.eti.pg.gda.pl/~wrona/lab_dsp/cw05/matlab/Help1.pdf
#       https://stackoverflow.com/questions/68206713/scipy-filter-force-minimal-value-of-sos-coefficient-to-prepare-integer-filter

classes = {'Input_Coeffs': 'b,a'}  #: Dict containing class name : display name

class Input_Coeffs(QWidget):
    """
    Widget with a (sort of) model-view architecture for viewing / editing /
    entering data contained in `self.ba` which is a list of two numpy arrays:

    - `self.ba[0]` contains the numerator coefficients ("b")
    - `self.ba[1]` contains the denominator coefficients ("a")

    The lists don't neccessarily have the same length but they are always defined.
    For FIR filters, `self.ba[1][0] = 1`, all other elements are zero.

    The length of both lists can be egalized with `self._equalize_ba_length()`.

    Views / formats are handled by the ItemDelegate() class.
    """
    sig_tx = pyqtSignal(object)  # emitted when filter has been saved
    sig_rx = pyqtSignal(object)  # incoming from input_tab_widgets

    # -------------------------------------------------------------------------
    def __init__(self):
        super().__init__()

        self.opt_widget = None  # handle for pop-up options widget
        self.tool_tip = "Display and edit filter coefficients."
        self.tab_label = "b,a"

        self.data_changed = True  # initialize flag: filter data has been changed
        self.fx_specs_changed = True  # fixpoint specs have been changed outside

        self.ui = Input_Coeffs_UI()  # create the UI part with buttons etc.

        # handles to quantization objects (`fx.Fixed()` instances) of coefficient widgets
        self.Q = [self.ui.wdg_wq_coeffs_b.Q,
                     self.ui.wdg_wq_coeffs_a.Q]

        self._construct_ui()

    # -------------------------------------------------------------------------
    def emit(self, dict_sig: dict) -> None:
        """
        Access imported function `emit()` as instance method, passing `self`
        with its attributes
        """
        emit(self, dict_sig)

    # -------------------------------------------------------------------------
    def process_sig_rx(self, dict_sig: dict) -> None:
        """
        Process signals coming from sig_rx
        """
        logger.debug("SIG_RX: vis=%s\n%s", self.isVisible(), pprint_log(dict_sig))

        if dict_sig['id'] == id(self):
            # logger.warning(f'Stopped infinite loop: "{first_item(dict_sig)}"')
            return

        if 'ui_global_changed' in dict_sig\
                and dict_sig['ui_global_changed'] == 'csv':
            self.ui.but_csv_options.setChecked(dirs.csv_options_handle is not None)
            return

        if 'ui_local_changed' in dict_sig and 'sender_name' in dict_sig and\
                dict_sig['sender_name'] in {'fx_ui_wq_coeffs_a', 'fx_ui_wq_coeffs_b'}:
            # local events from UI, trigger requant and refresh table
            self.refresh_table()
            self.emit({'fx_sim': 'specs_changed'})
            return

        if self.isVisible():
            if self.data_changed or 'data_changed' in dict_sig:
                self.load_dict()
                self.data_changed = False
            if self.fx_specs_changed or\
                    ('fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed'):
                # global event, update widget dicts and table
                self.dict2ui()
                self.fx_specs_changed = False
        else:
            # TODO: draw wouldn't be necessary for 'view_changed', only update view
            # TODO: what is emitted when fixpoint formats are changed?
            if 'data_changed' in dict_sig:
                self.data_changed = True
            elif 'fx_sim' in dict_sig and dict_sig['fx_sim'] == 'specs_changed':
                self.fx_specs_changed = True

# ------------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        # ---------------------------------------------------------------------
        #   Coefficient table widget
        # ---------------------------------------------------------------------
        self.tblCoeff = QTableWidget(self)
        self.tblCoeff.setAlternatingRowColors(True)
        # highlight section of header when a corresponding cell is selected
        self.tblCoeff.horizontalHeader().setHighlightSections(True)
        self.tblCoeff.horizontalHeader().setFont(self.ui.bfont)

#        self.tblCoeff.QItemSelectionModel.Clear
        self.tblCoeff.setDragEnabled(True)
#        self.tblCoeff.setDragDropMode(QAbstractItemView.InternalMove) # doesn't work
        self.tblCoeff.setItemDelegate(ItemDelegateCoeffs(self))

        # ============== Main UI Layout =====================================
        lay_v_main = QVBoxLayout()
        lay_v_main.setAlignment(Qt.AlignTop)  # only affects the first widget (intended)
        lay_v_main.addWidget(self.ui)
        lay_v_main.addWidget(self.tblCoeff)
        lay_v_main.setContentsMargins(*params['wdg_margins'])
        self.setLayout(lay_v_main)

        # initialize, quantize + refresh table with default values from filter dict
        self.load_dict()

        # ----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        self.sig_rx.connect(self.process_sig_rx)
        # ----------------------------------------------------------------------
        # LOCAL (UI) SIGNALS & SLOTs
        # ----------------------------------------------------------------------
        # wdg.textChanged() is emitted when contents of widget changes
        # wdg.textEdited() is only emitted for user changes
        # wdg.editingFinished() is only emitted for user changes
        self.ui.spn_digits.editingFinished.connect(self.refresh_table)

        self.ui.but_table_export.clicked.connect(self.export_table)
        self.ui.but_table_import.clicked.connect(self._import)

        self.ui.cmb_filter_type.currentIndexChanged.connect(self._filter_type)

        self.ui.but_del_cells.clicked.connect(self._delete_cells)
        self.ui.but_add_cells.clicked.connect(self._add_cells)
        self.ui.but_undo.clicked.connect(self.load_dict)
        self.ui.but_apply.clicked.connect(self._save_dict)
        self.ui.but_clear.clicked.connect(self.clear_table)
        self.ui.led_eps.editingFinished.connect(self._set_eps)
        self.ui.but_set_zero.clicked.connect(self._set_coeffs_zero)

        # store new settings and refresh table
        self.ui.cmb_fx_base.currentIndexChanged.connect(self.fx_base2dict)
        self.ui.cmb_qfrmt.currentIndexChanged.connect(self.qfrmt2dict)

        self.ui.wdg_wq_coeffs_a.sig_tx.connect(self.process_sig_rx)
        self.ui.wdg_wq_coeffs_b.sig_tx.connect(self.process_sig_rx)

        self.ui.but_quant.clicked.connect(self.quant_coeffs_apply)

        self.ui.sig_tx.connect(self.sig_tx)

# ------------------------------------------------------------------------------
    def quant_coeffs_view(self) -> None:
        """
        This method only creates a view on the quantized coefficients and stores
        it in `self.ba_q`, the actual coefficients in `self.ba` remain unchanged!

        * Reset overflow counters

        * Quantize filter coefficients `self.ba` with quantizer objects
          `self.Q[0]` and `self.Q[1]` for `b` and `a` coefficients respectively
          and store them in the array `self.ba_q`. Depending on the number base
          (float, dec, hex, ...) the result can be of type float or string.

        *  Store pos. / neg. overflows in the 3rd and 4th column of `self.ba_q` as
           0 or +/- 1.
        """

        # Reset overflow counters of quantization objects
        self.Q[0].resetN()
        self.Q[1].resetN()

        if np.isscalar(self.ba[0]) or np.isscalar(self.ba[1]):
            logger.error("No proper filter, coefficients are scalar!")
            return

        len_b = len(self.ba[0])
        len_a = len(self.ba[1])

        # Create a copy of the 'a' coefficients without the "1" as this could create
        # false overflows during quantization. The "1" is always printed though
        # by the `ItemDelegate.initStyleOption()` method

        a = np.concatenate(([0.], self.ba[1][1:]))

        # Quantize coefficients and store them in `self.ba_q` as a list of arrays
        # with the following structure:
        # [b coefficients, a coefficients, b overflows, a overflows]
        # where overflow items can be -1, 0, +1: 0 = no overflow, -1 = underflow, +1 = overflow

        # Float format: Set ba_q = ba, all overflow items are = 0
        if not get_fx():
            if fb_get('qfrmt') == 'float64':
                self.ba_q = [self.ba[0],
                            self.ba[1],
                            np.zeros(len_b),
                            np.zeros(len_a),
                            ]
            else:
                self.ba_q = [self.ba[0].astype(np.float32),
                            self.ba[1].astype(np.float32),
                            np.zeros(len_b),
                            np.zeros(len_a),
                            ]
        # Fixpoint decimal format: Print quantized coefficients in numeric format
        # with a defined number of `Q[0].places` resp. `Q[1].places``
        elif fb_get('fx_base') == 'dec':
            self.ba_q = [
                [f"{x:>{self.Q[0].places}}" for x in self.Q[0].float2frmt(self.ba[0])],
                [f"{x:>{self.Q[1].places}}" for x in self.Q[1].float2frmt(a)],
                self.Q[0].ovr_flag,
                self.Q[1].ovr_flag
                        ]
        # Other fixpoint formats: Print quantized coefficients as strings
        else:
            self.ba_q = [
                self.Q[0].float2frmt(self.ba[0]),
                self.Q[1].float2frmt(a),
                self.Q[0].ovr_flag,
                self.Q[1].ovr_flag
                        ]
        # convert self.ba_q to list of arrays for easier handling
        self.ba_q = [np.asarray(self.ba_q[i]) for i in range(4)]
        self.ui.wdg_wq_coeffs_b.update_ovfl_cnt()
        self.ui.wdg_wq_coeffs_a.update_ovfl_cnt()

# ------------------------------------------------------------------------------
    def quant_coeffs_apply(self) -> None:
        """
        Triggered by pushing "Quantize button":

        - Store selected / all quantized coefficients in shadow array `self.ba`
        - Refresh table (for the case that anything weird happens during quantization)
        - Reset Overflow flags `self.ba_q[2]` and `self.ba_q[3]`
        - Save quantized `self.ba` to filter dict (in `_save_dict()`). This emits
          {'data_changed': 'input_coeffs'}
        """
        idx = qget_selected(self.tblCoeff)['idx']  # get all selected indices
        # returns e.g. [[0, 0], [0, 6]]
        if not idx:  # nothing selected, quantize all elements
            self.ba[0] = self.Q[0].frmt2float(self.ba_q[0])
            self.ba[1] = self.Q[1].frmt2float(self.ba_q[1])
            self.ba_q[2] = np.zeros(len(self.ba_q[0]))  # reset overflows
            self.ba_q[3] = np.zeros(len(self.ba_q[1]))  # reset overflows
            # idx = [[j, i] for i in range(self.num_rows) for j in range(self.num_cols)]
        else:
            try:
                idx.remove([1, 0])  # don't process '1' of recursive filters
            except ValueError:
                pass
            for i in idx:
                self.ba[i[0]][i[1]] = self.Q[i[0]].frmt2float(self.ba_q[i[0]][i[1]])
                self.ba_q[i[0] + 2][i[1]] = 0  # reset overflows

        self.refresh_table()
        qstyle_widget(self.ui.but_apply, 'changed')
        qstyle_widget(self.ui.but_undo, 'changed')

    # --------------------------------------------------------------------------
    def _filter_type(self, ftype: set) -> None:
        """
        Get / set 'FIR' and 'IIR' filter from cmb_filter_type combobox and set filter
            dict and table properties accordingly.

        When argument fil_type is not None, set the combobox accordingly.

        Reload from filter dict unless ftype is specified [does this make sense?!]
        """
        if ftype in {'FIR', 'IIR'}:
            ret = qset_cmb_box(self.ui.cmb_filter_type, ftype)
            if ret == -1:
                logger.warning("Unknown filter type %s", ftype)

        if self.ui.cmb_filter_type.currentText() == 'IIR':
            fb_set('ft', 'IIR')
            self.col = 2
            self.tblCoeff.setColumnCount(2)
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
        else:
            fb_set('ft', 'FIR')
            self.col = 1
            self.tblCoeff.setColumnCount(1)
            self.tblCoeff.setHorizontalHeaderLabels(["b"])
            self.ba[1] = np.zeros_like(self.ba[1])  # enforce FIR filter
            self.ba[1][0] = 1.

        self._equalize_ba_length()
        self.refresh_table()
        qstyle_widget(self.ui.but_apply, 'changed')
        qstyle_widget(self.ui.but_undo, 'changed')

# ------------------------------------------------------------------------------
    def _refresh_table_item(self, row: int, col: int) -> None:
        """
        Refresh the table item with the index `row, col` from `self.ba_q`
        and color it according to overflow conditions
        """
        item = self.tblCoeff.item(row, col)

        if item:  # does item exist?
            item.setText(str(self.ba_q[col][row]).strip('()'))
        else:  # no, construct it:
            item = QTableWidgetItem(str(self.ba_q[col][row]).strip('()'))
            self.tblCoeff.setItem(row, col, item)

        brush = QBrush(Qt.SolidPattern)
        brush.setColor(QColor(255, 255, 255, 0))  # transparent white

        if self.ba_q[col + 2][row] > 0:
            # Color item backgrounds with pos. overflows in red
            brush.setColor(QColor(100, 0, 0, 80))

        elif self.ba_q[col + 2][row] < 0:
            # Color item backgrounds with neg. overflows in blue
            brush.setColor(QColor(0, 0, 100, 80))

        item.setTextAlignment(Qt.AlignRight | Qt.AlignCenter)
        item.setBackground(brush)

    # --------------------------------------------------------------------------
    def refresh_table(self) -> None:
        """
        Update `self.ba_q` from `self.ba` (list with 2 one-dimensional numpy arrays),
        i.e. requantize displayed values (not `self.ba`) and overflow counters.

        Refresh the table from it. Data is displayed via `ItemDelegate.displayText()` in
        the number format set by `fil[0]['fx_base']`.

        - self.ba[0] -> b coefficients
        - self.ba[1] -> a coefficients

        The table dimensions are set according to the filter type set in
        `fil[0]['ft']` which is either 'FIR' or 'IIR' and by the number of
        rows in `self.ba`.

        Called at the end of nearly every method.
        """
        params['FMT_ba'] = int(self.ui.spn_digits.text())
        # update quantized coefficient display and overflow counter
        self.quant_coeffs_view()
        if np.ndim(self.ba) == 1 or fb_get('ft') == 'FIR':
            self.num_rows = len(self.ba[0])
        else:
            self.num_rows = max(len(self.ba[1]), len(self.ba[0]))

        # When format is floating point, disable all fixpoint options and widgets,
        # only the quantizer widget is enabled also for 'float32':
        is_float = not get_fx()
        self.ui.spn_digits.setVisible(is_float)  # select number of float digits
        self.ui.lbl_digits.setVisible(is_float)
        self.ui.cmb_fx_base.setVisible(not is_float)  # hide fx base combobox
        # hide quantization button:
        self.ui.but_quant.setVisible(qget_cmb_box(self.ui.cmb_qfrmt) != 'float64')

        # hide all q-settings for float
        self.ui.wdg_wq_coeffs_b.setVisible(not is_float)

        # check whether filter is FIR and only needs one column
        if fb_get('ft') == 'FIR':
            self.num_cols = 1
            self.tblCoeff.setColumnCount(1)
            self.tblCoeff.setHorizontalHeaderLabels(["b"])
            qset_cmb_box(self.ui.cmb_filter_type, 'FIR')
            self.ui.wdg_wq_coeffs_a.setVisible(False)  # always hide a coeffs for FIR
        else:
            self.num_cols = 2
            self.tblCoeff.setColumnCount(2)
            self.tblCoeff.setHorizontalHeaderLabels(["b", "a"])
            qset_cmb_box(self.ui.cmb_filter_type, 'IIR')
            # hide all q-settings for float:
            self.ui.wdg_wq_coeffs_a.setVisible(not is_float)

            self.ba[1][0] = 1.0  # restore a[0] = 1 of denominator polynome

        self.tblCoeff.setRowCount(self.num_rows)
        self.tblCoeff.setColumnCount(self.num_cols)
        # Create strings for index column (vertical header), starting with "0"
        idx_str = [str(n) for n in range(self.num_rows)]
        self.tblCoeff.setVerticalHeaderLabels(idx_str)
        # ----------------------------------
        self.tblCoeff.blockSignals(True)

        for col in range(self.num_cols):
            for row in range(self.num_rows):
                self._refresh_table_item(row, col)

        # make a[0] selectable but not editable
        if fb_get('ft') == 'IIR':
            item = self.tblCoeff.item(0, 1)
            item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            item.setFont(self.ui.bfont)

        self.tblCoeff.blockSignals(False)
        # ---------------------------------
        self.tblCoeff.resizeColumnsToContents()
        self.tblCoeff.resizeRowsToContents()
        self.tblCoeff.clearSelection()

    # --------------------------------------------------------------------------
    def load_dict(self) -> None:
        """
        - Copy filter dict array `fil[0]['ba']` to the coefficient list `self.ba`
        - Set quantization UI from dict, update quantized coeff. display / overflow
          counter
        - Update the display via `self.refresh_table()`.

        The filter dict is a "normal" 2D-numpy float array for the b and a coefficients
        while the coefficient list `self.ba` is a list of two float ndarrays to allow
        for different lengths of b and a subarrays while adding / deleting items.
        """
        # TODO: deepcopy can be removed once the setter / getters work properly)
        self.ba = copy.deepcopy(fb_get('ba'))

        # set quantization UI from dictionary, update quantized coeff. display and
        # overflow counter, and refresh table
        self.dict2ui()

        qstyle_widget(self.ui.but_apply, 'normal')
        qstyle_widget(self.ui.but_undo, 'normal')

    # --------------------------------------------------------------------------
    def export_table(self) -> None:
        """
        Export data from coefficient table `self.tblCoeff` to clipboard / file in
        CSV format.
        """
        text = qtable2csv(
            self.tblCoeff, self.ba, formatted=self.ui.but_format.isChecked())
        if self.ui.load_save_clipboard:
            # clipboard is selected as export target
            dirs.clipboard.setText(text)
        else:
            # pass csv formatted text, key for accessing data in ``*.npz`` file or
            # Matlab workspace (``*.mat``) and a title for the file export dialog
            export_fil_data(self, text, 'ba', title="Export Filter Coefficients",
                            formatted=self.ui.but_format.isChecked())

    # --------------------------------------------------------------------------
    def _import(self) -> None:
        """
        Import data from clipboard / file and copy it to `self.ba` as float / cmplx.

        Quantize data to `self.ba_q` and refresh table.

        TODO: More checks for swapped row <-> col, single values, wrong data type ...
        """
        formatted_import = self.ui.but_format.isChecked()

        # Get data as ndarray of str:

        if self.ui.load_save_clipboard:  # data from clipboard
            data_str = file2array(
                None, None, 'ba', from_clipboard=True,
                as_str = self.ui.but_format.isChecked())
        else:  # data from file
            file_name, file_type = select_file(self, title="Import Filter Coefficients",
                                               mode="r", file_types=('csv', 'mat', 'npy', 'npz'))
            if file_name is None:  # operation cancelled or error
                return
            # file types 'csv', 'mat', 'npy', 'npz'
            data_str = file2array(
                file_name, file_type, 'ba',
                from_clipboard=False,
                as_str = self.ui.but_format.isChecked())

        if data_str is None:  # file operation has been aborted or some other error
            logger.info("Data was not imported.")
            return

        if np.ndim(data_str) > 1:
            num_cols, num_rows = np.shape(data_str)
            orientation_horiz = num_cols > num_rows  # need to transpose data
            if min(num_cols, num_rows) > 2:
                logger.error("Data cannot be imported, its shape is %d x %d.", num_cols, num_rows)
                return
        elif np.ndim(data_str) == 1:
            num_rows = len(data_str)
            num_cols = 1
            orientation_horiz = False
        else:
            logger.error("Data cannot be imported, it is a single value or None.")
            return

        self.ba = [[], []]
        if orientation_horiz:
            for c in range(num_cols):
                if formatted_import:
                    self.ba[0].append(
                        self.Q[0].frmt2float(data_str[c][0]))
                    if num_rows > 1:
                        self.ba[1].append(
                            self.Q[1].frmt2float(data_str[c][1]))
                else:
                    self.ba[0].append(data_str[c][0])
                    if num_rows > 1:
                        self.ba[1].append(data_str[c][1])
            if num_rows > 1:
                self._filter_type(ftype='IIR')
            else:
                self.ba[1] = zeros_with_val(len(self.ba[0]))
                self._filter_type(ftype='FIR')
        else:
            if formatted_import:
                self.ba[0] =\
                    [self.Q[0].frmt2float(s) for s in data_str[0]]
            else:
                self.ba[0] = data_str[0]
            # IIR
            if num_cols > 1:
                if formatted_import:
                    self.ba[1] =\
                        [self.Q[1].frmt2float(s) for s in data_str[1]]
                else:
                    self.ba[1] = data_str[1]
                self._filter_type(ftype='IIR')
            else:
                self.ba[1] = zeros_with_val(len(self.ba[0]))
                self._filter_type(ftype='FIR')

        logger.warning("Type of self.ba[0]: %s", type(self.ba[0]))
        logger.warning("Contents of self.ba: %s", self.ba)

        self.ba[0] = np.asarray(self.ba[0])
        self.ba[1] = np.asarray(self.ba[1])

        self._equalize_ba_length()
        self.refresh_table()
        logger.info("Successfully imported data.")
        qstyle_widget(self.ui.but_apply, 'changed')
        qstyle_widget(self.ui.but_undo, 'changed')

    # --------------------------------------------------------------------------
    def dict2ui(self) -> None:
        """
        - update the UI from the dictionary
        - Update the fixpoint quant. object
        - Update the quantized coefficient view and the overflow counter
        - Refresh the table

        Triggered by:

        - `process_sig_rx()`: self.fx_specs_changed == True or
            dict_sig['fx_sim'] == 'specs_changed'
        - `self.qfrmt2dict()`
        - `self.fx_base2dict()`
        """
        # update ui
        qset_cmb_box(self.ui.cmb_qfrmt, fb_get('qfrmt'), data=True)
        if get_fx():  # fixpoint mode, update quantizer objects and widgets
            # qset_cmb_box(self.ui.cmb_qfrmt, fb_get('qfrmt'), data=True)
            self.ui.wdg_wq_coeffs_a.dict2ui(fb_get('fxq', 'QCA'))
            self.ui.wdg_wq_coeffs_b.dict2ui(fb_get('fxq', 'QCB'))

        # quantize coefficient view according to new settings and update table
        self.quant_coeffs_view()
        self.refresh_table()

    # ------------------------------------------------------------------------------
    def qfrmt2dict(self) -> None:
        """
        Read out the UI settings of  `self.ui.cmb_qfrmt` (triggering this method)
        and store it under the 'qfrmt' key if it is a fixpoint format.

        Refresh the table and update quantization widgets, finally emit a signal
        `{'fx_sim': 'specs_changed'}`.
        """
        fb_set('qfrmt', qget_cmb_box(self.ui.cmb_qfrmt))

        # update quant. widgets and table with the new `qfrmt` settings and propagate
        # change in fixpoint settings to other widgets
        self.dict2ui()
        self.emit({'fx_sim': 'specs_changed'})

    # ------------------------------------------------------------------------------
    def fx_base2dict(self) -> None:
        """
        Read out the UI settings of `self.ui.cmb_fx_base` (triggering this method)
        which specifies the fx number base (dec, bin, ...) for display
        and store it in `fil[0]['fx_base']`.

        Refresh the table and update quantization widgets. Don't emit a signal
        because this only influences the view not the data itself.
        """
        fb_set('fx_base', qget_cmb_box(self.ui.cmb_fx_base))

        # update quant. widgets and table with the new `fx_base` settings
        self.dict2ui()

    # ------------------------------------------------------------------------------
    def _save_dict(self) -> None:
        """
        Save the coefficient register `self.ba` to the filter dict as `fil[0]['ba']`.
        """
        fb_set('N', max(len(self.ba[0]), len(self.ba[1])) - 1)

        # Switch to manual filter order and 'Manual_IIR' resp. 'Manual_FIR' filter class
        fb_set('fo', 'man')
        if fb_get('ft') == 'IIR':
            fb_set('fc', 'Manual_IIR')
        else:
            fb_set('fc','Manual_FIR')

        # save, check and convert coeffs, check filter type
        try:
            fil_save(self.ba, 'ba', __name__)
        except (ValueError, TypeError) as e:
            # catch exception due to malformatted coefficients:
            logger.error("While saving the filter coefficients, "
                         "the following error occurred:\n%s", e)

        if __name__ == '__main__':
            self.load_dict()  # only needed for stand-alone test

        # Change filter type to "Manual" and update UI in Input_Specs() ...
        self.emit({'filt_changed': 'input_coeffs'})
        # ... and update filter data and widgets
        self.emit({'data_changed': 'filter_designed'})

        qstyle_widget(self.ui.but_apply, 'normal')
        qstyle_widget(self.ui.but_undo, 'normal')

    # ------------------------------------------------------------------------------
    def clear_table(self) -> None:
        """
        Clear self.ba: Initialize coeff for a poles and a zero @ origin,
        a = b = [1; 0].

        Refresh QTableWidget
        """
        self.ba = np.asarray(([1., 0.], [1., 0.]))
        self.refresh_table()
        qstyle_widget(self.ui.but_apply, 'changed')
        qstyle_widget(self.ui.but_undo, 'changed')

    # ------------------------------------------------------------------------------
    def _equalize_ba_length(self) -> None:
        """
        test and equalize if b and a subarray have different lengths and copy to
        `self.ba_q`:
        """
        try:
            a_len = len(self.ba[1])
        except IndexError:
            self.ba.append(np.array(1))
            a_len = 1

        D = len(self.ba[0]) - a_len

        if D > 0:  # b is longer than a
            self.ba[1] = np.append(self.ba[1], np.zeros(D))
            # self.quant_coeffs_view()
        elif D < 0:  # a is longer than b
            if fb_get('ft') == 'IIR':
                self.ba[0] = np.append(self.ba[0], np.zeros(-D))
            else:
                self.ba[1] = self.ba[1][:D]  # discard last D elements of a
        self.quant_coeffs_view()

    # ------------------------------------------------------------------------------
    def _delete_cells(self) -> None:
        """
        Delete all selected elements in self.ba by:
        - determining the indices of all selected cells in the P and Z arrays
        - deleting elements with those indices
        - equalizing the lengths of b and a array by appending the required
          number of zeros.
        When nothing is selected, delete the last row.
        Finally, refresh the table
        """
        sel = qget_selected(self.tblCoeff)['sel']  # get indices of all selected cells

        if not any(sel) and len(self.ba[0]) > 0:  # nothing selected, delete last row
            self.ba = np.delete(self.ba, -1, axis=1)
        elif np.all(sel[0] == sel[1]) or fb_get('ft') == 'FIR':
            # only complete rows selected or FIR -> delete row
            self.ba = np.delete(self.ba, sel[0], axis=1)
        else:
            # self.ba[0][sel[0]] = 0
            # self.ba[1][sel[1]] = 0
            self.ba[0] = np.delete(self.ba[0], sel[0])
            self.ba[1] = np.delete(self.ba[1], sel[1])

        # If length is less than 2, re-initialize the table: this ain't no filter!
        # `_clear_table() also refreshes the table and sets 'changed' attribute
        if len(self.ba[0]) < 2 and len(self.ba[1]) < 2:
            self.clear_table()
        else:
            # test and equalize if b and a array have different lengths:
            self._equalize_ba_length()
            self.refresh_table()
            qstyle_widget(self.ui.but_apply, 'changed')
            qstyle_widget(self.ui.but_undo, 'changed')

    # ------------------------------------------------------------------------------
    def _add_cells(self) -> None:
        """
        Add the number of selected rows to self.ba and fill new cells with
        zeros from the bottom. If nothing is selected, add one row at the bottom.
        Refresh QTableWidget.
        """
        # get indices of all selected cells
        sel = qget_selected(self.tblCoeff)['sel']

        # merge selections in both columns, remove duplicates and sort
        sel_01 = sorted(set(sel[0]).union(set(sel[1])))

        if not any(sel):  # nothing selected, append row of zeros after last row
            self.ba = np.insert(self.ba, len(self.ba[0]), 0, axis=1)
        # elif fb_get('ft') == 'IIR':
        else:
            self.ba = np.insert(self.ba, sel_01, 0, axis=1)
        # else:
        # insert 'sel' contiguous rows  before 'row':
        # self.ba[0] = np.insert(self.ba[0], row, np.zeros(sel))

        self._equalize_ba_length()
        self.refresh_table()

        # don't tag as 'changed' when only zeros have been appended to end of table
        if any(sel_01):
            qstyle_widget(self.ui.but_apply, 'changed')
            qstyle_widget(self.ui.but_undo, 'changed')

    # ------------------------------------------------------------------------------
    def _set_eps(self) -> None:
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        self.ui.eps = safe_eval(
            self.ui.led_eps.text(), return_type='float', sign='pos', alt_expr=self.ui.eps)
        self.ui.led_eps.setText(str(self.ui.eps))

    # ------------------------------------------------------------------------------
    def _set_coeffs_zero(self) -> None:
        """
        Set all coefficients = 0 in self.ba with a magnitude less than eps
        and refresh QTableWidget
        """
        self._set_eps()
        idx = qget_selected(self.tblCoeff)['idx']  # get all selected indices

        test_val = 0.  # value against which array is tested
        targ_val = 0.  # value which is set when condition is true
        changed = False

        if not idx:  # nothing selected, check whole table
            # When entry is close to zero (but not = 0), mark as "b_close"
            # and set all marked entries and the corresponding overflow flags = 0
            b_close = np.logical_and(
                np.isclose(self.ba[0], test_val, rtol=0, atol=self.ui.eps),
                (self.ba[0] != targ_val))
            if np.any(b_close):  # found at least one coeff where condition was true
                self.ba[0] = np.where(b_close, targ_val, self.ba[0])
                changed = True

            if fb_get('ft') == 'IIR':
                a_close = np.logical_and(
                    np.isclose(self.ba[1], test_val, rtol=0, atol=self.ui.eps),
                    (self.ba[1] != targ_val))
                if np.any(a_close):
                    self.ba[1] = np.where(a_close, targ_val, self.ba[1])
                    changed = True

        else:  # only check selected cells
            for i in idx:
                if np.logical_and(
                    np.isclose(self.ba[i[0]][i[1]], test_val, rtol=0, atol=self.ui.eps),
                        (self.ba[i[0]][i[1]] != targ_val)):
                    self.ba[i[0]][i[1]] = targ_val
                    changed = True
        if changed:
            qstyle_widget(self.ui.but_apply, 'changed')  # mark save button as changed
            qstyle_widget(self.ui.but_undo, 'changed')

        self.refresh_table()


# ------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.input_coeffs`
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    mainw = Input_Coeffs()
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
