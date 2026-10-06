# -*- coding: utf-8 -*-
#
# This file is part of the pyfda project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyfda Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Library with various Qt classes used in pyfda.
"""
import logging

from pyfda.libs.pyfda_qt_lib import qstyle_widget
from pyfda.libs.compat import (
    Qt, QtGui, QtCore, QFrame, QPushButton, QLabel, QtWidgets,
    QSizePolicy, QIcon, QEvent, QHBoxLayout)

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
class EventTypes:
    """
    https://stackoverflow.com/questions/62196835/how-to-get-string-name-for-qevent-in-pyqt5
    Events in Qt5: https://doc.qt.io/qt-5/qevent.html

    Stores a string name for each event type.

    With PySide2 str() on the event type gives a nice string name,
    but with PyQt5 it does not. So this method works with both systems.

    Example usage (simultaneous initialization and method call / translation)
    > event_str = EventTypes().as_string(QEvent.UpdateRequest)
    > assert event_str == "UpdateRequest"

    Example usage, separate initialization and method call
    > event types = EventTypes()
    > event_str = event_types.as_string(event.type())
    """

    def __init__(self):
        """Create mapping for all known event types."""
        self.string_name = {}
        for name in vars(QEvent):
            attribute = getattr(QEvent, name)
            if isinstance(attribute, QEvent.Type):
                self.string_name[attribute] = name

    def as_string(self, event: QEvent.Type) -> str:
        """Return the string name for this event."""
        try:
            return self.string_name[event]
        except KeyError:
            return f"UnknownEvent:{event}"

# ----------------------------------------------------------------------------
class QHLine(QFrame):
    """
    Create a thin horizontal line utilizing the HLine property of QFrames.

    Parameters
    ----------
    width : int, optional
        Line width in pixels (default: 1).

    Usage:

    > myline = QHLine()
    > mylayout.addWidget(myline)
    """
    def __init__(self, width=1):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(width)


class QVLine(QFrame):
    """
    Create a thin vertical line utilizing the HLine property of QFrames.

    Parameters
    ----------
    width : int, optional
        Border width in pixels (default: 2). The width controls the visual
        thickness of the vertical line.

    Usage:

    > myline = QVLine()
    > mylayout.addWidget(myline)
    """

    def __init__(self, width: int = 2):
        super().__init__()
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
    Convenience class for creating a checkable QPushButton with attribute `checked`
    that reflects the button state and can be styled via `style_button()`.

    When `rich_text=True`, a transparent QLabel is used inside the button so HTML/
    rich-text labels can be displayed without duplicating the toggle logic.

    Parameters
    ----------
    parent : QWidget, optional
        Parent widget of the button.

    text : str, optional
        Text for the button (default: empty string).

    icon : QIcon, optional
        Icon for button. Either `text` or `icon` must be defined.

    checkable : bool, optional
        Whether button is checkable (default: True).

    checked : bool, optional
        Whether initial state is checked (default: False).

    objectName : str, optional
        Object name to set on the widget (useful for styling and testing).

    rich_text : bool, optional
        If True, render the button text with a QLabel using rich text.

    pad : int, optional
        Left/right padding in pixels used when `rich_text=True`.

    **kwargs
        Additional keyword arguments forwarded to `QPushButton`.
    """

    def __init__(self, parent: QtWidgets.QWidget = None, text: str = "", icon: QIcon = None,
                 checkable: bool = True, checked: bool = False, objectName: str = "",
                 rich_text: bool = False, pad: int = 5, **kwargs):

        if parent is not None:
            super().__init__(parent, **kwargs)
        else:
            super().__init__(**kwargs)

        self.setObjectName(objectName)

        self.rich_text = bool(rich_text)
        self.lbl_rtf = None
        self.pad = pad

        if self.rich_text:
            self.lbl_rtf = QLabel(self)
            self.lbl_rtf.setText(text if text is not None else "")
            self.lbl_rtf.setAttribute(Qt.WA_TranslucentBackground)
            self.lbl_rtf.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.lbl_rtf.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.lbl_rtf.setTextFormat(Qt.RichText)
            self.lay_h_main = QHBoxLayout()
            self.lay_h_main.setContentsMargins(pad, 0, pad, 0)  # L, T, R, B
            self.lay_h_main.setSpacing(0)
            self.setLayout(self.lay_h_main)
            self.lay_h_main.addWidget(self.lbl_rtf, Qt.AlignHCenter)
        elif icon is None:
            super().setText(text.strip() if isinstance(text, str) else text)
        else:
            self.setIcon(icon)

        self.setCheckable(checkable)
        self._checkable = checkable
        if self._checkable:
            self.setChecked(checked)
            self._checked = checked
        else:
            self.setChecked(False)
            self._checked = False

        self.style_button()
        self.installEventFilter(self)

    def setText(self, text: str) -> None:
        """Set the text, using a rich-text label when enabled."""
        if self.rich_text and self.lbl_rtf is not None:
            self.lbl_rtf.setText(text)
            self.updateGeometry()
            return
        super().setText(text.strip() if isinstance(text, str) else text)

    def isChecked(self) -> bool:
        """Return the internal checked state of the button."""
        return self._checked

    def setChecked(self, checked: bool) -> None:
        """Set the checked state and update the visual style."""
        if self._checkable:
            self._checked = checked
            self.style_button()

    def setCheckable(self, checkable: bool) -> None:
        """Enable or disable the button's checkable behavior."""
        self._checkable = checkable
        if not self._checkable:
            self.setChecked(False)
            self._checked = False
            self.style_button()

    def eventFilter(self, source: QtCore.QObject, event: QEvent) -> bool:
        """Handle the check toggle on mouse press for checkable buttons."""
        if event.type() == QEvent.MouseButtonPress:
            if self.isEnabled() and self._checkable and event.button() == Qt.LeftButton:
                # signal is passed to base class where "self.toggle()" is performed
                self._checked = not self._checked
                self.style_button()
        return super().eventFilter(source, event)

    def style_button(self) -> None:
        """Apply the style for the normal and highlighted state."""
        if self._checked:
            qstyle_widget(self, "highlight")
            if self.lbl_rtf is not None:
                qstyle_widget(self.lbl_rtf, "highlight")
        else:
            qstyle_widget(self, "normal")
            if self.lbl_rtf is not None:
                qstyle_widget(self.lbl_rtf, "normal")

    def sizeHint(self) -> QtCore.QSize:
        """Return a size hint that includes the rich-text label padding."""
        s = super().sizeHint()
        if self.lbl_rtf is not None:
            w = self.lbl_rtf.sizeHint()
            s.setWidth(w.width() + 2 * self.pad)
        return s

    def minimumSizeHint(self) -> QtCore.QSize:
        """Return a minimum size hint that includes the rich-text label padding."""
        s = super().minimumSizeHint()
        if self.lbl_rtf is not None:
            w = self.lbl_rtf.sizeHint()
            s.setWidth(w.width() + 2 * self.pad)
        return s


class PushButtonRT(PushButton):
    """Backward-compatible rich-text button alias for existing call sites."""

    def __init__(self, parent: QtWidgets.QWidget = None, text: str = "", pad: int = 5,
                 checkable: bool = True, checked: bool = False, objectName: str = "",
                 **kwargs):
        super().__init__(
            parent=parent,
            text=text,
            checkable=checkable,
            checked=checked,
            objectName=objectName,
            rich_text=True,
            pad=pad,
            **kwargs,
        )


class RotatedButton(QPushButton):
    """
    ##### currently unused #####
    Create a rotated QPushButton

    Taken from

    https://forum.qt.io/topic/9279/moved-how-to-rotate-qpushbutton-63/7

    Parameters
    ----------
    text : str
        The text to display on the button.
    parent : QWidget
        The parent widget of the button.
    orientation : str, optional
        The orientation of the button, default is "west".
    """

    def init(self, text: str, parent: QtWidgets.QWidget, orientation: str = "west") -> None:

        super().init(text, parent)
        self.orientation = orientation

    def paintEvent(self, event: QEvent) -> None:
        """
        Handle the paint event to draw the rotated button.

        Parameters
        ----------
        event : QEvent
            The paint event to process.
        """
        painter = QtWidgets.QStylePainter(self)
        painter.rotate(90)
        painter.translate(0, -1 * self.width())
        painter.drawControl(QtWidgets.QStyle.CE_PushButton, self.getSyleOptions())

    def minimumSizeHint(self) -> QtCore.QSize:
        """
        Provide the minimum size hint for the rotated button.

        Returns
        -------
        QtCore.QSize
            The minimum size hint for the button.
        """
        size = super().minimumSizeHint()
        size.transpose()
        return size

    def sizeHint(self) -> QtCore.QSize:
        """
        Provide the size hint for the rotated button.

        Returns
        -------
        QtCore.QSize
            The recommended size for the button.
        """
        size = super().sizeHint()
        size.transpose()
        return size

    def getSyleOptions(self) -> QtWidgets.QStyleOptionButton:
        """
        Retrieve the style options for the rotated button.

        Returns
        -------
        QtWidgets.QStyleOptionButton
            The style options for the button.
        """
        options = QtWidgets.QStyleOptionButton()
        options.initFrom(self)
        size = options.rect.size()
        size.transpose()
        options.rect.setSize(size)
        # options.features = QtWidgets.QStyleOptionButton.None
        if self.isFlat():
            options.features |= QtWidgets.QStyleOptionButton.Flat
        if self.menu():
            options.features |= QtWidgets.QStyleOptionButton.HasMenu
        if self.autoDefault() or self.isDefault():
            options.features |= QtWidgets.QStyleOptionButton.AutoDefaultButton
        if self.isDefault():
            options.features |= QtWidgets.QStyleOptionButton.DefaultButton
        if self.isDown() or (self.menu() and self.menu().isVisible()):
            options.state |= QtWidgets.QStyle.State_Sunken
        if self.isChecked():
            options.state |= QtWidgets.QStyle.State_On
        if not self.isFlat() and not self.isDown():
            options.state |= QtWidgets.QStyle.State_Raised

        options.text = self.text()
        options.icon = self.icon()
        options.iconSize = self.iconSize()
        return options


class QLabelVert(QLabel):
    """
    ##### currently unused #####

    Create a vertical label.

    Adapted from
    https://pyqtgraph.readthedocs.io/en/latest/_modules/pyqtgraph/widgets/VerticalLabel.html

    https://stackoverflow.com/questions/34080798/pyqt-draw-a-vertical-label

    check https://stackoverflow.com/questions/29892203/draw-rich-text-with-qpainter

    Parameters
    ----------
    text : str
        Label text to display (will be drawn rotated).

    orientation : str, optional
        Orientation of the label; currently 'west' (default) is supported.

    forceWidth : bool, optional
        Reserved for future use; if True, forces width handling (default True).
    """

    def __init__(self, text: str, orientation: str = 'west', forceWidth: bool = True):
        QLabel.__init__(self, text)
        # self.forceWidth = forceWidth
        self.orientation = orientation
        # self.setOrientation(orientation)

    # def setOrientation(self, o):
    #     self.orientation = o
    #     self.update()
    #     self.updateGeometry()

    def paintEvent(self, ev: QEvent) -> None:
        """
        Handle the paint event to draw the rotated label.

        Parameters
        ----------
        ev : QEvent
            The paint event to process.
        """
        # p = QtGui.QPainter(self)
        # p.setPen(QtCore.Qt.black)
        p = QtGui.QPainter(self)
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

    def sizeHint(self) -> QtCore.QSize:
        """
        Provide a size hint for the label based on its dimensions.

        Returns
        -------
        QSize
            The recommended size for the label.
        """
        size = super().sizeHint()
        size.transpose()
        return size

    def minimumSizeHint(self) -> QtCore.QSize:
        """
        Provide a minimum size hint for the label based on its dimensions.

        Returns
        -------
        QSize
            The minimum recommended size for the label.
        """
        size = super().minimumSizeHint()
        size.transpose()
        return size

# ==============================================================================


if __name__ == '__main__':
    pass
