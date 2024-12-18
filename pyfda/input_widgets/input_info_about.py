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

from pyfda.libs.pyfda_qt_lib import qwindow_stay_on_top
import pyfda.version as version
from pyfda.libs.pyfda_lib import mod_version, CRLF
import pyfda.libs.pyfda_dirs as dirs
import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params

# ------------------------------------------------------------------------------
class AboutWindow(QDialog):
    """
    Create a pop-up widget for the About Window.
    """
    # sig_tx = pyqtSignal(dict) # outgoing

    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent)
        self.setWindowTitle("About pyFDA")
        self.collect_info()
        self._construct_UI()
        qwindow_stay_on_top(self, True)

# ------------------------------------------------------------------------------
    def _construct_UI(self):
        """ initialize the User Interface """
        butClipboard = QPushButton(self)
        butClipboard.setIcon(QIcon(':/to_clipboard.svg'))
        butClipboard.setToolTip("Copy text to clipboard.")

        butAbout = QPushButton(self)
        butAbout.setText("About")
        butAbout.setToolTip("Display 'About' info")

        butChangelog = QPushButton(self)
        butChangelog.setText("Changelog")
        butChangelog.setToolTip("Display changelog")

        butLicMIT = QPushButton(self)
        butLicMIT.setText("MIT License")
        butLicMIT.setToolTip("MIT License for pyFDA source code")

        butLicGPLv3 = QPushButton(self)
        butLicGPLv3.setText("GPLv3 License")
        butLicGPLv3.setToolTip("GPLv3 License for bundled distribution")

        butClose = QPushButton(self)
        butClose.setIcon(QIcon(':/circle-x.svg'))
        butClose.setToolTip("Close Window.")

        layGButtons = QGridLayout()
        layGButtons.addWidget(butClipboard, 0, 0)
        layGButtons.addWidget(butAbout, 0, 1)
        layGButtons.addWidget(butChangelog, 0, 2)
        layGButtons.addWidget(butLicMIT, 0, 3)
        layGButtons.addWidget(butLicGPLv3, 0, 4)
        layGButtons.addWidget(butClose, 0, 5)

        lblInfo = QLabel(self)
        lblInfo.setText(self.info_str)
        lblInfo.setFixedHeight(int(lblInfo.height()*1.2))
        # lblInfo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        lblInfo.setOpenExternalLinks(True)

        lblIcon = QLabel(self)
        lblIcon.setPixmap(
            QPixmap(':/pyfda_icon.svg').scaledToHeight(lblInfo.height(),
                                                       Qt.SmoothTransformation))
        butClipboard.setFixedWidth(lblInfo.height())
        butClose.setFixedWidth(lblInfo.height())

        layHInfo = QHBoxLayout()
        layHInfo.addWidget(lblIcon)
        layHInfo.addWidget(lblInfo)

        self.txtDisplay = QTextBrowser(self)
        self.txtDisplay.setOpenExternalLinks(True)
        self.display_about_str()
        self.txtDisplay.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.txtDisplay.setFixedHeight(self.txtDisplay.width() * 2)

        layVMain = QVBoxLayout()
        # layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget
        layVMain.addLayout(layGButtons)
        layVMain.addLayout(layHInfo)
        layVMain.addWidget(self.txtDisplay)

        layVMain.setContentsMargins(*params['wdg_margins_spc'])
        self.setLayout(layVMain)
        # self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.resize(0,0)
        # self.adjustSize()
        # QApplication.processEvents()

        butClipboard.clicked.connect(
            lambda: self.to_clipboard(self.info_str + self.about_str))
        butAbout.clicked.connect(self.display_about_str)
        butChangelog.clicked.connect(self.display_changelog)
        butLicMIT.clicked.connect(self.display_MIT_lic)
        butLicGPLv3.clicked.connect(self.display_GPL_lic)
        butClose.clicked.connect(self.close)

# ------------------------------------------------------------------------------
    def to_clipboard(self, my_string, html=False):
        """
        Copy version info to clipboard
        TODO: This is stupid: md -> html -> md ?!
        """
        if not html:
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
            fb.clipboard.setText(re.sub(clean, '', my_string))
        else:
            fb.clipboard.setText(my_string)  # copy untreated string
# ------------------------------------------------------------------------------

    def collect_info(self):
        """
        Collect information about version, imported modules in strings:

        `self.info_str` : General info, copyright, version, link to readthedocs
                          This info is always visible.

        `self.about_str`: OS, user name, directories, versions of installed software
        """

        self.info_str = self.style_html_links(
            "<b><a href=https://www.github.com/chipmuenk/pyfda>pyfda</a> "
            f"Version {version.__version__} (c) 2013 - 2024 Christian Münker</b><br />"
            "Design, analyze and synthesize digital filters. Docs @ "
            "<a href=https://pyfda.rtfd.org>pyfda.rtfd.org</a>"
            " (<a href=https://media.readthedocs.org/pdf/pyfda/latest/pyfda.pdf>pdf</a>)"
            "<br />")

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
                   "| **Install Dir**  | `{install_dir}` |\n"
                   "| **User Module Dir** | `{user_dir}` |\n"
                   "| **Home Dir**  |   `{home_dir}` |\n"
                   "| **Temp Dir** | `{temp_dir}` |\n"
                   "| - - - - - - -  | - - - - - - - - -|\n"
                   "| **pyFDA Config** | `{pyfda_conf}` |\n"
                   "| **Log. Config** | `{log_conf}` |\n"
                   "| **Logfile**  | `{log_file}` |"
                   .format(home_dir=dirs.HOME_DIR, install_dir=dirs.INSTALL_DIR,
                           conf_dir=dirs.CONF_DIR, user_dir=user_dirs_str[:-6],
                           temp_dir=dirs.TEMP_DIR, pyfda_conf=dirs.USER_CONF_DIR_FILE,
                           log_conf=dirs.USER_LOG_CONF_DIR_FILE,
                           log_file=dirs.LOG_DIR_FILE))

        dirs_str = markdown.markdown(dirs_md, output_format='html5',
                                     extensions=['markdown.extensions.tables'])
        # pyinstaller needs explicit definition of extensions path

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        ver_str = mod_version()
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        if False:  # dirs.PYINSTALLER:
            self.lic_str = ""
        else:
            with open(os.path.join(dirs.INSTALL_DIR, "license_info.md"), 'r') as f:
                self.lic_str = markdown.markdown(
                    f.read(), output_format='html5',
                    extensions=['markdown.extensions.tables'])
            # pyinstaller needs explicit definition of extensions path

        self.about_str = os_str + dirs_str + ver_str

# ------------------------------------------------------------------------------

    def display_about_str(self):
        """ Display general "About" info """

        self.txtDisplay.setText(self.style_html_links(self.about_str + self.lic_str))

# ------------------------------------------------------------------------------

    def display_changelog(self):
        """ Display changelog """
        with open(os.path.join(dirs.INSTALL_DIR, "..", "CHANGELOG.md"), 'r') as f:
            log_str = markdown.markdown(f.read(), output_format='html5')
        self.txtDisplay.setText(self.style_html_links(log_str))

# ------------------------------------------------------------------------------

    def display_MIT_lic(self):
        """ Display MIT license """
        with open(os.path.join(dirs.INSTALL_DIR, "..", "LICENSE.md"), 'r') as f:
            lic_str = markdown.markdown(f.read(), output_format='html5')
        self.txtDisplay.setText(self.style_html_links(lic_str))

# ------------------------------------------------------------------------------

    def display_GPL_lic(self):
        """ Display GPL license """
        with open(os.path.join(dirs.INSTALL_DIR, "..", "LICENSE_GPLv3.md"), 'r') as f:
            lic_str = markdown.markdown(f.read(), output_format='html5')
        self.txtDisplay.setText(self.style_html_links(lic_str))

# ------------------------------------------------------------------------------

    def style_html_links(self, text):
        """ Embed HTML string between <body> tags with styling for links """
        return (f"<head><style>a:link {{color: {params['link_color']}}}</style></head>"
                f"<body>{text}</body>")

# =============================================================================
if __name__ == '__main__':
    """ Run widget standalone with `python -m pyfda.input_widgets.input_info_about` """
    import sys
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    fb.clipboard = QApplication.clipboard()
    mainw = AboutWindow()  # Test_button
    app.setActiveWindow(mainw)
    mainw.show()
    sys.exit(app.exec_())
