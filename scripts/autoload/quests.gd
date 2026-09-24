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
	match npc_id:
		&"bram":
			match stage(&"unmarked_cargo"):
				NOT_STARTED:
					return PackedStringArray([
						"Oi, cloak. You're one of those card racers, aren't you?",
						"Three crates came in on the night tide. No manifest. No harbor stamp. Nothing.",
						"Harbormaster says that's none of my business. Makes it my business, if you ask me.",
						"Take a look at 'em for me? They're stacked by the jetty. Just look. Don't open anything that bites.",
					])
				1:
					return PackedStringArray(["Three crates, by the jetty. I'll be here, pretending to coil rope. (%d/3 checked)" % _clues_found()])
				2:
					return PackedStringArray([
						"Desert sand in the straw... a glove that small... and 'D.M.' on a ledger scrap?",
						"Duskara. Has to be. There's nothing out that way but dunes and that old mine they say closed years ago.",
						"...Keep this between us. Here, for your trouble.",
						"If anyone asks, you were helping me count barrels.",
					])
				DONE:
					return PackedStringArray(["Barrel, barrel, barrel. Very normal harbor. Nothing to see."])
		&"mirela":
			if stage(&"unmarked_cargo") in [1, 2]:
				return PackedStringArray([
					"Unmarked crates? I don't know what Bram's been telling you.",
					"Everything on my quay is stamped. Everything.",
				])
	return PackedStringArray()


## "!" = has something for you, "?" = waiting on you to report back.
func marker_for(npc_id: StringName) -> String:
	if npc_id == &"bram":
		match stage(&"unmarked_cargo"):
			NOT_STARTED:
				return "!"
			2:
				return "?"
	return ""


func talked_to(npc_id: StringName) -> void:
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


func clue_found(clue_id: StringName) -> bool:
	return flag(StringName("clue:%s" % clue_id))


## One line for the HUD, or "" when nothing is active.
func tracker_text() -> String:
	match stage(&"unmarked_cargo"):
		1:
			return "%s: inspect the unmarked crates by the jetty (%d/3)" % [TITLES[&"unmarked_cargo"], _clues_found()]
		2:
			return "%s: report back to Bram" % TITLES[&"unmarked_cargo"]
	return ""


func _clues_found() -> int:
	return CARGO_CLUES.filter(func(c: StringName) -> bool: return clue_found(c)).size()
