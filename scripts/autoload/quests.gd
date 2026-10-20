extends Node
## Quests: progress lives in GameState.quest_flags ("quest:<id>" -> stage) so it
## resets with a new game. NPCs ask dialogue_for()/marker_for() and report
## talked_to(); clue objects report inspect(). Each quest's flow is a small
## function here; add new quests the same way.

signal quest_changed(id: StringName, stage: int)

const NOT_STARTED := -1
const DONE := 99

const TITLES := {
	&"unmarked_cargo": "The Unmarked Cargo",
	&"trees_remember": "What the Trees Remember",
	&"wens_boat": "A Boat for Wen",
	&"stones_remember": "Stones That Remember",
	&"merchants_ledger": "The Merchant's Ledger",
	&"light_on_water": "The Light on the Water",
	&"millstream": "What the Millstream Carries",
	&"glowcaps": "Glowcaps for the Fever",
	&"over_the_top": "The Three Who Went Over",
	&"beneath_dunes": "Beneath the Dunes",
	&"foremans_names": "The Foreman's Names",
	&"audience_throne": "An Audience Before the Throne",
	&"smugglers_route": "The Smuggler's Route",
	&"old_reef": "The Old Reef",
}
## Who gave each quest, and what it came to, for the journal.
const GIVERS := {
	&"unmarked_cargo": "Bram, Kalmora", &"trees_remember": "Pell, Sorenda", &"wens_boat": "Wen, Kalmora",
	&"stones_remember": "Aldous, Verdana", &"merchants_ledger": "Mirren, Frisalle",
	&"light_on_water": "Sparkle, Seabright Quay", &"millstream": "Oda, Verdana", &"glowcaps": "Juniper, Sorenda",
	&"over_the_top": "Sven, Frisalle",
	&"beneath_dunes": "Rafi, Duskara", &"foremans_names": "Hesper, Duskara",
	&"audience_throne": "Freya, Vetrassa",
	&"smugglers_route": "Nessa, Halmeer",
	&"old_reef": "Sparkle, Seabright Quay",
}
const ABOUT := {
	&"unmarked_cargo": "Sand-caked crates with no marks, a child's glove, a ledger page: Bram knows whose cargo it is and won't say it aloud.",
	&"trees_remember": "A laborer's satchel in the Hollow's moss. Whoever carried it was running, and young.",
	&"wens_boat": "A sail, oars and rope, and Wen's little boat is back on the water.",
	&"stones_remember": "The three standing stones tell the same story: every king paid for the crown the same way.",
	&"merchants_ledger": "Forty carts a winter through an ice road, weighed at night under the factors' second seal, for 'D.'",
	&"light_on_water": "A light on the water after dark, and Bungalow 3 answering it. The Duke's men guard that door.",
	&"millstream": "Red wool, a scrap of paper and a carved bird: Oda's grandson went north by the water.",
	&"glowcaps": "Blue glowcaps from the Hollow, and Harl's daughter is sitting up and eating.",
	&"over_the_top": "A frozen camp and new boards on an old mine. Small boots. The climbers didn't all freeze.",
	&"beneath_dunes": "Down the North Shaft for Ada, out the escape line's crawl, and into Zahra's caravan, walking north.",
	&"foremans_names": "The foreman's ledger of names: two years of children down the shaft, and very few up. Corin of Verdana among them.",
	&"audience_throne": "The Throne Ledger, in the King's own hand: every king since the first has signed for the seam. The Captain of the Guard has been waiting for someone to read it.",
	&"smugglers_route": "The dark nights at Halmeer: cards uncut from the North Shaft, over the mountain and down the coast, out of a sea cave under the cape by barge. Nessa's light is lit again.",
	&"old_reef": "Down at the old reef off Seabright, crates chained for the mainland ship. The newest carry no pick: they carry the crown. Sparkle knows her uncle's seal.",
}
## Frisalle (Sven, after his welcome gift): three climbers went over the top of the
## range when the pass came down; find what became of them (the frozen camp and the
## old adit in the Starfall Range).
## Duskara (Rafi, after his tonic): down the North Shaft for Ada, a sick child, and
## out the escape line's crawl to Zahra's caravan at the Sunwell. She follows you
## (Npc.follow_player) in the mine and the dunes; she won't go up the shaft.
## Halmeer (Nessa, at the cape light): the Company pays her to keep the light dark on
## moonless nights. Read the tide board on the quay, the salt house door and the
## barge's log in the sea cave under the cape, then tell her.
const SMUGGLER_CLUES := {
	"The tide board": "res://scenes/world/halmeer.tscn",
	"The salt house door": "res://scenes/world/halmeer.tscn",
	"The barge's log": "res://scenes/world/interiors/halmeer_cave.tscn",
}
## Seabright (Sparkle, after The Light on the Water and The Smuggler's Route): dive
## with her off the end of the diving pier after dark, to the old reef where the
## barge lets its crates down; tell her what was on them.
const REEF_DIVE := "The end of the diving pier"
const REEF_REWARD_GOLD := 80
const REEF_REWARD_CARD := &"seafoam_charm"
const SMUGGLER_REWARD_GOLD := 60
const SMUGGLER_REWARD_CARD := &"keepers_lamp"
## Vetrassa (Freya, once you've seen enough: two of the quests that follow the
## carts): read the Throne Ledger by the empty throne, and tell her. Done, it opens
## the ending that closes the North Shaft (Ending.choices).
const THRONE_LEDGER := "The Throne Ledger"
const AUDIENCE_NEEDS: Array[StringName] = [&"merchants_ledger", &"light_on_water", &"foremans_names", &"smugglers_route"]
const AUDIENCE_REWARD_GOLD := 100
const ADA_REWARD_GOLD := 80
const ADA_REWARD_CARD := &"green_lamp"
const ESCORT_ZONES: Array[String] = ["res://scenes/world/duskara_mine.tscn", "res://scenes/world/siroth_dunes.tscn"]
## Duskara (Hesper, after her welcome gift): the foreman's ledger of names, read in
## the mine's lower office.
const NAMES_LEDGER := "The ledger of names"
const NAMES_REWARD_GOLD := 70
const CLIMBER_CLUES: Array[String] = ["A frozen camp", "An old adit"]
const CLIMBERS_REWARD_GOLD := 50
## Sorenda (Juniper, after her tonic): three clumps of glowcaps in the Hollow, one in
## the grotto, one by the pool past the bear's den, one in the alcove.
const GLOWCAPS: Array[String] = ["Glowcaps by the grotto wall", "Glowcaps by the still pool", "Glowcaps in the alcove"]
const GLOWCAPS_REWARD_GOLD := 40
## Seabright (Sparkle, after her dare): watch the sea from the lookout after dark,
## then the bungalow the light answers from (Readables with night_lines).
const LIGHT_LOOKOUT := "A lookout on the headland"
const LIGHT_DOOR := "A bungalow door"
const LIGHT_REWARD_GOLD := 50
## Verdana (Oda, after her news from Lake Serin): three things caught in the reeds
## along the millstream (Readables with these titles).
const MILLSTREAM_FINDS: Array[String] = ["A snag of red wool", "A scrap of paper in the reeds", "A little carved bird"]
const MILLSTREAM_REWARD_GOLD := 45
## Kalmora: Wen is building a boat to fetch her papa home from the Duskara work.
const BOAT_PARTS: Array[StringName] = [&"boat_sail", &"boat_oars", &"boat_rope"]
const BOAT_REWARD_GOLD := 35
## Sorenda: Pell found a child's boot near the Hollow; what's in there is the proof.
const SATCHEL_TITLE := "A satchel in the moss"
const TREES_REWARD_GOLD := 50
## Elder Moss's own card, for bringing the child's things home.
const TREES_REWARD_CARD := &"sorenda_star_map"
## Verdana: Aldous wants eyes on the three standing stones (Readables with these titles).
const STONES := {
	"The Aurewind circle": "res://scenes/world/aurewind_plains.tscn",
	"The stone on Stone Point": "res://scenes/world/lake_serin.tscn",
	"The Starfall stone": "res://scenes/world/starfall_range.tscn",
}
const STONES_REWARD_GOLD := 60
const STONES_REWARD_CARD := &"stonesong_charm"
## Frisalle: Mirren the clerk wants three records read (Readables with these titles).
const LEDGER_CLUES := {
	"The weigh house tally board": "res://scenes/world/frisalle.tscn",
	"The great ledger": "res://scenes/world/interiors/frisalle_counting.tscn",
	"A letter in the desk drawer": "res://scenes/world/interiors/frisalle_weighmaster.tscn",
}
const LEDGER_REWARD_GOLD := 60
const LEDGER_REWARD_CARD := &"factors_seal"
## One resident in each town gives you that town's first return card, free, the
## first time you talk to them (after that they're 150 gold at the town's shop).
## Residents with no favour or quest of their own, so nothing else is waiting.
const WELCOME_GIFTS := {
	&"jobelle": &"kalmora_return",
	&"mate": &"sorenda_return",
	&"tally": &"verdana_return",
	&"fennick": &"seabright_return",
	&"sven": &"frisalle_return",
	&"hesper": &"duskara_return",
	&"brigid": &"vetrassa_return",
	&"maudie": &"halmeer_return",
}
const WELCOME_LINES := {
	&"jobelle": [
		"Oh, love, before you go off racing: here. A Kalmora Return. Sable charges the earth for them; I keep one by for every guest who looks like they'll get lost.",
		"Use it from your binder and you'll be back by our fountain before you can blink. Promise me you'll come home if it gets bad out there.",
	],
	&"mate": [
		"Here. Don't make a thing of it. A Sorenda Return. The forest eats racers, and I'm not having one of mine eaten.",
		"Use it from your binder and you're back on the green. My stew'll be waiting. Chef's won't.",
	],
	&"tally": [
		"A present! For YOU! A Verdana Return! One use, from your binder, and WHOOSH, you're back in the square!",
		"Use it to get back for dinner. Five o'clock. I'm not saying that's what it's for. That's what it's for.",
	],
	&"fennick": [
		"With the compliments of the Seabright Grand: a Seabright Return. Guests who wander are, regrettably, common.",
		"Use it from your binder and you'll find yourself on our forecourt. The first is on the house; the second, I'm afraid, is a hundred and fifty gold.",
	],
	&"sven": [
		"Here. Every guide carries one of these up the mountain: a Frisalle Return. Anselm had one in his pocket the night of the slide. He never got to use it.",
		"Use it from your binder and you're back in the square, wherever the mountain's put you. Don't be proud about it. Use it.",
	],
	&"hesper": [
		"Before you go back out into that oven: a Duskara Return. The dunes swallow the road every week. Use it from your binder and you'll wake up by my well.",
		"No charge. I give one to everyone who sits at my well the first time. The Company would charge you for the water in your eyes.",
	],
	&"brigid": [
		"Wait, love, before you go up those stairs: a Vetrassa Return. If the Steward finds a card missing you'll be sent back over the mountains for it, and you'll want a quick way home.",
		"No charge. Every racer who makes it this far gets one from me. Most of them need it.",
	],
	&"maudie": [
		"Here, before you go: a Halmeer Return. The cliff road washes out every other winter, and then it's a week's walk round.",
		"No charge. Anyone who comes all the way to the end of the coast deserves a quick way back to it.",
	],
}
const CARGO_CLUES: Array[StringName] = [&"crate_sand", &"crate_glove", &"crate_ledger"]
const CARGO_REWARD_GOLD := 40


## Set when talking to someone started a scene of its own (Ending.crown), so the
## resident doesn't open their question list over it.
var took_over := false


func _ready() -> void:
	EventBus.area_entered.connect(func(_t: String, _i: bool) -> void: _place_escort.call_deferred())


## Ada, out of the mine: in the North Shaft and the dunes she follows you while
## "Beneath the Dunes" is at stage 2 (her bunk is empty once she's left it).
func _place_escort() -> void:
	var zone := get_tree().current_scene
	if zone == null:
		return
	var here := zone.scene_file_path
	var bunk := zone.get_node_or_null(^"Npc_ada")
	if bunk and stage(&"beneath_dunes") >= 2:
		bunk.queue_free()
	if stage(&"beneath_dunes") != 2 or here not in ESCORT_ZONES or zone.get_node_or_null(^"Escort_ada"):
		return
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if player == null:
		return
	var ada: Npc = load("res://scenes/characters/npc.tscn").instantiate()
	ada.name = "Escort_ada"
	ada.npc_id = &"ada"
	ada.display_name = "Ada"
	ada.sprite_frames = load("res://assets/sprites/npcs/ada/ada_frames.tres")
	ada.sprite_offset_y = -22.0
	ada.lines = PackedStringArray(["I'm right behind you.", "Is it far? It's not far. It's not far.", "The air's different here. It moves."])
	ada.follow_player = true
	ada.walk_speed = 110.0
	ada.collision_layer = 0
	ada.position = player.position + Vector2(-24, 10)
	zone.add_child(ada)


func ada_following() -> bool:
	var zone := get_tree().current_scene
	return zone != null and zone.get_node_or_null(^"Escort_ada") != null


func stage(id: StringName) -> int:
	return GameState.quest_flags.get(StringName("quest:%s" % id), NOT_STARTED)


func set_stage(id: StringName, value: int) -> void:
	if stage(id) == NOT_STARTED and value != NOT_STARTED:
		noted_start(id)
	GameState.quest_flags[StringName("quest:%s" % id)] = value
	quest_changed.emit(id, value)


func flag(name: StringName) -> bool:
	return GameState.quest_flags.get(name, false)


## What an NPC says for quest reasons right now (empty = use their own lines).
func dialogue_for(npc_id: StringName) -> PackedStringArray:
	if gift_waiting(npc_id):
		return PackedStringArray(WELCOME_LINES[npc_id])
	match npc_id:
		&"bram":
			match stage(&"unmarked_cargo"):
				NOT_STARTED:
					return PackedStringArray([
						"Oi, cloak. You're one of those card racers, aren't you?",
						"Three crates came in on the night tide. No manifest. No harbor stamp. Nothing.",
						"Harbormaster says that's none of my business. Makes it my business, if you ask me.",
						"Somebody split 'em up before dawn, like they didn't want 'em seen together. One here on the quay, one on the west dock by the harbor office, one out on the pier.",
						"Take a look at 'em for me? Just look. Don't open anything that bites.",
					])
				1:
					return PackedStringArray(["One on the quay, one on the west dock, one out on the pier. I'll be here, pretending to coil rope. (%d/3 checked)" % _clues_found()])
				2:
					return PackedStringArray([
						"Desert sand in the straw... a glove that small... and 'D.M.' on a ledger scrap?",
						"Duskara. Has to be. There's nothing out that way but dunes and that old mine they say closed years ago.",
						"...Keep this between us. Here, for your trouble.",
						"If anyone asks, you were helping me count barrels.",
					])
				DONE:
					return PackedStringArray(["Barrel, barrel, barrel. Very normal harbor. Nothing to see."])
		&"pell":
			match stage(&"trees_remember"):
				NOT_STARTED:
					return PackedStringArray([
						"You're a racer. You go places the rest of us don't. Will you listen a moment?",
						"I found a little boot in the moss by the Hollow. That's the cave under the roots, north-east of the green. Too small to be a racer's boot. Too far from any house to be one of ours.",
						"The moss gate in front of it wants a Hollow Acorn card to open. The boars down in Thornveil carry them, and so do the hounds, now and then. I haven't one to spare.",
						"Something big has moved in down there this year. We hear it at night. Whatever's in there, somebody small went in first. Please. Go and look.",
					])
				1:
					return PackedStringArray(["The Hollow's up the path, north-east of the green: the moss gate takes a Hollow Acorn, then down under the roots. Mind whatever's living in it."])
				2:
					return PackedStringArray(["You found something. I can see it on you. Take it to Elder Moss. She keeps the names."])
				DONE:
					if not flag(&"pell_gift"):
						return PackedStringArray([
							"You came back up out of there. With the bear still down there, and you still walking. I didn't think anyone would.",
							"Moss told me about the tag. One-one-seven. She ran, and she made it as far as our roots. That's further than the rest of them got.",
							"I used to make fireworks for the solstice, before the spring. I've been packing something meaner since. Resin off the Hollow roots, and a pinch of what I won't say.",
							"Here. Emberburst rounds. Wear the card, then hold your pistol and let it gather before you loose it. It bursts where it lands, and anything close by feels it.",
							"If you ever get as far as Duskara, you'll want them. Whatever's taking children out there won't come quietly.",
						])
					return PackedStringArray([
						"Hold the shot until it glows, then let go. Mind you're not standing next to where it lands.",
						"Moss carved a new notch. Not low down, this time. Up where the grown ones go. For whoever finds that child.",
					])
		&"moss":
			match stage(&"trees_remember"):
				2:
					return PackedStringArray([
						"...A work tag. 'D.M. - No. 117.' And bread, and a carved bird.",
						"We sent seven children east for the Duskara work last spring. The foreman's men said it was apprentice wages. Room and board and a trade.",
						"'I ran. Tell mama I ran.' She did, then. One of them did.",
						"Take these, racer. For the road east. And this: the star map my mother drew. The stars on it aren't in our sky anymore. Perhaps you'll find where they went.",
						"And if you ever stand in Duskara, look for number 117. Tell her Sorenda remembers.",
					])
				DONE:
					return PackedStringArray(["Every notch on that post is a name. I've started carving them larger."])
		&"wen":
			match stage(&"wens_boat"):
				NOT_STARTED:
					return PackedStringArray([
						"You're a racer! You go everywhere. Will you help me?",
						"I'm building a boat, to sail round to the dunes and bring Papa home. I've got the hull. I need a sail, oars and rope.",
						"There's an old sail somebody left on the beach, a pair of oars down on the west quay, and a coil of rope out on the pier. Nobody wants them. I asked.",
					])
				1:
					return PackedStringArray(["A sail from the beach, oars from the west quay, rope from the pier. (%d/3 found)" % _parts_found()])
				2:
					return PackedStringArray([
						"You found them all! Look, the sail's hardly torn at all.",
						"Papa always said a boat's only as good as its knots. I'll tie them the way he showed me.",
						"Here. It's not much. When the boat's done, I'll write to you from the dunes.",
					])
				DONE:
					return PackedStringArray(["She'll float. I tried her in the bath. Well. Half of her."])
		&"aldous":
			match stage(&"stones_remember"):
				NOT_STARTED:
					return PackedStringArray([
						"A racer. Good. You go places an old cat's knees won't take him any more.",
						"There are three standing stones left on this side of the island: the circle on the Stonewatch Downs, north-west of the King's Road; the stone out on Stone Point in Lake Serin; and the Starfall stone, up under the pass.",
						"They all tell one story, carved smaller and smaller down the stone. I've read two of them in my life. I want to know how the last one ends.",
						"Go and look at all three. Read them properly. Then come back and tell me what's at the bottom.",
					])
				1:
					return PackedStringArray(["The circle on the downs, Stone Point in Lake Serin, and the Starfall stone under the pass. (%d/3 read)" % _stones_read()])
				2:
					return PackedStringArray([
						"All three? Tell me. Slowly.",
						"...A crown, and a line of figures under it, each smaller than the last. On the Starfall stone, the line runs into the snow. And someone has crossed out the crown.",
						"Then it's not a history. It's a ledger. Every king, and under each one, what it cost. Carved where anyone could read it, and nobody did.",
						"Take this. It was my teacher's, and hers before that. It hums when you're near the stones, and keeps you on your feet a little longer than you'd manage alone.",
					])
				DONE:
					if flag(&"read_kings_tomb"):
						return PackedStringArray([
							"You went down into the barrow? Under the downs? Forty years I've walked over that mound.",
							"'What the set costs is carved below', and below, the stone chiselled smooth. Somebody didn't want the cost read. Not lately: the chisel marks are fresh.",
							"Every king since has taken the set and the isle with it. I always thought the figures were a story. I think now they were a receipt.",
						])
					return PackedStringArray(["A ledger in stone. I've read it forty years and never once added it up."])
		&"sparkle":
			if Errands.state(&"sparkle_dare") != Errands.DONE:
				return PackedStringArray()
			match stage(&"light_on_water"):
				NOT_STARTED:
					return PackedStringArray([
						"You went all the way into the Grotto. That means you're the only person on this island I trust. Listen.",
						"Some nights there's a light out on the water, past the yachts. Low down. No ship I can see, and nobody here will say what it is.",
						"Go up to the lookout on the headland after dark and look through the telescope. Then tell me I'm not making it up.",
					])
				1:
					return PackedStringArray(["After dark! The telescope on the headland. Daylight's no good, it only shows up at night."])
				2:
					return PackedStringArray(["It blinked, and something here blinked back? From the jetty? Which bungalow? Go and look. At night. I'll keep watch from the pier."])
				3:
					return PackedStringArray([
						"Bungalow 3. The Duke's 'business guests'. Rope and sea water on the step and the Company's stencil on a crate. In MY resort.",
						"Sassy's going to say it's none of our business. It's literally our business. We own it.",
						"Here. For keeping watch with me. Don't tell Sassy where you got it. Don't tell anyone anything. Yet.",
					])
				DONE:
					if stage(&"smugglers_route") != DONE:
						return PackedStringArray(["Next time the light blinks, I'm swimming out after the rope. Don't tell the lifeguard."])
					match stage(&"old_reef"):
						NOT_STARTED:
							return PackedStringArray([
								"You've been to Halmeer. Nessa's light is lit again; we saw it from here last night. So the barge comes past us now, the long way, and it still stops at the old reef.",
								"I've dived that reef since I was four. Whatever they let down on that rope, it's sitting on my reef.",
								"Tonight. Meet me at the end of the diving pier after dark. Bring your breath.",
							])
						1:
							return PackedStringArray(["The end of the diving pier, after dark. I'll have the lanterns. Don't let Sassy see you, she'll want to come and she can't hold her breath for a sneeze."])
						2:
							return PackedStringArray([
								"...You saw it too. I didn't want it to be the crown. I wanted it to be the Duke, or the Company, or anybody.",
								"That's Uncle Loki's seal. The one on the deed to this place. On the crates going off the island.",
								"Here. My charm, the one I dive with. It makes you quick in the water, and quicker out of it. I don't think I'll be diving for a while.",
							])
						DONE:
							return PackedStringArray(["I've been reading the deed again. 'A gift from the Crown.' Everything here is a gift from the Crown. I used to think that was a nice thing to say."])
		&"rafi":
			if Errands.state(&"rafi_tonic") != Errands.DONE:
				return PackedStringArray()
			match stage(&"beneath_dunes"):
				NOT_STARTED:
					return PackedStringArray([
						"The girl you helped me with is on her way north. She has a sister. Ada. Seven years old, and sick, and still down the North Shaft.",
						"Sick ones get moved to the infirmary. Nobody comes back up from the infirmary.",
						"The tally gate at the bottom counts you in if you show it a tag. Nib's, if he's free of it. Old Gideon keeps the night watch; he'll be asleep, if you're the right sort.",
						"Find Ada in the bunks. Bring her out the old way: past the flooded workings there's a crawl that comes up in the Bone Hollow. Zahra will be watching for her at the Sunwell.",
					])
				1:
					return PackedStringArray(["Down the shaft on the terrace, through the tally gate. Ada's in the bunks, west of the sorting floor. Then out the crawl past the lake, never back up the shaft."])
				2:
					return PackedStringArray(["Not up the shaft! Out the old way, past the flooded workings, to the Bone Hollow, and Zahra at the Sunwell."])
				3:
					return PackedStringArray([
						"Zahra's bell rang twice, then once, at dusk. That means she's safe, and walking north with the caravan, and the sister will be waiting.",
						"You can't buy that and you can't sell it. Here: the lamp. Every friend of the line carries one. Light it where you need to not be seen.",
					])
				DONE:
					return PackedStringArray(["Every bell that rings twice, then once: that's someone you'll never meet, thanking you."])
		&"ada":
			match stage(&"beneath_dunes"):
				1:
					return PackedStringArray([
						"...Who are you? You're not the overseer. You've got sun on you.",
						"Rafi sent you? Then the bell's real. My sister said the bell was real.",
						"I can walk. I can. Just don't go fast. And not up the lift. They count you at the lift.",
					])
				2:
					return PackedStringArray(["I'm right behind you."])
		&"zahra":
			if stage(&"beneath_dunes") == 2 and ada_following():
				return PackedStringArray([
					"...Ada. Oh, little one. Come here, come into the shade. Water first.",
					"You brought her out the crawl? Then the line still holds. Good. Good.",
					"She'll ride north with the caravan tonight, hidden in the water casks; my cousin's people meet us past the plains. Tell Rafi the bell rang. He'll know.",
				])
		&"nessa":
			match stage(&"smugglers_route"):
				NOT_STARTED:
					return PackedStringArray([
						"A racer. Nobody comes to Halmeer on purpose, you know. Sit, if you can find a chair under the oil cans.",
						"Forty years I've kept this light. And for the last three, on the moonless nights, the Company pays me to keep it dark.",
						"On those nights I hear oars under the cape, and I see nothing, because I'm paid not to look. I'm too old for the cut down to the sea cave. You aren't.",
						"Look at the tide board on the quay, and the Company's salt house, and go down the cut to the cave. Then come and tell me what my dark has been for.",
					])
				1:
					return PackedStringArray(["The tide board on the quay, the salt house door, and the cave down the cut on the heath. (%d/3)" % _smuggler_found()])
				2:
					return PackedStringArray([
						"Cards. Uncut. From the mine under Duskara, over the mountain by the ice road, down the coast, and out of my cave on my dark nights.",
						"Maudie's Tom rowed on that barge. Half the village has. And I sat up here with the lamp out and the money in a tin.",
						"Well. The light's lit tonight, and every night, and they can find another keeper. Take this: the lamp I kept in my window on the dark nights anyway. The beasts on the cliff road don't like it.",
					])
				DONE:
					return PackedStringArray(["The light's lit every night now. The Company sent a letter about it. I used the letter to light the lamp."])
		&"freya":
			match stage(&"audience_throne"):
				NOT_STARTED:
					if not audience_ready():
						return PackedStringArray()
					return PackedStringArray([
						"You've been following the carts. Frisalle's ice road, the light off Seabright, the names under Duskara. Don't look surprised; the Guard reads the reports nobody else does.",
						"There's a book in the throne room, by the empty chair. The Throne Ledger. Only the King may read it. Go and read it.",
						"Then come and tell me what it says. I've read it. I need to hear somebody else say it out loud.",
					])
				1:
					return PackedStringArray(["The Throne Ledger. On the lectern by the throne. Read the last pages, the ones in my father's hand."])
				2:
					return PackedStringArray([
						"'Seam worked. Count true.' Every king. Every race. My grandfather's hand, and his, and then my father's.",
						"So now you know what I know. The island's kings have always signed for the mine. My mother runs it. My brother cooks for the men who buy from it. And I guard the chair.",
						"Whoever wins this race will sit in that chair and hold that pen. If it's you... you could write something else on the next page. Nobody ever has.",
						"Take this. Guard pay; I've had nothing to spend it on. And come up those steps with the whole set, if you can.",
					])
				DONE:
					return PackedStringArray(["I'll be on the steps. Bring the set. And when he asks you what you'll do with it, don't answer quickly."])
		&"steward":
			if Ending.has_set(GameState.PLAYER) and not Ending.is_over():
				return PackedStringArray([
					"Ah. Let me see them. Slowly, if you please; I've waited a long time for this part.",
					"...%d. %d. %d. Every one, and not a corner bent." % [CardDatabase.final_set().size() - 2, CardDatabase.final_set().size() - 1, CardDatabase.final_set().size()],
					"Wait here, racer. There is someone who has been waiting to meet you. He's been waiting the whole race.",
				])
			if Ending.is_over():
				return PackedStringArray(["Your Majesty. The ledger is on the lectern, whenever you're ready to write in it."])
			# Every other visit he counts what you hold; the rest of the time, his own lines.
			GameState.quest_flags[&"steward_counted"] = not flag(&"steward_counted")
			if not flag(&"steward_counted"):
				return PackedStringArray()
			var held := GameState.collection(GameState.PLAYER).set_progress(CardDatabase.final_set())
			return PackedStringArray(["You hold %d of the %d cards of the set. Come back with all of them, and I'll count them with you." % [held, CardDatabase.final_set().size()]])
		&"hesper":
			match stage(&"foremans_names"):
				NOT_STARTED:
					return PackedStringArray([
						"Families come to my well asking after their children. A son who went down the shaft for a season, a daughter 'transferred'. I can't tell them anything.",
						"The foreman keeps a ledger of names in the lower office, under the sorting floor. Every name in, every name out. Count true, she says.",
						"If you ever go down there, read it for me. Bring me the names. Somebody should be able to answer when a mother asks.",
					])
				1:
					return PackedStringArray(["The foreman's ledger of names, in the lower office under the sorting floor. Read it, and bring me what it says."])
				2:
					var lines := PackedStringArray([
						"...So many with no 'up'. Two years of them. And pages of numbers with nobody's name at all.",
						"Corin, of Verdana. A sheepdog with a red scarf. There's an old weaver in Verdana who asks every traveller about a red scarf. Now somebody can tell her.",
					])
					if &"raider" in GameState.active_rivals:
						lines.append("And here, one number crossed out, and circled, years ago. The one who got out. They say that one's racing now, with a mask on.")
					lines.append("Take this, for going where I couldn't. I'll copy the names onto the wall of my cistern, where the Company never looks.")
					return lines
				DONE:
					return PackedStringArray(["The names are on the cistern wall now. Mothers come and read them. Some of them leave flowers. Some of them leave and go north."])
		&"sven":
			match stage(&"over_the_top"):
				NOT_STARTED:
					return PackedStringArray([
						"When the slide came down, three young ones from the inn decided they'd go over the top instead. Brin, Tova and little Pike. I told them they were fools.",
						"They took my second-best rope. They never came down the other side.",
						"You go up and down that range. If you find where they camped, or where they went, come and tell me. Whatever it is.",
					])
				1:
					return PackedStringArray(["High on the west of the range, they'd have camped. And look for anywhere they might have sheltered. (%d/2 found)" % _climbers_found()])
				2:
					return PackedStringArray([
						"Day five, and nothing after. Brin's feet. And the camp left standing, the pack still in it.",
						"And at the adit: small boots, trodden flat, and new boards on an old mine. They didn't freeze, then. Or not all of them. Somebody took them in, and it wasn't to keep them warm.",
						"Here. My best rope, and a collar I took off a wolf that thought I was dinner. For the toll. You'll want to keep going places I can't.",
					])
				DONE:
					return PackedStringArray(["I've put three more names on the board in the tower. In pencil. Pencil rubs out."])
		&"juniper":
			if Errands.state(&"juniper_tonic") != Errands.DONE:
				return PackedStringArray()
			match stage(&"glowcaps"):
				NOT_STARTED:
					return PackedStringArray([
						"Harl's youngest has the fever. Feverfew won't touch it. Glowcaps will, the blue ones that only grow in the dark.",
						"They grow in the Hollow, past the moss gate. One clump in the mushroom grotto, one by the still pool past the bear's den, one right at the back in the alcove.",
						"I'd go myself, but I've seen what's living in the den. You've a sword. I've a mortar and pestle.",
					])
				1:
					return PackedStringArray(["The grotto, the pool past the den, the alcove at the back. Blue ones. The green ones will make him worse. (%d/3 gathered)" % _glowcaps_found()])
				2:
					return PackedStringArray([
						"Blue, all three. And you came back with all your fingers. I'll have the draught brewed by moonrise.",
						"Here. For the risk, and for Harl's girl. And take a tonic or two; you look like you went through the den, not round it.",
					])
				DONE:
					return PackedStringArray(["She's sitting up and eating. Harl hasn't stopped crying. Nor have I, if I'm honest."])
		&"oda":
			if Errands.state(&"oda_news") != Errands.DONE:
				return PackedStringArray()
			match stage(&"millstream"):
				NOT_STARTED:
					return PackedStringArray([
						"You went all the way to the lake for me. Will you do one more thing? It's only a little walk.",
						"The millstream comes down from Lake Serin, past the mill and through the town. Things catch in the reeds along it. Things from upstream.",
						"Walk the bank for me, from the barn to the bridges. If anything of his has come down that water, I want it home.",
					])
				1:
					return PackedStringArray(["Along the millstream, in the reeds: from the barn end, past the bridges. (%d/3 found)" % _millstream_found()])
				2:
					return PackedStringArray([
						"...That's my wool. That's the scarf. I'd know my own red anywhere; I dyed it with madder off the hedge.",
						"And Company scrip, and a bird carved the way they carve them in Sorenda. He passed through the forest, then. And north, by the water.",
						"He's alive. Nobody sends a ration chit after a dead boy. Take this, and thank you, and don't tell me how far north the water goes. Not yet.",
					])
				DONE:
					if flag(&"knows_corin") and not flag(&"told_oda_corin"):
						return PackedStringArray([
							"...You've seen the foreman's book. I can tell by your face. Say it plainly. I've had two years of nobody saying anything.",
							"'Transferred, North Workings.' Not 'up'. Not dead. Transferred. Then he went north under the mountain, with the rest of them, and some of them came out the other side.",
							"Thank you. Now I know which way to knit.",
						])
					return PackedStringArray(["I've unpicked the rest of the scarf and started another. Longer, this time. It's a long way north."])
		&"mirren":
			match stage(&"merchants_ledger"):
				NOT_STARTED:
					return PackedStringArray([
						"You're a racer. You go where you like and nobody asks you why. Will you do something for me? Quietly?",
						"The books don't add up. I keep the factors' ledger, and I keep it straight. But somebody keeps a second column, and it isn't me.",
						"Read the tally board at the weigh house in the square. Read the great ledger here, the facing page. And Bodo's house, across the square... I can't go into Bodo's house. You could.",
						"Then come back and tell me I'm not imagining it.",
					])
				1:
					return PackedStringArray(["The tally board in the square, the great ledger here, and whatever Bodo keeps at home. (%d/3 read)" % _ledger_read()])
				2:
					var lines := PackedStringArray([
						"Forty carts. Through an ice road under the mountain, weighed at night, sealed with the second seal, sent down to Vetrassa for 'the Company'.",
						"And signed 'D.', with a dachshund's head on the wax. The factors' charming friend. The Duke.",
					])
					if GameState.active_rivals.has(&"hoarder"):
						lines.append("...And the Vetrassa factors are the Hoarder's family's people. Ashcombe and Sons, on Vetrassa's square. The money your rival races on has been coming over my scales all winter.")
					lines.append_array([
						"Somebody brought the pass down so nobody would see the carts go by. Ottilie's Anselm was on the pass that night.",
						"Take this. The second seal. If it's in your binder, it isn't in theirs. It's the only thing I can think to do.",
					])
					return lines
				DONE:
					return PackedStringArray(["I've started keeping a third book. Just for me. Everything they don't want counted."])
		&"mirela":
			if not flag(&"met_mirela"):
				return PackedStringArray([
					"Another one off the morning boat. Welcome to Kalmora, racer. I'm Mirela, harbormaster. Everything that lands here, I stamp. Including you.",
					"You're here for the race, same as the other two cloaks who came in this week. Forty-seven cards makes a set. Carry the whole set into Vetrassa, far up the north-west coast, and it's yours: riches beyond anything, so they say.",
					"Talk to folk. Kalmora's people know things, and some of them have cards put by for a racer who asks nicely. Come back with three cards in hand and I'll give you one of mine.",
					"Ask me anything you like before you go.",
				])
			if stage(&"unmarked_cargo") in [1, 2]:
				return PackedStringArray([
					"Unmarked crates? I don't know what Bram's been telling you.",
					"Everything on my quay is stamped. Everything.",
				])
	return PackedStringArray()


## "!" = has something for you, "?" = waiting on you to report back.
func marker_for(npc_id: StringName) -> String:
	if gift_waiting(npc_id):
		return "!"
	if npc_id == &"pell" and (stage(&"trees_remember") == NOT_STARTED
			or stage(&"trees_remember") == DONE and not flag(&"pell_gift")):
		return "!"
	if npc_id == &"moss" and stage(&"trees_remember") == 2:
		return "?"
	if npc_id == &"bram":
		match stage(&"unmarked_cargo"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"wen":
		match stage(&"wens_boat"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"aldous":
		match stage(&"stones_remember"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"mirela" and not flag(&"met_mirela"):
		return "!"
	if npc_id == &"sparkle" and Errands.state(&"sparkle_dare") == Errands.DONE:
		match stage(&"light_on_water"):
			NOT_STARTED:
				return "!"
			3:
				return "?"
	if npc_id == &"sven":
		match stage(&"over_the_top"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"rafi" and Errands.state(&"rafi_tonic") == Errands.DONE:
		match stage(&"beneath_dunes"):
			NOT_STARTED:
				return "!"
			3:
				return "?"
	if npc_id == &"ada" and stage(&"beneath_dunes") == 1:
		return "!"
	if npc_id == &"zahra" and stage(&"beneath_dunes") == 2 and ada_following():
		return "?"
	if npc_id == &"hesper" and not gift_waiting(&"hesper"):
		match stage(&"foremans_names"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"juniper" and Errands.state(&"juniper_tonic") == Errands.DONE:
		match stage(&"glowcaps"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"oda" and Errands.state(&"oda_news") == Errands.DONE:
		match stage(&"millstream"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"sparkle" and stage(&"light_on_water") == DONE and stage(&"smugglers_route") == DONE:
		match stage(&"old_reef"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"nessa":
		match stage(&"smugglers_route"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	if npc_id == &"freya":
		match stage(&"audience_throne"):
			NOT_STARTED:
				return "!" if audience_ready() else ""
			2:
				return "?"
	if npc_id == &"steward" and Ending.has_set(GameState.PLAYER) and not Ending.is_over():
		return "?"
	if npc_id == &"mirren":
		match stage(&"merchants_ledger"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	return ""


func talked_to(npc_id: StringName) -> void:
	if gift_waiting(npc_id):
		var card: StringName = WELCOME_GIFTS[npc_id]
		GameState.quest_flags[StringName("gift:%s" % npc_id)] = true
		GameState.add_loose_card(GameState.PLAYER, card)
		EventBus.notify.emit("Got a %s. Use it from the binder to come straight back." % CardDatabase.get_card(card).display_name)
		return
	if npc_id == &"mirela":
		GameState.quest_flags[&"met_mirela"] = true
	if npc_id == &"steward" and Ending.has_set(GameState.PLAYER) and not Ending.is_over() 			and not flag(&"crowned"):
		Ending.crown(get_tree())
		return
	if npc_id == &"sparkle" and stage(&"light_on_water") == DONE and stage(&"smugglers_route") == DONE:
		match stage(&"old_reef"):
			NOT_STARTED:
				set_stage(&"old_reef", 1)
				EventBus.notify.emit("Quest started: The Old Reef")
				return
			2:
				GameState.add_currency(REEF_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, REEF_REWARD_CARD)
				set_stage(&"old_reef", DONE)
				EventBus.notify.emit("Quest complete: The Old Reef (+%d gold, the Seafoam Charm)" % REEF_REWARD_GOLD)
				return
	if npc_id == &"nessa":
		match stage(&"smugglers_route"):
			NOT_STARTED:
				set_stage(&"smugglers_route", 2 if _smuggler_found() == SMUGGLER_CLUES.size() else 1)
				EventBus.notify.emit("Quest started: The Smuggler's Route")
			2:
				GameState.add_currency(SMUGGLER_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, SMUGGLER_REWARD_CARD)
				set_stage(&"smugglers_route", DONE)
				EventBus.notify.emit("Quest complete: The Smuggler's Route (+%d gold, the Keeper's Lamp)" % SMUGGLER_REWARD_GOLD)
		return
	if npc_id == &"freya":
		match stage(&"audience_throne"):
			NOT_STARTED:
				if audience_ready():
					set_stage(&"audience_throne", 2 if flag(&"read_throne_ledger") else 1)
					EventBus.notify.emit("Quest started: An Audience Before the Throne")
			2:
				GameState.add_currency(AUDIENCE_REWARD_GOLD)
				set_stage(&"audience_throne", DONE)
				EventBus.notify.emit("Quest complete: An Audience Before the Throne (+%d gold)" % AUDIENCE_REWARD_GOLD)
		return
	if npc_id == &"oda" and stage(&"millstream") == DONE and flag(&"knows_corin"):
		GameState.quest_flags[&"told_oda_corin"] = true
	if npc_id == &"wen":
		match stage(&"wens_boat"):
			NOT_STARTED:
				set_stage(&"wens_boat", 1)
				EventBus.notify.emit("Quest started: A Boat for Wen")
			2:
				GameState.add_currency(BOAT_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, &"lockbox_seal")
				set_stage(&"wens_boat", DONE)
				EventBus.notify.emit("Quest complete: A Boat for Wen (+%d gold, Lockbox Seal)" % BOAT_REWARD_GOLD)
		return
	if npc_id == &"aldous":
		match stage(&"stones_remember"):
			NOT_STARTED:
				set_stage(&"stones_remember", 2 if _stones_read() == STONES.size() else 1)
				EventBus.notify.emit("Quest started: Stones That Remember")
			2:
				GameState.add_currency(STONES_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, STONES_REWARD_CARD)
				set_stage(&"stones_remember", DONE)
				EventBus.notify.emit("Quest complete: Stones That Remember (+%d gold, Stonesong Charm)" % STONES_REWARD_GOLD)
		return
	if npc_id == &"sparkle" and Errands.state(&"sparkle_dare") == Errands.DONE:
		match stage(&"light_on_water"):
			NOT_STARTED:
				set_stage(&"light_on_water", 1)
				EventBus.notify.emit("Quest started: The Light on the Water")
			3:
				GameState.add_currency(LIGHT_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, &"lockbox_seal")
				GameState.quest_flags[&"knows_bungalow_3"] = true
				set_stage(&"light_on_water", DONE)
				EventBus.notify.emit("Quest complete: The Light on the Water (+%d gold, Lockbox Seal)" % LIGHT_REWARD_GOLD)
		return
	if npc_id == &"rafi" and Errands.state(&"rafi_tonic") == Errands.DONE:
		match stage(&"beneath_dunes"):
			NOT_STARTED:
				set_stage(&"beneath_dunes", 1)
				EventBus.notify.emit("Quest started: Beneath the Dunes")
			3:
				GameState.add_currency(ADA_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, ADA_REWARD_CARD)
				set_stage(&"beneath_dunes", DONE)
				EventBus.notify.emit("Quest complete: Beneath the Dunes (+%d gold, the Green Lamp)" % ADA_REWARD_GOLD)
		return
	if npc_id == &"ada" and stage(&"beneath_dunes") == 1:
		set_stage(&"beneath_dunes", 2)
		EventBus.notify.emit("Ada will follow you. Take her out the crawl past the flooded workings, to Zahra at the Sunwell")
		_place_escort()
		var bunk := get_tree().current_scene.get_node_or_null(^"Npc_ada") if get_tree().current_scene else null
		if bunk:
			var escort := get_tree().current_scene.get_node_or_null(^"Escort_ada") as Node2D
			if escort:
				escort.global_position = (bunk as Node2D).global_position
			bunk.queue_free()
		return
	if npc_id == &"zahra" and stage(&"beneath_dunes") == 2 and ada_following():
		var escort := get_tree().current_scene.get_node_or_null(^"Escort_ada")
		if escort:
			escort.queue_free()
		set_stage(&"beneath_dunes", 3)
		EventBus.notify.emit("Ada is safe with Zahra's caravan. Tell Rafi in Duskara")
		return
	if npc_id == &"hesper" and not gift_waiting(&"hesper"):
		match stage(&"foremans_names"):
			NOT_STARTED:
				set_stage(&"foremans_names", 2 if flag(&"read_names_ledger") else 1)
				EventBus.notify.emit("Quest started: The Foreman's Names")
			2:
				GameState.add_currency(NAMES_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, &"lockbox_seal")
				GameState.quest_flags[&"knows_corin"] = true
				set_stage(&"foremans_names", DONE)
				EventBus.notify.emit("Quest complete: The Foreman's Names (+%d gold, Lockbox Seal)" % NAMES_REWARD_GOLD)
		return
	if npc_id == &"sven":
		match stage(&"over_the_top"):
			NOT_STARTED:
				set_stage(&"over_the_top", 2 if _climbers_found() == CLIMBER_CLUES.size() else 1)
				EventBus.notify.emit("Quest started: The Three Who Went Over")
			2:
				GameState.add_currency(CLIMBERS_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, &"iron_wolf_collar")
				GameState.quest_flags[&"knows_north_workings"] = true
				set_stage(&"over_the_top", DONE)
				EventBus.notify.emit("Quest complete: The Three Who Went Over (+%d gold, Iron Wolf Collar)" % CLIMBERS_REWARD_GOLD)
		return
	if npc_id == &"juniper" and Errands.state(&"juniper_tonic") == Errands.DONE:
		match stage(&"glowcaps"):
			NOT_STARTED:
				set_stage(&"glowcaps", 2 if _glowcaps_found() == GLOWCAPS.size() else 1)
				EventBus.notify.emit("Quest started: Glowcaps for the Fever")
			2:
				GameState.add_currency(GLOWCAPS_REWARD_GOLD)
				GameState.add_item(&"healers_tonic", 2)
				set_stage(&"glowcaps", DONE)
				EventBus.notify.emit("Quest complete: Glowcaps for the Fever (+%d gold, 2 Healer's Tonics)" % GLOWCAPS_REWARD_GOLD)
		return
	if npc_id == &"oda" and Errands.state(&"oda_news") == Errands.DONE:
		match stage(&"millstream"):
			NOT_STARTED:
				set_stage(&"millstream", 2 if _millstream_found() == MILLSTREAM_FINDS.size() else 1)
				EventBus.notify.emit("Quest started: What the Millstream Carries")
			2:
				GameState.add_currency(MILLSTREAM_REWARD_GOLD)
				GameState.add_item(&"healers_tonic", 2)
				GameState.quest_flags[&"knows_grandson_north"] = true
				set_stage(&"millstream", DONE)
				EventBus.notify.emit("Quest complete: What the Millstream Carries (+%d gold, 2 Healer's Tonics)" % MILLSTREAM_REWARD_GOLD)
		return
	if npc_id == &"mirren":
		match stage(&"merchants_ledger"):
			NOT_STARTED:
				set_stage(&"merchants_ledger", 2 if _ledger_read() == LEDGER_CLUES.size() else 1)
				EventBus.notify.emit("Quest started: The Merchant's Ledger")
			2:
				GameState.add_currency(LEDGER_REWARD_GOLD)
				GameState.add_loose_card(GameState.PLAYER, LEDGER_REWARD_CARD)
				GameState.quest_flags[&"knows_ice_road"] = true
				set_stage(&"merchants_ledger", DONE)
				EventBus.notify.emit("Quest complete: The Merchant's Ledger (+%d gold, Factors' Seal)" % LEDGER_REWARD_GOLD)
		return
	if npc_id == &"pell" and stage(&"trees_remember") == NOT_STARTED:
		set_stage(&"trees_remember", 1)
		EventBus.notify.emit("Quest started: What the Trees Remember")
		return
	if npc_id == &"pell" and stage(&"trees_remember") == DONE and not flag(&"pell_gift"):
		GameState.quest_flags[&"pell_gift"] = true
		GameState.add_loose_card(GameState.PLAYER, &"emberburst_rounds")
		EventBus.notify.emit("Pell gave you Emberburst Rounds. Wear it from the binder, then hold the pistol to charge.")
		return
	if npc_id == &"moss" and stage(&"trees_remember") == 2:
		GameState.add_item(&"healers_tonic", 2)
		GameState.add_currency(TREES_REWARD_GOLD)
		GameState.add_loose_card(GameState.PLAYER, TREES_REWARD_CARD)
		GameState.add_loose_card(GameState.PLAYER, &"mossheart_charm")
		GameState.quest_flags[&"knows_tag_117"] = true
		set_stage(&"trees_remember", DONE)
		EventBus.notify.emit("Quest complete: What the Trees Remember (+%d gold, 2 Healer's Tonics, Sorenda Star Map, Mossheart Charm)" % TREES_REWARD_GOLD)
		return
	if npc_id != &"bram":
		return
	match stage(&"unmarked_cargo"):
		NOT_STARTED:
			set_stage(&"unmarked_cargo", 1)
			EventBus.notify.emit("Quest started: The Unmarked Cargo")
		2:
			GameState.add_loose_card(GameState.PLAYER, &"second_wind")
			GameState.add_currency(CARGO_REWARD_GOLD)
			GameState.quest_flags[&"knows_duskara_shipments"] = true
			set_stage(&"unmarked_cargo", DONE)
			EventBus.notify.emit("Quest complete: The Unmarked Cargo (+%d gold, Second Wind)" % CARGO_REWARD_GOLD)


## A clue object was examined. Returns what the player learns.
func inspect(clue_id: StringName) -> PackedStringArray:
	if clue_id in BOAT_PARTS:
		if stage(&"wens_boat") != 1:
			return PackedStringArray([{
				&"boat_sail": "An old sail, folded and left on the sand.",
				&"boat_oars": "A pair of worn oars, propped against the quay wall.",
				&"boat_rope": "A coil of good rope, going green at one end.",
			}[clue_id]])
		if clue_found(clue_id):
			return PackedStringArray(["You've already got this for Wen."])
		GameState.quest_flags[StringName("clue:%s" % clue_id)] = true
		if _parts_found() >= BOAT_PARTS.size():
			set_stage(&"wens_boat", 2)
		else:
			quest_changed.emit(&"wens_boat", 1)
		return PackedStringArray([{
			&"boat_sail": "You fold the old sail under your arm. Patched, but it'll catch the wind.",
			&"boat_oars": "You take the oars. One is carved with a little fish: somebody's once.",
			&"boat_rope": "You sling the rope over your shoulder. Good hemp, Kalmora-twisted.",
		}[clue_id]])
	if clue_id in CARGO_CLUES:
		if stage(&"unmarked_cargo") != 1:
			return PackedStringArray(["An unmarked crate. No harbor stamp, no manifest tag."])
		var text: String = {
			&"crate_sand": "The straw packing is full of fine red sand, the kind that only blows off the Siroth Dunes.",
			&"crate_glove": "Caught on a splinter: a tiny work glove, worn through at the fingertips. Far too small for a dockhand.",
			&"crate_ledger": "A torn ledger scrap wedged in the slats: 'D.M. - lot 14 - 60 commons, 2 rares. Count the hands, not the cards.'",
		}[clue_id]
		GameState.quest_flags[StringName("clue:%s" % clue_id)] = true
		if _clues_found() >= CARGO_CLUES.size():
			set_stage(&"unmarked_cargo", 2)
		else:
			quest_changed.emit(&"unmarked_cargo", 1)
		return PackedStringArray([text])
	return PackedStringArray()


## Something was read (Readable): quests that hinge on a letter or an object hear it here.
func read(title: String, at_night := false) -> void:
	if STONES.has(title) and not flag(StringName("stone:%s" % title)):
		GameState.quest_flags[StringName("stone:%s" % title)] = true
		if stage(&"stones_remember") == 1:
			if _stones_read() == STONES.size():
				set_stage(&"stones_remember", 2)
				EventBus.notify.emit("All three stones read. Take what you saw to Aldous in Verdana")
			else:
				quest_changed.emit(&"stones_remember", 1)
				EventBus.notify.emit("Stones That Remember: %d of 3 stones read" % _stones_read())
	if title == LIGHT_LOOKOUT and at_night and stage(&"light_on_water") == 1:
		set_stage(&"light_on_water", 2)
		EventBus.notify.emit("Something on the jetty answered the light. Find which bungalow, after dark")
	if title == LIGHT_DOOR and at_night and stage(&"light_on_water") == 2:
		set_stage(&"light_on_water", 3)
		EventBus.notify.emit("Tell Sparkle what you found at Bungalow 3")
	if title in CLIMBER_CLUES and not flag(StringName("climbers:%s" % title)):
		GameState.quest_flags[StringName("climbers:%s" % title)] = true
		if stage(&"over_the_top") == 1:
			if _climbers_found() == CLIMBER_CLUES.size():
				set_stage(&"over_the_top", 2)
				EventBus.notify.emit("Tell Sven in Frisalle what you found")
			else:
				quest_changed.emit(&"over_the_top", 1)
	if title in GLOWCAPS and not flag(StringName("glowcap:%s" % title)):
		GameState.quest_flags[StringName("glowcap:%s" % title)] = true
		if stage(&"glowcaps") == 1:
			if _glowcaps_found() == GLOWCAPS.size():
				set_stage(&"glowcaps", 2)
				EventBus.notify.emit("All three gathered. Take the glowcaps to Juniper")
			else:
				quest_changed.emit(&"glowcaps", 1)
				EventBus.notify.emit("Glowcaps for the Fever: %d of 3 gathered" % _glowcaps_found())
	if title in MILLSTREAM_FINDS and not flag(StringName("stream:%s" % title)):
		GameState.quest_flags[StringName("stream:%s" % title)] = true
		if stage(&"millstream") == 1:
			if _millstream_found() == MILLSTREAM_FINDS.size():
				set_stage(&"millstream", 2)
				EventBus.notify.emit("All three found. Take them to Oda")
			else:
				quest_changed.emit(&"millstream", 1)
				EventBus.notify.emit("What the Millstream Carries: %d of 3 found" % _millstream_found())
	if title == NAMES_LEDGER:
		GameState.quest_flags[&"read_names_ledger"] = true
		if stage(&"foremans_names") == 1:
			set_stage(&"foremans_names", 2)
			EventBus.notify.emit("Take the names to Hesper at the Cistern")
	if title == REEF_DIVE and at_night and stage(&"old_reef") == 1:
		set_stage(&"old_reef", 2)
		EventBus.notify.emit("Tell Sparkle what you saw on the reef")
	if SMUGGLER_CLUES.has(title) and not flag(StringName("smuggler:%s" % title)):
		GameState.quest_flags[StringName("smuggler:%s" % title)] = true
		if stage(&"smugglers_route") == 1:
			if _smuggler_found() == SMUGGLER_CLUES.size():
				set_stage(&"smugglers_route", 2)
				EventBus.notify.emit("All three found. Tell Nessa at the cape light")
			else:
				quest_changed.emit(&"smugglers_route", 1)
				EventBus.notify.emit("The Smuggler's Route: %d of 3 found" % _smuggler_found())
	if title == THRONE_LEDGER:
		GameState.quest_flags[&"read_throne_ledger"] = true
		if stage(&"audience_throne") == 1:
			set_stage(&"audience_throne", 2)
			EventBus.notify.emit("Tell Freya on the palace steps what the ledger says")
	if title == "The first king's tomb":
		GameState.quest_flags[&"read_kings_tomb"] = true
	if LEDGER_CLUES.has(title) and not flag(StringName("ledger:%s" % title)):
		GameState.quest_flags[StringName("ledger:%s" % title)] = true
		if stage(&"merchants_ledger") == 1:
			if _ledger_read() == LEDGER_CLUES.size():
				set_stage(&"merchants_ledger", 2)
				EventBus.notify.emit("All three records read. Take what you found to Mirren at the counting house")
			else:
				quest_changed.emit(&"merchants_ledger", 1)
				EventBus.notify.emit("The Merchant's Ledger: %d of 3 records read" % _ledger_read())
	if title == SATCHEL_TITLE and stage(&"trees_remember") in [NOT_STARTED, 1]:
		set_stage(&"trees_remember", 2)
		EventBus.notify.emit("Take what you found to Elder Moss")


## A running quest still needs this readable read (its marker says so).
func wants(title: String, at_night := false) -> bool:
	if STONES.has(title):
		return stage(&"stones_remember") == 1 and not flag(StringName("stone:%s" % title))
	if title == LIGHT_LOOKOUT:
		return stage(&"light_on_water") == 1 and at_night
	if title == LIGHT_DOOR:
		return stage(&"light_on_water") == 2 and at_night
	if title in CLIMBER_CLUES:
		return stage(&"over_the_top") == 1 and not flag(StringName("climbers:%s" % title))
	if title in GLOWCAPS:
		return stage(&"glowcaps") == 1 and not flag(StringName("glowcap:%s" % title))
	if title in MILLSTREAM_FINDS:
		return stage(&"millstream") == 1 and not flag(StringName("stream:%s" % title))
	if LEDGER_CLUES.has(title):
		return stage(&"merchants_ledger") == 1 and not flag(StringName("ledger:%s" % title))
	if title == SATCHEL_TITLE:
		return stage(&"trees_remember") == 1
	if title == NAMES_LEDGER:
		return stage(&"foremans_names") == 1
	if title == THRONE_LEDGER:
		return stage(&"audience_throne") == 1
	if title == REEF_DIVE:
		return stage(&"old_reef") == 1 and at_night
	if SMUGGLER_CLUES.has(title):
		return stage(&"smugglers_route") == 1 and not flag(StringName("smuggler:%s" % title))
	return false


## This resident still has your free return card.
func gift_waiting(npc_id: StringName) -> bool:
	return WELCOME_GIFTS.has(npc_id) and not flag(StringName("gift:%s" % npc_id))


func clue_found(clue_id: StringName) -> bool:
	return flag(StringName("clue:%s" % clue_id))


## The HUD's quest lines, one per active quest ("" when nothing is active).
## Every line of the old tracker (all running quests and favours); tests read it.
func tracker_text() -> String:
	var lines: PackedStringArray = []
	for entry in journal():
		if not entry.done:
			lines.append("%s: %s" % [entry.title, entry.step])
	return "
".join(lines)


## The one quest or favour the HUD shows: the one picked in the journal
## (GameState.quest_flags "tracked"), else the newest running one; "" for none.
func tracked_text() -> String:
	var tracked: StringName = GameState.quest_flags.get(&"tracked", &"")
	if tracked == &"none":
		return ""
	var running := journal().filter(func(e: Dictionary) -> bool: return not e.done)
	for entry: Dictionary in running:
		if entry.id == tracked:
			return "%s
%s" % [entry.title, entry.step]
	if running.is_empty():
		return ""
	return "%s
%s" % [running[0].title, running[0].step]


## Picks the quest the HUD shows (`&"none"` shows nothing).
func track(id: StringName) -> void:
	GameState.quest_flags[&"tracked"] = id
	quest_changed.emit(id, stage(id))


func tracked_id() -> StringName:
	var tracked: StringName = GameState.quest_flags.get(&"tracked", &"")
	if tracked == &"none":
		return tracked
	var running := journal().filter(func(e: Dictionary) -> bool: return not e.done)
	for entry: Dictionary in running:
		if entry.id == tracked:
			return tracked
	return running[0].id if not running.is_empty() else &""


## The journal: every quest and favour you've taken on, newest first, as
## { "id", "title", "giver", "step", "done" }.
func journal() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	var order: Array = GameState.quest_flags.get(&"journal_order", [])
	var all: Array[Dictionary] = []
	for id: StringName in TITLES:
		var st := stage(id)
		if st == NOT_STARTED:
			continue
		all.append({ "id": id, "title": TITLES[id], "giver": GIVERS.get(id, ""), "done": st == DONE,
			"step": ABOUT.get(id, "") if st == DONE else _step(id) })
	for id: StringName in Errands.ERRANDS:
		var st := Errands.state(id)
		if st != Errands.ASKED and st != Errands.DONE:
			continue
		var who := Errands.npc_name(Errands.ERRANDS[id].npc)
		var key := StringName("errand:%s" % id)
		var step := ("ready to hand in to %s" % who) if Errands.is_met(id) else Errands.summary(id)
		all.append({ "id": key, "title": "A favour for %s" % who, "giver": who, "done": st == Errands.DONE,
			"step": ("Done: %s" % Errands.summary(id)) if st == Errands.DONE else step })
	# Newest first, in the order you took them on.
	all.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return order.find(a.id) > order.find(b.id))
	out.assign(all)
	return out


## Remembers when a quest or favour was taken on (journal order) and shows it.
func noted_start(id: StringName) -> void:
	var order: Array = GameState.quest_flags.get(&"journal_order", [])
	if not order.has(id):
		order.append(id)
		GameState.quest_flags[&"journal_order"] = order
	var tracked: StringName = GameState.quest_flags.get(&"tracked", &"")
	if tracked != &"none":
		GameState.quest_flags[&"tracked"] = id


## What a quest asks of you next ("" when it isn't running).
func _step(id: StringName) -> String:
	match id:
		&"unmarked_cargo":
			match stage(&"unmarked_cargo"):
				1:
					return "inspect the unmarked crates on the quay, west dock and pier (%d/3)" % _clues_found()
				2:
					return "report back to Bram"
		&"wens_boat":
			match stage(&"wens_boat"):
				1:
					return "find a sail, oars and rope (%d/3)" % _parts_found()
				2:
					return "bring the parts to Wen"
		&"trees_remember":
			match stage(&"trees_remember"):
				1:
					return "search the Hollow, the cave past Sorenda's moss gate"
				2:
					return "bring the satchel to Elder Moss"
		&"stones_remember":
			match stage(&"stones_remember"):
				1:
					return "read the three standing stones (%d/3)" % _stones_read()
				2:
					return "tell Aldous in Verdana what you read"
		&"light_on_water":
			match stage(&"light_on_water"):
				1:
					return "look through the headland telescope at Seabright after dark"
				2:
					return "find the bungalow that answered the light, after dark"
				3:
					return "tell Sparkle what you found"
		&"over_the_top":
			match stage(&"over_the_top"):
				1:
					return "search the Starfall Range for the climbers (%d/2)" % _climbers_found()
				2:
					return "tell Sven in Frisalle"
		&"glowcaps":
			match stage(&"glowcaps"):
				1:
					return "gather the blue glowcaps in the Hollow (%d/3)" % _glowcaps_found()
				2:
					return "bring the glowcaps to Juniper in Sorenda"
		&"millstream":
			match stage(&"millstream"):
				1:
					return "search the reeds along Verdana's millstream (%d/3)" % _millstream_found()
				2:
					return "bring what you found to Oda"
		&"beneath_dunes":
			match stage(&"beneath_dunes"):
				1:
					return "go down the North Shaft and find Ada in the bunks (the tally gate wants a Brass Tally Tag)"
				2:
					return "lead Ada out the crawl past the flooded workings, to Zahra at the Sunwell"
				3:
					return "tell Rafi in Duskara"
		&"foremans_names":
			match stage(&"foremans_names"):
				1:
					return "read the foreman's ledger of names in the North Shaft's lower office"
				2:
					return "bring the names to Hesper at the Cistern"
		&"old_reef":
			match stage(&"old_reef"):
				1:
					return "dive with Sparkle off the end of Seabright's diving pier, after dark"
				2:
					return "tell Sparkle what you saw on the reef"
		&"smugglers_route":
			match stage(&"smugglers_route"):
				1:
					return "read Halmeer's tide board, the salt house door and the barge's log in the sea cave (%d/3)" % _smuggler_found()
				2:
					return "tell Nessa at the cape light what you found"
		&"audience_throne":
			match stage(&"audience_throne"):
				1:
					return "read the Throne Ledger in Vetrassa's throne room"
				2:
					return "tell Freya on the palace steps what it says"
		&"merchants_ledger":
			match stage(&"merchants_ledger"):
				1:
					return "read the weigh house board, the great ledger and Bodo's papers (%d/3)" % _ledger_read()
				2:
					return "tell Mirren at the counting house what you found"
	return ""


## For the island map: the areas where an active quest or favour needs you next.
func map_goals() -> Array[String]:
	var out: Array[String] = []
	var add := func(zone: String) -> void:
		if not out.has(zone):
			out.append(zone)
	if stage(&"unmarked_cargo") in [1, 2]:
		add.call(WorldMap.KALMORA)
	if stage(&"wens_boat") in [1, 2]:
		add.call(WorldMap.KALMORA)
	match stage(&"trees_remember"):
		1:
			add.call(WorldMap.SORENDA_HOLLOW)
		2:
			add.call(WorldMap.SORENDA)
	match stage(&"stones_remember"):
		1:
			for title: String in STONES:
				if not flag(StringName("stone:%s" % title)):
					add.call(STONES[title])
		2:
			add.call(WorldMap.VERDANA)
	if stage(&"light_on_water") in [1, 2, 3]:
		add.call(WorldMap.SEABRIGHT)
	if stage(&"millstream") in [1, 2]:
		add.call(WorldMap.VERDANA)
	match stage(&"over_the_top"):
		1:
			add.call(WorldMap.STARFALL)
		2:
			add.call(WorldMap.FRISALLE)
	match stage(&"beneath_dunes"):
		1:
			add.call(WorldMap.DUSKARA_MINE)
		2:
			add.call(WorldMap.SIROTH)
		3:
			add.call(WorldMap.DUSKARA)
	match stage(&"foremans_names"):
		1:
			add.call(WorldMap.DUSKARA_MINE)
		2:
			add.call(WorldMap.DUSKARA)
	match stage(&"smugglers_route"):
		1, 2:
			add.call(WorldMap.HALMEER)
	if stage(&"old_reef") in [1, 2]:
		add.call(WorldMap.SEABRIGHT)
	match stage(&"audience_throne"):
		1:
			add.call(WorldMap.VETRASSA)
		2:
			add.call(WorldMap.VETRASSA)
	match stage(&"glowcaps"):
		1:
			add.call(WorldMap.SORENDA_HOLLOW)
		2:
			add.call(WorldMap.SORENDA)
	match stage(&"merchants_ledger"):
		1:
			for title: String in LEDGER_CLUES:
				if not flag(StringName("ledger:%s" % title)):
					add.call(WorldMap.FRISALLE)
		2:
			add.call(WorldMap.FRISALLE)
	for id: StringName in Errands.ERRANDS:
		if Errands.state(id) != Errands.ASKED:
			continue
		var e: Dictionary = Errands.ERRANDS[id]
		if Errands.is_met(id):
			add.call(e.zone)
		elif e.need == "kills":
			add.call(e.get("hunt", WorldMap.THORNVEIL))
		elif e.need == "visit":
			add.call(e.place)
		else:
			add.call(e.zone)
	return out


## Freya will tell you about the Throne Ledger once you've followed the carts far
## enough: two of the quests that trace them.
func audience_ready() -> bool:
	return AUDIENCE_NEEDS.filter(func(q: StringName) -> bool: return stage(q) == DONE).size() >= 2


func _smuggler_found() -> int:
	return SMUGGLER_CLUES.keys().filter(func(t: String) -> bool: return flag(StringName("smuggler:%s" % t))).size()


func _stones_read() -> int:
	return STONES.keys().filter(func(t: String) -> bool: return flag(StringName("stone:%s" % t))).size()


func _climbers_found() -> int:
	return CLIMBER_CLUES.filter(func(t: String) -> bool: return flag(StringName("climbers:%s" % t))).size()


func _glowcaps_found() -> int:
	return GLOWCAPS.filter(func(t: String) -> bool: return flag(StringName("glowcap:%s" % t))).size()


func _millstream_found() -> int:
	return MILLSTREAM_FINDS.filter(func(t: String) -> bool: return flag(StringName("stream:%s" % t))).size()


func _ledger_read() -> int:
	return LEDGER_CLUES.keys().filter(func(t: String) -> bool: return flag(StringName("ledger:%s" % t))).size()


func _parts_found() -> int:
	return BOAT_PARTS.filter(func(c: StringName) -> bool: return clue_found(c)).size()


func _clues_found() -> int:
	return CARGO_CLUES.filter(func(c: StringName) -> bool: return clue_found(c)).size()
