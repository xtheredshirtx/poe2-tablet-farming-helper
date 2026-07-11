"""Trade Search Builder.

Guardrails (from IMPLEMENTATION_READINESS_REPORT.md):
- Only modifiers with confirmed official stat IDs can be selected; conflicted or
  unknown rows are disabled and explain why.
- One user-triggered POST maximum per click; no scraping, no polling, no
  background searches. Results open in the user's default browser on the
  official site.
"""
import json
import urllib.parse
import urllib.request
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea,
    QSpinBox, QSplitter, QVBoxLayout, QWidget, QApplication,
)

from ..widgets import badge, dim, header, patch_bar, rank_chip, warn_panel

USER_AGENT = "POE2FarmingHelper/0.9.1 (unofficial open-source helper; user-initiated searches only)"
ANY = "Any"
MANUAL_PRESET = "Manual (no preset)"
MODE_MANUAL = "Manual"
MODE_JUICE = "Best Currency Juice"
MODE_BUDGET = "Budget"
MODE_HIGH = "High Investment"
# Tablets cannot have more than 4 modifiers, so searching for more than 4
# required modifiers can never match a real tablet. COUNT-mode presets may use
# more than 4 candidate filters as long as the required count stays <= 4.
MAX_TABLET_MODS = 4


class ModRow(QWidget):
    def __init__(self, mod, on_change, parent=None, allow_unready_select=False):
        super().__init__(parent)
        self.mod = mod
        self.allow_unready_select = allow_unready_select
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 1, 2, 1)
        self.check = QCheckBox(mod["name"])
        self.check.setToolTip(mod["text"])
        lay.addWidget(self.check, 2)
        text = QLabel(mod["text"])
        text.setProperty("role", "dim")
        lay.addWidget(text, 5)
        lay.addWidget(QLabel("min:"))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 999)
        self.min_spin.setSpecialValueText("—")
        lay.addWidget(self.min_spin)
        ready = mod.get("trade_ready", False)
        if not ready:
            self.check.setEnabled(bool(allow_unready_select))
            self.min_spin.setEnabled(bool(allow_unready_select))
            why = mod.get("conflict") or "UNKNOWN - NEEDS VERIFICATION"
            kind = "conflict" if mod.get("stat_status") in ("conflict", "duplicate") else "unknown"
            b = badge(kind)
            b.setToolTip(why)
            self.check.setToolTip("%s\n%s: %s" % (
                mod["text"],
                "Planning only" if allow_unready_select else "Disabled",
                why))
            lay.addWidget(b)
        else:
            lay.addWidget(badge("official" if mod.get("confidence") == "official" else "database"))
        if mod.get("currency_juice_rating"):
            lay.addWidget(rank_chip(mod["currency_juice_rating"]))
        if str(mod.get("risk_level", "")).lower() in ("high", "very_high"):
            lay.addWidget(badge("conflict", "HIGH RISK"))
        self.check.toggled.connect(on_change)
        self.min_spin.valueChanged.connect(on_change)

    def selected(self):
        return self.check.isChecked()

    def stat_filter(self):
        if self.mod.get("trade_filter_kind") == "type_only":
            return None
        entry = {"id": self.mod["stat_id"], "disabled": False}
        if self.min_spin.value() > 0:
            entry["value"] = {"min": self.min_spin.value()}
        return entry


class TradeBuilderTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        self.mod_rows = []

        root = QVBoxLayout(self)
        root.addWidget(header("Trade Search Builder", "h1"))
        root.addWidget(patch_bar(store.patch_banner()))
        root.addWidget(warn_panel([
            store.meta["trade"]["tos_note"],
            "Query shape is research-grade: validate results on the official site. "
            + store.meta["trade"]["deep_link_note"],
        ]))

        split = QSplitter(Qt.Horizontal)

        # ---- left: form -------------------------------------------------
        left = QWidget()
        form = QVBoxLayout(left)

        top = QGroupBox("Search filters")
        grid = QGridLayout(top)
        self._loading_presets = False
        grid.addWidget(QLabel("Filter mode:"), 0, 0)
        self.filter_mode = QComboBox()
        self.filter_mode.addItem(MODE_MANUAL, MODE_MANUAL)
        self.filter_mode.addItem(MODE_JUICE, MODE_JUICE)
        self.filter_mode.addItem(MODE_BUDGET, MODE_BUDGET)
        self.filter_mode.addItem(MODE_HIGH, MODE_HIGH)
        self.filter_mode.setToolTip(
            "Manual uses verified tablet modifier rows. Juice modes load the "
            "Phase 10 tablet-juice data pack and keep rankings labeled opinion.")
        grid.addWidget(self.filter_mode, 0, 1, 1, 3)
        grid.addWidget(QLabel("Preset:"), 1, 0)
        self.preset = QComboBox()
        self.preset.setToolTip(
            "Community-rated filter presets (opinion). COUNT presets may use "
            "more than %d candidate filters, but cannot require more than %d "
            "mods on a real tablet." % (MAX_TABLET_MODS, MAX_TABLET_MODS))
        self.preset.currentIndexChanged.connect(self._apply_preset)
        grid.addWidget(self.preset, 1, 1, 1, 3)
        self.preset_desc = QLabel("")
        self.preset_desc.setWordWrap(True)
        self.preset_desc.setProperty("role", "dim")
        grid.addWidget(self.preset_desc, 2, 0, 1, 4)
        grid.addWidget(QLabel("League:"), 3, 0)
        self.league = QComboBox()
        self.league.addItems(store.meta["leagues"])
        self.league.setCurrentText(store.settings.get("league", "Runes of Aldur"))
        grid.addWidget(self.league, 3, 1)
        grid.addWidget(QLabel("Tablet type:"), 3, 2)
        self.tablet_type = QComboBox()
        self.tablet_type.addItems([ANY] + store.tablet_base_names())
        grid.addWidget(self.tablet_type, 3, 3)
        grid.addWidget(QLabel("Rarity:"), 4, 0)
        self.rarity = QComboBox()
        self.rarity.addItems([ANY] + store.meta["trade"]["rarity_options"])
        grid.addWidget(self.rarity, 4, 1)
        grid.addWidget(QLabel("Corrupted:"), 4, 2)
        self.corrupted = QComboBox()
        self.corrupted.addItems([ANY, "No", "Yes"])
        grid.addWidget(self.corrupted, 4, 3)
        grid.addWidget(QLabel("Trade type:"), 5, 0)
        self.status = QComboBox()
        # Official PoE2 trade options (labels from GGG's filters metadata):
        # "Instant Buyout" = buy instantly from the seller's shop.
        for opt in store.meta["trade"]["status_options_labeled"]:
            self.status.addItem(opt["text"], opt["id"])
        default_status = store.settings.get(
            "trade_status", store.meta["trade"].get("default_status", "securable"))
        idx = self.status.findData(default_status)
        self.status.setCurrentIndex(idx if idx >= 0 else 0)
        grid.addWidget(self.status, 5, 1)
        grid.addWidget(QLabel("Match mode:"), 5, 2)
        self.match_mode = QComboBox()
        self.match_mode.addItems(["AND (all selected)", "COUNT (at least N)"])
        grid.addWidget(self.match_mode, 5, 3)
        grid.addWidget(QLabel("COUNT min:"), 6, 0)
        self.count_min = QSpinBox()
        self.count_min.setRange(1, MAX_TABLET_MODS)
        grid.addWidget(self.count_min, 6, 1)
        top.setLayout(grid)
        form.addWidget(top)

        form.addWidget(header("Modifiers / juice filters"))
        self.mods_scroll = QScrollArea()
        self.mods_scroll.setWidgetResizable(True)
        form.addWidget(self.mods_scroll, 1)

        for w in (self.league, self.rarity, self.corrupted,
                  self.status, self.match_mode):
            w.currentIndexChanged.connect(self._refresh)
        self.count_min.valueChanged.connect(self._refresh)
        self.tablet_type.currentIndexChanged.connect(self._on_tablet_type_changed)
        self.filter_mode.currentIndexChanged.connect(self._on_filter_mode_changed)

        split.addWidget(left)

        # ---- right: query preview + actions -----------------------------
        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.addWidget(header("Query JSON (debug preview)"))
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        rlay.addWidget(self.preview, 1)
        self.guard_label = QLabel("")
        self.guard_label.setWordWrap(True)
        rlay.addWidget(self.guard_label)
        buttons = QHBoxLayout()
        self.copy_btn = QPushButton("Copy JSON")
        self.copy_btn.clicked.connect(self._copy_json)
        buttons.addWidget(self.copy_btn)
        self.site_btn = QPushButton("Open official trade site")
        self.site_btn.clicked.connect(
            lambda: webbrowser.open(self.store.meta["trade"]["trade_site_url"]))
        buttons.addWidget(self.site_btn)
        self.search_btn = QPushButton("Create search && open in browser")
        self.search_btn.clicked.connect(lambda: self._create_search(live=False))
        buttons.addWidget(self.search_btn)
        self.live_btn = QPushButton("Create LIVE search")
        self.live_btn.setToolTip(store.meta["trade"].get("live_note", ""))
        self.live_btn.clicked.connect(lambda: self._create_search(live=True))
        buttons.addWidget(self.live_btn)
        rlay.addLayout(buttons)
        rlay.addWidget(dim("Both buttons perform ONE user-triggered POST to the official "
                           "API, then open the official trade URL. LIVE opens the official "
                           "site's own live-search view; the app itself never polls or "
                           "watches results."))
        split.addWidget(right)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 2)
        root.addWidget(split, 1)

        self._populate_presets()
        self._rebuild_mods()

    # ------------------------------------------------------------------
    def set_tablet_type(self, tablet_type):
        idx = self.tablet_type.findText(tablet_type)
        if idx >= 0:
            self.tablet_type.setCurrentIndex(idx)

    def _on_filter_mode_changed(self):
        self._populate_presets()
        self._rebuild_mods()

    def _on_tablet_type_changed(self):
        self._populate_presets()
        self._rebuild_mods()

    def _is_juice_mode(self):
        return self.filter_mode.currentData() in (MODE_JUICE, MODE_BUDGET, MODE_HIGH)

    def _humanize_juice_id(self, raw):
        text = raw
        for prefix in ("shared_prefix_", "shared_suffix_", "exp_suffix_", "rit_suffix_",
                       "breach_suffix_", "deli_suffix_", "abyss_suffix_",
                       "overseer_suffix_", "temple_suffix_"):
            text = text.replace(prefix, "")
        return text.replace("_", " ").title()

    def _juice_row(self, mod):
        stat_id = mod.get("trade_stat_id", "")
        return {
            "name": self._humanize_juice_id(mod["id"]),
            "text": mod["modifier_text"],
            "stat_id": stat_id,
            "trade_ready": bool(mod.get("trade_ready")),
            "confidence": "official" if mod.get("trade_ready") else "unknown",
            "conflict": mod.get("verification_note") or "Needs official trade2 stat ID verification",
            "currency_juice_rating": mod.get("currency_juice_rating"),
            "risk_level": mod.get("risk_level"),
            "trade_filter_kind": mod.get("trade_filter_kind", "explicit_stat"),
            "juice_id": mod["id"],
            "best_for": mod.get("best_for", []),
        }

    def _juice_mods_for_type(self):
        base = self.tablet_type.currentText()
        mode = self.filter_mode.currentData()
        rows = []
        for mod in self.store.tablet_juice_modifiers:
            if not mod.get("current_game_available", True):
                continue
            tablet_type = mod.get("tablet_type")
            if base == ANY:
                if tablet_type != "All tablets":
                    continue
            elif tablet_type not in ("All tablets", base):
                continue
            rating = str(mod.get("currency_juice_rating", ""))
            risk = str(mod.get("risk_level", "")).lower()
            if mode == MODE_BUDGET and ("HIGH_RISK" in rating or risk in ("high", "very_high")):
                continue
            rows.append(mod)
        return [self._juice_row(m) for m in sorted(
            rows, key=lambda x: x.get("priority", 0), reverse=True)]

    def _preset_rows(self):
        if not self._is_juice_mode():
            return self.store.trade_presets
        base = self.tablet_type.currentText()
        mode = self.filter_mode.currentData()
        rows = []
        for preset in self.store.tablet_juice_presets:
            if not preset.get("current_game_available", True):
                continue
            ptype = preset.get("tablet_type")
            if base == ANY:
                if ptype != "All tablets":
                    continue
            elif ptype not in ("All tablets", base):
                continue
            name_id = ("%s %s" % (preset.get("id", ""), preset.get("name", ""))).lower()
            if mode == MODE_BUDGET and "high" in name_id:
                continue
            if mode == MODE_HIGH and ptype == "All tablets" and "high" not in name_id:
                continue
            rows.append(preset)
        return rows

    def _populate_presets(self):
        self._loading_presets = True
        self.preset.blockSignals(True)
        self.preset.clear()
        self.preset.addItem(MANUAL_PRESET, None)
        for p in self._preset_rows():
            self.preset.addItem(p["name"], p["id"])
        self.preset.blockSignals(False)
        self._loading_presets = False
        self.preset_desc.setText("")

    def _apply_preset(self):
        if self._loading_presets:
            return
        preset_id = self.preset.currentData()
        if preset_id is None:
            self.preset_desc.setText("")
            self._refresh()
            return
        if not self._is_juice_mode():
            preset = next(p for p in self.store.trade_presets if p["id"] == preset_id)
            self.preset_desc.setText(
                "%s  [community opinion]" % preset.get("description", ""))
            idx = self.tablet_type.findText(preset.get("tablet_type", ANY))
            self.tablet_type.setCurrentIndex(idx if idx >= 0 else 0)  # rebuilds rows
            wanted = preset.get("mods", [])[:MAX_TABLET_MODS]
            for row in self.mod_rows:
                should = row.mod["name"] in wanted and row.check.isEnabled()
                row.check.blockSignals(True)
                row.check.setChecked(should)
                row.check.blockSignals(False)
            self.match_mode.setCurrentIndex(
                1 if preset.get("match_mode", "count") == "count" else 0)
            self.count_min.setValue(min(preset.get("count_min", 1), MAX_TABLET_MODS))
            self._refresh()
            return

        preset = next(p for p in self.store.tablet_juice_presets if p["id"] == preset_id)
        idx = self.tablet_type.findText(preset.get("tablet_type", ANY))
        if idx >= 0 and self.tablet_type.currentIndex() != idx:
            self.tablet_type.setCurrentIndex(idx)  # rebuilds rows
        wanted = {f["modifier_id"]: f for f in preset.get("filters", [])}
        for row in self.mod_rows:
            filt = wanted.get(row.mod.get("juice_id"))
            row.check.blockSignals(True)
            row.check.setChecked(bool(filt))
            row.check.blockSignals(False)
            if filt and filt.get("min") is not None:
                row.min_spin.setValue(int(filt["min"]))
        self.match_mode.setCurrentIndex(1 if preset.get("mode", "COUNT") == "COUNT" else 0)
        self.count_min.setValue(min(preset.get("count_min", 1), MAX_TABLET_MODS))
        self.preset_desc.setText(
            "%s  [community opinion; %s]" % (
                preset.get("description", ""),
                "official stat IDs verified" if preset.get("trade_ready")
                else preset.get("reason_disabled", "needs verification")))
        self._refresh()

    def _rebuild_mods(self):
        host = QWidget()
        lay = QVBoxLayout(host)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(0)
        self.mod_rows = []
        base = self.tablet_type.currentText()
        if self._is_juice_mode():
            mods = self._juice_mods_for_type()
            allow_unready = True
        elif base == ANY:
            mods = (self.store.tablets["shared_prefixes"]
                    + self.store.tablets["shared_suffixes"])
            allow_unready = False
        else:
            mods = self.store.modifiers_for_type(base)
            allow_unready = False
        for mod in mods:
            row = ModRow(mod, self._refresh, allow_unready_select=allow_unready)
            self.mod_rows.append(row)
            lay.addWidget(row)
        lay.addStretch(1)
        self.mods_scroll.setWidget(host)
        self._refresh()

    def _build_query(self):
        query = {"status": {"option": self.status.currentData()}}
        base = self.tablet_type.currentText()
        if base != ANY:
            query["type"] = base
        type_filters = {"category": {"option": self.store.meta["trade"]["item_category"]}}
        if self.rarity.currentText() != ANY:
            type_filters["rarity"] = {"option": self.rarity.currentText()}
        filters = {"type_filters": {"filters": type_filters}}
        if self.corrupted.currentText() != ANY:
            filters["misc_filters"] = {"filters": {
                "corrupted": {"option": "true" if self.corrupted.currentText() == "Yes" else "false"}}}
        query["filters"] = filters
        selected = [r for r in self.mod_rows if r.selected()]
        stat_filters = [f for f in (r.stat_filter() for r in selected) if f is not None]
        if stat_filters:
            if self.match_mode.currentIndex() == 0:
                group = {"type": "and", "filters": stat_filters}
            else:
                group = {"type": "count",
                         "value": {"min": min(self.count_min.value(), len(stat_filters))},
                         "filters": stat_filters}
            query["stats"] = [group]
        return {"query": query, "sort": {"price": "asc"}}

    def _refresh(self):
        payload = self._build_query()
        self.preview.setPlainText(json.dumps(payload, indent=2))
        selected = [r for r in self.mod_rows if r.selected()]
        n = len(selected)
        unready = [r for r in selected if not r.mod.get("trade_ready")]
        self.count_min.setEnabled(self.match_mode.currentIndex() == 1)
        over_cap = self.match_mode.currentIndex() == 0 and n > MAX_TABLET_MODS
        can_search = not over_cap and not unready
        for btn in (self.search_btn, self.live_btn):
            btn.setEnabled(can_search)
        if unready:
            self.guard_label.setText(
                "%d selected filter(s), but %d still need official trade2 stat ID "
                "verification. You can plan with them, but official search is locked."
                % (n, len(unready)))
            self.guard_label.setStyleSheet("color:#e0a95a;")
        elif over_cap:
            self.guard_label.setText(
                "%d required modifiers selected in AND mode. Tablets can never have "
                "more than %d explicit modifiers, so switch to COUNT mode or deselect "
                "down to %d." % (n, MAX_TABLET_MODS, MAX_TABLET_MODS))
            self.guard_label.setStyleSheet("color:#f08a7a;")
        elif self.match_mode.currentIndex() == 1 and n > MAX_TABLET_MODS:
            self.guard_label.setText(
                "%d candidate filters selected in COUNT mode; requiring at least %d. "
                "This is valid because a real tablet only needs to match the COUNT "
                "minimum, not every candidate." % (n, self.count_min.value()))
            self.guard_label.setStyleSheet("color:#7ddc8f;")
        else:
            self.guard_label.setText(
                "%d selected filter(s); all selected trade filters are verified "
                "against official trade2 metadata." % n)
            self.guard_label.setStyleSheet("color:#7ddc8f;")

    def _copy_json(self):
        QApplication.clipboard().setText(self.preview.toPlainText())

    def _create_search(self, live=False):
        selected = [r for r in self.mod_rows if r.selected()]
        unready = [r for r in selected if not r.mod.get("trade_ready")]
        if unready:
            QMessageBox.warning(
                self, "Needs verification",
                "One or more selected filters still need official trade2 stat ID "
                "verification. Official search generation is locked for this "
                "planning-only selection.")
            return
        if self.match_mode.currentIndex() == 0 and len(selected) > MAX_TABLET_MODS:
            QMessageBox.warning(
                self, "Too many required modifiers",
                "Tablets cannot have more than %d explicit modifiers. Switch to "
                "COUNT mode or select fewer required modifiers." % MAX_TABLET_MODS)
            return
        prompt = ("Send ONE search-creation POST to the official Path of Exile API "
                  "and open the result in your browser?")
        if live:
            prompt += ("\n\nLIVE mode opens the official site's live-search view. "
                       "The live updates run in your browser on pathofexile.com — "
                       "this app never polls or watches results itself.")
        confirm = QMessageBox.question(
            self, "Create official trade search", prompt,
            QMessageBox.Yes | QMessageBox.No)
        if confirm != QMessageBox.Yes:
            return
        league = self.league.currentText()
        url = self.store.meta["trade"]["search_endpoint_template"].format(
            league=urllib.parse.quote(league))
        payload = json.dumps(self._build_query()).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload, method="POST",
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # network/HTTP errors -> tell the user, do not retry
            QMessageBox.warning(
                self, "Search failed",
                "The official API request failed (no retries were attempted):\n%s\n\n"
                "You can still copy the JSON and use the official site manually." % exc)
            return
        search_id = body.get("id")
        if not search_id:
            QMessageBox.warning(self, "Unexpected response",
                                "No search id returned:\n%s" % json.dumps(body)[:500])
            return
        template = (self.store.meta["trade"]["live_url_template"] if live
                    else self.store.meta["trade"]["result_url_template"])
        result_url = template.format(
            league=urllib.parse.quote(league), id=search_id)
        webbrowser.open(result_url)
        total = body.get("total")
        if total == 0:
            QMessageBox.information(
                self, "Search created",
                "Search created (id %s) but the API reported 0 matches. The query "
                "shape is still research-grade — verify on the official site." % search_id)
