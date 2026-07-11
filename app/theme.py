"""App theming: selectable dark palettes with matched text colors.

The PoE item-tooltip card styles at the bottom stay fixed in every palette —
they replicate the in-game item popup and should always look like the game.
"""

PALETTES = {
    "PoE Gold (default)": {
        "bg": "#16130f", "panel": "#1b1712", "panel_alt": "#201b14",
        "border": "#3a3226", "input_bg": "#221d15", "input_border": "#4a4030",
        "header_bg": "#262016", "accent": "#d8b45a", "accent_bright": "#e6c877",
        "text": "#d8cfc0", "text_light": "#e8dfc8", "dim": "#8a7d65",
        "disabled": "#6a5f4c", "btn_bg": "#33290f", "btn_hover": "#4a3b16",
        "btn_border": "#6b5a2e", "selection": "#4a3d22",
        "selection_text": "#f0e6d2", "scroll": "#4a4030",
    },
    "Abyss Blue": {
        "bg": "#0d1218", "panel": "#121a24", "panel_alt": "#16202c",
        "border": "#263346", "input_bg": "#16202c", "input_border": "#33455e",
        "header_bg": "#1a2635", "accent": "#5ab4d8", "accent_bright": "#8fd0ea",
        "text": "#c6d2e0", "text_light": "#dde7f2", "dim": "#7d90a8",
        "disabled": "#55677e", "btn_bg": "#12283a", "btn_hover": "#1c3b54",
        "btn_border": "#3d6a8a", "selection": "#27455f",
        "selection_text": "#eaf3fb", "scroll": "#33455e",
    },
    "Blood Crimson": {
        "bg": "#170e0e", "panel": "#1d1212", "panel_alt": "#241616",
        "border": "#402626", "input_bg": "#241616", "input_border": "#573434",
        "header_bg": "#2a1818", "accent": "#d86a6a", "accent_bright": "#eb9090",
        "text": "#d8c6c6", "text_light": "#ecdcdc", "dim": "#9c7d7d",
        "disabled": "#6f5555", "btn_bg": "#3a1414", "btn_hover": "#542020",
        "btn_border": "#8a3d3d", "selection": "#5a2727",
        "selection_text": "#f7e9e9", "scroll": "#573434",
    },
    "Verdant Green": {
        "bg": "#0e150f", "panel": "#131c14", "panel_alt": "#17231a",
        "border": "#28402c", "input_bg": "#17231a", "input_border": "#375e3d",
        "header_bg": "#1a2a1e", "accent": "#6ad885", "accent_bright": "#93eaa9",
        "text": "#c8dccb", "text_light": "#dfeee1", "dim": "#85a08a",
        "disabled": "#5d745f", "btn_bg": "#14361d", "btn_hover": "#1e4f2b",
        "btn_border": "#3f8a4f", "selection": "#2a5a36",
        "selection_text": "#ecf7ee", "scroll": "#375e3d",
    },
    "Amethyst": {
        "bg": "#131019", "panel": "#191521", "panel_alt": "#1f1a29",
        "border": "#372c4a", "input_bg": "#1f1a29", "input_border": "#4c3d66",
        "header_bg": "#251e33", "accent": "#b48ae0", "accent_bright": "#ceadee",
        "text": "#d2c8e0", "text_light": "#e5dcf2", "dim": "#8f81a8",
        "disabled": "#65597e", "btn_bg": "#2b1c44", "btn_hover": "#3d2a5e",
        "btn_border": "#6b4d99", "selection": "#453061",
        "selection_text": "#f2ebfb", "scroll": "#4c3d66",
    },
}

DEFAULT_THEME = "PoE Gold (default)"

_TEMPLATE = """
* {
    font-family: "Segoe UI", "Verdana", sans-serif;
    font-size: 10pt;
}
QMainWindow, QWidget {
    background-color: %(bg)s;
    color: %(text)s;
}
QTabWidget::pane {
    border: 1px solid %(border)s;
    background-color: %(panel)s;
}
QTabBar::tab {
    background-color: %(panel_alt)s;
    color: %(dim)s;
    padding: 7px 14px;
    border: 1px solid %(border)s;
    border-bottom: none;
    margin-right: 1px;
}
QTabBar::tab:selected {
    background-color: %(header_bg)s;
    color: %(accent)s;
    border-bottom: 2px solid %(accent)s;
}
QTabBar::tab:hover {
    color: %(accent_bright)s;
}
QGroupBox {
    border: 1px solid %(border)s;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: bold;
    color: %(accent)s;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}
QTableWidget, QTableView {
    background-color: %(panel)s;
    alternate-background-color: %(panel_alt)s;
    gridline-color: %(border)s;
    border: 1px solid %(border)s;
    selection-background-color: %(selection)s;
    selection-color: %(selection_text)s;
}
QHeaderView::section {
    background-color: %(header_bg)s;
    color: %(accent)s;
    padding: 5px;
    border: none;
    border-right: 1px solid %(border)s;
    border-bottom: 1px solid %(border)s;
    font-weight: bold;
}
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: %(input_bg)s;
    color: %(text_light)s;
    border: 1px solid %(input_border)s;
    border-radius: 3px;
    padding: 4px 6px;
}
QComboBox QAbstractItemView {
    background-color: %(input_bg)s;
    color: %(text_light)s;
    selection-background-color: %(selection)s;
}
QPushButton {
    background-color: %(btn_bg)s;
    color: %(accent_bright)s;
    border: 1px solid %(btn_border)s;
    border-radius: 3px;
    padding: 6px 14px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: %(btn_hover)s;
    border-color: %(accent)s;
}
QPushButton:pressed {
    background-color: %(header_bg)s;
}
QPushButton:disabled {
    background-color: %(input_bg)s;
    color: %(disabled)s;
    border-color: %(border)s;
}
QToolButton {
    background-color: %(panel_alt)s;
    color: %(accent)s;
    border: 1px solid %(border)s;
    border-radius: 3px;
    padding: 4px 8px;
    font-weight: bold;
}
QCheckBox, QRadioButton {
    color: %(text)s;
    spacing: 6px;
}
QCheckBox:disabled {
    color: %(disabled)s;
}
QListWidget {
    background-color: %(panel)s;
    border: 1px solid %(border)s;
    color: %(text)s;
}
QListWidget::item:selected {
    background-color: %(selection)s;
    color: %(selection_text)s;
}
QScrollArea {
    border: none;
}
QScrollBar:vertical {
    background: %(panel)s;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: %(scroll)s;
    border-radius: 4px;
    min-height: 24px;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
}
QScrollBar:horizontal {
    background: %(panel)s;
    height: 12px;
}
QScrollBar::handle:horizontal {
    background: %(scroll)s;
    border-radius: 4px;
    min-width: 24px;
}
QLabel[role="h1"] {
    font-size: 15pt;
    font-weight: bold;
    color: %(accent_bright)s;
}
QLabel[role="h2"] {
    font-size: 11.5pt;
    font-weight: bold;
    color: %(accent)s;
}
QLabel[role="dim"] {
    color: %(dim)s;
}
QFrame[role="card"] {
    background-color: %(panel_alt)s;
    border: 1px solid %(border)s;
    border-radius: 6px;
}
QFrame[role="warnpanel"] {
    background-color: #2b1c14;
    border: 1px solid #7a4a2a;
    border-radius: 4px;
}
QLabel[role="warn"] {
    color: #e09a5a;
}
QToolTip {
    background-color: %(header_bg)s;
    color: %(text_light)s;
    border: 1px solid %(btn_border)s;
}
/* --- PoE in-game item tooltip look (fixed in every palette) ------- */
QFrame[role="poeitem"] {
    background-color: #050505;
    border: 1px solid #6b5a2e;
    border-radius: 3px;
}
QFrame[role="poeitem-head"] {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #1b130a, stop:0.5 #3a2a12, stop:1 #1b130a);
    border-bottom: 1px solid #6b5a2e;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
}
QLabel[role="poe-title"] {
    color: #e6c877;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 13pt;
    font-weight: bold;
    letter-spacing: 1px;
    background: transparent;
}
QLabel[role="poe-subtitle"] {
    color: #d8b45a;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 11pt;
    font-weight: bold;
    background: transparent;
}
QLabel[role="poe-mod"] {
    color: #8888ff;
    font-size: 10.5pt;
    background: transparent;
}
QLabel[role="poe-info"] {
    color: #b8b8b8;
    background: transparent;
}
QLabel[role="poe-white"] {
    color: #e8e8e8;
    background: transparent;
}
QLabel[role="poe-gold"] {
    color: #d8b45a;
    background: transparent;
}
QLabel[role="poe-warn"] {
    color: #e06060;
    background: transparent;
}
QFrame[role="poe-sep"] {
    background-color: #3a3226;
    border: none;
    max-height: 1px;
    min-height: 1px;
}
"""


def build_qss(theme_name=DEFAULT_THEME):
    palette = PALETTES.get(theme_name, PALETTES[DEFAULT_THEME])
    return _TEMPLATE % palette


# Backward-compatible default stylesheet.
QSS = build_qss()

# Badge colors keyed by semantic kind (readable on all dark palettes).
BADGE_STYLES = {
    "official":  ("#1e3a24", "#7ddc8f", "OFFICIAL"),
    "database":  ("#1c2f3f", "#7dbcdc", "DATABASE"),
    "community": ("#33290f", "#e6c877", "COMMUNITY"),
    "opinion":   ("#332440", "#c99ae0", "OPINION"),
    "conflict":  ("#40201c", "#f08a7a", "CONFLICT"),
    "unknown":   ("#3d2c14", "#e0a95a", "NEEDS VERIFICATION"),
    "patch":     ("#262016", "#d8b45a", "PATCH"),
}

RANK_COLORS = {
    "SS": "#f0c040", "S+": "#f0c040", "S": "#e6a23c",
    "A": "#7ddc8f", "B+": "#7dbcdc", "B": "#7dbcdc",
    "C": "#a89a80", "F": "#f08a7a", "Avoid": "#f08a7a",
    "Unknown": "#8a7d65", "Conflict": "#f08a7a",
}
