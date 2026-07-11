"""Tablet Database browser: bases, all modifier pools, unique tablets."""
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QSplitter,
    QVBoxLayout, QWidget,
)
from PySide6.QtCore import Qt

from ..widgets import dim, header, make_table, patch_bar, warn_panel

FILTER_ALL = "All modifiers"
FILTER_SHARED = "Shared pool (all tablets)"
FILTER_UNIQUES = "Unique tablets"
FILTER_BASES = "Tablet bases"


class TabletDbTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        root = QVBoxLayout(self)
        root.addWidget(header("Tablet Database", "h1"))
        root.addWidget(patch_bar(store.patch_banner()))
        root.addWidget(warn_panel([
            "Ratings are community/editorial OPINION. Rows tinted red have source conflicts; "
            "orange rows are UNKNOWN - NEEDS VERIFICATION.",
            "Modifier weights are unavailable from game files (PoE2DB) — no weighting shown.",
        ]))

        controls = QHBoxLayout()
        controls.addWidget(QLabel("View:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(
            [FILTER_ALL, FILTER_SHARED, FILTER_UNIQUES, FILTER_BASES]
            + store.tablet_base_names())
        self.view_combo.currentIndexChanged.connect(self.rebuild)
        controls.addWidget(self.view_combo)
        controls.addWidget(QLabel("Filter:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search name / text / stat ID…")
        self.search.textChanged.connect(self.rebuild)
        controls.addWidget(self.search, 1)
        root.addLayout(controls)

        self.split = QSplitter(Qt.Vertical)
        self.table_host = QWidget()
        self.table_layout = QVBoxLayout(self.table_host)
        self.table_layout.setContentsMargins(0, 0, 0, 0)
        self.split.addWidget(self.table_host)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setPlaceholderText("Select a row to see notes, conflicts, and sources.")
        self.detail.setMaximumHeight(120)
        self.split.addWidget(self.detail)
        self.split.setStretchFactor(0, 4)
        root.addWidget(self.split, 1)

        self.table = None
        self._detail_rows = []
        self.rebuild()

    def show_tablet_type(self, tablet_type):
        idx = self.view_combo.findText(tablet_type)
        self.view_combo.setCurrentIndex(idx if idx >= 0 else 0)

    def rebuild(self):
        view = self.view_combo.currentText()
        needle = self.search.text().strip().lower()

        if view == FILTER_BASES:
            columns = ["Tablet", "Function", "Uses", "Trade type", "Confidence"]
            rows, statuses, details = [], [], []
            for b in self.store.tablets["bases"]:
                rows.append([b["name"], b["function"], b["uses"],
                             b["trade_type"], b["confidence"]])
                statuses.append("confirmed")
                details.append("Sources: %s\n%s" % (
                    ", ".join(b.get("sources", [])), b.get("note", "")))
            stretch = 1
        elif view == FILTER_UNIQUES:
            columns = ["Unique", "Base", "Effect", "Stat IDs", "Rating*", "Confidence"]
            rows, statuses, details = [], [], []
            for u in self.store.tablets["uniques"]:
                rows.append([u["name"], u["base"], u["text"],
                             ", ".join(u["stat_ids"]) or "UNKNOWN",
                             u["rating"], u["confidence"]])
                statuses.append(u["stat_status"] if u["stat_status"] != "confirmed"
                                else ("conflict" if u["confidence"] == "conflict" else "confirmed"))
                details.append(u.get("conflict") or u.get("warning") or u.get("note") or "")
            stretch = 2
        else:
            if view == FILTER_ALL:
                mods = self.store.all_modifier_rows()
            elif view == FILTER_SHARED:
                mods = [m for m in self.store.all_modifier_rows()
                        if m["tablet"] == "All tablets"]
            else:
                mods = ([{**m, "tablet": "All tablets"}
                         for m in self.store.all_modifier_rows()
                         if m["tablet"] == "All tablets"]
                        + [m for m in self.store.all_modifier_rows()
                           if m["tablet"] == view])
            columns = ["Name", "Modifier text", "Roll", "Tablet", "Slot",
                       "Trade stat ID", "Rating*", "Best for", "Confidence"]
            rows, statuses, details = [], [], []
            for m in mods:
                rows.append([m["name"], m["text"], m["roll"], m["tablet"],
                             m["slot"], m["stat_id"], m["rating"],
                             m["best_for"], m["confidence"]])
                statuses.append(m["stat_status"] if m["stat_status"] != "confirmed"
                                else ("conflict" if m["confidence"] == "conflict" else "confirmed"))
                details.append(m.get("conflict") or m.get("warning") or m.get("note") or "")
            stretch = 1

        if needle:
            keep = [i for i, r in enumerate(rows)
                    if any(needle in str(c).lower() for c in r)]
            rows = [rows[i] for i in keep]
            statuses = [statuses[i] for i in keep]
            details = [details[i] for i in keep]

        if self.table is not None:
            self.table.deleteLater()
        self.table = make_table(columns, rows, statuses, stretch_column=stretch)
        self._detail_rows = details
        self.table.itemSelectionChanged.connect(self._show_detail)
        self.table_layout.addWidget(self.table)
        self.detail.clear()

    def _show_detail(self):
        selected = self.table.selectionModel().selectedRows()
        if selected and selected[0].row() < len(self._detail_rows):
            text = self._detail_rows[selected[0].row()]
            self.detail.setPlainText(text or "No extra notes for this row.")
