# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

@author: Michael Winkler, Christian Münker
"""
from __future__ import print_function, division, unicode_literals
import os, sys
import codecs
import databroker as db

# TODO: need to delete unused imports from memory? 
# TODO: replace __import__ by importlib.import_module()

class FilterFileReader(object):
    
    def __init__(self, initFile, directory, commentChar = '#', DEBUG = False):
        """
        - Extract the names of all Python files in 'initFile' in 'directory'  
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
        self.initDirFile = os.path.abspath(cwd+'/'+directory+"/"+ initFile)
        if DEBUG: print(self.initDirFile)
        self.DEBUG = DEBUG


        # Scan initFile for python file names and extract them
        db.gD['initFileNames'] = self.readInitFile(commentChar)
        
        # Try to import all filter modules in initFileNames, store names and 
        # modules in a dict {filterName:filterModule}:
        db.gD['imports'] = self.dynamicImport(directory,db.gD['initFileNames'])
        
        # Build a hierarchical dict with all found filter designs and 
        # response types:
        db.gD['filterTree'] = self.buildFilterTree()

#==============================================================================
    def readInitFile(self, commentChar = '#'):
        """
        Extract all file names = class names from self.initDirFile:
        - Lines that don't begin with commentCh are stripped from Newline 
          character, whitespace, '.py' and everything after it and returned as
          a list.
        - Lines starting with self.commentChar are stripped of newline, 
          whitespace and comment chars and written to list 'initFileComments'
        - All other lines are discarded (for now)

        Parameters
        ----------
        None
        
        Returns
        -------
        initFileNames : List with Filenames (without .py) found in initFile
        """

        initFileComments = [] # comment lines from initFile
        initFileNames = [] # Filenames found in initFile without .py
        
        try:
            # Try to open the initFile in read mode:
 #           fp = open(self.initDirFile,'rU', 1) # 1 = line buffered
            fp = codecs.open(self.initDirFile,'rU', encoding='utf-8')
            curLine = fp.readline()
            
            while curLine: # read until currentLine is empty (EOF reached)
                # remove white space and Newline characters at beginning and end:
#                curLine = curLine.encode('UTF-8')
                curLine = curLine.strip(' \n')
                # Only process line if it is longer than 1 character
                if len(curLine) > 1:
                    # Does current line begin with the comment character?
                    if(curLine[0] == commentChar): 
                        # yes, append line to list initFileComments :
                            initFileComments.append((curLine[1:])) 
                    # No, this is not a comment line
                    else:
                        # Is '.py' contained in curLine? Starting at which pos?
                        suffixPos = curLine.find(".py")
                        if(suffixPos > 0):
                            # Yes, strip '.py' and all characters after, 
                            # append the file name to the lines list, 
                            # otherwise discard the line
                            initFileNames.append(curLine[0:suffixPos])
                        
                curLine = fp.readline() # read next line
            
        except IOError as e:
            print('--- FilterFileReader.readInitFile ---')
            print("Init file {0} could not be found.".format(self.initDirFile))
            if self.DEBUG: 
                print("I/O error({0}): {1}".format(e.errno, e.strerror))

            initFileComments = initFileNames = []
            
        return initFileNames

#==============================================================================
    def dynamicImport(self, pyPackage, pyNames):
        """
        Try to import all modules / classes in 'pyNames' from 
        'pyPackage' (= subdirectory with __init__.py).
        
        The class names (= file name without .py) and the corresponding modules
        with full name (e.g. ' filterDesign.cheby1') are returned as dict
        'imports'.     
        
        Parameters
        ----------
        
        pyPackage:
            Subdirectory pyPackage with the Python-Files to import from
            IMPORTANT: pyPackage has to contain an __init__.py File
            
        pyNames:
            List with the classes to be imported, contained in the
            Python files (ending with .py !!) in pyPackage
            
        Returns
        -------
        
        imports : dict  containing - for SUCCESSFUL imports -

            {
             file names without .py (= class names), e.g. 'cheby1' in
            :
             full module names <module 'filterDesign.cheby1'> with path name in
            }

        """
        imports = {}
        
        for pyName in pyNames:
            try:
                # Try to import the module from the subDirectory (= package)
                importedModule = __import__(pyPackage + '.' + pyName, 
                                            fromlist=[''])
  
                # when successful, add the filename without '.py' and the 
                # dynamically imported module to the dict 'imports' which
                # looks like that:
                
#                {'cheby1': <module 'filterDesign.cheby1' from ...
                imports.update({pyName:importedModule})
                
                
              #  Now, modules should be deleted from memory (?)
#                setattr(pyPackage, pyName, None)
#                del sys.modules[pyPackage.pyName]
#                del pyName
                
            except ImportError:
                if self.DEBUG: 
                    print("Error in 'FilterFileReader.dynamicImport()':" )
                    print("Module '%s' could not be imported."%pyName) 
                    
        return imports
   
#==============================================================================
    def objectWizzard(self, objectName):
        """
        Try to create an instance of "objectName". This is only possible 
        when the corresponding module has been imported already, e.g. using
        the function dynamicImport.

        E.g.  self.myFilter = fr.objectWizzard('cheby1')
        
        Parameters
        ----------
        objectName: string
        
            The object to be constructed (e.g. 'cheby1' or 'equiripple')
            
        Returns
        -------
        The instance
        
        """

        inst = getattr(db.gD['imports'][objectName], objectName)
            
        if (inst != None):# yes, the attribute exists, return the instance
            return inst()
        else:
            if self.DEBUG: 
                print('--- FilterFileReader.objectWizzard ---')
                print("Unknown object '{0}', could not be created,".format(objectName))
                print("Class: FilterFileReader.objectWizzard\n")
 
#==============================================================================
    def buildFilterTree(self):
        """
        Read info attributes (ft, rt) from all filter objects and build 
        a tree of all possible filter combinatiions from it, with the elements
        - response type (rt): 'LP' (lowpass), 'HP' ...
        - filter type (ft): 'FIR', 'IIR', ... 
        - design method (dm): 'cheby1', 'equiripple', ...
        """
        filterTree = {}
        for dm in db.gD['imports']:           # iterate over designMethods 
            myFilter = self.objectWizzard(dm) # instantiate filter class
            ft = myFilter.ft                  # get filter type ('FIR')
            for rt in myFilter.rt:            # iterate over response types
                if rt not in filterTree:      # is rt in dict already?
                    filterTree.update({rt:{}}) # no, create it
                if ft not in filterTree[rt]:  # is ft already in dict[rt]?
                    filterTree[rt].update({ft:{}}) # no, create it
                filterTree[rt][ft].update({dm:{}}) # append dm to list dict[rt][ft]
                filterTree[rt][ft][dm].update(myFilter.rt[rt]) # append fo dict

        if self.DEBUG: print("filterTree = ", filterTree)
        
        return filterTree
            
#==============================================================================
if __name__ == "__main__":

#    import databroker as db
    print("===== Initialize FilterReader ====")
    
    initFileName = "Init.txt"
    subDirectory = "filterDesign"
    commentChar  = '#'  
    Debug = True
    
    # Create a new FilterFileReader instance & initialize it
    myFilterReader = FilterFileReader(initFileName, subDirectory, commentChar, Debug)

    print("\n===== Start Test ====")    
    for name in db.gD['imports']:
        myFilter = myFilterReader.objectWizzard(name)
        print('myFilter', myFilter)
    myFilterTree = myFilterReader.buildFilterTree()
    print('myFilterTree = ', myFilterTree)
    print(db.gD['imports'])
    