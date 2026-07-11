"""Loads the JSON seed data derived from the Phase 2 research folder."""
import json
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    DATA_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)) / "data"
else:
    APP_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = APP_DIR / "data"
SETTINGS_FILE = APP_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "league": "Runes of Aldur",
    "trade_status": "securable",
    "budget_mode": "budget",
    "theme": "PoE Gold (default)",
}


class DataStore:
    def __init__(self):
        self.meta = self._load("meta.json")
        self.tablets = self._load("tablets.json")
        self.waystones = self._load_optional("waystones.json", {"base_mods": [], "goals": []})
        self.strategies = self._load("strategies.json")["strategies"]
        self.expedition = self._load("expedition.json")
        self.atlas = self._load("atlas_masters.json")
        self.sources = self._load("sources.json")
        self.trade_presets = self._load_optional(
            "trade_presets.json", {"presets": []})["presets"]
        self.gear_presets = self._load_optional(
            "gear_trade_search_presets.json", {"presets": []})["presets"]
        self.crafting_materials = self._load_optional(
            "crafting_material_trade_presets.json", {"materials": []})["materials"]
        self.mod_priority_matrix = self._load_optional(
            "item_mod_priority_matrix.json", {})
        self.tablet_juice = self._load_optional(
            "tablet_juice_currency_filters.json",
            {"modifiers": [], "unique_tablets": [], "filter_presets": []})
        self.tablet_juice_presets = self._load_optional(
            "tablet_trade_filter_presets.json", {"presets": []})["presets"]
        self.tablet_juice_modifiers = self.tablet_juice.get("modifiers", [])
        self.settings = self._load_settings()
        self._crafting_cache = {}

    def crafting(self, name):
        """Lazy-load a data/crafting/<name>.json file (cached). Returns None
        if the Phase 6 crafting extraction has not been run."""
        if name not in self._crafting_cache:
            path = DATA_DIR / "crafting" / (name + ".json")
            if not path.exists():
                self._crafting_cache[name] = None
            else:
                try:
                    with open(path, encoding="utf-8") as f:
                        self._crafting_cache[name] = json.load(f)
                except (json.JSONDecodeError, OSError):
                    self._crafting_cache[name] = None
        return self._crafting_cache[name]

    @staticmethod
    def _load(name):
        with open(DATA_DIR / name, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _load_optional(name, fallback):
        path = DATA_DIR / name
        if not path.exists():
            return fallback
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return fallback

    def _load_settings(self):
        settings = dict(DEFAULT_SETTINGS)
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, encoding="utf-8") as f:
                    settings.update(json.load(f))
            except (json.JSONDecodeError, OSError):
                pass
        return settings

    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)

    # ---- tablet helpers -------------------------------------------------
    def tablet_base_names(self):
        """Current in-game tablet bases (owner-confirmed). Bases flagged
        removed_from_game (e.g. Expedition since the whispers rework) are
        excluded from the UI but their data stays on disk as legacy."""
        return [b["name"] for b in self.tablets["bases"]
                if not b.get("removed_from_game")]

    def mod_display_text(self, name_hint):
        """Resolve a community mod name/hint to the in-game modifier text.
        The game shows modifier text, never internal names, so UI cards should
        display text. Returns the hint unchanged when nothing matches."""
        pools = (self.tablets["shared_prefixes"] + self.tablets["shared_suffixes"])
        for suffixes in self.tablets["type_suffixes"].values():
            pools = pools + suffixes
        hint = name_hint.lower()
        best = None
        for row in pools:
            name = row.get("name", "")
            if name and name.lower() in hint:
                if best is None or len(name) > len(best.get("name", "")):
                    best = row
        if best is not None:
            roll = best.get("roll")
            text = best.get("text", name_hint)
            return "%s (%s)" % (text, roll) if roll and "(" not in text else text
        for u in self.tablets["uniques"]:
            if u["name"].lower() in hint:
                return "%s: %s" % (u["name"], u["text"])
        return name_hint

    def modifiers_for_type(self, base_name, include_shared=True):
        """All modifier rows applicable to a tablet base."""
        rows = []
        if include_shared:
            for row in self.tablets["shared_prefixes"]:
                rows.append({**row, "slot": "Prefix (shared)"})
            for row in self.tablets["shared_suffixes"]:
                rows.append({**row, "slot": "Suffix (shared)"})
        for row in self.tablets["type_suffixes"].get(base_name, []):
            rows.append({**row, "slot": "Suffix (%s)" % base_name})
        return rows

    def all_modifier_rows(self):
        """Every modifier row with a slot label, for the database browser."""
        rows = []
        for row in self.tablets["shared_prefixes"]:
            rows.append({**row, "slot": "Prefix (shared)", "tablet": "All tablets"})
        for row in self.tablets["shared_suffixes"]:
            rows.append({**row, "slot": "Suffix (shared)", "tablet": "All tablets"})
        for base, suffixes in self.tablets["type_suffixes"].items():
            for row in suffixes:
                rows.append({**row, "slot": "Suffix", "tablet": base})
        return rows

    def patch_banner(self):
        p = self.meta["patch"]
        return ("Patch basis: %s (posted %s, verified %s). "
                "Recheck the official patch forum before trusting recommendations."
                % (p["version"], p["posted"], p["verified"]))
