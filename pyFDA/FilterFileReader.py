# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

@author: Michael Winkler
"""
import os

import databroker as db

class FilterFileReader(object):
    

#==============================================================================
#Funktion __init__    
#==============================================================================
    def __init__(self, FileName, Directory, commentCh = '#', Debug = False):
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
        db.gD['imports'] = []
        db.gD['importNames'] = [] # names of imported modules
        self.subDirectory = Directory
        self.initFileName = Directory + "/" + FileName  
        self.commentChar = commentCh
        self.DEBUG = Debug
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
        lines, commentLines = self.readInitFile(self.initFileName, 
                                                self.commentChar)
                                                
        self.dynamicImport(self.subDirectory, lines)

        for line in lines:                
                db.gD["filterObjects"].append(self.ObjectWizzard(line.replace(".py", "")))

        print("filterObjects", db.gD["filterObjects"])

#==============================================================================
# Method readInitFile
#==============================================================================
    def readInitFile(self, initFileName, commentCh):
        """
        Read_FilterInitFile opens the file initFileName and reads all lines:
        - Lines that don't begin with commentCh are stripped of the Newline 
          character and passed back as a list.
        - Lines starting with commentCh are passed back without Newline and 
          commentCh as a second list.

        Parameters
        ----------
        initFileName: String containing name of init file
        
        commentCh: Character defining a comment line
        
        Returns
        -------
        1. list: Non-comment lines
        
        2. list: Comment lines
        """
        fp = None
        lines = []
        commentLines = []
        initFileNameCwd = self.cwd + "/" + initFileName
        
        try:
            # Try to open the initFile in read mode
            fp = open(initFileNameCwd,'r',-1)
            curLine = fp.readline()
            
            while curLine: # read until currentLine is empty (EOF reached)
                # remove white space and Newline characters at beginning and end:
                curLine = curLine.strip(' \n')
                # Only process line if it is longer than 1 character
                if len(curLine) > 1:
                    # does the line begin with the comment character?
                    if(curLine[0] == commentCh): 
                        # yes, remove it and append line to commentLines:
                        commentLines.append((curLine[1:])) 
                    # No, this is not a comment line
                    else:
                        # Position of '.py' in curLine:
                        suffixPos = curLine.find(".py") 
                        if(suffixPos > 0):
                            # Strip .py and any further characters
                            lines.append(curLine[0:suffixPos+3])
                        
                curLine = fp.readline()
            
        except IOError as e:
            print("File named {0} could not be found.".format(initFileNameCwd))
            if self.DEBUG: print("I/O error({0}): {1}".format(e.errno, e.strerror))

            del lines
            del commentLines
            lines = commentLines = "InitFile not found!"
    
        return lines, commentLines
            
        
#==============================================================================
# Method dynamicImport
#==============================================================================
    def dynamicImport(self, subDirectory, Files):
        """
        dynamicImport importiert aus dem übergegebenen "subDirectory" alle in
        "Files" spezifizierten Python-Files.
        
        Sollte der Import funktioniert haben, wird der Klassenname(= Filename)
        in "_ImportNames" abgelegt. Der eigentliche Import wird in der Files "_Imports"
        abgespeichert,
        
        Parameters
        ----------
        
        subDirectory:
            Das Unterverzeichnis mit den zu importierenden Python-Files.
            WICHTIG: das subDirectory muss einen __init__.py File enthalten
            
        Files:
            In "Files" steht der Dateiname des zu importierenden Python-Files.
            WICHTIG: Ein Pythonfile endet auf .py!
            
        Returns
        -------
        
        None:
            dynamicImport creates the following lists in databroker.py
            
            db.gD['imports']     : contains the actual imports
            db.gD['importNames'] : contains the class names = file names without .py 
 
        """
        
        for temp in Files:
            print(temp)
            if(temp.find(".py",0) > 0):                
                try:
                    # Try to import the file
                    db.gD['imports'].append(__import__("{0}.{1}".format(subDirectory,
                                    temp.replace(".py", "")), fromlist=['']))
#                    db.gD['imports'].append(__import__("{0}.{1}".format(subDirectory,
#                                    temp.replace(".py", "")), fromlist=['']))                    
                    # when successful, add the filename without suffix .py to
                    # the list _ImportNames .
                    db.gD['importNames'].append(temp.replace(".py", ""))
                    
                except ImportError:
                    if self.DEBUG: 
                        print("Error in 'FilterFileReader.dynamicImport()':" )
                        print("File %s.py could not be imported."%temp[0:-3])

        print("_Imports", db.gD['imports'])
        print("_ImportNames", db.gD['importNames'])                    
            
                
#==============================================================================
#Funktion ObjectWizzard
#==============================================================================
    def ObjectWizzard(self, ObjectTyp):
        """
        ObjectWizzard versucht ein Objekt des Typs "ObjectTyp" zu erstellen.
        ObjectWizzard kann nur Objekte erstellen, welche durch die Funktion dynamicImport
        eingebunden wurden. Für das pyFDA-Tool sind dies z.B. die Filter-Files.
        
        Parameters
        ----------
        ObjectType:
            Das Objekt welches erstellt werden soll. (z.B. cheby1 oder equiripple)
        
        """
        i = 0
        temp = None
        
        for element in db.gD['importNames']:
            if element == ObjectTyp:
 #           if(db.gD['importNames'][i] == ObjectTyp):
                temp = getattr(db.gD['imports'][i], db.gD['importNames'][i])
#            else:
#                i = i + 1

        if (temp != None):
            return temp()
        else:
            if self.DEBUG: 
                print("Es konnte kein {0}-Objekt erstellt werden,".format(ObjectTyp))
                print("da der Objektname unbekannt ist. Klasse: FilterFileReader Funktion: ObjectWizzard\n")
       
##==============================================================================
##Funktion DebugMsg                
##==============================================================================
#    def Debug_Msg(self, DebugMsg):
#        """
#        Debug_Msg ist eine Hilfsfunktion welche Debuginformationen zur verfügung
#        stellt.
#        Debuginformationen werden nur bei gesetztem DEBUG-Define angezeigt.
#                
#        Parameters
#        ----------
#        
#        self : 
#        
#        DebugMsg: String welcher die Debugnachricht enthällt und 
#        DEBUG == True ausgegeben wird.
#        """
#        if(self.DEBUG):
#            print(DebugMsg)
           
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