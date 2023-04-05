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

from pyfda.libs.pyfda_lib import CRLF, cmp_version
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
params = {'N_FFT':  2048,   # number of FFT points for plot commands (freqz etc.)
          'FMT': '{:.3g}',  # format string for QLineEdit fields
          'CSV':  {  # format options and parameters for CSV-files and clipboard
                  'delimiter': 'auto',  # default delimiter
                  'lineterminator': CRLF,  # OS-dependent line break from pyfda_lib
                  'orientation': 'auto',  # 'auto', 'vert', 'horiz'# table orientation
                  'header': 'auto',  # 'auto', 'on', 'off'
                  'cmsis' : False,  # True, False
                  'clipboard': False  # source/target is QClipboard or file
                  },
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
            'mpl_hatch': {                          # hatched area for specs
                         'facecolor': 'none',
                         'hatch': '/',
                         'edgecolor': '#808080',    # same as figure.edgecolor
                         'lw': 0.0},                # no border around hatched area

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
            'mpl_hatch': {                          # hatched area for specs
                         'facecolor': 'none',
                         'hatch': '/',
                         'edgecolor': '#808080',    # same as figure.edgecolor
                         'lw': 0.0},                # no border around hatched area

            'mpl_stimuli': {                         # style for stimulus signals
                          'mfc': 'k', 'mec': 'k',  # marker face + edge color
                          'ms': mpl_ms,            # marker size
                          'alpha': 0.25,           # transparency (marker + stem)
                          'markerfmt': '*',         # marker symbol
                          'lw': '2'}              # stem linewidth
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
          'font.size'                 : 12,
          'legend.fontsize'           : 12,
          'axes.labelsize'            : 12,
          'axes.titlesize'            : 14,
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

mpl_rc_33 = {'mathtext.fallback'      : 'cm'}  # new since mpl 3.3
mpl_rc_32 = {'mathtext.fallback_to_cm': True}  # deprecated since mpl 3.3

if cmp_version('matplotlib', '3.3') < 0:
    mpl_rc.update(mpl_rc_32)  # lower than matplotlib 3.3
else:
    mpl_rc.update(mpl_rc_33)


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
    .QWidget{color:white; background-color: black } /* background of application */
    QFrame{color:white;}
    QTextEdit{color: white; background-color: #444444;}
    QCheckBox{
        border: none;  /* dummy, needed to force using non-system widget rendering */
        color: white;
        }
    QCheckBox::indicator{
     /* setting any properties here removes all default styles ... */
       }


    QScrollArea{background-color: #222222}
    QScrollArea > QWidget > QWidget{background-color: #222222}

    /* background of tab content */
    .QTabWidget::pane{color: white; background-color: #555555;}

    QLineEdit{background: #222222;
                border-style: outset;
                border-width: 2px;
                border-color: darkgrey;
                color: white;
    }
    QLineEdit:disabled{background-color:darkgrey;}

    QPushButton{
         background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 white, stop: 0.5 lightgray, stop: 1.0 #C2C7CB);
         color: black;
                    }

    QTableView{alternate-background-color:#222222;
        background-color:#444444; gridline-color: white;}
    QHeaderView{background-color:#222222;}
    QHeaderView::section{background-color:#111111;}
    QTableWidget QTableCornerButton::section{background-color:#444444;}
    QHeaderView::section:checked{background-color:rgb(190,1,1);}

    QComboBox QListView {color:black}
    QMessageBox{background-color:#444444}
            """
# ---------------
# light QSS theme
# ---------------
qss_light = """
    .QWidget, .QFrame{color:black; background-color: white;}

    QScrollArea{color:black; background-color:white;}
    QScrollArea > QWidget > QWidget{color:black; background-color: white;}

    QTextEdit{background-color: white;}

    QTableWidget{color:black; background-color:white;}

    .QTabWidget::pane{background-color: #F0F0F0;} /* background of tab content */

    QLineEdit{background: white;
                border-color: darkgrey;}
    QLineEdit:disabled{background-color:lightgrey; color:blue}

    QPushButton{
         background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 white, stop: 0.5 lightgray, stop: 1.0 #C2C7CB);
                    }
    QPushButton:disabled{color:darkgrey; }

    QHeaderView::section{background-color:darkgray; color:white;}
    QHeaderView::section:checked{background-color:rgb(190,1,1); color:white;}

    QMessageBox{background-color: #EEEEEE}
    """


# common layout settings for QTabWidget
qss_tab_bar = """
 /* The tab _widget_ frame; general and for North / West orientation */
QTabWidget {
    padding: 0;
    margin:  0;
 }
 QTabWidget::pane {
    padding: 0;
    margin:  0;
 }

 QTabWidget::pane::left {border-left: 1px solid #C2C7CB;} /* tabs left (west) */
 .QTabWidget::pane::top {border-top: 2px solid #C2C7CB;} /* tabs top (north) */

/* Style the TAB using the tab sub-control. Note that it reads QTabBar _not_ QTabWidget */

 QTabBar {  font-weight: bold; font-size:11pt; }

 QTabBar::tab{
    color:black;
    font-size:10pt;
    font-weight:bold;
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 white, stop: 0.5 lightgray, stop: 1.0 #C2C7CB);
    border: 1px solid #C4C4C3;
    border-top-left-radius: 4px;
 }

QTabBar::tab:selected, QTabBar::tab:hover {background:lightblue;}

QTabBar::tab:selected {
     border-color: #9B9B9B;
 }

QTabBar::tab:only-one {
     margin: 0; /* if there is only one tab, we don't want overlapping margins */
 }

QTabBar::tab::top{
    border-top-right-radius: 4px;
    min-width: 2em;
    margin-bottom: -0.2em;
    padding: 0.2em;
    padding-bottom: 0.4em;
    }
QTabBar::tab::left{
    border-bottom-left-radius: 4px;
    width: 26px;
    margin-right: -4px;
    padding: 2px;
    padding-right: 2px;
 }

/* separate styling for stimuli / audio widget with icons @ tabs */
 QTabWidget#tab_stim_w QTabBar::tab{
     width: 30 px;
     height: 30 px;
     padding: 0;
 }

 /* small gap above vertical mplwidget tabs */
 QTabWidget#tab_mpl_w QTabBar::tab::left:first{
    margin-top: 2px;
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
                * [state="unused"], *[state="u"]{background-color: white; color:darkgrey}
                /* semi-transparent red */
                * [state="failed"]{background-color: rgba(255, 0, 0, 50%); color:black}

                QWidget{font-size:10pt; font-family: Tahoma;}

                #large{font-size: 12pt; font-weight: bold; }
                #xlarge{font-size: 14pt; font-weight: black;}

                /* Frame with control elements of all plot widgets */
                #frmControls{
                    border-top: solid darkgrey;
                    border-width: 2px;
                    margin: 0;
                    padding: 0;
                    }

                /* Frame for input subwidgets */
                QTabWidget#input_tabs > QFrame QFrame,
                QTabWidget#input_tabs QTextBrowser
                {
                    /* background-color: pink; */
                    border: solid darkgrey;
                    border-width: 1px 0 1px 0;
                    padding: 0;
                    margin: 0 0 0 0; /* was: 1px 0 0 0 */
                    }

                /* Frame in frame, e.g. for target specs, only border-top */
                QTabWidget#input_tabs > QFrame QFrame .QFrame
                {
                    /* background-color:lime; */
                    border: solid darkgrey;
                    border-width: 1px 0 0 0;
                    padding: 0;
                    margin: 0;
                    }

                QWidget#transparent{background-color:none}

                /* Dynamic filter subwidget */
                #wdg_fil{
                    /*background-color:lightblue;*/
                    border: none;
                    padding: 5px 0 0 0;
                    }

                /* setFrameStyle(QFrame.StyledPanel|QFrame.Sunken) */

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

                QPushButton[state="normal"]{background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 white, stop: 0.5 lightgray, stop: 1.0 #C2C7CB);
                    color: black;}

                QPushButton[state="changed"]{background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #cccccc, stop: 0.1 yellow, stop: 1.0 #999999);
                    color: black;}

                QPushButton[state="error"]{background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #cccccc, stop: 0.1 red, stop: 1.0 #444444);
                    color: white;}

                QPushButton[state="ok"]{background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #cccccc, stop: 0.1 green, stop: 1.0 #444444);
                    color: white;}

                QPushButton:pressed {background-color:black; color:white}

                QPushButton:checked{
                    background-color:lightblue; color:black;font-weight:800;}
                QPushButtonRT:checked{
                    background-color:lightblue; color:black;font-weight:800;}

                QLineEdit{background-color:lightblue;
                                /* border-style: outset; */
                                border-width: 2px;}

                /* QSplitter styling adopted from
                http://stackoverflow.com/questions/6832499/qsplitter-show-a-divider-or-a-margin-between-the-two-widgets
                */

                QSplitter::handle:vertical {
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0,
                                        stop:0 rgba(255, 255, 255, 0),
                                        stop:0.407273 rgba(200, 200, 200, 255),
                                        stop:0.4825 rgba(101, 104, 113, 235),
                                        stop:0.6 rgba(255, 255, 255, 0));
                    height: 8px;
                    image: url(':/ellipses_v.svg');
                    }

                QSplitter::handle:horizontal {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                                        stop:0 rgba(255, 255, 255, 0),
                                        stop:0.407273 rgba(200, 200, 200, 255),
                                        stop:0.4825 rgba(101, 104, 113, 235),
                                        stop:0.6 rgba(255, 255, 255, 0));
                    width: 8px;
                    image: url(':/ellipses_h.svg');
                    }

                QProgressBar{text-align: center; font-weight: bold;
                             border: 1px solid darkgrey;}
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
