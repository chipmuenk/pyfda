# -*- coding: utf-8 -*-
"""
MWE for
"""
from __future__ import print_function, division

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QTabWidget, QPushButton, QVBoxLayout, QApplication

#------------------------------------------------------------------------------
class TabWidgets(QTabWidget):
 
    sig_rx = pyqtSignal(object) # incoming signals
    sig_tx = pyqtSignal(object) # outgoing: emitted by process_signals  

    def __init__(self, parent):
        super(TabWidgets, self).__init__(parent)
        # instantiate all subwidgets and connect their tx signals to self.sig_rx:
        self.wdg1 = Button1(self)
        # self.sig_tx.connect(self.pltHf.sig_rx) # why doesn't this work?
        self.wdg1.sig_tx.connect(self.sig_rx)
        self.sig_tx.connect(self.wdg1.sig_rx)
        
        self.wdg2 = Button2(self)
        self.wdg2.sig_tx.connect(self.sig_rx)
        self.sig_tx.connect(self.wdg2.sig_rx)
        # now connect self.sig_rx to the slot self.process_signals:
        self.sig_rx.connect(self.process_signals)

        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(self.wdg1, 'Btn 1')
        self.tabWidget.addTab(self.wdg2, 'Btn 2')
        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tabWidget)
        self.setLayout(layVMain)

    #--------------------------------------------------------------------------
    def process_signals(self, dict_sig):
        """
        Process signals coming in via sig_rx
        """
        print("TAB.process_signals(): received dict {0}".format(dict_sig))
        if dict_sig['info'] == 'btn1':
            print("TAB: btn1")
        elif dict_sig['info'] == 'btn2':
            print("TAB: btn2")
        self.sig_tx.emit(dict_sig)

#------------------------------------------------------------------------------   
class Button1(QWidget):
    """
    Construct a widget for plotting impulse and general transient responses
    """
    sig_rx = pyqtSignal(object) # incoming signals
    sig_tx = pyqtSignal(object) # outgoing signals

    def __init__(self, parent):
        super(Button1, self).__init__(parent)
        self.button = QPushButton('Button 1', self)
        self.button.clicked.connect(self.handleButton)
        self.sig_rx.connect(self.process_signals)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)

    def handleButton(self):
        self.sig_tx.emit({'sender':type(self).__name__, 'info':'btn1'})
        
    @pyqtSlot(object)        
    def process_signals(self, dict_sig):
        print("BTN1: Signal received.")
        if dict_sig['sender'] == type(self).__name__:
            print("BTN1: generated here!")
            return
        if dict_sig['info'] == 'btn2':
            print("BTN1: btn2 pressed")
        
#------------------------------------------------------------------------------   
class Button2(QWidget):
    """
    Construct a widget for plotting impulse and general transient responses
    """
    sig_rx = pyqtSignal(object) # incoming signals
    sig_tx = pyqtSignal(object) # outgoing: emitted by process_signals  

    def __init__(self, parent):
        super(Button2, self).__init__(parent)
        self.button = QPushButton('Button 2', self)
        self.button.clicked.connect(self.handleButton)
        self.sig_rx.connect(self.process_signals)

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)

    def handleButton(self):
        self.sig_tx.emit({'sender':type(self).__name__, 'info':'btn2'})

    @pyqtSlot(object)        
    def process_signals(self, dict_sig):
        print("BTN2: Signal received.")
        if dict_sig['sender'] == type(self).__name__:
            print("BTN2: generated here!")
            return
        if dict_sig['info'] == 'btn1':
            print("BTN2: btn1 pressed")

       
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
