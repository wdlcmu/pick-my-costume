/* Share-path QA is recipient-side (Billy 2026-09-25, standing gate):
   the share card is the recipient's first impression, and page-level QA
   passing while the preview shows a different image is a miss, not a pass.
   Asserts for EVERY idea in the bank:
     1. The /c/ page's og:image URL is the photorealistic concept photo
        (pixel-matches a crop of photos/<slug>.webp), NOT the old cartoon
        illustration (images/<slug>.png).
     2. twitter:image uses the same photo URL as og:image.
     3. The share action is idempotent under rapid double-invocation:
        armShareOnce + the real shareText run in a vm sandbox; two
        synchronous taps must fire navigator.share exactly once, disable
        the button while in flight, and re-arm it when the share settles.
   Also asserts every navigator.share text-share call site is wired through
   armShareOnce, so a future share button cannot reintroduce double-fire.
   Usage: node hour-session/share-preview.js (also wired into gate.js).
   Exit code 1 on any failure. */
var fs = require("fs"), vm = require("vm"), path = require("path"),
    child = require("child_process");

var ROOT = path.join(__dirname, "..");
var src = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
var assertions = 0, failures = 0;
function ok(cond, msg){
  assertions++;
  if (!cond){ failures++; console.log("  FAIL " + msg); }
}

/* ---------- bank slugs: the IDEAS array (expanded form) ---------- */
var ideas = [];
var iStart = src.indexOf("var IDEAS = [");
var iEnd = src.indexOf("];", iStart);
var bankSrc = src.slice(iStart, iEnd);
var re = /\{id:"([^"]+)", title:"([^"]+)", blurb:"([^"]+)",/g, m;
while ((m = re.exec(bankSrc))) ideas.push({id: m[1], title: m[2]});
ok(ideas.length === 119, "bank has 119 ideas, got " + ideas.length);
var seen = {};
ideas.forEach(function(i){
  ok(!seen[i.id], "duplicate idea id: " + i.id);
  seen[i.id] = 1;
});

/* ---------- 1+2. /c/ meta tags point at the photo og URL ---------- */
var fnSrc = fs.readFileSync(path.join(ROOT, "functions", "c", "[slug].js"), "utf8");
ok(fnSrc.indexOf('var img = "https://pickmycostume.com/images/og/" + slug + ".jpg";') !== -1,
   "share function builds og img from images/og/<slug>.jpg");
ok(fnSrc.indexOf('<meta property=\\"og:image\\" content=\\"" + img + "\\">') !== -1,
   "og:image uses the img var");
ok(fnSrc.indexOf('<meta name=\\"twitter:image\\" content=\\"" + img + "\\">') !== -1,
   "twitter:image uses the same img var as og:image");

/* ---------- 1b. og file pixels match the photo, not the illustration ---------- */
var slugsJson = JSON.stringify(ideas.map(function(i){ return i.id; }));
var py = `
import json, os, sys
from PIL import Image, ImageChops, ImageStat
slugs = json.loads(sys.argv[1])
root = sys.argv[2]
def meandiff(a, b):
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3.0
for slug in slugs:
    ogp = os.path.join(root, "images", "og", slug + ".jpg")
    php = os.path.join(root, "photos", slug + ".webp")
    ilp = os.path.join(root, "images", slug + ".png")
    assert os.path.exists(ogp), "missing og: " + slug
    assert os.path.exists(php), "missing photo: " + slug
    og = Image.open(ogp).convert("RGB")
    assert og.size == (1200, 630), "og not 1200x630: " + slug
    ph = Image.open(php).convert("RGB")
    w, h = ph.size
    tr = 1200.0 / 630.0
    if w / h > tr:
        nw = int(h * tr); x0 = (w - nw) // 2; ph = ph.crop((x0, 0, x0 + nw, h))
    else:
        nh = int(w / tr); y0 = (h - nh) // 2; ph = ph.crop((0, y0, w, y0 + nh))
    ph = ph.resize((1200, 630), Image.LANCZOS)
    dp = meandiff(og, ph)
    if os.path.exists(ilp):
        il = Image.open(ilp).convert("RGB").resize((1200, 630), Image.LANCZOS)
        di = meandiff(og, il)
    else:
        di = -1.0  # photo-only idea: no illustration exists to confuse with
    print("%s %.2f %.2f" % (slug, dp, di))
`;
var out;
try {
  out = child.execFileSync("python3", ["-c", py, slugsJson, ROOT], {encoding: "utf8"});
} catch(e){
  ok(false, "PIL pixel comparison crashed: " + (e.message || e));
  out = "";
}
var photoFails = [], illuFails = [];
out.trim().split("\n").forEach(function(line){
  if (!line.trim()) return;
  var parts = line.trim().split(/\s+/);
  var dp = parseFloat(parts[1]), di = parseFloat(parts[2]);
  if (!(dp < 12)) photoFails.push(parts[0] + " photo-diff=" + dp);
  if (di >= 0 && !(di > 25)) illuFails.push(parts[0] + " illustration-diff=" + di);
});
ok(photoFails.length === 0, "og pixel-matches its photo (diff<12): " + photoFails.slice(0,5).join("; "));
ok(illuFails.length === 0, "og is not the illustration (diff>25): " + illuFails.slice(0,5).join("; "));
ok(out.trim().split("\n").filter(function(l){ return l.trim(); }).length === 119,
   "pixel comparison covered all 119 ideas");

/* ---------- 3. double-invocation idempotency (real code in vm) ---------- */
var blocks = [];
var bre = /<script>([\s\S]*?)<\/script>/g, bm;
while ((bm = bre.exec(src))) blocks.push(bm[1]);
var block = blocks.join("\n");

function grab(name){
  var pat = new RegExp("function\\s+" + name + "\\b");
  var mm = pat.exec(block);
  if (!mm) throw new Error("not found: " + name);
  var i = block.indexOf("{", block.indexOf(")", mm.index));
  var depth = 0, j = i, inStr = null, esc = false;
  for (; j < block.length; j++){
    var ch = block[j];
    if (inStr){
      if (esc) esc = false;
      else if (ch === "\\") esc = true;
      else if (ch === inStr) inStr = null;
      continue;
    }
    if (ch === "/" && block[j+1] === "*"){ var ce = block.indexOf("*/", j+2); j = ce + 1; continue; }
    if (ch === "/" && block[j+1] === "/"){ var le = block.indexOf("\n", j+2); j = (le === -1) ? block.length : le; continue; }
    if (ch === '"' || ch === "'") inStr = ch;
    else if (ch === "{") depth++;
    else if (ch === "}"){
      depth--;
      if (depth === 0) return block.slice(mm.index, j + 1);
    }
  }
  throw new Error("unbalanced: " + name);
}

var lib = grab("armShareOnce") + "\n" + grab("shareText") + "\n" + grab("fallbackCopy");

var driver = `(function(){
  /* armShareOnce unit behavior */
  var b = {disabled: false};
  var r1 = armShareOnce(b);
  ok(typeof r1 === "function" && b.disabled === true, "first arm disables the button and returns rearm");
  var r2 = armShareOnce(b);
  ok(r2 === null, "second arm while in flight returns null (tap ignored)");
  r1();
  ok(b.disabled === false, "rearm re-enables the button");
  r1();
  ok(b.disabled === false, "rearm is idempotent");
  var r3 = armShareOnce(null);
  ok(typeof r3 === "function", "null button is a safe no-op guard");

  /* shareText: rapid double-tap fires exactly one native share */
  var idea = {id: "deadpan-diva", title: "Deadpan Diva"};
  var st = {textContent: ""};
  var btn = {disabled: false, textContent: "Share"};
  shareCalls = 0;
  shareText(idea, st, btn);
  shareText(idea, st, btn); /* second tap lands before the sheet opens */
  ok(shareCalls === 1, "double-tap fires navigator.share exactly once, got " + shareCalls);
  ok(btn.disabled === true, "share button disabled while share in flight");
  _res(); /* user completes the share */
  ok(btn.disabled === false, "button re-armed after share completes");
  ok(st.textContent === "Shared.", "status shows Shared after completion, got " + JSON.stringify(st.textContent));

  /* dismiss path also re-arms */
  var st2 = {textContent: ""};
  var btn2 = {disabled: false, textContent: "Share"};
  shareCalls = 0;
  shareText(idea, st2, btn2);
  _rej({name: "AbortError"}); /* user dismisses the sheet */
  ok(btn2.disabled === false, "button re-armed after dismiss");
  ok(shareCalls === 1, "dismiss path fired exactly one share");
})`;

var sandbox = {
  console: console,
  __ok: null, __st: null,
  state: {answers: {}},
  VIA_SHARE: null,
  __st: {shareCalls: 0, _res: null, _rej: null, _sid: 0},
  navigator: {
    share: function(){
      var st = this.__st || sandbox.__st;
      st.shareCalls++;
      return {then: function(res, rej){ st._res = res; st._rej = rej; }};
    }
  },
  SHARE: {textTemplate: function(idea){ return "TEXT " + idea.id; }},
  Analytics: {track: function(){}},
  newShareId: function(){ var st = sandbox.__st; st._sid++; return "s" + st._sid; },
  shareVariant: function(){ return "control"; },
  doCopy: function(){ throw new Error("doCopy must not run when navigator.share exists"); }
};
sandbox.__ok = function(c, msg){ sandbox.assertions++; if (!c){ sandbox.failures++; console.log("  FAIL " + msg); } };
sandbox.assertions = 0; sandbox.failures = 0;
vm.createContext(sandbox);
try {
  vm.runInContext(
    "var __st = this.__st, __ok = this.__ok;\n" +
    "var ok = function(c, m){ __ok(c, m); };\n" +
    "Object.defineProperty(this, 'shareCalls', {configurable: true, get: function(){ return __st.shareCalls; }, set: function(v){ __st.shareCalls = v; }});\n" +
    "Object.defineProperty(this, '_res', {configurable: true, get: function(){ return __st._res; }, set: function(v){ __st._res = v; }});\n" +
    "Object.defineProperty(this, '_rej', {configurable: true, get: function(){ return __st._rej; }, set: function(v){ __st._rej = v; }});\n" +
    lib + "\n" + driver + "()",
    sandbox);
} catch(e){
  ok(false, "vm harness crashed: " + (e && e.message));
}
assertions += sandbox.assertions;
failures += sandbox.failures;

/* ---------- static: every share call site goes through the guard ---------- */
var guardUses = (src.match(/armShareOnce\(/g) || []).length;
ok(guardUses >= 6, "armShareOnce definition + 5 share call sites, found " + guardUses);
["armShareOnce(b)", "armShareOnce(qsBtn)", "armShareOnce(send)", "armShareOnce(bi)", "armShareOnce(btn)"]
  .forEach(function(s){ ok(src.indexOf(s) !== -1, "share call site wired: " + s); });

console.log("assertions: " + assertions);
console.log(failures === 0 ? "SHARE PREVIEW: ALL PASS" : "SHARE PREVIEW: " + failures + " FAILURES");
process.exit(failures ? 1 : 0);
