# -*- coding: utf-8 -*-
from __future__ import print_function
from PyQt5.QtWidgets import (QWidget, QTabWidget, QPlainTextEdit, QTextEdit, QSplitter, QLabel,
                             QMainWindow, QVBoxLayout, QApplication, QSizePolicy)
from PyQt5.QtGui import QFontMetrics
from PyQt5 import QtCore

#------------------------------------------------------------------------------
class TabWidgets(QTabWidget):
    def __init__(self, parent):
        super(TabWidgets, self).__init__(parent)
        self.wdg1 = QWidget(self)
        self.lay_wdg1 = QVBoxLayout(self.wdg1)
        self.wdg2 = QWidget(self)
        self.lay_wdg2 = QVBoxLayout(self.wdg2)
        #self.wdg1.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        #self.wdg2.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.wdg1.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.wdg2.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        
        self._construct_UI()
#------------------------------------------------------------------------------
    def _construct_UI(self):
        """ Initialize UI with tabbed subplots """
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.tabWidget.addTab(self.wdg1, 'Wdg 1')
        self.tabWidget.addTab(self.wdg2, 'Wdg 2')

        layVMain = QVBoxLayout()
        layVMain.addWidget(self.tabWidget)
        self.setLayout(layVMain)
        # When user has switched the tab, call self.current_tab_redraw
        print('size wdg1: {0}'.format(self.wdg1.size()))
        print('size wdg2: {0}'.format(self.wdg2.size()))
        self.tabWidget.currentChanged.connect(self.current_tab_redraw)
#------------------------------------------------------------------------------
        
    def current_tab_redraw(self):
        pass
        #self.tabWidget.currentWidget().resize()

class MWin(QMainWindow):
    """
    Main window consisting of a tabbed widget and a status window.
    QMainWindow is used as it understands GUI elements like central widget
    """
    def __init__(self, parent=None):
        super(QMainWindow,self).__init__()
 #---------------------------------------------------------------       
        statusWin = QLabel(self)
        #statusWin = QPlainTextEdit(self)  # status window
        #statusWin.appendHtml("<b>hallo<br>hallo2<br>hallo3</b>")
        tabWin    = TabWidgets(self) # tabbed window
        print('hint status win: {0}'.format(statusWin.sizeHint()))
        print('hint_tab win: {0}'.format(tabWin.sizeHint()))
        print('hint main win: {0}'.format(self.sizeHint()))
        mSize = QFontMetrics(statusWin.font())
        rowHt = mSize.lineSpacing()
        # fixed height for statusWin needed as the sizeHint of tabWin is very small
        #statusWin.setFixedHeight(4*rowHt+4)
        # add status window underneath plot Tab Widgets:
        spltVMain = QSplitter(QtCore.Qt.Vertical)
        spltVMain.addWidget(tabWin)
        spltVMain.addWidget(statusWin)
        # relative initial sizes of subwidgets, this doesn't work here
#        spltVMain.setStretchFactor(4,1)
        spltVMain.setSizes([statusWin.sizeHint().height()*2, statusWin.sizeHint().height()*0.05])

        spltVMain.setFocus()
        # make spltVMain occupy the main area of QMainWindow and set inheritance
        self.setCentralWidget(spltVMain)   
        print('size tabs: {0}'.format(tabWin.size()))
        print('size status: {0}'.format(statusWin.size()))
        print('size self: {0}'.format(self.size()))
#----------------------------------------------------------------------------
def main():
    import sys
    app = QApplication(sys.argv)

    mainw = MWin(None)
    mainw.resize(300,400)
    app.setActiveWindow(mainw) 
    mainw.show()
    
    sys.exit(app.exec_())
    
if __name__ == "__main__":
    main()
