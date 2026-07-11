# Project Status

PoE2 Tablet Farming Helper is a public work-in-progress prototype.

## Current Version

- App version: `0.9.1-phase13b-gear-builder`
- Patch/data basis: Path of Exile 2 `0.5.4b Hotfix 3`
- Last local test pass before public packaging: `python tools/full_app_test.py` -> `ALL 124 CHECKS PASSED`

## What Is Implemented

- Dashboard with strategy cards and confidence labels.
- Tablet pages for current tablet types.
- Waystone Optimizer with sourced modifier/danger tags.
- Crafting database from Craft of Exile POE2 beta data.
- Crafting guides from credited community sources.
- Expedition Whispers knowledge tab.
- Atlas Masters reference.
- Tablet trade search builder with official trade2 query generation.
- Gear preset trade builder with selectable modifier rows, min values, AND/COUNT modes, JSON preview, and live-search URL support.
- Crafting material quick searches by verified item names.
- Source Confidence tab with resolved conflict history and guardrails.

## Known Limitations

- This is not a final farming-profit calculator.
- Strategy rankings and "best setup" labels are community opinion, not official data.
- Market value and economy data can go stale quickly.
- Official `?q=` trade deep-link behavior is still treated as unverified; the app uses single user-triggered search-creation POSTs instead.
- Omen effect text and some third-party crafting details still need in-game verification.
- Craft of Exile data is third-party and can lag behind official patches.
- The app does not package a standalone executable yet; users run it with Python.

## Permanent Guardrails

- No trade listing scraping.
- No polling.
- No background searches.
- No invented stat IDs.
- Unverified rows remain visible but disabled for one-click search.
- Conflict and source labels should be preserved instead of silently choosing a winner.

## Expedition Rule

For the current project data, Expedition Tablets are treated as legacy/stale trade metadata. Expedition content is represented through Expedition Whispers, remnant order, map setup, Waystones, Atlas Masters, and other current tablets.

If future Path of Exile 2 patches reintroduce Expedition Tablets, update the data and documentation with dated evidence before enabling those workflows again.
