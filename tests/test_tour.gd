extends Node
## A tour of the whole demo: title screen, then every outdoor zone and every interior,
## with rivals running, a few seconds in each, at noon and at midnight. It fails if a
## scene doesn't load or the player isn't in it; script errors show in the output.
## Run it windowed too (without --headless) to exercise sound and the night grade:
## godot --path . res://tests/test_tour.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = true
	GameState.new_game(GameState.DEFAULT_RIVALS)
	get_tree().change_scene_to_file("res://scenes/ui/title_screen.tscn")
	await get_tree().create_timer(0.5).timeout
	_check("the title screen loads", get_tree().current_scene != null)
	var zones: Array = WorldMap.ZONES.keys()
	for hour in [12.0, 0.0]:
		TimeOfDay.set_hour(hour)
		for zone: String in zones:
			GameState.pending_spawn = &""
			get_tree().change_scene_to_file(zone)
			await get_tree().create_timer(1.5).timeout
			var scene := get_tree().current_scene
			var player := get_tree().get_first_node_in_group(&"player")
			_check("%s at %02d:00" % [zone.get_file().get_basename(), int(hour)],
				scene != null and scene.scene_file_path == zone and player != null)
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
