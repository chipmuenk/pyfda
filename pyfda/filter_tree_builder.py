# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

@author: Michael Winkler, Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import os, sys
import codecs
import pyfda.filterbroker as fb


class FilterTreeBuilder(object):
    
    def __init__(self, filtDir, filter_file, commentChar = '#', DEBUG = False):
        """
        - Extract the names of all Python files in 'filtDir'/'filter_file'  
          and write them to a list
        - Try to import all python files and return a dict with all file names 
          and corresponding objects (the class needs to have the same name as 
          the file)
        - Construct a tree with all the filter combinations
       
        Parameters
        ----------

        directory: string
            Name of the subdirectory containing the init-file and the 
            Python files to be read, needs to have __init__.py)
            
        fileName: string
            Name of the init file
            
        commentChar: char
            comment character at the beginning of a comment line
            
        DEBUG: Boolean
            True/False, for printing verbose debug messages
        """
        cwd = os.path.dirname(os.path.abspath(__file__))
#        self.filtDirFile = os.path.abspath(cwd + '/' + filtDir + "/" + filter_file)
        self.filtDirFile = os.path.join(cwd, filtDir, filter_file)
        if DEBUG: print(self.filtDirFile)
        self.DEBUG = DEBUG
        self.commentChar = commentChar
        self.filtDir = filtDir
        
        self.initFilters()

#==============================================================================
    def initFilters(self):
        """
        - Extract the names of all Python files in the file specified during  
          instantiation (self.filtDirFile) and write them to a list
        - Try to import all python files and return a dict with all file names 
          and corresponding objects (the class needs to have the same name as 
          the file)
        - Construct a tree with all the filter combinations
        
        This method can also be called when the main app runs to re-read the
        filter directory
        """
        # Scan filter_file.txt for python file names and extract them
        self.readFiltFile()
        
        # Try to import all filter modules in filtFileNames, store names and 
        # modules in the dict self.design_methods as {filterName:filterModule}:
        self.dynFiltImport()
        
        # Build a hierarchical dict with all valid filter designs and 
        # response types:
        fb.filTree = self.buildFilTree()
        
#==============================================================================
    def readFiltFile(self):
        """
        Extract all file names = class names from self.filtDirFile:
        - Lines that don't begin with commentCh are stripped from Newline 
          character, whitespace, '.py' and everything after it and returned as
          a list.
        - Lines starting with self.commentChar are stripped of newline, 
          whitespace and comment chars and written to list 'filtFileComments'
        - All other lines are discarded (for now)
        - Collect valid file names (without .py) self.filt_file_names

        Parameters
        ----------
        None
        
        Returns
        -------
        None
        """

        filtFileComments = []     # comment lines from filter_file
        # List with design method file names (= class names) in filter_file
        # (without .py suffix):
        self.filt_file_names = [] 
        
        num_filters = 0           # number of filter design files found
        
        try:
            # Try to open filtDirFile in read mode:
 #           fp = open(self.initDirFile,'rU', 1) # 1 = line buffered
            fp = codecs.open(self.filtDirFile,'rU', encoding='utf-8')
            curLine = fp.readline()
            
            while curLine: # read until currentLine is empty (EOF reached)
                # remove white space and Newline characters at beginning and end:
#                curLine = curLine.encode('UTF-8')
                curLine = curLine.strip(' \n')
                # Only process line if it is longer than 1 character
                if len(curLine) > 1:
                    # Does current line begin with the comment character?
                    if(curLine[0] == self.commentChar): 
                        # yes, append line to list filtFileComments :
                            filtFileComments.append((curLine[1:])) 
                    # No, this is not a comment line
                    else:
                        # Is '.py' contained in curLine? Starting at which pos?
                        suffixPos = curLine.find(".py")
                        if(suffixPos > 0):
                            # Yes, strip '.py' and all characters after, 
                            # append the file name to the lines list, 
                            # otherwise discard the line
                            self.filt_file_names.append(curLine[0:suffixPos])
                            num_filters += 1
                        
                curLine = fp.readline() # read next line
                
            print("FilterTreeBuilder: Filter list read, {0} entries found!\n"
                                                        .format(num_filters))
            
        except IOError as e:
            print("--- FilterTreeBuilder.readFiltFile ---")
            print("Init file {0} could not be found.".format(self.filtDirFile))
            if self.DEBUG: 
                print("I/O error({0}): {1}".format(e.errno, e.strerror))

            filtFileComments = self.filt_file_names = []
            

#==============================================================================
    def dynFiltImport(self):
        """
        Try to import all modules / classes found by readFiltFile() from 
        self.filtDir (= subdirectory with filter design algorithms + __init__.py).
        
        The class names (= file name without .py) and the corresponding modules
        with full name (e.g. ' filter_design.cheby1') are returned as dict
        'imports'.     
        
        Reads:
        ----------
        
        self.filtDir
            Subdirectory filtDir with the Python-Files to import from
            IMPORTANT: filtDir has to contain an __init__.py File
            
        fb.gD['imports']
            List with the classes to be imported, contained in the
            Python files (ending with .py !!) in pyPackage
            
        Returns
        -------
        
        imports : dict  containing entries (for SUCCESSFUL imports)

            {
             file name without .py (= class names), e.g. 'cheby1' in
            :
             full module name <module 'filter_design.cheby1'> with path name
            }

        """
        self.design_methods = {} # dict with filter name and 
        num_imports = 0   # number of successful filter imports
        
        for pyName in self.filt_file_names:
            try:
                # Try to import the module from the subDirectory (= package)
                importedModule = __import__('pyfda.' + self.filtDir + '.' + pyName, 
                                            fromlist=[''])
  
                # when successful, add the filename without '.py' and the 
                # dynamically imported module to the dict 'imports' which
                # looks like that:
                
#                {'cheby1': <module 'filterDesign.cheby1' from ...
                self.design_methods.update({pyName:importedModule})
                num_imports += 1
                
                
              #  Now, modules should be deleted from memory (?)
                del sys.modules['pyfda.' + self.filtDir + '.' + pyName]      
                
            except ImportError as e:
                print(e)
                print("Error in 'FilterTreeBuilder.dynFiltImport()':")
                print("Filter design '%s' could not be imported."%pyName)

        print("FilterTreeBuilder: Imported successfully the following "
                    "{0} filter designs:".format(num_imports))
        for dm in self.design_methods: 
            print(dm)
        print("\n")
 
#==============================================================================
    def buildFilTree(self):
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
        
        filTree : dict with filter tree 

        """
     
        filTree = {}
        for dm in self.design_methods:           # iterate over found designMethods(dm)

            cur_filter = self.objectWizzard(dm) # instantiate object of filter class dm

            ft = cur_filter.ft                  # get filter type ('FIR')
            
            for rt in cur_filter.rt:            # iterate over response types
                if rt not in filTree:           # is rt key in dict already?
                    filTree.update({rt:{}})     # no, create it

                if ft not in filTree[rt]:  # is ft key already in dict[rt]?
                    filTree[rt].update({ft:{}}) # no, create it
                filTree[rt][ft].update({dm:{}}) # append dm to list dict[rt][ft]
                # finally append all the individual 'min' / 'man' info 
                # to dm in filTree. These are e.g. the params for 'min' and /or
                # 'man' filter order
                filTree[rt][ft][dm].update(cur_filter.rt[rt]) 

                # combine common info for all response types 
                #     com = {'man':{...}, 'min':{...}}
                # with individual info from the last step
                #      e.g. {..., 'LP':{'man':{...}, 'min':{...}} 

                for minman in cur_filter.com:
                    # add info only when 'man' / 'min' exists in filTree
                    if minman in filTree[rt][ft][dm]: 
                        for i in cur_filter.com[minman]:
                            # Test whether entry exists in filTree:
                            if i in filTree[rt][ft][dm][minman]:
                                # yes, prepend common data
                                filTree[rt][ft][dm][minman][i] =\
                                cur_filter.com[minman][i] + filTree[rt][ft][dm][minman][i]
                            else:
                                # no, create new entry
                                filTree[rt][ft][dm][minman].update(\
                                                {i:cur_filter.com[minman][i]})

                            if self.DEBUG:
                                print('\n--- FilterFileReader.buildFilterTree ---')
                                print(dm, minman, i)
                                print("filTree[minman][i]:",
                                      filTree[rt][ft][dm][minman][i])
                                print("cur_filter.com[minman][i]",
                                  cur_filter.com[minman][i] )

            del cur_filter # delete obsolete filter object (needed?)
            
        if self.DEBUG: print("filTree = ", filTree)
        
        return filTree
        
#==============================================================================
    def objectWizzard(self, objectName):
        """
        Try to create an instance of "objectName". This is only possible 
        when the corresponding module has been imported already, e.g. using
        the method dynFiltImport.

        E.g.  self.cur_filter = fr.objectWizzard('cheby1')
        
        Parameters
        ----------
        objectName: string
        
            The object to be constructed (e.g. 'cheby1' or 'equiripple')
            
        Returns
        -------
        The instance
        
        """

        inst = getattr(self.design_methods[objectName], objectName)
            
        if (inst != None):# yes, the attribute exists, return the instance
            return inst()
        else:
            print('--- FilterTreeBuilder.objectWizzard\n ---')
            print("Unknown object '{0}', could not be created,".format(objectName))
            return None
            
#==============================================================================
if __name__ == "__main__":
    
    # Need to start a QApplication to avoid the error
    #  "QWidget: Must construct a QApplication before a QPaintDevice"
    # when instantiating filters with dynamic widgets (equiripple, firwin)

    from PyQt4 import QtGui
    app = QtGui.QApplication(sys.argv)
#    import filterbroker as fb
    print("===== Initialize FilterReader ====")
    
    filtFileName = "filter_list.txt"
    subDirectory = "filter_design"
    commentChar  = '#'  
    Debug = False
    
    # Create a new FilterFileReader instance & initialize it
    myTreeBuilder = FilterTreeBuilder(subDirectory, filtFileName, commentChar, Debug)

    print("\n===== Start Test ====")    
    for name in fb.gD['imports']:
        cur_filter = myTreeBuilder.objectWizzard(name)
        print('cur_filter', cur_filter)
    filterTree = myTreeBuilder.buildFilTree()
    print('filterTree = ', filterTree)
    