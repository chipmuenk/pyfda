# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

"""
from __future__ import print_function, division, unicode_literals, absolute_import
import os, sys, six
from pprint import pformat
import codecs
import importlib

import logging
logger = logging.getLogger(__name__)

import pyfda.filterbroker as fb
import pyfda.filter_factory as ff

from .frozendict import freeze_hierarchical

#--------------------------------------------------------------------------
def merge_dicts(d1, d2, path=None, mode='keep1'):
    """
    Merge the multi-level dictionaries d1 and d2. The ``mode`` flag determines the
    behaviour when the same key is present in both dictionaries:

    * keep1 : keep the entry from dict1
    * keep2 : keep the entry from dict2
    * add1  : merge the entries, putting the values from dict2 first (important for lists)
    * add2  : merge the entries, putting the values from dict1 first (  "  )

    The parameter ``path`` is only used for keeping track of the hierarchical structure
    for error messages, it should not be set when calling the function.

    dict1 is modified in place and returned, if this is not intended call the
    function using ``new_dict = merge_dicts(dict(d1), d2).

    If you need to merge more than two dicts use:

    from functools import reduce   # only for py3
    reduce(merge, [d1, d2, d3...]) # add / merge all other dicts into d1

    Taken with some modifications from:
    http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge
    """
    if not(isinstance(d1, dict) and isinstance(d2, dict)):
        # at least one of the arguments is not a dict -> don't do anything
        return d1

    if path is None: path = ""
    for key in d2:
        if key in d1:
            if isinstance(d1[key], dict) and isinstance(d2[key], dict):
                # both entries are dicts, recurse one level deeper:
                merge_dicts(d1[key], d2[key], path = path + str(key), mode=mode)
#TODO:            elif <either d1[key] OR d2[key] is not a dict> -> exception
            elif d1[key] == d2[key] or mode == 'keep1':
                pass  # keep item in dict1, discard item with same key in dict1
            elif mode == 'keep2':
                d1[key] = d2[key] # replace item in dict1 by item in dict2
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
                        logger.warning("Unknown merge mode {0}.".format(mode))
                except Exception as e:
                    logger.warning("Merge conflict at {0}: {1}".format(path + str(key), e ))
        else:
            d1[key] = d2[key] # add new entry to dict1
    return d1


class FilterTreeBuilder(object):
    """
    Construct a tree with all the filter combinations

    Parameters
    ----------

    filt_dir: string
        Name of the subdirectory containing the init-file and the
        Python files to be read, needs to have __init__.py)

    filt_list_file: string
        Name of the init file

    comment_char: char
        comment character at the beginning of a comment line

    """

    def __init__(self, filt_dir, filt_list_file, comment_char='#'):
        cwd = os.path.dirname(os.path.abspath(__file__))
        self.filt_dir_file = os.path.join(cwd, filt_dir, filt_list_file)

        logger.debug("Filter file list: %s\n", self.filt_dir_file)
        self.comment_char = comment_char
        self.filt_dir = filt_dir

        self.init_filters()

#==============================================================================
    def init_filters(self):
        """
        - Extract the names of all Python files in the file specified during
          instantiation (self.filt_dir_file) and write them to a list
        - Try to import all python files and return a dict with all file names
          and corresponding objects (the class needs to have the same name as
          the file)
        - Construct a tree with all the filter combinations

        This method can also be called when the main app runs to re-read the
        filter directory
        """
        # Scan filter_list.txt for python file names and extract them
        filt_list_names = self.read_filt_file()

        # Try to import all filter modules and classes found in filter_list,
        # store names and modules in the dict fb.fil_classes as {filterName:filterModule}:
        self.dyn_filt_import(filt_list_names)

        """
        Read attributes (ft, rt, fo) from all valid filter classes (fc)
        listed in the global dict ``fb.fil_classes`` and store them in a filter
        tree dict with the hierarchy
                                        rt-ft-fc-fo-subwidget:params.
        """

        fil_tree = {}

        for fc in fb.fil_classes:  # iterate over all previously found filter classes fc

            # instantiate a global instance ff.fil_inst() of filter class fc
            err_code = ff.fil_factory.create_fil_inst(fc)
            if err_code > 0:
                logger.warning('Skipping filter class "%s" due to import error %d', fc, err_code)
                continue # continue with next entry in fb.fil_classes

            # add attributes from dict to fil_tree for filter class fc
            fil_tree = self.build_fil_tree(fc, ff.fil_inst.rt_dict, fil_tree)

            # merge additional rt_dict (optional) into filter tree
            if hasattr(ff.fil_inst, 'rt_dict_add'):
                fil_tree_add = self.build_fil_tree(fc, ff.fil_inst.rt_dict_add)
                merge_dicts(fil_tree, fil_tree_add, mode='add1')


        # Make the dictionary and all sub-dictionaries read-only ("FrozenDict"):
        fb.fil_tree = freeze_hierarchical(fil_tree)

        # Test Immutatbility
#        fil_tree_ref = fb.fil_tree['LP']['FIR']['Equiripple']['min']
#        fil_tree_ref.update({'msg':("hallo",)}) # this changes  fb.fil_tree !!
#        fb.fil_tree['LP']['FIR']['Equiripple']['min']['par'] = ("A_1","F_1")
#        print(type(fb.fil_tree['LP']['FIR']['Equiripple']))

        logger.debug("\nfb.fil_tree =\n%s", pformat(fb.fil_tree))


#==============================================================================
    def read_filt_file(self):
        """
        Extract all file names = class names from self.filt_dir_file:

        - Lines that don't begin with commentCh are stripped from Newline
          character, whitespace, '.py' and everything after it and returned as
          a list.
        - Lines starting with self.comment_char are stripped of newline,
          whitespace and comment chars and written to list 'filt_list_comments'
        - All other lines are discarded (for now)
        - Collect and return valid file names (without .py) as `filt_list_names`.

        Parameters
        ----------
        None

        Returns
        -------
        List `filt_list_names` with the names of all design files
        """

        filt_list_comments = []     # comment lines from filt_list_file (not used yet)
        # List with filter design file names in filt_list_file without .py suffix:
        filt_list_names = []

        num_filters = 0           # number of filter design files found

        try:
            # Try to open filt_dir_file in read mode:
            fp = codecs.open(self.filt_dir_file, 'rU', encoding='utf-8')
            cur_line = fp.readline()

            while cur_line: # read until currentLine is empty (EOF reached)
#                cur_line = cur_line.encode('UTF-8') # enforce utf-8
                # remove white space and Newline characters at beginning and end:
                cur_line = cur_line.strip(' \n')
                # Only process line if it is longer than 1 character
                if len(cur_line) > 1:
                    # Does current line begin with the comment character?
                    if cur_line[0] == self.comment_char:
                        # yes, append line to list filt_list_comments :
                        filt_list_comments.append((cur_line[1:]))
                    # No, this is not a comment line
                    else:
                        # Is '.py' contained in cur_line? Starting at which pos?
                        suffix_pos = cur_line.find(".py")
                        if suffix_pos > 0:
                            # Yes, strip '.py' and all characters after,
                            # append the file name to the lines list,
                            # otherwise discard the line
                            filt_list_names.append(cur_line[0:suffix_pos])
                            num_filters += 1

                cur_line = fp.readline() # read next line

            logger.info("%d entries found in filter list!\n", num_filters)
            fp.close()

            return filt_list_names

        except IOError as e:
            logger.critical( 'Filter list file "%s" could not be found.\n\
                I/O Error(%d): %s' %(self.filt_dir_file, e.errno, e.strerror))
            sys.exit( 'Filter list file "%s" could not be found.\n\
                I/O Error(%d): %s' %(self.filt_dir_file, e.errno, e.strerror))

        except Exception as e:
            logger.error( "Unexpected error: %s", e)
            sys.exit( "Unexpected error: %s", e)

#==============================================================================
    def dyn_filt_import(self, filt_list_names):
        """
        Try to import from all filter files found by ``read_filt_file()``,
        auto-detecting available modules / classes:

        - The design classes in a module are specified in the module attribute
          ``filter_classes`` as a dictionary ``{"Cheby":"Chebychev 1"}`` where the
          key is the class name in the module and the value the corresponding name
          for display.

        - When ``filter_classes`` is a string, use the string
          for both class and combo box name.

        Filter class, display name and module path are stored in the global
        dict `fb.fil_classes`.

        Parameters
        ----------

        filt_list_names
            List with the classes to be imported, contained in the
            Python files (ending with .py !!) in the file filt_list_file

        Returns
        -------

        None, results are stored in the global dict fb.fil_classes,
        containing entries (for SUCCESSFUL imports) with:

            {<class name>:{'name':<display name>, 'mod':<full module name>}
             e.g. {'Cheby1':{'name':'Chebychev 1', 'mod':'pyfda.filter_design.cheby1'}

        """
        fb.fil_classes = {}   # initialize global dict for filter classes
        num_imports = 0           # number of successful filter module imports
        imported_fil_classes = "" # names of successful filter module imports

        for filt_mod in filt_list_names:
            module_name = 'pyfda.' + self.filt_dir + '.' + filt_mod
            try:  # Try to import the module from the  package and get a handle:
                ################################################
                mod = importlib.import_module(module_name)
                ################################################
                if hasattr(mod, 'filter_classes'):
                    # check type of module attribute 'filter_classes'
                    if isinstance(mod.filter_classes, dict): # dict {class name : combo box name}
                        fdict = mod.filter_classes
                    elif isinstance(mod.filter_classes, six.string_types): # String, convert to dict
                        fdict = {mod.filter_classes:mod.filter_classes}
                    else:
                        logger.warning("Skipping module '%s', its attribute 'filter_classes' has the wrong type '%s'."
                        %(str(filt_mod), str(type(mod.filter_classes).__name__)))
                        continue # with next entry in filt_list_names
                else:
                    # no filter_class attribute, use the module name as fallback:
                    logger.warning('Skipping filter module "%s" due to missing attribute "filter_classes".', filt_mod)
                    continue

            except ImportError as e:
                logger.warning('Filter module "{0}" could not be imported.\n{1}'.format(filt_mod, e))
                continue
            except Exception as e:
                logger.warning("Unexpected error during module import:\n%s", e)
                continue
            # Now, try to instantiate an instance ff.fil_inst() of filter class fc
            for fc in fdict:
                if not hasattr(mod, fc): # class fc doesn't exist in filter module
                    logger.warning("Skipping filter class '%s', it doesn't exist in module '%s'." %(fc, module_name))
                    continue # continue with next entry in fdict
                else:
                    fb.fil_classes.update({fc:{'name':fdict[fc],'mod':module_name}})
                    # when module + class import was successful, add a new entry
                    # to the dict with the class name as key and display name and
                    # and fully qualified module path as values, e.g.
                    # 'Butter':{'name':'Butterworth', 'mod':'pyfda.filter_design.butter'}

                    num_imports += 1
                    imported_fil_classes += "\t" + filt_mod + "."+ fc + "\n"

        if num_imports < 1:
            logger.critical("No filter class could be imported - shutting down.")
            sys.exit("No filter class could be imported - shutting down.")

        else:
            logger.info("Imported successfully the following %d filter classes:\n%s",
                    num_imports, imported_fil_classes)

#==============================================================================
    def build_fil_tree(self, fc, rt_dict, fil_tree = None):
        """
        Read attributes (ft, rt, rt:fo) from filter class fc)
        Attributes are stored in
        the design method classes in the format (example from common.py)

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

        Finally, the whole structure is frozen recursively to avoid inadvertedly
        changing the filter tree.

        For a full example, see the default filter tree ``fb.fil_tree`` defined
        in ``filter_broker.py``.

        Reads
        -----


        Returns
        -------

        fil_tree : filter tree

        """
        if not fil_tree:
            fil_tree = {}

        ft = ff.fil_inst.ft                  # get filter type (e.g. 'FIR')

        for rt in rt_dict:                   # iterate over all response types
            if rt == 'COM':                  # handle common info later
                continue

            if rt not in fil_tree:           # is response type already in dict?
                fil_tree.update({rt:{}})     # no, create it

            if ft not in fil_tree[rt]:       # filter type already in dict[rt]?
                fil_tree[rt].update({ft:{}}) # no, create it

            if fc not in fil_tree[rt][ft]:       # filter class already in dict[rt][ft]?
                fil_tree[rt][ft].update({fc:{}}) # no, create it

            # now append all the individual 'min' / 'man'  subwidget infos to fc:
            fil_tree[rt][ft][fc].update(rt_dict[rt])

            if 'COM' in rt_dict:      # Now handle common info
                for fo in rt_dict[rt]: # iterate over 'min' / 'max'
                    if fo in rt_dict['COM']: # and add common info first
                        merge_dicts(fil_tree[rt][ft][fc][fo],
                                    rt_dict['COM'][fo], mode='add2')

        return fil_tree


#==============================================================================
if __name__ == "__main__":

    # Need to start a QApplication to avoid the error
    #  "QWidget: Must construct a QApplication before a QPaintDevice"
    # when instantiating filters with dynamic widgets (equiripple, firwin)
    from .compat import QtGui
    app = QtGui.QApplication(sys.argv)

    print("===== Initialize FilterReader ====")

    filt_file_name = "filter_list.txt"
    filt_dir = "filter_design"
    comment_char = '#'

    # Create a new FilterFileReader instance & initialize it
    myTreeBuilder = FilterTreeBuilder(filt_dir, filt_file_name, comment_char)

    print("\n===== Start Test ====")
    filterTree = myTreeBuilder.build_fil_tree()
    print('fb.fil_tree = ', fb.fil_tree)
