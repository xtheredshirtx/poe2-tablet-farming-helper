"""Classify every tablet modifier's cross-tablet STACKING behavior.

Evidence base (recorded per row; NOT claimed as official):
- Community 3x-tablet strats (owner Dracorath sheet: "Run any of these 3x
  tablet strat on any map"; Phase 2 strategy matrix: Ritual x3, Breach x3,
  Delirium x3, Abyss x3, Overseer x3, "Cartographer x3 + of Pathways") imply
  the core numeric/flat modifiers stack across tablets.
- Standard PoE2 mechanics: '#% increased/reduced' modifiers from different
  sources combine additively; 'an additional X' applies per instance.
- Hilda 'Ancient Inscriptions' node ("...for each type of Tablet affecting
  Map area") confirms multiple tablets affect the same map simultaneously.

Classes written to each row as `stacking` + `stacking_note`:
  stacks        - numeric increased/reduced/more/faster/slower: additive
  stacks_flat   - 'an additional X' style: one more per tablet instance
  stacks_chance - flat '#% chance to ...': rolls per instance
  redundant     - boolean effects (never/duplicated/hunted): a second copy
                  of the same effect adds nothing
  unknown       - fixed values ('twice as likely', 'for 1 second') or rows
                  already flagged unknown/conflict - NEEDS VERIFICATION

Rerunnable; only adds/updates the two stacking fields.
"""
import json
import re
from pathlib import Path

TABLETS = Path(__file__).resolve().parent.parent / "data" / "tablets.json"
VDATE = "2026-07-12"

EVIDENCE = ("community 3x-tablet strats + standard additive stacking mechanics; "
            "not officially confirmed (%s)" % VDATE)

NOTES = {
    "stacks": "Stacks across tablets: '%% increased/reduced' values from multiple "
              "tablets affecting the same map combine additively. Evidence: " + EVIDENCE,
    "stacks_flat": "Stacks across tablets: each tablet instance adds another copy "
                   "(one more of the flat effect per tablet). Evidence: " + EVIDENCE,
    "stacks_chance": "Stacks across tablets: each tablet's chance applies per "
                     "instance (caps untested). Evidence: " + EVIDENCE,
    "redundant": "Does NOT benefit from stacking: boolean effect - a second copy "
                 "of the same effect changes nothing.",
    "unknown": "Stacking behavior UNKNOWN - NEEDS VERIFICATION (fixed-value or "
               "unverified wording). Test in game before buying duplicates for it.",
}


def classify(text, stat_status):
    t = text.lower()
    if stat_status in ("unknown", "conflict", "duplicate"):
        return "unknown"
    if "twice" in t or "for 1 second" in t or "for # second" in t:
        return "unknown"
    if "never" in t or "duplicated" in t or "hunted" in t:
        return "redundant"
    if re.search(r"%\s*(increased|reduced|more|less)", t) or \
       re.search(r"(increased|reduced|more)\b.*#%", t) or "#%" in t and (
           "increased" in t or "reduced" in t or "faster" in t or "slower" in t
           or "sooner" in t or "surpassing" in t):
        return "stacks"
    if "#% chance" in t or "% chance" in t:
        return "stacks_chance"
    if "additional" in t or t.startswith("+#") or "# additional" in t:
        return "stacks_flat"
    if "#" in t:
        return "stacks"      # remaining numeric rows (e.g. 'grant #% ...')
    return "unknown"


def main():
    data = json.loads(TABLETS.read_text(encoding="utf-8"))
    pools = [("shared_prefixes", data["shared_prefixes"]),
             ("shared_suffixes", data["shared_suffixes"])]
    pools += [("type:" + k, v) for k, v in data["type_suffixes"].items()]
    counts = {}
    for _, rows in pools:
        for r in rows:
            cls = classify(r.get("text", ""), r.get("stat_status", "confirmed"))
            r["stacking"] = cls
            r["stacking_note"] = NOTES[cls]
            counts[cls] = counts.get(cls, 0) + 1
    for u in data.get("uniques", []):
        cls = classify(u.get("text", ""), u.get("stat_status", "confirmed"))
        # unique tablet EFFECTS are one-of-a-kind; duplicates of the same unique
        # are boolean-redundant unless the effect itself is numeric
        if cls in ("stacks", "stacks_flat", "stacks_chance"):
            cls = "unknown"
        u["stacking"] = cls
        u["stacking_note"] = NOTES[cls]
        counts[cls] = counts.get(cls, 0) + 1
    data["_stacking_classification"] = (
        "%s: every modifier row classified for cross-tablet stacking "
        "(stacks/stacks_flat/stacks_chance/redundant/unknown) based on "
        "community 3x-strat evidence + standard additive mechanics. Not "
        "officially confirmed; unknown rows need in-game verification." % VDATE)
    TABLETS.write_text(json.dumps(data, indent=1, ensure_ascii=False),
                       encoding="utf-8")
    print("stacking classes:", counts)


if __name__ == "__main__":
    main()
