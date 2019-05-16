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
        
        - :func:`parse_conf_file()`:  Parse the configuration file ``pyfda.conf`` 
          (specified in ``dirs.USER_CONF_DIR_FILE``), writing classes and file
          paths to lists for the individual sections, a.o. to ``fb.filter_designs_list``
          for the filter design algorithms.
          
        - :func:`dyn_filt_import()` : Try to import all filter modules and classes 
          from ``fb.filter_designs_list`` and store successful imports in the
          dict ``fb.fil_classes`` as {filterName:filterModule}:
              
        - Read attributes (`ft`, `rt`, `fo`) from all valid filter classes (`fc`)
          in the global dict ``fb.fil_classes`` and store them in the filter
          tree dict ``fil_tree`` with the hierarchy
                                        
            **rt-ft-fc-fo-subwidget:params** .


        Parameters
        ----------
        None
        
        Returns
        -------
        None, but populates the following global attributes:
            
            - ``fb.fil_tree``:
                
            - 
    

        """

        self.parse_conf_file()

        self.dyn_filt_import()

        fil_tree = {}

        for fc in fb.fil_classes:  # iterate over all previously found filter classes fc

            # instantiate a global instance ff.fil_inst() of filter class fc
            err_code = ff.fil_factory.create_fil_inst(fc)
            if err_code > 0:
                logger.warning('Skipping filter class "{0:s}" due to import error {1:d}'.format(fc, err_code))
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
    def parse_conf_file(self):
        """
        Parse the file ``dirs.USER_CONF_DIR_FILE`` with the following sections

        :[Commons]:
            Try to find user directories and store them in ``dirs.USER_DIRS``

        For the other sections, a list of tuples is returned with the elements
        ``(class, opt)`` where "class" is the class name of the widget
        and "opt" specifies options:

        :[Input Widgets]:
            Store a list of tuples of (user) input widgets in ``fb.input_widgets_list``

        :[Plot Widgets]:
            Store a list of tuples of (user) plot widgets in ``fb.plot_widgets_list``

        :[Filter Designs]:
            Store a list of tuples of (user) filter designs in ``fb.filter_designs_list``
            
        :[Fixpoint Widgets]:
            Store a list of tuples of (user) fixpoint widgets in ``fb.fixpoint_widgets_list``


        Parameters
        ----------
        None

        Returns
        -------
        None

        """

        CONF_VERSION = 1
        try:
            # Test whether user config file is readable, this is necessary as
            # configParser quietly fails when the file doesn't exist
            if not os.access(dirs.USER_CONF_DIR_FILE, os.R_OK):
                raise IOError('Config file "{0}" cannot be read.'.format(dirs.USER_CONF_DIR_FILE))

            # -----------------------------------------------------------------
            # setup an instance of config parser, allow  keys without value
            # -----------------------------------------------------------------
            conf = configparser.ConfigParser(allow_no_value=True)
            # preserve case of parsed options by overriding optionxform():
            # Set it to function str()
            conf.optionxform = str
            # Allow interpolation across sections, ${Dirs:dir1}
            conf._interpolation = configparser.ExtendedInterpolation() # PY3 only
            conf.read(dirs.USER_CONF_DIR_FILE)
            logger.info('Parsing config file\n\t"{0}"\n\t\twith sections:\n\t{1}'
                        .format(dirs.USER_CONF_DIR_FILE, str(conf.sections())))

            # -----------------------------------------------------------------
            # Parsing [Common]
            #------------------------------------------------------------------
            self.commons = self.parse_conf_section(conf, "Common")

            if not 'version' in self.commons or int(self.commons['version'][0]) != CONF_VERSION:
                logger.critical("\nConfig file '{0:s}'\n has the wrong version '{2}' "
                                "(required: '{1}').\n"
                                "You can either edit the file or delete it, in this case " 
                                "a new configuration file will be created at restart."\
                                .format(dirs.USER_CONF_DIR_FILE, CONF_VERSION, int(self.commons['version'])))
                sys.exit()
            
            if 'user_dirs' in self.commons:
                for d in self.commons['user_dirs']:
                    d = os.path.abspath(os.path.normpath(d))
                    if os.path.isdir(d):
                        dirs.USER_DIRS.append(d)
                        if d not in sys.path:
                            sys.path.append(d)
                    else:
                        logger.warning("User directory doesn't exist:\n{0}\n".format(d))
                
            if dirs.USER_DIRS: 
                logger.info("User directory(s):\n{0}\n".format(dirs.USER_DIRS))
            else:
                logger.warning('No valid user directory found in "{0}\n.'
                            .format(dirs.USER_CONF_DIR_FILE))

            # -----------------------------------------------------------------
            # Parsing [Input Widgets]
            #------------------------------------------------------------------
            fb.input_widgets_dict = self.parse_conf_section(conf, "Input Widgets")

            # -----------------------------------------------------------------
            # Parsing [Plot Widgets]
            #------------------------------------------------------------------
            fb.plot_widgets_dict = self.parse_conf_section(conf, "Plot Widgets")

            # -----------------------------------------------------------------
            # Parsing [Filter Designs]
            #------------------------------------------------------------------
            fb.filter_designs_dict = self.parse_conf_section(conf, "Filter Designs")

            # -----------------------------------------------------------------
            # Parsing [Fixpoint Filters]
            #------------------------------------------------------------------
            fb.fixpoint_widgets_dict = self.parse_conf_section(conf, "Fixpoint Widgets")
            #logger.info("Fixpoint_widgets: \n{0}\n".format(fb.fixpoint_widgets_dict))

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
    def parse_conf_section(self, conf, section, req=True):
        """
        Parse ``section`` in config file `conf` and return an OrderedDict
        with the elements ``{key:{'opt':<OPTION>}}`` where `key` and <OPTION>
        have been read from the config file. <OPTION> has been sanitized and 
        converted to a list or a dict.

        Parameters
        ----------
        conf : instance of config parser

        section : str
            name of the section to be parsed

        req : bool
            when True, section is required: Terminate the program with an error
            if the section is missing in the config file

        Returns
        -------
        dict 
            dict with the 

        """
        try:
            wdg_dict = OrderedDict()
            items_list = conf.items(section) # entries from config file with [name, path]
                
            if len(items_list) > 0:
                for i in items_list:
                    # sanitize value and convert to a list, split at \n and ,
                    val = i[1].strip(' \t\n\r[]"')
                    if len(i[1]) == 0:
                        val = ""
                    elif i[1][0] == '{': # try to parse dict
                        try:
                            logger.info("\ndict: {0}\n".format(val))
                            val = ast.literal_eval(val)
                            val = {'opt':val}
                        except SyntaxError as e:
                            logger.warning("Syntax Error in config file\n{0}".format(e) )
                            val = ""
                    else:
                        val = re.sub('["\'\[\]]','', val)
                        val = re.split('; |, |\n|,\n|\r', val) # TODO: Test

                    wdg_dict.update({i[0]:val})

                logger.info('Found {0:2d} entries in [{1:s}].'
                        .format(len(wdg_dict), section))
            else:
                if req:
                    logger.critical('Empty section [{0:s}], aborting.'.format(section))
                    sys.exit()
                else:
                    logger.warning('Empty section [{0:s}].'.format(section))

        except configparser.NoSectionError as e:
            if req:
                logger.critical('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))
                sys.exit()
            else:
                logger.warning('No section [{0:s}] in config file "{1:s}".'
                           .format(section, dirs.USER_CONF_DIR_FILE))
            # configparser.NoOptionError
        except configparser.DuplicateOptionError as e:
            logger.warning('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))

        except configparser.InterpolationMissingOptionError as e:
            # catch unresolvable interpolations like ${wrongSection:wrongOption}
            # Attention: This terminates  current section() without result!
            logger.warning('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE)) 

        return wdg_dict

#==============================================================================
    def dyn_filt_import(self):
        """
        Try to import from all filter files found by ``parse_conf_file()``,
        auto-detecting available modules / classes:

        - The design classes in a module are specified in the module attribute
          ``filter_classes`` as a dictionary, e.g. ``{"Cheby":"Chebychev 1"}`` where
          the key is the class name in the module and the value the corresponding name
          for display.

        - When ``filter_classes`` is a string, use the string
          for both class and combo box name.

        Returns
        -------

        None
        
        ... but filter class, display name and module path are stored in the global
        dict ``fb.fil_classes`` where each entry (if the import of the class had 
        been successful) has the form
        
        {<class name>:{'name':<display name>, 'mod':<full module name>}} e.g.

        .. code-block:: python

             {'Cheby1':{'name':'Chebychev 1',
              'mod':'pyfda.filter_design.cheby1',
              'opt': {'fix': 'IIR_cascade'}}
        
        """
        fb.fil_classes = {}   # initialize global dict for filter classes
        num_imports = 0           # number of successful filter module imports
        imported_fil_classes = "" # names of successful filter module imports

        for filt_mod in fb.filter_designs_dict: # iterate over dict keys
            module_name = 'pyfda.filter_designs' + '.' + filt_mod # TODO: user_dirs!
 
            try:  # Try to import the module from the  package and get a handle:
                ################################################
                mod = importlib.import_module(module_name)
                ################################################
                if hasattr(mod, 'filter_classes'):
                    # check type of module attribute 'filter_classes'
                    if isinstance(mod.filter_classes, dict): # dict {class name : combo box name}
                        fdict = mod.filter_classes # one or more filter classes in one file
                    elif isinstance(mod.filter_classes, str): # String, convert to dict
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
                logger.warning("Unexpected error during module import:\n{0}".format(e))
                continue
            # Now, try to instantiate an instance ff.fil_inst() of filter class fc
            for fc in fdict:
                if not hasattr(mod, fc): # class fc doesn't exist in filter module
                    logger.warning("Skipping filter class '%s', it doesn't exist in module '%s'." %(fc, module_name))
                    continue # continue with next entry in fdict
                else:
                    fb.fil_classes.update({fc:{'name':fdict[fc],  # Class name
                                               'mod':module_name}})        # list with fixpoint implementations
                    # when module + class import was successful, add a new entry
                    # to the dict with the class name as key and display name and
                    # fully qualified module path as values, e.g.
                    # 'Butter':{'name':'Butterworth', 'mod':'pyfda.filter_design.butter'}
                    if 'opt' in fb.filter_designs_dict[filt_mod]: # does the filter have option(s)?
                        filt_opt = fb.filter_designs_dict[filt_mod].pop('opt')
                    else:
                        filt_opt = ""
                    
                if type(filt_opt) == dict and 'fix' in filt_opt:
                    opt_fix = filt_opt.pop('fix')
                    if len(opt_fix) > 0:
                        logger.info("FixOpt :{0} - {1}".format(len(opt_fix), opt_fix))
                        fb.fil_classes[fc].update({'fix':opt_fix})
                if len(filt_opt) > 0:
                    fb.fil_classes[fc].update({'opt':filt_opt})
                    
                logger.info("FilterOpt : {0}".format(fb.fil_classes[fc]))

                num_imports += 1
                imported_fil_classes += "\t" + filt_mod + "."+ fc + "\n"

        if num_imports < 1:
            logger.critical("No filter class could be imported - shutting down.")
            sys.exit("No filter class could be imported - shutting down.")
        else:
            logger.info("Imported {0:d} filter classes:\n{1:s}"\
                    .format(num_imports, imported_fil_classes))

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
