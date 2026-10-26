#!/usr/bin/env python3
"""build_play.py -- generate play.html from the re-exported live source.

HISTORY
  Originally (pre-2026-09-28) this generator ported the
  peekaboo-costume-game artifact export
  (~/workspace/your_files/peekaboo-costume-game/peekaboo-costume-game.html)
  into play.html through a chain of regex transformations. After that,
  play.html gained many post-generation features as DIRECT edits to the
  generated file (playtest fixes, the Peekaboo hider rebuild, the Chopped
  third game, the in-game switcher, deep links, share instrumentation).
  The old artifact pipeline never learned them, so its output drifted
  further from live with every direct edit (653 diff lines by
  2026-10-22). The FEATURE_GUARD added 2026-09-28 correctly refused
  every regen from the stale pipeline (proven in the 2026-09-28 drift
  audit and again in the 2026-10-22 parity audit, fix list #8).

REPAIR (2026-10-22, parity fix list #8)
  Re-export, as both audits recommended: the generator source is now
  play-source.html in this directory -- a byte-for-byte snapshot of the
  current live play.html (SHA-256 recorded in the repair report,
  hour-session/build-play-repair-2026-10-22.md). This generator reads
  that source, runs the feature guard and the banned-content checks
  below, and only then writes it to ../play.html verbatim. Future edits
  to the game are made to play-source.html (and the guard updated in
  the same change), never again only to the generated play.html.
  The old artifact export in your_files/ is now a historical reference
  only; nothing in this generator reads it.

FEATURE GUARD (kept, not weakened)
  The guard still refuses to write anything if a guarded feature is
  missing from the source; on refusal the tree file is NOT touched.
  One marker was corrected, none were dropped: the original marker
  "Cartoon friendly ghost costume" named an artifact aria-label that
  the 2026-09-28 Peekaboo rebuild deliberately replaced with
  "A hidden costume" on all six costume SVGs, because the old labels
  named the answer (a screen-reader giveaway; see
  hour-session/peekaboo-rebuild-edit.py). A correct regen of the live
  page can never contain the old string, so the guard now checks the
  live successor string instead, at the same strength (same marker
  count for the original set). Five markers were ADDED for features
  live gained after the guard was written (Chopped, switcher, deep
  links, share button), so the guard is strictly stronger than before.

Usage: python3 build_play.py   (writes ../play.html)
       PMC_PLAY_OUT=<path> python3 build_play.py   (scratch output)
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.join(HERE, "play-source.html")
OUT = os.environ.get("PMC_PLAY_OUT") or os.path.join(REPO, "play.html")

src = open(SRC, encoding="utf-8").read()

# Guard: post-generation features that live ONLY in play.html (made as
# direct edits after a regen). If the source ever loses one, fail loudly
# BEFORE writing, so a bad regen can never touch the tree's play.html.
FEATURE_GUARD = [
    "share_created",                 # Share-my-score analytics (f5963501)
    "play_shared_opened",            # ?s=<sid> recipient branch
    "tapGuard",                      # finger-bounce guard on multi-step flows
    "withProbe",                     # ?probe= passthrough on guide links
    "finishQuiz",                    # finish-screen quiz CTA (distribution)
    "Or find your costume",          # intro loop-back quiz CTA (2026-10-13 audit)
    "how-to guide coming soon",      # tooltip on guide-less chips
    "See how to make the",           # named guide links per costume
    "A hidden costume",              # neutral SVG aria-labels (2026-09-28 Peekaboo
                                     # rebuild; supersedes the artifact's
                                     # "Cartoon <name> costume" answer-giveaway
                                     # labels -- see docstring above)
    "og/play.jpg",                   # OG card meta
    # Added 2026-10-22: features live gained after the guard was written.
    "startChopped",                  # Chopped (third game) entry point
    "choppedIdeas",                  # Chopped bank-derived idea set
    "gswitch",                       # in-game game switcher
    "gameFromQuery",                 # ?game= deep links
    "shareScore",                    # Share-my-score button (finish screen)
]
missing = [m for m in FEATURE_GUARD if m not in src]
if missing:
    raise SystemExit(
        "REFUSING REGEN: generated play.html would be missing post-generation "
        f"features: {missing}. The generator source (play-source.html) is "
        "stale or was edited without porting the feature; the tree file was "
        "NOT touched. Port the listed features into play-source.html first, "
        "then re-run."
    )

# Banned content: a source carrying any of these is not the live page.
BANNED = [
    "Made by Billy",                 # footer credit is "Built with Muse." only;
                                     # live carries no footer element at all
                                     # (removed 2026-10-01) -- this string must
                                     # never reappear
    "data:image/png;base64",         # costume images are external .webp files
    '<script type="text/plain"',     # dead previous-version block (dropped 2026-09)
    "+ drying",                      # displayed times are hands-on only
]
banned = [b for b in BANNED if b in src]
if banned:
    raise SystemExit(
        f"REFUSING REGEN: source contains banned content: {banned}. "
        "The tree file was NOT touched."
    )

with open(OUT, "w", encoding="utf-8") as f:
    f.write(src)
print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB)")
print(f"feature guard OK: all {len(FEATURE_GUARD)} post-generation features present")
