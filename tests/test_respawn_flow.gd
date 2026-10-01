extends Node
## End-to-end respawn test across real zone changes:
## Thornveil spawns the Raider -> beaten at its camp (deep north) it wakes in
## Sorenda -> the player dies to a monster near the south edge -> comes round at
## Kalmora's inn (the Salted Lantern), Jobelle welcomes them back, and the card they
## dropped is left on the ground in Thornveil.
## Run: godot --headless --path . res://tests/test_respawn_flow.tscn

var _failures := 0


func _ready() -> void:
	# Detach from current_scene so zone changes don't free the test itself.
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false  # Keep rivals where the test puts them.
	GameState.new_game(GameState.DEFAULT_RIVALS)
	get_tree().change_scene_to_file(WorldMap.THORNVEIL)
	await _frames(3)
	var forest := get_tree().current_scene
	_check("in Thornveil", forest.scene_file_path == WorldMap.THORNVEIL)
	var raider := _rival(forest, &"raider")
	_check("Thornveil spawned the Raider at its camp", raider != null
		and raider.position.is_equal_approx(forest.get_node("RivalSpots/raider").position))
	_check("the Runner is not here", _rival(forest, &"runner") == null)

	# Beat the Raider.
	var player := forest.get_node("Player") as Player
	player.global_position = raider.global_position + Vector2(-20, 0)
	for i in raider.max_health:
		raider._on_hurt(_hit(forest, &"player", 1))
	await get_tree().create_timer(raider.down_time + 0.2).timeout
	_check("beaten Raider left Thornveil", not is_instance_valid(raider))
	_check("Raider woke in Sorenda (nearest to its camp)", GameState.rival_locations[&"raider"].zone == WorldMap.SORENDA)

	# The player falls to a monster while carrying a loose card.
	GameState.add_loose_card(GameState.PLAYER, &"bark_rune")
	player.global_position = Vector2(80, 40)
	player._on_hurt(_hit(forest, Combat.MONSTER, 99))
	await get_tree().create_timer(1.5).timeout
	await _frames(3)
	var inn := get_tree().current_scene
	_check("came round at Kalmora's inn", inn.scene_file_path == WorldMap.KALMORA_TAVERN)
	var new_player := inn.get_node("Player") as Player
	_check("by the door with full health", new_player.position.is_equal_approx(inn.get_node("Spawns/door").position)
		and new_player.health == new_player.max_health)
	await get_tree().create_timer(0.5).timeout
	_check("on their feet again", new_player._state == Player.State.MOVE)
	var box := get_tree().get_first_node_in_group(&"dialogue_box") as DialogueBox
	_check("Jobelle welcomes them back", box != null and box.is_open())
	_check("dropped card stays on the ground in Thornveil", GameState.zone_drops.get(WorldMap.THORNVEIL, []).size() == 1
		and GameState.zone_drops[WorldMap.THORNVEIL][0].dropped_by == GameState.PLAYER
		and GameState.collection(GameState.PLAYER).count(&"bark_rune") == 0)
	_check("Raider is not in Kalmora", GameState.rival_locations[&"raider"].zone != WorldMap.KALMORA)
	_check("Runner still in Kalmora", GameState.rival_locations[&"runner"].zone == WorldMap.KALMORA)

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _rival(zone: Node, id: StringName) -> Rival:
	for node in zone.get_children():
		if node is Rival and node.collector_id == id and not node.is_queued_for_deletion():
			return node
	return null


func _hit(parent: Node, source: StringName, damage: int) -> Hitbox:
	var hitbox := Hitbox.new()
	hitbox.source_id = source
	hitbox.damage = damage
	hitbox.knockback = 0.0
	parent.add_child(hitbox)
	return hitbox


func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
