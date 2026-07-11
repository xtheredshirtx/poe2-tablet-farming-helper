# Implementation Readiness Report

Prepared 2026-07-05 for Phase 2.

## Executive Decision

The project is ready for Phase 3 MVP/prototype coding.

It is not ready for full production-final recommendations, automated trade result fetching, or a complete Waystone optimizer. The correct next step is to build the program now with guardrails: data viewer first, confidence/conflict badges everywhere, and trade search disabled for unknown or conflicted stat IDs.

In plain English: yes, there is enough data to start building the app. No, there is not enough data to pretend every farming ranking and every trade preset is final.

## What Is Ready For Coding

| Area | Readiness | Notes |
|---|---|---|
| Source registry viewer | Ready | Canonical sources and confidence rules exist. |
| Tablet database viewer | Prototype-ready | Many modifier rows and trade stat IDs are confirmed; conflicts can be shown as badges. |
| Expedition spreadsheet viewer | Prototype-ready | Owner sheet CSV export succeeded and is preserved locally. |
| Atlas Master reference | Prototype-ready | PoE2DB provides all 36 node names/effects. |
| Trade Search Builder UI shell | Prototype-ready | Can show fields, missing-ID warnings, and generated debug JSON. |
| Schema drafting | Ready | Draft schema files exist. |

## Build-Now Instruction For Phase 3

The next LLM/developer should begin implementation now. Build a Windows desktop MVP/prototype using the Phase 2 canonical folder as the source of truth.

Minimum useful MVP:

1. Professional dark themed app shell.
2. Dashboard with draft strategy cards and confidence badges.
3. Tablet Database tab using confirmed modifier rows and stat IDs.
4. Expedition Tablet tab.
5. Expedition Logbook Planner using `external_source_exports/expedition_cheat_sheet_gid1976406181.csv`.
6. Atlas Masters tab using the 36 node records documented in `ATLAS_MASTER_UNLOCKS_AND_CHOICES.md`.
7. Trade Search Builder that only enables official trade search generation when all selected stat IDs are confirmed.
8. Source Confidence / Patch Notes tab.
9. Settings / League Selection tab.

Guardrails:

- Unknown data must remain visible as `UNKNOWN - NEEDS VERIFICATION`.
- Conflicted data must show conflict badges.
- No trade result scraping.
- No background polling.
- No final profit claims without source/date/confidence.
- Update `PROJECT_CONTEXT_AND_RESEARCH_LOG.md` before stopping.

## What Is Not Ready

| Area | Status | Blocker |
|---|---|---|
| Production one-click trade searches | Not ready | Query body with stat filters and `?q=` deep links need browser/live verification. |
| Final tablet rankings | Not ready | Community opinion and economy data are not enough for final "best" claims. |
| Waystone Optimizer | Not ready | Full Waystone modifier pool and trade IDs are missing. |
| Temple/Vaal Beacon tab | Not ready | Temple suffix roll ranges and reward strategy incomplete. |
| Final Expedition/logbook optimizer | Not ready | Spreadsheet imported, but exact remnant IDs/text and tested rates are incomplete. |
| Atlas unlock checklist | Not ready for final wording | Jado unlock and quest step wording conflicts remain. |
| Machine-readable runtime data | Not ready | No JSON/SQLite export exists yet. |

## Critical Missing Data

1. Full Waystone modifier pool with roll ranges, danger tags, and trade IDs.
2. Full Temple Tablet suffix pool with roll ranges and strategy value.
3. Verified live trade query examples for each tablet type.
4. Browser verification of `?q=` trade2 deep links.
5. Resolution of Ritual Tribute cost wording conflicts.
6. Resolution of Delirium fog/stat duplicate conflicts.
7. In-game or database-confirmed Atlas Master unlock quest text.
8. Current market/economy observations with dates and sample sizes.
9. Final unique tablet effect text for Irradiated and Breach unique tablets.

## Data Completeness By Domain

| Domain | Completeness | Coding recommendation |
|---|---|---|
| Tablet modifier data | Moderate/High for core tablet modifiers; Low/Medium for conflicts and Temple | Code viewer only; block final presets on conflicts. |
| Trade search data | Moderate | Code UI skeleton; one-click searches need validation harness first. |
| Expedition/logbook data | Moderate | Code planner table prototype; mark as community spreadsheet. |
| Atlas Master data | Moderate/High for nodes; Medium/Low for unlock steps | Code node reference; unlock checklist needs conflict labels. |
| UI planning | High enough for prototype | Build data-driven UI only after schema conversion. |
| Waystones | Low | Do not build optimizer beyond placeholder/requirements. |
| Strategy recommendations | Medium/Low | Use "draft/opinion" labels, no final scoring. |

## Recommended Next Phase

Phase 3 should continue research and produce machine-readable seed data, while allowing a read-only prototype in parallel.

Recommended order:

1. Create a `data_dev/` draft JSON export from confirmed tables only.
2. Build a trade validation harness that performs user-triggered test POSTs and opens official URLs, without fetching listings in loops.
3. Verify `?q=` deep links in a normal browser.
4. Extract Waystone and Temple data.
5. Resolve Ritual/Delirium conflicts.
6. Only then build final recommendation scoring and production trade presets.

## Ready-To-Code Scope If Prototype Starts Now

Acceptable:

- Markdown/JSON-backed desktop viewer.
- Source registry table.
- Tablet modifier browser with filters.
- Expedition CSV table and rumour rank cards.
- Atlas Master node browser.
- Trade Search Builder form that warns and refuses unverified preset execution.

Not acceptable yet:

- Automated trade listing fetch.
- Background live searches.
- Hard-coded stat IDs not present in the registry.
- Final "best current farming" claims without opinion badges.
- Waystone optimizer as if complete.

## Final Readiness Statement

Still needs research before full app coding. A careful prototype can begin, but the next LLM should continue verification rather than treating the data as final.

## Phase 2 Audit Notes

- Confirmed: readiness was evaluated after merging both ZIPs, importing the spreadsheet CSV, extracting official trade metadata, and creating schema drafts.
- Incomplete: no runnable app, JSON export, or validated live trade preset was created.
- Needs source verification: trade deep links, full Waystone data, Temple data, Ritual/Delirium conflicts, and Atlas unlock wording.
- Community opinion: strategy rankings and profit expectations.
- Missing for future app: final runtime data files, validation harness, and UI prototype.

## Phase 6 Crafting Readiness (added 2026-07-05)

| Area | Readiness | Notes |
|---|---|---|
| Crafting base/modifier database | Built (third-party) | 2,469 bases and 3,178 modifiers extracted from Craft of Exile beta data.json (CoE patch 0.5.4.1.2); original CoE IDs preserved; rerunnable converter at `POE2FarmingHelper/tools/convert_craftofexile.py`. |
| Modifier weights | Usable with caveat | Per-class weights extracted; they are Craft of Exile ESTIMATES, labeled as third-party in data and UI. Not official. |
| Crafting methods | Built | 93 method cards with constraints and omen hooks from the CoE method tree. Exact in-game behavior should be verified before high-cost crafts. |
| Omens | Partial | 38 omen/saga records with CoE action ids; exact in-game effect text NEEDS VERIFICATION. |
| Essences / Catalysts / Special bases | Built | 95 / 26 / 36 records respectively. |
| Craft guides | Empty by design | CoE exposes no guide content; guides require a real source before being added. |
| Crafting odds / simulation | Out of scope | Owner decision; nothing extracted or shown. |
| Crafting tab UI | Built | 8 sections with progressive disclosure; league-label conflict and third-party warnings displayed. |

Blockers for production-final crafting guidance: omen effect text verification, CoE vs official league label reconciliation, independent cross-checks of top-value modifiers, and dated economy prices for the cost planner.
