# Stale cross-promo sweep — FINAL report

Date: 2026-10-23
Scope: every deployed Pick My Costume surface, checked for links or promos pointing at sites Billy has killed or cut.

## Targets (dead/cut sites)
- **myweeklymove.com** (My Weekly Move) — KILLED Oct 21, 2026.
- **lifecapital.app** — CUT Oct 21, 2026 (to be folded into Clearline Family).
- **vitennia.com** — CUT Oct 21, 2026 (same).

Search patterns: `myweeklymove`, `my-weekly-move`, `my weekly move`, `weekly move`, `lifecapital`, `life capital`, `vitennia` — case-insensitive.

## Surfaces checked
- All root `*.html` pages (the deployed page set).
- `app.js` and the other root JS.
- `functions/` — the generated surfaces: `functions/c/[slug].js` (all 169 guide pages), the three hub functions (`couples.js`, `family.js`, `last-minute.js`), `functions/map/[[path]].js` (embedded map.html), `functions/browse/[[path]].js`, party/reminder/send-instructions functions.
- `collections/` pages.
- `llms.txt` and `llms-full.txt`.
- `sitemap.xml` and `_redirects` (every redirect target is internal to pickmycostume.com).
- `mcp-server` JS/JSON (read-only check; the MCP server is frozen regardless).
- Live spot checks fetched 2026-10-23: `/`, `/c/classic-ghost`, `/costumes`, `/about`.

## Result: ZERO stale promos found. Nothing to remove or replace.
- No deployed page, script, function, or data file links to or mentions any of the three dead/cut sites.
- Root pages carry essentially no outbound sister-site promo links at all — the only external https links in the page set are Google Fonts and one Frightgeist link. There is no cross-promo block left to go stale.
- All live spot checks returned 0 matches.
- The single text hit in the entire workspace tree is internal and not user-facing: `hour-session/ai-citation-onsite-checklist.md` line 153, a section heading "## Same notes for myweeklymove.com" in a working checklist doc. It is not deployed, not linked from any page, and not a promo. Left in place: it is an internal note, and deleting working files was outside this sweep's scope.

## Bottom line
The stale cross-promo sweep is CLOSED. An earlier cleanup (or the absence of any promo block) means PMC never carried live promos to the killed/cut sites on its deployed surfaces. No code changed and nothing was deployed for this item; this report is the sweep's first and final record.
