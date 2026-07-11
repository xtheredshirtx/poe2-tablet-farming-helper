"""Gear Presets and Crafting Materials trade panels (Phase 13 pack).

Guardrails: one user-triggered POST per search; one-click search uses ONLY
modifiers whose stat IDs were verified against official trade2 metadata
(2026-07-11); unverified rows stay visible as a copyable manual checklist.
"""
import json
import urllib.parse
import urllib.request
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGroupBox, QHBoxLayout, QLabel,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSplitter,
    QTabWidget, QVBoxLayout, QWidget,
)

from ..widgets import badge, dim, header, make_table, patch_bar, warn_panel
from .trade_builder import TradeBuilderTab, USER_AGENT

# Rare gear carries at most 6 explicit modifiers (3 prefixes + 3 suffixes) —
# the gear analogue of the tablet 4-modifier rule.
MAX_GEAR_MODS = 6


def _post_search(store, parent, query_payload, league, live=False):
    """Single user-confirmed POST to the official search API; opens result."""
    prompt = ("Send ONE search-creation POST to the official Path of Exile API "
              "and open the result in your browser?")
    if live:
        prompt += ("\n\nLIVE mode opens the official site's live-search view. "
                   "The live updates run in your browser on pathofexile.com — "
                   "this app never polls or watches results itself.")
    confirm = QMessageBox.question(
        parent, "Create official trade search", prompt,
        QMessageBox.Yes | QMessageBox.No)
    if confirm != QMessageBox.Yes:
        return
    url = store.meta["trade"]["search_endpoint_template"].format(
        league=urllib.parse.quote(league))
    req = urllib.request.Request(
        url, data=json.dumps(query_payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        QMessageBox.warning(parent, "Search failed",
                            "The official API request failed (no retries):\n%s" % exc)
        return
    search_id = body.get("id")
    if not search_id:
        QMessageBox.warning(parent, "Unexpected response",
                            json.dumps(body)[:400])
        return
    template = (store.meta["trade"]["live_url_template"] if live
                else store.meta["trade"]["result_url_template"])
    webbrowser.open(template.format(
        league=urllib.parse.quote(league), id=search_id))


class GearModRow(QWidget):
    """Selectable modifier row — same guardrail pattern as the tablet builder:
    unverified stat IDs cannot be selected."""

    def __init__(self, mod, group, on_change, parent=None):
        super().__init__(parent)
        self.mod = mod
        self.group = group
        from PySide6.QtWidgets import QCheckBox, QSpinBox
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 1, 2, 1)
        text = mod.get("official_text") or mod.get("stat_text") or mod.get("label")
        self.check = QCheckBox(text)
        self.check.setToolTip("%s\n%s" % (mod.get("why", ""), group))
        lay.addWidget(self.check, 5)
        lay.addWidget(QLabel("[%s, %s]" % (mod.get("priority", "?"),
                                           mod.get("mod_type", "?"))))
        lay.addWidget(QLabel("min:"))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 9999)
        self.min_spin.setSpecialValueText("—")
        if mod.get("min_value"):
            self.min_spin.setValue(int(mod["min_value"]))
        lay.addWidget(self.min_spin)
        verified = bool(mod.get("trade_ready")) and str(
            mod.get("trade_stat_id", "")).startswith("explicit.")
        self.verified = verified
        if verified:
            lay.addWidget(badge("official"))
        else:
            self.check.setEnabled(False)
            self.min_spin.setEnabled(False)
            b = badge("unknown")
            b.setToolTip("This modifier still needs official trade ID verification. "
                         "Use the checklist manually; one-click search is disabled "
                         "for this row until the stat is verified.")
            lay.addWidget(b)
        self.check.toggled.connect(on_change)
        self.min_spin.valueChanged.connect(on_change)

    def selected(self):
        return self.check.isChecked()

    def stat_filter(self):
        entry = {"id": self.mod["trade_stat_id"], "disabled": False}
        if self.min_spin.value() > 0:
            entry["value"] = {"min": self.min_spin.value()}
        return entry


class GearPresetsPanel(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.presets = store.gear_presets
        root = QVBoxLayout(self)
        root.addWidget(header("Gear Trade Presets", "h1"))
        root.addWidget(patch_bar(store.patch_banner()))
        root.addWidget(warn_panel([
            "Community/transcript presets (opinion). One-click search uses only "
            "modifiers verified against official trade2 metadata (2026-07-11); "
            "unverified rows stay on the manual checklist.",
        ]))

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Item category:"))
        self.category = QComboBox()
        cats = sorted({p["item_category"] for p in self.presets})
        self.category.addItems(["All"] + cats)
        controls.addWidget(self.category)
        controls.addWidget(QLabel("Goal / build:"))
        self.preset_combo = QComboBox()
        controls.addWidget(self.preset_combo, 1)
        controls.addWidget(QLabel("League:"))
        self.league = QComboBox()
        self.league.addItems(store.meta["leagues"])
        self.league.setCurrentText(store.settings.get("league", "Runes of Aldur"))
        controls.addWidget(self.league)
        root.addLayout(controls)

        # search options row (same logic as the tablet builder)
        opts = QHBoxLayout()
        opts.addWidget(QLabel("Trade type:"))
        self.status = QComboBox()
        for opt in store.meta["trade"]["status_options_labeled"]:
            self.status.addItem(opt["text"], opt["id"])
        idx = self.status.findData(store.settings.get(
            "trade_status", store.meta["trade"].get("default_status", "securable")))
        self.status.setCurrentIndex(idx if idx >= 0 else 0)
        opts.addWidget(self.status)
        opts.addWidget(QLabel("Match mode:"))
        self.match_mode = QComboBox()
        self.match_mode.addItems(["AND (all selected)", "COUNT (at least N)"])
        opts.addWidget(self.match_mode)
        opts.addWidget(QLabel("COUNT min:"))
        from PySide6.QtWidgets import QSpinBox
        self.count_min = QSpinBox()
        self.count_min.setRange(1, MAX_GEAR_MODS)
        opts.addWidget(self.count_min)
        opts.addStretch(1)
        root.addLayout(opts)

        split = QSplitter(Qt.Horizontal)
        self.detail_scroll = QScrollArea()
        self.detail_scroll.setWidgetResizable(True)
        split.addWidget(self.detail_scroll)

        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.addWidget(header("Query JSON (debug preview)"))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        rlay.addWidget(self.preview, 1)
        self.query_note = QLabel("")
        self.query_note.setWordWrap(True)
        rlay.addWidget(self.query_note)
        buttons = QHBoxLayout()
        self.copy_json_btn = QPushButton("Copy JSON")
        self.copy_json_btn.clicked.connect(
            lambda: QApplication.clipboard().setText(self.preview.toPlainText()))
        buttons.addWidget(self.copy_json_btn)
        self.copy_btn = QPushButton("Copy Search Checklist")
        self.copy_btn.setToolTip("Full checklist including unverified modifiers — "
                                 "paste it while searching manually on the trade site.")
        self.copy_btn.clicked.connect(self._copy_checklist)
        buttons.addWidget(self.copy_btn)
        rlay.addLayout(buttons)
        buttons2 = QHBoxLayout()
        self.search_btn = QPushButton("Create search && open in browser")
        self.search_btn.clicked.connect(lambda: self._run_search(live=False))
        buttons2.addWidget(self.search_btn)
        self.live_btn = QPushButton("Create LIVE search")
        self.live_btn.setToolTip(store.meta["trade"].get("live_note", ""))
        self.live_btn.clicked.connect(lambda: self._run_search(live=True))
        buttons2.addWidget(self.live_btn)
        rlay.addLayout(buttons2)
        rlay.addWidget(dim("Both buttons perform ONE user-triggered POST to the "
                           "official API, then open the official trade URL. LIVE "
                           "runs on the official site in your browser."))
        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        root.addWidget(split, 1)

        self.mod_rows = []
        self.category.currentIndexChanged.connect(self._rebuild_preset_list)
        self.preset_combo.currentIndexChanged.connect(self._show_preset)
        self.status.currentIndexChanged.connect(self._refresh)
        self.match_mode.currentIndexChanged.connect(self._refresh)
        self.count_min.valueChanged.connect(self._refresh)
        self._rebuild_preset_list()

    def _rebuild_preset_list(self):
        cat = self.category.currentText()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        for p in self.presets:
            if cat == "All" or p["item_category"] == cat:
                self.preset_combo.addItem(p["display_name"], p["id"])
        self.preset_combo.blockSignals(False)
        self._show_preset()

    def _current_preset(self):
        pid = self.preset_combo.currentData()
        return next((p for p in self.presets if p["id"] == pid), None)

    def _mod_lists(self, preset):
        for key, title in (("must_have_mods", "Must-have modifiers"),
                           ("optional_mods", "Strong optional modifiers")):
            mods = [m for m in preset.get(key) or [] if isinstance(m, dict)]
            if mods:
                yield key, title, mods

    def _show_preset(self):
        """Rebuild the left panel: preset info + selectable modifier rows.
        The preset pre-checks its must-have mods; everything stays editable,
        exactly like the tablet builder."""
        preset = self._current_preset()
        host = QWidget()
        lay = QVBoxLayout(host)
        self.mod_rows = []
        if preset is None:
            lay.addWidget(dim("No preset selected."))
            self.detail_scroll.setWidget(host)
            self._refresh()
            return
        top = QHBoxLayout()
        top.addWidget(header(preset["display_name"]))
        top.addStretch(1)
        top.addWidget(badge("opinion"))
        lay.addLayout(top)
        lay.addWidget(dim("Goal: %s   |   Patch %s, verified %s" % (
            preset["build_goal"], preset.get("patch", "?"),
            preset.get("last_verified", "?"))))
        cat_note = preset.get("trade_category_note") or ""
        if preset.get("trade_category"):
            lay.addWidget(dim("Official category: %s (%s)" % (
                preset["trade_category"], cat_note)))
        else:
            lay.addWidget(dim("No single official category — %s" % cat_note))

        for key, title, mods in self._mod_lists(preset):
            box = QGroupBox(title + "  (tick to include in the search)")
            blay = QVBoxLayout(box)
            blay.setSpacing(0)
            for m in mods:
                row = GearModRow(m, title, self._refresh)
                if key == "must_have_mods" and row.verified:
                    row.check.setChecked(True)
                self.mod_rows.append(row)
                blay.addWidget(row)
            lay.addWidget(box)

        for key, title in (("budget_mods", "Budget alternative"),
                           ("high_end_mods", "High-end target"),
                           ("avoid_notes", "Avoid / warnings")):
            lines = [x for x in preset.get(key) or [] if isinstance(x, str)]
            if lines:
                box = QGroupBox(title)
                blay = QVBoxLayout(box)
                for line in lines:
                    lbl = QLabel("• " + line)
                    lbl.setWordWrap(True)
                    if key == "avoid_notes":
                        lbl.setProperty("role", "warn")
                    blay.addWidget(lbl)
                lay.addWidget(box)
        lay.addStretch(1)
        self.detail_scroll.setWidget(host)
        self._refresh()

    def _selected_rows(self):
        return [r for r in self.mod_rows if r.selected()]

    def _build_query(self):
        preset = self._current_preset()
        query = {"status": {"option": self.status.currentData()
                            or self.store.settings.get("trade_status", "securable")}}
        if preset and preset.get("trade_category"):
            query["filters"] = {"type_filters": {"filters": {
                "category": {"option": preset["trade_category"]}}}}
        selected = self._selected_rows()
        if selected:
            if self.match_mode.currentIndex() == 0:
                group = {"type": "and",
                         "filters": [r.stat_filter() for r in selected]}
            else:
                group = {"type": "count",
                         "value": {"min": min(self.count_min.value(), len(selected))},
                         "filters": [r.stat_filter() for r in selected]}
            query["stats"] = [group]
        return {"query": query, "sort": {"price": "asc"}}

    def _refresh(self):
        self.preview.setPlainText(json.dumps(self._build_query(), indent=2))
        selected = self._selected_rows()
        n = len(selected)
        self.count_min.setEnabled(self.match_mode.currentIndex() == 1)
        and_mode = self.match_mode.currentIndex() == 0
        over_cap = and_mode and n > MAX_GEAR_MODS
        ok = n > 0 and not over_cap
        for btn in (self.search_btn, self.live_btn):
            btn.setEnabled(ok)
        if over_cap:
            self.query_note.setText(
                "%d modifiers selected in AND mode — rare gear can never have more "
                "than %d explicit modifiers, so this search cannot match anything. "
                "Deselect down to %d or switch to COUNT mode."
                % (n, MAX_GEAR_MODS, MAX_GEAR_MODS))
            self.query_note.setStyleSheet("color:#f08a7a;")
        elif n == 0:
            self.query_note.setText(
                "No verified modifiers selected. Tick verified rows to search, or "
                "use the checklist for unverified ones — one-click search stays "
                "disabled until at least one verified modifier is selected.")
            self.query_note.setStyleSheet("color:#e0a95a;")
        else:
            self.query_note.setText(
                "%d of max %d modifier(s) selected — all with officially verified "
                "stat IDs. Unverified rows cannot be selected." % (n, MAX_GEAR_MODS))
            self.query_note.setStyleSheet("color:#7ddc8f;")

    def _run_search(self, live=False):
        if not self._selected_rows():
            return
        _post_search(self.store, self, self._build_query(),
                     self.league.currentText(), live=live)

    def _copy_checklist(self):
        preset = self._current_preset()
        if preset is None:
            return
        lines = ["%s — %s (patch %s; community/transcript preset)" % (
            preset["display_name"], preset["build_goal"], preset.get("patch"))]
        for key, title, mods in self._mod_lists(preset):
            lines.append(title + ":")
            for m in mods:
                status = "VERIFIED" if m.get("trade_ready") else "manual search"
                lines.append("  - %s [%s, %s] (%s)" % (
                    m.get("official_text") or m.get("stat_text"),
                    m.get("priority", "?"), m.get("mod_type", "?"), status))
        for key, title in (("budget_mods", "Budget"), ("high_end_mods", "High-end"),
                           ("avoid_notes", "Avoid")):
            for line in preset.get(key) or []:
                if isinstance(line, str):
                    lines.append("%s: %s" % (title, line))
        QApplication.clipboard().setText("\n".join(lines))
        self.query_note.setText("Checklist copied to clipboard.")


class MaterialsPanel(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.materials = store.crafting_materials
        root = QVBoxLayout(self)
        root.addWidget(header("Crafting Materials — quick trade searches", "h1"))
        root.addWidget(dim("All %d item names verified against official trade2 items "
                           "metadata (2026-07-11). Each search is one user-triggered "
                           "POST that opens the official site." % len(self.materials)))
        rows = [[m["display_name"], m["item_type"],
                 ", ".join(m.get("used_for") or []) or "-",
                 "verified" if m.get("trade_ready") else "NOT VERIFIED"]
                for m in self.materials]
        self.table = make_table(
            ["Material", "Type", "Used by guide", "Name check"], rows,
            ["confirmed" if m.get("trade_ready") else "unknown"
             for m in self.materials],
            stretch_column=2)
        root.addWidget(self.table, 1)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("League:"))
        self.league = QComboBox()
        self.league.addItems(store.meta["leagues"])
        self.league.setCurrentText(store.settings.get("league", "Runes of Aldur"))
        controls.addWidget(self.league)
        self.search_btn = QPushButton("Open official trade search for selected material")
        self.search_btn.clicked.connect(self._run_search)
        controls.addWidget(self.search_btn)
        controls.addStretch(1)
        root.addLayout(controls)

    def _run_search(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return
        mat = self.materials[sel[0].row()]
        if not mat.get("trade_ready"):
            QMessageBox.information(self, "Not verified",
                                    "This material's exact item name is not verified yet.")
            return
        query = {"query": {"status": {"option": self.store.settings.get(
                     "trade_status", "securable")},
                 "type": mat["exact_name"]},
                 "sort": {"price": "asc"}}
        _post_search(self.store, self, query, self.league.currentText())


class TradeHubTab(QWidget):
    """Container: Tablets (existing builder) + Gear Presets + Materials."""

    def __init__(self, store, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        self.sub = QTabWidget()
        self.tablet_builder = TradeBuilderTab(store)
        self.sub.addTab(self.tablet_builder, "Tablets")
        self.gear = GearPresetsPanel(store)
        self.sub.addTab(self.gear, "Gear Presets")
        self.materials = MaterialsPanel(store)
        self.sub.addTab(self.materials, "Crafting Materials")
        root.addWidget(self.sub)

    # Delegation so existing dashboard/tablet-page routing keeps working.
    def set_tablet_type(self, tablet_type):
        self.tablet_builder.set_tablet_type(tablet_type)
        self.sub.setCurrentIndex(0)

    def __getattr__(self, name):
        # Forward attribute lookups (e.g. tests touching mod_rows, preset, …)
        return getattr(self.__dict__.get("tablet_builder") or object(), name)
