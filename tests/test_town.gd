extends Node
## Kalmora town life: talking to Bram through the real dialogue box starts
## "The Unmarked Cargo", the quay's crates advance it, the reward pays out, and
## interiors round-trip through their doors.
## Run: godot --headless --path . res://tests/test_town.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var town := await _load(WorldMap.KALMORA)
	var player := town.get_node("Player") as Player
	var bram := town.get_node("Npc_bram") as Npc

	_check("Bram has a quest for you", Quests.marker_for(&"bram") == "!")
	bram.talk(player)
	var box := get_tree().get_first_node_in_group(&"dialogue_box") as DialogueBox
	_check("talking opens the dialogue box", box.is_open() and GameState.menus_open > 0)
	await _read_all(box)
	_check("finishing the conversation starts the quest", Quests.stage(&"unmarked_cargo") == 1
		and not box.is_open() and GameState.menus_open == 0)
	_check("the HUD tracks it", "0/3" in Quests.tracker_text())

	var gold := GameState.currency
	for clue in Quests.CARGO_CLUES:
		var said := Quests.inspect(clue)
		_check("crate %s tells you something" % clue, said.size() == 1 and said[0].length() > 20)
	_check("all three crates checked: report back", Quests.stage(&"unmarked_cargo") == 2 and Quests.marker_for(&"bram") == "?")
	bram.talk(player)
	await _read_all(box)
	_check("reporting back completes it", Quests.stage(&"unmarked_cargo") == Quests.DONE)
	_check("reward: gold and a Second Wind", GameState.currency == gold + Quests.CARGO_REWARD_GOLD
		and GameState.collection(GameState.PLAYER).count(&"second_wind") == 1)

	# Into the tavern and back out onto its doorstep.
	GameState.pending_spawn = &"door"
	var tavern := await _load(WorldMap.KALMORA_TAVERN)
	var inside := tavern.get_node("Player") as Node2D
	_check("inside the tavern at its door", inside.global_position.is_equal_approx((tavern.get_node("Spawns/door") as Node2D).global_position))
	_check("Otto is behind the bar", tavern.get_node_or_null("Npc_otto") != null)
	_check("indoors is a safe zone", tavern.interior)
	var exit := tavern.get_node("Out") as ZoneExit
	GameState.pending_spawn = exit.target_spawn
	town = await _load(exit.target_scene)
	var outside := town.get_node("Player") as Node2D
	_check("back out on the tavern doorstep", outside.global_position.is_equal_approx((town.get_node("Spawns/from_tavern") as Node2D).global_position))

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _load(path: String) -> Zone:
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame
	while get_tree().current_scene == null or get_tree().current_scene.scene_file_path != path:
		await get_tree().process_frame
	await get_tree().physics_frame
	return get_tree().current_scene as Zone


## Presses interact until the conversation ends (first press skips typing).
func _read_all(box: DialogueBox) -> void:
	var guard := 0
	while box.is_open() and guard < 40:
		guard += 1
		var press := InputEventAction.new()
		press.action = &"interact"
		press.pressed = true
		box._unhandled_input(press)
		await get_tree().process_frame


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
