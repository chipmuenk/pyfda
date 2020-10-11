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
import logging
logger = logging.getLogger(__name__)
import markdown

from pyfda.libs.compat import (Qt, QPushButton, QFrame, QDialog,
                      QVBoxLayout, QHBoxLayout, QIcon, QPixmap,
                      QSizePolicy, QTextBrowser, QGridLayout, QLabel)

from pyfda.libs.pyfda_qt_lib import qwindow_stay_on_top
import pyfda.version as version
import pyfda.libs.pyfda_lib as pyfda_lib
import pyfda.libs.pyfda_dirs as dirs
import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params

#------------------------------------------------------------------------------
class AboutWindow(QDialog):
    """
    Create a pop-up widget for the About Window.
    """
    # sig_tx = pyqtSignal(dict) # outgoing

    def __init__(self, parent):
        super(AboutWindow, self).__init__(parent)
        self.setWindowTitle("About pyFDA")
        self.collect_info()
        self._construct_UI()
        qwindow_stay_on_top(self, True)

#------------------------------------------------------------------------------

    def to_clipboard(self, my_string):
        """
        Copy version info to clipboard
        """
        mapping = [('<br>','\n'),('<br />','\n'),  ('</tr>','\n'),
                   ('</th>','\n==============\n'), ('</table>','\n'),
                   ('<hr>','\n---------\n'),
                   ('<b>',''),('</b>',''),('<tr>',''), ('<td>',''),('</td>','\t'),
                   ('<th>',''), ('&emsp;',' '), ('<table>',''),# ('</a>',''),
                   ("<th style='font-size:large;'>","\n")
                   ]
        for k, v in mapping:
            my_string = my_string.replace(k, v)
        fb.clipboard.setText(my_string)

#------------------------------------------------------------------------------

    def collect_info(self):
        """
        Collect information about version, imported modules in strings:
            
        `self.info_str` : General info, copyright, version, link to readthedocs
                          This info is always visible.
        
        `self.about_str`: OS, user name, directories, versions of installed software
        """


        self.info_str = ("<b><a href=https://www.github.com/chipmuenk/pyfda>pyfda</a> "
        "Version {0} (c) 2013 - 2020 Christian Münker</b><br />"
        "Design, analyze and synthesize digital filters. Docs @ "
        "<a href=https://pyfda.rtfd.org>pyfda.rtfd.org</a>"
        " (<a href=https://media.readthedocs.org/pdf/pyfda/latest/pyfda.pdf>pdf</a>)<br />"\
        .format(version.__version__))

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

        user_dirs_str = ""
        if dirs.USER_DIRS:
            for d in dirs.USER_DIRS:
                user_dirs_str += d + '<br />'
        else:
            user_dirs_str = "None<br />"
            
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

        os_str =("<b>OS:</b> {0} {1}<br><b>User Name:</b> {2}"
                    .format(dirs.OS, dirs.OS_VER, dirs.USER_NAME))
        
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

        dirs_md = ("### Directories ###\n"
                      "| *Function*    | *Path*|\n"#"|  <!-- -->     |  <!-- -->  |\n"
                      "|:  ----        |:  ----     |\n"
                      "| **Install Dir **  | `{install_dir}` |\n"
                      "| **User Module Dir ** | `{user_dir}` |\n"
                      "| **Home Dir**  |   `{home_dir}` |\n"
                      "| **Temp Dir ** | `{temp_dir}` |\n"
                      "| **Config Dir ** | `{conf_dir}` |\n"
                      "| - - - - - - -  | - - - - - - - - -|\n"
                      "| **pyFDA Config ** | `{pyfda_conf}` |\n"
                      "| **Log. Config ** | `{log_conf}` |\n"
                      "| **Logfile **  | `{log_file}` |"\
                      .format(home_dir=dirs.HOME_DIR, install_dir=dirs.INSTALL_DIR,
                              conf_dir=dirs.CONF_DIR, user_dir=user_dirs_str[:-6],
                              temp_dir=dirs.TEMP_DIR, pyfda_conf=dirs.USER_CONF_DIR_FILE,
                              log_conf=dirs.USER_LOG_CONF_DIR_FILE, log_file=dirs.LOG_DIR_FILE))
                      
        dirs_str = markdown.markdown(dirs_md, output_format='html5', extensions=['tables'])
        
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

        ver_str = pyfda_lib.mod_version()
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        
        if False: #dirs.PYINSTALLER:
            self.lic_str = ""
        else:
            with open(os.path.join(dirs.INSTALL_DIR, "license_info.md"), 'r') as f:
                self.lic_str = markdown.markdown(f.read(), output_format='html5', extensions=['tables'])

        self.about_str = os_str + dirs_str + ver_str
        logger.warning(os.path.abspath("."))

#------------------------------------------------------------------------------
    def _construct_UI(self):
        """ initialize the User Interface """
            
        butClipboard = QPushButton(self)
        butClipboard.setIcon(QIcon(':/clipboard.svg'))
        butClipboard.setToolTip("Copy text to clipboard.")
        
        butClose = QPushButton(self)
        butClose.setText("Close")
        butClose.setToolTip("Close Window.")
        
        butLicMIT = QPushButton(self)
        butLicMIT.setText("MIT License")        
        butLicMIT.setToolTip("MIT License for pyFDA source code")
        
        butLicGPLv3 = QPushButton(self)
        butLicGPLv3.setText("GPLv3 License")        
        butLicGPLv3.setToolTip("GPLv3 License for bundled distribution")

        layGButtons = QGridLayout()
        layGButtons.addWidget(butClipboard,0,0)
        layGButtons.addWidget(butLicMIT, 0,1)
        layGButtons.addWidget(butLicGPLv3,0,2)
        layGButtons.addWidget(butClose,0,3)
# =============================================================================
#         layHButtons = QHBoxLayout()
#         #layHButtons.addWidget(pixIcon)
#         layHButtons.addWidget(butLicMIT)
#         layHButtons.addWidget(butLicGPLv3)
#         layHButtons.addStretch(1)
#         layHButtons.addWidget(butClipboard)
#         layHButtons.addWidget(butClose)
#         
# =============================================================================

        txtInfo = QLabel(self)
        txtInfo.setText(self.info_str)
        txtInfo.setFixedHeight(txtInfo.height()*1.2)
        txtInfo.adjustSize()
        
        lblIcon = QLabel(self)
        lblIcon.setPixmap(QPixmap(':/pyfda_icon.svg').scaledToHeight(txtInfo.height(), Qt.SmoothTransformation))
        butClipboard.setFixedWidth(txtInfo.height())
        
        layHInfo = QHBoxLayout()
        layHInfo.addWidget(lblIcon)
        layHInfo.addWidget(txtInfo)

        self.txtAboutBrowser = QTextBrowser(self)
        self.txtAboutBrowser.setText(self.about_str + self.lic_str)
        txtInfo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layVMain = QVBoxLayout()
        # layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addLayout(layGButtons)
        layVMain.addLayout(layHInfo)
        layVMain.addWidget(self.txtAboutBrowser)

        layVMain.setContentsMargins(*params['wdg_margins_spc'])
        self.setLayout(layVMain)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.resize(0,0)
        self.adjustSize()
        #QApplication.processEvents()
    
        butClipboard.clicked.connect(lambda: self.to_clipboard(self.info_str + self.about_str))
        butClose.clicked.connect(self.close)

# =============================================================================
if __name__ == '__main__':
    """ Test with python -m pyfda.input_widgets.input_info_about """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc
    import sys

    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    fb.clipboard = QApplication.clipboard()
    mainw = AboutWindow(None) # Test_button

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())