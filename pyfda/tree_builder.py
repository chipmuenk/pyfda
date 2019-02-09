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
from __future__ import print_function, division, unicode_literals, absolute_import
import os, sys, six
from pprint import pformat
import importlib
if sys.version_info > (3,): # True for Python 3
    import configparser
else:
    import ConfigParser as configparser

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

        :[Dirs1] and [Dirs2]:
            Try to find user directories and store them in ``dirs.USER_DIRS``
            and ``dirs.USER_DIR_LABEL``. 

        For the other sections, a list of tuples is returned with the elements
        ``(class, dir)`` where "class" is the class name of the widget
        and "dir" specifies the directory for user widgets and None for standard
        widgets:

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
        try:
            # Test whether user config file is readable, this is necessary as
            # configParser quietly fails when the file doesn't exist
            if not os.access(dirs.USER_CONF_DIR_FILE, os.R_OK):
                raise IOError('Config file "{0}" cannot be read.'.format(dirs.USER_CONF_DIR_FILE))

            # setup an instance of config parser, allow  keys without value
            conf = configparser.ConfigParser(allow_no_value=True)
            # preserve case of parsed options by overriding optionxform():
            # Set it to function str()
            conf.optionxform = str
            # Allow interpolation across sections, ${Dirs:dir1}
            # conf._interpolation = configparser.ExtendedInterpolation() # PY3 only
            conf.read(dirs.USER_CONF_DIR_FILE)
            logger.info('Parsing config file\n\t"{0}"\n\t\twith sections:\n\t{1}'
                        .format(dirs.USER_CONF_DIR_FILE, str(conf.sections())))

            # -----------------------------------------------------------------
            # Parsing [Common]
            #------------------------------------------------------------------
            try:
                commons = {}
                items_list = conf.items('Common') # list of entries from section [Common]

            except configparser.NoSectionError:
                    logger.critical("No section '[Common]' in\n"
                                    "'{0:s}'\n"
                                    "You can either edit the file or delete it, in this case " 
                                    "a new configuration file will be created at restart."\
                                    .format(dirs.USER_CONF_DIR_FILE))
                    sys.exit()

            if len(items_list) > 0:
                for i in items_list:
                    commons.update({i[0]:i[1]}) # standard widget, no dir specified
    
                if not 'version' in commons or int(commons['version']) < 1:
                    logger.critical("Version {2} of 'pyfda.conf' < {0} or no option 'version' in\n"
                                    "'{1:s}'\n"
                                    "Please delete the file and restart pyfdax, " 
                                    "a new configuration file will be created.".format(1, dirs.USER_CONF_DIR_FILE, commons['version']))
                    sys.exit()
            logger.info("commons: {0}\n".format(commons))

            # -----------------------------------------------------------------
            # Parsing directories [Dirs]
            #------------------------------------------------------------------
            #dirs.USER_DIR_LABEL = None  # last valid user label entry (legacy)
            #dirs.USER_DIR = None        # last valid user dir (legacy)
            dirs.USER_DIRS = {}         # dict with user label : user_dir pairs
            for section in ['Dirs1','Dirs2']:
                try:
                    for d in conf.items(section):
                        user_dir = os.path.normpath(d[1])
                        if os.path.exists(user_dir):
                            try:
                                dirs.USER_DIRS.update({d[0]:user_dir})
                                #dirs.USER_DIR_LABEL = d[0]
                                #dirs.USER_DIR = user_dir
                            except TypeError:
                                logger.warning('Unsuitable key - value pair\n"{0}" - "{1}".'
                                               .format(d[0],d[1]))

                except (AttributeError, KeyError):
                    logger.info("No user directory specified.")
                except configparser.NoSectionError:
                    logger.info("No section [{0:s}] found.".format(section))

            if dirs.USER_DIRS: # use last found directory
                logger.info("User directory(s):\n{0}".format(dirs.USER_DIRS))
            else:
                logger.warning('No valid user directory found in "{0}.'
                            .format(dirs.USER_CONF_DIR_FILE))

            # -----------------------------------------------------------------
            # Parsing [Input Widgets]
            #------------------------------------------------------------------
            fb.input_widgets_list = self.parse_conf_section(conf, "Input Widgets")

            # -----------------------------------------------------------------
            # Parsing [Plot Widgets]
            #------------------------------------------------------------------
            fb.plot_widgets_list = self.parse_conf_section(conf, "Plot Widgets")

            # -----------------------------------------------------------------
            # Parsing [Filter Designs]
            #------------------------------------------------------------------
            fb.filter_designs_list = self.parse_conf_section(conf, "Filter Designs")

            # -----------------------------------------------------------------
            # Parsing [Fixpoint Filters]
            #------------------------------------------------------------------
            fb.fixpoint_widgets_list = self.parse_conf_section(conf, "Fixpoint Widgets")


        # ----- Exceptions ----------------------
        except configparser.ParsingError as e:
            logger.critical('Parsing Error in config file "{0}:\n{1}".'
                            .format(dirs.USER_CONF_DIR_FILE,e))
            sys.exit()
        except configparser.NoSectionError as e:
            logger.critical('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))
            sys.exit()
            # configparser.NoOptionError
        except configparser.DuplicateSectionError as e:
            logger.warning('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))
        except configparser.Error as e:
            logger.critical('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))
            sys.exit()

# Py3 only?
#        except configparser.DuplicateOptionError as e:
#            logger.warning('{0} in config file "{1}".'.format(e, dirs.USER_CONF_DIR_FILE))

        except IOError as e:
            logger.critical('{0}'.format(e))
            sys.exit()

#==============================================================================
    def parse_conf_section(self, conf, section, req=True):
        """
        Parse ``section`` in ``dirs.USER_CONF_DIR_FILE`` and return a list of
        tuples with the elements ``(class, dir)`` where "class" is the
        class name of the widget and "dir" is the directory for
        user widgets and None for standard widgets:

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
        list 
            list of tuples containing class name and directory. The latter is none
            for standard widgets.

        """
        try:
            wdg_list = []
            items_list = conf.items(section) # entries from config file with [name, path]

            if len(items_list) > 0:
                for i in items_list:
                    if not i[1]:
                        wdg_list.append((i[0],i[1])) # standard widget, no dir specified
                    else:
                        try:
                            wdg_list.append((i[0], dirs.USER_DIRS[i[1]]))
                        except (KeyError, TypeError):
                            wdg_list.append((i[0],''))
                            logger.warning('Unknown / unsuitable user label "{0}"'
                                           .format((i[0],i[1])))
            if len(wdg_list) > 0:
                logger.info('Found {0:2d} entries in [{1:s}].'
                        .format(len(wdg_list), section))
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

        return wdg_list

#==============================================================================
    def dyn_filt_import(self):
        """
        Try to import from all filter files found by ``parse_conf_file()``,
        auto-detecting available modules / classes:

        - The design classes in a module are specified in the module attribute
          ``filter_classes`` as a dictionary ``{"Cheby":"Chebychev 1"}`` where the
          key is the class name in the module and the value the corresponding name
          for display.

        - When ``filter_classes`` is a string, use the string
          for both class and combo box name.

        Filter class, display name and module path are stored in the global
        dict ``fb.fil_classes``.

        Parameters
        ----------
        filt_list_names : list
            List with the classes to be imported, contained in the
            Python files (ending with .py !!) in the file conf_file,
            containing entries (for SUCCESSFUL imports) with:

            {<class name>:{'name':<display name>, 'mod':<full module name>}} e.g.

            .. code-block:: python

             {'Cheby1':{'name':'Chebychev 1',
               'mod':'pyfda.filter_design.cheby1'}
        
        """
        fb.fil_classes = {}   # initialize global dict for filter classes
        num_imports = 0           # number of successful filter module imports
        imported_fil_classes = "" # names of successful filter module imports

        for filt_mod in fb.filter_designs_list:
            if not filt_mod[1]: # standard filter directory / module
                module_name = 'pyfda.filter_designs' + '.' + filt_mod[0]
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
                logger.warning("Unexpected error during module import:\n{0}".format(e))
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
                    imported_fil_classes += "\t" + filt_mod[0] + "."+ fc + "\n"

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
