extends Node
## Edge exits are forgiving: each one by the edge of a zone's ground covers the whole
## opening and past it, and the rest of the edge is walled (Zone._wall_edges), so
## nothing walkable lies past the edge except inside an exit. No spawn may sit inside an exit (you'd bounce straight back out) or past
## the edge, and every place you can walk to inside the zone is on its ground.
## Run: godot --headless --path . res://tests/test_exits.tscn

const STEP := 8.0

var _failures := 0
var _checks := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	for path: String in WorldMap.ZONES:
		if "interiors/" in path:
			continue
		print("  zone ", path)
		var zone := await _load(path)
		if zone.interior:
			continue
		var label := String(zone.name)
		var rect := zone.ground_rect().grow(-4.0)
		var edge_exits: Array[ZoneExit] = []
		for node in zone.get_children():
			if node is ZoneExit and (node as ZoneExit).edge_side != Vector2.ZERO:
				edge_exits.append(node)
		for node in zone.get_children():
			if node is ZoneExit and not node.needs_interact:
				print("    %s %s side %s" % [label, node.name, (node as ZoneExit).edge_side])
		for marker in zone.get_node("Spawns").get_children():
			var p := (marker as Node2D).position
			_check("%s: spawn %s on the ground" % [label, marker.name], rect.has_point(p))
			for exit in edge_exits:
				_check("%s: spawn %s clear of %s" % [label, marker.name, exit.name], not _inside(exit, p))
		# Walk the zone from its first spawn: anywhere past the edge must be in an
		# exit's band (or the zone has an edge exit to send you to).
		var space := zone.get_world_2d().direct_space_state
		var start := (zone.get_node("Spawns").get_child(0) as Node2D).global_position
		var outside := 0
		for p in _flood(space, start, zone.ground_rect().grow(60)):
			if not zone.ground_rect().has_point(p) and not edge_exits.any(func(e: ZoneExit) -> bool: return _inside(e, p)):
				outside += 1
		_check("%s: nowhere walkable past the edge without an exit (%d points)" % [label, outside], outside == 0)
		print("  %s: %d edge exit(s), %d walkable points past the edge" % [label, edge_exits.size(), outside])
	print("%d checks" % _checks)
	print("PASS" if _failures == 0 and _checks > 5 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _inside(exit: ZoneExit, p: Vector2) -> bool:
	var collider := exit.get_node("CollisionShape2D") as CollisionShape2D
	var box := collider.shape as RectangleShape2D
	var centre := exit.position + collider.position
	return Rect2(centre - box.size / 2.0, box.size).has_point(p)


func _flood(space: PhysicsDirectSpaceState2D, start: Vector2, bounds: Rect2) -> Array[Vector2]:
	var query := PhysicsPointQueryParameters2D.new()
	query.collision_mask = 1
	var first := start.snapped(Vector2(STEP, STEP))
	var seen := { first: true }
	var out: Array[Vector2] = []
	var queue: Array[Vector2] = [first]
	var head := 0
	while head < queue.size() and out.size() < 150000:
		var p: Vector2 = queue[head]
		head += 1
		query.position = p
		if not bounds.has_point(p) or not space.intersect_point(query, 1).is_empty():
			continue
		out.append(p)
		for d in [Vector2(STEP, 0), Vector2(-STEP, 0), Vector2(0, STEP), Vector2(0, -STEP)]:
			var q: Vector2 = p + d
			if not seen.has(q):
				seen[q] = true
				queue.append(q)
	return out


func _load(path: String) -> Zone:
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame
	while get_tree().current_scene == null or get_tree().current_scene.scene_file_path != path:
		await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().physics_frame
	return get_tree().current_scene as Zone


func _check(label: String, ok: bool) -> void:
	_checks += 1
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
