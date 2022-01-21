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
import sys
from pyfda.libs.pyfda_lib import cmp_version

# do not import matplotlib.pyplot - pyplot brings its own GUI, event loop etc!!!
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from matplotlib import rcParams
from matplotlib import lines
from matplotlib.pyplot import setp

try:
    MPL_CURS = True
    import mplcursors
    if cmp_version('matplotlib', '3.1') < 0:
        MPL_CURS = False
except ImportError:
    MPL_CURS = False
try:
    import matplotlib.backends.qt_editor.figureoptions as figureoptions
except ImportError:
    figureoptions = None

from pyfda.libs.compat import (
    QtCore, QtGui, QWidget, QLabel, pyqtSignal, QSizePolicy, QIcon, QImage, QVBoxLayout,
    QHBoxLayout, QInputDialog, FigureCanvas, NavigationToolbar, pyqtSlot, QtWidgets)

from pyfda import pyfda_rc
import pyfda.filterbroker as fb
from pyfda import qrc_resources  # contains all icons

import logging
logger = logging.getLogger(__name__)

# read user settings for linewidth, font size etc. and apply them to matplotlib
for key in pyfda_rc.mpl_rc:
    rcParams[key] = pyfda_rc.mpl_rc[key]


# ------------------------------------------------------------------------------
def stems(x, y, ax=None, label=None, mkr_fmt=None, **kwargs):
    """
    Provide a faster replacement for stem plots under matplotlib < 3.1.0 using
    vlines (= LineCollection). LineCollection keywords are supported.
    """
    # create a copy of the kwargs dict without 'bottom' key-value pair, provide
    # pop bottom from dict (defuault = 0), not compatible with vlines
    bottom = kwargs.pop('bottom', 0)
    ax.axhline(bottom, **kwargs)
    if cmp_version("matplotlib", "3.1.0") >= 0:
        ml, sl, bl = ax.stem(x, y, use_line_collection=True, bottom=bottom)
        setp(ml, **mkr_fmt)
        setp(bl, **kwargs)
        setp(sl, **kwargs)
    else:
        ax.vlines(x, y, bottom, label=label, **kwargs)
        scatter(x, y, ax=ax, label=label, mkr_fmt=mkr_fmt, **kwargs)

    if mkr_fmt['marker']:
        handle = (lines.Line2D([], [], **kwargs), lines.Line2D([], [], **mkr_fmt))
    else:
        handle = lines.Line2D([], [], **kwargs)
    return handle


def scatter(x, y, ax=None, label=None, mkr_fmt=None, **kwargs):
    """
    Create a copy of matplolibs scatter that can handle 'ms' and 'markersize' keys
    These keys are removed from the mkr_fmt dictionary and translated to s = ms * ms
    When neither ms nor markersize are provided, a default of ms = 10 is used.

    Return a handle to the scatter plot.
    """
    ms = max(mkr_fmt.get('ms', -1), mkr_fmt.get('markersize', -1))
    if ms == -1:
        ms = 10
    mkr_fmt_cp = {k: v for k, v in mkr_fmt.items() if k not in ['ms', 'markersize']}
    return ax.scatter(x, y, s=ms*ms, label=label, **mkr_fmt_cp)


def no_plot(x, y, ax=None, bottom=0, label=None, **kwargs):
    """
    Don't plot anything - needed for plot factory
    """
    pass


# ------------------------------------------------------------------------------
class MplWidget(QWidget):
    """
    Construct a subwidget consisting of a Matplotlib canvas and a subclassed
    NavigationToolbar.
    """

    def __init__(self, parent):
        super(MplWidget, self).__init__(parent)
        # Create the mpl figure and subplot (white bg, 100 dots-per-inch).
        # Construct the canvas with the figure:
        self.plt_lim = []  # define variable for x,y plot limits

        if cmp_version("matplotlib", "2.2.0") >= 0:
            self.fig = Figure(constrained_layout=True)
        else:
            self.fig = Figure()

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding,
                                  QSizePolicy.Expanding)

        # Needed for mouse modifiers (x,y, <CTRL>, ...):
        #    Key press events in general are not processed unless you
        #    "activate the focus of Qt onto your mpl canvas"
        # http://stackoverflow.com/questions/22043549/matplotlib-and-qt-mouse-press-event-key-is-always-none

        self.canvas.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.canvas.setFocus()

        self.canvas.updateGeometry()

        # Create a custom navigation toolbar, tied to the canvas and
        # initialize toolbar settings
        #
        self.mplToolbar = MplToolbar(self.canvas, self)
        self.mplToolbar.zoom_locked = False
        self.mplToolbar.cursor_enabled = False
        # self.mplToolbar.enable_plot(state = True)
        self.mplToolbar.sig_tx.connect(self.process_signals)
        layHToolbar = QHBoxLayout()
        layHToolbar.addWidget(self.mplToolbar, 1, QtCore.Qt.AlignLeft)
        layHToolbar.addStretch(1)

        # =============================================
        # Main plot widget layout
        # =============================================
        self.layVMainMpl = QVBoxLayout()
        self.layVMainMpl.addLayout(layHToolbar)
        self.layVMainMpl.addWidget(self.canvas)

        self.setLayout(self.layVMainMpl)

# ------------------------------------------------------------------------------
    @pyqtSlot(object)
    def process_signals(self, dict_sig):
        """
        Process sig
        """
#        if 'enabled' in dict_sig:
#            self.clear_disabled_figure(dict_sig['enabled'])
#        else:
        pass

# ------------------------------------------------------------------------------
    def save_limits(self):
        """
        Save x- and y-limits of all axes in self.limits when zoom is unlocked
        """
        if not self.mplToolbar.zoom_locked:
            for ax in self.fig.axes:
                self.limits = ax.axis()  # save old limits

# ------------------------------------------------------------------------------
    def redraw(self):
        """
        Redraw the figure with new properties (grid, linewidth)
        """
        # only execute when at least one axis exists -> tight_layout crashes otherwise
        if self.fig.axes:
            self.mplToolbar.cycle_draw_grid(cycle=False, axes=self.fig.axes)
            for ax in self.fig.axes:

                if self.mplToolbar.zoom_locked:
                    ax.axis(self.limits)  # restore old limits
                else:
                    self.limits = ax.axis()  # save old limits

#            try:
#                # tight_layout() crashes with small figure sizes
#               self.fig.tight_layout(pad = 0.1)
#            except(ValueError, np.linalg.linalg.LinAlgError):
#                logger.debug("error in tight_layout")
        self.canvas.draw()  # now (re-)draw the figure

# ------------------------------------------------------------------------------
#    def clear_disabled_figure(self, enabled):
#        """
#        Clear the figure when it is disabled in the mplToolbar
#        """
#        if not enabled:
#            self.fig.clf()
#            self.pltCanv.draw()
#        else:
#            self.redraw()

# ----------------------------------------------------------------------------
    def plt_full_view(self):
        """
        Zoom to full extent of data if axes is set to "navigationable"
        by the navigation toolbar
        """
        # Add current view limits to view history to enable "back to previous view"
        self.mplToolbar.push_current()
        for ax in self.fig.axes:
            if ax.get_navigate():
                ax.autoscale()
        self.redraw()

# ----------------------------------------------------------------------------
    def get_full_extent(self, ax, pad=0.0):
        """
        Get the full extent of axes system `ax`, including axes labels, tick
        labels and titles.

        Needed for inset plot in H(f)
        """
        # http://stackoverflow.com/questions/14712665/matplotlib-subplot-background-axes-face-labels-colour-or-figure-axes-coor
        # For text objects, we need to draw the figure first, otherwise the extents
        # are undefined.
        self.canvas.draw()
        items = ax.get_xticklabels() + ax.get_yticklabels()
        items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
        bbox = Bbox.union([item.get_window_extent() for item in items])
        return bbox.expanded(1.0 + pad, 1.0 + pad)

# ----------------------------------------------------------------------------
    def toggle_cursor(self):
        """
        Toggle the tracking cursor
        """
        if MPL_CURS:
            self.mplToolbar.cursor_enabled = not self.mplToolbar.cursor_enabled
            if self.mplToolbar.cursor_enabled:
                if hasattr(self, "cursors"):  # dangling references to old cursors?
                    for i in range(len(self.cursors)):
                        self.cursors[i].remove()         # yes, remove them!
                self.cursors = []
                for ax in self.fig.axes:
                    if ax.__class__.__name__ in {"AxesSubplot", "Axes3DSubplot"}:
                        self.cursors.append(mplcursors.cursor(ax, hover=True))
            else:
                for i in range(len(self.cursors)):
                    self.cursors[i].remove()

        # see https://stackoverflow.com/questions/59800059/how-to-use-two-mplcursors-simultaneously-for-a-scatter-plot-of-two-sets


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
    https://stackoverflow.com/questions/53099295/matplotlib-navigationtoolbar-advanced-figure-options

    Using Tool Manager
    https://matplotlib.org/3.1.1/gallery/user_interfaces/toolmanager_sgskip.html
    https://stackoverflow.com/questions/52971285/add-toolbar-button-icon-matplotlib

    """

    toolitems = ()  # remove original icons and actions
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
    # def __init__(self, canvas, parent, coordinates=True):

    sig_tx = pyqtSignal(object)  # general signal, containing a dict
    from pyfda.libs.pyfda_qt_lib import emit

    def _init_toolbar(self): pass  # needed for backward compatibility with mpl < 3.3

    # disable coordinate display when mplcursors is available
    if MPL_CURS:
        def set_message(self, msg): pass

    def __init__(self, canv, mpl_widget, *args, **kwargs):
        NavigationToolbar.__init__(self, canv, mpl_widget, *args, **kwargs)

        # self.canvas = canv
        self.mpl_widget = mpl_widget

    # --------------------------------------------------------------------------
    # ----  Construct Toolbar using QRC icons -------------------

        # ---------------------------------------------
        # ENABLE:
        # ---------------------------------------------
        self.a_en = self.addAction(QIcon(':/circle-check.svg'), 'Enable Update',
                                   self.enable_plot)
        self.a_en.setToolTip('Enable / disable plot')
        self.a_en.setCheckable(True)
        self.a_en.setChecked(True)
        self.a_en.setVisible(False)

        # self.addSeparator()

        # ---------------------------------------------
        # HOME:
        # ---------------------------------------------
        self.a_ho = self.addAction(QIcon(':/home.svg'), 'Home', self.home)
        self.a_ho.setToolTip('Reset zoom')
        # BACK:
        self.a_ba = self.addAction(QIcon(':/action-undo.svg'), 'Back', self.back)
        self.a_ba.setToolTip('Back to previous zoom')

        # ---------------------------------------------
        # FORWARD:
        # ---------------------------------------------
        self.a_fw = self.addAction(QIcon(':/action-redo.svg'), 'Forward', self.forward)
        self.a_fw.setToolTip('Forward to next zoom')

        # ---------------------------------------------
        self.addSeparator()
        # ---------------------------------------------

        # ---------------------------------------------
        # PAN:
        # ---------------------------------------------
        self.a_pa = self.addAction(QIcon(':/move.svg'), 'Pan', self.pan)
        self.a_pa.setToolTip(
            "Pan axes with left mouse button, zoom with right,\npressing x / y / CTRL "
            "keys constrains to horizontal / vertical / diagonal movements.")
        self._actions['pan'] = self.a_pa
        self.a_pa.setCheckable(True)

        # ---------------------------------------------
        # ZOOM RECTANGLE:
        # ---------------------------------------------
        self.a_zo = self.addAction(QIcon(':/magnifying-glass.svg'), 'Zoom', self.zoom)
        self.a_zo.setToolTip(
            "Zoom in / out to rectangle with left / right mouse button,\n"
            "pressing x / y keys constrains zoom to horizontal / vertical direction.")
        self._actions['zoom'] = self.a_zo
        self.a_zo.setCheckable(True)

        # ---------------------------------------------
        # FULL VIEW:
        # ---------------------------------------------
        self.a_fv = self.addAction(
            QIcon(':/fullscreen-enter.svg'),
            'Zoom full extent', self.mpl_widget.plt_full_view)
        self.a_fv.setToolTip('Zoom to full extent')

        # ---------------------------------------------
        # LOCK ZOOM:
        # ---------------------------------------------
        self.a_lk = self.addAction(QIcon(':/lock-unlocked.svg'),
                                   'Lock zoom', self.toggle_lock_zoom)
        self.a_lk.setCheckable(True)
        self.a_lk.setChecked(False)
        self.a_lk.setToolTip('Lock / unlock current zoom setting')

        # ---------------------------------------------
        # TRACKING CURSOR:
        # ---------------------------------------------
        if MPL_CURS:
            self.a_cr = self.addAction(QIcon(':/map-marker.svg'),
                                       'Cursor', self.mpl_widget.toggle_cursor)
            self.a_cr.setCheckable(True)
            self.a_cr.setChecked(False)
            self.a_cr.setToolTip('Tracking Cursor')

        # --------------------------------------
        self.addSeparator()
        # --------------------------------------

        # ---------------------------------------------
        # GRID:
        # ---------------------------------------------
        self.a_gr = self.addAction(
            QIcon(':/grid_coarse.svg'), 'Grid', self.cycle_draw_grid)
        self.a_gr.setToolTip('Cycle grid: Off / coarse / fine')
        self.a_gr_state = 2  # 0: off, 1: major, 2: minor

        # ---------------------------------------------
        # REDRAW:
        # ---------------------------------------------
        # self.a_rd = self.addAction(QIcon(':/brush.svg'), 'Redraw', self.mpl_widget.redraw)
        # self.a_rd.setToolTip('Redraw Plot')

        # --------------------------------------
        # SAVE:
        # --------------------------------------
        self.a_sv = self.addAction(QIcon(':/save.svg'), 'Save', self._save_figure)
        self.a_sv.setToolTip('<span>Save the figure in various file formats. '
                             'Press &lt;ALT&gt; to hide title.</span>')
        self.cb = fb.clipboard

        # --------------------------------------
        # Copy to clipboard:
        # --------------------------------------
        self.a_cb = self.addAction(
            QIcon(':/clipboard.svg'), 'To Clipboard', self.mpl2Clip)
        self.a_cb.setToolTip(
            '<span>Copy figure to clipboard in png format.'
            '<ul><li>Press &lt;ALT&gt; to hide title.</li>'
            '<li>Press &lt;SHIFT&gt; for base64 '
            'encoded png format (e.g. for Jupyter Notebooks).</li> '
            '<li>Press &lt;CTRL&gt; to '
            'embed base64 encoded PNG in &lt;img&gt; tag.</li></ul></span>')
        self.a_cb.setShortcut("Ctrl+C")

        # --------------------------------------
        self.addSeparator()
        # --------------------------------------

        # --------------------------------------
        # SETTINGS:
        # --------------------------------------
        if figureoptions is not None:
            self.a_op = self.addAction(
                QIcon(':/settings.svg'), 'Customize', self.edit_parameters)
            self.a_op.setToolTip('Edit curves line and axes parameters')

#        self.buttons = {}

        # --------------------------------------
        # PRINT COORDINATES (only when mplcursors is not available):
        # --------------------------------------
        # Add the x,y location widget at the right side of the toolbar
        # The stretch factor is 1 which means any resizing of the toolbar
        # will resize this label instead of the buttons.
        # --------------------------------------
        if not MPL_CURS and self.coordinates:
            self.addSeparator()
            self.locLabel = QLabel("", self)
            self.locLabel.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
            self.locLabel.setSizePolicy(
                QSizePolicy(QSizePolicy.Expanding,
                            QSizePolicy.Ignored))
            labelAction = self.addWidget(self.locLabel)
            labelAction.setVisible(True)

        # ---------------------------------------------
        # HELP:
        # ---------------------------------------------
        self.a_he = self.addAction(QIcon(':/help.svg'), 'help', self.help)
        self.a_he.setToolTip('Open help page from https://pyfda.rtfd.org in browser')
        self.a_he.setDisabled(True)

# ------------------------------------------------------------------------------
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
                    titles.append(
                        fmt % dict(title=title, ylabel=ylabel, label=label,
                                   axes_repr=repr(axes)))
                item, ok = QInputDialog.getItem(
                    self, 'Customize', 'Select axes:', titles, 0, False)
                if ok:
                    axes = allaxes[titles.index(str(item))]
                else:
                    return

            figureoptions.figure_edit(axes, self)

# ------------------------------------------------------------------------------
    def home(self):
        """
        Reset zoom to default settings (defined by plotting widget).
        This method shadows `home()` inherited from NavigationToolbar.
        """
        self.push_current()
        self.emit({'home': ''})  # only the key is used by the slot
        self.mpl_widget.redraw()

# ------------------------------------------------------------------------------
    def help(self):
        """
        Open help page from https://pyfda.rtfd.org in browser
        """

        url = QtCore.QUrl('https://pyfda.readthedocs.io/en/latest/' + self.a_he.info)
        if not url.isValid():
            logger.warning("Invalid URL\n\t{0}\n\tOpening "
                           "'https://pyfda.readthedocs.io/en/latest/' instead".format(url.toString()))
            url = QtCore.QUrl('https://pyfda.readthedocs.io/en/latest/')
            # if url.isLocalFile()
        QtGui.QDesktopServices.openUrl(url)

        # https://stackoverflow.com/questions/28494571/how-in-qt5-to-check-if-url-is-available
        # https://stackoverflow.com/questions/16778435/python-check-if-website-exists

# ------------------------------------------------------------------------------
    def cycle_draw_grid(self, cycle=True, axes=None):
        """
        Cycle the grid of all axes through the states 'off', 'coarse' and 'fine'
        and redraw the figure.

        Parameters
        ----------
        cycle : bool, optional
            Cycle the grid display and redraw the canvas in the end when True.
            When false, only restore the grid settings.
        axes : matplotlib axes, optional
            When none is passed, use local `self.mpl_widget.fig.axes`

        Returns
        -------
        None.

        """

        if cycle:
            self.a_gr_state = (self.a_gr_state + 1) % 3

        if not axes:
            axes = self.mpl_widget.fig.axes

        for ax in self.mpl_widget.fig.axes:
            if hasattr(ax, "is_twin"):  # the axis is a twinx() system, suppress the gridlines
                ax.grid(False)
            else:
                if self.a_gr_state == 0:
                    ax.grid(False, which='both')

                    self.a_gr.setIcon(QIcon(':/grid_none.svg'))
                elif self.a_gr_state == 1:
                    ax.grid(True, which='major', lw=0.75, ls='-')
                    ax.grid(False, which='minor')
                    self.a_gr.setIcon(QIcon(':/grid_coarse.svg'))
                else:
                    ax.grid(True, which='major', lw=0.75, ls='-')
                    ax.grid(True, which='minor')
                    self.a_gr.setIcon(QIcon(':/grid_fine.svg'))

        if cycle:
            self.canvas.draw()  # don't use self.draw(), use FigureCanvasQTAgg.draw()

# ------------------------------------------------------------------------------
    def toggle_lock_zoom(self):
        """
        Toggle the lock zoom settings and save the plot limits in any case:
            when previously unlocked, settings need to be saved
            when previously locked, current settings can be saved without effect
        """
        self.mpl_widget.save_limits()  # save limits in any case:
        self.zoom_locked = not self.zoom_locked
        if self.zoom_locked:
            self.a_lk.setIcon(QIcon(':/lock-locked.svg'))
            if self.a_zo.isChecked():
                self.a_zo.trigger()  # toggle off programmatically
            self.a_zo.setEnabled(False)

            if self.a_pa.isChecked():
                self.a_pa.trigger()  # toggle off programmatically
            self.a_pa.setEnabled(False)

            self.a_fv.setEnabled(False)
            self.a_ho.setEnabled(False)
        else:
            self.a_lk.setIcon(QIcon(':/lock-unlocked.svg'))
            self.a_zo.setEnabled(True)
            self.a_pa.setEnabled(True)
            self.a_fv.setEnabled(True)
            self.a_ho.setEnabled(True)

        self.emit({'lock_zoom': self.zoom_locked})

# ------------------------------------------------------------------------------
    def enable_plot(self, state=None):
        """
        Toggle the enable button and setting
        """
        if state is not None:
            self.enabled = state
        else:
            self.enabled = not self.enabled

        if self.enabled:
            self.a_en.setIcon(QIcon(':/circle-check.svg'))
        else:
            self.a_en.setIcon(QIcon(':/circle-x.svg'))

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
#         self.emit({'enabled':self.enabled})
#
# =============================================================================
# ------------------------------------------------------------------------------
    def _save_figure(self):
        """
        Save current figure using matplotlib's `save_figure()`. When <ALT> key is
        pressed, remove the title before saving.
        """
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.AltModifier:
            title = self.mpl_widget.fig.get_axes()[0].get_title()  # store title text
            self.mpl_widget.fig.get_axes()[0].set_title("")  # and remove it from plot
            self.canvas.draw()  # redraw plot without title
            self.save_figure()
            self.mpl_widget.fig.get_axes()[0].set_title(title)  # restore title
            self.canvas.draw()  # and redraw once more
        else:
            self.save_figure()

# ------------------------------------------------------------------------------
    def mpl2Clip(self):
        """
        Copy current figure to the clipboard, either directly as PNG file or as
        base64 encoded PNG file.

        Qt.ShiftModifier = 0x02000000 # Shift key pressed
        Qt.ControlModifier = 0x04000000 # Control key
        Qt.AltModifier   = 0x08000000 # Alt key
        Qt.MetaModifier  = 0x10000000 # Meta key
        """
        try:
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            title_info = ""
            if modifiers & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier:
                # logger.warning(f"suptitle {self.mpl_widget.fig._suptitle.get_text()}")
                modifiers = modifiers & ~QtCore.Qt.AltModifier  # blank out AltMod. bit
                title_info = "(no title) "
                title = self.mpl_widget.fig.get_axes()[0].get_title()  # store title text
                self.mpl_widget.fig.get_axes()[0].set_title("")  # and remove it from plot
                self.canvas.draw()  # redraw plot without title
                img = QImage(self.canvas.grab())  # and grab it
                self.mpl_widget.fig.get_axes()[0].set_title(title)  # restore title
                self.canvas.draw()  # and redraw once more
            else:
                img = QImage(self.canvas.grab())  # grab original screen

            if modifiers in {QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier}:
                ba = QtCore.QByteArray()
                buffer = QtCore.QBuffer(ba)  # create buffer of ByteArray
                buffer.open(QtCore.QIODevice.WriteOnly)  # ... open it
                img.save(buffer, 'PNG')  # ... save image data to buffer
                # ... convert to base64 bytes -> str -> strip b' ... '
                base64_str = str(ba.toBase64().data()).lstrip("b'").rstrip("'")
                # ... and copy as string to clipboard after removing b' ... '
                if modifiers == QtCore.Qt.ShiftModifier:
                    self.cb.setText(base64_str)
                    logger.info(
                        f'Copied plot {title_info}as base64 encoded PNG image '
                        'to Clipboard.')
                elif modifiers == QtCore.Qt.ControlModifier:
                    self.cb.setText(
                        '<img src="data:image/png;base64,' + base64_str + '"/>')
                    logger.info(f'Copied plot {title_info}as base64 encoded PNG image '
                                'with <img> tag to Clipboard.')
                # elif modifiers == (QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier):
                #     logger.warning('Control+Shift+Click')
            else:
                self.cb.setImage(img)
                logger.info(f'Copied plot {title_info}as PNG image to Clipboard.')
        except:
            logger.error('Error copying figure to clipboard:\n{0}'.format(sys.exc_info()))
