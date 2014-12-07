# -*- coding: utf-8 -*-
"""
Created on Mon Nov 24 10:00:14 2014

@author: Michael Winkler
"""
import os

import databroker as db

class FilterFileReader(object):
    
#==============================================================================
# Class Globals
#==============================================================================

    _Imports = []   #Speicherort für die Importierten Module
    _ImportNames = [] #Speicherort für die FilterNamen der Importierten Module
      
#==============================================================================
#Funktion __init__    
#==============================================================================
    def __init__(self, FileName, Directory, commentCh, Debug):
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
        self.subDirectory = Directory
        self.initFileName = Directory + "/" + FileName  
        self.commentChar = commentCh
        self.DEBUG = Debug
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        
        self.GiveAllFilterObjects()
           
#==============================================================================
#Funktion GiveAllFilterObjects
#==============================================================================
    def GiveAllFilterObjects(self):
        """
        GiveAllFilterObjects liefert alle verfügbaren FilterObjekte zurück.
        Wichtig: GiveAllFilterObjects wertet erneut das Init.txt File aus,
        somit können Filter.py Files "on the flight" ausgetauscht/erweitert werden.
        """
        i = 0
        db.gD["filterObjects"] = []
        
        Zeilen, Kommentarzeilen = self.Read_FilterInitFile(self.initFileName, 
                                                           self.commentChar)
        self.dynamicImport(subDirectory, Zeilen)
        
        
        for elements in Zeilen:
            if(Zeilen[i].find(".py",0,len(Zeilen[i])) > 0 ): 
                
                temp = self.ObjectWizzard(Zeilen[i].replace(".py", ""))
                if(temp != None):
                    db.gD["filterObjects"].append(temp)   
                
            i = i + 1
            
        print(db.gD["filterObjects"])
        return db.gD["filterObjects"]
        
        

#==============================================================================
#Funktion Read_FilterInitFile
#==============================================================================
    def Read_FilterInitFile(self,FileName,KommChar):
        """
        Read_FilterInitFile öffnet die in FileName referenzierte Datei und liest diese aus.
        Dabei wird unterschieden zwischen Kommentarzeilen im File (beginnend mit 'KommChar'
        und normalen Zeilen.
        Kommentarzeilen, sowie normale Zeilen werden ohne "NewLine" bzw. KommChar
        in dafür vorgesehene Listen abgespeichert.
        
        Die Funktion gibt 2 Listen zurück.
        Die erste Liste enthällt alle Zeilen, welche nicht als Kommentarzeile
        identifiziert wurden.
        Die 2. Liste enthällt alle restlichen zeilen
        
        Parameters
        ----------
        FileName :String mit dem Filenamen
        
        KommChar :Das Kommentarzeichen auf das geprüft wird
        
        Returns
        -------
        1.Liste: Nicht Kommentarzeilen
        
        2.Liste: Kommentarzeilen
        """
        fp = None
        Lines = []
        InfoLines = []
        
        
        try:
            #Öffnet das InitFile "NAME", 'Zugriffsmods = Nur lesen',
            #Buffering = Systemdefault
            fp = open(self.cwd + "/" + FileName,'r',-1)
        except IOError as e:
            print(self.cwd + "/" + FileName)
            self.Debug_Msg( "I/O error({0}): {1}".format(e.errno, e.strerror))
            self.Debug_Msg("Das File Namens {0} konnte nicht gefunden werden.".format( FileName))
            del Lines
            del InfoLines
            Lines = InfoLines = "InitFile nicht gefunden!"
    
        #Hier nur weiter machen, wenn das File geöffnet werden konnte.
        if(fp != None):
            while(fp != None):
                currentLine = fp.readline()
                
                #wenn die gelesene Zeile leer ist, haben wir EoF (End of File) erreicht
                if(currentLine == ''):
                    fp = None
                else:            
                    #beginnt die gelesene Zeile mit einem Kommentarzeichen?
                    if(currentLine[0] == KommChar):
                        
                        #ist das letzte Zeichen der Zeile ein NewLine '\n'?
                        if(currentLine[len(currentLine)-1] == '\n'):
                            
                        #wenn Ja schneide das 1. u. letzte Element ab ('#' und \n)
                            InfoLines.append((currentLine[1:-1]))
                        #wenn Nein, schneide nur das 1. Element ab ('#')
                        else:
                            InfoLines.append((currentLine[1:0]))
                            
                    #Es handelt sich um keine Kommentarzeile
                    else:
                        #ist das letzte Zeichen der Zeile ein NewLine '\n'?
                        if(currentLine[len(currentLine)-1] == '\n'):
                            #wenn Ja schneide das letzte Element ab
                            Lines.append(currentLine[0:-1])
                        else:
                            Lines.append(currentLine)
                            
        return Lines, InfoLines
        
#==============================================================================
#Funktion dynamicImport
#==============================================================================
    def dynamicImport(self,subDirectory, Files):
        """
        dynamicImport importiert aus dem übergegebenen "subDirectory" alle in
        "Files" spezifizierten Python-Files.
        
        Sollte der Import funktioniert haben, wird der Klassenname(= Filename)
        in "_ImportNames" abgelegt. Der eigentliche Import wird in der Files "_Imports"
        abgespeichert,
        
        Parameters
        ----------
        
        subDirectory:
            Das Unterverzeichniss, in dem die zu Importierenden PythonFiles sind.
            WICHTIG: das subDirectory muss vorher mit einem __init__.py File
            initiieren werden.
            
        Files:
            In "Files" steht der Dateiname des zu importierenden Python-Files.
            WICHTIG: Ein Pythonfile endet auf .py!
            
        Returns
        -------
        
        Keine:
            dynamicImport editiert die globelen Klassenvariablen von ChooseParams.
            
            Diese sind:
                _Imports[] --> enthällt den eigentlichen Import
                _ImportNames[] --> enthällt den FileNamen (hier OHNE den Suffix .py)
 
        """
        
        for temp in Files:
            print(temp)
            if(temp.find(".py",0,len(temp)) > 0 ):                
                try:
                    # Try to import the file
                    self._Imports.append(__import__("{0}.{1}".format(subDirectory,
                                    temp.replace(".py", "")), fromlist=['']))
                    
                    # when successful, add the filename without suffix .py to
                    # the list _ImportNames .
                    self._ImportNames.append(temp.replace(".py", ""))
                    
                except ImportError:
                    self.Debug_Msg("Fehler: Datei %s.py konnte nicht Importiert werden. Klasse: FilterFileReader Funktion: dynamicImport\n" %temp[0:-3])
                    
                
#==============================================================================
#Funktion ObjectWizzard
#==============================================================================
    def ObjectWizzard(self, ObjectTyp):
        """
        ObjectWizzard versucht ein Objekt des Typs "ObjectTyp" zu erstellen.
        ObjectWizzard kann nur Objekte ertellen, welche durch die Funktion dynamicImport
        eingebunden wurden. Für das pyFDA-Tool sind dies z.B. die Filter-Files.
        
        Parameters
        ----------
        ObjectType:
            Das Objekt welches erstellt werden soll. (z.B. cheby1 oder equiripple)
        
        """
        i = 0
        temp = None
        
        for elements in self._ImportNames:
            if(self._ImportNames[i] == ObjectTyp):
                temp = getattr(self._Imports[i], self._ImportNames[i])
            else:
                i = i + 1

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

    import databroker as db
    
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