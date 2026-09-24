class_name Zone
extends Node2D
## Root of a town/zone scene. Places the player at the requested spawn marker
## (a child of "Spawns"), restores cards that were dropped here earlier, and
## spawns whichever rivals GameState says are in this zone. Rivals appear at
## "RivalSpots/<id>" (also their home for binding) unless they left from
## somewhere else here last time.
##
## Elevation: an optional level map (one pixel per ground cell; red = level x 40,
## 255 = cliff/edge) tells level_at() how high any point is. Characters only
## fight, see and steal on their own level.
## Navigation: a grid built from the zone's World collision gives rivals real
## paths (around trees, up stairs) via find_path().

@export var display_name := ""
@export var pickup_scene: PackedScene = preload("res://scenes/systems/card_pickup.tscn")
@export var rival_scene: PackedScene = preload("res://scenes/characters/rival.tscn")
@export_group("Elevation")
## One pixel per cell; red channel = level * 40, 255 = not walkable (cliff).
@export var level_map: Texture2D
@export var level_cell := 32
## Local position of the level map's top-left corner.
@export var level_origin := Vector2.ZERO

const NAV_CELL := 16

var _levels: Image
var _nav := AStarGrid2D.new()
var _nav_ready := false


func _enter_tree() -> void:
	# Presence in the previous zone's safe areas is gone once we switch scenes.
	GameState.reset_zone_presence()


func _ready() -> void:
	var spawn := get_node_or_null(NodePath("Spawns/%s" % GameState.pending_spawn)) as Marker2D
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if spawn and player:
		player.global_position = spawn.global_position
		var camera := player.get_node_or_null(^"Camera2D") as Camera2D
		if camera:
			camera.reset_smoothing()
	_limit_camera(player)
	if level_map:
		_levels = level_map.get_image()
	_build_nav.call_deferred()
	# Opened gates stop blocking: rebuild the grid once the collision is gone.
	EventBus.gate_opened.connect(func(_id: StringName, _by: StringName) -> void: _build_nav.call_deferred())
	GameState.pending_spawn = &""
	for drop: Dictionary in GameState.zone_drops.get(scene_file_path, []):
		_spawn_drop(drop.card_id, drop.position)
	for id in GameState.active_rivals:
		if GameState.rival_locations.get(id, {}).get("zone") == scene_file_path:
			spawn_rival(id)
	if display_name != "":
		EventBus.notify.emit(display_name)


## Keeps the player's camera over the painted ground (no grey void past the edges).
func _limit_camera(player: Node2D) -> void:
	var camera := player.get_node_or_null(^"Camera2D") as Camera2D if player else null
	var ground := _ground_sprite()
	if camera == null or ground == null:
		return
	var rect := Rect2(ground.position - ground.texture.get_size() / 2.0, ground.texture.get_size())
	camera.limit_left = int(rect.position.x)
	camera.limit_top = int(rect.position.y)
	camera.limit_right = int(rect.end.x)
	camera.limit_bottom = int(rect.end.y)


## Level at a global position: 0 without a level map, -1 on a cliff/edge cell.
func level_at(global_pos: Vector2) -> int:
	if _levels == null:
		return 0
	var cell := Vector2i(((to_local(global_pos) - level_origin) / level_cell).floor())
	if cell.x < 0 or cell.y < 0 or cell.x >= _levels.get_width() or cell.y >= _levels.get_height():
		return -1
	var v := _levels.get_pixel(cell.x, cell.y).r8
	return -1 if v == 255 else v / 40


## True when two points are on the same level (a cliff/edge cell counts as either).
static func same_level(tree: SceneTree, a: Vector2, b: Vector2) -> bool:
	var zone := current(tree)
	if zone == null:
		return true
	var la := zone.level_at(a)
	var lb := zone.level_at(b)
	return la == -1 or lb == -1 or la == lb


## Walkable route between two global points (empty if there's no grid yet or no way).
func find_path(from: Vector2, to: Vector2) -> PackedVector2Array:
	if not _nav_ready:
		return PackedVector2Array()
	var a := _nav_cell(from)
	var b := _nav_cell(to)
	if not _nav.is_in_boundsv(a) or not _nav.is_in_boundsv(b):
		return PackedVector2Array()
	var points := _nav.get_point_path(a, b, true)
	var out := PackedVector2Array()
	for p in points:
		out.append(to_global(p))
	return out


func _nav_cell(global_pos: Vector2) -> Vector2i:
	return Vector2i((to_local(global_pos) / NAV_CELL).floor())


## Marks every cell that has World collision (walls, cliffs, trees, buildings) solid.
func _build_nav() -> void:
	_nav_ready = false
	await get_tree().physics_frame
	await get_tree().physics_frame  # Let deferred collision changes (opened gates) land.
	var ground := _ground_sprite()
	var rect := Rect2(-640, -640, 1280, 1280)
	if ground:
		rect = Rect2(ground.position - ground.texture.get_size() / 2.0, ground.texture.get_size())
	var cells := Rect2i(Vector2i((rect.position / NAV_CELL).floor()), Vector2i((rect.size / NAV_CELL).ceil()))
	_nav.region = cells
	_nav.cell_size = Vector2(NAV_CELL, NAV_CELL)
	_nav.offset = Vector2(NAV_CELL, NAV_CELL) / 2.0
	_nav.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	_nav.update()
	var space := get_world_2d().direct_space_state
	var query := PhysicsPointQueryParameters2D.new()
	query.collision_mask = 1
	for y in range(cells.position.y, cells.end.y):
		for x in range(cells.position.x, cells.end.x):
			query.position = to_global(Vector2(x + 0.5, y + 0.5) * NAV_CELL)
			if not space.intersect_point(query, 1).is_empty():
				_nav.set_point_solid(Vector2i(x, y))
	_nav_ready = true


func _ground_sprite() -> Sprite2D:
	for name in [&"GroundTiles", &"Ground"]:
		var ground := get_node_or_null(NodePath(name)) as Sprite2D
		if ground and ground.texture:
			return ground
	return null


## Leaves a card lying here that survives the player leaving and coming back.
func drop_card(card_id: StringName, pos: Vector2) -> void:
	GameState.add_zone_drop(scene_file_path, card_id, pos)
	_spawn_drop(card_id, pos)


## Adds rival `id` to this zone at its saved position (or its RivalSpots marker).
func spawn_rival(id: StringName) -> Rival:
	var profile := GameState.rival_profile(id)
	if profile == null:
		return null
	var rival := rival_scene.instantiate() as Rival
	rival.apply_profile(profile)
	rival.home = rival_spot(id)
	var saved: Variant = GameState.rival_locations[id].get("position")
	rival.position = saved if saved is Vector2 else (rival.home.position if rival.home else Vector2.ZERO)
	add_child(rival)
	return rival


## This zone's marker for rival `id`: where it appears and binds its cards.
func rival_spot(id: StringName) -> Marker2D:
	return get_node_or_null(NodePath("RivalSpots/%s" % id)) as Marker2D


func _spawn_drop(card_id: StringName, pos: Vector2) -> void:
	var pickup := pickup_scene.instantiate() as CardPickup
	pickup.card_id = card_id
	pickup.zone_drop_of = scene_file_path
	pickup.position = pos
	add_child.call_deferred(pickup)


static func current(tree: SceneTree) -> Zone:
	return tree.current_scene as Zone
