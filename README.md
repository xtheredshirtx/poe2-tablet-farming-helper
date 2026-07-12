# PoE2 Tablet Farming Helper

Unofficial Windows desktop helper for Path of Exile 2 tablet farming, mapping setup, crafting references, Expedition Whispers, Atlas Masters, and safe official-trade search building.

This is a public work-in-progress prototype. It is useful today, but it is not a finished economy calculator and it should not be treated as final farming advice.

> This project is fan-made and is not affiliated with, endorsed by, or supported by Grinding Gear Games.

![Dashboard](screenshots/Main%20Page.png)

## What It Does

PoE2 Tablet Farming Helper collects several farming and crafting planning tools into one local desktop app:

- Dashboard with draft strategy cards and confidence labels.
- Focused tablet pages for Ritual, Breach, Delirium, Abyss, Overseer, Irradiated, and Temple.
- Community best-setup cards for each tablet type, labeled as opinion.
- Waystone Optimizer with reward/danger tags and patch-disabled guardrails.
- Crafting tab with base browser, modifier explorer, methods, omens, essences, catalysts, and sourced craft guides.
- Expedition Whispers tab with whisper/saga rankings, Aldurs helper, and current Expedition juice context.
- Atlas Masters reference with Doryani, Hilda, and Jado node data.
- Trade Search Builder for tablets, gear presets, and crafting materials.
- Source Confidence tab showing source history, resolved conflicts, and needs-verification guardrails.
- Settings for league, trade type, investment mode, and theme.

The app is built to be cautious: uncertain data is marked, unverified trade rows are disabled for one-click search, and community recommendations are not presented as official truth.

New users can also read the plain-text walkthrough:
[NEW_USER_GUIDE.txt](NEW_USER_GUIDE.txt)

## Screenshots

### Tablets

![Tablet page](screenshots/tablet%20page.png)

### Waystone Optimizer

![Waystone page](screenshots/Waystone%20Page.png)

### Crafting

![Crafting page](screenshots/crafting%20page.png)

### Expedition Whispers

![Expedition Whispers page](screenshots/Expedition%20Whispers%20Page.png)

### Atlas Masters

![Atlas Masters page](screenshots/Atlas%20Masters%20Page.png)

### Trade Search Builder

![Trade Search page](screenshots/Trade%20Search%20Page.png)

## Download And Run

### Option 1: Download The Windows EXE Release

This is the easiest option if you do not want to install Python.

1. Open the [Releases page](https://github.com/xtheredshirtx/poe2-tablet-farming-helper/releases).
2. Download the latest `POE2TabletFarmingHelper-...-windows.zip`.
3. Extract the ZIP.
4. Double-click `POE2TabletFarmingHelper.exe`.

Windows may show a SmartScreen warning because this is a new unsigned community app. Choose **More info** and **Run anyway** only if you trust the download source.

### Option 2: Run From Source ZIP

1. Click the green **Code** button on GitHub.
2. Choose **Download ZIP**.
3. Extract the ZIP somewhere easy, such as your Desktop.
4. Open the extracted folder.
5. Double-click `run_windows.bat`.

If the app says PySide6 is missing, install the requirement:

```powershell
python -m pip install -r requirements.txt
```

Then run again:

```powershell
python main.py
```

### Option 3: Clone With Git

```powershell
git clone https://github.com/xtheredshirtx/poe2-tablet-farming-helper.git
cd poe2-tablet-farming-helper
python -m pip install -r requirements.txt
python main.py
```

## Requirements

- Windows 10 or Windows 11 recommended.
- For the EXE release: no Python install is required.
- For source installs: Python 3.10 or newer and PySide6.
- Internet access only when you click an official trade-search button or open an external source/video.

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## How To Use The App

### Dashboard

Start here for a quick overview of draft farming strategies. Strategy cards are labeled with confidence and opinion badges. Budget/high-investment toggles change the displayed setup notes.

### Tablets

Use this tab when you want to plan tablet farming by mechanic. Pick a tablet type from the side list, then read the top community setup card first. Deeper modifier pools, unique tablet notes, shared modifiers, and source warnings are kept in expandable sections so the page stays readable.

Current active tablet pages:

- Ritual
- Breach
- Delirium
- Abyss
- Overseer
- Irradiated
- Temple

Expedition Tablets are treated as legacy/stale data for the current game state. Expedition gameplay is handled in the Expedition Whispers tab.

### Waystone Optimizer

Choose a goal and safety profile. The app highlights useful Waystone modifiers and warns about dangerous or patch-disabled rows. This is a planning helper, not a guaranteed profit simulator.

### Crafting

The Crafting tab includes:

- A Craft of Exile-style base/modifier view.
- Base browser.
- Modifier explorer.
- Crafting methods.
- Omens, essences, catalysts, and special bases.
- Sourced craft guides.
- Manual cost planner.
- Crafting source confidence notes.

Craft of Exile data is third-party data. It is useful, but it should be cross-checked before expensive crafts.

### Expedition Whispers

Use this for Expedition-related planning. The current project rule is:

> If a guide says to "juice Expedition," interpret that as other current tablets, map/Waystone setup, Atlas Master support, whispers, and remnant order. Do not interpret it as Expedition Tablets.

### Atlas Masters

Browse Atlas Master nodes and unlock/reference information. Data is source-labeled and should be rechecked after patches.

### Trade Search Builder

The Trade Search Builder has three sections:

- **Tablets**: build official trade searches for tablet modifiers and presets.
- **Gear Presets**: use starter presets for common gear goals, then edit selected modifiers and min values.
- **Crafting Materials**: quick name-based searches for verified crafting material names.

Trade guardrails:

- The app performs at most one user-triggered search-creation POST per button click.
- It opens the official Path of Exile trade site in your browser.
- It does not scrape listings.
- It does not poll.
- It does not run background live searches.
- Unverified stat IDs are disabled for one-click search and remain available as checklist text.

### Source Confidence

Use this tab to see where data came from, which conflicts were resolved, and what still needs verification.

### Settings

Choose default league, trade type, investment mode, and color theme. These preferences are stored in a local `settings.json` file, which is intentionally ignored by git.

## Data Snapshot

Current packaged data includes:

- 7 current tablet pages.
- 24 shared tablet modifiers.
- 55 type-specific tablet suffixes.
- 10 unique tablet rows.
- 35 Waystone base modifiers.
- 73 tablet-juice rows.
- 10 gear presets.
- 54 verified gear trade modifier rows.
- 19 gear checklist-only rows.
- 14 verified crafting material quick-search rows.
- 2,469 crafting bases.
- 3,178 crafting modifiers.
- 93 crafting methods.
- 38 omens, 95 essences, and 26 catalysts.
- 10 sourced crafting guides.

## Work In Progress

This project is still in active development. Known WIP areas:

- Current economy/profit scoring.
- More in-game verification for some crafting effects.
- Better packaging as a standalone `.exe`.
- More screenshots and user-facing polish.
- Patch refresh workflow when Path of Exile 2 changes.

See [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) for more details.

## Development And Testing

Run the full offscreen test suite:

```powershell
python tools/full_app_test.py
```

Before this public package was prepared, the suite passed:

```text
ALL 124 CHECKS PASSED
```

## Sources And Credits

This project uses source-labeled data from official Path of Exile trade/patch metadata, PoE2DB, poe2wiki, Craft of Exile beta data, and credited community guide material. See [docs/DATA_SOURCE_REGISTRY.md](docs/DATA_SOURCE_REGISTRY.md).

Community guide entries are credited inside the app where used.

## License

MIT License. See [LICENSE](LICENSE).
