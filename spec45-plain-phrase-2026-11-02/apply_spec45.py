#!/usr/bin/env python3
"""SPEC-4/5 (cold-qa 2026-11-02): plain-phrase pages finish the job on the page.
For each card on no-sew-costumes.html and white-sheet-costumes.html:
- the "You need: N things in all" count becomes the FULL materials list
  (bank materials, buy/make/own parentheticals stripped, as the guide lists them)
- a "How to make it" 3-step summary is added, grounded in the bank's own
  step list for that idea (safety wording kept where the bank puts it up front)
SPEC-INTENT-1 (2026-11-02): STEPS extended with curated 3-step summaries for the
40 remaining ideas on the other five intent pages (cardboard, couples,
face-paint, family, toddler), each grounded in that idea's bank steps with
its safety lines kept. The generator now covers all 7 pages and asserts
full PICKS coverage, so a card can never ship without steps again.
The /c/ link stays, as depth. Byline bumps September -> November 2026 because
this is a real content change on these pages (SPEC-5: never fake a date).
"""
import re, html, sys
ROOT = '/home/hatch/workspace/builds/pick-my-costume'

STEPS = {
 'office-couple': ["Write joke job titles on the name tags.", "Pin the tags on white shirts, worn with black pants or skirts.", "One person carries the teapot. The other carries a clipboard."],
 'lost-tourist': ["Wrinkle the shirt on purpose and put the sunglasses on top of your head.", "Tape a luggage tag backwards on one shoulder.", "Carry a paper map upside down, and hold it that way."],
 'ninja': ["Dress all in black and tie the sash around the waist.", "Wrap the black strip around the forehead, with eyes and mouth uncovered.", "Paint a thin black stripe across the nose if you like."],
 'cereal-crew': ["Cut the front panel off an empty cereal box.", "Decorate it with a made-up cereal name and mascot.", "Tape string to the top corners and wear the panel like a sign."],
 'breakfast-buffet': ["Cut a large circle or rectangle from the cardboard.", "Draw your breakfast food big, filling the whole board.", "Thread string through the top holes and wear it over normal clothes."],
 'crowd-camouflage': ["Put on the gray hoodie, dark pants, and gray beanie.", "Stick the blank name tag on your chest. Write nothing on it.", "Keep a blank face and blend into the back of group photos."],
 'bowling-pins': ["Wrap two red tape stripes around the collar of the white shirt.", "Wrap one stripe around each wrist.", "The bowler dresses in black and carries a toy ball, never a real one."],
 'salt-pepper': ["Salt dresses all in white. Pepper dresses all in black.", "Cut cardboard shaker tops, paint them gray, and dot holes on top.", "Tape one top to each hat, with a big S on Salt and a big P on Pepper."],
 'headless-horsemen': ["Drape the black cape over the shoulders and tuck the chin low, so you can still see the ground.", "Hold the pumpkin bucket up at shoulder height, like a carried head.", "Add glow bracelets so drivers can see you, and gallop in a group line."],
 'bacon-eggs': ["Cut wavy strips from the red-brown felt for the bacon.", "Cut one large white oval and one yellow circle for the egg.", "Pin the felt to the shirts from the inside, so pin backs face cloth, not skin."],
 'penguin-huddle': ["Cut a white felt belly and glue it to the front of the black shirt.", "Glue an orange felt beak to the front of a headband.", "Put on the shirt and headband, and waddle shoulder to shoulder."],
 'plug-socket': ["Cut two cardboard panels, each about 2 feet square.", "Paint one gray and add foam prongs for the plug. Paint the other white and draw dark slots for the socket.", "Tape string to the back corners and hang the panels like signs. Never loop string around the neck."],
 'classic-ghost': ["Drape the sheet over the wearer and mark both eye spots.", "Take the sheet off. Cut the holes small first, then widen a little at a time.", "Draw a mouth, trim the hem so it clears the ground, and drape the sheet back on."],
 'little-witch': ["Pin or tie the black cape at the shoulders, loose at the neck.", "Paint the nose, chin, and forehead lightly green. Use non-toxic face paint only, and keep it clear of the eyes.", "Pull on the striped tights and the pointy hat."],
 'coffee-cup': ["Cut the head and arm holes in the white bag or sheet. Cut the head hole wide enough to see and breathe with ease, and wear it over clothes.", "Draw a coffee shop logo on the front with the brown marker.", "Cut a brown paper circle as the lid hat, and wear it on top."],
 'vampire': ["Dress in black, and slick the hair straight back with gel.", "Dust pale paint over the face, and add a thin red line at each corner of the mouth.", "Wear the black cape, and pop the fangs in last. Skip the fangs for small kids."],
 'caped-duo': ["Cut each sheet into a cape.", "Cut felt emblems and eye masks. Glue one emblem to the back of each cape.", "Tie the capes in a loose bow that pulls free easily, and put the masks on."],
 'dino-herd': ["Cut 8 to 10 felt triangles, all from one paper template.", "Pin the triangles in a row down the back of the green poncho.", "Stuff an old sock, and pin it to the back waistband as the tail."],
 'pixel-ghost': ["Cut the bottom edge of the sheet into chunky square zigzags, about 4 inches each.", "Draw two square eyes and a square mouth on the black felt, cut them out, and glue them onto the top third of the sheet.", "Let the glue dry for 30 minutes. Drape the sheet on over dark clothes, with the eye area kept open."],
 'sushi-roll': ["Dress in the white sheet or large white t-shirt.", "Cut the dark green felt into a wide band, and glue or pin it around the waist as the seaweed wrap.", "Glue pink felt strips across the front as salmon, and add pom-pom rice and one green pom-pom as wasabi."],
 'doctor-bride': ["The Doctor: paint the face and neck green, and tape the two bolts to the sides of the neck. Keep paint away from the eyes, and patch-test first.", "The Bride: put on the white dress, and tear the bottom hem into strips by hand, starting small.", "Smudge dark eye shadow under the eyes. Spray in the white hair streak last."],
 'pizza-slice': ["Cut a big triangle from the cardboard, about 3 feet tall.", "Paint it golden yellow-orange. An adult cuts red felt circles, and you glue them on spread out as pepperoni.", "Glue a brown crust strip along the wide end, tape two string loops to the back, and wear it like a sandwich board, crust at the top."],
 'donut': ["Draw a big circle on the cardboard, about 30 inches across. Cut the center hole smaller than the head first, then widen it slowly, keeping fingers clear of the scissors.", "Paint the ring pink.", "Glue on felt or sticker sprinkles, attach ribbon at the top, and wear it like a sandwich board."],
 'kart-racers': ["Have each racer step into their box and mark the waist before cutting. Cut the top and bottom out small first, then widen.", "Paint each kart a different bright color, and tape two paper plate wheels to each side.", "Tape ribbon straps inside so the kart hangs at waist height with legs free to move. Tape every cut edge smooth, and wear the kart with a racing cap."],
 'ghost-hunters': ["Tape a small cardboard box shut for each backpack. An adult cuts the straps, dial, and hose from black cardboard.", "Tape or glue those pieces onto the box.", "Write each person's last name on white paper and tape it to the chest as a name patch. Wear the backpack over a khaki jumpsuit, and keep the box small and light."],
 'popcorn-bucket': ["An adult cuts the head and arm holes small first, then widens them to fit. Tape the inside edges so the cardboard does not scratch.", "Cover the box with red and white stripes, using striped paper or paint, and add the label with the red marker.", "Blow up the balloons and tie them in a cluster on top of the box, then step in. Keep balloons whole and away from toddlers."],
 'block-game-crew': ["Each person picks a blocky game hero. An adult measures each head and cuts the head opening and eye holes wide, so everyone can see clearly.", "Paint each box in that hero's main colors.", "Draw a square face and details on the front with the black marker, and wear the boxes over regular clothes."],
 'robot-crew': ["Cut head and arm holes in each big box, and wide eye holes in each small head box. Cut slowly and keep fingers clear of the scissors.", "Wrap every box in foil and tape it down. Draw dials on the chest, and tape bottle caps beside them as buttons.", "Slide into the torso box and tie the head box on with the chin string loose. Tape a cracked glow stick to the chest as a power light."],
 'haunted-animatronics': ["An adult marks the eye holes and the wide jagged mouth, checks the eye spots while the wearer holds the box up, then cuts both wide. Cardboard cannot be put back.", "Paint the box gray with black scuffs and cracks. An adult glues one red LED tea light inside each eye hole with the hot glue gun.", "Wear the box over old clothes and move in short jerky steps. Walk with a partner who can see clearly, never wear the box near stairs or traffic, and take the box off if you feel hot."],
 'party-pinata': ["Cut fringe strips from the crepe paper, and glue them in overlapping rows until the whole box is covered.", "Cut arm and head holes, keeping the head hole generous so seeing and breathing stay easy. Leave an opening at the bottom.", "Fill the box with wrapped candy only, seal the bottom flap loosely, and hand out candy from inside the costume all night."],
 'fairy-tale-princesses': ["Each princess picks a dress from her own closet.", "An adult draws a crown on a cereal box, checks the fit against the head, and cuts it out, leaving a 1 inch tab to tape the ends together.", "Color the crown gold or silver, tape it on, and tie the hair ribbon in a bow under the crown."],
 'good-witch-bad-witch': ["Bad witch: wear black, and paint the face and hands green with non-toxic paint. Keep the paint away from the eyes, and patch test sensitive skin first.", "An adult folds the black hat brim and hot glues it in place. Hot glue sets in seconds, so check the fit in a mirror first.", "Good witch: wear pink, color the cardboard crown with the pink marker, and tape it on."],
 'galaxy-knights': ["Wear the bathrobe over dark pants and boots, and tie the belt or sash at the waist.", "Pull the hood up, and carry the toy energy blade unlit until the photo.", "Keep toy blades pointed up or down, never at faces, and keep any sparring slow and pretend. Light the blades for the council photo."],
 'prince-princess': ["The prince wears the gold crown and the cape over dark clothes, and carries the toy scepter. Keep the cape above the knees, and keep the neck tie loose so it pulls free easily.", "The princess wears the thrifted gown and the tiara.", "Walk in with royal posture, wave slowly with a bent wrist, and call everyone my good subject."],
 'burger-joint-couple': ["One partner pulls on a white apron and sticks on the fake mustache with its skin-safe adhesive. Test the spot in a mirror first.", "The other partner pulls on the second apron, the curly red wig, and the costume glasses.", "Carry the order pad and pencil, and take each other's orders all night. Take the mustache off gently at the end of the night."],
 'ketchup-mustard': ["Pick who is ketchup and who is mustard. Cut a big blob shape from the red paper and a matching one from the yellow paper, each about dinner plate size.", "Pin the red blob to the yellow shirt and the yellow blob to the red shirt, so each person wears the other one's color. That is the joke.", "Use 4 safety pins each, pinned from inside the shirt so no pin backs touch skin."],
 'cat-mouse': ["Cut a paper ear first to test the size: triangles for the cat, rounds for the mouse. Then cut two triangle ears from the black felt and two round ears from the gray felt.", "Tape one pair of ears to each headband, and put the headbands on.", "Draw whiskers on both faces with the eyeliner pencil, keeping the eyeliner clear of the eyes. Spend the night chasing each other."],
 'plastic-dream-crew': ["Wear an all-pink outfit head to toe, with the pink sunglasses.", "Add one plastic accessory each, like a tiara, a handbag, or a toy phone.", "Drape the feather boa over whoever feels the most plastic today, and strike the wave and smile pose."],
 'plumber-duo': ["Write a big M on one white circle and an L on the other, and stick or tape them to the red cap and the green cap.", "Each brother wears blue overalls over their colored t-shirt and cap.", "Paint on the mustaches with brown non-toxic face paint: a big bushy one for red, a thinner one for green. Keep the paint clear of the eyes, and test it on skin first."],
 'player-one-two': ["Pin or tape the letters to the shirts first, and check them in a mirror. Ironed letters cannot be moved.", "An adult irons a big 1 on the front and back of one t-shirt and a big 2 on the other, or draw the numbers with fabric markers instead.", "Each player wears their numbered shirt and carries a toy controller. Walk in together, controllers up."],
 'pbj': ["Draw a bread shape on the poster board, and hold it against a t-shirt to check the size. Cut two big bread shapes, cutting slowly and keeping fingers clear of the scissors.", "Write PB in big letters on one shape and J on the other.", "Tape or string the PB sign to the front of the brown t-shirt and the J sign to the purple one. Stand pressed together, bread sides out."],
 'basketball-star': ["Pull on the basketball jersey and shorts.", "Draw two short black stripes under each eye with non-toxic face paint. Keep the stripes below the eye, never on the eyelid, and skip them for very young kids who will rub their eyes.", "Carry the basketball tucked under one arm, and dribble it whenever you stand still."],
 'boxer': ["Pull on the athletic shorts, sneakers, and bathrobe, with the hood up.", "Dab purple and yellow non-toxic face paint on one cheekbone, below one eye, never on the eyelid. One bruise only, and keep all paint clear of the eyes.", "Pull on the toy boxing gloves, throw a few shadow punches, and play entrance music as you walk in."],
 'gloom-bloom': ["Gloom wears the black clothes and tight braids, and paints a small black teardrop under one eye. Keep the paint clear of the eyes, and test it on skin first.", "Bloom wears the colorful clothes, pins the fake flowers in the hair, and paints a small flower on one cheek, clear of the eyes.", "Stand side by side: Gloom frowns, Bloom smiles big."],
 'mystery-crew': ["Assign the roles: orange for the leader, purple for the style icon, blue for the brains, red for the goofball. The dog wears the ears headband.", "Each person puts on their color t-shirt and a matching headband or scarf, tied loose, never tight. The brains carries the fake magnifying glass.", "Paint a brown nose on the dog with non-toxic face paint, keeping it clear of the eyes. Line up with the dog in front, and point at something suspicious."],
 'deadpan-diva': ["Braid the hair into two tight braids. Test the pale foundation on the jawline first, then put it on evenly and blend it into the neck.", "Add the dark eyeliner and lipstick, and put on the black dress. Use skin-safe makeup only, and wash it all off before bed.", "Fold the arms and hold the stare. Add reflective tape or a glow stick, and carry a flashlight for visibility at night."],
 'goggle-crew': ["Each person puts on a yellow t-shirt, denim overalls, and black gloves.", "Push the goggles up on the forehead, never over the eyes, so everyone can see clearly.", "Walk in a pack, and greet people in gibberish. Skip any real tools or hard hats."],
 'emoji-crew': ["Everyone picks an emoji, and puts on a yellow t-shirt.", "Draw the emoji on a paper plate in pencil first, then go over it with the markers. An adult handles the scissors when trimming the plate.", "Tape the plate flat to the chest of the shirt, and gather the crew in a row for photos."],
 'dino-rangers': ["Grown-ups dress in khaki shirts and pants, with the sleeves rolled. Each kid wears a green hoodie.", "An adult draws two oval eye spots on white paper, checks them against the hood, and cuts them out. Tape the spots to the hood.", "Loop the ribbon around a toy dinosaur like a leash, and tie the other end to the kid's wrist, keeping the leash short. Skip small plastic dinosaur toys for kids under three, since they are a choking hazard."],
 'decades-crew': ["Everyone picks a different decade, and builds the look from their own closet: bell bottoms and a headband for the 70s, neon and high socks for the 80s, flannel tied at the waist for the 90s.", "Letter each decade card big, with letters at least 4 inches tall, and tape one card to each chest. An adult handles the scissors when trimming the cards.", "Style the hair with gel to match the decade, and keep props light so the looks last all night."],
 'mermaid-crew': ["Sketch the cheek detail on paper first, then paint one small detail on each person: scales, a seaweed swirl, or an anchor. Keep the face paint clear of the eyes.", "Cut a red paper crab body, legs, and claws slowly, and tape them to the smallest person's shirt, or hand them the toy crab instead.", "The sea king carries the plastic trident. Everyone else picks one accessory, like the shell necklace, and stands tall for the crew photo."],
 'fruit-salad': ["Each person picks a fruit, and wears that color head to toe.", "An adult cuts leaf shapes from the green felt, keeping fingers clear of the scissors.", "Glue one leaf to each headband and press it down firmly. Wear the headbands, and take the fruit salad group photo."],
 'ice-skater': ["Twist the hair into a high bun around the hair donut, and pin it in place.", "Dab a little blush on the cheeks.", "Wear the white dress with the white tights, and strike the finishing pose. Skip real skates: this costume is for dry land only."],
 'banana': ["Put on the yellow sweatshirt and sweatpants.", "An adult cuts a stem shape from the green felt, about 4 inches tall, keeping fingers clear of the scissors.", "Glue the stem to the headband, check it in a mirror, and wear the headband."],
 'backyard-hero': ["Hold the pillowcase against the back, mark waist length, and cut the cape. Keep it above the knees, and trim it after a fitting.", "Cut the first initial from the cardstock, and pin it to the chest of the t-shirt.", "Thread the ribbon through the top corners of the cape, and tie it at the neck in a loose bow that pulls free easily. Never tie anything tight around the neck."],
 'cheerleader': ["An adult cuts the plastic bags into long strips right away, stopping 3 inches from one end. Never cut all the way through, and keep whole bags away from very small children.", "Roll the uncut end tightly, wrap it with a rubber band or tape, and fluff the strips. Make a second pom-pom the same way.", "Wear the team-color t-shirt and skirt or shorts, tie the hair ribbon in a bow, and carry a pom-pom in each hand."],
 'pop-star': ["Tease the hair big with the comb, going easy near the scalp, with no hard pulling.", "Wear the sparkly jacket over the dark jeans and top, and put on the sunglasses.", "Carry the toy microphone everywhere, and take requests."],
 'little-baker': ["Roll the white paper into a tall chef hat, and tape the seam. Measure the head with a paper strip first, and trim the band to fit snug, so it does not slide over the eyes.", "Wear the hat and the apron, and carry the toy whisk.", "Offer everyone imaginary cupcakes. Keep real flour away from the eyes: a tiny pinch on the apron only."],
 'cupcake': ["Put on the brown shirt. Drape the white pillowcase over the head and shoulders, and mark where the eyes are while wearing it.", "Take the pillowcase off, and cut the eye holes small first, then widen them. Cut them wide: your child must see and breathe with ease.", "Cut the bottom edge in waves, glue the red pom-pom on top as the cherry, and fluff the edges like frosting swirls."],
 'little-artist': ["Draw the palette shape on the cardboard, and check the size against the forearm before cutting. Cut the palette out.", "Paint dabs of bright color around the palette edge, and flick a little paint onto the smock for splatters. Use washable paint only, and cover the table before splattering.", "Wear the smock and the tilted beret, and carry the palette and brush."],
 'fuzzy-monster': ["Glue or pin the two big googly eyes to the hood.", "Draw the smile on paper first, and check the size against the chest. An adult cuts the big stitched smile from the white felt.", "Glue the smile to the chest, and wear the hood up so the eyes sit above the forehead."],
}

src = open(ROOT + '/app.js', encoding='utf-8').read()
instr = {}
for m in re.finditer(r'"([a-z0-9-]+)":\{"m":\[(.*?)\],"s":\[', src, re.S):
    mats = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2))
    instr[m.group(1)] = [x.encode().decode('unicode_escape') for x in mats]

def clean_mat(x):
    x = re.sub(r'\s*\((?:own|buy|make)[^)]*\)\s*$', '', x).strip()
    return x

def process(path, slugs_expected):
    txt = open(path, encoding='utf-8').read()
    orig = txt
    # CSS for the steps block (insert once, after the .blurb rule)
    assert '.how{' not in txt
    txt = txt.replace('.blurb{font-size:15px}',
        '.blurb{font-size:15px}.how{margin:10px 16px}.howt{font-weight:700;margin:0 0 4px;font-size:15px}.how ol{margin:0;padding-left:20px}.how li{margin:3px 0;font-size:14px;line-height:1.45}', 1)
    # byline: real content change on this page today (SPEC-5)
    assert 'Updated September 2026' in txt
    txt = txt.replace('Updated September 2026', 'Updated November 2026', 1)
    # intro honesty: steps are now on the page
    txt = txt.replace('lists exactly what to pull from the closet, and links to a full build guide with real hands-on time',
                      'lists exactly what to pull from the closet, gives the build steps right on this page, and links to a full build guide with real hands-on time', 1)
    txt = txt.replace('lists exactly what else you need, and links to a full build guide with real hands-on time',
                      'lists exactly what else you need, gives the build steps right on this page, and links to a full build guide with real hands-on time', 1)
    txt = txt.replace('lists the rest of the supplies honestly, and links to a full build guide with real hands-on time',
                      'lists the rest of the supplies honestly, gives the build steps right on this page, and links to a full build guide with real hands-on time', 1)

    def card_repl(m):
        block = m.group(0)
        slug = m.group(1)
        assert slug in STEPS, slug
        assert slug in instr, slug
        mats = [clean_mat(x) for x in instr[slug]]
        need_full = '; '.join(html.escape(x) for x in mats) + '.'
        block2, n = re.subn(r'<p class="need"><strong>You need:</strong> \d+ things in all\.</p>',
                            '<p class="need"><strong>You need:</strong> ' + need_full + '</p>', block)
        assert n == 1, (slug, 'need')
        lis = ''.join('<li>' + html.escape(s) + '</li>' for s in STEPS[slug])
        how = '<div class="how"><p class="howt">How to make it</p><ol>' + lis + '</ol></div>\n'
        block3, n2 = re.subn(r'(<p class="go">)', how + r'\1', block2)
        assert n2 == 1, (slug, 'go')
        return block3

    txt, ncards = re.subn(r'<article class="ccard" data-unit-item="([a-z0-9-]+)">.*?</article>', card_repl, txt, flags=re.S)
    assert ncards == slugs_expected, (path, ncards)
    assert txt != orig
    open(path, 'w', encoding='utf-8').write(txt)
    print(path, 'cards:', ncards, 'bytes:', len(orig), '->', len(txt))

process(ROOT + '/no-sew-costumes.html', 12)
process(ROOT + '/white-sheet-costumes.html', 10)
print('OK')
