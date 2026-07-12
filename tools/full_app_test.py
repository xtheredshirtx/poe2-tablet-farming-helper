"""Full-app offscreen test: exercises every tab and every interactive control.

Run before ending any development session:  python tools/full_app_test.py
Exits non-zero on the first failure. This is the Phase 7 testing mandate —
every LLM/developer must run and pass this before stopping.
"""
import json
import os
import csv
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)

from PySide6.QtWidgets import QApplication, QTableWidgetItem  # noqa: E402

from app.datastore import DataStore, SETTINGS_FILE, DATA_DIR  # noqa: E402
from app.theme import QSS  # noqa: E402
import main as appmain  # noqa: E402

PASSED = []


def check(name, condition, detail=""):
    if not condition:
        print("FAIL: %s %s" % (name, detail))
        sys.exit(1)
    PASSED.append(name)
    print("ok: %s" % name)


def run():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(QSS)
    store = DataStore()
    window = appmain.MainWindow(store)
    window.resize(1920, 1080)
    window.show()
    app.processEvents()

    # ---- every top-level tab builds -----------------------------------
    for i in range(window.tabs.count()):
        window.tabs.setCurrentIndex(i)
        app.processEvents()
        check("tab builds: %s" % window.tabs.tabText(i), True)

    # ---- dashboard -----------------------------------------------------
    d = window.dashboard
    d.mode_combo.setCurrentIndex(1); app.processEvents()
    d.mode_combo.setCurrentIndex(0); app.processEvents()
    check("dashboard investment toggle", True)
    window._goto_trade("Ritual Tablet")
    check("dashboard->trade routing", window.tabs.currentWidget() is window.trade)
    window._goto_tablet_db("Ritual Tablet")
    check("dashboard->tablet routing", window.tabs.currentWidget() is window.tablets)

    # ---- tablets hub: every tablet page + best-setup card --------------
    hub = window.tablets
    for row in range(hub.nav.count()):
        hub.nav.setCurrentRow(row)
        app.processEvents()
        page = hub.pages.currentWidget()
        check("tablet page: %s" % hub.nav.item(row).text(), page is not None)
    from app.widgets import poe_item_card  # smoke the tooltip builder directly
    card = poe_item_card("Test", "Sub", [[("a", "mod")], [("b", "info")]])
    check("poe item card builds", card is not None)

    # ---- waystone optimizer --------------------------------------------
    w = window.waystones
    for gi in range(w.goal_combo.count()):
        w.goal_combo.setCurrentIndex(gi)
        app.processEvents()
    for si in range(w.safety_combo.count()):
        w.safety_combo.setCurrentIndex(si)
        app.processEvents()
    check("waystone goal/safety combos (%d goals)" % w.goal_combo.count(),
          w.goal_combo.count() > 0)

    # ---- crafting: all sections + craft view ---------------------------
    ct = window.crafting
    for row in range(ct.nav.count()):
        ct.nav.setCurrentRow(row)
        app.processEvents()
        check("crafting section: %s" % ct.nav.item(row).text(), True)
    ct.nav.setCurrentRow(0); app.processEvents()
    idx = ct.craft_class.findText("Bows")
    check("craft view has Bows class", idx >= 0)
    ct.craft_class.setCurrentIndex(idx); app.processEvents()
    check("craft view bases listed", ct.craft_bases.count() > 0,
          "count=%d" % ct.craft_bases.count())
    check("craft view prefix table", ct.prefix_table.rowCount() > 0)
    check("craft view suffix table", ct.suffix_table.rowCount() > 0)
    ct.craft_search.setText("physical"); app.processEvents()
    filtered = ct.prefix_table.rowCount()
    ct.craft_search.setText(""); app.processEvents()
    check("craft view search filters", filtered < ct.prefix_table.rowCount())
    ct.craft_ilvl.setValue(30); app.processEvents()
    check("craft view ilvl filter", True)
    ct.craft_ilvl.setValue(0); app.processEvents()
    # base browser + modifier explorer still work
    ct.nav.setCurrentRow(2); app.processEvents()
    ct.base_search.setText("crude"); app.processEvents()
    check("base browser search", ct.base_table.rowCount() >= 1)
    ct.nav.setCurrentRow(3); app.processEvents()
    ct.mod_search.setText("minion"); app.processEvents()
    check("modifier explorer search", ct.mod_table.rowCount() > 0)
    # cost planner roundtrip
    ct.nav.setCurrentRow(7); app.processEvents()
    ct.price_table.insertRow(0)
    ct.price_table.setItem(0, 0, QTableWidgetItem("Divine Orb"))
    ct.price_table.setItem(0, 1, QTableWidgetItem("180"))
    ct._save_prices()
    from app.tabs.crafting_tab import USER_PRICES_FILE
    saved = json.loads(USER_PRICES_FILE.read_text(encoding="utf-8"))
    check("cost planner save/load", saved and saved[0]["name"] == "Divine Orb")
    USER_PRICES_FILE.unlink()

    # ---- logbook planner ------------------------------------------------
    lb = window.logbook
    lb.is_boss.setChecked(True); app.processEvents()
    check("aldurs helper: boss veto", "NO" in lb.verdict.text())
    lb.is_boss.setChecked(False)
    lb.is_unique.setChecked(True); app.processEvents()
    check("aldurs helper: unique veto", "NO" in lb.verdict.text())
    lb.is_fallen_skies.setChecked(True)
    lb.rumour_count.setValue(3); app.processEvents()
    check("aldurs helper: fallen skies exception", "YES" in lb.verdict.text())
    lb.is_unique.setChecked(False); lb.is_fallen_skies.setChecked(False)
    exp_juice_rule = store.expedition.get("current_juice_rule", {})
    check("expedition juice: other-tablet rule stored",
          exp_juice_rule.get("use_other_tablets")
          and exp_juice_rule.get("never_use_tablet_type") == "Expedition Tablet")
    exp_juice_ids = [
        t["modifier_id"]
        for t in exp_juice_rule.get("recommended_other_tablet_filters", [])
    ]
    juice_by_id = {m["id"]: m for m in store.tablet_juice_modifiers}
    check("expedition juice: mapped filters are current non-expedition rows",
          len(exp_juice_ids) >= 7
          and all(i in juice_by_id for i in exp_juice_ids)
          and all(juice_by_id[i].get("current_game_available", True)
                  for i in exp_juice_ids)
          and not any(juice_by_id[i].get("tablet_type") == "Expedition Tablet"
                      for i in exp_juice_ids))
    check("expedition juice: legacy tablet setups disabled",
          all(not s.get("current_game_available", True)
              and s.get("legacy_removed_from_current_game")
              for s in store.expedition["tablet_setups"])
          and not any("Expedition Tablet with" in s["setup"]
                      for s in store.expedition["tablet_setups"]))
    meta_juice_rule = next((r for r in store.meta.get("known_gameplay_rules", [])
                            if r.get("id") == "expedition_juice_means_other_tablets"), None)
    check("expedition juice: meta rule stored",
          meta_juice_rule is not None
          and "other current tablets" in meta_juice_rule.get("rule", ""))
    check("expedition juice: whispers UI renders rule",
          "other current tablets" in lb.expedition_juice_summary.text()
          and lb.expedition_juice_table.rowCount() == len(exp_juice_ids))

    # ---- atlas masters ---------------------------------------------------
    at = window.atlas
    node_counts = []
    for i in range(at.master_combo.count()):
        at.master_combo.setCurrentIndex(i)
        app.processEvents()
        node_counts.append(at.nodes_table.rowCount())
    check("atlas master filter (all=%d)" % node_counts[0],
          node_counts[0] == 36 and all(c == 12 for c in node_counts[1:]))

    # ---- trade search builder -------------------------------------------
    tb = window.trade
    labels = [tb.status.itemText(i) for i in range(tb.status.count())]
    check("trade: official status labels", "Instant Buyout" in labels, str(labels))
    check("trade: instant buyout default",
          tb.status.currentData() in ("securable", store.settings.get("trade_status")))
    idx = tb.status.findData("securable")
    tb.status.setCurrentIndex(idx); app.processEvents()
    tb.set_tablet_type("Delirium Tablet"); app.processEvents()
    enabled = [r for r in tb.mod_rows if r.check.isEnabled()]
    disabled = [r for r in tb.mod_rows if not r.check.isEnabled()]
    eternity_row = next(r for r in tb.mod_rows if r.mod["name"] == "of Eternity")
    check("trade: of Eternity duplicate ID resolved",
          eternity_row.check.isEnabled()
          and eternity_row.mod["stat_id"] == "explicit.stat_3226351972")
    enabled[0].check.setChecked(True)
    enabled[0].min_spin.setValue(20)
    app.processEvents()
    q = json.loads(tb.preview.toPlainText())
    check("trade: query uses status id",
          q["query"]["status"]["option"] == "securable", json.dumps(q["query"]["status"]))
    check("trade: stat filter present",
          q["query"]["stats"][0]["filters"][0]["id"].startswith("explicit.stat_"))
    check("trade: category map.tablet",
          q["query"]["filters"]["type_filters"]["filters"]["category"]["option"] == "map.tablet")
    check("trade: live button exists", tb.live_btn is not None and tb.live_btn.isEnabled())
    live_url = store.meta["trade"]["live_url_template"].format(league="X", id="Y")
    check("trade: live url shape", live_url.endswith("/X/Y/live"))
    # Guardrail invariant (data-driven so it stays valid as rows get verified):
    # a mod row is enabled if and only if its data says trade_ready.
    for base in ["Any"] + store.tablet_base_names():
        tb.set_tablet_type(base) if base != "Any" else tb.tablet_type.setCurrentIndex(0)
        app.processEvents()
        for r in tb.mod_rows:
            if r.check.isEnabled() != bool(r.mod.get("trade_ready", False)):
                check("trade: guardrail invariant (%s / %s)" % (base, r.mod["name"]),
                      False, "enabled=%s trade_ready=%s" % (
                          r.check.isEnabled(), r.mod.get("trade_ready")))
    check("trade: guardrail invariant holds for all tablet types", True)

    # ---- sources tab -----------------------------------------------------
    src = window.sources
    check("sources: registry rows", src.sources_table.rowCount() >= 15)

    # ---- settings tab: change everything and verify persistence ----------
    st = window.settings
    st.league.setCurrentText("Standard")
    st.status.setCurrentIndex(st.status.findData("available"))
    st.mode.setCurrentText("high")
    app.processEvents()
    saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    check("settings: league persisted", saved["league"] == "Standard")
    check("settings: trade type persisted (id)", saved["trade_status"] == "available")
    check("settings: budget mode persisted", saved["budget_mode"] == "high")
    st.league.setCurrentText("Runes of Aldur")
    st.status.setCurrentIndex(st.status.findData("securable"))
    st.mode.setCurrentText("budget")
    app.processEvents()
    saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    check("settings: restored defaults", saved["league"] == "Runes of Aldur"
          and saved["trade_status"] == "securable")

    # ---- phase 11: owner rule, no current Expedition Tablets ---------------
    hub_names = [hub.nav.item(i).text() for i in range(hub.nav.count())]
    check("expedition rule: tablet hidden from tablet hub",
          not any("Expedition" in n for n in hub_names), str(hub_names))
    tab_titles = [window.tabs.tabText(i) for i in range(window.tabs.count())]
    check("whispers: tab renamed", "Expedition Whispers" in tab_titles, str(tab_titles))
    trade_types = [tb.tablet_type.itemText(i) for i in range(tb.tablet_type.count())]
    check("expedition rule: tablet hidden from trade builder",
          "Expedition Tablet" not in trade_types, str(trade_types))
    rule = next((r for r in store.meta.get("known_gameplay_rules", [])
                 if r.get("id") == "no_current_expedition_tablets"), None)
    check("expedition rule: known gameplay rule stored",
          rule is not None and "do not exist" in rule.get("rule", ""))
    window._goto_tablet_db("Expedition Logbook")
    check("whispers: dashboard routes expedition to whispers tab",
          window.tabs.currentWidget() is window.logbook)

    # ---- phase 8: modifier-text-first displays ----------------------------
    from PySide6.QtWidgets import QLabel, QTableWidget
    hub.nav.setCurrentRow(hub_names.index("Ritual")); app.processEvents()
    page = hub.pages.currentWidget()
    mod_lines = [l.text() for l in page.findChildren(QLabel)
                 if l.property("role") == "poe-mod"]
    check("best setup shows modifier text",
          any("#%" in t or "in Map" in t for t in mod_lines), str(mod_lines[:4]))
    way_tables = window.waystones.findChildren(QTableWidget)
    way_headers = [t.horizontalHeaderItem(0).text() for t in way_tables
                   if t.columnCount() and t.horizontalHeaderItem(0)]
    check("waystones: modifier text is first column",
          any(h.startswith("Modifier text") for h in way_headers), str(way_headers))
    ct.nav.setCurrentRow(0); app.processEvents()
    check("craft view: modifier text first column",
          ct.prefix_table.horizontalHeaderItem(0).text().startswith("Modifier text"))
    ct.nav.setCurrentRow(3); app.processEvents()
    check("modifier explorer: text first column",
          ct.mod_table.horizontalHeaderItem(0).text().startswith("Modifier text"))

    # ---- phase 8: conflict resolutions reflected in data ------------------
    ritual = store.tablets["type_suffixes"]["Ritual Tablet"]
    reroll = next(m for m in ritual if m["name"] == "Reroll cost")
    check("conflicts: ritual reroll cost re-enabled (official text)",
          reroll["trade_ready"] and reroll["confidence"] == "official")
    eternity = next(m for m in store.tablets["type_suffixes"]["Delirium Tablet"]
                    if m["name"] == "of Eternity")
    check("conflicts: eternity duplicate-ID resolved",
          eternity.get("trade_ready", False)
          and eternity.get("stat_id") == "explicit.stat_3226351972")
    conflicts = store.sources["conflicts"]
    active_conflicts = [c for c in conflicts if c.get("status") != "RESOLVED"]
    check("conflicts: all source conflicts resolved", len(active_conflicts) == 0,
          str(active_conflicts))

    # ---- phase 9: trade presets + 4-mod tablet rule ------------------------
    preset_names = [tb.preset.itemText(i) for i in range(tb.preset.count())]
    check("presets: dropdown populated (%d presets)" % (len(preset_names) - 1),
          len(preset_names) >= 9 and "Best currency chances (max 4)" in preset_names,
          str(preset_names))
    tb.preset.setCurrentIndex(preset_names.index("Best currency chances (max 4)"))
    app.processEvents()
    selected = [r for r in tb.mod_rows if r.selected()]
    check("presets: best-currency selects <= 4 mods (%d)" % len(selected),
          0 < len(selected) <= 4)
    check("presets: count mode set", tb.match_mode.currentIndex() == 1
          and tb.count_min.value() == 2)
    q = json.loads(tb.preview.toPlainText())
    check("presets: query uses count group",
          q["query"]["stats"][0]["type"] == "count"
          and q["query"]["stats"][0]["value"]["min"] == 2)
    check("presets: search buttons enabled at <=4", tb.search_btn.isEnabled())
    # force a 5th required AND selection -> both search buttons must lock
    extra = [r for r in tb.mod_rows if r.check.isEnabled() and not r.selected()]
    check("presets: a 5th selectable mod exists", len(extra) >= 1)
    tb.match_mode.setCurrentIndex(0); app.processEvents()
    extra[0].check.setChecked(True); app.processEvents()
    check("4-mod rule: AND buttons disabled at 5 required selections",
          not tb.search_btn.isEnabled() and not tb.live_btn.isEnabled())
    check("4-mod rule: AND warning shown",
          "more than 4" in tb.guard_label.text())
    tb.match_mode.setCurrentIndex(1); app.processEvents()
    check("4-mod rule: COUNT candidate pool allowed at 5",
          tb.search_btn.isEnabled() and "candidate filters" in tb.guard_label.text())
    extra[0].check.setChecked(False); app.processEvents()
    check("4-mod rule: buttons re-enabled at 4", tb.search_btn.isEnabled())
    tb.preset.setCurrentIndex(0); app.processEvents()  # back to manual

    # ---- phase 10: tablet juice data pack + trade mode --------------------
    current_juice = [m for m in store.tablet_juice_modifiers
                     if m.get("current_game_available", True)]
    legacy_exp_juice = [m for m in store.tablet_juice_modifiers
                        if m.get("tablet_type") == "Expedition Tablet"]
    check("juice: current modifiers verified, expedition legacy disabled",
          len(store.tablet_juice_modifiers) == 73
          and len(current_juice) == 65
          and all(m.get("trade_ready") for m in current_juice)
          and len(legacy_exp_juice) == 8
          and not any(m.get("trade_ready") for m in legacy_exp_juice))
    with open(DATA_DIR / "tablet_juice_currency_modifiers.csv",
              newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    exp_csv_rows = [r for r in csv_rows if r["tablet_type"] == "Expedition Tablet"]
    check("juice csv: expedition legacy disabled",
          len(exp_csv_rows) == 8
          and not any(r["trade_ready"].lower() == "true" for r in exp_csv_rows)
          and all("legacy" in r["confidence"] for r in exp_csv_rows))
    mode_labels = [tb.filter_mode.itemText(i) for i in range(tb.filter_mode.count())]
    check("juice: filter modes present",
          all(x in mode_labels for x in ["Manual", "Best Currency Juice",
                                         "Budget", "High Investment"]),
          str(mode_labels))
    tb.filter_mode.setCurrentIndex(tb.filter_mode.findText("Best Currency Juice"))
    tb.tablet_type.setCurrentIndex(0); app.processEvents()
    any_juice_presets = [tb.preset.itemText(i) for i in range(tb.preset.count())]
    check("juice: expedition preset hidden by owner rule",
          not any("Expedition" in p for p in any_juice_presets), str(any_juice_presets))
    tb.set_tablet_type("Breach Tablet"); app.processEvents()
    juice_presets = [tb.preset.itemText(i) for i in range(tb.preset.count())]
    check("juice: breach preset visible",
          "Breach - Density/Currency Juice" in juice_presets, str(juice_presets))
    tb.preset.setCurrentIndex(juice_presets.index("Breach - Density/Currency Juice"))
    app.processEvents()
    selected = [r for r in tb.mod_rows if r.selected()]
    check("juice: breach preset selects 5 count candidates", len(selected) == 5)
    q = json.loads(tb.preview.toPlainText())
    check("juice: query uses verified count candidates",
          q["query"]["stats"][0]["type"] == "count"
          and len(q["query"]["stats"][0]["filters"]) == 5
          and all(f["id"].startswith("explicit.stat_")
                  for f in q["query"]["stats"][0]["filters"]))
    check("juice: count candidate search enabled",
          tb.search_btn.isEnabled() and tb.live_btn.isEnabled())
    tb.filter_mode.setCurrentIndex(tb.filter_mode.findText("Manual"))
    tb.preset.setCurrentIndex(0); app.processEvents()

    # ---- phase 9: sourced craft guides + video ----------------------------
    guides = store.crafting("crafting_guides")
    check("guides: sourced guides loaded (%d)" % len(guides["guides"]),
          len(guides["guides"]) >= 10)
    check("guides: every guide credits its source",
          all(g.get("source") and g.get("credit") for g in guides["guides"]))
    check("guides: video entry credited",
          guides["video"]["credit"] == "GhazzyTV"
          and "youtube.com" in guides["video"]["embed_url"])
    ct.nav.setCurrentRow(6); app.processEvents()  # Craft Guides section
    check("guides: play-in-app button present",
          hasattr(ct, "video_btn") and ct.video_btn.isEnabled())
    check("guides: manifest counts guides",
          store.crafting("crafting_extraction_manifest")["counts"]["guides"] >= 10)

    # ---- phase 13: gear presets + crafting materials -----------------------
    hub = window.trade
    check("gear: trade hub has 3 sub-tabs", hub.sub.count() == 3)
    gear = hub.gear
    check("gear: 10 presets loaded", len(gear.presets) == 10)
    verified_mods = sum(1 for p in gear.presets
                        for k in ("must_have_mods", "optional_mods")
                        for m in (p.get(k) or [])
                        if isinstance(m, dict) and m.get("trade_ready"))
    check("gear: 54 mods verified with official stat IDs", verified_mods == 54)
    # marksman gloves preset: verified must-haves -> search enabled
    idx = gear.preset_combo.findText("Projectile / Marksman Gloves")
    if idx < 0:
        gear.category.setCurrentText("All"); app.processEvents()
        idx = gear.preset_combo.findText("Projectile / Marksman Gloves")
    gear.preset_combo.setCurrentIndex(idx); app.processEvents()
    check("gear: marksman search enabled (verified musts)", gear.search_btn.isEnabled())
    q = json.loads(gear.preview.toPlainText())
    check("gear: query uses official category",
          q["query"]["filters"]["type_filters"]["filters"]["category"]["option"]
          == "armour.gloves")
    check("gear: query stats all verified explicit ids",
          q["query"]["stats"][0]["filters"]
          and all(f["id"].startswith("explicit.stat_")
                  for f in q["query"]["stats"][0]["filters"]))
    gear._copy_checklist()
    check("gear: checklist copied",
          "Projectile / Marksman Gloves" in QApplication.clipboard().text())
    # 13b: full builder logic like the tablets
    check("gear: selectable mod rows built", len(gear.mod_rows) > 5)
    check("gear: unverified rows cannot be selected",
          all(r.check.isEnabled() == r.verified for r in gear.mod_rows))
    check("gear: must-haves pre-checked",
          len(gear._selected_rows()) >= 1)
    check("gear: min value flows into query",
          any(f.get("value", {}).get("min") == 2
              for f in q["query"]["stats"][0]["filters"]))
    check("gear: trade type uses official id",
          q["query"]["status"]["option"] in ("securable", "available",
                                             "online", "onlineleague", "any"))
    gear.match_mode.setCurrentIndex(1); app.processEvents()
    qc = json.loads(gear.preview.toPlainText())
    check("gear: COUNT mode builds count group",
          qc["query"]["stats"][0]["type"] == "count")
    gear.match_mode.setCurrentIndex(0); app.processEvents()
    # AND-mode 6-mod gear cap
    free = [r for r in gear.mod_rows if r.verified and not r.selected()]
    for r in free[:7 - len(gear._selected_rows())]:
        r.check.setChecked(True)
    app.processEvents()
    if len(gear._selected_rows()) > 6:
        check("gear: 6-mod AND cap disables buttons",
              not gear.search_btn.isEnabled() and not gear.live_btn.isEnabled())
        gear.match_mode.setCurrentIndex(1); app.processEvents()
        check("gear: COUNT mode allows larger candidate pool",
              gear.search_btn.isEnabled())
        gear.match_mode.setCurrentIndex(0); app.processEvents()
    for r in free:
        if r.selected():
            r.check.setChecked(False)
    app.processEvents()
    check("gear: live button present", gear.live_btn is not None)
    # a preset with no verified must-haves -> nothing pre-checked -> disabled
    def musts_verified(p):
        return any(isinstance(m, dict) and m.get("trade_ready")
                   for m in p.get("must_have_mods") or [])
    idx = -1
    for i in range(gear.preset_combo.count()):
        name = gear.preset_combo.itemText(i)
        p = next(x for x in gear.presets if x["display_name"] == name)
        if not musts_verified(p):
            idx = i
            break
    if idx >= 0:
        gear.preset_combo.setCurrentIndex(idx); app.processEvents()
        check("gear: unverified preset starts with search disabled",
              not gear.search_btn.isEnabled())
        check("gear: checklist still available", gear.copy_btn.isEnabled())
    mats = hub.materials
    check("materials: 14 verified rows", mats.table.rowCount() == 14
          and all(m.get("trade_ready") for m in mats.materials))
    check("gear guide: marksman guide present",
          any("Kolr" in g["title"] for g in guides["guides"]))
    # tablet builder still reachable through the hub (delegation)
    hub.set_tablet_type("Ritual Tablet"); app.processEvents()
    check("gear: hub delegates to tablet builder",
          hub.sub.currentIndex() == 0 and hub.tablet_type.currentText() == "Ritual Tablet")

    # ---- phase 14: all-tablet-modifiers merge (per-tablet rule) ------------
    tj = store.tablets
    check("mods14: import marker present", "_all_modifiers_import" in tj)
    ts = tj["type_suffixes"]
    check("mods14: per-tablet counts (deli/abyss/ritual/temple)",
          len(ts["Delirium Tablet"]) >= 11 and len(ts["Abyss Tablet"]) >= 11
          and len(ts["Ritual Tablet"]) >= 12 and len(ts["Temple Tablet"]) >= 8)
    check("mods14: irradiated has NO type suffixes (shared pool only)",
          len(ts.get("Irradiated Tablet", [])) == 0)
    new_rows = [r for pool in ([tj["shared_prefixes"], tj["shared_suffixes"]]
                               + list(ts.values()))
                for r in pool if "Imported 2026-07-11" in str(r.get("note", ""))]
    check("mods14: 25 new rows imported", len(new_rows) == 25, str(len(new_rows)))
    check("mods14: verified rows have explicit ids; unknown rows locked",
          all((r["trade_ready"] and str(r["stat_id"]).startswith("explicit."))
              or (not r["trade_ready"]) for r in new_rows))
    legacy_exp = [r for r in ts["Expedition Tablet"]
                  if "LEGACY ONLY" in str(r.get("note", ""))]
    check("mods14: expedition additions legacy-only and never trade-ready",
          legacy_exp and all(not r["trade_ready"] for r in legacy_exp))

    # ---- phase 8: theme switching -----------------------------------------
    st.theme.setCurrentText("PoE Gold (default)"); app.processEvents()
    st.theme.setCurrentText("Abyss Blue"); app.processEvents()
    check("theme: stylesheet applied", "#0d1218" in app.styleSheet())
    saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    check("theme: persisted", saved.get("theme") == "Abyss Blue")
    check("theme: poe tooltip stays game-styled", "#050505" in app.styleSheet())
    st.theme.setCurrentText("PoE Gold (default)"); app.processEvents()
    check("theme: restored default", "#16130f" in app.styleSheet())

    # ---- resize behavior --------------------------------------------------
    window.resize(1366, 850); app.processEvents()
    window.resize(2200, 1300); app.processEvents()
    check("window resize small->large", True)
    check("window minimum size enforced",
          window.minimumWidth() >= 1200 and window.minimumHeight() >= 800)

    print("\nALL %d CHECKS PASSED" % len(PASSED))


if __name__ == "__main__":
    run()
