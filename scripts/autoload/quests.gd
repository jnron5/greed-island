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
}
## Sorenda: Pell found a child's boot near the Hollow; what's in there is the proof.
const SATCHEL_TITLE := "A satchel in the moss"
const TREES_REWARD_GOLD := 50
## Elder Moss's own card, for bringing the child's things home.
const TREES_REWARD_CARD := &"sorenda_star_map"
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
						"The moss gate in front of it needs a card to open, and I haven't got one to spare. You might.",
						"Something big has moved in down there this year. We hear it at night. Whatever's in there, somebody small went in first. Please. Go and look.",
					])
				1:
					return PackedStringArray(["The Hollow's up the path, north-east of the green, through the moss gate and down under the roots. Mind whatever's living in it."])
				2:
					return PackedStringArray(["You found something. I can see it on you. Take it to Elder Moss. She keeps the names."])
				DONE:
					return PackedStringArray(["Moss carved a new notch. Not low down, this time. Up where the grown ones go. For whoever finds that child."])
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
		&"mirela":
			if stage(&"unmarked_cargo") in [1, 2]:
				return PackedStringArray([
					"Unmarked crates? I don't know what Bram's been telling you.",
					"Everything on my quay is stamped. Everything.",
				])
	return PackedStringArray()


## "!" = has something for you, "?" = waiting on you to report back.
func marker_for(npc_id: StringName) -> String:
	if npc_id == &"pell" and stage(&"trees_remember") == NOT_STARTED:
		return "!"
	if npc_id == &"moss" and stage(&"trees_remember") == 2:
		return "?"
	if npc_id == &"bram":
		match stage(&"unmarked_cargo"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	return ""


func talked_to(npc_id: StringName) -> void:
	if npc_id == &"pell" and stage(&"trees_remember") == NOT_STARTED:
		set_stage(&"trees_remember", 1)
		EventBus.notify.emit("Quest started: What the Trees Remember")
		return
	if npc_id == &"moss" and stage(&"trees_remember") == 2:
		GameState.add_item(&"healers_tonic", 2)
		GameState.add_currency(TREES_REWARD_GOLD)
		GameState.add_loose_card(GameState.PLAYER, TREES_REWARD_CARD)
		GameState.quest_flags[&"knows_tag_117"] = true
		set_stage(&"trees_remember", DONE)
		EventBus.notify.emit("Quest complete: What the Trees Remember (+%d gold, 2 Healer's Tonics, Sorenda Star Map)" % TREES_REWARD_GOLD)
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
func read(title: String) -> void:
	if title == SATCHEL_TITLE and stage(&"trees_remember") in [NOT_STARTED, 1]:
		set_stage(&"trees_remember", 2)
		EventBus.notify.emit("Take what you found to Elder Moss")


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
	match stage(&"trees_remember"):
		1:
			lines.append("%s: search the Hollow, the cave past Sorenda's moss gate" % TITLES[&"trees_remember"])
		2:
			lines.append("%s: bring the satchel to Elder Moss" % TITLES[&"trees_remember"])
	lines.append_array(Errands.tracker_lines())
	return "\n".join(lines)


func _clues_found() -> int:
	return CARGO_CLUES.filter(func(c: StringName) -> bool: return clue_found(c)).size()
