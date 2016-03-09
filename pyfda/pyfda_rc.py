# -*- coding: utf-8 -*-
"""
pyfda_rc.py

This file contains layout definitions for Qt and matplotlib widgets
A dark and a light theme can be selected via a constant but this more a demonstration
on how to set things than a finished layout yet.

Default parameters, paths etc. are also defined at the end of the file.

Importing pyfda_rc runs the module once, defining all module variables
which are global (similar to class variables).

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

from __future__ import division, unicode_literals, absolute_import

# Various parameters for calculation and plotting
params = {'N_FFT':  2048, # number of FFT points for plot commands (freqz etc.)
          'P_Marker': [12, 'r'], # size and color for poles' marker
          'Z_Marker': [12, 'b']} # size and color for zeros' marker

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


# Default savedir for filter coefficients, filter dicts etc.
save_dir = "D:/Daten"

# Config file for logger
log_config_file = "pyfda_log.conf"

# ======================== LAYOUT =============================================

THEME = 'light' # select dark or light theme

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
css_dark = """
    QWidget{color:white;background: #222222;}
    
    QLineEdit{background: #222222;
                border-style: outset;
                border-width: 2px;
                border-color: darkgrey;
    }
    QLineEdit:disabled{background-color:darkgrey;}
    
    QPushButton{background-color:grey;}
    
    QTableView{alternate-background-color:#222222;
        background-color:black; gridline-color: white;}
    QHeaderView::section{background-color:rgb(190,1,1);}
                
            """
          

# light theme 
css_light = """
    /* only match QWidget, not subclasses: */
    QWidget{color:black; background: white;}

    QLineEdit{background: white;
                border-color: darkgrey;}
    QLineEdit:disabled{background-color:lightgrey;}
    
    QPushButton{background-color:lightgrey; }
    
    QHeaderView::section{background-color:rgb(190,1,1); color:white;}
    """    
#    QGridLayout#plotSpecSelect{border: 3px solid red;} /* doesnt work */
#    QGridLayout{border: 3px solid blue;} /* doesnt work */


# common layout settings for QTabWidget
TabBarCss = """
 QTabWidget::pane { /* The tab _widget_ frame */
     border-top: 2px solid #C2C7CB;
 }
 
 /* Only the right QTabWidget (named plot_tabs) gets a dashed left border */
 QTabWidget#plot_tabs::pane{border-left: 2px dashed grey;}

 QTabWidget::tab-bar {
     left: 0.3em; /* move bar to the right: hack to prevent truncation of labels (QTBUG-6905) */
     }

/* Style the TAB using the tab sub-control. Note that it reads QTabBar _not_ QTabWidget */
 QTabBar {  font-weight: bold; font-size:11pt; }
 QTabBar::tab{
     color:black;
     font-size:10pt;
     font-weight:bold;
     background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 white, stop: 0.5 lightgray, stop: 1.0 #C2C7CB);
     border: 1px solid #C4C4C3;
     border-bottom-color: #C2C7CB; /* same as the pane color */
     border-top-left-radius: 4px;
     border-top-right-radius: 4px;
     min-width: 2em;
     padding: 0.2em;
 }

 QTabBar::tab:selected, QTabBar::tab:hover {background:lightblue;}
 
 QTabBar::tab:selected {
     border-color: #9B9B9B;
     border-bottom-color: #C2C7CB; /* same as pane color */
 }

 QTabBar::tab:!selected {
     margin-top: 0.2em; /* make non-selected tabs look smaller */
 }

 /* make use of negative margins to produce overlapping selected tabs */
 QTabBar::tab:selected {
     /* expand/overlap to both sides by 0.2em */
     margin-left: -0.2em;
     margin-right: -0.2em;
 }
 
 QTabBar::tab:first{
    /* the first tab */
}

 QTabBar::tab:first:!selected {
    /* the first unselected tab */
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

css_common = """
                *[state="changed"]{background-color:yellow; color:black}
                *[state="error"]{background-color:red; color:white}
                *[state="failed"]{background-color:orange; color:white}
                *[state="ok"]{background-color:green; color:white}
                QPushButton:pressed {background-color:black; color:white}
                
                QWidget{font-size:10pt; font-family: Tahoma;}
                QLineEdit{background-color:lightblue;
                                /* border-style: outset; */
                                border-width: 2px;}
            """\
            + TabBarCss


if THEME == 'dark':

    mpl_rc.update(mpl_dark)
    css_rc = css_common + css_dark
else:
    mpl_rc.update(mpl_light)
    css_rc = css_common + css_light
    




