# -*- coding: utf-8 -*-
"""
Created 2012 - 2017

@author: Christian Muenker

Library with common routines for Qt widgets
"""

from __future__ import division, print_function
import logging
logger = logging.getLogger(__name__)
import csv
import numpy as np

from .compat import Qt, QtCore, QFrame, QFont, QEvent, QSysInfo

#import pyfda.simpleeval as se



#------------------------------------------------------------------------------
def qstr(text):
    """
    Convert text (QVariant, QString, string) or numeric object to plain string.

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" e.g. in a QComboBox and converted back when
    retrieving. In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    Parameter:
    ----------
    
    text: QVariant, QString, string or numeric data type that can be converted
      to string
    
    Returns:
    --------
    
    The current `text` data as a string
    """
    if "QString" in str(type(text)):
        # Python 3: convert QString -> str
        string = str(text)
#    elif not isinstance(text, six.text_type):
    elif "QVariant" in str(type(text)):
        # Python 2: convert QVariant -> QString -> str
        string = str(text.toString())
    else:
        # `text` is numeric or of type str
        string = str(text)
    return string


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
def qset_cmb_box(cmb_box, string, data=False):
    """
    Set combobox to the index corresponding to `string` in a text field (data = False)
    or in a data field (data=True). When `string` is not found in the combobox entries,
     select the first entry. Signals are blocked during the update of the combobox.
     
    Returns: the index of the found entry
    """
    if data:
        idx = cmb_box.findData(str(string)) # find index for data = string
    else:
        idx = cmb_box.findText(str(string)) # find index for text = string    

    ret = idx

    if idx == -1: # data does not exist, use first entry instead
        idx = 0
        
    cmb_box.blockSignals(True)
    cmb_box.setCurrentIndex(idx) # set index
    cmb_box.blockSignals(False)
    
    return ret

#------------------------------------------------------------------------------
def qstyle_widget(widget, state):
    """
    Apply the "state" defined in pyfda_rc.py to the widget, e.g.:  
    Color the >> DESIGN FILTER << button according to the filter design state:
    
    - "normal": default, no color styling
    - "ok":  green, filter has been designed, everything ok
    - "changed": yellow, filter specs have been changed
    - "error" : red, an error has occurred during filter design
    - "failed" : orange, filter fails to meet target specs
    - "unused": grey
    """
    state = str(state)
    if state == 'u':
        state = "unused"
    elif state == 'a':
        state = "active"
    elif state == 'd':
        state = "disabled"
    widget.setProperty("state", state)
    #fb.design_filt_state = state
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()

#------------------------------------------------------------------------------
def qhline(widget):
    # http://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    # solution 
    """
    Create a horizontal line
    
    Parameters:
    
    frame: instance of QFrame - not needed?
    
    widget: widget containing the QFrame to be created
    """
    line = QFrame(widget)
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    return line
    
#------------------------------------------------------------------------------

def qget_selected(table, reverse=True):
    """
    Get selected cells in `table`and return a dictionary with the following keys:
    
    'idx': indices of selected cells as an unsorted list of tuples
    
    'sel': list of selected cells per column, by default sorted in reverse
    
    'cur':  current cell selection as a tuple
    """
    idx = []
    for _ in table.selectedItems():
        idx.append([_.column(), _.row(), ])

    sel = [0, 0]
    sel[0] = sorted([i[1] for i in idx if i[0] == 0], reverse = reverse)
    sel[1] = sorted([i[1] for i in idx if i[0] == 1], reverse = reverse)

    # use set comprehension to eliminate multiple identical entries
    # cols = sorted(list({i[0] for i in idx}))
    # rows = sorted(list({i[1] for i in idx}))
    cur = (table.currentColumn(), table.currentRow())
    # cur_idx_row = table.currentIndex().row()
    return {'idx':idx, 'sel':sel, 'cur':cur}# 'rows':rows 'cols':cols, }
    
#------------------------------------------------------------------------------
def qcopy_to_clipboard(table, var, target, tab = "\t", cr = None):
    """
    Copy table to clipboard as CSV list
    
    Parameters:
    -----------
    table : object
            Instance of QTableWidget
            
    var:    object
            Instance of the variable containing table data
            
    target: object
            Target where the data is being copied to. If the object is a QClipboard
            instance, copy the text there, otherwise simply return the text.
    
    tab : String (default: "\t")
          Tabulator character for separating columns
          
    cr : String (default: None)
            Linefeed character for separating rows. When nothing is selected,
            the character is selected depending on the operating system:
            Windows: Carriage return + line feed
            MacOS  : Carriage return
            *nix   : Line feed
    """
    if not cr:
        if hasattr(QSysInfo, "WindowsVersion"):
            print("Win!", QSysInfo.WindowsVersion)
            cr = "\r\n" # Windows: carriage return + line feed
        elif hasattr(QSysInfo, "MacintoshVersion"):
            print("Mac!", QSysInfo.MacintoshVersion)
            cr = "\r" # Mac: carriage return only
        else:
            print("*nix!")
            cr = "\n" # *nix: line feed only

    text = ""

    sel = qget_selected(table, reverse=False)['sel']   
    if not np.any(sel): # nothing selected -> copy everything raw from ba
        for r in range(table.rowCount()):
            #                text += qstr(self.tblCoeff.horizontalHeaderItem(r).text())
            for c in range(table.columnCount()):
                text += str(var[c][r])
                if c != table.columnCount():
                    text += tab
            if r != table.rowCount():
                text += cr
    else: # copy only selected cells in selected format
        tab = ", "
        for r in sel[0]:
            item = table.item(r,0)
            if item:
                if item.text() != "":
                    text += table.itemDelegate().text(item)
        text += cr
        for r in sel[1]:
            item = table.item(r,1)
            if item:
                if item.text() != "":
                    text += table.itemDelegate().text(item)
                    
    if "clipboard" in str(target.__class__.__name__).lower() :
        target.setText(text)
    else:
        return text
        
#------------------------------------------------------------------------------
def qcopy_from_clipboard(source):
    """
    Copy table to clipboard as CSV list
    
    Parameters:
    -----------
            
    source: object
            Source of the data, this should be a QClipboard instance.
            
            If source is not a QClipBoard instance, return an error.
    
    tab : String (default: "\t")
          Tabulator character for separating columns
          
    cr : String (default: None)
            Linefeed character for separating rows. When nothing is selected,
            the character is selected depending on the operating system:
            Windows: Carriage return + line feed
            MacOS  : Carriage return
            *nix   : Line feed
    """
    source_type = str(source.__class__.__name__)
    if "clipboard" in source_type.lower() :
        text = source.text()
        
        dialect = csv.Sniffer.sniff(text)
        print("header:",dialect.has_header)
        print("delimiter:", dialect.delimiter)
        print("terminator:", dialect.lineterminator)
        return source.text() # read from clipboard
    else:
        logger.error("Unknown object {0}, cannot copy data.".format(source_type))


#==============================================================================
#         else: # copy only selected cells in selected format
#             tab = ", "
#             for r in sel[0]:
#                 item = self.tblCoeff.item(r,0)
#                 if item:
#                     if item.text() != "":
#                         text += self.tblCoeff.itemDelegate().text(item)
#             text += cr
#             for r in sel[1]:
#                 item = self.tblCoeff.item(r,1)
#                 if item:
#                     if item.text() != "":
#                         text += self.tblCoeff.itemDelegate().text(item)
# 
#==============================================================================





if __name__=='__main__':
    pass
