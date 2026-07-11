"""Focused per-tablet pages for Phase 4 UI reorganization."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QPushButton, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

from ..widgets import (
    CollapsibleSection, badge, dim, header, make_table, patch_bar,
    poe_item_card, rank_chip, warn_panel,
)


def _scrollable(widget):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll


def _row_status(row):
    if row.get("stat_status") != "confirmed":
        return row.get("stat_status")
    return "conflict" if row.get("confidence") == "conflict" else "confirmed"


def _table(columns, rows, statuses=None, stretch_column=1, max_height=None):
    # max_height is ignored since the Phase 7 big-screen pass: tables now
    # expand to their content so the page scrolls, not a tiny inner scrollbar.
    return make_table(columns, rows, statuses, stretch_column=stretch_column,
                      expand=True)


class TabletTypePage(QWidget):
    open_trade_builder = Signal(str)

    def __init__(self, store, base_name, parent=None):
        super().__init__(parent)
        self.store = store
        self.base_name = base_name
        self.base = next(b for b in store.tablets["bases"] if b["name"] == base_name)
        self.strategy = next(
            (s for s in store.strategies if s.get("tablet_type") == base_name), None)
        self.uniques = [u for u in store.tablets["uniques"] if u["base"] == base_name]

        outer = QVBoxLayout(self)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setSpacing(10)

        lay.addWidget(header(base_name, "h1"))
        lay.addWidget(patch_bar(store.patch_banner()))
        lay.addWidget(self._base_summary())
        lay.addWidget(self._best_setup_card())

        warnings = []
        if self.strategy:
            warnings.extend(self.strategy.get("warnings", []))
            if not self.strategy.get("trade_ready", True):
                warnings.append("Trade search is disabled for this tablet until missing data is verified.")
        if base_name == "Temple Tablet":
            warnings.append("Temple/Vaal Beacon data is experimental and incomplete.")
        if warnings:
            lay.addWidget(warn_panel(warnings))

        lay.addWidget(self._section(
            "Type-specific modifiers",
            self._type_modifiers(),
            expanded=True,
        ))
        lay.addWidget(self._section(
            "Unique tablets for this type",
            self._unique_tablets(),
            expanded=bool(self.uniques) and base_name in ("Expedition Tablet", "Ritual Tablet"),
        ))
        lay.addWidget(self._section(
            "Shared high-value modifiers",
            self._shared_modifiers(),
            expanded=False,
        ))
        lay.addWidget(self._section(
            "All applicable modifiers and guardrails",
            self._all_modifiers(),
            expanded=False,
        ))
        lay.addWidget(self._section(
            "System rules and source notes",
            self._system_notes(),
            expanded=False,
        ))
        lay.addStretch(1)
        outer.addWidget(_scrollable(inner))

    def _base_summary(self):
        frame = QFrame()
        frame.setProperty("role", "card")
        lay = QVBoxLayout(frame)
        top = QHBoxLayout()
        top.addWidget(header("What this tablet does"))
        top.addStretch(1)
        top.addWidget(badge("database"))
        top.addWidget(badge("patch", self.store.meta["patch"]["version"]))
        lay.addLayout(top)
        lay.addWidget(QLabel(self.base["function"]))
        lay.addWidget(dim(
            "Uses: %s   |   Trade type: %s   |   Confidence: %s"
            % (self.base["uses"], self.base["trade_type"], self.base["confidence"])))
        return frame

    def _best_setup_card(self):
        """Community Best Setup rendered like an in-game PoE item tooltip."""
        frame = QFrame()
        frame.setProperty("role", "card")
        lay = QVBoxLayout(frame)
        top = QHBoxLayout()
        top.addWidget(header("Community Best Setup"))
        top.addStretch(1)
        if self.strategy:
            top.addWidget(rank_chip(self.strategy["budget_rating"]))
            top.addWidget(rank_chip(self.strategy["high_investment_rating"]))
        top.addWidget(badge("opinion"))
        lay.addLayout(top)

        if not self.strategy:
            lay.addWidget(dim("No strategy mapping exists yet for this tablet."))
            return frame

        s = self.strategy
        info = [
            ("Budget rating: %s   |   High investment: %s"
             % (s["budget_rating"], s["high_investment_rating"]), "info"),
            ("Confidence: %s" % s["confidence"], "info"),
        ]
        # The game shows modifier TEXT, not names — resolve names to text.
        mods = [(self.store.mod_display_text(m), "mod") for m in s["best_mods"]]
        setups = [
            ("Budget: %s" % s["budget_setup"], "white"),
            ("High investment: %s" % s["high_investment_setup"], "white"),
        ]
        bottom = [("Rewards: %s" % s["rewards"], "gold"),
                  ("Main danger: %s" % s["main_danger"], "warn")]
        for warning in s.get("warnings", []):
            bottom.append(("⚠ " + warning, "warn"))

        card = poe_item_card(
            s["name"], self.base_name, [info, mods, setups, bottom])
        card_row = QHBoxLayout()
        card_row.addStretch(1)
        card_row.addWidget(card, 4)
        card_row.addStretch(1)
        lay.addLayout(card_row)
        lay.addWidget(dim("Community/editorial opinion — not official. Blue lines are "
                          "the modifiers the community recommends rolling."))

        buttons = QHBoxLayout()
        trade = QPushButton("Build trade search for this tablet")
        if s.get("trade_ready", True):
            trade.clicked.connect(lambda: self.open_trade_builder.emit(self.base_name))
        else:
            trade.setEnabled(False)
            trade.setToolTip("Disabled until missing or conflicted stat IDs are verified.")
        buttons.addWidget(trade)
        buttons.addStretch(1)
        lay.addLayout(buttons)
        return frame

    def _type_modifiers(self):
        host = QWidget()
        lay = QVBoxLayout(host)
        mods = self.store.tablets["type_suffixes"].get(self.base_name, [])
        if not mods:
            lay.addWidget(dim("No type-specific suffixes are confirmed for this tablet yet."))
            return host
        lay.addWidget(dim(
            "These are the modifiers most specific to this tablet type. Red/orange rows need caution."))
        lay.addWidget(_table(
            ["Name", "Modifier text", "Roll", "Trade stat ID", "Rating*", "Best for", "Confidence"],
            [[m["name"], m["text"], m["roll"], m["stat_id"], m["rating"],
              m["best_for"], m["confidence"]] for m in mods],
            [_row_status(m) for m in mods],
            stretch_column=1,
            max_height=360,
        ))
        return host

    def _unique_tablets(self):
        host = QWidget()
        lay = QVBoxLayout(host)
        if not self.uniques:
            lay.addWidget(dim("No unique tablet was listed for this base in the Phase 2 trade metadata."))
            return host
        lay.addWidget(_table(
            ["Unique", "Effect", "Stat IDs", "Rating*", "Confidence"],
            [[u["name"], u["text"], ", ".join(u["stat_ids"]) or "UNKNOWN",
              u["rating"], u["confidence"]] for u in self.uniques],
            [u["stat_status"] if u["stat_status"] != "confirmed"
             else ("conflict" if u["confidence"] == "conflict" else "confirmed")
             for u in self.uniques],
            stretch_column=1,
            max_height=240,
        ))
        for u in self.uniques:
            note = u.get("conflict") or u.get("warning") or u.get("note")
            if note:
                lay.addWidget(dim("%s: %s" % (u["name"], note)))
        return host

    def _shared_modifiers(self):
        host = QWidget()
        lay = QVBoxLayout(host)
        priority = {"SS", "S", "A", "A/S", "S/SS"}
        mods = [m for m in (self.store.tablets["shared_prefixes"]
                            + self.store.tablets["shared_suffixes"])
                if m["rating"] in priority]
        lay.addWidget(dim("Shared modifiers that commonly matter before niche side-content rows."))
        lay.addWidget(_table(
            ["Name", "Modifier text", "Roll", "Trade stat ID", "Rating*", "Best for"],
            [[m["name"], m["text"], m["roll"], m["stat_id"], m["rating"],
              m["best_for"]] for m in mods],
            [_row_status(m) for m in mods],
            stretch_column=1,
            max_height=300,
        ))
        return host

    def _all_modifiers(self):
        host = QWidget()
        lay = QVBoxLayout(host)
        mods = self.store.modifiers_for_type(self.base_name)
        lay.addWidget(dim(
            "Full applicable pool: shared prefixes, shared suffixes, and this tablet's suffixes. "
            "Disabled/conflicted rows are still shown for transparency."))
        lay.addWidget(_table(
            ["Slot", "Name", "Modifier text", "Roll", "Stat ID", "Rating*", "Confidence"],
            [[m["slot"], m["name"], m["text"], m["roll"], m["stat_id"],
              m["rating"], m["confidence"]] for m in mods],
            [_row_status(m) for m in mods],
            stretch_column=2,
        ))
        return host

    def _system_notes(self):
        host = QWidget()
        lay = QVBoxLayout(host)
        for line in self.store.tablets["system_rules"]:
            lbl = QLabel("- " + line)
            lbl.setWordWrap(True)
            lay.addWidget(lbl)
        if self.base_name == "Irradiated Tablet":
            lay.addWidget(dim(self.store.tablets.get("irradiated_note", "")))
        if self.strategy:
            lay.addWidget(dim("Atlas/Master notes: " + self.strategy["atlas_choices"]))
            if self.strategy.get("avoid"):
                lay.addWidget(dim("Avoid: " + ", ".join(self.strategy["avoid"])))
        return host

    def _section(self, title, content, expanded=False):
        return CollapsibleSection(title, content, expanded=expanded)


class TabletHubTab(QWidget):
    open_trade_builder = Signal(str)

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)

        self.nav = QListWidget()
        self.nav.setMaximumWidth(220)
        for base in store.tablet_base_names():
            self.nav.addItem(base.replace(" Tablet", ""))
        root.addWidget(self.nav)

        self.pages = QStackedWidget()
        self.page_by_base = {}
        for base in store.tablet_base_names():
            page = TabletTypePage(store, base)
            page.open_trade_builder.connect(self.open_trade_builder.emit)
            self.page_by_base[base] = page
            self.pages.addWidget(page)
        root.addWidget(self.pages, 1)

        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)

    def show_tablet_type(self, tablet_type):
        names = self.store.tablet_base_names()
        if tablet_type in names:
            self.nav.setCurrentRow(names.index(tablet_type))
