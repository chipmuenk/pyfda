# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Read the class dictionaries from ConfigFileParser and create a hierarchical filter_tree
dict with all filter response types as top level keys.
"""
import logging
import sys
from typing import ClassVar

from pyfda.filter_factory import get_fil_inst, create_fil_inst
from pyfda.config_file_parser import ConfigFileParser as CFP

from pyfda.libs import frozendict

logger = logging.getLogger(__name__)

REQ_VERSION = 4  # required version for config file

# --------------------------------------------------------------------------
def merge_dicts_hierarchically(d1: dict, d2: dict, path: str = "", mode: str = "keep1") -> dict:
    """
    Merge the hierarchical dictionaries ``d1`` and ``d2``.  The dict ``d1`` is
    modified in place and returned

    Parameters
    ----------
    d1 : dict
        hierarchical dictionary 1

    d2 : dict
        hierarchical dictionary 2

    mode : str
        Select the behaviour when the same key is present in both dictionaries:

        * :'keep1': keep the entry from ``d1`` (default)

        * :'keep2': keep the entry from ``d2``

        * :'add1': merge the entries, putting the values from ``d2`` first
                    (important for lists)

        * :'add2': merge the entries, putting the values from ``d1`` first (  "  )

    path : str
        internal parameter for keeping track of hierarchy during recursive calls,
        it should not be set by the user

    Returns
    -------
    d1 : dict
        a reference to the first dictionary, merged-in-place.

    Example
    -------
    >>> merge_dicts_hierarchically(fil_tree, fil_tree_add, mode='add1')

    Notes
    -----
    If you don't want to modify ``d1`` in place, call the function using:

    >>> new_dict = merge_dicts_hierarchically(dict(d1), d2)

    If you need to merge more than two dicts use:

    >>> from functools import reduce   # only for py3
    >>> reduce(merge, [d1, d2, d3...]) # add / merge all other dicts into d1

    Taken with some modifications from:

    http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
    """
    if not(isinstance(d1, dict) and isinstance(d2, dict)):
        # at least one of the arguments is not a dict -> don't do anything
        return d1

    for key in d2:
        if key in d1:
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                # both entries are dicts, recurse one level deeper:
                merge_dicts_hierarchically(d1[key], d2[key], path=path + str(key), mode=mode)
# TODO:            elif <either d1[key] OR d2[key] is not a dict> -> exception
            elif d1[key] == d2[key] or mode == 'keep1':
                pass  # keep item in dict1, discard item with same key in dict1
            elif mode == 'keep2':
                d1[key] = d2[key]  # replace item in dict1 by item in dict2
            else:
                try:
                    if mode == 'add2':
                        if (isinstance(d1[key], tuple) and
                                isinstance(d2[key], tuple)):
                            d1[key] = (d2[key][0], d2[key][1] + d1[key][1])
                        else:
                            d1[key] = d2[key] + d1[key]

                    elif mode == 'add1':
                        if (isinstance(d1[key], tuple) and
                                isinstance(d2[key], tuple)):
                            d1[key] = (d1[key][0], d1[key][1] + d2[key][1])
                        else:
                            d1[key] = d1[key] + d2[key]

                    else:
                        logger.warning("Unknown merge mode %s.", mode)
                except (TypeError, IndexError) as e:
                    logger.warning("Merge conflict at %s: %s", path + str(key), e)
        else:
            d1[key] = d2[key]  # add new entry to dict1
    return d1


class ParseError(Exception):
    """
    Exception raised when parsing filter tree data fails.

    This exception is used by :mod:`pyfda.tree_builder` when the
    configuration data for a filter tree cannot be interpreted or
    merged correctly.
    """


class FilterTreeBuilder():
    """
    Read the config file and construct the `fil_tree` dictionary as a class attribute with

    - all filter combinations
    - valid combinations of filter widgets and fixpoint implementations
    """
    # --------------------------------------------------------------------------
    # Filter tree dict as a class variable: Assigning this in an instance
    # shadows the class variable!
    # Example for dict with available combinations of response types (rt),
    # filter types (ft), filter class (fc) and filter order (fo).
    # This default dictionary is overwritten and frozen during initialization.

    # Dictionary with translations between short method names and long names for
    # response types - the long name can be changed as you like, but don't change
    # the short name - it is used to construct the filter design method names
    RT_NAMES = {'lp': 'Lowpass', 'hp': 'Highpass', 'bp': 'Bandpass',
                'bs': 'Bandstop', 'ap': 'Allpass', 'mb': 'Multiband',
                'hil': 'Hilbert', 'diff': 'Differentiator'}

    # Dictionary with translations between short method names and long names for
    # response types
    FT_NAMES = {'IIR': 'IIR', 'FIR': 'FIR'}

    fil_tree: ClassVar[dict[str, object]] =\
        {
        'lp': {
            'FIR': {
                'Equiripple': {
                    'man':{'fo':     ('a', 'N'),
                        'fspecs': ('a', 'F_C'),
                        'wspecs': ('a', 'W_PB', 'W_SB'),
                        'tspecs': ('u', {'frq': ('u', 'F_PB', 'F_SB'),
                                            'amp': ('u', 'A_PB', 'A_SB')}),
                        'msg':    ('a',
                                    'Enter desired filter order <b><i>N</i></b>, corner '
            'frequencies of pass and stop band(s), <b><i>F<sub>PB</sub></i></b>'
            '&nbsp; and <b><i>F<sub>SB</sub></i></b>, and a weight '
            'value <b><i>W</i></b>&nbsp; for each band.'
                                    )
                            },
                    'min':{'fo':     ('d', 'N'),
                        'fspecs': ('d', 'F_C'),
                        'wspecs': ('d', 'W_PB', 'W_SB'),
                        'tspecs': ('a', {'frq': ('a', 'F_PB', 'F_SB'),
                                            'amp': ('a', 'A_PB', 'A_SB')}),
                        'msg':    ('a',
                'Enter maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, '
                'minimum stop band attenuation <b><i>A<sub>SB</sub> </i></b>'
                '&nbsp;and the corresponding corner frequencies of pass and '
                'stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and '
                '<b><i>F<sub>SB</sub></i></b> .'
                                        )
                        },
                    }
                },
            'IIR': {
                'Cheby1': {
                    'man':{'fo':     ('a', 'N'),
                        'fspecs': ('a', 'F_C'),
                        'tspecs': ('u', {'frq': ('u', 'F_PB', 'F_SB'),
                                            'amp': ('u', 'A_PB', 'A_SB')})
                        },
                    'min':{'fo':     ('d', 'N'),
                        'fspecs': ('d', 'F_C'),
                        'tspecs': ('a', {'frq': ('a', 'F_PB', 'F_SB'),
                                            'amp': ('a', 'A_PB', 'A_SB')})
                        }
                    }
                }
            },
        'hp': {
            'FIR': {
                'Equiripple': {
                    'man':{'fo':     ('a', 'N'),
                        'fspecs': ('a', 'F_C'),
                        'wspecs': ('a', 'W_SB', 'W_PB'),
                        'tspecs': ('u', {'frq': ('u', 'F_SB', 'F_PB'),
                                            'amp': ('u', 'A_SB', 'A_PB')})
                        },
                    'min':{'fo':     ('d', 'N'),
                        'wspecs': ('d', 'W_SB', 'W_PB'),
                        'fspecs': ('d', 'F_C'),
                        'tspecs': ('a', {'frq': ('a', 'F_SB', 'F_PB'),
                                            'amp': ('a', 'A_SB', 'A_PB')})
                        }
                        }
                },
            'IIR': {
                'Cheby1': {
                    'man':{'fo':     ('a', 'N'),
                        'fspecs': ('a', 'F_C'),
                        'tspecs': ('u', {'frq': ('u', 'F_SB', 'F_PB'),
                                            'amp': ('u', 'A_SB', 'A_PB')})
                        },
                    'min':{'fo':     ('d', 'N'),
                        'fspecs': ('d', 'F_C'),
                        'tspecs': ('a', {'frq': ('a', 'F_SB', 'F_PB'),
                                            'amp': ('a', 'A_SB', 'A_PB')})
                        }
                        }
                    }
            },
        'bp': {
            'FIR': {
                'Equiripple': {
                    'man':{'fo':     ('a', 'N'),
                        'wspecs': ('a', 'W_SB', 'W_PB', 'W_SB2'),
                        'fspecs': ('a', 'F_C', 'F_C2'),
                        'tspecs': ('u', {'frq': ('u', 'F_SB', 'F_PB', 'F_PB2', 'F_SB2'),
                                            'amp': ('u', 'A_SB', 'A_PB', 'A_SB2')})
                        },
                    'min':{'fo':     ('d', 'N'),
                        'fspecs': ('d', 'F_C', 'F_C2'),
                        'wspecs': ('d', 'W_SB', 'W_PB', 'W_SB2'),
                        'tspecs': ('a', {'frq': ('a', 'F_SB', 'F_PB', 'F_PB2', 'F_SB2'),
                                            'amp': ('a', 'A_SB', 'A_PB', 'A_SB2')})
                        }
                        }
                    }
                },
        'bs': {
            'FIR': {
                'Equiripple': {
                    'man':{'fo':     ('a', 'N'),
                        'wspecs': ('a', 'W_PB', 'W_SB', 'W_PB2'),
                        'fspecs': ('a', 'F_C', 'F_C2'),
                        'tspecs': ('u', {'frq': ('u', 'F_PB', 'F_SB', 'F_SB2', 'F_PB2'),
                                            'amp': ('u', 'A_PB', 'A_SB', 'A_PB2')})
                        },
                    'min':{'fo':     ('d', 'N'),
                        'wspecs': ('d', 'W_PB', 'W_SB', 'W_PB2'),
                        'fspecs': ('d', 'F_C', 'F_C2'),
                        'tspecs': ('a', {'frq': ('a', 'F_PB', 'F_SB', 'F_SB2', 'F_PB2'),
                                            'amp': ('a', 'A_PB', 'A_SB', 'A_PB2')})
                        }
                            }
                    }
            }
        }
    # --------------------------------------------------------------------------

    def __init__(self):
        logger.info("This is TreeBuilder, not doing anything.")

    # --------------------------------------------------------------------------
    def build_fil_tree(self) -> None:
        """
        Run at startup from `pyfdax.py` to populate class attribute dictionaries and lists:

        Read attributes (`ft`, `rt`, `fo`) from all valid filter classes (`fc`)
        of the class attribute ``CFP.FILTER_CLASSES_DICT`` and return them as a frozen dict
        `fil_tree` with the hierarchy

        **rt-ft-fc-fo-subwidget:params** .

        Parameters
        ----------
        None

        Returns
        -------
        fil_tree : FrozenDict | None
            A frozen hierarchical dictionary with all filter combinations.

        """
        logger.info("Instantiating filter classes, building filter tree ...\n")

        fil_tree = {}

        for fc in CFP.FILTER_CLASSES_DICT:  # iterate over all previously found filter
                                            # classes fc

            # try to instantiate filter class fc
            err_code = create_fil_inst(fc)
            if err_code > 0:
                logger.warning(
                    'Skipping filter class "%s" due to import error %d', fc, err_code)
                continue  # continue with next entry in CFP.FILTER_CLASSES_DICT

            # add attributes from `rt_dict` to `fil_tree`` for filter class fc
            fil_tree = self._build_fil_tree_fc(fc, get_fil_inst().rt_dict, fil_tree)

            # merge optional instance specific `rt_dict_add` into `fil_tree`:
            if hasattr(get_fil_inst(), 'rt_dict_add'):
                fil_tree_add = self._build_fil_tree_fc(fc, get_fil_inst().rt_dict_add)
                merge_dicts_hierarchically(fil_tree, fil_tree_add, mode='add1')

        # Make the dictionary and all sub-dictionaries read-only ("FrozenDict"):
        FilterTreeBuilder.fil_tree = frozendict.freeze_hierarchical(fil_tree)

    # --------------------------------------------------------------------------
    def _build_fil_tree_fc(self, fc: str, rt_dict: dict[str, dict], fil_tree: dict = None) -> dict:
        """
        Read attributes (ft, rt, rt:fo) from attribute `rt_dict` of filter class ``fc``.
        Sort the attributes and return them as a dict with the parameters to be displayed and
        whether they are active, unused, disabled or invisible for each response type (`rt`)
        of the filter class.

        Parameters
        ----------
        fc : str
            filter class name (e.g. 'Equiripple', 'Cheby1')

        rt_dict : dict
            dictionary with response type information as defined in the filter class

        fil_tree : dict, optional
            existing filter tree to be extended (default: None -> create new tree)

        Returns
        -------
        dict
            filter tree

        Example
        -------
        Structure of `rt_dict` (taken from ``common.py``):

        .. code-block:: python

            self.rt_dict = {
                     'lp': {'man':{'fo':     ('a','N'),
                                   'msg':    ('a', r"<br /><b>Note:</b> Read this!"),
                                   'fspecs': ('a','F_C'),
                                   'tspecs': ('u', {'frq':('u','F_PB','F_SB'),
                                                    'amp':('u','A_PB','A_SB')})
                                  },
                           'min':{'fo':     ('d','N'),
                                  'fspecs': ('d','F_C'),
                                  'tspecs': ('a', {'frq':('a','F_PB','F_SB'),
                                                   'amp':('a','A_PB','A_SB')})
                                }
                          },
                    'hp': {'man':{'fo':     ('a','N'),
                                  'fspecs': ('a','F_C'),
                                  'tspecs': ('u', {'frq':('u','F_SB','F_PB'),
                                                   'amp':('u','A_SB','A_PB')})
                                 },
                           'min':{'fo':     ('d','N'),
                                  'fspecs': ('d','F_C'),
                                  'tspecs': ('a', {'frq':('a','F_SB','F_PB'),
                                                   'amp':('a','A_SB','A_PB')})
                                 }
                          }
                    }

        Build a dictionary of all filter combinations with the following hierarchy:

        response types -> filter types -> filter classes  -> filter order
        rt (e.g. 'lp')    ft (e.g. 'IIR') fc (e.g. 'cheby1') fo ('min' or 'man')

        Resulting dictionary for fc for the example above:

        .. code-block:: python

            'lp':{
            'IIR':{
                 'Cheby1':{
                     'man':{'fo':     ('a','N'),
                            'msg':    ('a', r"<br /><b>Note:</b> Read this!"),
                            'fspecs': ('a','F_C'),
                            'tspecs': ('u', {'frq':('u','F_PB','F_SB'),
                                             'amp':('u','A_PB','A_SB')})
                            },
                     'min':{'fo':     ('d','N'),
                            'fspecs': ('d','F_C'),
                            'tspecs': ('a', {'frq':('a','F_PB','F_SB'),
                                             'amp':('a','A_PB','A_SB')})
                            }
                         }
                   }
             }, ...

        For a full example of the resulting dict, see the default filter tree ``fil_tree``.

        """
        if not fil_tree:
            fil_tree = {}

        ft = get_fil_inst().ft                 # get filter type (e.g. 'FIR')

        for rt in rt_dict:                     # iterate over all response types
            if rt == 'COM':                    # handle common info later
                continue

            if rt not in fil_tree:             # is response type already in dict?
                fil_tree.update({rt: {}})      # no, create it

            if ft not in fil_tree[rt]:         # filter type already in dict[rt]?
                fil_tree[rt].update({ft: {}})  # no, create it

            if fc not in fil_tree[rt][ft]:         # filter class already in dict[rt][ft]?
                fil_tree[rt][ft].update({fc: {}})  # no, create it

            # now append all the individual 'min' / 'man'  subwidget infos to fc:
            fil_tree[rt][ft][fc].update(rt_dict[rt])

            if 'COM' in rt_dict:      # Now handle common info
                for fo in rt_dict[rt]:  # iterate over 'min' / 'max'
                    if fo in rt_dict['COM']:  # and add common info first
                        merge_dicts_hierarchically(fil_tree[rt][ft][fc][fo],
                                    rt_dict['COM'][fo], mode='add2')

        return fil_tree


# ==============================================================================
if __name__ == "__main__":
    # Run widget standalone with `python -m pyfda.tree_builder`
    #
    # Need to start a QApplication to avoid the error
    #  "QWidget: Must construct a QApplication before a QWidget"
    # when instantiating filters with dynamic widgets (equiripple, firwin)
    from pyfda.libs.compat import QApplication
    from pyfda.libs.pyfda_lib import pprint_log
    app = QApplication(sys.argv)
    logging.basicConfig(level=logging.INFO)

    # Initialize FilterTreeBuilder class attribute 'fil_tree'
    FilterTreeBuilder().build_fil_tree()

    fil_tree_ref = FilterTreeBuilder.fil_tree['lp']['FIR']['Equiripple']['min']
    # Test Immutability - the following lines should all raise an exception
    try:
        fil_tree_ref.update({'msg':("hallo",)}) # this would change 'fil_tree'
    except AttributeError as e:
        print(f"\nExpected AttributeError on update(): {e}\n")

    try:
        FilterTreeBuilder.fil_tree['lp']['FIR']['Equiripple']['min']['par'] = ("A_1","F_1")
    except TypeError as e:
        print(f"\nExpected TypeError on item assignment: {e}\n")

    print(f"\nDict type: {type(FilterTreeBuilder.fil_tree['lp']['FIR']['Equiripple']).__name__}\n")

    print('FilterTreeBuilder.fil_tree["BP"] = ', pprint_log(FilterTreeBuilder.fil_tree["BP"]))
