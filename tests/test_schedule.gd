extends Node
## Residents keep hours: Kalmora comes out to its Lantern Night party in the fountain
## square after dark (folk who keep to their houses by day too) till five, when Bram
## takes a last drink in the Salted Lantern; others spend the night somewhere else
## (Aldous watches the sky from the green); arriving at any time finds them in the
## right place, and at dusk they walk there.
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

	# Lantern Night: after dark the town is out in the fountain square till two.
	TimeOfDay.set_hour(22.0)
	town = await _load(WorldMap.KALMORA)
	bram = town.get_node("Npc_bram") as Npc
	mirela = town.get_node("Npc_mirela") as Npc
	var rosa := town.get_node("Npc_baker") as Npc
	var nonna := town.get_node("Npc_nonna") as Npc
	_check("at night Bram's at the party", bram.visible and bram.position.distance_to(bram.night_spot) < 30.0)
	_check("so is Rosa", rosa.visible and rosa.position.distance_to(rosa.night_spot) < 30.0)
	_check("Nonna comes out for it", nonna.visible and not nonna.get_node("CollisionShape2D").disabled)
	_check("Mirela keeps half an eye on the quay from the square", mirela.has_night_spot
		and mirela.position.distance_to(mirela.night_spot) < 30.0 and mirela.position.distance_to(by_day) > 20.0)
	_check("partygoers call out", not bram.chatter.is_empty() and not bram.night_lines.is_empty())
	tavern = await _load(WorldMap.KALMORA_TAVERN)
	_check("the tavern's quiet while the square's busy", not (tavern.get_node("Npc_bram") as Npc).visible)
	var nonna_home := await _load("res://scenes/world/interiors/kalmora_nonna_house.tscn")
	_check("and Nonna's not home", not (nonna_home.get_node("Npc_nonna") as Npc).visible)
	TimeOfDay.set_hour(5.5)
	town = await _load(WorldMap.KALMORA)
	_check("after five the square empties", not (town.get_node("Npc_bram") as Npc).visible)
	tavern = await _load(WorldMap.KALMORA_TAVERN)
	var drinking := tavern.get_node("Npc_bram") as Npc
	_check("and Bram has one last drink in the Salted Lantern", drinking.visible and not drinking.get_node("CollisionShape2D").disabled)

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
