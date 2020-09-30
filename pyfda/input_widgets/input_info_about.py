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
import logging
logger = logging.getLogger(__name__)

from pyfda.libs.compat import (QtCore, QFD, Qt, QWidget, QPushButton, QFont, QFrame,
                      QVBoxLayout, QMessageBox, QPixmap, QIcon)

import pyfda.version as version
import pyfda.libs.pyfda_lib as pyfda_lib
import pyfda.libs.pyfda_dirs as dirs
import pyfda.filterbroker as fb
from pyfda.pyfda_rc import params

from pyfda import qrc_resources # contains all icons

if pyfda_lib.mod_version('xlwt') == None:
    XLWT = False
else:
    XLWT = True
    import xlwt

if pyfda_lib.mod_version('xlsxwriter') == None:
    XLSX = False
else:
    XLSX = True
    import xlsxwriter as xlsx


classes = {'Input_Files':'Files'} #: Dict containing class name : display name

class Input_Files(QWidget):
    """
    Create the widget for saving / loading data
    """
    sig_tx = QtCore.pyqtSignal(object) # sent when loading filter ('data_changed')

    def __init__(self, parent):
        super(Input_Files, self).__init__(parent)
        self.tab_label = 'Files'
        self.tool_tip = "Load and save filter designs."

        self._construct_UI()

    def _construct_UI(self):
        """
        Intitialize the user interface
        -
        """
        # widget / subwindow for parameter selection
        self.butAbout = QPushButton("About", self)

        # ============== UI Layout =====================================
        bfont = QFont()
        bfont.setBold(True)

        bifont = QFont()
        bifont.setBold(True)
        bifont.setItalic(True)

        ifont = QFont()
        ifont.setItalic(True)

        layVIO = QVBoxLayout()
        layVIO.addWidget(self.butAbout) # pop-up "About" window

        # This is the top level widget, encompassing the other widgets
        frmMain = QFrame(self)
        frmMain.setLayout(layVIO)

        layVMain = QVBoxLayout()
        layVMain.setAlignment(Qt.AlignTop)
#        layVMain.addLayout(layVIO)
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(*params['wdg_margins'])


        self.setLayout(layVMain)

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------
        self.butAbout.clicked.connect(self.about_window)



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

#         dir_string = ("<table><th style='font-size:large;'>Imported Modules</th>"
#                           "<tr><td>&nbsp;&emsp;{0}</td></tr>"\
#                           .format( pyfda_lib.mod_version().replace("\n", "<br>&nbsp;&emsp;")))

        dir_string = ("<table><th style='font-size:large;'>Software Versions</th>")
        dir_string += pyfda_lib.mod_version()
        dir_string += "</table>"

        dir_string += ("<table><th style='font-size:large;'>Directories</th>"
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

        about_string = info_string + versions_string + dir_string

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

        retval = msg.exec_()


#------------------------------------------------------------------------------

if __name__ == '__main__':
    """ Test with python -m pyfda.input_widgets.input_files """
    from pyfda.libs.compat import QApplication
    from pyfda import pyfda_rc as rc
    import sys
    app = QApplication(sys.argv)
    app.setStyleSheet(rc.qss_rc)
    mainw = Input_Files(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
