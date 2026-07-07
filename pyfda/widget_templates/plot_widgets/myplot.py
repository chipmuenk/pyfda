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

from pyfda.libs.compat import QWidget, pyqtSignal
from pyfda.pyfda_rc import params
from pyfda.plot_widgets.mpl_widget import MplWidget

logger = logging.getLogger(__name__)

class MyPlot(QWidget):
    """
    Widget template for constructing your own plot widget
    TODO: some more details needed
    """
    # incoming, connected in sender widget (locally connected to self.process_sig_rx() )
    sig_rx = pyqtSignal(object)

    def __init__(self):
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
    mainw = MyPlot(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
