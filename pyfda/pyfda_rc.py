# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
This file contains layout definitions for Qt and matplotlib widgets
A dark and a light theme can be selected via a constant but this more a demonstration
on how to set things than a finished layout yet.

Default parameters, paths etc. are also defined at the end of the file.

Importing pyfda_rc runs the module once, defining all module variables
which are global (similar to class variables).
"""
from pyfda import qrc_resources  # contains all icons

from pyfda.libs.pyfda_lib import CRLF
import pyfda.filterbroker as fb
from cycler import cycler
import matplotlib.font_manager

import logging
logger = logging.getLogger(__name__)

# #############################################################################
# General layout settings
# #############################################################################
# Get all available system styles:
# from PyQt5.QtWidgets import QStyleFactory
# from PyQt4.QtGui import QStyleFactory
# print(QStyleFactory.keys())

THEME = 'light'     # select 'dark' or 'light' theme or 'none' or use one of the
                    # system styles like 'windows':
# QT5 only:         fusion
# MS Windows only:  windowsxp, windowsvista
# Mac only:         macintosh

mpl_ms = 8  # base size for matplotlib markers
# Various parameters for calculation and plotting
params = {
    'N_FFT':  2048,   # number of FFT points for plot commands (freqz etc.)
    'FMT': '{:.3g}',  # format string for QLineEdit fields
    'CSV': {  # format options and parameters for CSV-files and clipboard
            'delimiter': 'auto',  # default delimiter
            'lineterminator': CRLF,  # OS-dependent line break from pyfda_lib
            'orientation': 'auto',  # 'auto', 'vert', 'horiz'# table orientation
            'header': 'auto',  # 'auto', 'on', 'off'
            # 'cmsis' : False,  # True, False
            'destination': False  # source/target is 'clipboard' or 'file'
            },
    'screen': { # screen properties default values, updated in pyfdax.py
        'ref_dpi': 96, 'scaling': 1.0, # dpi for scaling = 1 and scaling factor
        'height': 720, 'width': 1024}, # height and width in pixels
    'FMT_ba': 4,      # number of digits for coefficient table
    'FMT_pz': 5,      # number of digits for Pole/Zero table
    'P_Marker': [mpl_ms, 'r'],  # size and color for poles' marker
    'Z_Marker': [mpl_ms, 'b'],  # size and color for zeros' marker
    'wdg_margins': (2, 1, 2, 0),  # (R, T, L, B) widget margins
    'wdg_margins_spc': (2, 2, 2, 2),  # widget margins with more vertical spacing
    'wdg_margins_0': (0, 0, 0, 0),  # set margins to zero
    'mpl_margins': (0, 0, 0, 0),  # margins around matplotlib widgets
    'mpl_hatch_border': {'linewidth': 1.0, 'color': 'blue', 'linestyle': '--'}
          }

mpl_params_dark = {
            'mpl_hatch': {                         # hatched area for specs
                         'facecolor': 'none',
                         'hatch': '/',
                         'edgecolor': '#808080',   # same as figure.edgecolor
                         'lw': 0.0},               # no border around hatched area

            'mpl_stimuli': {                       # style for stimulus signals
                          'mfc': 'w', 'mec': 'w',  # marker face + edge color
                          'ms': mpl_ms,            # marker size
                          'alpha': 0.25,           # transparency (marker + stem)
                          'markerfmt': '*',        # marker symbol
                          'lw': '2'}               # stem linewidth
                    }

# fill_params = {'facecolor':'none','hatch':'/', 'edgecolor':rcParams['figure.edgecolor'],
# 'lw':0.0}
mpl_params_light = {
            'mpl_hatch': {                         # hatched area for specs
                         'facecolor': 'none',
                         'hatch': '/',
                         'edgecolor': '#808080',   # same as figure.edgecolor
                         'lw': 0.0},               # no border around hatched area

            'mpl_stimuli': {                       # style for stimulus signals
                          'mfc': 'k', 'mec': 'k',  # marker face + edge color
                          'ms': mpl_ms,            # marker size
                          'alpha': 0.25,           # transparency (marker + stem)
                          'markerfmt': '*',        # marker symbol
                          'lw': '2'}               # stem linewidth
                    }

# Dictionary with translations between short method names and long names for
# response types - the long name can be changed as you like, but don't change
# the short name - it is used to construct the filter design method names
rt_names = {"LP": "Lowpass", "HP": "Highpass", "BP": "Bandpass",
            "BS": "Bandstop", "AP": "Allpass", "MB": "Multiband",
            "HIL": "Hilbert", "DIFF": "Differentiator"}

# Dictionary with translations between short method names and long names for
# response types
ft_names = {"IIR": "IIR", "FIR": "FIR"}

# Dictionary dm_names is created dynamically by FilterTreeBuilder and stored
# in filterbroker.py

# #############################################################################
# Matplotlib layout settings
# #############################################################################

# common matplotlib widget settings
mpl_rc = {'lines.linewidth'           : 1.5,
          'lines.markersize'          : mpl_ms,         # markersize, in points
          'font.family'               : 'sans-serif',  # 'serif',
          'font.style'                : 'normal',
          'mathtext.fontset'          : 'stixsans',  # 'stix',
          'mathtext.default'          : 'it',
          'mathtext.fallback'         : 'cm',
          'font.size'                 : 10, # TODO: set this depending on resolution
          'legend.fontsize'           : 'medium',
          'axes.labelsize'            : 'medium',
          'axes.titlesize'            : 'large',
          'axes.linewidth'            : 1,  # linewidth for coordinate system
          # grid settings are partially overwritten in mpl_widget.py
          'axes.formatter.use_mathtext': True,  # use mathtext for scientific notation.
          'grid.linestyle'            : ':',
          'grid.linewidth'            : 0.5,    # in points
          # 'grid.color'               : b0b0b0, # grid color, set in dark / light styles
          'grid.alpha'                : 0.5,    # transparency, between 0.0 and 1.0

          'xtick.direction'           : 'in',
          'ytick.direction'           : 'in',
          # 'xtick.top'               : False, 2.0 only
          'figure.figsize'            : (5, 4),
          'figure.dpi'                : 100,
          'hatch.color'               : '#808080',
          'hatch.linewidth'           : 0.5
          }

# dark theme for matplotlib widgets
mpl_rc_dark = {
            'axes.facecolor'    : 'black',
            'axes.labelcolor'   : 'white',
            'axes.edgecolor'    : 'white',
            'figure.facecolor'  : '#202020',
            'figure.edgecolor'  : '#808080',
            'savefig.facecolor' : 'black',
            'savefig.edgecolor' : 'black',
            'xtick.color'       : 'white',
            'ytick.color'       : 'white',
            'text.color'        : 'white',
            'grid.color'        : '#CCCCCC',
            'axes.prop_cycle'   : cycler('color', ['r', 'g', 'c', 'm', 'y', 'w'])
            }

# light theme for matplotlib widgets
mpl_rc_light = {
            'axes.facecolor'    : 'white',
            'axes.labelcolor'   : 'black',
            'axes.edgecolor'    : 'black',
            'figure.facecolor'  : 'white',
            'figure.edgecolor'  : '#808080',
            'savefig.facecolor' : 'white',
            'savefig.edgecolor' : 'white',
            'xtick.color'       : 'black',
            'ytick.color'       : 'black',
            'text.color'        : 'black',
            'grid.color'        : '#222222',
            'axes.prop_cycle'   : cycler('color', ['r', 'b', 'c', 'm', 'k'])
            }

# --------------------- Matplotlib Fonts --------------------------------------
afm_fonts = sorted({f.name for f in matplotlib.font_manager.fontManager.afmlist})
ttf_fonts = sorted({f.name for f in matplotlib.font_manager.fontManager.ttflist})

if 'DejaVu Sans' in ttf_fonts:
    logger.info("Using 'DejaVu Sans' font.")
    mpl_rc.update({
                   'mathtext.fontset': 'custom',
                   'mathtext.rm': 'DejaVu Sans',
                   'mathtext.it': 'DejaVu Sans:italic',
                   'mathtext.bf': 'DejaVu Sans:bold'
                  })
elif 'Bitstream Vera Sans' in ttf_fonts:
    logger.info("Using 'Bitstream Vera Sans' font.")
    mpl_rc.update({
                   'mathtext.fontset': 'custom',
                   'mathtext.rm': 'Bitstream Vera Sans',
                   'mathtext.it': 'Bitstream Vera Sans:italic',
                   'mathtext.bf': 'Bitstream Vera Sans:bold'
                  })
else:
    logger.info("Found neither 'DejaVu Sans' nor 'Bitstream Vera Sans' font, "
                "falling back to 'sans-serif' and 'stix-sans'.")
# else: use sans-serif and stix-sans

# set all text to Stix font
# matplotlib.rcParams['mathtext.fontset'] = 'stixsans'
# matplotlib.rcParams['font.family'] = 'STIXGeneral'


# #############################################################################
# QWidget style sheets (QSS)
# #############################################################################

#  Qxxx, Qyyy match Qxxx and Qyyy
# .Qxxx{} only matches Qxxx, not its children
#  Qxxx#mylabel {} only matches Qxxx with object name #mylabel
#  Qxxx Qyyy{} only matches Qyyy that is a child of Qxxx
#  Qxxx > Qyyy{} only matches Qyyy that is a direct child of Qxxxx
#  Qxxx:mystate{} only matches Qyyy in state 'mystate' (e.g. disabled)
#  Qxxx::YYY{} specify subcontrol like "tab"

# ---------------
# dark QSS theme
# ---------------
qss_dark = """
    QWidget{color:white;}  /* nearly all widgets are derived from this */
    /* background of QWidget and QFrame widgets, not of derived widgets: */
    .QWidget, .QFrame{background-color: black;}

     /* The tab _widget_ frame for all TabWidgets */
    QTabWidget {background: #303030;} /* Background tabs except input tabs */
    QScrollArea{color:white; background-color:#303030;} /* background of input tabs */
    QTabWidget::pane{background-color: #606060;} /* background of tab widget content */
    /* NavigationToolbar needs to have the same color as above */
    NavigationToolbar2QT{background-color:#606060;}
    /* QTabBar {background: pink;} */ /* background of Tabs */

    QTextEdit{background-color: #444444;}

    QTableView{alternate-background-color:#222222;
        background-color:#444444; gridline-color: white;}
    QHeaderView{background-color:#222222;}
    QHeaderView::section{background-color:#111111;}
    QHeaderView::section:checked{background-color:blue;}

    QCheckBox::indicator{border: 2px solid #606060;}
    QCheckBox::indicator:checked{background-color: lightblue;}

    QLineEdit{background: #444444;
                border-style: outset;
                border-width: 1px;
                border-color: #c0c0c0;
                color: white;
    }
    QLineEdit:disabled{background-color:#505050; color: #A0A0A0}


    /* Style for the combobox itself */
    QSpinBox, QComboBox{background-color: #222222; border: 1px solid #aaaaaa;}
    /* Color style for dropdown items */
    QComboBox QAbstractItemView {
        background-color: #222222;
        border: 1px solid #808080;
    }

    QMessageBox{background-color:#444444}

    QPlainTextEdit{background-color: black}

    QProgressBar{color: black;}

    QPushButton{background-color: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #C0C0C0, stop: 1.0 #303030);
                }
    QPushButton:disabled{color:#303030;}
    QPushButton {border: native; border-radius:-1px;}

    QPushButton[state="normal"]{background-color: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #C0C0C0, stop: 1.0 #303030);
                }

    QSplitter::handle:vertical {
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                            stop:0 #303030,
                            stop:0.5 #808080,
                            stop:1.0 #303030);
        }

    QSplitter::handle:horizontal {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                            stop:0 #303030,
                            stop:0.5 #808080,
                            stop:1.0 #303030);
        }
            """
# ---------------
# light QSS theme
# ---------------
qss_light = """
    QWidget{color:black;}  /* nearly all widgets are derived from this */
    /* background of QWidget and QFrame widgets, not of derived widgets: */
    .QWidget, .QFrame{background-color: white;}
    QTabWidget{background: #F0F0F0;} /* Background tabs except input tabs */
    QScrollArea{color:black; background-color:#F0F0F0;} /* background of input tabs */
    QTabWidget::pane{background-color: #F0F0F0;} /* background of tab widget content */
    /* NavigationToolbar needs to have the same color as above */
    /* NavigationToolbar2QT{background-color:#F0F0F0;} */

    QTextEdit{background-color: white;}

    QTableView{alternate-background-color:#C0C0C0;
        background-color:#F0F0F0; gridline-color: #A0A0A0;}
    QHeaderView::section{background-color:#808080; color:white;}
    QHeaderView::section:checked{background-color:blue; color:white;}

    QLineEdit{background: white; border-color: #303030;}
    QLineEdit:disabled{background-color:#c0c0c0; color:blue;}

    /* Style for the spinbox and combobox itself */
    /* QSpinBox, QComboBox{background-color: #e0e0e0; border: 1px solid gray;
            padding: 1px; selection-background-color: orange;}*/

    QPushButton{background-color: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 white, stop: 0.5 #C0C0C0, stop: 1.0 lightblue);
    }
    QPushButton:disabled{color:#303030;}

    QPushButton[state="normal"]{background-color: qlineargradient(
        x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 white, stop: 0.5 #C0C0C0, stop: 1.0 lightblue);
        }

    QMessageBox{background-color: #EEEEEE}

    QPlainTextEdit{background-color: white}

    QSplitter::handle:vertical {
        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                            stop:0 rgba(200, 200, 200, 0),
                            stop:0.5 rgba(160, 160, 160, 235),
                            stop:1.0 rgba(200, 200, 200, 0));
        }

    QSplitter::handle:horizontal {
    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                            stop:0 rgba(200, 200, 200, 0),
                            stop:0.5 rgba(160, 160, 160, 235),
                            stop:1.0 rgba(200, 200, 200, 0));
        }
        /*
        stop:0 rgba(255, 255, 255, 0),
        stop:0.4 rgba(200, 200, 200, 255),
        stop:0.5 rgba(101, 104, 113, 235),
        stop:0.6 rgba(255, 255, 255, 0));
        */
    """

# common layout settings for QTabWidget
qss_tab_bar = """
 /* The tab _widget_ frame; general and for North / West orientation */
QTabWidget {
    padding: 0;
    margin:  0;
    background: green;
 }
 QTabWidget::pane {
    padding: 0;
    margin:  0;
 }

 QTabWidget::pane::left {border-left: 1px solid #C2C7CB;} /* tabs left (west) */
 .QTabWidget::pane::top {border-top: 2px solid #C2C7CB;} /* tabs top (north) */

/* Style the TAB using the tab sub-control. Note that it reads QTabBar _not_ QTabWidget */

 QTabBar {font-weight: bold; font-size:11pt;}

 QTabBar::tab{
    color:black;
    font-size:10pt;
    font-weight:bold;
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 white, stop: 0.5 #C0C0C0, stop: 1.0 #C2C7CB);
    border: 1px solid #C4C4C3;
    border-top-left-radius: 0.2em;
 }

QTabBar::tab:selected, QTabBar::tab:hover {background:lightblue;}

QTabBar::tab:selected {
     border-color: #9B9B9B;
 }

QTabBar::tab:only-one {
     margin: 0; /* if there is only one tab, we don't want overlapping margins */
 }

QTabBar::tab::top{
    border-top-right-radius: 0.2em;
    min-width: 2em;
    margin-bottom: -0.2em;
    padding: 0.2em;
    padding-bottom: 0.4em;
    }

 QTabBar::tab::left{
    border-bottom-left-radius: 0.1em;
    /* width: 26px; */
    width: 1.5em;
    margin-right: -0.2em;
    padding: 0.1em;
    padding-right: 0.1em;
 }

/* separate styling for stimuli / audio widget with icons @ tabs  */
 QTabWidget#tab_stim_w QTabBar::tab{
     width: 1.5em;
     height: 1.5em;
     margin-right: -0.2em;
     /*padding: 0;
     margin: 0;*/
 }

 /* small gap above vertical mplwidget tabs */
 QTabWidget#tab_mpl_w QTabBar::tab::left:first{
    margin-top: 0.1em;
 }

QTabBar::tab::top:selected {
     border-bottom-color: #C2C7CB; /* same as pane color */
 }
QTabBar::tab::left:selected {
     border-right-color: #C2C7CB; /* same as pane color */
 }

/* make non-selected tabs look smaller */
QTabBar::tab::top:!selected {
     margin-top: 0.2em;}
QTabBar::tab::left:!selected {
     margin-left: 0.2em;}
"""
# Overlap effects for QTabWidget, currently not used
qss_tab_bar_ovlp = """

 /* make use of negative margins to produce overlapping selected tabs */
 QTabBar::tab::top:selected {
     /* expand/overlap to both sides by 0.2em */
     margin-left: -0.1em;
     margin-right: -0.1em;
 }

 QTabBar::tab::top:first:selected {
     margin-left: 0; /* the first selected tab has nothing to overlap with on the left */
 }

 QTabBar::tab::top:last:selected {
     margin-right: 0; /* the last selected tab has nothing to overlap with on the right */
 }

"""

# Common qss settings for all themes
qss_common = """
                * [state="changed"]{background-color: yellow}
                /* fully transparent background using white and alpha = 0 */
                * [state="normal"]{background-color: rgba(255, 255, 255, 0)}
                * [state="running"]{background-color: orange; color: white;}
                * [state="highlight"]{background-color: rgba(173, 216, 230, 25%)}
                * [state="unused"], *[state="u"]{background-color: white; color:#303030}
                /* semi-transparent red */
                * [state="failed"]{background-color: rgba(255, 0, 0, 50%); color:black;
                    font-weight:800;}

                QWidget{font-size:10pt; font-family: Tahoma;}

                #medium{font-size: 11pt; font-weight: bold; }
                #large{font-size: 12pt; font-weight: bold; }
                #xlarge{font-size: 14pt; font-weight: black;}

                /* Frame with control elements of all plot widgets */
                #frmControls{
                    border-top: solid #303030;
                    border-width: 0.1em;
                    margin: 0;
                    padding: 0;
                    }

                /* Frame for input subwidgets */
                QTabWidget#input_tabs > QFrame QFrame,
                QTabWidget#input_tabs QTextBrowser
                {
                    border: solid #303030;
                    border-width: 0.05em 0 0.05em 0;
                    padding: 0;
                    margin: 0 0 0 0; /* was: 1px 0 0 0 */
                    }

                /* Frame in frame, e.g. for target specs, only border-top */
                QTabWidget#input_tabs > QFrame QFrame .QFrame
                {
                    /* background-color:lime; */
                    border: solid #303030;
                    border-width: 0.05em 0 0 0;
                    padding: 0;
                    margin: 0;
                    }

                QWidget#transparent{background-color:none}

                /* Dynamic filter subwidget */
                #wdg_fil{
                    /*background-color:lightblue;*/
                    border: none;
                    padding: 0.2em 0 0 0;
                    }

                /* setFrameStyle(QFrame.StyledPanel|QFrame.Sunken) */

                /* Table Corner Button */
                QTableView QTableCornerButton::section{background-color:lightblue; border-color: green;}
                QTableView QTableCornerButton::section:pressed{background-color:red;}

                QSpinBox, QComboBox{padding-left: 0.2em; padding-right: 1em;}

                QComboBox QAbstractItemView {
                    border: none;
                }

                QComboBox::item {
                    /*padding-left: 0em;
                    padding-right: 1em;*/
                    height: 2em;
                }
                QComboBox::item:selected {
                    background-color: orange;
                }
                QComboBox::item:checked {
                    font-weight: bold;
                }

                QPushButton
                {
                /*
                width: 20px; # not needed
                height: 15px;# not needed
                border-radius: 1px; # destroys button shape
                border-style: outset; # destroys button shape
                padding-left: 5px; padding-right: 3px; # destroys button shape
                 */
                 }

                QPushButton[state="changed"]{color: white;
                    background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #cccccc, stop: 0.1 yellow, stop: 1.0 #999999);
                    color: black;}

                QPushButton[state="error"]{color: white;
                    background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #cccccc, stop: 0.1 red, stop: 1.0 #444444);
                    }

                QPushButton[state="ok"]{color: white;
                    background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #cccccc, stop: 0.1 green, stop: 1.0 #444444);
                    }

                /* Highlight button when pressed from checked / not checked state */
                QPushButton:pressed:checked, QPushButton:pressed:!checked
                    {background-color:orange; color:white}

                QPushButton:checked, QPushButton:checked, QPushButtonRT:checked > QLabel{
                    background-color:lightblue; color:black; font-weight: bold;}

                QLineEdit{background-color:lightblue;
                                /* border-style: outset; */
                                border-width: 0.1em;}

                /* QSplitter styling adopted from
                http://stackoverflow.com/questions/6832499/qsplitter-show-a-divider-or-a-margin-between-the-two-widgets
                */

                QSplitter::handle:vertical {
                    height: 8px;
                    image: url(':/ellipses_v.svg');
                    }
                QSplitter::handle:horizontal {
                    width: 8px;
                    image: url(':/ellipses_h.svg');
                    }

                QProgressBar{text-align: center; font-weight: bold;
                             border: 1px solid #303030;}
                QProgressBar::chunk{background-color: lightblue;}
/*
#GreenProgressBar {
    min-height: 12px;
    max-height: 12px;
    border: 2px solid #2196F3;
    border-radius: 6px;
}
#GreenProgressBar::chunk {
    border-radius: 6px;
    background-color: #009688;
    width: 10px;
    margin: 0.5px;
}
*/

            """
# QApplication.setStyle(QStyleFactory.create('Cleanlooks')) re-create default styles


THEME = fb.conf_settings['THEME']

if THEME == 'dark':
    mpl_rc.update(mpl_rc_dark)
    params.update(mpl_params_dark)
    qss_rc = qss_common + qss_tab_bar + qss_dark

elif THEME == 'light':
    mpl_rc.update(mpl_rc_light)
    params.update(mpl_params_light)
    qss_rc = qss_common + qss_tab_bar + qss_light

elif THEME == 'none':
    mpl_rc.update(mpl_rc_light)
    params.update(mpl_params_light)
    qss_rc = qss_common

else:  # use the THEME name as the QStyle name
    mpl_rc.update(mpl_rc_light)
    params.update(mpl_params_light)
    qss_rc = THEME
