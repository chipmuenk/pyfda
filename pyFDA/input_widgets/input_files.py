# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for exporting / importing and saving / loading data
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import scipy.io
import numpy as np
import re

#import shelve
try:
    import cPickle as pickle
except:
    import pickle
import pprint

try:
    import xlwt
except ImportError:
    XLWT = False
    print("Warning: Module xlwt not installed -> no *.xls import / export")
else:
    XLWT = True

try:
    import XlsxWriter as xlsx
except ImportError:
    XLSX = False
    print("Warning: Module XlsxWriter not installed -> no *.xlsx import / export")
else:
    XLSX = True

import xlrd

try:
    import myhdl
except ImportError:
    MYHDL = False
    print("Warning: Module myHDL not installed -> no filter synthesis")
else:
    MYHDL = True

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(os.path.dirname(__cwd__))

import filterbroker as fb # importing filterbroker initializes all its globals
import pyfda_lib_fix_v3 as fix

# TODO: Get rid of error messages when cancelling a file operation
# TODO: Save P/Z as well if possible

class InputFiles(QtGui.QWidget):
    """
    Create the widget for entering exporting / importing / saving / loading data
    """
    
    sigFilterDesigned = pyqtSignal()

    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputFiles, self).__init__()
        
        self.basedir = os.path.dirname(os.path.abspath(__file__))
        self.basedir = 'D:/Daten'
#        print("basedir =", self.basedir)

        self.initUI()

    def initUI(self):
        """
        Intitialize the main GUI, consisting of:
        - Buttons for Exporting and Saving
        -
        """
        # widget / subwindow for parameter selection
        self.butExport = QtGui.QPushButton("Export Coefficients", self)
        self.butImport = QtGui.QPushButton("Import Coefficients", self)
        self.butSave = QtGui.QPushButton("Save Filter", self)
        self.butLoad = QtGui.QPushButton("Load Filter", self)
#        self.butExportCSV = QtGui.QPushButton("Export -> CSV", self)

        # ============== UI Layout =====================================
        bfont = QtGui.QFont()
#        font.setPointSize(11)
        bfont.setBold(True)
        
        bifont = QtGui.QFont()
        bifont.setBold(True)
        bifont.setItalic(True)

        ifont = QtGui.QFont()
        ifont.setItalic(True)

        self.layVIO = QtGui.QVBoxLayout()
        self.layVIO.addWidget(self.butSave) # -> Matlab workspace
        self.layVIO.addWidget(self.butLoad) # -> Matlab workspace
        self.layVIO.addWidget(self.HLine())
        self.layVIO.addWidget(self.butExport) # export coeffs -> various formats
        self.layVIO.addWidget(self.butImport) # export coeffs -> various formats

        
#        self.layVExport.addWidget(self.butExportCSV) # -> CSV format
        self.layVIO.addStretch(1)

        layVMain = QtGui.QVBoxLayout()
        layVMain.addLayout(self.layVIO)

#        MYHDL = True # uncomment for test purposes
        if MYHDL:
            self.lblMyhdl1 = QtGui.QLabel("myHDL")
            self.lblMyhdl1.setFont(bfont)
            self.lblMyhdl2 = QtGui.QLabel("Enter variable formats as QI.QF:")

            
            ledMaxWid = 30 # Max. Width of QLineEdit fields
            qQuant = ['none', 'round', 'fix', 'floor']
            qOvfl = ['none', 'wrap', 'sat']
            tipOvfl = "Select overflow behaviour."
            tipQuant = "Select the kind of quantization."
            tipQI = "Specify number of integer bits."
            tipQF = "Specify number of fractional bits."
            lblQ = "Quant.:"
            lblOv = "Ovfl.:"


            self.lblQIQF  = QtGui.QLabel("QI.QF = ")

            self.lblDot_i = QtGui.QLabel(".")
            self.lblDot_c = QtGui.QLabel(".")
            self.lblQuant_c = QtGui.QLabel(lblQ)
            self.lblQOvfl_c = QtGui.QLabel(lblOv)
            self.lblDot_a = QtGui.QLabel(".")
            self.lblQuant_a = QtGui.QLabel(lblQ)
            self.lblQOvfl_a = QtGui.QLabel(lblOv)
            self.lblDot_o = QtGui.QLabel(".")
            self.lblQOvfl_o = QtGui.QLabel(lblOv)
            self.lblQuant_o = QtGui.QLabel(lblQ)

# -------------------------------------------------------------------

            self.lblQInput = QtGui.QLabel("Input:")
            self.lblQInput.setFont(bifont)
            self.ledQIInput = QtGui.QLineEdit()
            self.ledQIInput.setToolTip(tipQI)
            self.ledQIInput.setText("0")
            self.ledQIInput.setMaxLength(2) # maximum of 2 digits
            self.ledQIInput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
    
            self.ledQFInput = QtGui.QLineEdit()
            self.ledQFInput.setToolTip(tipQF)
            self.ledQFInput.setText("15")
            self.ledQFInput.setMaxLength(2) # maximum of 2 digits
            self.ledQFInput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

            self.layHButtonsHDL_i = QtGui.QHBoxLayout()
            self.layHButtonsHDL_i.addWidget(self.lblQInput)
            self.layHButtonsHDL_i.addStretch()
            self.layHButtonsHDL_i.addWidget(self.ledQIInput)
            self.layHButtonsHDL_i.addWidget(self.lblDot_i)
            self.layHButtonsHDL_i.addWidget(self.ledQFInput)
# -------------------------------------------------------------------
            self.lblQCoeff = QtGui.QLabel("Coeff:")
            self.lblQCoeff.setFont(bifont)
            self.ledQICoeff = QtGui.QLineEdit()
            self.ledQICoeff.setToolTip(tipQI)
            self.ledQICoeff.setText("0")
            self.ledQICoeff.setMaxLength(2) # maximum of 2 digits
            self.ledQICoeff.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
    
            self.ledQFCoeff = QtGui.QLineEdit()
            self.ledQFCoeff.setToolTip(tipQF)
            self.ledQFCoeff.setText("15")
            self.ledQFCoeff.setMaxLength(2) # maximum of 2 digits
    #        self.ledQFCoeff.setFixedWidth(30) # width of lineedit in points(?)
            self.ledQFCoeff.setMaximumWidth(ledMaxWid)

            self.layHButtonsHDL_c = QtGui.QHBoxLayout()
            self.layHButtonsHDL_c.addWidget(self.lblQCoeff)
            self.layHButtonsHDL_c.addStretch()
            self.layHButtonsHDL_c.addWidget(self.ledQICoeff)
            self.layHButtonsHDL_c.addWidget(self.lblDot_c)
            self.layHButtonsHDL_c.addWidget(self.ledQFCoeff)
# -------------------------------------------------------------------
            self.cmbQuant_c = QtGui.QComboBox()
            self.cmbQuant_c.addItems(qQuant)
            self.cmbQuant_c.setToolTip(tipQuant)
            self.cmbOvfl_c = QtGui.QComboBox()
            self.cmbOvfl_c.addItems(qOvfl)
            self.cmbOvfl_c.setToolTip(tipOvfl)
    
            # ComboBox size is adjusted automatically to fit the longest element
            self.cmbQuant_c.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
            self.cmbOvfl_c.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

            self.layHButtonsHDL_cc = QtGui.QHBoxLayout()
            self.layHButtonsHDL_cc.addWidget(self.lblQOvfl_c)            
            self.layHButtonsHDL_cc.addWidget(self.cmbOvfl_c)
            self.layHButtonsHDL_cc.addStretch()
            self.layHButtonsHDL_cc.addWidget(self.lblQuant_c)
            self.layHButtonsHDL_cc.addWidget(self.cmbQuant_c)
# -----------------------------------------------------------------------------
            self.lblQAccu = QtGui.QLabel("Accu:")
            self.lblQAccu.setFont(bifont)
            self.ledQIAccu = QtGui.QLineEdit()
            self.ledQIAccu.setToolTip(tipQI)
            self.ledQIAccu.setText("0")
            self.ledQIAccu.setMaxLength(2) # maximum of 2 digits
            self.ledQIAccu.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
    
            self.ledQFAccu = QtGui.QLineEdit()
            self.ledQFAccu.setToolTip(tipQF)
            self.ledQFAccu.setText("15")
            self.ledQFAccu.setMaxLength(2) # maximum of 2 digits
            self.ledQFAccu.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

            self.layHButtonsHDL_a = QtGui.QHBoxLayout()
            self.layHButtonsHDL_a.addWidget(self.lblQAccu)
            self.layHButtonsHDL_a.addStretch()
            self.layHButtonsHDL_a.addWidget(self.ledQIAccu)
            self.layHButtonsHDL_a.addWidget(self.lblDot_o)
            self.layHButtonsHDL_a.addWidget(self.ledQFAccu)
# -------------------------------------------------------------------
            self.cmbQuant_a = QtGui.QComboBox()
            self.cmbQuant_a.addItems(qQuant)
            self.cmbQuant_a.setToolTip(tipQuant)
            self.cmbOvfl_a = QtGui.QComboBox()
            self.cmbOvfl_a.addItems(qOvfl)
            self.cmbOvfl_a.setToolTip(tipOvfl)
    
            # ComboBox size is adjusted automatically to fit the longest element
            self.cmbQuant_a.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
            self.cmbOvfl_a.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

            self.layHButtonsHDL_ac = QtGui.QHBoxLayout()
            self.layHButtonsHDL_ac.addWidget(self.lblQOvfl_a)            
            self.layHButtonsHDL_ac.addWidget(self.cmbOvfl_a)
            self.layHButtonsHDL_ac.addStretch()
            self.layHButtonsHDL_ac.addWidget(self.lblQuant_a)
            self.layHButtonsHDL_ac.addWidget(self.cmbQuant_a)

# -------------------------------------------------------------------
            self.lblQOutput = QtGui.QLabel("Output:")
            self.lblQOutput.setFont(bifont)
            self.ledQIOutput = QtGui.QLineEdit()
            self.ledQIOutput.setToolTip(tipQI)
            self.ledQIOutput.setText("0")
            self.ledQIOutput.setMaxLength(2) # maximum of 2 digits
            self.ledQIOutput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)
    
            self.ledQFOutput = QtGui.QLineEdit()
            self.ledQFOutput.setToolTip(tipQF)
            self.ledQFOutput.setText("15")
            self.ledQFOutput.setMaxLength(2) # maximum of 2 digits
            self.ledQFOutput.setFixedWidth(ledMaxWid) # width of lineedit in points(?)

            self.layHButtonsHDL_o = QtGui.QHBoxLayout()
            self.layHButtonsHDL_o.addWidget(self.lblQOutput)
            self.layHButtonsHDL_o.addStretch()
            self.layHButtonsHDL_o.addWidget(self.ledQIOutput)
            self.layHButtonsHDL_o.addWidget(self.lblDot_o)
            self.layHButtonsHDL_o.addWidget(self.ledQFOutput)
# -------------------------------------------------------------------
            self.cmbQuant_o = QtGui.QComboBox()
            self.cmbQuant_o.addItems(qQuant)
            self.cmbQuant_o.setToolTip(tipQuant)
            self.cmbOvfl_o = QtGui.QComboBox()
            self.cmbOvfl_o.addItems(qOvfl)
            self.cmbOvfl_o.setToolTip(tipOvfl)
    
            # ComboBox size is adjusted automatically to fit the longest element
            self.cmbQuant_o.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
            self.cmbOvfl_o.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)

            self.layHButtonsHDL_oc = QtGui.QHBoxLayout()
            self.layHButtonsHDL_oc.addWidget(self.lblQOvfl_o)            
            self.layHButtonsHDL_oc.addWidget(self.cmbOvfl_o)
            self.layHButtonsHDL_oc.addStretch()
            self.layHButtonsHDL_oc.addWidget(self.lblQuant_o)
            self.layHButtonsHDL_oc.addWidget(self.cmbQuant_o)

            self.cmbHDL = QtGui.QComboBox()
            self.cmbHDL.addItems(['Verilog','VHDL'])
            self.cmbHDL.setToolTip("Select type of HDL for filter synthesis.")

            self.butHDL = QtGui.QPushButton()
            self.butHDL.setToolTip("Quantize coefficients = 0 with a magnitude < eps.")
            self.butHDL.setText("Create HDL")
            
            self.layHButtonsHDL_h = QtGui.QHBoxLayout()
            self.layHButtonsHDL_h.addWidget(self.cmbHDL)            
            self.layHButtonsHDL_h.addWidget(self.butHDL)
# -------------------------------------------------------------------


            layVMain.addWidget(self.HLine())

            layVMain.addWidget(self.lblMyhdl1)
            layVMain.addWidget(self.lblMyhdl2)
            layVMain.addLayout(self.layHButtonsHDL_i)
            
            layVMain.addLayout(self.layHButtonsHDL_c)
            layVMain.addLayout(self.layHButtonsHDL_cc)
            
            layVMain.addLayout(self.layHButtonsHDL_a)
            layVMain.addLayout(self.layHButtonsHDL_ac)
    
            layVMain.addLayout(self.layHButtonsHDL_o)
            layVMain.addLayout(self.layHButtonsHDL_oc)
            
            layVMain.addLayout(self.layHButtonsHDL_h)
            
            self.butHDL.clicked.connect(self.exportHDL)
# -------------------------------------------------------------------

            
        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.butExport.clicked.connect(self.export_coeffs)
        self.butImport.clicked.connect(self.import_coeffs)
        self.butSave.clicked.connect(self.save_filter)
        self.butLoad.clicked.connect(self.load_filter)
#        self.butExportCSV.clicked.connect(self.exportCSV)
        #----------------------------------------------------------------------

    def HLine(self):
        # http://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
        # solution 
        """
        Create a horizontal line
        """
        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        return line

        
    def load_filter(self):
        """
        Load (c)pickled filter dictionary and update input and plot widgets
        """
        file_types = ("Pickled (*.pkl);;Zipped Binary Numpy Array (*.npz)")   
        dlg=QtGui.QFileDialog( self )
        file_name, file_type = dlg.getOpenFileNameAndFilter(self,
                caption = "Load filter ", directory = self.basedir,
                filter = file_types)
        if file_name != "": # cancelled file operation returns empty string
            file_type_err = False              
            try:
                with open(file_name, 'rb') as f:
                    if file_name.endswith('pkl'):
                        fb.fil = pickle.load(f)
                    elif file_name.endswith('npz'):
                        # http://stackoverflow.com/questions/22661764/storing-a-dict-with-np-savez-gives-unexpected-result
                        a = np.load(f) # array containing dict, dtype 'object'
                        
                        for key in a:
                            if np.ndim(a[key]) == 0:
                                # scalar objects may be extracted with the item() method
                                fb.fil[0][key] = a[key].item()
                            else:
                                # array objects are converted to list first
                                fb.fil[0][key] = a[key].tolist()
                    else:
                        print('Unknown file type "%s"' 
                                            %os.path.splitext(file_name)[1])
                        file_type_err = True
                    if not file_type_err:
                        print('Loaded filter "%s"' %file_name)                    
                        self.sigFilterDesigned.emit() # emit signal -> pyFDA -> pltAll.updateAll()
            except IOError:
                print("Failed loading %s!" %file_name)
            

    def save_filter(self):
        """
        Save Filter as pickle object
        """
        file_types = ("Pickled (*.pkl);;Zipped Binary Numpy Array (*.npz)")        
        dlg = QtGui.QFileDialog( self )
        file_name, file_type = dlg.getSaveFileNameAndFilter(self,
                caption = "Save filter as", directory = self.basedir,
                filter = file_types)                
        if file_name != "": # cancelled file operation returns empty string 
            file_type_err = False
            try:
                with open(file_name, 'wb') as f:
                    if file_name.endswith('pkl'):
                        pickle.dump(fb.fil, f)
                    elif file_name.endswith('npz'):
                        np.savez(f, **fb.fil[0])
                    else:
                        print('Unknown file type "%s"' 
                                            %os.path.splitext(file_name)[1])
                        file_type_err = True
                    if not file_type_err:
                        print('Filter saved as "%s"' %file_name)
                            
            except IOError as e:
                    print('Failed saving "%s"!\n' %file_name, e)


    def export_coeffs(self):
        """
        Export filter coefficients in various formats - see also
        Summerfield p. 192 ff
        """
        dlg=QtGui.QFileDialog( self )

        file_types = ("CSV (*.csv);;Matlab-Workspace (*.mat)"
            ";;Binary Numpy Array (*.npy);;Zipped Binary Numpy Array (*.npz)")

        # Add further file types if modules could be imported:
        if XLWT:
            file_types += ";;Excel Worksheet (.xls)"
        if XLSX:
            file_types += ";;Excel 2007 Worksheet (.xlsx)"

        file_name, file_type = dlg.getSaveFileNameAndFilter(self,
                caption = "Export filter coefficients as", 
                directory = self.basedir, filter = file_types) 
        if file_name != '': # cancelled file operation returns empty string   
            ba = fb.fil[0]['ba']
            file_type_err = False
            try:
                with open(file_name, 'wb') as f:
                    if file_name.endswith('mat'):   
                        scipy.io.savemat(f, mdict={'ba':fb.fil[0]['ba']})
                    elif file_name.endswith('csv'):
                        np.savetxt(f, ba, delimiter = ', ')
                        # newline='\n', header='', footer='', comments='# ', fmt='%.18e'
                    elif file_name.endswith('npy'):
                        # can only store one array in the file:
                        np.save(f, ba)
                    elif file_name.endswith('npz'):
                        # would be possible to store multiple array in the file
                        np.savez(f, ba = ba)
                    elif file_name.endswith('xls'):
                        # see
                        # http://www.dev-explorer.com/articles/excel-spreadsheets-and-python
                        # https://github.com/python-excel/xlwt/blob/master/xlwt/examples/num_formats.py
                        # http://reliablybroken.com/b/2011/07/styling-your-excel-data-with-xlwt/
                        workbook = xlwt.Workbook(encoding="utf-8")
                        worksheet = workbook.add_sheet("Python Sheet 1")
                        bold = xlwt.easyxf('font: bold 1')
                        worksheet.write(0, 0, 'b', bold)
                        worksheet.write(0, 1, 'a', bold)
                        for col in range(2):
                            for row in range(np.shape(ba)[1]):
                                worksheet.write(row+1, col, ba[col][row]) # vertical
                        workbook.save(f)
            
                    elif file_name.endswith('xlsx'):
                        # from https://pypi.python.org/pypi/XlsxWriter
                        # Create an new Excel file and add a worksheet.
                        workbook = xlsx.Workbook(f)
                        worksheet = workbook.add_worksheet()
                        # Widen the first column to make the text clearer.
                        worksheet.set_column('A:A', 20)
                        # Add a bold format to use to highlight cells.
                        bold = workbook.add_format({'bold': True})
                        # Write labels with formatting.
                        worksheet.write('A1', 'b', bold)
                        worksheet.write('B1', 'a', bold)
            
                        # Write some numbers, with row/column notation.
                        for col in range(2):
                            for row in range(np.shape(ba)[1]):
                                worksheet.write(row+1, col, ba[col][row]) # vertical
            #                    worksheet.write(row, col, coeffs[col][row]) # horizontal
            
            
                        # Insert an image - useful for documentation export ?!.
            #            worksheet.insert_image('B5', 'logo.png')
            
                        workbook.close()
            
                    else:
                        print('Unknown file type "%s"' 
                                            %os.path.splitext(file_name)[1])
                        file_type_err = True
                        
                    if not file_type_err:
                        print('Exported coefficients as %s - file to \n"%s"' 
                                %(self.del_file_ext(file_type), file_name))
                    
            except IOError as e:
                print('Failed saving "%s"!\n' %file_name, e)

    
            # Download the Simple ods py module:
            # http://simple-odspy.sourceforge.net/
            # http://codextechnicanum.blogspot.de/2014/02/write-ods-for-libreoffice-calc-from_1.html


    def import_coeffs(self):
        """
        Import filter coefficients from a file
        """
        file_types = ("Matlab-Workspace (*.mat);;Binary Numpy Array (*.npy);;"
        "Zipped Binary Numpy Array(*.npz)")
        dlg=QtGui.QFileDialog( self )
        file_name, file_type = dlg.getOpenFileNameAndFilter(self,
                caption = "Import filter coefficients ", 
                directory = self.basedir, filter = file_types)
        if file_name != '': # cancelled file operation returns empty string  
            file_type_err = False
            try:
                with open(file_name, 'r') as f:
                    if file_name.endswith('mat'):
                        data = scipy.io.loadmat(f)
                        fb.fil[0]['ba'] = data['ba']
                    elif file_name.endswith('npy'):
                        fb.fil[0]['ba'] = np.load(f)
                        # can only store one array in the file
                    elif file_name.endswith('npz'):
                        fb.fil[0]['ba'] = np.load(f)['ba']
                        # would be possible to store several arrays in one file
                    else:
                        print('Unknown file type "%s"' 
                                            %os.path.splitext(file_name)[1])
                        file_type_err = True
                        
                    if not file_type_err:
                        print('Loaded coefficient file\n"%s"' %file_name)
                        self.sigFilterDesigned.emit() # emit signal -> pyFDA                     

            except IOError as e:
                print("Failed loading %s!\n" %file_name, e)


    def exportHDL(self):
        """
        Synthesize HDL description of filter using myHDL module
        """
        dlg=QtGui.QFileDialog( self )
        
        file_types = "Verilog (*.v);;VHDL (*.vhd)"


        hdl_file, hdl_filter = dlg.getSaveFileNameAndFilter(self,
                caption = "Save HDL as", directory="D:",
                filter = file_types)
        print(hdl_file)
        
        coeffs = fb.fil[0]['ba']
        zpk =  fb.fil[0]['zpk']
        sos = fb.fil[0]['sos']
        
        typeHDL = self.cmbHDL.currentText() # could use hdl_filter as well

        qI_i = int(self.ledQIInput.text())
        qF_i = int(self.ledQIInput.text())
        
        qI_o = int(self.ledQIOutput.text())
        qF_o = int(self.ledQIOutput.text())
        
        qQuant_o = self.cmbQuant_o.currentText()
        qOvfl_o = self.cmbOvfl_o.currentText()
        
        q_obj_o =  {'QI':qI_o, 'QF': qF_o, 'quant': qQuant_o, 'ovfl': qOvfl_o}
        myQ_o = fix.Fixed(q_obj_o) # instantiate fixed-point object


    def del_file_ext(self, file_type):
        """
        Delete file extension, e.g. '(*.txt)' from file type description
        """
        # regular expression: re.sub(pattern, repl, string) 
        #  Return the string obtained by replacing the leftmost non-overlapping 
        #  occurrences of the pattern in string by repl
        #   '.' means any character
        #   '+' means one or more
        #   '[^a]' means except for 'a'
        # '([^)]+)' : match '(', gobble up all characters except ')' till ')'
        # '(' must be escaped as '\('

        return re.sub('\([^\)]+\)', '', file_type) 

 
"""

Alternative to (c)pickle: Use the shelve module that opens
a persistent dictionary for reading and writing.
This would get rid of the fb global dictionary?


import shelve

### write to database:
s = shelve.open('test_shelf.fb')
try:
    s['key1'] = { 'int': 10, 'float':9.5, 'string':'Sample data' }
finally:
    s.close()

### read from database:
s = shelve.open('test_shelf.fb')
# s = shelve.open('test_shelf.fb', flag='r') # read-only
try:
    existing = s['key1']
finally:
    s.close()

print(existing)

### catch changes to objects, store in in-memory cache and write-back upon close
s = shelve.open('test_shelf.fb', writeback=True)
try:
    print s['key1']
    s['key1']['new_value'] = 'this was not here before'
    print s['key1']
finally:
    s.close()

"""
#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    form = InputFiles()
    form.show()

    app.exec_()