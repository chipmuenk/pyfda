# -*- coding: utf-8 -*-
"""
Created 2012 - 2017

@author: Christian Muenker

Library with common routines for Qt widgets
"""
# TODO: import data from files doesn't update FIR / IIR and data changed
# TODO: export data?
# TODO: export COE, Actel
from __future__ import division, print_function
import logging
logger = logging.getLogger(__name__)

import os
import csv
import io
import numpy as np
from scipy.io import loadmat, savemat
from .pyfda_lib import PY3, safe_eval, extract_file_ext
from .pyfda_rc import params
import pyfda.pyfda_rc as rc
import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

from .compat import (QFrame, QLabel, QComboBox, QDialog, QPushButton, QRadioButton,
                     QFD, QHBoxLayout, QVBoxLayout)
#------------------------------------------------------------------------------
class CSV_option_box(QDialog):

    def __init__(self, parent):
        super(CSV_option_box, self).__init__(parent)
        self._init_UI()

    def _init_UI(self):
        """ initialize the User Interface """
        self.setWindowTitle("CSV Options")
        lblDelimiter = QLabel("CSV-Delimiter:", self)
        delim = [('Auto','auto'), ('< , >',','), ('< ; >', ';'), ('<TAB>', '\t'), ('<SPACE>', ' '), ('< | >', '|')]
        self.cmbDelimiter = QComboBox(self)
        for d in delim:
            self.cmbDelimiter.addItem(d[0],d[1])
        self.cmbDelimiter.setToolTip("Delimiter between data fields.")

        lblTerminator = QLabel("Line Terminator:", self)
        terminator = [('Auto','auto'), ('CRLF (Win)', '\r\n'), ('CR (Mac)', '\r'), ('LF (Unix)', '\n')]
        self.cmbLineTerminator = QComboBox(self)
        self.cmbLineTerminator.setToolTip("<span>Terminator at the end of a data row."
                " (depending on the operating system).")
        for t in terminator:
            self.cmbLineTerminator.addItem(t[0], t[1])

        butClose = QPushButton(self)
        butClose.setText("Close")
        layHDelimiter = QHBoxLayout()
        layHDelimiter.addWidget(lblDelimiter)
        layHDelimiter.addWidget(self.cmbDelimiter)

        layHLineTerminator = QHBoxLayout()
        layHLineTerminator.addWidget(lblTerminator)
        layHLineTerminator.addWidget(self.cmbLineTerminator)

        lblOrientation = QLabel("Table orientation", self)
        orientation = [('Auto/Vert.', 'auto'), ('Vertical', 'vert'), ('Horizontal', 'horiz')]
        self.cmbOrientation = QComboBox(self)
        self.cmbOrientation.setToolTip("<span>Select orientation of table.</span>")
        for o in orientation:
            self.cmbOrientation.addItem(o[0], o[1])

        layHOrientation = QHBoxLayout()
        layHOrientation.addWidget(lblOrientation)
        layHOrientation.addWidget(self.cmbOrientation)

        lblHeader = QLabel("Enable header", self)
        header = [('Auto', 'auto'), ('On', 'on'), ('Off', 'off')]
        self.cmbHeader = QComboBox(self)
        self.cmbHeader.setToolTip("First row is a header.")
        for h in header:
            self.cmbHeader.addItem(h[0], h[1])
        layHHeader = QHBoxLayout()
        layHHeader.addWidget(lblHeader)
        layHHeader.addWidget(self.cmbHeader)
        
        self.radClipboard = QRadioButton("Clipboard", self)
        self.radFile = QRadioButton("File", self)
        self.radClipboard.setChecked(True)
        layHClipFile = QHBoxLayout()
        layHClipFile.addWidget(self.radClipboard)
        layHClipFile.addWidget(self.radFile)

        layVMain = QVBoxLayout()
        # layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addLayout(layHDelimiter)
        layVMain.addLayout(layHLineTerminator)
        layVMain.addLayout(layHOrientation)
        layVMain.addLayout(layHHeader)
        layVMain.addLayout(layHClipFile)
        layVMain.addWidget(butClose)
        layVMain.setContentsMargins(*params['wdg_margins'])
#        layVMain.addStretch(1)
        self.setLayout(layVMain)

        self._load_settings()

        # ============== Signals & Slots ================================
        butClose.clicked.connect(self.close)
        self.cmbOrientation.currentIndexChanged.connect(self._store_settings)
        self.cmbDelimiter.currentIndexChanged.connect(self._store_settings)
        self.cmbLineTerminator.currentIndexChanged.connect(self._store_settings)
        self.cmbHeader.currentIndexChanged.connect(self._store_settings)
        self.radClipboard.clicked.connect(self._store_settings)
        self.radFile.clicked.connect(self._store_settings)


    def _store_settings(self):
        try:
            params['CSV']['orientation'] =  qget_cmb_box(self.cmbOrientation, data=True)
            params['CSV']['delimiter'] = qget_cmb_box(self.cmbDelimiter, data=True)
            params['CSV']['lineterminator'] = qget_cmb_box(self.cmbLineTerminator, data=True)
            params['CSV']['header'] = qget_cmb_box(self.cmbHeader, data=True)
            params['CSV']['clipboard'] = self.radClipboard.isChecked()

        except KeyError as e:
            logger.error(e)

    def _load_settings(self):
        """
        Load settings of all widgets from `pyfda_rc`.
        """
        try:
            qset_cmb_box(self.cmbDelimiter, params['CSV']['delimiter'], data=True)
            qset_cmb_box(self.cmbLineTerminator, params['CSV']['lineterminator'], data=True)
            qset_cmb_box(self.cmbHeader, params['CSV']['header'], data=True)
            qset_cmb_box(self.cmbOrientation, params['CSV']['orientation'], data=True)
            self.radClipboard.setChecked(params['CSV']['clipboard'])
            self.radFile.setChecked(not params['CSV']['clipboard'])

        except KeyError as e:
            logger.error(e)

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
    
    The current `text` data as a unicode (utf8) string
    """
    text_type = str(type(text)).lower()

    if "qstring" in text_type:
        # Python 3: convert QString -> str
        #string = str(text)
        # Convert QString -> Utf8
        string = text.toUtf8()
#    elif not isinstance(text, six.text_type):
    elif "qvariant" in text_type:
        # Python 2: convert QVariant -> QString
        string = text.toString()
        #string = QVariant(text).toString()
        #string = str(text.toString())
    elif "unicode" in text_type:
        return text
    else:
        # `text` is numeric or of type str
        string = str(text)
        
    if not PY3:
        return unicode(string, 'utf8')
    else:
        return str(string) # convert QString -> str


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

    Parameters:
    -----------

    string: string
        The label in the text or data field to be selected. When the string is
        not found, select the first entry of the combo box.

    data: Boolean (default: False)
        Whether the string refers to the data or text fields of the combo box

    fireSignals: Boolean (default: True)
        When False, fire a signal if the index is changed (useful for GUI testing)

    Returns:
    --------
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

def qget_selected(table, select_all=False, reverse=True):
    """
    Get selected cells in `table`and return a dictionary with the following keys:
    
    'idx': indices of selected cells as an unsorted list of tuples
    
    'sel': list of selected cells per column, by default sorted in reverse
    
    'cur':  current cell selection as a tuple

    Flags:

    'select_all' : select all table items and create a list

    'reverse' : return selected fields upside down
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
def qtable2text(table, data, parent, key, frmt='float', comment=""):
    """
    Transform table to CSV formatted text and copy to clipboard or file
    
    Parameters:
    -----------
    table : object
            Instance of QTableWidget
            
    data:   object
            Instance of the numpy variable containing table data
            
    parent: parent class
            Used to get the clipboard instance from the parent class (if copying 
            to clipboard) or to construct a QFileDialog instance (if copying to a file)
            
    key:  string    
            Key for accessing data in *.npz file or Matlab workspace (*.mat)
            
    frmt: string
           when frmt='float', copy data from model, otherwise from the view 
           using the tables itemDelegate() methods.
           
    comment: string
            comment string indicating the type of data to be copied (e.g. 
            "filter coefficients ")


    The following keys from the dict pyfda_lib.params['CSV'] are evaluated:
         
    'delimiter' : string (default: <tab>)
          Character for separating columns
 
    'lineterminator' : string (default: As used by the operating system)
            Character for terminating rows. By default,
            the character is selected depending on the operating system:
            Windows: Carriage return + line feed
            MacOS  : Carriage return
            *nix   : Line feed

    'orientation' : string
            This string determines with which the orientation the table is read.

    'header': string (default: 'auto')
            When `header='on'`, treat first row as a header that will be discarded.

    'clipboard': Boolean (default: True)
            When 'clipboard' = True, copy data to clipboard, else use a file

    """
#------------------------------------------------------------------------------
    def export_coeffs(self, data, key, comment=""):
        """
        Export filter coefficients in various formats - see also
        Summerfield p. 192 ff
        
        Parameters
        ----------
        
        data: CSV data
            
        key: string
            Key for accessing data in *.npz file or Matlab workspace (*.mat)
            When key == 'ba', exporting to Xilinx Coeff format is enabled.
        """
        dlg = QFD(self)

        file_filters = ("CSV (*.csv);;Matlab-Workspace (*.mat)"
            ";;Binary Numpy Array (*.npy);;Zipped Binary Numpy Array (*.npz)")

        if fb.fil[0]['ft'] == 'FIR':
            file_filters += ";;Xilinx coefficient format (*.coe)"

#        # Add further file types when modules are available:
#        if XLWT:
#            file_filters += ";;Excel Worksheet (.xls)"
#        if XLSX:
#            file_filters += ";;Excel 2007 Worksheet (.xlsx)"

        # return selected file name (with or without extension) and filter (Linux: full text)
        file_name, file_type = dlg.getSaveFileName_(
                caption = "Export filter coefficients as",
                directory = rc.save_dir, filter = file_filters)
        file_name = str(file_name) # QString -> str needed for Python 2

        for t in extract_file_ext(file_filters): # extract the list of file extensions
            if t in str(file_type):
                file_type = t

        if file_name != '': # cancelled file operation returns empty string
            # strip extension from returned file name (if any) + append file type:
            file_name = os.path.splitext(file_name)[0] +  file_type

#            ba = fb.fil[0]['ba']
            file_type_err = False
            try:
                if file_type == '.coe': # text / string format
                    with io.open(file_name, 'w', encoding="utf8") as f:
                        self.save_file_coe(f)
                else: # binary format
                    with io.open(file_name, 'wb') as f:
                        if file_type == '.mat':
                            savemat(f, mdict={key:data})
                        elif file_type == '.csv':
                            np.savetxt(f, data, delimiter = ', ')
                            # newline='\n', header='', footer='', comments='# ', fmt='%.18e'
                        elif file_type == '.npy':
                            # can only store one array in the file:
                            np.save(f, data)
                        elif file_type == '.npz':
                            # would be possible to store multiple arrays in the file
                            np.savez(f, key = data)
                        elif file_type == '.xls':
                            # see
                            # http://www.dev-explorer.com/articles/excel-spreadsheets-and-python
                            # https://github.com/python-excel/xlwt/blob/master/xlwt/examples/num_formats.py
                            # http://reliablybroken.com/b/2011/07/styling-your-excel-data-with-xlwt/
                            workbook = xlwt.Workbook(encoding="utf-8")
                            worksheet = workbook.add_sheet("Python Sheet 1")
                            bold = xlwt.easyxf('font: bold 1')
                            worksheet.write(0, 0, 'b', bold)
                            worksheet.write(0, 1, 'a', bold)
                            for col in range(2):
                                for row in range(np.shape(data)[1]):
                                    worksheet.write(row+1, col, data[col][row]) # vertical
                            workbook.save(f)

                        elif file_type == '.xlsx':
                            # from https://pypi.python.org/pypi/XlsxWriter
                            # Create an new Excel file and add a worksheet.
                            workbook = xlsx.Workbook(f)
                            worksheet = workbook.add_worksheet()
                            # Widen the first column to make the text clearer.
                            worksheet.set_column('A:A', 20)
                            # Add a bold format to use to highlight cells.
                            bold = workbook.add_format({'bold': True})
                            # Write labels with formatting.
                            worksheet.write('A1', 'b', bold)
                            worksheet.write('B1', 'a', bold)

                            # Write some numbers, with row/column notation.
                            for col in range(2):
                                for row in range(np.shape(data)[1]):
                                    worksheet.write(row+1, col, data[col][row]) # vertical
                #                    worksheet.write(row, col, coeffs[col][row]) # horizontal


                            # Insert an image - useful for documentation export ?!.
                #            worksheet.insert_image('B5', 'logo.png')

                            workbook.close()

                        else:
                            logger.error('Unknown file type "%s"', file_type)
                            file_type_err = True

                        if not file_type_err:
                            logger.info('Filter saved as "%s"', file_name)
                            rc.save_dir = os.path.dirname(file_name) # save new dir

            except IOError as e:
                logger.error('Failed saving "%s"!\n%s\n', file_name, e)


            # Download the Simple ods py module:
            # http://simple-odspy.sourceforge.net/
            # http://codextechnicanum.blogspot.de/2014/02/write-ods-for-libreoffice-calc-from_1.html

            #------------------------------------------------------------------------------

    text = ""
    if params['CSV']['header'] in {'auto', 'on'}:
        use_header = True
    elif params['CSV']['header'] == 'off':
        use_header = False
    else:
        logger.error("Unknown key '{0}' for params['CSV']['header']"
                                        .format(params['CSV']['header']))

    if params['CSV']['orientation'] in {'auto', 'vert'}:
        orientation_horiz = False
    elif params['CSV']['orientation'] == 'horiz':
        orientation_horiz = True
    else:
        logger.error("Unknown key '{0}' for params['CSV']['orientation']"
                                        .format(params['CSV']['orientation']))

    delim = params['CSV']['delimiter']
    if delim == 'auto': # 'auto' doesn't make sense when exporting
        delim = ","
    cr = params['CSV']['lineterminator']

    num_cols = table.columnCount()
    num_rows = table.rowCount()

    sel = qget_selected(table, reverse=False)['sel']

    #============================================================================
    # Nothing selected, but cell format is non-float: 
    # -> select whole table, copy all cells further down below:
    #============================================================================
    if not np.any(sel) and frmt != 'float':
        sel = qget_selected(table, reverse=False, select_all = True)['sel']

    #============================================================================
    # Nothing selected, copy complete table from the model (data) in float format:
    #============================================================================
    if not np.any(sel): 
        if orientation_horiz: # rows are horizontal
            for c in range(num_cols):
                if use_header: # add the table header
                    text += table.horizontalHeaderItem(c).text() + delim
                for r in range(num_rows):
                    text += str(safe_eval(data[c][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr
            text = text.rstrip(cr) # delete last CR
        else:  # rows are vertical
            if use_header: # add the table header
                for c in range(num_cols):
                    text += table.horizontalHeaderItem(c).text() + delim
                text = text.rstrip(delim) + cr
            for r in range(num_rows):
                for c in range(num_cols):
                    text += str(safe_eval(data[c][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr
            text = text.rstrip(cr) # delete CR after last row

    #=======================================================================
    # Copy only selected cells in displayed format:
    #=======================================================================
    else:
        if orientation_horiz: # horizontal orientation, one or two rows
            if use_header: # add the table header
                text += table.horizontalHeaderItem(0).text() + delim
            if sel[0]:
                for r in sel[0]:
                    item = table.item(r,0)
                    if item  and item.text() != "":
                            text += table.itemDelegate().text(item).lstrip(" ") + delim
                text = text.rstrip(delim) # remove last tab delimiter again

            if sel[1]: # returns False for []
                text += cr # add a CRLF when there are two columns
                if use_header: # add the table header
                    text += table.horizontalHeaderItem(1).text() + delim
                for r in sel[1]:
                    item = table.item(r,1)
                    if item and item.text() != "":
                            text += table.itemDelegate().text(item) + delim
                text = text.rstrip(delim) # remove last tab delimiter again
        else: # vertical orientation, one or two columns
            sel_c = []
            if sel[0]:
                sel_c.append(0)
            if sel[1]:
                sel_c.append(1)

            if use_header:
                for c in sel_c:
                    text += table.horizontalHeaderItem(c).text() + delim
                    # cr is added further below
                text.rstrip(delim)
                
            for r in range(num_rows): # iterate over whole table
                for c in sel_c:
                    if r in sel[c]: # selected item?
                        item = table.item(r,c)
                        print(c,r)
                        if item and item.text() != "":
                            text += table.itemDelegate().text(item).lstrip(" ") + delim
                text = text.rstrip(delim) + cr
            text.rstrip(cr)

    if params['CSV']['clipboard']:
#        if "clipboard" in str(target.__class__.__name__).lower():
#            target.setText(text)
        if hasattr(parent, 'clipboard'):
            parent.clipboard.setText(text)
        else:
            logger.error("No clipboard instance defined!")
    else:
        export_coeffs(parent, text, key, comment=comment)

    # numpy.loadtxt  textfile -> array
    # numpy.savetxt array -> textfile
    # numpy.genfromtxt textfile -> array (with missing values)
    # numpy.recfromcsv
        
#==============================================================================
# http://stackoverflow.com/questions/6081008/dump-a-numpy-array-into-a-csv-file#6081043
#     # Write an example CSV file with headers on first line
#     with open('example.csv', 'w') as fp:
#         fp.write('''\
#     col1,col2,col3
#     1,100.1,string1
#     2,222.2,second string
#     ''')
#     
#     # Read it as a Numpy record array
#     ar = np.recfromcsv('example.csv')
#     print(repr(ar))
#     # rec.array([(1, 100.1, 'string1'), (2, 222.2, 'second string')], 
#     #           dtype=[('col1', '<i4'), ('col2', '<f8'), ('col3', 'S13')])
#     
#     # Write as a CSV file with headers on first line
#     with open('out.csv', 'w') as fp:
#         fp.write(','.join(ar.dtype.names) + '\n')
#         np.savetxt(fp, ar, '%s', ',')
#     
#     # Note that this example does not consider strings with commas, which would require quotes.
#         
#==============================================================================

#==============================================================================
#     # Here 'a' is the name of numpy array and 'file' is the variable to write in a file.
#     ##if you want to write in column:
# 
#     for x in np.nditer(a.T, order='C'): 
#             file.write(str(x))
#             file.write("\n")
# 
#     ## If you want to write in row: ## 
# 
#     writer= csv.writer(file, delimiter=',')
#     for x in np.nditer(a.T, order='C'): 
#             row.append(str(x))
#     writer.writerow(row)
# 
#==============================================================================
        
        
#------------------------------------------------------------------------------
def qtext2table(parent, key, comment = ""):
    """
    Copy data from clipboard or file to table

    Parameters:
    -----------

    parent: object
            parent instance, having a QClipboard and / or a QFileDialog instance.
            
    key: string
            Key for accessing data in *.npz file or Matlab workspace (*.mat)
    
    comment: string
            comment string stating the type of data to be copied (e.g. 
            "filter coefficients ")

    The following keys from the dict pyfda_lib.params['CSV'] are evaluated:
                
    'delimiter' : string (default: <tab>)
          Character for separating columns
          
    'lineterminator' : string (default: As used by the operating system)
            Character for terminating rows. By default,
            the character is selected depending on the operating system:
            Windows: Carriage return + line feed
            MacOS  : Carriage return
            *nix   : Line feed
            
    'orientation' : string
            This string determines with which the orientation the table is read.
            
    'header': string (default: 'auto')
            When `header='on'`, treat first row as a header that will be discarded.
            
    'clipboard': Boolean (default: True)
            When 'clipboard' = True, copy data from clipboard, else use a file

    Parameters that are 'auto', will be guessed by csv.Sniffer().

    Returns:
    --------

    numpy array of strings
                containing table data
    """

    if params['CSV']['clipboard']: # data from clipboard
        if not hasattr(parent, 'clipboard'):
            logger.error("No clipboard instance defined!")
            return None
        else:
            if PY3:
                text = parent.clipboard.text()
            else:
                text = unicode(parent.clipboard.text()) # Py 2 needs unicode here (why?)

            logger.info("Importing:\n{0}\n{1}".format(np.shape(text), text))

            return csv2text(io.StringIO(text)) # pass handle to text

    else: # data from file
        f_data = import_coeffs(parent, key, comment)
        return f_data



def csv2text(f):
    """
    Convert comma-separated values, passed either as file object or text object
    to numpy array, taking into accout the settings of the CSV dict.
    
    Returns
    -------
    numpy.array
    """
    #------------------------------------------------------------------------------
    # Get CSV parameter settings
    #------------------------------------------------------------------------------
    CSV_dict = params['CSV']
    try:
        header = CSV_dict['header'].lower()       
        if header in {'auto', 'on', 'off'}:
            pass
        else:
            header = 'auto'
            logger.error("Unknown key '{0}' for CSV_dict['header'], using {1} instead."
                                            .format(CSV_dict['header']), header)

        orientation_horiz = CSV_dict['orientation'].lower()
        if orientation_horiz in {'auto', 'vert', 'horiz'}:
            pass
        else:
            orientation_horiz = 'vert'
            logger.error("Unknown key '{0}' for CSV_dict['orientation'], using {1} instead."
                                        .format(CSV_dict['orientation']), orientation_horiz)

        tab = CSV_dict['delimiter'].lower()
        cr = CSV_dict['lineterminator'].lower()

    except KeyError as e:
        logger.error(e)

    try:
        if header == 'auto' or tab == 'auto' or cr == 'auto':
        # test the first line for delimiters (of the given selection)
            dialect = csv.Sniffer().sniff(f.readline(), delimiters=['\t',';',',', '|', ' ']) 
            f.seek(0)                               # and reset the file pointer
        else:
            dialect = csv.get_dialect('excel-tab') # fall back, alternatives: 'excel', 'unix'

        if header == "auto":                                  
            use_header = csv.Sniffer().has_header(f.read(1000)) # True when header detected
            f.seek(0)

    except csv.Error as e:
        logger.error("Error during CSV analysis:\n{0}".format(e)) 
        dialect = csv.get_dialect('excel-tab') # fall back
        use_header = False

    if header == 'on':
        use_header = True
    if header == 'off':
        use_header = False
    # case 'auto' has been treated above

    delimiter = dialect.delimiter
    lineterminator = dialect.lineterminator
    quotechar = dialect.quotechar

    if tab != 'auto':
        delimiter = str(tab)
        
    if cr != 'auto':
        lineterminator = str(cr)
        
    logger.info("using delimiter {0}, terminator {1} and quotechar {2}"\
                .format(repr(delimiter), repr(lineterminator), repr(quotechar))) 
    logger.info("using header '{0}'".format(use_header))
    logger.info("Type of passed text is '{0}'".format(type(f)))

    data_iter = csv.reader(f, dialect=dialect, delimiter=delimiter, lineterminator=lineterminator) # returns an iterator
#    except:
#        data_iter = iter(f) # convert to iterator
        
    if use_header:
        logger.info("Headers:\n{0}".format(next(data_iter, None))) # py3 and py2 
    
    data_list = []
    try:
        for row in data_iter:
            logger.info("{0}".format(row))
            data_list.append(row)
    except csv.Error as e:
        logger.error("Error during CSV reading:\n{0}".format(e))

    try:
        logger.info("Type of data list: {0}".format(type(data_list)))
        data_arr = np.array(data_list)
        cols, rows = np.shape(data_arr)
        logger.info("cols = {0}, rows = {1}, data_arr = {2}\n".format(cols, rows, data_arr))
        if params['CSV']['orientation'] == 'vert':
            logger.info("{0}".format(data_arr.T))
            return data_arr.T
        else:
            logger.info("{0}".format(data_arr))
            return data_arr
            
    except (TypeError, ValueError) as e:
        logger.error("{0}\n{1}".format(e, data_list))
        return None

#------------------------------------------------------------------------------
def import_coeffs(parent, key, comment):
    """
    Import filter coefficients from a file

    Parameters
    ----------
    parent: handle to calling instance

    key: string
        Key for accessing data in *.npz file or Matlab workspace (*.mat)

    comment: string
        comment string stating the type of data to be copied (e.g.
        "filter coefficients ") for user message while opening file

    Returns
    -------
    numpy array

    """
    file_filters = ("Matlab-Workspace (*.mat);;Binary Numpy Array (*.npy);;"
    "Zipped Binary Numpy Array(*.npz);;Comma / Tab Separated Values (*.csv)")
    dlg = QFD(parent)
    file_name, file_type = dlg.getOpenFileName_(
            caption = "Import "+ comment + "file",
            directory = rc.save_dir, filter = file_filters)
    file_name = str(file_name) # QString -> str

    for t in extract_file_ext(file_filters): # extract the list of file extensions
        if t in str(file_type):
            file_type = t

    if file_name != '': # cancelled file operation returns empty string

        # strip extension from returned file name (if any) + append file type:
        file_name = os.path.splitext(file_name)[0] + file_type

        file_type_err = False
        try:
            if file_type == '.csv':
                with io.open(file_name, 'r') as f:
                    data_arr = csv2text(f)
            else:
                with io.open(file_name, 'rb') as f:
                    if file_type == '.mat':
                        data_arr = loadmat(f)[key]
                    elif file_type == '.npy':
                        data_arr = np.load(f)
                        # contains only one array
                    elif file_type == '.npz':
                        data_arr = np.load(f)[key]
                        # pick the array `key` from the dict
                    else:
                        logger.error('Unknown file type "{0}"'.format(file_type))
                        file_type_err = True

            if not file_type_err:
                logger.info('Successfully loaded \n"{0}"'.format(file_name))
                rc.save_dir = os.path.dirname(file_name)
                return data_arr # returns numpy array

        except IOError as e:
            logger.error("Failed loading {0}!\n{1}".format(file_name, e))
            return None

#==============================================================================

if __name__=='__main__':
    pass
