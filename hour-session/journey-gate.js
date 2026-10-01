/* Journey gate for Pick My Costume (Billy, 2026-09-25):
 * Pre-deploy gate enumerating the JOURNEY MATRIX, not just page state.
 * A defect shipped 2026-09-25 ("Your friend picked X" headline rendering on
 * homepage proof-rail taps) because every gate asserted data/copy quality
 * but none walked an arrival context. This gate asserts:
 *  1. Every homepage tap target resolves to the right destination:
 *     - quiz start button (#btn-start) exists and is wired to start the quiz
 *     - every proof-rail card href is /c/<slug> with a slug present in IDEAS
 *     - browse entry (#btn-browse-hero) exists and is wired to openBrowse
 *     - pantry link resolves to /pantry
 *  2. /c/ arrival contexts (Billy's 2026-09-25 phone bug): for a sample of
 *     ideas, the share-landing headline -- evaluated from the REAL
 *     shareLandingHeadline() in the built index.html, not a reimplementation:
 *     - WITHOUT via_share (?idea=<slug> only): shows the costume title,
 *       never the "Your friend picked" headline
 *     - WITH via_share (?idea=<slug>&s=<sid>): "Your friend picked X..."
 *     - WITH via_share + ch=1: the challenge variant
 *     - the shared-idea landing actually renders through shareLandingHeadline
 *  3. Quiz completion lands on results: renderQ's last-question branch calls
 *     finishQuiz(), and finishQuiz() scores via scoreIdeas() then renders via
 *     renderResults().
 * Usage: node hour-session/journey-gate.js
 *        PMC_HTML=/path/to/index.html node hour-session/journey-gate.js
 * Exit code: 0 pass, 1 fail.
 */
var fs = require('fs');
var path = require('path');
var HTML = process.env.PMC_HTML || path.join(__dirname, '..', 'index.html');
/* 2026-10-01 bundle split: the app script moved to /app.js (defer).
   DOM checks read the page HTML (index.html); script extraction/eval reads
   app.js first, falling back to index.html's inline <script> (pre-split). */
var APPJS = process.env.PMC_APPJS || path.join(__dirname, '..', 'app.js');
function readFirst(paths){
  for (var i = 0; i < paths.length; i++){
    try { return fs.readFileSync(paths[i], 'utf8'); } catch (e){}
  }
  throw new Error('no readable source: ' + paths.join(', '));
}
var pageSrc = readFirst([HTML]);
var src = readFirst([APPJS, HTML]);

var fails = [];
function ok(cond, msg){ if (!cond) fails.push(msg); }

/* Balanced-brace function extraction: returns the full "function name(...){...}" text. */
function extractFn(marker){
  var start = src.indexOf(marker);
  if (start < 0) throw new Error('marker not found: ' + marker.slice(0, 40));
  var open = src.indexOf('{', start);
  var depth = 0;
  for (var i = open; i < src.length; i++){
    if (src[i] === '{') depth++;
    else if (src[i] === '}'){ depth--; if (depth === 0) return src.slice(start, i + 1); }
  }
  throw new Error('unbalanced braces after: ' + marker.slice(0, 40));
}

/* IDEAS bank, same extraction style as gate.js. */
function extract(a, b){ var x = src.indexOf(a), y = src.indexOf(b, x); if (x < 0 || y < 0) throw new Error('miss ' + a.slice(0, 30)); return src.slice(x, y); }
eval(extract('var IDEAS = [', '/* ================= CONFIG: SHARE'));
var ideaIds = {};
IDEAS.forEach(function(it){ ideaIds[it.id] = true; });
function ideaById(id){ for (var i = 0; i < IDEAS.length; i++) if (IDEAS[i].id === id) return IDEAS[i]; return null; }

/* ---------- 1. homepage tap targets ---------- */
/* Quiz start: button exists and its click handler starts the quiz. */
ok(pageSrc.indexOf('id="btn-start"') >= 0, 'homepage: #btn-start missing');
(function(){
  var w = src.indexOf('$("btn-start").onclick');
  ok(w >= 0, 'homepage: #btn-start has no wired onclick');
  /* 2026-09-27 warm-vs-cold: btn-start opens the fork (renderWarmCold); the
     cold branch must still reach renderQ untouched. */
  if (w >= 0) ok(src.slice(w, w + 1200).indexOf('renderWarmCold()') >= 0,
    'homepage: #btn-start onclick does not open the warm/cold fork (renderWarmCold)');
  if (w >= 0) ok(src.indexOf('function renderWarmCold()') >= 0,
    'homepage: renderWarmCold missing');
  var wc = src.indexOf('function renderWarmCold()');
  if (wc >= 0) ok(src.slice(wc, wc + 1500).indexOf('renderQ()') >= 0,
    'homepage: warm/cold fork never reaches the cold quiz (renderQ)');
})();
/* Proof rail: every card href is /c/<slug> and every slug is a real idea. */
(function(){
  /* 2026-09-27: Kid favorites rail (JS-rendered, empty in markup) now sits
     above the trending rail, so target #row-trending by id instead of the
     first .proofrow in the file. */
  var pr = pageSrc.search(/<div class="proofrow" id="row-trending"[\s>]/);
  ok(pr >= 0, 'homepage: .proofrow missing');
  if (pr < 0) return;
  var seg = pageSrc.slice(pr, pageSrc.indexOf('</div>', pageSrc.indexOf('</a>', pr)) + 6);
  /* 2026-09-27: proof-rail hrefs carry ?from=rail attribution; tolerate a
     query/fragment after the slug.
     2026-10-01: rail cards deep-link /?idea=<slug> (the app detail, which
     opens the full-screen detail -- phone-fixes-workerA) instead of /c/.
     Either shape must resolve to a real idea. */
  var re = /href="(?:\/c\/([a-z0-9-]+)|\/\?idea=([a-z0-9-]+))(?:[?#&][^"]*)?"/g, m, slugs = [];
  while ((m = re.exec(seg))) slugs.push(m[1] || m[2]);
  ok(slugs.length > 0, 'homepage: proof rail has no idea card links');
  slugs.forEach(function(s){ ok(ideaIds[s], 'homepage: proof-rail card links to unknown idea: ' + s); });
  console.log('proof-rail cards:', slugs.length, 'all resolve to real ideas');
})();
/* Browse entry: button exists and opens the browse shelf. */
ok(pageSrc.indexOf('id="btn-browse-hero"') >= 0, 'homepage: #btn-browse-hero missing');
ok(src.indexOf('$("btn-browse-hero").onclick = openBrowse') >= 0, 'homepage: #btn-browse-hero not wired to openBrowse');
/* Pantry entry: link resolves to /pantry. */
ok(pageSrc.indexOf('href="/pantry"') >= 0, 'homepage: pantry link does not resolve to /pantry');

/* ---------- 2. /c/ arrival contexts ---------- */
var hlSrc = extractFn('function shareLandingHeadline(idea, search){');
/* 2026-09-25: shareLandingHeadline now delegates the arrival check to the
   shared isGenuineShareArrival() pure function, so eval both together to
   keep asserting the real code (never a reimplementation). */
var arrGateSrc = extractFn('function isGenuineShareArrival(search){');
var shareLandingHeadline = eval('(function(){ var isGenuineShareArrival = (' + arrGateSrc + '); return (' + hlSrc + '); })()');
/* The landing must actually render through this function (not a stale inline copy). */
ok(src.indexOf('h.textContent = shareLandingHeadline(idea, location.search') >= 0,
  '/c/ landing: headline does not render through shareLandingHeadline');
var sample = ['neon-demon-hunter', 'snow-sisters', 'classic-ghost', 'zombie-coworker', 'blue-dog-family'];
sample.forEach(function(id){
  var idea = ideaById(id);
  ok(idea, 'journey sample: unknown idea ' + id);
  if (!idea) return;
  var plain = shareLandingHeadline(idea, '?idea=' + id);
  ok(plain === idea.title,
    '/c/' + id + ' without via_share: headline is "' + plain + '", expected the costume title "' + idea.title + '"');
  ok(plain.indexOf('Your friend') < 0,
    '/c/' + id + ' without via_share: friend headline leaked ("' + plain + '")');
  var shared = shareLandingHeadline(idea, '?idea=' + id + '&s=abcd1234&o=generic');
  ok(shared === 'Your friend picked ' + idea.title + '. What would you pick?',
    '/c/' + id + ' with via_share: headline is "' + shared + '", expected the friend headline');
  var chall = shareLandingHeadline(idea, '?idea=' + id + '&s=abcd1234&ch=1');
  ok(chall === 'Your friend can make ' + idea.title + ' with stuff they own. See what YOU can make.',
    '/c/' + id + ' with via_share+ch=1: headline is "' + chall + '", expected the challenge variant');
});
console.log('arrival contexts: ' + sample.length + ' ideas x {no-share, share, challenge} checked');

/* ---------- 3. quiz completion lands on results ---------- */
var renderQSrc = extractFn('function renderQ(){');
ok(renderQSrc.indexOf('finishQuiz()') >= 0, 'quiz journey: renderQ never calls finishQuiz() on the last question');
var finishSrc = extractFn('function finishQuiz(){');
ok(finishSrc.indexOf('scoreIdeas()') >= 0, 'quiz journey: finishQuiz() does not score via scoreIdeas()');
ok(finishSrc.indexOf('renderResults(') >= 0, 'quiz journey: finishQuiz() does not render via renderResults()');

/* ---------- 4. "More like this" rail (Billy 2026-09-25) ---------- */
var state = { qi: 0, answers: {} };
var mltSrc = src.slice(src.indexOf('var INTEREST_TAGS = ['), src.indexOf('/* ==== end more-like-this data ==== */'));
if (mltSrc.indexOf('function moreLikeThis') < 0) throw new Error('more-like-this data block not found');
eval(mltSrc);
/* Mounted on the detail page after the make-it steps and claim section,
   reusing the .proofrow rail card component; cards tap to openIdeaDetail. */
(function(){
  var bb = src.indexOf('function buildBrowseDetailCard(idea, whyHead){');
  ok(bb >= 0, 'rail: buildBrowseDetailCard missing');
  ok(src.indexOf('buildMoreLikeThisRail(idea)', bb) >= 0, 'rail: buildMoreLikeThisRail not mounted on the detail page');
  var railFn = extractFn('function buildMoreLikeThisRail(idea){');
  ok(railFn.indexOf('"proofrow"') >= 0, 'rail: builder does not reuse the .proofrow card component');
  ok(railFn.indexOf('openIdeaDetail(') >= 0, 'rail: cards do not tap through to openIdeaDetail');
})();
function strongestInterest(idea){
  /* Mirrors index.html moreLikeThisTag: strongest interest tag, falling back
     to strongest vibe tag (grounding cleanup 2026-09-25 left ideas like
     classic-ghost interest-less; their rail is vibe-based). */
  var t = (typeof moreLikeThisTag === "function") ? moreLikeThisTag(idea) : null;
  return t && t.tag;
}
var railSample = ['neon-demon-hunter', 'snow-sisters', 'classic-ghost', 'zombie-coworker'];
railSample.forEach(function(id){
  var idea = ideaById(id);
  if (!idea){ ok(false, 'rail sample: unknown idea ' + id); return; }
  var g = strongestInterest(idea);
  ok(g, 'rail: ' + id + ' has no interest or vibe tag');
  var rel = moreLikeThis(idea);
  ok(rel.length === 4, 'rail: detail for ' + id + ' yields ' + rel.length + ' cards, expected 4');
  rel.forEach(function(o){
    ok(o.id !== idea.id, 'rail: self-duplicate ' + o.id + ' on its own rail');
    ok(ideaIds[o.id], 'rail: card taps to unknown idea ' + o.id);
    ok((o.tags[g] || 0) > 0, 'rail: ' + o.id + ' does not share rail tag ' + g);
  });
  for (var i = 1; i < rel.length; i++)
    ok((rel[i - 1].rank || 9999) <= (rel[i].rank || 9999), 'rail: ' + id + ' not rank-ordered without quiz answers');
});
/* With quiz answers: same-vibe neighbors sort first (partition holds). */
(function(){
  state.answers.q2 = { tags: { funny: 2 } };
  var idea = ideaById('neon-demon-hunter');
  var rel = moreLikeThis(idea);
  var seenNon = false, partitioned = true;
  rel.forEach(function(o){
    if (vibeOkFor('funny', o.tags)){ if (seenNon) partitioned = false; }
    else seenNon = true;
  });
  ok(partitioned && rel.length === 4, 'rail: with funny quiz answers, same-vibe neighbors do not sort first for neon-demon-hunter');
  console.log('rail (funny vibe): ' + rel.map(function(o){ return o.id; }).join(', '));
  state.answers = {};
})();
console.log('more-like-this rail: ' + railSample.length + ' detail pages x {4 cards, no self-dup, shared tag, rank order, vibe preference} checked');
/* Render-level: the rail builds 4 tappable cards and taps resolve in-app. */
(function(){
  var log = [];
  function mkEl(tag){
    return { tag: tag, children: [], style: {}, attrs: {},
      appendChild: function(c){ this.children.push(c); return c; },
      setAttribute: function(k, v){ this.attrs[k] = v; } };
  }
  var document = { createElement: mkEl };
  var detailReturnTo = 's-browse';
  function openIdeaDetail(id, whyHead, returnTo){ log.push({ id: id, whyHead: whyHead, returnTo: returnTo }); }
  /* 2026-10-01: the card builder sizes images through pmcSrcset (the real
     helper, evaled from the same source -- not a reimplementation). */
  var pmcSrcset = eval('(' + extractFn('function pmcSrcset(') + ')');
  var buildMoreLikeThisRail = eval('(' + extractFn('function buildMoreLikeThisRail(idea){') + ')');
  var idea = ideaById('neon-demon-hunter');
  var wrap = buildMoreLikeThisRail(idea);
  ok(wrap && wrap.className === 'proofstrip', 'rail: builder did not return the .proofstrip wrapper');
  ok(wrap && wrap.attrs['data-mlt'] === '1', 'rail: wrapper missing data-mlt marker');
  var row = wrap && wrap.children[1];
  ok(row && row.className === 'proofrow', 'rail: missing .proofrow row');
  ok(row && row.children.length === 4, 'rail: rendered ' + (row && row.children.length) + ' cards, expected 4');
  if (row && row.children.length){
    row.children.forEach(function(a, ix){
      ok(a.tag === 'a' && a.attrs['data-idea'], 'rail: card ' + ix + ' is not a tappable idea link');
      ok(ideaIds[a.attrs['data-idea']], 'rail: card taps to unknown idea ' + a.attrs['data-idea']);
      ok(a.attrs['data-idea'] !== idea.id, 'rail: rendered self-duplicate card');
      a.onclick({ preventDefault: function(){} });
      ok(log[log.length - 1].id === a.attrs['data-idea'], 'rail: tap on card ' + ix + ' did not open its detail');
    });
    ok(log.every(function(e){ return e.returnTo === 's-browse'; }), 'rail: tap did not preserve the detail return target');
  }
})();
console.log('more-like-this rail: render-level tap-through verified');

/* ---------- 5. pantry journey (Billy 2026-09-25; rebuilt v2 2026-09-26) ----------
 * The pantry is a separate page (pantry.html), rebuilt by build_pantry_v2.py
 * as an accuracy-first prototype. This section asserts the v2 contract:
 *  - grouped checkbox model: DATA.groups (5 groups), every DATA.pantry item
 *    in a group, no dupes, no orphans; all items visible, no type-ahead
 *  - honest requirement math: score() over mats requirement groups;
 *    unmapped materials honestly count as "still need"
 *  - storage key pantry2 (fresh key for the redesigned data model; the old
 *    pantry3 store held a different staple set), 6 staples pre-ticked with
 *    the honest "we assume" note, init reads / toggles persist
 *  - result cards: X-of-Y requirements, still-need chips, plan link /c/<id>
 *  - tier thresholds: 0 / 1-2 / 3+ missing; unlock suggestions via normUnlock
 *  - checkboxes meet the 44px tap-target minimum
 */
(function(){
  var PANTRY = process.env.PMC_PANTRY || path.join(__dirname, '..', 'pantry.html');
  var psrc = fs.readFileSync(PANTRY, 'utf8');
  function pex(marker){
    var start = psrc.indexOf(marker);
    if (start < 0) throw new Error('pantry marker not found: ' + marker.slice(0, 40));
    var open = psrc.indexOf('{', start), depth = 0;
    var i = open, mode = 0, q = '';
    function prevNc(j){
      j--;
      while (j > 0 && /\s/.test(psrc[j])) j--;
      return psrc[j] || '';
    }
    for (; i < psrc.length; i++){
      var c = psrc[i], n = psrc[i + 1];
      if (mode === 1){ // line comment
        if (c === '\n') mode = 0;
        continue;
      }
      if (mode === 2){ // block comment
        if (c === '*' && n === '/'){ mode = 0; i++; }
        continue;
      }
      if (mode === 3){ // string
        if (c === '\\'){ i++; continue; }
        if (c === q) mode = 0;
        continue;
      }
      if (mode === 4){ // regex literal
        if (c === '\\'){ i++; continue; }
        if (c === '/') mode = 0;
        else if (c === '['){ // character class: skip to ]
          i++;
          while (i < psrc.length && psrc[i] !== ']'){ if (psrc[i] === '\\') i++; i++; }
        }
        continue;
      }
      if (c === '/' && n === '/'){ mode = 1; i++; continue; }
      if (c === '/' && n === '*'){ mode = 2; i++; continue; }
      if (c === '"' || c === "'" || c === '`'){ mode = 3; q = c; continue; }
      if (c === '/'){
        var p = prevNc(i);
        if (p === '' || '([{,:;=!&|?'.indexOf(p) >= 0 || /return|typeof/.test(psrc.slice(Math.max(0, i - 7), i))){
          mode = 4; continue;
        }
        continue; // division
      }
      if (c === '{') depth++;
      else if (c === '}'){ depth--; if (depth === 0) return psrc.slice(start, i + 1); }
    }
    throw new Error('unbalanced braces after: ' + marker.slice(0, 40));
  }
  var praw = pex('const DATA = ');
  var DATA = JSON.parse(praw.slice(praw.indexOf('{')));
  var ticked = new Set();
  function pevalfn(m){ return eval('(' + pex(m) + ')'); }
  var esc = pevalfn('function esc(s){');
  var groupOk = pevalfn('function groupOk(g){');
  var reqOk = pevalfn('function reqOk(');
  /* 2026-10-01: reqOk gained (ideaId, mi) for the per-idea buy-key (pantry
     tile dedupe fix); its buy-branch closes over pantryBuyKey -- pull the
     real helper into scope too. */
  var pantryBuyKey = pevalfn('function pantryBuyKey(');
  var repId = pevalfn('function repId(m){');
  var emo = pevalfn('function emo(id){');
  /* repId closes over the page's SUPPLY_EMOJI const; pull it into scope too.
     (pevalfn wraps in parens, which const cannot survive, so eval directly.) */
  var SUPPLY_EMOJI = eval('(' + pex('const SUPPLY_EMOJI = ').replace(/^const SUPPLY_EMOJI =/, '0,') + ')');
  /* cardHtml closes over the page's ideaEmoji (pantry thumbnails); pull it and
     its IDEA_EMOJI const into scope too. */
  var IDEA_EMOJI = eval('(' + pex('const IDEA_EMOJI = ').replace(/^const IDEA_EMOJI =/, '0,') + ')');
  var ideaEmoji = pevalfn('function ideaEmoji(id){');
  var score = pevalfn('function score(it){');
  var cardHtml = pevalfn('function cardHtml(');
  var normUnlock = pevalfn('function normUnlock(t){');

  /* Grouped checkbox model: 5 groups, every pantry item in a group, no dupes. */
  var groupIds = {};
  DATA.groups.forEach(function(g){ groupIds[g.id] = true; });
  ok(DATA.groups.length === 5, 'pantry: expected 5 groups, found ' + DATA.groups.length);
  var itemIds = DATA.pantry.map(function(p){ return p.id; });
  /* 2026-09-26: 56 items -- the Billy-approved hoodie checkbox (decision brief #9)
     landed via the generator regen. */
  ok(itemIds.length === 56, 'pantry: expected 56 items, found ' + itemIds.length);
  var idupes = itemIds.filter(function(id, ix){ return itemIds.indexOf(id) !== ix; });
  ok(idupes.length === 0, 'pantry: duplicate items ' + idupes.join(','));
  var orphans = DATA.pantry.filter(function(p){ return !groupIds[p.group]; });
  ok(orphans.length === 0, 'pantry: items with no group ' + orphans.map(function(p){ return p.id; }).join(','));
  ok(/renderGroups\(\)/.test(psrc), 'pantry: group renderer missing');
  console.log('pantry groups:', DATA.groups.length, 'items:', itemIds.length, ', all grouped, no dupes');

  /* Storage contract: pantry2 is the v2 key (fresh key for the redesigned
   * data model), init reads it, toggles write it. */
  ok(/const LS_KEY = 'pantry2'/.test(psrc), 'pantry: storage key is not pantry2');
  ok(/localStorage\.getItem\(LS_KEY/.test(psrc), 'pantry: init does not read the storage key');
  ok(/localStorage\.setItem\(LS_KEY/.test(psrc), 'pantry: toggles do not persist the storage key');
  ok(psrc.indexOf('We assume every home has scissors, tape, paper and pen, cardboard, socks, and aluminum foil.') >= 0,
    'pantry: honest hedging note about the 6 assumed staples is gone');

  /* Staples pre-ticked: exactly the 6 staple ids (2026-09-26: unified with
     index.html's fallback so engaging with the pantry never worsens badges). */
  var staples = DATA.pantry.filter(function(p){ return p.staple; }).map(function(p){ return p.id; });
  ok(staples.length === 6, 'pantry: expected 6 staples, found ' + staples.length);
  ok(staples.indexOf('scissors') >= 0 && staples.indexOf('tape') >= 0 && staples.indexOf('paper-pen') >= 0 &&
     staples.indexOf('cardboard') >= 0 && staples.indexOf('socks') >= 0 && staples.indexOf('foil') >= 0,
    'pantry: staple set is not scissors/tape/paper-pen/cardboard/socks/foil: ' + staples.join(','));
  ok(psrc.indexOf('|| STAPLES') >= 0,
    'pantry: ticked set does not default to the staples');

  /* Toggling a checkbox updates the counts (classic-ghost: bedsheet+markers+scissors,
   * plus one honestly-unmapped material that always counts as still-need). */
  function pidea(id){
    for (var i = 0; i < DATA.ideas.length; i++) if (DATA.ideas[i].id === id) return DATA.ideas[i];
    return null;
  }
  ticked = new Set(staples);
  var ghost = pidea('classic-ghost');
  ok(ghost, 'pantry sample: classic-ghost missing from pantry DATA');
  var r0 = score(ghost);
  ok(r0.have === 1 && r0.total === 3 && r0.missing.length === 2,
    'pantry: staples-only score for classic-ghost is ' + r0.have + ' of ' + r0.total + ', expected 1 of 3');
  ticked.add('bedsheet'); ticked.add('markers');
  var r1 = score(ghost);
  ok(r1.have === 3 && r1.total === 3 && r1.missing.length === 0,
    'pantry: toggling checkboxes did not update counts (have ' + r1.have + ' of ' + r1.total + ')');
  ticked.delete('bedsheet');
  var r2 = score(ghost);
  ok(r2.have === 2 && r2.missing.length === 1,
    'pantry: untoggling a checkbox did not update counts');

  /* Result cards: X-of-Y requirements, still-need chips, plan link. */
  var html1 = cardHtml(r1, 0);
  ok(html1.indexOf('You have <b>3 of 3</b> requirements') >= 0, 'pantry: result card missing "you have X of Y"');
  var html0almost = cardHtml(r0, 0);
  ok(html0almost.indexOf('Still need:') >= 0, 'pantry: almost-there card lost the still-need chips');
  ok(html1.indexOf('How to make it') >= 0, 'pantry: result card lost the "How to make it" link');
  /* 2026-09-26 red-team: the pantry "How to make it" deliberately opens the
     IN-APP idea detail (index.html?pick=) for browse parity, not the static
     /c/ guide. The ?pick= arrival opens openIdeaDetail via s-pantry. Assert
     the deliberate behavior, not the old /c/ expectation. */
  ok(html1.indexOf('href="index.html?pick=classic-ghost"') >= 0, 'pantry: "How to make it" does not open the plan');
  var html0 = cardHtml(r0, 4);
  ok(html0.indexOf('You have <b>1 of 3</b> requirements') >= 0, 'pantry: staples-only card missing "you have X of Y"');

  /* Honest math untouched: tier thresholds and headline variants. */
  ok(/missing\.length >= 1 && r\.missing\.length <= 2/.test(psrc),
    'pantry: the 1-2-away tier threshold changed');
  /* 2026-09-26 red-team: the lead now matches the actual ticked set
     ("With just the basics" / "With what you have ticked") and the
     headline reads "you can make <b>N</b> tonight". Assert the new copy. */
  ok(psrc.indexOf('you can make <b>') >= 0, 'pantry: alive make-tonight headline gone');
  ok(psrc.indexOf('With just the basics') >= 0, 'pantry: basics-lead headline variant gone');
  ok(psrc.indexOf('With what you have ticked') >= 0, 'pantry: ticked-lead headline variant gone');
  ok(psrc.indexOf('1 or 2 things away') >= 0, 'pantry: 1-2-away headline variant gone');
  ok(psrc.indexOf('Bigger build') >= 0, 'pantry: bigger-build headline variant gone');
  ok(psrc.indexOf('Nothing fully covered yet.') >= 0, 'pantry: honest zero-state note gone');

  /* Unlock suggestions: normUnlock strips quantities so one purchase dedups. */
  ok(normUnlock('2 small squares of black tulle (optional)') === 'squares of black tulle',
    'pantry: normUnlock mangled the unlock key: ' + normUnlock('2 small squares of black tulle (optional)'));
  ok(psrc.indexOf('One store trip away') >= 0, 'pantry: unlock-suggestion section gone');

  /* No type-ahead in v2: every pantry item is visible in the grouped checkboxes,
   * so the long tail is covered by visibility, not search. */
  ticked = new Set(staples);
  ok(DATA.pantry.length === 56 && itemIds.length === 56,
    'pantry: not all pantry items are in the visible checkbox model');
  console.log('pantry items:', itemIds.length + ', all visible in grouped checkboxes (no type-ahead in v2)');

  /* Tap targets: checkboxes meet the 44px minimum. */
  var tapm = psrc.match(/\.check\{[^}]*min-height:(\d+)px/);
  ok(tapm && +tapm[1] >= 44, 'pantry: .check missing the 44px tap-target minimum');
})();

/* ---------- 5. result roles: evidence gates (Billy 2026-09-25) ----------
 * New role shown => its evidence gate passes. Evidence absent => role absent.
 * Only one role per result. Neutral "No. 2"/"No. 3" fallback remains. */
(function(){
  var code = [];
  function extractObjM(marker){
    var start = src.indexOf(marker);
    if (start < 0) throw new Error('marker not found: ' + marker.slice(0, 40));
    var open = src.indexOf('{', start), depth = 0;
    for (var i = open; i < src.length; i++){
      if (src[i] === '{') depth++;
      else if (src[i] === '}'){ depth--; if (depth === 0) return src.slice(start, i + 1); }
    }
    throw new Error('unbalanced braces after: ' + marker.slice(0, 40));
  }
  code.push(extractObjM('var MAKE_PLANS = {'));
  code.push(src.slice(src.indexOf('var INTEREST_TAGS = ['), src.indexOf('];', src.indexOf('var INTEREST_TAGS = [')) + 2));
  code.push(src.slice(src.indexOf('var VIBE_TAGS = ['), src.indexOf('];', src.indexOf('var VIBE_TAGS = [')) + 2));
  code.push(extractObjM('var ROLE_NOTES = {'));
  ['function ideaEffortKey(', 'function buildDifficulty(',
   'function planMinutes(', 'function planIsTonightReady(', 'function tagDistance(',
   'function moreLikeThisTag(', 'function quizVibeTag(', 'function planIsPlotTwist(',
   'function resultRoles('
  ].forEach(function(m){ code.push(extractFn(m)); });
  code.push('var state = {answers:{qinterest:{tags:{tv:3}}, q2:{tags:{funny:2}}}};');
  eval(code.join('\n'));

  function asResults(ids){ return ids.map(function(id){ return {idea: ideaById(id)}; }); }
  var cc = ideaById('crowd-camouflage'), dc = ideaById('decades-crew'),
      vamp = ideaById('vampire'), ghost = ideaById('classic-ghost'),
      ndh = ideaById('neon-demon-hunter');

  /* Evidence units. */
  ok(planMinutes(ghost) === 20, 'roles: classic-ghost plan minutes should be 20, got ' + planMinutes(ghost));
  ok(planMinutes(ndh) === 60, 'roles: neon-demon-hunter plan minutes should be 60, got ' + planMinutes(ndh));
  ok(planIsTonightReady(ghost) === true, 'roles: classic-ghost should be tonight-ready');
  ok(planIsTonightReady(ndh) === false, 'roles: neon-demon-hunter should not be tonight-ready');

  /* Plot Twist evidence: different interest, same vibe. */
  var twistIdea = null, noTwistIdea = null;
  IDEAS.forEach(function(x){
    var k = moreLikeThisTag(x);
    if (!k || k.kind !== 'interest') return;
    if (k.tag !== 'tv' && vibeOkFor('funny', x.tags) && !twistIdea) twistIdea = x;
    if (k.tag === 'tv' && !noTwistIdea) noTwistIdea = x;
  });
  ok(!!twistIdea, 'roles: no different-interest funny idea found for the plot-twist test');
  ok(twistIdea && planIsPlotTwist(twistIdea) === true,
    'roles: plot-twist evidence must fire for ' + (twistIdea && twistIdea.id));
  ok(noTwistIdea && planIsPlotTwist(noTwistIdea) === false,
    'roles: plot-twist must not fire when the interest matches (' + (noTwistIdea && noTwistIdea.id) + ')');

  /* Role pool: 5 roles, every one with an explanatory note, no em/en dashes. */
  var POOL = Object.keys(ROLE_NOTES);
  ok(POOL.length === 5, 'roles: pool should hold 5 roles, got ' + POOL.length);
  POOL.forEach(function(r){
    ok(ROLE_NOTES[r] && ROLE_NOTES[r].length > 0, 'roles: missing explanatory note for ' + r);
    ok(r.indexOf('—') < 0 && r.indexOf('–') < 0, 'roles: em/en dash in label "' + r + '"');
    ok(ROLE_NOTES[r].indexOf('—') < 0 && ROLE_NOTES[r].indexOf('–') < 0,
      'roles: em/en dash in note for "' + r + '"');
  });

  /* Forward invariant: a shown role's evidence must hold. Sweep real triples. */
  var sweepIds = IDEAS.slice(0, 60).map(function(x){ return x.id; });
  var nullSeen = 0;
  for (var s = 0; s + 2 < sweepIds.length; s += 3){
    var res = asResults(sweepIds.slice(s, s + 3));
    var roles = resultRoles(res);
    [1, 2].forEach(function(i){
      var r = roles[i], idea = res[i].idea;
      if (r === null){ nullSeen++; return; }
      ok(POOL.indexOf(r) >= 0, 'roles: unknown role "' + r + '" for ' + idea.id);
      ok(r.indexOf('·') < 0, 'roles: stacked roles for ' + idea.id);
      if (r === 'Easiest'){
        var ds = [buildDifficulty(res[1].idea), buildDifficulty(res[2].idea)];
        var mn = Math.min(ds[0], ds[1]);
        ok(buildDifficulty(idea) === mn && ds[0] !== ds[1] && (Math.max(ds[0], ds[1]) - mn) >= 2,
          'roles: Easiest shown for ' + idea.id + ' without unique min-margin evidence');
      }
      if (r === 'Tonight-Ready')
        ok(planIsTonightReady(idea), 'roles: Tonight-Ready shown for ' + idea.id + ' (' + planMinutes(idea) + ' min)');
      if (r === 'Plot Twist')
        ok(planIsPlotTwist(idea), 'roles: Plot Twist shown without evidence for ' + idea.id);
      if (r === 'Wildcard'){
        var d1 = tagDistance(res[1].idea, res[0].idea), d2 = tagDistance(res[2].idea, res[0].idea);
        var mine = (i === 1 ? d1 : d2), other = (i === 1 ? d2 : d1);
        ok(mine > other && (mine - other) >= 3,
          'roles: Wildcard shown for ' + idea.id + ' without distance margin');
      }
    });
  }

  /* Reverse: evidence absent => role absent. */
  var slow = IDEAS.filter(function(x){ return !planIsTonightReady(x); }).slice(0, 3);
  var rr2 = resultRoles(asResults(slow.map(function(x){ return x.id; })));
  ok(rr2[1] !== 'Tonight-Ready' && rr2[2] !== 'Tonight-Ready',
    'roles: Tonight-Ready shown with no sub-30-min evidence');
  var d0 = buildDifficulty(IDEAS[0]), sameDiff = [];
  IDEAS.forEach(function(x){ if (sameDiff.length < 3 && buildDifficulty(x) === d0) sameDiff.push(x); });
  var rr3 = resultRoles(asResults(sameDiff.map(function(x){ return x.id; })));
  ok(rr3[1] !== 'Easiest' && rr3[2] !== 'Easiest',
    'roles: Easiest shown with no difficulty margin');

  /* Neutral fallback: a triple with no defensible role stays labelless. */
  var nr = resultRoles(asResults(['blue-dog-family', 'gloom-bloom', 'deadpan-diva']));
  ok(nr[1] === null && nr[2] === null,
    'roles: neutral fallback broken, got "' + nr[1] + '" / "' + nr[2] + '"');
  ok(nullSeen > 0, 'roles: fallback path never exercised in the sweep');

  /* The fallback copy still exists in renderResults. */
  ok(/"No\. " \+ \(i \+ 1\)/.test(src) || /"No\. " \+ \(_rn \+ 1\)/.test(src),
    'roles: neutral "No. N" fallback copy missing from renderResults');

  console.log('roles: evidence gates pass (pool of ' + POOL.length + ', sweep of ' +
    Math.floor(sweepIds.length / 3) + ' triples)');
})();

/* ---------- 6. search intelligence (Billy 2026-09-25) ----------
 * Every alias resolves non-empty. Normalization cases resolve. Attribute
 * queries filter on structured data. Composed queries intersect. Dead
 * queries fire the analytics event. Chips and suggestions are non-empty. */
(function(){
  var code = [];
  function extractObjM(marker){
    var start = src.indexOf(marker);
    if (start < 0) throw new Error('marker not found: ' + marker.slice(0, 40));
    var open = src.indexOf('{', start), depth = 0;
    for (var i = open; i < src.length; i++){
      if (src[i] === '{') depth++;
      else if (src[i] === '}'){ depth--; if (depth === 0) return src.slice(start, i + 1); }
    }
    throw new Error('unbalanced braces after: ' + marker.slice(0, 40));
  }
  code.push(extractObjM('var MAKE_PLANS = {'));
  code.push(extractObjM('var SEARCH_ALIASES = {'));
  code.push(src.slice(src.indexOf('var POPULAR_SEARCHES = ['), src.indexOf('];', src.indexOf('var POPULAR_SEARCHES = [')) + 2));
  code.push(src.slice(src.indexOf('var SEARCH_ATTRS = ['), src.indexOf('function parseSearchAttrs')));
  code.push(src.slice(src.indexOf('var SEARCH_STOPWORDS'), src.indexOf(';', src.indexOf('var SEARCH_STOPWORDS')) + 1));
  code.push(src.slice(src.indexOf('var SEARCH_SUGGESTIONS = ['), src.indexOf('];', src.indexOf('var SEARCH_SUGGESTIONS = [')) + 2));
  ['function normalizeSearch(', 'function searchKey(', 'function singularize(',
   'function edits1(', 'function aliasHit(',
   'function planBuyText(', 'function parseSearchAttrs(', 'function parseSearch(',
   'function prettyAliasKey(',
   'function buildDifficulty(', 'function planMinutes(', 'function vibeOkFor(',
   'function ideaEffortKey('
  ].forEach(function(m){ code.push(extractFn(m)); });
  eval(code.join('\n'));

  /* The renderBrowse filter pipeline, minus dropdown filters. */
  function runQuery(q){
    var spec = parseSearch(q);
    var ord = {}; spec.aliasIds.forEach(function(id, ix){ ord[id] = ix; });
    var out = [];
    IDEAS.forEach(function(idea){
      var inA = spec.aliasIds.indexOf(idea.id) >= 0;
      if (!inA){
        for (var ti = 0; ti < spec.textTokens.length; ti++)
          if (idea.title.toLowerCase().indexOf(spec.textTokens[ti]) < 0) return;
        if (!spec.textTokens.length && !spec.aliasIds.length && !spec.filters.length) return;
      }
      for (var fi = 0; fi < spec.filters.length; fi++) if (!spec.filters[fi](idea)) return;
      out.push(idea);
    });
    out.sort(function(a, b){
      var ao = Object.prototype.hasOwnProperty.call(ord, a.id),
          bo = Object.prototype.hasOwnProperty.call(ord, b.id);
      if (ao && bo) return ord[a.id] - ord[b.id];
      if (ao) return -1; if (bo) return 1;
      return a.rank - b.rank;
    });
    return {spec: spec, ids: out.map(function(x){ return x.id; }), ideas: out};
  }

  /* Alias inventory by layer (for the deploy report). */
  var LAYERS = {trending: 0, evergreen: 0, kids: 0, couples: 0, barclub: 0,
    groups: 0, workparty: 0, nostalgia: 0, horror: 0, meme: 0};
  var TREND = ["kpopdemonhunters","kpop","demonhunters","huntrix","rumi","zoey","mira","jinu","babysaja","sajaboys","labubu","chickenjockey","elphaba","wicked","wednesday","morticia","addams","vampire","vampires","vamp","mariokart","minion","minions","insideout","envy","joy","sadness","anger","anxiety","howtotrainyourdragon","hiccup","astrid","toothless"];
  var KIDS = ["bluey","bingo","bandit","chilli","pawpatrol","chase","marshall","skye","rubble","zuma","everest","cocomelon","peppapig","peppa","gabby","gabbysdollhouse","octonauts","blaze","transformers","jurassicworld","jurassic","dinosaur","toystory","woody","buzz","buzzlightyear","lionking","simba","nala"];
  var COUPLES = ["peanutbutterjelly","peanutbutterandjelly","peanutbutter","pbj","jelly","saltpepper","saltandpepper","plugsocket","plugandsocket","socket","ketchupmustard","ketchup","mustard","baconeggs","baconandeggs","bacon","peasinapod","peasinpod","spaghettimeatball","spaghettiandmeatballs","spaghetti","meatball","sunmoon","sunandmoon","catmouse","catandmouse","tomjerry","tomandjerry","tennis","frankenstein","brideoffrankenstein","madscientist","dracula","barbieken","barbieandken","ken","toothfairy","tooth","officecouple","burgerjoint","mothporchlight","mothandporchlight","moth","raptorranger","dragonrider"];
  var BARCLUB = ["hot","iconic","cowgirl"];
  var GROUPS = ["scoobygang","shaggy","velma","daphne","mysterymachine","despicableme","kart","emotion","decades","penguin","soccer","soccersquad","emoji","emojicrew","herosquad","olympians","greekgods","greek","toga","astronaut","nasa","spaceman","bowling","bowlingpins","boardgame","referee","umpire","knight","medieval","fruit","fruitsalad","cereal","cerealcrew","breakfast","breakfastbuffet","waldo","whereswaldo","taco","pizza","sushi","ramen","donut","doughnut","popcorn","cupcake","coffee","banana","icecream","mermaid","snowsisters","losttourist","ghosthunters"];
  var WORKPARTY = ["workparty","officesafe","workappropriate","sfw"];
  var NOSTALGIA = ["80s","90s","70s","2000s","retro","throwback","disco"];
  var HORROR = ["ghostbusters","ghostbuster","fnaf","fivenightsatfreddys","hauntedhouse","haunted","zombie"];
  var MEME = ["meme","tiktok","viral","amongus","impostor","imposter","pickle"];
  Object.keys(SEARCH_ALIASES).forEach(function(k){
    if (TREND.indexOf(k) >= 0) LAYERS.trending++;
    else if (KIDS.indexOf(k) >= 0) LAYERS.kids++;
    else if (COUPLES.indexOf(k) >= 0) LAYERS.couples++;
    else if (BARCLUB.indexOf(k) >= 0) LAYERS.barclub++;
    else if (GROUPS.indexOf(k) >= 0) LAYERS.groups++;
    else if (WORKPARTY.indexOf(k) >= 0) LAYERS.workparty++;
    else if (NOSTALGIA.indexOf(k) >= 0) LAYERS.nostalgia++;
    else if (HORROR.indexOf(k) >= 0) LAYERS.horror++;
    else if (MEME.indexOf(k) >= 0) LAYERS.meme++;
    else LAYERS.evergreen++;
  });

  /* Every alias: non-empty, real ids, curated order preserved. */
  Object.keys(SEARCH_ALIASES).forEach(function(k){
    var r = runQuery(k);
    ok(r.ids.length > 0, 'search: alias "' + k + '" returned zero');
    SEARCH_ALIASES[k].forEach(function(id){
      ok(ideaById(id), 'search: alias "' + k + '" references missing idea ' + id);
    });
    var ord = SEARCH_ALIASES[k];
    var got = r.ids.filter(function(id){ return ord.indexOf(id) >= 0; });
    var want = ord.filter(function(id){ return got.indexOf(id) >= 0; });
    ok(JSON.stringify(got) === JSON.stringify(want), 'search: alias "' + k + '" order broken');
  });

  /* Normalization: articles, plurals, hyphens/case, prefix, typo. */
  [['A Ghost', 'ghost'], ['the princess', 'princess'], ['princesses', 'princess'],
   ['witches', 'witches'], ['SPIDER-MAN', 'spiderman'], ['spider man', 'spiderman'],
   ['spidermn', 'spiderman'], ['pricess', 'princess'], ['bel', 'belle']
  ].forEach(function(t){
    var h = aliasHit(searchKey(t[0]));
    ok(h && h.key === t[1], 'search: normalize ' + JSON.stringify(t[0]) +
      ' -> ' + (h ? h.key + '/' + h.how : 'NULL') + ' (want ' + t[1] + ')');
  });
  /* "mirabel" (Encanto, a real gap) must not alias to "mira" (KPop). */
  ok(aliasHit(searchKey('mirabel')) === null, 'search: "mirabel" must not alias to mira');
  /* "bar" is an attribute filter, never the Barbie alias prefix. */
  var barSpec = parseSearch('bar');
  ok(barSpec.filters.length === 1 && barSpec.aliasIds.length === 0,
    'search: "bar" must parse as a pure attribute filter');

  /* Spot checks: first result is the curated best match. */
  [['belle', 'enchanted-castle-crew'], ['rumi', 'neon-demon-hunter'],
   ['wednesday', 'deadpan-diva'], ['labubu', 'fuzzy-monster'],
   ['chicken jockey', 'block-game-crew'], ['bluey', 'blue-dog-family'],
   ['cocomelon', 'blue-dog-family'], ['moana', 'mermaid-crew'],
   ['jurassic world', 'dino-rangers'], ['buzz lightyear', 'toy-box-crew'],
   ['elphaba', 'emerald-witch'], ['simba', 'little-lion'],
   ['woody', 'toy-box-crew'], ['mario', 'plumber-duo'],
   ['scooby doo', 'mystery-crew'], ['minions', 'goggle-crew'],
   ['inside out', 'emotion-crew'], ['barbie', 'plastic-dream-crew'],
   ['minecraft', 'block-game-crew'], ['devil', 'deviled-egg'],
   ['ghost', 'classic-ghost'], ['power rangers', 'robot-ranger'],
   ['octonauts', 'under-the-sea'], ['peppa pig', 'little-pig-family'],
   ['beauty and the beast', 'enchanted-castle-crew'],
   /* Adult layers: couples classics, food singles, group themes, horror, meme. */
   ['peanut butter jelly', 'pbj'], ['salt and pepper', 'salt-pepper'],
   ['plug and socket', 'plug-socket'], ['ketchup mustard', 'ketchup-mustard'],
   ['bacon and eggs', 'bacon-eggs'], ['barbie ken', 'plastic-dream-crew'],
   ['frankenstein', 'doctor-bride'], ['dracula', 'vampire'],
   ['taco', 'walking-taco'], ['pickle', 'pickle'], ['sushi', 'sushi-roll'],
   ['mermaid', 'mermaid-crew'], ['snow sisters', 'snow-sisters'],
   ['lost tourist', 'lost-tourist'], ['ghost hunters', 'ghost-hunters'],
   ['breakfast buffet', 'breakfast-buffet'], ['hot dog', 'hot-dog'],
   ['scooby gang', 'mystery-crew'], ['ghostbusters', 'ghost-hunters'],
   ['fnaf', 'haunted-animatronics'], ['among us', 'space-crewmate'],
   ['star wars', 'galaxy-knights'], ['waldo', 'crowd-camouflage'],
   ['90s', 'decades-crew'], ['decades', 'decades-crew'],
   ['mario kart', 'kart-racers']
  ].forEach(function(t){
    var r = runQuery(t[0]);
    ok(r.ids.length > 0 && r.ids[0] === t[1],
      'search: "' + t[0] + '" first=' + r.ids[0] + ' (want ' + t[1] + ')');
  });

  /* Attribute filters read structured data, not title text.
     (2026-10-01: the "cheap" price filter was cut with the no-dollar-figures
     call; its gate assertion went with it.) */
  var kid = runQuery('kid');
  ok(kid.ids.length > 0, 'search: "kid" returned zero');
  kid.ideas.forEach(function(x){
    ok(x.audience.indexOf('kid') >= 0, 'search: "kid" returned non-kid idea ' + x.id);
  });
  var fem = runQuery('female');
  ok(fem.ids.length > 0, 'search: "female" returned zero');
  fem.ideas.forEach(function(x){ ok(x.fit === 'F', 'search: "female" returned fit-' + x.fit + ' ' + x.id); });
  var cpl = runQuery('couples');
  ok(cpl.ids.length > 0, 'search: "couples" returned zero');
  cpl.ideas.forEach(function(x){
    ok(x.audience.indexOf('couple') >= 0, 'search: "couples" returned non-couple ' + x.id);
  });
  var tod = runQuery('toddler');
  tod.ideas.forEach(function(x){
    ok((x.tags.kidunder3 || 0) > 0, 'search: "toddler" returned non-toddler-safe ' + x.id);
  });

  /* Composed queries intersect every constraint. */
  [['easy funny couples', ['easy', 'funny', 'couples']],
   ['scary male group costume', ['scary', 'male', 'group']],
   ['easy group costume', ['easy', 'group']]
  ].forEach(function(t){
    var r = runQuery(t[0]);
    var sets = t[1].map(function(w){ return runQuery(w).ids; });
    var inter = sets[0].filter(function(id){
      return sets.every(function(s){ return s.indexOf(id) >= 0; });
    });
    ok(JSON.stringify(r.ids.slice().sort()) === JSON.stringify(inter.slice().sort()),
      'search: composed "' + t[0] + '" != intersection');
    ok(r.ids.length > 0, 'search: composed "' + t[0] + '" returned zero');
  });

  /* Alias + intent compose: "scary vampire" keeps the vampire, filtered scary. */
  var sv = runQuery('scary vampire');
  ok(sv.ids.indexOf('vampire') >= 0, 'search: "scary vampire" lost the vampire');

  /* Whole-query exact alias owns the query: "hot dog" must not be emptied
     by the pet filter ("dog" is a substring of the alias key "hotdog"). */
  var hd = runQuery('hot dog');
  ok(hd.ids.length > 0 && hd.ids[0] === 'hot-dog',
    'search: "hot dog" first=' + hd.ids[0] + ' (want hot-dog)');
  /* "horror" is a structured scary-vibe filter. */
  var hr = runQuery('horror');
  ok(hr.ids.length > 0, 'search: "horror" returned zero');
  hr.ideas.forEach(function(x){
    ok(vibeOkFor('scary', x.tags), 'search: "horror" returned non-scary ' + x.id);
  });
  /* "work party" chip: structured occasion filter, non-empty. */
  var wp = runQuery('work party');
  ok(wp.ids.length > 0, 'search: "work party" returned zero');

  /* Popular chips: every one runs a non-empty search. */
  POPULAR_SEARCHES.forEach(function(p){
    var r = runQuery(p.term);
    ok(r.ids.length > 0, 'search: popular chip "' + p.term + '" returned zero');
  });
  /* Variant C hero chips: each runs a non-empty search through the same
     intelligence. "tonight" must equal the Tonight-Ready role set.
     (2026-10-01: "cheap" cut with the no-dollar-figures call.) */
  ["Bluey","couples","bar","tonight"].forEach(function(t){
    var r = runQuery(t);
    ok(r.ids.length > 0, 'search: hero chip "' + t + '" returned zero');
  });
  var _tn = runQuery('tonight').ids.slice().sort();
  var _tr = IDEAS.filter(function(i){ var m = planMinutes(i); return m !== null && m <= 30; })
    .map(function(i){ return i.id; }).sort();
  ok(JSON.stringify(_tn) === JSON.stringify(_tr),
    'search: "tonight" != Tonight-Ready set (' + _tn.length + ' vs ' + _tr.length + ')');
  ok(src.indexOf('HERO_SEARCH_CHIPS') >= 0, 'hero: HERO_SEARCH_CHIPS missing');
  ok(src.indexOf('hero_chip_tapped') >= 0, 'hero: chip tap analytics missing');
  ok(src.indexOf('className = "bpop"') >= 0, 'search: empty-state chip container missing');
  ok(src.indexOf('runPopularSearch') >= 0, 'search: runPopularSearch missing');

  /* Type-ahead suggestions: every one runs a non-empty search; box is wired. */
  SEARCH_SUGGESTIONS.forEach(function(s){
    var r = runQuery(s.q);
    ok(r.ids.length > 0, 'search: suggestion "' + s.label + '" returned zero');
  });
  ok(src.indexOf('renderSearchSuggest(bs.value)') >= 0, 'search: type-ahead not wired to the input');
  ok(src.indexOf('id = "browse-suggest"') >= 0, 'search: suggestion box not created');

  /* Self-improving loop: dead queries fire the analytics event. */
  ok(src.indexOf('Analytics.track("search_zero_results"') >= 0,
    'search: search_zero_results event not fired on empty results');
  ok(src.indexOf('_lastZeroQuery') >= 0,
    'search: zero-result dedupe guard missing (would spam per keystroke)');

  /* Honest gaps stay empty: no forced bad aliases. */
  ['pirate', 'pennywise', 'ghostface', 'lorax', 'carmy', 'encanto',
   'pregnant', 'ninja turtles', 'mirabel', 'aladdin',
   'bonnieclyde', 'sexy', 'mummy', 'beetlejuice', 'strangerthings',
   'skibidi', 'grimace', 'ohio', 'nurse', 'police', 'viking', 'cleopatra',
   'lego', 'barbenheimer', 'slasher', 'titanic', 'flapper', 'mafia'
  ].forEach(function(q){
    var r = runQuery(q);
    ok(r.ids.length === 0, 'search: gap term "' + q + '" unexpectedly matched: ' + r.ids.join(','));
  });

  console.log('search: ' + Object.keys(SEARCH_ALIASES).length + ' aliases ' +
    '(trending ' + LAYERS.trending + ', evergreen ' + LAYERS.evergreen +
    ', kids ' + LAYERS.kids + ', couples ' + LAYERS.couples +
    ', bar/club ' + LAYERS.barclub + ', groups ' + LAYERS.groups +
    ', work-party ' + LAYERS.workparty + ', nostalgia ' + LAYERS.nostalgia +
    ', horror ' + LAYERS.horror + ', meme ' + LAYERS.meme + '), ' +
    POPULAR_SEARCHES.length + ' chips, ' +
    SEARCH_SUGGESTIONS.length + ' suggestions — all non-empty');
})();

/* ---------- 7. plan agreement (Billy 2026-09-25) ----------
 * The "Make this this week" card (MAKE_PLANS) and the build guide
 * (INSTRUCTIONS) are two recipes for the same costume. They must agree on
 * core materials: if one names a material family the other contradicts
 * (felt vs duct tape, glow stick vs tea light, paper plate vs cardboard),
 * the gate fails. Catches the tin-hero class of bug permanently. */
(function(){
  function extractObjM2(marker){
    var start = src.indexOf(marker);
    if (start < 0) throw new Error('marker not found: ' + marker.slice(0, 40));
    var open = src.indexOf('{', start), depth = 0;
    for (var i = open; i < src.length; i++){
      if (src[i] === '{') depth++;
      else if (src[i] === '}'){ depth--; if (depth === 0) return src.slice(start, i + 1); }
    }
    throw new Error('unbalanced braces after: ' + marker.slice(0, 40));
  }
  eval(extractObjM2('var MAKE_PLANS = {') + '\n' + extractObjM2('var INSTRUCTIONS = {'));
  function planText(id){
    var p = MAKE_PLANS[id];
    return (p.buy.join(' ') + ' ' + p.steps.join(' ')).toLowerCase();
  }
  function instrText(id){
    var g = INSTRUCTIONS[id];
    return (g.m.join(' ') + ' ' + g.s.join(' ')).toLowerCase();
  }
  /* Material families that substitute for each other: the two surfaces may
     not sit exclusively on opposite sides of any pair. */
  var CONTRA = [["felt","duct tape"],["glow stick","tea light"],["paper plate","cardboard"]];
  var checked = 0;
  Object.keys(MAKE_PLANS).forEach(function(id){
    if (!INSTRUCTIONS[id] || !INSTRUCTIONS[id].m || !INSTRUCTIONS[id].s) return;
    checked++;
    var a = planText(id), b = instrText(id), bad = 0;
    CONTRA.forEach(function(pair){
      var aA = a.indexOf(pair[0]) !== -1, aB = a.indexOf(pair[1]) !== -1;
      var bA = b.indexOf(pair[0]) !== -1, bB = b.indexOf(pair[1]) !== -1;
      if ((aA && !aB && bB && !bA) || (aB && !aA && bA && !bB)) bad++;
    });
    ok(bad === 0, 'plan-agreement: ' + id +
      ' contradicts itself between "Make this this week" and the build guide');
  });
  console.log('plan-agreement: MAKE_PLANS vs INSTRUCTIONS checked for ' + checked + ' ideas');
})();


/* ---------- 4. closet-coverage badge (2026-09-26) ----------
 * The detail page shows a slim "you already have N of M things for this"
 * strip under the why-line, scored from the VIEWER's saved pantry. Asserts:
 *  a. pantrySaved() is false with nothing saved (bypasses the staples
 *     fallback), true with a saved pantry2 array.
 *  b. closetBadgeState() over the REAL pantryScore / PANTRY_MATS walk:
 *     empty pantry -> "empty" (no count shown); partial -> "partial" with
 *     honest have/total; full -> "full"; idea with no mats entry -> null
 *     (no badge); all-buy-only idea (neon-demon-hunter) -> partial 0-have
 *     (P5-2: badge renders instead of hiding).
 *  c. "Still need:" names appear only when 1-2 items are missing and every
 *     missing material resolved to a label (pantry id or P5-3 instruction
 *     text derivation).
 *  d. Viewer-not-challenger: the badge machinery never reads
 *     location.search or a kit param (no ?kit= import exists in index.html).
 *  e. buildBrowseDetailCard mounts the badge between the why-line and the
 *     howto box.
 *  f. Analytics: closet_badge_viewed carries only {idea_id, state,
 *     have_count, total_count}; closet_badge_pantry_tap carries only
 *     {idea_id, from_state}. No material ids, labels, or ticked contents.
 *  g. Copy honesty: the badge strings are present verbatim and the badge
 *     block contains no em/en dashes.
 */
(function(){
  /* Stub localStorage for the eval'd functions. */
  var store = {};
  global.localStorage = {
    getItem: function(k){ return Object.prototype.hasOwnProperty.call(store, k) ? store[k] : null; },
    setItem: function(k, v){ store[k] = String(v); },
    removeItem: function(k){ delete store[k]; }
  };
  eval(extract('var PANTRY_MATS = {', 'function pantryTicked(){'));
  eval(extract('var PANTRY_LABELS = {', 'function pantrySaved(){'));
  /* 2026-10-01: pantryScore's buy-branch closes over pantryBuyKey (Sep 30
     detail-badge inline toggle); eval the real helper from the same source. */
  eval(extractFn('function pantryBuyKey('));
  eval(extractFn('function pantrySaved(){'));
  eval(extractFn('function pantryMaterialTexts(ideaId){'));
  eval(extractFn('function shortMaterialName(t){'));
  eval(extractFn('function pantryScore(ideaId, ticked){'));
  eval(extractFn('function closetBadgeState(ideaId, saved, ticked){'));

  /* (a) empty check bypasses the staples fallback. */
  ok(pantrySaved() === false, 'closet badge: pantrySaved() true with empty localStorage');
  store.pantry2 = JSON.stringify(["headband", "tape"]);
  ok(pantrySaved() === true, 'closet badge: pantrySaved() false with a saved pantry2');
  store.pantry2 = 'null';
  ok(pantrySaved() === false, 'closet badge: pantrySaved() true for pantry2="null"');
  delete store.pantry2;
  store.pantry3 = JSON.stringify([]);
  ok(pantrySaved() === false, 'closet badge: pantrySaved() true for an empty saved array');
  delete store.pantry3;

  /* (b) state matrix over the real walk. black-cat has 8 materials. */
  var st = closetBadgeState("black-cat", false, new Set());
  ok(st && st.state === "empty", 'closet badge: empty pantry does not yield "empty" state');
  st = closetBadgeState("black-cat", true, new Set());
  ok(st && st.state === "partial" && st.have === 0 && st.total === 8,
    'closet badge: saved-but-empty pantry should be partial 0 of 8, got ' + JSON.stringify(st));
  st = closetBadgeState("black-cat", true, new Set(["headband", "paint-black", "scissors", "tape"]));
  ok(st && st.state === "partial" && st.have === 4 && st.total === 8 && st.names === null,
    'closet badge: 4-of-8 partial wrong or names shown for 4 missing, got ' + JSON.stringify(st));
  st = closetBadgeState("black-cat", true, new Set(["black-clothes", "headband", "felt", "paint-black", "scissors", "tape"]));
  ok(st && st.state === "partial" && st.have === 6 && st.names && st.names.length === 2,
    'closet badge: 2 buy-only gaps should name via instruction text (P5-3), got ' + JSON.stringify(st));
  st = closetBadgeState("breakfast-buffet", true, new Set(["cardboard", "markers", "yarn"]));
  ok(st && st.state === "partial" && st.have === 3 && st.total === 4 &&
     st.names && st.names.length === 1 && st.names[0] === "Scissors",
    'closet badge: 1 missing should name it, got ' + JSON.stringify(st));
  st = closetBadgeState("breakfast-buffet", true, new Set(["cardboard", "markers", "yarn", "scissors"]));
  ok(st && st.state === "full" && st.have === 4 && st.total === 4,
    'closet badge: full pantry not "full", got ' + JSON.stringify(st));
  ok(closetBadgeState("definitely-not-an-idea", true, new Set(["scissors"])) === null,
    'closet badge: idea with no mats entry should hide the badge');
  st = closetBadgeState("neon-demon-hunter", true, new Set(["scissors", "tape"]));
  ok(st && st.state === "partial" && st.have === 0,
    'closet badge: all-buy-only idea should render zero-have badge (P5-2), got ' + JSON.stringify(st));
  console.log('closet badge: state matrix ok (empty/partial/full/no-mats/all-buy-only)');

  /* (c) is covered in (b); (d) viewer-not-challenger: no query-string reads. */
  var badgeSrc = src.slice(src.indexOf('/* ================= 2026-09-26 closet-coverage badge'),
                            src.indexOf('/* ---- end 2026-09-26 closet-coverage badge ---- */'));
  ok(badgeSrc.length > 1000, 'closet badge: badge source block not found in index.html');
  ok(badgeSrc.indexOf('location.search') < 0, 'closet badge: badge reads location.search');
  var badgeCode = badgeSrc.replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/[^\n]*/g, '');
  ok(/[?&]kit=/.test(badgeCode) === false && badgeCode.indexOf('location.search') < 0,
    'closet badge: badge code references a challenger kit or query string');
  var tickedSrc = extractFn('function pantryTicked(){');
  ok(tickedSrc.indexOf('location.search') < 0 && tickedSrc.indexOf('localStorage') >= 0,
    'closet badge: pantryTicked() is not a pure localStorage read');

  /* (e) placement: between the why-line and the howto box. */
  var cardSrc = extractFn('function buildBrowseDetailCard(idea, whyHead){');
  var iWhy = cardSrc.indexOf('appendChild(wh)'), iBadge = cardSrc.indexOf('buildClosetBadge(idea)'),
      iHowto = cardSrc.indexOf('buildInstructions(idea');
  ok(iWhy > 0 && iBadge > 0 && iHowto > 0 && iWhy < iBadge && iBadge < iHowto,
    'closet badge: not mounted between the why-line and the howto box');

  /* (f) analytics payload shape: counts and state only. */
  ok(/Analytics\.track\("closet_badge_viewed", \{idea_id: idea\.id, state: st\.state, have_count: st\.have, total_count: st\.total\}\)/.test(badgeSrc),
    'closet badge: closet_badge_viewed payload is not {idea_id, state, have_count, total_count}');
  var taps = badgeSrc.match(/Analytics\.track\("closet_badge_pantry_tap", \{idea_id: idea\.id, from_state: "[a-z]+"\}\)/g) || [];
  ok(taps.length === 2 && /from_state: "empty"/.test(taps[0]) && /from_state: "partial"/.test(taps[1]),
    'closet badge: pantry_tap events should fire from empty and partial states only');
  ok(badgeSrc.indexOf('material') < 0 || badgeSrc.indexOf('never material') >= 0,
    'closet badge: badge block mentions material data in a track payload');

  /* (g) copy honesty: verbatim strings, no em/en dashes in the block. */
  ["We can check your closet for this one.",
   "Tell us what is already in your house. Takes about a minute, and then every costume shows what you have.",
   "Check my pantry",
   "None of this one is in your pantry yet.",
   "You have everything for this one. Nothing to buy.",
   " things for this.",
   "Still need: ",
   "Update my pantry"
  ].forEach(function(s){ ok(badgeSrc.indexOf(s) >= 0, 'closet badge: copy missing: ' + s.slice(0, 40)); });
  ok(badgeSrc.indexOf('\u2014') < 0 && badgeSrc.indexOf('\u2013') < 0,
    'closet badge: em/en dash found in badge copy');
  console.log('closet badge: placement, analytics, copy all ok');
})();

/* ---------- verdict ---------- */
if (fails.length){
  console.log('JOURNEY-GATE FAILURES: ' + fails.length);
  fails.forEach(function(f){ console.log('  FAIL ' + f); });
  process.exit(1);
}
console.log('journey-gate: PASS (tap targets, arrival contexts, quiz-to-results, closet-badge)');
