# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

@author: Michael Winkler, Christian Münker
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import os, sys
import codecs
import filterbroker as fb


class FilterTreeBuilder(object):
    
    def __init__(self, filtDir, filtFile, commentChar = '#', DEBUG = False):
        """
        - Extract the names of all Python files in 'filtDir'/'filtFile'  
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
        self.filtDirFile = os.path.abspath(cwd+'/'+filtDir+"/"+ filtFile)
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
        # Scan filtFile for python file names and extract them
        fb.gD['filtFileNames'] = self.readFiltFile()
        
        # Try to import all filter modules in filtFileNames, store names and 
        # modules in a dict as {filterName:filterModule}:
        fb.gD['imports'] = self.dynFiltImport()
        
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

        Parameters
        ----------
        None
        
        Returns
        -------
        filtFileNames : List with Filenames (without .py) found in filtFile
        """

        filtFileComments = [] # comment lines from filtFile
        filtFileNames = [] # Filenames found in filtFile without .py
        
        try:
            # Try to open the filtFile in read mode:
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
                            filtFileNames.append(curLine[0:suffixPos])
                        
                curLine = fp.readline() # read next line
            
        except IOError as e:
            print('--- FilterFileReader.readFiltFile ---')
            print("Init file {0} could not be found.".format(self.filtDirFile))
            if self.DEBUG: 
                print("I/O error({0}): {1}".format(e.errno, e.strerror))

            filtFileComments = filtFileNames = []
            
        return filtFileNames

#==============================================================================
    def dynFiltImport(self):#, pyPackage):
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
        imports = {}
        
        for pyName in fb.gD['filtFileNames']:
            try:
                # Try to import the module from the subDirectory (= package)
                importedModule = __import__(self.filtDir + '.' + pyName, 
                                            fromlist=[''])
  
                # when successful, add the filename without '.py' and the 
                # dynamically imported module to the dict 'imports' which
                # looks like that:
                
#                {'cheby1': <module 'filterDesign.cheby1' from ...
                imports.update({pyName:importedModule})
                
                
              #  Now, modules should be deleted from memory (?)
                del sys.modules[self.filtDir + '.' + pyName]      
                
            except ImportError:
                if self.DEBUG: 
                    print("Error in 'FilterFileReader.dynamicImport()':" )
                    print("Module '%s' could not be imported."%pyName) 
                    
        return imports
 
#==============================================================================
    def buildFilTree(self):
        """
        Read info attributes (ft, rt, fo) from all filter objects (dm) and build 
        a dictionary of all possible filter combinations from it 
        with the hierarchy:
        
        response type -> filter type -> design method  -> filter order        
        rt ('LP')        ft ('IIR')     dm ('Elliptic')   fo ('min','man')
        
        For each branch (filter combination), all the attributes found in the
        corresponding filter class are stored, e.g.
        'par':['f_S', 'F_PB', 'F_SB', 'A_PB', 'A_SB']   # required parameters
        'msg':r"<br /><b>Note:</b> Order needs to be even!" # message
        'enb':['fo','fspecs','wspecs']                     # enabled widgets
        'vis':['fo','fspecs']  # visibe widgets (not yet implemented) 
     """
        filTree = {}
        for dm in fb.gD['imports']:           # iterate over designMethods(dm)
            myFilter = self.objectWizzard(dm) # instantiate object of filter class dm
            ft = myFilter.ft                  # get filter type ('FIR')
            
            for rt in myFilter.rt:            # iterate over response types
                if rt not in filTree:         # is rt key in dict already?
                    filTree.update({rt:{}})   # no, create it

                if ft not in filTree[rt]:  # is ft key already in dict[rt]?
                    filTree[rt].update({ft:{}}) # no, create it
                filTree[rt][ft].update({dm:{}}) # append dm to list dict[rt][ft]
                # finally append all the individual 'min' / 'man' info 
                # to dm in filTree. These are e.g. the params for 'min' and /or
                # 'man' filter order
                filTree[rt][ft][dm].update(myFilter.rt[rt]) 

                # combine common info for all response types 
                #     com = {'man':{...}, 'min':{...}}
                # with individual info from the last step
                #      e.g. {..., 'LP':{'man':{...}, 'min':{...}} 

                for minman in myFilter.com:
                    # add info only when 'man' / 'min' exists in filTree
                    if minman in filTree[rt][ft][dm]: 
                        for i in myFilter.com[minman]:
                            # Test whether entry exists in filTree:
                            if i in filTree[rt][ft][dm][minman]:
                                # yes, prepend common data
                                filTree[rt][ft][dm][minman][i] =\
                                myFilter.com[minman][i] + filTree[rt][ft][dm][minman][i]
                            else:
                                # no, create new entry
                                filTree[rt][ft][dm][minman].update(\
                                                {i:myFilter.com[minman][i]})

                            if self.DEBUG:
                                print('--- FilterFileReader.buildFilterTree ---')
                                print(dm, minman, i)
                                print("filTree[minman][i]:",
                                      filTree[rt][ft][dm][minman][i])
                                print("myFilter.com[minman][i]",
                                  myFilter.com[minman][i] )

            del myFilter # delete obsolete filter object (needed?)
            
        if self.DEBUG: print("filTree = ", filTree)
        
        return filTree
        
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

        inst = getattr(fb.gD['imports'][objectName], objectName)
            
        if (inst != None):# yes, the attribute exists, return the instance
            return inst()
        else:
            if self.DEBUG: 
                print('--- FilterFileReader.objectWizzard ---')
                print("Unknown object '{0}', could not be created,".format(objectName))
                print("Class: FilterFileReader.objectWizzard\n")
            
#==============================================================================
if __name__ == "__main__":

#    import filterbroker as fb
    print("===== Initialize FilterReader ====")
    
    filtFileName = "init.txt"
    subDirectory = "filter_design"
    commentChar  = '#'  
    Debug = True
    
    # Create a new FilterFileReader instance & initialize it
    myTreeBuilder = FilterTreeBuilder(subDirectory, filtFileName, commentChar, Debug)

    print("\n===== Start Test ====")    
    for name in fb.gD['imports']:
        myFilter = myTreeBuilder.objectWizzard(name)
        print('myFilter', myFilter)
    myFilterTree = myTreeBuilder.buildFilTree()
    print('myFilterTree = ', myFilterTree)
    print(fb.gD['imports'])
    