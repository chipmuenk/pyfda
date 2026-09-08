# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
This file defines the style for Qt and matplotlib widgets.
A dark and a light theme can be selected via the `pyfda.conf` config file.

Default parameters, paths etc. are defined in the params dict.

Some parameters are specified as symbolic strings, e.g. |FONT_SIZE_BASE|, which are replaced
by the actual values in `pyfda_rc.py`.
"""
# pylint: disable=too-few-public-methods
from cycler import cycler
from pyfda.libs.pyfda_lib import replace_mult

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
# ---------------------------------------------------
# Light QSS theme
# ---------------------------------------------------
QSS_LIGHT = """
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

    /* NavigationToolbar needs to have the same color as pane */
    NavigationToolbar2QT{background-color: #E0E0E0;}
    NavigationToolbar2QT::separator{background-color: black;}

    /* background of Tabs, normally defined by pane */
    /* QTabBar {background-color: pink;} */

    QTextEdit{background-color: #F0F0F0;}
    QLineEdit{background-color: white; border-color: #303030;}
    QLineEdit:disabled{background-color:#C0C0C0; color: white;}

    QFileDialog QWidget{background-color: #F0F0F0;}

    /* Applies to all widgets in "normal" resp. "active" state
    * [state="normal"], * [state="active"], * [state="a"]
            {background-color: #C0C0C0;}
    /* 'unused', e.g. for lineedit fields with some filter designs */
    * [state="unused"], *[state="u"]{background-color: #E0E0E0; color:blue}

    /* Style 'normal' background for all push buttons */
    QPushButton{background-color: #C0C0C0;}
    .QPushButton:disabled, PushButton:disabled{
            background-color: #C0C0C0; color: white}

    /* Style the button of QRadioButton */
    QRadioButton::indicator:checked{
        background-color:black; border: 2px solid lightblue;}
    QRadioButton::indicator:unchecked{border: 2px solid black;}

    QCheckBox::indicator:checked{
        background-color: black; border: 2px solid lightblue;}
    QCheckBox::indicator:unchecked{border: 2px solid black;}

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
    /* Styling for context pop-up menu */
    QMenu {background-color: #E0E0E0; border: 1px solid grey; padding: 1px;}

    QTableView{alternate-background-color:#C0C0C0;
        background-color:#F0F0F0; gridline-color: #A0A0A0;}
    QHeaderView{background-color:#F0F0F0;}
    QHeaderView::section{background-color:#808080; color:white;}
    QHeaderView::section:checked{background-color:blue; color:white;}

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

# ---------------------------------------------------
# Dark QSS theme
# ---------------------------------------------------
QSS_DARK = """
    /* Background color #303030 should be same as matplotlib figure.facecolor */
    QSplitter{background-color: #303030;} /* Top Level background */
    QWidget{color:white;}  /* nearly all widgets are derived from this */
    /* background of QWidget and QFrame widgets, not of derived widgets: */
    .QWidget, .QFrame{background-color: #303030;}

    /* The tab _widget_ frame for all TabWidgets */
    QTabWidget {background-color: #303030;} /* Background for tabs except input tabs */
    /* background for input tabs, here QTabWidget is encompassed by QScrollArea */
    QScrollArea{color:white; background-color:#303030;}

    /* background of tab widget content */
    QTabWidget::pane{background-color: #707070;}
    /* Background of Tabs, normally defined by pane */
    /* QTabBar {background-color: pink;} */

    /* NavigationToolbar needs to have the same color as pane */
    NavigationToolbar2QT{background-color:#707070;}
    NavigationToolbar2QT::separator{background-color: white;}

    QTextEdit{background-color: #505050;}
    QLineEdit{background-color: #505050; border-color: #A0A0A0;}
    /* QLineEdit{selection-background-color: darkgray;} */
    QLineEdit:disabled{background-color: #707070; color: #B0B0B0}

    QFileDialog QWidget{background-color: #505050;}

    /* Applies to all widgets in "normal" resp. "active" state
    * [state="normal"], * [state="active"], * [state="a"]
        {background-color: #505050; color: white;}
    /* 'unused', e.g. for lineedit fields with some filter designs */
    * [state="unused"], *[state="u"]{background-color: #606060; color:lightblue}

    /* Style 'normal' background for all push buttons */
    QPushButton{background-color: #505050;}
    .QPushButton:disabled, PushButton:disabled{
        background-color: #707070; color: #A0A0A0;}

    /* Style the button of QRadioButton */
    QRadioButton::indicator:checked{
        background-color:black; border: 2px solid lightblue;}
    QRadioButton::indicator:unchecked{border: 2px solid grey;}

    QCheckBox::indicator:checked{
        background-color: black; border: 2px solid lightblue;}
    QCheckBox::indicator:unchecked{border: 2px solid grey;}

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
    /* Styling for context pop-up menu */
    QMenu {background-color: #404040; border: 1px solid white; padding: 1px;}

    QTableView{alternate-background-color:#202020;
        background-color:#505050; gridline-color: white;}
    QHeaderView{background-color:#202020;}
    QHeaderView::section{background-color:#101010;}
    QHeaderView::section:checked{background-color:blue;}

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
# ---------------------------------------------------------------
# Common QSS settings for all themes
# ---------------------------------------------------------------
QSS_COMMON = """
    * [state="ok"]{background-color: green; color: white;}
    * [state="changed"]{background-color: yellow; color: black;}
    * [state="running"]{background-color: orange; color: white;}
    * [state="highlight"]{background-color: lightblue; color: black;}
    * [state="error"]{background-color: red; color:white; font-weight:bold;}
    * [state="u_error"]{background-color: pink; color:white; font-weight:bold;}

    QWidget{font-size: |FONT_SIZE_BASE|; font-family: Tahoma;}
    #medium{font-size: |FONT_SIZE_MEDIUM|; font-weight: bold; }
    #large{font-size: |FONT_SIZE_LARGE|; font-weight: bold; }
    #xlarge{font-size: |FONT_SIZE_XLARGE|; font-weight: bold;}

    /* Frame with control elements of all plot widgets */
    #frm_controls{
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
    /* Toolbar for Matplotlib canvas */
    /* separator height / width is for horizontal / vertical toolbars */
    NavigationToolbar2QT::separator{width: 1px; height: 1px;
            margin-left: 6px; margin-right: 6px;}

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

    QRadioButton::indicator{
        background-color: transparent; border-radius:5px;} /*width:8px; height:8px;
    QCheckBox::indicator{background-color: transparent;}

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
    QProgressBar{
        text-align: center; font-weight: bold; border: 1px solid gray; border-radius: 2px;}
    QProgressBar::chunk{background-color: lightblue;}

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
# ---------------------------------------------------------------
# Common layout settings for QTabWidget
# ---------------------------------------------------------------
QSS_TAB_BAR = """
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

    QTabBar {font-weight: bold; font-size: |FONT_SIZE_MEDIUM|;}

    QTabBar::tab{
        color:black;
        font-size: |FONT_SIZE_MEDIUM|;
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
#--------------------------------------------------------------------------------
# Overlap effects for QTabWidget, currently not used
# -------------------------------------------------------------------------------
QSS_TAB_BAR_OVLP = """
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

# provide a default value for module testing
qss_rc = '\n/* Light QSS Mode */\n' + QSS_COMMON + QSS_TAB_BAR + QSS_LIGHT
QSS_RC = replace_mult(qss_rc, {
    "|FONT_SIZE_BASE|": "12",
    "|FONT_SIZE_MEDIUM|": "13",
    "|FONT_SIZE_LARGE|": "14",
    "|FONT_SIZE_XLARGE|": "15"
})

# #############################################################################
# Matplotlib layout settings
# #############################################################################

# dark theme for matplotlib widgets
MPL_RC_DARK = {
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
MPL_RC_LIGHT = {
    'axes.facecolor'    : 'white',
    'axes.labelcolor'   : 'black',
    'axes.edgecolor'    : 'black',  # figure edge
    'figure.facecolor'  : '#D0D0D0', # canvas background
    'figure.edgecolor'  : '#808080',
    'savefig.facecolor' : 'white',
    'savefig.edgecolor' : 'white',
    'xtick.color'       : 'black',
    'ytick.color'       : 'black',
    'text.color'        : 'black',
    'grid.color'        : '#202020',
    'axes.prop_cycle'   : cycler('color', ['r', 'b', 'c', 'm', 'k'])
    }

MPL_PARAMS_LIGHT = {
            'mpl_hatch': {                         # hatched area for specs
                         'facecolor': 'none',
                         'hatch': '/',
                         'edgecolor': '#808080',   # same as figure.edgecolor
                         'lw': 0.0},               # no border around hatched area

            'mpl_stimuli': {                       # style for stimulus signals
                          'mfc': 'k', 'mec': 'k',  # marker face + edge color
                          'ms': '|MPL_MS|',        # marker size
                          'alpha': 0.25,           # transparency (marker + stem)
                          'markerfmt': '*',        # marker symbol
                          'lw': '2'}               # stem linewidth
                    }

MPL_PARAMS_DARK = {
            'mpl_hatch': {                         # hatched area for specs
                         'facecolor': 'none',
                         'hatch': '/',
                         'edgecolor': '#808080',   # same as figure.edgecolor
                         'lw': 0.0},               # no border around hatched area

            'mpl_stimuli': {                       # style for stimulus signals
                          'mfc': 'w', 'mec': 'w',  # marker face + edge color
                          'ms': '|MPL_MS|',        # marker size
                          'alpha': 0.25,           # transparency (marker + stem)
                          'markerfmt': '*',        # marker symbol
                          'lw': '2'}               # stem linewidth
                    }

# fill_params = {'facecolor':'none','hatch':'/', 'edgecolor':rcParams['figure.edgecolor'],
# 'lw':0.0}

