/* Bank triple sync gate (2026-09-29 #23 drift postmortem).
 *
 * Why this exists: three-way drift -- the /c/ chips said "10 min" (from
 * [slug].js), the og badge baked "15 min + drying" from a stale
 * mcp-server/bank.json, and the card file was stale even against that.
 * index.html's INSTRUCTIONS is the canonical single source of truth; the
 * MCP worker's bank.json is rebuilt from it via `npm run build`
 * (mcp-server/scripts/build-bank.mjs). If bank.json is ever rebuilt from
 * a stale index.html, or hand-edited, the MCP tools start quoting
 * different times/costs/efforts than the quiz and share pages.
 *
 * Invariant: for every idea, bank.json instructions[slug].time/cost/effort
 * === index.html INSTRUCTIONS[slug].time/cost/effort. Same id sets both
 * sides. Fail loudly so the copies can never fork silently again.
 */
var fs = require("fs");
var ROOT = process.env.HOME + "/workspace/builds/pick-my-costume/";
var failures = [];
function fail(m){ failures.push(m); }
function ok(c, m){ if (!c) fail(m); }

var src = (function(){
  /* 2026-09-30: the inline script moved to /app.js (defer); the bank lives
     there now. index.html fallback kept for history. */
  try { return fs.readFileSync(ROOT + "app.js", "utf8"); }
  catch (e) { return fs.readFileSync(ROOT + "index.html", "utf8"); }
})();

/* Brace-match var INSTRUCTIONS (same technique as gen_share_function.py). */
function extractInstructions(s){
  var marker = "var INSTRUCTIONS =";
  var i = s.indexOf("{", s.indexOf(marker) + len(marker));
  var depth = 0, instr = false, esc = false;
  for (var j = i; j < s.length; j++){
    var c = s[j];
    if (instr){
      if (esc) esc = false;
      else if (c === "\\") esc = true;
      else if (c === '"') instr = false;
      continue;
    }
    if (c === '"') instr = true;
    else if (c === "{") depth++;
    else if (c === "}"){
      depth--;
      if (depth === 0) return s.slice(i, j + 1);
    }
  }
  throw new Error("INSTRUCTIONS object not balanced");
}
function len(x){ return x.length; }

var insRaw = extractInstructions(src)
  .replace(/,\s*([}\]])/g, "$1");  // trailing commas -> strict JSON
var htmlInstr = JSON.parse(insRaw);

var bank = JSON.parse(fs.readFileSync(ROOT + "mcp-server/bank.json", "utf8"));
var bankInstr = bank.instructions || {};

var htmlIds = Object.keys(htmlInstr).sort();
var bankIds = Object.keys(bankInstr).sort();
ok(htmlIds.length === 164, "index.html INSTRUCTIONS entries=" + htmlIds.length + ", want 164");
ok(bankIds.length === 164, "bank.json instructions entries=" + bankIds.length + ", want 164");

var missing = htmlIds.filter(function(id){ return bankIds.indexOf(id) < 0; });
var extra = bankIds.filter(function(id){ return htmlIds.indexOf(id) < 0; });
missing.forEach(function(id){ fail("bank.json missing instructions for " + id); });
extra.forEach(function(id){ fail("bank.json has instructions for unknown id " + id); });

/* The sync invariant: decision triple identical in both copies. */
["time", "cost", "effort"].forEach(function(k){
  htmlIds.forEach(function(id){
    var a = (htmlInstr[id] || {})[k];
    var b = (bankInstr[id] || {})[k];
    if (a !== b) fail("triple drift on " + id + "." + k +
      ": index.html=" + JSON.stringify(a) + " bank.json=" + JSON.stringify(b));
  });
});

console.log("bank-triple-sync-gate: compared " + htmlIds.length + " ideas x 3 fields");
if (failures.length){
  console.error("TRIPLE SYNC GATE FAIL (" + failures.length + "):");
  failures.slice(0, 20).forEach(function(f){ console.error("  - " + f); });
  process.exit(1);
}
console.log("BANK TRIPLE SYNC GATE PASS");
