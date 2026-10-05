#!/usr/bin/env python3
"""Regenerate functions/c/[slug].js from the IDEAS bank in index.html.

The Pages Function serves /c/<slug> share pages: each unfurls the shared
costume's own illustration via og:/twitter: meta tags and serves the full
build guide as static HTML (h1, materials, steps) so fetchers and AI
assistants can read and quote it. A prominent CTA deep-links humans into
the app idea page, preserving share params. Re-run after adding, removing,
or renaming ideas.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

# One-line flag for the recipient banner experiment (Experiment 3 recipient
# ship). True = /c/ pages show the warm recipient banner to visitors arriving
# through a share link (?s= present). False = the current no-banner control
# page. Flips RECIPIENT_BANNER in the generated JS (also a one-line flip
# directly in functions/c/[slug].js). Code only, no deploy: house taste
# call in the morning.
RECIPIENT_BANNER = True

# One-line flag for the "I made it" proof-photo section (novel-find
# 2026-09-26i, MakerWorld steal). True = /c/ guides render a "Wore this?
# Show us" block inviting builders to share a costume photo; the CTA deep
# link carries ?madeit=1 so a later stream can wire a submission flow.
# False = today's control (no block). Code only, no deploy: house taste
# call in the morning.
IMADEIT = False

src = open(os.path.join(ROOT, "app.js"), encoding="utf-8").read()  # bank + INSTRUCTIONS moved to app.js (2026-10-01)

def _extract_json(src, marker):
    i = src.index(marker); j = src.index('{', i)
    depth, in_str, esc = 0, False, False
    for k in range(j, len(src)):
        c = src[k]
        if in_str:
            if esc: esc = False
            elif c == '\\': esc = True
            elif c == '"': in_str = False
        else:
            if c == '"': in_str = True
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    raw = re.sub(r'/\*.*?\*/', '', src[j:k+1], flags=re.S)
                    return json.loads(raw)
    raise ValueError('unterminated JSON after ' + marker)

# 2026-10-05 (Billy): the visual supply cards are the single materials
# presentation on /c/ guides. The tile model is ported from app.js (same
# PANTRY_MATS / LABELS / EMOJI the app badge uses) so /c/ cards and app
# cards can never drift.
_PANTRY_MATS = _extract_json(src, 'var PANTRY_MATS =')
_PANTRY_LABELS = _extract_json(src, 'var PANTRY_LABELS =')
_PANTRY_EMOJI = _extract_json(src, 'var PANTRY_EMOJI =')
_PANTRY_STAPLES = _PANTRY_MATS['staples']
_OPTIONAL_PAREN_RE = re.compile(r'\([^)]*optional', re.I)
ideas = re.findall(r'\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)"', src)
assert ideas, "no ideas parsed from index.html"
data = {slug: {"t": title, "b": blurb} for slug, title, blurb in ideas}
# Split-the-build (2026-09-26): the 51 group/family ideas get a "Split the
# build" materials divider on their /c/ guides. Audience is parsed per idea
# here; the generator asserts the parse covers every idea so a bank edit can
# never silently drop an idea from (or into) the splittable set.
_auds = dict(re.findall(r'\{id:"([^"]+)"[^}]*?audience:\[([^\]]*)\]', src))
assert len(_auds) == len(data), \
    "audience parse mismatch: %d auds vs %d ideas" % (len(_auds), len(data))
SPLIT_SLUGS = sorted(
    [s for s in data if "group" in _auds.get(s, "") or "family" in _auds.get(s, "")])
assert SPLIT_SLUGS, "no splittable ideas found"
# Partner Split (2026-09-27): halves for every couple-audience idea, derived
# by gen_split.py (single source of truth, shared with split.html). The
# generator asserts full coverage so a bank edit can never silently leave a
# couple idea half-less, and the set must match this file's audience parse.
from gen_split import load_halves as _load_halves
HALVES = _load_halves()
assert set(HALVES) == {s for s in data if "couple" in _auds.get(s, "")}, \
    "halves/couple-audience mismatch: %s" % (set(HALVES) ^ {s for s in data if "couple" in _auds.get(s, "")})
for slug in data:
    assert os.path.exists(os.path.join(ROOT, "images", "og", slug + ".jpg")), \
        "missing share image: images/og/" + slug + ".jpg (this is what onRequest serves as og:image)"

# Old slugs renamed in the Sep 2026 IP sweep. Every alias must resolve to a
# slug present in the current bank; the generator asserts this below.
ALIASES = {
    "bluey-family": "blue-dog-family",
    "incredibles-family": "superhero-family",
    "stitch-ohana": "blue-alien-ohana",
    "wednesday-enid": "gloom-bloom",
    "iron-man": "tin-hero",
    "elphaba-glinda": "good-witch-bad-witch",
    "minecraft-crew": "block-game-crew",
    "spider-verse": "web-slinger-crew",
    "spider-man-mj": "web-hero-duo",
    "peppa-pig": "little-pig-family",
    "jurassic-rangers": "dino-rangers",
    "creeper": "block-monster",
    "among-us": "space-crewmate",
    "little-mermaid-crew": "mermaid-crew",
    "bumblebee": "bumble-bee",
    "jim-pam": "office-couple",
    "bob-linda": "burger-joint-couple",
    "be-our-guest": "enchanted-castle-crew",
    "disney-princesses": "fairy-tale-princesses",
    "wheres-waldo": "crowd-camouflage",
}
for old, new in ALIASES.items():
    assert new in data, "alias target missing from bank: " + new
    assert old not in data, "alias source still in bank: " + old

# Friendly 404 page served (with a real 404 status) for unknown /c/<slug>
# requests. Single source of truth: the site's /404.html, embedded into the
# generated function at build time. Fail loudly if it goes missing so a
# regeneration can never silently ship a bare "Not found".
NOTFOUND_SRC = open(os.path.join(ROOT, "404.html"), encoding="utf-8").read()
assert "That page is still in the box" in NOTFOUND_SRC, \
    "404.html marker text changed: update the friendly-404 assert"

# Materials, numbered steps, decision triple (time/effort), and FAQs per
# idea, for schema.org HowTo JSON-LD on the /c/ pages and the static guide
# body (triple + FAQs are visible content; only m/s feed the JSON-LD).
# Parsed with brace matching because the object has a trailing comma that
# strict JSON rejects.
def _parse_instructions(src):
    marker = "var INSTRUCTIONS ="
    i = src.index("{", src.index(marker) + len(marker))
    depth, in_str, esc = 0, False, False
    for j in range(i, len(src)):
        ch = src[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    seg = re.sub(r",\s*([}\]])", r"\1", src[i:j + 1])
                    return json.loads(seg)
    raise ValueError("INSTRUCTIONS object not balanced")

_instructions = _parse_instructions(src)
_missing_ins = [s for s in data if s not in _instructions]
assert not _missing_ins, "ideas missing instructions: %s" % _missing_ins

# SEO meta descriptions (fix list P2-11, 2026-09-30): the /c/ meta description
# template must land 120-155 chars for every idea. This mirrors the _desc JS
# built in the function template below (same article rule, same >155 trim,
# same esc() entity expansion on the title); fail loudly so a bank edit can
# never silently ship a thin or search-truncated description again.
def _esc_len(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
def _meta_desc(title, hw):
    t = _esc_len(title)
    art = "" if t.lower().startswith("the ") else ("an " if t[0].lower() in "aeiou" else "a ")
    # Meta descriptions use hands-on time only (drying estimates would push
    # over the 155-char limit); the full time incl. drying is on the page.
    ht = re.sub(r'\s*\+.*$', '', _esc_len(hw["time"]))
    d = ("How to make %s%s costume in %s. %s DIY project "
         "with a full supplies list, step-by-step guide, and sizing tips."
         % (art, t, ht, _esc_len(hw["effort"])))
    if len(d) > 155:
        d = d.replace("a full supplies list", "a supplies list")
    return d
_bad_desc = [(s, len(_meta_desc(data[s]["t"], _instructions[s]))) for s in data
             if not 110 <= len(_meta_desc(data[s]["t"], _instructions[s])) <= 155]
assert not _bad_desc, "meta description outside 120-155 chars: %s" % (_bad_desc[:10],)
# Sourced-facts layer (AI-citation checklist item #10, audited 2026-09-26):
# one audited external citation per guide, on safety-relevant steps only.
# The mapping lives in hour-session/safety-links.json and is audited by
# hand: every URL was fetched and its page verified to support the claim
# before embedding (see hour-session/sourced-facts-2026-09-26.md). Never
# fabricate or pad links; fewer honest links beats coverage.
# One link per idea max, attached to the first Safety step whose claim the
# linked page directly supports. Topics are matched in match_order
# (choking first: the most severe claim wins).
_safety = json.load(open(os.path.join(ROOT, "hour-session", "safety-links.json"),
                         encoding="utf-8"))

# Role share cards (2026-09-27, MagicShot.ai novel-scout steal): family
# cast shares mint one unfurl link per family member role. ROLE_CARDS maps
# idea slug -> {role-slug: role display label}, parsed from CASTS in
# index.html; the generated function allowlist-validates ?role= against it.
from gen_role_cards import parse_casts, role_slug, role_display
_casts = parse_casts(src)
ROLE_CARDS = {slug: {role_slug(r): role_display(r) for r in roles}
              for slug, roles in sorted(_casts.items())}
assert ROLE_CARDS, "no role cards parsed from CASTS"
# Fail loudly on any missing role card (og-regen lesson: every card the
# function can serve must exist on disk before it can be referenced).
for _slug, _rmap in ROLE_CARDS.items():
    for _rs in _rmap:
        _p = os.path.join(ROOT, "images", "og", "%s--%s.jpg" % (_slug, _rs))
        assert os.path.exists(_p), "missing role share card: " + _p + \
            " (run gen_role_cards.py)"
_topics = sorted(_safety["topics"], key=lambda t: t["match_order"])
# Word-boundary keyword matching (2026-09-28): the old naive substring test
# (`k in low`) false-positived on partial words, e.g. "trip" inside
# "stripes" and "hem" inside "them", attaching the CPSC citation to Safety
# steps the linked page does not support. Each keyword now compiles to
# \b<keyword>s?\b: the leading boundary kills interior/suffix hits, while
# the optional plural "s" keeps legitimate matches ("eye hole" in
# "eye holes", "trip" in "trips", "headband" in "headbands").
_topic_res = [(t, [re.compile(r"\b" + re.escape(k) + r"s?\b")
                   for k in t["keywords"]])
              for t in _topics]
def _safety_link_for(steps):
    for i, st in enumerate(steps):
        low = st.lower()
        if not low.startswith("safety:"):
            continue
        for t, res in _topic_res:
            if any(r.search(low) for r in res):
                return {"step_idx": i, "url": t["url"], "label": t["label"]}
    return None

howto = {s: {"m": _instructions[s]["m"], "s": _instructions[s]["s"],
             "time": _instructions[s].get("time", ""),
             "cost": _instructions[s].get("cost", ""),
             "effort": _instructions[s].get("effort", ""),
             "faqs": _instructions[s].get("faqs", []),
             "sizing": _instructions[s].get("sizing", ""),
             "safelink": _safety_link_for(_instructions[s]["s"])}
        for s in data}

# 2026-10-05: the /c/ supply cards align tile indices 1:1 with pantry mats,
# exactly like app.js pantryMaterialTexts. Fail fast if any idea drifts.
for _s in data:
    _pm = _PANTRY_MATS['mats'].get(_s) or []
    _tx = [t for t in _instructions[_s]["m"] if not _OPTIONAL_PAREN_RE.search(t)]
    assert _pm, 'no pantry mats for ' + _s
    assert len(_pm) == len(_tx), \
        'pantry/text misalignment for %s: %d mats vs %d texts' % (_s, len(_pm), len(_tx))
print('pantry/text alignment ok for %d ideas' % len(data))

# Related-costume internal links (SEO, 2026-09-27): every /c/ guide renders a
# "More costumes like this" block of plain static <a href="/c/..."> anchors
# (crawler-visible, same for every visitor: not cloaking). Relatedness =
# shared bank tag keys weighted by tag rarity (IDF: distinctive tags like
# princess/dinos outrank generic cute/occparty) + 1.5 per shared audience.
# Deterministic tiebreak by slug so regeneration is stable.
import math as _math
from collections import Counter as _Counter
_tagmap = {}
for _m in re.finditer(r'\{id:"([^"]+)"[^}]*?tags:\{([^}]*)\}', src):
    _slug, _tbody = _m.group(1), _m.group(2)
    if _slug not in data:
        continue
    _tagmap[_slug] = {k: int(v) for k, v in re.findall(r'(\w+):(\d+)', _tbody)}
_audmap = {s: [a.strip().strip('"') for a in _auds.get(s, "").split(",") if a.strip()]
           for s in data}
_dfc = _Counter()
for _s in data:
    for _k in _tagmap.get(_s, {}):
        _dfc[_k] += 1
_idf = {k: _math.log(len(data) / c) for k, c in _dfc.items()}
RELATED = {}
for s in data:
    _st, _sa = _tagmap.get(s, {}), set(_audmap.get(s, []))
    _scored = []
    for o in data:
        if o == s:
            continue
        _ot, _oa = _tagmap.get(o, {}), set(_audmap.get(o, []))
        _score = sum(min(_st.get(k, 0), _ot.get(k, 0)) * _idf[k]
                     for k in set(_st) & set(_ot))
        _score += 1.5 * len(_sa & _oa)
        _scored.append((_score, o))
    _scored.sort(key=lambda t: (-t[0], t[1]))
    RELATED[s] = [o for _, o in _scored[:5]]
assert set(RELATED) == set(data), "related map missing slugs"
assert all(len(v) == 5 and all(t in data for t in v) for v in RELATED.values()), \
    "related map must hold 5 valid slugs per idea"

# Primary-material classification (SEO 2026-10-01, Claude 4c): every idea gets
# a primary material for (a) the SEO title pattern "DIY <T> Costume: <N>-Min
# <Material> Build (Step-by-Step)", (b) the descriptive og/img alt text, and
# (c) the "More <material> builds" related block. Category-priority scan over
# the full materials list (cardboard before felt before paper ...): the most
# craft-distinctive material defines the build, not the first-listed garment.
# OVERRIDES are hand-verified misfires where the priority order picks an
# accent (optional face paint, tiny tulle eye squares) over the signature
# piece. Any bank edit that leaves an idea unclassified fails loudly.
_MAT_CATS = [
    # 2026-10-02: "cereal boxes" (plural) never matched "cereal box"+s?,
    # so cereal-crew classified as fabric. Box plurals are real bank words.
    ("cardboard", ["cardboard", "cardstock", "shoe box", "cereal box",
                   "cereal boxes", "pizza box", "moving box"]),
    ("felt", ["felt"]),
    ("paper", ["paper", "crepe", "tissue", "newspaper", "poster board"]),
    ("balloons", ["balloon"]),
    ("tulle", ["tulle"]),
    ("foam", ["foam"]),
    ("foil", ["foil", "aluminum"]),
    ("plastic", ["plastic"]),
    ("paint", ["paint"]),
    ("makeup", ["makeup", "eyeliner", "lipstick", "face crayon", "mascara"]),
    ("trash bags", ["trash bag", "garbage bag"]),
    ("wigs", ["wig", "hair spray", "hairspray"]),
    ("hats", ["hat", "headband", "cap", "crown", "beanie", "tiara", "helmet"]),
    ("fabric", ["shirt", "pants", "hoodie", "sweatshirt", "dress", "pillowcase",
                "t-shirt", "tshirt", "tee", "jacket", "jeans", "skirt",
                "onesie", "pajama", "scarf", "socks", "tights", "leggings",
                "shorts", "robe", "towel", "blanket", "sheet", "fabric",
                "apron", "vest", "cape", "cloth", "sweatpants", "tank top",
                "blouse", "cardigan", "sweater", "underwear"]),
    ("wood", ["dowel", "wooden", "stick"]),
    ("yarn", ["yarn", "twine"]),
    ("tape", ["duct tape", "masking tape", "packing tape"]),
]
_MAT_OVERRIDES = {
    # accent (optional face paint / tiny eye squares) beat the signature piece
    "classic-ghost": "fabric",   # the white sheet IS the costume
    "galaxy-knights": "fabric",  # optional face-paint hood shadow, not the build
    "wizard": "hats",            # pointy hat is the signature
    "ninja": "hats",             # headband + beanie, paint is optional
    "little-witch": "hats",      # pointy hat is the signature
    "beekeeper-bee": "hats",     # wide-brim veil hat is the signature
    "scarecrow": "hats",         # old hat is the signature
    "chill-painter": "wigs",     # the afro wig is the signature
}
_mat_res = [(c, [re.compile(r"\b" + re.escape(k) + r"s?\b") for k in ks])
            for c, ks in _MAT_CATS]
# Title-case noun per category for the SEO title ("Hat Build", not "Hats Build").
_MAT_TITLE_NOUN = {"cardboard": "Cardboard", "felt": "Felt", "paper": "Paper",
                   "balloons": "Balloon", "tulle": "Tulle", "foam": "Foam",
                   "foil": "Foil", "plastic": "Plastic", "paint": "Paint",
                   "makeup": "Makeup", "trash bags": "Trash Bag",
                   "wigs": "Wig", "hats": "Hat", "fabric": "Fabric",
                   "wood": "Wood", "yarn": "Yarn", "tape": "Tape"}


def _primary_material(slug, mats):
    if slug in _MAT_OVERRIDES:
        return _MAT_OVERRIDES[slug]
    for c, res_ in _mat_res:
        for m in mats:
            if any(r.search(m.lower()) for r in res_):
                return c
    return None


PRIMARYMAT = {s: _primary_material(s, howto[s]["m"]) for s in data}
_unmat = [s for s, c in PRIMARYMAT.items() if c is None]
assert not _unmat, "ideas with no primary material: %s" % _unmat
assert all(_MAT_OVERRIDES.get(s, c) == c
           for s, c in PRIMARYMAT.items()), "override drift"

# "The Tin Hero" -> "Tin Hero" for sentence/SEO-title use, so we never emit
# "The The Tin Hero" or "DIY The Tin Hero Costume".
def _bare_title(slug):
    t = data[slug]["t"]
    return t[4:] if t.lower().startswith("the ") else t


# SEO titles (Claude 4c, shortened 2026-10-01 Lane 4): "DIY Pizza Slice
# Costume: 45-Min Cardboard Build" -- build time + primary material from the
# bank, the same fields the plan page uses. Dropped " (Step-by-Step)" (15 chars)
# to keep all titles <=60 chars. No costs/dollar figures anywhere.
# Per-slug overrides for the two names still >60 chars after the drop.
_TITLE_OVERRIDES = {
    "kpop-demon-huntresses": "DIY Pop Star Demon Huntresses: 40-Min Cardboard Build",
    "pumpkin-king-bride": "DIY Pumpkin Groom & Patchwork Bride: 45-Min Cardboard Build",
}
def _seo_title(slug):
    t = _bare_title(slug)
    m = re.match(r"^\s*(\d+)\s*min", howto[slug]["time"] or "")
    assert m, "time not minute-based for " + slug
    if slug in _TITLE_OVERRIDES:
        return _TITLE_OVERRIDES[slug]
    if slug in _EASY_TITLE_SLUGS or _is_clothing_based(slug, howto[slug]["m"]):
        return "DIY %s Costume: Easy %s-Min Build" % (
            t, m.group(1))
    return "DIY %s Costume: %s-Min %s Build" % (
        t, m.group(1), _MAT_TITLE_NOUN[PRIMARYMAT[slug]])


# Material-claim audit (Item 4, 2026-10-01): the <Material> in the title must
# be the main BUILD material (what the hands-on work actually builds from).
# The slugs below named a purchased prop / worn accessory / minor accent
# instead (plastic fangs & whistles, one wig among props, a store-bought hat,
# accent face paint), so their titles drop the material claim and read
# "DIY <Name> Costume: Easy <N>-Min Build (Step-by-Step)".
# Deliberately NOT moved (judgment calls): chill-painter keeps "Wig Build"
# (the fro IS the costume's identity); beekeeper-bee / bumble-bee / ninja
# keep "Hat Build" (the veil / antennae / headband is the constructed
# centerpiece, not a worn accessory); ballerina keeps "Tulle Build" (the
# tulle tutu is the whole build); demon-boy-band / web-slinger-crew keep
# "Paint Build" (neon/web paint on the shirts is the main customization);
# daisy / hot-dog keep "Foam Build" (foam sheets / pool noodle is the build).
# Dominant-material rule (Claude recheck, 2026-10-01): the title material must
# be the DOMINANT build material, not the first craft material listed. When
# the first (base) material is clothing -- the costume is worn, not built --
# and the craft materials are minor accents (a felt stem, labels, leaf hats),
# no material gets named: the title uses the "Easy" form. Detected from the
# bank, not hardcoded per-slug.
_CLOTHING_RE = re.compile(
    r"sweatshirt|sweatpants|t-shirt|hoodie|\bshirt\b|outfits|\bvest\b|tunic",
    re.I)
# Judgment calls: clothing-first but the craft element IS the build focus,
# so the material title stays honest.
_CLOTHING_KEEP_MAT = {
    # felt spikes + stuffed tail are the hands-on build, hoodie is the canvas
    "baby-dino",
    # neon paint on the shirts IS the customization (Item 4 keep)
    "demon-boy-band",
    # large felt sheets wrap the body as seaweed; felt is the costume
    "sushi-roll",
    # NOTE (Claude 2026-10-01): blue-alien-ohana removed -- antennas are an
    # accessory; the costume reads from blue clothes. Gets Easy title.
}
# Substantial construction: a box, yards of fabric, large sheets, or
# multiple sheets. A single 9x12 sheet is an accent, not a build.
_SUBSTANTIAL_RE = re.compile(
    r"box|boxes|yards?|large sheets?|([2-9]|\d{2,})\s+sheets?|\bpack\b",
    re.I)

# Slugs with unique (costume-specific) sizing advice. Templated/duplicated
# sizing texts are not shown -- only real costume-specific guidance appears,
# as a "Sizing" line in the plan card. (Claude review 2026-10-01.)
_UNIQUE_SIZING = {'web-slinger-kid', 'pixel-ghost', 'macabre-couple', 'little-prince', 'hero-squad', 'moonwalk-star', 'backyard-hero', 'party-pinata', 'little-witch', 'chill-painter', 'prince-princess', 'juke-joint-vampires', 'kpop-demon-huntresses', 'wayfinder-princess', 'fuzzy-gremlin', 'blue-heeler-pup', 'yellow-henchmen', 'smores-duo', 'rescue-pups', 'cowboy-duo', 'astronaut', 'garden-fairy', 'block-monster', 'fossil-hunter', 'scarecrow', 'baby-pumpkin', 'mystery-teens', 'goth-braids', 'pirate-captain', 'pumpkin-king-bride', 'witchy-sisters'}



def _is_clothing_based(slug, mats):
    if slug in _CLOTHING_KEEP_MAT:
        return False
    if not mats or not _CLOTHING_RE.search(mats[0]):
        return False
    # Clothing-first: Easy unless some non-clothing material is substantial
    # construction. A felt stem or paper label on a sweatsuit isn't a
    # "Felt Build".
    return not any(_SUBSTANTIAL_RE.search(m) for m in mats[1:])


_EASY_TITLE_SLUGS = {
    # plastic props, bought not built
    "cheerleader", "vampire", "juke-joint-vampires", "little-lifeguard",
    "referee", "plastic-dream-crew",
    # wig is one of several props, not the build
    "burger-joint-couple",
    # makeup is an accent, not the build
    "macabre-couple",
    # hats bought/worn, not built
    "little-witch", "wizard", "scarecrow", "moonwalk-star",
    "crowd-camouflage",
    # paint is an accent, not the build
    "basketball-star", "boxer", "deadpan-diva", "goth-braids",
    "hero-squad", "web-hero-duo", "glow-skeleton", "little-lion",
    "pickle", "zombie-coworker",
    # foam props bought, not built
    "headless-horsemen", "neon-demon-hunter",
    # 2026-10-02 (Lane D fabric-build audit): worn clothing + props/accents,
    # not a fabric craft build -- the sheet/robe/dress/shirt is worn, the
    # signature piece is a bought prop or nothing at all
    "classic-ghost",    # bedsheet is clothing-like; "Fabric Build" mislabels
    "dino-tourist",     # Hawaiian shirt + bought plush tail/camera props
    "galaxy-knights",   # bathrobe + bought toy prop, paint optional
    "ice-skater",       # white dress + tights + hair/makeup accessories
    "office-couple",    # button-downs + name tags + teapot prop
    "pop-star",         # sequin jacket + bought mic/sunglasses props
}
assert _EASY_TITLE_SLUGS <= set(data), \
    "easy-title slug not in bank: %s" % (_EASY_TITLE_SLUGS - set(data))


SEOTITLE = {s: _seo_title(s) for s in data}
assert set(SEOTITLE) == set(data), "seo title map missing slugs"
_long_titles = [(s, len(t)) for s, t in SEOTITLE.items() if len(t) > 90]
assert not _long_titles, "seo title over 90 chars: %s" % (_long_titles[:5],)

# Related-by-material internal links (Claude 4c): up to 5 other ideas sharing
# the primary material, deterministic slug order. Rendered only when the
# group has at least one other idea (singletons get no block).
_mat_groups = {}
for s in data:
    _mat_groups.setdefault(PRIMARYMAT[s], []).append(s)
MATRELATED = {}
for s in data:
    _others = sorted(o for o in _mat_groups[PRIMARYMAT[s]] if o != s)
    MATRELATED[s] = _others[:5]
assert set(MATRELATED) == set(data), "material-related map missing slugs"

# Related-block heading labels (Item 4, 2026-10-01): "More <material> builds"
# reads wrong for bought-not-built categories ("More hats builds",
# "More wigs builds"). Per-category labels embedded as MATRELLABEL; anything
# not listed keeps the default "More <category> builds".
_MAT_REL_LABEL = {
    "hats": "More hat costumes",
    "wigs": "More costumes with wigs",
    "plastic": "More costumes with plastic props",
    "makeup": "More makeup costumes",
    "trash bags": "More costumes from trash bags",
}
assert set(_MAT_REL_LABEL) <= set(_MAT_TITLE_NOUN), "label for unknown mat cat"

# Material-name cleaning for the intro paragraph and alt text: strip the
# parenthetical buy/make hints, trailing quantities ("Red felt, 1 sheet" ->
# "red felt"), and leading counts. Never carries a dollar figure (asserted
# below along with the other generated copy).
def _clean_mat(m, max_words=None):
    m = m.split("(")[0].strip()
    # Role labels ("Hero: red sweatsuit...") vs detail tails ("1 white flat
    # sheet: twin size..."): a short prefix is a label, drop it; a long
    # prefix is the item name, drop the tail.
    if ":" in m:
        pre, post = m.split(":", 1)
        m = post.strip() if len(pre.split()) <= 2 else pre.strip()
    m = re.sub(r",\s*for\s+\w+.*$", "", m).strip()  # ", for the sheriff"
    m = re.sub(r"\s+for the \w+.*$", "", m).strip()  # "pants for the rider"
    m = re.sub(r",\s*e\.g\..*$", "", m).strip()
    while re.search(r",\s*\d+(\s+[a-z]+)?\s*,", m):  # ", 1," / ", 1 set,"
        m = re.sub(r",\s*\d+(\s+[a-z]+)?\s*,", ",", m)
    m = re.sub(r",\s+and\s+", " and ", m)
    m = re.sub(r",\s*\d+[^,]*$", "", m).strip()  # trailing ", 1 set" etc.
    m = re.sub(r",\s*per\s+\w+.*$", "", m).strip()  # ", per grown-up"
    m = re.sub(r",\s*\d+\s+per\s+\w+\s*$", "", m).strip()
    m = re.sub(r",\s*about\s+\d+\s*$", "", m).strip()
    # mid-string quantities: "1 pair dark pants" -> "dark pants"
    m = re.sub(r"\s+\d+\s+(pairs?|sets?|tubes?|bottles?|packs?|rolls?|sheets?|yards?)\b",
               "", m)
    m = re.sub(r"\b(or|and)\s+\d+\s+", r"\1 ", m)  # "or 1 old blanket"
    m = re.sub(r",\s*,", ",", m)  # safety net: collapse double commas
    m = re.sub(r"^\d+(\s*to\s*\d+)?\s+", "", m)
    m = re.sub(r"^(sets?|sheets?|pairs?|rolls?|bottles?|packs?|tubes?|yards?)\s+",
               "", m, flags=re.I)
    m = re.sub(r"^(one|two|three|a|an)\s+", "", m, flags=re.I)
    m = re.sub(r"\s+in\s+\d+.*$", "", m)
    if max_words:
        m = " ".join(m.split()[:max_words])
    m = re.sub(r"\s+(in|or|of|and|with|for|to|a|an|the)\s*$", "", m,
               flags=re.I)
    m = m.rstrip(" ,;")
    return (m[0].lower() + m[1:]) if m else m


def _short_mat(m):
    return _clean_mat(m, max_words=7)


_AUD_WORD = {"solo": "solo costumers", "couple": "couples",
             "family": "families", "group": "groups", "kid": "kids",
             "class": "classrooms"}


def _aud_phrase(slug):
    words = [_AUD_WORD[a] for a in _audmap.get(slug, []) if a in _AUD_WORD]
    assert words, "no audience words for " + slug
    if len(words) == 1:
        return words[0]
    return ", ".join(words[:-1]) + ", and " + words[-1] if len(words) > 2 \
        else words[0] + " and " + words[1]


# Hand-written intro paragraphs (Billy-approved voice, 2026-10-01).
# Loaded from hidden_files/intro-rewrites-164.py. Facts (time, materials)
# validated against the bank before deploy; see intro validation script.
_INTRO_NEW_PATH = os.path.join(ROOT, "hidden_files", "intro-rewrites-164.py")
_intro_new_src = open(_INTRO_NEW_PATH, encoding="utf-8").read()
_intro_new_ns = {}
exec(_intro_new_src, _intro_new_ns)
INTRO_NEW = _intro_new_ns["INTRO_NEW"]


# Answer-first intro paragraph: hand-written per costume (Billy-approved
# voice). Falls back to the templated _intro_tmpl if a slug is missing.
def _intro_tmpl(slug):
    mats = [_clean_mat(x) for x in howto[slug]["m"][:3]]
    assert len(mats) == 3 and all(mats), "need 3 materials for " + slug
    time = (howto[slug]["time"] or "").strip()
    dm = re.search(r"\+\s*([\d.]+)\s*(min|hr)s?\s*drying\s*$", time)
    if dm:
        drying = " plus %s drying time" % (dm.group(1) + " " + ("hrs" if "hr" in dm.group(2) and float(dm.group(1)) != 1 else dm.group(2)))
        time = re.sub(r"\s*\+\s*[\d.]+\s*(min|hr)s?\s*drying\s*$", "", time)
    else:
        drying = ""
    return ("The %s is a DIY Halloween costume. Plan on %s of hands-on work%s; "
            "difficulty: %s. You need %s, %s, and %s. It suits %s." % (
                _bare_title(slug), time, drying, howto[slug]["effort"],
                mats[0], mats[1], mats[2], _aud_phrase(slug)))


INTRO = {s: INTRO_NEW.get(s, _intro_tmpl(s)) for s in data}
assert set(INTRO) == set(data), "intro map missing slugs"
_missing = [s for s in data if s not in INTRO_NEW]
assert not _missing, "intros missing hand-written copy: %s" % _missing

# Descriptive alt text (Claude 4c): generated from the materials list, with a
# short material form (parentheticals, quantities, and leading counts
# stripped) so it reads like a human description. Falls back to 2 materials
# when 3 would run long; hard cap 140 chars. No dollar figures (asserted).
# Descriptive file names are deliberately NOT done: renaming images/og/*.jpg
# would require updating every reference (og:image, twitter:image, Pinterest
# pin media, app.js) and a missed one 404s the share card -- too risky.
def _alt(slug, n, short):
    mats = [(_short_mat if short else _clean_mat)(x)
            for x in howto[slug]["m"][:n]]
    assert len(mats) == n and all(mats), "need %d materials for %s" % (n, slug)
    joined = ", ".join(mats[:-1]) + ", and " + mats[-1] if n > 2 \
        else " and ".join(mats)
    return "DIY %s costume built from %s" % (data[slug]["t"].lower(), joined)


SEALT = {}
for _s in data:
    _a = _alt(_s, 3, True)
    if len(_a) > 140:
        _a = _alt(_s, 2, False)  # full 2-material form reads better
    if len(_a) > 140:
        _a = _alt(_s, 2, True)
    SEALT[_s] = _a
assert set(SEALT) == set(data), "alt map missing slugs"
assert not [s for s in data if len(SEALT[s]) > 140], "alt text over 140 chars"
# Costs are dead: no dollar figures in any generated SEO copy.
for _s in data:
    for _v in (SEOTITLE[_s], INTRO[_s], SEALT[_s]):
        assert "$" not in _v, "dollar figure in generated copy: " + _s

# Pictured honesty captions (Billy 2026-10-01): the bank's pictured field
# (full "Pictured: ..." caption, written by viewing the actual concept
# photo) is mirrored into the /c/ guides so the hero renders the same
# caption that in-app ideaMedia shows under the AI honesty label. Parsed
# from the bank at every regen, so a caption edit can never silently desync
# the share pages.
# (Lane 4 batch-1 regen on 2026-10-03 silently dropped this map -- the bank
# never lost the captions. Restored 2026-10-03. Per the standing rule: never
# hand-fix the generated file alone; this parse is the single source of
# truth and every regen re-emits it.)
def _idea_block(slug):
    """Return the bank's {id:"<slug>", ...} object text, brace-matched."""
    i = src.index('{id:"%s",' % slug)
    depth, in_str, esc = 0, False, False
    for j in range(i, len(src)):
        ch = src[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return src[i:j + 1]
    raise AssertionError("unbalanced braces in bank entry: " + slug)

PICTURED = {}
for _s in data:
    _pm = re.search(r'pictured:"((?:[^"\\]|\\.)*)"', _idea_block(_s))
    if _pm:
        PICTURED[_s] = _pm.group(1)
assert len(PICTURED) >= 50, "pictured map too small: %d" % len(PICTURED)
for _s, _c in PICTURED.items():
    assert _c.startswith("Pictured:"), "pictured caption must lead with 'Pictured:': " + _s
    assert "\u2014" not in _c and "\u2013" not in _c, \
        "em/en dash in pictured caption: " + _s
    assert "$" not in _c, "dollar figure in pictured caption: " + _s
    assert _s in data and data[_s]["t"], "pictured slug not in bank: " + _s


# 2026-10-05 (Billy): client-side tick script for the /c/ supply cards.
# Reads/writes the same pantry2 localStorage the app uses, so ticks carry
# over between /c/ guides and the app. Runs synchronously right after the
# cards markup, correcting tick state before paint.
_CLIENTJS = """(function(){
var root=document.getElementById("detail-mats");
if(!root||!window.PMD)return;
var D=window.PMD,SLUG=root.getAttribute("data-slug"),MATS=D.mats,TILES=D.tiles,STAPLES=D.staples||[];
function readTicked(){var s=null;try{s=JSON.parse(localStorage.getItem("pantry2")||localStorage.getItem("pantry3")||"null");}catch(_){}
var set={};for(var i=0;i<STAPLES.length;i++)set[STAPLES[i]]=1;if(s&&s.length)for(var j=0;j<s.length;j++)set[s[j]]=1;return set;}
function saveTicked(set){try{localStorage.setItem("pantry2",JSON.stringify(Object.keys(set)));}catch(_){}}
function has(set,k){return !!set[k];}
function buyKey(mi){return "buy:"+SLUG+"#"+mi;}
function matOk(mat,tk,mi){var hasReal=false,g,k,id,grp;
for(g=0;g<mat.length;g++){grp=mat[g];for(k=0;k<grp.length;k++){if(grp[k]){hasReal=true;break;}}if(hasReal)break;}
for(g=0;g<mat.length;g++){grp=mat[g];var gok=false;
for(k=0;k<grp.length;k++){id=grp[k];if(!id)continue;if(has(tk,id)){gok=true;break;}}
if(!gok){var allNull=true;for(k=0;k<grp.length;k++){if(grp[k]){allNull=false;break;}}
if(allNull&&has(tk,buyKey(mi)))gok=true;if(allNull&&hasReal)gok=true;}
if(!gok)return false;}return true;}
function tileOk(t,tk){for(var j=0;j<t.idxs.length;j++){if(!matOk(MATS[t.idxs[j]],tk,t.idxs[j]))return false;}return true;}
function nextTapId(mat,tk){for(var g=0;g<mat.length;g++){var grp=mat[g],gsat=false,k,id;
for(k=0;k<grp.length;k++){id=grp[k];if(id&&has(tk,id)){gsat=true;break;}}if(gsat)continue;
for(k=0;k<grp.length;k++){id=grp[k];if(id)return id;}return null;}return null;}
function escH(s){return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");}
function render(){var tk=readTicked(),btns=root.querySelectorAll(".ptile"),have=0,total=MATS.length,missHtml="",b,t,btn;
for(b=0;b<TILES.length;b++){t=TILES[b];btn=btns[b];if(!btn)continue;var ok=tileOk(t,tk);
btn.className="ptile "+(ok?"have":"miss");
var badge=btn.querySelector(".ptbadge");if(badge)badge.textContent=ok?"\\u2713":"\\u25CB";
btn.setAttribute("aria-label",btn.getAttribute("data-label")+": "+(ok?"you have this":"missing")+". Tap to update.");
if(!ok)missHtml+='<span class="pchip"><span class="pmemo" aria-hidden="true">'+t.e+"</span>"+escH(t.label)+"</span>";}
for(var mi=0;mi<MATS.length;mi++){if(matOk(MATS[mi],tk,mi))have++;}
var head=root.querySelector("[data-role=chead]");
if(head)head.textContent=have>=total?"You have everything for this one. Nothing to buy.":(have===0?"You have 0 of "+total+" things for this.":"You already have "+have+" of "+total+" things for this.");
var needP=root.querySelector("[data-role=cneed]"),chips=root.querySelector("[data-role=cchips]");
if(needP)needP.style.display=missHtml?"":"none";
if(chips){chips.innerHTML=missHtml;chips.style.display=missHtml?"":"none";}}
function onTap(btn){var t=TILES[parseInt(btn.getAttribute("data-ti"),10)];if(!t)return;
var tk=readTicked(),j,mi;
if(t.rep){var target=null;
for(j=0;j<t.idxs.length;j++){mi=t.idxs[j];if(!matOk(MATS[mi],tk,mi)){target=nextTapId(MATS[mi],tk);break;}}
if(!target||has(tk,target))return;tk[target]=1;}
else{var keys=t.idxs.map(function(x){return buyKey(x);});
var anyUnticked=keys.some(function(k){return !has(tk,k);});
keys.forEach(function(k){if(anyUnticked)tk[k]=1;else delete tk[k];});}
saveTicked(tk);render();}
var all=root.querySelectorAll(".ptile");
for(var b2=0;b2<all.length;b2++)(function(btn){btn.addEventListener("click",function(e){e.preventDefault();onTap(btn);});})(all[b2]);
render();})();"""
assert "\u2014" not in _CLIENTJS and "\u2013" not in _CLIENTJS, "em/en dash in client tick script"


FN = '''// Per-idea share pages: /c/<slug> unfurls the shared costume's own
// illustration for messengers and serves the full build guide as static
// HTML (h1, decision triple, materials, steps, FAQs) so fetchers and AI
// assistants can read and quote it. A CTA deep-links humans into the app
// idea page (?idea=<slug>, share params preserved).
// Regenerate with gen_share_function.py when the idea bank changes.
var IDEAS = %s;

// Old slugs renamed in the Sep 2026 IP sweep: keep every share link ever
// minted working by resolving them to the current canonical slug.
var ALIASES = %s;

// Split-the-build (2026-09-26): slugs whose audience includes group/family
// get the materials divider on their /c/ guide. Emitted from the live bank
// by gen_share_function.py; assert-covered at generation time.
var SPLITABLE = %s;

// Partner Split (2026-09-27): slug -> [halfA, halfB] for couple-audience
// ideas. Halves are derived by gen_split.py, the single source of truth
// shared with split.html; assert-covered at generation time just above.
var DRAFT_HALVES = %s;

// Role share cards (2026-09-27, MagicShot.ai novel-scout steal): idea slug
// -> {role-slug: role display label}, parsed from CASTS by
// gen_share_function.py. The family cast share mints one unfurl link per
// family member role (?o=role&role=<role-slug>); onRequest allowlist-
// validates the role against this map, so forged roles fall back to the
// classic per-costume card and no name ever enters a URL or card pixels.
var ROLE_CARDS = %s;

// Related-costume internal links (SEO 2026-09-27): idea slug -> 5 kindred
// idea slugs, emitted from bank tags + audience by gen_share_function.py.
// Rendered as plain static anchors in the guide body (same for every
// visitor: not cloaking).
var RELATED = %s;

// SEO title + primary material + material-related links + answer-first intro
// + descriptive alt text (SEO 2026-10-01, Claude 4c): all generated from the
// bank by gen_share_function.py. SEOTITLE targets "how to make" searches:
// "DIY Pizza Slice Costume: 45-Min Cardboard Build" -- build time + primary
// material from the idea bank, the same fields the plan uses. Titles kept
// <=60 chars (Lane 4, 2026-10-01).
// No costs/dollar figures anywhere.
var SEOTITLE = %s;
var _UNIQUE_SIZING = new Set(%s);

// Primary material per idea ("cardboard", "felt", ...): the heading noun
// for the "More <material> builds" block.
var PRIMARYMAT = %s;

// Per-category heading labels for the material-related block (Item 4,
// 2026-10-01: "More hat costumes", "More costumes with wigs", ...).
// Falls back to "More <category> builds" when a category has no override.
var MATRELLABEL = %s;

// Material-related internal links: slug -> up to 5 other ideas sharing the
// primary material (deterministic slug order). Singletons render no block.
var MATRELATED = %s;

// Answer-first intro paragraph (Claude 5 /c/ half): what it is, build time,
// difficulty, 3 main materials, who it suits. Plain text; esc()d at use so
// fetchers and AI assistants read it as static HTML.
var INTRO = %s;

// Descriptive alt text for the costume image, generated from the materials
// list. File renames deliberately skipped: images/og/*.jpg are referenced
// from og:image, twitter:image, and Pinterest pin media, and a missed rename
// 404s the share card.
var SEALT = %s;

// Pictured honesty captions (Billy 2026-10-01): slug -> full "Pictured: ..."
// caption, parsed from the bank's pictured fields by gen_share_function.py.
// The hero renders the caption under the AI honesty label when PICTURED has
// the slug; ideas without the field render nothing -- same as in-app
// ideaMedia.
var PICTURED = %s;

// Per-idea guide data, embedded in the page: materials + numbered steps
// feed the schema.org HowTo JSON-LD in the head (honest structured data:
// each page's costume genuinely is a materials list plus steps); the
// decision triple (time/effort) and the 2 parent FAQs are rendered as
// visible static HTML so AI assistants can quote them.
var HOWTO = %s;

// Pantry tile model (2026-10-05): the visual supply cards are the single
// materials presentation on /c/ guides. Same PANTRY_MATS / LABELS / EMOJI
// the app badge uses (extracted from app.js at generation time), so /c/
// cards and app cards can never drift.
var PANTRY_MATS = %s;
var PANTRY_LABELS = %s;
var PANTRY_EMOJI = %s;

/* Supply-card tile computation (2026-10-05): mirrors app.js pantryTileBits
   + buildClosetBadge dup-merge. Output is static HTML (same for every
   visitor); tick state applies client-side from localStorage. */
function _cShortName(t){
  if (!t) return null;
  var s = String(t);
  s = s.replace(/\\s*\\([^)]*\\)/g, "");
  s = s.replace(/,\\s*\\d+\\s*(pairs?|sets?|packs?|rolls?|sheets?|bottles?|tubes?)?\\s*$/i, "");
  s = s.replace(/,\\s*\\d+\\s+(per\\s+person|to\\s+share)\\s*$/i, "");
  s = s.replace(/\\s+per\\s+person\\s*$/i, "");
  s = s.replace(/^\\s*(a|an|the)\\s+/i, "");
  s = s.replace(/^\\d+\\s+(pair\\s+|set\\s+)?/i, "");
  s = s.replace(/\\s+/g, " ").trim();
  s = s.split(",")[0].trim();
  if (/\\sor\\s/i.test(s)) s = s.split(/\\sor\\s/i)[0].trim();
  if (s.length > 42 && /\\sand\\s/i.test(s)) s = s.split(/\\sand\\s/i)[0].trim();
  if (s.length > 42 && s.indexOf(":") > 0){
    var sides = s.split(":"), longest = sides[0];
    for (var si = 1; si < sides.length; si++){ if (sides[si].length > longest.length) longest = sides[si]; }
    s = longest.trim();
  }
  s = s.replace(/^\\s*(a|an|the)\\s+/i, "");
  s = s.replace(/^\\d+\\s+(pair\\s+|set\\s+)?/i, "");
  s = s.replace(/\\s+/g, " ").trim();
  if (!s || s.length > 42) return null;
  return s;
}
function _cTileBits(mat, texts, i){
  var reps = [];
  for (var g = 0; g < mat.length; g++){
    var grp = mat[g];
    for (var k = 0; k < grp.length; k++){
      var id = grp[k];
      if (id && PANTRY_EMOJI[id]){ if (reps.indexOf(id) < 0) reps.push(id); break; }
    }
  }
  if (reps.length){
    var label = PANTRY_LABELS[reps[0]] || reps[0];
    if (mat.length > 1) label += " +" + (mat.length - 1);
    return {e: PANTRY_EMOJI[reps[0]], label: label, rep: reps[0]};
  }
  return {e: "🛒", label: _cShortName(texts[i]) || "Item", rep: null};
}
/* Merged tile list for a slug: [{rep, idxs:[material indices], e, label}].
   Returns null when pantry data is missing or misaligned (fail safe). */
function _cTiles(slug){
  var mats = (PANTRY_MATS.mats[slug] || []);
  var hw = HOWTO[slug];
  if (!hw || !hw.m || !mats.length) return null;
  var texts = hw.m.filter(function(t){ return !/\\([^)]*optional/i.test(t); });
  if (texts.length !== mats.length) return null;
  var tiles = [], seen = {};
  for (var i = 0; i < mats.length; i++){
    var bits = _cTileBits(mats[i], texts, i);
    var key = bits.rep ? ("id:" + bits.rep) : ("buy:" + bits.label);
    if (seen[key]){ seen[key].idxs.push(i); continue; }
    var t = {rep: bits.rep, idxs: [i], e: bits.e, label: bits.label};
    seen[key] = t; tiles.push(t);
  }
  return {mats: mats, texts: texts, tiles: tiles};
}
/* Static supply-cards HTML. Rendered neutral (all miss, zero count); the
   inline client script corrects tick state from localStorage before paint.
   Each card carries the full material text (quantity + buy/make hint) as a
   sub-line, so the cards are the complete materials list. */
function _cCardsHtml(slug, ct){
  if (!ct) return "";
  var staples = PANTRY_MATS.staples || [];
  var cards = ct.tiles.map(function(t, ti){
    var assumed = t.rep && staples.indexOf(t.rep) >= 0;
    var sub = t.idxs.map(function(mi){ return esc(ct.texts[mi]); }).join("<br>");
    return "<button type=\\"button\\" class=\\"ptile miss\\" data-ti=\\"" + ti + "\\" data-label=\\"" + esc(t.label) + "\\" aria-label=\\"" + esc(t.label) + ": missing. Tap to update.\\">" +
      "<span class=\\"ptbadge\\" aria-hidden=\\"true\\">\\u25CB</span>" +
      "<span class=\\"ptemo\\" aria-hidden=\\"true\\">" + t.e + "</span>" +
      "<span class=\\"ptlabel\\">" + esc(t.label) + "</span>" +
      "<span class=\\"ptsub\\">" + sub + "</span>" +
      (assumed ? "<span class=\\"ptag\\">assumed</span>" : "") +
      "</button>";
  }).join("");
  var chips = ct.tiles.map(function(t){
    return "<span class=\\"pchip\\"><span class=\\"pmemo\\" aria-hidden=\\"true\\">" + t.e + "</span>" + esc(t.label) + "</span>";
  }).join("");
  return "<div class=\\"closet-badge\\" id=\\"detail-mats\\" data-slug=\\"" + slug + "\\">" +
    "<p class=\\"closet-line\\" data-role=\\"chead\\">You have 0 of " + ct.mats.length + " things for this.</p>" +
    "<p class=\\"ptiles-sub\\">Tap a supply to tick what you own.</p>" +
    "<div class=\\"ptiles\\">" + cards + "</div>" +
    "<p class=\\"closet-need\\" data-role=\\"cneed\\">Still need:</p>" +
    "<div class=\\"pchips\\" data-role=\\"cchips\\">" + chips + "</div>" +
    "<a class=\\"closet-link\\" href=\\"/pantry?for=" + slug + "\\">Update my pantry</a>" +
    "</div>";
}
/* Client-side tick script source (static): reads/writes the same pantry2
   localStorage the app uses, so ticks carry over between /c/ guides and
   the app. Runs synchronously right after the cards markup. */
var _clientJsSrc = %s;

// Friendly 404 for unknown slugs: the site's own 404 page, embedded at
// generation time (NOTFOUND_SRC in gen_share_function.py), served below
// with a real 404 status.
var NOTFOUND_HTML = %s;

function esc(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;")
          .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

export function onRequest(context) {
  var slug = context.params.slug || "";
  if (ALIASES[slug]) slug = ALIASES[slug]; /* renamed slug -> canonical */
  var idea = IDEAS[slug];
  if (!idea) return new Response(NOTFOUND_HTML, { status: 404, headers: { "Content-Type": "text/html;charset=utf-8", "Cache-Control": "no-store" } });
  var title = esc(idea.t), blurb = esc(idea.b);
  /* SEO title (Claude 4c, 2026-10-01): targets "how to make" searches --
     "DIY Pizza Slice Costume: 45-Min Cardboard Build (Step-by-Step)".
     Generated from bank data (build time + primary material); the fallback
     keeps the page honest if a slug ever misses the map. */
  var seoTitle = esc(SEOTITLE[slug] || (idea.t + " Costume: DIY Guide"));
  /* Descriptive alt text (Claude 4c): generated from the materials list. */
  var imgAlt = esc(SEALT[slug] || (idea.t + " costume idea"));
  var img = "https://pickmycostume.com/images/og/" + slug + ".jpg";
  /* schema.org HowTo JSON-LD: this page's costume genuinely is a materials
     list plus numbered steps, so this is honest structured data aimed at AI
     assistants parsing the page. (Google retired HowTo rich results in 2023;
     this is not for Google rich results.) Built with JSON.stringify so all
     escaping is handled at request time. */
  var _hw = HOWTO[slug] || null;
  /* Share-preview upgrade (2026-09-26): the unfurl text carries the decision
     triple, matching the new og:image decision cards. The triple is asserted
     present at generation time; the empty fallback keeps the page honest if
     it ever is not. esc()d: these land inside a meta content attribute. */
var _tripleText = (_hw && _hw.time && _hw.effort) ?
    /* 2026-09-30 traffic-operator cold-arrival polish: the triple carries
       its labels in the share preview (a bare "Medium" pill read as
       meaningless to cold recipients), and "+ drying" is spelled out as
       passive wait -- the bank's time value is hands-on time (see the
       JSON-LD comment below). */
    "Time: " + esc(_hw.time).replace(/ \\+ drying$/, " of hands-on work + drying time") +
    " \\u00b7 Effort: " + esc(_hw.effort) + ". " : "";
  /* SEO meta description (2026-09-30, fix list P2-11): the old triple+blurb
     ran 54-157 chars with 147 of 164 under 120. This template lands 120-155
     for every idea (asserted at generation time in Python below): the article
     agrees with the title ("an" before vowels, none before "The ..."), and
     "full" drops out if a long title would push past 155. Falls back to the
     blurb when guide data is missing so the tag is never empty. title/blurb
     are already esc()d above; _hw fields are esc()d here like _tripleText. */
  var _desc = blurb;
  if (_hw && _hw.time && _hw.effort) {
    var _art = /^the /i.test(title) ? "" : (/^[aeiou]/i.test(title) ? "an " : "a ");
    _desc = "How to make " + _art + title + " costume in " + esc(_hw.time) +
      ". " + esc(_hw.effort) +
      " DIY project with a full supplies list, step-by-step guide, and sizing tips.";
    if (_desc.length > 155) _desc = _desc.replace("a full supplies list", "a supplies list");
  }
  var _ld = "";
  if (_hw) {
    /* Total hands-on time: bank stores "25 min" (also "25 min + drying").
       Emit the leading minutes as ISO 8601 (PT25M), matching the visible
       decision triple, so AI assistants can lift it. */
    var _hld = {
      "@context": "https://schema.org",
      "@type": "HowTo",
      "name": idea.t + " Halloween costume",
      "description": idea.b,
      "image": img,
      "author": {"@type": "Organization", "name": "Pick My Costume"},
      /* Entity anchor: link guide markup to the site's Organization,
         declared as an @id on the homepage (checklist item 15). */
      "publisher": {"@id": "https://pickmycostume.com/#organization"},
      /* First-publication date of the guide corpus (v7 bank, live
         2026-09-23). Fixed per page, never regenerated for freshness:
         no fake freshness. */
      "datePublished": "2026-09-23",
      "supply": _hw.m.map(function(x){ return {"@type": "HowToSupply", "name": x}; }),
      "step": _hw.s.map(function(x){ return {"@type": "HowToStep", "text": x}; })
    };
    var _tm = /^\\s*(\\d+)\\s*min/i.exec(_hw.time || "");
    if (_tm) _hld.totalTime = "PT" + _tm[1] + "M";
    /* No estimatedCost: prices are not decision-useful and can mislead
       (2026-10-01). The bank keeps its internal cost field; schema omits it. */
    _ld = '<script type="application/ld+json">' + JSON.stringify(_hld) +
      '<' + '/script>';
    /* FAQPage block: the same parent FAQs rendered visibly in the page
       body, as structured data so AI assistants can lift them directly.
       Google retired HowTo rich results in 2023; this is not for Google
       rich results. FAQ markup is honest here: the visible details/summary answers
       the identical questions. */
    var _fq = (_hw.faqs || []).map(function(f){
      return {"@type": "Question", "name": f[0],
              "acceptedAnswer": {"@type": "Answer", "text": f[1]}};
    });
    if (_fq.length) _ld += '<script type="application/ld+json">' +
      JSON.stringify({"@context": "https://schema.org", "@type": "FAQPage",
                      "publisher": {"@id": "https://pickmycostume.com/#organization"},
                      "mainEntity": _fq}) + '<' + '/script>';
    /* BreadcrumbList (SEO 2026-09-27): mirrors the visible breadcrumb nav in
       the body above the h1. Static, same for every visitor. */
    _ld += '<script type="application/ld+json">' + JSON.stringify({
      "@context": "https://schema.org", "@type": "BreadcrumbList",
      "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home",
         "item": "https://pickmycostume.com/"},
        {"@type": "ListItem", "position": 2, "name": "All costumes",
         "item": "https://pickmycostume.com/costumes"},
        {"@type": "ListItem", "position": 3, "name": idea.t}]}) +
      '<' + '/script>';
  }
  /* CTA target: the in-app idea page, with every query param preserved --
     notably ?s=, so genuine-share recipient attribution keeps working (see
     hour-session/arrival-context-gate.js). This is the URL the old
     auto-redirect pointed at; it is now a visible CTA so fetchers and
     humans alike read the guide first. */
  var _qp = new URLSearchParams(new URL(context.request.url).search);
  _qp.set("idea", slug);
  /* 2026-09-26 evening red-team: QA-hygiene. The ?probe= param exists only so
     QA-harness traffic can be excluded from analytics; it must never leak
     into quiz-bound hrefs, or a harness click-through would mint share links
     carrying probe= and recipient traffic would be mis-excluded. Real users
     never have probe=, so deleting it changes nothing for them. */
  _qp.delete("probe");
  /* 2026-09-27 red-team partner split: ?for=/?partner= are /c/-page-only
     recipient params. Deleting them here keeps the sender-typed partner
     name out of the top CTA's homepage URL (and out of PostHog pageview
     URLs) the same way probe= is scrubbed. The draft banner already
     rendered; the quiz-bound links never carried for/partner. */
  _qp.delete("for");
  _qp.delete("partner");
  /* 2026-09-29 named-share variant (index.html NAMED_RESULT_ENABLED): the
     sharer name arrives as ?nm= (URL shape ?s=<sid>&o=named&named=<id>&nm=<name>).
     Sanitized to letters/spaces/hyphens, 20 chars max; rendered in page HTML
     and og meta only -- never into card pixels (the ROLE_CARDS invariant).
     Scrubbed from the top CTA target like probe=/for=/partner=: the name must
     not leak into homepage URLs or PostHog pageviews. */
  var _nm = (_qp.get("nm") || "").replace(/[^A-Za-z \\-]/g, "").trim().slice(0, 20);
  var _sharer = _nm || "Your friend";
  var _sharerEsc = esc(_sharer);
  _qp.delete("nm");
  /* 2026-09-27 role share cards (MagicShot.ai novel-scout steal): the family
     cast share mints one unfurl link per family member role
     (?o=role&role=<role-slug>). The role is allowlist-validated against
     ROLE_CARDS (emitted from CASTS at generation time); a forged or absent
     role falls back to the classic per-costume card above, and no name ever
     enters the URL or the card pixels -- the card identifies the ROLE. */
  var _role = "";
  var _rc = ROLE_CARDS[slug] || {};
  var _rq = _qp.get("role") || "";
  if (_rc[_rq]) _role = _rq;
  if (_role) {
    img = "https://pickmycostume.com/images/og/" + slug + "--" + _role + ".jpg";
    title = esc(_rc[_role]) + ": " + title;
  }
  /* 2026-09-26 red-team recipient audit: the friend's pick must survive the
     top CTA into the quiz too, not just the banner/quizline path. On share
     arrivals the idea landing otherwise drops ?duel=, so the landing's duel
     entry button never appears and the results page cannot render the
     you-vs-friend compare -- the friend context died on the most prominent
     tap target. Mirror the quiz-bound duel rule below (gift excluded: a
     gift is not a duel).
     2026-09-26 red-team recipient audit (pm2): the duel compare is the
     intended payoff only for competitive origins. Pair shares render the
     pair-up verdict INSTEAD of a duel score -- forcing duel= put a Duel-X
     button first on the idea landing and stacked a you-vs-friend box above
     the pair verdict. Vote shares ask the recipient to reply 1/2/3, not to
     duel a finalist.
     2026-09-27 red-team recipient audit (grandparent loop): a grandparent
     arrival is a build-helper recruitment, not a competition -- ?duel= on
     the quiz-bound links put a "Costume duel: your friend picked X" banner
     and a "Duel X: answer 2 questions" entry button in front of the
     grandkid plan. Grandparent shares skip the duel frame like pair/vote.
     2026-09-27 red-team partner split: a drafted partner is not a duelist --
     ?duel= on the quiz-bound links put a "Costume duel: your friend picked X"
     banner and a "Duel X: answer 2 questions" entry button in front of
     someone who was just told which half they ARE. Split arrivals skip the
     duel frame like pair/vote. */
  var _oNoDuel = ["gift", "pair", "vote", "grandparent", "role", "split"].indexOf(_qp.get("o") || "") >= 0;
  if ((_qp.get("s") || "") && _qp.get("gift") !== "1" && !_oNoDuel) _qp.set("duel", slug);
  _qp.set("plan", "1");
  var target = "/?" + _qp.toString();
    /* 2026-09-27 Billy: arrivals from the app's own rails (from=rail /
     from=hero) were invited to "Open this costume in Pick My Costume" --
     the app they just came from. In-app arrivals got a make-it label.
     2026-09-30 traffic-operator (cold-arrival polish): cycle-5 QA found the
     cold label opaque to cold arrivals (Pinterest/Google/direct) -- it names
     a site they have never seen. One clear label for every arrival now.
     Reversible: restore the /^(rail|hero)/ branch with the old cold string
     above to re-split. */
  var _ctaLabel = "Plan this costume \\u2192";
  var targetAttr = target.replace(/&/g, "&amp;");
  /* 2026-10-03 Stream 17 (citation deep-link bridge): bottom-of-guide
     planner CTA uses the exact deep-link shape ChatGPT generates in the
     wild (?idea=<slug>&plan=1), carrying ?s= through only when the guide
     was reached from a share link, so recipient attribution survives the
     tap. Cold arrivals get the bare deep link, matching the assistant
     channel's proven entry point. */
  var _plnQ = new URLSearchParams();
  _plnQ.set("idea", slug);
  _plnQ.set("plan", "1");
  if (_qp.get("s")) _plnQ.set("s", _qp.get("s"));
  var _plannerAttr = ("/?" + _plnQ.toString()).replace(/&/g, "&amp;");
  /* Recipient banner wiring (Experiment 3 recipient ship). One-line flag:
     RECIPIENT_BANNER = false returns the page to the no-banner control.
     The flag's value is emitted INTO the served page's script below, so the
     toggle is a single line in this generated file. The banner is injected
     client-side only, so fetchers, messenger crawlers, and AI assistants
     see byte-identical static HTML either way: this is not cloaking. */
  var RECIPIENT_BANNER = %s;
  /* "I made it" proof-photo section (novel-find 2026-09-26i, MakerWorld
     steal): IMADEIT = false keeps the guide at today's control (no block).
     Flip the one-line Python flag to true, regenerate, and guides render a
     "Wore this? Show us" invite with a photo-share CTA carrying ?madeit=1
     (a later stream wires the submission flow). Static either way. */
  var IMADEIT = %s;
  var _s = _qp.get("s") || "";
  /* Split-the-build (2026-09-26): group/family guides get the materials
     divider (sender panel + recipient self-ID banner). Per-slug, same for
     every visitor: not cloaking. */
  var _canSplit = SPLITABLE.indexOf(slug) >= 0;
  /* Supporting fix (2026-09-26): ?s= must survive EVERY quiz-bound tap.
     The page's bottom quiz link previously pointed at a bare
     pickmycostume.com/ and dropped recipient attribution. It is now built
     at request time from the real query string, exactly like the top CTA. */
  var _qz = new URLSearchParams();
  if (_s) _qz.set("s", _s);
  /* 2026-09-26 red-team W2: the quiz-bound links (bottom quizline + the
     recipient banner's "Find your costume" CTA) preserved ?s= but dropped
     &o=, so taps through them lost share-origin attribution for the running
     card-vs-generic and SMS experiments. Preserve o like the top CTA does. */
  var _o = _qp.get("o") || "";
  if (_o) _qz.set("o", _o);
  /* 2026-09-26 red-team PM: the quiz-bound links (bottom quizline + the
     recipient banner's "Find your costume" CTA) preserved ?s= and ?o= but
     dropped ?pair=, so pair-share recipients tapping the top banner lost the
     pair context and the homepage never rendered the "How you two pair up"
     match banner. Preserve pair like the top CTA does. */
  var _pair = _qp.get("pair") || "";
  if (_pair) _qz.set("pair", _pair);
  /* 2026-09-26 red-team distro: the quiz-bound links (top CTA, recipient
     banner CTA, bottom quizline) preserved s/o/pair/duel but dropped ?sp=,
     so a split-the-build recipient tapping "Take the 2-minute quiz" arrived
     at / without ?sp= and index.html's build_split_link_opened (the only
     measurable recipient leg of the split loop) never fired. Carry the
     builder count, range-validated exactly like parseSplit (2-8); nm/as
     stay /c/-page-internal. */
  var _spn = parseInt(_qp.get("sp") || "", 10);
  if (_spn >= 2 && _spn <= 8) _qz.set("sp", String(_spn));
  /* 2026-09-27 ?src= attribution audit: the quiz-bound links (bottom
     quizline + recipient banner "Find your costume" CTAs) preserved
     s/o/pair/sp/duel but dropped ?src=, so print and share arrivals
     tapping "Take the 2-minute quiz" on a /c/ guide lost landing_src
     at quiz_started. Carry it, namespace-validated exactly like the
     homepage LANDING_SRC allowlist (collection/print/share). Junk and
     forged values never reach the homepage query string. */
  var _src = _qp.get("src") || "";
  if (/^(?:collection|print|share)-[a-z-]+$/.test(_src)) _qz.set("src", _src);
  /* 2026-09-27 role share cards: carry the validated role into the
     quiz-bound links (top CTA, banner CTA, bottom quizline) so the
     homepage arrival can render the role-aware friend headline. _role is
     allowlist-validated above: only real role slugs reach the query string,
     never names. */
  if (_role) _qz.set("role", _role);
  /* 2026-09-26 duel experiment: on share arrivals, carry the sender's
     canonical idea slug so the quiz results page can render the
     "you vs your friend" compare panel and close the quiz return leg.
     Gift links skip the duel panel: the gift IS the comparison context.
     2026-09-26 red-team recipient audit (pm2): pair and vote skip it too --
     pair has its own verdict, vote is not a duel (see _oNoDuel above). */
  var _gift = _qp.get("gift") === "1";
  if (_s && !_gift && !_oNoDuel) _qz.set("duel", slug);
  /* 2026-09-26 gift experiment: ?gfrom= carries the sender's first name
     (sender-typed, length-capped). HTML-escaped here, JSON-encoded below so
     it lands safely inside the injected script's string literal. */
  var _gfromJs = JSON.stringify(esc((_qp.get("gfrom") || "").slice(0, 24)));
  var quizTarget = "/?" + _qz.toString();
  var quizTargetAttr = quizTarget.replace(/&/g, "&amp;");
  /* Static guide body: the same HTML for every visitor (curl fetchers, AI
     assistant browsers, humans, messenger preview crawlers). Identical
     content for everyone: not cloaking. Messenger link previews only read
     the meta tags in the head, so they cannot regress. */
  var _mats = "", _steps = "", _triple = "", _faqs = "", _fit = "", _sharerLine = "";
  if (_hw) {
    _mats = _hw.m.map(function(x){ return "<li>" + esc(x) + "</li>"; }).join("");
    _steps = _hw.s.map(function(x, i){
      var _tx = esc(x).replace(/^Safety:\\s*/, "<strong>Safety:</strong> ");
      /* Sourced-facts layer (checklist item #10, audited 2026-09-26): one
         audited external citation per guide, on the first safety-relevant
         step only. The (step_idx, url, label) triple is computed at
         generation time from hour-session/safety-links.json; every URL was
         fetched and its page verified to support the claim before
         embedding. No em dashes in the link text (the voice rule). */
      if (_hw.safelink && i === _hw.safelink.step_idx) {
        _tx += " (<a class=\\"safesrc\\" href=\\"" + esc(_hw.safelink.url) +
          "\\" rel=\\"noopener\\" target=\\"_blank\\">" + esc(_hw.safelink.label) + "</a>)";
      }
      return "<li>" + _tx + "</li>";
    }).join("");
    /* 2026-09-25: quick version leads. 2026-09-29 (#31): the quickcard
       used to render first-sentences of the same 5 steps the full ordered
       list repeats below -- structural duplication. The quickcard is now a
       materials summary (the "can I make this tonight?" scan); the numbered
       steps live only in the Steps section, and the standalone "You need"
       block is folded in here for the same reason. */
    var _qtip = null;
    _hw.s.forEach(function(x){
      if (/^Optional pro finish:\\s*/i.test(x)){ if (!_qtip) _qtip = x.replace(/^Optional pro finish:\\s*/i, ""); }
    });
    /* 2026-10-05 (Billy): the "DIY this week" quickcard is gone. The visual
       supply cards are the single materials presentation; the tip and the
       sizing note stay. Materials remain indexable via the noscript block
       below and the HowTo JSON-LD supply list. */
    var _tipHtml = _qtip ? "<p class=\\"qtip\\">Tip: " + esc(_qtip) + "</p>" : "";
    /* Sizing guidance: the fit note every parent asks about. (It used to be
       concatenated into _quick before assignment, so it never rendered;
       fixed 2026-10-05.) */
    if (_hw.sizing && _UNIQUE_SIZING.has(slug)) _fit = "<p class=\\"sizing\\">Sizing: " + esc(_hw.sizing) + "</p>";
    var _ct = _cTiles(slug);
    var _cardsHtml = _cCardsHtml(slug, _ct);
    var _pmd = _ct ? JSON.stringify({mats: _ct.mats, tiles: _ct.tiles, staples: (PANTRY_MATS.staples || [])}) : "null";
    var _cardsScript = _ct ? "<script>window.PMD=" + _pmd + ";" + _clientJsSrc + "</scr" + "ipt>" : "";
    var _noscriptMats = "<noscript><div class=\\"nsmats\\"><h2>Materials</h2><ul class=\\"mats\\">" + _mats + "</ul></div></noscript>";
    /* Decision triple: the most quotable line of the guide, first under h1.
       2026-09-30 traffic-operator cold-arrival polish: pills carry their
       labels (a bare "Medium" pill read as meaningless to cold recipients),
       and "+ drying" is spelled out as passive wait, matching the share
       preview text. Reversible: restore the bare _t.map line. */
    var _timeText = esc(_hw.time).replace(/ \\+ drying$/, " of hands-on work + drying time");
    var _pills = [];
    if (_hw.time) _pills.push("<span class=\\"pill\\"><span class=\\"pl\\">Time</span>" + _timeText + "</span>");
    if (_hw.effort) _pills.push("<span class=\\"pill\\"><span class=\\"pl\\">Effort</span>" + esc(_hw.effort) + "</span>");
    if (_pills.length) _triple = "<p class=\\"triple\\">" + _pills.join("") + "</p><p class=\\"timenote\\">Build times are estimates. Yours may vary.</p>";
    /* Sizing guidance: the fit note every parent asks about. */
    if (_hw.sizing && _UNIQUE_SIZING.has(slug)) _fit = "<p class=\\"sizing\\">Sizing: " + esc(_hw.sizing) + "</p>";
    /* 2026-09-29 named share: "<Name> picked <Costume>" static line, HTML +
       og meta only (never card pixels). Defaults to "Your friend".
       2026-09-29 QA cycle 1 arrival gate: emit ONLY on genuine share arrivals
       (8+ char share id, the standing red-team rule a forged ?s=x must not
       render a fake friend claim). Direct visits get no sharer line -- the
       unconditional line read as fabricated social proof. */
    if ((_s || "").length >= 8) {
      _sharerLine = "<p class=\\"sharerline\\">" + _sharerEsc + " picked <strong>" + title + "</strong>.</p>";
    }
    /* Parent FAQs: visible static HTML so AI assistants can quote them. */
    if (_hw.faqs && _hw.faqs.length) {
      _faqs = "<h2>Common questions</h2>" + _hw.faqs.map(function(f){
        return "<details class=\\"faq\\"><summary>" + esc(f[0]) + "</summary><p>" + esc(f[1]) + "</p></details>";
      }).join("");
    }
  }
  /* Related guides (SEO 2026-09-27): thumbnail cards with lazy 256px photos,
     each linking to the related /c/ page as a plain static anchor (SEO-safe;
     same for every visitor: not cloaking).
     2026-10-01 (Billy): cards carry thumbnails, not bare text links. The
     thumbnail falls back to the full-size photo if the -256.webp is ever
     missing. */
  var _relHtml = "";
  var _rel = RELATED[slug] || [];
  if (_rel.length) {
    _relHtml = "<h2>More costumes like this</h2><ul class=\\"rellist\\">" +
      _rel.map(function(s){ return "<li class=\\"relcard\\"><a href=\\"/c/" + s + "\\">" +
        "<img src=\\"/photos/" + s + "-256.webp\\" loading=\\"lazy\\" onerror=\\"this.onerror=null;this.src='/photos/" + s + ".webp'\\" alt=\\"\\">" +
        "<span>" + esc(IDEAS[s].t) + "</span></a></li>"; }).join("") +
      "</ul>";
  }
  /* Related by material (SEO 2026-10-01, Claude 4c): "More cardboard
     builds" next to "More costumes like this", grouped by primary material
     from the bank (cardboard builds, felt builds, etc.). Same for every
     visitor: not cloaking. Singletons render no block.
     2026-10-01 (Billy): thumbnail cards here too, matching the kindred
     block above. */
  var _matHtml = "";
  var _matRel = MATRELATED[slug] || [];
  if (_matRel.length && PRIMARYMAT[slug]) {
    var _matLabel = (MATRELLABEL[PRIMARYMAT[slug]] ||
      ("More " + PRIMARYMAT[slug] + " builds"));
    _matHtml = "<h2>" + esc(_matLabel) + "</h2><ul class=\\"rellist\\">" +
      _matRel.map(function(s){ return "<li class=\\"relcard\\"><a href=\\"/c/" + s + "\\">" +
        "<img src=\\"/photos/" + s + "-256.webp\\" loading=\\"lazy\\" onerror=\\"this.onerror=null;this.src='/photos/" + s + ".webp'\\" alt=\\"\\">" +
        "<span>" + esc(IDEAS[s].t) + "</span></a></li>"; }).join("") +
      "</ul>";
  }
  /* Answer-first intro (Claude 5 /c/ half, 2026-10-01): the first paragraph
     states what it is, build time, difficulty, the 3 main materials, and who
     it suits -- generated from the bank, static HTML so fetchers and AI
     assistants can read it. */
  var _introHtml = INTRO[slug] ? "<p class=\\"intro\\">" + esc(INTRO[slug]) + "</p>" : "";
  /* Recipient banner (Experiment 3 recipient ship). Client-side injection:
     genuine share arrivals (?s= present) get the warm friend banner with a
     quiz CTA that preserves ?s= attribution; everyone else (and the
     no-banner control) sees the page exactly as before. Copy mirrors the
     in-app share landing voice (shareLandingHeadline): "Your friend picked
     X. What would you pick?" -- no em dashes, phone-first. */
  var _bannerScript = "<script>var RECIPIENT_BANNER = " + (RECIPIENT_BANNER ? "true" : "false") + ";" +
    "var GIFT_FROM = " + _gfromJs + ";" +
    "var SHARER_NAME=" + JSON.stringify(_sharerEsc) + ";" +
    "var DRAFTH = " + JSON.stringify(DRAFT_HALVES[slug] || null) + ";" +
    "(function(){" +
    "function _rmSL(){var _sl=document.querySelector('.sharerline');if(_sl)_sl.parentNode.removeChild(_sl);}" +
    "var q = new URLSearchParams(location.search || \\\"\\\");" +
    "var main = document.querySelector(\\\"main.guide\\\");" +
    "if (!main) return;" +
    "var b = document.createElement(\\\"div\\\");" +
    "b.className = \\\"rbanner\\\";" +
    "/* 2026-09-26 red-team: the gift branch must require ?s= like every other" +
    " recipient context. A bare ?gift=1 (no share id) would otherwise render" +
    " a fake gift banner with an attacker-typed ?gfrom=. App-minted gift" +
    " links always carry ?s=<sid>, so this is behavior-safe. */" +
    "/* 2026-09-26 pm3 red-team: forged ?s=x rendered a fake gift banner with a typed name. Require 8+ chars like the generic branch. */" +
    "if (!RECIPIENT_BANNER) return;" +
    "if (q.get(\\"gift\\") === \\"1\\" && (q.get(\\"s\\") || \\"\\").length >= 8) {" +
    "var who = GIFT_FROM ? GIFT_FROM + \\" picked\\" : \\"Someone picked\\";" +
    "b.innerHTML = \\\"<p class=\\\\\\\"rbanner-line\\\\\\\">\\\\u{1F381} \\" + who + \\" <strong>" + title + "</strong> for you.</p>\\\" +" +
    " \\\"<p class=\\\\\\\"rbanner-sub\\\\\\\">A starting idea, not a verdict. Take the 2-minute quiz to get your own costume.</p>\\\" +" +
    " \\\"<a class=\\\\\\\"cta rbanner-cta\\\\\\\" href=\\\\\\\"" + quizTargetAttr + "\\\\\\\">Find your costume</a>\\\";" +
    "_rmSL();" +
    "main.insertBefore(b, main.firstChild);" +
    "return;" +
    "}" +
    "var s = q.get(\\\"s\\\") || \\\"\\\";" +
    "/* Partner Split (2026-09-27): drafted-partner arrival (?for=0|1)." +
    "   Names both halves, so it takes precedence over the generic" +
    "   friend banner below. Built with DOM methods + textContent (no" +
    "   innerHTML): the sender-typed ?partner= can never inject markup." +
    "   Client-side only: fetchers see byte-identical static HTML." +
    "   2026-09-27 red-team: require a genuine share id (8+ chars) like the" +
    "   generic and gift branches, so a hand-typed ?for=0 with no ?s= cannot" +
    "   render a forged draft banner. */" +
    "var _for = q.get('for');" +
    "var _halves = (typeof DRAFTH !== 'undefined') ? DRAFTH : null;" +
    "if ((_for === '0' || _for === '1') && s.length >= 8 && _halves && _halves.length === 2) {" +
    "var _fi = parseInt(_for, 10);" +
    "var _pn = (q.get('partner') || '').trim().slice(0, 24);" +
    "var _me = _halves[_fi], _them = _halves[1 - _fi];" +
    "var _olds = main.querySelectorAll('.rbanner');" +
    "for (var _oi = 0; _oi < _olds.length; _oi++) _olds[_oi].parentNode.removeChild(_olds[_oi]);" +
    "var _b2 = document.createElement('div');" +
    "_b2.className = 'rbanner';" +
    "var _l1 = document.createElement('p');" +
    "_l1.className = 'rbanner-line';" +
    "_l1.textContent = '🎃 You have been drafted!';" +
    "var _l2 = document.createElement('p');" +
    "_l2.className = 'rbanner-sub';" +
    "_l2.appendChild(document.createTextNode(_pn ? _pn + ' is going as ' : 'Your partner is going as '));" +
    "var _s1 = document.createElement('strong');" +
    "_s1.textContent = _them;" +
    "_l2.appendChild(_s1);" +
    "_l2.appendChild(document.createTextNode(' You are the '));" +
    "var _s2 = document.createElement('strong');" +
    "_s2.textContent = _me;" +
    "_l2.appendChild(_s2);" +
    "_l2.appendChild(document.createTextNode('. The build guide is below.'));" +
    "var _cta = document.createElement('a');" +
    "_cta.className = 'cta rbanner-cta';" +
    "_cta.href = '" + quizTarget + "';" +
    "_cta.textContent = 'Get your own costume';" +
    "_b2.appendChild(_l1);" +
    "_b2.appendChild(_l2);" +
    "_b2.appendChild(_cta);" +
    "_rmSL();" +
    "main.insertBefore(_b2, main.firstChild);" +
    "return;" +
    "}" +
"/* Red-team 2026-09-26 PM: align with the homepage isGenuineShareArrival" +
    " rule (8+ chars). A forged ?s=x rendered a fake anonymous friend" +
    " banner; the homepage already rejects short ids. */" +
    "if (!s || s.length < 8) return;" +
    "_rmSL();" +
    "var main = document.querySelector(\\\"main.guide\\\");" +
    "if (!main) return;" +
    "/* 2026-09-26 red-team recipient audit (pm2): pair-share recipients saw" +
    " the generic friend-picked banner with no match framing, and vote-share" +
    " recipients saw it too -- wrong for a reply-1-2-3 ask. Origin-aware" +
    " banner copy; both keep the quiz door open. */" +
    "if (q.get(\\\"o\\\") === \\\"pair\\\") {" +
    "var b = document.createElement(\\\"div\\\");" +
    "b.className = \\\"rbanner\\\";" +
    "b.innerHTML = \\\"<p class=\\\\\\\"rbanner-line\\\\\\\">Your friend is going as <strong>" + title + "</strong>.</p>\\\" +" +
    " \\\"<p class=\\\\\\\"rbanner-sub\\\\\\\">Take the 2-minute quiz to find YOUR costume to match.</p>\\\" +" +
    " \\\"<a class=\\\\\\\"cta rbanner-cta\\\\\\\" href=\\\\\\\"" + quizTargetAttr + "\\\\\\\">Find your costume</a>\\\";" +
    "main.insertBefore(b, main.firstChild);" +
    "return;" +
    "}" +
    "if (q.get(\\\"o\\\") === \\\"vote\\\") {" +
    "var b = document.createElement(\\\"div\\\");" +
    "b.className = \\\"rbanner\\\";" +
    "b.innerHTML = \\\"<p class=\\\\\\\"rbanner-line\\\\\\\">Your friend is taking votes on 3 Halloween finalists.</p>\\\" +" +
    " \\\"<p class=\\\\\\\"rbanner-sub\\\\\\\"><strong>" + title + "</strong> is one of them. Reply 1, 2, or 3 in the chat with your vote.</p>\\\" +" +
    " \\\"<a class=\\\\\\\"cta rbanner-cta\\\\\\\" href=\\\\\\\"" + quizTargetAttr + "\\\\\\\">Find your costume</a>\\\";" +
    "main.insertBefore(b, main.firstChild);" +
    "return;" +
    "}" +
    "/* 2026-09-27 no-clone pact experiment: ?o=noclone marks class-chat" +
    " coordination shares. The recipient job is to reply with their kid's" +
    " costume, not just pick -- the banner names the pact. */" +
    "if (q.get(\\\"o\\\") === \\\"noclone\\\") {" +
    "var b = document.createElement(\\\"div\\\");" +
    "b.className = \\\"rbanner\\\";" +
    "b.innerHTML = \\\"<p class=\\\\\\\"rbanner-line\\\\\\\">Your friend picked <strong>" + title + "</strong> and started a no-clone pact.</p>\\\" +" +
    " \\\"<p class=\\\\\\\"rbanner-sub\\\\\\\">No matching costumes at the parade. Reply with your kid's costume in the chat, or take the 2-minute quiz to get your own.</p>\\\" +" +
    " \\\"<a class=\\\\\\\"cta rbanner-cta\\\\\\\" href=\\\\\\\"" + quizTargetAttr + "\\\\\\\">Find your costume</a>\\\";" +
    "main.insertBefore(b, main.firstChild);" +
    "return;" +
    "}" +
    "/* 2026-09-27 team-kit experiment: ?o=team marks youth-sports team" +
    " coordination shares. The recipient job is to reply with their kid's" +
    " shirt size, not just pick -- the banner names the team job. */" +
    "if (q.get(\\\"o\\\") === \\\"team\\\") {" +
    "var b = document.createElement(\\\"div\\\");" +
    "b.className = \\\"rbanner\\\";" +
    "b.innerHTML = \\\"<p class=\\\\\\\"rbanner-line\\\\\\\">Your team is going as <strong>" + title + "</strong>.</p>\\\" +" +
    " \\\"<p class=\\\\\\\"rbanner-sub\\\\\\\">One costume for the whole team. Reply with your kid's shirt size in the team chat, or take the 2-minute quiz to find your own.</p>\\\" +" +
    " \\\"<a class=\\\\\\\"cta rbanner-cta\\\\\\\" href=\\\\\\\"" + quizTargetAttr + "\\\\\\\">Find your costume</a>\\\";" +
    "main.insertBefore(b, main.firstChild);" +
    "return;" +
    "}" +
    "var b = document.createElement(\\\"div\\\");" +
    "b.className = \\\"rbanner\\\";" +
    "b.innerHTML = \\\"<p class=\\\\\\\"rbanner-line\\\\\\\">\\\" + SHARER_NAME + \\\" picked <strong>" + title + "</strong>. What would you pick?</p>\\\" +" +
    " \\\"<p class=\\\\\\\"rbanner-sub\\\\\\\">Take the 2-minute quiz to get your own costume.</p>\\\" +" +
    " \\\"<a class=\\\\\\\"cta rbanner-cta\\\\\\\" href=\\\\\\\"" + quizTargetAttr + "\\\\\\\">Find your costume</a>\\\";" +
    "main.insertBefore(b, main.firstChild);" +
    "})();" +
    "<" + "/script>";
  /* Split-the-build (2026-09-26): sender panel markup (static, group/family
     guides only) and the client script. The recipient self-ID banner is
     injected client-side so fetchers see byte-identical static HTML. */
  var _splitHtml = "";
  var _splitScript = "";
  if (_canSplit) {
    _splitHtml = "<div class='splitwrap' id='splitwrap'>" +
      "<button type='button' class='ghost splitopen'>Splitting the shopping? Divide this list.</button>" +
      "<div class='splitpanel' style='display:none'>" +
      "<p class='splitq'>How many builders?</p>" +
      "<p class='splitstepper'><button type='button' class='ghost splitminus' aria-label='Fewer builders'>&minus;</button>" +
      "<span class='splitcount'>3</span>" +
      "<button type='button' class='ghost splitplus' aria-label='More builders'>+</button></p>" +
      "<div class='splitnameset'></div>" +
      "<p><button type='button' class='cta splitmake'>Make the split</button></p>" +
      "<div class='splitresult'></div>" +
      "</div></div>";
    _splitScript = "<script>" +
      "var SPLIT_MATS = " + JSON.stringify(_hw.m) + ";" +
      "var SPLIT_TITLE = " + JSON.stringify(idea.t) + ";" +
      "var SPLIT_SLUG = " + JSON.stringify(slug) + ";" +
      "(function(){" +
      "var q = new URLSearchParams(location.search || '');" +
      "function escH(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\\x22/g,'&quot;');}" +
      "function cleanName(s){return String(s || '').replace(/[~|&=<>\\\"']/g,'').trim().slice(0,24);}" +
      "function newSid(){var abc='abcdefghijklmnopqrstuvwxyz0123456789';var s='';for(var i=0;i<8;i++)s+=abc[Math.floor(Math.random()*abc.length)];return s;}" +
      "function assignMats(n){var a=[];for(var i=0;i<n;i++)a.push([]);for(var m=0;m<SPLIT_MATS.length;m++)a[m %% n].push(m);return a;}" +
      "function encAssign(a){return a.map(function(l){return l.map(function(i){return i.toString(36);}).join('.');}).join('|');}" +
      "function parseSplit(){" +
      "var n=parseInt(q.get('sp')||'',10);" +
      "if(!(n>=2&&n<=8))return null;" +
      "if(!q.get('nm'))return null;" +
      "var names=(q.get('nm')||'').split('~').map(cleanName);" +
      "while(names.length<n)names.push('Person '+(names.length+1));" +
      "names=names.slice(0,n);" +
      "var parts=(q.get('as')||'').split('|');" +
      "if(parts.length!==n)return null;" +
      "var assign=parts.map(function(p){" +
      "var idx=p.split('.').map(function(t){return parseInt(t,36);}).filter(function(i){return i>=0&&i<SPLIT_MATS.length;});" +
      "return idx.filter(function(v,i){return idx.indexOf(v)===i;});});" +
      "return {n:n,names:names,assign:assign};}" +
      "function splitUrl(names,a,sid){var p=new URLSearchParams();p.set('sp',String(names.length));p.set('nm',names.join('~'));p.set('as',encAssign(a));p.set('s',sid);return 'https://pickmycostume.com/c/'+SPLIT_SLUG+'?'+p.toString();}" +
      "function groupText(names,a,url){var lines=['We are splitting the '+SPLIT_TITLE+' build!',''];" +
      "names.forEach(function(nm,i){var items=a[i].map(function(mi){return SPLIT_MATS[mi];});lines.push((i+1)+'. '+nm+': '+(items.join(', ')||'nothing yet'));});" +
      "lines.push('','Tap to see your list:',url);return lines.join('\\\\n');}" +
      "function copyText(t,done){" +
      "function fb(){var ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');}catch(e){}document.body.removeChild(ta);if(done)done(true);}" +
      "if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){if(done)done(true);},fb);}else{fb();}}" +
      "if(typeof window!=='undefined'){window.__splitTest={parseSplit:parseSplit,assignMats:assignMats,encAssign:encAssign,splitUrl:splitUrl,groupText:groupText,cleanName:cleanName};}" +
      "var sp=parseSplit();" +
      "if(sp){" +
      "var main=document.querySelector('main.guide');" +
      "if(main){" +
      "var olds=main.querySelectorAll('.rbanner');" +
      "for(var oi=0;oi<olds.length;oi++)olds[oi].parentNode.removeChild(olds[oi]);" +
      "var b=document.createElement('div');b.className='rbanner splitbanner';" +
      "var h='<p class=\\\"rbanner-line\\\">Your crew build list: '+escH(SPLIT_TITLE)+'</p><p class=\\\"rbanner-sub\\\">Tap your name to see what you are getting.</p><p class=\\\"splitnames\\\">';" +
      "sp.names.forEach(function(nm,i){h+='<button type=\\\"button\\\" class=\\\"splitname\\\" data-i=\\\"'+i+'\\\">'+escH(nm)+'</button>';});" +
      "h+='</p><div class=\\\"splitmine\\\"></div>';" +
      "b.innerHTML=h;" +
      "main.insertBefore(b,main.firstChild);" +
      "var mine=b.querySelector('.splitmine');" +
      "var btns=b.querySelectorAll('.splitname');" +
      "for(var bi=0;bi<btns.length;bi++)(function(btn,i){" +
      "btn.onclick=function(){" +
      "var items=sp.assign[i].map(function(mi){return SPLIT_MATS[mi];});" +
      "mine.innerHTML='<p class=\\\"splitmine-head\\\">'+escH(sp.names[i])+', you are getting:</p>'+(items.length?'<ul class=\\\"splititems\\\">'+items.map(function(x){return '<li>'+escH(x)+'</li>';}).join('')+'</ul>':'<p class=\\\"splititems-empty\\\">Nothing assigned to you. Everything is covered.</p>')+'<button type=\\\"button\\\" class=\\\"ghost splitcopy\\\">Copy my items</button>';" +
      "mine.querySelector('.splitcopy').onclick=function(){copyText(sp.names[i]+', you are getting for '+SPLIT_TITLE+':\\\\n'+items.join('\\\\n'));};};" +
      "})(btns[bi],bi);}}" +
      "var wrap=document.getElementById('splitwrap');" +
      "if(!wrap)return;" +
      "var N=3;" +
      "function renderNames(){var box=wrap.querySelector('.splitnameset');var html='';for(var i=0;i<N;i++)html+='<input class=\\\"splitnamein\\\" maxlength=\\\"24\\\" placeholder=\\\"Person '+(i+1)+'\\\" aria-label=\\\"Builder '+(i+1)+' name\\\">';box.innerHTML=html;}" +
      "wrap.querySelector('.splitopen').onclick=function(){wrap.querySelector('.splitpanel').style.display='block';this.style.display='none';renderNames();};" +
      "var stepEl=wrap.querySelector('.splitcount');" +
      "wrap.querySelector('.splitminus').onclick=function(){if(N>2){N--;stepEl.textContent=N;renderNames();}};" +
      "wrap.querySelector('.splitplus').onclick=function(){if(N<8){N++;stepEl.textContent=N;renderNames();}};" +
      "function getNames(){var ins=wrap.querySelectorAll('.splitnamein');var out=[];for(var i=0;i<ins.length;i++)out.push(cleanName(ins[i].value)||('Person '+(i+1)));return out;}" +
      "wrap.querySelector('.splitmake').onclick=function(){" +
      "var names=getNames();" +
      "var a=assignMats(names.length);" +
      "var sid=newSid();" +
      "var url=splitUrl(names,a,sid);" +
      "var res=wrap.querySelector('.splitresult');" +
      "var html='<p class=\\\"splitres-head\\\">The split is ready. Send it to the group chat:</p><ol class=\\\"splitres-list\\\">';" +
      "names.forEach(function(nm,i){var items=a[i].map(function(mi){return SPLIT_MATS[mi];});html+='<li><strong>'+escH(nm)+':</strong> '+escH(items.join(', ')||'nothing yet')+'</li>';});" +
      "html+='</ol><p><button type=\\\"button\\\" class=\\\"cta splitcopygroup\\\">Copy group text</button> <button type=\\\"button\\\" class=\\\"ghost splitcopylink\\\">Copy link only</button></p><p class=\\\"splitnote\\\">Everyone taps the link, taps their name, and sees exactly what to get.</p>';" +
      "res.innerHTML=html;" +
      "res.querySelector('.splitcopygroup').onclick=function(){var btn=this;copyText(groupText(names,a,url),function(){btn.textContent='Copied. Send it to the group chat.';});};" +
      "res.querySelector('.splitcopylink').onclick=function(){var btn2=this;copyText(url,function(){btn2.textContent='Link copied.';});};" +
      "};" +
      "})();" +
      "<" + "/script>";
  }
  /* Partner Split (2026-09-27): couple guides get a static "draft your
     partner" CTA into split.html. Per-slug, same for every visitor: not
     cloaking. DRAFT_HALVES[slug] is the couple check. */
  var _splitPartnerHtml = "";
  if (DRAFT_HALVES[slug]) {
    _splitPartnerHtml = "<h2>Splitting this costume?</h2>" +
      "<p class='splitpartner-line'>Going as a duo? Claim your half and draft your partner into theirs.</p>" +
      "<p class='ctawrap'><a class='cta' href='/split.html?idea=" + slug + "'>Split it with your partner</a></p>";
  }
  /* 2026-09-29 QA cycle 1 arrival gate: og/twitter titles keep the friend
     voice ONLY on genuine share arrivals (8+ char share id; the ?nm= named
     variant already requires ?s= in practice). Direct visits and crawlers get
     the honest guide title, mirroring the <title> tag. */
  var _ogTitle = ((_s || "").length >= 8)
    ? _sharerEsc + " picked " + title + " - Pick My Costume"
    : seoTitle;
  /* 2026-10-03 Stream 17: bottom-of-guide planner CTA. Rendered at
     request time so ?s= (when present) is carried into the deep link. */
  var _plannerCtaHtml =
    "<p class=\\"ctawrap\\"><a class=\\"cta plancta\\" href=\\"" + _plannerAttr + "\\">Start this costume in the planner</a></p>";
  /* 2026-10-03 Stream 17: tapGuard for the plan-flow CTAs (standing rule
     2026-09-27). Both the top CTA and the new bottom planner CTA open the
     app plan flow; a finger bounce must not double-fire the entry. */
  var _plannerGuardScript = "<script>" +
    "(function(){" +
    "var _tg={};" +
    "function _tgOk(k){var n=Date.now();if(n-(_tg[k]||0)<400)return false;_tg[k]=n;return true;}" +
    "var links=document.querySelectorAll('a.plancta');" +
    "for(var i=0;i<links.length;i++){" +
    "(function(a){if(a._tgW)return;a._tgW=true;" +
    "a.addEventListener('click',function(ev){if(!_tgOk('plancta'))ev.preventDefault();});})(links[i]);}" +
    "})();" +
    " <" + "/script>";
  var html = "<!DOCTYPE html>" +
    "<html lang=\\"en\\"><head><meta charset=\\"utf-8\\">" +
    "<title>" + seoTitle + "</title>" +
    "<link rel=\\"canonical\\" href=\\"https://pickmycostume.com/c/" + slug + "\\">" +
    "<meta name=\\"description\\" content=\\"" + _desc + "\\">" +
    "<meta name=\\"author\\" content=\\"Pick My Costume\\">" +
    "<meta property=\\"og:type\\" content=\\"website\\">" +
    "<meta property=\\"og:url\\" content=\\"https://pickmycostume.com/c/" + slug + "\\">" +
    "<meta property=\\"og:title\\" content=\\"" + _ogTitle + "\\">" +
    "<meta property=\\"og:description\\" content=\\"" + _tripleText + blurb + "\\">" +
    "<meta property=\\"og:image\\" content=\\"" + img + "\\">" +
    "<meta property=\\"og:image:secure_url\\" content=\\"" + img + "\\">" +
    "<meta property=\\"og:image:type\\" content=\\"image/jpeg\\">" +
    "<meta property=\\"og:image:width\\" content=\\"1200\\">" +
    "<meta property=\\"og:image:height\\" content=\\"630\\">" +
    "<meta property=\\"og:image:alt\\" content=\\"" + imgAlt + "\\">" +
    "<meta name=\\"twitter:card\\" content=\\"summary_large_image\\">" +
    "<meta name=\\"twitter:title\\" content=\\"" + _ogTitle + "\\">" +
    "<meta name=\\"twitter:description\\" content=\\"" + blurb + "\\">" +
    "<meta name=\\"twitter:image\\" content=\\"" + img + "\\">" +
    "<meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1\\">" +
    _ld +
    "<style>" +
    "body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;color:#fdf3e3;background:#160d28;line-height:1.55;}" +
    ".topbar{background:#160d28;border-bottom:1px solid #4b3486;padding:10px 20px;position:sticky;top:0;z-index:5;}" +
    ".topbar a{color:#fdf3e3;text-decoration:none;font-weight:800;font-size:16px;}" +
    ".topbar a span{color:#ff8c1a;}" +
    ".guide{max-width:640px;margin:0 auto;padding:20px 20px 48px;}" +
    "h1{font-size:30px;margin:0 0 10px;letter-spacing:-0.01em;}" +
    ".triple{margin:0 0 10px;display:flex;flex-wrap:wrap;gap:8px;}" +
    ".pill{display:inline-block;background:#2a1c52;border:1px solid #4b3486;color:#fdf3e3;font-size:14px;font-weight:700;padding:5px 12px;border-radius:999px;}" +
    /* 2026-09-30 traffic-operator: the small-caps unit labels inside the
       decision pills (Time / Effort). */
    ".pl{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;opacity:.65;margin-right:7px;}" +
    ".fit{font-size:15px;color:#cdbcf0;margin:0 0 8px;}" +
    ".sizing{font-size:14px;color:#cdbcf0;margin:8px 0 0;font-style:italic;}" +
    ".lede{font-size:17px;color:#fdf3e3;margin:0;}" +
    ".intro{font-size:17px;color:#fdf3e3;margin:0 0 12px;}" +
    "h2{font-size:22px;margin:32px 0 12px;letter-spacing:-0.01em;}" +
    ".closet-badge{border:1px solid #4b3486;border-radius:14px;padding:12px 14px;margin:18px 0;background:#2a1c52;}" +
    ".closet-badge p{margin:0 0 6px;}" +
    ".closet-line{font-weight:700;font-size:15px;color:#fdf3e3;}" +
    ".ptiles-sub{margin:0 0 10px;color:#cdbcf0;font-size:14px;}" +
    ".ptiles{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:0 0 10px;}" +
    ".ptile{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;min-height:96px;padding:10px 6px;text-align:center;font:inherit;cursor:pointer;border:2px solid #4b3486;border-radius:14px;background:rgba(0,0,0,.18);color:#fdf3e3;}" +
    ".ptile .ptemo{font-size:36px;line-height:1.1;}" +
    ".ptile .ptlabel{font-size:11px;line-height:1.25;overflow-wrap:anywhere;}" +
    ".ptile .ptsub{font-size:11px;line-height:1.35;color:#cdbcf0;overflow-wrap:anywhere;}" +
    ".ptile.have{border-color:#7ee2a8;}" +
    ".ptile.have .ptlabel{color:#cdbcf0;}" +
    ".ptile.miss{border-style:dashed;}" +
    ".ptile .ptbadge{position:absolute;top:6px;right:6px;width:20px;height:20px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;}" +
    ".ptile.have .ptbadge{background:#7ee2a8;color:#0c2b18;}" +
    ".ptile.miss .ptbadge{border:2px solid #ff8c1a;color:#ff8c1a;}" +
    ".ptile .ptag{font-size:10px;color:#cdbcf0;border:1px solid #4b3486;border-radius:10px;padding:2px 7px;white-space:nowrap;}" +
    ".ptile:active{background:rgba(255,255,255,.06);}" +
    ".pchips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 10px;}" +
    ".pchip{display:inline-flex;align-items:center;gap:6px;font-size:13px;padding:6px 10px;border:1px dashed #4b3486;border-radius:999px;color:#fdf3e3;}" +
    ".pchip .pmemo{font-size:16px;}" +
    ".closet-need{color:#cdbcf0;font-size:13px;}" +
    ".closet-link{font-size:13px;color:#ff8c1a;text-decoration:underline;cursor:pointer;}" +
    ".qtip{font-size:15px;color:#cdbcf0;font-style:italic;margin:10px 0 0;}" +
    "details.faq{border:1px solid #4b3486;border-radius:10px;margin:8px 0;background:#211540;}" +
    "details.faq summary{font-weight:700;font-size:16px;padding:12px 14px;cursor:pointer;list-style:none;}" +
    "details.faq summary::-webkit-details-marker{display:none;}" +
    "details.faq summary::before{content:'+ ';color:#ff8c1a;font-weight:700;}" +
    "details.faq[open] summary::before{content:'\u2212 ';}" +
    "details.faq p{margin:0;padding:0 14px 12px;font-size:16px;line-height:1.55;}" +
    ".mats{list-style:none;padding:0;margin:0;background:#211540;border:1px solid #4b3486;border-radius:14px;padding:6px 18px;}" +
    ".mats li{margin:0;padding:10px 0 10px 28px;border-bottom:1px solid #4b3486;position:relative;font-size:16px;}" +
    ".mats li:last-child{border-bottom:none;}" +
    ".mats li::before{content:'✓';position:absolute;left:2px;color:#ff8c1a;font-weight:700;}" +
    "ol.steps{list-style:none;counter-reset:step;padding:0;margin:0;}" +
    "ol.steps li{counter-increment:step;margin:0 0 4px;padding:10px 0 10px 44px;position:relative;font-size:16px;line-height:1.6;}" +
    "ol.steps li::before{content:counter(step);position:absolute;left:0;top:10px;width:30px;height:30px;border-radius:50%%;background:#ff8c1a;color:#fff;font-weight:800;font-size:15px;display:flex;align-items:center;justify-content:center;}" +
    ".ctawrap{margin:20px 0;}" +
    ".storyline{font-size:16px;margin:0 0 14px;color:#cdbcf0;}" +
    ".storyline a{color:#ff8c1a;font-weight:700;text-decoration:none;}" +
    ".cta{display:inline-block;background:#ff8c1a;color:#fff;font-weight:700;padding:14px 22px;border-radius:12px;text-decoration:none;font-size:17px;}" +
    ".guide img{max-width:100%%;height:auto;border-radius:12px;margin:6px 0;}" +
    "ul,ol{font-size:16px;line-height:1.55;padding-left:22px;margin:0;}" +
    ".quizline{font-size:15px;color:#cdbcf0;margin-top:26px;}" +
    ".quizline a{color:#ff8c1a;font-weight:700;}" +
    ".pinline{font-size:14px;color:#cdbcf0;margin:10px 0 0;}" +
    ".sharerline{font-size:16px;color:#cdbcf0;margin:2px 0 12px;}" +
    ".ctasub{display:block;font-size:14px;color:#cdbcf0;margin-top:10px;}" +
    ".quickcard .qmats{margin:12px 0;}" +
    ".pinline a{color:#ff8c1a;font-weight:700;}" +
    ".splitpartner-line{font-size:15px;color:#cdbcf0;margin:6px 0 0;}" +
    ".safesrc{font-size:14px;color:#cdbcf0;}" +
    ".rbanner{background:#2a1c52;border:1px solid #4b3486;border-radius:14px;padding:16px 16px 18px;margin:0 0 18px;}" +
    ".rbanner-line{font-size:17px;font-weight:700;color:#fdf3e3;margin:0 0 6px;line-height:1.4;}" +
    ".rbanner-sub{font-size:15px;color:#cdbcf0;margin:0 0 14px;line-height:1.45;}" +
    ".rbanner .cta{margin:0;}" +
    ".splitwrap{margin:18px 0;padding:16px;border:1px dashed #4b3486;border-radius:14px;background:#211540;}" +
    ".splitwrap .splitopen{width:100%%;}" +
    ".splitq{font-size:16px;font-weight:700;margin:0 0 8px;}" +
    ".splitstepper{display:flex;align-items:center;gap:14px;margin:0 0 12px;}" +
    ".splitstepper .ghost{margin:0;}" +
    ".splitcount{font-size:20px;font-weight:700;min-width:24px;text-align:center;}" +
    ".splitnamein{display:block;width:100%%;box-sizing:border-box;font-size:16px;padding:10px 12px;margin:0 0 8px;border:1px solid #4b3486;border-radius:10px;background:#160d28;color:#fdf3e3;}" +
    ".splitresult{margin-top:12px;}" +
    ".splitres-head{font-size:16px;font-weight:700;margin:0 0 8px;}" +
    ".splitres-list{font-size:15px;}" +
    ".splitnote{font-size:14px;color:#cdbcf0;}" +
    ".splitnames{margin:10px 0;}" +
    ".splitname{display:inline-block;margin:0 8px 8px 0;padding:10px 16px;font-size:16px;font-weight:700;border-radius:999px;border:1px solid #ff8c1a;background:#2a1c52;color:#ff8c1a;cursor:pointer;}" +
    ".splitmine-head{font-size:16px;font-weight:700;margin:12px 0 6px;}" +
    ".splititems{font-size:16px;}" +
    ".splititems-empty{font-size:15px;color:#cdbcf0;}" +
    ".madeit-line{font-size:16px;color:#cdbcf0;margin:0 0 14px;line-height:1.55;}" +
    ".rellist{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:8px;}" +
    ".rellist li{margin:0;}" +
    ".rellist a{display:inline-block;padding:8px 14px;border:1px solid #4b3486;border-radius:999px;color:#ff8c1a;text-decoration:none;font-size:15px;font-weight:600;}" +
    /* 2026-10-01 (Billy): related thumbnail cards. Overrides the pill link
       above: thumb + title side by side. */
    ".relcard a{display:flex;align-items:center;gap:10px;padding:8px 14px 8px 8px;}" +
    ".relcard img{width:56px;height:56px;object-fit:cover;border-radius:8px;flex:none;}" +
    /* 2026-10-01 (Billy): pictured honesty caption -- same type scale as the
       in-app ideaMedia caption. */
    ".pictured{font-size:11px;color:#9a8fb8;margin:-8px 0 12px;}" +
    ".crumb{font-size:13px;color:#cdbcf0;margin:0 0 8px;}" +
    ".crumb a{color:#ff8c1a;text-decoration:none;}" +
    ".foot{margin:40px 0 0;padding-top:18px;border-top:1px solid #4b3486;text-align:center;font-size:14px;color:#cdbcf0;}" +
    ".foot a{color:#ff8c1a;text-decoration:none;font-weight:700;}" +
    "</style>" +
    "<script>(function(){var s=document.createElement(\\"script\\");s.async=true;s.src=\\"https://us.i.posthog.com/static/array.js\\";s.onload=function(){try{if(window.posthog&&posthog.init){posthog.init(\\"phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7\\",{api_host:\\"https://us.i.posthog.com\\",autocapture:false,capture_pageview:false,disable_session_recording:true});}}catch(e){}};document.head.appendChild(s);document.addEventListener(\\"click\\",function(e){var t=e.target.closest&&e.target.closest(\\"[data-claude]\\");if(t&&window.posthog&&posthog.capture){try{posthog.capture(\\"add_to_claude_clicked\\",{source:\\"guide_page\\"});}catch(_){}}});})();</script>" +
    "</head><body><div class=\\"topbar\\"><a href=\\"/\\">🎃 Pick My <span>Costume</span></a><a class=\\"claudebtn\\" href=\\"https://pickmycostume.com/mcp\\" data-claude=\\"1\\">Add to Claude</a></div><main class=\\"guide\\">" +
    "<nav class=\\"crumb\\" aria-label=\\"Breadcrumb\\"><a href=\\"/\\">Home</a> &rsaquo; <a href=\\"/costumes\\">All costumes</a> &rsaquo; " + title + "</nav>" +
    "<h1>" + seoTitle + "</h1>" +
    _introHtml +
    _triple +
    _sharerLine +
    ((["little-witch","classic-ghost","glow-skeleton","fuzzy-monster","neon-demon-hunter","baby-dino","bumble-bee","walking-taco","blue-alien-ohana","emerald-witch"].indexOf(slug) >= 0) ? "<p class=\\"storyline\\"><a href=\\"/storytime?costume=" + slug + "\\">See this costume in a story</a></p>" : "") +
    "<p class=\\"ctawrap\\"><a class=\\"cta plancta\\" href=\\"" + targetAttr + "\\">" + _ctaLabel + "</a><span class=\\"ctasub\\">No signup \\u00b7 2 minutes.</span></p>" +
    "<img src=\\"" + img + "\\" alt=\\"" + imgAlt + "\\">" +
    /* 2026-09-30: AI honesty label, same wording as the quiz-results tag. */
    "<div class=\\"aiphoto\\">AI-generated concept photo</div>" +
    /* 2026-10-01 (Billy): pictured honesty caption under the hero photo --
       the same caption in-app ideaMedia renders. No pictured field = no
       caption. */
    (PICTURED[slug] ? "<p class=\\"pictured\\">" + esc(PICTURED[slug]) + "</p>" : "") +
    _cardsHtml + _cardsScript + _tipHtml + _fit + _noscriptMats +
    _splitHtml +
    "<h2>Steps</h2><ol class=\\"steps\\">" + _steps + "</ol>" +
    _plannerCtaHtml +
    _faqs +
    _relHtml +
    _matHtml +
    _splitPartnerHtml +
    /* "I made it" proof-photo block (novel-find 2026-09-26i, MakerWorld steal):
       gated on the IMADEIT one-line flag. The CTA deep-links into the app's
       idea page with ?madeit=1 so a later stream can wire a submission flow. */
    (IMADEIT ? "<h2>Wore this? Show us</h2>" +
    "<p class=\\"madeit-line\\">Made this costume? Your photo helps the next person see the real thing.</p>" +
    "<p class=\\"ctawrap\\"><a class=\\"cta\\" href=\\"" + (targetAttr + "&amp;madeit=1") + "\\">Share my costume photo</a></p>" : "") +
    "<p class=\\"quizline\\">Want one picked for you? <a href=\\"" + quizTargetAttr + "\\">Take the 2-minute quiz</a> - free, no signup.</p>" +
    "<p class=\\"pinline\\">Saving this idea? <a target=\\"_blank\\" rel=\\"noopener\\" href=\\"https://pinterest.com/pin/create/button/?url=" + encodeURIComponent("https://pickmycostume.com/c/" + slug) + "&amp;media=" + encodeURIComponent(img) + "&amp;description=" + encodeURIComponent(idea.t + " - DIY Halloween costume guide from Pick My Costume") + "\\">Pin it on Pinterest</a></p>" +
    "<footer class=\\"foot\\"><a href=\\"/\\">Pick My Costume</a> - Built with Muse.</footer>" +
    _bannerScript +
    _splitScript +
    _plannerGuardScript +
    "</main></body></html>";
  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "max-age=0, must-revalidate"
    }
  });
}
''' % (json.dumps(data), json.dumps(ALIASES), json.dumps(SPLIT_SLUGS), json.dumps(HALVES), json.dumps(ROLE_CARDS), json.dumps(RELATED),
       json.dumps(SEOTITLE), json.dumps(sorted(_UNIQUE_SIZING)), json.dumps(PRIMARYMAT), json.dumps(_MAT_REL_LABEL), json.dumps(MATRELATED), json.dumps(INTRO), json.dumps(SEALT), json.dumps(PICTURED),
       json.dumps(howto), json.dumps(_PANTRY_MATS), json.dumps(_PANTRY_LABELS), json.dumps(_PANTRY_EMOJI), json.dumps(_CLIENTJS), json.dumps(NOTFOUND_SRC),
       "true" if RECIPIENT_BANNER else "false", "true" if IMADEIT else "false")

out = os.path.join(ROOT, "functions", "c", "[slug].js")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(FN)
print("wrote %s (%d ideas)" % (out, len(data)))
