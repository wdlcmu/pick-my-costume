# NRF 2026 cross-check — STAGED REVIEW for Billy's approval

Date: 2026-10-23
Status: **STAGED ONLY. Nothing in this document was published, deployed, or edited on the live site.** The live homepage currently carries no NRF line at all (it was removed earlier); the corrected line below exists only here, awaiting Billy's approval.

Companion file: `hour-session/nrf-claim-check-2026-10-22.md` (claim-by-claim verdicts on every NRF wording the site has used).

---

## 1. The corrected homepage NRF line — verbatim, FOR APPROVAL

> Halloween by the numbers: Americans are expected to spend $13.5 billion on Halloween in 2026. Half of consumers plan to dress in costume. Nearly half of shoppers use AI to help with Halloween shopping. (Source: NRF 2026 Halloween survey, Sept 2026.)

Why this wording: every figure holds against the release. "Half of consumers" fixes the older draft's denominator error (the 50% is a share of all consumers surveyed, not of celebrants). "Use AI to help with Halloween shopping" fixes the older draft's activity error (47% use AI for shopping support; brainstorming alone is 34% of consumers). Short sentences, no em or en dashes, per site copy rules.

---

## 2. The authoritative lists

Source: NRF press release, "NRF Halloween Survey Shows Consumer Spending Expected to Reach $13.5 Billion," published 2026-09-22 (date on the NRF page itself). Survey by Prosper Insights & Analytics: 7,889 U.S. consumers, surveyed Sept 1–9, 2026, margin of error ±1.1 points. Cross-checked against the full release text as reproduced by Chain Store Age (2026-09-22) and The Dead Pixels Society. Supporting survey facts: $13.5B total expected spend, $115.14 per person, 74% plan to celebrate, costumes $4.4B.

### Kids (children), NRF 2026 top 5
| # | Costume | Children planning it |
|---|---------|----------------------|
| 1 | Spider-Man | 4.6 million |
| 2 | Superhero (generic) | 2.3 million |
| 3 | Princess | 2.2 million |
| 4 | Witch | 1.6 million |
| 5 | Ghost | 1.6 million |

### Adults, NRF 2026 top 5
| # | Costume | Adults planning it |
|---|---------|--------------------|
| 1 | Witch | 4.8 million |
| 2 | Vampire | 4.2 million |
| 3 | Batman | 2.0 million |
| 4 | Spider-Man | 1.5 million |
| 5 | Ghost | 1.4 million |

For the record, the release's pet list: pumpkin 11.6%, hot dog 5.9%, ghost 2.8%. PMC's bank has zero pet-audience guides, so the pet list has no PMC counterpart at all.

---

## 3. Ranked gaps: what PMC is missing, buries, or mislabels

Bank checked: `mcp-server/bank.json`, 169 guides (verified today: the sitemap's 169 bank slugs match the bank exactly).

### Gap 1 — MISSING: Batman (Adults #3, 2.0 million adults)
There is no Batman or dark-knight guide in the bank, for any audience. The closest titled guide, `night-hero` "Masked Night Hero" ("a dark cowl and a cape cut from an old t-shirt, ready for rooftop patrol"), is kid-only. `app.js` quietly routes the search term "batman" to substitutes — `caped-duo` (couple), `superhero-family` (family), `backyard-hero` (kid) — none of which is a solo adult dark-knight build. **This is the only outright absence on either list.**

### Gap 2 — MISLABELED (genericized): Spider-Man (Kids #1, 4.6 million; also Adults #4, 1.5 million)
The guide exists and is unmistakably the right costume: `web-slinger-kid` "Web Hero" (kid) — "Red sweatsuit, tape web lines, big white eye lenses." Its why-line in `app.js` even says "A Spider-Man inspired look from the closet." But neither the bank nor the guide title ever names Spider-Man; the #1 kids costume in America wears a generic name. (This genericization is deliberate IP hygiene in the bank — the finding is about findability, not about the guide's quality.) Same pattern for the duo: `web-hero-duo` "Web Hero Duo" (couple), why-line "A Spider-Man inspired duo."

Trap for anyone mapping by keyword: `spider` "Eight-Legged Spider" (kid) is an actual arachnid costume (stuffed sock legs). It is NOT the Spider-Man entry.

### Gap 3 — BURIED: Spider-Man for solo adults (Adults #4, 1.5 million)
There is no solo adult web-hero guide. An adult dressing alone reaches the look only through `web-hero-duo` (couple) or `web-slinger-crew` "Web Hero Crew" (group/class). The costume is in the bank; the solo-adult door to it is not.

### Gap 4 — COVERED, with a label note: Witch for adults (Adults #1, 4.8 million)
The solo adult witch guide is `emerald-witch` "Emerald Witch" — the green, Wicked-coded version ("an all-green-everything gown, dramatic makeup, and a pointy hat gone couture"); the homepage trend card labels its photo "Elphaba costume." The title does contain "Witch," so a searcher lands fine. But a plain black-hat solo witch exists only as `good-witch-bad-witch` (group) or `little-witch` (kid). Covered; the adult flagship witch is a character variant, not the classic.

### Covered cleanly (no action)
- Kids #2 Superhero (2.3M): `backyard-hero` "Backyard Superhero" (kid). Exact label match. Also `superhero-family` (family).
- Kids #3 Princess (2.2M): `fairy-tale-princesses` "Fairy Tale Princesses" (kid/family/group/class) and `wayfinder-princess` "Wayfinder Princess" (kid).
- Kids #4 Witch (1.6M): `little-witch` "Little Witch" (kid).
- Kids #5 Ghost (1.6M) and Adults #5 Ghost (1.4M): `classic-ghost` "Classic Ghost" (kid/solo/family) plus `pixel-ghost` (kid).
- Adults #2 Vampire (4.2M): `vampire` "Classic Vampire" (solo), plus `juke-joint-vampires` (couple).

Related, already correct: the live /aisle-dupes page presents the kids top 5 with the release's exact figures (Spider-Man 4.6M, superhero 2.3M, princess 2.2M, witch 1.6M, ghost 1.6M). The generator defect the Oct 22 check found (an invented "6.9 million" stat) has since been patched at the generator level — verified today: no "6.9" remains in `hour-session/build_aisle_dupes.py`, and the live page contains 0 occurrences of "6.9 million."

---

## 4. What this review did NOT do

- Nothing was published, deployed, or edited on any live page.
- The corrected homepage line in section 1 is staged for Billy's approval only.
- No bank, quiz, or guide changes are proposed as part of this document; Gaps 1–3 are findings for Billy's call, not work orders.
