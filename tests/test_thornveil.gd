extends Node
## Headless test of Thornveil's things to do: each chest pays out once and stays open
## when you come back, the Heartwood spring heals, Tobin at the camp trades, the zone's
## exits lead where the world map says, and the level map puts the plaza below the
## north terrace.
## Run: godot --headless --path . res://tests/test_thornveil.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var forest := await _load(WorldMap.THORNVEIL)
	var chests: Array[Chest] = []
	for node in forest.get_children():
		if node is Chest:
			chests.append(node)
	_check("three chests (%d)" % chests.size(), chests.size() == 3)
	var gold := GameState.currency
	var first := chests[0]
	first.open()
	_check("a chest pays out", GameState.currency == gold + first.gold and first.is_open())
	first.open()
	_check("and only once", GameState.currency == gold + first.gold)
	var opened := String(first.name)
	_finish_dialogue()

	var player := forest.get_node("Player") as Player
	player.health = 1
	var spring := forest.get_node("Spring") as HealingSpring
	player.global_position = spring.global_position + Vector2(0, 30)
	await get_tree().physics_frame
	var press := InputEventAction.new()
	press.action = &"interact"
	press.pressed = true
	spring._unhandled_input(press)
	_check("the Heartwood spring heals", player.health == player.max_health)

	var tobin := forest.get_node_or_null("Npc_tobin") as Npc
	_check("Tobin keeps camp and trades", tobin != null and not tobin.shop_stock.is_empty())

	for exit_name in ["ToKalmora", "ToSorenda", "ToLake", "ToGrove"]:
		var exit := forest.get_node_or_null(exit_name) as ZoneExit
		var edge_ok := false
		for edge in WorldMap.EDGES:
			if edge.from == WorldMap.THORNVEIL and exit and edge.to == exit.target_scene:
				edge_ok = edge.exit.distance_to(exit.position) < 4.0
		_check("%s matches the world map" % exit_name, edge_ok)

	var plaza := forest.level_at(forest.get_node("GreatTree").global_position + Vector2(0, 60))
	var north := forest.level_at(forest.get_node("Card_owl_quill").global_position)
	_check("the plaza (%d) sits below the north terrace (%d)" % [plaza, north], plaza >= 0 and north > plaza)

	_check_water(forest, "res://assets/sprites/tiles/thornveil/thornveil_water_mask.png")

	# Leave and come back: the opened chest is still open.
	var town := await _load(WorldMap.KALMORA)
	_check_water(town, "res://assets/sprites/tiles/kalmora2/kalmora_bay_mask.png")
	forest = await _load(WorldMap.THORNVEIL)
	_check("an opened chest stays open", (forest.get_node(opened) as Chest).is_open())
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


## Nobody walks on water: sample the zone's water (its wave mask, a few px in from
## the edge, away from decks and bridges, which the level map marks green) and every
## sample must be inside the World collision.
func _check_water(zone: Zone, mask_path: String) -> void:
	var mask := (load(mask_path) as Texture2D).get_image()
	var ground := zone.get_node("GroundTiles") as Sprite2D
	var origin := ground.global_position - Vector2(mask.get_size()) / 2.0
	var levels := zone.level_map.get_image() if zone.level_map else null
	var space := zone.get_world_2d().direct_space_state
	var query := PhysicsPointQueryParameters2D.new()
	query.collision_mask = 1
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var tested := 0
	var dry: Array[Vector2] = []
	for i in 20000:
		if tested >= 400:
			break
		var p := Vector2i(rng.randi_range(8, mask.get_width() - 9), rng.randi_range(8, mask.get_height() - 9))
		var inside := true
		for d in [Vector2i(0, 0), Vector2i(8, 0), Vector2i(-8, 0), Vector2i(0, 8), Vector2i(0, -8)]:
			if mask.get_pixelv(p + d).a < 0.5:
				inside = false
		if not inside:
			continue
		var world := origin + Vector2(p)
		if levels:
			var cell := Vector2i(((world - zone.level_origin) / zone.level_cell).floor())
			if cell.x >= 0 and cell.y >= 0 and cell.x < levels.get_width() and cell.y < levels.get_height() \
					and levels.get_pixelv(cell).g > 0.5:
				continue                                  # a deck or bridge over the water
		tested += 1
		query.position = world
		if space.intersect_point(query, 1).is_empty():
			dry.append(world)
	_check("%s: water blocks (%d of %d samples open, e.g. %s)" % [zone.name, dry.size(), tested,
		str(dry.slice(0, 3))], tested > 50 and dry.is_empty())


## Reads through whatever the dialogue box is showing, the way a player would.
func _finish_dialogue() -> void:
	var box := get_tree().get_first_node_in_group(&"dialogue_box") as DialogueBox
	var press := InputEventAction.new()
	press.action = &"interact"
	press.pressed = true
	for i in 20:
		if box == null or not box.is_open():
			return
		box._unhandled_input(press)


func _load(path: String) -> Zone:
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame
	while get_tree().current_scene == null or get_tree().current_scene.scene_file_path != path:
		await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().physics_frame
	return get_tree().current_scene as Zone


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
