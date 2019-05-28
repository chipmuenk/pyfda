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
import os, sys, re, ast
from collections import OrderedDict
from pprint import pformat
import importlib
import configparser # only py3

import logging
logger = logging.getLogger(__name__)

import pyfda.filterbroker as fb
import pyfda.filter_factory as ff
import pyfda.pyfda_dirs as dirs

from .frozendict import freeze_hierarchical

#--------------------------------------------------------------------------
def merge_dicts(d1, d2, path=None, mode='keep1'):
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
        
        * :'add1': merge the entries, putting the values from ``d2`` first (important for lists)
    
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
    >>> merge_dicts(fil_tree, fil_tree_add, mode='add1')

    Notes
    -----
    If you don't want to modify ``d1`` in place, call the function using: 
    
    >>> new_dict = merge_dicts(dict(d1), d2)
    
    If you need to merge more than two dicts use:

    >>> from functools import reduce   # only for py3
    >>> reduce(merge, [d1, d2, d3...]) # add / merge all other dicts into d1

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

class ParseError(Exception):
    pass

class Tree_Builder(object):
    """
    Read the config file and construct dictionary trees with

    - all filter combinations
    - valid combinations of filter designs and fixpoint implementations


    """

    def __init__(self):

        logger.debug("Config file: {0:s}\n".format(dirs.USER_CONF_DIR_FILE))

        self.init_filters()

#==============================================================================
    def init_filters(self):
        """
        Run at startup to populate global dictionaries and lists:
        
        - :func:`parse_conf_file()`:  Parse the configuration file `pyfda.conf` 
          (specified in ``dirs.USER_CONF_DIR_FILE``) using :func:`build_class_dict()`
          which calls :func:`parse_conf_section()`: Try to find and import the
          modules specified in the corresponding sections  there; extract and 
          import the classes defined in each module and give back an OrderedDict
          containing successfully imported classes with their options 
          (like fully qualified module names, display name, associated fixpoint 
          widgets etc.). Information for each  section is stored in globally 
          accessible OrderdDicts like`fb.filter_classes`.
              
        - Read attributes (`ft`, `rt`, `fo`) from all valid filter classes (`fc`)
          in the global dict ``fb.filter_classes`` and store them in the filter
          tree dict ``fil_tree`` with the hierarchy
                                        
            **rt-ft-fc-fo-subwidget:params** .


        Parameters
        ----------
        None
        
        Returns
        -------
        None, but populates the following global attributes:
            
            - `fb.fil_tree` :
                
        """

        self.parse_conf_file()

        fil_tree = {}

        for fc in fb.filter_classes:  # iterate over all previously found filter classes fc

            # instantiate a global instance ff.fil_inst() of filter class fc
            err_code = ff.fil_factory.create_fil_inst(fc)
            if err_code > 0:
                logger.warning('Skipping filter class "{0:s}" due to import error {1:d}'.format(fc, err_code))
                continue # continue with next entry in fb.filter_classes

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
    def parse_conf_file(self):
        """
        Parse the file ``dirs.USER_CONF_DIR_FILE`` with the following sections

        :[Commons]:
            Try to find user directories; if they exist add them to 
            `dirs.USER_DIRS` and `sys.path`

        For the other sections, OrderedDicts are returned with the class names
        as keys and dictionaries with options as values.

        :[Input Widgets]:
            Store (user) input widgets in `fb.input_dict`

        :[Plot Widgets]:
            Store (user) plot widgets in `fb.plot_dict`

        :[Filter Designs]:
            Store (user) filter designs in `fb.filter_dict`
            
        :[Fixpoint Widgets]:
            Store (user) fixpoint widgets in `fb.fixpoint_dict`


        Parameters
        ----------
        None

        Returns
        -------
        None

        """

        CONF_VERSION = 2
        try:
            # Test whether user config file is readable, this is necessary as
            # configParser quietly fails when the file doesn't exist
            if not os.access(dirs.USER_CONF_DIR_FILE, os.R_OK):
                raise IOError('Config file "{0}" cannot be read.'.format(dirs.USER_CONF_DIR_FILE))

            # -----------------------------------------------------------------
            # setup an instance of config parser, allow  keys without value
            # -----------------------------------------------------------------
            self.conf = configparser.ConfigParser(allow_no_value=True)
            # preserve case of parsed options by overriding optionxform():
            # Set it to function str()
            self.conf.optionxform = str
            # Allow interpolation across sections, ${Dirs:dir1}
            self.conf._interpolation = configparser.ExtendedInterpolation() # PY3 only
            self.conf.read(dirs.USER_CONF_DIR_FILE)
            logger.info('Parsing config file\n\t"{0}"\n\t\twith sections:\n\t{1}'
                        .format(dirs.USER_CONF_DIR_FILE, str(self.conf.sections())))

            # -----------------------------------------------------------------
            # Parsing [Common]
            #------------------------------------------------------------------
            self.commons = self.parse_conf_section("Common")

            if not 'version' in self.commons or int(self.commons['version'][0]) != CONF_VERSION:
                logger.critical("Config file\n\t'{0:s}'\n\thas the wrong version '{2}' "
                                "(required: '{1}').\n"
                                "\tYou can either edit the file or delete it.\n\tWhen deleted, " 
                                "a new configuration file will be created at restart."\
                                .format(dirs.USER_CONF_DIR_FILE, CONF_VERSION, int(self.commons['version'][0])))
                sys.exit()
            
            if 'user_dirs' in self.commons:
                for d in self.commons['user_dirs']:
                    d = os.path.abspath(os.path.normpath(d))
                    if os.path.isdir(d):
                        dirs.USER_DIRS.append(d)
                        if d not in sys.path:
                            sys.path.append(d)
                    else:
                        logger.warning("User directory doesn't exist:\n\t{0}\n".format(d))
                
            if dirs.USER_DIRS: 
                logger.info("User directory(s):\n\t{0}\n".format(dirs.USER_DIRS))
            else:
                logger.warning('No valid user directory found in "{0}\n.'
                            .format(dirs.USER_CONF_DIR_FILE))

            # -----------------------------------------------------------------
            # Parsing [Input Widgets]
            #------------------------------------------------------------------
            fb.input_classes = self.build_class_dict("Input Widgets", "input_widgets")
            # -----------------------------------------------------------------
            # Parsing [Plot Widgets]
            #------------------------------------------------------------------
            fb.plot_classes = self.build_class_dict("Plot Widgets", "plot_widgets")
            # -----------------------------------------------------------------
            # Parsing [Filter Designs]
            #------------------------------------------------------------------
            fb.filter_classes = self.build_class_dict("Filter Designs", "filter_designs")
            # currently, option "opt" can only be an association with a fixpoint
            # widget, so replace key "opt" by key "fix":
            # Convert to list in any case
            for c in fb.filter_classes:
                if 'opt' in fb.filter_classes[c]:
                    fb.filter_classes[c]['fix'] = fb.filter_classes[c].pop('opt')
                if 'fix' in fb.filter_classes[c] and type(fb.filter_classes[c]['fix']) == str:
                    fb.filter_classes[c]['fix'] = fb.filter_classes[c]['fix'].split(',')
            # -----------------------------------------------------------------
            # Parsing [Fixpoint Filters]
            #------------------------------------------------------------------
            fb.fixpoint_classes = self.build_class_dict("Fixpoint Widgets", "fixpoint_widgets")
            logger.info("\nFixpoint_widgets: \n{0}\n".format(fb.fixpoint_classes))

            # First check whether fixpoint options of the filter designs are 
            # valid fixpoint classes by comparing them to the verified items of
            # fb.fixpoint_classes:
            for c in fb.filter_classes:
                if 'fix' in fb.filter_classes[c]:
                    for w in fb.filter_classes[c]['fix']:
                        if w not in fb.fixpoint_classes:
                            logger.warning('Removing invalid fixpoint module\n\t"{0}" for filter class "{1}".'\
                                           .format(w,c))
                            fb.filter_classes[c]['fix'].remove(w)
            # merge fb.filter_classes info "filter class":[fx_class1, fx_class2]
            # and fb.fixpoint_classes info "fixpoint class":[fil_class1, fil_class2]
            # into the fb.filter_classes dict

                # collect all fixpoint widgets (keys in fb.fixpoint_classes) which
                # have the class name c as a value
                fix_wdg = {k for k,val in fb.fixpoint_classes.items() if c in val['opt']}
                if len(fix_wdg) > 0:
                    if 'fix' in fb.filter_classes[c]:
                        #... and merge it with the fixpoint options of class c
                        fix_wdg = fix_wdg.union(fb.filter_classes[c]['fix'])

                    fb.filter_classes[c].update({'fix':list(fix_wdg)})

        # ----- Exceptions ----------------------
        except configparser.DuplicateSectionError as e:
            logger.critical('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))
            sys.exit()
        except configparser.ParsingError as e:
            logger.critical('Parsing Error in config file "{0}:\n{1}".'
                            .format(dirs.USER_CONF_DIR_FILE,e))
            sys.exit()
        except configparser.Error as e:
            logger.critical('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))
            sys.exit()

#==============================================================================
    def parse_conf_section(self, section):
        """
        Parse ``section`` in config file `conf` and return an OrderedDict
        with the elements ``{key:<OPTION>}`` where `key` and <OPTION>
        have been read from the config file. <OPTION> has been sanitized and 
        converted to a list or a dict.

        Parameters
        ----------
        section : str
            name of the section to be parsed

        Returns
        -------
        section_conf_dict : dict 
            Ordered dict with the keys of the config files and corresponding values
        """
        try:
            section_conf_dict = OrderedDict()
            items_list = self.conf.items(section) # entries from config file with [name, path]
                
            if len(items_list) > 0:
                for i in items_list:
                    # sanitize value and convert to a list, split at \n and ,
                    val = i[1].strip(' \t\n\r[]"')
                    if len(i[1]) == 0:
                        val = ""
                    elif i[1][0] == '{': # try to convert to dict
                        try:
                            val = ast.literal_eval(val)
                        except SyntaxError as e:
                            logger.warning("Syntax Error in config file\n{0}".format(e) )
                            val = ""
                    else:
                        val = re.sub('["\'\[\]]','', val)
                        val = re.split('; |, |\n|,\n|\r', val) # TODO: Test

                    section_conf_dict.update({i[0]:val})

                logger.info('Found {0:2d} entries in [{1:s}].'
                        .format(len(section_conf_dict), section))
            else:
                logger.warning('Empty section [{0:s}].'.format(section))

        except configparser.NoSectionError:
            logger.warning('No section [{0:s}] in config file "{1:s}".'
                           .format(section, dirs.USER_CONF_DIR_FILE))
            # configparser.NoOptionError
        except configparser.DuplicateOptionError as e:
            logger.warning('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))

        except configparser.InterpolationMissingOptionError as e:
            # catch unresolvable interpolations like ${wrongSection:wrongOption}
            # Attention: This terminates  current section() without result!
            logger.warning('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE)) 

        return section_conf_dict

#==============================================================================
    def build_class_dict(self, section, subpackage=""):
        """
        - Try to dynamically import the modules (= files) parsed in `section`
          reading their module level attribute `classes` with classes contained 
          in the module.

          `classes` is a dictionary, e.g. `{"Cheby":"Chebychev 1"}` where
          the key is the class name in the module and the value the corresponding
          display name (used for the combo box).

        - When `classes` is a string or a list, use the string resp. the list items
          for both class and display name.
          
        - Try to import the filter classes
        
        Parameters
        ----------
        section: str
            Name of the section in the configuration file to be parsed by
            `self.parse_conf_section'.
        
        subpackage: str
            Name of the subpackage containing the module to be imported. Module
            names are prepended successively with
            `['pyfda.' + subpackage + '.', '', subpackage + '.']`
        
        Returns
        -------
        classes_dict : dict
        
        A dictionary with the classes as keys; values are dicts which define 
        the options (like display name, module path, fixpoint implementations etc).
        
        Each entry has the form e.g.
        
        {<class name>:{'name':<display name>, 'mod':<full module name>}} e.g.

        .. code-block:: python

             {'Cheby1':{'name':'Chebychev 1',
              'mod':'pyfda.filter_design.cheby1',
              'fix': 'IIR_cascade',
              'opt': ["option1", "option2"]}
        """
        classes_dict = OrderedDict() # dict for all successfully imported classes
        num_imports = 0       # number of successful module imports
        imported_classes = "" # names of successful module imports
        pckg_names = ['pyfda.'+subpackage+'.', '', subpackage+'.'] # search in that order
        
        section_conf_dict = self.parse_conf_section(section)
        
        for mod_name in section_conf_dict: # iterate over dict keys found in config file
            for p in pckg_names:
                try:  # Try to import the module from the package list above
                    mod_fq_name = p + mod_name # fully qualified module name (fqn)
                    # Try to import the module from the  package and get a handle:
                    ################################################
                    mod = importlib.import_module(mod_fq_name)
                    ################################################
                    break #-> successful import, break out of pckg_names loop
                except ImportError:
                    mod_fq_name = None
                    continue # module not found, try next package
                except Exception as e:
                    logger.warning('Error during import of "{0}":\n{1}'.format(mod_fq_name, e))
                    mod_fq_name = None
                    continue # Some other error ocurred during import, try next package

            if not mod_fq_name:
                logger.warning('Module "{0}" could not be imported.'.format(mod_name))
                continue

            if hasattr(mod, 'classes'):
                # check type of module attribute 'classes', try to convert to dict
                if isinstance(mod.classes, dict): # dict {class name : combo box name}
                    mod_dict = mod.classes # one or more filter classes in one file
                elif isinstance(mod.classes, str): # String, create a dict with the
                    mod_dict = {mod.classes:mod.classes} # string as both key and value
                elif isinstance(mod.classes, list): # list, create a dict with list items
                    mod_dict = {l:l for l in list}  # as both key and value 
                else:
                    logger.warning("Skipping module '%s', its attribute 'classes' has the wrong type '%s'."
                    %(str(mod_name), str(type(mod.classes).__name__)))
                    continue # with next entry in section_conf_dict
                #logger.info("MOD_DICT: {0}".format(mod_dict))
            else:
                # no `classes` attribute - skip entry
                logger.warning('Skipping module "{0}" due to missing attribute "classes".'.format(mod_name))
                continue

            # Now, check whether class `c` is part of module `mod`
            for c in mod_dict:
                if not hasattr(mod, c): # class c doesn't exist in module
                    logger.warning("Skipping filter class '{0}', it doesn't exist in module '{1}'."\
                                   .format(c, mod_fq_name))
                    continue # continue with next entry in classes_dict
                else:
                    classes_dict.update({c:{'name':mod_dict[c],  # Class name
                                            'mod':mod_fq_name}}) # Fully qualified module name
                    # when module + class import was successful, add a new entry
                    # to the dict with the class name as key and a dict containing 
                    # "name":display name and "mod":fully qualified module name as values, e.g.
                    # 'Butter':{'name':'Butterworth', 'mod':'pyfda.filter_design.butter'}

                    # check whether options have been defined in the config file
                    opt = section_conf_dict[mod_name]
                    if opt:
                        if type(opt) == dict: 
                            classes_dict[c].update(opt)
                        elif type(opt) in {str, list}: # create dict {'opt':<OPTION>}
                            classes_dict[c].update({"opt":opt})
                        else:
                            logger.warning('Class "{0}" option data type "{1}" not understood:\n "{2}"'\
                                           .format(c, type(opt).__name__, opt))

                # logger.info("Opt : {0}".format(classes_dict[c]))
                num_imports += 1
                imported_classes += "\t" + mod_name + "."+ c + "\n"

        if num_imports < 1:
            logger.warning("No class could be imported.")
        else:
            logger.info("Imported {0:d} filter classes:\n{1:s}"\
                    .format(num_imports, imported_classes))
        return classes_dict

#==============================================================================
    def build_fil_tree(self, fc, rt_dict, fil_tree = None):
        """
        Read attributes (ft, rt, rt:fo) from filter class fc)
        Attributes are stored in
        the design method classes in the format (example from ``common.py``)

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

        Finally, the whole structure is frozen recursively to avoid inadvertedly
        changing the filter tree.

        For a full example, see the default filter tree ``fb.fil_tree`` defined
        in ``filterbroker.py``.

        Parameters
        ----------
        None


        Returns
        -------
        dict
            filter tree

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
    from .compat import QApplication
    app = QApplication(sys.argv)

    print("===== Initialize FilterReader ====")

    filt_file_name = "filter_list.txt"
    conf_dir = "filter_design"

    # Create a new FilterFileReader instance & initialize it
    myTreeBuilder = Tree_Builder(conf_dir, filt_file_name)

    print("\n===== Start Test ====")
    filterTree = myTreeBuilder.build_fil_tree()
    print('fb.fil_tree = ', fb.fil_tree)
