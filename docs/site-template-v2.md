# Site Template v2 — "A 3rd grader gets it in 5 seconds"

**Version:** 2.0 · **Effective:** Oct 22, 2026 · **Owner:** Template Owner (standing agent A)
**Canonical copy:** this file, `~/workspace/playbooks/site-template-v2.md`.
**Repo copy:** `docs/site-template-v2.md` in `wdlcmu/pick-my-costume` (versioned in GitHub; changelog below).
**Supersedes:** the copy standard in `pick-engine-submission-template.md` (Oct 22, 2026) and all v1 page habits. Template v2 is a SITE template — broader than copy: words, budgets, one-job layout, and proof of done.

Applies to every live portfolio site: Pick My Costume, Clearline Family, The Present Picker, ThawDay, Pick My Resolution, Fill My Bracket, Dadiosity. A page that breaks this spec is not done, no matter how it looks.

---

## 1. WORDS

- **Reading level: Flesch-Kincaid grade 3 or lower. Measured, not eyeballed.** Run the scorer in §6 on the page's visible text. A number, not a feeling. Grade claims in any report must come from the scorer.
- **Sentences: 10 words or fewer.** Short words. Plain words.
- **No jargon.** A term the product cannot avoid (a "must-use" term) is explained once, in plain words, the first time it appears — then used freely.
- **Steps = one short action each.** "1. Put on sweatshirt. 2. Paint face." One action per step, nothing else in the step.
- **Items = just the name.** "sweatshirt, felt" — no role explanations, no "used for" clauses.
- **Say it once.** Never restate the same fact in a second box. If two blocks say the same thing, delete one.
- **No duplicated blocks.** Identical content for two people/roles renders ONCE, not once per person.
- **Hidden costs stay hidden.** Show hands-on time only. Anything the math counts but the user does not do with their hands (e.g. drying time) is never displayed. Sizes are shown only where there is real, specific sizing advice for that item.
- **Every word earns its place.** If a word does not change what the user does, cut it. No filler, no hedging prose.
- **Legal/compliance line: exempt from the grade check, but it stays ONE short line.**

## 2. BUDGETS (counted, not estimated)

| Element | Budget |
|---|---|
| Hero headline | ≤ 6 words |
| Hero subline | ≤ 12 words |
| Hero buttons | exactly 1 |
| Any other section | ≤ 25 words |
| Whole page | ≤ 300 words total |

- Word counts are produced by the counter in §6 and reported with every page change.
- **Prefer a picture, an icon, or a 3-step strip over a sentence.** If a visual can carry it, the sentence goes.
- The budget only goes DOWN over time, unless data shows a loss (Template Owner rule, §7).

## 3. ONE JOB

- **One page = one job.** One big button = the quiz (the moat). Nothing competes with it: no second CTA of equal weight, no competing starts.
- **Every graphic answers "what does this show?"** If it doesn't answer, it's cut.
- **No empty white gaps.** Dead space is a defect, not a style.
- Footer credit on every site, exactly: **Built with Muse.**

## 4. PROOF OF DONE (Billy, Part 2 — applies to everything)

"Done" requires ALL of:

1. **Live URL** — the page as served in production, not a local file or preview.
2. **Live screenshot** — captured from the live URL after deploy.
3. **GitHub commit link** — the commit that put it there.
4. **PostHog event firing from the new version** — a real event from the deployed build, seen in PostHog.
5. **FK grade + word counts** for any page change, from the §6 tools.

**No evidence = "in progress."** Never grade your own work with words ("done, verified, looks good"); grade it with the evidence above.

- After every deploy: check the live page. **Revert on any error.**
- If a problem can be fixed with Cloudflare, GitHub, or PostHog, fix it in the same run. Never report a fixable problem as "next run" or "tomorrow's run."
- Before repeating or relying on any "unconfigured / dormant / not set up" claim about a production endpoint, probe the live behavior first.

## 5. HOW A PAGE GETS BUILT TO THIS SPEC

1. Write the page's ONE job in one sentence before writing any copy.
2. Draft the hero first: headline ≤6 words, subline ≤12, one button (the quiz).
3. Fill sections under 25 words each; swap sentences for pictures/icons/3-step strips wherever a visual carries the meaning.
4. Run the §6 checklist. Fix every failure before deploy — grade, budgets, CTA count.
5. Deploy, then produce the §4 evidence pack. Report the numbers, not adjectives.

## 6. COMPLIANCE CHECKLIST (a builder runs this, in order)

- [ ] **Word count** — strip the page's visible text and count. Hero headline ≤6, subline ≤12, each section ≤25, page ≤300.
- [ ] **FK grade** — score the visible text; must be ≤ 3.0 (legal/compliance line excluded).
- [ ] **Sentence length** — no sentence over 10 words (legal line exempt).
- [ ] **CTA count** — exactly 1 primary button in the hero; it starts the quiz. No competing start anywhere on the page.
- [ ] **Graphic test** — for each graphic, write what it shows in 3 words or fewer. No answer = cut it.
- [ ] **Footer** — reads exactly "Built with Muse."
- [ ] **Live screenshot** — from the production URL, post-deploy, 390px wide (phone) + desktop.
- [ ] **PostHog check** — the page's key event (e.g. quiz start) fires from the new version.
- [ ] **Evidence pack filed** — live URL + screenshot + commit link + PostHog event + FK grade + word counts, all in the ship note.

Reference scorer/counter (Python, no dependencies):

```python
import re, sys

def syllables(word):
    word = word.lower()
    groups = re.findall(r'[aeiouy]+', word)
    n = len(groups)
    if word.endswith('e') and n > 1: n -= 1
    return max(n, 1)

def check(text):
    words = re.findall(r"[A-Za-z']+", text)
    sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]
    ns = max(len(sentences), 1)
    nw = len(words)
    sy = sum(syllables(w) for w in words)
    fk = 0.39 * (nw / ns) + 11.8 * (sy / max(nw, 1)) - 15.59
    longest = max((len(re.findall(r"[A-Za-z']+", s)) for s in sentences), default=0)
    print(f"words={nw} sentences={ns} fk_grade={fk:.1f} longest_sentence={longest} words")
    assert fk <= 3.0, "FAIL: grade above 3"
    assert longest <= 10, "FAIL: sentence over 10 words"
    assert nw <= 300, "FAIL: page over 300 words"

check(open(sys.argv[1]).read())  # pass a file of the page's visible text
```

## 7. VERSIONING + ROLLOUT

- This spec is versioned. Every change bumps the version and adds a changelog line below, committed to GitHub with the doc.
- The Template Owner rolls each new version out to every live site **within 48 hours** of the version landing.
- Fail states: any live site more than 1 version behind; any live page over budget or over grade 3.
- Word budgets only go down unless PostHog data shows a loss from the cut.

## Changelog

- **v2.0 — Oct 22, 2026.** First versioned release. Billy's operating instructions (Oct 22) Part 3 + Part 2: FK grade ≤3 measured, sentence cap 10 words, counted budgets (hero 6/12/1, section ≤25, page ≤300), one-job rule, proof-of-done evidence pack, footer credit "Built with Muse.", runnable compliance checklist. Absorbs the Oct 22 copy standard from the pick-engine submission template (one action per step, items are names, say it once, no duplicated blocks, hidden costs hidden).
