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
import ast
from collections import OrderedDict
import configparser
import importlib
import logging
import os
# from pprint import pformat
import re
import sys
from typing import ClassVar

from pyfda.libs.frozendict import freeze_hierarchical
import pyfda.libs.pyfda_dirs as dirs

logger = logging.getLogger(__name__)

REQ_VERSION = 4  # required version for config file

# --------------------------------------------------------------------------
class ParseError(Exception):
    """
    Exception raised for errors in the config file parsing, not yet implemented.
    Could be used as raise ParseError("message") in the code below to indicate
    problems during parsing.
    """


class ConfigFileParser():
    """
    Parse the config file and store the information in the following class variables. The
    resulting hierarchical dicts may not be modified afterwards, however, this cannot be
    enforced at the moment as the FrozenDict() class is derived from FrozenSet() and does
    not preserve the order of the dict entries.

    - FILTER_CLASSES_DICT
    - FIXPOINT_CLASSES_DICT
    - INPUT_CLASSES_DICT
    - PLOT_CLASSES_DICT
    - conf_settings

    The existence of filter classes etc. is not tested, entries are generated as found in the
    config file. Actual testing and importing is done in :func:`_build_widget_class_dict()`.

    The keys are the class names of the widgets in the configuration file that have been parsed
    and successfully instantiated. The values are dicts containing display names (e.g. for tabs
    and comboboxes) and module paths in dotted notation for dynamic importing.

    The order of the entries defines the order of tabs and combobox entries in the UI. Since Python
    3.7+, dicts preserve insertion order, hence an OrderedDict is not required.

    The following initial definitions are only meant to illustrate the expected structure
    for documentation and for module test, they are overwritten during the initialization.

    see @classmethod in docs.python.org/3/library/functions.html#classmethod
    C.func() is class method, C().func() instance method

    Use self.__class__  to access class variables from instance methods
    """

    PLOT_CLASSES_DICT: ClassVar[dict[str, dict[str, str]]] =\
        {
        'Plot_Hf': {'name': '|H(f)|', 'mod': 'pyfda.plot_widgets.plot_hf'},
        'Plot_Phi': {'name': 'φ(f)', 'mod': 'pyfda.plot_widgets.plot_phi'},
        'Plot_tau_g': {'name': 'tau_g', 'mod': 'pyfda.plot_widgets.plot_tau_g'},
        'Plot_PZ': {'name': 'P / Z', 'mod': 'pyfda.plot_widgets.plot_pz'},
        'Plot_Impz': {'name': 'h[n]', 'mod': 'pyfda.plot_widgets.plot_impz'},
        'Plot_3D': {'name': '3D', 'mod': 'pyfda.plot_widgets.plot_3d'}
        }
    INPUT_CLASSES_DICT: ClassVar[dict[str, dict[str, str]]] =\
        {
        'Input_Specs': {'name': 'Specs', 'mod': 'pyfda.input_widgets.input_specs'},
        'Input_Coeffs': {'name': 'b,a', 'mod': 'pyfda.input_widgets.input_coeffs'},
        'Input_PZ': {'name': 'P/Z', 'mod': 'pyfda.input_widgets.input_pz'},
        'Input_Info': {'name': 'Info', 'mod': 'pyfda.input_widgets.input_info'},
        'Input_Files': {'name': 'Files', 'mod': 'pyfda.input_widgets.input_files'},
        'Input_Fixpoint_Specs': {'name': 'Fixpoint',
                                'mod': 'pyfda.input_widgets.input_fixpoint_specs'}
        }

    FIXPOINT_CLASSES_DICT: ClassVar[dict[str, dict[str, str]]] =\
        {
        'FIR_DF_wdg': {'name': 'FIR_DF',
                       'mod': 'pyfda.fixpoint_widgets.fir_df', 'opt': ['Equiripple', 'Firwin']},
        'Delay_wdg': {'name': 'Delay',
                      'mod': 'pyfda.fixpoint_widgets.delay1', 'opt': ['Equiripple']}
        }
    FILTER_CLASSES_DICT: ClassVar[dict[str, dict[str, str]]] =\
        {# IIR
        'Bessel': {'name': 'Bessel', 'mod': 'pyfda.filter_widgets.bessel'},
        'Butter': {'name': 'Butterworth', 'mod': 'pyfda.filter_widgets.butter'},
        'Cheby1': {'name': 'Chebyshev 1', 'mod': 'pyfda.filter_widgets.cheby1'},
        'Cheby2': {'name': 'Chebyshev 2', 'mod': 'pyfda.filter_widgets.cheby2'},
        'Ellip': {'name': 'Elliptic', 'mod': 'pyfda.filter_widgets.ellip'},
         # test undefined:
        'FancyFilter': {'name': 'Fancy', 'mod': 'pyfda.filter_widgets.fancyfilter'},
        # FIR
        'Equiripple': {'name': 'Equiripple', 'mod': 'pyfda.filter_widgets.equiripple'},
        'Firwin': {'name': 'Windowed FIR', 'mod': 'pyfda.filter_widgets.firwin'},
        'MA': {'name': 'Moving Average', 'mod': 'pyfda.filter_widgets.ma'},
        'Manual_FIR': {'name': 'Manual', 'mod': 'pyfda.filter_widgets.manual'},
        'Manual_IIR': {'name': 'Manual', 'mod': 'pyfda.filter_widgets.manual'}
        }

    # -----------------------------------------------------------------------------
    # Dictionary containing configuration settings for pyfda which can be modified
    # in the [Config Settings] of `pyfda.conf` and from the UI
    # ------------------------------------------------------------------------------

    conf_settings: ClassVar[dict[str, object]] =\
        {
        'EXCEPTION_LEVEL': 0,  # 0: quiet, 1: print error stack, 2: end pyfda
        'THEME': 'light',
        'N_FFT':  8192  # number of FFT points for most widgets except y[n]
        }


    # ==============================================================================
    def __init__(self):
        logger.info("Instantiating ConfigFileParser")

    # --------------------------------------------------------------------------
    def parse_conf_file(self) -> None:
        """
        Parse the following sections from configuration file `pyfda.conf` (specified in
        ``dirs.USER_CONF_DIR_FILE``).

        :[Commons]:
            Try to find user directories; if they exist add them to
            `dirs.USER_DIRS` and `sys.path`

        :[Config Settings]
            Store settings in class attribute `ConfigFileParser.conf_settings`

        The other sections are processed in :func:`build_widget_tree()`.

        This is called only once at instantiation from `pyfdax.py`.

        Returns
        -------
        None
        """
        # -----------------
        def _print_conf_file() -> None:
            """
            Read configuration file and print its sections.
            """
            self.conf.clear()
            self.conf.read(dirs.USER_CONF_DIR_FILE)
            sect = ""
            for s in self.conf.sections():
                sect += "\t\t[" + str(s) + "]\n"
            logger.info("Parsing config file\n\t'%s' with sections:\n%s",
                        dirs.USER_CONF_DIR_FILE, sect)

        # -----------------
        def _read_conf_version() -> bool:
            """
            Try to read out the version of the config file, if the version
            number cannot be read or is not equal to the required number,
            return False.
            """
            success = True
            try:
                conf_ver = int(self.commons['version'][0])
                if conf_ver != REQ_VERSION:
                    logger.error(
                        "User config file\n\t'%s'\n\thas the wrong version '%s' (required: '%s').",
                        dirs.USER_CONF_DIR_FILE, conf_ver, REQ_VERSION)
                    success = False
            except KeyError:
                logger.error("No entry 'version' in %s", dirs.USER_CONF_DIR_FILE)
                success = False
            except (IndexError, ValueError, TypeError):
                logger.error("No suitable value for 'version' in %s", dirs.USER_CONF_DIR_FILE)
                success = False

            return success

        # --------------
        logger.info("Reading config file: %s\n", dirs.USER_CONF_DIR_FILE)
        try:
            # Test whether user config file is readable, this is necessary as
            # configParser quietly fails when the file doesn't exist
            if not os.access(dirs.USER_CONF_DIR_FILE, os.R_OK):
                raise IOError(
                    f'Config file not found / not readable\n\t"{dirs.USER_CONF_DIR_FILE}"')

            # -----------------------------------------------------------------
            # setup an instance of config parser, allow  keys without value and
            # interpolation across sections, i.e. ${Dirs:dir1}
            # -----------------------------------------------------------------
            self.conf = configparser.ConfigParser(
                allow_no_value=True, interpolation=configparser.ExtendedInterpolation())
            # preserve case of parsed options by overriding optionxform() with function str()
            self.conf.optionxform = str
            _print_conf_file()
            # ------------------------------------------------------------------
            # Parsing [Common]
            # ------------------------------------------------------------------
            self.commons = self._parse_conf_section("Common")
            logger.info("Found %d entries in [Common]", len(self.commons))

            if not _read_conf_version():
                # update configuration files and try again
                dirs.update_conf_files(logger)
                _print_conf_file()
                self.commons = self._parse_conf_section("Common")
                logger.info(
                    "Found %s entries in [Common] (new config file)", len(self.commons))

                if not _read_conf_version():
                    logger.critical("Version number is still invalid, terminating.")
                    sys.exit()

            if 'user_dirs' in self.commons:
                for d in self.commons['user_dirs']:
                    d = os.path.abspath(os.path.normpath(d))
                    if os.path.isdir(d):
                        dirs.USER_DIRS.append(d)
                        if d not in sys.path:
                            sys.path.append(d)
                    else:
                        logger.info("User directory doesn't exist:\n\t%s\n", d)

            if dirs.USER_DIRS:
                logger.info("User directory(s):\n\t%s\n", dirs.USER_DIRS)
            else:
                logger.info("No valid user directory specified.")

            # ------------------------------------------------------------------
            # Parsing [Config Settings]
            # ------------------------------------------------------------------
            conf_settings = self._parse_conf_section("Config Settings")
            i = 0
            if conf_settings:
                # logger.info(conf_settings)
                for k in conf_settings:
                    if k in ConfigFileParser.conf_settings:
                        # TODO: why are the values lists?
                        try:
                            # try to convert to a numeric type
                            ConfigFileParser.conf_settings[k]\
                                = ast.literal_eval(conf_settings[k][0])
                        except ValueError:
                            # unsuccessful, store entry as string
                            ConfigFileParser.conf_settings[k] = conf_settings[k][0]
                        i += 1
                    else:
                        logger.warning(
                            "Ignoring unknown entry '[%s]' in configuration file 'pyfda.conf'", k)
                logger.info("Found %d entries in [Config Settings]", i)
            else:
                logger.info("No valid entries in [Config Settings]")

        # ----- Exceptions ----------------------
        except configparser.DuplicateSectionError as e:
            logger.critical('Duplicate section in config file "%s":\n%s.',
                            dirs.USER_CONF_DIR_FILE, e)
            sys.exit()
        except configparser.ParsingError as e:
            logger.critical('Parsing error in config file "%s:\n%s".',
                            dirs.USER_CONF_DIR_FILE, e)
            sys.exit()
        except configparser.Error as e:
            logger.critical('%s in config file "%s".', e, dirs.USER_CONF_DIR_FILE)
            sys.exit()

    # --------------------------------------------------------------------------
    def build_widget_tree(self) -> None:
        """
        This is only called once during the start from `pyfdax.py`.

        This part needs a running application as Qt widgets are instantiated to ensure
        they exist and run without error.

        The following sections are processed here, creating dicts with
        widget class names as keys and dictionaries with options as values.

        This is performed using :func:`_build_widget_class_dict()` which calls
        :func:`_parse_conf_section()`:

        - Try to find and import the modules specified in the corresponding sections

        - Extract and import the classes defined in each module and give back a dict with
          the successfully imported classes and their options (like fully qualified module
          names, display name, associated fixpoint widgets etc.).

        - Information for each  section is stored in dicts like `FILTER_CLASSES_DICT`.

        The following sections are processed here:

        :[Input Widgets]:
            Store (user) input widget classes in `INPUT_CLASSES_DICT`

        :[Plot Widgets]:
            Store (user) plot widget classes in `PLOT_CLASSES_DICT`

        :[Filter Widgets]:
            Store (user) filter widget classes in `FILTER_CLASSES_DICT`

        :[Fixpoint Widgets]:
            Store (user) fixpoint widget classes in `FIXPOINT_CLASSES_DICT`

        Parameters
        ----------
        None

        Returns
        -------
        None, but `fb.xxx` contains the parsed configuration file sections
        """

        # ------------------------------------------------------------------
        # Parsing [Input Widgets]
        # ------------------------------------------------------------------
        ConfigFileParser.INPUT_CLASSES_DICT =\
            self._build_widget_class_dict("Input Widgets", "input_widgets")
        # ------------------------------------------------------------------
        # Parsing [Plot Widgets]
        # ------------------------------------------------------------------
        ConfigFileParser.PLOT_CLASSES_DICT =\
            self._build_widget_class_dict("Plot Widgets", "plot_widgets")
        # ------------------------------------------------------------------
        # Parsing [Filter Widgets] -> filter_widgets
        # ------------------------------------------------------------------
        filter_classes = self._build_widget_class_dict("Filter Widgets", "filter_widgets")
        # Dict with filter classes as keys and dicts with options as values, e.g.
        # {'Cheby1':{'name':'Chebyshev 1',
        #            'mod':'pyfda.filter_design.cheby1',
        #            'fix': 'IIR_cascade',
        #            'opt': ["option1", "option2"]}}
        #
        # currently, option "opt" can only be an association with a fixpoint
        # widget, so replace key "opt" by key "fix":
        # Convert to list in any case

        for options in filter_classes.values():
            if 'opt' in options:
                options['fix'] = options.pop('opt')
            if 'fix' in options and\
                    isinstance(options['fix'], str):
                options['fix'] = options['fix'].split(',')

        # ------------------------------------------------------------------
        # Parsing [Fixpoint Filters] / modifying filter_classes dict
        # ------------------------------------------------------------------
        ConfigFileParser.FIXPOINT_CLASSES_DICT =\
            freeze_hierarchical(
                self._build_widget_class_dict("Fixpoint Widgets", "fixpoint_widgets"))

        # First check whether fixpoint options of the filter_classes are valid fixpoint
        # classes by comparing them to the verified items of `FIXPOINT_CLASSES_DICT:
        for c in filter_classes:
            if 'fix' in filter_classes[c]:
                for w in filter_classes[c]['fix']:
                    if w not in ConfigFileParser.FIXPOINT_CLASSES_DICT:
                        logger.warning(
                            'Removing invalid fixpoint module\n\t"%s" for filter class "%s".',
                            w, c)
                        filter_classes[c]['fix'].remove(w)

            # merge filter_classes info "filter class":[fx_class1, fx_class2]
            # and `FIXPOINT_CLASSES_DICT`` info "fixpoint class":[fil_class1, fil_class2]
            # into the filter_classes dict
            #
            # collect all fixpoint widgets (keys in FIXPOINT_CLASSES_DICT) which
            # have the class name c as a value
            fix_wdg = {
                k for k, val in ConfigFileParser.FIXPOINT_CLASSES_DICT.items() if c in val['opt']}
            if len(fix_wdg) > 0:
                if 'fix' in filter_classes[c]:
                    # ... and merge it with the fixpoint options of class c
                    fix_wdg = fix_wdg.union(filter_classes[c]['fix'])

                filter_classes[c].update({'fix': list(fix_wdg)})

        ConfigFileParser.FILTER_CLASSES_DICT = freeze_hierarchical(filter_classes)

    # --------------------------------------------------------------------------
    def _parse_conf_section(self, section: str) -> dict:
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
            # get entries from config file with [name, path]
            items_list = self.conf.items(section)

            if len(items_list) > 0:
                for i in items_list:
                    # sanitize value and convert to a list, split at \n and ,
                    val = i[1].strip(' \t\n\r[]"')
                    if len(i[1]) == 0:
                        val = ""
                    elif i[1][0] == '{':  # try to convert to dict
                        try:
                            val = ast.literal_eval(val)
                        except SyntaxError as e:
                            logger.warning("Syntax Error in config file\n%s", e)
                            val = ""
                    else:
                        val = re.sub(r'["\'\[\]]','', val)
                        val = re.split('; |, |\n|,\n|\r', val)  # TODO: Test

                    section_conf_dict.update({i[0]: val})

                logger.debug('Found %2d entries in [%s].', len(section_conf_dict), section)
            else:
                logger.warning('Empty section [%s].', section)

        except configparser.NoSectionError:
            logger.warning(
                "\n[WARNING] No section '[%s]' in config file %s,\n\t"
                "consider creating a new config file using 'pyfdax -r' .\n",
                section, dirs.USER_CONF_DIR_FILE
            )
            # configparser.NoOptionError
        except configparser.DuplicateOptionError as e:
            logger.warning('%s in config file "%s".', e, dirs.USER_CONF_DIR_FILE)

        except configparser.InterpolationMissingOptionError as e:
            # catch unresolvable interpolations like ${wrongSection:wrongOption}
            # Attention: This terminates  current section() without result!
            logger.warning('%s in config file "%s".', e, dirs.USER_CONF_DIR_FILE)

        return section_conf_dict

    # --------------------------------------------------------------------------
    def _build_widget_class_dict(self, section: str, subpackage: str = "") -> dict:
        """
        - Try to dynamically import the modules (= files) parsed in `section`
          reading their module level attribute `classes` listing the classes
          contained in the module.

          When `classes` is a dictionary, e.g. `{"Cheby":"Chebyshev 1"}` where
          the key is the class name in the module and the value the corresponding
          display name (used for the combo box).

        - When `classes` is a string or a list, use the string resp. the list items
          for both class and display name.

        - Try to import the filter classes

        Parameters
        ----------
        section: str
            Name of the section in the configuration file to be parsed by
            ``self._parse_conf_section``.

        subpackage: str
            Name of the subpackage containing the module to be imported. Module
            names are prepended successively with
            `['pyfda.' + subpackage + '.', '', subpackage + '.']`

        Returns
        -------
        classes_dict : dict

        A dictionary with the classes as keys; values are dicts which define
        the options (like display name, module path, fixpoint implementations etc).

        Each entry has the form

        {<class name>:{'name':<display name>, 'mod':<full module name>}} e.g.

        .. code-block:: python

             {'Cheby1':{'name':'Chebyshev 1',
              'mod':'pyfda.filter_design.cheby1',
              'fix': 'IIR_cascade',
              'opt': ["option1", "option2"]}

        Clear initial setting and create a dict with all successfully imported classes:
        """
        classes_dict = {}
        num_imports = 0        # number of successful module imports
        imported_classes = ""  # names of successful module imports
        pckg_names = ['pyfda.'+subpackage+'.', '', subpackage+'.']  # search in that order

        section_conf_dict = self._parse_conf_section(section)

        for mod_name in section_conf_dict:  # iterate over dict keys found in config file
            for p in pckg_names:
                try:  # Try to import the module from the package list above
                    mod_fq_name = p + mod_name  # fully qualified module name (fqn)
                    # Try to import the module from the  package and get a handle:
                    logger.debug(mod_fq_name)
                    ################################################
                    mod = importlib.import_module(mod_fq_name)
                    ################################################
                    break  # -> successful import, break out of pckg_names loop
                except ImportError as e:
                    logger.warning('Import error for "%s":\n%s', mod_fq_name, e)
                    mod_fq_name = None
                    continue  # module not found, try next package
                except Exception as e:
                    logger.warning('Error during import of "%s":\n%s', mod_fq_name, e)
                    mod_fq_name = None
                    continue  # Some other error ocurred during import, try next package

            if not mod_fq_name:
                logger.warning('Module "%s" could not be imported.', mod_name)
                continue

            if hasattr(mod, 'classes'):
                # check type of module attribute 'classes', try to convert to dict
                if isinstance(mod.classes, dict):  # dict {class name : combo box name}
                    mod_dict = mod.classes  # one or more filter classes in one file
                elif isinstance(mod.classes, str):  # String, create a dict with the
                    mod_dict = {mod.classes: mod.classes}  # string as both key and value
                elif isinstance(mod.classes, list):  # list, create a dict with list items
                    mod_dict = {i: i for i in list}  # as both key and value
                else:
                    logger.warning("Skipping module '%s', its attribute 'classes' has the "
                                   "wrong type '%s'.", mod_name, type(mod.classes).__name__)
                    continue  # with next entry in section_conf_dict
            else:
                # no `classes` attribute - skip entry
                logger.warning(
                    'Skipping module "%s" due to missing attribute "classes".', mod_name)
                continue

            # Now, check whether class `c` is part of module `mod`
            for c in mod_dict:
                if not hasattr(mod, c):  # class c doesn't exist in module
                    logger.warning("Skipping class '%s', it doesn't exist in module '%s'.",
                                   c, mod_fq_name)
                    continue  # continue with next entry in classes_dict

                classes_dict.update(
                    {c: {'name': mod_dict[c],   # Class name
                            'mod': mod_fq_name}})  # Fully qualified module name
                # when module + class import was successful, add a new entry
                # to the dict with the class name as key and a dict containing
                # "name":display name and "mod":fully qualified module name as values,
                # e.g. 'Butter':{'name':'Butterworth',
                #                'mod':'pyfda.filter_design.butter'}

                # check whether options have been defined in the config file
                opt = section_conf_dict[mod_name]
                if opt:
                    if isinstance(opt, dict):
                        classes_dict[c].update(opt)
                    elif type(opt) in {str, list}:  # create dict {'opt':<OPTION>}
                        classes_dict[c].update({"opt": opt})
                    else:
                        logger.warning('Class "%s" option data type "%s" not understood:\n "%s"',
                                        c, type(opt).__name__, opt)

                num_imports += 1
                imported_classes += "\t" + mod_fq_name + "." + c + "\n"

        if num_imports < 1:
            logger.warning("No class could be imported.")
        else:
            logger.info("Found %d classes in [%s]:\n\t----------\n%s",
                        num_imports, section, imported_classes)

        return classes_dict


# ==============================================================================
if __name__ == "__main__":
    # Run widget standalone with `python -m pyfda.libs.config_file_parser`
    # The test information is taken from the dicts in filterbroker.py
    #
    logging.basicConfig(level=logging.INFO)
    from pyfda.libs.pyfda_lib import pprint_log
    cfp = ConfigFileParser()

    cfp.parse_conf_file()
    cfp.build_widget_tree()  # needs a working config file

    print('\nINPUT_CLASSES_DICT =\n', pprint_log(ConfigFileParser().INPUT_CLASSES_DICT))
    print('\nfPLOT_CLASSES_DICT =\n', pprint_log(ConfigFileParser().PLOT_CLASSES_DICT))
    print('\nFILTER_CLASSES_DICT =\n', pprint_log(ConfigFileParser().FILTER_CLASSES_DICT))
    print('\nFIXPOINT_CLASSES_DICT =\n', pprint_log(ConfigFileParser().FIXPOINT_CLASSES_DICT))
