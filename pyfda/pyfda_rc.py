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

mpl_ms = 8  # base size for matplotlib markers
# Various parameters for calculation, plotting and UI
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
    'mpl_hatch_border': {'linewidth': 1.0, 'color': 'blue', 'linestyle': '--'},
    'link_color': 'blue'  # link color in HTML text
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
            'figure.facecolor'  : '#303030',
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
            'figure.facecolor'  : 'D0D0D0',
            'figure.edgecolor'  : '#808080',
            'savefig.facecolor' : 'white',
            'savefig.edgecolor' : 'white',
            'xtick.color'       : 'black',
            'ytick.color'       : 'black',
            'text.color'        : 'black',
            'grid.color'        : '#202020',
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
    /* Background color #303030 should be same as matplotlib figure.facecolor */
    QSplitter{background-color: #303030;} /* Top Level background */
    QWidget{color:white;}  /* nearly all widgets are derived from this */
    /* background of QWidget and QFrame widgets, not of derived widgets: */
    .QWidget, .QFrame{background-color: #303030;}

    /* The tab _widget_ frame for all TabWidgets */
    QTabWidget {background-color: #303030;} /* Background for tabs except input tabs */
    /* background for input tabs, here QTabWidget is encompassed by QScrollArea */
    QScrollArea{color:white; background-color:#303030;}
    QTabWidget::pane{background-color: #707070;} /* background of tab widget content */
    /* NavigationToolbar needs to have the same color as above */
    NavigationToolbar2QT{background-color:#707070;}
    /* QTabBar {background-color: pink;} */ /* background of Tabs, normally defined by pane */

    QTextEdit{background-color: #505050;}
    QLineEdit{background-color: #505050; border-color: #A0A0A0;}
    /* QLineEdit{selection-background-color: darkgray;} */
    QLineEdit:disabled{background-color: #707070; color: #B0B0B0}

    /* Applies to all widgets in "normal" resp. "active" state
    * [state="normal"], * [state="active"], * [state="a"]
        {background-color: #505050; color: white;}
    /* 'unused', e.g. for lineedit fields with some filter designs */
    * [state="unused"], *[state="u"]{background-color: #606060; color:lightblue}

    /* Style 'normal' background for all push buttons */
    QPushButton{background-color: #505050;}
    .QPushButton:disabled, PushButton:disabled{
        background-color: #707070; color: #A0A0A0;}

    /* Background color for the spinbox and combobox itself  */
    QSpinBox, QComboBox{background-color: #505050;}
    /* Background color for dropdown items */
    QComboBox QAbstractItemView {background-color: #404040;}
    /* Border for the spinbox and combobox itself */
    /* QSpinBox, QComboBox{border: 1px solid #C0C0C0;} */
    /* Border around dropdown menu */
    /* QComboBox QAbstractItemView {border: 1px solid orange;} */

    QComboBox:disabled{background-color: #505050; color: #A0A0A0}

    QDialog{background-color: #404040;}
    QMessageBox{background-color:#404040;}

    QPlainTextEdit{background-color: #303030;}

    QTableView{alternate-background-color:#202020;
        background-color:#505050; gridline-color: white;}
    QHeaderView{background-color:#202020;}
    QHeaderView::section{background-color:#101010;}
    QHeaderView::section:checked{background-color:blue;}

    QProgressBar::chunk{background-color: #505050;}
    /* QProgressBar:disabled::chunk{...} */

    QScrollBar {background: #707070; border-radius: 3px;}
    QScrollBar::handle {background: #303030; border-radius: 3px; border: 1px solid #A0A0A0}

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
    /* Background color #D0D0D0 should be same as matplotlib figure.facecolor */
    QSplitter{background-color: #F0F0F0;} /* Top Level background */
    QWidget{color:black;}  /* nearly all widgets are derived from this */
    /* background of QWidget and QFrame widgets, not of derived widgets: */
    .QWidget, .QFrame{background-color: #F0F0F0;}

    /* The tab _widget_ frame for all TabWidgets */
    QTabWidget{background-color: #F0F0F0;} /* Background for tabs except input tabs */
    /* background for input tabs, here QTabWidget is encompassed by QScrollArea */
    QScrollArea{color:black; background-color:#F0F0F0;} /* background of input tabs */
    QTabWidget::pane{background-color: #E0E0E0;} /* background of tab widget content */
    /* NavigationToolbar needs to have the same color as above */
    NavigationToolbar2QT{background-color:#E0E0E0;}
    /* QTabBar {background-color: pink;} */ /* background of Tabs, normally defined by pane */

    QTextEdit{background-color: #F0F0F0;}
    QLineEdit{background-color: white; border-color: #303030;}
    QLineEdit:disabled{background-color:#C0C0C0; color: white;}

    /* Applies to all widgets in "normal" resp. "active" state
    * [state="normal"], * [state="active"], * [state="a"]
            {background-color: #C0C0C0;}
    /* 'unused', e.g. for lineedit fields with some filter designs */
    * [state="unused"], *[state="u"]{background-color: #E0E0E0; color:blue}

    /* Style 'normal' background for all push buttons */
    QPushButton{background-color: #C0C0C0;}
    .QPushButton:disabled, PushButton:disabled{
            background-color: #C0C0C0; color: white}

    /* Background color for the spinbox and combobox itself */
    QSpinBox, QComboBox{background-color: #D0D0D0;}
    /* Background color for dropdown items */
    QComboBox QAbstractItemView {background-color: #F0F0F0;}
    /* Border for the spinbox and combobox itself */
    /* QSpinBox, QComboBox{border: 1px solid #404040;} */
    /* Border around dropdown menu */
    /* QComboBox QAbstractItemView {border: 1px solid orange;} */

    QComboBox:disabled{background-color: #C0C0C0; color: white}

    QDialog{background-color: #E0E0E0;}
    QMessageBox{background-color: #E0E0E0;}

    QPlainTextEdit{background-color: white}

    QTableView{alternate-background-color:#C0C0C0;
        background-color:#F0F0F0; gridline-color: #A0A0A0;}
    QHeaderView{background-color:#F0F0F0;}
    QHeaderView::section{background-color:#808080; color:white;}
    QHeaderView::section:checked{background-color:blue; color:white;}

    QProgressBar::chunk{background-color: #F0F0F0;}
    /* QProgressBar:disabled::chunk{...} */

    QScrollBar {background: darkgrey; border-radius: 3px;}
    QScrollBar::handle {background: lightgrey; border-radius: 3px;}

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

    /* Align the tabs on the left hand side, MacOS styles them in the center */
    QTabWidget::tab-bar {alignment: left;}
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
    * [state="ok"]{background-color: green; color: white;}
    * [state="changed"]{background-color: yellow; color: black;}
    * [state="running"]{background-color: orange; color: white;}
    * [state="highlight"]{background-color: lightblue; color: black;}
    * [state="error"]{background-color: red; color:white; font-weight:bold;}
    * [state="u_error"]{background-color: pink; color:white; font-weight:bold;}

    QWidget{font-size:10pt; font-family: Tahoma;}

    #medium{font-size: 11pt; font-weight: bold; }
    #large{font-size: 12pt; font-weight: bold; }
    #xlarge{font-size: 14pt; font-weight: bold;}

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

    /* Frame in frame, e.g. for target specs, only border-top - unused?
    QTabWidget#input_tabs > QFrame QFrame .QFrame
    {
        background-color:lime;
        border: solid #303030;
        border-width: 0.05em 0 0 0;
        padding: 0;
        margin: 0;
        }
    */

    QWidget#transparent{background-color:none}

    /* Dynamic filter subwidget */
    #wdg_fil{
        /*background-color:lightblue;*/
        border: none;
        padding: 0.2em 0 0 0;
        }

    /* Dynamic fixpoint widget */
    #fx_filt_ui .QFrame {background-color: lightblue;}
    #fx_filt_ui QFrame {color: black;}

    QCheckBox::indicator{border: 2px solid #808080;}
    QCheckBox::indicator:checked{background-color: lightblue;}

    /* Table Corner Button */
    QTableView QTableCornerButton::section{background-color:lightblue; border-color: green;}
    QTableView QTableCornerButton::section:pressed{background-color:red;}

    /* Padding of QSpin/Combobox and color of selected item */
    /* QSpinBox, QComboBox{
        padding-left: 0.2em; padding-right: 1em;
        padding-top: 2px; padding-bottom: 2px;
        selection-background-color: orange; }
    */
    /* These break the Combobox layout as well
        QComboBox::item:selected {background-color: orange;}
        QComboBox::item:checked {font-weight: bold;}
    */

    .QPushButton, PushButton{font-weight: bold;}
    QPushButton QLabel{font-weight: bold}
    /* Highlight push buttons when pressed from checked or unchecked state */
    QPushButton:pressed:checked, QPushButton:pressed:!checked
        {background-color:orange;} /* color: white */
    /* Define 'border' to avoid "grey dots" in all push buttons due to transparent border overlay
       This breaks the default layout
    https://forum.qt.io/topic/41325/solved-background-of-checked-qpushbutton-with-stylesheet
    https://stackoverflow.com/questions/24718722/how-to-style-qpushbuttons-checked-state-to-remove-grey-dots */
    /*QPushButton:checked {background-color:lightblue; border: lightblue;}
    .QPushButton:checked, PushButton:checked {color:black;}*/

    QProgressBar{background-color: orange;} /* running */
    QProgressBar{text-align: center; font-weight: bold; border: 1px solid #303030;}

    /* QSplitter styling adopted from
    http://stackoverflow.com/questions/6832499/qsplitter-show-a-divider-or-a-margin-between-the-two-widgets
    */

    /* needed to avoid "grey stipples" under windows: */
    QScrollBar::sub-page:horizontal, QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:vertical, QScrollBar::add-page:vertical
        {background: transparent;}

    QScrollBar:horizontal {height: 14px;}
    QScrollBar:vertical {width: 14px;}

    QScrollBar::handle:horizontal {min-width: 0px; image: url(':/scrollbar_handle.svg');}
    QScrollBar::handle:vertical {min-height: 0px; image: url(':/scrollbar_handle.svg');}

    /* turn off buttons */
    QScrollBar::add-line {
        border: none; background: none;}
    QScrollBar::sub-line {
        border: none; background: none;}

    QSplitter::handle:vertical {
        height: 8px;
        image: url(':/ellipses_v.svg');
        }
    QSplitter::handle:horizontal {
        width: 8px;
        image: url(':/ellipses_h.svg');
        }

    """
# Get all available system styles:
# from PyQt5.QtWidgets import QStyleFactory
# print(QStyleFactory.keys())

# General:          fusion
# MS Windows only:  windowsxp, windowsvista
# Mac only:         macintosh

# QApplication.setStyle(QStyleFactory.create('Cleanlooks')) re-create default styles


THEME = fb.conf_settings['THEME']

if THEME == 'dark':
    mpl_rc.update(mpl_rc_dark)
    params.update(mpl_params_dark)
    qss_rc = qss_common + qss_tab_bar + qss_dark
    params['link_color'] = 'lightblue'

elif THEME == 'light':
    mpl_rc.update(mpl_rc_light)
    params.update(mpl_params_light)
    qss_rc = qss_common + qss_tab_bar + qss_light
    params['link_color'] = 'blue'

elif THEME == 'none':
    mpl_rc.update(mpl_rc_light)
    params.update(mpl_params_light)
    qss_rc = qss_common

else:  # use the THEME name as the QStyle name
    mpl_rc.update(mpl_rc_light)
    params.update(mpl_params_light)
    qss_rc = THEME
