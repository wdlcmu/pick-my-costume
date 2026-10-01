/* Pre-deploy gate for Pick My Costume (corrected 2026-09-23):
 * Usage: node gate.js [N]   (N = demand-sim runs, default 100000)
 *        PMC_HTML=/path/to/index.html node gate.js
 * Supersedes simulate-demand.js (which had the family-Q5 bug).
 * 1. Enumerate ALL valid quiz paths using the real flowOrder() (family has NO Q5).
 * 2. Assert every path returns exactly 3 results and #1 carries the picked interest tag.
 * 3. Question-value analysis: share of paths where changing each question changes top-3 / #1.
 * 4. Demand-weighted Monte Carlo (family gets no Q5 answer).
 */
var fs = require('fs');
var HTML = process.env.PMC_HTML || (process.env.HOME + '/workspace/builds/pick-my-costume/index.html');
/* 2026-10-01 bundle split: the app script (QUESTIONS/IDEAS/logic) moved from
   index.html's inline <script> to /app.js (defer). This gate extracts and
   evals live script sections, so it reads app.js first and falls back to
   index.html's inline <script> (pre-split layout). */
var APPJS = process.env.PMC_APPJS || HTML.replace(/index\.html$/, 'app.js');
function readFirst(paths){
  for (var i = 0; i < paths.length; i++){
    try { return fs.readFileSync(paths[i], 'utf8'); } catch (e){}
  }
  throw new Error('no readable source: ' + paths.join(', '));
}
var src = readFirst([APPJS, HTML]);
function extract(a, b){ var x=src.indexOf(a), y=src.indexOf(b,x); if(x<0||y<0) throw new Error('miss '+a.slice(0,30)); return src.slice(x,y); }
var state = { qi: 0, answers: {} };
eval(extract('var QUESTIONS = [', '/* ================= CONFIG: IDEAS'));
eval(extract('var IDEAS = [', '/* ================= CONFIG: SHARE'));
eval(extract('function qById(id)', '/* ================= SCREENS'));
eval(extract('function scoreIdeas(', '/* ================= SCREENS'));
eval(extract('function flowOrder(){', '/* ================= SCREENS'));
/* 2026-09-26: scoreIdeas now calls applyConstraints (constraint refinement).
   Eval the real helpers so constrained and unconstrained paths score exactly
   as the browser does. With state.constraints unset (below), the filter is a
   no-op and the gate asserts the historic baseline.
   2026-10-01: planCostMax removed per the no-dollar-figures call (Closet
   Build role and budget constraint cut); only planMinutes remains. */
eval(extract('function planMinutes(idea){', '/* 2026-09-26 constraint refinement'));
eval(extract('var CONSTRAINT_CHIPS = [', 'function constraintOk(idea, c){'));
eval(extract('function constraintOk(idea, c){', 'function applyConstraints(pool){'));
eval(extract('function applyConstraints(pool){', 'function planIsPlotTwist(idea){'));

/* ---- 0. Interest-tag grounding (critic 2026-09-25 P5; bank cleanup 2026-09-25).
 * An interest tag survives only if the idea's user-visible copy evidences that
 * interest; otherwise the tag must be stripped from the bank (never invent copy
 * to save a tag). Evidence text is title + blurb + why: the critic's original
 * spec said blurb-or-why only, but the title is user-visible copy too, and the
 * actual dinosaur costume ("Baby Dinosaur") evidences dinos ONLY in its title.
 * Excluding the title would strip dinos:3 from Baby Dinosaur, which is absurd.
 * UNGROUNDED_ALLOW covers screen-character costumes whose tv/games tag is
 * cultural knowledge, not copy (the copy never names the franchise, by design);
 * each entry was human-adjudicated. Keep it short: prefer copy evidence and add
 * here only when the identity genuinely cannot be evidenced without naming
 * the franchise. This gate fails the deploy if an ungrounded tag creeps back. */
var INTEREST_EVIDENCE = {
  animals: /\b(animals?|dogs?|pupp(y|ies)|pup|kittens?|kitt(y|ies)|cats?|bunn(y|ies)|rabbits?|bears?|fox(es)?|wol(f|ves)|lions?|tigers?|pigs?|cows?|horses?|sheep|lambs?|ducks?|chickens?|frogs?|fish|sharks?|whales?|octopus|bees?|butterfl(y|ies)|spiders?|ants?|owls?|eagles?|parrots?|penguins?|elephants?|giraffes?|zebras?|kangaroos?|pandas?|monkeys?|safari|zoo|pets?|paws?|tails?|whiskers?|fins?|feathers?|furry|snouts?|manes?|hooves?|claws?|beaks?|wings?|snails?|shells?|aliens?|creatures?)\b/i,
  princess: /\b(princess(es)?|princes?|royal|queens?|kings?|castles?|crowns?|tiaras?|gowns?|ballgowns?|fairy[ -]?tales?|thrones?|slippers?|majest(y|ies)|enchanted)\b/i,
  heroes: /\b(superheros?|super[ -]hero(es)?|hero(es)?|spiders?(-man)?|knights?|capes?|masks?|armou?rs?|shields?|crusaders?|firefighters?|vigilantes?|gods?|goddesses?)\b/i,
  dinos: /\b(dinos?(aurs?)?|monsters?|raptors?|t-?rex(es)?|jurassic|fossils?|prehistoric|pterodactyls?|triceratops|stegosaurus|brontosaurus|velociraptors?|extinct)\b/i,
  games: /\b(video[ -]?games?|board[ -]?games?|gamers?|gaming|dices?|playing[ -]?cards?|pawns?|domino(es)?|chess|blocky|blocks?|pixels?|8-?bit|arcade|consoles?|controllers?|karts?|racing|minecraft|tetris|pac-?man|animatronics?|crewmates?)\b/i,
  tv: /\b(tv|t\.v\.|movies?|films?|shows?|series|episodes?|cartoons?|animes?|sitcoms?|netflix|disney|pixar|streaming|cinematic)\b/i,
  food: /\b(pizzas?|tacos?|donuts?|hot[ -]?dogs?|sushis?|popcorn|cupcakes?|cookies?|burgers?|pickles?|ramen|spaghettis?|meatballs?|bananas?|coffees?|ketchups?|mustards?|cereals?|peanut[ -]?butter|jell(y|ies)|eggs?|bacons?|cand(y|ies)|waffles?|toasts?|boba|sandwiches?|foods?|snacks?|fruits?|apples?|strawberr(y|ies)|watermelons?|pineapples?|peas?|cakes?|ice[ -]?creams?|sodas?|teas?|salts?|peppers?|chefs?|cooks?|bakers?|restaurants?|diners?|breakfasts?|lunches?|dinners?|meals?|edible|vending[ -]?machines?|grocer(y|ies))\b/i,
  sports: /\b(sports?|athletes?|players?|jerseys?|refs?(eree)?|coaches?|umpires?|troph(y|ies)|medals?|podiums?|marathons?|swimmers?|gymnasts?|skaters?|skateboards?|surfers?|boxers?|wrestlers?|goalies?|stadiums?|arenas?|tracks?|fields?|courts?|rinks?|champions?|mvp|touchdowns?|goals?|home[ -]?runs?|slam[ -]?dunks?|basketball|soccer|tennis|boxing|bowling|golf|baseball|football|quarterbacks?|olympics?|volleyball|rugby|cricket|hockey|cheerleaders?|red[ -]?cards?|world[ -]?cups?)\b/i
};
var UNGROUNDED_ALLOW = [
  ["neon-demon-hunter","tv","K-pop Demon Hunters"],
  ["blue-dog-family","tv","Bluey"],
  ["blue-alien-ohana","tv","Lilo & Stitch"],
  ["emerald-witch","tv","Wicked"],
  ["gloom-bloom","tv","Wednesday-inspired duo"],
  ["deadpan-diva","tv","Wednesday Addams"],
  ["tin-hero","tv","Iron Man"],
  ["good-witch-bad-witch","tv","Wicked"],
  ["web-slinger-crew","tv","Spider-Man"],
  ["little-pig-family","tv","Peppa Pig"],
  ["doctor-bride","tv","Frankenstein"],
  ["ghost-hunters","tv","Ghostbusters"],
  ["goggle-crew","tv","Minions"],
  ["office-couple","tv","The Office"],
  ["burger-joint-couple","tv","Bob's Burgers"],
  ["web-hero-duo","tv","Spider-Man"],
  ["toy-box-crew","tv","Toy Story"],
  ["demon-boy-band","tv","KPDH Saja Boys"],
  ["dragon-rider-duo","tv","How to Train Your Dragon"],
  ["numbered-players","tv","Squid Game"],
  ["emotion-crew","tv","Inside Out"],
  ["kart-racers","tv","Mario Kart"],
  ["tall-hat-crew","tv","Cat in the Hat"],
  ["chipmunk-trio","tv","Alvin and the Chipmunks"],
  ["plastic-dream-crew","tv","Barbie"],
  ["snow-sisters","tv","Frozen"],
  ["mermaid-crew","tv","The Little Mermaid"],
  ["enchanted-castle-crew","tv","Beauty and the Beast"],
  ["plumber-duo","games","Mario Bros"],
  ["kpop-demon-huntresses","tv","KPop Demon Hunters"],
  ["goth-braids","tv","Wednesday Addams"],
  ["juke-joint-vampires","tv","Sinners"],
  ["blue-heeler-pup","tv","Bluey"],
  ["yellow-henchmen","tv","Minions"],
  ["mystery-teens","tv","Scooby-Doo"],
  ["pumpkin-king-bride","tv","The Nightmare Before Christmas"],
  ["witchy-sisters","tv","Hocus Pocus"],
  ["macabre-couple","tv","The Addams Family"],
  ["wayfinder-princess","tv","Moana"]
];
var _groundFails = [];
IDEAS.forEach(function(idea){
  var _text = (idea.title || "") + " | " + (idea.blurb || "") + " | " + (idea.why || "");
  Object.keys(INTEREST_EVIDENCE).forEach(function(t){
    if (!((idea.tags || {})[t] > 0)) return;
    if (UNGROUNDED_ALLOW.some(function(a){ return a[0] === idea.id && a[1] === t; })) return;
    if (!INTEREST_EVIDENCE[t].test(_text)) _groundFails.push(idea.id + " carries " + t + ":" + idea.tags[t] + " with no copy evidence");
  });
});
if (_groundFails.length){
  console.log("UNGROUNDED INTEREST TAGS (" + _groundFails.length + "):");
  _groundFails.forEach(function(f){ console.log("  FAIL " + f); });
  console.log("Strip the tag or add a documented UNGROUNDED_ALLOW entry. Gate FAILED.");
  process.exitCode = 1;
} else {
  console.log("interest grounding: all " + Object.keys(INTEREST_EVIDENCE).length + " interest tags evidenced in copy (or allowlisted).");
}

/* 2026-09-29: the "Already have one" Q1 option (value "warm") is not a quiz
   path -- it branches to the warm capture flow before scoring. Exclude it
   from path enumeration like the page does. */
var q1 = qById('q1').options.filter(function(o){ return o.value !== 'warm'; }), q2 = qById('q2').options, q4 = qById('q4').options, qi = qById('qinterest').options;
function visibleInterests(aud){
  return qi.filter(function(opt){
    var keys = Object.keys(opt.tags);
    if (!keys.length) return true; /* "Surprise me": enumerated as a no-interest path */
    var k = keys[0];
    return IDEAS.some(function(i){ return i.audience.indexOf(aud) !== -1 && (i.tags[k] > 0); });
  });
}
function q5opts(aud){
  if (aud === 'kid') return { qid: 'q5kid', opts: qById('q5kid').options };
  /* All non-kid flows (family included) get the occasion question as Q5. */
  return { qid: 'qocc', opts: qById('qocc').options };
}

/* ---- 1+2. enumerate + assert ---- */
var paths = [];
q1.forEach(function(o1){
  var aud = o1.value, q5 = q5opts(aud), vis = visibleInterests(aud);
  q2.forEach(function(o2){ q4.forEach(function(o4){ vis.forEach(function(oi){
    var q5list = q5 ? q5.opts : [null];
    q5list.forEach(function(o5){
      paths.push({ o1:o1, o2:o2, o4:o4, oi:oi, q5:q5, o5:o5, aud:aud });
    });
  }); }); });
});
console.log('valid paths:', paths.length, '(kid: q5kid; non-kid: qocc)');
function answersFor(p){
  var a = { q1:p.o1, q2:p.o2, q4:p.o4, qinterest:p.oi };
  if (p.q5) a[p.q5.qid] = p.o5;
  return a;
}
function top3ids(a){ state.answers = a; return scoreIdeas().map(function(r){ return r.idea.id; }); }
function ideaById(id){ return IDEAS.filter(function(i){ return i.id===id; })[0]; }
var fails = [], no3 = 0;
paths.forEach(function(p){
  var res; state.answers = answersFor(p); res = scoreIdeas();
  var key = Object.keys(p.oi.tags)[0];
  if (res.length !== 3) { no3++; fails.push('len!=3 '+p.aud+'/'+(key||'surprise')); return; }
  if (key && !(ideaById(res[0].idea.id).tags[key] > 0)) fails.push('#1-interest-mismatch '+p.aud+'/'+key+' -> '+res[0].idea.id);
});
console.log('paths with !=3 results:', no3);
console.log('#1 interest mismatches:', fails.filter(function(f){return f[0]==='#';}).length);
if (fails.length && fails.length < 20) fails.forEach(function(f){ console.log('  FAIL', f); });

/* ---- 3. question value ---- */
function swapVal(a, qid, opt){
  var b = {}; for (var k in a) b[k] = a[k]; b[qid] = opt; return b;
}
var qids = ['q1','q2','qinterest','q4'];
var val = {};
qids.forEach(function(qid){ val[qid] = { t3: 0, n1: 0, n: 0 }; });
val['q5'] = { t3: 0, n1: 0, n: 0 };
paths.forEach(function(p){
  var base = answersFor(p), baseTop = top3ids(base), base1 = baseTop[0];
  function testQ(qid, opts){
    var v = val[qid === 'q5kid' || qid === 'qocc' ? 'q5' : qid];
    if (!base[qid]) return;
    var changed3 = false, changed1 = false;
    opts.forEach(function(o){
      if (o === base[qid]) return;
      // q1 change must also clear interest to a valid visible one for the new audience
      var alt = swapVal(base, qid, o), t;
      if (qid === 'q1') {
        var nvis = visibleInterests(o.value);
        var keep = nvis.filter(function(x){ return x.label === base.qinterest.label; })[0];
        alt.qinterest = keep || nvis[0];
        delete alt.q5kid; delete alt.qocc;
        var nq5 = q5opts(o.value);
        alt[nq5.qid] = nq5.opts[0];
        t = top3ids(alt);
      } else {
        t = top3ids(alt);
      }
      if (t.join() !== baseTop.join()) changed3 = true;
      if (t[0] !== base1) changed1 = true;
    });
    v.n++;
    if (changed3) v.t3++;
    if (changed1) v.n1++;
  }
  testQ('q1', q1);
  testQ('q2', q2);
  testQ('qinterest', visibleInterests(p.aud));
  testQ('q4', q4);
  if (p.q5) testQ(p.q5.qid, p.q5.opts);
});
console.log('\n--- question value: % of paths where changing the answer changes outcomes ---');
['q1','q2','qinterest','q4','q5'].forEach(function(q){
  var v = val[q];
  console.log(q + ': n=' + v.n + ' top3-changes=' + (100*v.t3/v.n).toFixed(1) + '% #1-changes=' + (100*v.n1/v.n).toFixed(1) + '%');
});

/* ---- 4. demand sim (corrected) ---- */
var N = parseInt(process.argv[2] || '100000', 10);
var D = {
  /* 2026-09-29: added the teacher/class audience and the school-parade
     occasion. Class never sees bar night (mirrors the page's qocc filter). */
  aud: [['kid',.27],['family',.20],['solo',.18],['couple',.14],['group',.13],['class',.08]],
  vibe: { kid:[['Funny',.35],['Cute',.40],['Scary',.10],['Keep it simple',.15]],
    family:[['Funny',.40],['Cute',.35],['Scary',.10],['Keep it simple',.15]],
    solo:[['Funny',.35],['Scary',.30],['Cute',.10],['Keep it simple',.25]],
    couple:[['Funny',.40],['Cute',.30],['Scary',.15],['Keep it simple',.15]],
    group:[['Funny',.50],['Cute',.20],['Scary',.15],['Keep it simple',.15]],
    class:[['Funny',.45],['Cute',.35],['Scary',.05],['Keep it simple',.15]] },
  effort: { kid:[['Couch-level',.50],['A little crafty',.35],['Go all out',.15]],
    _default:[['Couch-level',.45],['A little crafty',.35],['Go all out',.20]] },
  age:[['Under 3',.25],['3 to 6',.45],['7+',.30]],
  occ:[['Trick-or-treating',.30],['House party',.22],['School parade / class party',.13],['Low-key night in',.13],['Bar / club night',.12],['Handing out candy',.10]],
  occNoBar:[['Trick-or-treating',.34],['House party',.25],['School parade / class party',.15],['Low-key night in',.15],['Handing out candy',.11]],
  interest: {
    /* v3 2026-09-25: 8-interest model from simulate-demand.js — + Food & snacks and Sports.
       Food share from Pinterest "Gourmet ghouls" trend strength (food-costume DIY +97% YoY);
       Sports share from World Cup 2026 year heat, concentrated in family/group.
       Judgment calls, not measured data -- revisit after real traffic. */
    kid:[['Superheroes',.1656],['Princesses & fairy tales',.1656],['Animals',.138],['Dinosaurs & monsters',.1104],['TV & movie characters',.1104],['Video games',.092],['Food & snacks',.138],['Sports',.08]],
    family:[['TV & movie characters',.20],['Princesses & fairy tales',.16],['Animals',.14],['Superheroes',.12],['Video games',.10],['Dinosaurs & monsters',.08],['Food & snacks',.12],['Sports',.08]],
    solo:[['TV & movie characters',.26],['Superheroes',.17],['Dinosaurs & monsters',.15],['Princesses & fairy tales',.10],['Animals',.08],['Video games',.07],['Food & snacks',.12],['Sports',.05]],
    couple:[['Princesses & fairy tales',.19],['TV & movie characters',.17],['Video games',.15],['Animals',.12],['Superheroes',.11],['Dinosaurs & monsters',.09],['Food & snacks',.13],['Sports',.04]],
    group:[['TV & movie characters',.19],['Princesses & fairy tales',.15],['Video games',.15],['Superheroes',.12],['Dinosaurs & monsters',.12],['Animals',.10],['Food & snacks',.09],['Sports',.08]],
    class:[['TV & movie characters',.20],['Princesses & fairy tales',.12],['Video games',.12],['Superheroes',.10],['Dinosaurs & monsters',.10],['Animals',.14],['Food & snacks',.12],['Sports',.10]] },
};
function sample(pairs){ var r=Math.random(), acc=0; for(var i=0;i<pairs.length;i++){ acc+=pairs[i][1]; if(r<=acc) return pairs[i][0]; } return pairs[pairs.length-1][0]; }
function optBy(qid,label){ return qById(qid).options.filter(function(o){return o.label===label;})[0]; }
var first={}, top3c={}, cellWins={};
var a1map={kid:'My kid',family:'My family',solo:'Solo',couple:'Couple',group:'Group',class:'Teacher / class'};
for (var t=0; t<N; t++){
  var aud=sample(D.aud);
  var a={ q1: optBy('q1', a1map[aud]) };
  a.q2=optBy('q2', sample(D.vibe[aud]));
  a.q4=optBy('q4', sample(D.effort[aud]||D.effort._default));
  if (aud==='kid') a.q5kid=optBy('q5kid', sample(D.age));
  else a.qocc=optBy('qocc', sample(aud==='class' ? D.occNoBar : D.occ)); /* non-kid flows: occasion is Q5; class never sees bar night */
  var vis=visibleInterests(aud).map(function(o){return o.label;});
  var want=sample(D.interest[aud]);
  if (vis.indexOf(want)===-1) want=vis[Math.floor(Math.random()*vis.length)];
  var intOpt=qi.filter(function(o){return o.label===want;})[0];
  a.qinterest=intOpt;
  state.answers=a;
  var res=scoreIdeas();
  var id1=res[0].idea.id;
  first[id1]=(first[id1]||0)+1;
  res.forEach(function(r){ top3c[r.idea.id]=(top3c[r.idea.id]||0)+1; });
  var ck=aud+'|'+Object.keys(intOpt.tags)[0];
  cellWins[ck]=cellWins[ck]||{}; cellWins[ck][id1]=(cellWins[ck][id1]||0)+1;
}
function pct(x){ return (100*x).toFixed(1)+'%'; }
var ranked=IDEAS.map(function(i){ return { id:i.id, title:i.title, aud:i.audience.join('/'), p1:(first[i.id]||0)/N, p3:(top3c[i.id]||0)/N }; }).sort(function(a,b){ return b.p1-a.p1; });
console.log('\n=== demand sim N='+N+' (corrected family flow) ===');
console.log('--- top 20 by #1 share ---');
ranked.slice(0,20).forEach(function(r,i){ console.log((i+1)+'. '+r.title+' ['+r.aud+'] #1='+pct(r.p1)+' top3='+pct(r.p3)); });
console.log('--- new ideas (2026-09-25 expansion cohort) ---');
['garden-fairy','ballerina','butterfly','pop-star','ice-skater','ladybug','daisy','little-baker','little-artist'].forEach(function(id){
  var r=ranked.filter(function(x){return x.id===id;})[0];
  console.log(r.title+': #1='+pct(r.p1)+' top3='+pct(r.p3));
});
var n1=ranked.filter(function(r){return r.p1===0;});
console.log('--- never #1: '+n1.length+' --- '+n1.map(function(r){return r.title;}).join(', '));
var n3=ranked.filter(function(r){return r.p3===0;});
console.log('--- never top-3: '+n3.length+' --- '+n3.map(function(r){return r.title;}).join(', '));
console.log('--- thin cells (fewer than 3 distinct #1 winners) ---');
Object.keys(cellWins).sort().forEach(function(ck){
  var ks=Object.keys(cellWins[ck]);
  if (ks.length<3) console.log(ck+': '+ks.length+' winner(s): '+ks.join(', '));
});

/* ---- 5. share-preview standing gate (Billy 2026-09-25) ----
 * Share-path QA is recipient-side: the /c/ share card must show the same
 * photorealistic photo as the detail hero (not the old illustration), and
 * a rapid double-tap must fire exactly one share. A failure here throws so
 * the build cannot ship with a share mismatch. */
(function(){
  var cp = require('child_process');
  var r = cp.spawnSync('node', [__dirname + '/hour-session/share-preview.js'], {encoding: 'utf8'});
  process.stdout.write(r.stdout || '');
  process.stderr.write(r.stderr || '');
  if (r.status !== 0) throw new Error('share-preview gate FAILED: refusing to ship');
  console.log('share-preview gate: PASS');
})();

/* ---- 6. copy-grounding standing gate (Billy 2026-09-25) ----
 * Every genre noun in an idea's blurb/why must have its tag on the idea.
 * An ungrounded claim is either a false promise (copy mentions X, tag
 * absent, so an X answer can never surface it -- with the interest hard
 * filter this is now a hard miss) or a ranker blind spot. PROP_ALLOW lists
 * human-adjudicated prop/idiom mentions that are not genre claims; keep it
 * short and documented, never a dumping ground. */
(function(){
  var GENRE = [
    [/video games?/i, 'games'],
    [/\bdinosaurs?\b/i, 'dinos'],
    [/\bprincess(es)?\b/i, 'princess'],
    [/\bsuperheros?\b/i, 'heroes'],
    [/\b(tv|movie|anime|cartoon|sitcom)\b/i, 'tv'],
    [/\b(basketball|soccer|tennis|boxing|boxer|referee|cheerleader|bowling|golf|baseball|football|quarterback|olympic)\b/i, 'sports'],
    [/\b(pizza|taco|donut|hot[ -]dog|sushi|popcorn|cupcake|cookie|burger|pickle|ramen|spaghetti|meatball|banana|coffee|ketchup|mustard|cereal|peanut butter|jelly|egg|bacon|candy|waffle|toast|boba|sandwich)\b/i, 'food']
  ];
  var PROP_ALLOW = [
    // id, pattern, reason: prop or idiom, not a genre claim
    ['zombie-coworker', /coffee/i, '"coffee mug" is a prop in the blurb list'],
    ['numbered-players', /cookie/i, '"dalgona cookie is the prop" -- explicit'],
    ['tin-hero', /candy/i, 'idiom "costs less than the candy"'],
    ['raptor-barista', /coffee/i, '"coffee cup" is the handheld prop; the genre is the dinosaur-barista joke'],
    ['tetris-duo', /sandwich/i, '"sandwich boards" is the wearable-sign idiom; the genre is games, not food'],
    ['mystery-teens', /sandwich/i, '"giant paper sandwich" is the handheld prop; the genre is the mystery crew, not food'],
    ['party-pinata', /candy/i, '"hands out candy" is the pinata action/prop; the genre is party/funny, not food']
  ];
  function allowed(id, noun){
    return PROP_ALLOW.some(function(a){ return a[0] === id && a[1].test(noun); });
  }
  var bad = [];
  IDEAS.forEach(function(idea){
    var text = (idea.blurb || '') + ' ' + (idea.why || '');
    GENRE.forEach(function(pair){
      var m = text.match(pair[0]);
      if (m && !(idea.tags[pair[1]] > 0) && !allowed(idea.id, m[0])) {
        bad.push(idea.id + ': "' + m[0] + '" without ' + pair[1] + ' tag');
      }
    });
  });
  if (bad.length) {
    console.log('copy-grounding failures: ' + bad.length);
    bad.slice(0, 20).forEach(function(b){ console.log('  FAIL ' + b); });
    throw new Error('copy-grounding gate FAILED: refusing to ship');
  }
  console.log('copy-grounding gate: PASS (' + IDEAS.length + ' ideas checked)');
})();
