"""Crafting tab (Phase 6): Craft of Exile POE2 gear/weapon crafting data.

Eight progressive-disclosure sections behind a left-side navigator:
Overview, Base Browser, Modifier Explorer, Crafting Methods,
Omens / Essences / Catalysts, Craft Guides, Cost Planner, Source Confidence.

All data is third-party (Craft of Exile beta). No simulation, no invented
values; unknown/omitted fields stay visible as gaps.
"""
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QPlainTextEdit, QPushButton, QSpinBox, QSplitter, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from ..datastore import APP_DIR
from ..widgets import CollapsibleSection, badge, dim, header, make_table, warn_panel

MAX_ROWS = 800
ALL = "All"

USER_PRICES_FILE = APP_DIR / "user_prices.json"

NAV_SECTIONS = [
    "Craft", "Overview", "Base Browser", "Modifier Explorer",
    "Crafting Methods", "Omens / Essences / Catalysts", "Craft Guides",
    "Cost Planner", "Source Confidence",
]


class CraftingTab(QWidget):
    def __init__(self, store, parent=None):
        super().__init__(parent)
        self.store = store
        root = QHBoxLayout(self)

        self.nav = QListWidget()
        self.nav.addItems(NAV_SECTIONS)
        self.nav.setMaximumWidth(210)
        root.addWidget(self.nav)

        self.pages = QStackedWidget()
        root.addWidget(self.pages, 1)

        manifest = store.crafting("crafting_extraction_manifest")
        if manifest is None:
            missing = QWidget()
            lay = QVBoxLayout(missing)
            lay.addWidget(header("Crafting data not extracted yet", "h1"))
            lay.addWidget(warn_panel([
                "Run tools/convert_craftofexile.py after downloading the Craft of "
                "Exile raw data to enable this tab."]))
            lay.addStretch(1)
            for _ in NAV_SECTIONS:
                self.pages.addWidget(missing)
            self.nav.setCurrentRow(0)
            return

        self.manifest = manifest
        self._all_bases = [b for b in store.crafting("crafting_bases")["bases"]
                           if b.get("name")]
        self._all_mods = store.crafting("crafting_modifiers")["modifiers"]
        self.pages.addWidget(self._craft_page())
        self.pages.addWidget(self._overview_page())
        self.pages.addWidget(self._base_browser_page())
        self.pages.addWidget(self._modifier_page())
        self.pages.addWidget(self._methods_page())
        self.pages.addWidget(self._oec_page())
        self.pages.addWidget(self._guides_page())
        self.pages.addWidget(self._cost_page())
        self.pages.addWidget(self._sources_page())
        self.nav.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.nav.setCurrentRow(0)

    # ------------------------------------------------------------------
    def _craft_page(self):
        """Craft of Exile-style layout: base picker on the left, the base's
        prefix and suffix pools side by side in the middle, and crafting
        options on the right. Everything scales with the window."""
        page = QWidget()
        lay = QVBoxLayout(page)

        top = QHBoxLayout()
        top.addWidget(header("Craft", "h1"))
        top.addSpacing(16)
        top.addWidget(QLabel("Item class:"))
        self.craft_class = QComboBox()
        weight_classes = sorted({c for m in self._all_mods for c in m["weights_by_class"]})
        base_classes = sorted({b["class"] for b in self._all_bases if b.get("class")})
        self.craft_class.addItems([c for c in base_classes if c in weight_classes]
                                  or base_classes)
        top.addWidget(self.craft_class)
        top.addWidget(QLabel("Max req. ilvl:"))
        self.craft_ilvl = QSpinBox()
        self.craft_ilvl.setRange(0, 100)
        self.craft_ilvl.setSpecialValueText(ALL)
        top.addWidget(self.craft_ilvl)
        top.addWidget(QLabel("Filter mods:"))
        self.craft_search = QLineEdit()
        self.craft_search.setPlaceholderText("Stat text / name / tag…")
        top.addWidget(self.craft_search, 1)
        lay.addLayout(top)
        lay.addWidget(dim("Weights are Craft of Exile per-class estimates (third-party). "
                          "Pick a base on the left; its modifier pool fills the middle."))

        split = QSplitter(Qt.Horizontal)

        # left: bases of the selected class + base details
        left = QWidget()
        llay = QVBoxLayout(left)
        llay.setContentsMargins(0, 0, 4, 0)
        llay.addWidget(header("Base Items"))
        self.craft_bases = QListWidget()
        llay.addWidget(self.craft_bases, 2)
        self.craft_base_info = QPlainTextEdit()
        self.craft_base_info.setReadOnly(True)
        self.craft_base_info.setPlaceholderText("Select a base…")
        llay.addWidget(self.craft_base_info, 1)
        split.addWidget(left)

        # center: prefix / suffix pools side by side
        center = QWidget()
        clay = QHBoxLayout(center)
        clay.setContentsMargins(4, 0, 4, 0)
        self.prefix_col = QVBoxLayout()
        self.suffix_col = QVBoxLayout()
        clay.addLayout(self.prefix_col, 1)
        clay.addLayout(self.suffix_col, 1)
        self.prefix_header = header("Prefixes")
        self.suffix_header = header("Suffixes")
        self.prefix_col.addWidget(self.prefix_header)
        self.suffix_col.addWidget(self.suffix_header)
        self.prefix_table = None
        self.suffix_table = None
        split.addWidget(center)

        # right: crafting options
        right = QWidget()
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(4, 0, 0, 0)
        rlay.addWidget(header("Crafting Options"))
        methods = self.store.crafting("crafting_methods")["methods"]
        rlay.addWidget(make_table(
            ["Method", "Applies when"],
            [[("%s — %s" % (m["group"], m["name"])) if m.get("group") else m["name"],
              ", ".join(m.get("constraints") or [])]
             for m in methods if m.get("name")],
            stretch_column=0), 1)
        rlay.addWidget(dim("Full method details, omens, essences, and catalysts are in "
                           "the sections on the left."))
        split.addWidget(right)

        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 6)
        split.setStretchFactor(2, 2)
        split.setSizes([320, 1100, 380])
        lay.addWidget(split, 1)

        self.craft_class.currentIndexChanged.connect(self._craft_class_changed)
        self.craft_bases.currentRowChanged.connect(self._craft_base_changed)
        self.craft_ilvl.valueChanged.connect(self._craft_rebuild_mods)
        self.craft_search.textChanged.connect(self._craft_rebuild_mods)
        default = self.craft_class.findText("Bows")
        self.craft_class.setCurrentIndex(default if default >= 0 else 0)
        self._craft_class_changed()
        return page

    def _craft_class_changed(self):
        cls = self.craft_class.currentText()
        self._craft_class_bases = [b for b in self._all_bases if b.get("class") == cls]
        self.craft_bases.blockSignals(True)
        self.craft_bases.clear()
        for b in self._craft_class_bases:
            self.craft_bases.addItem(b["name"])
        self.craft_bases.blockSignals(False)
        if self._craft_class_bases:
            self.craft_bases.setCurrentRow(0)
        else:
            self._craft_base_changed()

    def _craft_base_changed(self, *_):
        row = self.craft_bases.currentRow()
        if 0 <= row < len(self._craft_class_bases):
            b = self._craft_class_bases[row]
            lines = ["%s  (drop level %s)" % (b["name"], b.get("drop_level"))]
            if b.get("implicits"):
                lines.append("Implicit: " + " | ".join(b["implicits"]))
            if b.get("properties"):
                lines.append("Properties: " + json.dumps(b["properties"]))
            if b.get("requirements"):
                lines.append("Requirements: " + json.dumps(b["requirements"]))
            if b.get("sockets"):
                lines.append("Rune sockets: %s" % b["sockets"])
            if b.get("unmodifiable"):
                lines.append("UNMODIFIABLE — most crafting does not apply.")
            self.craft_base_info.setPlainText("\n".join(lines))
        else:
            self.craft_base_info.setPlainText("No bases for this class.")
        self._craft_rebuild_mods()

    def _craft_rebuild_mods(self):
        cls = self.craft_class.currentText()
        max_ilvl = self.craft_ilvl.value()
        needle = self.craft_search.text().strip().lower()
        prefixes, suffixes = [], []
        for m in self._all_mods:
            weight = m["weights_by_class"].get(cls)
            if weight is None:
                continue
            if max_ilvl and (m.get("min_item_level") or 0) > max_ilvl:
                continue
            if needle:
                haystack = " ".join([str(m.get("name") or ""), m.get("text") or "",
                                     " ".join(m.get("tags") or [])]).lower()
                if needle not in haystack:
                    continue
            if m["affix"] == "prefix":
                prefixes.append((weight, m))
            elif m["affix"] == "suffix":
                suffixes.append((weight, m))
        prefixes.sort(key=lambda x: -x[0])
        suffixes.sort(key=lambda x: -x[0])

        def rebuild(col, old_table, rows, which):
            if old_table is not None:
                old_table.deleteLater()
            # Modifier text first — the game never shows internal mod names.
            cells = [[m.get("text") or "",
                      m.get("min_item_level") or "", w,
                      ", ".join(m.get("tags") or [])] for w, m in rows]
            table = make_table(
                ["Modifier text (rolls)", "ilvl", "Weight*", "Tags"],
                cells, stretch_column=0)
            col.addWidget(table, 1)
            return table

        self.prefix_header.setText("Prefixes (%d)" % len(prefixes))
        self.suffix_header.setText("Suffixes (%d)" % len(suffixes))
        self.prefix_table = rebuild(self.prefix_col, self.prefix_table, prefixes, "prefix")
        self.suffix_table = rebuild(self.suffix_col, self.suffix_table, suffixes, "suffix")

    # ------------------------------------------------------------------
    def _overview_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(header("Crafting Overview", "h1"))
        m = self.manifest
        lay.addWidget(dim(
            "Craft of Exile beta POE2 data — CoE patch %s (label %s), extracted %s. "
            "Third-party source; not official GGG data."
            % (m["coe_patch"], m["coe_patch_label"], m["extraction_date"])))
        lay.addWidget(warn_panel([
            "Weights and any implied odds are Craft of Exile ESTIMATES, not official.",
            "League label conflict: CoE says '%s' but the official API says 'Runes of Aldur'."
            % m["coe_league_label"],
            "Simulation / success odds are out of scope by owner decision.",
        ]))

        counts = m["counts"]
        box = QGroupBox("Extracted data (see manifest for hashes)")
        box_lay = QVBoxLayout(box)
        box_lay.addWidget(QLabel(
            "%(bases)d item bases  •  %(modifiers)d modifiers in %(mod_groups)d groups  •  "
            "%(methods)d crafting methods  •  %(omens)d omens  •  %(essences)d essences  •  "
            "%(catalysts)d catalysts  •  %(special_bases)d special bases" % counts))
        box_lay.addWidget(dim(
            "Sourced guide entries: %d (Craft of Exile exposes no guide content; "
            "these entries come from credited community sources such as GhazzyTV)."
            % counts["guides"]))
        lay.addWidget(box)

        gaps = QGroupBox("Known gaps")
        gaps_lay = QVBoxLayout(gaps)
        for gap in m["known_gaps"]:
            lbl = QLabel("• " + gap)
            lbl.setWordWrap(True)
            gaps_lay.addWidget(lbl)
        lay.addWidget(gaps)

        lay.addWidget(dim("Use the sections on the left: pick a base in Base Browser, "
                          "explore its modifier pool in Modifier Explorer, then check "
                          "Crafting Methods for how to get there."))
        lay.addStretch(1)
        return page

    # ------------------------------------------------------------------
    def _base_browser_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(header("Base Item Browser", "h1"))
        bases = self.store.crafting("crafting_bases")["bases"]
        self._bases = [b for b in bases if b.get("name")]

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Item class:"))
        self.base_class = QComboBox()
        classes = sorted({b["class"] for b in self._bases if b.get("class")})
        self.base_class.addItems([ALL] + classes)
        controls.addWidget(self.base_class)
        controls.addWidget(QLabel("Search:"))
        self.base_search = QLineEdit()
        self.base_search.setPlaceholderText("Base name…")
        controls.addWidget(self.base_search, 1)
        lay.addLayout(controls)

        split = QSplitter(Qt.Vertical)
        self.base_table_host = QWidget()
        self.base_table_layout = QVBoxLayout(self.base_table_host)
        self.base_table_layout.setContentsMargins(0, 0, 0, 0)
        split.addWidget(self.base_table_host)
        self.base_detail = QPlainTextEdit()
        self.base_detail.setReadOnly(True)
        self.base_detail.setPlaceholderText(
            "Select a base to see implicits, properties, requirements, and tags.")
        self.base_detail.setMaximumHeight(170)
        split.addWidget(self.base_detail)
        lay.addWidget(split, 1)

        self.base_table = None
        self._base_rows = []
        self.base_class.currentIndexChanged.connect(self._rebuild_bases)
        self.base_search.textChanged.connect(self._rebuild_bases)
        self._rebuild_bases()
        return page

    def _rebuild_bases(self):
        cls = self.base_class.currentText()
        needle = self.base_search.text().strip().lower()
        rows = [b for b in self._bases
                if (cls == ALL or b.get("class") == cls)
                and (not needle or needle in b["name"].lower())]
        truncated = len(rows) > MAX_ROWS
        self._base_rows = rows[:MAX_ROWS]
        cells = [[b["name"], b.get("class") or "", b.get("category") or "",
                  b.get("drop_level") if b.get("drop_level") is not None else "",
                  b.get("sockets") or 0,
                  "yes" if b.get("corrupted_only") else ""]
                 for b in self._base_rows]
        if self.base_table is not None:
            self.base_table.deleteLater()
        self.base_table = make_table(
            ["Base", "Class", "Category", "Drop lvl", "Sockets", "Corrupt-only"],
            cells, stretch_column=0)
        self.base_table.itemSelectionChanged.connect(self._show_base_detail)
        self.base_table_layout.addWidget(self.base_table)
        self.base_detail.setPlainText(
            "Showing %d of %d matching bases%s." % (
                len(self._base_rows), len(rows) if not truncated else len(rows),
                " (refine filters to see the rest)" if truncated else ""))

    def _show_base_detail(self):
        sel = self.base_table.selectionModel().selectedRows()
        if not sel or sel[0].row() >= len(self._base_rows):
            return
        b = self._base_rows[sel[0].row()]
        lines = ["%s  (class: %s, CoE id %s)" % (b["name"], b.get("class"), b["coe_id"])]
        if b.get("implicits"):
            lines.append("Implicits: " + " | ".join(b["implicits"]))
        if b.get("properties"):
            lines.append("Properties: " + json.dumps(b["properties"]))
        if b.get("requirements"):
            lines.append("Requirements: " + json.dumps(b["requirements"]))
        if b.get("tags"):
            lines.append("Tags: " + ", ".join(b["tags"]))
        if b.get("unmodifiable"):
            lines.append("UNMODIFIABLE base — most crafting methods do not apply.")
        if b.get("wiki"):
            lines.append("Wiki name: " + b["wiki"])
        self.base_detail.setPlainText("\n".join(lines))

    # ------------------------------------------------------------------
    def _modifier_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(header("Modifier Explorer", "h1"))
        lay.addWidget(dim("Weights are Craft of Exile estimates (per item class), "
                          "shown only for the selected class."))
        self._mods = self.store.crafting("crafting_modifiers")["modifiers"]
        weight_classes = sorted({c for m in self._mods for c in m["weights_by_class"]})

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Item class:"))
        self.mod_class = QComboBox()
        self.mod_class.addItems([ALL] + weight_classes)
        controls.addWidget(self.mod_class)
        controls.addWidget(QLabel("Affix:"))
        self.mod_affix = QComboBox()
        self.mod_affix.addItems([ALL, "prefix", "suffix", "corrupted", "unique"])
        controls.addWidget(self.mod_affix)
        controls.addWidget(QLabel("Max req. ilvl:"))
        self.mod_ilvl = QSpinBox()
        self.mod_ilvl.setRange(0, 100)
        self.mod_ilvl.setSpecialValueText(ALL)
        controls.addWidget(self.mod_ilvl)
        controls.addWidget(QLabel("Search:"))
        self.mod_search = QLineEdit()
        self.mod_search.setPlaceholderText("Stat text / name / tag…")
        controls.addWidget(self.mod_search, 1)
        lay.addLayout(controls)

        self.mod_table_host = QWidget()
        self.mod_table_layout = QVBoxLayout(self.mod_table_host)
        self.mod_table_layout.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.mod_table_host, 1)
        self.mod_note = dim("")
        lay.addWidget(self.mod_note)

        self.mod_table = None
        for w in (self.mod_class, self.mod_affix):
            w.currentIndexChanged.connect(self._rebuild_mods)
        self.mod_ilvl.valueChanged.connect(self._rebuild_mods)
        self.mod_search.textChanged.connect(self._rebuild_mods)
        self._rebuild_mods()
        return page

    def _rebuild_mods(self):
        cls = self.mod_class.currentText()
        affix = self.mod_affix.currentText()
        max_ilvl = self.mod_ilvl.value()
        needle = self.mod_search.text().strip().lower()

        rows = []
        for m in self._mods:
            if cls != ALL and cls not in m["weights_by_class"]:
                continue
            if affix != ALL and m["affix"] != affix:
                continue
            if max_ilvl and (m.get("min_item_level") or 0) > max_ilvl:
                continue
            if needle:
                haystack = " ".join([str(m.get("name") or ""), m.get("text") or "",
                                     " ".join(m.get("tags") or [])]).lower()
                if needle not in haystack:
                    continue
            rows.append(m)
        total = len(rows)
        rows = rows[:MAX_ROWS]
        cells = []
        for m in rows:
            weight = m["weights_by_class"].get(cls, "") if cls != ALL else ""
            cells.append([m.get("text") or "", m["affix"],
                          m.get("min_item_level") or "", weight,
                          ", ".join(m.get("tags") or [])])
        if self.mod_table is not None:
            self.mod_table.deleteLater()
        # Modifier text first — internal CoE names are never shown in game.
        self.mod_table = make_table(
            ["Modifier text (rolls)", "Affix", "Req ilvl",
             "Weight*" if cls != ALL else "Weight* (pick class)", "Tags"],
            cells, stretch_column=0)
        self.mod_table_layout.addWidget(self.mod_table)
        note = "Showing %d of %d matching modifiers." % (len(rows), total)
        if total > MAX_ROWS:
            note += " Refine filters to see the rest."
        note += "  *Weights are third-party estimates."
        self.mod_note.setText(note)

    # ------------------------------------------------------------------
    def _methods_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(header("Crafting Methods", "h1"))
        lay.addWidget(dim("From Craft of Exile's method tree. Constraints show when a "
                          "method applies; omen hooks show which omens modify it. Exact "
                          "in-game behavior should be verified before high-cost crafts."))
        methods = self.store.crafting("crafting_methods")["methods"]
        rows = []
        for m in methods:
            rows.append([
                m.get("group") or "", m.get("name") or "",
                m.get("currency_item") or "",
                ", ".join(m.get("constraints") or []),
                ", ".join(m.get("omens") or []),
                json.dumps(m.get("properties")) if m.get("properties") else "",
            ])
        lay.addWidget(make_table(
            ["Group", "Method", "Currency/item", "Applies when", "Omen hooks", "Notes"],
            rows, stretch_column=4), 1)
        return page

    # ------------------------------------------------------------------
    def _oec_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(header("Omens, Essences & Catalysts", "h1"))
        sub = QTabWidget()

        omens = self.store.crafting("crafting_omens")["omens"]
        omen_page = QWidget()
        omen_lay = QVBoxLayout(omen_page)
        omen_lay.addWidget(warn_panel([
            "Effect text below is the Craft of Exile action id, not verified in-game "
            "wording. NEEDS VERIFICATION before relying on exact behavior."]))
        omen_lay.addWidget(make_table(
            ["Omen / Saga", "CoE action", "Constraints"],
            [[o.get("name") or "?", o.get("action") or "",
              json.dumps(o.get("constraints")) if o.get("constraints") else ""]
             for o in omens],
            ["unknown"] * len(omens), stretch_column=1))
        sub.addTab(omen_page, "Omens (%d)" % len(omens))

        essences = self.store.crafting("crafting_essences")["essences"]
        ess_rows = [[e.get("name") or "?", e.get("type"),
                     e.get("level") if e.get("level") is not None else "",
                     json.dumps(e.get("restriction")) if e.get("restriction") else ""]
                    for e in essences]
        ess_page = QWidget()
        ess_lay = QVBoxLayout(ess_page)
        ess_lay.addWidget(make_table(
            ["Essence", "Type", "Level", "Restriction"], ess_rows, stretch_column=0))
        sub.addTab(ess_page, "Essences (%d)" % len(essences))

        catalysts = self.store.crafting("crafting_catalysts")["catalysts"]
        cat_page = QWidget()
        cat_lay = QVBoxLayout(cat_page)
        cat_lay.addWidget(make_table(
            ["Catalyst", "Class", "Tags"],
            [[c["name"], c.get("class") or "", ", ".join(c.get("tags") or [])]
             for c in catalysts], stretch_column=0))
        sub.addTab(cat_page, "Catalysts (%d)" % len(catalysts))

        special = self.store.crafting("crafting_special_bases")["special_bases"]
        sp_page = QWidget()
        sp_lay = QVBoxLayout(sp_page)
        sp_lay.addWidget(make_table(
            ["Special base", "Class", "Category", "Implicits"],
            [[s["name"], s.get("class") or "", s.get("category") or "",
              " | ".join(s.get("implicits") or [])]
             for s in special], stretch_column=3))
        sub.addTab(sp_page, "Special bases (%d)" % len(special))

        lay.addWidget(sub, 1)
        return page

    # ------------------------------------------------------------------
    def _guides_page(self):
        import webbrowser
        from PySide6.QtWidgets import QScrollArea

        page = QWidget()
        outer = QVBoxLayout(page)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.addWidget(header("Craft Guides", "h1"))
        guides = self.store.crafting("crafting_guides")
        if not guides or not guides.get("guides"):
            lay.addWidget(warn_panel([
                "No sourced craft guides yet. Guides can be added to "
                "data/crafting/crafting_guides.json with a source URL, source "
                "type, patch, and date — never invented.",
            ]))
            lay.addStretch(1)
            outer.addWidget(inner)
            return page

        video = guides.get("video")
        if video:
            from PySide6.QtWidgets import QFrame, QPushButton
            card = QFrame()
            card.setProperty("role", "card")
            vlay = QVBoxLayout(card)
            top = QHBoxLayout()
            top.addWidget(header("Video guide: %s" % video["title"]))
            top.addStretch(1)
            top.addWidget(badge("community"))
            vlay.addLayout(top)
            vlay.addWidget(dim("Credit: %s  —  %s  (added %s)" % (
                video["credit"], video["url"], video["date_added"])))
            buttons = QHBoxLayout()
            self.video_btn = QPushButton("▶ Play video in app")
            self.video_btn.clicked.connect(lambda: self._embed_video(vlay, video))
            buttons.addWidget(self.video_btn)
            yt_btn = QPushButton("Open on YouTube")
            yt_btn.clicked.connect(lambda: webbrowser.open(video["url"]))
            buttons.addWidget(yt_btn)
            buttons.addStretch(1)
            vlay.addLayout(buttons)
            self._video_host = vlay
            lay.addWidget(card)

        lay.addWidget(dim("Written guides below are summarized from the credited video "
                          "(community content, not official). Every guide keeps its "
                          "source link."))
        for g in guides["guides"]:
            body = QWidget()
            blay = QVBoxLayout(body)
            blay.addWidget(dim("Goal: %s   |   Source: %s (credit %s, %s)" % (
                g["goal"], g["source"], g["credit"], g["confidence"])))
            for i, step in enumerate(g["steps"], 1):
                lbl = QLabel("%d. %s" % (i, step))
                lbl.setWordWrap(True)
                blay.addWidget(lbl)
            lay.addWidget(CollapsibleSection(g["title"], body, expanded=False))
        lay.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return page

    def _embed_video(self, host_layout, video):
        """Lazy-create the in-app YouTube player (WebEngine is heavy, so it is
        only started when the user asks for it). Falls back to the browser."""
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtWebEngineWidgets import QWebEngineView
            view = QWebEngineView()
            view.setMinimumHeight(560)
            view.load(QUrl(video["embed_url"]))
            host_layout.addWidget(view)
            self.video_btn.setEnabled(False)
            self.video_btn.setText("Video loaded below — credit %s" % video["credit"])
        except Exception:
            import webbrowser
            webbrowser.open(video["url"])

    # ------------------------------------------------------------------
    def _cost_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(header("Cost Planner (manual prices)", "h1"))
        lay.addWidget(dim("Enter your own currency prices — the app does not auto-scrape "
                          "prices. Rows are saved locally to user_prices.json."))
        self.price_table = QTableWidget(0, 3)
        self.price_table.setHorizontalHeaderLabels(["Currency / item", "Price (exalted)", "Note"])
        self.price_table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.price_table, 1)
        buttons = QHBoxLayout()
        add_btn = QPushButton("Add row")
        add_btn.clicked.connect(lambda: self.price_table.insertRow(self.price_table.rowCount()))
        buttons.addWidget(add_btn)
        save_btn = QPushButton("Save prices")
        save_btn.clicked.connect(self._save_prices)
        buttons.addWidget(save_btn)
        buttons.addStretch(1)
        lay.addLayout(buttons)
        self._load_prices()
        return page

    def _load_prices(self):
        if not USER_PRICES_FILE.exists():
            return
        try:
            rows = json.loads(USER_PRICES_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        for row in rows:
            r = self.price_table.rowCount()
            self.price_table.insertRow(r)
            for c, key in enumerate(("name", "price", "note")):
                self.price_table.setItem(r, c, QTableWidgetItem(str(row.get(key, ""))))

    def _save_prices(self):
        rows = []
        for r in range(self.price_table.rowCount()):
            cells = [self.price_table.item(r, c) for c in range(3)]
            values = [c.text().strip() if c else "" for c in cells]
            if any(values):
                rows.append({"name": values[0], "price": values[1], "note": values[2]})
        USER_PRICES_FILE.write_text(json.dumps(rows, indent=1), encoding="utf-8")

    # ------------------------------------------------------------------
    def _sources_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.addWidget(header("Crafting Source Confidence", "h1"))
        src = self.store.crafting("crafting_sources")
        lay.addWidget(warn_panel([src["_note"], src["league_label_conflict"]]))
        lay.addWidget(make_table(
            ["Source", "URL", "Type", "Reliability"],
            [[s["name"], s["url"], s["type"], s["reliability"]]
             for s in src["sources"]], stretch_column=1))
        m = self.manifest
        box = QGroupBox("Extraction manifest")
        box_lay = QVBoxLayout(box)
        box_lay.addWidget(dim("Extracted %s (converted %s). Raw files with SHA-256 hashes:"
                              % (m["extraction_date"], m["converted_on"])))
        for f in m["raw_files"]:
            box_lay.addWidget(dim("%s  (%d bytes)  %s…" % (f["file"], f["bytes"],
                                                           f["sha256"][:16])))
        lay.addWidget(box)
        lay.addStretch(1)
        return page
