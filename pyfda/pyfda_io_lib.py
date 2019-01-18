# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with classes and functions for file and text IO
"""
# TODO: import data from files doesn't update FIR / IIR and data changed

from __future__ import division, print_function
import logging
logger = logging.getLogger(__name__)

import os, re, io
import csv
import datetime

import numpy as np
from scipy.io import loadmat, savemat

from .pyfda_lib import unicode_23, safe_eval
from .pyfda_qt_lib import qget_selected, qget_cmb_box, qset_cmb_box
import pyfda.pyfda_fix_lib as fix_lib
from .pyfda_rc import params
import pyfda.pyfda_dirs as dirs
import pyfda.filterbroker as fb # importing filterbroker initializes all its globals

from .compat import (QLabel, QComboBox, QDialog, QPushButton, QRadioButton,
                     QFD, QHBoxLayout, QVBoxLayout)
#------------------------------------------------------------------------------
class CSV_option_box(QDialog):
    """
    Create a pop-up widget for setting CSV options. This is needed when storing /
    reading Comma-Separated Value (CSV) files containing coefficients or poles 
    and zeros.
    """

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
        """
        Store settings of CSV options widget in ``pyfda_rc.params``.
        """

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
        Load settings of CSV options widget from ``pyfda_rc.params``.
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
def prune_file_ext(file_type):
    """
    Prune file extension, e.g. '(\*.txt)' from file type description returned
    by QFileDialog. This is achieved with the regular expression

    .. code::

        return = re.sub('\([^\)]+\)', '', file_type)

    Parameters
    ----------
    file_type : str

    Returns
    -------
    str
        The pruned file description

    Notes
    -----
    Syntax of python regex: ``re.sub(pattern, replacement, string)``

    This returns the string obtained by replacing the leftmost non-overlapping
    occurrences of ``pattern`` in ``string`` by ``replacement``.

    - '.' means any character

    - '+' means one or more

    - '[^a]' means except for 'a'

    - '([^)]+)' : match '(', gobble up all characters except ')' till ')'

    - '(' must be escaped as '\\\('

    """



    return re.sub('\([^\)]+\)', '', file_type)

#------------------------------------------------------------------------------
def extract_file_ext(file_type):
    """
    Extract list with file extension(s), e.g. '.vhd' from type description
    (e.g. 'VHDL (\*.vhd)') returned by QFileDialog
    """

    ext_list = re.findall('\([^\)]+\)', file_type) # extract '(*.txt)'
    return [t.strip('(*)') for t in ext_list] # remove '(*)'

#------------------------------------------------------------------------------
def qtable2text(table, data, parent, fkey, frmt='float', comment=""):
    """
    Transform table to CSV formatted text and copy to clipboard or file

    Parameters
    -----------
    table : object
            Instance of QTableWidget

    data:   object
            Instance of the numpy variable containing table data

    parent: object
            Used to get the clipboard instance from the parent instance (if copying
            to clipboard) or to construct a QFileDialog instance (if copying to a file)

    fkey:  str
            Key for accessing data in ``*.npz`` file or Matlab workspace (``*.mat``)

    frmt: str
           when ``frmt=='float'``, copy data from model, otherwise from the view
           using the ``itemDelegate()`` method of the table.

    comment: str
            comment string indicating the type of data to be copied (e.g.
            "filter coefficients ")


    The following keys from the global dict dict ``params['CSV']`` are evaluated:

    :'delimiter': str (default: "<tab>"),
          character for separating columns

    :'lineterminator': str (default: As used by the operating system),
            character for terminating rows. By default,
            the character is selected depending on the operating system:

            - Windows: Carriage return + line feed

            - MacOS  : Carriage return

            - \*nix   : Line feed

    :'orientation': str (one of 'auto', 'horiz', 'vert') determining with which
            orientation the table is read.

    :'header': str (default: 'auto').
            When ``header='on'``, treat first row as a header that will be discarded.

    :'clipboard': bool (default: True),
            when ``clipboard = True``, copy data to clipboard, else use a file.

    Returns
    -------
    None
        Nothing, text is exported to clipboard or to file via ``export_data``
    """

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
                        # print(c,r)
                        if item and item.text() != "":
                            text += table.itemDelegate().text(item).lstrip(" ") + delim
                text = text.rstrip(delim) + cr
            text.rstrip(cr)

    if params['CSV']['clipboard']:
        if hasattr(parent, 'clipboard'):
            parent.clipboard.setText(text)
        else:
            logger.error("No clipboard instance defined!")
    else:
        export_data(parent, unicode_23(text), fkey, comment=comment)

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
def qtext2table(parent, fkey, comment = ""):
    """
    Copy data from clipboard or file to table

    Parameters
    -----------

    parent: object
            parent instance, having a QClipboard and / or a QFileDialog attribute.

    fkey: str
            Key for accessing data in *.npz file or Matlab workspace (*.mat)

    comment: str
            comment string stating the type of data to be copied (e.g.
            "filter coefficients ")


    The following keys from the global dict ``params['CSV']`` are evaluated:

    :'delimiter': str (default: <tab>), character for separating columns

    :'lineterminator': str (default: As used by the operating system),
            character for terminating rows. By default,
            the character is selected depending on the operating system:

            - Windows: Carriage return + line feed

            - MacOS  : Carriage return

            - \*nix   : Line feed

    :'orientation': str (one of 'auto', 'horiz', 'vert') determining with which
            orientation the table is read.

    :'header': str (**'auto'**, 'on', 'off').
            When ``header=='on'``, treat first row as a header that will be discarded.

    :'clipboard': bool (default: True).
            When ``clipboard == True``, copy data from clipboard, else use a file

    Parameters that are 'auto', will be guessed by ``csv.Sniffer()``.

    Returns
    --------
    ndarray of str
        table data
    """

    if params['CSV']['clipboard']: # data from clipboard
        if not hasattr(parent, 'clipboard'):
            logger.error("No clipboard instance defined!")
            data_arr = None
        else:
            text = unicode_23(parent.clipboard.text())
            logger.debug("Importing data from clipboard:\n{0}\n{1}".format(np.shape(text), text))
            # pass handle to text and convert to numpy array:
            data_arr = csv2array(io.StringIO(text))
    else: # data from file
        data_arr = import_data(parent, fkey, comment)
        # pass data as numpy array
        logger.debug("Imported data from file. shape = {0}\n{1}".format(np.shape(data_arr), data_arr))

    return data_arr


#------------------------------------------------------------------------------
def csv2array(f):
    """
    Convert comma-separated values from file or text
    to numpy array, taking into accout the settings of the CSV dict.

    Parameters
    ----------

    f: handle to file or file-like object
        e.g.

        >>> f = io.open(file_name, 'r') # or
        >>> f = io.StringIO(text)

    Returns
    -------

    ndarray
        numpy array containing table data from file or text
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
        #------------------------------------------------------------------------------
        # Analyze CSV object
        #------------------------------------------------------------------------------
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
    #------------------------------------------------
    # finally, create iterator from csv data
    data_iter = csv.reader(f, dialect=dialect, delimiter=delimiter, lineterminator=lineterminator) # returns an iterator
    #------------------------------------------------
    if use_header:
        logger.info("Headers:\n{0}".format(next(data_iter, None))) # py3 and py2

    data_list = []
    try:
        for row in data_iter:
            logger.debug("{0}".format(row))
            data_list.append(row)
    except csv.Error as e:
        logger.error("Error during CSV reading:\n{0}".format(e))

    try:
        data_arr = np.array(data_list)
        cols, rows = np.shape(data_arr)
        logger.debug("cols = {0}, rows = {1}, data_arr = {2}\n".format(cols, rows, data_arr))
        if params['CSV']['orientation'] == 'vert':
            return data_arr.T
        else:
            return data_arr

    except (TypeError, ValueError) as e:
        logger.error("{0}\n{1}".format(e, data_list))
        return None

#------------------------------------------------------------------------------
def import_data(parent, fkey, comment):
    """
    Import data from a file and convert it to a numpy array.

    Parameters
    ----------
    parent: handle to calling instance

    fkey: string
        Key for accessing data in *.npz or Matlab workspace (*.mat) file.

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
            directory = dirs.save_dir, filter = file_filters)
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
                    data_arr = csv2array(f)
            else:
                with io.open(file_name, 'rb') as f:
                    if file_type == '.mat':
                        data_arr = loadmat(f)[fkey]
                    elif file_type == '.npy':
                        data_arr = np.load(f)
                        # contains only one array
                    elif file_type == '.npz':
                        fdict = np.load(f)
                        if fkey not in fdict:
                            file_type_err = True
                            raise IOError("Key '{0}' not in file '{1}'.\nKeys found: {2}"\
                                         .format(fkey, file_name, fdict.files))
                        else:
                            data_arr = fdict[fkey] # pick the array `fkey` from the dict
                    else:
                        logger.error('Unknown file type "{0}"'.format(file_type))
                        file_type_err = True

            if not file_type_err:
                logger.info('Successfully loaded \n"{0}"'.format(file_name))
                dirs.save_dir = os.path.dirname(file_name)
                return data_arr # returns numpy array

        except IOError as e:
            logger.error("Failed loading {0}!\n{1}".format(file_name, e))
            return None
    else:
        return -1 # operation cancelled
#------------------------------------------------------------------------------
def export_data(parent, data, fkey, comment=""):
    """
    Export coefficients or pole/zero data in various formats

    Parameters
    ----------
    parent: handle to calling instance for creating file dialog instance

    data: str
        formatted as CSV data, i.e. rows of elements separated by 'delimiter',
        terminated by 'lineterminator'

    fkey: str
        Key for accessing data in ``*.npz`` or Matlab workspace (``*.mat``) file.
        When fkey == 'ba', exporting to FPGA coefficients format is enabled.

    comment: str
        comment string stating the type of data to be copied (e.g.
        "filter coefficients ") for user message while opening file

    """
    dlg = QFD(parent) # create instance for QFileDialog

    logger.debug("imported data: type{0}|dim{1}|shape{2}\n{3}"\
                   .format(type(data), np.ndim(data), np.shape(data), data))

    file_filters = ("CSV (*.csv);;Matlab-Workspace (*.mat)"
        ";;Binary Numpy Array (*.npy);;Zipped Binary Numpy Array (*.npz)")

    if fb.fil[0]['ft'] == 'FIR':
        file_filters += (";;Xilinx FIR coefficient format (*.coe)"
                         ";;Microsemi FIR coefficient format (*.txt)")

#        # Add further file types when modules are available:
#        if XLWT:
#            file_filters += ";;Excel Worksheet (.xls)"
#        if XLSX:
#            file_filters += ";;Excel 2007 Worksheet (.xlsx)"

    # return selected file name (with or without extension) and filter (Linux: full text)
    file_name, file_type = dlg.getSaveFileName_(
            caption = "Export filter coefficients as",
            directory = dirs.save_dir, filter = file_filters)
    file_name = str(file_name) # QString -> str needed for Python 2

    for t in extract_file_ext(file_filters): # extract the list of file extensions
        if t in str(file_type):
            file_type = t

    if file_name != '': # cancelled file operation returns empty string
        # strip extension from returned file name (if any) + append file type:
        file_name = os.path.splitext(file_name)[0] +  file_type
        file_type_err = False

        try:
            if file_type in {'.coe', '.csv', '.txt'}: # text / string format
                with io.open(file_name, 'w', encoding="utf8") as f:
                    if file_type == '.coe':
                        export_coe_xilinx(f)
                    elif file_type == '.txt':
                        export_coe_microsemi(f)
                    else: # csv format
                        f.write(data)

            else: # binary format
                np_data = csv2array(io.StringIO(data))

                with io.open(file_name, 'wb') as f:
                    if file_type == '.mat':
                        savemat(f, mdict={fkey:np_data})
                        # newline='\n', header='', footer='', comments='# ', fmt='%.18e'
                    elif file_type == '.npy':
                        # can only store one array in the file, no pickled data
                        # for Py2 <-> 3 compatibility
                        np.save(f, np_data, allow_pickle=False)
                    elif file_type == '.npz':
                        # would be possible to store multiple arrays in the file
                        fdict = {fkey:np_data}
                        np.savez(f, **fdict) # unpack kw list (only one here)
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
                        logger.error('Unknown file type "{0}"'.format(file_type))
                        file_type_err = True

                    if not file_type_err:
                        logger.info('Filter saved as "{0}"'.format(file_name))
                        dirs.save_dir = os.path.dirname(file_name) # save new dir

        except IOError as e:
            logger.error('Failed saving "{0}"!\n{1}\n'.format(file_name, e))


        # Download the Simple ods py module:
        # http://simple-odspy.sourceforge.net/
        # http://codextechnicanum.blogspot.de/2014/02/write-ods-for-libreoffice-calc-from_1.html

#------------------------------------------------------------------------------
def export_coe_xilinx(f):
    """
    Save FIR filter coefficients in Xilinx coefficient format as file '\*.coe', specifying
    the number base and the quantized coefficients (decimal or hex integer).
    """
    qc = fix_lib.Fixed(fb.fil[0]['q_coeff']) # instantiate fixpoint object

    if qc.frmt == 'hex': # select hex format
        coe_radix = 16
    else:
        qc.setQobj({'frmt':'dec'}) # select decimal format in all other cases
        coe_radix = 10

    # Quantize coefficients to decimal / hex integer format, returning an array of strings
    bq = qc.float2frmt(fb.fil[0]['ba'][0])

    date_frmt = "%d-%B-%Y %H:%M:%S" # select date format

    xil_str = (
        "; #############################################################################\n"
         ";\n; XILINX CORE Generator(tm) Distributed Arithmetic FIR filter coefficient (.COE) file\n"
         ";\n; Generated by pyFDA 0.1 (https://github.com/chipmuenk/pyfda)\n;\n")

    xil_str += "; Designed:\t{0}\n".format(datetime.datetime.fromtimestamp(int(fb.fil[0]['timestamp'])).strftime(date_frmt))
    xil_str += "; Saved:\t{0}\n;\n".format(datetime.datetime.now().strftime(date_frmt))
    xil_str += "; Filter order = {0}, type: {1}\n".format(fb.fil[0]["N"], fb.fil[0]['rt'])
    xil_str += "; Params:\t f_S = {0}\n".format(fb.fil[0]["f_S"])
    xil_str += "; #############################################################################\n"
    xil_str += "Radix = {0};\n".format(coe_radix)
    xil_str += "Coefficient_width = {0};\n".format(qc.W) # quantized wordlength
    coeff_str = "CoefData = "
    for b in bq:
        coeff_str += str(b) + ",\n"
    xil_str += coeff_str[:-2] + ";" # replace last "," by ";"

    f.write(unicode_23(xil_str)) # convert to unicode for Python 2

#------------------------------------------------------------------------------
def export_coe_microsemi(f):
    """
    Save FIR filter coefficients in Actel coefficient format as file '\*.txt'.
    Coefficients have to be in integer format, the last line has to be empty.
    For (anti)aymmetric filter only one half of the coefficients must be
    specified?
    """
    qc = fix_lib.Fixed(fb.fil[0]['q_coeff']) # instantiate fixpoint object
    qc.setQobj({'frmt':'dec'}) # select decimal format in all other cases
    # Quantize coefficients to decimal integer format, returning an array of strings
    bq = qc.float2frmt(fb.fil[0]['ba'][0])

    coeff_str = "coefficient_set_1\n"
    for b in bq:
        coeff_str += str(b) + "\n"

    f.write(unicode_23(coeff_str)) # convert to unicode for Python 2

#------------------------------------------------------------------------------
def export_coe_TI(f):
    """
    Save FIR filter coefficients in TI coefficient format
    Coefficient have to be specified by an identifier 'b0 ... b191' followed
    by the coefficient in normalized fractional format, e.g.

    b0 .053647
    b1 -.27485
    b2 .16497
    ...

    ** not implemented yet **
    """
    pass

#==============================================================================

if __name__=='__main__':
    pass
