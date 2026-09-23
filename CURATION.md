# Pick My Costume — Curation Rules

Rules for adding ideas to the bank. Every new idea must pass all five before it goes in.

## 1. Instantly readable from title + thumbnail
A cold visitor must get the costume from the title and the illustration alone, no blurb needed. Test: show the title to someone who knows nothing about the idea. If they ask "what is that?" — rewrite the title or kill the idea. This is why "Moth & Porch Light" beat "Cloud With a Silver Lining."

## 2. Light how-to in the blurb
Every blurb is one line that says how to make or buy it. Not a joke, not a vibe — an instruction. ("Silver clothes with taped-on foil squares.") If you can't write the blurb in one concrete line, the idea isn't clear enough yet.

## 3. No dead entries
Every idea needs: title, blurb, why-line, audience, budget, tags, and a matching illustration in images/. Never ship an idea without its image.

## 4. No stale counts
Never hardcode the idea count anywhere ("Browse all 40"). All labels derive from the data (IDEAS.length). Lesson from the 40→41→51 expansion.

## 5. No volatile prices in the bank
Product prices change; the bank is permanent. Costume instructions outlive prices. If an idea depends on a specific product, check the price live before shipping that batch, but keep the number out of the idea's permanent copy.

## Quality bar from the AI sweeps (Sep 2026)
- Prefer ideas that survive scoring across multiple quiz paths (no one-trick tags).
- Group/couple ideas need distinct roles for each person — everyone gets their own job, not just matching outfits.
- Kid ideas favor warm layers, uncovered faces, no long hems.
- When two ideas are similar, keep the one with the clearer title and drop the other.
## Share pages
- `/c/<slug>` is a Cloudflare Pages Function (`functions/c/[slug].js`) with per-idea og:/twitter: meta tags, so messengers unfurl the shared costume's own illustration. Humans are redirected to `/?idea=<slug>`, which shows a "Your friend is going as ..." landing with a quiz CTA.
- Regenerate with `python3 gen_share_function.py` (reads the IDEAS bank in index.html) whenever ideas are added, removed, or renamed, and deploy the function file with the change.
- The share text links to `pickmycostume.com/c/<slug>` (no trailing slash).
