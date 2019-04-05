# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Construct a widget consisting of a matplotlib canvas and an improved Navigation
toolbar.
"""
from __future__ import print_function, division, unicode_literals
import logging
logger = logging.getLogger(__name__)

import sys
import six
import numpy as np

# do not import matplotlib.pyplot - pyplot brings its own GUI, event loop etc!!!
#from matplotlib.backend_bases import cursors as mplCursors
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from matplotlib import rcParams

try:
    import matplotlib.backends.qt_editor.figureoptions as figureoptions
except ImportError:
    figureoptions = None
    
from ..compat import (QtCore, QWidget, QLabel, pyqtSignal, pyqtSlot, HAS_QT5,
                      QSizePolicy, QIcon, QImage, QPixmap, QVBoxLayout,
                      QInputDialog, FigureCanvas, NavigationToolbar)

from pyfda import pyfda_rc
import pyfda.filterbroker as fb
from pyfda import qrc_resources # contains all icons

# read user settings for linewidth, font size etc. and apply them to matplotlib
for key in pyfda_rc.mpl_rc:
    rcParams[key] = pyfda_rc.mpl_rc[key]

#------------------------------------------------------------------------------
def stems(x, y, ax=None, label=None, **kwargs):
    """ A faster replacement for stem plot
    """
    # pop the 'bottom' key-value pair from the dict, provide default value 0
    bottom=kwargs.pop('bottom', 0) 
    ax.axhline(bottom, **kwargs)
    ax.vlines(x, y, bottom, label=label, **kwargs)
    # ax.set_ylim([1.05*y.min(), 1.05*y.max()])

def no_plot(x, y, ax=None, bottom=0, label=None, **kwargs):
    """
    Don't plot anything - needed for plot factory
    """
    pass 
    
#------------------------------------------------------------------------------
class MplWidget(QWidget):
    """
    Construct a subwidget, instantiating a Matplotlib canvas and a modified
    NavigationToolbar.
    """

    def __init__(self, parent):
        super(MplWidget, self).__init__(parent)
        # Create the mpl figure and subplot (white bg, 100 dots-per-inch).
        # Construct the canvas with the figure:
        self.plt_lim = [] # define variable for x,y plot limits
        self.fig = Figure()

        self.pltCanv = FigureCanvas(self.fig)
        self.pltCanv.setSizePolicy(QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)

        # Needed for mouse modifiers (x,y, <CTRL>, ...):
        #    Key press events in general are not processed unless you
        #    "activate the focus of Qt onto your mpl canvas"
        # http://stackoverflow.com/questions/22043549/matplotlib-and-qt-mouse-press-event-key-is-always-none
        self.pltCanv.setFocusPolicy( QtCore.Qt.ClickFocus )
        self.pltCanv.setFocus()

        self.pltCanv.updateGeometry()

        # Create a custom navigation toolbar, tied to the canvas and
        # initialize toolbar settings
        #
        #self.mplToolbar = NavigationToolbar(self.pltCanv, self) # original
        self.mplToolbar = MplToolbar(self.pltCanv, self) # inherits all methods
        self.mplToolbar.lock_zoom = False
        #self.mplToolbar.enable_plot(state = True)
        self.mplToolbar.sig_tx.connect(self.process_signals)

        #=============================================
        # Main plot widget layout
        #=============================================
        self.layVMainMpl = QVBoxLayout()
        self.layVMainMpl.addWidget(self.mplToolbar)
        self.layVMainMpl.addWidget(self.pltCanv)

        self.setLayout(self.layVMainMpl)

#------------------------------------------------------------------------------
    @pyqtSlot(object)
    def process_signals(self, dict_sig):
        """
        Process sig
        """
#        if 'enabled' in dict_sig:
#            self.clear_disabled_figure(dict_sig['enabled'])
#        else:
        pass

#------------------------------------------------------------------------------
    def save_limits(self):
        """
        Save x- and y-limits of all axes in self.limits when zoom is unlocked
        """
        if not self.mplToolbar.lock_zoom:
            for ax in self.fig.axes:
                self.limits = ax.axis() # save old limits

#------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the figure with new properties (grid, linewidth)
        """
        # only execute when at least one axis exists -> tight_layout crashes otherwise
        if self.fig.axes:
            for ax in self.fig.axes:
                if hasattr(ax, "is_twin"):
                    ax.grid(False)  # the axis is a twinx() system, suppress the gridlines
                else:
                    ax.grid(self.mplToolbar.a_gr.isChecked())  # collect axes objects and apply grid settings

                if self.mplToolbar.lock_zoom:
                    ax.axis(self.limits) # restore old limits
                else:
                    self.limits = ax.axis() # save old limits

            try:
                # tight_layout() crashes with small figure sizes
               self.fig.tight_layout(pad = 0.1)
            except(ValueError, np.linalg.linalg.LinAlgError):
                logger.debug("error in tight_layout")
        self.pltCanv.draw() # now (re-)draw the figure

#------------------------------------------------------------------------------
#    def clear_disabled_figure(self, enabled):
#        """
#        Clear the figure when it is disabled in the mplToolbar
#        """
#        if not enabled:
#            self.fig.clf()
#            self.pltCanv.draw()
#        else:
#            self.redraw()

#------------------------------------------------------------------------------
    def plt_full_view(self):
        """
        Zoom to full extent of data if axes is set to "navigationable"
        by the navigation toolbar
        """
        #Add current view limits to view history to enable "back to previous view"
        self.mplToolbar.push_current()
        for ax in self.fig.axes:
            if ax.get_navigate():
                ax.autoscale()
        self.redraw()
#------------------------------------------------------------------------------
    def get_full_extent(self, ax, pad=0.0):
        """
        Get the full extent of axes system `ax`, including axes labels, tick labels
        and titles.
        """
        #http://stackoverflow.com/questions/14712665/matplotlib-subplot-background-axes-face-labels-colour-or-figure-axes-coor
        # For text objects, we need to draw the figure first, otherwise the extents
        # are undefined.
        self.pltCanv.draw()
        items = ax.get_xticklabels() + ax.get_yticklabels()
        items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
        bbox = Bbox.union([item.get_window_extent() for item in items])
        return bbox.expanded(1.0 + pad, 1.0 + pad)

###############################################################################

class MplToolbar(NavigationToolbar):
    """
    Custom Matplotlib Navigationtoolbar, derived (subclassed) from Qt's
    NavigationToolbar with the following changes:
    - new icon set
    - new functions and icons for grid toggle, full view, screenshot
    - removed buttons for configuring subplots and editing curves
    - added an x,y location widget and icon
    
    Signalling / communication works via the signal `sig_tx'


    derived from http://www.python-forum.de/viewtopic.php?f=24&t=26437

    http://pydoc.net/Python/pyQPCR/0.7/pyQPCR.widgets.matplotlibWidget/  !!
    http://matplotlib.org/users/navigation_toolbar.html !!

    see also http://stackoverflow.com/questions/17711099/programmatically-change-matplotlib-toolbar-mode-in-qt4
             http://matplotlib-users.narkive.com/C8XwIXah/need-help-with-darren-dale-qt-example-of-extending-toolbar
             https://sukhbinder.wordpress.com/2013/12/16/simple-pyqt-and-matplotlib-example-with-zoompan/

    Changing the info:
    http://stackoverflow.com/questions/15876011/add-information-to-matplotlib-navigation-toolbar-status-bar
    """

#    toolitems = (
#        ('Home', 'Reset original view', 'home', 'home'),
#        ('Back', 'Back to  previous view', 'action-undo', 'back'),
#        ('Forward', 'Forward to next view', 'action-redo', 'forward'),
#        (None, None, None, None),
#        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
#        ('Zoom', 'Zoom to rectangle', 'magnifying-glass', 'zoom'),
#        (None, None, None, None),
#        ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
#        ('Save', 'Save the figure', 'file', 'save_figure'),
#      )

# subclass NavigationToolbar, passing through arguments:
    #def __init__(self, canvas, parent, coordinates=True):

    sig_tx = pyqtSignal(object) # general signal, containing a dict 

    def __init__(self, *args, **kwargs):
        NavigationToolbar.__init__(self, *args, **kwargs)

#------------------------------------------------------------------------------
    def _init_toolbar(self):

        #---------------- Construct Toolbar using QRC icons -------------------
        # ENABLE:
#        self.a_en = self.addAction(QIcon(':/circle-x.svg'), 'Enable Update', self.enable_plot)
#        self.a_en.setToolTip('Enable / disable plot')
#        self.a_en.setCheckable(True)
#        self.a_en.setChecked(True)
##        self.a.setEnabled(False)

        self.addSeparator() #---------------------------------------------

        # HOME:
        self.a_ho = self.addAction(QIcon(':/home.svg'), 'Home', self.home)
        self.a_ho.setToolTip('Reset zoom')
        # BACK:
        self.a_ba = self.addAction(QIcon(':/action-undo.svg'), 'Back', self.back)
        self.a_ba.setToolTip('Back to previous zoom')
        # FORWARD:
        self.a_fw = self.addAction(QIcon(':/action-redo.svg'), 'Forward', self.forward)
        self.a_fw.setToolTip('Forward to next zoom')

        self.addSeparator() #---------------------------------------------

        # PAN:
        self.a_pa = self.addAction(QIcon(':/move.svg'), 'Pan', self.pan)
        self.a_pa.setToolTip("Pan axes with left mouse button, zoom with right,\n"
        "pressing x / y / CTRL keys constrains to horizontal / vertical / diagonal movements.")
        self._actions['pan'] = self.a_pa
        self.a_pa.setCheckable(True)

        # ZOOM RECTANGLE:
        self.a_zo = self.addAction(QIcon(':/magnifying-glass.svg'), 'Zoom', self.zoom)
        self.a_zo.setToolTip("Zoom in / out to rectangle with left / right mouse button,\n"
        "pressing x / y keys constrains zoom to horizontal / vertical direction.")
        self._actions['zoom'] = self.a_zo
        self.a_zo.setCheckable(True)

        # FULL VIEW:
        self.a_fv = self.addAction(QIcon(':/fullscreen-enter.svg'), \
            'Zoom full extent', self.parent.plt_full_view)
        self.a_fv.setToolTip('Zoom to full extent')

        # LOCK ZOOM:
        self.a_lk = self.addAction(QIcon(':/lock-unlocked.svg'), \
                                   'Lock zoom', self.toggle_lock_zoom)
        self.a_lk.setCheckable(True)
        self.a_lk.setChecked(False)
        self.a_lk.setToolTip('Lock / unlock current zoom setting')

        # --------------------------------------
        self.addSeparator()
        # --------------------------------------

        # GRID:
        self.a_gr = self.addAction(QIcon(':/grid.svg'), 'Grid', self.toggle_grid)
        self.a_gr.setToolTip('Toggle Grid')
        self.a_gr.setCheckable(True)
        self.a_gr.setChecked(True)

        # REDRAW:
        #self.a_rd = self.addAction(QIcon(':/brush.svg'), 'Redraw', self.parent.redraw)
        #self.a_rd.setToolTip('Redraw Plot')

        # SAVE:
        self.a_sv = self.addAction(QIcon(':/save.svg'), 'Save', self.save_figure)
        self.a_sv.setToolTip('Save the figure')

        self.cb = fb.clipboard

        self.a_cb = self.addAction(QIcon(':/clipboard.svg'), 'To Clipboard', self.mpl2Clip)
        self.a_cb.setToolTip('Copy to clipboard in png format.')
        self.a_cb.setShortcut("Ctrl+C")

        # --------------------------------------
        self.addSeparator()
        # --------------------------------------

        if figureoptions is not None:
            self.a_op = self.addAction(QIcon(':/settings.svg'), 'Customize', self.edit_parameters)
            self.a_op.setToolTip('Edit curves line and axes parameters')

#        self.buttons = {}

        # Add the x,y location widget at the right side of the toolbar
        # The stretch factor is 1 which means any resizing of the toolbar
        # will resize this label instead of the buttons.
        if self.coordinates:
            self.locLabel = QLabel("", self)
            self.locLabel.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
            self.locLabel.setSizePolicy(
                QSizePolicy(QSizePolicy.Expanding,
                                  QSizePolicy.Ignored))
            labelAction = self.addWidget(self.locLabel)
            labelAction.setVisible(True)

        # reference holder for subplots_adjust window
        self.adj_window = None

    if figureoptions is not None:
        def edit_parameters(self):
            allaxes = self.canvas.figure.get_axes()
            if len(allaxes) == 1:
                axes = allaxes[0]
            else:
                titles = []
                for axes in allaxes:
                    title = axes.get_title()
                    ylabel = axes.get_ylabel()
                    label = axes.get_label()
                    if title:
                        fmt = "%(title)s"
                        if ylabel:
                            fmt += ": %(ylabel)s"
                        fmt += " (%(axes_repr)s)"
                    elif ylabel:
                        fmt = "%(axes_repr)s (%(ylabel)s)"
                    elif label:
                        fmt = "%(axes_repr)s (%(label)s)"
                    else:
                        fmt = "%(axes_repr)s"
                    titles.append(fmt % dict(title=title,
                                         ylabel=ylabel, label=label,
                                         axes_repr=repr(axes)))
                item, ok = QInputDialog.getItem(
                    self, 'Customize', 'Select axes:', titles, 0, False)
                if ok:
                    axes = allaxes[titles.index(six.text_type(item))]
                else:
                    return

            figureoptions.figure_edit(axes, self)

#    def mouse_move(self, event):
#        if not event.inaxes or not self._active:
#            if self._lastCursor != mplCursors.POINTER:
#                self.set_cursor(mplCursors.POINTER)
#                self._lastCursor = mplCursors.POINTER
#        else:
#            if self._active == 'ZOOM':
#                if self._lastCursor != mplCursors.SELECT_REGION:
#                    self.set_cursor(mplCursors.SELECT_REGION)
#                    self._lastCursor = mplCursors.SELECT_REGION
#                if self._xypress:
#                    x, y = event.x, event.y
#                    lastx, lasty, _, _, _, _ = self._xypress[0]
#                    self.draw_rubberband(event, x, y, lastx, lasty)
#            elif (self._active == 'PAN' and
#                  self._lastCursor != mplCursors.MOVE):
#                self.set_cursor(mplCursors.MOVE)
#
#                self._lastCursor = mplCursors.MOVE
#
#        if event.inaxes and event.inaxes.get_navigate():
#
#            try: s = event.inaxes.format_coord(event.xdata, event.ydata)
#            except ValueError: pass
#            except OverflowError: pass
#            else:
#                if len(self.mode):
#                    self.set_message('%s : %s' % (self.mode, s))
#                else:
#                    self.set_message(s)
#        else: self.set_message(self.mode)
    
    def home(self):
        """
        Reset zoom to default settings (defined by plotting widget).
        This method shadows `home()` inherited from NavigationToolbar.
        """
        self.push_current()
        self.sig_tx.emit({'sender':__name__, 'home':''}) # only the key is used by the slot
        self.parent.redraw()

#------------------------------------------------------------------------------
    def toggle_grid(self):
        """Toggle the grid and redraw the figure."""
        for ax in self.parent.fig.axes:
            if hasattr(ax, "is_twin"): # the axis is a twinx() system, suppress the gridlines
                ax.grid(False)
            else:
                ax.grid(self.a_gr.isChecked())#(self.grid)
        self.parent.pltCanv.draw() # don't use self.redraw()

#------------------------------------------------------------------------------
    def toggle_lock_zoom(self):
        """
        Toggle the lock zoom settings and save the plot limits in any case:
            when previously unlocked, settings need to be saved
            when previously locked, current settings can be saved without effect
        """
        self.parent.save_limits() # save limits in any case:
        self.lock_zoom = not self.lock_zoom
        if self.lock_zoom:
            self.a_lk.setIcon(QIcon(':/lock-locked.svg'))
            self.a_zo.setEnabled(False)
            self.a_pa.setEnabled(False)
            self.a_fv.setEnabled(False)
            self.a_ho.setEnabled(False)
        else:
            self.a_lk.setIcon(QIcon(':/lock-unlocked.svg'))
            self.a_zo.setEnabled(True)
            self.a_pa.setEnabled(True)
            self.a_fv.setEnabled(True)
            self.a_ho.setEnabled(True)
            
        self.sig_tx.emit({'sender':__name__, 'lock_zoom':self.lock_zoom})

#------------------------------------------------------------------------------
# =============================================================================
#     def enable_plot(self, state = None):
#         """
#         Toggle the enable button and setting and enable / disable all
#         buttons accordingly.
#         """
#         if state is not None:
#             self.enabled = state
#         else:
#             self.enabled = not self.enabled
#         if self.enabled:
#             self.a_en.setIcon(QIcon(':/circle-x.svg'))
#         else:
#             self.a_en.setIcon(QIcon(':/circle-check.svg'))
# 
#         self.a_ho.setEnabled(self.enabled)
#         self.a_ba.setEnabled(self.enabled)
#         self.a_fw.setEnabled(self.enabled)
#         self.a_pa.setEnabled(self.enabled)
#         self.a_zo.setEnabled(self.enabled)
#         self.a_fv.setEnabled(self.enabled)
#         self.a_lk.setEnabled(self.enabled)
#         self.a_gr.setEnabled(self.enabled)
#         #self.a_rd.setEnabled(self.enabled)
#         self.a_sv.setEnabled(self.enabled)
#         self.a_cb.setEnabled(self.enabled)
#         self.a_op.setEnabled(self.enabled)
# 
#         self.sig_tx.emit({'sender':__name__, 'enabled':self.enabled})
# 
# =============================================================================
#------------------------------------------------------------------------------
    def mpl2Clip(self):
        """
        Save current figure to temporary file and copy it to the clipboard.
        """
        try:
            if HAS_QT5:
                img = QImage(self.canvas.grab())
                self.cb.setImage(img)
            else:
                pixmap = QPixmap.grabWidget(self.canvas)
                self.cb.setPixmap(pixmap)
        except:
            logger.error('Error copying figure to clipboard:\n{0}'.format(sys.exc_info()))
