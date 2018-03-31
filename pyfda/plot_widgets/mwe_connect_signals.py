# -*- coding: utf-8 -*-
"""
Tabbed container with all plot widgets
"""
from __future__ import print_function, division

from PyQt5.QtCore import Qt, QEvent, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QTabWidget, QPushButton, QVBoxLayout, QApplication
#from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QEvent, QtCore, pyqtSlot, pyqtSignal

#------------------------------------------------------------------------------
class TabWidgets(QTabWidget):
 
    sig_rx = pyqtSignal(dict) # incoming signals
    sig_tx = pyqtSignal(dict) # outgoing: emitted by process_signals  

    def __init__(self, parent):
        super(TabWidgets, self).__init__(parent)

        self.btn1 = Button1(self)
        # self.sig_tx.connect(self.pltHf.sig_rx) # why doesn't this work?
        self.sig_rx.connect(self.btn1.sig_rx)
        self.btn2 = Button2(self)
        # self.sig_tx.connect(self.pltHf.sig_rx) # why doesn't this work?
        self.sig_rx.connect(self.btn2.sig_rx)

        self._construct_UI()

#------------------------------------------------------------------------------
    def _construct_UI(self):
        """ Initialize UI with tabbed subplots """
        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.btn1, 'Btn 1')
        self.tabWidget.addTab(self.btn2, 'Btn 2')
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tabWidget)

        self.setLayout(layVMain)
        
        #----------------------------------------------------------------------
        # GLOBAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.sig_rx.connect(self.process_signals)
        #----------------------------------------------------------------------

    @pyqtSlot(object)
    def process_signals(self, sig_dict):
        """
        Process signals coming in via sig_rx
        """
        if type(sig_dict) != 'dict':
            sig_dict = {'sender':__name__}

        self.sig_tx.emit(sig_dict)

#------------------------------------------------------------------------------
        
    def current_tab_redraw(self):
        #self.tabWidget.currentWidget().redraw()
        self.sig_tx.emit({'sender':__name__, 'tab_changed':True})
            
#------------------------------------------------------------------------------   
class Button1(QWidget):
    """
    Construct a widget for plotting impulse and general transient responses
    """
    sig_rx = pyqtSignal(dict) # incoming signals
    sig_tx = pyqtSignal(dict) # outgoing: emitted by process_signals  

    def __init__(self, parent):
        super(Button1, self).__init__(parent)
        self.button = QPushButton('Test', self)
        self.button.clicked.connect(self.handleButton)
        layout = QVBoxLayout(self)
        layout.addWidget(self.button)

    def handleButton(self):
        print ('Button 1 pressed')
        
#------------------------------------------------------------------------------   
class Button2(QWidget):
    """
    Construct a widget for plotting impulse and general transient responses
    """
    sig_rx = pyqtSignal(dict) # incoming signals
    sig_tx = pyqtSignal(dict) # outgoing: emitted by process_signals  

    def __init__(self, parent):
        super(Button2, self).__init__(parent)
        self.button = QPushButton('Test 2', self)
        self.button.clicked.connect(self.handleButton)
        layout = QVBoxLayout(self)
        layout.addWidget(self.button)

    def handleButton(self):
        print ('Button 2 pressed')

       
#------------------------------------------------------------------------

def main():
    import sys
    
    app = QApplication(sys.argv)

    mainw = TabWidgets(None)
    mainw.resize(300,400)
    
    app.setActiveWindow(mainw) 
    mainw.show()
    
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
