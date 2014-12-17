# -*- coding: utf-8 -*-
"""
SelectFilter.py
---------------
Subwidget for selecting the filter, consisting of combo boxes for:
- Response Type (LP, HP, Hilbert, ...)
- Filter Type (IIR, FIR, CIC ...) 
- DesignMethod (Butterworth, ...)

@author: Julia Beike, Christian Münker
Datum: 4.12.2014
"""
import sys, os
from PyQt4 import QtGui

# import databroker from one level above if this file is run as __main__
# for test purposes
if __name__ == "__main__": 
    __cwd__ = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(__cwd__ + '/..')

import databroker as db

class SelectFilter(QtGui.QWidget):
    """
    Construct combo boxes for selecting the filter, consisting of:
      - Response Type (LP, HP, Hilbert, ...)
      - Filter Type (IIR, FIR, CIC ...) 
      - DesignMethod (Butterworth, ...)
    """
    
    def __init__(self):
        super(SelectFilter, self).__init__()        
        self.initUI()
        
        
    def initUI(self): 
        """
        Initialize UI with comboboxes for selecting filter
        """
#-----------------------------------------------------------------------------
#        Example for structure and content of "filterTree" dictionary:
#-----------------------------------------------------------------------------
#        gD['filterTree'] = {\
#        "LP":\
#            {"IIR": ["Butterworth","Chebychev 1", "Chebychev 2", "Elliptic"],
#             "FIR": ['Equiripple','Least-squares','Window']},
#        "HP":\
#            {"IIR": ["Butterworth","Chebychev 1", "Chebychev 2", "Elliptic"],
#             "FIR": ['Equiripple','Least-squares','Window']},
#        "HIL":\
#            {"FIR": ['Equiripple']}
#         }

        #----------------------------------------------------------------------
        # Create combo boxes 
        # - comboResponseType for selecting response type rt (LP, HP, ...)
		# - comboFilterType for selection of filter type (IIR, FIR, ...)
		# - comboDesignMethod for selection of design method (Chebychev, ...)
		# and populate them from the "filterTree" dict either directly or by
		# calling setResponseType() :
        self.comboResponseType=QtGui.QComboBox(self)
        self.comboFilterType=QtGui.QComboBox(self)
        self.comboDesignMethod=QtGui.QComboBox(self)
        
        for rt in db.gD["filterTree"]:
            self.comboResponseType.addItem(db.gD["rtNames"][rt], rt)
        self.comboResponseType.setCurrentIndex(2) # set initial index
        self.setResponseType()

        #------------------------------------------------------------
        # SIGNALS & SLOTS      
        #
        # Connect comboBoxes and setters
        
        self.comboResponseType.activated.connect(self.setResponseType) # 'LP'
        self.comboFilterType.activated.connect(self.setFilterType) #'IIR'
        self.comboDesignMethod.activated.connect(self.setDesignMethod) #'cheby1'

        """
        LAYOUT      
        """
        layout=QtGui.QGridLayout()
        layout.addWidget(self.comboResponseType,0,0)
        layout.addWidget(self.comboFilterType,0,1)
        layout.addWidget(self.comboDesignMethod,0,2)

        self.setLayout(layout)

    def setResponseType(self):
        """
        Triggered when comboResponseType (LP, HP, ...) is changed:
        Copy selection to self.rt and db.gD and reconstruct filter type combo
        """ 
        self.rtIdx =self.comboResponseType.currentIndex()       
        self.rt = str(self.comboResponseType.itemData(self.rtIdx))
         
#        self.rt = str(self.comboResponseType.currentText())
        db.gD["curFilter"]["rt"] = self.rt # abbreviation
#        rt=db.gD["rtNames"][self.rt] # full text
#        print(db.gD["filterTree"][self.rt].keys())
        # 
        self.comboFilterType.clear() 
        self.comboFilterType.addItems(
            db.gD["filterTree"][self.rt].keys())
        self.setFilterType()
        
    def setFilterType(self):
        """"
        Triggered when comboFilterType (IIR, FIR, ...) is changed: 
        Copy selected setting to self.ft and (re)construct design method combo, 
        adding displayed text (e.g. "Chebychev 1") and hidden data (e.g. "cheby1")
        """
        self.ft = str(self.comboFilterType.currentText())
        self.comboDesignMethod.clear()  

        for dm in db.gD["filterTree"][self.rt][self.ft]:
            self.comboDesignMethod.addItem(db.gD["dmNames"][dm], dm)

        db.gD['curFilter']["ft"] = self.ft
        self.setDesignMethod()
            
    def setDesignMethod(self):
        """
        Triggered when comboDesignMethod (cheby1, ...) is changed: 
        Copy selected setting to self.dm # TODO: really needed? 
        """
        self.dmIdx = self.comboDesignMethod.currentIndex()
        self.dm = str(self.comboDesignMethod.itemData(self.dmIdx))
        db.gD["curFilter"]["dm"] = self.dm  
        # reverse dictionary lookup
        #key = [key for key,value in dict.items() if value=='value' ][0]        

#------------------------------------------------------------------------------ 
    
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    form = SelectFilter()
    form.show()
   
    app.exec_()

