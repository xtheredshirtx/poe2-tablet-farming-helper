"""Convert raw Craft of Exile beta POE2 data into normalized app JSON.

Input : raw_sources/craftofexile/{data,english,prices,settings}.json
        (JS assignments like `coedata={...}` downloaded from the static URLs
        referenced by https://beta.craftofexile.com/?game=poe2)
Output: POE2FarmingHelper/data/crafting/*.json  (11 files)

Guardrails: original Craft of Exile IDs are preserved; nothing is invented.
Weights come from Craft of Exile's classmods table and are third-party
estimates, not official GGG data. Simulation data is not converted.
"""
import hashlib
import json
from datetime import date
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = APP_DIR.parent / "raw_sources" / "craftofexile"
OUT_DIR = APP_DIR / "data" / "crafting"

COE_PATCH = "4.5.4.1.2"
COE_PATCH_LABEL = "0.5.4.1.2"
COE_LEAGUE_LABEL = "Return of the Ancients"
ACCESS_DATE = "2026-07-05"

GROUP_TYPES = {1: "prefix", 2: "suffix", 3: "unique", 4: "nemesis", 5: "corrupted"}

SPECIAL_BASE_KEYWORDS = [
    "Gloam", "Tenebrous", "Dusk", "Penumbra", "Distorted", "Absent",
    "Portent", "Lament", "Corona", "Stalking", "Grasping Mail",
    "Breach Ring", "Runic Ward", "Altered Collarbone",
]


def load_js(path):
    text = path.read_text(encoding="utf-8")
    payload = text.split("=", 1)[1].strip().rstrip(";")
    return json.loads(payload)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data = load_js(RAW_DIR / "data.json")
    lang = load_js(RAW_DIR / "english.json")

    def L(i):
        if isinstance(i, int) and 0 <= i < len(lang):
            return lang[i]
        return i

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    classes = {c["id"]: c for c in data["classes"]["entries"]}
    class_name = {cid: L(c["label"]) for cid, c in classes.items()}
    categories = {c["id"]: L(c["label"]) for c in data["categories"]["entries"]}
    tags = {t["id"]: L(t.get("label")) for t in data["tags"]["entries"]}
    modgroups = {g["id"]: g for g in data["modgroups"]["entries"]}
    domains = {int(k): v for k, v in data["enums"]["domains"].items()}
    items_by_id = {i["id"]: i for i in data["items"]["entries"]}

    def item_name(item_id):
        entry = items_by_id.get(item_id)
        return L(entry["label"]) if entry else None

    mods_by_id = {m["id"]: m for m in data["mods"]["entries"]}

    def mod_text(mod):
        parts = []
        for stat in mod.get("stats") or []:
            text = L(stat.get("label"))
            rng = stat.get("range")
            if rng and stat.get("values"):
                lo, hi = rng[0], rng[1]
                span = ("%g" % lo) if lo == hi else ("%g-%g" % (lo, hi))
                text = "%s (%s)" % (text, span)
            parts.append(str(text))
        return "; ".join(parts)

    # weights: classmods is {class_id: {mod_id: weight}} -> invert per mod
    weights_by_mod = {}
    for cid, modmap in data["classmods"].items():
        cname = class_name.get(int(cid), "class %s" % cid)
        for mid, weight in modmap.items():
            weights_by_mod.setdefault(int(mid), {})[cname] = weight

    # ---- crafting_bases.json ----------------------------------------
    bases = []
    for it in data["items"]["entries"]:
        cls = classes.get(it.get("class"))
        bases.append({
            "coe_id": it["id"],
            "key": it.get("key"),
            "name": L(it.get("label")),
            "class_id": it.get("class"),
            "class": class_name.get(it.get("class")),
            "category": categories.get((cls or {}).get("group")),
            "drop_level": it.get("drop"),
            "implicit_mod_ids": it.get("implicits") or [],
            "implicits": [mod_text(mods_by_id[m]) for m in (it.get("implicits") or [])
                          if m in mods_by_id],
            "domain": domains.get(it.get("domain")),
            "requirements": it.get("reqs"),
            "properties": it.get("props"),
            "tags": [tags[t] for t in (it.get("tags") or []) if tags.get(t)],
            "sockets": it.get("sockets"),
            "corrupted_only": it.get("corrupt", False),
            "unmodifiable": it.get("unmodifiable", False),
            "wiki": it.get("wiki"),
        })

    # ---- crafting_modifiers.json ------------------------------------
    modifiers = []
    for m in data["mods"]["entries"]:
        group = modgroups.get(m.get("group"), {})
        modifiers.append({
            "coe_id": m["id"],
            "key": m.get("key"),
            "name": L(m.get("label")),
            "text": mod_text(m),
            "group_id": m.get("group"),
            "affix": GROUP_TYPES.get(group.get("type"), "other(%s)" % group.get("type")),
            "domain": domains.get(group.get("domain")),
            "tags": [tags[t] for t in (group.get("tags") or []) if tags.get(t)],
            "families": group.get("families") or [],
            "min_item_level": m.get("minlvl"),
            "max_item_level": m.get("maxlvl"),
            "power": m.get("power"),
            "weights_by_class": weights_by_mod.get(m["id"], {}),
            "weight_note": "Craft of Exile estimate - third party, not official",
        })

    # ---- crafting_methods.json --------------------------------------
    def flatten_methods(nodes, group_label=None, out=None):
        out = out if out is not None else []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            label = node.get("label") or item_name(node.get("item")) or node.get("handler")
            entry = {
                "coe_id": node.get("id"),
                "name": label if isinstance(label, str) else L(label),
                "group": group_label,
                "currency_item": item_name(node.get("item")),
                "handler": node.get("handler"),
                "constraints": node.get("constraints"),
                "omens": node.get("omens"),
                "properties": node.get("properties"),
                "reroll_affix_types": node.get("reroll"),
            }
            if node.get("handler") or node.get("item"):
                out.append(entry)
            children = node.get("elements") or []
            flatten_methods(children, entry["name"] if node.get("label") else group_label, out)
        return out

    methods = flatten_methods(data["methods"]["crafting"])

    # ---- crafting_omens.json ----------------------------------------
    descriptions = data["items"].get("descriptions") or {}

    def item_description(item_id):
        entry = items_by_id.get(item_id, {})
        key = entry.get("key")
        desc = descriptions.get(str(item_id)) or descriptions.get(key)
        if isinstance(desc, int):
            return L(desc)
        return desc

    omens = []
    for o in data["methods"]["omens"]["entries"]:
        omens.append({
            "item_id": o.get("item"),
            "name": item_name(o.get("item")),
            "action": o.get("action"),
            "constraints": o.get("constraints"),
            "description": item_description(o.get("item")),
            "effect_text_status": "action id from Craft of Exile; exact in-game text NEEDS VERIFICATION",
        })

    # ---- crafting_essences.json -------------------------------------
    essence_types = data["essences"].get("types")
    essences = []
    for e in data["essences"]["entries"]:
        essences.append({
            "coe_id": e.get("id"),
            "item_id": e.get("item"),
            "name": item_name(e.get("item")) or L(e.get("label")),
            "type": e.get("type"),
            "level": e.get("level"),
            "restriction": e.get("restriction"),
        })

    # ---- crafting_catalysts.json ------------------------------------
    catalysts = [b for b in bases
                 if b["name"] and "Catalyst" in b["name"]]

    # ---- crafting_special_bases.json ---------------------------------
    special = [b for b in bases if b["name"] and any(
        k.lower() in b["name"].lower() for k in SPECIAL_BASE_KEYWORDS)]

    # ---- crafting_tags.json ------------------------------------------
    tag_rows = [{"coe_id": t["id"], "name": L(t.get("label")), "key": t.get("key")}
                for t in data["tags"]["entries"]]

    # ---- crafting_sources.json ---------------------------------------
    sources = {
        "_note": "Craft of Exile is third-party and not affiliated with GGG. "
                 "Weights/odds are estimates. Simulation is out of scope.",
        "coe_patch": COE_PATCH,
        "coe_patch_label": COE_PATCH_LABEL,
        "coe_league_label": COE_LEAGUE_LABEL,
        "league_label_conflict": "Craft of Exile labels the league 'Return of the Ancients' "
                                 "but the official trade2 API lists 'Runes of Aldur' as the "
                                 "current league (verified %s). Treat labels separately." % ACCESS_DATE,
        "accessed": ACCESS_DATE,
        "sources": [
            {"name": "Craft of Exile Beta POE2 app shell", "url": "https://beta.craftofexile.com/?game=poe2", "type": "Third-party crafting/data app", "reliability": "Medium/High utility, not official"},
            {"name": "Craft of Exile Beta POE2 data.json", "url": "https://beta.craftofexile.com/json/poe2/4.5.4.1.2/data.json", "type": "Static data file referenced by the app shell", "reliability": "Medium/High utility, not official"},
            {"name": "Craft of Exile Beta POE2 english.json", "url": "https://beta.craftofexile.com/json/poe2/4.5.4.1.2/localization/english.json", "type": "Localization file", "reliability": "Medium/High"},
            {"name": "Craft of Exile Beta POE2 prices.json", "url": "https://beta.craftofexile.com/json/poe2/4.5.4.1.2/prices.json", "type": "Third-party price snapshot", "reliability": "Medium; perishable"},
            {"name": "Official trade2 leagues metadata", "url": "https://www.pathofexile.com/api/trade2/data/leagues", "type": "Official metadata", "reliability": "High"},
        ],
    }

    # ---- crafting_guides.json ----------------------------------------
    guides = {
        "_note": "No step-by-step guide content is exposed by the Craft of Exile "
                 "POE2 data files. Guides must be added only with a real source. "
                 "Do not invent guide steps.",
        "guides": [],
    }
    existing_guides_path = OUT_DIR / "crafting_guides.json"
    existing_guides_count = 0
    if existing_guides_path.exists():
        try:
            existing_guides_count = len(json.loads(
                existing_guides_path.read_text(encoding="utf-8")).get("guides", []))
        except (ValueError, OSError):
            pass

    outputs = {
        "crafting_sources.json": sources,
        "crafting_bases.json": {"_source": "Craft of Exile beta data.json items", "_patch": COE_PATCH_LABEL, "_accessed": ACCESS_DATE, "bases": bases},
        "crafting_modifiers.json": {"_source": "Craft of Exile beta data.json mods/modgroups/classmods", "_patch": COE_PATCH_LABEL, "_accessed": ACCESS_DATE, "modifiers": modifiers},
        "crafting_methods.json": {"_source": "Craft of Exile beta data.json methods.crafting", "_patch": COE_PATCH_LABEL, "_accessed": ACCESS_DATE, "methods": methods},
        "crafting_omens.json": {"_source": "Craft of Exile beta data.json methods.omens", "_patch": COE_PATCH_LABEL, "_accessed": ACCESS_DATE, "omens": omens},
        "crafting_essences.json": {"_source": "Craft of Exile beta data.json essences", "_patch": COE_PATCH_LABEL, "_accessed": ACCESS_DATE, "essence_types": essence_types, "essences": essences},
        "crafting_catalysts.json": {"_source": "Craft of Exile beta data.json items (name contains Catalyst)", "_patch": COE_PATCH_LABEL, "_accessed": ACCESS_DATE, "catalysts": catalysts},
        "crafting_special_bases.json": {"_source": "Craft of Exile beta data.json items filtered by Phase 6 special-base keyword list", "_patch": COE_PATCH_LABEL, "_accessed": ACCESS_DATE, "keywords": SPECIAL_BASE_KEYWORDS, "special_bases": special},
        "crafting_guides.json": guides,
        "crafting_tags.json": {"_source": "Craft of Exile beta data.json tags", "_patch": COE_PATCH_LABEL, "_accessed": ACCESS_DATE, "tags": tag_rows},
    }

    manifest = {
        "extraction_date": ACCESS_DATE,
        "converted_on": str(date.today()),
        "coe_patch": COE_PATCH,
        "coe_patch_label": COE_PATCH_LABEL,
        "coe_league_label": COE_LEAGUE_LABEL,
        "raw_files": [
            {"file": f.name, "bytes": f.stat().st_size, "sha256": sha256(f)}
            for f in sorted(RAW_DIR.glob("*")) if f.is_file()
        ],
        "counts": {
            "bases": len(bases),
            "modifiers": len(modifiers),
            "mod_groups": len(modgroups),
            "methods": len(methods),
            "omens": len(omens),
            "essences": len(essences),
            "catalysts": len(catalysts),
            "special_bases": len(special),
            "tags": len(tag_rows),
            "classes": len(classes),
            "guides": existing_guides_count,
        },
        "known_gaps": [
            "Omen exact in-game effect text not present in data files; only Craft of Exile action ids.",
            "Craft of Exile exposes no guide/how-to content; existing sourced community guides are preserved and not overwritten.",
            "Weights are Craft of Exile estimates, not official GGG weights.",
            "Simulation/odds calculations were intentionally not extracted (owner scope).",
            "League label mismatch: CoE 'Return of the Ancients' vs official 'Runes of Aldur'.",
        ],
    }
    outputs["crafting_extraction_manifest.json"] = manifest

    for name, payload in outputs.items():
        path = OUT_DIR / name
        if name == "crafting_guides.json" and path.exists():
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (ValueError, OSError):
                existing = {}
            if existing.get("guides"):
                print("kept  %-38s (has %d sourced guides — not overwritten)"
                      % (name, len(existing["guides"])))
                continue
        path.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
        print("wrote %-38s %8d bytes" % (name, path.stat().st_size))

    print("\ncounts:", json.dumps(manifest["counts"]))


if __name__ == "__main__":
    main()
