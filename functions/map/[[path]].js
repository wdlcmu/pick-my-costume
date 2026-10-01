// Per-URL server rendering for the Costume Galaxy (/map/).
// Regenerate with: python3 hidden_files/galaxy/build_map_ssr.py (emits this
// file from galaxy-data.json + the region table -- do not hand-edit the tables).
//
// map.html is a static file, so /map/ unfurls with the generic galaxy preview.
// This function serves three flavors from the one static asset:
//   GET /map/                  -> map.html untouched, 200
//   GET /map/<region>          -> map.html with per-region head (title,
//                                 description, self-referencing canonical,
//                                 og/twitter with the flagship image) and an SSR
//                                 body (h1, 80-120 word synopsis, costume photo
//                                 grid), 200
//   GET /map/<region>/<costume> -> per-costume head (title, blurb, og:image,
//                                 canonical -> /c/<slug>) and a small SSR block
//                                 (title, blurb, guide link), 200; a costume URL
//                                 under the wrong region 301s to its true region
// Unknown region slugs, unknown costume ids, and deeper paths -> 404.html, 404.
// /browse* is handled by functions/browse/[[path]].js (301 -> /map/).
// Non-GET requests pass through to ASSETS untouched.
//
// Mirrors the /party pattern: data table -> esc() -> setMeta() -> Response.
// The SSR body is swapped via the <!--MAP_SSR_PRE--> / <!--MAP_SSR_POST-->
// markers the generator writes into map.html: the region/costume block replaces
// the PRE block, the POST block (region cards + full index) is removed, and the
// canvas section between them stays put so the interactive map keeps working on
// every flavor. No /map/<region>/<costume> URL ever appears in a crawlable
// <a href>: in-map navigation uses pushState, and region/costume grids link to
// /c/<slug>.

// (tables emitted by build_map_ssr.py from galaxy-data.json + REGIONS)
var MAP_REGIONS = {"dinosaur-land": {"name": "Dinosaur Land", "keyword": "dinosaur costume ideas", "count": 10, "img": "baby-dino", "syn": "Stomp, roar, repeat. Dinosaur Land is the Jurassic corner of the Costume Galaxy, with 10 dinosaur costume ideas for every age \u2014 from a baby in soft spikes to a full T. rex built out of a cardboard box. Most of these are genuinely simple builds: paint, a box, and a grown-up with scissors get you most of the way there, and every guide says exactly what to buy versus what you probably own already. If your kid has watched the same dinosaur movie forty times, start here. The flagship Baby Dino is the crowd favorite for a reason. Every costume below links to a free step-by-step build guide with honest time and cost."}, "food-court": {"name": "Food Court", "keyword": "food costume ideas", "count": 31, "img": "pizza-slice", "syn": "Dress as dinner. The Food Court is the tastiest corner of the galaxy, with 31 food costume ideas \u2014 pizza slices, tacos, and everything in between. Food costumes are some of the easiest wins in the whole bank: a lot of them are felt, cardboard, and a headband, which means low cost and genuinely make-it-tonight builds. They are also natural group costumes \u2014 feed the whole family or the whole friend group. Every guide lists the real time and cost up front, and says what you can pull from the pantry versus what to buy. Come hungry. Every costume below links to a free step-by-step build guide."}, "princess-castle": {"name": "Princess Castle", "keyword": "princess costume ideas", "count": 13, "img": "fairy-tale-princesses", "syn": "Tiaras, fairy wings, and happily ever after. Princess Castle holds 13 princess and fairy-tale costume ideas, from classic royalty to woodland fairies. A lot of these start in the closet \u2014 a dress you own, plus a crown or wings you make \u2014 so the guides lean hard on the no-sew, use-what-you-have route. Where a buy is the honest answer, the cost says so. These are kid favorites, and most build in an afternoon. Every costume below links to a free step-by-step guide with honest time and cost, so you know before you start whether it is a tonight project or a weekend one."}, "fright-night": {"name": "Fright Night", "keyword": "scary costume ideas", "count": 18, "img": "classic-ghost", "syn": "Ghosts, ghouls, and things that go bump. Fright Night is the galaxy\u2019s spooky district, with 18 scary (and scary-cute) costume ideas \u2014 the classic ghost leads the pack. These lean on makeup, thrift-store black, and bedsheets rather than expensive props, so most come in cheap. The guides flag which ones read genuinely creepy versus just spooky-silly, so you can match the costume to the kid. Every build lists honest time and cost, including the makeup you will actually use up. Every costume below links to a free step-by-step guide."}, "hero-headquarters": {"name": "Hero Headquarters", "keyword": "superhero costume ideas", "count": 12, "img": "superhero-family", "syn": "Capes on. Time to save Halloween. Hero Headquarters is home to 12 superhero costume ideas, from solo heroes to the whole family in matching capes. Superhero builds are wonderfully pantry-friendly: a felt cape, a mask, and clothes you own do most of the work, and the guides say so. For family and group heroes, each guide notes how to scale the look across ages without it getting fiddly. Every costume below links to a free step-by-step build guide with honest time and cost \u2014 no cape required to start."}, "animal-kingdom": {"name": "Animal Kingdom", "keyword": "animal costume ideas", "count": 16, "img": "bumble-bee", "syn": "Go wild. Animal Kingdom holds 16 animal costume ideas, from a buzzing bumblebee to big jungle energy. Most of these are ears, tails, and face paint over clothes you already own \u2014 the guides call out exactly which pieces to make and which to buy. Face paint looks are flagged honestly: cute in photos, and the guide tells you how long the paint actually takes. Toddlers do especially well here \u2014 soft, warm, and nap-friendly. Every costume below links to a free step-by-step build guide with honest time and cost."}, "sports-arena": {"name": "Sports Arena", "keyword": "sports costume ideas", "count": 8, "img": "soccer-squad", "syn": "Game on. The Sports Arena is the smallest region in the galaxy, with 8 sports costume ideas for the MVPs of Halloween. These are the ultimate own-it costumes \u2014 most start with a uniform or jersey and add a few made pieces, so the cost stays low and the build stays short. The guides are upfront about which bits are worth making versus buying. Perfect for the kid who would rather wear their real gear anyway. Every costume below links to a free step-by-step guide with honest time and cost."}, "pop-culture-plaza": {"name": "Pop Culture Plaza", "keyword": "pop culture costume ideas", "count": 32, "img": "mystery-crew", "syn": "Screen legends, memes, and main characters. Pop Culture Plaza is the biggest region in the galaxy, with 32 costume ideas from the shows, movies, and games everyone is quoting. These builds mix closet staples with a few signature pieces \u2014 the guides name the one or two items that sell the character, so you do not overbuy. Because characters change fast, every guide sticks to what the costume needs, not what is hot this week. Every costume below links to a free step-by-step build guide with honest time and cost."}, "silly-street": {"name": "Silly Street", "keyword": "funny costume ideas", "count": 24, "img": "moth-porch-light", "syn": "Pure silliness, zero scares. Silly Street is where the galaxy keeps its 24 funniest costume ideas \u2014 puns, sight gags, and the inflatable-adjacent chaos kids love. Funny costumes live or die on commitment, so the guides focus on the one big gag and keep everything else simple. Most are cheap builds: cardboard, felt, and a willingness to look ridiculous. If the goal is making the neighbors laugh, start here. Every costume below links to a free step-by-step build guide with honest time and cost."}};
var MAP_IDEAS = {"neon-demon-hunter": {"t": "Neon Demon Hunter", "b": "Streetwear with glowing sigils, a foam sword, and pop-idol hair and makeup.", "r": "pop-culture-plaza"}, "classic-ghost": {"t": "Classic Ghost", "b": "A white sheet with cut-out eyes.", "r": "fright-night"}, "blue-dog-family": {"t": "Aussie Dog Family", "b": "Dog-ear headbands and blue-or-orange shirts: mama, dad, and the pups.", "r": "pop-culture-plaza"}, "superhero-family": {"t": "Superhero Family", "b": "Red sweatsuits, black eye masks, felt logo. The whole family goes super.", "r": "hero-headquarters"}, "blue-alien-ohana": {"t": "Blue Alien Ohana", "b": "A blue hoodie and an antenna headband turn the kid into the alien.", "r": "pop-culture-plaza"}, "emerald-witch": {"t": "Emerald Witch", "b": "An all-green-everything gown, dramatic makeup, and a pointy hat gone couture.", "r": "pop-culture-plaza"}, "gloom-bloom": {"t": "Gloom & Bloom", "b": "Braids and black for Gloom, color-pop and smiles for Bloom.", "r": "fright-night"}, "deadpan-diva": {"t": "Deadpan Diva", "b": "Black dress, two braids, pale makeup, and a stare that ends conversations.", "r": "fright-night"}, "safari-zoo-crew": {"t": "Safari / Zoo Crew", "b": "Everyone picks an animal: closet clothes in matching colors plus an ear headband.", "r": "animal-kingdom"}, "fairy-tale-princesses": {"t": "Fairy Tale Princesses", "b": "A dress or a crown from the closet. Every princess works.", "r": "princess-castle"}, "tin-hero": {"t": "The Tin Hero", "b": "Red and gold plus a glowing chest circle: the suit does the talking.", "r": "hero-headquarters"}, "good-witch-bad-witch": {"t": "Good Witch, Bad Witch", "b": "Green face paint and black for one, pink gown and crown for the other.", "r": "princess-castle"}, "fuzzy-monster": {"t": "Fuzzy Monster", "b": "A pastel fuzzy sweatsuit with giant googly eyes and an oversized stitched smile.", "r": "silly-street"}, "pocket-plush": {"t": "Pocket Plush Monster", "b": "A fuzzy one-piece, giant ears, a stitched smile, and an oversized collector tag.", "r": "silly-street"}, "soccer-squad": {"t": "Soccer Squad", "b": "Jerseys for the players, black for the ref, one red card.", "r": "sports-arena"}, "glow-skeleton": {"t": "Glow Skeleton", "b": "Black sweats with glow-in-the-dark bone tape, plus glow bracelets.", "r": "fright-night"}, "block-game-crew": {"t": "Block Game Crew", "b": "Cardboard-box heads: pick your blocky hero.", "r": "pop-culture-plaza"}, "web-slinger-crew": {"t": "Web Hero Crew", "b": "Red, black, and pink hoodies plus masks. Pick your spider.", "r": "hero-headquarters"}, "mermaid-crew": {"t": "Mermaid Crew", "b": "The mermaid, the prince, the sea king, the sea witch, or the crab: pick your role.", "r": "princess-castle"}, "little-pig-family": {"t": "Little Pig Family", "b": "Pink clothes and a snout headband; little brother brings the dinosaur.", "r": "pop-culture-plaza"}, "enchanted-castle-crew": {"t": "Enchanted Castle Crew", "b": "The bookish princess, the cursed prince, the talking candelabra, the talking clock, the talking teapot: pick your role.", "r": "princess-castle"}, "bumble-bee": {"t": "Bumble Bee", "b": "Black sweats with yellow tape stripes and soft felt antennae.", "r": "animal-kingdom"}, "baby-dino": {"t": "Baby Dinosaur", "b": "Green hoodie, felt spikes down the back, stuffed tail.", "r": "dinosaur-land"}, "little-lion": {"t": "Little Lion", "b": "Tan sweatsuit plus a fuzzy mane hood.", "r": "animal-kingdom"}, "tiny-firefighter": {"t": "Tiny Firefighter", "b": "Red sweats, a plastic helmet, and a toy hose.", "r": "hero-headquarters"}, "little-shark": {"t": "Little Shark", "b": "Gray hoodie with a felt fin glued on the back.", "r": "animal-kingdom"}, "walking-taco": {"t": "Walking Taco", "b": "Tan vest painted like a taco shell with felt toppings.", "r": "food-court"}, "ramen-bowl": {"t": "Ramen Bowl", "b": "Cardboard bowl rim, noodle-yarn hair, a foam egg on top.", "r": "food-court"}, "tiny-snail": {"t": "Tiny Snail", "b": "Neutral clothes plus a lightweight spiral shell from cardboard worn like a backpack.", "r": "animal-kingdom"}, "little-witch": {"t": "Little Witch", "b": "Black cape, pointy hat, striped tights, green face paint.", "r": "princess-castle"}, "spider": {"t": "Eight-Legged Spider", "b": "Black sweats with stuffed sock legs attached at the sides.", "r": "fright-night"}, "backyard-hero": {"t": "Backyard Superhero", "b": "Short cape plus a first initial on the chest, mask optional.", "r": "hero-headquarters"}, "pickle": {"t": "Pickle", "b": "Green tunic, bumpy texture, smug grin.", "r": "food-court"}, "vampire": {"t": "Classic Vampire", "b": "Black cape, fangs, slicked hair.", "r": "fright-night"}, "bamboo-demon": {"t": "Bamboo-Muzzle Demon", "b": "Pink robe, long dark wig, and a cardboard bamboo muzzle tied with ribbon.", "r": "pop-culture-plaza"}, "emoji-crew": {"t": "Emoji Crew", "b": "Everyone picks an emoji: a yellow tee plus a big printed face.", "r": "silly-street"}, "robot-crew": {"t": "Cardboard Robot Crew", "b": "Boxy robots built from cardboard boxes, foil, and bottle-cap buttons.", "r": "silly-street"}, "cereal-crew": {"t": "Cereal Crew", "b": "Solid-color clothes plus a cereal-box front you decorate.", "r": "food-court"}, "decades-crew": {"t": "Decades Crew", "b": "Each person picks a decade and dresses from their own closet.", "r": "silly-street"}, "under-the-sea": {"t": "Under the Sea", "b": "Jellyfish from an umbrella with ribbon tentacles, crab from red clothes and claw mittens, plus fish, seaweed, and waves.", "r": "animal-kingdom"}, "dino-rangers": {"t": "Dino Rangers", "b": "Khaki outfits for the grown-ups, dino hoods for the kids. Leash a toy raptor.", "r": "dinosaur-land"}, "board-game-pieces": {"t": "Board Game Pieces", "b": "Each person picks a piece: cardboard die, playing card, pawn, or domino over monochrome clothes.", "r": "pop-culture-plaza"}, "rain-cloud-rainbow": {"t": "Rain Cloud and Rainbow", "b": "One wears gray with cotton clouds and paper raindrops; the other wears rainbow stripes.", "r": "silly-street"}, "doctor-bride": {"t": "The Doctor & the Bride", "b": "Green face paint and neck bolts for one; tall streaked wig and torn gown for the other.", "r": "fright-night"}, "breakfast-buffet": {"t": "Breakfast Buffet", "b": "Everyone picks a breakfast: egg, bacon, toast, pancake, OJ, coffee. Cardboard signs over normal clothes.", "r": "food-court"}, "ghost-hunters": {"t": "Ghost Hunters", "b": "Khaki jumpsuits, cardboard ghost-catching backpacks, name patches.", "r": "pop-culture-plaza"}, "haunted-animatronics": {"t": "Haunted Animatronics", "b": "Glitchy mascot heads from cardboard boxes, flickering LED eyes, jerky moves.", "r": "fright-night"}, "mystery-crew": {"t": "Mystery Crew", "b": "Assign the leader, the style icon, the brains, the goofball, and one very good dog.", "r": "pop-culture-plaza"}, "headless-horsemen": {"t": "Headless Horsemen", "b": "Black capes, jack-o-lanterns held at shoulder height, group gallop.", "r": "fright-night"}, "haunted-portraits": {"t": "Haunted Portraits", "b": "Gray makeup, old-timey clothes, hold a gilt frame.", "r": "fright-night"}, "goggle-crew": {"t": "Goggle Crew", "b": "Yellow tees, denim overalls, goggles, black gloves.", "r": "pop-culture-plaza"}, "garden-gnome": {"t": "Garden Gnome", "b": "Wear earth tones, make a pointy hat from cardboard, draw a white beard, carry a tiny fishing rod or garden shovel.", "r": "princess-castle"}, "black-cat": {"t": "Black Cat Burglar", "b": "Black sweatsuit, cat-ear headband, eye mask. Add a toy sack for burglar.", "r": "animal-kingdom"}, "block-monster": {"t": "Block Monster", "b": "Wear all one solid color, square up your silhouette with foam or cardboard blocks on shoulders/limbs, draw a pixelated face.", "r": "pop-culture-plaza"}, "space-crewmate": {"t": "Space Crewmate", "b": "Colored sweatsuit plus a cardboard backpack.", "r": "pop-culture-plaza"}, "sun-moon": {"t": "Sun and Moon", "b": "One in yellow with cardboard rays, one in navy with paper stars and a crescent.", "r": "silly-street"}, "moth-porch-light": {"t": "Moth and Porch Light", "b": "One wears neutrals with cardboard wings; the other wears yellow and carries a lampshade.", "r": "silly-street"}, "raptor-ranger": {"t": "Raptor & Ranger", "b": "One khaki ranger, one green dino hood. The ranger holds the leash.", "r": "dinosaur-land"}, "cat-mouse": {"t": "Cat & Mouse", "b": "Cat ears versus mouse ears. Spend the night chasing each other.", "r": "animal-kingdom"}, "ketchup-mustard": {"t": "Ketchup & Mustard", "b": "Red bottle tunic and cap for one, yellow for the other.", "r": "food-court"}, "plumber-duo": {"t": "Plumber Duo", "b": "Overalls, red and green caps and shirts, drawn mustaches.", "r": "pop-culture-plaza"}, "office-couple": {"t": "Office Couple", "b": "White shirts, name tags, and a teapot. The office's finest.", "r": "pop-culture-plaza"}, "burger-joint-couple": {"t": "Burger Joint Couple", "b": "White apron plus fake mustache, curly red wig plus glasses. Burger shop owners.", "r": "food-court"}, "plug-socket": {"t": "Plug and Socket", "b": "Cardboard plug and outlet worn front and back.", "r": "silly-street"}, "lost-tourist": {"t": "Lost Tourist", "b": "Wear wrinkled clothes, carry a crumpled map, add one luggage tag backwards on your shoulder.", "r": "silly-street"}, "tooth-fairy": {"t": "Tooth and Tooth Fairy", "b": "One all-white with a cardboard tooth outline; the other adds wings and an envelope of tooth money.", "r": "princess-castle"}, "web-hero-duo": {"t": "Web Hero Duo", "b": "Red-blue sweatsuit plus web mask; partner gets the black jacket and attitude.", "r": "hero-headquarters"}, "plague-doctor": {"t": "Plague Doctor", "b": "Long coat, wide hat, beaked mask.", "r": "fright-night"}, "crowd-camouflage": {"t": "Crowd Camouflage", "b": "Gray hoodie, dark pants, blank expression. Vanish into any crowd.", "r": "silly-street"}, "error-404": {"t": "Error 404", "b": "Wear all black with a blank white page taped to your chest; carry a phone with a cracked-screen prop.", "r": "silly-street"}, "zombie-coworker": {"t": "Zombie Coworker", "b": "Torn button-down, loosened tie, pale makeup, coffee mug.", "r": "fright-night"}, "the-olympians": {"t": "The Olympians", "b": "Bedsheet togas, gold rope belts, laurel crowns. Pick your god: lightning bolt, owl, or trident.", "r": "hero-headquarters"}, "safari-photographer": {"t": "Safari Photographer", "b": "Khaki vest, toy camera and binoculars, plus a stuffed lion cub under one arm.", "r": "animal-kingdom"}, "player-one-two": {"t": "Player One & Two", "b": "Matching tees with 1 and 2, toy controllers in hand, ready for co-op.", "r": "pop-culture-plaza"}, "dinosaur-family": {"t": "Dinosaur Family", "b": "Matching dino-hoodie sweatsuits for the whole crew, spikes down every back.", "r": "dinosaur-land"}, "snow-sisters": {"t": "Ice Kingdom Crew", "b": "The ice queen, the snow princess, the talking snowman, the reindeer: pick your role.", "r": "princess-castle"}, "sushi-roll": {"t": "Sushi Roll", "b": "A white-sheet wrap with felt salmon and pom-pom wasabi. Chopsticks optional.", "r": "food-court"}, "deviled-egg": {"t": "Deviled Egg", "b": "White shirt with a felt yolk, devil horns, and a red tail. Half egg, half devil.", "r": "food-court"}, "pizza-slice": {"t": "Pizza Slice", "b": "A big cardboard triangle, painted golden with felt pepperoni.", "r": "food-court"}, "popcorn-bucket": {"t": "Popcorn Bucket", "b": "A striped cardboard-box body with balloon popcorn on top.", "r": "food-court"}, "ice-cream-cone": {"t": "Ice Cream Cone", "b": "A tan paper cone hat and a sprinkle-dotted scoop shirt.", "r": "food-court"}, "pbj": {"t": "Peanut Butter & Jelly", "b": "One in brown with a PB label, one in purple with a J label.", "r": "food-court"}, "bacon-eggs": {"t": "Bacon & Eggs", "b": "Wavy bacon stripes and a sunny-side-up egg yolk.", "r": "food-court"}, "peas-pod": {"t": "Peas in a Pod", "b": "Green shirts in a row under one long felt pod sash.", "r": "food-court"}, "basketball-star": {"t": "Basketball Star", "b": "Jersey, shorts, eye-black stripes, and a ball that never leaves your hand.", "r": "sports-arena"}, "referee": {"t": "Referee", "b": "A striped shirt, a whistle, and a yellow penalty flag.", "r": "sports-arena"}, "boxer": {"t": "Boxer", "b": "Bathrobe, toy gloves, bruise makeup, and entrance music.", "r": "sports-arena"}, "cheerleader": {"t": "Cheerleader", "b": "Team colors and pom-poms made from cut plastic bags.", "r": "sports-arena"}, "tennis-duo": {"t": "Tennis Duo", "b": "All-white outfits, headbands, toy rackets, and a tube of balls.", "r": "sports-arena"}, "bowling-pins": {"t": "Bowling Pins", "b": "White outfits with red neck stripes, plus one bowler in black.", "r": "sports-arena"}, "cardboard-knight": {"t": "Cardboard Knight", "b": "Silver-painted cardboard armor and a pool-noodle sword.", "r": "hero-headquarters"}, "ninja": {"t": "Ninja", "b": "All black with a belt sash and a slit headband.", "r": "fright-night"}, "caped-duo": {"t": "Caped Duo", "b": "Matching sheet capes, felt masks, and your own emblems.", "r": "hero-headquarters"}, "hero-squad": {"t": "Hero Squad", "b": "Color-coded capes and masks, one team pose for photos.", "r": "hero-headquarters"}, "astronaut": {"t": "Astronaut", "b": "White sweats, a paper-bag helmet, and a flag patch.", "r": "silly-street"}, "robot-ranger": {"t": "Robot Ranger", "b": "Silver boxes, dryer-vent arms, and sticker dials.", "r": "silly-street"}, "penguin-huddle": {"t": "Penguin Huddle", "b": "Black shirts, felt bellies, beak headbands. Waddle together.", "r": "animal-kingdom"}, "prince-princess": {"t": "Prince & Princess", "b": "A crown and cape, a thrifted gown and tiara.", "r": "princess-castle"}, "dino-herd": {"t": "Dino Herd", "b": "Green ponchos with felt spikes and stuffed-sock tails.", "r": "dinosaur-land"}, "pixel-ghost": {"t": "Pixel Ghost", "b": "A white sheet cut in chunky pixel squares with felt eyes.", "r": "fright-night"}, "spaghetti-meatball": {"t": "Spaghetti & Meatball", "b": "White shirt with yarn spaghetti glued on, brown pom-pom meatballs.", "r": "food-court"}, "cupcake": {"t": "Cupcake", "b": "Brown tunic for the wrapper, white pillowcase for frosting, cherry on top.", "r": "food-court"}, "banana": {"t": "Banana", "b": "Yellow sweatsuit with a green felt stem hat.", "r": "food-court"}, "hot-dog": {"t": "Hot Dog", "b": "Tan foam pool noodle bun, red shirt for the dog, mustard squiggle.", "r": "food-court"}, "donut": {"t": "Donut", "b": "Pink cardboard ring with sprinkles, worn like a sandwich board.", "r": "food-court"}, "coffee-cup": {"t": "Coffee Cup", "b": "White trash bag over a cardboard tube, brown lid hat.", "r": "food-court"}, "salt-pepper": {"t": "Salt & Pepper", "b": "White and black outfits with shaker tops made from cardboard.", "r": "food-court"}, "fruit-salad": {"t": "Fruit Salad Crew", "b": "Each person picks a fruit color, wears it head to toe with a leaf hat.", "r": "food-court"}, "wizard": {"t": "Classic Wizard", "b": "Tall black pointy hat, flowing plain black robe, tall straight wooden staff, gray beard optional.", "r": "fright-night"}, "toy-box-crew": {"t": "Toy Box Crew", "b": "A cowboy sheriff, a space ranger, and the rest of the toy box: pick your favorite.", "r": "pop-culture-plaza"}, "demon-boy-band": {"t": "Demon Boy Band", "b": "Matching streetwear-idol outfits with glowing patterns for your whole boy band.", "r": "pop-culture-plaza"}, "dragon-rider-duo": {"t": "Dragon Rider Duo", "b": "A viking rider and a cardboard dragon, ready to fly over the neighborhood.", "r": "pop-culture-plaza"}, "numbered-players": {"t": "Numbered Players", "b": "Green tracksuits, numbered bibs, and a survival-game attitude.", "r": "pop-culture-plaza"}, "emotion-crew": {"t": "Emotion Crew", "b": "One loud color per person: each of you is a different emotion.", "r": "pop-culture-plaza"}, "kart-racers": {"t": "Kart Racers", "b": "Cardboard karts and racing caps for a full starting grid of friends.", "r": "pop-culture-plaza"}, "tall-hat-crew": {"t": "Tall Hat Crew", "b": "A striped stovepipe hat, a bow tie, and two wild blue-haired Things.", "r": "pop-culture-plaza"}, "chipmunk-trio": {"t": "Chipmunk Trio", "b": "Letter sweaters, felt ears, and whiskers for a singing trio of chipmunks.", "r": "pop-culture-plaza"}, "galaxy-knights": {"t": "Galaxy Knights", "b": "Robes, belts, and toy energy blades for knights of a far-off galaxy.", "r": "pop-culture-plaza"}, "plastic-dream-crew": {"t": "Plastic Dream Crew", "b": "Head-to-toe pink outfits with plastic accessories for the dream crew.", "r": "pop-culture-plaza"}, "extinct-party-animal": {"t": "Extinct Party Animal", "b": "Felt dino spikes on a normal jacket, plus a party hat and a badge that reads Last seen 66 million years ago.", "r": "dinosaur-land"}, "dino-tourist": {"t": "Dino Tourist", "b": "Hawaiian shirt, dino tail, camera around your neck, and a fanny pack. The meteor missed this one.", "r": "dinosaur-land"}, "raptor-barista": {"t": "Raptor Barista", "b": "Green hoodie with a dino snout hood, tiny T. rex arms strapped on, and a coffee cup you can barely hold.", "r": "dinosaur-land"}, "emotional-support-dinosaur": {"t": "Emotional Support Dinosaur", "b": "Dino-spike vest over normal clothes with a badge that says Emotional Support Dinosaur. Do not pet.", "r": "dinosaur-land"}, "garden-fairy": {"t": "Garden Fairy", "b": "Tulle wings, a flower crown, and a wand: the backyard turns into a fairy tale.", "r": "princess-castle"}, "ballerina": {"t": "Ballerina", "b": "A tulle tutu tied onto elastic, a leotard, and a neat ballerina bun.", "r": "princess-castle"}, "butterfly": {"t": "Butterfly", "b": "Painted cardboard wings on black sweats: the garden's prettiest visitor.", "r": "animal-kingdom"}, "pop-star": {"t": "Pop Star", "b": "A sparkly jacket, a toy microphone, and the biggest hair in the room.", "r": "silly-street"}, "ice-skater": {"t": "Ice Skater", "b": "A white dress, tights, and a perfect bun: gold-medal energy, no ice required.", "r": "sports-arena"}, "ladybug": {"t": "Ladybug", "b": "Red sweats, black felt dots, and little spotted wings.", "r": "animal-kingdom"}, "daisy": {"t": "Daisy", "b": "A yellow petal headband and a green dress: a walking flower.", "r": "silly-street"}, "little-baker": {"t": "Little Baker", "b": "A paper chef hat, an apron, and a toy whisk.", "r": "food-court"}, "little-artist": {"t": "Little Artist", "b": "A beret, a cardboard paint palette, and a splatter-painted smock.", "r": "silly-street"}, "beekeeper-bee": {"t": "Beekeeper & Bee", "b": "One goes as the beekeeper in white with a mesh veil; the other wears yellow and black stripes with antennae.", "r": "animal-kingdom"}, "tetris-duo": {"t": "Block Party Duo", "b": "Two interlocking tetromino shapes built from painted cardboard boxes, worn like sandwich boards.", "r": "pop-culture-plaza"}, "little-lifeguard": {"t": "Little Lifeguard", "b": "Red tee, whistle, and a rescue buoy made from a pool noodle ring: an everyday hero costume.", "r": "hero-headquarters"}, "little-prince": {"t": "Little Prince", "b": "Crown, cape, and a royal sash from the dress-up box or the craft drawer.", "r": "princess-castle"}, "fossil-hunter": {"t": "Fossil Hunter", "b": "Khaki vest, toy brush, magnifying glass, and cardboard fossil bones in a belt pouch.", "r": "dinosaur-land"}, "web-slinger-kid": {"t": "Web Hero", "b": "Red sweatsuit, tape web lines, big white eye lenses.", "r": "hero-headquarters"}, "milk-cookies": {"t": "Milk & Cookies", "b": "White carton tunic for one, brown cookie with felt chips for the other.", "r": "food-court"}, "chips-guac": {"t": "Chips & Guac", "b": "Green guac tunic with red tomato dots for one, giant triangle chip hat for the other.", "r": "food-court"}, "sushi-soy": {"t": "Sushi & Soy Sauce", "b": "White rice tunic with orange fish sash for one, dark soy bottle for the other.", "r": "food-court"}, "burger-fries": {"t": "Burger & Fries", "b": "Sesame-seed bun top for one, red fry carton with yellow fry sticks for the other.", "r": "food-court"}, "donut-coffee": {"t": "Donut & Coffee", "b": "Pink frosted ring tunic for one, takeout coffee cup for the other.", "r": "food-court"}, "wine-cheese": {"t": "Wine & Cheese", "b": "Burgundy wine glass tunic for one, yellow cheese wedge with holes for the other.", "r": "food-court"}, "kpop-demon-huntresses": {"t": "Pop Star Demon Huntresses", "b": "Matching stage outfits, toy microphones, and demon-hunter poses for three.", "r": "pop-culture-plaza"}, "goth-braids": {"t": "Goth Girl with Braids", "b": "Black dress, two tight braids, and a stare that ends conversations.", "r": "fright-night"}, "juke-joint-vampires": {"t": "Juke-Joint Vampires", "b": "Sharp vintage suits, fangs, and a trumpet one of you never puts down.", "r": "fright-night"}, "blue-heeler-pup": {"t": "Blue Heeler Pup", "b": "Blue-gray hoodie, felt ears, and a painted nose for the littlest pup.", "r": "animal-kingdom"}, "baby-pumpkin": {"t": "Baby Pumpkin", "b": "An orange onesie, green felt leaves, and the easiest first Halloween ever.", "r": "silly-street"}, "pirate-captain": {"t": "Pirate Captain", "b": "Striped shirt, cardboard captain hat, and a treasure map you drew yourself.", "r": "silly-street"}, "cowboy-duo": {"t": "Cowboy and Cowgirl", "b": "Denim, cardboard hats, and bandanas for the pair that rides together.", "r": "silly-street"}, "smores-duo": {"t": "S'mores Duo", "b": "Two graham-cracker tunics with a marshmallow and chocolate candy square between you.", "r": "food-court"}, "scarecrow": {"t": "Friendly Scarecrow", "b": "Plaid shirt, straw poking out, and a stitched smile.", "r": "animal-kingdom"}, "yellow-henchmen": {"t": "Yellow Henchmen Crew", "b": "Yellow shirts, blue overalls, and swim goggles for the whole crew.", "r": "pop-culture-plaza"}, "mystery-teens": {"t": "Mystery-Solving Teens", "b": "Color-coded outfits, a toy magnifying glass, and one giant sandwich.", "r": "pop-culture-plaza"}, "pumpkin-king-bride": {"t": "Pumpkin Groom and Patchwork Bride", "b": "Pinstripe suit and pumpkin mask for one, patchwork dress and yarn hair for the other.", "r": "pop-culture-plaza"}, "moonwalk-star": {"t": "Moonwalking Pop Star", "b": "Red jacket, one glitter glove, and the lean everyone attempts.", "r": "silly-street"}, "witchy-sisters": {"t": "Witchy Sister Trio", "b": "Three color-coded witch dresses: green, purple, and orange.", "r": "pop-culture-plaza"}, "macabre-couple": {"t": "Macabre Goth Couple", "b": "Long black gown and calm stare for one, sharp suit for the other.", "r": "fright-night"}, "party-pinata": {"t": "Party Pinata", "b": "A cardboard box wrapped in rainbow fringe, with real candy inside.", "r": "silly-street"}, "fuzzy-gremlin": {"t": "Fuzzy Gremlin Plush", "b": "A furry brown onesie, big felt ears, and googly eyes.", "r": "silly-street"}, "rescue-pups": {"t": "Rescue Pup Team", "b": "Color-coded pup vests and felt ears for the whole preschool crew.", "r": "animal-kingdom"}, "wayfinder-princess": {"t": "Wayfinder Princess", "b": "A printed sailcloth top, grass skirt, and a cardboard hook.", "r": "princess-castle"}, "chill-painter": {"t": "Chill Painter with Fro", "b": "A big brown afro wig, denim shirt, and a palette you painted yourself.", "r": "silly-street"}};

// Same esc() as /party: these values land inside meta content="".
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Same setMeta() as /party: replace one meta tag by tag identity (property/name
// + content attribute, content LAST). Silent no-op if the tag disappears.
function setMeta(html, attr, value) {
  var re = new RegExp("<meta " + attr + ' content="[^"]*">');
  return html.replace(re, "<meta " + attr + ' content="' + value + '">');
}

function setTitle(html, title) {
  return html.replace(/<title>[^<]*<\/title>/, "<title>" + title + "</title>");
}

function setCanonical(html, href) {
  return html.replace(/<link rel="canonical" href="[^"]*">/,
                      '<link rel="canonical" href="' + href + '">');
}

// SSR body for /map/<region>: h1, synopsis, photo grid (links go to /c/<slug>).
function regionBody(rg, slug) {
  var h = '<div class="page-head"><p class="kicker">Pick My Costume</p>' +
    "<h1>" + esc(rg.name) + "</h1>" +
    '<p class="lede">' + esc(rg.syn) + "</p></div>" +
    '<section id="regiongrid" aria-label="' + esc(rg.name) + ' costumes">' +
    '<div class="costume-grid">';
  for (var id in MAP_IDEAS) {
    var it = MAP_IDEAS[id];
    if (it.r !== slug) continue;
    h += '<a href="/c/' + id + '"><img src="/photos/' + id + '.webp" alt="' +
      esc(it.t) + '" loading="lazy"><span>' + esc(it.t) + "</span></a>";
  }
  h += "</div></section>";
  return h;
}

// SSR body for /map/<region>/<costume>: title, blurb, link to the real guide.
function costumeBody(it, id) {
  return '<div class="page-head"><p class="kicker">Pick My Costume</p>' +
    "<h1>" + esc(it.t) + "</h1>" +
    '<p class="lede">' + esc(it.b) + "</p>" +
    '<p><a class="guide" href="/c/' + id + '">Open the full build guide &rarr;</a></p></div>';
}

function swapBody(html, preBlock) {
  html = html.replace(/<!--MAP_SSR_PRE-->[\s\S]*?<!--MAP_SSR_PRE_END-->/,
                      "<!--MAP_SSR_PRE-->" + preBlock + "<!--MAP_SSR_PRE_END-->");
  html = html.replace(/<!--MAP_SSR_POST-->[\s\S]*?<!--MAP_SSR_POST_END-->/, "");
  return html;
}

async function fetchMapHtml(context, url) {
  // Rewrite to the static asset, preserving the query string (?probe= etc.).
  var rewritten = new URL(url);
  rewritten.pathname = "/map.html";
  return context.env.ASSETS.fetch(new Request(rewritten.toString(), context.request));
}

async function serve404(context, url) {
  var u = new URL("/404.html", url.origin);
  var resp = await context.env.ASSETS.fetch(new Request(u.toString(), context.request));
  var body = await resp.text();
  return new Response(body || "Not found", {
    status: 404,
    headers: { "Content-Type": "text/html;charset=utf-8", "Cache-Control": "no-store" }
  });
}

function htmlResponse(html) {
  return new Response(html, {
    headers: {
      "Content-Type": "text/html;charset=utf-8",
      "Cache-Control": "public, max-age=3600"
    }
  });
}

export async function onRequest(context) {
  // Non-GET: serve the static asset exactly as-is.
  if (context.request.method !== "GET") {
    return context.env.ASSETS.fetch(context.request);
  }
  var url;
  try {
    url = new URL(context.request.url);
  } catch (e) {
    return context.env.ASSETS.fetch(context.request);
  }

  var segs = url.pathname.split("/").filter(function (s) { return s; });
  // ["map"] | ["map", region] | ["map", region, costume]; trailing slashes stripped
  if (segs.length === 0 || segs[0] !== "map") {
    return context.env.ASSETS.fetch(context.request);
  }
  if (segs.length === 1) {
    // GET /map/ -> the static asset, untouched, 200.
    return fetchMapHtml(context, url);
  }

  var region = segs[1].toLowerCase();
  var rg = MAP_REGIONS[region] || null;
  if (!rg) return serve404(context, url);   // unknown region slug

  var resp = await fetchMapHtml(context, url);
  var ctype = resp.headers.get("Content-Type") || "";
  if (!resp.ok || ctype.indexOf("text/html") === -1) return resp;
  var html = await resp.text();
  if (!html) return resp;

  if (segs.length === 2) {
    // GET /map/<region> -> per-region head + SSR body, 200.
    var title = rg.name + ": " + rg.keyword + " | Pick My Costume";
    var canon = "https://pickmycostume.com/map/" + region;
    var img = "https://pickmycostume.com/images/og/" + rg.img + ".jpg";
    html = setTitle(html, esc(title));
    html = setMeta(html, 'name="description"', esc(rg.syn));
    html = setCanonical(html, canon);
    html = setMeta(html, 'property="og:title"', esc(title));
    html = setMeta(html, 'property="og:description"', esc(rg.syn));
    html = setMeta(html, 'property="og:image"', img);
    html = setMeta(html, 'property="og:url"', canon);
    html = setMeta(html, 'name="twitter:title"', esc(title));
    html = setMeta(html, 'name="twitter:description"', esc(rg.syn));
    html = setMeta(html, 'name="twitter:image"', img);
    html = swapBody(html, regionBody(rg, region));
    return htmlResponse(html);
  }

  if (segs.length === 3) {
    // GET /map/<region>/<costume> -> per-costume head + SSR block, 200.
    var cid = segs[2].toLowerCase();
    var it = MAP_IDEAS[cid] || null;
    if (!it) return serve404(context, url);   // unknown costume id
    if (it.r !== region) {
      // Wrong region for this costume: single 301 to its true region.
      return Response.redirect(url.origin + "/map/" + it.r + "/" + cid + url.search, 301);
    }
    var ctitle = it.t + " | Costume Galaxy \u2014 Pick My Costume";
    var curl = "https://pickmycostume.com/map/" + region + "/" + cid;
    var cimg = "https://pickmycostume.com/images/og/" + cid + ".jpg";
    html = setTitle(html, esc(ctitle));
    html = setMeta(html, 'name="description"', esc(it.b));
    // These views canonicalize to the real guide (REQUIRED).
    html = setCanonical(html, "https://pickmycostume.com/c/" + cid);
    html = setMeta(html, 'property="og:title"', esc(ctitle));
    html = setMeta(html, 'property="og:description"', esc(it.b));
    html = setMeta(html, 'property="og:image"', cimg);
    html = setMeta(html, 'property="og:url"', curl);
    html = setMeta(html, 'name="twitter:title"', esc(ctitle));
    html = setMeta(html, 'name="twitter:description"', esc(it.b));
    html = setMeta(html, 'name="twitter:image"', cimg);
    html = swapBody(html, costumeBody(it, cid));
    return htmlResponse(html);
  }

  return serve404(context, url);   // deeper paths
}
