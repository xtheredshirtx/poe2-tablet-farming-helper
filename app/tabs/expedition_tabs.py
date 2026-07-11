"""Expedition Tablet tab and Expedition Logbook Planner tab."""
from PySide6.QtWidgets import (
    QCheckBox, QGroupBox, QHBoxLayout, QLabel, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)

from ..widgets import dim, header, make_table, patch_bar, warn_panel


def _scrollable(inner):
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(inner)
    return scroll


class ExpeditionTabletTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        outer = QVBoxLayout(self)
        inner = QWidget()
        lay = QVBoxLayout(inner)

        lay.addWidget(header("Expedition Tablet", "h1"))
        lay.addWidget(patch_bar(store.patch_banner()))

        official = QGroupBox("Official 0.5.4 / 0.5.4b Expedition changes (GGG patch notes)")
        official_lay = QVBoxLayout(official)
        for line in store.expedition["official_054_changes"]:
            lbl = QLabel("• " + line)
            lbl.setWordWrap(True)
            official_lay.addWidget(lbl)
        lay.addWidget(official)

        lay.addWidget(header("Recommended tablet setups (community; IDs confirmed)"))
        setups = store.expedition["tablet_setups"]
        lay.addWidget(make_table(
            ["Goal", "Setup", "Trade stat IDs", "Confidence"],
            [[s["goal"], s["setup"], ", ".join(s["stat_ids"]), s["confidence"]]
             for s in setups],
            stretch_column=1, expand=True))

        lay.addWidget(header("Expedition Tablet suffixes"))
        mods = store.tablets["type_suffixes"]["Expedition Tablet"]
        lay.addWidget(make_table(
            ["Name", "Modifier text", "Roll", "Stat ID", "Rating*", "Best for"],
            [[m["name"], m["text"], m["roll"], m["stat_id"], m["rating"], m["best_for"]]
             for m in mods],
            [m["stat_status"] for m in mods],
            stretch_column=1, expand=True))

        lay.addWidget(header("Unique tablet"))
        fbt = next(u for u in store.tablets["uniques"] if u["name"] == "Forgotten By Time")
        lay.addWidget(make_table(
            ["Unique", "Effect", "Stat IDs", "Rating*", "Confidence"],
            [[fbt["name"], fbt["text"], ", ".join(fbt["stat_ids"]),
              fbt["rating"], fbt["confidence"]]],
            stretch_column=1, expand=True))

        lay.addWidget(header("Remnant priority (community; NOT retroactive)"))
        lay.addWidget(make_table(
            ["Priority", "Remnant"],
            [[r["priority"], r["remnant"]]
             for r in store.expedition["remnant_priority"]],
            stretch_column=1, expand=True))
        lay.addWidget(warn_panel([store.expedition["remnant_rule"]]))
        lay.addWidget(warn_panel(store.expedition["avoid_warnings"]))
        lay.addStretch(1)
        outer.addWidget(_scrollable(inner))


class LogbookPlannerTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        outer = QVBoxLayout(self)
        inner = QWidget()
        lay = QVBoxLayout(inner)

        lay.addWidget(header("Expedition Whispers Knowledge Base", "h1"))
        lay.addWidget(patch_bar(store.patch_banner()))
        owner_note = store.expedition.get("_owner_update")
        notes = [
            "Community spreadsheet data (Dracorath; rumor credit Guitaraholic). NOT official.",
            "F-rank maps can spawn untargetable enemies — avoid until verified fixed.",
        ]
        if owner_note:
            notes.insert(0, owner_note)
        lay.addWidget(warn_panel(notes))

        self._add_current_juice_rule(lay)

        lay.addWidget(header("Aldurs decision helper (spreadsheet rules)"))
        helper = QGroupBox("Should I use the Aldurs Saga on this map?")
        helper_lay = QVBoxLayout(helper)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Rumours on map:"))
        self.rumour_count = QSpinBox()
        self.rumour_count.setRange(0, 5)
        self.rumour_count.setValue(3)
        controls.addWidget(self.rumour_count)
        self.is_boss = QCheckBox("Boss map")
        controls.addWidget(self.is_boss)
        self.is_unique = QCheckBox("Unique map")
        controls.addWidget(self.is_unique)
        self.is_fallen_skies = QCheckBox("…it is Fallen Skies")
        controls.addWidget(self.is_fallen_skies)
        controls.addStretch(1)
        helper_lay.addLayout(controls)
        self.verdict = QLabel("")
        self.verdict.setWordWrap(True)
        helper_lay.addWidget(self.verdict)
        helper_lay.addWidget(dim(
            "Sheet rules: no Aldurs on Boss; no Aldurs on Unique maps except Fallen Skies; "
            "use with 3 rumours, not 2; confirm rumours don't change first."))
        for w in (self.rumour_count, ):
            w.valueChanged.connect(self._update_verdict)
        for w in (self.is_boss, self.is_unique, self.is_fallen_skies):
            w.toggled.connect(self._update_verdict)
        self._update_verdict()
        lay.addWidget(helper)

        lay.addWidget(header("Whisper rankings — what each whisper means and its value"))
        rumours = store.expedition["rumours"]
        lay.addWidget(make_table(
            ["Rank*", "Type", "Whisper", "Map", "Reward", "What it means", "How to use it"],
            [[r["rank"], r["type"], r["rumour"], r["map"], r["mods"],
              r["details"], r["note"]] for r in rumours],
            ["conflict" if r["rank"] == "F" else "confirmed" for r in rumours],
            stretch_column=5, expand=True))

        lay.addWidget(header("Sagas (community spreadsheet)"))
        sagas = store.expedition["sagas"]
        lay.addWidget(make_table(
            ["Saga", "Target", "Rank*", "Note", "Usage rule"],
            [[s["name"], s["target"], s["rank"], s["note"], s["rule"]]
             for s in sagas],
            stretch_column=4, expand=True))

        lay.addWidget(header("Tips preserved from the sheet"))
        for tip in store.expedition["tips"]:
            lbl = QLabel("• " + tip)
            lbl.setWordWrap(True)
            lay.addWidget(lbl)

        gvs = store.expedition["grand_vs_standard"]
        box = QGroupBox("Grand vs Standard Expedition")
        box_lay = QVBoxLayout(box)
        box_lay.addWidget(QLabel("Standard: " + gvs["standard"]))
        box_lay.addWidget(QLabel("Grand: " + gvs["grand"]))
        warn = QLabel("⚠ Open question: " + gvs["open_question"])
        warn.setProperty("role", "warn")
        for lbl in box.findChildren(QLabel):
            lbl.setWordWrap(True)
        box_lay.addWidget(warn)
        lay.addWidget(box)
        lay.addStretch(1)
        outer.addWidget(_scrollable(inner))

    def _add_current_juice_rule(self, lay):
        rule = self.store.expedition.get("current_juice_rule")
        if not rule:
            return

        box = QGroupBox("Current Expedition juice: use other tablets")
        box_lay = QVBoxLayout(box)
        self.expedition_juice_summary = QLabel(rule["summary"])
        self.expedition_juice_summary.setWordWrap(True)
        box_lay.addWidget(self.expedition_juice_summary)
        box_lay.addWidget(dim(rule["current_game_rule"]))

        mods_by_id = {m["id"]: m for m in self.store.tablet_juice_modifiers}
        rows = []
        status = []
        for target in rule.get("recommended_other_tablet_filters", []):
            mod = mods_by_id.get(target["modifier_id"], {})
            min_roll = mod.get("recommended_min_roll_for_filter")
            min_text = "" if min_roll is None else str(min_roll)
            risk = target.get("risk") or mod.get("risk_level") or "low"
            rows.append([
                target["label"],
                mod.get("modifier_text", target["modifier_id"]),
                min_text,
                mod.get("currency_juice_rating", ""),
                risk.upper(),
                target["why"],
            ])
            status.append("conflict" if risk == "high" else "confirmed")
        self.expedition_juice_table = make_table(
            ["Use", "Current tablet filter", "Min", "Rating*", "Risk", "Why"],
            rows, status, stretch_column=5, expand=True)
        box_lay.addWidget(self.expedition_juice_table)

        presets_by_id = {p["id"]: p for p in self.store.tablet_juice_presets}
        preset_rows = []
        for rec in rule.get("recommended_current_presets", []):
            preset = presets_by_id.get(rec["preset_id"], {})
            preset_rows.append([
                rec["label"],
                preset.get("tablet_type", "All tablets"),
                preset.get("mode", ""),
                rec["why"],
            ])
        if preset_rows:
            box_lay.addWidget(make_table(
                ["Preset", "Tablet type", "Mode", "When to use"],
                preset_rows, stretch_column=3, expand=True))

        master_rows = [
            [m["master"], m["node"], m["why"]]
            for m in rule.get("atlas_master_support", [])
        ]
        if master_rows:
            box_lay.addWidget(make_table(
                ["Master", "Node", "Why"],
                master_rows, stretch_column=2, expand=True))
        lay.addWidget(box)

    def _update_verdict(self):
        if self.is_boss.isChecked():
            text, ok = "NO — do not use Aldurs on Boss maps.", False
        elif self.is_unique.isChecked() and not self.is_fallen_skies.isChecked():
            text, ok = "NO — do not use Aldurs on Unique maps (Fallen Skies is the only exception).", False
        elif self.rumour_count.value() >= 3:
            text, ok = "YES — 3+ rumours. Confirm the rumours do not change before committing.", True
        elif self.rumour_count.value() == 2:
            text, ok = "NO — only 2 rumours means less content.", False
        else:
            text, ok = "NO — not enough rumours to justify the Saga.", False
        color = "#7ddc8f" if ok else "#f08a7a"
        self.verdict.setText("Verdict: " + text)
        self.verdict.setStyleSheet("color:%s;font-weight:bold;" % color)
