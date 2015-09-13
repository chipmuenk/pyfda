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
for css styling

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
css_dark = {'TopWidget':( 'QWidget{color:white;background: #222222;}'
                        'QPushButton{background-color:grey; color:white;}'),
            'TabBar':('QTabBar{color:black;} QTabBar::tab{background:darkgrey;}'
                        'QTabBar::tab:selected{background:lightblue;}'
                        'QTableView{alternate-background-color:#222222;'
                             'background-color:black; gridline-color: white;}' 
                        'QHeaderView::section{background-color:rgb(190,1,1);}'),
          'LineEdit':'QLineEdit{background: #222222; color:white;}'
          }
          
# light theme          
css_light = {'TopWidget':('QWidget{color:black; background: white}'
                        'QPushButton{background-color:lightgrey; color:black;}'),
            'TabBar':'',
            'LineEdit':''
}
#            'TabBar':('QTabWidget::pane {border-top: 2px solid #C2C7CB;}' 
#                      'QTabBar{color:black;}'
#                       'QTabBar::tab:selected {background:lightblue;}'),
#          'LineEdit':'QLineEdit{background: #EEFFFF; color:black;}'
#          }

# common layout settings
css_rc = {'TopWidget':'QWidget{font-size:12px; font-family: Tahoma;}',
          'TabBar':'QTabBar{font-size:13px; font-weight:bold;}',
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
    
N_FFT = 2048 # number of FFT points for plot commands (freqz etc.)


#          'QWidget':('QWidget{Background: #CCCCCC; color:black; font-size:14px;'
#                     'font-weight:bold; border-radius: 1px;}')
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