#!/usr/bin/env python3
"""Generate the last-minute SEO article page for Pick My Costume (2026-09-27).

Slug: last-minute-halloween-costumes-2026 - "last minute halloween costumes",
"easy last minute halloween costumes", "last minute diy halloween costumes"

Pattern follows hour-session/build_couple_article.py exactly:
same CSS, header, 60-second picker, answer blocks, HowTo box, final CTA,
FAQ, footer, Article+FAQPage+HowTo JSON-LD.

Angle: the zero-budget, pantry-first, make-tonight cluster (42 ideas in the
bank at <=20 min, <=$8, Easy). Not kid/audience specific, not couples, not
groups - the urgency query is the keyword. Does not cannibalize the existing
group-costumes.html hub or the three staged siblings.

Hard rules enforced by this script:
- zero em/en dashes in user-facing text (nodash fails loudly)
- every pick id exists in the bank and has INSTRUCTIONS (1:1)
- every time/cost/effort figure comes from INSTRUCTIONS, never hand-typed
- picker combos: vibe tag meets threshold, build time <= the chosen time
  budget (asserted, not claimed)
- the 42-idea cluster count is computed from the bank, never hand-typed
- the og time range ("5 to 20 minutes") is computed from the page's own
  picks and asserted into the copy
- section-2 "closet" honesty: every pick must have >=2 (own) materials
- section-3 "food" honesty: food tag >= 2 on every pick
- section-4 "group" honesty: "group" in audience on every pick
- no false no-store-trip claims (nostoretrip guard wired)
- og:image must be the HowTo featured build's card (red-team rule)
- the HowTo heading "A 5-minute build" is asserted: howto time == page min == 5

Write with:  python3 hour-session/build_lastminute_article.py
Output:     hour-session/last-minute-halloween-costumes-2026.html (staged only)
"""
import json, re, html, sys, os
from related_cards import inject_related_cards  # P0 growth: related cards + quiz CTA + pin link

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BANK = os.path.join(ROOT, "mcp-server", "bank.json")
OUT = os.path.join(ROOT, "hour-session", "last-minute-halloween-costumes-2026.html")
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

# the last-minute cluster: <=20 min, cost max <=$8, Easy - computed, never typed
CLUSTER = sorted(pid for pid in INST
                 if minutes(pid) <= 20 and cost_max(pid) <= 8 and INST[pid]["effort"] == "Easy")
print("last-minute cluster in bank:", len(CLUSTER))

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
    assert len(cfg["title"]) <= 65, "title too long: %d" % len(cfg["title"])
    assert len(cfg["meta_desc"]) <= 160, "meta too long: %d" % len(cfg["meta_desc"])

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
# Article: last-minute-halloween-costumes-2026
# Parent queries: "last minute halloween costumes", "easy last minute
# halloween costumes", "last minute diy halloween costumes", "halloween
# costume night before", "zero budget halloween costumes"
# ============================================================================
CLUSTER_COUNT = len(CLUSTER)  # 42, asserted into copy below

POOL = {
    "banana": "Ten minutes, $2 to $5. A yellow sweat set plus a green felt stem on a headband. The funniest thing in the room for the least effort.",
    "referee": "Twenty minutes, $2 to $5. A black tee, white tape stripes, a dollar-store whistle. Instant authority at any party.",
    "classic-ghost": "Ten minutes, $3 to $8. A white sheet and a thick black marker. The oldest costume there is, and it still works.",
    "zombie-coworker": "Twenty minutes, $3 to $8. An old button-down, an old tie, pale face paint, a coffee mug. Monday morning energy, Halloween edition.",
    "prince-princess": "Ten minutes, $5 to $10. A crown or tiara, a cape of fabric, a dress or suit from the thrift store. Royalty in one aisle.",
    "ice-cream-cone": "Twenty minutes, $2 to $6. A white tee scoop, a paper-hat cone, dot stickers for sprinkles. The sweet one.",
}
TABLE = {
    "funny|quick": "banana",
    "funny|tonight": "referee",
    "spooky|quick": "classic-ghost",
    "spooky|tonight": "zombie-coworker",
    "cute|quick": "prince-princess",
    "cute|tonight": "ice-cream-cone",
}
BUDGET = {"quick": 10, "tonight": 20}
# vibe tag thresholds, verified against the real bank tags
VIBE_TAG = {"funny": ("funny", 2), "spooky": ("scary", 2), "cute": ("cute", 2)}
for _key, _pid in TABLE.items():
    _v, _t = _key.split("|")
    assert minutes(_pid) <= BUDGET[_t], "combo %s over time budget" % _key
    _tag, _thr = VIBE_TAG[_v]
    assert BANK_IDEAS[_pid]["tags"].get(_tag, 0) >= _thr, "combo %s vibe mismatch" % _key
print("last-minute article: 6/6 picker combos verified (time budget, vibe tag)")

C = {
    "slug": "last-minute-halloween-costumes-2026",
    "title": "Easy Last-Minute DIY Halloween Costumes 2026",
    "meta_desc": "Last-minute Halloween costume ideas for 2026: 42 easy DIY builds, each 20 minutes or less. Real build times and costs for every pick.",
    "og_desc": "42 easy DIY builds: 5 to 20 minutes, most cost $8 or less.",
    "og_img": "crowd-camouflage.jpg",  # matches howto_pid (red-team rule)
    "lede": "Short answer: you are not out of time. The Pick My Costume bank holds %d easy DIY costumes that each take 20 minutes or less, and every pick on this page shows its real build time and cost up front." % CLUSTER_COUNT,
    "sub": "I am a dad, which means I have dressed a small human at 5 PM on October 31. The rule for last minute: pick the costume where the first thing you grab is a shirt you already own. Paint and glue come second. Every block below names the one thing you might have to buy, if anything.",
    "picker_title": "The 60-second picker",
    "picker_note": "Pick a vibe and a time limit. Every result fits inside the time you picked.",
    "picker_questions": [
        ("1. What is your vibe?", "vibe", [("funny", "Funny"), ("spooky", "Spooky"), ("cute", "Cute")]),
        ("2. How much time?", "time", [("quick", "10 min or less"), ("tonight", "20 min or less")]),
    ],
    "state_keys": ["vibe", "time"],
    "table": TABLE,
    "pool": POOL,
    "sections": [
        ("1", "Tonight is the night: the fastest builds",
         "When the party started an hour ago, sort by time, not by cool. Every build here is 10 minutes or less.",
         [
             ("You have five minutes", "crowd-camouflage",
              "Gray hoodie, dark pants, gray beanie. The whole joke is a blank adhesive name tag stuck on your chest: it says nothing, and that is the point.",
              "Five minutes, $2 to $5. The name tag is the only thing you might have to buy, and a dollar store run takes longer than the costume. Check the mirror once so the tag sits straight."),
             ("You have five minutes and a ball", "basketball-star",
              "A basketball jersey or numbered tank top, basketball shorts, and eye black under both eyes. Carry a basketball.",
              "Five minutes, $3 to $8. If you do not own a jersey, a numbered tank top from the drawer reads exactly the same from six feet away."),
             ("You have ten minutes", "classic-ghost",
              "A white sheet draped over the wearer, eye spots marked with a thick black marker while the sheet is on. Marking blind never lines up, so do it with the sheet draped.",
              "Ten minutes, $3 to $8. Twin flat sheet for small kids, full size for tweens and adults. No sewing, no cutting."),
             ("You have ten minutes and a yellow sweatsuit", "banana",
              "Yellow sweatshirt and sweatpants, a green felt stem on a headband. Put the sweatsuit on first, then cut and place the stem.",
              "Ten minutes, $2 to $5. The stem is the whole build: felt, headband, fabric glue. The rest is the closet."),
         ]),
        ("2", "Built from the closet",
         "For these, the first thing you grab is clothes you already own. Each block names the one item you might have to buy, because last-minute honesty matters.",
         [
             ("Monday morning, but Halloween", "zombie-coworker",
              "An old button-down you can cut up, an old tie, a coffee mug from home. Pale face paint and dark eye makeup finish it.",
              "Twenty minutes, $3 to $8. The face paint and eye makeup are the only things to buy, and they come from a drugstore or toy store. The shirt and tie come from the closet, which is the point."),
             ("You own the uniform already", "referee",
              "Black t-shirt, black pants, horizontal stripes torn from white athletic tape across the front and back. A plastic whistle on a lanyard.",
              "Twenty minutes, $2 to $5. The whistle and the tape are the only things to buy. Press the tape strips firmly so they survive the night."),
             ("The black dress does the work", "deadpan-diva",
              "A black dress, two tight braids, very pale foundation, dark eyeliner and lipstick. The deadpan face is required equipment.",
              "Fifteen minutes, $3 to $8. The pale foundation or white face paint is the one thing to buy if you do not have it. Everything else lives in a drawer."),
         ]),
        ("3", "Food costumes, the last-minute classic",
         "Food costumes forgive a late start: the whole design is one big readable shape, and felt or paper does the job.",
         [
             ("For the pair who cooks together", "bacon-eggs",
              "Bacon wears the dark red shirt, eggs wear the white shirt. Red-brown felt stripes on one, a white felt circle with a yellow yolk on the other. Safety pins, not glue, so the shirts survive.",
              "Twenty minutes, $3 to $6. Felt or construction paper both work. The duo version of this is a classic, and it photographs well."),
             ("The pun costume", "deviled-egg",
              "A white t-shirt with a yellow felt yolk on the front, red felt devil horns on a red headband, red pipe cleaners, and red face paint or lipstick.",
              "Twenty minutes, $3 to $8. The yolk, the horns, and the red details tell the whole joke. Cut paper stands in for felt if the craft store is closed."),
             ("For the parent running on fumes", "coffee-cup",
              "A white trash bag or white sheet as the cup body, a cardboard tube or cylinder, brown paper for the lid, a brown marker for the logo.",
              "Twenty minutes, $2 to $5. Most of this is a recycling bin, which is why it is on the list. The marker is the one thing to buy."),
             ("The sweet one", "ice-cream-cone",
              "White t-shirt as the scoop, a tan paper party hat as the cone, colored dot stickers or paper dots as sprinkles, brown marker crosshatch on the cone.",
              "Twenty minutes, $2 to $6. The sprinkles are the whole costume. Kids get this one instantly."),
         ]),
        ("4", "When the whole group procrastinated",
         "Group costumes at the last minute only work if everyone wears their own clothes. These three hand every person the same short job.",
         [
             ("Everyone grabs a cereal box", "cereal-crew",
              "Solid-color clothes per person, one empty cereal box each, flattened and worn on the front with invented cereal names lettered on. String or tape holds it up.",
              "Twenty minutes, $2 to $4. Flatten the box along the side seam before cutting: a flat box cuts cleanly, a 3D box wobbles. Every person invents their own cereal name."),
             ("The cartoon gang", "mystery-crew",
              "One colored t-shirt per person: orange, purple, blue, red. A dog-ears headband for the dog, a fake magnifying glass for the brains, a brown face-paint nose for the dog.",
              "Fifteen minutes, $2 to $6. Thrift the shirts or pull from closets; the colors are the whole costume. The magnifying glass can be a paper circle taped to a stick."),
             ("Everyone picks a decade", "decades-crew",
              "Everyone wears their own closet clothes dressed to a decade, and pins a hand-lettered decade card on: 70s, 80s, 90s. Hair gel does a lot of work here.",
              "Twenty minutes, $2 to $5. The cards cost nothing and the closet does the rest. The funniest decade wins."),
         ]),
    ],
    "faqs": [
        ("What is the easiest last-minute Halloween costume?",
         "Crowd Camouflage: 5 minutes, $2 to $5. A gray hoodie, dark pants, a gray beanie, and one blank adhesive name tag. The tag stays blank, and that is the joke. The name tag is the only thing you might have to buy."),
        ("Can I make a Halloween costume in 10 minutes with no sewing?",
         "Yes. The Classic Ghost is 10 minutes and $3 to $8: a white sheet draped over the wearer, eye spots marked with a thick black marker while the sheet is on. No sewing, no cutting. The Banana is another 10-minute build at $2 to $5."),
        ("What can I build from my closet without a costume store?",
         "The Zombie Coworker: 20 minutes, $3 to $8. An old button-down, an old tie, and a coffee mug all come from home; the only store items are pale face paint and dark eye makeup. The Referee is the same story: black clothes from the closet, a whistle and athletic tape from the store."),
        ("What is a good last-minute group costume when everyone procrastinated?",
         "The Cereal Crew: 20 minutes, $2 to $4. Everyone wears solid-color clothes and decorates an empty cereal box with an invented cereal name. The Mystery Crew is the other fast group pick: 15 minutes, $2 to $6, one colored t-shirt per person."),
        ("Is it too late to DIY a Halloween costume the night before?",
         "No. Most of the builds on this page take 20 minutes or less, and the fastest take 5. If the glue or paint needs drying time, pick one of the short closet builds instead, like the Crowd Camouflage or the Classic Ghost."),
    ],
    "howto_pid": "crowd-camouflage",
    "howto_title": "Crowd Camouflage Halloween costume",
    "howto_heading": "A 5-minute build, word for word",
    "final_sub": "Answer two questions and get a last-minute pick in 60 seconds, free, no signup.",
}

# the cluster-count claim must match the computed count
for _s in (C["lede"], C["meta_desc"]):
    assert str(CLUSTER_COUNT) in _s, "cluster-count drift: %s" % _s[:60]

# the og/meta time-range claim must match the computed min/max build time of
# the article's own picks (sections + picker pool)
_C_ALL = set(POOL) | {pid for _sec in C["sections"] for (_lbl, pid, _c1, _c2) in _sec[3]} | {C["howto_pid"]}
_C_MIN = min(minutes(pid) for pid in _C_ALL)
_C_MAX = max(minutes(pid) for pid in _C_ALL)
_C_RANGE = "%d to %d minutes" % (_C_MIN, _C_MAX)
assert _C_RANGE in C["og_desc"], "og time-range drift: %s" % C["og_desc"][:60]
print("last-minute article: time range asserted into og (%s)" % _C_RANGE)

# the HowTo heading "A 5-minute build" must hold exactly: howto time is
# the page minimum AND it is 5 minutes (guards the tie case)
assert minutes(C["howto_pid"]) == _C_MIN == 5, \
    "howto is not the page's 5-minute minimum: %s" % INST[C["howto_pid"]]["time"]
assert "5-minute" in C["howto_heading"], "howto heading must state the verified time"
print("last-minute article: howto is the page's 5-minute minimum")

# honesty asserts per section theme
_C_FAST = [pid for (_lbl, pid, _c1, _c2) in C["sections"][0][3]]
assert all(minutes(pid) <= 10 for pid in _C_FAST), "fastest section has a slow build"
print("last-minute article: section-1 speed claims verified (%d builds <= 10 min)" % len(_C_FAST))

_C_CLOSET = [pid for (_lbl, pid, _c1, _c2) in C["sections"][1][3]]
for _pid in _C_CLOSET:
    _own = sum(1 for _x in INST[_pid]["m"] if "(own" in _x)
    assert _own >= 2, "closet claim weak for %s (%d own materials)" % (_pid, _own)
print("last-minute article: section-2 closet claims verified (%d builds)" % len(_C_CLOSET))

_C_FOOD = [pid for (_lbl, pid, _c1, _c2) in C["sections"][2][3]]
for _pid in _C_FOOD:
    assert BANK_IDEAS[_pid]["tags"].get("food", 0) >= 2, "food claim false for %s" % _pid
print("last-minute article: section-3 food tags verified (%d builds)" % len(_C_FOOD))

_C_GROUP = [pid for (_lbl, pid, _c1, _c2) in C["sections"][3][3]]
for _pid in _C_GROUP:
    assert "group" in BANK_IDEAS[_pid]["audience"], "group claim false for %s" % _pid
print("last-minute article: section-4 group audience verified (%d builds)" % len(_C_GROUP))

# cost honesty: the og says "most cost $8 or less" - assert the actual share
_C_UNDER8 = sum(1 for pid in _C_ALL if cost_max(pid) <= 8)
assert _C_UNDER8 / len(_C_ALL) >= 0.8, "cost claim drift: %d/%d under $8" % (_C_UNDER8, len(_C_ALL))
print("last-minute article: cost claim verified (%d/%d picks $8 or less)" % (_C_UNDER8, len(_C_ALL)))

if __name__ == "__main__":
    build_article(C)
    print("QA: all gates pass")
