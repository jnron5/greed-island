class_name Combat
extends RefCounted
## Rules shared by every fight: monsters, bosses and rival confrontations.
## - Nobody damages themselves or their own team (all monsters are one team).
## - Collectors can't fight each other while either one is in a safe zone (towns).
## - A collector who goes down drops one card where they fell (see resolve_defeat).

const MONSTER := &"monster"


static func is_collector(id: StringName) -> bool:
	return id == GameState.PLAYER or id in GameState.RIVALS


static func can_damage(source_id: StringName, victim_id: StringName) -> bool:
	if source_id == victim_id:
		return false
	if is_collector(source_id) and is_collector(victim_id):
		if source_id != GameState.PLAYER and in_truce(source_id, victim_id):
			return false   # Rivals keep a boss truce; the player can break it.
		return not GameState.is_in_safe_zone(source_id) and not GameState.is_in_safe_zone(victim_id)
	return true


## Both collectors are in the arena of a boss being fought, truce unbroken.
static func in_truce(a: StringName, b: StringName) -> bool:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return false
	var nodes := {}
	for node in tree.get_nodes_in_group(&"collectors"):
		nodes[node.get(&"collector_id")] = node
	if not nodes.has(a) or not nodes.has(b):
		return false
	for node in tree.get_nodes_in_group(&"bosses"):
		var boss := node as Boss
		if boss == null or boss.is_dead() or boss.truce_broken or boss._state == Boss.State.DORMANT:
			continue
		if boss._lair.distance_to(nodes[a].global_position) <= boss.arena_radius \
				and boss._lair.distance_to(nodes[b].global_position) <= boss.arena_radius:
			return true
	return false


## A collector goes down (to a collector or a monster): they always lose one card,
## and it lands on the ground where they fell for anyone to pick up, the winner
## included. Returns the card dropped, or &"" if they had nothing at all.
static func resolve_defeat(winner_id: StringName, loser_id: StringName, tree: SceneTree = null,
		pos := Vector2.INF) -> StringName:
	if not is_collector(loser_id):
		return &""
	var card_id := GameState.lose_card(loser_id)
	if card_id != &"" and tree and pos != Vector2.INF:
		_drop_card(tree, card_id, pos + _scatter(), loser_id, pos + Vector2(0, -16))
	if is_collector(winner_id):
		EventBus.combat_won.emit(winner_id, loser_id, card_id)
	return card_id


## What a kill leaves behind, flung out of the body at `pos`: a card (kept in the
## zone until someone takes it), and maybe some gold or a satchel item (for the
## player). Nothing goes straight into anyone's hands.
static func drop_loot(tree: SceneTree, pos: Vector2, card_id: StringName = &"", gold := 0,
		item_id: StringName = &"", fling_height := 16.0) -> void:
	var parent := tree.current_scene
	if parent == null:
		return
	var from := pos + Vector2(0, -fling_height)
	if card_id != &"":
		_drop_card(tree, card_id, pos + _scatter(), &"", from)
	if gold > 0 or item_id != &"":
		var loot := LootPickup.new()
		loot.gold = gold
		loot.item_id = item_id
		loot.position = pos + _scatter()
		loot.fling_from = from
		parent.add_child.call_deferred(loot)


## A card on the ground: kept in the zone's drops (so it's still there when you
## come back), or just placed in the scene when there's no zone (tests).
static func _drop_card(tree: SceneTree, card_id: StringName, at: Vector2, dropped_by: StringName, from: Vector2) -> void:
	var zone := Zone.current(tree)
	if zone:
		zone.drop_card(card_id, at, dropped_by, from)
		return
	if tree.current_scene == null:
		return
	var pickup := preload("res://scenes/systems/card_pickup.tscn").instantiate() as CardPickup
	pickup.card_id = card_id
	pickup.dropped_by = dropped_by
	pickup.fling_from = from
	pickup.position = at
	tree.current_scene.add_child.call_deferred(pickup)


static func _scatter() -> Vector2:
	return Vector2.from_angle(randf() * TAU) * randf_range(12.0, 26.0)


## Kept for callers that just want a card dropped where something died.
static func award_card(parent: Node, _killer: StringName, card_id: StringName, pos: Vector2,
		_pickup_scene: PackedScene) -> void:
	drop_loot(parent.get_tree(), pos, card_id)


## A short camera shake (a landed blow, a boss slam).
static func shake(tree: SceneTree, strength: float, steps := 5) -> void:
	var camera := tree.root.get_viewport().get_camera_2d()
	if camera == null or DisplayServer.get_name() == "headless":
		return
	var tween := camera.create_tween()
	for i in steps:
		tween.tween_property(camera, "offset", Vector2(randf_range(-1, 1), randf_range(-1, 1)) * strength, 0.03)
	tween.tween_property(camera, "offset", Vector2.ZERO, 0.03)


## Hit-stop: the world freezes for a few hundredths of a second so a blow lands with
## weight. Real-time timer, so it ends even though time is stopped.
static func hit_stop(tree: SceneTree, seconds := 0.05) -> void:
	if DisplayServer.get_name() == "headless" or Engine.time_scale < 1.0:
		return
	Engine.time_scale = 0.05
	await tree.create_timer(seconds, true, false, true).timeout
	Engine.time_scale = 1.0


## Floating damage number at `pos` in `parent`'s space.
static func pop_number(parent: Node, pos: Vector2, amount: int, color := Color.WHITE) -> void:
	var label := Label.new()
	label.text = str(amount)
	label.add_theme_font_size_override("font_size", 10)
	label.add_theme_color_override("font_color", color)
	label.add_theme_color_override("font_outline_color", Color.BLACK)
	label.add_theme_constant_override("outline_size", 3)
	label.z_index = 30
	parent.add_child(label)
	label.global_position = pos + Vector2(-4, -40)
	var tween := label.create_tween()
	tween.tween_property(label, "global_position:y", label.global_position.y - 14.0, 0.5)
	tween.parallel().tween_property(label, "modulate:a", 0.0, 0.5).set_delay(0.2)
	tween.tween_callback(label.queue_free)
