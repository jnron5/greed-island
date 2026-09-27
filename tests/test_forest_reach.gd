extends Node
## The forest zones dressed by scripts/tools/build_forest.py stay fully walkable:
## from the first spawn marker, every card, every zone exit, every spawn marker and
## every rival spot can be reached on foot (trees, rocks and logs only ever
## decorate; they never wall anything off). Gated exits count as reachable up to
## the gate.
## Run: godot --headless --path . res://tests/test_forest_reach.tscn

const ZONES := ["res://scenes/world/thornveil.tscn", "res://scenes/world/sorenda.tscn"]
const STEP := 8.0

var _failures := 0
var _checks := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	for path in ZONES:
		var zone := await _load(path)
		var space := zone.get_world_2d().direct_space_state
		var start := (zone.get_node("Spawns").get_child(0) as Node2D).global_position
		var reach := _flood(space, start)
		var label := String(zone.name)
		_check("%s: the flood covers the zone (%d points)" % [label, reach.size()], reach.size() > 3000)
		for node in zone.get_children():
			var target := ""
			if node is CardPickup and (node as CardPickup).behind_gate == &"":
				target = "card " + String(node.card_id)
			elif node is ZoneExit:
				target = "exit " + String(node.name)
			elif node is Npc:
				target = "resident " + String(node.name)
			if target != "":
				_check("%s: %s reachable" % [label, target], _near(reach, node.global_position, 30))
		for group in ["Spawns", "RivalSpots"]:
			for marker in zone.get_node(group).get_children():
				_check("%s: %s/%s reachable" % [label, group, marker.name], _near(reach, marker.global_position, 16))
	print("%d checks" % _checks)
	print("PASS" if _failures == 0 and _checks > 5 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _open(space: PhysicsDirectSpaceState2D, point: Vector2) -> bool:
	var query := PhysicsPointQueryParameters2D.new()
	query.collision_mask = 1
	for offset in [Vector2.ZERO, Vector2(-5, -3), Vector2(5, -3)]:
		query.position = point + offset
		if not space.intersect_point(query, 1).is_empty():
			return false
	return true


func _flood(space: PhysicsDirectSpaceState2D, start: Vector2) -> Array[Vector2]:
	var first := start.snapped(Vector2(STEP, STEP))
	var seen := { first: true }
	var out: Array[Vector2] = []
	var queue: Array[Vector2] = [first]
	var head := 0
	while head < queue.size() and out.size() < 60000:
		var p: Vector2 = queue[head]
		head += 1
		if not _open(space, p):
			continue
		out.append(p)
		for d in [Vector2(STEP, 0), Vector2(-STEP, 0), Vector2(0, STEP), Vector2(0, -STEP)]:
			var q: Vector2 = p + d
			if not seen.has(q):
				seen[q] = true
				queue.append(q)
	return out


func _near(points: Array[Vector2], target: Vector2, radius: float) -> bool:
	for p in points:
		if p.distance_squared_to(target) <= radius * radius:
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
	_checks += 1
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
