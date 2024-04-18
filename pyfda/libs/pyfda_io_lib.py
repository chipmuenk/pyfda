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
import copy
import csv
import wave
import datetime
import warnings
from typing import TextIO, Tuple  # replace by built-in tuple from Py 3.9

import pickle
import json

import numpy as np
from scipy.io import loadmat, savemat, wavfile

try:
    import xlwt
except ImportError:
    xlwt = None
try:
    import xlsx
except ImportError:
    xlsx = None

from pyfda.libs.pyfda_lib import (
    safe_eval, lin2unit, pprint_log, iter2ndarray, sanitize_imported_dict)
from pyfda.libs.pyfda_qt_lib import qget_selected, popup_warning

import pyfda.libs.pyfda_fix_lib as fx
from pyfda.pyfda_rc import params
import pyfda.libs.pyfda_dirs as dirs
import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals
from pyfda.version import __version__

from .compat import QFileDialog

import logging
logger = logging.getLogger(__name__)


# ##############################################################################
# Include this version number as `'_id': ('pyfda', FILTER_FILE_VERSION)` when saving
# filter files and test for the version when loading filter files.
FILTER_FILE_VERSION = 1

# file filters for the QFileDialog object are constructed from this dict
file_filters_dict = {
    'cmsis': 'CMSIS DSP FIR or IIR SOS coefficients',
    'coe': 'Xilinx FIR coefficients format',
    'csv': 'Comma / Tab Separated Values',
    'json': 'Javascript Object Notation',
    'mat': 'Matlab-Workspace',
    'npy': 'Binary Numpy Array',
    'npz': 'Zipped Binary Numpy Array',
    'pkl': 'Pickled data',
    'txt': 'Microsemi FIR coefficient format',
    'vhd': 'VHDL package or architecture',
    'wav': 'WAV audio format',
    'xls': 'Excel Worksheet',
    'xlsx': 'Excel 2007 Worksheet'
    }

# regex pattern that yields true in a re.search() when only the specified
#  characters (numeric, "eEjJ(),.+-" and blank / line breaks) are contained
pattern_num_chars = re.compile('[eEjJ()0-9,\.\+\-\s]+$')
# regex pattern that identifies characters and their position *not* specified
pattern_no_num = re.compile('(?![eEjJ()0-9,\.\+\-\s])')

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
def extract_file_ext(file_type: str, return_list: bool = False) -> str:
    """
    Extract list with file extension(s), e.g. '.vhd' from type description
    'VHDL (\*.vhd)' returned by QFileDialog. Depending on the OS, this may be the
    full file type description or just the extension like '(\*.vhd)'.

    When `file_type` contains no '(', the passed string is returned unchanged.

    For an explanation of the RegEx, see the docstring for `prune_file_ext`.

    Parameters
    ----------
    file_type : str

    return_list: bool (default = False)
       When True, return a list with file extensions (possibly empty or with only one
       element), when False (default) only return the first element (a string)

    Returns
    -------
    str or list of str
        The file extension between ( ... ), e.g. 'csv' or the list of file extension
        or the unchanged input argument `file_type` when no '('  was contained.

    """
    if "(" in file_type:
        ext_list = re.findall('\([^\)]+\)', file_type)  # extract '(*.txt)'
        file_type_list = [t.strip('(*.)') for t in ext_list]  # remove '(*.)'
        if return_list:
            return file_type_list
        else:
            return str(file_type_list[0])
    else:
        return file_type


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
        `"Comma / Tab Separated Values (*.csv);; Audio (*.wav *.mp3)"`. By default,
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
def select_file(parent: object, title: str = "", mode: str = "r",
                file_types: Tuple[str, ...] = ('csv', 'txt')) -> Tuple[str, str]:
    """
    Select a file from a file dialog box for either reading or writing and return
    the selected file name and type.

    Parameters
    ----------
    title : str
        title string for the file dialog box (e.g. "Filter Coefficients"),

    mode : str
        file access mode, must be either "r" or "w" for read / write access

    file_types : tuple of str
        supported file types, e.g. `('txt', 'npy', 'mat') which need to be keys
        of `file_filters_dict`

    Returns
    -------
    file_name: str
        Fully qualified name of selected file. `None` when operation has been
        cancelled.

    file_type: str
        File type, e.g. 'wav'. `None` when operation has been cancelled.
    """

    file_filters, last_file_filter = create_file_filters(file_types=file_types)

    # check whether last file type is in the list of file types for the current
    # operation, otherwise delete last_file_filter
    if extract_file_ext(last_file_filter) not in file_types:
        last_file_filter = ""

    dlg = QFileDialog(parent)  # create instance for QFileDialog
    dlg.setDirectory(dirs.last_file_dir)
    if mode in {"r", "rb"}:
        if title == "":
            title = "Import"
        dlg.setWindowTitle(title)
        dlg.setAcceptMode(QFileDialog.AcceptOpen)  # set dialog to "file open" mode
        dlg.setFileMode(QFileDialog.ExistingFile)
    elif mode in {"w", "wb"}:
        if title == "":
            title = "Export"
        dlg.setWindowTitle(title)
        dlg.setAcceptMode(QFileDialog.AcceptSave) # set dialog to "file save" mode
        dlg.setFileMode(QFileDialog.AnyFile)
    else:
        logger.error(f"Unknown mode '{mode}'")
        return None, None

    dlg.setNameFilter(file_filters)  # pass available file filters
    # dlg.setDefaultSuffix(file_types[0])  # default suffix when none is given
    if last_file_filter:
        dlg.selectNameFilter(last_file_filter)  # filter selected in last file dialog

    if dlg.exec_() == QFileDialog.Accepted:
        file_name = dlg.selectedFiles()[0]  # pick only first selected file
        file_type = os.path.splitext(file_name)[-1].strip('.')
        sel_filt = dlg.selectedNameFilter()  # selected file filter

        if file_type == "":
            # No file type specified, add the type from the file filter
            file_type = extract_file_ext(sel_filt)
            file_name = file_name + '.' + file_type

        dirs.last_file_name = file_name
        dirs.last_file_dir = os.path.dirname(file_name)
        dirs.last_file_type = file_type
    else:  # operation cancelled
        file_name = None
        file_type = None

    return file_name, file_type


# ------------------------------------------------------------------------------
def qtable2csv(table: object, data: np.ndarray, zpk=False,
               formatted: bool = False) -> str:
    """
    Transform QTableWidget data to CSV formatted text

    Parameters
    ----------

    table : object
            Instance of QTableWidget

    data:   object
            Instance of the numpy variable shadowing table data

    zpk: bool
            when True, append the gain (`data[2]`) to the table

    formatted: bool
        When True, copy data as formatted in the table, otherwise copy from the
        model ("shadow").


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
            when ``clipboard == True``, copy data to clipboard, else use a file.

    Returns
    -------

    None
        Nothing, text is exported to clipboard or to file via ``export_fil_data``
    """

    text = ""
    if params['CSV']['header'] == 'on':
        use_header = True
    elif params['CSV']['header'] in {'off', 'auto'}:
        use_header = False
    else:
        logger.error(
            f"Unknown key '{params['CSV']['header']}' for params['CSV']['header']")

    if not params['CSV']['orientation'] in {'rows', 'cols', 'auto'}:
        logger.error(
            f"Unknown key '{params['CSV']['orientation']}' for "
            "params['CSV']['orientation']")

    delim = params['CSV']['delimiter'].lower()
    if delim == 'auto':  # 'auto' doesn't make sense when exporting
        delim = ","
    cr = params['CSV']['lineterminator']

    num_cols = table.columnCount()  # visible columns of table
    num_rows = table.rowCount()  # visible rows of data

    # TODO: This shouldn't be neccessary anymore
    # If gain is just a scalar, convert to a list with one item
    if zpk and np.isscalar(data[2]):
        data[2] = [data[2]]

    sel = qget_selected(table, reverse=False)['sel']

    # ==========================================================================
    # Copy data from the model in float format:
    # ==========================================================================
    if not formatted:
        if params['CSV']['orientation'] == 'rows':  # write table in row format
            for c in range(num_cols):  # for each column (b,a or z,p) ...
                if use_header:  # ... start text line with table header and ...
                    text += table.horizontalHeaderItem(c).text() + delim
                for r in range(num_rows):  # ... construct text line from data.
                    text += str(safe_eval(data[c][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr  # finish text line, remove last delimiter
            if zpk:  # add another text line with the gain items
                if use_header:
                    text += 'k' + delim
                for r in range(len(data[2])):
                    text += str(safe_eval(data[2][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr  # finish text line, remove last delimiter

        else:  # write table in column format
            if use_header:  # construct a text line with the table header(s)
                for c in range(num_cols):
                    text += table.horizontalHeaderItem(c).text() + delim
                if zpk:
                    text += 'k' + delim
                text = text.rstrip(delim) + cr  # finish text line, remove last delimiter
            for r in range(num_rows):  # for each data row ...
                # ... construct a text line from the columns (b,a or z,p)
                for c in range(num_cols):
                    text += str(safe_eval(data[c][r], return_type='auto')) + delim
                if zpk and r < len(data[2]):  # add another item with a gain value
                    text += str(safe_eval(data[2][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr  # finish text line, remove last delimiter

    # =======================================================================
    # Copy table in displayed format:
    # =======================================================================
    else:
        if params['CSV']['orientation'] == 'rows':  # write table in row format
            for c in range(num_cols):  # for each column (b,a or z,p) ...
                if use_header:  # ... start text line with table header and ...
                    text += table.horizontalHeaderItem(c).text() + delim
                for r in range(num_rows):  # ... construct text line from table column
                    item = table.item(r, c)
                    if item and item.text() != "":
                        text += table.itemDelegate().text(item).lstrip(" ") + delim
                    else:
                        text += "0" + delim
                text = text.rstrip(delim) + cr  # finish text line, remove last delimiter
            if zpk:  # add another text line with a gain item from the data
                if use_header:
                    text += 'k' + delim
                for r in range(len(data[2])):
                    text += str(safe_eval(data[2][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr  # finish text line, remove last delimiter

        else:  # write table in column format
            if use_header: # construct a text line with the table header(s)
                for c in range(num_cols):
                    text += table.horizontalHeaderItem(c).text() + delim
                if zpk:
                    text += 'k' + delim
                text = text.rstrip(delim) + cr
            for r in range(num_rows):  # for each table row ...
                # ... construct a text line from the table columns (b,a or z,p)
                for c in range(num_cols):
                    item = table.item(r, c)
                    if item and item.text() != "":
                        text += table.itemDelegate().text(item).lstrip(" ") + delim
                    else:
                        text += "0" + delim
                if zpk and r < len(data[2]):  # add another item with a gain value
                    text += str(safe_eval(data[2][r], return_type='auto')) + delim
                text = text.rstrip(delim) + cr

    text = text.rstrip(cr)  # delete CR after last row
    return text


# ==============================================================================
#     # Here 'a' is the name of numpy array and 'file' is the filename to write to.
#
#     # If you want to write in column:
#     for x in np.nditer(a.T, order='C'):
#             file.write(str(x))
#             file.write("\n")
#
#     # If you want to write in row:
#     writer= csv.writer(file, delimiter=',')
#     for x in np.nditer(a.T, order='C'):
#             row.append(str(x))
#     writer.writerow(row)
#
# ==============================================================================


# ------------------------------------------------------------------------------
def data2array(parent: object, fkey: str, title: str = "Import", as_str: bool = False):
    """
    Copy tabular data from clipboard or file to a numpy array

    Parameters
    ----------

    parent: object
            parent instance with a QFileDialog attribute.

    fkey: str
            Key for accessing data in *.npz file or Matlab workspace (*.mat)

    title: str
        title string for the file dialog box

    as_str: bool
        When True, return ndarray in raw str format, otherwise convert to float or complex

    Returns
    -------

    ndarray of str or None
        table data


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

    """
    if params['CSV']['destination'] == 'clipboard':  # data from clipboard
        text = fb.clipboard.text()
        logger.debug(
            f"Importing data from clipboard:\n{np.shape(text)}\n{text}")
        # pass handle to text and convert to numpy array:
        data_arr = csv2array(io.StringIO(text))

    else:  # data from file
        file_name, file_type = select_file(parent, title=title, mode="r",
                                   file_types=('csv', 'mat', 'npy', 'npz'))
        if file_name is None:  # operation cancelled or error
            return None
        else:  # file types 'csv', 'mat', 'npy', 'npz'
            data_arr = load_data_np(file_name, file_type, fkey, as_str = as_str)

    if data_arr is None:
            logger.error("Couldn't import data.")
    elif isinstance(data_arr, str):  # returned an error message instead of numpy data
        logger.error(
            "You shouldn't see this message!\n"
            f"Error importing data:\n\t{data_arr}")
        return None

    return data_arr

# ------------------------------------------------------------------------------
def csv2array(f: TextIO):
    """
    Convert comma-separated values from file or text
    to numpy array, taking into accout the settings of the CSV dict.

    Parameters
    ----------

    f: TextIO
        handle to file or file-like object, e.g.

    >>> f = open(file_name, 'r') # or
    >>> f = io.StringIO(text)

    Returns
    -------

    data_arr: ndarray
        numpy array of str with table data from file or `None` when import was
        unsuccessful

    Read data as it is, splitting each row into the column items when:

    - `CSV_dict['orientation'] == cols` or
    - `CSV_dict['orientation'] == auto` and cols <= rows:

    Transpose data when:

    - `CSV_dict['orientation'] == rows` or
    - `CSV_dict['orientation'] == auto` and cols > rows:

    `np.shape(data)` returns rows, columns

    While opening a file, the `newline` parameter can be used to
    control how universal newlines works (it only applies to text mode).
    It can be None, '', '`\\n`', '`\\r`', and '`\\r\\n`'. It works as follows:

    - Input: If `newline == None`, universal newlines mode is enabled. Lines in
      the input can end in '\\n', '\\r', or '\\r\\n', and these are translated into
      '\\n' before being returned to the caller. If it is '', universal newline
      mode is enabled, but line endings are returned to the caller untranslated.
      If it has any of the other legal values, input lines are only terminated
      by the given string, and the line ending is returned to the caller untranslated.

    - On output, if newline is None, any '\\n' characters written are translated
      to the system default line separator, os.linesep. If newline is '',
      no translation takes place. If newline is any of the other legal values,
      any '\\n' characters written are translated to the given string.

    Example: convert from Windows-style line endings to Linux:

    .. code-block:: python

        fileContents = open(filename,"r").read()
        f = open(filename,"w", newline="\\n")
        f.write(fileContents)
        f.close()

    https://pythonconquerstheuniverse.wordpress.com/2011/05/08/newline-conversion-in-python-3/

    """

    # throw an error (instead of just issueing a deprecation warning) when trying to
    # create a numpy array from nested ragged sequences. This error can then be
    # caught easily.
    warnings.filterwarnings('error', category=np.VisibleDeprecationWarning)
    # ------------------------------------------------------------------------------
    # Get CSV parameter settings
    # ------------------------------------------------------------------------------
    csv2array.info_str = ""  # initialize function attribute
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

        if not CSV_dict['orientation'].lower() in {'auto', 'cols', 'rows'}:
            logger.error(
                f"Unknown key '{CSV_dict['orientation']}' for CSV_dict['orientation'], "
                "using column mode.")

        tab = CSV_dict['delimiter'].lower()
        cr = CSV_dict['lineterminator'].lower()

    except KeyError as e:
        logger.error(f"Dict 'params':\n{e}.")
        return None

    sample = ""

    # ------------------------------------------------------------------------------
    # Analyze CSV object
    # ------------------------------------------------------------------------------
    if header == 'auto' or tab == 'auto' or cr == 'auto':
        # test the first line for delimiters (of the given selection)
        sample = f.readline()
        f.seek(0)  # and reset the file pointer
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=['\t', ';', ',', '|', ' '])
        except csv.Error as e:
            logger.warning(f'CSV sniffing reported "{e}",\n'
                        'continuing with format "excel-tab"')
            dialect = csv.get_dialect('excel-tab')
    else:
        # fall back, alternatives: 'excel', 'unix':
        dialect = csv.get_dialect('excel-tab')

    if header == "auto":
        # yields True when a non-numeric character is detected, indicating a header:
        use_header = not pattern_num_chars.search(sample)
    elif header == 'on':
        use_header = True
    else:
        use_header = False

    delimiter = dialect.delimiter
    lineterminator = dialect.lineterminator
    quotechar = dialect.quotechar

    if tab != 'auto':
        delimiter = str(tab)

    if cr != 'auto':
        lineterminator = str(cr)

    logger.info(f"Parsing CSV data with header = '{use_header}'\n"
                f"\tDelimiter = {repr(delimiter)} | Lineterm. = {repr(lineterminator)} "
                f"| quotechar = ' {quotechar} as '{f.__class__.__name__}'")

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
#    data_list = []
#    def process(line):
#        # split into lines (if not split yet):
#        data_list.append(line.split(lineterminator))
#
#     This will work nicely for any file size and you go through your file in just 1 pass.
#     This is typically how generic parsers will work.
#     (https://stackoverflow.com/questions/3277503/how-to-read-a-file-line-by-line-into-a-list)
# =============================================================================

    csv2array.info_str = f"'{repr(lineterminator)}' # '{repr(delimiter)}'"

    # ------- Read CSV file into a list --------------------
    data_list = []
    try:
        for row in data_iter:
            if row:  # only append non-empty rows
                data_list.append(row)
    except csv.Error as e:
        logger.error(f"Error during CSV import:\n{e}")
        return None

    if data_list == [] or data_list ==[""]:
        logger.error("Imported data is empty.")
        return None

    # ------- Convert list to an array of str --------------------
    try:
        data_arr = np.array(data_list)
    except np.VisibleDeprecationWarning:
        # prevent creation of numpy arrays from nested ragged sequences
        logger.error("Can't convert to array, columns have different lengths.")
        return None
    except (TypeError, ValueError) as e:
        logger.error(f"{e}\nData = {pprint_log(data_list)}")
        return None

    if np.ndim(data_arr) == 0:
        logger.error(f"Imported data is a scalar: '{data_arr}'")
        return None

    elif np.ndim(data_arr) == 1:
        if len(data_arr) < 2:
            logger.error(f"Not enough data: '{data_arr}'")
            return None
        else:
            return data_arr

    elif np.ndim(data_arr) == 2:
        rows, cols = np.shape(data_arr)
        # The check for max. number of columns has to be handled downstream
        # logger.info(f"cols = {cols}, rows = {rows}, data_arr = {data_arr}\n")
        # if cols > max_cols and rows > max_cols:
        #     logger.error(f"Unsuitable data shape {np.shape(data_arr)}")
        #     return None
        if params['CSV']['orientation'] == 'rows'\
                or params['CSV']['orientation'] == 'auto' and cols > rows:
            # returned table is transposed, swap cols and rows
            logger.info(f"Building transposed table with {cols} row(s) and {rows} columns.")
            csv2array.info_str = "T:" + csv2array.info_str
            if use_header:
                logger.info(f"Skipping header {data_arr.T[0]}")
                return data_arr.T[1:]
            else:
                return data_arr.T
        else:  # column format
            logger.info(f"Building table with {cols} column(s) and {rows} rows.")
            if use_header:
                logger.info(f"Skipping header {data_arr[0]}")
                return data_arr[1:]
            else:
                return data_arr
    else:
        logger.error(f"Unsuitable data shape: ndim = {np.ndim(data_arr)}, "
                     f"shape = { np.shape(data_arr)}")
        return None

#-------------------------------------------------------------------------------
def read_csv_info_old(filename):
#-------------------------------------------------------------------------------
    """
    DON'T USE ANYMORE!
    Get infos about the size of a csv file without actually loading the whole
    file into memory.

    See
    https://stackoverflow.com/questions/64744161/best-way-to-find-out-number-of-rows-in-csv-without-loading-the-full-thing
    """
    file_size = os.path.getsize(filename)
    logger.info(f"File Size is {file_size} bytes")

    sniffer = csv.Sniffer()

    with open(filename) as f:
        first_line = f.readline()
        sample = first_line + f.readline()
        # pattern search returns true when only allowed characters are found
        # when the first line contains other characters, it is assumed that this
        # is a header
        has_header = not pattern_num_chars.search(sample)
        # if has_header:
        #      logger.warning(pattern_no_num.search(sample))
        dialect = sniffer.sniff(sample)
        delimiter = dialect.delimiter
        lineterminator = repr(dialect.lineterminator)

        nchans = first_line.count(delimiter) + 1  # number of columns
        # count rows in file
        f.seek(0)
        N = sum(1 for row in f)  # f isfileobject (csv.reader)  # number of rows

    del f

    logger.info(f"Terminator = '{lineterminator}', Delimiter = '{delimiter}', "
                f"RowCount = {N}, Header={has_header}")

    if not params['CSV']['orientation'] in {'rows', 'cols', 'auto'}:
        logger.error(
            f"Unknown key '{params['CSV']['orientation']}' for "
            "params['CSV']['orientation']")
    if params['CSV']['orientation'] == 'auto' and (N < nchans)\
        or params['CSV']['orientation'] == 'rows':  # swap rows and columns
        N, nchans = nchans, N
        row_mode = True
        transpose = "T #"
    else:
        row_mode = False
        transpose = ""

    if N < 2:
        logger.error(f"No suitable CSV file, has only {N} data entries.")
        return -1

    # file is ok, copy local variables to function attributes
    read_csv_info.row_mode = row_mode
    read_csv_info.file_size = file_size
    read_csv_info.N = N
    read_csv_info.nchans = nchans
    read_csv_info.info_str = f"{transpose} '{lineterminator}' # '{delimiter}'"

    return 0

#-------------------------------------------------------------------------------
def read_wav_info(file):
    """
    Get infos about the following properties of a wav file without actually
    loading the whole file into memory. This is achieved by reading the
    header.
    """
    # https://wavefilegem.com/how_wave_files_work.html
    # https://stackoverflow.com/questions/7833807/get-wav-file-length-or-duration
    # http://soundfile.sapp.org/doc/WaveFormat/
    # https://ccrma.stanford.edu/courses/422/projects/WaveFormat/
    def str2int(s: str) -> int:
        """ convert argument from str `s` in little endian format to int """
        int = 0
        for i in range(len(s)):
             int = int + ord(s[i]) * pow(256, i)
        return int

    f = open(file,'r', encoding='latin-1')
    # Get the file size in bytes
    file_size = os.path.getsize(file)
    if file_size < 44:  # minimum length for WAV file due to header
        logger.error(f"Not a wav file: Filesize is only {file_size} bytes!")
        return -1
    HEADER = f.read(44)  # read complete header

    RIFF = HEADER[:4]  # file pos. 0
    WAVE = HEADER[8:12]  # pos. 8
    if RIFF != "RIFF" or WAVE != "WAVE":
        logger.error("Not a wav file: 'RIFF' or 'WAVE' id missing in file header.")
        return -1

    # Pos. 12: String 'fmt ' marks beginning of format subchunk
    FMT = HEADER[12:16]  # f.read(4)
    if FMT != "fmt ":  # pos. 12
        logger.error(f"Invalid format header '{FMT}' instead of 'fmt'!")
        return -1

    # Pos. 16: Size of subchunk with format infos in bytes, 16 for Int., 18 for float
    fmt_chnk_size1 = str2int(HEADER[16:20])
    if fmt_chnk_size1 not in {16, 18}:
        logger.error(f"Invalid size {fmt_chnk_size1} of format subchunk!")
        return -1

    # Pos. 20: Audio encoding format, must be 1 for uncompressed PCM
    encoding = str2int(HEADER[20:22])
    if encoding == 1:
        sample_format = "int"  # Integer PCM
    elif encoding == 3:
        sample_format = "float"  # IEEE Float PCM
    else:
        logger.error(f"Invalid audio encoding {encoding}, only uncompressed "
                     "PCM supported!")
        sample_format = ""
        return -1

    # Pos. 22: Number of channels
    nchans = str2int(HEADER[22:24])

    f.seek(24)
    # Pos. 24: Sampling rate f_S
    f_S = str2int(f.read(4))

    # Pos. 28: Byte rate = f_S * n_chans * Bytes per sample
    byte_rate = str2int(f.read(4))

    # Pos. 32: Block align, # of bytes per sample incl. all channels
    block_align = str2int(f.read(2))

    # Pos. 34: Bits per sample, WL = wordlength in bytes
    bits_per_sample = str2int(f.read(2))

    if sample_format == "float":
        # Format subchunk is 18 bytes long for float samples, hence file pointer
        # has to be advanced by two bytes
        _ = f.read(2)

        # ###################### FACT Subchunk ###################################
        # The fact chunk indicates how many sample frames are in the file. For
        # integer formats the tag it’s optional; otherwise it’s required. For float
        # PCM, calculation is performed exactly as for integer PCM, hence, it is not
        # evaluated here.
        FACT = f.read(12)

    # ###################### DATA Subchunk #######################################
    # String 'data' marks beginning of data subchunk
    DATA = f.read(4)
    if DATA != "data":
        logger.error(f"Invalid data header '{DATA}' instead of 'data'!")
        return -1

    # -- Function attributes that are accessible from outside
    # ------------------------------------------------------------
    read_wav_info.file_size = file_size

    if sample_format == "int":
        if bits_per_sample == 8:
            read_wav_info.sample_format = "uint8"
        elif bits_per_sample == 16:
            read_wav_info.sample_format = "int16"
        elif bits_per_sample == 24:
            read_wav_info.sample_format = "int24"
        elif bits_per_sample == 32:
            read_wav_info.sample_format = "int32"
        else:
            logger.error("Unsupported integer sample format with {bits_per_sample} "
                         "bits per sample.")
            return -1
    else:
        if bits_per_sample == 32:
            read_wav_info.sample_format = "Float32"
        elif bits_per_sample == 64:
            read_wav_info.sample_format = "Float64"
        else:
            logger.error("Unsupported float sample format with {bits_per_sample} "
                         "bits per sample.")
            return -1

    read_wav_info.WL = bits_per_sample // 8  # Wordlength in bytes

    # Pos. 40 or 42: Total number of samples per channel
    read_wav_info.N = str2int(f.read(4)) // (nchans * read_wav_info.WL)

    read_wav_info.nchans = nchans  # number of channels

    read_wav_info.f_S = f_S  # sampling rate in Hz

    # duration of the data in milliseconds
    read_wav_info.ms = read_wav_info.N * 1000 / (f_S * nchans)

    return 0

# ------------------------------------------------------------------------------
def load_data_np(file_name: str, file_type: str, fkey: str = "", as_str: bool = False
                 )-> np.ndarray:
    """
    Import data from a file and convert it to a numpy array.

    Parameters
    ----------
    file_name: str
        Full path and name of the file to be imported

    file_type: str
        File type, currently supported are 'csv', 'mat', 'npy', 'npz, 'txt', 'wav'.

    fkey : str
        Key for accessing data in *.npz or Matlab workspace (*.mat) files with
        multiple entries.

    as_str: bool
        When False (default), try to convert results to ndarray of float or complex.
        Otherwise, return an ndarray of str.

    Returns
    -------
    ndarray of float / complex / int or str
        Data from the file (ndarray) or None (error)
    """
    load_data_np.info_str = "" # function attribute for file infos
    if file_name is None:  # error or operation cancelled
        return -1

    try:
        if file_type == 'wav':
            f_S, data_arr = wavfile.read(file_name, mmap=False)
            # data_arr is 1D for single channel (mono) files and
            # 2D otherwise (n_chans, n_samples)
            fb.fil[0]['f_s_wav'] = f_S

        elif file_type in {'csv', 'txt'}:
            with open(file_name, 'r', newline=None) as f:
                data_arr = csv2array(f)
                load_data_np.info_str = csv2array.info_str
                # data_arr = np.loadtxt(f, delimiter=params['CSV']['delimiter'].lower())
                if data_arr is None:
                    # an error has occurred
                    logger.error(f"Error loading file '{file_name}'")
                    return None
                elif isinstance(data_arr, str):
                    # returned an error message instead of numpy data:
                    load_data_np.info_str = ""
                    logger.error(f"You shouldn't see this message!! \n"
                                 "Error loading file '{file_name}':\n{data_arr}")
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
                    if fkey in{"", None}:
                        data_arr = fdict  # pick the whole array
                    elif fkey not in fdict:
                        raise IOError(
                            f"Key '{fkey}' not in file '{file_name}'.\n"
                            f"Keys found: {fdict.files}")
                    else:
                        data_arr = fdict[fkey]  # pick the array `fkey` from the dict
                else:
                    logger.error(f'Unknown file type "{file_type}"')
                    return None

        if not as_str:
            try:  # try to convert array elements to float
                data_arr = data_arr.astype(float)
            except ValueError as e:
                try: # try to convert array elements to complex
                    data_arr = data_arr.astype(complex)
                except ValueError:
                    logger.error(f"{e},\n\tconversion to float and complex failed.")
                    return None

        logger.info(
            f'Successfully imported file "{file_name}"\n{pprint_log(data_arr, N=5)}')
        return data_arr  # returns numpy array of type string or float/complex

    except (IOError, KeyError) as e:
        logger.error("Failed loading {0}!\n{1}".format(file_name, e))
        return None


# ------------------------------------------------------------------------------
def save_data_np(file_name: str, file_type: str, data: np.ndarray,
                 f_S: int = 1, fmt: str = '%f') -> int:
    """
    Save numpy ndarray data to a file in wav or csv format

    Parameters
    ----------
    file_name: str
        Full path and name of the file to be imported

    file_type: str
        File type, currently supported are 'csv' or 'wav'

    data : np.ndarray
        Data to be saved to a file. The data dtype (uint8, int16, int32, float32)
        determines the bits-per-sample and PCM/float of the WAV file

    f_S : int (optional)
        Sampling frequency (only used for WAV file format), only integer sampling
        frequencies are supported by the WAV format.

    fmt : str (optional)
        Optional, default '%f'. Format string, only used for exporting data in CSV
        format. Other options are e.g. '%1.2f' for reduced number of digits, '%d' for
        integer format or '%s' for strings.

    Returns
    -------
    0 for success, -1 for file cancel or error
    """
    # file_name, file_type = select_file(parent, title=title, mode='wb', file_types=('wav'))

    if file_name is None:  # error or operation cancelled
        return -1
    elif np.ndim(data) < 1 or np.ndim(data) > 2:
        logger.error(f"Unsuitable data format for a wav file, ndim = {np.ndim(data)}.")
        logger.error(data)
        return -1
    try:
        if file_type == 'wav':
            f_S_int = int(abs(f_S))
            if f_S_int == 0:
                f_S_int = 1
            if f_S != f_S_int:
                logger.warning(
                    "Only integer sampling frequencies can be used for WAV files,\n"
                    f"sampling frequency has been changed to f_S = {f_S_int}")

            # audio = data.T  # transpose data, needed?
            wavfile.write(file_name, f_S_int, data)
            # To write multiple-channels, use a 2-D array of shape (Nsamples, Nchannels).

        elif file_type == 'csv':
            delimiter = params['CSV']['delimiter'].lower()
            if delimiter == 'auto':
                delimiter = ','
            np.savetxt(file_name, data, fmt=fmt, delimiter=delimiter)
            # TODO: Integer formats like int16 should be stored as integers
        else:
            logger.error(f"File type {file_type} not supported!")
            return -1

        logger.info(f'Saved data as\n\t"{file_name}".')
        return 0


    except IOError as e:
        logger.error(f'Failed saving "{file_name}"!\n{e}\n')
        return -1

# ------------------------------------------------------------------------------
def write_wav_frame(parent, file_name, data: np.array, f_S = 1,
                    title: str = "Export"):
    """
    Export a frame of data in wav format

    Parameters
    ----------
    parent: handle to calling instance for creating file dialog instance

    data: np.array
        data to be exported

    title: str
        title string for the file dialog box (e.g. "audio data ")

    """
    file_name, file_type = select_file(parent, title=title, mode='wb', file_types=('wav'))
    if file_name is None:
        return None  # file operation cancelled or other error

    try:
        if np.ndim(data) == 1:  # mono
            audio = data
            n_chan = 1
        elif np.ndim(data) != 2:
            logger.error(f"Unsuitable data format, ndim = {np.ndim(data)}.")
            return
        elif np.shape(data)[1] != 2:
            logger.error(f"Unsuitable number of channels = {np.shape(data)[1]}")
            return
        else:
            audio = data.T  # transpose data
            n_chan = np.shape(data)[1]
            # audio = np.array([left_channel, right_channel]).T
        with wave.open(file_name, "w") as f:
            # 2 Channels.
            f.setnchannels(n_chan)
            # 2 bytes per sample.
            f.setsampwidth(2)
            f.setframerate(f_S)
            f.writeframes(audio.tobytes())
        with open(file_name, 'w', encoding="utf8", newline='') as f:
                        f.write(data)

        logger.info(f'Filter saved as\n\t"{file_name}"')

    except IOError as e:
        logger.error(f'Failed saving "{file_name}"!\n{e}\n')


# ------------------------------------------------------------------------------
def export_fil_data(parent: object, data: str, fkey: str = "", title: str = "Export",
                file_types: Tuple[str, ...] = ('csv', 'mat', 'npy', 'npz')):
    """
    Export filter coefficients or pole/zero data in various formats, file name and type
    are selected via the ui.

    Parameters
    ----------
    parent: handle to calling instance for creating file dialog instance

    data: str
        formatted as CSV data, i.e. rows of elements separated by 'delimiter',
        terminated by 'lineterminator'. Some data formats

    fkey: str
        Key for accessing data in ``*.npz`` or Matlab workspace (``*.mat``) file.
        When fkey == 'ba', exporting to FPGA coefficients format is enabled.

    title: str
        title string for the file dialog box (e.g. "filter coefficients ")

    file_types: tuple of strings
        file extension (e.g. `(csv)` or list of file extensions (e.g. `(csv, txt)`
        which are used to create a file filter.
    """
    # logger.debug(
    #     f"export data: type{type(data)}|dim{np.ndim(data)}|"
    #     f"shape{np.shape(data)}\n{data}")

    # add file types for coefficients and a description text for messages.
    if fkey == 'ba':
        if fb.fil[0]['ft'] == 'FIR':
            file_types += ('coe', 'vhd', 'txt')
        else:
            file_types += ('cmsis',)
        description = "Coefficient"
    else:
        description = "Pole / zero"

    # Add file types when Excel modules are available:
    if xlwt is not None:
        file_types += ('xls',)
    if xlsx is not None:
        file_types += ('xlsx',)

    file_name, file_type = select_file(parent,title=title, mode='wb',
                                       file_types=file_types)
    if file_name is None:
        return None  # file operation cancelled or other error

    err = False

    try:
        if file_type == 'csv':
            with open(file_name, 'w', encoding="utf8", newline='') as f:
                f.write(data)
        elif file_type in {'coe', 'txt', 'vhd', 'cmsis'}:  # text / string formats
            with open(file_name, 'w', encoding="utf8") as f:
                if file_type == 'coe':
                    err = export_coe_xilinx(f)
                elif file_type == 'txt':
                    err = export_coe_microsemi(f)
                elif file_type == 'vhd':
                    err = export_coe_vhdl_package(f)
                elif file_type == 'cmsis':
                    err = export_coe_cmsis(f)
                else:
                    logger.error(f'Unknown file extension "{file_type}')
                    return None

        else:  # binary formats, storing numpy arrays
            np_data = csv2array(io.StringIO(data))  # convert csv data to numpy array
            if isinstance(np_data, str):
                # returned an error message instead of numpy data:
                logger.error(f"Error converting {description.lower()} data:\n{np_data}")
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
                            worksheet.write(row+1, col, data[col][row])  # columns
        #                    worksheet.write(row, col, coeffs[col][row])  # rows

                    # Insert an image - useful for documentation export ?!.
        #            worksheet.insert_image('B5', 'logo.png')

                    workbook.close()

                else:
                    logger.error(f'Unknown file type "{file_type}"')
                    err = True

        if not err:
            logger.info(f'{description} data saved as\n\t"{file_name}"')

    except IOError as e:
        logger.error('Failed saving "{0}"!\n{1}\n'.format(file_name, e))

        # Download the Simple ods py module:
        # http://simple-odspy.sourceforge.net/
        # http://codextechnicanum.blogspot.de/2014/02/write-ods-for-libreoffice-calc-from_1.html


# ------------------------------------------------------------------------------
def coe_header(title: str) -> str:
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
        f"{title}\n"
        f"Generated by pyfda {__version__} (https://github.com/chipmuenk/pyfda)\n\n")
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
def export_coe_xilinx(f: TextIO) -> bool:
    """
    Save FIR filter coefficients in Xilinx coefficient format as file '\*.coe', specifying
    the number base and the quantized coefficients (decimal or hex integer).

    Returns error status (False if the file was saved successfully)
    """
    qc = fx.Fixed(fb.fil[0]['fxq']['QCB'])  # instantiate fixpoint object

    if qc.q_dict['WF'] != 0  and fb.fil[0]['qfrmt'] != 'qint':
        logger.error("Fractional formats are not supported!")
        return True

    if fb.fil[0]['fx_base'] == 'hex':  # select hex format
        coe_radix = 16
    if fb.fil[0]['fx_base'] == 'bin':  # select binary format
        coe_radix = 2
    else:
        logger.warning(f"Coefficients in {fb.fil[0]['fx_base']} format are "
                       f'not supported in COE files, converting to decimal format.')
        fb.fil[0]['fx_base'] =  'dec'  # select decimal format in all other cases
        coe_radix = 10

    # Quantize coefficients to decimal / hex integer format, return an array of strings
    bq = qc.float2frmt(fb.fil[0]['ba'][0])

    exp_str = "; " + coe_header(
        "XILINX CORE Generator(tm) Distributed Arithmetic FIR filter coefficient (.COE) file").replace("\n", "\n; ")

    exp_str += "\nRadix = {0};\n".format(coe_radix)
      # quantized wordlength
    exp_str += f"Coefficient_width = {qc.q_dict['WI'] + qc.q_dict['WF'] + 1};\n"
    coeff_str = "CoefData = "
    for b in bq:
        coeff_str += str(b) + ",\n"
    exp_str += coeff_str[:-2] + ";"  # replace last "," by ";"

    f.write(exp_str)

    return False


# ------------------------------------------------------------------------------
def export_coe_microsemi(f: TextIO) -> bool:
    """
    Save FIR filter coefficients in Microsemi coefficient format as file '\*.txt'.
    Coefficients have to be in integer format, the last line has to be empty.
    For (anti)symmetric filter only one half of the coefficients must be
    specified?
    """
    qc = fx.Fixed(fb.fil[0]['fxq']['QCB'])  # instantiate fixpoint object

    if qc.q_dict['WF'] != 0  and fb.fil[0]['qfrmt'] != 'qint':
        logger.error("Fractional formats are not supported!")
        return True

    if fb.fil[0]['fx_base'] != 'dec':
        fb.fil[0]['fx_base'] = 'dec'  # select decimal format in all other cases
        logger.warning('Converting to decimal coefficient format, other numeric formats '
                       'are not supported by Microsemi tools.')

    # Quantize coefficients to decimal integer format, returning an array of strings
    bq = qc.float2frmt(fb.fil[0]['ba'][0])

    coeff_str = "coefficient_set_1\n"
    for b in bq:
        coeff_str += str(b) + "\n"

    f.write(coeff_str)

    return False


# ------------------------------------------------------------------------------
def export_coe_vhdl_package(f: TextIO) -> bool:
    """
    Save FIR filter coefficients as a VHDL package '\*.vhd', specifying
    the number base and the quantized coefficients (decimal or hex integer).
    """
    qc = fx.Fixed(fb.fil[0]['fxq']['QCB'])  # instantiate fixpoint object
    if not fb.fil[0]['fx_sim'] or fb.fil[0]['qfrmt'] == 'qint'\
        or fb.fil[0]['qfrmt'] == 'qfrac' and qc.q_dict['WF'] == 0:
            pass
    else:
        logger.error("Fractional numbers are only supported for floats!")
        return True

    WO = fb.fil[0]['fxq']['QO']['WI'] + fb.fil[0]['fxq']['QO']['WF'] + 1

    if fb.fil[0]['fx_base'] == 'dec' or not fb.fil[0]['fx_sim']:
        pre = ""
        post = ""
    elif fb.fil[0]['fx_base'] == 'hex':
        pre = "#16#"
        post = "#"
    elif fb.fil[0]['fx_base'] == 'bin':
        pre = "#2#"
        post = "#"
    else:
        fb.fil[0]['fx_base'] = 'dec'  # select decimal format in all other cases
        pre = ""
        post = ""
        logger.warning(f"Coefficients in {fb.fil[0]['fx_base']} format are "
                       'not supported, converting to decimal format.')

    # Quantize coefficients to selected fixpoint format, returning an array of strings
    bq = qc.float2frmt(fb.fil[0]['ba'][0])

    exp_str = "-- " + coe_header(
        "VHDL FIR filter coefficient package file").replace("\n", "\n-- ")

    exp_str += "\nlibrary IEEE;\n"
    if not fb.fil[0]['fx_sim']:
        exp_str += "use IEEE.math_real.all;\n"
    exp_str += "USE IEEE.std_logic_1164.all;\n\n"
    exp_str += "package coeff_package is\n"
    exp_str += "constant n_taps: integer := {0:d};\n".format(len(bq)-1)
    if not fb.fil[0]['fx_sim']:
        exp_str += "type coeff_type is array(0 to n_taps) of real;\n"
    else:
        exp_str += "type coeff_type is array(0 to n_taps) of integer "
        exp_str += f"range {-1 << WO-1} to {(1 << WO-1) - 1};\n\n"
    exp_str += "constant coeff : coeff_type := "

    coeff_str = "(\n"
    for b in bq:
        coeff_str += "\t" + pre + str(b) + post + ",\n"
    exp_str += coeff_str[:-2] + ");\n\n"  # replace last "," by ");"

    exp_str += "end coeff_package;"

    f.write(exp_str)

    return False


# ------------------------------------------------------------------------------
def export_coe_TI(f: TextIO) -> None:
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


# ------------------------------------------------------------------------------
def export_coe_cmsis(f: TextIO) -> None:
    """
    Get coefficients in SOS format and delete 4th column containing the
    '1.0' of the recursive parts.

    See https://www.keil.com/pack/doc/CMSIS/DSP/html/group__BiquadCascadeDF1.html
    https://dsp.stackexchange.com/questions/79021/iir-design-scipy-cmsis-dsp-coefficient-format
    https://github.com/docPhil99/DSP/blob/master/MatlabSOS2CMSIS.m

    # TODO: check `scipy.signal.zpk2sos` for details concerning sos paring
    """
    sos_coeffs = np.delete(fb.fil[0]['sos'], 3, 1)

    delim = params['CSV']['delimiter'].lower()
    if delim == 'auto':  # 'auto' doesn't make sense when exporting
        delim = ","
    cr = params['CSV']['lineterminator']

    text = ""
    for r in range(np.shape(sos_coeffs)[0]):  # number of rows
        for c in range(5):  # always has 5 columns
            text += str(safe_eval(sos_coeffs[r][c], return_type='auto')) + delim
        text = text.rstrip(delim) + cr
    text = text.rstrip(cr)  # delete last CR

    f.write(text)

    return False


# ==============================================================================
def load_filter(self) -> int:
    """
    Load filter from zipped binary numpy array or (c)pickled object to
    filter dictionary
    """
    file_name, file_type = select_file(
        self, title="Load Filter", mode="rb", file_types = ("json", "npz", "pkl"))

    if file_name is None:
        return -1  # operation cancelled or some other error

    err = False
    fb.redo() # backup filter dict

    if file_type in {"npz", "pkl"}:
        try:
            with io.open(file_name, 'rb') as f:  # open in binary mode for npy and pkl
                if file_type == 'npz':
                    # array containing dict, dtype 'object':
                    arr = np.load(f, allow_pickle=True)

                    # convert arrays to lists and extract scalar objects
                    for key in sorted(arr):
                        if np.ndim(arr[key]) == 0:
                            # scalar objects may be extracted with the item() method
                            fb.fil[0][key] = arr[key].item()
                        else:
                            # array objects are converted to list first
                            fb.fil[0][key] = arr[key].tolist()
                else:  # file_type == 'pkl':
                    fb.fil[0] = pickle.load(f)

        except IOError as e:
            logger.error(f"Failed loading {file_name}!\n{e}")
            return -1

    elif file_type == 'json':
        try:
            with io.open(file_name, 'r') as f:  # open in text mode for json files
                fb.fil[0] = json.load(f)

        except IOError as e:
            logger.error(f"Failed loading {file_name}!\n{e}")
            return -1
    else:
        logger.error(f'Unknown file type "{file_type}"')
        err = True

    if '_id' not in fb.fil[0] or len(fb.fil[0]['_id']) != 2\
            or fb.fil[0]['_id'][0] != 'pyfda':
        msg = "This is no pyfda filter or an outdated file format! Load anyway?"
        err = not popup_warning(None, message=msg)

    elif fb.fil[0]['_id'][1] != FILTER_FILE_VERSION:
        msg = (
            f"The filter file has version {str(fb.fil[0]['_id'][1])} instead of "
            f"of required version {FILTER_FILE_VERSION}! Load anyway?")
        err = not popup_warning(None, message=msg)

    # Catch errors occurring during file opening
    if err:
        fb.undo()
        return -1

# --------------------
    try:
        keys_missing, keys_unsupported = sanitize_imported_dict(fb.fil[0])
        err_str = ""
        if keys_missing != []:
            # '\n'.join(...) converts list to multi-line string
            err_str += (
                f"The following {len(keys_missing)} key(s) have not been found in "
                f"the loaded dict,\n"\
                f"\tthey are copied with their values from the reference dict:\n"
                    + "{0}".format('\n'.join(keys_missing))
                )
        if keys_unsupported != []:
            err_str += (
                f"\nThe following {len(keys_unsupported)} key(s) are not part of the "
                f"reference dict and have been deleted:\n"
                + "{0}".format('\n'.join(keys_unsupported))
            )
        if err_str != "":
            logger.warning(err_str)

        # sanitize *values* in filter dictionary, keys are ok by now
        for k in fb.fil[0]:
            # Bytes need to be decoded for py3 to be used as keys later on
            if type(fb.fil[0][k]) == bytes:
                fb.fil[0][k] = fb.fil[0][k].decode('utf-8')
            if fb.fil[0][k] is None:
                logger.warning(f"Entry fb.fil[0][{k}] is empty!")
        if 'ba' not in fb.fil[0]\
            or type(fb.fil[0]['ba']) not in {list, np.ndarray}\
                or np.ndim(fb.fil[0]['ba']) != 2\
                or (np.shape(fb.fil[0]['ba'][0]) != 2
                    and np.shape(fb.fil[0]['ba'])[1] < 3):
            logger.error("Missing key 'ba' or wrong data type!")
            fb.undo()
            return -1
        elif 'zpk' not in fb.fil[0]:
            logger.error("Missing key 'zpk'!")
            fb.undo()
            return -1
        elif 'sos' not in fb.fil[0]\
                or type(fb.fil[0]['sos']) not in {list, np.ndarray}:
            logger.error("Missing key 'sos' or wrong data type!")
            fb.undo()
            return -1

        if type(fb.fil[0]['ba']) == np.ndarray:
            if np.ndim(fb.fil[0]['ba']) != 2:
                logger.error(
                    f"Unsuitable dimension of 'ba' data, ndim = {np.ndim(fb.fil[0]['ba'])}")
            elif np.shape(fb.fil[0]['ba'])[0] != 2:
                logger.error(
                    f"Unsuitable shape {np.shape(fb.fil[0]['ba'])} of 'ba' data ")
        elif type(fb.fil[0]['ba']) == list:
            fb.fil[0]['ba'] = iter2ndarray(fb.fil[0]['ba'])

        if type(fb.fil[0]['zpk']) == np.ndarray:
            if np.ndim(fb.fil[0]['zpk']) != 2:
                logger.error(
                    f"Unsuitable dimension of 'zpk' data, ndim = {np.ndim(fb.fil[0]['zpk'])}")
            elif np.shape(fb.fil[0]['zpk'])[0] != 3:
                logger.error(
                    f"Unsuitable shape {np.shape(fb.fil[0]['zpk'])} of 'zpk' data ")
        elif type(fb.fil[0]['zpk']) == list:
            fb.fil[0]['zpk'] = iter2ndarray(fb.fil[0]['zpk'])

        logger.info(f'Successfully loaded filter\n\t"{file_name}"')
        dirs.last_file_name = file_name
        dirs.last_file_dir = os.path.dirname(file_name)  # update default working dir
        dirs.last_file_type = file_type  # save new default file type
        return 0

    except Exception as e:
        logger.error(f"Unexpected error:\n{e}")
        fb.undo()
        return -1


# ------------------------------------------------------------------------------
def save_filter(self):
    """
    Save filter as JSON formatted textfile, zipped binary numpy array or pickle object
    """
    # provide an identifier with version number for pyfda files
    fb.fil[0].update({'_id': ['pyfda', FILTER_FILE_VERSION]})

    file_name, file_type = select_file(
        self, title="Save Filter", mode='w', file_types = ("json", "npz", "pkl"))

    if file_name is None:
        return -1  # operation cancelled or other error
    err = False
    # create a copy of the filter to be saved that only contains keys of the
    # reference filter dict and warn of unsupported keys:
    keys_unsupported = [k for k in fb.fil[0] if k not in fb.fil_ref]
    if keys_unsupported != []:
        fil_0 = {k:v for k, v in fb.fil[0].items() if k in fb.fil_ref}
        logger.warning(
            "The following keys are ignored because they are not part of the\n"
            f"\tfilter reference dict:\n\t{keys_unsupported}")
    else:
        fil_0 = fb.fil[0]

    if file_type in {"npz", "pkl"}:
        try:
            with io.open(file_name, 'wb') as f:  # open in binary mode
                if file_type == 'npz':
                    np.savez(f, **fil_0)
                else:  # file_type == 'pkl':
                    pickle.dump(fb.fil[0], f)  # save in default pickle version

        except IOError as e:
            err = True
            logger.error(f'Failed saving "{file_name}"!\n{e}')

    elif file_type == 'json':
        try:
            with io.open(file_name, 'w') as f:  # open in text mode
                # first, convert dict containing numpy arrays to a pure json string
                fb_fil_0_json = json.dumps(fil_0, cls=NumpyEncoder, indent=2,
                                        ensure_ascii=False, sort_keys=True )
                # next, dump the string to a file
                f.write(fb_fil_0_json)

        except IOError as e:
            err = True
            logger.error(f'Failed saving "{file_name}"!\n{e}')
    else:
        err = True
        logger.error('Unknown file type "{0}"'.format(file_type))

    if not err:
        logger.info(f'Filter saved as\n\t"{file_name}"')
        dirs.last_file_name = file_name
        dirs.last_file_dir = os.path.dirname(file_name)  # save new default dir
        dirs.last_file_type = file_type  # save new default file type


# ------------------------------------------------------------------------------
class NumpyEncoder(json.JSONEncoder):
    """
    Special json encoder for numpy and other non-supported types, building upon
    https://stackoverflow.com/questions/26646362/numpy-array-is-not-json-serializable
    """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, complex):
            if obj.imag < 0:
                return str(obj.real) + str(obj.imag) + "j"
            else:
                return str(obj.real) + "+" + str(obj.imag) + "j"
        elif callable(obj):
            logger.warning(f"Object '{obj}' not JSON serializable as it is a function.")
            return ""
        else:
            try:
                return json.JSONEncoder.default(self, obj)
            except TypeError as e:
                logger.warning(
                    f"Object of type '{type(obj)}' is not JSON serializable.\n{e}")
                return ""


# ==============================================================================
if __name__ == '__main__':
    pass
