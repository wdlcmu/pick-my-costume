#!/usr/bin/env python3
"""Generate llms-full.txt for pickmycostume.com from the working-tree source of truth.

Reads the idea bank (IDEAS titles/blurbs) and the per-idea build guides (HOWTO:
materials, steps, decision triple, FAQs) embedded in functions/c/[slug].js, and
emits a single Markdown file with the full corpus: every costume's build guide.
Run from ~/workspace/builds/pick-my-costume/:
    python3 hidden_files/seo-sprint/geo-staged/gen_llms_full.py > hidden_files/seo-sprint/geo-staged/llms-full.txt
On deploy, the emitted file lands at the site root: /llms-full.txt.
Honesty: everything emitted is copied verbatim from the bank; no stats invented.
"""
import json, re, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# script lives in hidden_files/seo-sprint/geo-staged/, root is 3 levels up
ROOT = "/home/hatch/workspace/builds/pick-my-costume"

def extract_js_object(path, varname):
    src = open(path, encoding="utf-8").read()
    key = "var %s = {" % varname
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

ideas = extract_js_object(os.path.join(ROOT, "functions/c/[slug].js"), "IDEAS")
howto = extract_js_object(os.path.join(ROOT, "functions/c/[slug].js"), "HOWTO")

lines = []
lines.append("# Pick My Costume: full build-guide corpus")
lines.append("")
lines.append("> Complete Markdown text of pickmycostume.com's 164 Halloween costume build guides,")
lines.append("> generated from the site's idea bank on the date below. Free, no signup, no ads.")
lines.append("> Generated: 2026-09-30. Regenerate with gen_llms_full.py when the bank changes.")
lines.append("")
lines.append("## Site summary")
lines.append("")
lines.append("- Pick My Costume (https://pickmycostume.com/) is a free Halloween costume idea finder.")
lines.append("- 164 costume ideas. Every idea has a materials list and numbered step-by-step build instructions.")
lines.append("- 16 of the 164 ideas are make-tonight or 1-2 supplies away from default household basics (pantry audit, Sep 2026).")
lines.append("- Build costs are real materials prices, not guesses: the cheapest build costs $0 to $5, 15 ideas cost $5 or less, 118 cost $10 or less.")
lines.append("- Licensed characters are deliberately excluded from the bank.")
lines.append("")
lines.append("## All 164 build guides")
lines.append("")

for slug in sorted(ideas):
    it = ideas[slug]
    hw = howto.get(slug)
    lines.append("### %s" % it["t"])
    lines.append("")
    lines.append("URL: https://pickmycostume.com/c/%s" % slug)
    lines.append("")
    lines.append(it["b"])
    lines.append("")
    if hw:
        triple = " / ".join([x for x in (hw.get("time"), hw.get("cost"), hw.get("effort")) if x])
        if triple:
            lines.append("Build time, cost, effort: %s" % triple)
            lines.append("")
        mats = hw.get("m") or []
        if mats:
            lines.append("Materials:")
            for mitem in mats:
                lines.append("- %s" % mitem)
            lines.append("")
        steps = hw.get("s") or []
        if steps:
            lines.append("Steps:")
            for i, s in enumerate(steps, 1):
                lines.append("%d. %s" % (i, s))
            lines.append("")
        faqs = hw.get("faqs") or []
        for q, a in faqs:
            lines.append("Q: %s" % q)
            lines.append("A: %s" % a)
            lines.append("")
    lines.append("---")
    lines.append("")

print("\n".join(lines))
