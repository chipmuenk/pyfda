# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with various helper functions for Qt widgets
"""

from __future__ import division, print_function
import logging
logger = logging.getLogger(__name__)

from .pyfda_lib import qstr

from .compat import QFrame, QMessageBox

#------------------------------------------------------------------------------
def qget_cmb_box(cmb_box, data=True):
    """
    Get current itemData or Text of comboBox and convert it to string.

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" e.g. in a QComboBox and converted back when
    retrieving. In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    Returns:
    
    The current text or data of combobox as a string
    """
    if data:
        idx = cmb_box.currentIndex()
        cmb_data = cmb_box.itemData(idx)
        cmb_str = qstr(cmb_data) # convert QVariant, QString, string to plain string
    else:
        cmb_str = cmb_box.currentText()
  
    cmb_str = str(cmb_str)

    return cmb_str

#------------------------------------------------------------------------------
def qset_cmb_box(cmb_box, string, data=False, fireSignals=False):
    """
    Set combobox to the index corresponding to `string` in a text field (`data = False`)
    or in a data field (`data=True`). When `string` is not found in the combobox entries,
    select the first entry. Signals are blocked during the update of the combobox unless
    `fireSignals` is set `True`.

    Parameters
    ----------

    string: str
        The label in the text or data field to be selected. When the string is
        not found, select the first entry of the combo box.

    data: bool (default: False)
        Whether the string refers to the data or text fields of the combo box

    fireSignals: bool (default: True)
        When False, fire a signal if the index is changed (useful for GUI testing)

    Returns
    -------
        The index of the string. When the string was not found in the combo box,
        return index -1.
    """
    if data:
        idx = cmb_box.findData(str(string)) # find index for data = string
    else:
        idx = cmb_box.findText(str(string)) # find index for text = string    

    ret = idx

    if idx == -1: # data does not exist, use first entry instead
        idx = 0
        
    cmb_box.blockSignals(not fireSignals)
    cmb_box.setCurrentIndex(idx) # set index
    cmb_box.blockSignals(False)
    
    return ret

#------------------------------------------------------------------------------
def qstyle_widget(widget, state):
    """
    Apply the "state" defined in pyfda_rc.py to the widget, e.g.:  
    Color the >> DESIGN FILTER << button according to the filter design state.
    
    - "normal": default, no color styling
    - "ok":  green, filter has been designed, everything ok
    - "changed": yellow, filter specs have been changed
    - "error" : red, an error has occurred during filter design
    - "failed" : orange, filter fails to meet target specs
    - "u" or "unused": grey text color
    - "d" or "disabled": background color darkgrey
    - "a" or "active": no special style defined
    """
    state = str(state)
    if state == 'u':
        state = "unused"
        # *[state="unused"], *[state="u"]{background-color:white; color:darkgrey}
    elif state == 'a':
        state = "active"
    elif state == 'd':
        state = "disabled"
        # QLineEdit:disabled{background-color:darkgrey;}
    widget.setProperty("state", state)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()

#------------------------------------------------------------------------------
def qhline(widget):
    # http://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    # solution 
    """
    Create a horizontal line
    
    Parameters
    ----------
    
    widget: widget containing the QFrame to be created
    """
    line = QFrame(widget)
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line
    
#------------------------------------------------------------------------------
def qget_selected(table, select_all=False, reverse=True):
    """
    Get selected cells in ``table`` and return a dictionary with the following keys:
    
    'idx': indices of selected cells as an unsorted list of tuples
    
    'sel': list of selected cells per column, by default sorted in reverse
    
    'cur':  current cell selection as a tuple

    Parameters
    ----------

    select_all : bool
        select all table items and create a list when True

    reverse : bool
        return selected fields upside down when True
    """
    if select_all:
        table.selectAll()

    idx = []
    for _ in table.selectedItems():
        idx.append([_.column(), _.row(), ])

    sel = [0, 0]
    sel[0] = sorted([i[1] for i in idx if i[0] == 0], reverse = reverse)
    sel[1] = sorted([i[1] for i in idx if i[0] == 1], reverse = reverse)

    if select_all:
        table.clearSelection()

    # use set comprehension to eliminate multiple identical entries
    # cols = sorted(list({i[0] for i in idx}))
    # rows = sorted(list({i[1] for i in idx}))
    cur = (table.currentColumn(), table.currentRow())
    # cur_idx_row = table.currentIndex().row()
    return {'idx':idx, 'sel':sel, 'cur':cur}# 'rows':rows 'cols':cols, }

#------------------------------------------------------------------------------
def qfilter_warning(self, N, fil_class):
    """
    Pop-up a warning box for very large filter orders
    """
    reply = QMessageBox.warning(self, 'Warning',
        ("<span><i><b>N = {0}</b></i> &nbsp; is a rather high order for<br />"
         "an {1} filter and may cause large <br />"
         "numerical errors and compute times.<br />"
         "Continue?</span>".format(N, fil_class)),
         QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        return True
    else:
        return False

    
#==============================================================================

if __name__=='__main__':
    pass
