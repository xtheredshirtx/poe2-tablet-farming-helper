"""Shared UI building blocks: badges, rank chips, tables, warning panels."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QAbstractItemView, QHeaderView, QSizePolicy, QToolButton, QWidget,
)

from .theme import BADGE_STYLES, RANK_COLORS


def badge(kind, text=None):
    """Small colored label such as OFFICIAL / CONFLICT / NEEDS VERIFICATION."""
    bg, fg, default_text = BADGE_STYLES.get(kind, BADGE_STYLES["unknown"])
    lbl = QLabel(text or default_text)
    lbl.setStyleSheet(
        "background-color:%s;color:%s;border-radius:3px;"
        "padding:2px 6px;font-size:8pt;font-weight:bold;" % (bg, fg))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
    return lbl


def confidence_badge(confidence):
    kind = str(confidence or "unknown").lower()
    if kind not in BADGE_STYLES:
        kind = "community" if "medium" in kind or "high" in kind else "unknown"
    return badge(kind)


def rank_chip(rank):
    color = RANK_COLORS.get(str(rank), "#8a7d65")
    lbl = QLabel(str(rank))
    lbl.setStyleSheet(
        "background-color:#221d15;color:%s;border:1px solid %s;"
        "border-radius:3px;padding:2px 8px;font-weight:bold;" % (color, color))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
    return lbl


def header(text, role="h2"):
    lbl = QLabel(text)
    lbl.setProperty("role", role)
    return lbl


def dim(text):
    lbl = QLabel(text)
    lbl.setProperty("role", "dim")
    lbl.setWordWrap(True)
    return lbl


def warn_panel(lines):
    frame = QFrame()
    frame.setProperty("role", "warnpanel")
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 6, 10, 6)
    for line in lines:
        lbl = QLabel("⚠ " + line)
        lbl.setProperty("role", "warn")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
    return frame


def patch_bar(text):
    row = QFrame()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.addWidget(badge("patch", "PATCH 0.5.4b HF3"))
    lay.addWidget(dim(text))
    lay.addStretch(1)
    return row


class CollapsibleSection(QWidget):
    """Simple disclosure widget for progressive detail."""

    def __init__(self, title, content, expanded=False, parent=None):
        super().__init__(parent)
        self.content = content
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 4)
        root.setSpacing(4)

        self.toggle = QToolButton()
        self.toggle.setText(title)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(expanded)
        self.toggle.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle.clicked.connect(self._sync)
        root.addWidget(self.toggle)
        root.addWidget(content)
        self._sync()

    def _sync(self):
        expanded = self.toggle.isChecked()
        self.content.setVisible(expanded)
        self.toggle.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)


STATUS_COLORS = {
    "confirmed": None,                # normal text
    "conflict": QColor("#f08a7a"),
    "unknown": QColor("#e0a95a"),
    "duplicate": QColor("#e0a95a"),
    "partial": QColor("#e0a95a"),
}


def poe_item_card(title, subtitle=None, sections=None, min_width=560):
    """PoE in-game item tooltip style card.

    sections: list of line-lists; each line is (text, kind) with kind one of
    'mod' (magic blue), 'info' (grey), 'white', 'gold', 'warn'. Sections are
    separated by hairlines, lines are centered — like an item popup.
    """
    frame = QFrame()
    frame.setProperty("role", "poeitem")
    frame.setMinimumWidth(min_width)
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(0, 0, 0, 10)
    outer.setSpacing(6)

    head = QFrame()
    head.setProperty("role", "poeitem-head")
    head_lay = QVBoxLayout(head)
    head_lay.setContentsMargins(14, 6, 14, 6)
    head_lay.setSpacing(0)
    title_lbl = QLabel(title)
    title_lbl.setProperty("role", "poe-title")
    title_lbl.setAlignment(Qt.AlignCenter)
    head_lay.addWidget(title_lbl)
    if subtitle:
        sub_lbl = QLabel(subtitle)
        sub_lbl.setProperty("role", "poe-subtitle")
        sub_lbl.setAlignment(Qt.AlignCenter)
        head_lay.addWidget(sub_lbl)
    outer.addWidget(head)

    for i, section in enumerate(sections or []):
        if i:
            sep = QFrame()
            sep.setProperty("role", "poe-sep")
            sep_wrap = QHBoxLayout()
            sep_wrap.setContentsMargins(60, 0, 60, 0)
            sep_wrap.addWidget(sep)
            outer.addLayout(sep_wrap)
        for text, kind in section:
            lbl = QLabel(text)
            lbl.setProperty("role", "poe-" + kind)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            outer.addWidget(lbl)
    return frame


def make_table(columns, rows, status_key=None, stretch_column=None, expand=False):
    """rows: list of lists of cell strings; status_key: parallel list of row
    status names used to tint text for conflicted/unknown rows.

    expand=True sizes the table to its full content height (capped) so pages
    inside a scroll area show the rows directly instead of a tiny inner
    scrollbar — the page scrolls, not the table."""
    table = QTableWidget(len(rows), len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setAlternatingRowColors(True)
    table.setWordWrap(True)
    for r, row in enumerate(rows):
        color = STATUS_COLORS.get(status_key[r]) if status_key else None
        for c, cell in enumerate(row):
            item = QTableWidgetItem(str(cell))
            if color is not None:
                item.setForeground(color)
            table.setItem(r, c, item)
    headerv = table.horizontalHeader()
    headerv.setSectionResizeMode(QHeaderView.ResizeToContents)
    if stretch_column is not None:
        headerv.setSectionResizeMode(stretch_column, QHeaderView.Stretch)
    table.verticalHeader().setDefaultSectionSize(26)
    table.resizeRowsToContents()
    if expand:
        content = table.horizontalHeader().height() + 12
        for r in range(table.rowCount()):
            content += table.rowHeight(r)
        table.setMinimumHeight(min(content, 1600))
        if content <= 1600:
            table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    return table
