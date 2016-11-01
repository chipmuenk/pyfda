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

        # Build a hierarchical dict fb.fil_tree with all valid filter designs
        # and response types:
        self.build_fil_tree()

#==============================================================================
    def read_filt_file(self):
        # TODO: file name shouldn't have to be identical to class name, 
        #       multiple classes per file should be possible.
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
                # remove white space and Newline characters at beginning and end:
#                cur_line = cur_line.encode('UTF-8')
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
                logger.warning('Filter module "%s" could not be imported.', filt_mod)
                continue
            except Exception as e:
                logger.warning("Unexpected error during module import:\n%s", e)
                continue
            # Now, try to instantiate an instance ff.fil_inst() of filter class fc
            for fc in fdict:
                if not hasattr(mod, fc): # class k doesn't exist in filter module
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
    def build_fil_tree(self):
        """
        Read attributes (ft, rt, rt:fo) from all filter classes (fc)
        listed in the global dict ``fb.fil_classes``. Attributes are stored in
        the design method classes in the format (example from cheby1.py)

        self.ft = 'IIR'
        self.rt = {
          "LP": {"man":{"par":[]},
                 "min":{"par":['F_PB','F_SB']}},
          "HP": {"man":{"par":[]},
                 "min":{"par":['F_SB','F_PB']}},
          "BP": {"man":{"par":['F_C2']},
                 "min":{"par":['F_SB','F_PB','F_PB2','F_SB2']}},
          "BS": {"man":{"par":['F_C2']},
                 "min":{"par":['F_PB','F_SB','F_SB2','F_PB2']}}
                 }

        Build a dictionary of all filter combinations with the following hierarchy:

        response types -> filter types -> filter classes  -> filter order
        rt (e.g. 'LP')    ft (e.g. 'IIR') fc (e.g. 'cheby1') fo ('min' or 'man')

        Additionally, all the attributes found in each filter branch (e.g. cheby1.LPmin)
        are stored, e.g.
        'par':['f_S', 'F_PB', 'F_SB', 'A_PB', 'A_SB']   # required parameters
        'msg':r"<br /><b>Note:</b> Order needs to be even!" # message
        'dis':['fo','fspecs','wspecs']  # disabled widgets
        'vis':['fo','fspecs']           # visible widgets

        Reads
        -----


        Returns
        -------

        fil_tree : dict with filter tree

        """

        fb.fil_tree = {} # Dict with a hierarical tree fc-ft- ...

        for fc in fb.fil_classes:  # iterate over keys (= fc)

            # instantiate a global instance ff.fil_inst() of filter class fc
            err_code = ff.fil_factory.create_fil_inst(fc)
            if err_code > 0:
                logger.warning('Skipping filter class "%s" due to import error %d', fc, err_code)
                continue # continue with next entry in fb.fil_classes
                
            ft = ff.fil_inst.ft                  # get filter type (e.g. 'FIR')

            for rt in ff.fil_inst.rt:            # iterate over response types
                if rt not in fb.fil_tree:           # is rt key already in dict?
                    fb.fil_tree.update({rt:{}})     # no, create it

                if ft not in fb.fil_tree[rt]:  # is ft key already in dict[rt]?
                    fb.fil_tree[rt].update({ft:{}}) # no, create it
                fb.fil_tree[rt][ft].update({fc:{}}) # append fc to list dict[rt][ft]
                # finally append all the individual 'min' / 'man' / ' targ' info
                # to fc in fb.fil_tree. These are e.g. the params for 'min' / 'man' 
                # filter order and 'targ' specifications
                fb.fil_tree[rt][ft][fc].update(ff.fil_inst.rt[rt])

                # combine common info for all response types
                #     com = {'man':{...}, 'min':{...}, 'targ':{...}}
                # with individual info from the last step
                #      e.g. {..., 'LP':{'man':{...}, 'min':{...}, 'targ':{...}}

                for mmt in ff.fil_inst.com: # read common parameters Min/Man/Targ
                    # add info only when 'man'/'min'/'targ' exists for the rt-fc combination
                    if mmt in fb.fil_tree[rt][ft][fc]:
                        for p in ff.fil_inst.com[mmt]: # yes, add all info in mmt
                            # Test whether entry exists already in fb.fil_tree:
                            if p in fb.fil_tree[rt][ft][fc][mmt]:
                                # yes, prepend common data
                                fb.fil_tree[rt][ft][fc][mmt][p] =\
                                ff.fil_inst.com[mmt][p] + fb.fil_tree[rt][ft][fc][mmt][p]
                            else:
                                # no, create new entry
                                fb.fil_tree[rt][ft][fc][mmt].update(\
                                                {p:ff.fil_inst.com[mmt][p]})

                            logger.debug("%s - %s - %s\n"
                                "fb.fil_tree[rt][ft][fc][par][i]: %s\n"
                                "fb.fil_inst.com[par][i]: %s",
                                 fc, mmt, p,
                                 pformat(fb.fil_tree[rt][ft][fc][mmt][p]), 
                                 pformat(ff.fil_inst.com[mmt][p]))

        logger.debug("\nfb.fil_tree =\n%s", pformat(fb.fil_tree))


#==============================================================================
if __name__ == "__main__":

    # Need to start a QApplication to avoid the error
    #  "QWidget: Must construct a QApplication before a QPaintDevice"
    # when instantiating filters with dynamic widgets (equiripple, firwin)
    from PyQt4 import QtGui
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
