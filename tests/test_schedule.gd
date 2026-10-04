extends Node
## Residents keep hours: some are only out by day (Bram drinks in the Salted Lantern at
## night, Rosa and Pip go home), some spend the night somewhere else in town (Mirela
## keeps watch on the quay, Aldous watches the sky from the green); arriving at either
## time finds them in the right place, and at dusk they walk there.
## Run: godot --headless --path . res://tests/test_schedule.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)

	TimeOfDay.set_hour(12.0)
	var town := await _load(WorldMap.KALMORA)
	var bram := town.get_node("Npc_bram") as Npc
	var mirela := town.get_node("Npc_mirela") as Npc
	var by_day := mirela.position
	_check("by day Bram works the quay", bram.visible and not bram.get_node("CollisionShape2D").disabled)
	var tavern := await _load(WorldMap.KALMORA_TAVERN)
	_check("and isn't in the tavern", not (tavern.get_node("Npc_bram") as Npc).visible)

	TimeOfDay.set_hour(22.0)
	town = await _load(WorldMap.KALMORA)
	bram = town.get_node("Npc_bram") as Npc
	mirela = town.get_node("Npc_mirela") as Npc
	_check("at night Bram's off the quay", not bram.visible)
	_check("Rosa's gone home", not (town.get_node("Npc_baker") as Npc).visible)
	_check("Mirela keeps watch somewhere else", mirela.has_night_spot and mirela.position.distance_to(mirela.night_spot) < 1.0
		and mirela.position.distance_to(by_day) > 20.0)
	tavern = await _load(WorldMap.KALMORA_TAVERN)
	var drinking := tavern.get_node("Npc_bram") as Npc
	_check("Bram's in the Salted Lantern", drinking.visible and not drinking.get_node("CollisionShape2D").disabled)

	# Dusk while you're there: Aldous walks out to his night spot on the green.
	TimeOfDay.set_hour(19.9)
	var verdana := await _load(WorldMap.VERDANA)
	var aldous := verdana.get_node("Npc_aldous") as Npc
	var start := aldous.position
	TimeOfDay.set_hour(20.5)
	for i in 600:
		await get_tree().physics_frame
	_check("at dusk Aldous sets off for his night spot", aldous.position.distance_to(aldous.night_spot)
		< start.distance_to(aldous.night_spot) - 20.0)
	TimeOfDay.set_hour(12.0)
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _load(path: String) -> Zone:
	get_tree().change_scene_to_file(path)
	for i in 300:
		await get_tree().process_frame
		if get_tree().current_scene != null and get_tree().current_scene.scene_file_path == path:
			await get_tree().physics_frame
			await get_tree().physics_frame
			return get_tree().current_scene as Zone
	return null


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
