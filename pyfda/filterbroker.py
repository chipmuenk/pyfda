# -*- coding: utf-8 -*-
#
# This file is part of the pyfda project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyfda Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

# Replace fb.fil[0]['some_key'] with fb_get('some_key') with the regular expression
#   fb.fil\[0\]\['([\s\S\r]*?)'\] -> fb_get('$1')

"""
Dynamic parameters and settings are exchanged via the dictionaries in this file.
Importing ``filterbroker.py`` runs the module once, defining all module variables
which have a global scope like class variables.

The entries in the global dict `fil[0]` contain the current filter design parameters, they
can be accessed and modified via the getter and setter `fb_get()` and `fb_set()`.

The entries in this file are only used as initial / default entries and to
demonstrate the structure of the global dicts and lists.
These initial values are also handy for module-level testing where some useful
setting of the variables is required.

Attributes
----------


Notes
-----

Alternative approaches for data persistence could be the packages `shelve` or pickleshare
More info on data persistence and storing / accessing global variables:

* http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
* http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
* http://pymotw.com/2/articles/data_persistence.html
* http://stackoverflow.com/questions/9058305/getting-attributes-of-a-class
* http://stackoverflow.com/questions/2447353/getattr-on-a-module
"""
import copy
import logging
from typing import Iterable

from pyfda.libs.pyfda_num_lib import iter2ndarray
from pyfda.libs.pyfda_text_lib import compare_dictionaries

from pyfda.filter_storage import fil_ref

import numpy as np

logger = logging.getLogger(__name__)
# ==========================================================
# Variables that can be accessed from all modules
#
# State of filter design: 'ok', 'changed', 'error', 'active'
design_filt_state = 'changed'
# ===========================================================
# ----------------------------------------------------------------------------------
# Include this version number as `'_id': ('pyfda', FILTER_FILE_VERSION)` when saving
# filter files and test for the version when loading filter files.
FILTER_FILE_VERSION = '3'

UNDO_LEN = 20  # depth of circular undo buffer
undo_step = 0  # number of undo steps, limited to UNDO_LEN
undo_ptr = 0  # pointer to current undo memory % UNDO_LEN

  # create empty lists with length 10 for multiple filter designs and undo memory
fil = [None] * 10
fil_undo = [None] * UNDO_LEN

# -----------------------------------------------------------------------
def fil_copy(src: str = "ref", dest: str = "all") -> None:
    """
    Copy `'src'` filter to `'dest'` filter where:
    - `'src'` can be  the reference filter ("ref") or fil[0] ... fil[9] ("0" ... "9") 
    - `'dest'` can be all filters ("all") or fil[0] ... fil[9] ("0" ... "9")
    Other source or target destinations give an error.
    """

    # for f in fil:
    #   f = copy.deepcopy(fil_ref)
    # does not work because all entries in fil[0] ... fil[9] become references to the same dict `fil_ref`,
    # so that changing one of them changes all of them. This is not the case for the nested dicts and
    # lists, which are also references but they are not changed by changing the reference to the
    # outer dict. So we need to create a deep copy of fil_ref for each entry in `fil``.

    if dest == "all":
        for i, _ in enumerate(fil):
            fil[i] = copy.deepcopy(fil_ref)
            return

    targ_idx = int(dest)

    if src == "ref":
        fil[targ_idx] = copy.deepcopy(fil_ref)
        return

    src_idx = int(src)
    fil[targ_idx] = fil[src_idx]
    return

def fil_info(idx: int) -> str:
    """
    Return filter info string
    """
    return fil[idx]['info']


# -------------------
fil_copy()
# -------------------


# =============================================================================

# -------------------------
def _print_dict(keys_tuple: tuple, top_dict_str = "fil[0]") -> str:
    """
    Print a string representation for a nested dictionary, defined by the list
    or tuple of strings `keys_tuple`. This is used to issue meaningful error messages.

    Parameters
    ----------
    keys_tuple : tuple
        Tuple of keys to create representation of the nested dictionary.
    top_dict_str : str
        The top-level dictionary as a string to use for printing.

    Returns
    -------
    str
        The string representation of the (nested) dictionary.

    Example
    -------
    keys_tuple = ('fxq', 'QCA', 'WF') returns "fil[0]['fxq']['QCA']['WF']"

    """
    if not keys_tuple or not isinstance(keys_tuple, tuple):
        raise KeyError("Need a non-empty tuple of keys for printing the dictionary!")

    dict_str = top_dict_str
    if len(keys_tuple) == 1:  # only one level dictionary with keys_tuple[0]
        dict_str += '[' + keys_tuple[0] + ']'
    else:
        for k in keys_tuple:
            dict_str += '[' + k + ']'
    return dict_str


# -------------------------
def _traverse_dict(keys_tuple: tuple, fil_dict: dict) -> dict:
    """
    Use the tuple of strings `keys_tuple` to traverse the (nested) dict `fil_dict`
    and return the addressed subdictionary.

    In order to set the value of the returned dict, use the key for the lowest
    nesting level on the returned dict `d`, i.e. `d[keys_tuple[-1]] = arg` .

    Parameters
    ----------
    keys_tuple : tuple
        Tuple of keys to traverse the nested dictionary.

    fil_dict : dict
        The dictionary to traverse.

    Returns
    -------
    dict
        A copy of the the traversed dictionary at the specified (usually lowest) level.

    Raises
    ------
    KeyError
        If a key does not exist in the dictionary or is not of type string
    TypeError
        If a key does not point to another dictionary
    """
    if not keys_tuple:
        raise KeyError("Tuple of keys was empty!")

    d = fil_dict
    for k in keys_tuple[:-1]:  # Traverse all keys except the last one
        if k not in d or not isinstance(k, str):
            raise KeyError(f"Key '{k}' not found or is not a dictionary!")
        if not isinstance(d[k], dict):
            raise TypeError(f"Key '{k}' points to '{d[k]}' which is not a dict!")
        d = d[k]
    return d

# -------------------------
def get_fx() -> bool:
    """
    Check if a fixpoint mode is active globally by checking the current

    Returns
    -------
    bool
        True if qfrmt is one of the fixpoint formats 'qint' or 'qfrac'
        False if qfrmt is one of the floating point formats 'float32' or 'float64'

    Raises
    ------
    KeyError
        If qfrmt is not one of the expected values above
    """
    qfrmt = fb_get('qfrmt')
    if qfrmt not in ['qint', 'qfrac', 'float32', 'float64']:
        raise KeyError("Invalid value for 'qfrmt', assuming floating-point!")

    return qfrmt in ['qint', 'qfrac']

# -------------------------
def set_fx(fx: bool) -> None:
    """
    Set fixpoint mode by restoring previous fixpoint format
    when `fx == True`, otherwise restore previous float format.
    """
    if fx:
        fb_set('qfrmt', fb_get('qfrmt_fx_last'))
    else:
        fb_set('qfrmt', fb_get('qfrmt_float_last'))

# -------------------------
def fb_get(*keys_tuple: tuple, fil_dict: dict = fil[0], verbose: bool = True)\
    -> str | int | float | Iterable | dict | None:
    """
    Get the value of a key in the global dict `fil[0]`. Multiple arguments
    access nested dicts:
    fb_get('qfrmt') == fb.fil[0]['qfrmt']
    fb_get('ba', 0) == fb.fil[0]['ba'][0]

    Parameters
    ----------
    keys_tuple : tuple
        Tuple of keys for traversing the nested dictionary.
    fil_dict : dict
        The dictionary to traverse, the default is the global `fil[0]`.
    verbose : bool
        Whether to log errors and warnings, default is True. Setting this to False
        can be used to detect silently whether a key exists in the dictionary

    Returns
    -------
    str | int | float | Iterable | dict | None
        The value of the specified key in the dictionary, or None if the key
        does not exist or a deep copy if keys_tuple is empty.
    """
    if not isinstance(keys_tuple, tuple):
        logger.error("A tuple of keys is needed for traversing the filter dict '%s', not a '%s'!",
                     keys_tuple, type(keys_tuple).__name__)
    if len(keys_tuple) == 0:
        # called without arguments, return a deepcopy of the whole dict
        return copy.deepcopy(fil_dict)

    # traverse nested dict 'fil_dict' using tuple of keys and access subdictionary
    ret = fil_dict
    try:
        for key in keys_tuple:
            ret = ret[key]
            # ret = fil_dict[keys_tuple[0]][keys_tuple[1]][keys_tuple[2]] ...
    except (KeyError, IndexError, TypeError):
        # create a meaningful error message with a string of the failed dict
        if verbose:
            logger.error("Dict '%s' does not exist!", _print_dict(keys_tuple))
        return None

    if ret is None and verbose:
        logger.warning("Key '%s' not found in filter dict!", keys_tuple[-1])
    return ret

# -------------------------
def fb_set(*keys_tuple: tuple, backup: bool = True, new_key: bool = False,
           accept_dict: bool = False, fil_dict: dict = fil[0]) -> int:
    """
    Use the individual arguments that have been collected as `keys_tuple` to access a
    nested dict `fil_dict` (default: `fil[0]`) and write the last item in `keys_tuple` to the dict.

    Example:
    fb_set('fxq', 'QCA', 'WF', 12) is equivalent to `fil[0]['fxq']['QCA']['WF'] = 12`
    fb_set('fxq', 'QCA', {'WF': 15, 'WI': 0}) is equivalent to
            `fil[0]['fxq']['QCA']['WF'] = 15` and `fil[0]['fxq']['QCA']['WI'] = 0`

    Parameters
    ----------
    keys_tuple : tuple
        Collect arguments into a tuple of keys for traversing the (nested) dictionary, the
        last element is the value to be set. Hence, this element is not used for traversing
        the dictionary.
    backup : bool
        Whether the previous state of the filter dict should be backed up (default: True)
    new_key : bool
        Whether a new key:value pair should be added to the dictionary (default: False).
        If False, an error is generated if the key does not exist, if True, a new key:value pair
        is added to the dictionary. If the key already exists, a warning is issued and the old
        value is overwritten (default: False).
    accept_dict : bool
        Allow a dictionary to be stored as a value in the filter dict, this speeds up storing
        complex data but is dangerous because the keys of the new dict might be different from
        the old dict (default: False).
    fil_dict : dict
        The dictionary to traverse.

    Returns
    -------
    int
        The error code; 0 for successful operation, -1 for an error

    Raises
    ------
    KeyError
        If a key does not exist in the dictionary or the tuple of keys is empty

    TypeError
        If `keys_tuple` is not of type Tuple or if it has less than two items
    """

    logger.debug("tuple_keys: %s", keys_tuple)

    if backup:
        backup_fil()  # backup old settings

    # Ensure that the tuple consisting of the passed keys is valid
    if not isinstance(keys_tuple, tuple):
        logger.error("A tuple of keys is needed for traversing the filter dict '%s', not a '%s'!",
                     keys_tuple, type(keys_tuple).__name__)
        raise TypeError

    if len(keys_tuple) < 2:
        if isinstance(keys_tuple[0], dict):  # top-level dict
            return _set_dict_subvalues(keys_tuple, fil_dict)

        logger.error("Only one parameter '%s'; key *and* value need to be given", keys_tuple)
        raise KeyError

    set_val = keys_tuple[-1]  # last element is the value to be set
    set_key = keys_tuple[-2]  # second last element is the key for setting

    try:
        # traverse nested dict 'fil_dict' using `keys_tuple` (without `set_val`)
        # and access subdictionary:
        d = _traverse_dict(keys_tuple[:-1], fil_dict)

        # Create a new key:value pair when flag `new_key` is True
        # --------------------------------------------------------
        if new_key:
            return _set_new_key(d, set_key, set_val)

        # Unknown key
        # -----------
        if set_key not in d:
            logger.error("Key '%s' not found in filter dictionary!", set_key )
            raise KeyError

        # Different types of old and new value, check if they are compatible
        # -------------------------------------------------------------------
        if type(set_val) is not type(d[set_key]):
            _ensure_type_compatible(d, set_key, set_val, keys_tuple)

        # Value to be set is a dict. When `accept_dict == True`, assign this dict
        # directly to `set_key` which is fast, but risky.
        # --------------------------------------------------------------
        if isinstance(set_val, dict) and not accept_dict:
            return _set_dict_subvalues(keys_tuple, fil_dict)

        # Set the global quantization format 'qfrmt'.
        # -------------------------------------------------------------------
        if set_key =='qfrmt':
            # Setting the global quantization format 'qfrmt' can change fixpoint mode, so
            # store the last used fixpoint or float format.
            _handle_qfrmt_change(keys_tuple, fil_dict)

            # ======== everything ok, finally update dictionary ========
        d[set_key] = set_val  # update key with new value
        logger.debug("Setting '%s' with value '%s'", _print_dict(keys_tuple[:-1]), set_val)
        # ==========================================================

    except TypeError:
        if backup:
            # Error, undo backup.
            restore_fil()
        return -1

    except KeyError:
        if backup:
            # Error, undo backup.
            restore_fil()
        return -1

    return 0


# =================
# Helper functions
# =================
def _set_new_key(d: dict, set_key: str, set_val: any) -> int:
    """ Create a new key:value pair when flag `new_key` is True """
    if set_key in d:
        logger.warning("Overwriting value '%s' for existing key '%s' in dictionary \n"
                        "\twith new value '%s'!", d[set_key], set_key, set_val)
    d[set_key] = set_val  # set new key:value pair
    return 0

# --------------
def _ensure_type_compatible(d: dict, set_key: str, set_val, keys_tuple: tuple[str]) -> None:
    """ check if two types are similar enough """
    # union of types of current and new value, e.g. {'float', 'float64'}
    types = {type(set_val).__name__, type(d[set_key]).__name__}
    # the following types are considered fully compatible
    if types.issubset({'float', 'float64'}):
        pass
    # the following types are considered mostlycompatible, just issue a warning
    elif types.issubset({'list', 'tuple', 'ndarray'}):
        logger.warning("Possible type mismatch: Setting\n\t'%s' of type '%s' with value "
                        "of similar type '%s'",
                        _print_dict(keys_tuple[:-1]), type(d[set_key]).__name__,
                        type(set_val).__name__)
    else:
        logger.error("Type mismatch: Refusing to set\n\t'%s' of type '%s' "
            "with value of type '%s'",
            _print_dict(keys_tuple[:-1]), type(d[set_key]).__name__,
            type(set_val).__name__)
        raise KeyError

# --------------
def _set_dict_subvalues(keys_tuple: tuple, fil_dict: dict):
    """
    `set_val == keys_tuple[-1]` is a dict, iterate over its keys
    to set the key-value pairs.
    """
    # get dict to be set from tuple, it's either the last or the only item
    d = keys_tuple[-1]

    for k, v in d.items():
        # Call `fb_set()` recursively to set k:v of the sub-dict `set_val`
        # Remove the sub-dict `set_val == keys_tuple[-1]` from `keys_tuple`
        fb_set(*keys_tuple[:-1], k, v, backup=False, new_key=False,
            accept_dict=False, fil_dict=fil_dict)
    return 0
# --------------
def _handle_qfrmt_change(keys_tuple: tuple, fil_dict: dict) -> None:
    """
    Setting the global quantization format 'qfrmt' can change fixpoint mode, so
    store the last used fixpoint or float format.
    """
    if len(keys_tuple) > 2:
        logger.error("More than one value '%s' for setting 'qfrmt'!", keys_tuple[1:])
        raise KeyError

    if get_fx():  # fixpoint mode, store current fixpoint format
        fil_dict['qfrmt_fx_last'] = fil_dict['qfrmt']
    else:  # float mode, store current float format
        fil_dict['qfrmt_float_last'] = fil_dict['qfrmt']

# -------------------------------------------------------------------------------
def load_cleaned_filter(fil_loaded: dict) -> int:
    """
    Sanitize loaded filter dictionary `fil_loaded` by comparing it to the reference dict `fil_ref`.
    If keys are missing in the loaded dict, they are copied with their default values from the
    reference dict. If unsupported keys are found, they are ignored and a warning is issued.

    Parameters
    ----------
    fil_loaded : dict
        The loaded filter dictionary to be sanitized.

    Returns
    -------
    int:
        0: Successful sanitization
        1: Error occurred during sanitization (e.g. missing keys or unsuitable data type/shape)


    """
    # --- Sanitize *keys* by comparing to reference dict -----------------------
    key_errs = compare_dictionaries(fil_ref, fil_loaded)
    key_errs[0].sort()  # keys missing in the loaded dict
    key_errs[1].sort()  # unsupported keys; keys not in reference dict

    err_str = ""
    if key_errs[0]:
        # '\n'.join(...) converts list to multi-line string
        err_str += (
            f"\n\tThe following {len(key_errs[0])} key(s) have not been found in "
            "the loaded dict,\n"\
            "\tthey are copied with their default values from the reference dict:\n\t\t"
                + "\n\t\t".join(key_errs[0])
            )
    if key_errs[1]:
        err_str += (
            f"\n\tThe following {len(key_errs[1])} key(s) are not part of the "
            "reference dict and have been ignored:\n\t\t"
            + "\n\t\t".join(key_errs[1])
        )
    if err_str != "":
        logger.warning(err_str)

    # sanitize some of the values of the loaded filter dict
    fil_loaded = sanitize_dict_values(fil_loaded)

    if not fil_loaded:
        return 1  # values could not be sanitized, return with an error

    fil[0] = fil_loaded  # update global filter dict with sanitized loaded dict
    return 0

# ---------------------------------------------------------
def clean_filter_keys(all_filters: bool = True) -> list[dict] | dict:
    """
    Test if the keys in the global dict `fil[0]` are identical to th the reference dict `fil_ref`.
    If not, remove the unsupported keys and issue a warning.

    Parameters
    ----------
    all_filters : bool
        If True, clean all filter dicts `fil[0]` ... `fil[9]`, otherwise only clean `fil[0]`.

    Returns
    -------
    list[dict] | dict
        The cleaned filter dict(s) with only the keys that are in the reference dict `fil_ref`.
    """
    def _clean_dict_i(i: int) -> dict:
        # provide identifier and version number for pyfda files
        fil[i].update({'_id': ['pyfda', FILTER_FILE_VERSION]})
        # only copy the keys that are in the reference dict, remove unsupported keys
        fil_clean_i = {k:v for k, v in fil[i].items() if k in fil_ref}
        keys_unsupported = [k for k in fil[i] if k not in fil_ref]
        if keys_unsupported != []:
            logger.warning(
                "The following keys are ignored because they are not part of the\n"
                "\tfilter reference dict:\n\t%s", keys_unsupported)
        return fil_clean_i

    if all_filters:
        fil_clean = [None] * 10
        for i in range(10):
            fil_clean[i] = _clean_dict_i(i)
    else:
        fil_clean = _clean_dict_i(0)

    return fil_clean

# ---------------------------------------------------------
def sanitize_dict_values(fil_dict: dict) -> dict | None:
    """
    Sanitize *values* of filter data entries ('sos', 'zpk', 'ba') in filter dictionary,
    they all should be NDArrays. If not, try to correct the data type or try to convert
    them from one of the other data entries. If this does not work, return error code 1.

    Parameters
    ----------
    fil_dict : dict
        The filter dict that will be stored as `fil[0]`.

    Returns
    -------
    dict | None:
        dict: dict with verified / cleaned values
        None: dict contained unrecoverable errors

    """
    for k in fil_dict:
        # Bytes need to be decoded for py3 to be used as keys later on
        if isinstance(fil_dict[k], bytes):
            fil_dict[k] = fil_dict[k].decode('utf-8')
        if fil_dict[k] is None:
            logger.warning("fil[%s] is empty!", k)

    if 'ba' not in fil_dict:
        logger.error(
            "Missing key 'ba', cancelling file operation.")
        return None

    # check whether d['ba'] is an iterable
    if not isinstance(fil_dict['ba'], (np.ndarray, list, tuple)):
        logger.error("Unsuitable 'ba' data type '%s', cancelling file operation.",
                        type(fil_dict['ba']).__name__)
        return None

    # check whether data has correct dimensions
    if np.ndim(fil_dict['ba']) != 2 or len(fil_dict['ba'][0]) < 3:
        logger.error(
            "Unsuitable shape %s of 'ba' data, cancelling file operation.",
            np.shape(fil_dict['ba']))
        return None

    elif isinstance(fil_dict['ba'], (list, tuple)):
        # convert list / tuple to numpy array
        fil_dict['ba'] = iter2ndarray(fil_dict['ba'])

    # check whether d['zpk'] is an NDArray
    if 'zpk' not in fil_dict:
        logger.error("Missing key 'zpk', cancelling file operation.")
        return None

    if not isinstance(fil_dict['zpk'], (np.ndarray, list, tuple)):
        logger.error("Unsuitable 'zpk' data type '%s', cancelling file operation.",
                        type(fil_dict['zpk']).__name__)

    if np.ndim(fil_dict['zpk']) != 2 or np.shape(fil_dict['zpk'])[0] != 3:
        logger.error(
            "Unsuitable shape %s of 'zpk' data, cancelling file operation.",
            np.shape(fil_dict['zpk']))
        return None

    if isinstance(fil_dict['zpk'], (list, tuple)):
        # convert list / tuple to numpy array
        fil_dict['zpk'] = iter2ndarray(fil_dict['zpk'])

    # check whether d['sos'] is an NDArray of shape 2 x 6
    if 'sos' not in fil_dict:
        logger.error("Missing key 'sos', creating key and empty entry.")
        fil_dict['sos'] = []

    if not isinstance(fil_dict['sos'], (np.ndarray, list, tuple)):
        logger.error("Unsuitable 'sos' data type '%s', creating empty entry.",
                        type(fil_dict['sos']).__name__)
        fil_dict['sos'] = []

    elif np.ndim(fil_dict['sos']) != 2 or np.shape(fil_dict['sos'])[1] != 6:
        logger.warning("Unsuitable shape %s of 'sos' data, creating empty entry.",
            np.shape(fil_dict['sos']))
        fil_dict['sos'] = []

    elif isinstance(fil_dict['sos'], (list, tuple)):
        fil_dict['sos'] = iter2ndarray(fil_dict['sos'])

    return fil_dict

# ------------------------------------------------------------------------------
class _BackupFilterDict():
    """
    Back up and restore the global filter dict `fil[0]`.

    """
    def __init__(self):
        # undo step, limited to 0 ... UNDO_LEN. This prevents exceeding the available
        # UNDO_LEN memories and trying to restore more than the stored copies
        self.undo_stp = 0
        self.undo_ptr = 0  # pointer to current undo memory % UNDO_LEN

    def restore_fil(self) -> int:
        """
        Restore current global dict `fil[0]` from undo memory `fil_undo`

        Returns
        -------
        int
            -1: undo buffer empty, nothing restored
            0: successful restore
        """

        # undo buffer is empty, don't restore anything
        if self.undo_stp < 1:
            self.undo_stp = 0
            return -1

        fil[0] = copy.deepcopy(fil_undo[undo_ptr])
        self.undo_stp -= 1
        self.undo_ptr = (self.undo_ptr + UNDO_LEN - 1) % UNDO_LEN
        return 0

    # -------------------------
    def backup_fil(self) -> int:
        """
        Store current global dict `fil[0]` to undo memory `fil_undo`

        Returns
        -------
        int
            undo step, limited to 0 ... UNDO_LEN
        """

        # prevent buffer overflow
        self.undo_stp += 1
        self.undo_stp = min(self.undo_stp, UNDO_LEN)
        # increase buffer pointer, allowing for circular wrap around
        self.undo_ptr = (self.undo_ptr + 1) % UNDO_LEN
        fil_undo[self.undo_ptr] = copy.deepcopy(fil[0])
        logger.debug("Undo ptr = %s", self.undo_ptr)
        return self.undo_stp

# -------------------------------------------------
_backup_filter_dict = _BackupFilterDict()
# import this from other modules
backup_fil = _backup_filter_dict.backup_fil
restore_fil = _backup_filter_dict.restore_fil
# -------------------------------------------------

# ===============================================================================================

if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.filterbroker`
    logging.basicConfig()  # setup a basic logger

    print('zpk: ' + str(fb_get('zpk', 0)))
    print('fxq QACC WF: ' + str(fb_get('fxq', 'QACC', 'WF')))
    print('fxq QI WF: ' + str(fb_get('fxq', 'QI', 'WF')))
    fb_set('ft', 'CIC')
    print('ft: ' + str(fb_get('ft')))
    fb_set('ft', 23)  # wrong type, should be str
    fb_set('xxx', 13)  # key does not exist
    fb_set('xxx', 13, new_key=True)  # create new key
    print('xxx: ' + str(fb_get('xxx')))  # ... and read it back
    fb_set('fxq', 'QACC', 'WF', 12)  # set a key within a sub-dict
    print('fxq QACC WF: ' + str(fb_get('fxq', 'QACC', 'WF')))  # ... and read it back
    print('fxq QACC 1: ' + str(fb_get('fxq', 'QACC')))  # ... and read the whole sub-dict
    fb_set('fxq', 'QACC', {'WF': 1, 'WI': 2})  # set a sub-dict
    print('fxq QACC 2: ' + str(fb_get('fxq', 'QACC')))  # ... and read it back
    fb_set('fxq', 'QACC', {'WF': 1, 'WA': 2, 'quant': 'well...'})  # set a sub-dict with wrong key
    print('fxq QACC 3: ' + str(fb_get('fxq', 'QACC')))  # ... and read it back

    fb_set('fxq', {'QACC': {'WF': 49, 'WI': 50}})  # set a nested sub-dict
    print('fxq QACC 4: ' + str(fb_get('fxq', 'QACC')))  # ... and read it back
    fb_set('fxq', 'QACC', {'WF': 'a', 'WI': 5, 'N_over': 7})  # wrong type for WF
    print('fxq QACC 5: ' + str(fb_get('fxq', 'QACC')))  # ... and read it back
