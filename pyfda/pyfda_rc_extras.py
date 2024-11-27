

qss_common = """
                /* Background color of popup-list.*/ 
                QComboBox QListView{
                    background-color:white;
                    border:1px solid gray;
                }
                /* Needed to complete the rule set. */
                QComboBox::item:alternate {
                    background: white;
                }
                /* Color of the selected list item. */
                QComboBox::item:selected {
                    border: 1px solid transparent;
                    background:yellow;
                }

                QComboBox::item {
                    padding-left: 0.1em;
                    height: 2em;
                }
                QComboBox::item:selected {
                    padding-left: 0.1em;
                    color: black;
                    background-color: lightgray;
                }
                QComboBox::item:checked {
                    padding-left: 0em;
                    font-weight: bold;
                }

                /* Indicator will shine through the label text if you don't make it hidden. */
                QComboBox::indicator {
                    color: transparent;
                    background-color: transparent;
                    selection-color: transparent;
                    selection-background-color: transparent;
                }

                    /* Style for dropdown items */
    /*QComboBox QAbstractItemView {
        background-color: white;
        border: 1px solid gray;
    }*/
    /* https://stackoverflow.com/questions/29939990/qcombobox-style-for-choosen-item-in-drop-down-list */
    /* Style for editable text field in combobox*/
    /* QComboBox::editable QLineEdit {background-color: white; border: none;} */

    QComboBox
    {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        selection-background-color: #111;
        selection-color: yellow;
        color: white;
        background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);
        border-style: solid;
        border: 1px solid #1e1e1e;
        border-radius: 5;
        padding: 1px 0px 1px 20px;
    }


    QComboBox:hover, QPushButton:hover
    {
        border: 1px solid yellow;
        color: white;
    }

    QComboBox:editable {
        background: red;
        color: pink;
    }

    QComboBox:on
    {
        padding-top: 0px;
        padding-left: 0px;
        color: white;
        background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);
        selection-background-color: #ffaa00;
    }

    QComboBox:!on
    {
        color: white;
        background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #666, stop: 0.1 #555, stop: 0.5 #555, stop: 0.9 #444, stop: 1 #333);
    }

    QComboBox QAbstractItemView
    {
        border: 2px solid darkgray;
        color: black;
        selection-background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #111, stop: 1 #333);
    }

    QComboBox::drop-down
    {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        color: white;
        border-left-width: 0px;
        border-left-color: darkgray;
        border-left-style: solid; /* just a single line */
        border-top-right-radius: 3px; /* same radius as the QComboBox */
        border-bottom-right-radius: 3px;
        padding-left: 10px;
    }

    QComboBox::down-arrow, QSpinBox::down-arrow, QTimeEdit::down-arrow, QDateEdit::down-arrow
    {
        image: url(:/icons/down_arrow.png);
        width: 7px;
        height: 5px;
    }



                """