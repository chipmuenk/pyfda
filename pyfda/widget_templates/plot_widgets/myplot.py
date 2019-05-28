# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
User plotting widget
"""
import logging
logger = logging.getLogger(__name__)

from pyfda.compat import (QWidget, QLabel, QCheckBox, QFrame, QDial, QHBoxLayout, pyqtSlot, pyqtSignal)

from pyfda.pyfda_rc import params
from pyfda.pyfda_lib import unique_roots

from pyfda.plot_widgets.mpl_widget import MplWidget


class Myplot(QWidget):
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)

    def __init__(self, parent):
        super(Myplot, self).__init__(parent)
        self.needs_draw = True   # flag whether plot needs to be updated  
        self.needs_redraw = True # flag whether plot needs to be redrawn 
        self.tool_tip = "My first pyfda plot widget"
        self.tab_label = "xxx"

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from ..compat import QApplication
    import sys
    app = QApplication(sys.argv)
    mainw = Myplot(None)

    app.setActiveWindow(mainw) 
    mainw.show()

    sys.exit(app.exec_())
