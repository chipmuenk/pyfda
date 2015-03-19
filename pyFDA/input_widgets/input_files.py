# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 10:57:30 2013

@author: Christian Muenker

Tab-Widget for exporting / importing and saving / loading data
"""
from __future__ import print_function, division, unicode_literals, absolute_import
import sys, os
from PyQt4 import QtGui
#from PyQt4.QtCore import SIGNAL
import scipy.io
import numpy as np
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

# import filterbroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__":
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import filterbroker as fb # importing filterbroker initializes all its globals


class InputFiles(QtGui.QWidget):
    """
    Create the window for entering exporting / importing and saving / loading data
    """
    def __init__(self, DEBUG = True):
        self.DEBUG = DEBUG
        super(InputFiles, self).__init__()

        self.initUI()

    def initUI(self):
        """
        Intitialize the main GUI, consisting of:
        - Buttons for Exporting and Saving
        -
        """
        # widget / subwindow for parameter selection
        self.butExport = QtGui.QPushButton("Export Coefficients", self)
#        self.butExportCSV = QtGui.QPushButton("Export -> CSV", self)

        # ============== UI Layout =====================================
        self.layVExport = QtGui.QVBoxLayout()
        self.layVExport.addWidget(self.butExport) # -> Matlab workspace
#        self.layVExport.addWidget(self.butExportCSV) # -> CSV format
        self.layVExport.addStretch(1)

        layHMain = QtGui.QHBoxLayout()
        layHMain.addLayout(self.layVExport)
        self.setLayout(layHMain)

        # ============== Signals & Slots ================================
        self.butExport.clicked.connect(self.export)
#        self.butExportCSV.clicked.connect(self.exportCSV)


    def export(self):
        """
        Export filter coefficients in various formats - see also
        Summerfield p. 192 ff
        """
        dlg=QtGui.QFileDialog( self )

        file_types = "CSV (*.csv);;Matlab-Workspace (*.mat);;Numpy Array (*.npz)"
        
        if XLWT:
            file_types += ";;Excel Worksheet (.xls)"
        if XLSX:
            file_types += ";;Excel 2007 Worksheet (.xlsx)"

        myFile, myFilter = dlg.getSaveFileNameAndFilter(self,
                caption = "Save filter coefficients as", directory="D:/Daten",
                filter = file_types)
#        print(myFile, myFilter)
        coeffs = fb.fil[0]['coeffs']
        if myFile.endswith('mat'):
            scipy.io.savemat(myFile,
                             mdict={'filt_coeffs': coeffs})
            print("Matlab workspace exported to %s!" %myFile)
        elif myFile.endswith('csv'):
            np.savetxt(myFile, coeffs, delimiter = ', ')
            print("CSV - File exported to %s!" %myFile)
            # newline='\n', header='', footer='', comments='# ', fmt='%.18e'
        elif myFile.endswith('npz'):
            np.savez(myFile, coeffs)
            print("NPZ - File exported to %s!" %myFile)
        elif myFile.endswith('xls'):
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
                for row in range(np.shape(coeffs)[1]):
                    worksheet.write(row+1, col, coeffs[col][row]) # vertical 
            workbook.save(myFile)
            print("Exported %s!" %myFile)

        elif myFile.endswith('xlsx'):
            # from https://pypi.python.org/pypi/XlsxWriter
            # Create an new Excel file and add a worksheet.
            workbook = xlsx.Workbook(myFile)
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
                for row in range(np.shape(coeffs)[1]):
                    worksheet.write(row+1, col, coeffs[col][row]) # vertical 
#                    worksheet.write(row, col, coeffs[col][row]) # horizontal

            
            # Insert an image - useful for documentation export ?!.
#            worksheet.insert_image('B5', 'logo.png')
            
            workbook.close()
            print("Exported %s!" %myFile)
            
        else:
            print("No File exported!")

        # Download the Simple ods py module:
        # http://simple-odspy.sourceforge.net/
        # http://codextechnicanum.blogspot.de/2014/02/write-ods-for-libreoffice-calc-from_1.html


"""
File save format: use cPickle?

Alternative: Use the shelve module


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