# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

@author: Michael Winkler, Christian Münker
"""
import os
import databroker as db

class FilterFileReader(object):
    

#==============================================================================
#Funktion __init__    
#==============================================================================
    def __init__(self, fileName, directory, commentCh = '#', DEBUG = False):
        """
        FilterFileReader liest das Init.txt File des pyFDA-tools aus,
        importiert die in dem InitFile stehenden PythonFiles und gibt jeweils ein
        Objekt dieser Files zurück.
        WICHTIG: die PythonFiles müssen eine Klasse haben, die gleich dem
        Dateinamen ist (nat. ohne Suffix .py)
       
        Parameters
        ----------

        Directory:
            Name of the subdirectory containing the init-file and the 
            Python files to be read
            
        FileName:
            Name of the init file
            
        commentCh:
            comment character at the beginning of a comment line
            
        Debug:
            True/False, for printing verbose debug messages
        """
        
        self.subDirectory = directory #(= package, needs to have __init__.py)
        self.initFile = directory + "/" + fileName  
        self.commentChar = commentCh
        self.DEBUG = DEBUG
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        
        self.readAllFilterObjects()
           
#==============================================================================
# Method readAllFilterObjects
#==============================================================================
    def readAllFilterObjects(self):
        """
        readAllFilterObjects liefert alle verfügbaren FilterObjekte zurück.
        Wichtig: readAllFilterObjects wertet beim Aufruf das Init.txt File aus,
        somit können Filter.py Files "on the flight" ohne Neustart 
        ausgetauscht/erweitert werden.
        """

        db.gD["filterObjects"] = []
        # parse the initFile.py, giving back one list with the lines containing
        # python files and one with comment lines:  

        self.readInitFile(self.initFile, self.commentChar)
                                                
        self.dynamicImport(self.subDirectory, db.gD['initFileNames'])

        for line in db.gD['importNames']:                
                db.gD["filterObjects"].append(self.objectWizzard(line))

        print("filterObjects:", db.gD["filterObjects"])

#==============================================================================
    def readInitFile(self, initFile, commentCh):
        """
        Reads all lines from initFile:
        - Lines that don't begin with commentCh are stripped from Newline 
          character, whitespace, '.py' and everything after it and written
          to gD["initFileNames"][].
        - Lines starting with commentCh are stripped off of Newline, 
          whitespace and commentCh and written to gD["initFileComments"][]
        - All other lines are discarded (for now)

        Parameters
        ----------
        initFile: String containing name of init file
        
        commentCh: Character defining a comment line
        
        Returns
        -------
        None
        
          gD["initFileNames"][]
          gD["initFileComments"][]
        """

        db.gD['initFileComments'] = [] # comment lines from initFile
        db.gD['initFileNames'] = [] # Filenames found in initFile without .py

 
        initFileCwd = self.cwd + "/" + initFile
        
        try:
            # Try to open the initFile in read mode
            fp = open(initFileCwd,'r', 1) # 1 = line buffered
            curLine = fp.readline()
            
            while curLine: # read until currentLine is empty (EOF reached)
                # remove white space and Newline characters at beginning and end:
                curLine = curLine.strip(' \n')
                # Only process line if it is longer than 1 character
                if len(curLine) > 1:
                    # Does current line begin with the comment character?
                    if(curLine[0] == commentCh): 
                        # yes, remove it and append line to commentLines:
                            db.gD['initFileComments'].append((curLine[1:])) 
                    # No, this is not a comment line
                    else:
                        # Is '.py' contained in curLine?
                        suffixPos = curLine.find(".py")
                        if(suffixPos > 0):
                            # Yes, strip '.py' and all characters after, 
                            # append the file name to the lines list, 
                            # otherwise discard the line
                            db.gD['initFileNames'].append(curLine[0:suffixPos])
                        
                curLine = fp.readline() # read next line
            
        except IOError as e:
            print("Init file named\n{0} could not be found.".format(initFileCwd))
            if self.DEBUG: 
                print("I/O error({0}): {1}".format(e.errno, e.strerror))

            db.gD['initFileComments'] = db.gD['initFileNames'] = []           

#==============================================================================
    def dynamicImport(self, pyPackage, pyNames):
        """
        dynamicImport tries to import all modules / classes given in 'pyNames'
        from python files in 'package' (= subdirectory with __init__.py).
        
        Hat der Import funktioniert, wird der Klassenname(= Filename) in
        db.gD["importNames"] abgelegt. Das Modul mit vollständigem Namen 
        (e.g. ' filterDesign.cheby1') wird in  db.gD["importModules"] abgespeichert,
        
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
            dynamicImport creates the following lists in databroker.py
            
            db.gD['importModules'] : contains actual imported Modules
            db.gD['importNames'] : contains class names = file names without .py 
 
        """
        db.gD['importNames'] = [] # names of imported files (without .py)
        db.gD['importModules'] = [] # actual imported modules (with path)

        if self.DEBUG:
            print('--- dynamicImport ---')
            print('pyNames:', pyNames)      
        
        for pyName in pyNames:
            try:
                # Try to import the module from the subDirectory (= package)
                db.gD['importModules'].append(__import__
                                    (pyPackage + '.' + pyName, fromlist=['']))
  
                # when successful, add the filename without '.py' to
                # the list importNames:
                db.gD['importNames'].append(pyName)
                
            except ImportError:
                if self.DEBUG: 
                    print("Error in 'FilterFileReader.dynamicImport()':" )
                    print("Module '%s' could not be imported."%pyName) 
   
#==============================================================================
    def objectWizzard(self, objectType):
        """
        ObjectWizzard versucht ein Objekt vom Typ "objectType" zu erstellen.
        ObjectWizzard kann nur Objekte erstellen, welche durch die Funktion dynamicImport
        eingebunden wurden. Für das pyFDA-Tool sind dies z.B. die Filter-Files.
        
        Parameters
        ----------
        ObjectType:
            The object to be constructed (e.g. cheby1 or equiripple)
            
        Returns
        -------
        The object
        
        """
        temp = None
        if self.DEBUG:
            print('--- ObjectWizzard ---')
            print('importNames:', db.gD['importNames'])
            print('importModules:', db.gD['importModules'])
        # iterate over both lists at the same time by "zipping" the lists           
        for name, module in zip(db.gD['importNames'], db.gD['importModules']):
            if name == objectType:
                temp = getattr(module, name)
                print(temp)
            
        if (temp != None):
            return temp()
        else:
            if self.DEBUG: 
                print("Es konnte kein {0}-Objekt erstellt werden,".format(objectType))
                print("da der Objektname unbekannt ist. Klasse: FilterFileReader Funktion: ObjectWizzard\n")
      
           
#==============================================================================
#Debug Main
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