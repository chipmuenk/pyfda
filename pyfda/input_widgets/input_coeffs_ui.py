# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Create the UI for the FilterCoeffs class
"""

from __future__ import print_function, division, unicode_literals, absolute_import
import logging
logger = logging.getLogger(__name__)

from ..compat import (pyqtSignal, Qt, QtGui, QWidget, QLabel, QLineEdit, QComboBox,
                      QPushButton, QFrame, QSpinBox, QFont, QIcon,
                      QVBoxLayout, QHBoxLayout, QGridLayout, QSizePolicy)

from pyfda.pyfda_qt_lib import qset_cmb_box
from pyfda.pyfda_io_lib import CSV_option_box
 
from pyfda.pyfda_rc import params

class Input_Coeffs_UI(QWidget):
    """
    Create the UI for the FilterCoeffs class
    """
    sig_rx = pyqtSignal(dict) # incoming
    sig_tx = pyqtSignal(dict) # outgoing

    def __init__(self, parent):
        super(Input_Coeffs_UI, self).__init__(parent)
        self.eps = 1.e-6 # initialize tolerance value
        """
        Intitialize the widget, consisting of:
        - top chkbox row
        - coefficient table
        - two bottom rows with action buttons
        """
        self.bfont = QFont()
        self.bfont.setBold(True)
        self.bifont = QFont()
        self.bifont.setBold(True)
        self.bifont.setItalic(True)
#        q_icon_size = QSize(20, 20) # optional, size is derived from butEnable

        #######################################################################
        # frmMain
        #
        # This frame contains all the buttons
        #######################################################################
        # ---------------------------------------------
        # layHDisplay
        #
        # UI Elements for controlling the display
        # ---------------------------------------------
        self.butEnable = QPushButton(self)
        self.butEnable.setIcon(QIcon(':/circle-x.svg'))
        q_icon_size = self.butEnable.iconSize() # <- uncomment this for manual sizing
        self.butEnable.setIconSize(q_icon_size)
        self.butEnable.setCheckable(True)
        self.butEnable.setChecked(True)
        self.butEnable.setToolTip("<span>Show / hide filter coefficients in an editable table."
                " For high order systems, table display might be slow.</span>")

        fix_formats = ['Dec', 'Hex', 'Bin', 'CSD']
        self.cmbFormat = QComboBox(self)
        model = self.cmbFormat.model()
        item = QtGui.QStandardItem('Float')
        item.setData('child', Qt.AccessibleDescriptionRole)
        model.appendRow(item)

        item = QtGui.QStandardItem('Fixp.:')
        item.setData('parent', Qt.AccessibleDescriptionRole)
        item.setData(0, QtGui.QFont.Bold)
        item.setFlags(item.flags() & ~Qt.ItemIsEnabled)# | Qt.ItemIsSelectable))
        model.appendRow(item)

        for idx in range(len(fix_formats)):
            item = QtGui.QStandardItem(fix_formats[idx])
#            item.setForeground(QtGui.QColor('red'))
            model.appendRow(item)

        self.cmbFormat.insertSeparator(1)
        qset_cmb_box(self.cmbFormat, 'float')
        self.cmbFormat.setToolTip('Set the display format.')
        self.cmbFormat.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        self.spnDigits = QSpinBox(self)
        self.spnDigits.setRange(0,16)
        self.spnDigits.setValue(params['FMT_ba'])
        self.spnDigits.setToolTip("Number of digits to display.")
        self.lblDigits = QLabel("Digits", self)
        self.lblDigits.setFont(self.bifont)

        self.cmbQFrmt = QComboBox(self)
        q_formats = [('Integer', 'qint' ), ('Norm. Frac.', 'qnfrac'), ('Fractional', 'qfrac')]
        for q in q_formats:
            self.cmbQFrmt.addItem(*q)

        self.lbl_W  = QLabel("W = ", self)
        self.lbl_W.setFont(self.bifont)

        self.ledW = QLineEdit(self)
        self.ledW.setToolTip("Specify total wordlength.")
        self.ledW.setText("16")
        self.ledW.setMaxLength(2) # maximum of 2 digits
        self.ledW.setFixedWidth(30) # width of lineedit in points(?)

        layHDisplay = QHBoxLayout()
        layHDisplay.setAlignment(Qt.AlignLeft)
        layHDisplay.addWidget(self.butEnable)
        layHDisplay.addWidget(self.cmbFormat)
        layHDisplay.addWidget(self.spnDigits)
        layHDisplay.addWidget(self.lblDigits)
        layHDisplay.addWidget(self.cmbQFrmt)
        layHDisplay.addWidget(self.lbl_W)
        layHDisplay.addWidget(self.ledW)
        layHDisplay.addStretch()

        # -----------------------------------------------------------------
        # layHButtonsCoeffs1
        #
        # UI Elements for loading / storing / manipulating cells and rows
        # -----------------------------------------------------------------
        self.cmbFilterType = QComboBox(self)
        self.cmbFilterType.setObjectName("comboFilterType")
        self.cmbFilterType.setToolTip("<span>Select between IIR and FIR filter for manual entry."
                                      "Changing the type reloads the filter from the filter dict.</span>")
        self.cmbFilterType.addItems(["FIR","IIR"])
        self.cmbFilterType.setSizeAdjustPolicy(QComboBox.AdjustToContents)


        self.butAddCells = QPushButton(self)
        self.butAddCells.setIcon(QIcon(':/row_insert_above.svg'))
        self.butAddCells.setIconSize(q_icon_size)
        self.butAddCells.setToolTip("<SPAN>Select cells to insert a new cell above each selected cell. "
                                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
                                "When nothing is selected, add a row at the end.</SPAN>")

        self.butDelCells = QPushButton(self)
        self.butDelCells.setIcon(QIcon(':/row_delete.svg'))
        self.butDelCells.setIconSize(q_icon_size)
        self.butDelCells.setToolTip("<SPAN>Delete selected cell(s) from the table. "
                "Use &lt;SHIFT&gt; or &lt;CTRL&gt; to select multiple cells. "
                "When nothing is selected, delete the last row.</SPAN>")

        self.butSave = QPushButton(self)
        self.butSave.setIcon(QIcon(':/upload.svg'))
        self.butSave.setIconSize(q_icon_size)
        self.butSave.setToolTip("<span>Copy coefficient table to filter dict and update all plots and widgets.</span>")

        self.butLoad = QPushButton(self)
        self.butLoad.setIcon(QIcon(':/download.svg'))
        self.butLoad.setIconSize(q_icon_size)
        self.butLoad.setToolTip("Reload coefficient table from filter dict.")

        self.butClear = QPushButton(self)
        self.butClear.setIcon(QIcon(':/trash.svg'))
        self.butClear.setIconSize(q_icon_size)
        self.butClear.setToolTip("Clear all table entries.")

        self.butFromTable = QPushButton(self)
        self.butFromTable.setIconSize(q_icon_size)

        self.butToTable = QPushButton(self)
        self.butToTable.setIconSize(q_icon_size)
        self._set_load_save_icons()

        butSettingsClipboard = QPushButton(self)
        butSettingsClipboard.setIcon(QIcon(':/settings.svg'))
        butSettingsClipboard.setIconSize(q_icon_size)
        butSettingsClipboard.setToolTip("<span>Select CSV format and whether "
                                "to copy to/from clipboard or file.</span>")

        layHButtonsCoeffs1 = QHBoxLayout()
        layHButtonsCoeffs1.addWidget(self.cmbFilterType)
        layHButtonsCoeffs1.addWidget(self.butAddCells)
        layHButtonsCoeffs1.addWidget(self.butDelCells)
        layHButtonsCoeffs1.addWidget(self.butClear)
        layHButtonsCoeffs1.addWidget(self.butSave)
        layHButtonsCoeffs1.addWidget(self.butLoad)
        layHButtonsCoeffs1.addWidget(self.butFromTable)
        layHButtonsCoeffs1.addWidget(self.butToTable)
        layHButtonsCoeffs1.addWidget(butSettingsClipboard)
        layHButtonsCoeffs1.addStretch()

        #----------------------------------------------------------------------
        # layHButtonsCoeffs2
        #
        # Eps / set zero settings
        # ---------------------------------------------------------------------
        self.butSetZero = QPushButton("= 0", self)
        self.butSetZero.setToolTip("<span>Set selected coefficients = 0 with a magnitude &lt; &epsilon;. "
        "When nothing is selected, test the whole table.</span>")
        self.butSetZero.setIconSize(q_icon_size)

        lblEps = QLabel(self)
        lblEps.setText("<b><i>for b, a</i> &lt;</b>")

        self.ledEps = QLineEdit(self)
        self.ledEps.setToolTip("Specify tolerance value.")

        layHButtonsCoeffs2 = QHBoxLayout()
        layHButtonsCoeffs2.addWidget(self.butSetZero)
        layHButtonsCoeffs2.addWidget(lblEps)
        layHButtonsCoeffs2.addWidget(self.ledEps)
        layHButtonsCoeffs2.addStretch()

        #######################################################################
        # frmQSettings
        #
        # This frame contains all quantization settings
        #######################################################################
        #-------------------------------------------------------------------
        # layHW_Scale
        #
        # QFormat and scale settings
        # ---------------------------------------------------------------------
        lbl_Q = QLabel("Q =", self)
        lbl_Q.setFont(self.bifont)

        self.ledWI = QLineEdit(self)
        self.ledWI.setToolTip("Specify number of integer bits.")
        self.ledWI.setText("0")
        self.ledWI.setMaxLength(2) # maximum of 2 digits
        self.ledWI.setFixedWidth(30) # width of lineedit in points(?)

        self.lblDot = QLabel(".", self) # class attribute, visibility is toggled
        self.lblDot.setFont(self.bfont)

        self.ledWF = QLineEdit(self)
        self.ledWF.setToolTip("Specify number of fractional bits.")
        self.ledWF.setText("15")
        self.ledWF.setMaxLength(2) # maximum of 2 digits
#        self.ledWF.setFixedWidth(30) # width of lineedit in points(?)
        self.ledWF.setMaximumWidth(30)

        self.lblScale = QLabel("<b><i>Scale</i> =</b>", self)
        self.ledScale = QLineEdit(self)
        self.ledScale.setToolTip("Set the scale for converting float to fixpoint representation.")
        self.ledScale.setText(str(1))

        layHWI_WF = QHBoxLayout()
        layHWI_WF.addWidget(lbl_Q)
        layHWI_WF.addWidget(self.ledWI)
        layHWI_WF.addWidget(self.lblDot)
        layHWI_WF.addWidget(self.ledWF)
        layHWI_WF.addStretch()

        layHScale = QHBoxLayout()
        layHScale.addWidget(self.lblScale)
        layHScale.addWidget(self.ledScale)
        layHScale.addStretch()

        layHW_Scale = QHBoxLayout()
        layHW_Scale.addLayout(layHWI_WF)
        layHW_Scale.addLayout(layHScale)

        #-------------------------------------------------------------------
        # layGQOpt
        #
        # Quantization / Overflow / MSB / LSB settings
        # ---------------------------------------------------------------------
        lblQOvfl = QLabel("Ovfl.:", self)
        lblQOvfl.setFont(self.bifont)
        lblQuant = QLabel("Quant.:", self)
        lblQuant.setFont(self.bifont)

        self.cmbQOvfl = QComboBox(self)
        qOvfl = ['wrap', 'sat']
        self.cmbQOvfl.addItems(qOvfl)
        qset_cmb_box(self.cmbQOvfl, 'sat')
        self.cmbQOvfl.setToolTip("Select overflow behaviour.")
        # ComboBox size is adjusted automatically to fit the longest element
        self.cmbQOvfl.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layHQOvflOpt = QHBoxLayout()
        layHQOvflOpt.addWidget(lblQOvfl)
        layHQOvflOpt.addWidget(self.cmbQOvfl)
        layHQOvflOpt.addStretch()

        self.cmbQuant = QComboBox(self)
        qQuant = ['none', 'round', 'fix', 'floor']
        self.cmbQuant.addItems(qQuant)
        qset_cmb_box(self.cmbQuant, 'round')
        self.cmbQuant.setToolTip("Select the kind of quantization.")
        self.cmbQuant.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        layHQuantOpt = QHBoxLayout()
        layHQuantOpt.addWidget(lblQuant)
        layHQuantOpt.addWidget(self.cmbQuant)
        layHQuantOpt.addStretch()

        self.butQuant = QPushButton(self)
        self.butQuant.setToolTip("<span>Quantize selected coefficients / "
        "whole table with specified settings.</span>")
        self.butQuant.setIcon(QIcon(':/quantize.svg'))
        self.butQuant.setIconSize(q_icon_size)
        self.butQuant.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        lblMSBtxt = QLabel(self)
        lblMSBtxt.setText("<b><i>MSB</i><sub>10</sub> =</b>")
        self.lblMSB = QLabel(self)
        layHMSB = QHBoxLayout()
        layHMSB.addWidget(lblMSBtxt)
        layHMSB.addWidget(self.lblMSB)
        layHMSB.addStretch()

        lblLSBtxt = QLabel(self)
        lblLSBtxt.setText("<b><i>LSB</i><sub>10</sub> =</b>")
        self.lblLSB = QLabel(self) #
        layHLSB = QHBoxLayout()
        layHLSB.addWidget(lblLSBtxt)
        layHLSB.addWidget(self.lblLSB)
        layHLSB.addStretch()

        layGQOpt = QGridLayout()
        layGQOpt.addLayout(layHQOvflOpt,0,0)
        layGQOpt.addLayout(layHQuantOpt, 0,1)
        layGQOpt.addWidget(self.butQuant, 0, 2, Qt.AlignCenter)
        layGQOpt.addLayout(layHMSB,1,0)
        layGQOpt.addLayout(layHLSB,1,1)

        #-------------------------------------------------------------------
        #   Display MAX
        # ---------------------------------------------------------------------
        lblMAXtxt = QLabel(self)
        lblMAXtxt.setText("<b><i>Max =</i></b>")
        self.lblMAX = QLabel(self)

        layHCoeffs_MAX = QHBoxLayout()
        layHCoeffs_MAX.addWidget(lblMAXtxt)
        layHCoeffs_MAX.addWidget(self.lblMAX)
        layHCoeffs_MAX.addStretch()

        #######################################################################
        # Now put all the coefficient HBoxes into frmQSettings
        # ---------------------------------------------------------------------
        layVButtonsQ = QVBoxLayout()
        layVButtonsQ.addLayout(layHW_Scale)
        layVButtonsQ.addLayout(layGQOpt)
        layVButtonsQ.addLayout(layHCoeffs_MAX)
        layVButtonsQ.setContentsMargins(0,5,0,0)
        # This frame encompasses all Quantization Settings
        self.frmQSettings = QFrame(self)
        self.frmQSettings.setLayout(layVButtonsQ)

        # ########################  Main UI Layout ############################
        # layout for frame (UI widget)
        layVMainF = QVBoxLayout()
        layVMainF.addLayout(layHDisplay)
        layVMainF.addLayout(layHButtonsCoeffs1)
        layVMainF.addLayout(layHButtonsCoeffs2)
        layVMainF.addWidget(self.frmQSettings)
        # This frame encompasses all UI elements
        frmMain = QFrame(self)
        frmMain.setLayout(layVMainF)

        layVMain = QVBoxLayout()
        layVMain.setAlignment(Qt.AlignTop) # this affects only the first widget (intended here)
        layVMain.addWidget(frmMain)
        layVMain.setContentsMargins(*params['wdg_margins'])
        self.setLayout(layVMain)
        #######################################################################

        #--- set initial values from dict ------------
        self.spnDigits.setValue(params['FMT_ba'])
        self.ledEps.setText(str(self.eps))

        #----------------------------------------------------------------------
        # LOCAL SIGNALS & SLOTs
        #----------------------------------------------------------------------                
        butSettingsClipboard.clicked.connect(self._copy_options)
        self.sig_rx.connect(self._set_load_save_icons)
        
    #------------------------------------------------------------------------------
    def _copy_options(self):
        """
        Set options for copying to/from clipboard or file, storing the selections
        in `params`
        """
        self.opt_widget = CSV_option_box(self) # important: Handle must be class attribute
        #self.opt_widget.show() # modeless dialog, i.e. non-blocking
        self.opt_widget.exec_() # modal dialog (blocking)

        self._set_load_save_icons()
        self.sig_tx.emit({'sender':__name__, 'ui_changed': 'csv'})

    #------------------------------------------------------------------------------
    def _set_load_save_icons(self):
        """
        Set icons / tooltipps for loading and saving data to / from file or
        clipboard depending on selected options.
        """
        if params['CSV']['clipboard']:
            self.butFromTable.setIcon(QIcon(':/to_clipboard.svg'))
            self.butFromTable.setToolTip("<span>"
                    "Copy table to clipboard, SELECTED items are copied as "
                    "displayed. When nothing is selected, the whole table "
                    "is copied with full precision in decimal format.</span>")

            self.butToTable.setIcon(QIcon(':/from_clipboard.svg'))
            self.butToTable.setToolTip("<span>Copy clipboard to table.</span>")
        else:
            self.butFromTable.setIcon(QIcon(':/save.svg'))
            self.butFromTable.setToolTip("<span>"
                    "Save table to file, SELECTED items are copied as "
                    "displayed. When nothing is selected, the whole table "
                    "is copied with full precision in decimal format.</span>")

            self.butToTable.setIcon(QIcon(':/file.svg'))
            self.butToTable.setToolTip("<span>Load table from file.</span>")

#------------------------------------------------------------------------------
if __name__ == '__main__':
    """ Test with python -m pyfda.input_widgets.input_coeffs_ui """
    import sys
    from ..compat import QApplication

    app = QApplication(sys.argv)
    mainw = Input_Coeffs_UI(None)

    app.setActiveWindow(mainw)
    mainw.show()

    sys.exit(app.exec_())
