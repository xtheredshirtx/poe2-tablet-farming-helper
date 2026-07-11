"""Atlas Masters reference: unlocks, 36 nodes, strategy mapping."""
from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ..widgets import badge, dim, header, make_table, patch_bar, warn_panel

ALL = "All Masters"


class AtlasMastersTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        outer = QVBoxLayout(self)
        inner = QWidget()
        lay = QVBoxLayout(inner)

        lay.addWidget(header("Atlas Masters", "h1"))
        lay.addWidget(patch_bar(store.patch_banner()))
        lay.addWidget(dim("Source: PoE2DB Masters of the Atlas (database, not official patch "
                          "text). Node effects are database-confirmed; Phase 10 resolved "
                          "the tracked Jado unlock source conflict against PoE2DB quest "
                          "steps."))

        rules = QGroupBox("System rules (PoE2DB)")
        rules_lay = QVBoxLayout(rules)
        for line in store.atlas["system_rules"]:
            lbl = QLabel("• " + line)
            lbl.setWordWrap(True)
            rules_lay.addWidget(lbl)
        lay.addWidget(rules)

        lay.addWidget(header("Unlock requirements"))
        unlocks = store.atlas["unlocks"]
        lay.addWidget(make_table(
            ["Master", "Requirement", "Detail", "Confidence", "Conflict notes"],
            [[u["master"], u["requirement"], u["detail"], u["confidence"],
              u.get("conflict", u.get("evidence", ""))]
             for u in unlocks],
            ["conflict" if "CONFLICT" in u.get("conflict", "") else "confirmed"
             for u in unlocks],
            stretch_column=2, expand=True))
        lay.addWidget(warn_panel([
            "Atlas unlock data is database-confirmed, not official patch text; follow "
            "your in-game quest tracker if it differs.",
        ]))

        controls = QHBoxLayout()
        controls.addWidget(header("Master nodes (12 per Master, 4 active)"))
        controls.addStretch(1)
        controls.addWidget(QLabel("Master:"))
        self.master_combo = QComboBox()
        masters = [ALL] + sorted({n["master"] for n in store.atlas["nodes"]})
        self.master_combo.addItems(masters)
        self.master_combo.currentIndexChanged.connect(self._rebuild_nodes)
        controls.addWidget(self.master_combo)
        lay.addLayout(controls)

        self.nodes_host = QVBoxLayout()
        lay.addLayout(self.nodes_host)
        self.nodes_table = None
        self._rebuild_nodes()

        lay.addWidget(header("Strategy → Master mapping (community)"))
        mapping = store.atlas["strategy_mapping"]
        lay.addWidget(make_table(
            ["Strategy", "Suggested focus", "Why", "Confidence"],
            [[m["strategy"], m["focus"], m["why"], m["confidence"]] for m in mapping],
            stretch_column=2, expand=True))
        lay.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _rebuild_nodes(self):
        if self.nodes_table is not None:
            self.nodes_table.deleteLater()
        choice = self.master_combo.currentText()
        nodes = [n for n in self.store.atlas["nodes"]
                 if choice == ALL or n["master"] == choice]
        self.nodes_table = make_table(
            ["Master", "Tier", "Node", "Effect", "Strategy use", "Confidence"],
            [[n["master"], "T%d" % n["tier"], n["name"], n["effect"], n["use"],
              n["confidence"] + (" — " + n["note"] if n.get("note") else "")]
             for n in nodes],
            stretch_column=3, expand=True)
        self.nodes_host.addWidget(self.nodes_table)
