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
}
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
}
const CARGO_CLUES: Array[StringName] = [&"crate_sand", &"crate_glove", &"crate_ledger"]
const CARGO_REWARD_GOLD := 40


func stage(id: StringName) -> int:
	return GameState.quest_flags.get(StringName("quest:%s" % id), NOT_STARTED)


func set_stage(id: StringName, value: int) -> void:
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
					return PackedStringArray(["Next time the light blinks, I'm swimming out after the rope. Don't tell the lifeguard."])
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
						lines.append("...And the Vetrassa factors are the Hoarder's family's people. The money your rival races on has been coming over my scales all winter.")
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
	if npc_id == &"oda" and Errands.state(&"oda_news") == Errands.DONE:
		match stage(&"millstream"):
			NOT_STARTED:
				return "!"
			2:
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
	if title in MILLSTREAM_FINDS and not flag(StringName("stream:%s" % title)):
		GameState.quest_flags[StringName("stream:%s" % title)] = true
		if stage(&"millstream") == 1:
			if _millstream_found() == MILLSTREAM_FINDS.size():
				set_stage(&"millstream", 2)
				EventBus.notify.emit("All three found. Take them to Oda")
			else:
				quest_changed.emit(&"millstream", 1)
				EventBus.notify.emit("What the Millstream Carries: %d of 3 found" % _millstream_found())
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


## This resident still has your free return card.
func gift_waiting(npc_id: StringName) -> bool:
	return WELCOME_GIFTS.has(npc_id) and not flag(StringName("gift:%s" % npc_id))


func clue_found(clue_id: StringName) -> bool:
	return flag(StringName("clue:%s" % clue_id))


## The HUD's quest lines, one per active quest ("" when nothing is active).
func tracker_text() -> String:
	var lines: PackedStringArray = []
	match stage(&"unmarked_cargo"):
		1:
			lines.append("%s: inspect the unmarked crates on the quay, west dock and pier (%d/3)" % [TITLES[&"unmarked_cargo"], _clues_found()])
		2:
			lines.append("%s: report back to Bram" % TITLES[&"unmarked_cargo"])
	match stage(&"wens_boat"):
		1:
			lines.append("%s: find a sail, oars and rope (%d/3)" % [TITLES[&"wens_boat"], _parts_found()])
		2:
			lines.append("%s: bring the parts to Wen" % TITLES[&"wens_boat"])
	match stage(&"trees_remember"):
		1:
			lines.append("%s: search the Hollow, the cave past Sorenda's moss gate" % TITLES[&"trees_remember"])
		2:
			lines.append("%s: bring the satchel to Elder Moss" % TITLES[&"trees_remember"])
	match stage(&"stones_remember"):
		1:
			lines.append("%s: read the three standing stones (%d/3)" % [TITLES[&"stones_remember"], _stones_read()])
		2:
			lines.append("%s: tell Aldous in Verdana what you read" % TITLES[&"stones_remember"])
	match stage(&"light_on_water"):
		1:
			lines.append("%s: look through the headland telescope at Seabright after dark" % TITLES[&"light_on_water"])
		2:
			lines.append("%s: find the bungalow that answered the light, after dark" % TITLES[&"light_on_water"])
		3:
			lines.append("%s: tell Sparkle what you found" % TITLES[&"light_on_water"])
	match stage(&"millstream"):
		1:
			lines.append("%s: search the reeds along Verdana's millstream (%d/3)" % [TITLES[&"millstream"], _millstream_found()])
		2:
			lines.append("%s: bring what you found to Oda" % TITLES[&"millstream"])
	match stage(&"merchants_ledger"):
		1:
			lines.append("%s: read the weigh house board, the great ledger and Bodo's papers (%d/3)" % [TITLES[&"merchants_ledger"], _ledger_read()])
		2:
			lines.append("%s: tell Mirren at the counting house what you found" % TITLES[&"merchants_ledger"])
	lines.append_array(Errands.tracker_lines())
	return "\n".join(lines)


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


func _stones_read() -> int:
	return STONES.keys().filter(func(t: String) -> bool: return flag(StringName("stone:%s" % t))).size()


func _millstream_found() -> int:
	return MILLSTREAM_FINDS.filter(func(t: String) -> bool: return flag(StringName("stream:%s" % t))).size()


func _ledger_read() -> int:
	return LEDGER_CLUES.keys().filter(func(t: String) -> bool: return flag(StringName("ledger:%s" % t))).size()


func _parts_found() -> int:
	return BOAT_PARTS.filter(func(c: StringName) -> bool: return clue_found(c)).size()


func _clues_found() -> int:
	return CARGO_CLUES.filter(func(c: StringName) -> bool: return clue_found(c)).size()
