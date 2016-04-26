# -*- coding: utf-8 -*-
"""
Widget for entering frequency specifications

Author: Christian Münker
"""
# TODO: using objectName is an ugly hack that causes problems in Python 2
from __future__ import print_function, division, unicode_literals, absolute_import
import sys
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal

import pyfda.filterbroker as fb
from pyfda.pyfda_lib import rt_label
from pyfda.simpleeval import simple_eval

class InputFreqSpecs(QtGui.QWidget):
    """
    Build and update widget for entering the frequency
    specifications like F_sb, F_pb etc.
    """

    # class variables (shared between instances if more than one exists)
    sigSpecsChanged = pyqtSignal() # emitted when filter has been changed

    def __init__(self, parent, title = "Frequency Specs"):

        super(InputFreqSpecs, self).__init__(parent)
        self.title = title

        self.qlabels = []    # list with references to QLabel widgets
        self.qlineedit = [] # list with references to QLineEdit widgets

        self._init_UI()


#-------------------------------------------------------------
    def _init_UI(self):
        """
        Initialize the User Interface
        """
        self.layVMain = QtGui.QVBoxLayout() # Widget main layout

        bfont = QtGui.QFont()
        bfont.setBold(True)
#            bfont.setWeight(75)
        self.lblTitle = QtGui.QLabel(self) # field for widget title
        self.lblTitle.setText(str(self.title))
        self.lblTitle.setFont(bfont)
        self.lblTitle.setWordWrap(True)
        self.layVMain.addWidget(self.lblTitle)
        
        # Create a gridLayout consisting of QLabel and QLineEdit fields
        # for the frequency specs:
        self.layGSpecs = QtGui.QGridLayout() # sublayout for spec fields        

        sfFrame = QtGui.QFrame()
        sfFrame.setFrameStyle(QtGui.QFrame.StyledPanel|QtGui.QFrame.Sunken)
        sfFrame.setLayout(self.layGSpecs)

        self.layVMain.addWidget(sfFrame)
        self.layVMain.setContentsMargins(1,1,1,1)
        self.setLayout(self.layVMain)

        #----------------------------------------------------------------------
        # SIGNALS & SLOTs
        #----------------------------------------------------------------------
        # DYNAMIC SIGNAL SLOT CONNECTION:
        # Every time a field is edited, call self.store_entries 
        # This signal-slot connection is constructed in self._add_entry / 
        # destructed in self._del_entry each time the widget is updated, 
        # i.e. when a new filter design method is selected.
        #----------------------------------------------------------------------


#-------------------------------------------------------------
    def update_UI(self, new_labels = []):
        """
        Set labels and get corresponding values from filter dictionary.
        When number of elements changes, the layout of subwidget is rebuilt.
        
        Connect new QLineEdit fields to store_entries so that the filter
        dictionary is updated automatically when a QLineEdit field has been
        edited.
        """
        # Check whether the number of entries has changed: 
        #  self.qlabels is a list with references to existing QLabel widgets,
        #  new_labels is a list of strings from the filter_dict for the current
        #    filter design

        delta_new_labels = len(new_labels) - len(self.qlabels)
        
        if delta_new_labels < 0: # less new labels, delete old ones
            self._del_entries(-delta_new_labels)

        elif delta_new_labels > 0: # more new labels, create new ones
            self._add_entries(delta_new_labels)

        logger.debug("update_UI: {0}-{1}-{2}".format(
                            fb.fil[0]["rt"],fb.fil[0]["dm"],fb.fil[0]["fo"]))

        fparams = ""
        for i in range(len(new_labels)):
#            else:
                # when entry has changed, update signal-slot connection, 
                #  label and corresponding value
                if str(self.qlineedit[i].objectName()) != new_labels[i]:
                    try:
                        self.qlineedit[i].editingFinished.disconnect()
                    except TypeError:
                        pass
                    self.qlabels[i].setText(rt_label(new_labels[i]))
    
                    self.qlineedit[i].setText(
                        str(fb.fil[0][new_labels[i]] * fb.fil[0]['f_S']))
                    self.qlineedit[i].setObjectName(new_labels[i])  # update ID                      
                    self.qlineedit[i].editingFinished.connect(
                                        lambda: self.store_entries(emit_sig = True))
                    
                    fparams += str(self.qlineedit[i].objectName()) + " = "\
                         + str(fb.fil[0][str(self.qlineedit[i].objectName())]) + "\n"


        logger.debug(fparams)

        self.store_entries()    # sort & store values to dict for the case 
                                # that the response type has been changed 
                                # eg. from LP -> HP, changing the order 
                                # of frequency entries

#-------------------------------------------------------------        
    def load_entries(self):
        """
        Reload textfields from filter dictionary 
        Transform the displayed frequency spec input fields according to the units
        setting (i.e. f_S). Spec entries are always stored normalized w.r.t. f_S 
        in the dictionary; when f_S or the unit are changed, only the displayed values
        of the frequency entries are updated, not the dictionary!

        load_entries is called during init and when the frequency unit or the
        sampling frequency have been changed.

        It should be called when sigSpecsChanged or sigFilterDesigned is emitted
        at another place, indicating that a reload is required.
        """

        # recalculate displayed freq spec values for (maybe) changed f_S
        logger.debug("exec load_entries")
        for i in range(len(self.qlineedit)):
            f = fb.fil[0][str(self.qlineedit[i].objectName())] * fb.fil[0]['f_S']
            self.qlineedit[i].setText(str(round(f,11)))

#-------------------------------------------------------------
    def _del_entries(self, num):
        """
        Delete num subwidgets (QLabel and QLineEdit) from layout and memory and
        disconnect the editingFinished signals from self.store_entries.
        """
        Nmax = len(self.qlabels)-1  # number of existing labels
        for i in range(Nmax, Nmax-num, -1):  # start with len, last element len - num
            
            self.qlineedit[i].editingFinished.disconnect()
    
            self.layGSpecs.removeWidget(self.qlabels[i])
            self.layGSpecs.removeWidget(self.qlineedit[i])
    
#            self.qlabels[i].deleteLater() # 
            self.qlabels[i].setParent(None) # alternative: change ownership back to python
            del self.qlabels[i]
#            self.qlineedit[i].deleteLater()
            self.qlineedit[i].setParent(None) # alternative: change ownership back to python
            del self.qlineedit[i]        
                
#------------------------------------------------------------------------
    def _add_entries(self, num):
        """
        Append num subwidgets (QLabel und QLineEdit) to memory and layout and 
        initialize them with dummy information.
        """
        Nmax = len(self.qlabels)-1 # number of existing labels

        # start with Nmax + 1, last element Nmax + num +1
        for i in range(Nmax+1, Nmax+num+1, 1): 
            self.qlabels.append(QtGui.QLabel(self))
            self.qlabels[i].setText(rt_label("dummy"))
    
            self.qlineedit.append(QtGui.QLineEdit(""))
            self.qlineedit[i].setObjectName("dummy")
    
            self.layGSpecs.addWidget(self.qlabels[i],(i+2),0)
            self.layGSpecs.addWidget(self.qlineedit[i],(i+2),1)   

#-------------------------------------------------------------
    def store_entries(self, emit_sig = False):
        """
        store_entries is called when:
        * a lineedit field has been edited
        * update_UI has been called after changing the filter design algorithm

        It performs the following actions:
        * Sort spec entries with ascending frequency if sort button is activated
        * Store _normalized_ specification entries in filter dictionary:
            - Entries are normalized with sampling frequency fb.fil[0]['f_S'] !
            - The unit scale factor (khz, ...) only influences the display of
              of f_S and the specs, it does not influence the normalized specs.
              
        sigSpecsChanged is _not_ fired normally as this signal is already 
        generated by input_filter. If needed, emit_sig can be set to True (e.g. 
        when a line_edit field has been changed).
        """
        logger.debug("exec store_entries")
        if fb.fil[0]['freq_specs_sort']:
            fSpecs = [simple_eval(self.qlineedit[i].text())
                                            for i in range(len(self.qlineedit))]
            fSpecs.sort()
            
            for i in range(len(self.qlineedit)):
                self.qlineedit[i].setText(str(fSpecs[i]))
           
        for i in range(len(self.qlineedit)):
            fb.fil[0].update(
                {str(self.qlineedit[i].objectName()):round(
                    simple_eval(self.qlineedit[i].text())/fb.fil[0]['f_S'],11)})

        if emit_sig:
            logger.debug("sigSpecsChanged emitted")
            self.sigSpecsChanged.emit()


#------------------------------------------------------------------------------

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    mainw = InputFreqSpecs(None)

    mainw.update_UI(new_labels = ['F_SB','F_SB2','F_PB','F_PB2'])
#    mainw.update_UI(new_labels = ['F_PB','F_PB2'])

    app.setActiveWindow(mainw) 
    mainw.show()
    sys.exit(app.exec_())
