class_name Ending
extends RefCounted
## The end of the race. The first collector to stand in Vetrassa with the whole set
## wins: the player by handing it to the Steward in the throne room (then the old
## card player from the plains fire walks in, and he is the King), a rival by
## reaching Vetrassa with it (RivalDirector). The player's ending branches on what
## they learned about the Duskara mine (`choices`): rule as kings always have; keep
## the mine but pay the laborers (any of the mine quests done); or close the North
## Shaft (both mine quests and "An Audience Before the Throne" done). The ending
## scene (`SCENE`, scripts/ui/ending_screen.gd) reads quest_flags "ending" and
## "winner" and tells how it went, then goes back to the title.

const SCENE := "res://scenes/ui/ending.tscn"
const RULE := &"rule"
const WAGES := &"wages"
const CLOSE := &"close"
const LOST := &"lost"
const KING_FRAMES := "res://assets/sprites/npcs/loki/loki_frames.tres"
## Where the King stands up from beside the throne (throne room local).
const KING_SPOT := Vector2(128, 124)

## Tests turn this off so finishing the race doesn't leave the test scene.
static var show_scene := true


static func has_set(collector: StringName) -> bool:
	return GameState.collection(collector).has_complete_set(CardDatabase.final_set())


static func is_over() -> bool:
	return GameState.quest_flags.get(&"race_over", false)


## The endings open to the player now, in the order they're offered.
static func choices() -> Array[Dictionary]:
	var out: Array[Dictionary] = [{ "id": RULE, "label": "Rule as kings always have" }]
	var shaft := Quests.stage(&"beneath_dunes") == Quests.DONE
	var names := Quests.stage(&"foremans_names") == Quests.DONE
	if shaft or names:
		out.append({ "id": WAGES, "label": "Keep the mine, but pay the laborers" })
	if shaft and names and Quests.stage(&"audience_throne") == Quests.DONE:
		out.append({ "id": CLOSE, "label": "Close the North Shaft" })
	return out


## The player has handed the Steward the whole set: the King comes out, says who
## he is and what the prize was, and asks what they'll do with it.
static func crown(tree: SceneTree) -> void:
	if is_over():
		return
	GameState.quest_flags[&"crowned"] = true
	var portrait: Texture2D = null
	var frames := load(KING_FRAMES) as SpriteFrames
	if frames:
		portrait = DialogueBox.portrait_from(frames)
	_king_steps_out(tree, frames)
	var lines := PackedStringArray([
		"Don't kneel. Please. My knees haven't let me do it in years, and I'd hate to be outdone.",
		"You know me. The old fool by the travellers' fire on the plains, losing at cards on purpose. I watch every race from the roadside. It's the only way to see who people are.",
		"I am Loki, King of Virelia Isle. This was my chair. Every race, the King steps down for whoever can gather the whole island in their hands.",
		"Riches beyond your wildest dreams, they tell you. It's the island itself. The towns, the roads, the gates, the Guard. All of it. That was always the prize.",
	])
	if Quests.stage(&"beneath_dunes") == Quests.DONE or Quests.stage(&"foremans_names") == Quests.DONE:
		lines.append("And you've been down the shaft, or read the names. Then you know what the set is made of. My wife counts it out in Duskara. My father counted it before her. Now it's yours to count.")
	else:
		lines.append("Everything on this island is paid for somewhere. Read the ledger by the throne tonight, and you'll see where. My father read it. His father read it.")
	DialogueBox.say(tree, "Loki", lines, func() -> void: _ask(tree, portrait), portrait)


static func _ask(tree: SceneTree, portrait: Texture2D) -> void:
	var options := PackedStringArray()
	var picks := choices()
	for c: Dictionary in picks:
		options.append(c.label)
	DialogueBox.ask(tree, "Loki", "So. What will you do with Virelia?", options,
		func(i: int) -> void: _answer(tree, picks[clampi(i, 0, picks.size() - 1)].id, portrait), portrait)


static func _answer(tree: SceneTree, id: StringName, portrait: Texture2D) -> void:
	var reply: PackedStringArray
	match id:
		CLOSE:
			reply = PackedStringArray(["Close it. Hm. Do you know, nobody has ever said that to me in this room.",
				"The island will be poorer for it. The Company will scream, and the Duke will leave, and my wife... my wife will unlock the gate herself, I think. She's been waiting for someone to order her to.",
				"Here. The crown is heavier than it looks. Most things are."])
		WAGES:
			reply = PackedStringArray(["Wages. Coin, not scrip. No children down the shaft. That's more than I ever ordered.",
				"It won't be enough, you know. It never is. But it's more than enough to sleep on, some nights.",
				"Here. The crown is heavier than it looks. Most things are."])
		_:
			reply = PackedStringArray(["As kings always have. Yes. That's what I said, too, at your age.",
				"The seam will be worked, the carts will come over the mountain, and the island will be beautiful. It always is, from up here.",
				"Here. The crown is heavier than it looks. You'll stop noticing."])
	DialogueBox.say(tree, "Loki", reply, func() -> void: finish(tree, id), portrait)


## The race is over: remember how, and show the ending.
static func finish(tree: SceneTree, id: StringName, winner: StringName = GameState.PLAYER) -> void:
	if is_over():
		return
	GameState.quest_flags[&"race_over"] = true
	GameState.quest_flags[&"ending"] = id
	GameState.quest_flags[&"winner"] = winner
	EventBus.race_finished.emit(winner, id)
	if show_scene and tree:
		Transition.go(SCENE)


## A rival reached Vetrassa with the whole set: the race is lost.
static func rival_wins(tree: SceneTree, rival: StringName) -> void:
	if is_over():
		return
	finish(tree, LOST, rival)


static func _king_steps_out(tree: SceneTree, frames: SpriteFrames) -> void:
	var zone := tree.current_scene as Zone
	if zone == null or frames == null or zone.scene_file_path != WorldMap.VETRASSA_PALACE:
		return
	var king := (load("res://scenes/characters/npc.tscn") as PackedScene).instantiate() as Npc
	king.name = "King"
	king.npc_id = &"loki_king"
	king.display_name = "Loki"
	king.sprite_frames = frames
	king.position = KING_SPOT
	king.modulate.a = 0.0
	var parent := zone.get_node_or_null("YSort")
	(parent if parent else zone).add_child(king)
	king.create_tween().tween_property(king, "modulate:a", 1.0, 0.8)
	var player := tree.get_first_node_in_group(&"player") as Node2D
	if player:
		king.facing = king.global_position.direction_to(player.global_position)
