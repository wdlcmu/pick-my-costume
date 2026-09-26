# Pick My Costume — Experiment Ledger

Every bet we've made on this site, what we assumed, what we projected, what
actually happened, and what we learned. Plain-English names first; internal
codes in parentheses for traceability.

**Standing truth, updated 2026-09-25:** we have almost no stranger traffic.
The site is used by Billy's insider circle (a handful of Seattle iPhones).
That means most "observed" columns below honestly read "no traffic read yet."
A shipped experiment with green gates and a live verification is a *bet
placed*, not a *bet won*. This ledger exists so we never confuse the two.

---

## Holistic read: what the experiments are telling us

### Assumptions that have held up

1. **The loop is persona-driven, not average-driven.** The share-loop
   simulation (Sep 23) found family-chat shares work ~40x harder than casual
   shares. Everything since — personal cards, cast mapping, the reciprocal
   share copy — has been built on this, and Billy's own family-chat tests
   keep confirming it.
2. **Honest math beats inflated claims.** The pantry "10 costumes you can
   make tonight" idea died on contact with the real materials data (zero
   makeable under every defensible assumption set). The honest reframe —
   "5 costumes are 1-2 items away" — shipped instead. Same pattern in the
   search work: terms with no genuine bank match stay unmapped and get
   logged as gaps instead of force-matched.
3. **The site's own copy is a spec.** Twice now, shipping meant making the
   site do what its words already promised ("tap one to save your pick" →
   whole-card tap; "why this fits you" → actually about you). When copy and
   behavior disagree, behavior is the bug.
4. **Simulate before shipping bank or quiz changes.** The all-paths gate
   (every answer path returns 3 results, #1 matches the picked interest)
   has caught real defects multiple times. No bank change ships without it.

### Assumptions that have been challenged

1. **"Our interest tags describe our costumes."** The Sep 25 critic rerun
   proved this false: 15 tags (vampire/dinos, zombie-coworker/dinos,
   garden-gnome/princess, etc.) had no grounding in the visible copy. We
   stripped them. Cost: four thin pools dropped below the hard-filter
   threshold, including solo dinosaurs going to zero until the new dino
   batch lands. Lesson: metadata lies; the gate now checks tags against
   visible copy (title, blurb, why-line).
2. **"Baseline share rate is 15%."** The simulation assumed it; Billy's own
   testing suggested ~4%. If 4% is true, every absolute R number in the Sep
   23 simulation is overstated — only the *ranking* of experiments survives.
   Lesson: re-run the simulation with a 4% baseline before citing absolute
   numbers again.
3. **"More options = better."** The interest question keeps its full set
   (shrinking it was rejected — findability is a data problem, not a
   question problem), but the kid-age question now asks itself out of a job
   on ~30% of paths, and the fit question fires only when it changes
   results. Every question must earn its place.
4. **"Browse is the surface to optimize."** Billy corrected this directly:
   the site optimizes for the creation loop (quiz → pick → share → plan),
   not browsing. Browse is secondary. The E25 interactive-browse-videos
   prototype stays staged partly for this reason.

### Assumptions still untested (need real traffic)

- Whether card-origin shares actually outperform generic shares 2x (the
  share-origin test's decision rule).
- Whether any share-message variant moves recipient behavior (the A/B test).
- Whether the homepage proof strip lifts quiz starts.
- Whether photo or cutout thumbnails win on browse.
- The audience-mismatch cost of pre-answering a recipient's first question
  (the one thing that could make that staged idea wrong).

---

## How to read an entry

- **Hypothesis:** what we believed would happen and why.
- **Assumptions:** the judgment calls underneath (stated, not hidden).
- **Projected:** the movement we expected, with the source (simulated,
  modeled, or judgment).
- **Observed:** what actually happened. "No traffic read yet" is an honest
  and complete answer.
- **Learning:** what we'd do differently.
- **Status:** won / lost / running / staged / declined / shipped-awaiting-read.

---

## Running right now (live A/B tests)

### Share-message wording test (share_msg_variant)
- **Shipped:** 2026-09-25. **Status:** running.
- **Hypothesis:** the words in the share text change whether the friend
  opens the link and takes the quiz. Four arms: A generic invitation, B
  personal pick, C reciprocal ask ("take the quiz and send me what you
  get" — the control), D pantry challenge dare (fires only when the pantry
  honestly covers the pick, else falls back to C).
- **Assumptions:** arm persists per session; one user stays in one arm;
  a message wins only if recipients *act* (opens → quiz starts →
  completions), not on share taps.
- **Projected:** unknown — this is the read, not a bet. The Sep 23
  simulation suggested share-copy is the highest-leverage surface, but its
  key assumption was the softest in the set.
- **Observed:** no read yet. Needs the reciprocal-copy baseline to settle
  first (~1 week) so attribution isn't muddied.
- **Learning (so far):** none yet.

### Share-origin test: personal cards vs generic shares (?o=card vs ?o=generic) (E29)
- **Shipped:** 2026-09-24. **Status:** running.
- **Hypothesis:** a share sent as a personal card ("Dido, you're the Ice
  Queen") earns more friend quiz-starts than a generic "share this idea"
  send.
- **Assumptions:** origin survives the /c/ redirect; 50 opened share links
  is enough to call it.
- **Projected / decision rule:** at 50 opened links, if card-origin earns
  >= 2x the friend-quiz-starts of generic, personal cards become the only
  share path on cast ideas.
- **Observed:** zero valid organic opened shares so far — the
  recipient_landing_viewed event was polluted by on-site ?idea= navigation
  (flagged 2026-09-25; fix is open work, see backlog). No read possible
  until attribution is fixed.
- **Learning:** instrument first, decide later. A test with broken
  attribution is worse than no test.

### Browse thumbnails: photo vs cutout (pmc_thumb_arm)
- **Shipped:** 2026-09-25. **Status:** running.
- **Hypothesis:** one presentation of browse card art earns more
  detail-opens and saves. Arm persists per session; detail heroes and share
  images are unaffected.
- **Assumptions:** 50/50 random per session is fair; browse detail opens +
  browse-origin saves are the metric.
- **Projected:** unknown — pure read.
- **Observed:** no read yet.

---

## Shipped — verified live, awaiting a traffic read

These are bets placed with green gates and live verification, but no
stranger traffic to judge them yet. They are NOT wins.

### Homepage proof strip ("Real ideas you might get")
- **Shipped:** 2026-09-25 (commit 6b051ac). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** showing real top-save costumes with photos above the
  fold lets visitors see the taste before starting the quiz, lifting quiz
  starts. Slim swipe rail; the hero CTA stays dominant.
- **Assumptions:** the top saves (Snow Sisters, Lost Tourist, Mermaid
  Crew, Blue Dog Family) represent the site's best taste; proof beats
  promises.
- **Projected:** lift in quiz start rate (no number attached — judgment bet).
- **Observed:** tapped twice on day one (Blue Dog Family, Neon Demon
  Hunter) by insider devices. No stranger read.
- **Learning:** none yet.

### Contextual result roles (Zero-Dollar Build, Tonight-Ready, Plot Twist)
- **Shipped:** 2026-09-25. **Status:** shipped-awaiting-read.
- **Hypothesis:** labeled roles (Best Match, Easiest, Wildcard, plus the
  three new ones) contextualize the top 3 better than plain 1/2/3, and each
  role earns trust only if its evidence gate passes — never forced, never
  stacked, neutral numbering when nothing is defensible.
- **Assumptions:** "Zero-Dollar Build" only when the plan genuinely costs
  $0; "Tonight-Ready" only when build time is <= 30 min; "Plot Twist" only
  when the pick comes from outside the picked interest but matches the
  vibe.
- **Projected:** more confident picks; fewer bounces from the results
  screen (judgment, no number).
- **Observed:** no traffic read yet.

### Search intelligence layer (aliases, typo tolerance, attribute filters)
- **Shipped:** 2026-09-25. **Status:** shipped-awaiting-read.
- **Hypothesis:** users type anything — "belle", "spidermn", "cheap funny
  couples" — and the search should understand it: character aliases across
  kids' universes and adult categories, typo tolerance, structured filters
  (price, gender, age, party size) that compose by intersection, popular
  searches weighted by what our own audience actually saves/shares/taps,
  and an honest empty state instead of a dead end.
- **Assumptions:** an alias maps only to genuinely relevant ideas;
  unmapped terms are logged as bank gaps (search_zero_results event), not
  force-matched; on-site behavior (30-day saves/shares/taps) outranks pure
  trend data for "popular right now."
- **Projected:** fewer dead searches; search becomes a discovery surface,
  not just a filter.
- **Observed:** no traffic read yet. The zero-result log is the
  self-improving loop — it will tell us what costumes to build next.
- **Learning:** the work started as a Belle alias patch and Billy widened
  it twice ("think holistically", "not just for kids"). The patch would
  have been the wrong scope.

### Pantry honest-math rework ("5 costumes are 1-2 items away")
- **Shipped:** 2026-09-25 (commit 3cad428). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** the old "0 you can make tonight" headline was a dead end;
  honest math with 6 data-backed default items (scissors, tape, paper+pen,
  foil, cardboard, socks) and a reframe to "N costumes are 1-2 items away"
  gives the page a real value prop without lying.
- **Assumptions:** Billy's instinct ("10 makeable") was tested against
  every defensible default set and refuted — even base 6 + t-shirt + black
  clothes + bedsheet = 0 makeable. The headline celebrates make-tonight
  only when it goes nonzero.
- **Projected:** more pantry engagement; fewer bounces from a zero-state.
- **Observed:** no traffic read yet.
- **Learning:** test the instinct against the data before building the
  instinct's version. The instinct was directionally right (the page was
  dead) and literally wrong (10 was never achievable).

### Pantry visual redesign (tappable item tiles + photos on cards)
- **Shipped:** 2026-09-25 (commit 55a6ff42). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** the free-text "what do you have" box was vague (users
  don't know what to type) and the text-only result cards had no visuals.
  Recognition beats recall: 44 household items as tappable photo tiles in
  4 categories; every result card shows the costume photo with a progress
  bar.
- **Assumptions:** the 44 tiles cover the common stuff; the 11 long-tail
  items stay reachable via type-ahead; the 6 pre-toggled basics keep the
  honest hedging note.
- **Projected:** more items ticked per session; higher pantry-to-plan
  conversion (judgment).
- **Observed:** no traffic read yet.

### "More like this" rail on detail pages
- **Shipped:** 2026-09-25 (commit 151edb0e). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** four related costumes under the make-it steps keep
  browsers moving instead of dead-ending. Same-interest preferred,
  same-vibe fallback when an idea has no interest tag (25 ideas are
  interest-less after the grounding cleanup — an honest state, and the
  fallback covers all of them).
- **Projected:** more detail-page depth per visit (judgment).
- **Observed:** no traffic read yet.

### Share-landing headline honesty fix
- **Shipped:** 2026-09-25 (commit e2106cc). **Status:**
  shipped-awaiting-read (defect fix, not a bet).
- **Hypothesis (bug):** the "Your friend picked X" headline leaked into
  direct homepage-rail, browse, and Pinterest arrivals. Now it renders
  only on genuine share arrivals (?s= present); everything else shows the
  costume title.
- **Observed:** verified live on both arrival types. Defect-class: the win
  is correctness.

### Critic-round accuracy fixes (bar filter, interest grounding, effort honesty)
- **Shipped:** 2026-09-25 (commit a0373319). **Status:**
  shipped-awaiting-read (defect fixes).
- **What:** (1) bar:0 is now an absolute ban (the old falsy check let
  bar-banned ideas leak into bar results); (2) 15 interest tags with no
  grounding in visible copy were stripped; (3) why-lines now describe the
  costume's actual effort, not the user's selected effort. Permanent gates
  added for all three.
- **Observed:** 1,860 bar paths enumerated, zero leaks; 119 ideas x 3
  adversarial effort answers pass the new lint. Correctness wins.
- **Learning:** the metadata was lying about the bank's contents. The
  honest cost: solo dinosaurs went to zero until the new dino batch lands
  — which is exactly what the next bank expansion is for.

### Animated loops on result cards (all 76 ideas)
- **Shipped:** 2026-09-23/24 (commits 794d0a7, 97807b8). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** subtle motion on result cards and share landings
  increases engagement; browse grid stays static for load performance.
- **Assumptions:** 8-12 frames reviewed per video (76/76 pass, zero
  warping/morphing); prefers-reduced-motion respected.
- **Projected:** higher card engagement (judgment).
- **Observed:** no traffic read yet. Billy's tap test is the feel gate.

### Group cast mapping + personal role cards (E17/E24)
- **Shipped:** 2026-09-24 (commit 97807b8; hardened 564137c8).
  **Status:** shipped-awaiting-read.
- **Hypothesis:** for group/family ideas, assigning "who is each person
  going as" — and making per-person shareable cards — turns one share into
  a cast that recruits itself.
- **Assumptions:** Billy's family-of-three tap test is the real gate;
  names stay in JS memory, only explicitly-shared text leaves.
- **Projected:** the Sep 23 simulation's highest-conviction compounding
  lever (+42% second-generation shares for the reply nudge; cast mapping
  modeled +38.6% on group flows, direction robust, magnitude unproven).
- **Observed:** no traffic read yet.

### Browse search, filters, and detail parity (E20/E20b)
- **Shipped:** 2026-09-24 (commit 97807b8; hardened 564137c8).
  **Status:** shipped-awaiting-read.
- **Hypothesis:** at 76+ ideas, browse needs search + filters, and a
  tapped card should open the same full pick/customization flow as quiz
  results (Billy: no dead-end cards).
- **Assumptions:** 3 controls (search + audience + effort) beat a filter
  drawer for this catalog size (competitor recon: drawers serve 10+ facet
  groups).
- **Observed:** no traffic read yet.

### "What's the Halloween plan?" occasion question (E6)
- **Shipped:** 2026-09-23 (commit d4d00fd). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** the dead "store-bought, homemade, or mix?" question
  (0.0% outcome power for family) should be replaced by one occasion
  question for all non-kid flows.
- **Projected:** simulated +2.8% R; structurally, the family flow now asks
  five questions like the site promises.
- **Observed:** gates green (2,052 paths, zero mismatches); no traffic read.

### TV-born ideas escape the TV bucket (E7)
- **Shipped:** 2026-09-23 (commit 5198675). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** Blue Dog Family and friends were invisible to
  Animals-pickers; a reduced-weight secondary animals tag fixes
  findability without dethroning dedicated animals ideas.
- **Projected:** findability 8.3% → 94.8% with #1 relevance intact
  (simulated).
- **Observed:** gates green; no traffic read. One documented cost: Tiny
  Snail no longer surfaces under demand — candidate for a future
  bank-pruning pass.

### Whole result card tappable to pick (E3)
- **Shipped:** 2026-09-23 (commit 76eacf1). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** the copy said "tap one to save your pick" but only the
  small button worked. Make the card do what the copy promises.
- **Projected:** simulated +9.8% R, broad across personas.
- **Observed:** no traffic read. Defect-class at heart.

### Post-share re-offer, "show 3 more," conditional kid-age (E8/E9/E10)
- **Shipped:** 2026-09-23 (commits e3bbff2, df10ace, f98df1d).
  **Status:** shipped-awaiting-read.
- **Hypotheses:** after a share lands, offer "who else needs a costume"
  (E8, simulated +28% R — strongest share-growth lift at the time); the
  "still stuck" dead end leads with ranks 4-6 (E9, +5.8%); the kid-age
  question skips itself on ~30% of paths where it can't change the top 3
  (E10).
- **Observed:** no traffic reads.

### Conditional fit question + dynamic why-lines (E14/E15/E15b)
- **Shipped:** 2026-09-23 (commits 90cb7ae, 0d81fab). **Status:**
  shipped-awaiting-read.
- **Hypotheses:** "which look feels more like you?" fires only when it
  changes results (E14); "why this fits you" opens with the user's real
  answers (E15); the why-line overhaul killed duplicates and Mad-Libs
  templates (E15b, Billy's tap test).
- **Observed:** gates green incl. why-lint; no traffic reads.

### Snow Sisters bank addition (E19)
- **Shipped:** 2026-09-24 (commit 2fa05e8). **Status:**
  shipped-awaiting-read.
- **Hypothesis:** Billy asked "should we add frozen too" — a Frozen-style
  family set earns a healthy demand share without orphaning anything.
- **Projected:** demand sim #4 overall (4.2% #1, 12.3% top-3).
- **Observed:** became a top-save and proof-strip headliner among insider
  devices. No stranger read.

### Link-preview / unfurl fixes (og images)
- **Shipped:** 2026-09-24 (commits 651ab32, a0e855e5). **Status:**
  shipped-awaiting-read (defect fixes).
- **What:** dedicated 1200x630 og images for all ideas + homepage (message
  apps center-crop; the old square art got sliced); iMessage fetch
  fingerprint gets clean og-only HTML (no JS redirect markup).
- **Observed:** 24 live checks pass (4 slugs x 3 UAs x apex/www). The last
  mile needs a real phone: fresh share, new conversation.

### Small defect fixes (Walking Taco crop, browse buttons, "My family" copy, AI-plan copy)
- **Shipped:** 2026-09-23/25. **Status:** done (defect-class).
- **Observed:** verified live; correctness wins.

---

## Staged — waiting on Billy (tap test or word approval)

### One-hero results layout (E12)
- **Staged:** 2026-09-23 (preview /e12-preview). **Status:** staged.
- **Hypothesis:** one big winner ("here is what you got") beats three
  equal cards. Biggest visual change of the Sep 23 batch; Billy explicitly
  asked to tap it before anything ships.
- **Closeout needed:** Billy's tap test → ship, iterate, or kill.

### Share-card image on native share (E13)
- **Staged:** 2026-09-23 (preview /e13-preview). **Status:** staged.
- **Hypothesis:** attaching the costume image to the native share sheet
  lifts opens. Simulated +53.1% R — largest modeled lift in the set, but
  the opens multiplier is the softest assumption; direction robust,
  magnitude unproven.
- **Closeout needed:** Billy's phone tap test (canvas/file behavior varies
  by phone) → ship or kill.

### Interactive browse videos (E25)
- **Staged:** 2026-09-24 (preview /e25-preview). **Status:** staged.
- **Hypothesis:** video-on-tap browse cards lift engagement.
- **Why staged anyway:** Billy flagged "images sometimes don't match the
  animations" (unresolved — his eyes outrank the 4-sample audit); result
  cards already carry motion via the shipped loops; a second motion
  surface works against the declutter mandate.
- **Closeout needed:** Billy says where he saw the mismatch → audit and
  ship the coherent subset, or drop it.

### Complete-the-cast via URL (E27)
- **Staged:** preview /e27-preview (cast state travels in the URL, no
  backend; recipient sees "the cast so far"). **Status:** staged.
- **Closeout needed:** Billy's tap test → ship or fold into the shipped
  cast mapping.

### Kid results lead with copyable build list (E31)
- **Staged:** preview /e31-preview. **Status:** staged.
- **Closeout needed:** Billy's tap test → ship or kill.

### Staged copy needing Billy's exact words (E1/E2/E4/E5)
- **Status:** staged. The Sep 23 simulation's two highest-conviction copy
  bets are still on the shelf: the reply-nudge share header ("send your
  pick back to your friend", +42% second-generation shares modeled) and
  the quiz hook in the share text (+15.7% R modeled, softest assumption).
  Also staged: pre-answering the recipient's first question (needs real
  traffic to check the audience-mismatch cost) and the "take the
  2-minute quiz" CTA. Billy approves exact public copy himself.
- **Closeout needed:** Billy's word approval → ship; real traffic →
  validate or revert.

### Haunted Goalie replacement
- **Staged:** 2026-09-25, three options (Cracked Porcelain Doll, Shadow
  Person, Ventriloquist Dummy). **Status:** staged — Billy's taste call.
- **Closeout needed:** his pick → ship.

---

## Deliberately not shipped

- **Interest question keeps all its options (E11).** Tested 2026-09-23:
  no change justified; findability is solved at the data level (E7's
  cross-tags), not by shrinking the question. Status: closed (no-change).
- **"Pick up to 2 interests" multi-select.** Billy proposed it, then
  killed it himself: "ignore that idea, do a higher ROI question." Do not
  resurface. Status: declined.
- **Mobile filter drawer.** Rejected as over-engineering for 3 controls;
  sticky single-row bar won (competitor recon backed it). Status: closed.

---

## Distribution pushes

### Pinterest: 5 pins published (2026-09-25)
- Baby Dinosaur, Giant Board Game Pieces, Bacon & Eggs, Block Monster,
  Astronaut. Boards created/used per plan.
- **Status:** live. Next: one "make-it" carousel per day on Billy's tap
  (test cadence, ~1/day), starting with the Baby Dinosaur how-to carousel
  (published 2026-09-25).

### Pinterest: make-it carousel batch (staged)
- 5 carousels + pantry hero staged in pinterest-pack/make-it-batch/.
  Process-over-polish line: show how costumes get made from household
  stuff. **Status:** staged for the daily tap.

### Instagram reels
- Snow Sisters v4 reel live 2026-09-25
  (https://www.instagram.com/reel/DdugBI0Dmjw/). Old duplicate deleted.
  **Status:** live. Caption caveat open: "tells you what you can make
  tonight" overstates the pantry's honest zero — Billy's tap if he wants
  it changed.

### Reddit distribution
- **Status:** scheduled, not posted. Push fires 2026-10-15 ~9:30 AM PDT
  for Billy's one-tap fire. Never auto-post.

---

## In flight (not yet decided)

- **Four funny dinosaur costumes** (Extinct Party Animal, Dino Tourist,
  Raptor Barista, Emotional Support Dinosaur) — merging into the bank as
  ranks 120-123, gates then deploy. Fills the solo/funny/dinos thin cell
  the critic exposed.
- **Homepage experiment program** — cold audit + 3 staged variants +
  simulated persona runs; Billy picks the winner. (Spawned 2026-09-25.)

---

## Never got a closeout (backlog — owned)

1. E12, E13, E25, E27, E31 staged previews — Billy's tap tests pending.
2. E1/E2/E4/E5 staged copy — Billy's word approval pending.
3. Share-origin test (E29) — cannot be read until the
   recipient_landing_viewed attribution fix ships (flagged 2026-09-25).
4. Share-message A/B test — close when the read is clean.
5. Browse thumbnail A/B — close when decided.
6. Proof strip, search layer, pantry redesign, contextual roles — close
   with a traffic read or an explicit "judgment call, keeping it" note.

---

## The ongoing process (standing rules)

1. **Pre-launch entry required.** Every new experiment gets a ledger entry
   BEFORE it ships: hypothesis, assumptions, and projected movement are
   mandatory. No entry, no ship. Simulated projections must name their
   model and its softest assumption.
2. **Closeout entry required.** When an experiment is decided (won, lost,
   killed, or kept on judgment), the entry gets its observed-vs-projected
   closeout within 48 hours. "No traffic read yet" is a valid closeout
   state for defect fixes; it is not valid for bets that claimed a lift.
3. **Attribution before decision.** No experiment is decided on broken
   instrumentation. If the metric can't be trusted, the experiment stays
   open and the instrumentation fix becomes the work.
4. **Holistic review trigger.** Every 10th closed experiment — or monthly,
   whichever comes first — a review runs over this ledger and explicitly
   asks: *which of our standing assumptions did this batch challenge?*
   The "Holistic read" section at the top is rewritten from the answer.
   Assumptions that fail twice get a dedicated experiment to kill or
   confirm them.
5. **Plain-English names.** Entries lead with what a human would call the
   thing. Codes live in parentheses. Billy: "I don't know what e12,13 etc
   are lol."
6. **Bets vs fixes.** Defect fixes (correctness) close on verification.
   Bets (lifts) close on data or on an explicit judgment call — never on
   "it shipped."
