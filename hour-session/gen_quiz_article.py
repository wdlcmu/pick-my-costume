#!/usr/bin/env python3
"""Generate halloween-costume-ideas-2026.html (quiz-as-article SEO page).

Data comes only from the real bank: var IDEAS + var INSTRUCTIONS in app.js.
Self-contained: extracts directly from index.html, no caches needed.
Regenerate: python3 hour-session/gen_quiz_article.py
Output: repo root halloween-costume-ideas-2026.html (working tree only, no deploy)
"""
import json, html, re, os

REPO = os.path.expanduser('~/workspace/builds/pick-my-costume')

def js_to_python(src):
    """Transform a JS object/array literal into Python syntax (handles unquoted keys)."""
    out, i, n = [], 0, len(src)
    while i < n:
        ch = src[i]
        if ch in '"\'':
            q = ch
            j = i + 1
            while j < n:
                if src[j] == '\\':
                    j += 2
                    continue
                if src[j] == q:
                    break
                j += 1
            out.append(src[i:j + 1])
            i = j + 1
            continue
        if ch == '/' and i + 1 < n and src[i + 1] == '/':
            j = src.index('\n', i)
            i = j + 1
            continue
        # unquoted key: identifier followed by ':'
        m = re.match(r'[A-Za-z_$][A-Za-z0-9_$]*', src[i:])
        if m:
            word = m.group(0)
            j = i + len(word)
            k = j
            while k < n and src[k] in ' \t':
                k += 1
            if k < n and src[k] == ':':
                if word == 'true':
                    out.append('True')
                elif word == 'false':
                    out.append('False')
                elif word == 'null':
                    out.append('None')
                else:
                    out.append('"' + word + '"')
                i = j
                continue
            out.append({'true': 'True', 'false': 'False', 'null': 'None'}.get(word, word))
            i = j
            continue
        out.append(ch)
        i += 1
    return ''.join(out)

def extract_var(varname, html_text, opener):
    return eval(js_to_python(_extract_raw(varname, html_text, opener)))

def _extract_raw(varname, html_text, opener):
    marker = f'var {varname} = '
    start = html_text.index(marker) + len(marker)
    closer = ']' if opener == '[' else '}'
    depth, i, in_str = 0, start, None
    while True:
        ch = html_text[i]
        if in_str:
            if ch == '\\':
                i += 2
                continue
            if ch == in_str:
                in_str = None
        else:
            if ch in '"\'':
                in_str = ch
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    break
        i += 1
    return html_text[start:i + 1]
_html = open(os.path.join(REPO, 'app.js')).read()
_ide = extract_var('IDEAS', _html, '[')
_ins = extract_var('INSTRUCTIONS', _html, '{')
ideas = [{'id': x['id'], 'title': x['title'], 'blurb': x['blurb'], 'why': x['why'],
          'audience': x['audience'], 'budget': x['budget'], 'rank': x.get('rank'),
          'trending': bool(x.get('trending'))} for x in _ide]
plans = {k: {'effort': v.get('effort'), 'time': v.get('time')}
         for k, v in _ins.items()}
byid = {i['id']: i for i in ideas}
# 2026-10-22 reconciliation (Family C part 2): the live page's card
# blurb for this slug was scrubbed of its franchise name by hand;
# app.js still carries the old text. Live text verbatim (matches
# mcp-server/bank.json exactly, verified 2026-10-22). Do not undo.
# Deliberately NOT overridden: neon-demon-hunter and blue-alien-ohana,
# where the bank has moved AHEAD of the live page (wanted bank-ahead).
LIVE_BLURBS = {
    'emerald-witch': 'An all-green-everything gown, dramatic makeup, and a pointy hat gone couture.',
}
for _sid, _blurb in LIVE_BLURBS.items():
    assert _sid in byid, 'live blurb override for unknown idea %s' % _sid
    byid[_sid]['blurb'] = _blurb
esc = html.escape

SITE = 'https://pickmycostume.com'
SLUG = 'halloween-costume-ideas-2026'
# Byline is the live page's static text ("Updated September 2026"),
# ported 2026-10-22 (Family C reconciliation part 2). It no longer
# depends on the run date, so regens are deterministic.

def dash_free(s):
    # zero em/en dashes in user-facing text
    return s.replace('\u2014', ', ').replace('\u2013', ', ').replace('--', ', ')

def display_time(t):
    # 2026-10-22 display rule (Billy, 2026-10-03): displayed time is
    # hands-on only. The bank time may carry a "+ ... drying" suffix
    # that counts in Tonight scoring but is never displayed. Same
    # helper as gen_costumes_hub.py / gen_closet.py.
    return re.sub(r"\s*\+.*drying\s*$", "", t or "")

SECTIONS = [
    ('solo', 'Solo costumes', 'solo',
     'Going alone means the costume has to read instantly, with no context. These solo picks do that.',
     ['neon-demon-hunter', 'deadpan-diva', 'tin-hero', 'emerald-witch']),
    ('couples', 'Couple costumes', 'couple',
     'Couple costumes live or die on the contrast between the two halves. Pick a pair, not two solos.',
     ['cat-mouse', 'rain-cloud-rainbow', 'sun-moon', 'doctor-bride']),
    ('group', 'Group costumes', 'group',
     'Groups need a costume that scales: one base idea, room for everyone to be a little different.',
     ['gloom-bloom', 'safari-zoo-crew', 'good-witch-bad-witch', 'soccer-squad']),
    ('family', 'Family costumes', 'family',
     'The whole crew in one photo. These scale from two people to six without anyone feeling like filler.',
     ['blue-dog-family', 'superhero-family', 'blue-alien-ohana', 'little-pig-family']),
    ('kid', 'Kid costumes', 'kid',
     'Comfortable enough to wear all night, recognizable enough that the neighbors get it in one look.',
     ['classic-ghost', 'fuzzy-monster', 'pocket-plush', 'baby-dino']),
    ('last-minute', 'Last-minute costumes', 'lastminute',
     'It is the night of the party and you have nothing. These are the fastest builds on this page, straight from the guides.',
     ['classic-ghost', 'deadpan-diva', 'cat-mouse', 'gloom-bloom']),
]

TIERS = [
    ('tonight', 'Tonight ready',
     'Fifteen minutes or less, almost all from things you already own.',
     ['classic-ghost', 'deadpan-diva', 'cat-mouse', 'gloom-bloom']),
    ('evening', 'One evening project',
     'About half an hour at the kitchen table. These are the sweet spot: real costumes, one night of work.',
     ['neon-demon-hunter', 'tin-hero', 'blue-dog-family', 'superhero-family']),
    ('all-out', 'Go all out',
     'Forty five minutes to an hour. The builds that make people stop you for photos.',
     ['emerald-witch', 'spider', 'haunted-animatronics', 'dragon-rider-duo']),
]

def card(slug):
    i = byid[slug]; p = plans[slug]
    meta = f"Build: {esc(display_time(p['time']))} &middot; Effort: {esc(p['effort'])}"
    return f"""<article class="idea">
<img src="{SITE}/photos/{esc(slug)}.webp" alt="{esc(dash_free(i['title']))} costume concept photo" loading="lazy" width="300" height="300">
<div class="idea-body">
<h3>{esc(dash_free(i['title']))}</h3>
<p>{esc(dash_free(i['blurb']))}</p>
<p class="meta">{meta}</p>
<a class="go" href="/c/{esc(slug)}">Open this costume</a>
</div>
</article>"""

def tier_card(slug):
    i = byid[slug]; p = plans[slug]
    return f"""<a class="tier-pick" href="/c/{esc(slug)}">
<span class="tier-name">{esc(dash_free(i['title']))}</span>
<span class="tier-meta">{esc(display_time(p['time']))} &middot; {esc(p['effort'])} effort</span>
</a>"""

def section_cta():
    return f"""<div class="cta">
<p><strong>Not sure which one is you?</strong> <a href="{SITE}/">Take the 2-minute quiz</a> and get a personal pick, then tap <strong>Try it on</strong> on your result card to preview the costume on your own face. The photo never leaves your phone.</p>
</div>"""

sections_html = []
for anchor, title, _aud, note, slugs in SECTIONS:
    cards = '\n'.join(card(s) for s in slugs)
    sections_html.append(f"""<section id="{anchor}">
<h2>{title}</h2>
<p class="section-note">{note}</p>
{cards}
{section_cta()}
</section>""")

tiers_html = []
for anchor, title, note, slugs in TIERS:
    picks = '\n'.join(tier_card(s) for s in slugs)
    tiers_html.append(f"""<div class="tier">
<h3>{title}</h3>
<p class="section-note">{note}</p>
{picks}
</div>""")

howto_steps = [
    "Pick two or three costumes from the lists above, or take the 2-minute quiz and get a personal pick.",
    "On your result card, tap Try it on.",
    "Upload a front-facing photo. The photo never leaves your phone: the preview runs on your device.",
    "Compare the previews and go with the one you would actually wear out the door, not the one that looked best in your head.",
]

# ---------- FAQ data, computed from the actual page picks (never hard-coded) ----------
# 2026-10-22: the bank dropped its cost field on 2026-10-01, so the FAQ
# answers below are computed from build time and effort only. No dollar
# figures are stated anywhere on this page; every guide lists its own
# materials, and the cost question is answered on that basis.
def _faq_title(s):
    return dash_free(byid[s]['title']).replace(' & ', ' and ')
def _approx_time(time):
    t = display_time(time).replace('min', 'minutes')
    if t == '1 hr':
        return 'about an hour'
    if t == '1.5 hrs':
        return 'about an hour and a half'
    return 'about ' + t
def _mins(time):
    return int(re.search(r'(\d+)\s*min', time).group(1))
def _pw(slug):
    # Live text (ported 2026-10-22) shows time only in these parentheses.
    p = plans[slug]
    return f"{_faq_title(slug)} ({_approx_time(p['time'])})"
# 2026-10-22 reconciliation part 2: the three answers below are the
# live page's hand-written texts, ported verbatim (the computed versions
# they replace read differently). WART KEPT FOR PARITY: the last-minute
# answer's "takes about 10 minutes of materials" is the live page's
# broken sentence, kept byte-exact like the part-1 spacing warts; fixing
# it is a deploy-time copy decision for the parent, not this port.
_cost_faq_a = (
    "Every guide on this page lists its real materials, closet items "
    "first. The simplest picks need nothing beyond what is already in "
    "the house (Soccer Squad, Superhero Family). Most builds take under "
    "an hour, and every guide shows the full shopping list before you "
    "start.")
_last_minute_a = (
    "The Classic Ghost takes about 10 minutes of materials. Cat and "
    "Mouse takes about 15 minutes. The Deadpan Diva takes about 15 "
    "minutes. All three read instantly at any party.")
_couple_a = (
    "Pick a pair with built-in contrast: "
    f"{_pw('cat-mouse')}, {_pw('sun-moon')}, {_pw('doctor-bride')}, "
    f"or {_pw('rain-cloud-rainbow')}.")
_fam_slugs = ['blue-dog-family', 'superhero-family', 'blue-alien-ohana', 'little-pig-family']
_fam_names = ", ".join(_faq_title(s) for s in _fam_slugs)
_family_a = (
    f"The {_fam_names} all work from toddlers to grown-ups. "
    # Live hand text ported verbatim 2026-10-22 (it is looser than the
    # bank's 25-30 min range; flagged in the part-2 report, not decided).
    "Build times run about half an hour to an hour, and every guide "
    "lists what you already own first.")

faq = [
    ("What should I be for Halloween 2026?",
     "Start with your Halloween night, not your personality. Pick your effort level above, then your section: solo, couple, group, family, kid, or last minute. Every pick below shows its real build time and materials list from the costume guide. Still torn? Take the 2-minute quiz and get one personal pick."),
    ("What are the most popular Halloween costumes for 2026?",
     "The year's breakout is the Neon Demon Hunter. Witches are a top pick for adults this year, from the Emerald Witch to the Good Witch, Bad Witch duo. For kids, princesses and the spider hero lead the list, and the Classic Ghost remains a perennial favorite."),
    ("How do I see what a costume looks like on me before I buy or build it?",
     "Open any costume, or take the 2-minute quiz to get a personal pick, then tap Try it on on the result card and upload a front-facing photo. The preview runs on your device and the photo never leaves your phone. Try two or three and commit to the one you would actually wear out the door."),
    ("What is an easy last-minute Halloween costume?",
     _last_minute_a),
    ("How much does a DIY Halloween costume cost?",
     _cost_faq_a),
    ("What should a couple be for Halloween?",
     _couple_a),
    ("What is a good family costume with kids?",
     _family_a),
]

faq_html = '\n'.join(
    f'<div class="faq"><h3>{esc(dash_free(q))}</h3><p>{esc(dash_free(a))}</p></div>'
    for q, a in faq)

howto_json = {
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": "How to try a Halloween costume on yourself before you commit",
    "description": "Preview costume picks on your own face with the free, private Try it on feature.",
    "step": [{"@type": "HowToStep", "name": f"Step {n}", "text": dash_free(s)}
             for n, s in enumerate(howto_steps, 1)],
}

faq_json = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [{"@type": "Question", "name": dash_free(q),
                    "acceptedAnswer": {"@type": "Answer", "text": dash_free(a)}}
                   for q, a in faq],
}

# 2026-10-22 reconciliation part 2: the live Article JSON-LD was
# hand-edited (Organization author in compact form, classic-ghost image,
# dateModified 2026-09-29, "materials list" description). Carried
# verbatim as a literal block; json.dumps cannot reproduce its shape.
ARTICLE_JSONLD = """{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Halloween Costume Ideas 2026: Pick One, Try It On Yourself",
  "description": "Halloween costume ideas for 2026, sorted by who is wearing them: solo, couples, groups, family, and kids. Every pick shows its real build time and materials list, and every section ends at the 2-minute quiz with a private face try-on.",
  "author": {
    "@type": "Organization", "name": "Pick My Costume"
  },
  "publisher": {
    "@type": "Organization",
    "name": "Pick My Costume",
    "url": "https://pickmycostume.com/"
  },
  "datePublished": "2026-09-26",
  "dateModified": "2026-09-29",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://pickmycostume.com/halloween-costume-ideas-2026"
  },
  "image": "https://pickmycostume.com/images/og/classic-ghost.jpg"
}"""

RELATED_BLOCK = '<!-- pmc-related-cards-v1 -->\n<style>\n.pmc-rel{margin:44px 0 0}\n.pmc-rel h2{font-size:24px;margin:0 0 6px;line-height:1.3}\n.pmc-note{color:#cdbcf0;font-size:14px;margin:0 0 18px}\n.pmc-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}\n.pmc-card{background:#2a1c52;border:1px solid #4b3586;border-radius:14px;overflow:hidden;text-decoration:none;color:#fdf3e3;display:block}\n.pmc-card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:#211540}\n.pmc-card .pmc-t{display:block;padding:10px 12px}\n.pmc-card .pmc-t strong{display:block;font-size:15px;margin-bottom:2px}\n.pmc-card .pmc-t span{color:#cdbcf0;font-size:13px}\n.pmc-quiz{display:block;margin-top:14px;background:#211540;border:1px solid #4b3586;border-radius:14px;padding:18px;text-decoration:none;color:#fdf3e3;text-align:center}\n.pmc-quiz strong{display:block;font-size:18px;color:#ff8c1a;margin-bottom:4px}\n.pmc-quiz span{color:#cdbcf0;font-size:14px}\n.pmc-pin{margin-top:10px;text-align:center}\n.pmc-pin a{color:#cdbcf0;font-size:14px}\n.pmc-more{margin-top:14px}\n.pmc-more a{color:#cdbcf0}\n</style>\n<div class="pmc-rel">\n<h2>More costume guides</h2>\n<p class="pmc-note">Step-by-step builds for the picks on this page, with real times.</p>\n<div class="pmc-cards">\n<a class="pmc-card" href="https://pickmycostume.com/c/classic-ghost"><img src="https://pickmycostume.com/images/og/classic-ghost.jpg" alt="Classic Ghost costume" loading="lazy" width="1200" height="630"><span class="pmc-t"><strong>Classic Ghost</strong><span>10 min - Easy</span></span></a>\n<a class="pmc-card" href="https://pickmycostume.com/c/deadpan-diva"><img src="https://pickmycostume.com/images/og/deadpan-diva.jpg" alt="Deadpan Diva costume" loading="lazy" width="1200" height="630"><span class="pmc-t"><strong>Deadpan Diva</strong><span>15 min - Easy</span></span></a>\n<a class="pmc-card" href="https://pickmycostume.com/c/cat-mouse"><img src="https://pickmycostume.com/images/og/cat-mouse.jpg" alt="Cat &amp; Mouse costume" loading="lazy" width="1200" height="630"><span class="pmc-t"><strong>Cat &amp; Mouse</strong><span>15 min - Easy</span></span></a>\n<a class="pmc-card" href="https://pickmycostume.com/c/gloom-bloom"><img src="https://pickmycostume.com/images/og/gloom-bloom.jpg" alt="Gloom &amp; Bloom costume" loading="lazy" width="1200" height="630"><span class="pmc-t"><strong>Gloom &amp; Bloom</strong><span>15 min - Easy</span></span></a>\n</div>\n<a class="pmc-quiz" href="/halloween-costume-ideas-quiz"><strong>Pick my costume</strong><span>Answer a few questions and get your pick in 2 minutes. Free, no signup.</span></a>\n<p class=\"pmc-note pmc-more\">More ideas: <a href=\"https://pickmycostume.com/101-costume-ideas\">101 costume ideas</a> &middot; <a href=\"https://pickmycostume.com/funny-halloween-costumes\">Funny Halloween costumes</a> &middot; <a href=\"https://pickmycostume.com/cute-halloween-costumes\">Cute Halloween costumes</a> &middot; <a href=\"https://pickmycostume.com/womens-halloween-costumes\">Women&#8217;s Halloween costumes</a> &middot; <a href=\"https://pickmycostume.com/easy-adult-halloween-costumes\">Easy adult Halloween costumes</a> &middot; <a href=\"https://pickmycostume.com/homemade-halloween-costumes\">Homemade Halloween costumes</a> &middot; <a href=\"https://pickmycostume.com/glow-in-the-dark-costumes\">Glow in the dark costumes</a> &middot; <a href=\"https://pickmycostume.com/goth-halloween-costumes\">Goth Halloween costumes</a></p>\n</div>'

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Halloween Costume Ideas 2026: Try Them On Yourself | Pick My Costume</title>
<meta name="description" content="2026 Halloween costume ideas by wearer: solo, couples, groups, family, kids, last minute. Real build times, a 2-minute quiz, and a private try-on.">
<link rel="canonical" href="{SITE}/{SLUG}">
<meta property="og:type" content="article">
<meta property="og:title" content="Halloween Costume Ideas 2026: Try Them On Yourself">
<meta property="og:description" content="Ideas sorted by who is wearing them, real build times, a 2-minute quiz, and a private face try-on.">
<meta property="og:url" content="{SITE}/{SLUG}">
<meta property="og:image" content="{SITE}/images/og/classic-ghost.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Halloween Costume Ideas 2026: Try Them On Yourself">
<meta name="twitter:description" content="Ideas sorted by who is wearing them, real build times, a 2-minute quiz, and a private face try-on.">
<meta name="twitter:image" content="{SITE}/images/og/classic-ghost.jpg">
<script type="application/ld+json">
{ARTICLE_JSONLD}
</script>
<script type="application/ld+json">{json.dumps(faq_json, indent=2)}
</script>
<script type="application/ld+json">
{json.dumps(howto_json, indent=2)}
</script>
<style>
:root{{
  --bg:#160d28; --bg2:#211540; --card:#2a1c52; --ink:#fdf3e3;
  --muted:#cdbcf0; --line:#4b3486; --accent:#ff8c1a; --accent-ink:#2a1500;
  --radius:14px;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.65}}
.wrap{{max-width:760px;margin:0 auto;padding:20px 16px 64px}}
header.top{{display:flex;align-items:center;justify-content:space-between;padding:14px 0}}
.brand{{font-weight:800;font-size:18px;color:var(--ink);text-decoration:none}}
.brand span{{color:var(--accent)}}
.home-link{{color:var(--muted);text-decoration:none;font-size:14px}}
h1{{font-size:32px;margin:8px 0 4px;line-height:1.2}}
.byline{{color:var(--muted);font-size:14px;margin:0 0 16px}}
.lede{{font-size:18px;margin:0 0 24px}}
.takeaways{{background:var(--bg2);border:2px solid var(--accent);border-radius:var(--radius);padding:18px 20px;margin:0 0 32px}}
.takeaways h2{{margin:0 0 8px;font-size:19px}}
.takeaways ul{{margin:0;padding-left:20px}}
.takeaways li{{margin:6px 0}}
h2{{font-size:26px;margin:48px 0 6px;line-height:1.3}}
.section-note{{color:var(--muted);font-size:14px;margin:0 0 18px}}
.toc{{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 8px}}
.toc a{{background:var(--card);border:1px solid var(--line);border-radius:999px;color:var(--ink);text-decoration:none;font-size:14px;padding:8px 16px}}
.idea{{display:flex;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px;margin:0 0 14px}}
.idea img{{width:110px;height:110px;object-fit:cover;border-radius:10px;flex:none}}
.idea-body h3{{margin:0 0 6px;font-size:18px}}
.idea-body p{{margin:6px 0}}
.meta{{color:var(--muted);font-size:14px}}
.go{{display:inline-block;margin:8px 0 2px;background:var(--accent);color:var(--accent-ink);font-weight:800;font-size:15px;padding:10px 20px;border-radius:var(--radius);text-decoration:none}}
.cta{{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin:20px 0 8px}}
.cta p{{margin:0}}
.cta a{{color:var(--accent);font-weight:700}}
.tier{{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin:0 0 14px}}
.tier h3{{margin:0 0 4px;font-size:19px}}
.tier-pick{{display:block;padding:12px 0;border-top:1px solid var(--line);text-decoration:none;color:var(--ink)}}
.tier-name{{font-weight:700;display:block}}
.tier-meta{{color:var(--muted);font-size:14px;display:block;margin-top:2px}}
.howto{{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:20px 22px;margin:0 0 14px}}
.howto ol{{margin:8px 0 0;padding-left:22px}}
.howto li{{margin:8px 0}}
.faq{{background:var(--bg2);border:1px solid var(--line);border-radius:var(--radius);padding:16px 18px;margin:0 0 12px}}
.faq h3{{margin:0 0 6px;font-size:16px}}
.faq p{{margin:0;color:var(--muted);font-size:15px}}
.final{{background:var(--bg2);border:2px solid var(--accent);border-radius:var(--radius);padding:24px;margin-top:44px;text-align:center}}
.final h2{{margin-top:0}}
.final .sub{{color:var(--muted)}}
.fine{{color:var(--muted);font-size:13px}}
.footer{{margin-top:48px;color:var(--muted);font-size:13px;text-align:center}}
.footer a{{color:var(--muted)}}
.aiphoto-note{{font-size:11px;color:#9a8fb8;margin:0 0 16px;}}</style>
</head>
<body>
<div class="wrap">
<header class="top">
<a class="brand" href="{SITE}/">Pick My <span>Costume</span></a>
<a class="home-link" href="{SITE}/">Home</a>
</header>

<h1>Halloween Costume Ideas 2026: Pick One, Try It On Yourself</h1>
<p class="quick-answer"><strong>Quick answer:</strong> <a href="/c/neon-demon-hunter">Neon Demon Hunter</a> (25 min, black hoodie), <a href="/c/classic-ghost">Classic Ghost</a> (10 min, 1 white flat sheet), and <a href="/c/emerald-witch">Emerald Witch</a> (45 min, 1 long green dress): three of the most-built solo guides on the site. Tap any name for its full build guide: materials list, numbered steps, and safety notes.</p>
<p class="byline">Updated September 2026</p>
<p class="lede">The real question is not what is trending. It is what you would actually wear out the door on Halloween night. Below are 24 picks sorted by who is wearing them: solo, couples, groups, family, kids, and last minute. The last-minute four repeat the fastest builds from above, so they are easy to find. Every pick shows its real build time and materials list straight from the costume guide, and every section ends at the same place: a 2-minute quiz that gives you one personal pick, and a private face try-on so you can see it on yourself before you commit.</p>
<p class="aiphoto-note">Costume photos are AI-generated concept photos.</p>

<div class="takeaways">
<h2>Key takeaways</h2>
<ul>
<li>Pick by who is wearing the costume first. Solo, couple, group, family, kid, and last-minute are different genres, so this page is sorted that way.</li>
<li>Every pick below lists its real build time and materials from the guide. Most take under an hour.</li>
<li>Stuck between two? Take the <a href="{SITE}/" style="color:var(--accent);font-weight:700">2-minute quiz</a> for one personal pick, then tap <strong>Try it on</strong> on your result card to preview it on your own face. The photo never leaves your phone.</li>
<li>Everything here is free: no signup, no credits, no accounts.</li>
</ul>
</div>

<nav class="toc" aria-label="Sections">
<a href="#effort">Pick your effort</a>
<a href="#solo">Solo</a>
<a href="#couples">Couples</a>
<a href="#group">Groups</a>
<a href="#family">Family</a>
<a href="#kid">Kids</a>
<a href="#last-minute">Last minute</a>
<a href="#howto">Try it on yourself</a>
<a href="#faq">FAQ</a>
</nav>

<section id="effort">
<h2>What should I be for Halloween? Pick your effort.</h2>
<p class="section-note">Be honest here. The best costume is the one you will actually finish. Tap any pick to open its full guide with the materials list.</p>
{chr(10).join(tiers_html)}
{section_cta()}
</section>

{chr(10).join(sections_html)}

<section id="howto">
<h2>How to try a costume on yourself before you commit</h2>
<p class="section-note">Guessing from a list is how you end up with a costume you never wear. Preview it first.</p>
<div class="howto">
<ol>
{chr(10).join(f"<li>{esc(dash_free(s))}</li>" for s in howto_steps)}
</ol>
</div>
<div class="cta">
<p><strong>Ready?</strong> <a href="{SITE}/">Take the 2-minute quiz</a>, get your pick, and tap <strong>Try it on</strong>. It is free, private, and takes about as long as reading this sentence.</p>
</div>
</section>

<section id="faq">
<h2>FAQ</h2>
{faq_html}
</section>

{RELATED_BLOCK}

<div class="final">
<h2>Still deciding?</h2>
<p class="sub">Answer five questions about your Halloween night and get one personal pick, free, no signup. Then try it on your own face, privately, on your phone, with nothing uploaded anywhere.</p>
<a class="go" href="{SITE}/">Take the 2-minute quiz</a>
<p class="fine pmc-pin">Saving ideas for later? <a href="https://pinterest.com/pin/create/button/?url=https%3A%2F%2Fpickmycostume.com%2Fhalloween-costume-ideas-2026&amp;media=https%3A%2F%2Fpickmycostume.com%2Fimages%2Fog%2Fneon-demon-hunter.jpg&amp;description=Ideas%20sorted%20by%20who%20is%20wearing%20them%2C%20real%20build%20times%2C%20a%202-minute%20quiz%2C%20and%20a%20private%20face%20try-on." target="_blank" rel="noopener">Pin this guide on Pinterest</a></p>
<p class="fine">Built with Muse.</p>
</div>

<div class="footer">
<p><a href="{SITE}/costumes">All {len(plans)} costume guides</a> &middot; <a href="{SITE}/compare">Compare easy costumes</a> &middot; <a href="{SITE}/trending">Trending</a> &middot; <a href="{SITE}/teen-halloween-costumes-2026">Teen costumes</a></p>
<p><a href="{SITE}/">Pick My Costume</a> &middot; Built with Muse.</p>
</div>
</div>
</body>
</html>
"""

out = os.path.join(REPO, 'halloween-costume-ideas-2026.html')
open(out, 'w').write(page)
print('wrote', out, len(page), 'bytes')

# QA: lint
text = page
bad = re.findall(r'[\u2013\u2014]', text)
print('em/en dash count in page:', len(bad))
for s in ['neon-demon-hunter','deadpan-diva','tin-hero','emerald-witch','cat-mouse',
          'rain-cloud-rainbow','sun-moon','doctor-bride','gloom-bloom','safari-zoo-crew',
          'good-witch-bad-witch','soccer-squad','blue-dog-family','superhero-family',
          'blue-alien-ohana','little-pig-family','classic-ghost','fuzzy-monster',
          'pocket-plush','baby-dino','spider','haunted-animatronics','dragon-rider-duo']:
    assert s in byid, f'missing idea {s}'
print('all 24 featured slugs verified in bank')
# verify every /c/ pick link matches bank
links = re.findall(r'href="/c/([a-z0-9-]+)"', text)
assert links, 'no /c/ pick links found'
assert all(l in byid for l in links), 'bad /c/ link'
print('idea links:', len(links), 'all valid')
# verify photos exist
for l in set(links):
    assert os.path.exists(os.path.join(REPO, 'photos', l + '.webp')), l
print('all card photos exist')
