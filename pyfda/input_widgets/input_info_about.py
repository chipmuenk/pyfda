# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Widget for exporting / importing and saving / loading filter data
"""
import os
import re

import markdown

from pyfda.libs.compat import (
    Qt, QPushButton, QDialog, QVBoxLayout, QHBoxLayout, QIcon, QPixmap,
    QSizePolicy, QTextBrowser, QGridLayout, QLabel)

# load the icons resource file:
from pyfda import qrc_resources  # noqa: F401  # pylint: disable=unused-import
from pyfda.libs.pyfda_qt_lib import qwindow_stay_on_top
from pyfda.libs.pyfda_lib import mod_version, CRLF
import pyfda.libs.pyfda_dirs as dirs
from pyfda.pyfda_rc import params

# ------------------------------------------------------------------------------
class AboutWindow(QDialog):
    """
    Create a pop-up widget for the About Window.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("About pyFDA")
        self.collect_info()
        self._construct_ui()
        qwindow_stay_on_top(self, True)

    # ------------------------------------------------------------------------------
    def _construct_ui(self) -> None:
        """ initialize the User Interface """
        but_clipboard = QPushButton(self)
        but_clipboard.setIcon(QIcon(':/to_clipboard.svg'))
        but_clipboard.setToolTip("Copy text to clipboard.")

        but_about = QPushButton(self)
        but_about.setText("About")
        but_about.setToolTip("Display 'About' info")

        but_changelog = QPushButton(self)
        but_changelog.setText("Changelog")
        but_changelog.setToolTip("Display changelog")

        but_lic_mit = QPushButton(self)
        but_lic_mit.setText("MIT License")
        but_lic_mit.setToolTip("MIT License for pyFDA source code")

        but_lic_gpl_v3 = QPushButton(self)
        but_lic_gpl_v3.setText("GPLv3 License")
        but_lic_gpl_v3.setToolTip("GPLv3 License for bundled distribution")

        but_close = QPushButton(self)
        but_close.setIcon(QIcon(':/circle-x.svg'))
        but_close.setToolTip("Close Window.")

        lay_g_buttons = QGridLayout()
        lay_g_buttons.addWidget(but_clipboard, 0, 0)
        lay_g_buttons.addWidget(but_about, 0, 1)
        lay_g_buttons.addWidget(but_changelog, 0, 2)
        lay_g_buttons.addWidget(but_lic_mit, 0, 3)
        lay_g_buttons.addWidget(but_lic_gpl_v3, 0, 4)
        lay_g_buttons.addWidget(but_close, 0, 5)

        lbl_info = QLabel(self)
        lbl_info.setText(self.info_str)
        lbl_info.setOpenExternalLinks(True)
        lbl_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        lbl_icon = QLabel(self)
        lbl_icon.setPixmap(
            QPixmap(':/pyfda_icon.svg').scaledToHeight(lbl_info.height(),
                                                       Qt.SmoothTransformation))
        but_clipboard.setFixedHeight(lbl_info.height())
        but_clipboard.setFixedWidth(lbl_info.height())
        but_close.setFixedWidth(lbl_info.height())
        but_close.setFixedHeight(lbl_info.height())

        lay_h_info = QHBoxLayout()
        lay_h_info.addWidget(lbl_icon)
        lay_h_info.addWidget(lbl_info)

        self.txt_display = QTextBrowser(self)
        self.txt_display.setOpenExternalLinks(True)
        self.display_about_str()
        self.txt_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        lay_v_main = QVBoxLayout()
        lay_v_main.addLayout(lay_g_buttons)
        lay_v_main.addLayout(lay_h_info)
        lay_v_main.addWidget(self.txt_display)

        lay_v_main.setContentsMargins(*params['wdg_margins_spc'])
        self.setLayout(lay_v_main)

        but_clipboard.clicked.connect(
            lambda: self.to_clipboard(self.info_str + "<br />" + self.about_str))
        but_about.clicked.connect(self.display_about_str)
        but_changelog.clicked.connect(self.display_changelog)
        but_lic_mit.clicked.connect(self.display_mit_lic)
        but_lic_gpl_v3.clicked.connect(self.display_gpl_lic)
        but_close.clicked.connect(self.close)

    # ------------------------------------------------------------------------------
    def to_clipboard(self, my_string: str, html: bool = False) -> None:
        """
        Copy version info to clipboard
        TODO: This is stupid: md -> html -> md ?!

        Parameters
        ----------
        my_string: str
            The string to be copied to the clipboard

        html: bool
            When true, map some HTML tags to control codes and remove the rest
        """
        if html:
            dirs.clipboard.setText(my_string)  # copy untreated string
        else:
            # remove line breaks from string
            my_string = re.sub('\n', '', my_string)
            # a_string.replace("\n", " ")
            # map some HTML tags to control codes
            mapping = [('\r\n', ' '), ('\n', ' '), ('\r', ' '),
                       ('</th></tr>', CRLF + '=' * 20 + CRLF),
                       ('</table>', CRLF), ('<h3>', CRLF + '*'),
                       ('<br>', CRLF), ('<br />', CRLF),  ('</tr>', CRLF),
                       ('<hr>', '-' * 20), ('</h3>', '*' + CRLF + '-' * 20 + CRLF),
                       ('<b>', '*'), ('</b>', '*'), ('<em>', '*'), ('</em>', '*'),
                       ('<strong>', '*'), ('</strong>', '*'),
                       ('</td>', '\t'), ('</th>', '\t'), ('&emsp;', ' '), ('&gt;', '>')
                       ]
            for k, v in mapping:
                my_string = my_string.replace(k, v)

            # Remove remaining HTML tags and style settings
            # .  : match any character except newline
            # *  : match 0 or more repetitions of preceding RE
            # ?  : match 0 or one repetition of preceding RE
            # *? : make the '*' non-greedy, i.e. match as few chars as possible, e.g.
            #     only '<a>', not '<a> b <c>'
            clean = re.compile('<style>.*</style>|<.*?>')
            dirs.clipboard.setText(re.sub(clean, '', my_string))



    # ------------------------------------------------------------------------------
    def collect_info(self) -> None:
        """
        Collect information about version, imported modules in strings:

        `self.info_str` : General info, copyright, version, link to readthedocs
                          This info is always visible.

        `self.about_str`: OS, user name, directories, versions of installed software
        """

        self.info_str = self.style_html_links(
            "<b><a href=https://www.github.com/chipmuenk/pyfda>pyfda</a> "
            f"Version {dirs.VERSION} (c) 2013 - 2026 Christian Münker</b><br />"
            "Design, analyze and synthesize digital filters. Docs @ "
            "<a href=https://pyfda.rtfd.org>pyfda.rtfd.org</a>"
            " (<a href=https://media.readthedocs.org/pdf/pyfda/latest/pyfda.pdf>pdf</a>)")

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        user_dirs_str = ""
        if dirs.USER_DIRS:
            for d in dirs.USER_DIRS:
                user_dirs_str += d + '<br />'
        else:
            user_dirs_str = "None<br />"

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        os_str = (f"<b>OS:</b> {dirs.OS} {dirs.OS_VER}<br><b>User Name:</b> "
                  f"{dirs.USER_NAME}")

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        dirs_md = ("### Directories ###\n"
                   "| *Function*    | *Path*|\n"  # "|  <!-- -->     |  <!-- -->  |\n"
                   "|:  ----        |:  ----     |\n"
                   f"| **Install Dir**  | `{dirs.INSTALL_DIR}` |\n"
                   f"| **User Module Dir** &nbsp; | `{user_dirs_str[:-6]}` |\n"
                   f"| **Home Dir**  |   `{dirs.HOME_DIR}` |\n"
                   f"| **Temp Dir** | `{dirs.TEMP_DIR}` |\n"
                   "| - - - - - - -  | - - - - - - - - -|\n"
                   f"| **pyFDA Config** | `{dirs.USER_CONF_DIR_FILE}` |\n"
                   f"| **Log. Config** | `{dirs.USER_LOG_CONF_DIR_FILE}` |\n"
                   f"| **Logfile**  | `{dirs.LOG_DIR_FILE}` |"
        )



        dirs_str = markdown.markdown(dirs_md, output_format='html5',
                                     extensions=['markdown.extensions.tables'])
        # pyinstaller needs explicit definition of extensions path

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        ver_str = mod_version()
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        with open(os.path.join(dirs.INSTALL_DIR, "license_info.md"), 'r',
                    encoding="utf-8") as f:
            self.lic_str = markdown.markdown(
                f.read(), output_format='html5',
                extensions=['markdown.extensions.tables'])
        # pyinstaller needs explicit definition of extensions path

        self.about_str = os_str + dirs_str + ver_str

    # ------------------------------------------------------------------------------
    def display_about_str(self) -> None:
        """ Display general "About" info """
        self.txt_display.setText(self.style_html_links(self.about_str + self.lic_str))

    # ------------------------------------------------------------------------------
    def display_changelog(self) -> None:
        """ Display changelog """
        with open(os.path.join(dirs.INSTALL_DIR, "..", "CHANGELOG.md"), 'r',
                  encoding="utf-8") as f:
            log_str = markdown.markdown(f.read(), output_format='html5')
        self.txt_display.setText(self.style_html_links(log_str))

    # ------------------------------------------------------------------------------
    def display_mit_lic(self) -> None:
        """ Display MIT license """
        with open(os.path.join(dirs.INSTALL_DIR, "..", "LICENSE.md"), 'r',
                  encoding="utf-8") as f:
            lic_str = markdown.markdown(f.read(), output_format='html5')
        self.txt_display.setText(self.style_html_links(lic_str))

    # ------------------------------------------------------------------------------
    def display_gpl_lic(self) -> None:
        """ Display GPL license """
        with open(os.path.join(dirs.INSTALL_DIR, "..", "LICENSE_GPLv3.md"), 'r',
                  encoding="utf-8") as f:
            lic_str = markdown.markdown(f.read(), output_format='html5')
        self.txt_display.setText(self.style_html_links(lic_str))

    # ------------------------------------------------------------------------------
    def style_html_links(self, text: str) -> None:
        """ Embed HTML string between <body> tags with styling for links """
        return (f"<head><style>a:link {{color: {params['link_color']}}}</style></head>"
                f"<body>{text}</body>")

# =============================================================================
if __name__ == '__main__':
    # Run widget standalone with `python -m pyfda.input_widgets.input_info_about`
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda.pyfda_rc import QSS

    app = QApplication(sys.argv)
    app.setStyleSheet(QSS.QSS_RC)
    dirs.clipboard = QApplication.clipboard()
    mainw = AboutWindow()  # Test_button
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
