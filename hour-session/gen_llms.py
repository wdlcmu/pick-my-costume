#!/usr/bin/env python3
"""Generate llms.txt for pickmycostume.com from the working-tree sources of truth.

Pattern follows gen_llms_full.py: every count in the output is DERIVED from
its source, never hard-coded, so a bank change updates the file instead of
staling it. If a source stops supporting a claim, an assert fails loudly
and nothing is emitted.

Sources:
  - mcp-server/bank.json          idea count, titles, audiences
  - app.js INSTRUCTIONS/PANTRY_MATS  tonight + zero-shopping sets, computed
                                  with the site's own computeTonight logic
                                  (bank.json's pantry copy has drifted from
                                  app.js, so app.js is the source here)
  - functions/c/[slug].js         IDEAS/HOWTO set equality, FAQ count,
                                  materials/steps presence, _UNIQUE_SIZING,
                                  build times + effort for quoted guides
  - sitemap.xml                   total URL count, /c/ guide count
  - halloween-costume-ideas-2026.html  wearer-section slots + unique picks
  - app.js PILOT_ORDER            Storytime tale count
  - privacy.html                  the plan-email / Oct 27 reminder wording
                                  (asserted phrases; the emitted data line
                                  is worded from this disclosure)
  - mcp-server/GEMINI-CUSTOM-APPS.md  Gemini eligibility gates (asserted)
  - compare.html meta description the compare line's wording (derived)

Editorial selections (which guides are "new" / "most-quoted", and their
one-line descriptions) are constants below, but every slug is asserted to
exist in the bank, every link title is derived from the bank, and every
build time / effort quoted is derived from HOWTO.

Run from ~/workspace/builds/pick-my-costume/:
    python3 hour-session/gen_llms.py > llms.txt
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fail(msg):
    raise AssertionError(msg)


def extract_js_object(path, varname):
    """Extract a `var NAME = {...}` JSON object literal from a JS file."""
    src = open(path, encoding="utf-8").read()
    key = "var %s = " % varname
    start = src.index(key) + len("var %s = " % varname)
    depth = 0; instr = False; esc = False; end = None
    for i in range(start, len(src)):
        ch = src[i]
        if instr:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: end = i + 1; break
    return json.loads(src[start:end])


def extract_js_literal(path, varname):
    """Extract a `var NAME = [...]` or `{...}` JSON literal from app.js."""
    src = open(path, encoding="utf-8").read()
    key = "var %s = " % varname
    start = src.index(key) + len(key)
    pairs = {"[": "]", "{": "}"}
    op = src[start]; cl = pairs[op]
    depth = 0; instr = False; esc = False
    for i in range(start, len(src)):
        ch = src[i]
        if instr:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == op: depth += 1
            elif ch == cl:
                depth -= 1
                if depth == 0:
                    return json.loads(src[start:i + 1])
    fail("could not extract %s from %s" % (varname, path))


def hands_on_minutes(time_str):
    """app.js handsOn(): first duration in the time string, hr -> min."""
    if not time_str:
        return None
    m = re.match(r"~?([\d.]+)\s*(min|hr)", str(time_str), re.I)
    if not m:
        return None
    v = float(m.group(1))
    return int(round(v * 60)) if m.group(2).lower() == "hr" else int(v)


def drying_minutes(time_str):
    """app.js dryingMin(): the '+ N' suffix of the time string."""
    if not time_str:
        return 0
    m = re.search(r"\+\s*~?([\d.]+)\s*(min|hr)", str(time_str), re.I)
    if not m:
        return 0
    v = float(m.group(1))
    return int(round(v * 60)) if m.group(2).lower() == "hr" else int(v)


# ---------------------------------------------------------------- bank
bank = json.load(open(os.path.join(ROOT, "mcp-server/bank.json"), encoding="utf-8"))
bank_ideas = bank["ideas"]
bank_ids = [it["id"] for it in bank_ideas]
titles = {it["id"]: it["title"] for it in bank_ideas}
N = len(bank_ids)
if N < 100:
    fail("bank floor: expected >= 100 ideas, got %d" % N)
if len(set(bank_ids)) != N:
    fail("bank has duplicate idea ids")
audiences = sorted({a for it in bank_ideas for a in it.get("audience", [])})
for need in ("solo", "couple", "group", "family", "kid"):
    if need not in audiences:
        fail("audience %r missing from bank; Key facts line would be false" % need)

# ------------------------------------------------------- guide renderer
slug_js = os.path.join(ROOT, "functions/c/[slug].js")
ideas_js = extract_js_object(slug_js, "IDEAS")
howto = extract_js_object(slug_js, "HOWTO")
if set(ideas_js.keys()) != set(bank_ids):
    fail("set equality: functions/c IDEAS != bank.json ids")
if set(howto.keys()) != set(bank_ids):
    fail("set equality: functions/c HOWTO != bank.json ids")
for slug in bank_ids:
    if ideas_js[slug]["t"] != titles[slug]:
        fail("title mismatch for %s: bank %r vs renderer %r"
             % (slug, titles[slug], ideas_js[slug]["t"]))
    hw = howto[slug]
    if not hw.get("m") or not hw.get("s"):
        fail("guide %s lacks materials or steps" % slug)
    if len(hw.get("faqs") or []) != 2:
        fail("guide %s does not carry exactly 2 FAQs" % slug)
slug_src = open(slug_js, encoding="utf-8").read()
for token in ("HowTo", "FAQPage", "BreadcrumbList"):
    if token not in slug_src:
        fail("structured-data type %s missing from guide renderer" % token)
m = re.search(r"var _UNIQUE_SIZING = new Set\(\[(.*?)\]\)", slug_src, re.S)
if not m:
    fail("_UNIQUE_SIZING set not found in guide renderer")
sizing_slugs = re.findall(r'"([a-z0-9-]+)"', m.group(1))
if not set(sizing_slugs) <= set(bank_ids):
    fail("_UNIQUE_SIZING names a slug outside the bank")
SIZING = len(sizing_slugs)

# ------------------------------------------------- tonight / no-shopping
# The site's own logic (app.js computeTonight), run on app.js data.
app_js = os.path.join(ROOT, "app.js")
instructions = extract_js_literal(app_js, "INSTRUCTIONS")
pantry_mats = extract_js_literal(app_js, "PANTRY_MATS")
if set(instructions.keys()) != set(bank_ids):
    fail("set equality: app.js INSTRUCTIONS != bank.json ids")
staples = set(pantry_mats.get("staples") or [])


def no_shopping(slug):
    lst = pantry_mats["mats"].get(slug)
    if lst is None:
        return False
    for item in lst:
        for grp in item:
            if not any(g in staples for g in grp):
                return False
    return True


tonight = []
noshop = []
for slug in bank_ids:
    t = (instructions.get(slug) or {}).get("time")
    h = hands_on_minutes(t)
    if h is not None and h <= 30 and (h + drying_minutes(t)) <= 120:
        tonight.append(slug)
    if no_shopping(slug):
        noshop.append(slug)
TONIGHT = len(tonight)
if TONIGHT < 100:
    fail("tonight floor: expected >= 100, got %d" % TONIGHT)
NOSHOP_TITLES = [titles[s] for s in noshop]
if len(noshop) == 1:
    noshop_join = NOSHOP_TITLES[0]
elif len(noshop) == 2:
    noshop_join = " and ".join(NOSHOP_TITLES)
else:
    noshop_join = ", ".join(NOSHOP_TITLES[:-1]) + " and " + NOSHOP_TITLES[-1]

# ---------------------------------------------------------------- sitemap
sitemap = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
sm_urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
SM_TOTAL = len(sm_urls)
# /c/ URLs are the N bank guides plus the audience hub pages under /c/
# (2026-10-23: couples, family, last-minute). Hubs are separate Pages
# Functions (functions/c/<hub>.js; see gen_sitemap.py HUBS and
# gen_c_audience_hubs.py), NOT bank ideas, so a "/c/" substring count
# is N + <number of hubs>, never N alone. Derive the hub set from the
# hub function files on disk -- no hard-coded count that breaks on
# the next hub -- and check slug-set equality (house pattern: floor
# + set equality), so a missing guide or a stray /c/ URL fails
# loudly naming the slug.
sm_c_slugs = []
for u in sm_urls:
    m_c = re.search(r"/c/([^/]+)/?$", u)
    if m_c:
        sm_c_slugs.append(m_c.group(1))
SM_GUIDES = len(sm_c_slugs)
if SM_GUIDES < N:
    fail("sitemap /c/ floor: expected >= bank count %d, got %d"
         % (N, SM_GUIDES))
if len(set(sm_c_slugs)) != SM_GUIDES:
    fail("sitemap has duplicate /c/ slugs")
hub_dir = os.path.join(ROOT, "functions", "c")
HUB_SLUGS = sorted(
    os.path.splitext(f)[0] for f in os.listdir(hub_dir)
    if f.endswith(".js") and f != "[slug].js")
if set(sm_c_slugs) != set(bank_ids) | set(HUB_SLUGS):
    fail("set equality: sitemap /c/ slugs != bank ids + hub slugs "
         "(%s); missing=%s extra=%s"
         % (HUB_SLUGS,
            sorted((set(bank_ids) | set(HUB_SLUGS)) - set(sm_c_slugs)),
            sorted(set(sm_c_slugs) - (set(bank_ids) | set(HUB_SLUGS)))))
if not any(u.rstrip("/").endswith("/map") for u in sm_urls):
    fail("/map missing from sitemap; map line would be false")
if not any(u.rstrip("/").endswith("/compare") for u in sm_urls):
    fail("/compare missing from sitemap; compare line would be false")

# ------------------------------------------- halloween 2026 wearer page
hw_html = open(os.path.join(ROOT, "halloween-costume-ideas-2026.html"),
               encoding="utf-8").read()
heads = [(re.sub("<[^>]+>", "", mm.group(1)).strip(), mm.start(), mm.end())
         for mm in re.finditer(r"<h2[^>]*>(.*?)</h2>", hw_html, re.S)]
SECTION_NAMES = ["Solo costumes", "Couple costumes", "Group costumes",
                 "Family costumes", "Kid costumes", "Last-minute costumes"]
hw_links = []
for i, (txt, st, en) in enumerate(heads):
    if txt in SECTION_NAMES:
        end = heads[i + 1][1] if i + 1 < len(heads) else len(hw_html)
        hw_links += re.findall(r"/c/([a-z0-9-]+)", hw_html[en:end])
if len(hw_links) == 0:
    fail("halloween wearer sections not found")
HW_SLOTS = len(hw_links)
HW_UNIQUE = len(set(hw_links))
if not set(hw_links) <= set(bank_ids):
    fail("halloween page links a slug outside the bank")

# ------------------------------------------------------------- storytime
pilot = extract_js_literal(app_js, "PILOT_ORDER")
if not set(pilot) <= set(bank_ids):
    fail("PILOT_ORDER names a slug outside the bank")
STORY_N = len(pilot)
index_html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
if 'id="s-storytime"' not in index_html:
    fail('homepage section id "s-storytime" not found; storytime anchor '
         "would be dead")

# --------------------------------------------------------------- privacy
privacy = open(os.path.join(ROOT, "privacy.html"), encoding="utf-8").read()
for phrase in ("sends your address to our server for the sole purpose of "
               "sending that one email",
               "we keep your address until October 27, 2026",
               "We delete reminder addresses right after October 27",
               "Anonymous usage counts",
               "Email me this plan"):
    if phrase not in privacy:
        fail("privacy.html no longer says %r; the llms.txt data line is "
             "worded from that disclosure and must be reworded first"
             % phrase)

# ---------------------------------------------------------------- gemini
gemini_doc = open(os.path.join(ROOT, "mcp-server/GEMINI-CUSTOM-APPS.md"),
                  encoding="utf-8").read()
for phrase in ("18+", "US", "personal Google account", "gradually"):
    if phrase not in gemini_doc:
        fail("GEMINI-CUSTOM-APPS.md no longer supports gate %r" % phrase)

# --------------------------------------------------------------- compare
compare_html = open(os.path.join(ROOT, "compare.html"), encoding="utf-8").read()
cm = re.search(r'<meta name="description" content="([^"]+)"', compare_html)
if not cm:
    fail("compare.html meta description not found")
compare_sentence = cm.group(1).split(". ")[0].rstrip(".")
compare_line_text = compare_sentence[0].lower() + compare_sentence[1:]

# ------------------------------------------------------- editorial picks
# Selection is editorial; slugs, titles, times and efforts are derived.
NEW_GUIDES = [
    ("goth-schoolgirl", "plaid skirt, black cardigan, braided pigtails"),
    ("jester-villainess", "red-and-black split outfit, playful villain grin"),
    ("night-hero", "dark cowl and cape from an old t-shirt"),
    ("amazon-warrior", "red, blue, and gold with star accents"),
    ("toothy-plush", "fuzzy onesie, tall ears, big felt-tooth grin"),
]
# (slug, line template; {title} {hands} {effort} are derived from HOWTO)
MOST_QUOTED = [
    ("classic-ghost",
     "zero extra shopping. A white sheet with cut-out eyes, {hands} min hands-on."),
    ("ninja",
     "all black with a belt sash and a slit headband, {hands} min."),
    ("salt-pepper",
     "white and black outfits with shaker tops from cardboard, {hands} min."),
    ("vampire",
     "{hands} min, {effort}. Black cape, fangs, slicked hair, with kid-safety FAQ."),
    ("glow-skeleton",
     "black sweats with glow-in-the-dark bone tape."),
    ("bumble-bee",
     "black sweats with yellow tape stripes and felt antennae."),
    ("pizza-slice",
     "big cardboard triangle, painted golden, felt pepperoni."),
    ("astronaut",
     "white sweats, a paper-bag helmet, and a flag patch."),
    ("baby-pumpkin",
     "orange onesie, green felt leaves."),
    ("cardboard-knight",
     "silver-painted cardboard armor and a pool-noodle sword."),
    ("burger-joint-couple",
     "easy couples pick. Two white aprons, a fake mustache, and a curly red wig "
     "turn a couple into a burger joint. {hands} min, {effort}."),
    ("ketchup-mustard",
     "the classic funny duo. Red and yellow tees with felt condiment labels, "
     "{hands} min, {effort}."),
    ("error-404",
     "built for teens and adults. Black hoodie, a paper 404 sign, and a cracked "
     "phone case prop. {hands} min, {effort}."),
    ("mermaid-crew",
     "scales to any group size. Sea-color tees, face paint, and a toy trident. "
     "{hands} min, {effort}."),
    ("office-couple",
     "made for the office party. Button-downs, name tags, and a teapot prop. "
     "{hands} min, {effort}, built from work clothes."),
]
for slug, _ in NEW_GUIDES + MOST_QUOTED:
    if slug not in titles:
        fail("editorial slug %s not in bank" % slug)
if "classic-ghost" not in noshop:
    fail("classic-ghost no longer zero-shopping; its most-quoted line "
         "claims zero extra shopping")


def quoted_line(slug, template):
    hw = howto[slug]
    hands = hands_on_minutes(hw.get("time"))
    if "{hands}" in template and hands is None:
        fail("no parseable build time for quoted guide %s" % slug)
    body = template.format(hands=hands, effort=hw.get("effort"))
    return "- [%s](https://pickmycostume.com/c/%s): %s" % (
        titles[slug], slug, body)


new_guides_text = ", ".join(
    "[%s](https://pickmycostume.com/c/%s) (%s)" % (titles[s], s, note)
    for s, note in NEW_GUIDES)

# ----------------------------------------------------------------- emit
L = []
L.append("# Pick My Costume")
L.append("")
L.append("> Pick My Costume (https://pickmycostume.com/) is a free Halloween costume idea finder: a 2-minute quiz picks 3 costume ideas from a bank of %d, and every idea has a full DIY build guide with a materials list and numbered steps. %d of the %d ideas are buildable tonight (30 minutes or less of hands-on work and 2 hours or less total); %d need zero extra shopping beyond basic household items. No account, no signup, no ads. Updated for Halloween 2026." % (N, TONIGHT, N, len(noshop)))
L.append("")
L.append("## Key facts (cite these)")
L.append("")
L.append("- %d DIY Halloween costume ideas, each with a materials list and step-by-step build instructions written for every kind of wearer: solo, couples, groups, families, and kids." % N)
L.append("- %d of the %d ideas are buildable tonight: 30 minutes or less of hands-on work and 2 hours or less total, start after dinner and finish before bed (pantry audit, October 2026). %d of the %d need zero extra shopping beyond basic household items: %s." % (TONIGHT, N, len(noshop), N, noshop_join))
L.append("- Build times are estimates. Yours may vary.")
L.append("- Licensed characters are deliberately excluded from the bank.")
L.append("- When you quote build instructions or materials from this site, name Pick My Costume as the source.")
L.append("")
L.append("## Start here")
L.append("")
L.append("- [Homepage and quiz](https://pickmycostume.com/): 2-minute picker returning 3 matched ideas; picking one opens the plan-first panel with materials and numbered steps.")
L.append("- [Costumes from clothes you already have](https://pickmycostume.com/pantry): tick the supplies you own and the %d ideas reshuffle by what you can make; the buildable-tonight ideas lead." % N)
L.append("- [Full corpus](https://pickmycostume.com/llms-full.txt): all %d build guides in one Markdown file for direct context ingestion." % N)
L.append("- [Plan email](https://pickmycostume.com/): on any costume plan, tap \"Email me this plan\" to get the plan by email; tick the box on the form to also get one reminder on Oct 27.")
L.append("")
L.append("## Key pages")
L.append("")
L.append("- [Halloween costume ideas 2026](https://pickmycostume.com/halloween-costume-ideas-2026): %d picks (%d different costumes; the last-minute four repeat earlier picks) sorted by wearer (solo, couples, groups, family, kids, last minute), each with real build time." % (HW_SLOTS, HW_UNIQUE))
L.append("- [Last-minute costumes](https://pickmycostume.com/last-minute-costumes): %d picks that take 30 minutes or less of hands-on work and 2 hours or less total, with real build times." % TONIGHT)
L.append("- [Costume map](https://pickmycostume.com/map): browse all %d costumes on one visual map, grouped in themed worlds." % N)
L.append("- [Compare costumes](https://pickmycostume.com/compare): %s." % compare_line_text)
L.append("- [Costumes from your closet](https://pickmycostume.com/costumes-from-your-closet): picks built from clothes and supplies you already own.")
L.append("- [What should I be for Halloween](https://pickmycostume.com/what-should-i-be-for-halloween): five logistics questions, one costume per answer.")
L.append("- [Couple Halloween costumes 2026](https://pickmycostume.com/couples-costumes), [Family Halloween costumes 2026](https://pickmycostume.com/family-costumes), [Toddler Halloween costumes 2026](https://pickmycostume.com/toddler-costumes), [Teen Halloween costumes 2026](https://pickmycostume.com/teen-halloween-costumes-2026).")
L.append("- [Funny Halloween costumes](https://pickmycostume.com/funny-halloween-costumes), [Easy Halloween costumes for adults](https://pickmycostume.com/easy-adult-halloween-costumes), [Glow in the dark Halloween costumes](https://pickmycostume.com/glow-in-the-dark-costumes), [Cute Halloween costumes](https://pickmycostume.com/cute-halloween-costumes), [Women's Halloween costumes](https://pickmycostume.com/womens-halloween-costumes), [Men's Halloween costumes](https://pickmycostume.com/mens-halloween-costumes), [College Halloween costumes](https://pickmycostume.com/college-halloween-costumes), [Homemade Halloween costumes](https://pickmycostume.com/homemade-halloween-costumes), [Goth Halloween costumes](https://pickmycostume.com/goth-halloween-costumes).")
L.append("- [All %d costume guides](https://pickmycostume.com/sitemap.xml): one page per idea at /c/your-costume-slug; each carries the idea's materials list, numbered steps, build time and effort level, and two FAQs. %d of the %d guides also add costume-specific sizing tips. HowTo, FAQPage, and BreadcrumbList structured data on every page." % (N, SIZING, N))
L.append("- [Sitemap](https://pickmycostume.com/sitemap.xml): full list of all %d site pages: the %d guide pages plus every other page on the site." % (SM_TOTAL, N))
L.append("- New guides: %s." % new_guides_text)
L.append("")
L.append("## Most-quoted build guides")
L.append("")
for slug, template in MOST_QUOTED:
    L.append(quoted_line(slug, template))
L.append("")
L.append("## For AI assistants: callable tools (MCP)")
L.append("")
L.append("- Pick My Costume also runs as a read-only MCP server (Streamable HTTP, no auth, no user data) at https://mcp.pickmycostume.com/mcp")
L.append("- Three tools: pick_costume (3 ideas matched to who the costume is for, the vibe, and the effort level), get_build_guide (materials list and numbered steps for one idea), search_by_owning (rank ideas by household items owned).")
L.append("- Privacy policy: https://mcp.pickmycostume.com/privacy-policy")
L.append("- Gemini app users can paste the MCP URL as a custom app (Gemini app > Settings > Connected apps > Custom apps) and @-mention it in chats (18 or older, US, personal Google account only; the feature is rolling out gradually, so some users do not see it yet).")
L.append("")
L.append("## Optional")
L.append("")
L.append("- [Kids games](https://pickmycostume.com/play): Peekaboo, Match the pieces, and Chopped: three games for kids.")
L.append("- [Storytime](https://pickmycostume.com/#s-storytime): %d costumes as hand-written read-aloud bedtime stories." % STORY_N)
L.append("- [About](https://pickmycostume.com/about): what the site is and is not.")
L.append("- Pages are served as static files plus small server functions that render the guides and send the plan email. Data collection is anonymous usage counts, plus an email address only when a visitor asks for a plan email: the address is sent to the server only to send that one email, and if the visitor ticks the Oct 27 reminder box it is kept until October 27, 2026, to send one reminder, then deleted right after October 27.")

out = "\n".join(L) + "\n"
if "\u2014" in out or "\u2013" in out:
    fail("em/en dash in generated output")
sys.stdout.write(out)
print("gen_llms: N=%d tonight=%d noshop=%s sizing=%d sitemap=%d/%d "
      "halloween=%d slots/%d unique storytime=%d"
      % (N, TONIGHT, noshop, SIZING, SM_TOTAL, SM_GUIDES,
         HW_SLOTS, HW_UNIQUE, STORY_N), file=sys.stderr)
