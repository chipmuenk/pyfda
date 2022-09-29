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
import os, re, io
import csv
import datetime
from typing import TextIO

import pickle

import numpy as np
from scipy.io import loadmat, savemat, wavfile

from .pyfda_lib import safe_eval, lin2unit, pprint_log
from .pyfda_qt_lib import qget_selected

import pyfda.libs.pyfda_fix_lib as fx
from pyfda.pyfda_rc import params
import pyfda.libs.pyfda_dirs as dirs
import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals

from .compat import QFileDialog

import logging
logger = logging.getLogger(__name__)


# ##############################################################################

# file filters for the QFileDialog object are constructed from this dict
file_filters_dict = {
    'cmsis': 'CMSIS DSP FIR or IIR SOS coefficients',
    'coe': 'Xilinx FIR coefficients format',
    'csv': 'Comma / Tab Separated Values',
    'mat': 'Matlab-Workspace',
    'npy': 'Binary Numpy Array',
    'npz': 'Zipped Binary Numpy Array',
    'pkl': 'Pickled data',
    'txt': 'Microsemi FIR coefficient format',
    'vhd': 'VHDL package or architecture',
    'wav': 'WAV audio format'
    }


# ------------------------------------------------------------------------------
def prune_file_ext(file_type: str) -> str:
    """
    Prune file extension, e.g. 'Text file' from 'Text file (\*.txt)' returned
    by QFileDialog file type description.

    Pruning is achieved with the following regular expression:

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



# ------------------------------------------------------------------------------
def extract_file_ext(file_type: str) -> str:
    """
    Extract list with file extension(s), e.g. '.vhd' from type description
    'VHDL (\*.vhd)' returned by QFileDialog

    Depending on the OS, this may be the full file type description
    or just the extension. When `file_type` contains no '(', the passed string is
    returned unchanged.
    """
    if "(" in file_type:
        ext_list = re.findall('\([^\)]+\)', file_type)  # extract '(*.txt)'
        return [t.strip('(*)') for t in ext_list]  # remove '(*)'
    else:
        return file_type


# ------------------------------------------------------------------------------
def qtable2text(table: object, data: np.ndarray, parent: object,
                fkey: str, frmt: str = 'float', title: str = "Export"):
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

    :'delimiter': str (default: ","),
          character for separating columns

    :'lineterminator': str (default: As used by the operating system),
            character for terminating rows. By default,
            the character is selected depending on the operating system:

            - Windows: Carriage return + line feed

            - MacOS  : Carriage return

            - \*nix   : Line feed

    :'orientation': str (one of 'auto', 'horiz', 'vert') determining with which
            orientation the table is written. 'vert' means a line break after
            each entry or pair of entries which usually is not what you want.
            'auto' doesn't make much sense when writing, 'horiz' is used in this case.

    :'header': str (default: 'auto').
            When ``header='on'``, write the first row with 'b, a'.

    :'clipboard': bool (default: True),
            when ``clipboard = True``, copy data to clipboard, else use a file.

    Returns
    -------
    None
        Nothing, text is exported to clipboard or to file via ``export_csv_data``
    """

    text = ""
    if params['CSV']['header'] in {'auto', 'on'}:
        use_header = True
    elif params['CSV']['header'] == 'off':
        use_header = False
    else:
        logger.error(
            f"Unknown key '{params['CSV']['header']}' for params['CSV']['header']")

    if params['CSV']['orientation'] in {'horiz', 'auto'}:
        orientation_horiz = True
    elif params['CSV']['orientation'] == 'vert':
        orientation_horiz = False
    else:
        logger.error(
            f"Unknown key '{params['CSV']['orientation']}' for "
            "params['CSV']['orientation']")

    delim = params['CSV']['delimiter'].lower()
    if delim == 'auto':  # 'auto' doesn't make sense when exporting
        delim = ","
    cr = params['CSV']['lineterminator']

    num_cols = table.columnCount()
    num_rows = table.rowCount()

    sel = qget_selected(table, reverse=False)['sel']

    # ==========================================================================
    # Nothing selected, but cell format is non-float:
    # -> select whole table, copy all cells further down below:
    # ==========================================================================
    if not np.any(sel) and frmt != 'float':
        sel = qget_selected(table, reverse=False, select_all=True)['sel']

    # ==========================================================================
    # Nothing selected, copy complete table from the model (data) in float format:
    # ==========================================================================
    if not np.any(sel):
        if orientation_horiz:  # rows are horizontal
            for c in range(num_cols):
                if use_header:  # add the table header
                    text += table.horizontalHeaderItem(c).text() + delim
                for r in range(num_rows):
                    text += str(safe_eval(data[c][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr
            text = text.rstrip(cr)  # delete last CR
        else:  # rows are vertical
            if use_header:  # add the table header
                for c in range(num_cols):
                    text += table.horizontalHeaderItem(c).text() + delim
                text = text.rstrip(delim) + cr
            for r in range(num_rows):
                for c in range(num_cols):
                    text += str(safe_eval(data[c][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr
            text = text.rstrip(cr)  # delete CR after last row

    # =======================================================================
    # Copy only selected cells in displayed format:
    # =======================================================================
    else:
        if orientation_horiz:  # horizontal orientation, one or two rows
            if use_header:  # add the table header
                text += table.horizontalHeaderItem(0).text() + delim
            if sel[0]:
                for r in sel[0]:
                    item = table.item(r, 0)
                    if item and item.text() != "":
                        text += table.itemDelegate().text(item).lstrip(" ") + delim
                text = text.rstrip(delim)  # remove last tab delimiter again

            if sel[1]:  # returns False for []
                text += cr  # add a CRLF when there are two columns
                if use_header:  # add the table header
                    text += table.horizontalHeaderItem(1).text() + delim
                for r in sel[1]:
                    item = table.item(r, 1)
                    if item and item.text() != "":
                        text += table.itemDelegate().text(item) + delim
                text = text.rstrip(delim)  # remove last tab delimiter again
        else:  # vertical orientation, one or two columns
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

            for r in range(num_rows):  # iterate over whole table
                for c in sel_c:
                    if r in sel[c]:  # selected item?
                        item = table.item(r, c)
                        # print(c,r)
                        if item and item.text() != "":
                            text += table.itemDelegate().text(item).lstrip(" ") + delim
                text = text.rstrip(delim) + cr
            text.rstrip(cr)

    if params['CSV']['clipboard']:
        fb.clipboard.setText(text)
    else:
        export_csv_data(parent, text, fkey, title=title)

# ==============================================================================
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
# ==============================================================================


# ------------------------------------------------------------------------------
def qtext2table(parent: object, fkey: str, title: str = "Import"):
    """
    Copy data from clipboard or file to table

    Parameters
    -----------

    parent: object
            parent instance, having a QClipboard and / or a QFileDialog attribute.

    fkey: str
            Key for accessing data in *.npz file or Matlab workspace (*.mat)

    title: str
        title string for the file dialog box


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

    if params['CSV']['clipboard']:  # data from clipboard
        text = fb.clipboard.text()
        logger.debug(
            f"Importing data from clipboard:\n{np.shape(text)}\n{text}")
        # pass handle to text and convert to numpy array:
        data_arr = csv2array(io.StringIO(text))
        if isinstance(data_arr, str):  # returned an error message instead of numpy data
            logger.error("Error importing clipboard data:\n\t{0}".format(data_arr))
            return None
    else:  # data from file
        data_arr = import_data(
            parent, fkey, title=title, file_types=('csv', 'mat', 'npy', 'npz'))
        # pass data as numpy array
        logger.debug("Imported data from file. shape = {0} | {1}\n{2}"
                     .format(np.shape(data_arr), np.ndim(data_arr), data_arr))
        if type(data_arr) == int and data_arr == -1:  # file operation cancelled
            data_arr = None
    return data_arr


# ------------------------------------------------------------------------------
def csv2array(f: TextIO):
    """
    Convert comma-separated values from file or text
    to numpy array, taking into accout the settings of the CSV dict.

    Parameters
    ----------

    f: handle to file or file-like object
        e.g.

        >>> f = open(file_name, 'r') # or
        >>> f = io.StringIO(text)

    Returns
    -------

    ndarray
        numpy array containing table data from file or text when import was
        successful

    io_error: str
        String with the error message when import was unsuccessful
    """
    # throw an error (instead of a deprecation warning) when trying to create a numpy
    # array from nested ragged sequences. This error can then be caught easily.
    np.warnings.filterwarnings('error', category=np.VisibleDeprecationWarning)
    # ------------------------------------------------------------------------------
    # Get CSV parameter settings
    # ------------------------------------------------------------------------------
    io_error = ""  # initialize string for I/O error messages
    CSV_dict = params['CSV']
    try:
        header = CSV_dict['header'].lower()
        if header in {'auto', 'on', 'off'}:
            pass
        else:
            header = 'auto'
            logger.warning(
                f"Unknown key '{CSV_dict['header']}' for CSV_dict['header'], "
                f"using {header} instead.")

        orientation_horiz = CSV_dict['orientation'].lower()
        if orientation_horiz in {'auto', 'vert', 'horiz'}:
            pass
        else:
            orientation_horiz = 'vert'
            logger.warning(
                f"Unknown key '{CSV_dict['orientation']}' for CSV_dict['orientation'], "
                f"using {orientation_horiz} instead.")

        tab = CSV_dict['delimiter'].lower()
        cr = CSV_dict['lineterminator'].lower()

    except KeyError as e:
        io_error = "Dict 'params':\n{0}".format(e)
        return io_error

    try:
        # ------------------------------------------------------------------------------
        # Analyze CSV object
        # ------------------------------------------------------------------------------
        if header == 'auto' or tab == 'auto' or cr == 'auto':
            # test the first line for delimiters (of the given selection)
            dialect = csv.Sniffer().sniff(f.readline(),
                                          delimiters=['\t', ';', ',', '|', ' '])
            f.seek(0)                               # and reset the file pointer
        else:
            # fall back, alternatives: 'excel', 'unix':
            dialect = csv.get_dialect('excel-tab')

        if header == "auto":
            # True when header detected:
            use_header = csv.Sniffer().has_header(f.read(1000))
            f.seek(0)

    except csv.Error as e:
        logger.warning("Error during CSV analysis:\n{0},\n"
                       "continuing with format 'excel-tab'".format(e))
        dialect = csv.get_dialect('excel-tab')  # fall back
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

    logger.info("Parsing CSV data with \n"
                "\tHeader = {0} | Delim. = {1} | Lineterm. = {2} | Quotechar = ' {3} '"
                # "\n\tType of passed text: '{4}'"
                .format(use_header, repr(delimiter), repr(lineterminator),
                        quotechar))  # ,f.__class__.__name__))
    # --------------------------------------------------------------------------
    # finally, create iterator from csv data
    data_iter = csv.reader(f, dialect=dialect, delimiter=delimiter,
                           lineterminator=lineterminator)  # returns an iterator
    # --------------------------------------------------------------------------
# =============================================================================
#     with open('/your/path/file') as f:
#         for line in f:
#             process(line)
#
#     Where you define your process function any way you want. For example:
#
#         def process(line):
#             if 'save the world' in line.lower():
#                 superman.save_the_world()
#
#     This will work nicely for any file size and you go through your file in just 1 pass.
#     This is typically how generic parsers will work.
#     (https://stackoverflow.com/questions/3277503/how-to-read-a-file-line-by-line-into-a-list)
# =============================================================================

    if use_header:
        logger.info("Headers:\n{0}".format(next(data_iter, None)))  # py3 and py2

    data_list = []
    try:
        for row in data_iter:
            logger.debug("{0}".format(row))
            data_list.append(row)
    except csv.Error as e:
        io_error = f"Error during CSV import:\n{e}"
        return io_error

    try:
        if data_list is None:
            return "Imported data is None."
        try:
            data_arr = np.array(data_list)
        except np.VisibleDeprecationWarning:
            # prevent creation of numpy arrays from nested ragged sequences
            return "Columns with different number of elements."

        if np.ndim(data_arr) == 0 or (np.ndim(data_arr) == 1 and len(data_arr) < 2):
            return f"Imported data is a scalar: '{data_arr}'"
        elif np.ndim(data_arr) == 1:
            if len(data_arr) < 2:
                return f"Not enough data: '{data_arr}'"
            else:
                return data_arr
        elif np.ndim(data_arr) == 2:
            cols, rows = np.shape(data_arr)
            logger.debug(f"cols = {cols}, rows = {rows}, data_arr = {data_arr}\n")
            if cols > 2 and rows > 2:
                return f"Unsuitable data shape {np.shape(data_arr)}"
            elif cols > rows:
                return data_arr.T
            else:
                return data_arr
        else:
            return "Unsuitable data shape: ndim = {0}, shape = {1}"\
                .format(np.ndim(data_arr), np.shape(data_arr))

    except (TypeError, ValueError) as e:
        io_error = "{0}\nFormat = {1}\n{2}".format(e, np.shape(data_arr), data_list)
        return io_error

# =============================================================================
#     try:
#         data_arr = np.array(data_list)
#         cols, rows = np.shape(data_arr)
#         logger.debug("cols = {0}, rows = {1}, data_arr = {2}\n"
#                       .format(cols, rows, data_arr))
#         if params['CSV']['orientation'] == 'vert':
#             return data_arr.T
#         else:
#             return data_arr
#
#     except (TypeError, ValueError) as e:
#         io_error = "{0}\nFormat = {1}\n{2}".format(e, np.shape(data_arr), data_list)
#         return io_error
#
# =============================================================================


# ------------------------------------------------------------------------------
def csv2array_new(f: TextIO):
    """
    Convert comma-separated values from file or text
    to numpy array, taking into accout the settings of the CSV dict.

    Parameters
    ----------

    f: handle to file or file-like object
        e.g.

        >>> f = open(file_name, 'r') # or
        >>> f = io.StringIO(text)

    Returns
    -------

    ndarray
        numpy array containing table data from file or text when import was
        successful

    io_error: str
        String with the error message when import was unsuccessful
    """
    # ------------------------------------------------------------------------------
    # Get CSV parameter settings
    # ------------------------------------------------------------------------------
    io_error = ""  # initialize string for I/O error messages
    CSV_dict = params['CSV']
    logger.warning("Fileobject format: {0}".format(type(f).__name__))
    try:
        header = CSV_dict['header'].lower()
        if header in {'auto', 'on', 'off'}:
            pass
        else:
            header = 'auto'
            logger.warning(
                f"Unknown key '{CSV_dict['header']}' for CSV_dict['header'], "
                f"using {header} instead.")

        orientation_horiz = CSV_dict['orientation'].lower()
        if orientation_horiz in {'auto', 'vert', 'horiz'}:
            pass
        else:
            orientation_horiz = 'vert'
            logger.warning(
                f"Unknown key '{CSV_dict['orientation']}' for CSV_dict['orientation'], "
                f"using {orientation_horiz} instead.")

        tab = CSV_dict['delimiter'].lower()
        cr = CSV_dict['lineterminator'].lower()

    except KeyError as e:
        io_error = "Dict 'params':\n{0}".format(e)
        return io_error

    try:
        # ------------------------------------------------------------------------------
        # Analyze CSV object
        # ------------------------------------------------------------------------------
        if header == 'auto' or tab == 'auto' or cr == 'auto':
            # test the first line for delimiters (of the given selection)
            dialect = csv.Sniffer().sniff(f.readline(),
                                          delimiters=['\t', ';', ',', '|', ' '])
            f.seek(0)                               # and reset the file pointer
        else:
            # fall back, alternatives: 'excel', 'unix':
            dialect = csv.get_dialect('excel-tab')

        if header == "auto":
            # True when header detected:
            use_header = csv.Sniffer().has_header(f.read(1000))
            f.seek(0)

    except csv.Error as e:
        logger.warning("Error during CSV analysis:\n{0},\n"
                       "continuing with format 'excel-tab'".format(e))
        dialect = csv.get_dialect('excel-tab')  # fall back
        use_header = False

    if header == 'on':
        use_header = True
    elif header == 'off':
        use_header = False
    # case 'auto' has been treated above

    delimiter = dialect.delimiter
    lineterminator = dialect.lineterminator
    quotechar = dialect.quotechar

    if tab != 'auto':
        delimiter = str(tab)

    if cr != 'auto':
        lineterminator = str(cr)

    logger.info("Parsing CSV data with header = '{0}'\n"
                "\tDelimiter = {1} | Lineterm. = {2} | quotechar = ' {3} '\n"
                "\tType of passed text: '{4}'"
                .format(use_header, repr(delimiter), repr(lineterminator),
                        quotechar, f.__class__.__name__))
    # ------------------------------------------------
    # finally, create iterator from csv data
    data_iter = csv.reader(f, dialect=dialect, delimiter=delimiter,
                           lineterminator=lineterminator)
    # ------------------------------------------------
# =============================================================================
    """
    newline controls how universal newlines works (it only applies to text mode).
    It can be None, '', '\n', '\r', and '\r\n'. It works as follows:

    - On input, if newline is None, universal newlines mode is enabled. Lines in
      the input can end in '\n', '\r', or '\r\n', and these are translated into
      '\n' before being returned to the caller. If it is '', universal newline
      mode is enabled, but line endings are returned to the caller untranslated.
      If it has any of the other legal values, input lines are only terminated
      by the given string, and the line ending is returned to the caller untranslated.

    - On output, if newline is None, any '\n' characters written are translated
      to the system default line separator, os.linesep. If newline is '',
      no translation takes place. If newline is any of the other legal values,
      any '\n' characters written are translated to the given string.

      Example: convert from Windows-style line endings to Linux:
      fileContents = open(filename,"r").read()
      f = open(filename,"w", newline="\n")
      f.write(fileContents)
      f.close()
      https://pythonconquerstheuniverse.wordpress.com/2011/05/08/newline-conversion-in-python-3/
     """

    data_list = []

    def process(line):
        # split into lines (if not split yet):
        data_list.append(line.split(lineterminator))

    # with open(fo) as f:
    for line in f:
        process(line)

    for e in data_list:
        pass

    # Where you define your process function any way you want. For example:

    # This will work nicely for any file size and you go through your file in just 1 pass.
    # This is typically how generic parsers will work.
    # (https://stackoverflow.com/questions/3277503/how-to-read-a-file-line-by-line-into-a-list)
# =============================================================================

# =============================================================================
#     if use_header:
#         logger.info("Headers:\n{0}".format(next(data_iter, None))) # py3 and py2
#
#     try:
#         for row in data_iter:
#             logger.debug("{0}".format(row))
#             data_list.append(row)
#     except csv.Error as e:
#         io_error = "Error during CSV reading:\n{0}".format(e)
#         return io_error
# =============================================================================

    try:
        if data_list is None:
            return "Imported data is None."
        data_arr = np.array(data_list)
        if np.ndim(data_arr) == 0 or (np.ndim(data_arr) == 1 and len(data_arr) < 2):
            return f"Imported data is a scalar: '{data_arr}'"
        elif np.ndim(data_arr) == 1:
            return data_arr
        elif np.ndim(data_arr) == 2:
            cols, rows = np.shape(data_arr)
            logger.debug(f"cols = {cols}, rows = {rows}, data_arr = {data_arr}\n")
            if cols > 2 and rows > 2:
                return "Unsuitable data shape {0}".format(np.shape(data_arr))
            elif cols > rows:
                return data_arr.T
            else:
                return data_arr
        else:
            return "Unsuitable data shape: ndim = {0}, shape = {1}"\
                .format(np.ndim(data_arr), np.shape(data_arr))

    except (TypeError, ValueError) as e:
        io_error = f"{e}\nFormat = {np.shape(data_arr)}\n{data_list}"
        return io_error


# ------------------------------------------------------------------------------
def create_file_filters(file_types: tuple, file_filters: str = ""):
    """
    Create a string with file filters for QFileDialog object from `file_types`,
    a tuple of file extensions and the global `file_filters_dict`.

    When the file extension stored after last QFileDialog operation is in the tuple
    of file types, return this file extension for e.g. preselecting the file type
    in QFileDialog.

    Parameters
    ----------
    file_types : tuple of str
        list of file extensions which are used to create a file filter.

    file_filters : str
        String with file filters for QFileDialog object with the form
        "Comma / Tab Separated Values (*.csv);; Audio (*.wav *.mp3)". By default,
        this string is empty, but it can be used to add file filters not contained
        in the global `file_filters_dict`.

    Returns
    -------
    file_filters : str
        String containing file filters for a QFileDialog object

    last_file_filter : str
        Single file filter to setup the default file extension in QFileDialog

    """
    for t in file_types:
        if t in file_filters_dict:
            file_filters += file_filters_dict[t] + f" (*.{t});;"
        else:
            logger.warning(f"Unknown file extension '.{t}'")
    # remove trailing ';;', otherwise file filter '*' is appended
    file_filters = file_filters.rstrip(';;')

    if dirs.last_file_type and dirs.last_file_type in file_filters_dict:
        last_file_filter =\
            file_filters_dict[dirs.last_file_type] + f" (*.{dirs.last_file_type})"
    else:
        last_file_filter = ""

    return file_filters, last_file_filter


# ------------------------------------------------------------------------------
def import_data(parent, fkey=None, title="Import",
                file_types=('csv', 'mat', 'npy', 'npz')):
    """
    Import data from a file and convert it to a numpy array.

    Parameters
    ----------
    parent : handle to calling instance

    fkey : str
        Key for accessing data in *.npz or Matlab workspace (*.mat) file with
        multiple entries.

    title : str
        title string for the file dialog box (e.g. "Filter Coefficients")

    file_types : tuple of str
        supported file types, e.g. `('txt', 'npy', 'mat') which need to be keys
        of `file_filters_dict`

    Returns
    -------
    ndarray
        Data from the file
    """
    file_filters, last_file_filter = create_file_filters(file_types=file_types)

    dlg = QFileDialog(parent)  # create instance for QFileDialog
    dlg.setWindowTitle(title)
    dlg.setDirectory(dirs.last_file_dir)
    dlg.setAcceptMode(QFileDialog.AcceptOpen)  # set dialog to "file open" mode
    dlg.setNameFilter(file_filters)  # pass available file filters
    dlg.setDefaultSuffix('csv')  # default suffix when none is given
    if last_file_filter:
        dlg.selectNameFilter(last_file_filter)  # filter selected in last file dialog

    if dlg.exec_() == QFileDialog.Accepted:
        file_name = dlg.selectedFiles()[0]  # pick only first selected file
        file_type = os.path.splitext(file_name)[-1].strip('.')
    else:
        return -1  # operation cancelled

    err = False
    try:
        if file_type == 'wav':
            f_S, data_arr = wavfile.read(file_name, mmap=False)
            fb.fil[0]['f_S_wav'] = f_S
        elif file_type in {'csv', 'txt'}:
            with open(file_name, 'r', newline=None) as f:
                data_arr = csv2array(f)
                # data_arr = np.loadtxt(f, delimiter=params['CSV']['delimiter'].lower())
                if isinstance(data_arr, str):
                    # returned an error message instead of numpy data:
                    logger.error(f"Error loading file '{file_name}':\n{data_arr}")
                    return None
        else:
            with open(file_name, 'rb') as f:
                if file_type == 'mat':
                    data_arr = loadmat(f)[fkey]
                elif file_type == 'npy':
                    data_arr = np.load(f)
                    # contains only one array
                elif file_type == 'npz':
                    fdict = np.load(f)
                    if fkey not in fdict:
                        err = True
                        raise IOError(
                            "Key '{0}' not in file '{1}'.\nKeys found: {2}"
                            .format(fkey, file_name, fdict.files))
                    else:
                        data_arr = fdict[fkey]  # pick the array `fkey` from the dict
                else:
                    logger.error('Unknown file type "{0}"'.format(file_type))
                    err = True

        if not err:
            logger.info(
                f'Imported file "{file_name}"\n{pprint_log(data_arr, N=3)}')
            dirs.last_file_name = file_name
            dirs.last_file_dir = os.path.dirname(file_name)
            dirs.last_file_type = file_type
            return data_arr  # returns numpy array

    except IOError as e:
        logger.error("Failed loading {0}!\n{1}".format(file_name, e))
        return None


# ------------------------------------------------------------------------------
def export_csv_data(parent: object, data: str, fkey: str = "", title: str = "Export",
                file_types=('csv', 'mat', 'npy', 'npz')):
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

    title: str
        title string for the file dialog box (e.g. "filter coefficients ")

    file_types: tuple of strings
        file extension (e.g. `(csv)` or list of file extensions (e.g. `(csv, txt)`
        which are used to create a file filter.
    """
    logger.debug(
        f"imported data: type{type(data)}|dim{np.ndim(data)}|"
        f"shape{np.shape(data)}\n{data}")

    # add file types for FIR filter coefficients
    if fb.fil[0]['ft'] == 'FIR':
        file_types += ('coe', 'vhd', 'txt')

    file_filters, last_file_filter = create_file_filters(file_types=file_types)

#        # Add further file types when modules are available:
#        if XLWT:
#            file_filters += ";;Excel Worksheet (.xls)"
#        if XLSX:
#            file_filters += ";;Excel 2007 Worksheet (.xlsx)"

    # return selected file name (with or without extension) and filter (Linux: full text)
    dlg = QFileDialog(parent)  # create instance for QFileDialog
    dlg.setWindowTitle(title)
    dlg.setDirectory(dirs.last_file_dir)
    dlg.setAcceptMode(QFileDialog.AcceptSave)  # set dialog to "file save" mode
    dlg.setNameFilter(file_filters)  # set the list with all available file formats
    # dlg.setDefaultSuffix()  # does not work, need to specify the suffix

    if last_file_filter:
        dlg.selectNameFilter(last_file_filter)  # filter selected in last file dialog

    if dlg.exec_() == QFileDialog.Accepted:
        file_name = dlg.selectedFiles()[0]   # convert list (with single entry?) to item
        sel_filt = dlg.selectedNameFilter()  # selected file filter
    else:
        return -1

    # Slice off file extension
    file_type = os.path.splitext(file_name)[-1].strip('.')
    if file_type == "":
        # No file type specified, add the type from the file filter
        file_type = extract_file_ext(sel_filt)[0].strip('.')
        file_name = file_name + '.' + file_type

    err = False

    try:
        if file_type == 'csv':
            with open(file_name, 'w', encoding="utf8", newline='') as f:
                f.write(data)
        elif file_type in {'coe', 'txt', 'vhd'}:  # text / string format
            with open(file_name, 'w', encoding="utf8") as f:
                if file_type == 'coe':
                    err = export_coe_xilinx(f)
                elif file_type == 'txt':
                    err = export_coe_microsemi(f)
                elif file_type == '.vhd':
                    err = export_coe_vhdl_package(f)
                else:
                    logger.error(f'Unknown file extension "{file_type}')
                    return None

        else:  # binary formats, storing numpy arrays
            np_data = csv2array(io.StringIO(data))  # convert csv data to numpy array
            if isinstance(np_data, str):
                # returned an error message instead of numpy data:
                logger.error("Error converting coefficient data:\n{0}".format(np_data))
                return None

            with open(file_name, 'wb') as f:
                if file_type == 'mat':
                    savemat(f, mdict={fkey: np_data})
                    # newline='\n', header='', footer='', comments='# ', fmt='%.18e'
                elif file_type == 'npy':
                    np.save(f, np_data)  # can only store one array
                elif file_type == 'npz':
                    # would be possible to store multiple arrays in the file
                    fdict = {fkey: np_data}
                    np.savez(f, **fdict)  # unpack kw list (only one here)
                elif file_type == 'xls':
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
                            worksheet.write(row+1, col, data[col][row])  # vertical
                    workbook.save(f)

                elif file_type == 'xlsx':
                    # from https://pypi.python.org/pypi/XlsxWriter
                    # Create an new Excel file and add a worksheet.
                    workbook = xlsx.Workbook(f)
                    worksheet = workbook.add_worksheet()
                    # Widen the first column to make the text clearer.
                    worksheet.set_column('A:A', 20)
                    # define a bold format to highlight cells
                    bold = workbook.add_format({'bold': True})
                    # Write labels with formatting.
                    worksheet.write('A1', 'b', bold)
                    worksheet.write('B1', 'a', bold)

                    # Write some numbers, with row/column notation.
                    for col in range(2):
                        for row in range(np.shape(data)[1]):
                            worksheet.write(row+1, col, data[col][row])  # vertical
        #                    worksheet.write(row, col, coeffs[col][row])  # horizontal

                    # Insert an image - useful for documentation export ?!.
        #            worksheet.insert_image('B5', 'logo.png')

                    workbook.close()

                else:
                    logger.error('Unknown file type "{0}"'.format(file_type))
                    err = True

        if not err:
            logger.info(f'Filter saved as\n\t"{file_name}"')
            dirs.last_file_name = file_name
            dirs.last_file_dir = os.path.dirname(file_name)  # save new dir
            dirs.last_file_type = file_type  # save file type

    except IOError as e:
        logger.error('Failed saving "{0}"!\n{1}\n'.format(file_name, e))

        # Download the Simple ods py module:
        # http://simple-odspy.sourceforge.net/
        # http://codextechnicanum.blogspot.de/2014/02/write-ods-for-libreoffice-calc-from_1.html


# ------------------------------------------------------------------------------
def generate_header(title: str) -> str:
    """
    Generate a file header (comment) for various FPGA FIR coefficient export formats
    with information on the filter type, corner frequencies, ripple etc

    Parameters
    ----------
    title: str
       A string that is written in the top of the comment section of the exported
       file.

    Returns
    -------
    header: str
        The string with all the gathered information
    """
    f_lbls = []
    f_vals = []
    a_lbls = []
    a_targs = []
    a_targs_dB = []
    ft = fb.fil[0]['ft']  # get filter type ('IIR', 'FIR')
    unit = fb.fil[0]['amp_specs_unit']
    unit = 'dB'  # fix this for the moment
    # construct pairs of corner frequency and corresponding amplitude
    # labels in ascending frequency for each response type
    if fb.fil[0]['rt'] in {'LP', 'HP', 'BP', 'BS', 'HIL'}:
        if fb.fil[0]['rt'] == 'LP':
            f_lbls = ['F_PB', 'F_SB']
            a_lbls = ['A_PB', 'A_SB']
        elif fb.fil[0]['rt'] == 'HP':
            f_lbls = ['F_SB', 'F_PB']
            a_lbls = ['A_SB', 'A_PB']
        elif fb.fil[0]['rt'] == 'BP':
            f_lbls = ['F_SB', 'F_PB', 'F_PB2', 'F_SB2']
            a_lbls = ['A_SB', 'A_PB', 'A_PB', 'A_SB2']
        elif fb.fil[0]['rt'] == 'BS':
            f_lbls = ['F_PB', 'F_SB', 'F_SB2', 'F_PB2']
            a_lbls = ['A_PB', 'A_SB', 'A_SB', 'A_PB2']
        elif fb.fil[0]['rt'] == 'HIL':
            f_lbls = ['F_PB', 'F_PB2']
            a_lbls = ['A_PB', 'A_PB']

        # Try to get lists of frequency / amplitude specs from the filter dict
        # that correspond to the f_lbls / a_lbls pairs defined above
        # When one of the labels doesn't exist in the filter dict, delete
        # all corresponding amplitude and frequency entries.
        err = [False] * len(f_lbls)  # initialize error list
        f_vals = []
        a_targs = []
        for i in range(len(f_lbls)):
            try:
                f = fb.fil[0][f_lbls[i]]
                f_vals.append(f)
            except KeyError as e:
                f_vals.append('')
                err[i] = True
                logger.debug(e)
            try:
                a = fb.fil[0][a_lbls[i]]
                a_dB = lin2unit(fb.fil[0][a_lbls[i]], ft, a_lbls[i], unit)
                a_targs.append(a)
                a_targs_dB.append(a_dB)
            except KeyError as e:
                a_targs.append('')
                a_targs_dB.append('')
                err[i] = True
                logger.debug(e)

        for i in range(len(f_lbls)):
            if err[i]:
                del f_lbls[i]
                del f_vals[i]
                del a_lbls[i]
                del a_targs[i]
                del a_targs_dB[i]

    date_frmt = "%d-%B-%Y %H:%M:%S"  # select date format
    unit = fb.fil[0]['plt_fUnit']
    if unit in {'f_S', 'f_Ny'}:
        f_S = ""
    else:
        f_S = fb.fil[0]["f_S"]
    header = (
        "-" * 85 + "\n\n"
        "{0}".format(title) + "\n"
        "Generated by pyFDA 0.6 (https://github.com/chipmuenk/pyfda)\n\n")
    header += "Designed:\t{0}\n".format(
        datetime.datetime.fromtimestamp(
            int(fb.fil[0]['timestamp'])).strftime(date_frmt))
    header += "Saved:\t{0}\n\n".format(datetime.datetime.now().strftime(date_frmt))
    header += f"Filter type:\t{fb.fil[0]['rt']}, {fb.fil[0]['fc']} "
    header += f"(Order = {fb.fil[0]['N']})\n"
    header += f"Sample Frequency \tf_S = {f_S} {unit}\n\n"
    header += "Corner Frequencies:\n"
    for lf, f, la, a in zip(f_lbls, f_vals, a_lbls, a_targs_dB):
        header += "\t" + lf + " = " + str(f) + " " + unit + " : " + la + " = "
        header += str(a) + " dB\n"
    header += "-" * 85 + "\n"
    return header


# ------------------------------------------------------------------------------
def export_coe_xilinx(f: TextIO):
    """
    Save FIR filter coefficients in Xilinx coefficient format as file '\*.coe', specifying
    the number base and the quantized coefficients (decimal or hex integer).
    """
    qc = fx.Fixed(fb.fil[0]['fxqc']['QCB'])  # instantiate fixpoint object
    logger.debug("scale = {0}, WF = {1}".format(qc.q_dict['scale'], qc.q_dict['WF']))

    if qc.q_dict['WF'] != 0:
        # Set the fixpoint format to integer (WF=0) with the original wordlength
        qc.set_qdict({'W': qc.q_dict['W'], 'scale': 1 << qc.q_dict['W']-1})
        logger.warning("Fractional formats are not supported, using integer format.")

    if qc.q_dict['fx_base'] == 'hex':  # select hex format
        coe_radix = 16
    if qc.q_dict['fx_base'] == 'bin':  # select binary format
        coe_radix = 2
    else:
        logger.warning('Coefficients in "{0}" format are not supported in COE files, '
                       'using decimal format.')
        qc.set_qdict({'fx_base': 'dec'})  # select decimal format in all other cases
        coe_radix = 10

    # Quantize coefficients to decimal / hex integer format, returning an array of strings
    bq = qc.float2frmt(fb.fil[0]['ba'][0])

    exp_str = "; " + generate_header(
        "XILINX CORE Generator(tm) Distributed Arithmetic FIR filter coefficient (.COE) file").replace("\n", "\n; ")

    exp_str += "\nRadix = {0};\n".format(coe_radix)
    exp_str += f"Coefficient_width = {qc.q_dict['W']};\n"  # quantized wordlength
    coeff_str = "CoefData = "
    for b in bq:
        coeff_str += str(b) + ",\n"
    exp_str += coeff_str[:-2] + ";"  # replace last "," by ";"

    f.write(exp_str)

    return False


# ------------------------------------------------------------------------------
def export_coe_microsemi(f: TextIO):
    """
    Save FIR filter coefficients in Microsemi coefficient format as file '\*.txt'.
    Coefficients have to be in integer format, the last line has to be empty.
    For (anti)symmetric filter only one half of the coefficients must be
    specified?
    """
    qc = fx.Fixed(fb.fil[0]['fxqc']['QCB'])  # instantiate fixpoint object

    if qc.q_dict['WF'] != 0:
        # Set the fixpoint format to integer (WF=0) with the original wordlength:
        qc.set_qdict({'W': qc.q_dict['W'], 'scale': 1 << qc.q_dict['W']-1})
        logger.warning("Fractional formats are not supported, using integer format.")

    if qc.q_dict['fx_base'] != 'dec':
        qc.set_qdict({'fx_base': 'dec'})  # select decimal format in all other cases
        logger.warning('Only coefficients in "dec" format are supported,'
                       'using decimal format.')

    # Quantize coefficients to decimal integer format, returning an array of strings
    bq = qc.float2frmt(fb.fil[0]['ba'][0])

    coeff_str = "coefficient_set_1\n"
    for b in bq:
        coeff_str += str(b) + "\n"

    f.write(coeff_str)

    return False


# ------------------------------------------------------------------------------
def export_coe_vhdl_package(f: TextIO):
    """
    Save FIR filter coefficients as a VHDL package '\*.vhd', specifying
    the number base and the quantized coefficients (decimal or hex integer).
    """
    qc = fx.Fixed(fb.fil[0]['fxqc']['QCB'])  # instantiate fixpoint object
    if not qc.q_dict['fx_base'] == 'float' and qc.q_dict['WF'] != 0:
        # Set the fixpoint format to integer (WF=0) with the original wordlength
        qc.set_qdict({'W': qc.q_dict['W'], 'scale': 1 << qc.q_dict['W']-1})
        logger.warning("Fractional formats are not supported, using integer format.")

    WO = fb.fil[0]['fxqc']['QO']['W']

    if qc.q_dict['fx_base'] == 'hex':
        pre = "#16#"
        post = "#"
    elif qc.q_dict['fx_base'] == 'bin':
        pre = "#2#"
        post = "#"
    elif qc.q_dict['fx_base'] in {'dec', 'float'}:
        pre = ""
        post = ""
    else:
        qc.set_qdict({'fx_base': 'dec'})  # select decimal format in all other cases
        pre = ""
        post = ""
        logger.warning('Coefficients in "{0}" format are currently not supported, '
                       'using decimal format.'.format(qc.q_dict['fx_base']))

    # Quantize coefficients to selected fixpoint format, returning an array of strings
    bq = qc.float2frmt(fb.fil[0]['ba'][0])

    exp_str = "-- " + generate_header(
        "VHDL FIR filter coefficient package file").replace("\n", "\n-- ")

    exp_str += "\nlibrary IEEE;\n"
    if qc.q_dict['fx_base'] == 'float':
        exp_str += "use IEEE.math_real.all;\n"
    exp_str += "USE IEEE.std_logic_1164.all;\n\n"
    exp_str += "package coeff_package is\n"
    exp_str += "constant n_taps: integer := {0:d};\n".format(len(bq)-1)
    if qc.q_dict['fx_base'] == 'float':
        exp_str += "type coeff_type is array(0 to n_taps) of real;\n"
    else:
        exp_str += "type coeff_type is array(0 to n_taps) of integer "
        exp_str += "range {0} to {1};\n\n".format(-1 << WO-1, (1 << WO-1) - 1)
    exp_str += "constant coeff : coeff_type := "

    coeff_str = "(\n"
    for b in bq:
        coeff_str += "\t" + pre + str(b) + post + ",\n"
    exp_str += coeff_str[:-2] + ");\n\n"  # replace last "," by ");"

    exp_str += "end coeff_package;"

    f.write(exp_str)

    return False


# ------------------------------------------------------------------------------
def export_coe_TI(f: TextIO):
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


# ==============================================================================
def load_filter(self):
    """
    Load filter from zipped binary numpy array or (c)pickled object to
    filter dictionary and update input and plot widgets
    """
    file_types = ("npz", "pkl")
    file_filters, last_file_filter = create_file_filters(file_types)

    dlg = QFileDialog(self)
    dlg.setWindowTitle("Load Filter")
    dlg.setDirectory(dirs.last_file_dir)
    dlg.setAcceptMode(QFileDialog.AcceptOpen)  # set dialog to "file open" mode
    dlg.setNameFilter(file_filters)  # pass available file filters
    # dlg.setDefaultSuffix('csv')  # default suffix when none is given
    if last_file_filter:
        dlg.selectNameFilter(last_file_filter)  # filter selected in last file dialog

    if dlg.exec_() == QFileDialog.Accepted:
        file_name = dlg.selectedFiles()[0]  # pick only first selected file
        file_type = os.path.splitext(file_name)[-1].strip('.')
    else:
        return -1  # operation cancelled

    err = False
    fb.fil[1] = fb.fil[0].copy()  # backup filter dict
    try:
        with io.open(file_name, 'rb') as f:
            if file_type == 'npz':
                # array containing dict, dtype 'object':
                a = np.load(f, allow_pickle=True)

                logger.debug(f"Entries in {file_name}:\n{a.files}")
                for key in sorted(a):
                    logger.debug(
                        f"key: {key}|{type(key).__name__}|"
                        f"{type(a[key]).__name__}|{a[key]}")

                    if np.ndim(a[key]) == 0:
                        # scalar objects may be extracted with the item() method
                        fb.fil[0][key] = a[key].item()
                    else:
                        # array objects are converted to list first
                        fb.fil[0][key] = a[key].tolist()
            elif file_type == 'pkl':
                fb.fil[0] = pickle.load(f)
            else:
                logger.error('Unknown file type "{0}"'.format(file_type))
                err = True
            if not err:
                # sanitize values in filter dictionary, keys are ok by now
                for k in fb.fil[0]:
                    # Bytes need to be decoded for py3 to be used as keys later on
                    if type(fb.fil[0][k]) == bytes:
                        fb.fil[0][k] = fb.fil[0][k].decode('utf-8')
                    if fb.fil[0][k] is None:
                        logger.warning("Entry fb.fil[0][{0}] is empty!".format(k))

                logger.info('Successfully loaded filter\n\t"{0}"'.format(file_name))
                dirs.last_file_name = file_name
                dirs.last_file_dir = os.path.dirname(file_name)  # update working dir
                dirs.last_file_type = file_type  # save file type
                # emit signal -> filter loaded
                self.emit({'data_changed': 'filter_loaded'})

    except IOError as e:
        logger.error("Failed loading {0}!\n{1}".format(file_name, e))
    except Exception as e:
        logger.error("Unexpected error:\n{0}".format(e))
        fb.fil[0] = fb.fil[1]  # restore backup


# ------------------------------------------------------------------------------
def save_filter(self):
    """
    Save filter as zipped binary numpy array or pickle object
    """
    file_types = ("npz", "pkl")
    file_filters, last_file_filter = create_file_filters(file_types)

    dlg = QFileDialog(self)
    dlg.setWindowTitle("Save filter as")
    dlg.setDirectory(dirs.last_file_dir)
    dlg.setAcceptMode(QFileDialog.AcceptSave)  # set dialog to "file save" mode
    dlg.setNameFilter(file_filters)

    if last_file_filter:
        dlg.selectNameFilter(last_file_filter)  # filter selected in last file dialog

    if dlg.exec_() == QFileDialog.Accepted:
        file_name = dlg.selectedFiles()[0]  # pick only first selected file
        # sel_filt = dlg.selectedNameFilter()  # selected file filter
    else:
        return -1  # operation cancelled

    file_type = os.path.splitext(file_name)[-1].strip('.')  # slice off file extension

    err = False
    try:
        with io.open(file_name, 'wb') as f:
            if file_type == 'npz':
                np.savez(f, **fb.fil[0])
            elif file_type == 'pkl':
                pickle.dump(fb.fil[0], f)  # save in default pickle version
            else:
                err = True
                logger.error('Unknown file type "{0}"'.format(file_type))

        if not err:
            logger.info(f'Filter saved as\n\t"{file_name}"')
            dirs.last_file_name = file_name
            dirs.last_file_dir = os.path.dirname(file_name)  # save new dir
            dirs.last_file_type = file_type  # save file type

    except IOError as e:
        logger.error('Failed saving "{0}"!\n{1}'.format(file_name, e))


# ==============================================================================
if __name__ == '__main__':
    pass
