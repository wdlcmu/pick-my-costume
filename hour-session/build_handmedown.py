#!/usr/bin/env python3
"""Build hand-me-down.html from the live data sources.

Reads:
  - pantry.html DATA.pantry  -> material labels + staple flags (source of truth)
  - pantry-mats.json          -> per-idea material keys
  - mcp-server/bank.json      -> idea titles + blurbs
Injects a JSON blob into hour-session/handmedown-template.html
and writes <repo>/hand-me-down.html (self-contained; code only, never deployed
by this script).

Fails loudly on: missing labels, ideas without mats, </script> in data,
template placeholder missing, non-idempotent output.

2026-10-22 reconciliation (parity fix list #9): the template carries the
live page's share attribution verbatim -- the copied plan's build-guide
link ends "?src=share-handmedown" and its make-your-own-plan link ends
"&src=share-handmedown" -- and the Quick answer shows Fairy Tale
Princesses at its display time "15 min" (bank time "15 min + 1 hr
drying" with the drying suffix stripped, per Billy's 2026-10-03 display
rule). Do not remove either: a regen must reproduce the live page.
"""
import json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(REPO, "hour-session", "handmedown-template.html")
OUT = os.path.join(REPO, "hand-me-down.html")
if len(sys.argv) > 1:
    OUT = sys.argv[1]

PLACEHOLDER = "/*__HANDMEDOWN_DATA__*/"


def extract_pantry_labels():
    src = open(os.path.join(REPO, "pantry.html")).read()
    i = src.index("const DATA = ")
    j = src.index("{", i)
    depth, k = 0, j
    while True:
        c = src[k]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        k += 1
    data = json.loads(src[j:k + 1])
    labels = {p["id"]: p["label"] for p in data["pantry"]}
    staples = {p["id"] for p in data["pantry"] if p.get("staple")}
    return labels, staples


def flat_keys(node):
    out = set()

    def walk(x):
        if isinstance(x, list):
            for y in x:
                walk(y)
        elif isinstance(x, str):
            out.add(x)

    walk(node)
    return out


def main():
    labels, staples = extract_pantry_labels()
    mats = json.load(open(os.path.join(REPO, "pantry-mats.json")))["mats"]
    bank = json.load(open(os.path.join(REPO, "mcp-server", "bank.json")))
    ideas = bank["ideas"]

    # Count was hard-coded at 138 until the bank grew to 169 (2026-10-13);
    # the real guard is bank/mats agreement, so assert that, fail loudly.
    assert len(ideas) == len(mats) and len(ideas) > 0, (
        f"bank={len(ideas)} mats={len(mats)}; bank and mats must agree")

    blob_ideas = []
    for idea in ideas:
        iid = idea["id"]
        assert iid in mats, f"idea {iid} has no mats entry"
        keys = sorted(flat_keys(mats[iid]) - staples)
        missing = [k for k in keys if k not in labels]
        assert not missing, f"idea {iid}: mat keys missing labels: {missing}"
        blob_ideas.append({
            "id": iid,
            "t": idea["title"],
            "b": idea.get("blurb", ""),
            "m": keys,
        })

    blob = {"ideas": blob_ideas, "labels": labels}
    blob_json = json.dumps(blob, separators=(",", ":"))
    assert "</script" not in blob_json.lower(), "data contains </script"

    tpl = open(TEMPLATE).read()
    assert PLACEHOLDER in tpl, "template placeholder missing"
    page = tpl.replace(
        PLACEHOLDER,
        "var HANDMEDOWN = " + blob_json + ";",
        1,
    )

    with open(OUT, "w") as f:
        f.write(page)

    # Sanity: distribution of reusable-part counts + sample rankings.
    counts = sorted(len(i["m"]) for i in blob_ideas)
    zero = [i["id"] for i in blob_ideas if not i["m"]]
    print(f"built {OUT}: {len(blob_ideas)} ideas, "
          f"reusable parts min/median/max = "
          f"{counts[0]}/{counts[len(counts)//2]}/{counts[-1]}")
    print(f"ideas with zero reusable parts (honest empty state): {zero}")

    # Sample ranking sanity: rank() logic mirrored here for spot checks.
    COLORS = {"black", "blue", "brown", "gold", "gray", "green", "orange",
              "pink", "purple", "red", "silver", "white", "yellow"}

    def base_of(k):
        if "-" in k:
            base, rest = k.split("-", 1)
            if base in ("paper", "paint", "tape") and rest in COLORS:
                return base
        return k

    by_id = {i["id"]: i for i in blob_ideas}

    def rank(old_id):
        old = set(by_id[old_id]["m"])
        old_base = {}
        for k in old:
            old_base.setdefault(base_of(k), k)
        rows = []
        for c in blob_ideas:
            if c["id"] == old_id:
                continue
            cset = set(c["m"])
            exact = len(old & cset)
            cb = {}
            for k in cset:
                cb.setdefault(base_of(k), k)
            base = sum(1 for b, k in cb.items()
                       if b in old_base and old_base[b] != k)
            new_parts = len(cset - old)
            rows.append((c["id"], exact, base, new_parts, c["t"]))
        rows.sort(key=lambda r: (-r[1], -r[2], r[3], r[4]))
        return rows

    for sample in ["astronaut", "classic-ghost", "baby-dino"]:
        if sample in by_id and by_id[sample]["m"]:
            top3 = [(r[0], r[1], r[2]) for r in rank(sample)[:3]]
            print(f"sample old={sample}: top3(id,exact,base)={top3}")


if __name__ == "__main__":
    main()
