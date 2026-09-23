class_name Zone
extends Node2D
## Root of a town/zone scene. Places the player at the requested spawn marker
## (a child of "Spawns"), restores cards that were dropped here earlier, and
## spawns whichever rivals GameState says are in this zone. Rivals appear at
## "RivalSpots/<id>" (also their home for binding) unless they left from
## somewhere else here last time.

@export var display_name := ""
@export var pickup_scene: PackedScene = preload("res://scenes/systems/card_pickup.tscn")
@export var rival_scene: PackedScene = preload("res://scenes/characters/rival.tscn")


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
	GameState.pending_spawn = &""
	for drop: Dictionary in GameState.zone_drops.get(scene_file_path, []):
		_spawn_drop(drop.card_id, drop.position)
	for id in GameState.active_rivals:
		if GameState.rival_locations.get(id, {}).get("zone") == scene_file_path:
			spawn_rival(id)
	if display_name != "":
		EventBus.notify.emit(display_name)


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
