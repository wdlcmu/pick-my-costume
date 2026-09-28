/* Bank-level toddler-safety gate (2026-09-27 kidunder3 audit).
 *
 * Why this exists: two red-teams found the same defect class on two
 * surfaces -- classic-ghost carried kidunder3:1 in the bank, and every
 * surface that filters on the tag (main quiz, gift flow, sibling draft,
 * kid article, MCP bank consumers) trusted it blindly and served a
 * sheet-over-the-head costume to under-3s. The tag was a data error:
 * the bank's own sizing note admits toddlers trip on ghost hems, and the
 * kid article's own copy says toddlers shouldn't wear face-covering
 * costumes. The systemic fix is the bank tag itself, not per-surface
 * blocklists -- this gate makes the invariant fail-loud so no future
 * bank edit can reintroduce it.
 *
 * Invariants:
 *  1. No idea with scary>=1 may carry the kidunder3 tag, in EITHER bank
 *     copy (index.html IDEAS, mcp-server/bank.json). Scary picks for
 *     toddlers are banned by the quiz filter; the tag must never be the
 *     loophole that re-admits them.
 *  2. classic-ghost (scary:2) must never appear in the top 3 of a
 *     kid + "Under 3" or kid + "Mixed ages" quiz path.
 *  3. Age tags (kidunder3/kid36/kid7plus) must be identical across the
 *     two bank copies -- a fix in one copy but not the other is a silent
 *     fork.
 *  4. Both banks hold 137 unique ids.
 */
var fs = require('fs');
var ROOT = process.env.HOME + '/workspace/builds/pick-my-costume/';
var failures = [];
function fail(m){ failures.push(m); }
function ok(c, m){ if (!c) fail(m); }

/* ---- bank copy 1: index.html IDEAS ---- */
var src = fs.readFileSync(ROOT + 'index.html', 'utf8');
function extract(a, b){ var x = src.indexOf(a), y = src.indexOf(b, x); if (x < 0 || y < 0) throw new Error('miss ' + a.slice(0, 30)); return src.slice(x, y); }
var state = { qi: 0, answers: {} };
eval(extract('var QUESTIONS = [', '/* ================= CONFIG: IDEAS'));
eval(extract('var IDEAS = [', '/* ================= CONFIG: SHARE'));
var htmlIdeas = IDEAS;

/* ---- bank copy 2: mcp-server/bank.json ---- */
var mcp = JSON.parse(fs.readFileSync(ROOT + 'mcp-server/bank.json', 'utf8'));
var mcpIdeas = mcp.ideas || mcp.IDEAS;
var mcpById = {};
mcpIdeas.forEach(function(i){ mcpById[i.id] = i; });

/* ---- invariant 4: 144 unique each, same ids ---- */
ok(htmlIdeas.length === 144, 'index.html IDEAS count=' + htmlIdeas.length + ', want 144');
ok(mcpIdeas.length === 144, 'bank.json ideas count=' + mcpIdeas.length + ', want 144');
var htmlIds = htmlIdeas.map(function(i){ return i.id; });
ok(new Set(htmlIds).size === 144, 'index.html IDEAS has duplicate ids');
ok(new Set(mcpIdeas.map(function(i){ return i.id; })).size === 144, 'bank.json has duplicate ids');

/* ---- invariant 1: scary>=1 must never carry kidunder3 ---- */
[['index.html', htmlIdeas], ['bank.json', mcpIdeas]].forEach(function(pair){
  var name = pair[0];
  pair[1].forEach(function(i){
    var t = i.tags || {};
    if ((t.scary || 0) >= 1 && (t.kidunder3 || 0) > 0){
      fail(name + ': ' + i.id + ' has scary=' + t.scary + ' AND kidunder3=' + t.kidunder3 + ' (toddler-unsafe tag)');
    }
  });
});

/* ---- invariant 3: age tags in sync across copies ---- */
htmlIdeas.forEach(function(i){
  var m = mcpById[i.id];
  if (!m){ fail('bank.json missing id ' + i.id); return; }
  ['kidunder3', 'kid36', 'kid7plus'].forEach(function(k){
    var a = (i.tags || {})[k] || 0, b = (m.tags || {})[k] || 0;
    if (a !== b) fail('age-tag drift on ' + i.id + '.' + k + ': index.html=' + a + ' bank.json=' + b);
  });
});

/* ---- invariant 2: quiz-level -- classic-ghost never in under-3 top 3 ---- */
eval(extract('function qById(id)', '/* ================= SCREENS'));
eval(extract('function flowOrder(){', '/* ================= SCREENS'));
eval(extract('function scoreIdeas(', '/* ================= SCREENS'));
function extractFn(s, name){
  var marker = 'function ' + name + '(';
  var start = s.indexOf(marker);
  if (start < 0) throw new Error('missing fn ' + name);
  var i = s.indexOf('{', start), depth = 0, end = -1;
  for (var j = i; j < s.length; j++){
    if (s[j] === '{') depth++;
    else if (s[j] === '}'){ depth--; if (depth === 0){ end = j + 1; break; } }
  }
  if (end < 0) throw new Error('unbalanced ' + name);
  return s.slice(start, end);
}
function planMinutes(){ return null; }
function planCostMax(){ return null; }
var ccStart = src.indexOf('var CONSTRAINT_CHIPS = [');
eval(src.slice(ccStart, src.indexOf('];', ccStart) + 2));
eval(extractFn(src, 'constraintOk'));
eval(extractFn(src, 'applyConstraints'));
eval(extractFn(src, 'kidAgeNeeded'));

var kidOpt = qById('q1').options.filter(function(o){ return o.value === 'kid'; })[0];
var ageOpts = qById('q5kid').options;
var under3 = ageOpts.filter(function(o){ return o.label === 'Under 3'; })[0];
var mixed = ageOpts.filter(function(o){ return o.label === 'Mixed ages'; })[0];
var q2 = qById('q2').options, q4 = qById('q4').options;
var qocc = qById('qocc').options.filter(function(o){ return o.value !== 'bar'; });
var qint = qById('qinterest').options.filter(function(o){ return !o.aud || o.aud.indexOf('kid') !== -1; });

var paths = 0, ghostHits = 0, scaryHits = 0, shortRes = 0;
q2.forEach(function(o2){ q4.forEach(function(o4){ qocc.forEach(function(oo){ qint.forEach(function(oi){
  [under3, mixed].forEach(function(age){
    paths++;
    state.answers = { q1: kidOpt, q2: o2, q4: o4, qocc: oo, qinterest: oi, q5kid: age };
    var res = scoreIdeas();
    if (res.length < 3){ shortRes++; fail('SHORT under-3/mixed results: ' + [o2.label, o4.label, oo.label, oi.label, age.label].join('/') + ' -> ' + res.length); return; }
    res.slice(0, 3).forEach(function(s){
      var t = s.idea.tags || {};
      if (s.idea.id === 'classic-ghost'){ ghostHits++; fail('classic-ghost in under-3/mixed top 3: ' + [o2.label, o4.label, oo.label, oi.label, age.label].join('/')); }
      if ((t.scary || 0) >= 1 && !((t.kidunder3 || 0) > 0)){ scaryHits++; fail('scary-unsafe in under-3/mixed top 3: ' + s.idea.id); }
    });
  });
});});});});

console.log('bank-safety-gate: paths=' + paths + ' ghost-in-top3=' + ghostHits + ' scary-unsafe=' + scaryHits + ' short=' + shortRes);
if (failures.length){
  console.error('BANK SAFETY GATE FAIL (' + failures.length + '):');
  failures.slice(0, 20).forEach(function(f){ console.error('  - ' + f); });
  process.exit(1);
}
console.log('BANK SAFETY GATE PASS');
