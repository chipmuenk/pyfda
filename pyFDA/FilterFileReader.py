# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

@author: Michael Winkler, Christian Münker
"""
from __future__ import print_function, division
import os, sys
import databroker as db


# TODO: extract module name in dynamicImport via dict lookup, not iteration
# TODO: need to delete unused imports from memory? 

class FilterFileReader(object):
    
#==============================================================================
#Funktion __init__    
#==============================================================================
    def __init__(self, initFile, directory, commentChar = '#', DEBUG = False):
        """
        FilterFileReader liest das Init.txt File des pyFDA-tools aus,
        importiert die in dem InitFile stehenden PythonFiles und gibt jeweils ein
        Objekt dieser Files zurück.
        WICHTIG: die PythonFiles müssen eine Klasse haben, die gleich dem
        Dateinamen ist (nat. ohne Suffix .py)
       
        Parameters
        ----------

        directory:
            Name of the subdirectory containing the init-file and the 
            Python files to be read, needs to have __init__.py)
            
        fileName:
            Name of the init file
            
        commentChar: char
            comment character at the beginning of a comment line
            
        DEBUG: Boolean
            True/False, for printing verbose debug messages
        """
        cwd = os.path.dirname(os.path.abspath(__file__))
        self.initDirFile = os.path.abspath(cwd+'/'+directory+"/"+ initFile)
        print(self.initDirFile)
        self.DEBUG = DEBUG


        # Scan initFile for python file names and extract them
        db.gD['initFileNames'] = self.readInitFile(commentChar)
        # Try to import all filter modules in initFileNames:
        self.dynamicImport(directory, db.gD['initFileNames'])
        self.buildDesignTree()

        
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
            fp = open(self.initDirFile,'r', 1) # 1 = line buffered
            curLine = fp.readline()
            
            while curLine: # read until currentLine is empty (EOF reached)
                # remove white space and Newline characters at beginning and end:
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
        
        The class name (= file name without .py) is appended to        
        db.gD["importedFiles"] for each successful import. The module with full
        name (e.g. ' filterDesign.cheby1') is appended to 
        db.gD["importedModules"].
        
        
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
        
        None:
            dynamicImport creates the following lists in databroker.py, 
            containing - for SUCCESSFUL imports -

            - file names without .py (= class names), e.g. 'cheby1' in
                db.gD['importedFiles']
                
            - full module names <module 'filterDesign.cheby1'> with path name in
                db.gD['importedModules']

        """
        db.gD['importedFiles'] = [] 
        db.gD['importedModules'] = [] 

        if self.DEBUG:
            print('--- FilterFileReader.dynamicImport ---')
            print('pyNames:', pyNames)      
        
        for pyName in pyNames:
            try:
                # Try to import the module from the subDirectory (= package)
                db.gD['importedModules'].append(__import__
                                    (pyPackage + '.' + pyName, fromlist=['']))
  
                # when successful, add the filename without '.py' to
                # the list importedFiles:
                db.gD['importedFiles'].append(pyName)
                
              #  Now, modules should be deleted from memory (?)
#                setattr(pyPackage, pyName, None)
#                del sys.modules[pyPackage.pyName]
#                del pyName
                
            except ImportError:
                if self.DEBUG: 
                    print("Error in 'FilterFileReader.dynamicImport()':" )
                    print("Module '%s' could not be imported."%pyName) 
                    
#        db.gD["filterObjects"] = []
#        for line in db.gD['importedFiles']:                
#                db.gD["filterObjects"].append(self.objectWizzard(line))
#
#        if self.DEBUG:
#            print("filterObjects:", db.gD["filterObjects"])
   
#==============================================================================
    def objectWizzard(self, objectType):
        """
        Try to create an instance of type "objectType". This is only possible 
        when the corresponding module has been imported already, e.g. using
        the function dynamicImport.

        E.g.  self.myFilter = fr.objectWizzard('cheby1')
        
        Parameters
        ----------
        ObjectType:
            The object to be constructed (e.g. cheby1 or equiripple)
            
        Returns
        -------
        The instance
        
        """
        inst = None
        if self.DEBUG:
            print('--- ObjectWizzard ---')
            print('importedFiles:', db.gD['importedFiles'])
            print('importedModules:', db.gD['importedModules'])
        # iterate over both lists at the same time by "zipping" the lists           
        for name, module in zip(db.gD['importedFiles'], db.gD['importedModules']):
            if name == objectType:
                # create object instance by getting a named attribute <name> 
                # from the object given in module
                inst = getattr(module, name) # = module.<name>
                print(inst)
            
        if (inst != None):# yes, the attribute exists, return the instance
            return inst()
        else:
            if self.DEBUG: 
                print("Unknown object '{0}', could not be created,".format(objectType))
                print("Class: FilterFileReader.objectWizzard\n")
 
#==============================================================================
    def buildDesignTree(self):
        """
        Read the info attribute from all filter objects and build a tree of 
        all possible filter options from it
        """
        designTree = {}
        for name in db.gD['importedFiles']:
            myFilter = self.objectWizzard(name)
            designTree.update({name:myFilter.rt})
        print("designTree = ", designTree)
            
            
            

     

#==============================================================================
if __name__ == "__main__":
    #Für das Auslesen des InitFiles essentielle Angaben!

#    import databroker as db
    
    initFileName = "Init.txt"
    subDirectory = "filterDesign"
 #   subDirectory = "."
    commentChar  = '#'  
    Debug = True
    
    #Hilfsvariable
    i = 0
    

    #Liste zum Abspeichern der Objekt-Pointer
    FilterObjects = []
    
    #Erstellen eines neuen FilterFileReader Objektes
    MyFilterReader = FilterFileReader(initFileName, subDirectory, commentChar, Debug)
    FilterObjects = db.gD["filterObjects"]# MyFilterReader.GiveAllFilterObjects()
    
    for elements in FilterObjects:
        print(FilterObjects)
        print(FilterObjects[i].has())
        i = i + 1
        print("\n")
    
"""   
    #Auslesen des Init-Textfiles. Trennen des Inhaltes in Zeilen und Kommentarzeilen
    Zeilen, Kommentarzeilen = myFilterFileReader.Read_FilterInitFile(initFileName,commentChar)
    
    #Die nicht Kommentarzeilen Importieren
    myFilterFileReader.dynamicImport(subDirectory, Zeilen)
    
    
    #von jeder Importierten Klasse ein Objekt erstellen u. auf d. Konsole ausgeben
    i = 0
    for elements in Zeilen:
        if(elements != ''):                              
            FilterObjects.append(myFilterFileReader.ObjectWizzard(elements[0:-3]))
            i = i + 1
            
            if(FilterObjects[i-1] != None):
                print(FilterObjects[i-1])
                print(FilterObjects[i-1].has())
                print("\n")
               
"""