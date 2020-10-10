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

from pyfda.libs.compat import (Qt, QWidget, QPushButton, QFont, QFrame, QDialog,
                      QVBoxLayout, QHBoxLayout, QMessageBox, QIcon, QPixmap, QTextBrowser)

from pyfda.libs.pyfda_qt_lib import qwindow_stay_on_top
import pyfda.version as version
import pyfda.libs.pyfda_lib as pyfda_lib
import pyfda.libs.pyfda_dirs as dirs
import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params
# from pyfda import qrc_resources # contains all icons


#------------------------------------------------------------------------------
class AboutWindow(QDialog):
    """
    Create a pop-up widget for the About Window.
    """
    # sig_tx = pyqtSignal(dict) # outgoing

    def __init__(self, parent):
        super(AboutWindow, self).__init__(parent)
        self.setWindowTitle("About pyFDA")
        #self.setWindowIcon(QIcon(':/pyfda_icon.svg'))
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

 
    def collect_about_string(self):

        user_dirs_str = ""
        if dirs.USER_DIRS:
            for d in dirs.USER_DIRS:
                user_dirs_str += d + '<br />'
        else:
            user_dirs_str = "None<br />"

        info_str = ("<b><a href=https://www.github.com/chipmuenk/pyfda>pyfda</a> "
        "Version {0} (c) 2013 - 2020 Christian Münker</b><br />"
        "Design, analyze and synthesize digital filters. Docs @ "
        "<a href=https://pyfda.rtfd.org>pyfda.rtfd.org</a>"
        " (<a href=https://media.readthedocs.org/pdf/pyfda/latest/pyfda.pdf>pdf</a>)<hr>"\
        .format(version.__version__))
            
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
# =============================================================================
#         with open(os.path.join(dirs.INSTALL_DIR, "module_versions.md"), 'r') as f:
#             # return a list, split at linebreaks while keeping linebreaks    
#             v = f.read().splitlines(True) 
#         
#         for l in v:
#             try:
#                 v_md += l.format(**MOD_VERSIONS) # evaluate {V_...} from MOD_VERSIONS entries
#             except (KeyError) as e: # encountered undefined {V_...}
#                 logger.warning("KeyError: {0}".format(e)) # simply drop the line
# 
#         ver_str = markdown.markdown(v_md, output_format='html5', extensions=['tables'])
# 
# =============================================================================
        ver_str = pyfda_lib.mod_version()
        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 
        
        if False: #dirs.PYINSTALLER:
            lic_str = ""
        else:
            with open(os.path.join(dirs.INSTALL_DIR, "license_info.md"), 'r') as f:
                lic_str = markdown.markdown(f.read(), output_format='html5', extensions=['tables'])

        about_string = info_str + os_str + dirs_str + ver_str + lic_str
        logger.warning(os.path.abspath("."))
        return about_string

#------------------------------------------------------------------------------
    def _construct_UI(self):
        """ initialize the User Interface """
        butClipboard = QPushButton(self)
        butClipboard.setIcon(QIcon(':/clipboard.svg'))
        butClipboard.setToolTip("Copy text to clipboard.")
        
        #pixIcon = QPixmap(':/pyfda_icon.svg').scaledToHeight(32, Qt.SmoothTransformation)
        
        butClose = QPushButton(self)
        butClose.setText("Close")
        butClose.setToolTip("Close Window.")
        layHButtons = QHBoxLayout()
        #layHButtons.addWidget(pixIcon)
        
        butLicMIT = QPushButton(self)
        butLicMIT.setText("MIT License")        
        butLicMIT.setToolTip("MIT License for pyFDA source code")
        
        butLicGPLv3 = QPushButton(self)
        butLicGPLv3.setText("GPLv3 License")        
        butLicGPLv3.setToolTip("GPLv3 License for bundled distribution")

        layHButtons.addWidget(butLicMIT)
        layHButtons.addWidget(butLicGPLv3)
        layHButtons.addStretch(5)
        layHButtons.addWidget(butClipboard)
        layHButtons.addWidget(butClose)
        
        # butClipboard.adjustSize()
        # butClipboard.setFixedSize(self.checkLayout.sizeHint())
        self.txtAboutBrowser = QTextBrowser(self)
        self.txtAboutBrowser.setText(self.collect_about_string())
        
        layVMain = QVBoxLayout()
        # layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addWidget(self.txtAboutBrowser)
        layVMain.addLayout(layHButtons)
        layVMain.setContentsMargins(*params['wdg_margins_spc'])
        self.setLayout(layVMain)
    
        butClipboard.clicked.connect(lambda: self.to_clipboard(self.collect_about_string()))
        butClose.clicked.connect(self.close)

#------------------------------------------------------------------------------

def about_window(self):
    """
    Display an "About" window with copyright and version infos
    """
    def to_clipboard(my_string):
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

    user_dirs_str = ""
    if dirs.USER_DIRS:
        for d in dirs.USER_DIRS:
            user_dirs_str += d + '<br />'

    info_string = ("<b><a href=https://www.github.com/chipmuenk/pyfda>pyfda</a> "
    "Version {0} (c) 2013 - 2020 Christian Münker</b><br />"
    "Design, analyze and synthesize digital filters. Docs @ "
    "<a href=https://pyfda.rtfd.org>pyfda.rtfd.org</a>"
    " (<a href=https://media.readthedocs.org/pdf/pyfda/latest/pyfda.pdf>pdf</a>)<hr>"\
    .format(version.__version__))

    versions_string =("<b>OS:</b> {0} {1}<br><b>User Name:</b> {2}<br>"
                .format(dirs.OS, dirs.OS_VER, dirs.USER_NAME))


    dir_string =    ("<h3>Directories</h3><table>"
                    "<tr><td><b>Home:</b></td><td>{0}</td></tr>"
                    "<tr><td><b>Install:&emsp;</b></td><td>{1}</td></tr>"
                     "<tr><td><b>Config:&emsp;</b></td><td>{2}</td></tr>"
                     "<tr><td><b>User:&emsp;</b></td><td>{3}</td></tr>"
                     "<tr><td><b>Temp:</b></td><td>{4}</td></tr>"\
                    .format( dirs.HOME_DIR, dirs.INSTALL_DIR, dirs.CONF_DIR,
                            user_dirs_str[:-6], dirs.TEMP_DIR))
    dir_string += ("<th style='font-size:large;'>Logging Files</th>"
                    "<tr><td><b>Config:</b></td><td>{0}</td></tr>"
                    "<tr><td><b>Output:&emsp;</b></td><td>{1}</td></tr>"
                    "</table>"\
                   .format(dirs.USER_LOG_CONF_DIR_FILE, dirs.LOG_DIR_FILE))

    about_string = info_string + versions_string + dir_string + pyfda_lib.mod_version()

    #msg = QMessageBox.about(self, "About pyFDA", info_string)
    butClipboard = QPushButton(self)
    butClipboard.setIcon(QIcon(':/clipboard.svg'))
    butClipboard.setToolTip("Copy text to clipboard.")
    # butClipboard.adjustSize()
    # butClipboard.setFixedSize(self.checkLayout.sizeHint())
    msg = QMessageBox(self)
    msg.setIconPixmap(QPixmap(':/pyfda_icon.svg').scaledToHeight(32, Qt.SmoothTransformation))
    msg.addButton(butClipboard, QMessageBox.ActionRole)
    msg.setText(about_string)
    # msg.setInformativeText("This is additional information")
    #msg.setDetailedText(versions_string) # adds a button that opens another textwindow

    msg.setWindowTitle("About pyFDA")
    msg.setStandardButtons(QMessageBox.Ok) # | QMessageBox.Cancel
    # close Message box with close event triggered by "x" icon
    msg.closeEvent = self.closeEvent

    butClipboard.clicked.connect(lambda: to_clipboard(about_string))

    _ = msg.exec_()
#------------------------------------------------------------------------------

if __name__ == '__main__':
    """ Test with python -m pyfda.input_widgets.input_info_about """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc
    import sys

# =============================================================================
#     class Test_button(QWidget):
#         """Create a widget with a button"""
#         def __init__(self, parent):
#             super(Test_button, self).__init__(parent)
#             
#             self.butAbout = QPushButton("About", self)
#             layVIO = QVBoxLayout()
#             layVIO.addWidget(self.butAbout) # pop-up "About" window
#             self.setLayout(layVIO)
# 
#             self.butAbout.clicked.connect(lambda: about_window(self))
# 
# =============================================================================
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = AboutWindow(None) # Test_button

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())