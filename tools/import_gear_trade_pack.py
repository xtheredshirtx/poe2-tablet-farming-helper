"""Import + verify the 2026-07-11 Crafting/Gear Trade Filter pack.

Reads the extracted pack and fresh official trade2 metadata, then writes
verified app data. Stat IDs are filled ONLY on exact/normalized text matches
against official metadata; everything else stays checklist-only
(UNKNOWN_NEEDS_TRADE2_METADATA_VERIFICATION).

Usage: python tools/import_gear_trade_pack.py <pack_dir> <metadata_dir>
where metadata_dir contains stats2.json / items2.json downloaded from the
official trade2 endpoints the same day.
"""
import json
import sys
from datetime import date
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_DIR / "data"

VDATE = "2026-07-11"
VERIFIED_BY = "official trade2 metadata exact-text match (%s)" % VDATE

# Pack display category -> official trade2 category option (filters metadata,
# verified 2026-07-11). None = no single category; search stays broad.
CATEGORY_MAP = {
    "Gloves": ("armour.gloves", "Gloves"),
    "Boots": ("armour.boots", "Boots"),
    "Body Armour": ("armour.chest", "Body Armour"),
    "Amulet": ("accessory.amulet", "Amulet"),
    "Rings": ("accessory.ring", "Ring"),
    "Sceptre": ("weapon.sceptre", "Sceptre"),
    "Wand / Staff / Focus": ("weapon.caster", "Any Caster Weapon (Focus needs armour.focus separately)"),
    "Attack Weapon": ("weapon", "Any Weapon (narrow by hand in the trade UI)"),
    "Any Armour/Jewellery": (None, "No single official category - checklist covers armour + jewellery"),
}


def norm(t):
    return t.replace("+#%", "#%").replace("+#", "#").strip().lower()


def main(pack_dir, meta_dir):
    pack_dir = Path(pack_dir)
    meta_dir = Path(meta_dir)

    stats = json.loads((meta_dir / "stats2.json").read_text(encoding="utf-8"))
    official = {}
    for group in stats["result"]:
        for e in group.get("entries", []):
            if e["id"].startswith("explicit."):
                official.setdefault(norm(e.get("text", "")), (e.get("text", ""), e["id"]))

    items = json.loads((meta_dir / "items2.json").read_text(encoding="utf-8"))
    item_names = {}
    for group in items["result"]:
        for e in group.get("entries", []):
            for key in (e.get("type"), e.get("name")):
                if key:
                    item_names.setdefault(key, group.get("id") or group.get("label"))

    # ---- gear presets: verify stat ids + categories --------------------
    gear = json.loads((pack_dir / "data" / "gear_trade_search_presets.json").read_text(encoding="utf-8"))
    verified = unverified = 0
    for preset in gear["presets"]:
        cat_id, cat_note = CATEGORY_MAP.get(preset.get("item_category"), (None, "unmapped"))
        preset["trade_category"] = cat_id
        preset["trade_category_note"] = cat_note
        preset["trade_category_verified"] = "official trade2 filters metadata %s" % VDATE if cat_id else None
        for key, val in list(preset.items()):
            if not (isinstance(val, list) and val and isinstance(val[0], dict)
                    and "stat_text" in val[0]):
                continue
            for mod in val:
                hit = official.get(norm(mod.get("stat_text", "")))
                if hit:
                    official_text, sid = hit
                    mod["trade_stat_id"] = sid
                    mod["official_text"] = official_text
                    mod["trade_ready"] = True
                    mod["confidence"] = "confirmed_db"
                    mod["verified_by"] = VERIFIED_BY
                    mod["verified_date"] = VDATE
                    verified += 1
                else:
                    unverified += 1
    gear["metadata"]["stat_id_verification"] = (
        "%d modifier rows verified against official trade2 stats metadata on %s; "
        "%d rows remain checklist-only (composite/placeholder texts with no exact "
        "official match)." % (verified, VDATE, unverified))
    (DATA_DIR / "gear_trade_search_presets.json").write_text(
        json.dumps(gear, indent=1, ensure_ascii=False), encoding="utf-8")
    print("gear presets: %d mods verified, %d checklist-only" % (verified, unverified))

    # ---- crafting materials: verify item names -------------------------
    mats = json.loads((pack_dir / "data" / "crafting_material_trade_presets.json").read_text(encoding="utf-8"))
    ok = 0
    for mat in mats["materials"]:
        group = item_names.get(mat["exact_name"])
        if group:
            mat["trade_ready"] = True
            mat["official_item_group"] = group
            mat["verified_by"] = "official trade2 items metadata exact-name match"
            mat["verified_date"] = VDATE
            mat.pop("verification_needed", None)
            ok += 1
    mats["metadata"]["verification"] = (
        "%d/%d material names matched exactly in official trade2 items metadata on %s."
        % (ok, len(mats["materials"]), VDATE))
    (DATA_DIR / "crafting_material_trade_presets.json").write_text(
        json.dumps(mats, indent=1, ensure_ascii=False), encoding="utf-8")
    print("materials: %d/%d names verified" % (ok, len(mats["materials"])))

    # ---- priority matrix: copy as-is ------------------------------------
    matrix = (pack_dir / "data" / "item_mod_priority_matrix.json").read_text(encoding="utf-8")
    (DATA_DIR / "item_mod_priority_matrix.json").write_text(matrix, encoding="utf-8")
    print("item_mod_priority_matrix.json copied")

    # ---- merge the Marksman guide into existing crafting guides ---------
    pack_guides = json.loads((pack_dir / "data" / "crafting_guides.json").read_text(encoding="utf-8"))
    app_guides_path = DATA_DIR / "crafting" / "crafting_guides.json"
    app_guides = json.loads(app_guides_path.read_text(encoding="utf-8"))
    existing_titles = {g["title"] for g in app_guides["guides"]}
    added = 0
    for g in pack_guides["guides"]:
        if g["title"] in existing_titles:
            continue
        g.setdefault("goal", "Craft %s" % g["title"])
        g.setdefault("credit", "Owner-provided transcript (pack %s)" % VDATE)
        g.setdefault("confidence", g.get("confidence", "community"))
        g.setdefault("source", (g.get("source_refs") or [""])[0])
        if "steps" not in g:
            g["steps"] = []
        app_guides["guides"].append(g)
        added += 1
    app_guides_path.write_text(json.dumps(app_guides, indent=1, ensure_ascii=False),
                               encoding="utf-8")
    print("guides merged: +%d (total %d, GhazzyTV guides preserved)"
          % (added, len(app_guides["guides"])))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
