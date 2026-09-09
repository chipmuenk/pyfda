# -*- coding: utf-8 -*-
#
# This file is part of the pyfda project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyfda Project Contributors
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
import logging
from typing import Any, ClassVar

import matplotlib.font_manager

from pyfda.libs.pyfda_lib import CRLF, replace_mult
from pyfda.config_file_parser import ConfigFileParser as CFP
# Register resources like icons, this also gets rid of "unused import" warnings
# during module test
from pyfda import qrc_resources  # noqa: F401 # pylint: disable=unused-import

from pyfda import ui_styles

logger = logging.getLogger(__name__)

# #############################################################################
# General layout settings
# #############################################################################
MPL_MS = 8  # base size for matplotlib markers
# Various parameters for calculation, plotting and UI
params = {
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
        'ref_dpi': 96, 'scaling': 1.0, # dpi ref. value for scaling = 1 and scaling factor
        'ldpi': 96, 'pdpi': 96, # logical and physical dpi of the screen, updated in pyfdax.py
        'height': 720, 'width': 1024}, # height and width in pixels
    'FMT_ba': 4,      # number of digits for coefficient table
    'FMT_pz': 5,      # number of digits for Pole/Zero table
    'P_Marker': [MPL_MS, 'r'],  # size and color for poles' marker
    'Z_Marker': [MPL_MS, 'b'],  # size and color for zeros' marker
    'wdg_margins': (2, 1, 2, 0),  # (R, T, L, B) widget margins
    'wdg_margins_spc': (2, 2, 2, 2),  # widget margins with more vertical spacing
    'wdg_margins_0': (0, 0, 0, 0),  # set margins to zero
    'mpl_margins': (0, 0, 0, 0),  # margins around matplotlib widgets
    'mpl_hatch_border': {'linewidth': 1.0, 'color': 'blue', 'linestyle': '--'},
    'link_color': 'blue'  # link color in HTML text
          }


class QSS():
    """
    Container for the application's Qt and Matplotlib style definitions.

    This class groups the dark/light theme settings, widget style sheets, and
    Matplotlib runtime configuration used by pyfda.
    """

    # common matplotlib widget settings
    mpl_rc : ClassVar[dict[str, dict[str, Any]]] =\
        { 'lines.linewidth'           : 1.5,
          'lines.markersize'          : '|MPL_MS|',         # markersize, in points
          'font.family'               : 'sans-serif',  # 'serif',
          'font.style'                : 'normal',
          'mathtext.fontset'          : 'stixsans',  # 'stix',
          'mathtext.default'          : 'it',
          'mathtext.fallback'         : 'cm',
          'font.size'                 : '|FONT_SIZE_MPL|',
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
          'figure.figsize'            : (5, 4),
          'figure.dpi'                : 100,
          'hatch.color'               : '#808080',
          'hatch.linewidth'           : 0.5
        }

    # provide a default value for module level testing
    QSS_RC = ui_styles.QSS_RC

    def __init__(self):
        pass

    def set_qss(self):
        """
        Collate QSS string from common settings, special settings for the tab bar and a
        color scheme that depends on the theme selected in `pyfda.conf`.
        """
        FONT_SIZE_QT = 12 * CFP.conf_settings['SCALE_UI']  # base size for Qt fonts
        FONT_SIZE_BASE = str(FONT_SIZE_QT) + "pt"  # base font size of widgets in pt
        FONT_SIZE_MEDIUM = str(FONT_SIZE_QT * 1.1) + "pt"
        FONT_SIZE_LARGE = str(FONT_SIZE_QT * 1.2) + "pt"
        FONT_SIZE_XLARGE = str(FONT_SIZE_QT * 1.4) + "pt"

        QSS.FONT_SIZE_MPL = FONT_SIZE_QT * CFP.conf_settings['SCALE_MPL']

        # dictionary for replacing placeholders in the QSS string with actual values
        replace_dict = {
            '|FONT_SIZE_BASE|': FONT_SIZE_BASE,
            '|FONT_SIZE_MEDIUM|': FONT_SIZE_MEDIUM,
            '|FONT_SIZE_LARGE|': FONT_SIZE_LARGE,
            '|FONT_SIZE_XLARGE|': FONT_SIZE_XLARGE,
            '|FONT_SIZE_MPL|': QSS.FONT_SIZE_MPL,
            '|MPL_MS|': MPL_MS
        }

        QSS.THEME = CFP.conf_settings['THEME']
        if QSS.THEME == 'dark':
            params.update(ui_styles.MPL_PARAMS_DARK)
            params['link_color'] = 'lightblue'
            QSS.mpl_rc.update(ui_styles.MPL_RC_DARK)

            QSS.QSS_RC = '\n/* Dark QSS Mode */\n' +\
                ui_styles.QSS_COMMON + ui_styles.QSS_TAB_BAR + ui_styles.QSS_DARK

        elif QSS.THEME == 'light':
            params.update(ui_styles.MPL_PARAMS_LIGHT)
            params['link_color'] = 'blue'
            QSS.mpl_rc.update(ui_styles.MPL_RC_LIGHT)

            QSS.QSS_RC = '\n/* Light QSS Mode */\n' +\
            ui_styles.QSS_COMMON + ui_styles.QSS_TAB_BAR + ui_styles.QSS_LIGHT

        elif QSS.THEME == 'none':
            QSS.mpl_rc.update(ui_styles.MPL_RC_LIGHT)
            params.update(ui_styles.MPL_PARAMS_LIGHT)
            QSS.QSS_RC = '\n/* Default QSS Mode */\n' + ui_styles.QSS_COMMON

        else:  # use the THEME name as the QStyle name
            QSS.mpl_rc.update(ui_styles.MPL_RC_LIGHT)
            params.update(ui_styles.MPL_PARAMS_LIGHT)
            QSS.QSS_RC = QSS.THEME

        QSS.QSS_RC = replace_mult(QSS.QSS_RC, replace_dict)
        QSS.mpl_rc = replace_mult(QSS.mpl_rc, replace_dict)

        # --------------------- Matplotlib Fonts --------------------------------------
        # afm_fonts = sorted({f.name for f in matplotlib.font_manager.fontManager.afmlist})
        ttf_fonts = sorted({f.name for f in matplotlib.font_manager.fontManager.ttflist})

        if 'DejaVu Sans' in ttf_fonts:
            logger.info("Using 'DejaVu Sans' font.")
            QSS.mpl_rc.update({
                        'mathtext.fontset': 'custom',
                        'mathtext.rm': 'DejaVu Sans',
                        'mathtext.it': 'DejaVu Sans:italic',
                        'mathtext.bf': 'DejaVu Sans:bold'
                        })
        elif 'Bitstream Vera Sans' in ttf_fonts:
            logger.info("Using 'Bitstream Vera Sans' font.")
            QSS.mpl_rc.update({
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

#------------------------------------------------------------------------------

if __name__ == '__main__':
    # Run this module standalone with 'python -m pyfda.pyfda_rc'

    QSS().set_qss()
