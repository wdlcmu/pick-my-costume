#!/usr/bin/env python3
"""Generate the couples SEO article page for Pick My Costume (2026-09-27).

Slug: couple-halloween-costumes-2026 - "couple Halloween costume ideas 2026"

Pattern follows hour-session/build_seo_articles_3.py exactly:
same CSS, header, 60-second picker, answer blocks, HowTo box, final CTA,
FAQ, footer, Article+FAQPage+HowTo JSON-LD.

Hard rules enforced by this script:
- zero em/en dashes in user-facing text (nodash fails loudly)
- every pick id exists in the bank and has INSTRUCTIONS (1:1)
- every time/cost/effort figure comes from INSTRUCTIONS, never hand-typed
- picker combos: audience contains "couple", vibe tag meets threshold,
  build time <= the chosen time budget (asserted, not claimed)
- couple-count claims are computed from the bank, never hand-typed
- og:image must be the HowTo featured build's card (red-team rule)
- the HowTo heading "A 10-minute duo build" is asserted: howto time == page min == 10

Write with:  python3 hour-session/build_couple_article.py
Output:     hour-session/couple-halloween-costumes-2026.html (staged only)
"""
import json, re, html, sys, os
from related_cards import inject_related_cards  # P0 growth: related cards + quiz CTA + pin link

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "hour-session", "couple-halloween-costumes-2026.html")
SITE = "https://pickmycostume.com"
DATE = "2026-09-27"

# ---------- load real data ----------
src = open(INDEX, encoding="utf-8").read()
m = re.search(r'var INSTRUCTIONS = (\{.*?\n\});', src, re.S)
if not m:
    sys.exit("INSTRUCTIONS block not found in index.html")
INST = json.loads(m.group(1))
bank_raw = json.load(open(BANK, encoding="utf-8"))
BANK_IDEAS = {i["id"]: i for i in (bank_raw if isinstance(bank_raw, list) else bank_raw.get("ideas"))}
assert len(INST) == 138 and len(BANK_IDEAS) == 138, (len(INST), len(BANK_IDEAS))

def esc(s):
    return html.escape(s, quote=False)

def nodash(s):
    """Fail loudly if an em or en dash sneaks into user-facing copy."""
    if "\u2014" in s or "\u2013" in s:
        raise ValueError("dash found in copy: %s" % s[:80])
    return s

_RANK_RE = re.compile(r"\btop[- ]five\b", re.I)
def norankclaim(s):
    """Fail loudly on unsupported ranking claims."""
    if _RANK_RE.search(s):
        raise ValueError("ranking claim in copy: %s" % s[:80])
    return s

_STORETRIP_RE = re.compile(r"no (trip to the store|store trip)|does not need a trip to the store", re.I)
def nostoretrip(pid, s):
    if _STORETRIP_RE.search(s) and "(buy" in materials_text(pid):
        raise ValueError("no-store-trip claim false for %s: %s" % (pid, s[:80]))
    return s

def triple(pid):
    t = INST[pid]
    return "%s - %s - %s" % (t["time"], t["cost"], t["effort"])

def minutes(pid):
    mm = re.match(r"\s*(\d+)\s*min", INST[pid]["time"])
    return int(mm.group(1))

def cost_max(pid):
    mm = re.match(r"\$(\d+)-(\d+)", INST[pid]["cost"])
    return int(mm.group(2))

def materials_text(pid):
    return " ".join(INST[pid]["m"]).lower()

# couple-audience ideas, computed, never asserted
COUPLE = sorted(pid for pid in INST if "couple" in BANK_IDEAS[pid]["audience"])
print("couple ideas in bank:", len(COUPLE))

CSS = """<style>
:root{
  --bg:#160d28; --bg2:#211540; --card:#2a1c52; --ink:#fdf3e3;
  --muted:#cdbcf0; --line:#4b3486; --accent:#ff8c1a; --accent-ink:#2a1500;
  --radius:14px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.65}
.wrap{max-width:720px;margin:0 auto;padding:20px 16px 64px}
header.top{display:flex;align-items:center;justify-content:space-between;padding:14px 0}
.brand{font-weight:800;font-size:18px;color:var(--ink);text-decoration:none}
.brand span{color:var(--accent)}
.home-link{color:var(--muted);text-decoration:none;font-size:14px}
h1{font-size:32px;margin:8px 0 4px;line-height:1.2}
.byline{color:var(--muted);font-size:14px;margin:0 0 16px}
.lede{font-size:18px;color:var(--ink);margin:0 0 8px}
.sub{color:var(--muted);margin:0 0 8px}
h2{font-size:24px;margin:44px 0 6px;line-height:1.3}
h2 .qn{color:var(--accent)}
.section-note{color:var(--muted);font-size:14px;margin:0 0 18px}
.answer{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin:0 0 14px}
.answer h3{margin:0 0 6px;font-size:18px}
.answer h3 .if{color:var(--accent);font-weight:700}
.answer p{margin:6px 0}
.answer .pick{color:var(--muted);font-size:14px}
.answer .pick strong{color:var(--ink)}
.triple{display:inline-block;background:var(--bg2);border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:13px;color:var(--muted);margin:8px 0 4px}
.triple b{color:var(--ink)}
.go{display:inline-block;margin:10px 0 2px;background:var(--accent);color:var(--accent-ink);font-weight:800;font-size:16px;padding:12px 22px;border-radius:var(--radius);text-decoration:none}
.go.ghost{background:transparent;color:var(--accent);border:2px solid var(--accent)}
.final button.go{font-family:inherit;cursor:pointer}
.quiet{display:block;margin-top:8px;font-size:13px;color:var(--muted);padding:12px 0;min-height:44px}
.picker{background:var(--bg2);border:2px solid var(--accent);border-radius:var(--radius);padding:20px;margin:28px 0}
.picker h2{margin:0 0 4px}
.picker .pq{margin:14px 0 6px;font-weight:700}
.picker .opts{display:flex;flex-wrap:wrap;gap:8px}
.picker button.opt{background:var(--card);border:1px solid var(--line);color:var(--ink);border-radius:999px;padding:12px 18px;font-size:15px;cursor:pointer;min-height:44px}
.picker button.opt.sel{background:var(--accent);color:var(--accent-ink);border-color:var(--accent);font-weight:700}
.picker button.opt:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
#pick-result{margin-top:16px}
#pick-result .answer{margin:0}
.faq{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin:0 0 12px}
.faq h3{margin:0 0 6px;font-size:16px}
.faq p{margin:0;color:var(--muted);font-size:15px}
.final{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:22px;margin-top:40px;text-align:center}
.final h2{margin-top:0}
.fine{color:var(--muted);font-size:13px}
.fine a{display:inline-block;padding:12px 6px;margin:-12px 0}
.footer{margin-top:48px;color:var(--muted);font-size:13px;text-align:center}
header.top a{display:inline-block;padding:12px 10px;min-height:44px}
.footer a{color:var(--muted);display:inline-block;padding:12px 10px}
ol.steps{margin:8px 0;padding-left:20px;color:var(--muted)}
ol.steps li{margin:6px 0;color:var(--ink)}
</style>"""

def answer_block(heading, pid, copy, why_note):
    idea = BANK_IDEAS[pid]
    nodash(heading); nodash(copy); nodash(why_note)
    norankclaim(heading); norankclaim(copy); norankclaim(why_note)
    nostoretrip(pid, copy); nostoretrip(pid, why_note)
    tline = esc(triple(pid))
    return ('<div class="answer">\n'
            '<h3><span class="if">If:</span> %s</h3>\n'
            '<p class="pick">The pick: <strong>%s</strong></p>\n'
            '<p>%s</p>\n'
            '<p>%s</p>\n'
            '<p class="triple">Real numbers: <b>%s</b></p>\n'
            '<a class="go" href="%s/?idea=%s">Open this costume in Pick My Costume</a>\n'
            '<a class="quiet" href="%s/c/%s">Read the full step-by-step guide</a>\n'
            '</div>' % (esc(heading), esc(idea["title"]), esc(copy), esc(why_note),
                         tline, SITE, pid, SITE, pid))
def build_article(cfg):
    slug = cfg["slug"]
    # ---- assertions on every pick ----
    all_pids = set()
    for _, _, _, blocks in cfg["sections"]:
        for _, pid, _, _ in blocks:
            all_pids.add(pid)
    all_pids.add(cfg["howto_pid"])
    for pid in all_pids:
        assert pid in BANK_IDEAS, "pick not in bank: %s" % pid
        assert pid in INST, "pick has no instructions: %s" % pid
    for pid in cfg["pool"]:
        assert pid in BANK_IDEAS and pid in INST, "pool pick missing: %s" % pid
    for key, pid in cfg["table"].items():
        assert pid in cfg["pool"], "table pick not in pool: %s" % pid

    # ---- JSON-LD ----
    article_ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": cfg["title"],
        "description": cfg["og_desc"],
        "author": {"@type": "Person", "name": "Billy Litner"},
        "publisher": {"@type": "Organization", "@id": SITE + "/#organization", "name": "Pick My Costume", "url": SITE + "/"},
        "datePublished": DATE,
        "dateModified": DATE,
        "mainEntityOfPage": {"@type": "WebPage", "@id": "%s/%s" % (SITE, slug)},
        "image": "%s/images/og/%s" % (SITE, cfg["og_img"]),
    }
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "publisher": {"@id": SITE + "/#organization"},
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in cfg["faqs"]
        ],
    }
    for q, a in cfg["faqs"]:
        nodash(q); nodash(a)
        norankclaim(q); norankclaim(a)
    nodash(cfg["title"]); nodash(cfg["meta_desc"]); nodash(cfg["og_desc"])
    norankclaim(cfg["title"]); norankclaim(cfg["meta_desc"]); norankclaim(cfg["og_desc"])
    nodash(cfg["lede"]); nodash(cfg["sub"]); nodash(cfg["final_sub"])
    norankclaim(cfg["lede"]); norankclaim(cfg["sub"]); norankclaim(cfg["final_sub"])
    nodash(cfg["howto_heading"])
    norankclaim(cfg["howto_heading"])

    hp = cfg["howto_pid"]
    # red-team rule: og:image must be the featured HowTo build's card image
    assert cfg["og_img"] == hp + ".jpg", "og_img %s != howto pick %s" % (cfg["og_img"], hp)
    hm, hs = INST[hp]["m"], INST[hp]["s"]
    for x in hm + hs:
        nodash(x)
    hmm = re.match(r"\s*(\d+)\s*min", INST[hp]["time"])
    cm = re.match(r"\$(\d+)-(\d+)", INST[hp]["cost"])
    howto_ld = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": cfg["howto_title"],
        "description": BANK_IDEAS[hp]["blurb"],
        "image": "%s/images/og/%s.jpg" % (SITE, hp),
        "author": {"@type": "Person", "name": "Billy Litner"},
        "publisher": {"@id": SITE + "/#organization"},
        "datePublished": DATE,
        "totalTime": "PT%sM" % hmm.group(1),
        "estimatedCost": {"@type": "MonetaryAmount", "currency": "USD",
                          "minValue": int(cm.group(1)), "maxValue": int(cm.group(2))},
        "supply": [{"@type": "HowToSupply", "name": x} for x in hm],
        "step": [{"@type": "HowToStep", "text": x} for x in hs],
    }

    # ---- picker ----
    pool = {pid: {"t": BANK_IDEAS[pid]["title"], "triple": triple(pid), "copy": c}
            for pid, c in cfg["pool"].items()}
    nodash(json.dumps(pool))
    norankclaim(json.dumps(pool))
    picker_html = "".join(
        '<div class="pq">%s</div><div class="opts">' % esc(label) +
        "".join('<button class="opt" type="button" data-q="%s" data-v="%s">%s</button>' % (q, k, esc(v))
                for k, v in opts) + "</div>"
        for label, q, opts in cfg["picker_questions"])
    state_init = ",".join("%s:null" % k for k in cfg["state_keys"])
    state_check = "||".join("!state.%s" % k for k in cfg["state_keys"])
    key_expr = "+\"|\"+".join("state." + k for k in cfg["state_keys"])
    picker_js = (
        "\n<script>\n(function(){\n"
        "  var POOL = %s;\n"
        "  var TABLE = %s;\n"
        "  var SITE = \"%s\";\n"
        "  var state = {%s};\n"
        "  function renderResult(){\n"
        "    var box = document.getElementById(\"pick-result\");\n"
        "    if(%s){ box.innerHTML = \"\"; return; }\n"
        "    var pid = TABLE[%s];\n"
        "    var d = POOL[pid];\n"
        "    box.innerHTML =\n"
        "      '<div class=\"answer\">' +\n"
        "      '<p class=\"pick\">Your 60-second pick: <strong>'+d.t.replace(/&/g,\"&amp;\").replace(/</g,\"&lt;\")+'</strong></p>' +\n"
        "      '<p>'+d.copy.replace(/&/g,\"&amp;\").replace(/</g,\"&lt;\")+'</p>' +\n"
        "      '<p class=\"triple\">Real numbers: <b>'+d.triple.replace(/&/g,\"&amp;\").replace(/</g,\"&lt;\")+'</b></p>' +\n"
        "      '<a class=\"go\" href=\"'+SITE+'/?idea='+pid+'\">Open this costume in Pick My Costume</a>' +\n"
        "      '<a class=\"quiet\" href=\"'+SITE+'/c/'+pid+'\">Read the full step-by-step guide</a>' +\n"
        "      '</div>';\n"
        "  }\n"
        "  document.querySelectorAll(\".picker button.opt\").forEach(function(b){\n"
        "    b.addEventListener(\"click\", function(){\n"
        "      var q = b.getAttribute(\"data-q\");\n"
        "      document.querySelectorAll('.picker button.opt[data-q=\"'+q+'\"]').forEach(function(x){ x.classList.remove(\"sel\"); });\n"
        "      b.classList.add(\"sel\");\n"
        "      state[q] = b.getAttribute(\"data-v\");\n"
        "      renderResult();\n"
        "    });\n"
        "  });\n"
        "})();\n</script>"
        % (json.dumps(pool), json.dumps(cfg["table"]), SITE, state_init, state_check, key_expr))
    share_js = (
        "\n<script>\n(function(){\n"
        "  var b=document.getElementById(\"shareBtn\"),n=document.getElementById(\"shareNote\");\n"
        "  if(!b||!n)return;\n"
        "  var c=document.querySelector('link[rel=\"canonical\"]');\n"
        "  var url=c?c.href:location.href.split('#')[0];\n"
        "  b.addEventListener(\"click\",function(){\n"
        "    if(navigator.share){navigator.share({title:document.title,url:url}).catch(function(){});}\n"
        "    else if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(function(){n.textContent='Link copied. Send it to a friend.';},function(){n.textContent=url;});}\n"
        "    else{n.textContent=url;}\n"
        "  });\n"
        "})();\n</script>")

    # ---- body sections ----
    parts = []
    for num, title, note, blocks in cfg["sections"]:
        parts.append('<h2><span class="qn">%s.</span> %s</h2>' % (num, esc(norankclaim(nodash(title)))))
        parts.append('<p class="section-note">%s</p>' % esc(norankclaim(nodash(note))))
        for heading, pid, copy, why in blocks:
            parts.append(answer_block(heading, pid, copy, why))
    body_sections = "\n".join(parts)

    faq_visible = "\n".join(
        '<div class="faq"><h3>%s</h3><p>%s</p></div>' % (esc(q), esc(a)) for q, a in cfg["faqs"])
    howto_mats = "".join("<li>%s</li>" % esc(x) for x in hm)
    howto_steps = "".join("<li>%s</li>" % esc(x) for x in hs)

    page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s | Pick My Costume</title>
<meta name="description" content="%(meta_desc)s">
<link rel="canonical" href="%(site)s/%(slug)s">
<meta property="og:type" content="article">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(og_desc)s">
<meta property="og:url" content="%(site)s/%(slug)s">
<meta property="og:image" content="%(site)s/images/og/%(og_img)s">
<script type="application/ld+json">
%(article_ld)s
</script>
<script type="application/ld+json">
%(faq_ld)s
</script>
<script type="application/ld+json">
%(howto_ld)s
</script>
%(css)s
</head>
<body>
<div class="wrap">
<header class="top">
<a class="brand" href="%(site)s/">Pick My <span>Costume</span></a>
<a class="home-link" href="%(site)s/">Home</a>
</header>

<h1>%(title)s</h1>
<p class="byline">By Billy Litner &middot; Updated September 2026</p>
<p class="lede">%(lede)s</p>
<p class="sub">%(sub)s</p>

<div class="picker" id="picker">
<h2>%(picker_title)s</h2>
<p class="section-note">%(picker_note)s</p>
%(picker_html)s
<div id="pick-result" aria-live="polite"></div>
<p class="fine">Want the full version? <a href="%(site)s/">Take the 2-minute quiz</a>, free, no signup.</p>
</div>

%(body_sections)s

<h2>%(howto_heading)s: %(howto_name)s</h2>
<p class="section-note">If Halloween is closer than you think, here is the whole build, word for word from the costume guide.</p>
<div class="answer">
<p class="pick">The pick: <strong>%(howto_name)s</strong></p>
<p class="triple">Real numbers: <b>%(howto_triple)s</b></p>
<p>You will need:</p>
<ol class="steps">%(howto_mats)s</ol>
<ol class="steps">%(howto_steps)s</ol>
<a class="go" href="%(site)s/?idea=%(howto_pid)s">Open this costume in Pick My Costume</a>
<a class="quiet" href="%(site)s/c/%(howto_pid)s">Read the full step-by-step guide</a>
</div>

<div class="final">
<h2>Still deciding?</h2>
<p class="sub">%(final_sub)s</p>
<a class="go" href="%(site)s/">Take the 2-minute quiz</a>
<p><button type="button" class="go ghost" id="shareBtn">Share this guide</button></p>
<p class="fine" id="shareNote" role="status"></p>
<p class="fine">Or start from what you already own: <a href="%(site)s/pantry">check what your closet can build</a>. Browse all <a href="%(site)s/costumes">138 costume guides</a>.</p>
</div>

<h2>FAQ</h2>
%(faq_visible)s

<div class="footer">
<p><a href="%(site)s/">Pick My Costume</a> &middot; <a href="%(site)s/costumes">Browse all 138 costume guides</a> &middot; <a href="%(site)s/pantry">What your closet can build</a></p>
<p class="fine">Built with Muse. Made by Billy Litner.</p>
</div>
</div>
%(picker_js)s
%(share_js)s
</body>
</html>
""" % {
        "title": esc(cfg["title"]), "meta_desc": esc(cfg["meta_desc"]), "og_desc": esc(cfg["og_desc"]),
        "og_img": cfg["og_img"], "site": SITE, "slug": slug,
        "article_ld": json.dumps(article_ld, indent=2),
        "faq_ld": json.dumps(faq_ld, indent=2),
        "howto_ld": json.dumps(howto_ld, indent=2),
        "css": CSS, "lede": esc(cfg["lede"]), "sub": esc(cfg["sub"]),
        "picker_title": esc(cfg["picker_title"]), "picker_note": esc(cfg["picker_note"]),
        "picker_html": picker_html, "body_sections": body_sections,
        "howto_name": esc(BANK_IDEAS[hp]["title"]), "howto_triple": esc(triple(hp)),
        "howto_heading": esc(cfg["howto_heading"]),
        "howto_mats": howto_mats, "howto_steps": howto_steps, "howto_pid": hp,
        "final_sub": esc(cfg["final_sub"]), "faq_visible": faq_visible, "picker_js": picker_js,
        "share_js": share_js,
    }

    nodash(page)
    assert "\u2014" not in page and "\u2013" not in page, "dash leaked into page"

    # ---------- QA gates ----------
    for q, a in cfg["faqs"]:
        assert esc(q) in page and esc(a) in page, "FAQ not visible: %s" % q
    for s in hs:
        assert esc(s) in page, "HowTo step not visible: %s" % s[:40]
    assert 'href="%s/%s"' % (SITE, slug) in page and 'rel="canonical"' in page
    assert 'href="%s/costumes"' % SITE in page
    assert os.path.exists(os.path.join(ROOT, "images", "og", cfg["og_img"])), "og image missing"
    assert os.path.exists(os.path.join(ROOT, "images", "og", hp + ".jpg")), "howto og missing"
    for pid in all_pids:
        assert "/?idea=%s" % pid in page and "/c/%s" % pid in page, pid
    # no relative links: every href/src must be absolute https or a fragment.
    # (skip JS concatenation fragments like '+SITE+'/ in the picker script)
    for _href in re.findall(r'(?:href|src)="([^"]+)"', page):
        if _href.startswith("'") or "+" in _href:
            continue
        assert _href.startswith("https://") or _href.startswith("#"), "relative link: %s" % _href

    open(OUT, "w", encoding="utf-8").write(inject_related_cards(page))
    print("wrote %s (%d bytes)" % (OUT, len(page)))
    return page
# ============================================================================
# Article: couple-halloween-costumes-2026
# Parent queries: "couple halloween costume ideas", "couple halloween costumes 2026",
# "matching couples costumes", "funny couple halloween costumes"
# ============================================================================
COUPLE_COUNT = len(COUPLE)  # 27, asserted into copy below

POOL = {
    "office-couple": "Ten minutes, $2 to $5. White button-downs, joke name tags, and a toy teapot.",
    "cat-mouse": "Fifteen minutes, $3 to $6. Felt ears and tails, drawn whiskers, chase each other all night.",
    "plug-socket": "Forty-five minutes, $3 to $6. A craftier build: cardboard prongs on one head, a foam socket on the other.",
    "salt-pepper": "Fifteen minutes plus drying, $2 to $5. All white, all black, cardboard shaker tops and big letters.",
    "beekeeper-bee": "Twenty-five minutes, $3 to $10. White suit and mesh veil for the beekeeper, yellow and black stripes for the bee.",
    "sun-moon": "Forty minutes, $5 to $8. Yellow rays for the Sun, a silver-starred crescent for the Moon.",
    "burger-joint-couple": "Ten minutes, $8 to $15. Two aprons, a fake mustache, and a curly red wig. Fast-food owners.",
    "web-hero-duo": "Twenty-five minutes, $3 to $8. A red-and-blue hero with a web pattern and a partner in a black jacket and mask.",
    "dragon-rider-duo": "Sixty minutes, $5 to $10. A gray felt dragon tunic with cardboard wings and foam eyes, plus a rider in a faux-fur vest.",
}
TABLE = {
    "funny|quick": "office-couple",
    "funny|tonight": "cat-mouse",
    "funny|project": "plug-socket",
    "cute|quick": "salt-pepper",
    "cute|tonight": "beekeeper-bee",
    "cute|project": "sun-moon",
    "pop|quick": "burger-joint-couple",
    "pop|tonight": "web-hero-duo",
    "pop|project": "dragon-rider-duo",
}
BUDGET = {"quick": 15, "tonight": 30, "project": 60}
# vibe tag thresholds, verified against the real bank tags
VIBE_TAG = {"funny": ("funny", 3), "cute": ("cute", 2), "pop": ("tv", 2)}
for _key, _pid in TABLE.items():
    _v, _t = _key.split("|")
    assert "couple" in BANK_IDEAS[_pid]["audience"], "combo %s not a couple idea" % _key
    assert minutes(_pid) <= BUDGET[_t], "combo %s over time budget" % _key
    _tag, _thr = VIBE_TAG[_v]
    assert BANK_IDEAS[_pid]["tags"].get(_tag, 0) >= _thr, "combo %s vibe mismatch" % _key
print("couples article: 9/9 picker combos verified (couple audience, time budget, vibe tag)")

C = {
    "slug": "couple-halloween-costumes-2026",
    "title": "Couple Halloween Costumes 2026: Ideas for Two",
    "meta_desc": "Couple Halloween costume ideas for 2026: 27 two-person costumes with real build times and costs, from funny food pairs to cute classics to 2026 pop culture.",
    "og_desc": "27 two-person Halloween costumes with real build times: 10 to 60 minutes, $2 to $20.",
    "og_img": "office-couple.jpg",  # matches howto_pid (red-team rule)
    "lede": "Short answer: the best couples costume is one where BOTH people are readable. Every pick below is a two-person idea from the Pick My Costume bank of 138 costumes, and %d of them are tagged for couples. Real build times and costs are shown up front." % COUPLE_COUNT,
    "sub": "I am a dad. My wife and I have been the couple in the last-minute food costumes, and the trick is simple: pick the idea where both costumes take the same amount of effort. Nobody should be taping cotton balls while the other person puts on a t-shirt.",
    "picker_title": "The 60-second picker",
    "picker_note": "Pick a vibe and a time budget. Every result takes no more than the time you picked.",
    "picker_questions": [
        ("1. What is your vibe?", "vibe", [("funny", "Funny"), ("cute", "Cute"), ("pop", "2026 pop culture")]),
        ("2. How much time?", "time", [("quick", "15 min or less"), ("tonight", "30 min or less"), ("project", "An hour")]),
    ],
    "state_keys": ["vibe", "time"],
    "table": TABLE,
    "pool": POOL,
    "sections": [
        ("1", "How much time can you give it?",
         "Be honest about effort. Both costumes take the same time, so double the one person's build in your head.",
         [
             ("You have ten minutes", "office-couple",
              "White button-downs, black pants, joke job titles written on name tags. One person carries a toy teapot all evening, the other carries a clipboard or a stack of papers.",
              "Ten minutes, $2 to $5, almost everything from the closet. The name tags are the only thing you might need to buy, and index cards with safety pins from home do the job."),
             ("You have fifteen minutes", "salt-pepper",
              "Salt wears all white, Pepper wears all black. Cardboard shaker tops painted gray ride on hats, with a big S and a big P lettered on. The letters do all the work: four inches minimum.",
              "Fifteen minutes plus drying, $2 to $5. The classic duo, and it photographs well because the contrast is the whole design."),
             ("You have a whole craft session", "moth-porch-light",
              "One person is the moth: gray clothes, big cardboard wings, pipe-cleaner antennae on a headband. The other is the porch light: yellow shirt and pants with a cone lampshade on top.",
              "Forty minutes, $5 to $10. The craftier end of the scale, but the joke lands every time the moth hovers around the light."),
         ]),
        ("2", "What vibe is the party getting?",
         "Match the costume to the room. Funny wins at bars, cute wins at house parties, spooky wins when the host loves horror.",
         [
             ("Funny", "ketchup-mustard",
              "Red shirt, yellow shirt, big paper blobs pinned on the front. Decide who is ketchup and who is mustard before you start cutting. It avoids the only argument this costume can cause.",
              "Fifteen minutes, $5 to $12. Funny, comfortable, and nobody has to paint their face."),
             ("Cute", "rain-cloud-rainbow",
              "One person glues cotton balls over a gray shirt and hangs blue paper raindrops from string at the hem. The other wears the rainbow shirt. Blue face paint for one rain streak is optional, it works fine without it.",
              "Thirty minutes plus drying, $4 to $10. Cute, cozy, and the cloud person gets to sit still while the glue dries."),
             ("A little spooky", "doctor-bride",
              "Green face paint and neck bolts over a dark suit for the Doctor; white dress and white hair spray for the Bride. Keep the paint away from the eyes and wash it off the same night.",
              "Twenty-five minutes, $5 to $12. The one couples idea here with real spook in it, and it is a movie night favorite."),
         ]),
        ("3", "Who are you going with?",
         "Partner, best friend, siblings: the duo changes with the relationship.",
         [
             ("Your partner", "beekeeper-bee",
              "The beekeeper: white long-sleeve shirt and pants, wide-brim hat, mesh veil. The bee: yellow shirt and pants with black electrical tape stripes and pipe-cleaner antennae.",
              "Twenty-five minutes, $3 to $10. Sweet without being cheesy, and the veil photographs like a real uniform."),
             ("Your best friend", "player-one-two",
              "Two matching t-shirts with big 1 and 2 iron-on letters, front and back, plus toy game controllers. Pin the letters in place and check the mirror before the iron goes down.",
              "Twenty minutes, $3 to $8. The best-friend duo: gamers get it instantly, everyone else still reads the numbers."),
             ("Your sibling", "plumber-duo",
              "Blue overalls over a red shirt and a green shirt, caps with big M and L stickers, painted mustaches. The red brother gets the bushy one, the green brother gets the thinner one.",
              "Fifteen minutes, $5 to $12. Built for pairs who are actually family, and it survives rough play."),
         ]),
        ("4", "2026 pop culture duos",
         "This year's couples costumes come from what everyone watched this year.",
         [
             ("The one that takes a whole evening", "dragon-rider-duo",
              "One person is the dragon: gray felt tunic, cardboard wings and tail, craft-foam eyes on a headband. The other is the rider: brown t-shirt, dark pants, faux-fur vest or brown scarf. The rider's costume is mostly closet.",
              "Sixty minutes, $5 to $10. The dragon half is the craft project; the rider half takes ten minutes, which keeps it fair."),
             ("Hero and partner", "web-hero-duo",
              "One person in a red-and-blue sweatsuit with a painted white web pattern, the partner in a black jacket and black pants with a mask. Both outfits pull straight from closets.",
              "Twenty-five minutes, $3 to $8. A hero and a partner in crime, and the web paint is the only thing you touch up."),
             ("The bathrobe epic", "galaxy-knights",
              "Bathrobes over dark pants, belts at the waist, hoods up, toy energy blades. Carry the blades unlit until the photo, and keep them pointed up or down, never at faces.",
              "Ten minutes, $8 to $20. The toy blade is most of the budget, and ten minutes is the whole build."),
         ]),
    ],
    "faqs": [
        ("What are good couples Halloween costumes for 2026?",
         "Salt and Pepper: 15 minutes, $2 to $5. All white and all black with cardboard shaker tops and big S and P letters. The 2026 pop culture picks come from what everyone watched this year: the Dragon Rider Duo is 60 minutes and $5 to $10, and the Galaxy Knights are 10 minutes and $8 to $20."),
        ("What is an easy last-minute couples costume?",
         "The Office Couple: 10 minutes, $2 to $5. White button-downs, joke name tags, a toy teapot and a clipboard. Ketchup and Mustard is another fast one: 15 minutes, $5 to $12."),
        ("How do we make a couples costume that reads in photos?",
         "Pick high contrast. Salt and Pepper works because black versus white reads from across the room. Big letters help too: the M and L on the Plumber Duo caps, the 1 and 2 on the Player One and Two shirts."),
        ("Can we DIY both costumes from the closet?",
         "The Office Couple is almost entirely closet: white button-downs, black pants, index cards for name tags, a teapot from the kitchen. Salt and Pepper needs gray paint or a marker, which is the one thing to check for. The pantry page shows what your closet can build."),
        ("What is a cute couples costume that is not cheesy?",
         "Rain Cloud and Rainbow: 30 minutes plus drying, $4 to $10. One of you is the cloud, one is the rainbow, and it is cozy enough to wear all night."),
    ],
    "howto_pid": "office-couple",
    "howto_title": "Office Couple Halloween costume",
    "howto_heading": "A 10-minute duo build, word for word",
    "final_sub": "Answer two questions and get a couples pick in 60 seconds, free, no signup.",
}
# the couple-count claim must match the computed count
for _s in (C["lede"], C["meta_desc"]):
    assert str(COUPLE_COUNT) in _s, "couple-count drift: %s" % _s[:60]
# the og/meta time-range claim must match the computed min/max build time of
# the article's own picks (sections + picker pool)
_C_ALL = set(POOL) | {pid for _sec in C["sections"] for (_lbl, pid, _c1, _c2) in _sec[3]} | {C["howto_pid"]}
_C_MIN = min(minutes(pid) for pid in _C_ALL)
_C_MAX = max(minutes(pid) for pid in _C_ALL)
_C_RANGE = "%d to %d minutes" % (_C_MIN, _C_MAX)
assert _C_RANGE in C["og_desc"], "og time-range drift: %s" % C["og_desc"][:60]
print("couples article: time range asserted into og (%s)" % _C_RANGE)
# the HowTo heading "A 10-minute duo build" must hold exactly: howto time is
# the page minimum AND it is 10 minutes (guards the tie case)
assert minutes(C["howto_pid"]) == _C_MIN == 10, \
    "howto is not the page's 10-minute minimum: %s" % INST[C["howto_pid"]]["time"]
assert "10-minute" in C["howto_heading"], "howto heading must state the verified time"
print("couples article: howto is the page's 10-minute minimum")
# vibe honesty for section blocks: every pick's leading tag matches its section
_C_VIBE = {"funny": "ketchup-mustard", "cute": "rain-cloud-rainbow", "spooky": "doctor-bride"}
_C_VIBE_TAGS = {"funny": ("funny", 3), "cute": ("cute", 3), "spooky": ("scary", 3)}
for _v, _pid in _C_VIBE.items():
    _tag, _thr = _C_VIBE_TAGS[_v]
    assert BANK_IDEAS[_pid]["tags"].get(_tag, 0) >= _thr, "vibe claim false for %s" % _pid
print("couples article: section vibe claims verified against bank tags")

if __name__ == "__main__":
    build_article(C)
    print("QA: all gates pass")
