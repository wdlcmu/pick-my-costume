#!/usr/bin/env python3
"""build_play.py -- port the peekaboo-costume-game artifact export into play.html.

Source: ~/workspace/your_files/peekaboo-costume-game/peekaboo-costume-game.html
(artifact.export of the peekaboo-costume-game web artifact).

Transformations:
  1. Drop the dead <script type="text/plain"> block (the previous 6-round
     game version; inert, ~1.27MB).
  2. Replace the 6 inlined costume PNG data URIs in `looks` with external
     images/play/<key>.webp files (~95KB total vs ~945KB base64).
  3. Site head: title, meta description, og tags, canonical, pumpkin favicon.
  4. Slim top bar with a back link + site footer credit.
  5. PostHog pageview + minimal play_started / play_completed events.

2026-09-28 root-cause guard: play.html now carries post-generation edits made
DIRECTLY to the generated file (playtest fixes: tapGuard, withProbe, named
guide links, tooltip, cartoon alt texts, no mid-run HUD switcher; distribution:
"Share my score" button, share_created analytics, ?s= recipient branch,
finish-screen quiz CTA). A blind regen from the artifact source would silently
WIPE all of that (it did once: commit cc25518e). The FEATURE_GUARD assertion
below fails loudly instead of writing a wiped file. If it fails, do not
regen: port the listed features into the generator first.

Usage: python3 build_play.py   (writes ../play.html)
"""
import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = os.path.expanduser("~/workspace/your_files/peekaboo-costume-game/peekaboo-costume-game.html")
OUT = os.path.join(REPO, "play.html")

KEYS = ["little-pumpkin", "bumblebee", "baby-dino",
        "friendly-ghost", "little-witch", "tiny-astronaut"]

src = open(SRC, encoding="utf-8").read()

# 1. Drop the dead text/plain block (previous game version, inert).
src, n = re.subn(r'<script type="text/plain"[^>]*>.*?</script>\s*', "", src, flags=re.S)
assert n == 1, f"expected 1 text/plain block, removed {n}"
assert "var makes=" not in src, "dead makes array survived"

# 2. Externalize costume images.
for key in KEYS:
    pat = re.compile(r"image:'data:image/png;base64,[A-Za-z0-9+/=]+'")
    src, n = pat.subn(f"image:'images/play/{key}.webp'", src, count=1)
    assert n == 1, f"expected 1 data URI for {key}, replaced {n}"
assert "data:image/png;base64" not in src, "a data URI survived"

# 2b. Guide-link remap (Billy 2026-09-28): the artifact's guide slugs
# little-pumpkin, friendly-ghost, tiny-astronaut have no /c/ guides on the
# site (the bank carries astronaut + classic-ghost, and no pumpkin at all),
# so their "See how to make it" links 404'd. Remap to the closest live
# guides. Round 1's featured costume becomes bumblebee (the kid matched
# bee antennae that round; /c/bumble-bee is live).
src, n = re.subn(r"guide:'https://pickmycostume\.com/c/friendly-ghost'",
                 "guide:'https://pickmycostume.com/c/classic-ghost'", src)
assert n == 1, f"expected 1 friendly-ghost guide, remapped {n}"
src, n = re.subn(r"guide:'https://pickmycostume\.com/c/tiny-astronaut'",
                 "guide:'https://pickmycostume.com/c/astronaut'", src)
assert n == 1, f"expected 1 tiny-astronaut guide, remapped {n}"
src, n = re.subn(r"\{label:'Easy matches',featured:'little-pumpkin'",
                 "{label:'Easy matches',featured:'bumblebee'", src)
assert n == 1, f"expected 1 little-pumpkin featured, remapped {n}"
# The little-pumpkin looks entry keeps its image/name (used by round 1 pairs)
# but there is no pumpkin guide on the site, so its guide stays empty and the
# finish screen renders it unlinked rather than pointing at a wrong costume.
src, n = re.subn(r"guide:'https://pickmycostume\.com/c/little-pumpkin'",
                 "guide:''", src)
assert n == 1, f"expected 1 little-pumpkin guide, remapped {n}"

# 2c. Expanded game (Billy 2026-09-28).
#   a. Six peekaboo rounds (all 6 inline SVG costumes) with rising difficulty:
#      reveal type (center split / side peek / top peek) + open amount shrink.
#      Per-round peek button labels. Dynamic "N of M" finish copy.
#   b. Game switcher: HUD topline button + finish-screen button, both directions.
#   c. Finish screen lists each costume found with its /c/ guide link
#      (pirate + little-pumpkin have no guide: rendered unlinked, honestly).

# --- a1. peekRounds: 3 -> 6. Choices per round reuse the artifact's own
# --- retired 6-round lists (kid-tested naming: 'Friendly Ghost', 'Dinosaur').
src, n = re.subn(
    r"var peekRounds=\[.*?\];",
    "var peekRounds=["
    "     {id:'ghost',name:'Friendly Ghost',level:'easy',rv:'center',open:72,label:'Easy peek',peek:'Peek!',guide:'https://pickmycostume.com/c/classic-ghost',choices:['Friendly Ghost','Astronaut','Dinosaur']},"
    "     {id:'witch',name:'Witch',level:'easy',rv:'center',open:55,label:'Getting warmer',peek:'Take a peek',guide:'https://pickmycostume.com/c/little-witch',choices:['Pirate','Robot','Witch']},"
    "     {id:'pirate',name:'Pirate',level:'tricky',rv:'side',open:45,label:'Trickier',peek:'Sneak a look',guide:'',choices:['Astronaut','Pirate','Friendly Ghost']},"
    "     {id:'astronaut',name:'Astronaut',level:'tricky',rv:'top',open:35,label:'Look closer',peek:'Spy the top',guide:'https://pickmycostume.com/c/astronaut',choices:['Robot','Dinosaur','Astronaut']},"
    "     {id:'dinosaur',name:'Dinosaur',level:'super',rv:'center',open:22,label:'Super sleuth',peek:'Tiny peek',guide:'https://pickmycostume.com/c/baby-dino',choices:['Witch','Friendly Ghost','Dinosaur']},"
    "     {id:'robot',name:'Robot',level:'super',rv:'side',open:12,label:'Master detective',peek:'Super sneaky peek',guide:'https://pickmycostume.com/c/robot-ranger',choices:['Pirate','Robot','Astronaut']}"
    "   ];",
    src, flags=re.S)
assert n == 1, f"expected 1 peekRounds block, replaced {n}"

# --- a2. Curtain variety: reveal-type classes driven by --open, replacing the
# --- three hardcoded level-based open amounts. (level-* classes remain for the
# --- super-zoom rule only.)
old_curtain = (".stage.peeked.level-easy .curtain div:first-child{transform:translateX(-72%)}"
    ".stage.peeked.level-easy .curtain div:last-child{transform:translateX(72%)}"
    ".stage.peeked.level-tricky .curtain div:first-child{transform:translateX(-42%)}"
    ".stage.peeked.level-tricky .curtain div:last-child{transform:translateX(42%)}"
    ".stage.peeked.level-super .curtain div:first-child{transform:translateX(-13%)}"
    ".stage.peeked.level-super .curtain div:last-child{transform:translateX(13%)}")
new_curtain = (".stage{--open:60%;overflow:hidden}"
    ".stage.peeked.rv-center .curtain div:first-child{transform:translateX(calc(var(--open)*-1))}"
    ".stage.peeked.rv-center .curtain div:last-child{transform:translateX(var(--open))}"
    ".stage.peeked.rv-side .curtain div{transform:translateX(var(--open))}"
    ".stage.peeked.rv-top .curtain div{transform:translateY(var(--open))}")
assert old_curtain in src, "curtain CSS anchor not found"
src = src.replace(old_curtain, new_curtain)

# --- a3. renderPeek: set rv class + --open + per-round peek label.
old = "stage.className='stage level-'+item.level;"
assert src.count(old) == 1, "renderPeek className anchor not unique"
src = src.replace(old,
    "stage.className='stage level-'+item.level+' rv-'+item.rv;"
    "stage.style.setProperty('--open',item.open+'%');")
old = "document.getElementById('peek').style.display='block';"
assert src.count(old) == 1, "peek-button anchor not unique"
src = src.replace(old,
    "var pk=document.getElementById('peek');pk.style.display='block';pk.textContent=item.peek;")

# --- c1. Finish screen: dynamic "N of M" copy + per-costume guide list.
old = ("document.getElementById('result').textContent="
       "mode==='match'?'You matched all 3 rounds':'You found 3 out of 3';")
assert src.count(old) == 1, "showFinish result anchor not unique"
src = src.replace(old,
    "document.getElementById('result').textContent="
    "mode==='match'?'You matched all 3 rounds!':'You found '+points+' out of '+peekRounds.length+'!';")
old = ("document.getElementById('finishCopy').textContent="
       "mode==='match'?'Every piece found its costume.':'Easy peek to super sleuth \u2014 you spotted them all.';")
assert src.count(old) == 1, "showFinish copy anchor not unique"
src = src.replace(old,
    "document.getElementById('finishCopy').textContent="
    "mode==='match'?'Every piece found its costume.':'Easy peek to master detective \u2014 you spotted them all.';"
    "renderFoundList();")

# NOTE: the game script is wrapped in (function(){...})(); all game-logic
# additions must be injected INSIDE that IIFE, not as separate <script>
# blocks (separate blocks cannot see mode/start/looks/peekRounds).
IIFE_TAIL = "if(soundOn)tone(600,.15,0)});\n})();\n"
assert src.count(IIFE_TAIL) == 1, "IIFE tail anchor not unique"

# --- c2. renderFoundList(): every costume found, linked to its /c/ guide.
# --- Costumes without a guide (pirate, little-pumpkin: no such guides exist
# --- in the bank) render as plain unlinked chips.
inner_js = """
/* 2026-09-28: finish screen lists each costume found with its guide link. */
function renderFoundList(){
  var box=document.getElementById('foundList');if(!box)return;box.innerHTML='';
  var items=mode==='match'
    ?Object.keys(looks).map(function(k){return {name:looks[k].name,guide:looks[k].guide};})
    :peekRounds.map(function(r){return {name:r.name,guide:r.guide};});
  var head=document.createElement('p');head.className='found-head';
  head.textContent='See how to make them:';box.appendChild(head);
  var grid=document.createElement('div');grid.className='found-grid';
  items.forEach(function(it){
    if(it.guide){
      var a=document.createElement('a');a.className='found-chip';a.href=it.guide;
      a.target='_blank';a.rel='noopener';
      var nm=document.createElement('span');nm.textContent=it.name;a.appendChild(nm);
      var ar=document.createElement('span');ar.setAttribute('aria-hidden','true');ar.textContent=' \\u2192';a.appendChild(ar);
      grid.appendChild(a);
    }else{
      var s=document.createElement('span');s.className='found-chip no-link';s.textContent=it.name;
      grid.appendChild(s);
    }
  });
  box.appendChild(grid);
}
/* 2026-09-28: game switcher. Either mode can jump to the other mid-run. */
var switchGame=document.getElementById('switchGame'),switchGameEnd=document.getElementById('switchGameEnd');
function syncSwitchLabel(){if(switchGame)switchGame.textContent=mode==='peek'?'Try: Match the pieces':'Try: Peekaboo';}
function switchToOther(){if(mode==='peek'){startMaterials()}else{start()}}
if(switchGame)switchGame.addEventListener('click',switchToOther);
if(switchGameEnd)switchGameEnd.addEventListener('click',switchToOther);
"""
src = src.replace(IIFE_TAIL,
    "if(soundOn)tone(600,.15,0)});\n" + inner_js + "\n})();\n")

# --- c3. found-list + switcher CSS.
found_css = """
    /* 2026-09-28: finish-screen guide list + game switcher. */
    .hudswitch{font:inherit;font-size:13px;font-weight:700;color:var(--teal-dark);background:#fff;
      border:2px solid var(--teal-dark);border-radius:999px;padding:8px 14px;min-height:44px;cursor:pointer}
    .found-list{margin:20px auto 0;max-width:560px}
    .found-head{margin:0 0 10px;font-weight:800;color:var(--ink)}
    .found-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
    .found-chip{min-height:56px;display:flex;align-items:center;justify-content:center;gap:6px;
      background:#fff;border:2px solid var(--ink);border-radius:16px;font-weight:800;color:var(--ink);
      text-decoration:none;font-size:16px;padding:10px 12px}
    a.found-chip{color:var(--teal-dark);border-color:var(--teal-dark)}
    .found-chip.no-link{opacity:.65;border-style:dashed}
"""
src = src.replace("</style>", found_css + "  </style>", 1)

# --- b1. Switcher buttons: HUD topline + finish actions + found-list mount.
old = '<div class="round-label" id="roundLabel">Round 1 of 3</div>\n      <div class="score">'
assert src.count(old) == 1, "HUD anchor not unique"
src = src.replace(old,
    '<div class="round-label" id="roundLabel">Round 1 of 6</div>\n'
    '      <button class="hudswitch" id="switchGame" type="button">Try: Match the pieces</button>\n'
    '      <div class="score">')
old = ('<div class="actions"><button class="primary" id="again">Play again</button>'
       '<button class="quiet" id="sound" aria-pressed="true">Sound on</button></div>')
assert src.count(old) == 1, "finish actions anchor not unique"
src = src.replace(old,
    '<div class="found-list" id="foundList"></div>'
    '<div class="actions"><button class="primary" id="again">Play again</button>'
    '<button class="quiet" id="switchGameEnd" type="button">Try the other game</button>'
    '<button class="quiet" id="sound" aria-pressed="true">Sound on</button></div>')

# --- b2. Switcher labels synced on every mode start.
old = "function start(){mode='peek';resetRun();setScreen(game);renderPeek()}"
assert src.count(old) == 1, "start() anchor not unique"
src = src.replace(old,
    "function start(){mode='peek';resetRun();setScreen(game);syncSwitchLabel();renderPeek()}")
old = "function startMaterials(){mode='match';resetRun();setScreen(materials);renderMatch()}"
assert src.count(old) == 1, "startMaterials() anchor not unique"
src = src.replace(old,
    "function startMaterials(){mode='match';resetRun();setScreen(materials);syncSwitchLabel();renderMatch()}")

# 2d. Match-mode variety (Billy 2026-09-28): round 1's three pieces were all
# green and the mode had only 3 rounds reusing the same costumes. Expand to
# 6 rounds x 3 pairs; every costume appears 3x with a DIFFERENT literal piece
# each time; within a round the 3 pieces differ in color, shape, silhouette.
# Difficulty ramps via piece size (big obvious pieces -> tiny details).
src, n = re.subn(
    r"var matchRounds=\[.*?\];",
    "var matchRounds=["
    "     {label:'Easy matches',tip:'Tap a piece, then its costume.',featured:'bumblebee',pairs:["
    "       {id:'witch-hat',label:'Pointy hat',type:'hat',to:'little-witch'},"
    "       {id:'dino-tail',label:'Dinosaur tail',type:'tail',to:'baby-dino'},"
    "       {id:'bee-wings',label:'Bee wings',type:'wings',to:'bumblebee'}]},"
    "     {label:'More pieces',tip:'New pieces — look at the shapes.',featured:'friendly-ghost',pairs:["
    "       {id:'stem',label:'Pumpkin stem',type:'stem',to:'little-pumpkin'},"
    "       {id:'poncho',label:'White poncho',type:'poncho',to:'friendly-ghost'},"
    "       {id:'helmet',label:'Space helmet',type:'helmet',to:'tiny-astronaut'}]},"
    "     {label:'Look closer',tip:'Small details count.',featured:'little-witch',pairs:["
    "       {id:'antennae',label:'Bee antennae',type:'headband',to:'bumblebee'},"
    "       {id:'broom',label:'Broom',type:'broom',to:'little-witch'},"
    "       {id:'orange-fabric',label:'Orange fabric',type:'fabric-orange',to:'little-pumpkin'}]},"
    "     {label:'Tricky pairs',tip:'Look at every little detail.',featured:'friendly-ghost',pairs:["
    "       {id:'ghost-eyes',label:'Ghost eyes',type:'ghost-eyes',to:'friendly-ghost'},"
    "       {id:'stripes',label:'Bee stripes',type:'stripes',to:'bumblebee'},"
    "       {id:'vine',label:'Pumpkin vine',type:'vine',to:'little-pumpkin'}]},"
    "     {label:'Super matcher',tip:'Almost there — look closely.',featured:'tiny-astronaut',pairs:["
    "       {id:'mission-patch',label:'Mission patch',type:'patch',to:'tiny-astronaut'},"
    "       {id:'claws',label:'Dino claws',type:'claws',to:'baby-dino'},"
    "       {id:'black-fabric',label:'Black fabric',type:'fabric-black',to:'little-witch'}]},"
    "     {label:'Master matcher',tip:'The tiniest clues. You’ve got this.',featured:'baby-dino',pairs:["
    "       {id:'silver-tape',label:'Silver tape',type:'tape',to:'tiny-astronaut'},"
    "       {id:'spikes',label:'Dino spikes',type:'spikes',to:'baby-dino'},"
    "       {id:'white-fabric',label:'White fabric',type:'fabric-white',to:'friendly-ghost'}]}"
    "   ];",
    src, flags=re.S)
assert n == 1, f"expected 1 matchRounds block, replaced {n}"

# 9 new literal piece icons (hand-drawn SVGs of the actual items).
anchor = "'fabric-black':"
i = src.find(anchor)
assert i > 0, "icon paths anchor not found"
j = src.find("\n    };", i)
assert j > i, "icon paths end not found"
new_icons = (
    ",\n       'wings':'<ellipse cx=\"8\" cy=\"13\" rx=\"4.6\" ry=\"8\" fill=\"#fff\"/>"
    "<ellipse cx=\"16\" cy=\"13\" rx=\"4.6\" ry=\"8\" fill=\"#fff\"/>"
    "<path d=\"M8 6v14M16 6v14\" stroke=\"#9db8c6\" stroke-width=\"1.2\"/>',\n"
    "       'spikes':'<path d=\"M5 19l4-11 4 11Z\" fill=\"#67b96b\"/>"
    "<path d=\"M11 19l4-8 4 8Z\" fill=\"#4da355\"/><path d=\"M15.5 19l3-5 3 5Z\" fill=\"#67b96b\"/>',\n"
    "       'ghost-eyes':'<ellipse cx=\"8.5\" cy=\"12\" rx=\"3.2\" ry=\"4.5\" fill=\"#26223a\"/>"
    "<ellipse cx=\"15.5\" cy=\"12\" rx=\"3.2\" ry=\"4.5\" fill=\"#26223a\"/>',\n"
    "       'broom':'<path d=\"M14 2l2 1-6 12-2-1Z\" fill=\"#8a5a33\"/>"
    "<path d=\"M4 15l6-2 3 5-6 2Z\" fill=\"#e3b96b\"/>"
    "<path d=\"M6.5 15.5 9.5 19M8.5 14.8l2.6 3\" stroke=\"#8a5a33\" stroke-width=\"1\"/>',\n"
    "       'helmet':'<circle cx=\"12\" cy=\"12\" r=\"8\" fill=\"#dceef5\"/>"
    "<path d=\"M7.5 11a5 5 0 0 1 9 0\" stroke=\"#fff\" stroke-width=\"2\" fill=\"none\"/>',\n"
    "       'fabric-orange':'<path d=\"M5 5h13l1 13H6Z\" fill=\"#ff8c1a\"/>"
    "<path d=\"m8 5 1 13M14 5l1 13M6 12h13\" stroke=\"#d96f0a\"/>',\n"
    "       'stripes':'<rect x=\"4\" y=\"9\" width=\"16\" height=\"7\" rx=\"3.5\" fill=\"#ffbd2e\"/>"
    "<path d=\"M9.5 9v7M14.5 9v7\" stroke=\"#26223a\" stroke-width=\"2.5\"/>',\n"
    "       'vine':'<path d=\"M6 20Q6 12 12 12q5 0 5-6\" fill=\"none\"/>"
    "<path d=\"M12 12q-4-1-5-5q4 0 5 5Z\" fill=\"#67b96b\"/>',\n"
    "       'claws':'<path d=\"M7 18 9 8l3 10Z\" fill=\"#fff\"/>"
    "<path d=\"M12 19l2-11 3 11Z\" fill=\"#fff\"/><path d=\"M16.5 18l2-7 2.5 7Z\" fill=\"#eef2f5\"/>'\n"
)
src = src[:j] + new_icons + src[j:]

# Per-round match prompt (was a 3-round ternary with a wrong fallback line).
old = ("document.getElementById('matchPrompt').textContent="
       "round===0?'Tap a piece, then its costume.':round===1?'The clues are getting smaller.'"
       ":'Look closely — two costumes look alike.';")
assert src.count(old) == 1, "matchPrompt anchor not unique"
src = src.replace(old,
    "document.getElementById('matchPrompt').textContent=item.tip;")

# Dynamic match finish copy (was hardcoded "3 rounds").
old = "mode==='match'?'You matched all 3 rounds!'"
assert src.count(old) == 1, "match finish copy anchor not unique"
src = src.replace(old, "mode==='match'?'You matched all '+matchRounds.length+' rounds!'")

# 3a. Head: title + meta.
src = src.replace(
    "<title>Peekaboo Costume Game</title>",
    "<title>Costume Games for Kids: Play to Pick | Pick My Costume</title>\n"
    '  <meta name="description" content="Two free costume games for kids: peek behind the curtain and match the pieces to pick a Halloween costume. No account, no email.">\n'
    '  <meta property="og:type" content="website">\n'
    '  <meta property="og:url" content="https://pickmycostume.com/play">\n'
    '  <meta property="og:title" content="Costume Games for Kids | Pick My Costume">\n'
    '  <meta property="og:description" content="Peek behind the curtain or match the pieces, then see how to make the costume. Free, no account.">\n'
    '  <meta property="og:image" content="https://pickmycostume.com/images/og/play.jpg">\n'
    '  <meta name="twitter:card" content="summary_large_image">\n'
    '  <link rel="canonical" href="https://pickmycostume.com/play">\n'
    '  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 64 64\'%3E%3Cellipse cx=\'32\' cy=\'37\' rx=\'24\' ry=\'20\' fill=\'%23ff8c1a\'/%3E%3Crect x=\'29\' y=\'9\' width=\'6\' height=\'12\' rx=\'3\' fill=\'%232e7d32\'/%3E%3Ccircle cx=\'24\' cy=\'35\' r=\'3\' fill=\'%232a1500\'/%3E%3Ccircle cx=\'40\' cy=\'35\' r=\'3\' fill=\'%232a1500\'/%3E%3Cpath d=\'M24 45 Q32 51 40 45\' stroke=\'%232a1500\' stroke-width=\'3\' fill=\'none\' stroke-linecap=\'round\'/%3E%3C/svg%3E">',
)

# 3b. PostHog pageview (same anonymous snippet as the rest of the site).
posthog = """<script>
/* PostHog: anonymous usage stats only. Session replay is off. */
(function(){
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://us.i.posthog.com/static/array.js";
  s.onload = function(){
    try {
      if (window.posthog && posthog.init) {
        posthog.init("phc_t9dkHXAZR5VEjPFm3K5JDzGKFsNNxKcwSxxcEBEeLbS7", {
          api_host: "https://us.i.posthog.com",
          autocapture: false,
          capture_pageview: true,
          disable_session_recording: true
        });
      }
    } catch(e){}
  };
  document.head.appendChild(s);
})();
</script>
"""
src = src.replace("</head>", posthog + "</head>")

# 4. Site chrome: top bar + footer CSS + markup.
chrome_css = """
    /* 2026-09-28 Play tab: site chrome. Slim top bar + footer credit. */
    .sitebar{max-width:760px;margin:0 auto;padding:14px clamp(16px,4vw,30px) 0;display:flex;align-items:center}
    .sitebar a{color:var(--teal-dark);font-weight:800;text-decoration:none;font-size:15px}
    .sitebar a:hover{text-decoration:underline}
    .sitefoot{max-width:760px;margin:0 auto;padding:26px clamp(16px,4vw,30px) calc(30px + env(safe-area-inset-bottom));text-align:center}
    .sitefoot p{margin:0;font-size:13px;color:var(--muted)}
    .loopback{margin:20px auto 0;text-align:center;font-size:1rem;color:var(--muted)}
    .loopback a{color:var(--teal-dark);font-weight:800}
    .loopback a:hover{text-decoration:underline}
"""
src = src.replace("</style>", chrome_css + "  </style>")

topbar = '<div class="sitebar"><a href="/">&larr; Pick My Costume</a></div>\n'
src = src.replace("<body>", "<body>\n" + topbar, 1)

footer = ('<footer class="sitefoot"><p>Built with Muse. Made by Billy Litner.</p></footer>\n')
src = src.replace("</body>", footer + "</body>", 1)

# 4b. 2026-10-13 audit fix: loop-back CTA under the intro game buttons, so a
# /play landing can still reach the quiz (the /c/ banner's quiz target is
# "/?" + context params; with no share context here it reduces to "/",
# the same target the finish-screen CTA uses). Mirrors the direct edit
# in play.html; FEATURE_GUARD below carries the marker.
loopback = ('\n        <p class="loopback"><a href="/">Or find your costume</a>'
            ' with the 2-minute quiz</p>')
src, n = re.subn(r'(<div class="mode-buttons">.*?</div>)', r'\1' + loopback,
                 src, count=1, flags=re.S)
assert n == 1, "loop-back CTA anchor (mode-buttons) not found"

# 5. Game events (guarded; never break the game if PostHog is blocked).
events = """<script>
/* 2026-09-28 Play tab: minimal game analytics. Guarded so ad-blockers never break play. */
(function(){
  function cap(name, props){
    try { if (window.posthog && posthog.capture) posthog.capture(name, props || {}); } catch(e){}
  }
  var curMode = '';
  document.addEventListener('DOMContentLoaded', function(){
    var s1 = document.getElementById('start'), s2 = document.getElementById('startMaterials');
    if (s1) s1.addEventListener('click', function(){ curMode='peek'; cap('play_started', {mode:'peek'}); });
    if (s2) s2.addEventListener('click', function(){ curMode='match'; cap('play_started', {mode:'match'}); });
    var fin = document.getElementById('finish');
    if (fin && window.MutationObserver) {
      var fired = false;
      new MutationObserver(function(){
        if (!fired && fin.classList.contains('active')) {
          fired = true;
          var sc = document.getElementById('score');
          cap('play_completed', {mode: curMode, stars: sc ? sc.textContent : ''});
        }
      }).observe(fin, {attributes:true, attributeFilter:['class']});
    }
    var again = document.getElementById('again');
    if (again) again.addEventListener('click', function(){ fired = false; });
  });
})();
</script>
"""
src = src.replace("</body>", events + "</body>", 1)

# 6. 2026-09-28 root-cause guard: the generated output must carry the
# post-generation features that live ONLY in the generated play.html (made
# as direct edits after a regen: playtest fixes + Share-my-score). If the
# artifact source is stale, the regen silently wipes them (commit cc25518e
# wiped them on the live site). Fail loudly BEFORE writing, so a bad regen
# can never touch the tree's play.html.
FEATURE_GUARD = [
    "share_created",                 # Share-my-score analytics (f5963501)
    "play_shared_opened",            # ?s=<sid> recipient branch
    "tapGuard",                      # finger-bounce guard on multi-step flows
    "withProbe",                     # ?probe= passthrough on guide links
    "finishQuiz",                    # finish-screen quiz CTA (distribution)
    "Or find your costume",          # intro loop-back quiz CTA (2026-10-13 audit)
    "how-to guide coming soon",      # tooltip on guide-less chips
    "See how to make the",           # named guide links per costume
    "Cartoon friendly ghost costume",# cartoon alt texts (playtest fix)
    "og/play.jpg",                   # OG card meta
]
missing = [m for m in FEATURE_GUARD if m not in src]
if missing:
    raise SystemExit(
        "REFUSING REGEN: generated play.html would be missing post-generation "
        f"features: {missing}. The artifact source is stale; the tree file was "
        "NOT touched. Port the listed features into this generator first, "
        "then re-run."
    )

open(OUT, "w", encoding="utf-8").write(src)
print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB)")
print("feature guard OK: all post-generation features present")
