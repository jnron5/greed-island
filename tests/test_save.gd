extends Node
## Save and continue: a run saved in Sorenda with cards in every state, gold, items,
## quest and favour progress, an opened gate, an opened chest and the hour comes
## back exactly, in the same zone at the same spot.
## Run: godot --headless --path . res://tests/test_save.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	SaveGame.path = "user://test_save.dat"
	SaveGame.delete()
	var rivals: Array[StringName] = [&"hoarder", &"runner"]
	GameState.new_game(rivals)
	GameState.add_loose_card(GameState.PLAYER, &"tide_bell")
	GameState.add_loose_card(GameState.PLAYER, &"salt_compass")
	GameState.bind_card(GameState.PLAYER, &"salt_compass")
	GameState.add_loose_card(&"runner", &"thorn_sprig")
	GameState.add_currency(123)
	GameState.add_item(&"healers_tonic", 3)
	Quests.set_stage(&"trees_remember", 1)
	GameState.quest_flags[&"errand:pip_bread"] = Errands.ASKED
	GameState.opened_gates[&"kalmora_north_gate"] = GameState.PLAYER
	GameState.collected_pickups["res://scenes/world/kalmora.tscn:Card_sea_glass"] = true
	TimeOfDay.set_hour(21.5)
	get_tree().change_scene_to_file(WorldMap.SORENDA)
	await get_tree().process_frame
	await get_tree().process_frame
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	player.global_position = Vector2(0, 120)
	SaveGame.save(true)
	_check("a save was written", SaveGame.has_save())

	# Wipe everything, then continue.
	GameState.new_game(GameState.DEFAULT_RIVALS)
	TimeOfDay.set_hour(8.0)
	get_tree().change_scene_to_file(WorldMap.KALMORA)
	await get_tree().process_frame
	await get_tree().process_frame
	_check("continuing works", SaveGame.continue_game())
	for i in 30:
		await get_tree().process_frame
	var scene := get_tree().current_scene
	_check("back in Sorenda", scene != null and scene.scene_file_path == WorldMap.SORENDA)
	player = get_tree().get_first_node_in_group(&"player") as Node2D
	_check("standing where you were (%s)" % (player.global_position if player else Vector2.INF), player != null and player.global_position.distance_to(Vector2(0, 120)) < 1.0)
	var col := GameState.collection(GameState.PLAYER)
	_check("the rivals you picked", GameState.active_rivals == rivals)
	_check("loose and bound cards", col.count(&"tide_bell", CardCollection.State.LOOSE) == 1
		and col.count(&"salt_compass", CardCollection.State.BOUND) == 1)
	_check("the rivals' cards", GameState.collection(&"runner").count(&"thorn_sprig") == 1)
	_check("gold", GameState.currency == GameState.STARTING_GOLD + 123)
	_check("satchel", GameState.item_count(&"healers_tonic") == 3 and GameState.item_count(&"bread") == 2)
	_check("quests and favours", Quests.stage(&"trees_remember") == 1 and Errands.state(&"pip_bread") == Errands.ASKED)
	_check("gates and chests", GameState.opened_gates.has(&"kalmora_north_gate")
		and GameState.collected_pickups.has("res://scenes/world/kalmora.tscn:Card_sea_glass"))
	_check("the hour", absf(TimeOfDay.hour - 21.5) < 0.01)
	SaveGame.delete()
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
