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
## Atmosphere: outdoor zones follow the TimeOfDay tint (multiplied with any
## CanvasModulate the scene already has); interiors keep a warm fixed light.
## Zones with a level map get a water shimmer over their sea cells.
## Surfaces: an optional surface map (one pixel per ground pixel; green = sand)
## makes sand take footprints.

@export var display_name := ""
@export var pickup_scene: PackedScene = preload("res://scenes/systems/card_pickup.tscn")
@export var rival_scene: PackedScene = preload("res://scenes/characters/rival.tscn")
## Indoors: fixed warm light instead of the day/night tint.
@export var interior := false
## Caves: the scene's own (dark) CanvasModulate, no day or night; light comes from
## the glowing moss and lanterns placed in it. Unlike interiors, caves are reached
## along WorldMap.EDGES, so rivals can go in too.
@export var underground := false
@export var water_shimmer := true
@export_group("Elevation")
## One pixel per cell; red channel = level * 40, 255 = not walkable (cliff).
@export var level_map: Texture2D
@export var level_cell := 32
## Local position of the level map's top-left corner.
@export var level_origin := Vector2.ZERO
@export_group("Surfaces")
## Same size as the ground image; green = sand (takes footprints).
@export var surface_map: Texture2D

const NAV_CELL := 16

var _levels: Image
var _modulate: CanvasModulate
var _base_tint := Color.WHITE
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
	if player:
		SaveGame.place_player(player)
	_limit_camera(player)
	_wall_edges()
	_see_through()
	# Every zone can talk: residents, signs and readables need the dialogue box.
	if get_tree().get_first_node_in_group(&"dialogue_box") == null:
		add_child(preload("res://scenes/ui/dialogue_box.tscn").instantiate())
	if level_map:
		_levels = level_map.get_image()
	_build_nav.call_deferred()
	_setup_atmosphere()
	# Opened gates stop blocking: rebuild the grid once the collision is gone.
	EventBus.gate_opened.connect(func(_id: StringName, _by: StringName) -> void: _build_nav.call_deferred())
	GameState.pending_spawn = &""
	for drop: Dictionary in GameState.zone_drops.get(scene_file_path, []):
		_spawn_drop(drop.card_id, drop.position, drop.get("dropped_by", &""))
	for id in GameState.active_rivals:
		if GameState.rival_locations.get(id, {}).get("zone") == scene_file_path:
			spawn_rival(id)
	if not interior and not underground:
		Travellers.populate(self)
	if display_name != "":
		EventBus.area_entered.emit(display_name, interior)


## Night in the wild: the first time each night you're outdoors somewhere with
## monsters (at dusk, or arriving after dark), a warning that they're savage now.
static var _warned_night := -1
var _night_clock := 0.0


func _process(delta: float) -> void:
	_night_clock -= delta
	if _night_clock > 0.0:
		return
	_night_clock = 2.0
	if interior or underground or not TimeOfDay.is_night():
		return
	var night_id := TimeOfDay.day - (1 if TimeOfDay.hour < 12.0 else 0)
	if night_id == _warned_night or get_tree().get_first_node_in_group(&"monsters") == null:
		return
	_warned_night = night_id
	EventBus.notify.emit("Night has fallen. The beasts are savage after dark: tougher, faster, and carrying richer loot.")


## Tall things the player can walk behind (buildings, big trees: a body with a sprite
## taller than SEE_THROUGH_HEIGHT) fade while they do (SeeThrough).
const SEE_THROUGH_HEIGHT := 80.0


func _see_through() -> void:
	if interior:
		return
	for body in get_children():
		if not body is StaticBody2D:
			continue
		for child in body.get_children():
			var tall := false
			if child is Sprite2D and (child as Sprite2D).texture:
				tall = (child as Sprite2D).get_rect().size.y * absf((child as Sprite2D).scale.y) > SEE_THROUGH_HEIGHT
			elif child is AnimatedSprite2D and (child as AnimatedSprite2D).sprite_frames:
				var a := child as AnimatedSprite2D
				var tex := a.sprite_frames.get_frame_texture(a.animation, 0)
				tall = tex != null and tex.get_height() * absf(a.scale.y * (body as Node2D).scale.y) > SEE_THROUGH_HEIGHT
			if tall:
				child.add_child(SeeThrough.new())
				break


## Walls the zone in just outside its painted ground, leaving openings only where
## an edge exit is (each as wide as the exit's band, ZoneExit.EDGE_SPAN), so nobody
## wanders off the map and every way out is the exit itself.
func _wall_edges() -> void:
	var rect := ground_rect()
	if interior or not rect.has_area():
		return
	const THICK := 64.0
	var gaps := { Vector2.LEFT: [], Vector2.RIGHT: [], Vector2.UP: [], Vector2.DOWN: [] }
	for node in get_children():
		var exit := node as ZoneExit
		if exit and exit.edge_side != Vector2.ZERO:
			var along := exit.position.y if exit.edge_side.x != 0 else exit.position.x
			gaps[exit.edge_side].append(Vector2(along - ZoneExit.EDGE_SPAN / 2.0, along + ZoneExit.EDGE_SPAN / 2.0))
	var body := StaticBody2D.new()
	body.name = "EdgeWalls"
	for side: Vector2 in gaps:
		var horizontal := side.y != 0
		var lo := (rect.position.x if horizontal else rect.position.y) - THICK
		var hi := (rect.end.x if horizontal else rect.end.y) + THICK
		var spans: Array = gaps[side]
		spans.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.x < b.x)
		var pieces: Array[Vector2] = []
		var at := lo
		for gap: Vector2 in spans:
			if gap.x > at:
				pieces.append(Vector2(at, gap.x))
			at = maxf(at, gap.y)
		if at < hi:
			pieces.append(Vector2(at, hi))
		for piece in pieces:
			var box := RectangleShape2D.new()
			var shape := CollisionShape2D.new()
			var across: float
			match side:
				Vector2.LEFT: across = rect.position.x - THICK / 2.0
				Vector2.RIGHT: across = rect.end.x + THICK / 2.0
				Vector2.UP: across = rect.position.y - THICK / 2.0
				_: across = rect.end.y + THICK / 2.0
			var mid := (piece.x + piece.y) / 2.0
			box.size = Vector2(piece.y - piece.x, THICK) if horizontal else Vector2(THICK, piece.y - piece.x)
			shape.position = Vector2(mid, across) if horizontal else Vector2(across, mid)
			shape.shape = box
			body.add_child(shape)
	add_child(body)


## The painted ground's area in zone coordinates (empty if there's none).
func ground_rect() -> Rect2:
	var ground := _ground_sprite()
	return _ground_rect(ground) if ground else Rect2()


## Keeps the player's camera over the painted ground (no grey void past the edges).
func _limit_camera(player: Node2D) -> void:
	var camera := player.get_node_or_null(^"Camera2D") as Camera2D if player else null
	var ground := _ground_sprite()
	if camera == null or ground == null:
		return
	var rect := _ground_rect(ground)
	# A room smaller than the screen sits centred in it instead of against one edge.
	var view := get_viewport().get_visible_rect().size / camera.zoom
	rect = rect.grow_individual(maxf(0.0, (view.x - rect.size.x) / 2.0), maxf(0.0, (view.y - rect.size.y) / 2.0),
		maxf(0.0, (view.x - rect.size.x) / 2.0), maxf(0.0, (view.y - rect.size.y) / 2.0))
	camera.limit_left = int(rect.position.x)
	camera.limit_top = int(rect.position.y)
	camera.limit_right = int(rect.end.x)
	camera.limit_bottom = int(rect.end.y)


func _setup_atmosphere() -> void:
	for child in get_children():
		if child is CanvasModulate:
			_modulate = child
			_base_tint = child.color
	if _modulate == null:
		_modulate = CanvasModulate.new()
		add_child(_modulate)
	if interior:
		_modulate.color = _base_tint * Color(1.0, 0.93, 0.84)
	elif underground:
		_modulate.color = _base_tint
	else:
		_apply_tint(TimeOfDay.hour)
		TimeOfDay.hour_changed.connect(_apply_tint)
		add_child(NightGrade.new())
	if level_map and water_shimmer and not interior:
		var water := ColorRect.new()
		water.z_index = -9
		water.mouse_filter = Control.MOUSE_FILTER_IGNORE
		water.position = level_origin
		water.size = Vector2(level_map.get_size()) * level_cell
		var mat := ShaderMaterial.new()
		mat.shader = preload("res://assets/shaders/water_shimmer.gdshader")
		mat.set_shader_parameter(&"level_map", level_map)
		mat.set_shader_parameter(&"map_cells", Vector2(level_map.get_size()))
		water.material = mat
		add_child(water)
	var ground := _ground_sprite()
	if surface_map and ground and not interior:
		var prints := Footprints.new()
		prints.surface = surface_map.get_image()
		prints.origin = ground.position - ground.texture.get_size() / 2.0
		add_child(prints)


func _apply_tint(_hour: float) -> void:
	_modulate.color = _base_tint * TimeOfDay.tint()


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
		rect = _ground_rect(ground)
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


## The ground sprite's area in zone coordinates (interiors draw their room scaled up).
func _ground_rect(ground: Sprite2D) -> Rect2:
	var size := ground.texture.get_size() * ground.scale
	return Rect2(ground.position - size / 2.0, size)


func _ground_sprite() -> Sprite2D:
	for name in [&"GroundTiles", &"Ground"]:
		var ground := get_node_or_null(NodePath(name)) as Sprite2D
		if ground and ground.texture:
			return ground
	return null


## Leaves a card lying here that survives the player leaving and coming back.
## A card left on the ground here (it stays in this zone until someone takes it).
## `dropped_by`: the collector who lost it; `fling_from`: where it flies out from.
func drop_card(card_id: StringName, pos: Vector2, dropped_by: StringName = &"", fling_from := Vector2.INF) -> void:
	GameState.add_zone_drop(scene_file_path, card_id, pos, dropped_by)
	_spawn_drop(card_id, pos, dropped_by, fling_from)


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


func _spawn_drop(card_id: StringName, pos: Vector2, dropped_by: StringName = &"", fling_from := Vector2.INF) -> void:
	var pickup := pickup_scene.instantiate() as CardPickup
	pickup.card_id = card_id
	pickup.zone_drop_of = scene_file_path
	pickup.dropped_by = dropped_by
	pickup.fling_from = fling_from
	pickup.position = pos
	add_child.call_deferred(pickup)


static func current(tree: SceneTree) -> Zone:
	return tree.current_scene as Zone
