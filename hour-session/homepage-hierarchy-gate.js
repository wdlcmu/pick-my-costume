/* Homepage hierarchy regression gate for Pick My Costume (rewritten 2026-10-01,
 * galaxy-detour clause updated 2026-10-04).
 * The shipped information architecture (Oct 3 - Oct 4):
 *   quiz hero (slim: headline + one button + no-signup line -- Billy 2026-10-03
 *   simplification dropped the countdown, honestline, and galaxy detour out
 *   of the hero; the galaxy keeps its nav link for explorers)
 *   -> explore (pantry + play + tools)
 * The Sep 27 contract (pantry-only visible secondary, collapsed <details>
 * "More tools:") is superseded: the explore section is now a 5-tab tool row
 * with hidden panels, a visible kid-games bar, and a visible pantry link.
 * Deliberate removals this gate locks in: #trending-line (Sep 30 delight),
 * the "Trending this week" text prefix, the old <details> "More tools:"
 * disclosure, the hidden roulette entry, and the galaxy hero detour
 * (Billy 2026-10-03). The 2026-10-13 restructure (Billy-approved) also
 * removed the hidden #row-trending rail and the "More" expander that buried
 * the FAQ and tools; section 5 now asserts the approved replacement
 * structure (visible FAQ, labeled Tools row, real footer) instead.
 * Static DOM checks (no jsdom): the hierarchy is a static-HTML contract.
 * Exit code: 0 pass, 1 fail. Wired into run-gates.sh.
 */
var fs = require('fs');
var path = require('path');

var REPO = process.env.REPO || path.join(__dirname, '..');
var html = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');
var failures = 0;
function fail(msg) { failures++; console.log('FAIL | ' + msg); }
function ok(msg) { console.log('PASS | ' + msg); }

/* ---- 1. quiz hero: the quiz is the primary CTA ---- */
var heroMatch = html.match(/<section class="screen on" id="s-hero">([\s\S]*?)<\/section>/);
if (!heroMatch) { fail('s-hero section not found'); }
else {
  var hero = heroMatch[1];
  if (hero.indexOf('id="btn-start"') === -1) fail('hero lost the quiz entry (#btn-start)');
  else ok('quiz hero keeps #btn-start as the primary CTA');
}

/* ---- 2. galaxy detour out of the hero (Billy 2026-10-03 simplification);
        the galaxy keeps its nav link for explorers ---- */
var heroHtml = heroMatch ? heroMatch[1] : '';
if (/Rather wander/.test(heroHtml))
  fail('galaxy detour returned to the hero (deliberately removed 2026-10-03)');
else ok('hero stays slim: no galaxy detour (Billy 2026-10-03)');
if (!/href="\/map\/"/.test(html)) fail('galaxy lost its nav link (/map/)');
else ok('galaxy keeps its nav link (/map/) for explorers');

/* ---- 3. explore section: 5 tool tabs, panels hidden ---- */
var exploreMatch = html.match(/<div class="explore">([\s\S]*?)<\/div>\s*<!--/);
if (!exploreMatch) { fail('explore section not found'); }
else {
  var explore = exploreMatch[1];
  var tabs = ['toolt-handmedown', 'toolt-flyer', 'toolt-browse', 'toolt-planner', 'toolt-shuffle'];
  var missing = tabs.filter(function (t) { return explore.indexOf('id="' + t + '"') === -1; });
  if (missing.length) fail('tool tabs missing: ' + missing.join(', '));
  else ok('explore has all 5 tool tabs (handmedown/flyer/browse/planner/shuffle)');
  var panels = ['toolpanel-handmedown', 'toolpanel-flyer', 'toolpanel-browse', 'toolpanel-planner', 'toolpanel-shuffle'];
  var openPanels = panels.filter(function (p) {
    var m = explore.match(new RegExp('<div[^>]*id="' + p + '"[^>]*>'));
    return m && !/\bhidden\b/.test(m[0]);
  });
  if (openPanels.length) fail('tool panels visible on load: ' + openPanels.join(', '));
  else ok('all 5 tool panels hidden on load');
  /* old <details> "More tools:" disclosure is gone */
  if (/<details/.test(explore)) fail('old collapsed <details> still present in explore');
  else ok('old <details> "More tools:" disclosure gone');
  if (explore.indexOf('More tools:') !== -1) fail('"More tools:" label returned');
  else ok('no "More tools:" label');
}

/* ---- 4. kid-games bar + pantry link visible in explore ---- */
if (!/\/play\?game=peekaboo/.test(html) || !/\/play\?game=match/.test(html) || !/\/play\?game=chopped/.test(html))
  fail('kid-games bar missing a game link (/play?game=peekaboo|match|chopped)');
else ok('kid-games bar visible with all 3 game links');
if ((html.match(/href="\/pantry"/g) || []).length < 1) fail('no visible /pantry link in explore');
else ok('pantry link visible in explore');

/* ---- 5. deliberate removals: #trending-line, text prefix, old details ---- */
if (html.indexOf('id="trending-line"') !== -1) fail('#trending-line returned (deliberately removed 2026-09-30)');
else ok('#trending-line stays removed');
/* "Trending this week" may appear only inside the HTML comment documenting
   its removal — never as visible copy. */
var stripped = html.replace(/<!--[\s\S]*?-->/g, '');
if (stripped.indexOf('Trending this week') !== -1) fail('"Trending this week" text prefix returned as visible copy');
else ok('no "Trending this week" text prefix');
/* 2026-10-13 restructure (Billy-approved): the hidden #row-trending rail and
   the "More" expander that buried the FAQ + tools are gone for good. The
   approved structure in their place: a visible FAQ section, the labeled
   Tools entries, and a real footer. Assert the new structure is present and
   the burial stays gone. */
if (html.indexOf('id="row-trending"') !== -1) fail('#row-trending returned (removed with the More expander 2026-10-13)');
else ok('hidden #row-trending rail stays removed');
if (html.indexOf('id="faq"') === -1) fail('FAQ section (#faq) missing');
else ok('FAQ section visible on the page');
if (html.indexOf('Is it really free?') === -1) fail('FAQ lost the "Is it really free?" question');
else ok('FAQ includes "Is it really free?"');
var toolLabels = ['Closet refresh', 'Printables', 'Explore the galaxy', 'Halloween plan', 'Role shuffle'];
var missingTools = toolLabels.filter(function (l) { return html.indexOf(l) === -1; });
if (missingTools.length) fail('Tools entries missing: ' + missingTools.join(', '));
else ok('Tools section has all 5 labeled entries');
var footMatch = html.match(/<footer[\s\S]*?<\/footer>/);
if (!footMatch) fail('footer missing');
else {
  var footMissing = [];
  if (footMatch[0].indexOf('href="/about"') === -1) footMissing.push('About link');
  if (footMatch[0].indexOf('href="/privacy"') === -1) footMissing.push('Privacy link');
  if (footMatch[0].indexOf('Built with Muse.') === -1) footMissing.push('"Built with Muse." credit');
  if (footMissing.length) fail('footer missing: ' + footMissing.join(', '));
  else ok('footer present with About, Privacy, and "Built with Muse."');
}
if (html.indexOf('id="more-body"') !== -1 || html.indexOf('id="more-wrap"') !== -1 || html.indexOf('id="more-opts"') !== -1)
  fail('More expander returned (FAQ/tools burial)');
else ok('More expander stays removed (no burial)');

/* ---- 6. roulette entry stays hidden ---- */
var spinHidden = /<p[^>]*\bhidden\b[^>]*>\s*<button[^>]*id="btn-spin"/.test(html);
if (!spinHidden) fail('roulette entry #btn-spin is not inside a hidden wrapper');
else ok('roulette entry stays hidden');

/* ---- 7. no closet link; pantry CTA count sane ---- */
if (/href="\/closet"|href="closet|\/closet"/.test(html)) fail('closet link returned');
else ok('no closet link anywhere');
var pantryCount = (html.match(/href="\/pantry"/g) || []).length;
if (pantryCount > 5) fail('too many /pantry links (' + pantryCount + '); CTA clutter is back');
else ok('/pantry link count sane (' + pantryCount + ')');

/* ---- 8. the killed hero count does not return ---- */
var killed = ['5 questions to see if we', 'see if we\u2019re right', 'see if we\'re right'];
var found = killed.filter(function (s) { return html.indexOf(s) !== -1; });
if (found.length) fail('killed hero count returned: ' + found.join(', '));
else ok('killed hero count stays dead');

/* ---- 9. no invented usage count in visible copy ---- */
var invented = stripped.match(/(\d{1,3}(,\d{3})+|\d+k)\s+(parents|families|people|users|visitors)\s+(use|love|picked|chose|trust)/i);
if (invented) fail('invented usage count in visible copy: ' + invented[0]);
else ok('no invented usage count');

if (failures) { console.log('HOMEPAGE HIERARCHY GATE: ' + failures + ' FAILURES'); process.exit(1); }
console.log('HOMEPAGE HIERARCHY GATE: ALL CHECKS PASS');
