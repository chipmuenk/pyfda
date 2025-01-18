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

from pyfda.libs.compat import (QWidget, QLabel,  QFrame, QHBoxLayout, pyqtSlot, pyqtSignal)
from pyfda.pyfda_rc import params
from pyfda.libs.pyfda_lib import unique_roots
from pyfda.plot_widgets.mpl_widget import MplWidget

logger = logging.getLogger(__name__)

class Myplot(QWidget):
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)

    def __init__(self, parent):
        super().__init__()
        self.needs_calc = True   # flag whether plot needs to be recalculated
        self.needs_redraw = True # flag whether plot needs to be redrawn
        self.tool_tip = "My first pyfda plot widget"
        self.tab_label = "xxx"

#------------------------------------------------------------------------------

if __name__ == '__main__':

    from pyfda.libs.compat import QApplication
    import sys
    app = QApplication(sys.argv)
    mainw = Myplot(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
