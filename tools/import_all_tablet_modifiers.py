"""Import the 2026-07-11 All-Tablet-Modifiers pack into data/tablets.json.

OWNER RULE enforced here: a modifier is added ONLY to the tablet type(s) that
can actually roll it, keyed strictly on the pack's tablet_type field:
- shared_prefix / shared_suffix ("All tablets") -> shared pools
- type_specific_suffix -> that tablet's own suffix list, nowhere else
- Expedition Tablet rows -> legacy Expedition section only (Expedition
  Tablets do not exist in the current game per the owner gameplay rule) and
  are never trade-enabled.

Trade stat IDs are filled ONLY on exact/normalized text matches against the
official trade2 stats metadata; everything else stays UNKNOWN.

Usage: python tools/import_all_tablet_modifiers.py <pack_data_dir> <stats_json>
"""
import json
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
TABLETS = APP_DIR / "data" / "tablets.json"
VDATE = "2026-07-11"

ROLL_RE = re.compile(r"\((\d+(?:\.\d+)?)[–—-](\d+(?:\.\d+)?)\)")
NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def placeholderize(text):
    """Turn '(12-26)% increased X' / '+2 to Y' style text into #-placeholders."""
    text = ROLL_RE.sub("#", text)
    text = NUM_RE.sub("#", text)
    text = text.replace("+#", "#")
    return text.strip()


def norm(text, loose=False):
    t = placeholderize(text).lower()
    if loose:
        t = re.sub(r"[\s']", "", t)
    return t


def main(pack_data_dir, stats_path):
    pack = json.loads((Path(pack_data_dir) / "all_tablet_modifiers.json")
                      .read_text(encoding="utf-8"))
    stats = json.loads(Path(stats_path).read_text(encoding="utf-8"))
    official_exact, official_loose = {}, {}
    for group in stats["result"]:
        for e in group.get("entries", []):
            if e["id"].startswith("explicit."):
                text = e.get("text", "")
                official_exact.setdefault(norm(text), (text, e["id"]))
                official_loose.setdefault(norm(text, loose=True), (text, e["id"]))

    tablets = json.loads(TABLETS.read_text(encoding="utf-8"))

    def existing_keys():
        keys = set()
        pools = ([("shared", tablets["shared_prefixes"]),
                  ("shared", tablets["shared_suffixes"])]
                 + [(t, rows) for t, rows in tablets["type_suffixes"].items()])
        for scope, rows in pools:
            for r in rows:
                sid = str(r.get("stat_id", ""))
                if sid.startswith("explicit."):
                    keys.add((scope, sid))
                keys.add((scope, norm(r.get("text", ""), loose=True)))
        return keys

    known = existing_keys()
    added = {"shared_prefixes": 0, "shared_suffixes": 0}
    verified = duplicates = unknown = legacy = 0

    for m in pack["modifiers"]:
        text = m["normalized_modifier_text"]
        hit = official_exact.get(norm(text)) or official_loose.get(norm(text, loose=True))
        row = {
            "name": m["id"],
            "text": hit[0] if hit else placeholderize(text),
            "roll": m.get("roll_range_text") or "",
            "stat_id": hit[1] if hit else "UNKNOWN - NEEDS VERIFICATION",
            "stat_status": "confirmed" if hit else "unknown",
            "rating": m.get("farming_value_rating") or "Unknown",
            "best_for": m.get("best_for") or m.get("affected_mechanic") or "",
            "confidence": "database",
            "trade_ready": bool(hit),
            "note": ("Imported %s from PoE2DB Precursor Towers Mods /83 (pack id %s). %s"
                     % (VDATE, m["id"], (m.get("player_notes") or ""))).strip(),
            "danger": m.get("danger_level"),
            "tags": m.get("tags") or [],
        }
        if hit:
            row["note"] += " Stat ID verified against official trade2 metadata %s." % VDATE
            verified += 1
        else:
            unknown += 1

        ttype = m["tablet_type"]
        if ttype == "All tablets":
            scope = "shared"
            pool_name = ("shared_prefixes" if m["prefix_or_suffix"] == "Prefix"
                         else "shared_suffixes")
            pool = tablets[pool_name]
        else:
            scope = ttype
            pool = tablets["type_suffixes"].setdefault(ttype, [])
            pool_name = None

        sid_key = (scope, row["stat_id"]) if row["stat_id"].startswith("explicit.") else None
        text_key = (scope, norm(row["text"], loose=True))
        if (sid_key and sid_key in known) or text_key in known:
            duplicates += 1
            continue

        if ttype == "Expedition Tablet":
            row["trade_ready"] = False
            row["note"] = ("LEGACY ONLY - Expedition Tablets do not exist in the "
                           "current game (owner rule); kept for history. " + row["note"])
            legacy += 1
        pool.append(row)
        known.add(text_key)
        if sid_key:
            known.add(sid_key)
        if pool_name:
            added[pool_name] += 1

    tablets["_all_modifiers_import"] = (
        "%s: merged the PoE2DB 83-modifier pack. Rows added ONLY to the tablet "
        "types that can roll them (owner rule). %d stat IDs verified against "
        "official trade2 metadata, %d stay UNKNOWN, %d duplicates skipped, "
        "%d Expedition rows stored as legacy only." % (VDATE, verified, unknown,
                                                       duplicates, legacy))
    TABLETS.write_text(json.dumps(tablets, indent=1, ensure_ascii=False),
                       encoding="utf-8")

    counts = {t: len(rows) for t, rows in tablets["type_suffixes"].items()}
    print("verified:", verified, "| unknown:", unknown,
          "| duplicates skipped:", duplicates, "| expedition legacy:", legacy)
    print("shared added:", added)
    print("type_suffix counts now:", counts)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
