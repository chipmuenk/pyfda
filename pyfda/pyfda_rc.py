# -*- coding: utf-8 -*-
"""
pyfdarc.py

This file contains layout definitions for Qt and matplotlib widgets
A dark and a light theme can be selected via a constant but this more a demonstration
on how to set things than a finished layout yet.

See
http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
http://pymotw.com/2/articles/data_persistence.html
for information on passing/storing data between files

See
http://doc.qt.io/qt-4.8/stylesheet-examples.html
http://www.informit.com/articles/article.aspx?p=1405556
for qss styling

Author: Christian Muenker
"""

from __future__ import division, unicode_literals
# importing pyfdarc runs the module once, defining all module variables
# which are global (similar to class variables)

THEME = 'light'

# -----------------------------
# Layout for matplotlib widgets
# -----------------------------

# dark theme
mpl_dark = {'axes.facecolor':'black',
            'axes.labelcolor':'white',
            'axes.edgecolor':'white',
            'axes.color_cycle': ['r', 'g', 'c', 'm', 'y', 'w'],
            'figure.facecolor':'#202020',
            'figure.edgecolor':'#808080', # also color for hatched specs in |H(f)|
            'savefig.facecolor':'black',
            'savefig.edgecolor':'black', 
            'xtick.color':'white',
            'ytick.color':'white',
            'text.color':'white',
            'grid.color':'#CCCCCC'
            }
            
# light theme
mpl_light = {'axes.facecolor':'white',
             'axes.labelcolor':'black',
            'axes.edgecolor':'black',
            'axes.color_cycle': ['r', 'b', 'c', 'm', 'k'],
            'figure.facecolor':'white',
            'figure.edgecolor':'#808080', # also color for hatched specs in |H(f)|
            'savefig.facecolor':'white',
            'savefig.edgecolor':'white', 
            'xtick.color':'black',
            'ytick.color':'black',
            'text.color':'black',
            'grid.color':'#222222'
            }
            
# common layout settings
mpl_rc = {'lines.linewidth': 1.5,
            'font.size':12, 'legend.fontsize':12, 
            'axes.labelsize':12, 'axes.titlesize':14, 'axes.linewidth':1,
            'axes.formatter.use_mathtext': True,
            'figure.figsize':(5,4), 'figure.dpi' : 100}
            
# ---------------------
# Layout for Qt widgets
# ---------------------

# dark theme            
css_dark = {'TopWidget':('QWidget{color:white;background: #222222;}'
                        'QPushButton{background-color:grey; color:white;}'
                        'QTableView{alternate-background-color:#222222;'
                             'background-color:black; gridline-color: white;}' 
                        'QHeaderView::section{background-color:rgb(190,1,1);color:white}'
                        'QLineEdit{background: #222222; color:white;}'
                        'QLineEdit:disabled{background-color:darkgrey;}'),
          'LineEdit':'QLineEdit{background: #222222; color:white;}'
          }
          
#                                  'QTabBar{color:black;} QTabBar::tab{background:darkgrey;}'
#                        'QTabBar::tab:selected{background:lightblue;}'
          
# light theme          
css_light = {'TopWidget':('.QTabWidget>QWidget>QWidget{border: 1px solid grey}'
                        'QTabWidget>QWidget{border-right: 1px solid grey;}'
                        '.QWidget{color:black; background: white}'
                        'QPushButton{background-color:lightgrey; color:black;}'
                        'QHeaderView::section{background-color:rgb(190,1,1);color:white}'
                        'QLineEdit{background: white; color:black;}'
                        'QLineEdit:disabled{background-color:lightgrey;}'
),
            'LineEdit':''
}
#            'TabBar':('QTabWidget::pane {border-top: 2px solid #C2C7CB;}' 
#                      'QTabBar{color:black;}'
#                       'QTabBar::tab:selected {background:lightblue;}'),
#          'LineEdit':'QLineEdit{background: #EEFFFF; color:black;}'
#          }

# common layout settings
TabBarCss = """
 QTabWidget::pane { /* The tab widget frame */
     border-top: 2px solid #C2C7CB;
 }
 QTabWidget::tab-bar {
     left: 1px; /* move to the right by 1px */
 }
 /* Style the tab using the tab sub-control. Note that
     it reads QTabBar _not_ QTabWidget */
 QTabBar::tab{color:black;}
 QTabBar::tab {
     background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 white, stop: 0.5 lightgray, stop: 1.0 #C2C7CB);
     border: 1px solid #C4C4C3;
     border-bottom-color: #C2C7CB; /* same as the pane color */
     border-top-left-radius: 4px;
     border-top-right-radius: 4px;
     min-width: 8ex;
     padding: 2px;
 }
 QTabBar::tab:selected, QTabBar::tab:hover {background:lightblue;}

 QTabBar::tab:selected {
     border-color: #9B9B9B;
     border-bottom-color: #C2C7CB; /* same as pane color */
 }
 QTabBar::tab:!selected {
     margin-top: 2px; /* make non-selected tabs look smaller */
 }
 /* make use of negative margins for overlapping tabs */
 QTabBar::tab:selected {
     /* expand/overlap to the left and right by 4px */
     margin-left: -4px;
     margin-right: -4px;
 }
 QTabBar::tab:first:selected {
     margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
 }
 QTabBar::tab:last:selected {
     margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
 }
 QTabBar::tab:only-one {
     margin: 0; /* if there is only one tab, we don't want overlapping margins */
 }
"""
css_rc = {'TopWidget':('*[state="changed"]{background-color:yellow; color:black}'
                      '*[state="error"]{background-color:red; color:white}'
                      '*[state="fail"]{background-color:orange; color:white}'
                      '*[state="ok"]{background-color:green; color:white}'
                      'QPushButton:pressed {background-color:black; color:white}'
                      'QWidget{font-size:12px; font-family: Tahoma;}'
                      'QLineEdit{background-color:lightblue;}'
                      'QTabBar{font-size:13px; font-weight:bold;}') + TabBarCss,
          'LineEdit':''
          }


if THEME == 'dark':

    mpl_rc.update(mpl_dark)
    for key in css_rc:
        css_rc[key]+= css_dark[key]
else:
    mpl_rc.update(mpl_light)
    for key in css_rc:
        css_rc[key]+= css_light[key]
    
params = {'N_FFT':  2048} # number of FFT points for plot commands (freqz etc.)

# Dictionary with translations between short method names and long names for
# response types
rt_names = {"LP":"Lowpass", "HP":"Highpass", "BP":"Bandpass",
            "BS":"Bandstop", "AP":"Allpass", "MB":"Multiband",
            "HIL":"Hilbert", "DIFF":"Differentiator"}
            
# Dictionary with translations between short method names and long names for
# response types
ft_names = {"IIR":"IIR", "FIR":"FIR"}

# Dictionary dm_names is created dynamically by FilterTreeBuilder and stored
# in filterbroker.py
            
################## Some layout ideas ##########################################

#self.em = QtGui.QFontMetricsF(QtGui.QLineEdit.font()).width('m')

#          'QWidget':('QWidget{Background: #CCCCCC; color:black; font-size:14px;'
#                     'font-weight:bold; border-radius: 1px;}')

""" QTabBar::tab:selected, QTabBar::tab:hover {
     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #fafafa, stop: 0.4 #f4f4f4,
                                 stop: 0.5 #e7e7e7, stop: 1.0 #fafafa);
 QTabBar::tab {
     background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
 }
"""
css = """
/*height: 14px;*/
/*
QDialog{
Background-image:url('img/xxx.png');
font-size:14px;
color: black;
}
*/


QToolButton:hover{
Background: #DDEEFF;
}
"""
