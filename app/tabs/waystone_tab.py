"""Waystone optimizer draft backed by sourced modifier data."""
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from ..widgets import (
    CollapsibleSection, badge, dim, header, make_table, patch_bar, warn_panel,
)


def _scrollable(widget):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            _clear_layout(item.layout())


class WaystoneOptimizerTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.data = store.waystones
        self.mods = self.data.get("base_mods", [])
        self.goals = self.data.get("goals", [])

        outer = QVBoxLayout(self)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setSpacing(10)

        lay.addWidget(header("Waystone Optimizer", "h1"))
        lay.addWidget(patch_bar(store.patch_banner()))
        lay.addWidget(self._summary_card())
        lay.addWidget(warn_panel([
            "This is a rule-of-thumb planner, not a live profit simulator.",
            "No trade listings are scraped or polled; official stat IDs are shown only where metadata has exact text.",
            "Rows disabled by official patch notes are preserved for research visibility, not recommendations.",
        ]))

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Goal:"))
        self.goal_combo = QComboBox()
        for goal in self.goals:
            self.goal_combo.addItem(goal["name"], goal["id"])
        controls.addWidget(self.goal_combo)
        controls.addWidget(QLabel("Safety:"))
        self.safety_combo = QComboBox()
        self.safety_combo.addItems(["Conservative", "Balanced", "Aggressive"])
        controls.addWidget(self.safety_combo)
        controls.addStretch(1)
        lay.addLayout(controls)

        self.recommendation_host = QFrame()
        self.recommendation_host.setProperty("role", "card")
        self.recommendation_layout = QVBoxLayout(self.recommendation_host)
        lay.addWidget(self.recommendation_host)

        lay.addWidget(CollapsibleSection(
            "Full Waystone modifier pool",
            self._full_pool(),
            expanded=False,
        ))
        lay.addWidget(CollapsibleSection(
            "Official patch guardrails and source limits",
            self._source_notes(),
            expanded=False,
        ))
        lay.addStretch(1)

        self.goal_combo.currentIndexChanged.connect(self._refresh)
        self.safety_combo.currentIndexChanged.connect(self._refresh)
        self._refresh()
        outer.addWidget(_scrollable(inner))

    def _summary_card(self):
        frame = QFrame()
        frame.setProperty("role", "card")
        lay = QVBoxLayout(frame)
        top = QHBoxLayout()
        top.addWidget(header("Research Status"))
        top.addStretch(1)
        top.addWidget(badge("database"))
        top.addWidget(badge("patch", self.store.meta["patch"]["version"]))
        top.addWidget(badge("opinion", "DRAFT"))
        lay.addLayout(top)
        active = len([m for m in self.mods if m.get("status") == "active"])
        disabled = len(self.mods) - active
        matched = len([m for m in self.mods if m.get("trade_stats")])
        lay.addWidget(QLabel(
            "%s active Waystone modifier groups, %s patch-disabled groups, %s groups with official stat matches."
            % (active, disabled, matched)
        ))
        lay.addWidget(dim(self.data.get("_source", "")))
        return frame

    def _selected_goal(self):
        goal_id = self.goal_combo.currentData()
        return next((g for g in self.goals if g["id"] == goal_id), self.goals[0] if self.goals else {})

    def _score(self, mod, goal):
        if mod.get("status") != "active":
            return -999
        prefer = set(goal.get("prefer_reward_tags", []))
        avoid = set(goal.get("avoid_danger_tags", []))
        reward = set(mod.get("reward_tags", []))
        danger = set(mod.get("danger_tags", []))

        score = 2 * len(reward & prefer) - 3 * len(danger & avoid)
        safety = self.safety_combo.currentText()
        if safety == "Conservative":
            score -= len(danger)
        elif safety == "Aggressive":
            score += min(2, len(reward))
        else:
            score -= len(danger & avoid)
        return score

    def _refresh(self):
        _clear_layout(self.recommendation_layout)
        goal = self._selected_goal()
        scored = [(self._score(mod, goal), mod) for mod in self.mods]
        active = [(score, mod) for score, mod in scored if mod.get("status") == "active"]
        best = [mod for score, mod in sorted(active, key=lambda x: x[0], reverse=True)[:8]]
        avoid = [
            mod for score, mod in sorted(active, key=lambda x: x[0])[:8]
            if score < 1 or "Avoid" in mod.get("recommendation", "")
        ]
        disabled = [mod for mod in self.mods if mod.get("status") != "active"]

        top = QHBoxLayout()
        top.addWidget(header(goal.get("name", "Waystone Goal")))
        top.addStretch(1)
        top.addWidget(badge("opinion", "RULES"))
        self.recommendation_layout.addLayout(top)
        self.recommendation_layout.addWidget(dim(goal.get("notes", "")))

        self.recommendation_layout.addWidget(header("Use First"))
        self.recommendation_layout.addWidget(self._mods_table(best, compact=True))
        self.recommendation_layout.addWidget(header("Check Before Running"))
        self.recommendation_layout.addWidget(self._mods_table(avoid or disabled, compact=True))

    def _tier_summary(self, mod):
        parts = []
        for tier in mod.get("tiers", []):
            first = tier.get("text", "").split("|")[0].strip()
            parts.append("%s: %s" % (tier.get("tier", "?"), first))
        return " ; ".join(parts)

    def _mod_text(self, mod):
        """In-game modifier text per tier — PoE2 shows text, not names/tags."""
        tiers = mod.get("tiers", [])
        if not tiers:
            return mod.get("name", "")
        lines = []
        for tier in tiers:
            text = tier.get("text", "").strip()
            label = tier.get("tier")
            lines.append(("%s: %s" % (label, text)) if label and len(tiers) > 1 else text)
        return "\n".join(lines)

    def _trade_ids(self, mod):
        ids = [s["id"] for s in mod.get("trade_stats", [])]
        return ", ".join(ids) if ids else "not exposed / not matched"

    def _status_for_mod(self, mod):
        if mod.get("status") != "active":
            return "conflict"
        return "confirmed" if mod.get("trade_stats") else "unknown"

    def _mods_table(self, mods, compact=False):
        if not mods:
            return dim("No matching Waystone modifiers for this view.")
        # In-game Waystones show modifier TEXT — text is the primary column.
        if compact:
            columns = ["Modifier text (as shown in game)", "Slot", "Recommendation"]
            rows = [[
                self._mod_text(mod),
                mod.get("slot", ""),
                mod.get("recommendation", ""),
            ] for mod in mods]
            return make_table(columns, rows, [self._status_for_mod(m) for m in mods],
                              stretch_column=0, expand=True)

        columns = ["Modifier text by tier (as shown in game)", "Slot", "Trade stat IDs",
                   "Reward tags", "Danger tags", "Recommendation"]
        rows = [[
            self._mod_text(mod),
            mod.get("slot", ""),
            self._trade_ids(mod),
            ", ".join(mod.get("reward_tags", [])) or "-",
            ", ".join(mod.get("danger_tags", [])) or "-",
            mod.get("recommendation", ""),
        ] for mod in mods]
        return make_table(columns, rows, [self._status_for_mod(m) for m in mods],
                          stretch_column=0, expand=True)

    def _full_pool(self):
        host = QWidget()
        lay = QVBoxLayout(host)
        lay.addWidget(dim(
            "The full pool includes active rows plus rows preserved as disabled by official patch notes."
        ))
        lay.addWidget(self._mods_table(self.mods, compact=False))
        return host

    def _source_notes(self):
        host = QWidget()
        lay = QVBoxLayout(host)
        for line in self.data.get("_limitations", []):
            lay.addWidget(dim("- " + line))
        for line in self.data.get("official_patch_guardrails", []):
            lay.addWidget(dim("- " + line))
        for src in self.data.get("sources", []):
            lay.addWidget(dim("- %s: %s" % (src.get("name", ""), src.get("url", ""))))
        return host
