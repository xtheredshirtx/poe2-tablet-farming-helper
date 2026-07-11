# Data Source Registry

Access date for Phase 2 verification: 2026-07-05 unless noted.

Reliability: High = official or direct database/metadata; Medium = reputable current guide or public sheet; Low = anecdotal, commercial, old, or uncited.

| Source | URL / local path | Type | Author | Patch/date | Reliability | Data extracted | Limitations |
|---|---|---|---|---|---|---|---|
| Owner current gameplay rule - no Expedition Tablets | N/A | Owner in-game rule | Owner | 2026-07-05 | High for current gameplay behavior | Expedition Tablets do not exist in the current game; Expedition uses logbooks/whispers instead. | If owner later reports Expedition Tablets returned in a patch, revisit explicitly. Imported Expedition Tablet data must be legacy/current_game_available=false until then. |
| Owner current gameplay interpretation - Expedition juice means other tablets | N/A | Owner in-game rule | Owner | 2026-07-05 | High for current gameplay interpretation | When current Expedition notes say to juice Expedition, interpret that as other current tablets, map/waystone modifiers, Atlas Master choices, whispers, and remnant order around Expedition content, not Expedition Tablets. | Does not make Expedition Tablet current-game-available; imported old Expedition Tablet suffixes still remain legacy only. |
| Full-project ZIP | Original uploaded research archive; local path removed for public release | Uploaded archive | Owner/session output | 2026-07-04 | High for project history | README and full research snapshot | Not all game data complete. |
| Core-doc ZIP | Original uploaded core-doc archive; local path removed for public release | Uploaded archive | Owner/session output | 2026-07-04 | High for project history | Alternate research snapshot | No README; many claims needed verification. |
| Official Early Access Patch Notes forum | https://www.pathofexile.com/forum/view-forum/2212 | Official patch index | GGG | Viewed 2026-07-05 | High | Latest visible first-page patch thread was `0.5.4b Hotfix 3` | Must recheck after every patch. |
| Official 0.5.4 Patch Notes | https://www.pathofexile.com/forum/view-thread/3975218 | Official patch notes | GGG | 2026-06-24 | High | Expedition Atlas tree, Liquid Verisium, Grand Expedition modifiers, Doryani Refined Formula update, Abyssal Depths fix | Superseded by 0.5.4b/hotfix details where applicable. |
| Official 0.5.4b Patch Notes | https://www.pathofexile.com/forum/view-thread/3980516 | Official patch notes | GGG | 2026-07-02 | High | Expedition fixes, boss fixes, Endgame fixes, Doryani/Jado fix | Read before old community guides. |
| Official 0.5.4b Hotfix 3 | https://www.pathofexile.com/forum/view-thread/3980829 | Official hotfix | GGG | 2026-07-03 | High | Verisium Remnant interaction fix and Grand Expedition portal fixes | Latest visible forum thread during Phase 2. |
| Official developer docs | https://www.pathofexile.com/developer/docs | Official docs | GGG | Current | High | API policy, OAuth cautions, user-agent/rate-limit/error guidance | Does not document every trade2 query detail. |
| Official trade2 stats metadata | https://www.pathofexile.com/api/trade2/data/stats | Official metadata endpoint | GGG | Current | High | Confirmed many `explicit.stat_*` IDs for tablet modifiers | Endpoint is not fully documented in developer docs; respect rate limits and ToS. |
| Official trade2 items metadata | https://www.pathofexile.com/api/trade2/data/items | Official metadata endpoint | GGG | Current | High | Tablet base names and unique tablet names; group `map` | Does not by itself prove query filters. |
| Official trade2 leagues metadata | https://www.pathofexile.com/api/trade2/data/leagues | Official metadata endpoint | GGG | Current | High | `Runes of Aldur`, `HC Runes of Aldur`, `Standard`, `Hardcore` | Seasonal IDs will change. |
| Official trade2 filters metadata | https://www.pathofexile.com/api/trade2/data/filters | Official metadata endpoint | GGG | Current | High | Category `map.tablet`, rarity, corruption, item level, trade status, price filters | Query POST still needs full per-filter validation. |
| Official trade2 static metadata | https://www.pathofexile.com/api/trade2/data/static | Official metadata endpoint | GGG | Current | High | Currency/static definitions available | Not deeply mined in Phase 2. |
| Official trade2 minimal POST test | https://www.pathofexile.com/api/trade2/search/poe2/Runes%20of%20Aldur | Official endpoint test | GGG | 2026-07-05 | Medium/High | Minimal tablet search returned HTTP 200 and search id | Do not poll or scrape listings; one test only. |
| Official trade2 web UI | https://www.pathofexile.com/trade2 | Official site | GGG | Current | High | Official user-facing trade surface exists | Raw shell request returned 403; normal browser behavior still needs manual validation. |
| Owner Expedition Google Sheet CSV export | https://docs.google.com/spreadsheets/d/1d5FFDUSgoL2WNbEwv1gkBra3ALnI4UsdokksSADxx_0/export?format=csv&gid=1976406181 | Public spreadsheet export | Dracorath/editor; rumor credit Guitaraholic; Travic guide linked | Exported 2026-07-05 | Medium | Rumour/map/saga rankings and notes | Community spreadsheet; not official; typos preserved in CSV. |
| Preserved spreadsheet CSV | `external_source_exports/expedition_cheat_sheet_gid1976406181.csv` | Local exported source | Same as above | 2026-07-05 | Medium | Audit copy of the owner sheet tab | Only one gid was exported. |
| PoE2DB Tablets | https://poe2db.tw/us/Tablets | Database | PoE2DB | Current | High/Medium | Tablet system, Ancient Infuser, tablet passives, Precursor Towers | PoE2DB notes modifier weight info may be unavailable. |
| PoE2DB Expedition Tablet | https://poe2db.tw/us/Expedition_Tablet | Database | PoE2DB | Current | High/Medium | Expedition Tablet base, 10 uses, Forgotten By Time text | Individual pages need repeated checks after patches. |
| PoE2DB Atlas Masters | https://poe2db.tw/us/Atlas_Masters | Database | PoE2DB | Current | High/Medium | 36 Atlas Master nodes for Jado, Doryani, Hilda; unlock notes | Phase 10 resolved the tracked Jado source conflict against PoE2DB Jado quest/map steps; still follow in-game tracker if it differs. |
| poe2wiki tablet modifier list | https://www.poe2wiki.net/wiki/List_of_modifiers_for_tablets | Community wiki/database list | poe2wiki | Current page; inherited oldid 126017 reference | High/Medium | Full modifier pools and roll ranges for many tablets | Must reconcile with official trade stats where wording differs. |
| Mobalytics, Maxroll, creator/community guides | URLs preserved in source ZIPs | Community guides | Various | 0.5.x | Medium/Low | Strategy rankings, setup ideas, warnings | Treat as opinion unless backed by data/sample sizes. |

## Phase 2 Audit Notes

- Confirmed: official patch pages, official trade metadata endpoints, PoE2DB pages, poe2wiki page, and spreadsheet CSV export were checked in Phase 2.
- Incomplete: community guide URLs from the prior snapshots were not all re-browsed in Phase 2; their claims remain inherited and lower-confidence.
- Needs source verification: final live-trade query behavior, `?q=` links, dated economy/profit samples, and any future patch changes. Phase 10 resolved the previously tracked source conflicts in app data.
- Community opinion: most strategy ratings, profit estimates, and route advice.
- Missing for future app: source IDs should become stable UUIDs in final JSON/SQLite, and every app row should link back to this registry.

## Phase 10 Tablet Juice Sources (merged 2026-07-05)

The tablet-juice update pack was imported from `../POE2_054_Tablet_Juice_Filter_Update.zip`. Its source appendix is preserved as `SOURCE_REGISTRY_APPEND_TABLET_JUICE.md`; the most important added rows are:

| Source | URL | Type | Reliability | Used for | Notes |
|---|---|---|---|---|---|
| Official trade2 stats metadata refresh | https://www.pathofexile.com/api/trade2/data/stats | Official metadata | High | Verified all 73 tablet-juice trade stat IDs and resolved the Delirium duration duplicate-ID issue. | No listing fetches or polling. |
| PoE2DB Tablet page | https://poe2db.tw/Tablet | Database | High/Medium | Tablet bases, shared/type-specific modifier text and roll ranges. | Official trade stats remain authority for `explicit.stat_*`. |
| PoE2 Regex Tablet helper | https://poe2.re/tablet | Community tool | Medium | Cross-check of visible tablet modifier wording for filter text. | Convenience cross-check only. |
| Mobalytics PoE2 0.5 patch hub | https://mobalytics.gg/poe-2/guides/0-5-patch-notes | Guide/aggregation | Medium | Current 0.5 strategy context and Monster Effectiveness discussion. | Not official; value/ranking claims stay opinion. |
| Reddit/community tablet discussions | See `SOURCE_REGISTRY_APPEND_TABLET_JUICE.md` | Community | Low/Medium | Irradiated, Expedition, Ritual, Abyss, and tablet-rolling strategy context. | Anecdotal and perishable. |
| Creator/commercial farming guides | See `SOURCE_REGISTRY_APPEND_TABLET_JUICE.md` | Community guide | Low/Medium | SS/S/A/B juice ranking context. | Profit claims require dated market samples before final scoring. |

## Phase 11 Owner Rule (2026-07-05)

The owner clarified after Phase 10 that **Expedition Tablets do not exist in the current game now**. This is authoritative for current app behavior. Trade2/PoE2DB/imported data that lists Expedition Tablet is retained only as legacy/source-history data and must not re-enable Expedition Tablet in the Tablets hub, Trade Builder, or juice presets without an explicit owner reversal.

## Phase 12 Expedition Juice Interpretation (2026-07-05)

The owner clarified that when current Expedition strategy notes say to "juice Expedition," they may be referring to what to put on other current tablets and maps around Expedition/logbook/whisper content. Current interpretation: use shared current tablet juice, Irradiated/general presets where appropriate, map/waystone modifiers, Atlas Master support, and remnant order. Do not interpret that language as a recommendation to use an Expedition Tablet.
