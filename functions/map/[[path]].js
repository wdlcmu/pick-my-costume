// Per-URL og injection for /map region + costume deep links.
// Regenerate with: python3 hidden_files/galaxy/build_map_function.py (emits this
// file from galaxy-data.json -- do not hand-edit the tables).
//
// map.html is a static file, so every shared /map/* URL would unfurl in chat
// apps with the same generic preview ("Costume Galaxy: explore all 164
// costumes" / blue-dog-family image). Per-region and per-costume
// og:title/og:description/og:image/og:url are injected here, server-side, on
// the fetch path. Unknown regions, unknown costume ids, and /map itself fall
// through to the generic asset meta. The page is served by rewriting the
// pathname to /map.html and proxying through ASSETS, so query params
// (?probe=) pass through untouched.
//
// Mirrors the /party pattern: region/idea table -> esc() -> og meta values ->
// Response. The difference is a table lookup keyed by the URL path segments
// instead of a query token. GET only: non-GET requests pass through to ASSETS
// untouched (crawlers unfurl with GET, so this path is the only one that ever
// needs injection).

// (tables emitted by build_map_function.py from galaxy-data.json -- see header)
var MAP_REGIONS = {
  "dinosaur-land": {
    "name": "Dinosaur Land",
    "syn": "Stomp, roar, repeat \u2014 Jurassic joy for every age.",
    "img": "baby-dino",
    "count": 10
  },
  "food-court": {
    "name": "Food Court",
    "syn": "Dress as dinner. The tastiest corner of the galaxy.",
    "img": "pizza-slice",
    "count": 31
  },
  "princess-castle": {
    "name": "Princess Castle",
    "syn": "Tiaras, fairy wings, and happily-ever-after.",
    "img": "fairy-tale-princesses",
    "count": 13
  },
  "fright-night": {
    "name": "Fright Night",
    "syn": "Ghosts, ghouls, and things that go bump.",
    "img": "classic-ghost",
    "count": 18
  },
  "hero-headquarters": {
    "name": "Hero Headquarters",
    "syn": "Capes on. Time to save Halloween.",
    "img": "superhero-family",
    "count": 12
  },
  "animal-kingdom": {
    "name": "Animal Kingdom",
    "syn": "Go wild \u2014 from buzzing bees to big jungle energy.",
    "img": "bumble-bee",
    "count": 16
  },
  "sports-arena": {
    "name": "Sports Arena",
    "syn": "Game on \u2014 the MVPs of the costume world.",
    "img": "soccer-squad",
    "count": 8
  },
  "pop-culture-plaza": {
    "name": "Pop Culture Plaza",
    "syn": "Screen legends, memes, and main characters.",
    "img": "mystery-crew",
    "count": 32
  },
  "silly-street": {
    "name": "Silly Street",
    "syn": "Pure silliness, zero scares.",
    "img": "moth-porch-light",
    "count": 24
  }
};

var MAP_IDEAS = {"neon-demon-hunter": {"t": "Neon Demon Hunter", "b": "Streetwear with glowing sigils, a foam sword, and pop-idol hair and makeup."}, "classic-ghost": {"t": "Classic Ghost", "b": "A white sheet with cut-out eyes."}, "blue-dog-family": {"t": "Aussie Dog Family", "b": "Dog-ear headbands and blue-or-orange shirts: mama, dad, and the pups."}, "superhero-family": {"t": "Superhero Family", "b": "Red sweatsuits, black eye masks, felt logo. The whole family goes super."}, "blue-alien-ohana": {"t": "Blue Alien Ohana", "b": "A blue hoodie and an antenna headband turn the kid into the alien."}, "emerald-witch": {"t": "Emerald Witch", "b": "An all-green-everything gown, dramatic makeup, and a pointy hat gone couture."}, "gloom-bloom": {"t": "Gloom & Bloom", "b": "Braids and black for Gloom, color-pop and smiles for Bloom."}, "deadpan-diva": {"t": "Deadpan Diva", "b": "Black dress, two braids, pale makeup, and a stare that ends conversations."}, "safari-zoo-crew": {"t": "Safari / Zoo Crew", "b": "Everyone picks an animal: closet clothes in matching colors plus an ear headband."}, "fairy-tale-princesses": {"t": "Fairy Tale Princesses", "b": "A dress or a crown from the closet. Every princess works."}, "tin-hero": {"t": "The Tin Hero", "b": "Red and gold plus a glowing chest circle: the suit does the talking."}, "good-witch-bad-witch": {"t": "Good Witch, Bad Witch", "b": "Green face paint and black for one, pink gown and crown for the other."}, "fuzzy-monster": {"t": "Fuzzy Monster", "b": "A pastel fuzzy sweatsuit with giant googly eyes and an oversized stitched smile."}, "pocket-plush": {"t": "Pocket Plush Monster", "b": "A fuzzy one-piece, giant ears, a stitched smile, and an oversized collector tag."}, "soccer-squad": {"t": "Soccer Squad", "b": "Jerseys for the players, black for the ref, one red card."}, "glow-skeleton": {"t": "Glow Skeleton", "b": "Black sweats with glow-in-the-dark bone tape, plus glow bracelets."}, "block-game-crew": {"t": "Block Game Crew", "b": "Cardboard-box heads: pick your blocky hero."}, "web-slinger-crew": {"t": "Web Hero Crew", "b": "Red, black, and pink hoodies plus masks. Pick your spider."}, "mermaid-crew": {"t": "Mermaid Crew", "b": "The mermaid, the prince, the sea king, the sea witch, or the crab: pick your role."}, "little-pig-family": {"t": "Little Pig Family", "b": "Pink clothes and a snout headband; little brother brings the dinosaur."}, "enchanted-castle-crew": {"t": "Enchanted Castle Crew", "b": "The bookish princess, the cursed prince, the talking candelabra, the talking clock, the talking teapot: pick your role."}, "bumble-bee": {"t": "Bumble Bee", "b": "Black sweats with yellow tape stripes and soft felt antennae."}, "baby-dino": {"t": "Baby Dinosaur", "b": "Green hoodie, felt spikes down the back, stuffed tail."}, "little-lion": {"t": "Little Lion", "b": "Tan sweatsuit plus a fuzzy mane hood."}, "tiny-firefighter": {"t": "Tiny Firefighter", "b": "Red sweats, a plastic helmet, and a toy hose."}, "little-shark": {"t": "Little Shark", "b": "Gray hoodie with a felt fin glued on the back."}, "walking-taco": {"t": "Walking Taco", "b": "Tan vest painted like a taco shell with felt toppings."}, "ramen-bowl": {"t": "Ramen Bowl", "b": "Cardboard bowl rim, noodle-yarn hair, a foam egg on top."}, "tiny-snail": {"t": "Tiny Snail", "b": "Neutral clothes plus a lightweight spiral shell from cardboard worn like a backpack."}, "little-witch": {"t": "Little Witch", "b": "Black cape, pointy hat, striped tights, green face paint."}, "spider": {"t": "Eight-Legged Spider", "b": "Black sweats with stuffed sock legs attached at the sides."}, "backyard-hero": {"t": "Backyard Superhero", "b": "Short cape plus a first initial on the chest, mask optional."}, "pickle": {"t": "Pickle", "b": "Green tunic, bumpy texture, smug grin."}, "vampire": {"t": "Classic Vampire", "b": "Black cape, fangs, slicked hair."}, "bamboo-demon": {"t": "Bamboo-Muzzle Demon", "b": "Pink robe, long dark wig, and a cardboard bamboo muzzle tied with ribbon."}, "emoji-crew": {"t": "Emoji Crew", "b": "Everyone picks an emoji: a yellow tee plus a big printed face."}, "robot-crew": {"t": "Cardboard Robot Crew", "b": "Boxy robots built from cardboard boxes, foil, and bottle-cap buttons."}, "cereal-crew": {"t": "Cereal Crew", "b": "Solid-color clothes plus a cereal-box front you decorate."}, "decades-crew": {"t": "Decades Crew", "b": "Each person picks a decade and dresses from their own closet."}, "under-the-sea": {"t": "Under the Sea", "b": "Jellyfish from an umbrella with ribbon tentacles, crab from red clothes and claw mittens, plus fish, seaweed, and waves."}, "dino-rangers": {"t": "Dino Rangers", "b": "Khaki outfits for the grown-ups, dino hoods for the kids. Leash a toy raptor."}, "board-game-pieces": {"t": "Board Game Pieces", "b": "Each person picks a piece: cardboard die, playing card, pawn, or domino over monochrome clothes."}, "rain-cloud-rainbow": {"t": "Rain Cloud and Rainbow", "b": "One wears gray with cotton clouds and paper raindrops; the other wears rainbow stripes."}, "doctor-bride": {"t": "The Doctor & the Bride", "b": "Green face paint and neck bolts for one; tall streaked wig and torn gown for the other."}, "breakfast-buffet": {"t": "Breakfast Buffet", "b": "Everyone picks a breakfast: egg, bacon, toast, pancake, OJ, coffee. Cardboard signs over normal clothes."}, "ghost-hunters": {"t": "Ghost Hunters", "b": "Khaki jumpsuits, cardboard ghost-catching backpacks, name patches."}, "haunted-animatronics": {"t": "Haunted Animatronics", "b": "Glitchy mascot heads from cardboard boxes, flickering LED eyes, jerky moves."}, "mystery-crew": {"t": "Mystery Crew", "b": "Assign the leader, the style icon, the brains, the goofball, and one very good dog."}, "headless-horsemen": {"t": "Headless Horsemen", "b": "Black capes, jack-o-lanterns held at shoulder height, group gallop."}, "haunted-portraits": {"t": "Haunted Portraits", "b": "Gray makeup, old-timey clothes, hold a gilt frame."}, "goggle-crew": {"t": "Goggle Crew", "b": "Yellow tees, denim overalls, goggles, black gloves."}, "garden-gnome": {"t": "Garden Gnome", "b": "Wear earth tones, make a pointy hat from cardboard, draw a white beard, carry a tiny fishing rod or garden shovel."}, "black-cat": {"t": "Black Cat Burglar", "b": "Black sweatsuit, cat-ear headband, eye mask. Add a toy sack for burglar."}, "block-monster": {"t": "Block Monster", "b": "Wear all one solid color, square up your silhouette with foam or cardboard blocks on shoulders/limbs, draw a pixelated face."}, "space-crewmate": {"t": "Space Crewmate", "b": "Colored sweatsuit plus a cardboard backpack."}, "sun-moon": {"t": "Sun and Moon", "b": "One in yellow with cardboard rays, one in navy with paper stars and a crescent."}, "moth-porch-light": {"t": "Moth and Porch Light", "b": "One wears neutrals with cardboard wings; the other wears yellow and carries a lampshade."}, "raptor-ranger": {"t": "Raptor & Ranger", "b": "One khaki ranger, one green dino hood. The ranger holds the leash."}, "cat-mouse": {"t": "Cat & Mouse", "b": "Cat ears versus mouse ears. Spend the night chasing each other."}, "ketchup-mustard": {"t": "Ketchup & Mustard", "b": "Red bottle tunic and cap for one, yellow for the other."}, "plumber-duo": {"t": "Plumber Duo", "b": "Overalls, red and green caps and shirts, drawn mustaches."}, "office-couple": {"t": "Office Couple", "b": "White shirts, name tags, and a teapot. The office's finest."}, "burger-joint-couple": {"t": "Burger Joint Couple", "b": "White apron plus fake mustache, curly red wig plus glasses. Burger shop owners."}, "plug-socket": {"t": "Plug and Socket", "b": "Cardboard plug and outlet worn front and back."}, "lost-tourist": {"t": "Lost Tourist", "b": "Wear wrinkled clothes, carry a crumpled map, add one luggage tag backwards on your shoulder."}, "tooth-fairy": {"t": "Tooth and Tooth Fairy", "b": "One all-white with a cardboard tooth outline; the other adds wings and an envelope of tooth money."}, "web-hero-duo": {"t": "Web Hero Duo", "b": "Red-blue sweatsuit plus web mask; partner gets the black jacket and attitude."}, "plague-doctor": {"t": "Plague Doctor", "b": "Long coat, wide hat, beaked mask."}, "crowd-camouflage": {"t": "Crowd Camouflage", "b": "Gray hoodie, dark pants, blank expression. Vanish into any crowd."}, "error-404": {"t": "Error 404", "b": "Wear all black with a blank white page taped to your chest; carry a phone with a cracked-screen prop."}, "zombie-coworker": {"t": "Zombie Coworker", "b": "Torn button-down, loosened tie, pale makeup, coffee mug."}, "the-olympians": {"t": "The Olympians", "b": "Bedsheet togas, gold rope belts, laurel crowns. Pick your god: lightning bolt, owl, or trident."}, "safari-photographer": {"t": "Safari Photographer", "b": "Khaki vest, toy camera and binoculars, plus a stuffed lion cub under one arm."}, "player-one-two": {"t": "Player One & Two", "b": "Matching tees with 1 and 2, toy controllers in hand, ready for co-op."}, "dinosaur-family": {"t": "Dinosaur Family", "b": "Matching dino-hoodie sweatsuits for the whole crew, spikes down every back."}, "snow-sisters": {"t": "Ice Kingdom Crew", "b": "The ice queen, the snow princess, the talking snowman, the reindeer: pick your role."}, "sushi-roll": {"t": "Sushi Roll", "b": "A white-sheet wrap with felt salmon and pom-pom wasabi. Chopsticks optional."}, "deviled-egg": {"t": "Deviled Egg", "b": "White shirt with a felt yolk, devil horns, and a red tail. Half egg, half devil."}, "pizza-slice": {"t": "Pizza Slice", "b": "A big cardboard triangle, painted golden with felt pepperoni."}, "popcorn-bucket": {"t": "Popcorn Bucket", "b": "A striped cardboard-box body with balloon popcorn on top."}, "ice-cream-cone": {"t": "Ice Cream Cone", "b": "A tan paper cone hat and a sprinkle-dotted scoop shirt."}, "pbj": {"t": "Peanut Butter & Jelly", "b": "One in brown with a PB label, one in purple with a J label."}, "bacon-eggs": {"t": "Bacon & Eggs", "b": "Wavy bacon stripes and a sunny-side-up egg yolk."}, "peas-pod": {"t": "Peas in a Pod", "b": "Green shirts in a row under one long felt pod sash."}, "basketball-star": {"t": "Basketball Star", "b": "Jersey, shorts, eye-black stripes, and a ball that never leaves your hand."}, "referee": {"t": "Referee", "b": "A striped shirt, a whistle, and a yellow penalty flag."}, "boxer": {"t": "Boxer", "b": "Bathrobe, toy gloves, bruise makeup, and entrance music."}, "cheerleader": {"t": "Cheerleader", "b": "Team colors and pom-poms made from cut plastic bags."}, "tennis-duo": {"t": "Tennis Duo", "b": "All-white outfits, headbands, toy rackets, and a tube of balls."}, "bowling-pins": {"t": "Bowling Pins", "b": "White outfits with red neck stripes, plus one bowler in black."}, "cardboard-knight": {"t": "Cardboard Knight", "b": "Silver-painted cardboard armor and a pool-noodle sword."}, "ninja": {"t": "Ninja", "b": "All black with a belt sash and a slit headband."}, "caped-duo": {"t": "Caped Duo", "b": "Matching sheet capes, felt masks, and your own emblems."}, "hero-squad": {"t": "Hero Squad", "b": "Color-coded capes and masks, one team pose for photos."}, "astronaut": {"t": "Astronaut", "b": "White sweats, a paper-bag helmet, and a flag patch."}, "robot-ranger": {"t": "Robot Ranger", "b": "Silver boxes, dryer-vent arms, and sticker dials."}, "penguin-huddle": {"t": "Penguin Huddle", "b": "Black shirts, felt bellies, beak headbands. Waddle together."}, "prince-princess": {"t": "Prince & Princess", "b": "A crown and cape, a thrifted gown and tiara."}, "dino-herd": {"t": "Dino Herd", "b": "Green ponchos with felt spikes and stuffed-sock tails."}, "pixel-ghost": {"t": "Pixel Ghost", "b": "A white sheet cut in chunky pixel squares with felt eyes."}, "spaghetti-meatball": {"t": "Spaghetti & Meatball", "b": "White shirt with yarn spaghetti glued on, brown pom-pom meatballs."}, "cupcake": {"t": "Cupcake", "b": "Brown tunic for the wrapper, white pillowcase for frosting, cherry on top."}, "banana": {"t": "Banana", "b": "Yellow sweatsuit with a green felt stem hat."}, "hot-dog": {"t": "Hot Dog", "b": "Tan foam pool noodle bun, red shirt for the dog, mustard squiggle."}, "donut": {"t": "Donut", "b": "Pink cardboard ring with sprinkles, worn like a sandwich board."}, "coffee-cup": {"t": "Coffee Cup", "b": "White trash bag over a cardboard tube, brown lid hat."}, "salt-pepper": {"t": "Salt & Pepper", "b": "White and black outfits with shaker tops made from cardboard."}, "fruit-salad": {"t": "Fruit Salad Crew", "b": "Each person picks a fruit color, wears it head to toe with a leaf hat."}, "wizard": {"t": "Classic Wizard", "b": "Tall black pointy hat, flowing plain black robe, tall straight wooden staff, gray beard optional."}, "toy-box-crew": {"t": "Toy Box Crew", "b": "A cowboy sheriff, a space ranger, and the rest of the toy box: pick your favorite."}, "demon-boy-band": {"t": "Demon Boy Band", "b": "Matching streetwear-idol outfits with glowing patterns for your whole boy band."}, "dragon-rider-duo": {"t": "Dragon Rider Duo", "b": "A viking rider and a cardboard dragon, ready to fly over the neighborhood."}, "numbered-players": {"t": "Numbered Players", "b": "Green tracksuits, numbered bibs, and a survival-game attitude."}, "emotion-crew": {"t": "Emotion Crew", "b": "One loud color per person: each of you is a different emotion."}, "kart-racers": {"t": "Kart Racers", "b": "Cardboard karts and racing caps for a full starting grid of friends."}, "tall-hat-crew": {"t": "Tall Hat Crew", "b": "A striped stovepipe hat, a bow tie, and two wild blue-haired Things."}, "chipmunk-trio": {"t": "Chipmunk Trio", "b": "Letter sweaters, felt ears, and whiskers for a singing trio of chipmunks."}, "galaxy-knights": {"t": "Galaxy Knights", "b": "Robes, belts, and toy energy blades for knights of a far-off galaxy."}, "plastic-dream-crew": {"t": "Plastic Dream Crew", "b": "Head-to-toe pink outfits with plastic accessories for the dream crew."}, "extinct-party-animal": {"t": "Extinct Party Animal", "b": "Felt dino spikes on a normal jacket, plus a party hat and a badge that reads Last seen 66 million years ago."}, "dino-tourist": {"t": "Dino Tourist", "b": "Hawaiian shirt, dino tail, camera around your neck, and a fanny pack. The meteor missed this one."}, "raptor-barista": {"t": "Raptor Barista", "b": "Green hoodie with a dino snout hood, tiny T. rex arms strapped on, and a coffee cup you can barely hold."}, "emotional-support-dinosaur": {"t": "Emotional Support Dinosaur", "b": "Dino-spike vest over normal clothes with a badge that says Emotional Support Dinosaur. Do not pet."}, "garden-fairy": {"t": "Garden Fairy", "b": "Tulle wings, a flower crown, and a wand: the backyard turns into a fairy tale."}, "ballerina": {"t": "Ballerina", "b": "A tulle tutu tied onto elastic, a leotard, and a neat ballerina bun."}, "butterfly": {"t": "Butterfly", "b": "Painted cardboard wings on black sweats: the garden's prettiest visitor."}, "pop-star": {"t": "Pop Star", "b": "A sparkly jacket, a toy microphone, and the biggest hair in the room."}, "ice-skater": {"t": "Ice Skater", "b": "A white dress, tights, and a perfect bun: gold-medal energy, no ice required."}, "ladybug": {"t": "Ladybug", "b": "Red sweats, black felt dots, and little spotted wings."}, "daisy": {"t": "Daisy", "b": "A yellow petal headband and a green dress: a walking flower."}, "little-baker": {"t": "Little Baker", "b": "A paper chef hat, an apron, and a toy whisk."}, "little-artist": {"t": "Little Artist", "b": "A beret, a cardboard paint palette, and a splatter-painted smock."}, "beekeeper-bee": {"t": "Beekeeper & Bee", "b": "One goes as the beekeeper in white with a mesh veil; the other wears yellow and black stripes with antennae."}, "tetris-duo": {"t": "Block Party Duo", "b": "Two interlocking tetromino shapes built from painted cardboard boxes, worn like sandwich boards."}, "little-lifeguard": {"t": "Little Lifeguard", "b": "Red tee, whistle, and a rescue buoy made from a pool noodle ring: an everyday hero costume."}, "little-prince": {"t": "Little Prince", "b": "Crown, cape, and a royal sash from the dress-up box or the craft drawer."}, "fossil-hunter": {"t": "Fossil Hunter", "b": "Khaki vest, toy brush, magnifying glass, and cardboard fossil bones in a belt pouch."}, "web-slinger-kid": {"t": "Web Hero", "b": "Red sweatsuit, tape web lines, big white eye lenses."}, "milk-cookies": {"t": "Milk & Cookies", "b": "White carton tunic for one, brown cookie with felt chips for the other."}, "chips-guac": {"t": "Chips & Guac", "b": "Green guac tunic with red tomato dots for one, giant triangle chip hat for the other."}, "sushi-soy": {"t": "Sushi & Soy Sauce", "b": "White rice tunic with orange fish sash for one, dark soy bottle for the other."}, "burger-fries": {"t": "Burger & Fries", "b": "Sesame-seed bun top for one, red fry carton with yellow fry sticks for the other."}, "donut-coffee": {"t": "Donut & Coffee", "b": "Pink frosted ring tunic for one, takeout coffee cup for the other."}, "wine-cheese": {"t": "Wine & Cheese", "b": "Burgundy wine glass tunic for one, yellow cheese wedge with holes for the other."}, "kpop-demon-huntresses": {"t": "Pop Star Demon Huntresses", "b": "Matching stage outfits, toy microphones, and demon-hunter poses for three."}, "goth-braids": {"t": "Goth Girl with Braids", "b": "Black dress, two tight braids, and a stare that ends conversations."}, "juke-joint-vampires": {"t": "Juke-Joint Vampires", "b": "Sharp vintage suits, fangs, and a trumpet one of you never puts down."}, "blue-heeler-pup": {"t": "Blue Heeler Pup", "b": "Blue-gray hoodie, felt ears, and a painted nose for the littlest pup."}, "baby-pumpkin": {"t": "Baby Pumpkin", "b": "An orange onesie, green felt leaves, and the easiest first Halloween ever."}, "pirate-captain": {"t": "Pirate Captain", "b": "Striped shirt, cardboard captain hat, and a treasure map you drew yourself."}, "cowboy-duo": {"t": "Cowboy and Cowgirl", "b": "Denim, cardboard hats, and bandanas for the pair that rides together."}, "smores-duo": {"t": "S'mores Duo", "b": "Two graham-cracker tunics with a marshmallow and chocolate candy square between you."}, "scarecrow": {"t": "Friendly Scarecrow", "b": "Plaid shirt, straw poking out, and a stitched smile."}, "yellow-henchmen": {"t": "Yellow Henchmen Crew", "b": "Yellow shirts, blue overalls, and swim goggles for the whole crew."}, "mystery-teens": {"t": "Mystery-Solving Teens", "b": "Color-coded outfits, a toy magnifying glass, and one giant sandwich."}, "pumpkin-king-bride": {"t": "Pumpkin King and Stitched Bride", "b": "Pinstripe suit and pumpkin mask for one, patchwork dress and yarn hair for the other."}, "moonwalk-star": {"t": "Moonwalking Pop Star", "b": "Red jacket, one glitter glove, and the lean everyone attempts."}, "witchy-sisters": {"t": "Witchy Sister Trio", "b": "Three color-coded witch dresses: green, purple, and orange."}, "macabre-couple": {"t": "Macabre Goth Couple", "b": "Long black gown and calm stare for one, sharp suit for the other."}, "party-pinata": {"t": "Party Pinata", "b": "A cardboard box wrapped in rainbow fringe, with real candy inside."}, "fuzzy-gremlin": {"t": "Fuzzy Gremlin Plush", "b": "A furry brown onesie, big felt ears, and googly eyes."}, "rescue-pups": {"t": "Rescue Pup Team", "b": "Color-coded pup vests and felt ears for the whole preschool crew."}, "wayfinder-princess": {"t": "Wayfinder Princess", "b": "A printed sailcloth top, grass skirt, and a cardboard hook."}, "chill-painter": {"t": "Chill Painter with Fro", "b": "A big brown afro wig, denim shirt, and a palette you painted yourself."}};

// Generic meta: the same preview map.html ships with.
var DEFAULT_OG_TITLE = "Costume Galaxy: explore all 164 costumes | Pick My Costume";
var DEFAULT_OG_DESCRIPTION = "All 164 Halloween costume ideas as an explorable galaxy \u2014 9 worlds from Dinosaur Land to Food Court. Zoom in, tap a costume, open the free DIY build guide.";
var DEFAULT_OG_IMAGE = "https://pickmycostume.com/images/og/blue-dog-family.jpg";
var DEFAULT_OG_URL = "https://pickmycostume.com/map/";

// Same esc() as /c/[slug].js: these values land inside meta content="".
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Replace the value of one meta tag, matched by tag identity (property/name
// + content attribute). If map.html's copy changes, the match still holds;
// if the tag ever disappears, this is a silent no-op (generic stays).
function setMeta(html, attr, value) {
  var re = new RegExp("<meta " + attr + ' content="[^"]*">');
  return html.replace(re, "<meta " + attr + ' content="' + value + '">');
}

export async function onRequest(context) {
  // Non-GET fetch: serve the static asset exactly as-is.
  if (context.request.method !== "GET") {
    return context.env.ASSETS.fetch(context.request);
  }
  var url;
  try {
    url = new URL(context.request.url);
  } catch (e) {
    return context.env.ASSETS.fetch(context.request);
  }

  var segs = url.pathname.split("/").filter(function(s){ return s; });
  // segs: ["map"] | ["map", region] | ["map", region, costume]
  var region = segs.length > 1 ? segs[1].toLowerCase() : "";
  var costume = segs.length > 2 ? segs[2].toLowerCase() : "";
  var rg = MAP_REGIONS[region] || null;

  var title = DEFAULT_OG_TITLE;
  var desc = DEFAULT_OG_DESCRIPTION;
  var img = DEFAULT_OG_IMAGE;
  var ogurl = DEFAULT_OG_URL;

  if (rg) {
    title = rg.name + " \u2014 Costume Galaxy | Pick My Costume";
    desc = rg.syn + " " + rg.count + " costume ideas to explore.";
    img = "https://pickmycostume.com/images/og/" + rg.img + ".jpg";
    ogurl = "https://pickmycostume.com/map/" + region;
    var idea = costume ? MAP_IDEAS[costume] : null;
    if (idea) {
      title = idea.t + " | Costume Galaxy \u2014 Pick My Costume";
      desc = idea.b;
      img = "https://pickmycostume.com/images/og/" + costume + ".jpg";
      ogurl = "https://pickmycostume.com/map/" + region + "/" + costume;
    }
    // Unknown costume id: the region meta stands.
  }
  // Unknown region (or /map itself): the generic meta stands.

  var rewritten = new URL(url);
  rewritten.pathname = "/map.html";
  var resp = await context.env.ASSETS.fetch(new Request(rewritten.toString(), context.request));
  var ctype = resp.headers.get("Content-Type") || "";
  if (!resp.ok || ctype.indexOf("text/html") === -1) return resp;
  var html = await resp.text();
  if (!html) return resp;

  html = setMeta(html, 'property="og:title"', esc(title));
  html = setMeta(html, 'name="twitter:title"', esc(title));
  html = setMeta(html, 'property="og:description"', esc(desc));
  html = setMeta(html, 'name="twitter:description"', esc(desc));
  html = setMeta(html, 'property="og:image"', img);
  html = setMeta(html, 'name="twitter:image"', img);
  html = setMeta(html, 'property="og:url"', ogurl);

  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}
