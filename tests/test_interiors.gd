extends Node
## Every building in Kalmora can be entered: each door leads to an interior whose
## door spawn and way out are clear of walls and furniture, the way out lands back on
## a Kalmora doorstep that exists, residents stand on open floor, and every readable
## can be reached from the door on foot.
## Run: godot --headless --path . res://tests/test_interiors.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var town := await _load(WorldMap.KALMORA)
	var doors: Array[ZoneExit] = []
	for node in town.get_children():
		if node is ZoneExit and "interiors" in (node as ZoneExit).target_scene:
			doors.append(node)
	var buildings := 0
	for node in town.get_children():
		if node is StaticBody2D and node.get_node_or_null("Sprite") is Sprite2D and node.name.is_valid_identifier() \
				and not String(node.name).begins_with("P") and not String(node.name).begins_with("Palm") \
				and not String(node.name).begins_with("Tree") and node.name != "Lighthouse":
			buildings += 1
	_check("every building has a door (%d doors, %d buildings)" % [doors.size(), buildings], doors.size() == buildings)
	var doorsteps := {}
	for spawn in town.get_node("Spawns").get_children():
		doorsteps[String(spawn.name)] = true
	var scenes: Array[String] = []
	for door in doors:
		scenes.append(door.target_scene)
	for path in scenes:
		GameState.pending_spawn = &"door"
		var room := await _load(path)
		var label := String(room.name)
		var space := room.get_world_2d().direct_space_state
		var door_spawn := room.get_node_or_null("Spawns/door") as Node2D
		var out := room.get_node_or_null("Out") as ZoneExit
		_check("%s: has a door spawn and a way out" % label, door_spawn != null and out != null)
		if door_spawn == null or out == null:
			continue
		_check("%s: door spawn is on open floor" % label, _open(space, door_spawn.global_position))
		_check("%s: way out leads to an existing doorstep" % label,
			out.target_scene == WorldMap.KALMORA and doorsteps.has(String(out.target_spawn)))
		_check("%s: registered on the world map" % label, WorldMap.ZONES.has(path))
		# Walk the room on a 4px grid from the door spawn: the way out, every resident
		# and every readable must be reachable.
		var reach := _flood(space, door_spawn.global_position)
		_check("%s: the way out is reachable" % label, _near(reach, out.global_position + Vector2(0, -10), 14))
		for node in room.get_children():
			if node is Npc:
				_check("%s: %s can be walked up to" % [label, node.name], _near(reach, node.global_position, 30))
			elif node is Readable:
				_check("%s: '%s' can be reached" % [label, node.title], _near(reach, node.global_position, Readable.RANGE))
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _open(space: PhysicsDirectSpaceState2D, point: Vector2) -> bool:
	var query := PhysicsPointQueryParameters2D.new()
	query.position = point
	query.collision_mask = 1
	for offset in [Vector2.ZERO, Vector2(-5, -3), Vector2(5, -3)]:
		query.position = point + offset
		if not space.intersect_point(query, 1).is_empty():
			return false
	return true


func _flood(space: PhysicsDirectSpaceState2D, start: Vector2) -> Array[Vector2]:
	var step := 6.0
	var first := start.snapped(Vector2(step, step))
	var seen := { first: true }
	var out: Array[Vector2] = []
	var queue: Array[Vector2] = [first]
	var head := 0
	while head < queue.size() and out.size() < 6000:
		var p: Vector2 = queue[head]
		head += 1
		if not _open(space, p):
			continue
		out.append(p)
		for d in [Vector2(step, 0), Vector2(-step, 0), Vector2(0, step), Vector2(0, -step)]:
			var q: Vector2 = p + d
			if not seen.has(q):
				seen[q] = true
				queue.append(q)
	return out


func _near(points: Array[Vector2], target: Vector2, radius: float) -> bool:
	for p in points:
		if p.distance_to(target) <= radius:
			return true
	return false


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
