# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with various helper functions for Qt widgets
"""
from .pyfda_lib import qstr, pprint_log

from .compat import (
    Qt, QtGui, QtCore, QFrame, QMessageBox, QPushButton, QLabel, QComboBox, QDialog,
    QFont, QSize, QFontMetrics, QIcon)
from .pyfda_dirs import OS, OS_VER

import logging
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
def emit(self, dict_sig: dict = {}, sig_name: str = 'sig_tx') -> None:
    """
    Emit a signal `self.<sig_name>` (defined as a class attribute) with a
    dict `dict_sig` using Qt's `emit()`.
    - Add the keys `'id'` and `'class'` with id resp. class name of the calling
      instance if not contained in the dict
    - If key 'ttl' is in the dict and its value is less than one, terminate the
      signal. Otherwise, reduce the value by one.
    """
    if 'id' not in dict_sig:
        dict_sig.update({'id': id(self)})
    if 'class' not in dict_sig:
        dict_sig.update({'class': self.__class__.__name__})
    # Count down time-to-live counter and terminate the signal when ttl < 1
    if 'ttl' in dict_sig:
        if dict_sig['ttl'] < 1:
            return
        else:
            dict_sig.update({'ttl': dict_sig['ttl'] - 1})
    # Get signal (default name: `sig_tx`) from calling instance and emit it
    signal = getattr(self, sig_name)
    signal.emit(dict_sig)


# # ------------------------------------------------------------------------------
# def sig_loop(self, dict_sig: dict, logger, **kwargs) -> int:
#     """
#     Test whether the signal has been emitted by self, leading to a possible
#     infinite loop.
#     """
#     # if 'id' not in dict_sig:
#     #     if kwargs:
#     #         logger.error("id missing in {0}\n{1}"
#     #                      .format(pprint_log(dict_sig), pprint_log(kwargs)))
#     #     else:
#     #         logger.error(f"id missing in {pprint_log(dict_sig)}")
#     #     return 0

#     if dict_sig['id'] == id(self):
#         if kwargs:
#             logger.warning("Stopped infinite loop:\n{0}\n{1}"
#                            .format(pprint_log(dict_sig), pprint_log(kwargs)))
#         else:
#             logger.warning(f"Stopped infinite loop:\n{pprint_log(dict_sig)}")
#         return 1
#     else:
#         return -1


# ------------------------------------------------------------------------------
def qwindow_stay_on_top(win: QDialog, top: bool) -> None:
    """
    Set flags for a window such that it stays on top (True) or not

    On Windows 7 the new window stays on top anyway.
    Additionally setting WindowStaysOnTopHint blocks the message window when
    trying to close pyfda.

    On Windows 10 and Linux, `WindowStaysOnTopHint` needs to be set.
    """

    win_flags = (Qt.CustomizeWindowHint | Qt.Window |  # always needed
                 Qt.WindowTitleHint |  # show title bar, make window movable
                 Qt.WindowCloseButtonHint |  # show close button
                 Qt.WindowContextHelpButtonHint |  # right Mousebutton context menu
                 Qt.WindowMinMaxButtonsHint)  # show min/max buttons

    if OS == "Windows" and OS_VER in {'XP', '7', 'Vista', '2008Server'} or not top:
        win.setWindowFlags(win_flags)
    else:
        win.setWindowFlags(win_flags | Qt.WindowStaysOnTopHint)


# ------------------------------------------------------------------------------
def qcmb_box_populate(cmb_box: QComboBox, items_list: list, item_init: str) -> None:
    """
    Clear and populate combo box `cmb_box` with text, data and tooltip from the list
    `items_list` with initial selection of `init_item` (data).

    Text and tooltip are prepared for translation via `self.tr()`

    Parameters
    ----------

    cmb_box: instance of QComboBox
        Combobox to be populated

    items_list: list
        List of combobox entries, in the format
        [ "Tooltip for Combobox", # [optional]
         ("data 1st item", "text 1st item", "tooltip for 1st item" # [optional]),
         ("data 2nd item", "text 2nd item", "tooltip for 2nd item")]

    item_init: str
        data for initial positition of combobox. When data is not found,
        set combobox to first item.

    Returns
    -------
    None
    """
    cmb_box.clear()
    if type(items_list[0]) is str:  # combo box tool tipp (optional)
        cmb_box.setToolTip(cmb_box.tr(items_list[0]))
    for i in range(1, len(items_list)):
        if type(items_list[i][1]) == QtGui.QIcon:
            cmb_box.addItem("", items_list[i][0])
            cmb_box.setItemIcon(i-1, items_list[i][1])
            # cmb_box.setItemData(i-1, items_list[i][0])
        else:
            cmb_box.addItem(cmb_box.tr(items_list[i][1]), items_list[i][0])
        if len(items_list[i]) == 3:  # add item tool tip (optional)
            cmb_box.setItemData(i-1, cmb_box.tr(items_list[i][2]), Qt.ToolTipRole)
    qset_cmb_box(cmb_box, item_init, data=True)

    """ icon = QIcon('logo.png')
    # adding icon to the given index
    self.combo_box.setItemIcon(i, icon)
    size = QSize(10, 10)
    self.combo_box.setIconSize(size)  """


# ------------------------------------------------------------------------------
def qget_cmb_box(cmb_box: QComboBox, data: bool = True) -> str:
    """
    Get current itemData or Text of comboBox and convert it to string.

    In Python 3, python Qt objects are automatically converted to QVariant
    when stored as "data" e.g. in a QComboBox and converted back when
    retrieving. In Python 2, QVariant is returned when itemData is retrieved.
    This is first converted from the QVariant container format to a
    QString, next to a "normal" non-unicode string.

    Returns:

    The current text or data of combobox as a string
    """
    if data:
        idx = cmb_box.currentIndex()
        cmb_data = cmb_box.itemData(idx)
        cmb_str = qstr(cmb_data)  # convert QVariant, QString, string to plain string
    else:
        cmb_str = cmb_box.currentText()

    cmb_str = str(cmb_str)

    return cmb_str


# ------------------------------------------------------------------------------
def qset_cmb_box(cmb_box: QComboBox, string: str, data: bool = False,
                 fireSignals: bool = False, caseSensitive: bool = False) -> int:
    """
    Set combobox to the index corresponding to `string` in a text field (`data = False`)
    or in a data field (`data=True`). When `string` is not found in the combobox entries,
    select the first entry. Signals are blocked during the update of the combobox unless
    `fireSignals` is set `True`. By default, the search is case insensitive, this
    can be changed by passing `caseSensitive=False`.

    Parameters
    ----------

    string: str
        The label in the text or data field to be selected. When the string is
        not found, select the first entry of the combo box.

    data: bool (default: False)
        Whether the string refers to the data or text fields of the combo box

    fireSignals: bool (default: False)
        When True, fire a signal if the index is changed (useful for GUI testing)

    caseSensitive: bool (default: False)
        When true, perform case sensitive search.

    Returns
    -------
        The index of the string. When the string was not found in the combo box,
        select first entry of combo box and return index -1.
    """
    sig_blocked_old = cmb_box.signalsBlocked()

    if caseSensitive:
        flag = Qt.MatchFixedString | Qt.MatchCaseSensitive
    else:
        flag = Qt.MatchFixedString  # string based matching (case insensitive)

    # Other more or less self explanatory flags:
    # MatchExactly (default), MatchContains, MatchStartsWith, MatchEndsWith,
    # MatchRegExp, MatchWildcard, MatchRecursive
    if data:
        idx = cmb_box.findData(str(string), flags=flag)  # find index for data == string
    else:
        idx = cmb_box.findText(str(string), flags=flag)  # find index for text == string

    ret = idx

    # if idx == old_idx:
    #     return -2

    cmb_box.blockSignals(not fireSignals)
    if idx == -1:  # string hasn't been found
        cmb_box.setCurrentIndex(0)  # set index to first entry
    else:
        cmb_box.setCurrentIndex(idx)  # set index as found in combobox
    cmb_box.blockSignals(sig_blocked_old)

    return ret


# -----------------------------------------------------------------------------
def qcmb_box_del_item(cmb_box: QComboBox, string: str, data: bool = False,
                      fireSignals: bool = False, caseSensitive: bool = False) -> int:
    """
    Try to find the entry in combobox corresponding to `string` in a text field
    (`data = False`) or in a data field (`data=True`) and delete the item. When `string`
    is not found,do nothing. Signals are blocked during the update of the combobox unless
    `fireSignals` is set `True`. By default, the search is case insensitive, this
    can be changed by passing `caseSensitive=False`.

    Parameters
    ----------

    string: str
        The label in the text or data field to be deleted.

    data: bool (default: False)
        Whether the string refers to the data or text fields of the combo box

    fireSignals: bool (default: False)
        When True, fire a signal if the index is changed (useful for GUI testing)

    caseInsensitive: bool (default: False)
        When true, perform case sensitive search.

    Returns
    -------
        The index of the item with string / data. When not found in the combo box,
        return index -1.
    """
    sig_blocked_old = cmb_box.signalsBlocked()

    if caseSensitive:
        flag = Qt.MatchFixedString | Qt.MatchCaseSensitive
    else:
        flag = Qt.MatchFixedString  # string based matching (case insensitive)

    # Other more or less self explanatory flags:
    # MatchExactly (default), MatchContains, MatchStartsWith, MatchEndsWith,
    # MatchRegExp, MatchWildcard, MatchRecursive

    if data:
        idx = cmb_box.findData(str(string), flags=flag)  # find index for data == string
    else:
        idx = cmb_box.findText(str(string), flags=flag)  # find index for text == string

    if idx > -1:  # data  / text exists in combo box, delete it.
        cmb_box.blockSignals(not fireSignals)
        cmb_box.removeItem(idx)  # set index
        cmb_box.blockSignals(sig_blocked_old)

    return idx


# ----------------------------------------------------------------------------
def qcmb_box_add_item(cmb_box, item_list, data=True, fireSignals=False,
                      caseSensitive=False):
    """
    Add an entry in combobox with text / data / tooltipp from `item_list`.
    When the item is already in combobox (searching for data or text item, depending
    `data`), do nothing. Signals are blocked during the update of the combobox unless
    `fireSignals` is set `True`. By default, the search is case insensitive, this
    can be changed by passing `caseSensitive=False`.

    Parameters
    ----------

    item_list: list
        List with `["new_data", "new_text", "new_tooltip"]` to be added.

    data: bool (default: False)
        Whether the string refers to the data or text fields of the combo box

    fireSignals: bool (default: False)
        When True, fire a signal if the index is changed (useful for GUI testing)

    caseInsensitive: bool (default: False)
        When true, perform case sensitive search.

    Returns
    -------
        The index of the found item with string / data. When not found in the
        combo box, return index -1.
    """
    if caseSensitive:
        flag = Qt.MatchFixedString | Qt.MatchCaseSensitive
    else:
        flag = Qt.MatchFixedString  # string based matching (case insensitive)

    # Other more or less self explanatory flags:
    # MatchExactly (default), MatchContains, MatchStartsWith, MatchEndsWith,
    # MatchRegExp, MatchWildcard, MatchRecursive

    if data:
        idx = cmb_box.findData(item_list[0], flags=flag)  # find index for data
    else:
        idx = cmb_box.findText(item_list[1], flags=flag)  # find index for text

    if idx == -1:  # data  / text doesn't exist in combo box, add it.
        cmb_box.blockSignals(not fireSignals)
        cmb_box.addItem(cmb_box.tr(item_list[1]), item_list[0])  # set index
        idx = cmb_box.findData(item_list[0])
        cmb_box.setItemData(idx, cmb_box.tr(item_list[2]), Qt.ToolTipRole)
        cmb_box.blockSignals(False)

    return idx


# ------------------------------------------------------------------------------
def qstyle_widget(widget, state):
    """
    Apply the "state" defined in pyfda_rc.py to the widget, e.g.:
    Color the >> DESIGN FILTER << button according to the filter design state.

    This requires settinng the property, "unpolishing" and "polishing" the widget
    and finally forcing an update.

    - "normal": default, no color styling
    - "ok":  green, filter has been designed, everything ok
    - "changed": yellow, filter specs have been changed
    - "running": orange, simulation is running
    - "error" : red, an error has occurred during filter design
    - "failed" : pink, filter fails to meet target specs (not used yet)
    - "u" or "unused": grey text color
    - "d" or "disabled": background color darkgrey
    - "a" or "active": no special style defined
    """
    state = str(state)
    if state == 'u':
        state = "unused"
        # *[state="unused"], *[state="u"]{background-color:white; color:darkgrey}
    elif state == 'a':
        state = "active"
    elif state == 'd':
        state = "disabled"
        # QLineEdit:disabled{background-color:darkgrey;}
    widget.setProperty("state", state)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


# ----------------------------------------------------------------------------
def qget_selected(table, select_all=False, reverse=True):
    """
    Get selected cells in ``table`` and return a dictionary with the following keys:

    'idx': indices of selected cells as an unsorted list of tuples

    'sel': list of lists of selected cells per column, by default sorted in reverse

    'cur':  current cell selection as a tuple

    Parameters
    ----------

    select_all : bool
        select all table items and create a list when True

    reverse : bool
        return selected fields upside down when True
    """
    if select_all:
        table.selectAll()

    idx = []
    for _ in table.selectedItems():
        idx.append([_.column(), _.row(), ])

    sel = [[], []]
    sel[0] = sorted([i[1] for i in idx if i[0] == 0], reverse=reverse)
    sel[1] = sorted([i[1] for i in idx if i[0] == 1], reverse=reverse)

    if select_all:
        table.clearSelection()

    # use set comprehension to eliminate multiple identical entries
    # cols = sorted(list({i[0] for i in idx}))
    # rows = sorted(list({i[1] for i in idx}))
    cur = (table.currentColumn(), table.currentRow())
    # cur_idx_row = table.currentIndex().row()
    return {'idx': idx, 'sel': sel, 'cur': cur}  # 'rows':rows 'cols':cols, }


# ----------------------------------------------------------------------------
def qfilter_warning(self, N, fil_class):
    """
    Pop-up a warning box for very large filter orders
    """
    reply = QMessageBox.warning(
        self, 'Warning',
        ("<span><i><b>N = {0}</b></i> &nbsp; is a rather high order for<br />"
         "an {1} filter and may cause large <br />"
         "numerical errors and compute times.<br />"
         "Continue?</span>".format(N, fil_class)),
        QMessageBox.Yes, QMessageBox.No)
    if reply == QMessageBox.Yes:
        return True
    else:
        return False


# ----------------------------------------------------------------------------
def qtext_width(text: str = '', N_x: int = 17, bold: bool = True, font=None) -> int:
    """
    Calculate width of `text` in points`. When `text=``, calculate the width
    of number `N_x` of characters 'x'.

    The actual width of the string is calculated by creating a
    QTextDocument with the passed text and retrieving its `idealWidth()`

    Parameters
    ----------

    test: str
        string to calculate the width for

    N_x: int
        When `text == ''`, calculate the width from `N_x * width('x')`

    bold: bool (default: True)
        When `True`, determine width based on bold font

    Returns
    -------

    width: int
        The width of the text in points

    Notes
    -----
    This is based on
    https://stackoverflow.com/questions/27433165/how-to-reimplement-sizehint-for-bold-text-in-a-delegate-qt

    and

    https://stackoverflow.com/questions/47285303/how-can-i-limit-text-box-width-of-
    #    qlineedit-to-display-at-most-four-characters/47307180#47307180

    """
    if text == '':
        text = "x" * N_x

    if font is None:
        font = QFont()
    if bold:
        font.setBold(True)

    document = QtGui.QTextDocument(text)
    document.setDefaultFont(font)
    width = int(document.idealWidth())

    return width


# ----------------------------------------------------------------------------
def qtext_height(text: str = 'X', font=None) -> int:
    """
    Calculate size of `text` in points`.

    The actual size of the string is calculated using fontMetrics and the default
    or the passed font

    Parameters
    ----------

    test: str
        string to calculate the height for (default: "X")

    Returns
    -------

    lineSpacing: int
        The height of the text (line spacing) in points

    Notes
    -----
    This is based on
    https://stackoverflow.com/questions/27433165/how-to-reimplement-sizehint-for-bold-text-in-a-delegate-qt

    and

    https://stackoverflow.com/questions/47285303/how-can-i-limit-text-box-width-of-
    #    qlineedit-to-display-at-most-four-characters/47307180#47307180

    https://stackoverflow.com/questions/56282199/fit-qtextedit-size-to-text-size-pyqt5

    """
    if font is None:
        font = QFont()

    fm = QFontMetrics(font)

    return fm.lineSpacing()

    # width_frm = wdg.textMargins().left() + wdg.textMargins().right() +\
    #     wdg.contentsMargins().left() + wdg.contentsMargins().left() +\
    #     8  # 2 * horizontalMargin() + 2 * frame margin.

    # fm = QFontMetrics(loggerWin.font())
    # row4_height = fm.lineSpacing() * 4
    # fm_size = fm.size(0, text)


# ----------------------------------------------------------------------------
class QHLine(QFrame):
    """
    Create a thin horizontal line utilizing the HLine property of QFrames
    Usage:
        myline = QHLine()
        mylayout.addWidget(myline)
    """
    def __init__(self, width=1):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(width)


class QVLine(QFrame):
    def __init__(self, width=2):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Plain)
        # self.setStyleSheet('border-color: rgb(50,50,50)')
        # self.setFrameShadow(QFrame.Sunken)
        # self.setLineWidth(width)
        # self.setFrameShape(QFrame.StyledPanel);
        self.setStyleSheet(
            f"border-width: {str(width)}px; border-top-style: none; "
            "border-right-style: none; border-bottom-style: none; "
            "border-left-style: solid; border-color: grey;")


class PushButton(QPushButton):
    """
    Create a QPushButton with a width fitting the label with bold font as well

    Parameters
    ----------
    txt : str
        Text for button (optional)

    icon : QIcon
        Icon for button. Either `txt` or `icon` must be defined.

    N_x : int
        Width in number of "x"

    checkable : bool
        Whether button is checkable

    checked : bool
        Whether initial state is checked
    """
    def __init__(self, txt: str = "", icon: QIcon = None, N_x: int = 8,
                 checkable: bool = True, checked: bool = False):
        super(PushButton, self).__init__()

        self.setCheckable(checkable)
        self.setChecked(checked)
        if icon is None:
            self.w = qtext_width(text=txt, N_x=N_x, font=self.font())
            self.h = super(PushButton, self).sizeHint().height()
            self.setText(txt.strip())
        else:
            self.setIcon(icon)
            # use sizeHint of parent
            self.w = super(PushButton, self).sizeHint().width()
            self.h = super(PushButton, self).sizeHint().height()

    def sizeHint(self) -> QtCore.QSize:
        return QSize(self.w, self.h)

    def minimumSizeHint(self) -> QtCore.QSize:
        return QSize(self.w, self.h)


class RotatedButton(QPushButton):
    """
    Create a rotated QPushButton

    Taken from

    https://forum.qt.io/topic/9279/moved-how-to-rotate-qpushbutton-63/7
    """

    def init(self, text, parent, orientation="west"):
        super(RotatedButton, self).init(text, parent)
        self.orientation = orientation

    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        painter.rotate(90)
        painter.translate(0, -1 * self.width())
        painter.drawControl(QtGui.QStyle.CE_PushButton, self.getSyleOptions())

    def minimumSizeHint(self):
        size = super(RotatedButton, self).minimumSizeHint()
        size.transpose()
        return size

    def sizeHint(self):
        size = super(RotatedButton, self).sizeHint()
        size.transpose()
        return size

    def getSyleOptions(self):
        options = QtGui.QStyleOptionButton()
        options.initFrom(self)
        size = options.rect.size()
        size.transpose()
        options.rect.setSize(size)
        # options.features = QtGui.QStyleOptionButton.None
        if self.isFlat():
            options.features |= QtGui.QStyleOptionButton.Flat
        if self.menu():
            options.features |= QtGui.QStyleOptionButton.HasMenu
        if self.autoDefault() or self.isDefault():
            options.features |= QtGui.QStyleOptionButton.AutoDefaultButton
        if self.isDefault():
            options.features |= QtGui.QStyleOptionButton.DefaultButton
        if self.isDown() or (self.menu() and self.menu().isVisible()):
            options.state |= QtGui.QStyle.State_Sunken
        if self.isChecked():
            options.state |= QtGui.QStyle.State_On
        if not self.isFlat() and not self.isDown():
            options.state |= QtGui.QStyle.State_Raised

        options.text = self.text()
        options.icon = self.icon()
        options.iconSize = self.iconSize()
        return options


class QLabelVert(QLabel):
    """
    Create a vertical label

    Adapted from
    https://pyqtgraph.readthedocs.io/en/latest/_modules/pyqtgraph/widgets/VerticalLabel.html

    https://stackoverflow.com/questions/34080798/pyqt-draw-a-vertical-label

    check https://stackoverflow.com/questions/29892203/draw-rich-text-with-qpainter
    """

    def __init__(self, text, orientation='west', forceWidth=True):
        QLabel.__init__(self, text)
        # self.forceWidth = forceWidth
        self.orientation = orientation
        # self.setOrientation(orientation)

    # def setOrientation(self, o):
    #     self.orientation = o
    #     self.update()
    #     self.updateGeometry()

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        # p.setPen(QtCore.Qt.black)
        p.rotate(-90)
        rgn = QtCore.QRect(-self.height(), 0, self.height(), self.width())
        # align = self.alignment()  # use alignment of original widget
        align = QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter
        # p.translate(0, -1 * self.width())

        # Draw plain text in `rgn` with alignment `align`
        self.hint = p.drawText(rgn, align, self.text())
        p.drawText(rgn, align, self.text())  # returns (height, width)
        # p.drawControl()
        p.end()

    def sizeHint(self):
        # if hasattr(self, 'hint'):
        #     return QSize(self.hint.height(), self.hint.width())
        # else:
        #     return QSize(19, 50)
        size = super(QLabelVert, self).sizeHint()
        size.transpose()
        return size

    def minimumSizeHint(self):
        size = super(QLabelVert, self).minimumSizeHint()
        size.transpose()
        return size

# ==============================================================================


if __name__ == '__main__':
    pass
