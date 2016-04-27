# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

@author: Michael Winkler, Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import os, sys
from pprint import pformat
import codecs
import importlib
import logging
logger = logging.getLogger(__name__)

import pyfda.filterbroker as fb


class FilterTreeBuilder(object):
    """
    Construct a tree with all the filter combinations

    Parameters
    ----------

    filt_dir: string
        Name of the subdirectory containing the init-file and the
        Python files to be read, needs to have __init__.py)

    filt_list: string
        Name of the init file

    comment_char: char
        comment character at the beginning of a comment line

    """

    def __init__(self, filt_dir, filt_list, comment_char='#'):
        cwd = os.path.dirname(os.path.abspath(__file__))
        self.filt_dir_file = os.path.join(cwd, filt_dir, filt_list)

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
        self.read_filt_file()

        # Try to import all filter modules found in filter_list, store names and
        # modules in the dict self.design_methods as {filterName:filterModule}:
        self.dyn_filt_import()

        # Build a hierarchical dict fb.fil_tree with all valid filter designs
        # and response types:
        self.build_fil_tree()

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
        - Collect valid file names (without .py) self.filt_list_names

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        filt_list_comments = []     # comment lines from filt_list
        # List with design method file names (= class names) in filt_list
        # (without .py suffix):
        self.filt_list_names = []

        num_filters = 0           # number of filter design files found

        try:
            # Try to open filt_dir_file in read mode:
 #           fp = open(self.initDirFile,'rU', 1) # 1 = line buffered
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
                            self.filt_list_names.append(cur_line[0:suffix_pos])
                            num_filters += 1

                cur_line = fp.readline() # read next line

            logger.info("%d entries found in filter list!\n", num_filters)
            fp.close()
            
        except IOError as e:
            logger.critical( 'Init file "%s" could not be found.\n\
                I/O Error(%d): %s' %(self.filt_dir_file, e.errno, e.strerror))
            sys.exit( 'Init file "%s" could not be found.\n\
                I/O Error(%d): %s' %(self.filt_dir_file, e.errno, e.strerror))
            
        except Exception as e:
            logger.error( "Unexpected error: %s", e)
            sys.exit( "Unexpected error: %s", e)

#==============================================================================
    def dyn_filt_import(self):
        """
        Try to import all modules / classes found by readFiltFile() from
        self.filt_dir (= subdirectory with filter design algorithms + __init__.py).

        The class names (= file name without .py) and the corresponding modules
        with full name (e.g. ' filter_design.cheby1') are returned as dict
        'imports'.

        Reads:
        ----------

        self.filt_dir
            Subdirectory filt_dir with the Python-Files to import from
            IMPORTANT: filt_dir has to contain an __init__.py File

        self.filt_list_names
            List with the classes to be imported, contained in the
            Python files (ending with .py !!) in pyPackage

        Returns
        -------

        None, results are stored in

        fb.design_methods: dict  containing entries (for SUCCESSFUL imports)

            {file name without .py (= class name):full module name}
             e.g. {"cheby1":"pyfda.filter_design.cheby1"}

        """
        fb.design_methods = {} # clear global dict
        num_imports = 0   # initialize number of successful filter imports

        for dm in self.filt_list_names:
            try:
                # Try to import the module from the  package)
                # http://stackoverflow.com/questions/2724260/why-does-pythons-import-require-fromlist
                module_name = 'pyfda.' + self.filt_dir + '.' + dm

                importlib.import_module(module_name)

                # when successful, add the filename without '.py' and the
                # full module name to the dict 'imports', e.g.
                #      {'cheby1': 'pyfda.filter_design.cheby1'}
                fb.design_methods.update({dm:module_name})
                num_imports += 1

                #  Now, module should be deleted to free memory (?)
                del sys.modules[module_name]

            except ImportError as e:
                logger.error('Filter design "%s" could not be imported.', dm)
            except Exception as e:
                logger.error("Unexpected error: %s", e)
           

        methods = ""
        for dm in fb.design_methods:
            methods += "\t" + dm + "\n"

        logger.info("Imported successfully the following %d filter designs:\n%s", 
                    num_imports, methods)

#==============================================================================
    def build_fil_tree(self):
        """
        Read attributes (ft, rt, rt:fo) from all design method (dm) classes
        listed in the global dict fb.gD['imports']. Attributes are stored in
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

        Build a dictionary of all filter combinations with the hierarchy:

        response types -> filter types -> design methods  -> filter order
        rt (e.g. 'LP')    ft (e.g. 'IIR') dm (e.g. 'cheby1') fo ('min' or 'man')

        Additionally, all the attributes found in each filter branch ()
        corresponding design method class are stored, e.g.
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

        fb.fil_tree = {}
        fb.dm_names = {}
        for dm in fb.design_methods:  # iterate over keys in designMethods (= dm)

            # instantiate / update global instance of filter class dm
            fb.fil_factory.create_fil_inst(dm)
            try:
                fb.dm_names.update(fb.fil_inst.name)
            except AttributeError:
                logger.warning('Skipping design method "%s" due to missing attribute "name"', dm)
                continue # continue with next entry in design_methods
            ft = fb.fil_inst.ft                  # get filter type (e.g. 'FIR')

            for rt in fb.fil_inst.rt:            # iterate over response types
                if rt not in fb.fil_tree:           # is rt key already in dict?
                    fb.fil_tree.update({rt:{}})     # no, create it

                if ft not in fb.fil_tree[rt]:  # is ft key already in dict[rt]?
                    fb.fil_tree[rt].update({ft:{}}) # no, create it
                fb.fil_tree[rt][ft].update({dm:{}}) # append dm to list dict[rt][ft]
                # finally append all the individual 'min' / 'man' info
                # to dm in fb.fil_tree. These are e.g. the params for 'min' and /or
                # 'man' filter order
                fb.fil_tree[rt][ft][dm].update(fb.fil_inst.rt[rt])

                # combine common info for all response types
                #     com = {'man':{...}, 'min':{...}}
                # with individual info from the last step
                #      e.g. {..., 'LP':{'man':{...}, 'min':{...}}

                for minman in fb.fil_inst.com:
                    # add info only when 'man' / 'min' exists in fb.fil_tree
                    if minman in fb.fil_tree[rt][ft][dm]:
                        for i in fb.fil_inst.com[minman]:
                            # Test whether entry exists in fb.fil_tree:
                            if i in fb.fil_tree[rt][ft][dm][minman]:
                                # yes, prepend common data
                                fb.fil_tree[rt][ft][dm][minman][i] =\
                                fb.fil_inst.com[minman][i] + fb.fil_tree[rt][ft][dm][minman][i]
                            else:
                                # no, create new entry
                                fb.fil_tree[rt][ft][dm][minman].update(\
                                                {i:fb.fil_inst.com[minman][i]})

                            logger.debug("%s - %s - %s\n"
                                "fb.fil_tree[rt][ft][dm][minman][i]: %s\n"
                                "fb.fil_inst.com[minman][i]: %s",
                                 dm, minman, i,
                                 pformat(fb.fil_tree[rt][ft][dm][minman][i]), 
                                 pformat(fb.fil_inst.com[minman][i]))

#            del cur_filter # delete obsolete filter object (needed?)

        logger.debug("\nfb.fil_tree =\n%s", pformat(fb.fil_tree))


#==============================================================================
if __name__ == "__main__":

    # Need to start a QApplication to avoid the error
    #  "QWidget: Must construct a QApplication before a QPaintDevice"
    # when instantiating filters with dynamic widgets (equiripple, firwin)

    from PyQt4 import QtGui
    app = QtGui.QApplication(sys.argv)
#    import pyfda.filterbroker as fb
    print("===== Initialize FilterReader ====")

    filt_file_name = "filter_list.txt"
    filt_dir = "filter_design"
    comment_char = '#'

    # Create a new FilterFileReader instance & initialize it
    myTreeBuilder = FilterTreeBuilder(filt_dir, filt_file_name, comment_char)

    print("\n===== Start Test ====")
    filterTree = myTreeBuilder.build_fil_tree()
    print('fb.fil_tree = ', fb.fil_tree)
