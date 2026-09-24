extends Node
## Multilevel Kalmora: the level map, routes that climb stairs, and fights that
## don't reach across cliffs.
## Run: godot --headless --path . res://tests/test_elevation.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	get_tree().change_scene_to_file(WorldMap.KALMORA)
	while get_tree().current_scene == null:
		await get_tree().process_frame
	var town := get_tree().current_scene as Zone
	while not town._nav_ready:
		await get_tree().physics_frame

	_check("quay is level 1", town.level_at(town.to_global(Vector2(-300, 60))) == 1)
	_check("market terrace is level 2", town.level_at(town.to_global(Vector2(-300, -250))) == 2)
	_check("upper town is level 3", town.level_at(town.to_global(Vector2(-300, -800))) == 3)
	_check("the cliff between them is no level", town.level_at(town.to_global(Vector2(-300, -150))) == -1)

	# A route from the harbor to the upper town has to use the stairs.
	var from := (town.get_node("Spawns/from_tavern") as Node2D).global_position  # quay, outside the tavern
	var to := town.to_global(Vector2(-450, -600))
	var path := town.find_path(from, to)
	_check("there is a route from the quay to the upper town", path.size() > 2
		and path[path.size() - 1].distance_to(to) < 24.0)
	var levels_seen := {}
	var uses_stairs := false
	for p in path:
		var lv := town.level_at(p)
		levels_seen[lv] = true
		uses_stairs = uses_stairs or lv == -1
	_check("it climbs through levels 1, 2 and 3 via stairs", levels_seen.has(1) and levels_seen.has(2)
		and levels_seen.has(3) and uses_stairs)

	# A sword swung on the market terrace can't hit a dummy on the quay below.
	var dummy := town.get_node("TrainingDummy1") as TrainingDummy
	var hit := Hitbox.new()
	hit.source_id = GameState.PLAYER
	hit.damage = 1
	hit.level = 2
	town.add_child(hit)
	var hp := dummy.health
	dummy.hurtbox._on_area_entered(hit)
	_check("no hits across a cliff", dummy.health == hp)
	hit.level = 1
	dummy.hurtbox._on_area_entered(hit)
	_check("same-level hits land", dummy.health == hp - 1)

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
