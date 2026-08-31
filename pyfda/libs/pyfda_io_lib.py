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

import csv
import datetime
import io
import logging
import os
import re
from typing import TextIO
import warnings
import wave

import numpy as np
from scipy.io import loadmat, savemat, wavfile

try:
    import xlwt  # noqa: F401
except ImportError:
    xlwt = None
try:
    import xlsx  # noqa: F401
except ImportError:
    xlsx = None

from pyfda.libs.pyfda_lib import safe_eval, pprint_log
from pyfda.libs.special_functions import lin2unit

import pyfda.libs.pyfda_fix_lib as fx
from pyfda.pyfda_rc import params
import pyfda.libs.pyfda_dirs as dirs
import pyfda.filterbroker as fb  # importing filterbroker initializes all its globals
from pyfda.filterbroker import get_fx, fb_get, fb_set

from .compat import QFileDialog

logger = logging.getLogger(__name__)
__version__ = dirs.VERSION

# ##############################################################################
# file filters for the QFileDialog object are constructed from this dict
file_filters_dict = {
    'cmsis': 'CMSIS DSP coefficients',
    'coe': 'Xilinx FIR coefficients',
    'csv': 'Comma / Tab Separated Values',
    'json': 'Javascript Object Notation',
    'mat': 'Matlab-Workspace',
    'npy': 'Binary Numpy Array',
    'npz': 'Zipped Binary Numpy Array',
    'pkl': 'Pickled data',
    'sos': 'Scipy / Matlab SOS coefficients',
    'txt': 'Microsemi FIR coefficients',
    'vhd': 'VHDL package or architecture',
    'wav': 'WAV audio format',
    'xls': 'Excel Worksheet',
    'xlsx': 'Excel 2007 Worksheet'
    }

# regex pattern that yields true in a re.search() when only the specified
#  characters (numeric, "eEjJ(),.+-" and blank / line breaks) are contained
pattern_num_chars = re.compile(r'[eEjJ()0-9,\.\+\-\s]+$')
# regex pattern that identifies characters and their position *not* specified
pattern_no_num = re.compile(r'(?![eEjJ()0-9,\.\+\-\s])')

# ------------------------------------------------------------------------------
def prune_file_ext(file_type: str) -> str:
    r"""
    Prune file extension, e.g. 'Text file' from 'Text file (\*.txt)' returned
    by QFileDialog file type description.

    Pruning is achieved with the following regular expression:

    .. code::

        return = re.sub('\([^\)]+\)', '', file_type)

    Parameters
    ----------
    file_type : str
        File type description string, e.g. 'Text file (\*.txt)'

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

    return re.sub(r'\([^\)]+\)', '', file_type)


# ------------------------------------------------------------------------------
def extract_file_ext(file_type: str, return_list: bool = False) -> str:
    r"""
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
        ext_list = re.findall(r'\([^\)]+\)', file_type)  # extract '(*.txt)'
        file_type_list = [t.strip('(*.)') for t in ext_list]  # remove '(*.)'
        if return_list:
            return file_type_list

        return str(file_type_list[0])

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
            logger.warning("Unknown file extension '.%s'", t)
    # remove trailing ';;', otherwise file filter '*' is appended
    file_filters = file_filters.removesuffix(';;')

    if dirs.last_file_type and dirs.last_file_type in file_filters_dict:
        last_file_filter =\
            file_filters_dict[dirs.last_file_type] + f" (*.{dirs.last_file_type})"
    else:
        last_file_filter = ""

    return file_filters, last_file_filter


# ------------------------------------------------------------------------------
def select_file(parent: object, title: str = "", mode: str = "r",
                file_types: tuple[str, ...] = ('csv', 'txt')) -> tuple[str, str]:
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
        logger.error("Unknown mode '%s'", mode)
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
def qtable2csv(table: object, data: np.ndarray, zpk: bool = False,
               formatted: bool = False) -> str:
    r"""
    Transform QTableWidget data to CSV formatted text for export to file or clipboard.

    Parameters
    ----------

    table : object
            Instance of QTableWidget

    data:   object
            Instance of the numpy variable shadowing table data

    zpk: bool
            when True, append the gain (``data[2]``) to the table

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

    Returns
    -------

    text: str
         text formatted with selected delimiter and linefeed.
    """
    def item2text(r: int, c: int, formatted: bool) -> str:
        """
        Convert table item at coordinate (r, c) to text, return '0' when item is None or empty

        When `formatted` is False, get data from the model (`data`) with full precision,
        otherwise convert the table item as displayed.
        """
        if formatted:
            if c == 2: # gain column
                return str(safe_eval(data[c][r], return_type='auto')) + delim
                # TODO: should use the value from the gain widget instead
            item = table.item(r, c)
            if item and item.text() != "":
                return table.itemDelegate().text(item).lstrip(" ") + delim
            return "0" + delim  # empty table item
        # unformatted, get data from the model
        return str(safe_eval(data[c][r], return_type='auto')).strip("()") + delim

    text = ""
    if params['CSV']['header'] == 'on':
        use_header = True
    elif params['CSV']['header'] in {'off', 'auto'}:
        use_header = False
    else:
        logger.error(
            "Unknown key '%s' for params['CSV']['header']", params['CSV']['header'])

    if params['CSV']['orientation'] not in {'rows', 'cols', 'auto'}:
        logger.error(
            "Unknown key '%s' for params['CSV']['orientation']",
            params['CSV']['orientation'])

    delim = params['CSV']['delimiter'].lower()
    if delim == 'auto':  # 'auto' doesn't make sense when exporting
        delim = ","
    cr = params['CSV']['lineterminator']

    num_cols = table.columnCount()  # visible columns of table
    num_rows = table.rowCount()  # visible rows of data

    # use this to get a list of lists with selected items per row
    # sel = qget_selected(table, reverse=False)['sel']

    # ==========================================================================
    # Copy data from the model (formatted = False) or the table (formatted = True)
    # ==========================================================================
    if params['CSV']['orientation'] == 'rows':  # write table in row format
        for c in range(num_cols):  # for each column (b,a or z,p) ...
            if use_header:  # ... start text line with table header and ...
                text += table.horizontalHeaderItem(c).text() + delim
            for r in range(num_rows):  # ... construct text line from data.
                text += item2text(r, c, formatted)
            text = text.rstrip(delim) + cr  # finish text line, remove last delimiter
        if zpk:  # add another text line with the gain items
            if use_header:
                text += 'k' + delim
            for r in range(len(data[2])):
                text += item2text(r, 2, formatted)  # gain value
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
                text += item2text(r, c, formatted)
            if zpk and r < len(data[2]):  # add another item with a gain value
                text += item2text(r, 2, formatted)  # gain value
            text = text.rstrip(delim) + cr  # finish text line, remove last delimiter

    return text.rstrip(cr)  # delete CR after last row


# ------------------------------------------------------------------------------
def csv2array(f: TextIO) -> np.ndarray[str] | None:
    """
    Convert comma-separated values from file or text to numpy array of str,
     taking into account the settings of the CSV dict.

    Parameters
    ----------

    f: TextIO
        handle to file or file-like object, e.g.

    >>> f = open(file_name, 'r') # or
    >>> f = io.StringIO(text)

    Returns
    -------

    data_arr: ndarray
        numpy array of ``str_ `` with table data from file or ``None`` when import was
        unsuccessful. Conversion to a numeric array is not performed here as the array
        elements can be string representations of various formats like float, complex,
        or fixpoint formats (bin, hex, oct, csd, ...).

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
      to the system default line separator, `os.linesep`. If newline is '',
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

    # throw an error (instead of just issuing a deprecation warning) when trying to
    # create a numpy array from nested ragged sequences. This error can then be
    # caught easily.
    warnings.filterwarnings('error', category=DeprecationWarning)
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
                "Unknown key '%s' for CSV_dict['header'], using %s instead.",
                CSV_dict['header'], header)

        if CSV_dict['orientation'].lower() not in {'auto', 'cols', 'rows'}:
            logger.error(
                "Unknown key '%s' for CSV_dict['orientation'], using column mode.",
                CSV_dict['orientation'])

        tab = CSV_dict['delimiter'].lower()
        cr = CSV_dict['lineterminator'].lower()

    except KeyError as e:
        logger.error("Dict 'params':\n%s.", e)
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
            logger.warning(
                'CSV sniffing reported error "%s",\n\tcontinuing with format "excel-tab"', e)
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

    logger.info(
        "Parsing CSV data with\n\theader = '%s' | Delimiter = %r | Lineterm. = %r | "
        "quotechar = ' %s '", use_header, delimiter, lineterminator, quotechar)

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
        logger.error("Error during CSV import:\n%s", e)
        return None

    if data_list in ([], [""]):  # empty list or list with one empty string
        logger.error("Imported data is empty.")
        return None

    # ------- Convert list to an array of str --------------------
    try:
        data_arr = np.array(data_list)
    except np.exception.VisibleDeprecationWarning as e:
        # prevent creation of numpy arrays from nested ragged sequences
        logger.error("numpy deprecation warning treated as error: %s", e)
        return None
    except (TypeError, ValueError) as e:
        logger.error("%s\nData = %s", e, pprint_log(data_list))
        return None

    if np.ndim(data_arr) == 0:
        logger.error("Imported data is a scalar: '%s'", data_arr)
        return None

    if np.ndim(data_arr) == 1:
        if len(data_arr) < 2:
            logger.error("Not enough data: '%s'", data_arr)
            return None
        data = data_arr

    elif np.ndim(data_arr) == 2:
        rows, cols = np.shape(data_arr)
        # The check for max. number of columns has to be handled downstream
        # logger.info("cols = %s, rows = %s, data_arr = %s\n", cols, rows, data_arr)
        # if cols > max_cols and rows > max_cols:
        #     logger.error("Unsuitable data shape %s", np.shape(data_arr))
        #     return None
        if params['CSV']['orientation'] == 'rows'\
                or params['CSV']['orientation'] == 'auto' and cols > rows:
            # returned table is transposed, swap cols and rows
            logger.info("Building transposed table with %d row(s) and %d columns.", cols, rows)
            csv2array.info_str = "T:" + csv2array.info_str
            if use_header:
                logger.info("Skipping header %s", data_arr.T[0])
                data = data_arr.T[1:]
            else:
                data = data_arr.T
        else:  # column format
            logger.info("Building table with %d column(s) and %d rows.", cols, rows)
            if use_header:
                logger.info("Skipping header %s", data_arr[0])
                data = data_arr[1:]
            else:
                data = data_arr
    else:
        logger.error("Unsuitable data shape: ndim = %d, shape = %s",
                     np.ndim(data_arr), np.shape(data_arr))
        return None

    csv2array.nchans = np.ndim(data)

    return data
#-------------------------------------------------------------------------------
def read_csv_info_large(filename):
#-------------------------------------------------------------------------------
    """
    Get infos about the size of a csv file without actually loading the whole
    file into memory - this only makes sense for very large files.

    See
    https://stackoverflow.com/questions/64744161/best-way-to-find-out-number-of-rows-in-csv-without-loading-the-full-thing
    """
    file_size = os.path.getsize(filename)
    logger.info("File Size is %d bytes", file_size)

    sniffer = csv.Sniffer()

    with open(filename, 'r', encoding='utf-8') as f:
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

    logger.info(
        "Terminator = '%s', Delimiter = '%s', RowCount = %d, Header=%s",
        lineterminator, delimiter, N, has_header)

    if params['CSV']['orientation'] not in {'rows', 'cols', 'auto'}:
        logger.error("Unknown key '%s' for params['CSV']['orientation']",
                     params['CSV']['orientation'])
    if params['CSV']['orientation'] == 'auto' and (N < nchans)\
        or params['CSV']['orientation'] == 'rows':  # swap rows and columns
        N, nchans = nchans, N
        row_mode = True
        transpose = "T #"
    else:
        row_mode = False
        transpose = ""

    if N < 2:
        logger.error("No suitable CSV file, has only %d data entries.", N)
        return -1

    # file is ok, copy local variables to function attributes
    read_csv_info_large.row_mode = row_mode
    read_csv_info_large.file_size = file_size
    read_csv_info_large.N = N
    read_csv_info_large.nchans = nchans
    read_csv_info_large.info_str = f"{transpose} '{lineterminator}' # '{delimiter}'"

    return 0

#-------------------------------------------------------------------------------
def read_wav_info(file) -> int:
    """
    Get infos about the following properties of a wav file without actually
    loading the whole file into memory by reading the header.
    """
    # https://wavefilegem.com/how_wave_files_work.html
    # https://stackoverflow.com/questions/7833807/get-wav-file-length-or-duration
    # http://soundfile.sapp.org/doc/WaveFormat/
    # https://ccrma.stanford.edu/courses/422/projects/WaveFormat/
    def str2int(s: str) -> int:
        """ convert argument from str `s` in little endian format to int """
        num = 0
        for i in range(len(s)):
            num = num + ord(s[i]) * pow(256, i)
        return num

    f = open(file,'r', encoding='latin-1')
    # Get the file size in bytes
    file_size = os.path.getsize(file)
    if file_size < 44:  # minimum length for WAV file due to header
        logger.error("Not a wav file: Filesize is only %d bytes!", file_size)
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
        logger.error("Invalid format header '%s' instead of 'fmt'!", FMT)
        return -1

    # Pos. 16: Size of subchunk with format infos in bytes, 16 for Int., 18 for float
    fmt_chnk_size1 = str2int(HEADER[16:20])
    if fmt_chnk_size1 not in {16, 18}:
        logger.error("Invalid size %s of format subchunk!", fmt_chnk_size1)
        return -1

    # Pos. 20: Audio encoding format, must be 1 for uncompressed PCM
    encoding = str2int(HEADER[20:22])
    if encoding == 1:
        sample_format = 'int'  # Integer PCM
    elif encoding == 3:
        sample_format = 'float'  # IEEE Float PCM
    else:
        logger.error("Invalid audio encoding %s, only uncompressed PCM supported!", encoding)
        sample_format = ""
        return -1

    # Pos. 22: Number of channels
    nchans = str2int(HEADER[22:24])

    # Pos. 24: Sampling rate f_S (4 bytes)
    # f.seek(24)
    f_S = str2int(HEADER[24:28])

    # Pos. 28: Byte rate = f_S * n_chans * Bytes per sample (4 bytes)
    # byte_rate = str2int(HEADER[28:32])

    # Pos. 32: Block align, # of bytes per sample incl. all channels (2 bytes)
    # block_align = str2int(HEADER[32:34])

    # Pos. 34: Bits per sample, wl = wordlength in bytes (2 bytes)
    bits_per_sample = str2int(HEADER[34:36])

    if sample_format == 'float':
        # Format subchunk is 18 bytes long for float samples, hence file pointer
        # has to be advanced by two bytes

        # ###################### FACT Subchunk ###################################
        # The fact chunk indicates how many sample frames are in the file. For
        # integer formats the tag it’s optional; otherwise it’s required. For float
        # PCM, calculation is performed exactly as for integer PCM, hence, it is not
        # evaluated here.
        # f.seek(38)
        # FACT = f.read(12)
        f.seek(50)
    else:
        f.seek(36)

    # ###################### DATA Subchunk #######################################
    # String 'data' marks beginning of data subchunk
    DATA = f.read(4)
    if DATA != "data":
        logger.error("Invalid data header '%s' instead of 'data'!", DATA)
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
            logger.error("Unsupported integer sample format with %d "
                         "bits per sample.", bits_per_sample)
            return -1
    else:
        if bits_per_sample == 32:
            read_wav_info.sample_format = "Float32"
        elif bits_per_sample == 64:
            read_wav_info.sample_format = "Float64"
        else:
            logger.error("Unsupported float sample format with %d "
                         "bits per sample.", bits_per_sample)
            return -1

    read_wav_info.wl = bits_per_sample // 8  # Wordlength in bytes

    # Pos. 40 or 42: Total number of samples per channel
    read_wav_info.N = str2int(f.read(4)) // (nchans * read_wav_info.wl)

    read_wav_info.nchans = nchans  # number of channels

    read_wav_info.f_S = f_S  # sampling rate in Hz

    # duration of the data in milliseconds
    read_wav_info.ms = read_wav_info.N * 1000 / (f_S * nchans)

    return 0

# ------------------------------------------------------------------------------
def file2array(file_name: str, file_type: str, fkey: str = "",
               from_clipboard: bool = False, as_str: bool = False
                 ) -> np.ndarray | None:
    r"""
    Import data from a file or from clipboard and convert it to a numpy array.

    Parameters
    ----------
    file_name: str
        Full path and name of the file to be imported

    file_type: str
        File type, currently supported are 'csv', 'mat', 'npy', 'npz, 'txt', 'wav'.

    fkey : str
        Key for accessing data in *.npz or Matlab workspace (*.mat) files with
        multiple entries.

    from_clipboard: bool
        When False (default), read data from passed file_name / file_type, else get
        data from clipboard.

    as_str: bool
        When False (default), try to convert results to ndarray of float or complex.
        Otherwise, return an ndarray of str.

    Returns
    -------
    ndarray of float / complex / int or str
        Data from the file (ndarray) or None (error)


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

    Parameters that are 'auto', will be guessed by ``csv.Sniffer()``.
    """
    file2array.info_str = "" # function attribute for file infos

    # ----- Data from clipboard -----------------------------------------------
    if from_clipboard:
        clip_text = dirs.clipboard.text()
        if clip_text in {None, ""}:
            # an error has occurred
            logger.error("Clipboard is empty!")
            return None

        logger.info("Importing data from clipboard.")

        # convert text from clipboard to a file-like object than can be handled by
        data_arr = csv2array(io.StringIO(clip_text))

        if data_arr is None:
            # an error has occurred
            logger.error("Couldn't import data from clipboard.")
            return None
        if isinstance(data_arr, str):
            # returned an error message instead of numpy data:
            file2array.info_str = ""
            logger.error("You shouldn't see this message!! \n"
                         "Error copying from clipboard:\n%s", data_arr)
            return None

        file2array.info_str = csv2array.info_str

    # ----- Data from file -----------------------------------------------------
    else:
        logger.info("Importing data from file '%s'.", file_name)
        try:
            if file_type == 'wav':
                _, data_arr = wavfile.read(file_name, mmap=False)
                # data_arr is 1D for single channel (mono) files and
                # 2D otherwise (n_chans, n_samples)

            elif file_type in {'csv', 'txt'}:
                with open(file_name, 'r', newline=None) as f:
                    data_arr = csv2array(f)
                    file2array.info_str = csv2array.info_str
                    if data_arr is None:
                        # an error has occurred
                        logger.error("Error loading file '%s'!", file_name)
                        return None
                    if isinstance(data_arr, str):
                        # returned an error message instead of numpy data:
                        file2array.info_str = ""
                        logger.error("You shouldn't see this message!! \n"
                                     "Error loading file '%s':\n%s", file_name, data_arr)
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
                                "Key '%s' not in file '%s'.\nKeys found: %s",
                                fkey, file_name, fdict.files)
                        else:
                            data_arr = fdict[fkey]  # pick the array `fkey` from the dict
                    else:
                        logger.error('Unknown file type "%s"', file_type)
                        return None

        except (IOError, KeyError) as e:
            logger.error("Failed loading %s!\n%s", file_name, e)
            return None

    if data_arr is None:
        logger.error("Couldn't import data.")
        return None

    if not as_str:
        try:  # try to convert array elements to float
            data_arr = data_arr.astype(float)
        except ValueError as e:
            try: # try to convert array elements to complex
                data_arr = data_arr.astype(complex)
            except ValueError:
                logger.error("%s,\n\tconversion to float and complex failed.", e)
                return None

    logger.info('Successfully imported data\n%s', pprint_log(data_arr, N=5))
    return data_arr  # returns numpy array of type string or float/complex

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
    if file_name is None:  # error or operation cancelled
        return -1
    if np.ndim(data) < 1 or np.ndim(data) > 2:
        logger.error("Unsuitable data format for a wav file, ndim = %d.", np.ndim(data))
        return -1
    try:
        if file_type == 'wav':
            f_S_int = int(abs(f_S))
            if f_S_int == 0:
                f_S_int = 1
            if f_S != f_S_int:
                logger.warning(
                    "Only positive integer sampling frequencies can be used for WAV files,\n"
                    "sampling frequency has been changed to f_S = %d", f_S_int)

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
            logger.error("File type %s not supported!", file_type)
            return -1

        logger.info('Saved data as\n\t"%s".', file_name)
        return 0


    except IOError as e:
        logger.error('Failed saving "%s"!\n%s\n', file_name, e)
        return -1

# ------------------------------------------------------------------------------
def write_wav_frame(parent: object, file_name: str, data: np.ndarray, f_S: int = 1,
                    title: str = "Export") -> None:
    """
    Export a frame of data in wav format

    TODO: Currently unused!
    TODO: Remove pylint: disable=no-member once bug
          https://github.com/pylint-dev/pylint/issues/10316 is fixed

    Parameters
    ----------
    parent: handle to calling instance for creating file dialog instance

    file_name: str
        Full path and name of the file to be imported

    data: np.ndarray
        data to be exported

    f_S: int
        Sampling frequency in Hz

    title: str
        title string for the file dialog box (e.g. "audio data ")

    Returns
    -------
    None
    """
    file_name, _ = select_file(parent, title=title, mode='wb', file_types=('wav',))
    if file_name is None:
        return  # file operation cancelled or other error

    try:
        if np.ndim(data) == 1:  # mono
            audio = data
            n_chan = 1
        elif np.ndim(data) != 2:
            logger.error("Unsuitable data format, ndim = %d.", np.ndim(data))
            return
        elif np.shape(data)[1] != 2:
            logger.error("Unsuitable number of channels = %d", np.shape(data)[1])
            return
        else:
            audio = data.T  # transpose data
            n_chan = np.shape(data)[1]
            # audio = np.array([left_channel, right_channel]).T
        with wave.open(file_name, "wb") as wf:
            # 2 Channels.
            wf.setnchannels(n_chan)  # pylint: disable=no-member
            # 2 bytes per sample.
            wf.setsampwidth(2)  # pylint: disable=no-member
            wf.setframerate(f_S)  # pylint: disable=no-member
            # get the raw bytes from the numpy array:
            wf.writeframes(audio.tobytes())  # pylint: disable=no-member

        logger.info('Data saved as\n\t"%s"', file_name)

        # # Interleave the stereo data: [L1, R1, L2, R2, ...]
        # # Stacks arrays into columns and then flattens them
        # interleaved_data = np.stack((left_channel, right_channel), axis=1).flatten()

    except IOError as e:
        logger.error('Failed saving "%s"!\n%s\n', file_name, e)


# ------------------------------------------------------------------------------
def export_fil_data(parent: object, data: str, fkey: str = "", title: str = "Export",
                file_types: tuple[str, ...] = ('csv', 'mat', 'npy', 'npz'),
                formatted: bool = True) -> None:
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

    formatted: bool
        export data as displayed in table (fixpoint format, number of digits etc.)
    """
    # logger.debug(
    #     f"export data: type{type(data)}|dim{np.ndim(data)}|"
    #     f"shape{np.shape(data)}\n{data}")

    # add file types for coefficients and a description text for messages.
    # TODO: Add CMSIS export for FIR filters
    # TODO: Add fixpoint format export for CMSIS / SOS coefficients
    if fkey == 'ba':
        if fb_get('ft') == 'FIR':
            file_types += ('coe', 'vhd', 'txt', 'cmsis')
        else:
            file_types += ('cmsis', 'sos')
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
        return  # file operation cancelled or other error

    err = False

    try:
        if file_type == 'csv':
            with open(file_name, 'w', encoding="utf8", newline='') as f:
                f.write(data)
        # other text / string formats
        elif file_type in {'coe', 'txt', 'vhd', 'cmsis', 'sos'}:
            with open(file_name, 'w', encoding="utf8") as f:
                if file_type == 'coe':
                    err = export_coe_xilinx(f)
                elif file_type == 'txt':
                    err = export_coe_microsemi(f)
                elif file_type == 'vhd':
                    err = export_coe_vhdl_package(f)
                elif file_type in {'cmsis', 'sos'} and fb_get('ft') == 'IIR':
                    err = export_coe_cmsis_sos(f, file_type, formatted)
                elif file_type == 'cmsis' and fb_get('ft') == 'FIR':
                    err = export_coe_cmsis_fir(f, formatted)
                else:
                    logger.error('Unknown file extension "%s"', file_type)
                    return

        else:  # binary formats, storing numpy arrays
            np_data = csv2array(io.StringIO(data))  # convert csv data to numpy array
            if isinstance(np_data, str):
                # returned an error message instead of numpy data:
                logger.error("Error converting %s data:\n%s", description.lower(), np_data)
                return

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
                    logger.error('Unknown file type "%s"', file_type)
                    err = True

        if not err:
            logger.info('%s data saved as\n\t"%s"', description, file_name)

    except IOError as e:
        logger.error('Failed saving "%s"!\n%s\n', file_name, e)

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
    a_targs_db = []
    ft = fb_get('ft')  # get filter type ('IIR', 'FIR')
    unit = fb_get('amp_specs_unit')
    unit = 'dB'  # fix this for the moment
    # construct pairs of corner frequency and corresponding amplitude
    # labels in ascending frequency for each response type
    if fb_get('rt') in {'lp', 'hp', 'bp', 'bs', 'hil'}:
        if fb_get('rt') == 'lp':
            f_lbls = ['F_PB', 'F_SB']
            a_lbls = ['A_PB', 'A_SB']
        elif fb_get('rt') == 'hp':
            f_lbls = ['F_SB', 'F_PB']
            a_lbls = ['A_SB', 'A_PB']
        elif fb_get('rt') == 'bp':
            f_lbls = ['F_SB', 'F_PB', 'F_PB2', 'F_SB2']
            a_lbls = ['A_SB', 'A_PB', 'A_PB', 'A_SB2']
        elif fb_get('rt') == 'bs':
            f_lbls = ['F_PB', 'F_SB', 'F_SB2', 'F_PB2']
            a_lbls = ['A_PB', 'A_SB', 'A_SB', 'A_PB2']
        elif fb_get('rt') == 'hil':
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
                a_targs_db.append(a_dB)
            except KeyError as e:
                a_targs.append('')
                a_targs_db.append('')
                err[i] = True
                logger.debug(e)

        for i in range(len(f_lbls)):
            if err[i]:
                del f_lbls[i]
                del f_vals[i]
                del a_lbls[i]
                del a_targs[i]
                del a_targs_db[i]

    date_frmt = "%d-%B-%Y %H:%M:%S"  # select date format
    unit = fb_get('plt_fUnit')
    if unit in {'f_S', 'f_Ny'}:
        f_S = ""
    else:
        f_S = int(fb_get('f_S'))
    header = (
        "-" * 85 + "\n\n"
        f"{title}\n"
        f"Generated by pyfda {__version__} (https://github.com/chipmuenk/pyfda)\n\n")
    header += f"Designed:\t\
        {datetime.datetime.fromtimestamp(int(fb_get('timestamp'))).strftime(date_frmt)}\n"
    header += f"Saved:\t{datetime.datetime.now().strftime(date_frmt)}\n\n"
    header += f"Filter type:\t{fb_get('rt')}, {fb_get('fc')} "
    header += f"(Order = {fb_get('N')})\n"
    header += f"Sample Frequency \tf_S = {f_S} {unit}\n\n"
    header += "Corner Frequencies:\n"
    for lf, f, la, a in zip(f_lbls, f_vals, a_lbls, a_targs_db, strict=True):
        header += "\t" + lf + " = " + str(f) + " " + unit + " : " + la + " = "
        header += str(a) + " dB\n"
    header += "-" * 85 + "\n"
    return header


# ------------------------------------------------------------------------------
def export_coe_xilinx(f: TextIO) -> bool:
    r"""
    Save FIR filter coefficients in Xilinx coefficient format as file '\*.coe', specifying
    the number base and the quantized coefficients (decimal or hex integer).

    Returns error status (False if the file was saved successfully)
    """
    qc = fx.Fixed(fb_get('fxq', 'QCB'))  # instantiate fixpoint object

    if qc.q_dict['WF'] != 0  and fb_get('qfrmt') != 'qint':
        logger.error("Fractional formats are not supported!")
        return True

    if fb_get('fx_base') == 'hex':  # select hex format
        coe_radix = 16
    if fb_get('fx_base') == 'bin':  # select binary format
        coe_radix = 2
    else:
        logger.warning(
            "Coefficients in %s format are not supported in COE files, converting to "
            "decimal format.", fb_get('fx_base'))
        fb_set('fx_base', 'dec')  # select decimal format in all other cases
        coe_radix = 10

    # Quantize coefficients to decimal / hex integer format, return an array of strings
    bq = qc.float2frmt(fb_get('ba')[0])

    exp_str = "; " + coe_header(
        "XILINX CORE Generator(tm) Distributed Arithmetic FIR filter coefficient (.COE) "
        "file").replace("\n", "\n; ")

    exp_str += f"\nRadix = {coe_radix};\n"
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
    r"""
    Save FIR filter coefficients in Microsemi coefficient format as file '\*.txt'.
    Coefficients have to be in integer format, the last line has to be empty.
    For (anti)symmetric filter only one half of the coefficients must be
    specified?
    """
    qc = fx.Fixed(fb_get('fxq', 'QCB'))  # instantiate fixpoint object

    if qc.q_dict['WF'] != 0  and fb_get('qfrmt') != 'qint':
        logger.error("Fractional formats are not supported!")
        return True

    if fb_get('fx_base') != 'dec':
        fb_set('fx_base', 'dec')  # select decimal format in all other cases
        logger.warning('Converting to decimal coefficient format, other numeric formats '
                       'are not supported by Microsemi tools.')

    # Quantize coefficients to decimal integer format, returning an array of strings
    bq = qc.float2frmt(fb_get('ba')[0])

    coeff_str = "coefficient_set_1\n"
    for b in bq:
        coeff_str += str(b) + "\n"

    f.write(coeff_str)

    return False


# ------------------------------------------------------------------------------
def export_coe_vhdl_package(f: TextIO) -> bool:
    r"""
    Save FIR filter coefficients as a VHDL package '\*.vhd', specifying
    the number base and the quantized coefficients (decimal or hex integer).
    """
    qc = fx.Fixed(fb_get('fxq', 'QCB'))  # instantiate fixpoint object
    if fb_get('qfrmt') == 'qfrac' and qc.q_dict['WF'] != 0:
        logger.error("Fractional numbers are only supported for floats!")
        return True

    WO = fb_get('fxq', 'QO','WI') + fb_get('fxq', 'QO', 'WF') + 1

    if fb_get('fx_base') == 'dec' or not get_fx():
        pre = ""
        post = ""
    elif fb_get('fx_base') == 'hex':
        pre = "#16#"
        post = "#"
    elif fb_get('fx_base') == 'bin':
        pre = "#2#"
        post = "#"
    else:
        prev_fx_base = fb_get('fx_base')
        fb_set('fx_base', 'dec')  # select decimal format in all other cases
        pre = ""
        post = ""
        logger.warning(
            "Coefficients in %s format are not supported, converting to decimal format.",
            prev_fx_base)

    # Quantize coefficients to selected fixpoint format, returning an array of strings
    bq = qc.float2frmt(fb_get('ba')[0])

    exp_str = "-- " + coe_header(
        "VHDL FIR filter coefficient package file").replace("\n", "\n-- ")

    exp_str += "\nlibrary IEEE;\n"
    if not get_fx():
        exp_str += "use IEEE.math_real.all;\n"
    exp_str += "USE IEEE.std_logic_1164.all;\n\n"
    exp_str += "package coeff_package is\n"
    exp_str += f"constant n_taps: integer := {len(bq)-1};\n"
    if not get_fx():
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


def export_coe_cmsis_fir(f: TextIO, formatted: bool = False) -> bool:
    """
    The CMSIS FIR filter function requires the coefficients to be in time reversed
    order, hence the coefficient array is flipped before exporting.
    """
    logger.error("Not implemented yet! (formatted = %s)", formatted)
    # coeffs = fb_get('ba')[0][::-1]
    return True


# ------------------------------------------------------------------------------
def export_coe_cmsis_sos(f: TextIO, file_type: str, formatted: bool = False) -> bool:
    """
    Export coefficients in either CMSIS or scipy SOS format.

    Scipy SOS coefficients are specified in the following format:
    [b_00, b_10, b_20, a_00, a_10, a_20],
    [b_01, b_11, b_21, a_01, a_11, a_21],
    ...

    The CMSIS DSP format is used by the ARM Cortex-M DSP library. In the CMSIS IIR SOS
    format, the 'a_0i = 1.0' coefficients are omitted by deleting the 4th column.
    The recursive coefficients have the opposite sign compared to the scipy format.

    The CMSIS format is specified as follows:
    [b_00, b_10, b_20, -a_10, -a_20],
    [b_01, b_11, b_21, -a_11, -a_21],
    ...

    See https://www.keil.com/pack/doc/CMSIS/DSP/html/group__BiquadCascadeDF1.html
    https://dsp.stackexchange.com/questions/79021/iir-design-scipy-cmsis-dsp-coefficient-format
    https://github.com/docPhil99/DSP/blob/master/MatlabSOS2CMSIS.m

    # TODO: check `scipy.signal.zpk2sos` for details concerning sos pairing
    # TODO: qc = fx.Fixed(fb_get('fxq', 'QCB'))
    """

    sos_coeffs = fb_get('sos')  # copy coeffs in scipy SOS format
    if np.ndim(sos_coeffs) < 2 or np.shape(sos_coeffs)[1] != 6\
            or np.shape(sos_coeffs)[0] < 1:
        logger.error("SOS coefficients have a bad shape '%s'!", np.shape(sos_coeffs))
        return True

    if fb_get('creator')[0] == 'ba':
        logger.warning("Second-order sections have been calculated from "
                       "'ba' format, results may be inaccurate.")

    # check whether a_0 coefficients of all sections are == 1
    if not np.all(np.isclose(sos_coeffs[:, 3], 1.0, atol=1e-8)):
        logger.warning(
            "Not all a_0 coefficients are 1.0, results may be wrong!")

    if file_type == 'cmsis':
    # delete a_0 coefficients which always should be 1
    # and invert the sign of recursive coefficients:
        sos_coeffs = np.delete(sos_coeffs, 3, 1)
        sos_coeffs[:, 3:] = - sos_coeffs[:, 3:]

    if formatted:
        pass

    delim = params['CSV']['delimiter'].lower()
    if delim == 'auto':  # 'auto' doesn't make sense when exporting
        delim = ","
    cr = params['CSV']['lineterminator']

    text = ""
    for r in range(np.shape(sos_coeffs)[0]):  # number of rows
        for c in range(np.shape(sos_coeffs)[1]):  # always has 5 or 6 columns
            text += str(safe_eval(sos_coeffs[r][c], return_type='auto')) + delim
        text = text.rstrip(delim) + cr
    text = text.rstrip(cr)  # delete last CR

    f.write(text)

    return False

# ==============================================================================
if __name__ == '__main__':
    pass
