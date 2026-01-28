# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create the tree dictionaries containing information about filters,
filter implementations, widgets etc. in hierarchical form
"""
import logging
import sys
from typing import ClassVar

import pyfda.filterbroker as fb
import pyfda.filter_factory as ff
from pyfda.config_file_parser import ConfigFileParser as cfp

import pyfda.libs.frozendict as frozendict

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
                except Exception as e:
                    logger.warning("Merge conflict at %s: %s", path + str(key), e)
        else:
            d1[key] = d2[key]  # add new entry to dict1
    return d1


class ParseError(Exception):
    pass


class Tree_Builder():
    """
    Read the config file and construct dictionary trees with

    - all filter combinations
    - valid combinations of filter widgets and fixpoint implementations
    """
    # --------------------------------------------------------------------------
    # Class attribute: Default filter tree structure:
    # Example for dict with the available combinations of response types (rt),
    # filter types (ft), filter class (fc) and filter order (fo).
    # This dictionary is overwritten during initialization as a frozendict.
    #
    # TODO: Move fil_tree from filterbroker to here

    fil_tree: ClassVar[dict[str, object]] =\
        {
        'LP': {
            'FIR': {
                'Equiripple': {
                    'man':{'fo':     ('a', 'N'),
                        'fspecs': ('a', 'F_C'),
                        'wspecs': ('a', 'W_PB', 'W_SB'),
                        'tspecs': ('u', {'frq': ('u', 'F_PB', 'F_SB'),
                                            'amp': ('u', 'A_PB', 'A_SB')}),
                        'msg':    ('a',
                                    "Enter desired filter order <b><i>N</i></b>, corner "
            "frequencies of pass and stop band(s), <b><i>F<sub>PB</sub></i></b>"
            "&nbsp; and <b><i>F<sub>SB</sub></i></b>, and a weight "
            "value <b><i>W</i></b>&nbsp; for each band."
                                    )
                            },
                    'min':{'fo':     ('d', 'N'),
                        'fspecs': ('d', 'F_C'),
                        'wspecs': ('d', 'W_PB', 'W_SB'),
                        'tspecs': ('a', {'frq': ('a', 'F_PB', 'F_SB'),
                                            'amp': ('a', 'A_PB', 'A_SB')}),
                        'msg':    ('a',
                "Enter maximum pass band ripple <b><i>A<sub>PB</sub></i></b>, "
                "minimum stop band attenuation <b><i>A<sub>SB</sub> </i></b>"
                "&nbsp;and the corresponding corner frequencies of pass and "
                "stop band(s), <b><i>F<sub>PB</sub></i></b>&nbsp; and "
                "<b><i>F<sub>SB</sub></i></b> ."
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
        'HP': {
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
        'BP': {
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
        'BS': {
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
        logger.info("Instantiating TreeBuilder")

    # --------------------------------------------------------------------------
    def init_filters(self) -> 'frozendict.FrozenDict':
        """
        Run at startup from `pyfdax.py` to populate "global" dictionaries and lists:

        Read attributes (`ft`, `rt`, `fo`) from all valid filter classes (`fc`)
        in the global dict ``cfp.FILTER_CLASSES_DICT`` and return them as a frozen dict
        tree dict with the hierarchy

        **rt-ft-fc-fo-subwidget:params** .

        Parameters
        ----------
        None

        Returns
        -------
        fil_tree : FrozenDict
            A frozen hierarchical dictionary with all filter combinations.

        """
        logger.info("Instantiating filter classes, building filter tree ...\n")

        fil_tree = {}

        for fc in cfp.FILTER_CLASSES_DICT:  # iterate over all previously found filter
                                            # classes fc

            # instantiate a global instance ff.fil_inst() of filter class fc
            err_code = ff.fil_factory.create_fil_inst(fc)
            if err_code > 0:
                logger.warning(
                    'Skipping filter class "%s" due to import error %d', fc, err_code)
                continue  # continue with next entry in cfp.FILTER_CLASSES_DICT

            # add attributes from dict to fil_tree for filter class fc
            fil_tree = self._build_fil_tree(fc, ff.fil_inst.rt_dict, fil_tree)

            # merge additional rt_dict (optional) into filter tree
            if hasattr(ff.fil_inst, 'rt_dict_add'):
                fil_tree_add = self._build_fil_tree(fc, ff.fil_inst.rt_dict_add)
                merge_dicts_hierarchically(fil_tree, fil_tree_add, mode='add1')

            # Test Immutability
            # fil_tree_ref = tb.fil_tree['LP']['FIR']['Equiripple']['min']
            # fil_tree_ref.update({'msg':("hallo",)}) # this changes  tb.fil_tree !!
            # tb.fil_tree['LP']['FIR']['Equiripple']['min']['par'] = ("A_1","F_1")
            # print(type(tb.fil_tree['LP']['FIR']['Equiripple']))

        # Make the dictionary and all sub-dictionaries read-only ("FrozenDict"):
        return frozendict.freeze_hierarchical(fil_tree)



    # --------------------------------------------------------------------------
    def _build_fil_tree(self, fc: str, rt_dict: dict, fil_tree: dict = None) -> dict:
        """
        Read attributes (ft, rt, rt:fo) from filter class where they are stored
        in the following format (example from ``common.py``):

        .. code-block:: python

            self.ft = 'IIR'
            self.rt_dict = {
                     'LP': {'man':{'fo':     ('a','N'),
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
                    'HP': {'man':{'fo':     ('a','N'),
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
        rt (e.g. 'LP')    ft (e.g. 'IIR') fc (e.g. 'cheby1') fo ('min' or 'man')

        All attributes found for fc are arranged in a dict, e.g.
        for ``cheby1.LPman`` and ``cheby1.LPmin``, listing the parameters to be
        displayed and whether they are active, unused, disabled or invisible for
        each subwidget:

        .. code-block:: python

            'LP':{
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

        Finally, the whole structure is frozen recursively to prevent inadvertedly
        changing the filter tree.

        For a full example, see the default filter tree ``fil_tree``.

        Parameters
        ----------
        fc : str
            filter class name (e.g. 'Equiripple', 'Cheby1')

        rt_dict : dict
            dictionary with response type information as defined in the filter class

        fil_tree : dict, optional
            existing filter tree to be extended (default is None)

        Returns
        -------
        dict
            filter tree

        """
        if not fil_tree:
            fil_tree = {}

        ft = ff.fil_inst.ft                    # get filter type (e.g. 'FIR')

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
    from .compat import QApplication
    from pyfda.libs.pyfda_lib import pprint_log
    app = QApplication(sys.argv)
    logging.basicConfig(level=logging.INFO)

    # Create a new Tree_Builder instance & initialize it
    tbl = Tree_Builder()
    filterTree = tbl.init_filters()
    print('fb.fil_tree = ', pprint_log(fb.fil_tree))
