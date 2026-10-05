extends Node
## The forest zones dressed by scripts/tools/build_forest.py, and the regions past
## Kalmora's west gate (build_region.py), stay fully walkable: from the first spawn
## marker, every card, chest, readable, resident, zone exit, spawn marker and rival
## spot can be reached on foot (trees, rocks and logs only ever
## decorate; they never wall anything off). Gated exits count as reachable up to
## the gate (the walk opens every gate first).
## Run: godot --headless --path . res://tests/test_forest_reach.tscn

const ZONES := ["res://scenes/world/thornveil.tscn", "res://scenes/world/sorenda.tscn", "res://scenes/world/sorenda_hollow.tscn", "res://scenes/world/wardens_grove.tscn", "res://scenes/world/lake_veyra.tscn",
	"res://scenes/world/aurewind_plains.tscn", "res://scenes/world/verdana.tscn", "res://scenes/world/lake_serin.tscn", "res://scenes/world/starfall_range.tscn", "res://scenes/world/starfall_grotto.tscn", "res://scenes/world/seabright_quay.tscn", "res://scenes/world/frisalle.tscn", "res://scenes/world/aurewind_barrow.tscn"]
const STEP := 8.0

var _failures := 0
var _checks := 0
## The walk stays within the zone's ground (and a little past it, to the exits),
## so a flood that slips out through an exit can't wander off the map.
var _bounds := Rect2()


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	for path in ZONES:
		var zone := await _load(path)
		# Walk it as a player who has paid every gate would find it.
		for node in zone.get_children():
			if node is CardGate:
				(node as CardGate)._apply_open()
		await get_tree().physics_frame
		await get_tree().physics_frame
		var space := zone.get_world_2d().direct_space_state
		_bounds = _ground_rect(zone)
		var start := (zone.get_node("Spawns").get_child(0) as Node2D).global_position
		var reach := _flood(space, start)
		var label := String(zone.name)
		# A real share of the ground is walkable (caves are mostly rock, so a tenth).
		var cells := _bounds.get_area() / (STEP * STEP)
		_check("%s: the flood covers the zone (%d points of %d)" % [label, reach.size(), cells], reach.size() > mini(3000, int(cells * 0.1)))
		for node in zone.get_children():
			var target := ""
			if node is CardPickup:
				target = "card " + String(node.card_id)
			elif node is ZoneExit:
				target = "exit " + String(node.name)
			elif node is Npc:
				target = "resident " + String(node.name)
			elif node is Chest:
				target = "chest " + String(node.name)
			elif node is Readable:
				target = "readable " + String(node.title)
			if target != "":
				_check("%s: %s reachable" % [label, target], _near(reach, node.global_position, 30))
		for group in ["Spawns", "RivalSpots"]:
			if zone.get_node_or_null(group) == null:
				continue
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
	while head < queue.size() and out.size() < 120000:
		var p: Vector2 = queue[head]
		head += 1
		if not _open(space, p) or (_bounds.has_area() and not _bounds.has_point(p)):
			continue
		out.append(p)
		for d in [Vector2(STEP, 0), Vector2(-STEP, 0), Vector2(0, STEP), Vector2(0, -STEP)]:
			var q: Vector2 = p + d
			if not seen.has(q):
				seen[q] = true
				queue.append(q)
	return out


func _ground_rect(zone: Node) -> Rect2:
	var ground := zone.get_node_or_null("GroundTiles") as Sprite2D
	if ground == null or ground.texture == null:
		return Rect2()
	var size := ground.texture.get_size() * ground.scale
	return Rect2(ground.global_position - size / 2.0, size).grow(48)


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
