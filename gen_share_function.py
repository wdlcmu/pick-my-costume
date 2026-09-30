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

src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
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
assert "This costume is still in the box" in NOTFOUND_SRC, \
    "404.html marker text changed: update the friendly-404 assert"

# Materials, numbered steps, decision triple (time/cost/effort), and FAQs per
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

// Per-idea guide data, embedded in the page: materials + numbered steps
// feed the schema.org HowTo JSON-LD in the head (honest structured data:
// each page's costume genuinely is a materials list plus steps); the
// decision triple (time/cost/effort) and the 2 parent FAQs are rendered as
// visible static HTML so AI assistants can quote them.
var HOWTO = %s;

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
  var _tripleText = (_hw && _hw.time && _hw.cost && _hw.effort) ?
    esc(_hw.time) + " · " + esc(_hw.cost) + " · " + esc(_hw.effort) + ". " : "";
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
    /* Estimated cost: bank stores "$3-10". Emit a USD MonetaryAmount
       range, same numbers as the visible triple. */
    var _cm = /^\\$(\\d+)-(\\d+)$/.exec(_hw.cost || "");
    /* Parse the dollar range as numbers: schema.org QuantitativeValue
       expects numeric minValue/maxValue. Same numbers as the visible
       decision triple. */
    if (_cm) _hld.estimatedCost = {"@type": "MonetaryAmount",
      "currency": "USD", "minValue": parseInt(_cm[1], 10),
      "maxValue": parseInt(_cm[2], 10)};
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
  var target = "/?" + _qp.toString();
  /* 2026-09-27 Billy: arrivals from the app\u2019s own rails (from=rail /
     from=hero) were invited to "Open this costume in Pick My Costume" --
     the app they just came from. In-app arrivals get a make-it label. */
  var _fromP = _qp.get("from") || "";
  var _ctaLabel = /^(rail|hero)/.test(_fromP) ? "Make this costume" : "Open this costume in Pick My Costume";
  var targetAttr = target.replace(/&/g, "&amp;");
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
  var _mats = "", _steps = "", _triple = "", _faqs = "", _quick = "", _fit = "", _sharerLine = "";
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
    _quick = "<p class=\\"qtriple\\">DIY this week: ~" + esc(_hw.cost) + ", " + esc(_hw.time) + "</p>" +
      "<ul class=\\"mats qmats\\">" + _mats + "</ul>" +
      (_qtip ? "<p class=\\"qtip\\">Tip: " + esc(_qtip) + "</p>" : "");
    /* Decision triple: the most quotable line of the guide, first under h1. */
    var _t = [_hw.time, _hw.cost, _hw.effort].filter(function(x){ return x; });
    if (_t.length) _triple = "<p class=\\"triple\\">" + _t.map(function(x){ return "<span class=\\"pill\\">" + esc(x) + "</span>"; }).join("") + "</p>";
    /* Sizing guidance: the fit note every parent asks about. */
    if (_hw.sizing) _fit = "<p class=\\"fit\\">Fit: " + esc(_hw.sizing) + "</p>";
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
  /* Related guides (SEO 2026-09-27): plain static anchors to kindred
     costumes. Same for every visitor and query string: not cloaking. */
  var _relHtml = "";
  var _rel = RELATED[slug] || [];
  if (_rel.length) {
    _relHtml = "<h2>More costumes like this</h2><ul class=\\"rellist\\">" +
      _rel.map(function(s){ return "<li><a href=\\"/c/" + s + "\\">" + esc(IDEAS[s].t) + "</a></li>"; }).join("") +
      "</ul>";
  }
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
    : title + " Costume: DIY Guide | Pick My Costume";
  var html = "<!DOCTYPE html>" +
    "<html lang=\\"en\\"><head><meta charset=\\"utf-8\\">" +
    "<title>" + title + " Costume: DIY Guide | Pick My Costume</title>" +
    "<link rel=\\"canonical\\" href=\\"https://pickmycostume.com/c/" + slug + "\\">" +
    "<meta name=\\"description\\" content=\\"" + _tripleText + blurb + "\\">" +
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
    "<meta property=\\"og:image:alt\\" content=\\"" + title + " costume idea\\">" +
    "<meta name=\\"twitter:card\\" content=\\"summary_large_image\\">" +
    "<meta name=\\"twitter:title\\" content=\\"" + _ogTitle + "\\">" +
    "<meta name=\\"twitter:description\\" content=\\"" + blurb + "\\">" +
    "<meta name=\\"twitter:image\\" content=\\"" + img + "\\">" +
    "<meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1\\">" +
    _ld +
    "<style>" +
    "body{font-family:-apple-system,system-ui,'Segoe UI',Roboto,sans-serif;margin:0;color:#1f1f1f;background:#fff;line-height:1.55;}" +
    ".topbar{background:#fff;border-bottom:1px solid #eee2d3;padding:10px 20px;position:sticky;top:0;z-index:5;}" +
    ".topbar a{color:#1f1f1f;text-decoration:none;font-weight:800;font-size:16px;}" +
    ".topbar a span{color:#ff8c1a;}" +
    ".guide{max-width:640px;margin:0 auto;padding:20px 20px 48px;}" +
    "h1{font-size:30px;margin:0 0 10px;letter-spacing:-0.01em;}" +
    ".triple{margin:0 0 10px;display:flex;flex-wrap:wrap;gap:8px;}" +
    ".pill{display:inline-block;background:#fff4e5;border:1px solid #ffd9a3;color:#8a4a0c;font-size:14px;font-weight:700;padding:5px 12px;border-radius:999px;}" +
    ".fit{font-size:15px;color:#444;margin:0 0 8px;}" +
    ".lede{font-size:17px;color:#444;margin:0;}" +
    "h2{font-size:22px;margin:32px 0 12px;letter-spacing:-0.01em;}" +
    ".quickcard{background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:16px 18px;margin:18px 0;}" +
    ".quickcard .qtriple{font-size:16px;font-weight:700;color:#222;margin:0 0 8px;}" +
    ".quickcard .qsteps{font-size:16px;line-height:1.5;padding-left:22px;margin:0;}" +
    ".quickcard .qsteps li{margin:8px 0;}" +
    ".quickcard .qtip{font-size:15px;color:#555;font-style:italic;margin:10px 0 0;}" +
    "details.faq{border:1px solid #e3ddd2;border-radius:10px;margin:8px 0;background:#faf8f4;}" +
    "details.faq summary{font-weight:700;font-size:16px;padding:12px 14px;cursor:pointer;list-style:none;}" +
    "details.faq summary::-webkit-details-marker{display:none;}" +
    "details.faq summary::before{content:'+ ';color:#b3540c;font-weight:700;}" +
    "details.faq[open] summary::before{content:'\\u2212 ';}" +
    "details.faq p{margin:0;padding:0 14px 12px;font-size:16px;line-height:1.55;}" +
    ".mats{list-style:none;padding:0;margin:0;background:#faf8f4;border:1px solid #eee2d3;border-radius:14px;padding:6px 18px;}" +
    ".mats li{margin:0;padding:10px 0 10px 28px;border-bottom:1px solid #f0e8da;position:relative;font-size:16px;}" +
    ".mats li:last-child{border-bottom:none;}" +
    ".mats li::before{content:'✓';position:absolute;left:2px;color:#b3540c;font-weight:700;}" +
    "ol.steps{list-style:none;counter-reset:step;padding:0;margin:0;}" +
    "ol.steps li{counter-increment:step;margin:0 0 4px;padding:10px 0 10px 44px;position:relative;font-size:16px;line-height:1.6;}" +
    "ol.steps li::before{content:counter(step);position:absolute;left:0;top:10px;width:30px;height:30px;border-radius:50%%;background:#ff8c1a;color:#fff;font-weight:800;font-size:15px;display:flex;align-items:center;justify-content:center;}" +
    ".ctawrap{margin:20px 0;}" +
    ".storyline{font-size:16px;margin:0 0 14px;color:#444;}" +
    ".storyline a{color:#b3541e;font-weight:700;text-decoration:none;}" +
    ".cta{display:inline-block;background:#ff8c1a;color:#fff;font-weight:700;padding:14px 22px;border-radius:12px;text-decoration:none;font-size:17px;}" +
    ".guide img{max-width:100%%;height:auto;border-radius:12px;margin:6px 0;}" +
    "ul,ol{font-size:16px;line-height:1.55;padding-left:22px;margin:0;}" +
    ".quizline{font-size:15px;color:#555;margin-top:26px;}" +
    ".quizline a{color:#ff8c1a;font-weight:700;}" +
    ".pinline{font-size:14px;color:#555;margin:10px 0 0;}" +
    ".sharerline{font-size:16px;color:#555;margin:2px 0 12px;}" +
    ".ctasub{display:block;font-size:14px;color:#777;margin-top:10px;}" +
    ".quickcard .qmats{margin:12px 0;}" +
    ".pinline a{color:#b3541e;font-weight:700;}" +
    ".splitpartner-line{font-size:15px;color:#555;margin:6px 0 0;}" +
    ".safesrc{font-size:14px;color:#777;}" +
    ".rbanner{background:#fff7ec;border:1px solid #ffd9a3;border-radius:14px;padding:16px 16px 18px;margin:0 0 18px;}" +
    ".rbanner-line{font-size:17px;font-weight:700;color:#333;margin:0 0 6px;line-height:1.4;}" +
    ".rbanner-sub{font-size:15px;color:#666;margin:0 0 14px;line-height:1.45;}" +
    ".rbanner .cta{margin:0;}" +
    ".splitwrap{margin:18px 0;padding:16px;border:1px dashed #e0a33e;border-radius:14px;background:#fffdf6;}" +
    ".splitwrap .splitopen{width:100%%;}" +
    ".splitq{font-size:16px;font-weight:700;margin:0 0 8px;}" +
    ".splitstepper{display:flex;align-items:center;gap:14px;margin:0 0 12px;}" +
    ".splitstepper .ghost{margin:0;}" +
    ".splitcount{font-size:20px;font-weight:700;min-width:24px;text-align:center;}" +
    ".splitnamein{display:block;width:100%%;box-sizing:border-box;font-size:16px;padding:10px 12px;margin:0 0 8px;border:1px solid #ddd;border-radius:10px;}" +
    ".splitresult{margin-top:12px;}" +
    ".splitres-head{font-size:16px;font-weight:700;margin:0 0 8px;}" +
    ".splitres-list{font-size:15px;}" +
    ".splitnote{font-size:14px;color:#777;}" +
    ".splitnames{margin:10px 0;}" +
    ".splitname{display:inline-block;margin:0 8px 8px 0;padding:10px 16px;font-size:16px;font-weight:700;border-radius:999px;border:1px solid #ff8c1a;background:#fff;color:#ff8c1a;cursor:pointer;}" +
    ".splitmine-head{font-size:16px;font-weight:700;margin:12px 0 6px;}" +
    ".splititems{font-size:16px;}" +
    ".splititems-empty{font-size:15px;color:#777;}" +
    ".madeit-line{font-size:16px;color:#444;margin:0 0 14px;line-height:1.55;}" +
    ".rellist{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:8px;}" +
    ".rellist li{margin:0;}" +
    ".rellist a{display:inline-block;padding:8px 14px;border:1px solid #e0a33e;border-radius:999px;color:#b3541e;text-decoration:none;font-size:15px;font-weight:600;}" +
    ".crumb{font-size:13px;color:#777;margin:0 0 8px;}" +
    ".crumb a{color:#b3541e;text-decoration:none;}" +
    ".foot{margin:40px 0 0;padding-top:18px;border-top:1px solid #eee2d3;text-align:center;font-size:14px;color:#888;}" +
    ".foot a{color:#b3541e;text-decoration:none;font-weight:700;}" +
    /* AI honesty label (2026-09-30): the quiz-results page tags concept
       photos "AI-generated concept photo"; the guide page shows the same AI
       photo (og card rendered from photos/<slug>.webp), so it carries the
       same tag with the same styling. */
    ".aiphoto{font-size:11px;color:#9a8fb8;margin:4px 0 12px;}" +
    "</style>" +
    "</head><body><div class=\\"topbar\\"><a href=\\"/\\">🎃 Pick My <span>Costume</span></a></div><main class=\\"guide\\">" +
    "<nav class=\\"crumb\\" aria-label=\\"Breadcrumb\\"><a href=\\"/\\">Home</a> &rsaquo; <a href=\\"/costumes\\">All costumes</a> &rsaquo; " + title + "</nav>" +
    "<h1>" + title + "</h1>" +
    _triple +
    _sharerLine +
    _fit +
    "<p class=\\"lede\\">" + blurb + "</p>" +
    ((["little-witch","classic-ghost","glow-skeleton","fuzzy-monster","neon-demon-hunter","baby-dino","bumble-bee","walking-taco","blue-alien-ohana","emerald-witch"].indexOf(slug) >= 0) ? "<p class=\\"storyline\\"><a href=\\"/storytime?costume=" + slug + "\\">See this costume in a story</a></p>" : "") +
    "<p class=\\"ctawrap\\"><a class=\\"cta\\" href=\\"" + targetAttr + "\\">" + _ctaLabel + "</a><span class=\\"ctasub\\">No signup \\u00b7 2 minutes.</span></p>" +
    "<img src=\\"" + img + "\\" alt=\\"" + title + " costume idea\\">" +
    /* 2026-09-30: AI honesty label, same wording as the quiz-results tag. */
    "<div class=\\"aiphoto\\">AI-generated concept photo</div>" +
    (_quick ? "<div class=\\"quickcard\\">" + _quick + "</div>" : "") +
    _splitHtml +
    "<h2>Steps</h2><ol class=\\"steps\\">" + _steps + "</ol>" +
    _faqs +
    _relHtml +
    _splitPartnerHtml +
    /* "I made it" proof-photo block (novel-find 2026-09-26i, MakerWorld steal):
       gated on the IMADEIT one-line flag. The CTA deep-links into the app's
       idea page with ?madeit=1 so a later stream can wire a submission flow. */
    (IMADEIT ? "<h2>Wore this? Show us</h2>" +
    "<p class=\\"madeit-line\\">Made this costume? Your photo helps the next person see the real thing.</p>" +
    "<p class=\\"ctawrap\\"><a class=\\"cta\\" href=\\"" + (targetAttr + "&amp;madeit=1") + "\\">Share my costume photo</a></p>" : "") +
    "<p class=\\"ctawrap\\"><a class=\\"cta\\" href=\\"" + targetAttr + "\\">" + _ctaLabel + "</a></p>" +
    "<p class=\\"quizline\\">Want one picked for you? <a href=\\"" + quizTargetAttr + "\\">Take the 2-minute quiz</a> - free, no signup.</p>" +
    "<p class=\\"pinline\\">Saving this idea? <a target=\\"_blank\\" rel=\\"noopener\\" href=\\"https://pinterest.com/pin/create/button/?url=" + encodeURIComponent("https://pickmycostume.com/c/" + slug) + "&amp;media=" + encodeURIComponent(img) + "&amp;description=" + encodeURIComponent(idea.t + " - DIY Halloween costume guide from Pick My Costume") + "\\">Pin it on Pinterest</a></p>" +
    "<footer class=\\"foot\\"><a href=\\"/\\">Pick My Costume</a> - Built with Muse.</footer>" +
    _bannerScript +
    _splitScript +
    "</main></body></html>";
  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}
''' % (json.dumps(data), json.dumps(ALIASES), json.dumps(SPLIT_SLUGS), json.dumps(HALVES), json.dumps(ROLE_CARDS), json.dumps(RELATED), json.dumps(howto), json.dumps(NOTFOUND_SRC),
       "true" if RECIPIENT_BANNER else "false", "true" if IMADEIT else "false")

out = os.path.join(ROOT, "functions", "c", "[slug].js")
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write(FN)
print("wrote %s (%d ideas)" % (out, len(data)))
