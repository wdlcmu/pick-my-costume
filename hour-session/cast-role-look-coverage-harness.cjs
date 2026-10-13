/* Cast role-look coverage harness (2026-10-13, Billy).
   Companion to cast-card-visual-harness.cjs. Billy on the cast flow:
   "I don't know what 'snowflake sprite' and others look like." ROLE_DIY
   started with 5 ideas; on 2026-10-13 it was expanded to every cast idea,
   each line grounded in its own guide (bank title, materials, steps,
   pictured caption). This harness is the guardrail for that expansion:

   - every role a user can pick or be assigned (castRoleOptions: named
     roles/pool + filler) resolves a ROLE_DIY look line, OR is listed in
     EXCEPTIONS below with a stated reason (the guide never dresses that
     role; inventing a look is worse than none)
   - every role resolves art: images/og/<idea>--<role>.jpg exists, or the
     role is the idea's filler (fillers use the crew-photo fallback in
     renderPersonalCards by design)
   - no stray ROLE_DIY lines (every key is a real cast option) and no
     stale exceptions (every exception is a real option with no line)
   - the original five ideas' lines stay byte-unchanged (ORIGINAL5)

   Run: node hour-session/cast-role-look-coverage-harness.cjs [app.js path]
   Exit code 1 on any failure. */
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const appPath = process.argv[2] ? path.resolve(process.argv[2]) : path.join(ROOT, "app.js");
const src = fs.readFileSync(appPath, "utf8");

function extractVar(name){
  const i = src.indexOf("var " + name + " = ");
  if (i < 0) throw new Error("var " + name + " not found");
  let j = src.indexOf("{", i), depth = 0, k = j, inStr = false, q = "", esc = false;
  for (; k < src.length; k++){
    const c = src[k];
    if (inStr){ if (esc) esc = false; else if (c === "\\") esc = true; else if (c === q) inStr = false; continue; }
    if (c === '"' || c === "'"){ inStr = true; q = c; continue; }
    if (c === "{") depth++;
    else if (c === "}"){ depth--; if (depth === 0){ k++; break; } }
  }
  return src.slice(j, k);
}
const CASTS = eval("(" + extractVar("CASTS") + ")");
const ROLE_DIY = eval("(" + extractVar("ROLE_DIY") + ")");
function roleSlugFor(role){
  return String(role || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}
function castRoleOptions(ideaId){
  const cast = CASTS[ideaId]; if (!cast) return [];
  const opts = (cast.mode === "choose") ? cast.pool.slice() : cast.roles.map(function(r){ return r.r; });
  const out = [];
  opts.forEach(function(o){ if (out.indexOf(o) < 0) out.push(o); });
  if (out.indexOf(cast.filler) < 0) out.push(cast.filler);
  return out;
}

const EXCEPTIONS = {
 "under-the-sea": {
  "sea witch": "The guide builds only the jellyfish, crab, fish, and seaweed looks; the sea witch is named in the cast list but given no garments, colors, materials, or props anywhere in the guide.",
  "sea king": "Same gap as sea witch: named in the cast list, but the guide assigns it no build, materials, or look.",
  "mermaid": "Named in the cast list, but the guide has no mermaid build; its sea looks are the umbrella jellyfish, red crab, cardboard fish, and streamer seaweed.",
  "prince": "Named in the cast list, but the guide assigns it no garments, materials, or props.",
  "seagull": "Named in the cast list, but the guide assigns it no garments, materials, or props."
 },
 "enchanted-castle-crew": {
  "dancing spoon": "Named in the cast list, but the guide gives the spoon no materials, build steps, or look; only the princess, prince, candelabra, clock, and teapot are built.",
  "castle guest": "Overflow filler role; the guide builds only its named characters and states no generic guest look."
 },
 "soccer-squad": {
  "coach": "Named in the cast list, but the guide dresses only the players (matching jerseys) and the referee (all black); the coach gets no garments or props.",
  "superfan": "Named in the cast list, but the guide assigns the superfan no garments, colors, or props."
 },
 "plug-socket": {
  "extension cord": "Overflow filler only; the guide builds just the plug and socket panels and gives a cord no look of its own."
 },
 "good-witch-bad-witch": {
  "munchkin": "Overflow filler only; the guide builds just the good witch and the bad witch and gives a munchkin no look."
 },
 "blue-alien-ohana": {
  "ohana elder": "Named in the cast list, but the guide builds only two looks: the alien (blue hoodie and antenna headband) and the girl (red dress with felt leaves). The elder is given no garments or props.",
  "ohana friend": "Overflow filler only; the guide builds only the alien and girl looks and states no third look."
 },
 "referee": {
  "player": "Named in the cast list, but this guide builds only the referee look (tape-striped black shirt, whistle, yellow flag); the player gets no garments or props."
 },
 "robot-ranger": {
  "ranger": "The guide builds only the robot look (foil box, vent-hose arms, sticker dials); the ranger role is given no garments, colors, or props."
 },
 "snow-sisters": {
  "snow friend": "Overflow filler for one of the original five ROLE_DIY ideas, whose entries stay byte-unchanged in this pass; the guide builds its eight named winter roles and gives the generic snow friend no look of its own."
 },
 "blue-dog-family": {
  "pup": "Overflow filler for one of the original five ROLE_DIY ideas, whose entries stay byte-unchanged in this pass; the guide covers pups through the named big pup and little pup lines."
 },
 "mermaid-crew": {
  "sea creature": "Overflow filler for one of the original five ROLE_DIY ideas, whose entries stay byte-unchanged in this pass; the guide builds its six named sea roles and gives the generic sea creature no look of its own."
 },
 "ghost-hunters": {
  "ghost hunter": "Overflow filler for one of the original five ROLE_DIY ideas, whose entries stay byte-unchanged in this pass; the guide covers hunters through the named team leader, tech expert, and rookie lines."
 }
};
const ORIGINAL5 = {
 "snow-sisters": {
  "ice queen": "Blue dress or a blue top and skirt, then stick snowflake stickers all over it.",
  "snow princess": "Blue or white dress with a few snowflake stickers, lighter than the queen.",
  "talking snowman": "White clothes, black button dots down the front, and the carrot nose.",
  "reindeer friend": "Brown clothes with the antler headband.",
  "mountain guide": "Hiking clothes and boots, with a coil of rope over one shoulder.",
  "snowflake sprite": "White or silver clothes with snowflake stickers, like the queen in miniature.",
  "ice harvester": "Flannel and work gloves, carrying a cardboard ice block.",
  "winter villager": "Cozy sweater and scarf in winter colors."
 },
 "blue-dog-family": {
  "mama dog": "Blue or orange shirt with matching felt ears on a headband, plus an eyeliner nose and whiskers.",
  "papa dog": "Blue or orange shirt with matching felt ears on a headband, plus an eyeliner nose and whiskers.",
  "big pup": "Same ears and whiskers as the grown-ups, on a blue or orange shirt.",
  "little pup": "Same ears and whiskers as the grown-ups, on a blue or orange shirt."
 },
 "mermaid-crew": {
  "mermaid": "Wrap shiny fabric as a tail skirt over leggings.",
  "prince": "White shirt and dark pants, like you just stepped off the boat.",
  "sea king": "Blue or teal clothes with a seashell crown.",
  "sea witch": "Dark clothes, dark makeup, and a shell crown.",
  "crab": "Red clothes with red claw mittens.",
  "seagull": "White and gray clothes. Flap your arms."
 },
 "ghost-hunters": {
  "team leader": "Khaki outfit, box backpack, and a name patch that says LEADER.",
  "tech expert": "Khaki outfit, box backpack with extra blinking buttons drawn on.",
  "rookie": "Khaki outfit, box backpack worn a little crooked.",
  "ghost": "White sheet with eye holes, floating behind the hunters."
 },
 "little-pig-family": {
  "mama pig": "Pink clothes, pink felt ears and a snout on a headband.",
  "papa pig": "Pink clothes, pink felt ears and a snout on a headband.",
  "little pig": "Pink clothes with smaller felt ears and a snout.",
  "dinosaur": "Green or brown clothes, carrying the toy dinosaur."
 }
};

let pass = 0, fail = 0;
function ok(cond, name, extra){
  if (cond){ pass++; }
  else { fail++; console.log("  FAIL:", name, extra || ""); }
}

let totalOpts = 0, withLine = 0, withExc = 0;
Object.keys(CASTS).forEach(function(ideaId){
  const cast = CASTS[ideaId];
  const opts = castRoleOptions(ideaId);
  opts.forEach(function(role){
    totalOpts++;
    const line = ROLE_DIY[ideaId] && ROLE_DIY[ideaId][role];
    const exc = EXCEPTIONS[ideaId] && EXCEPTIONS[ideaId][role];
    if (typeof line === "string" && line.length > 0){
      withLine++;
      ok(!exc, ideaId + " :: " + role + " has both a line and an exception");
    } else if (exc){
      withExc++;
      ok(typeof exc === "string" && exc.length >= 20, ideaId + " :: " + role + " exception states a real reason");
    } else {
      ok(false, ideaId + " :: " + role + " resolves a look line or an exception");
    }
    const art = path.join(ROOT, "images/og", ideaId + "--" + roleSlugFor(role) + ".jpg");
    ok(fs.existsSync(art) || role === cast.filler,
       ideaId + " :: " + role + " resolves art (file or filler fallback)", art);
  });
  /* No stray lines: every ROLE_DIY key is a real option. */
  Object.keys(ROLE_DIY[ideaId] || {}).forEach(function(role){
    ok(opts.indexOf(role) >= 0, ideaId + " :: ROLE_DIY key '" + role + "' is a real cast option");
  });
  /* No stale exceptions. */
  Object.keys(EXCEPTIONS[ideaId] || {}).forEach(function(role){
    ok(opts.indexOf(role) >= 0, ideaId + " :: exception '" + role + "' is a real cast option");
    ok(!(ROLE_DIY[ideaId] && ROLE_DIY[ideaId][role]), ideaId + " :: exception '" + role + "' has no line");
  });
});
/* Original five ideas: byte-unchanged lines. */
Object.keys(ORIGINAL5).forEach(function(ideaId){
  ok(JSON.stringify(ROLE_DIY[ideaId]) === JSON.stringify(ORIGINAL5[ideaId]),
     "original-five entry unchanged: " + ideaId);
});
ok(Object.keys(ROLE_DIY).length === Object.keys(CASTS).length,
   "ROLE_DIY covers every cast idea", Object.keys(ROLE_DIY).length + " vs " + Object.keys(CASTS).length);

console.log("cast options: " + totalOpts + " | with look line: " + withLine + " | with exception: " + withExc);
console.log(pass + " passed, " + fail + " failed");
process.exit(fail ? 1 : 0);
