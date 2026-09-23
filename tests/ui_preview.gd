extends Node
## Loads Kalmora with a stocked binder and opens a menu, for screenshots:
## godot --path . --write-movie out.png --quit-after 30 res://tests/ui_preview.tscn
## Set `menu` to "binder", "shop", "stealth" (player sneaking up on the Runner),
## or "combat" (Thornveil: player with loose cards near a Briar Hound and the Raider).

@export var menu := "binder"


func _ready() -> void:
	if menu == "combat":
		_combat_preview()
		return
	var town: Node = load("res://scenes/world/kalmora.tscn").instantiate()
	add_child(town)
	await get_tree().process_frame
	for id: StringName in [&"harbor_lantern", &"sea_glass", &"sea_glass", &"sunken_crown_shard", &"tide_bell",
			&"pickpockets_whisper", &"lockbox_seal", &"second_wind"]:
		GameState.add_loose_card(GameState.PLAYER, id)
	GameState.bind_card(GameState.PLAYER, &"sea_glass")
	GameState.bind_card(GameState.PLAYER, &"tide_bell")
	GameState.expose_card(GameState.PLAYER, &"tide_bell")
	CardSpells.use_lockbox(GameState.PLAYER, &"sunken_crown_shard")
	if menu == "stealth":
		var runner := _rival(town, &"runner")
		var player := town.get_node("Player") as Player
		runner.set_physics_process(false)
		runner.global_position = Vector2(-120, 60)
		runner.facing = Vector2.RIGHT
		runner.awareness.facing = Vector2.RIGHT
		runner.awareness.bump(45.0)
		GameState.add_loose_card(&"runner", &"coral_coin")
		GameState.add_loose_card(&"runner", &"gull_feather")
		player.global_position = runner.global_position + Vector2(-18, 0)
		player.facing = Vector2.RIGHT
		runner.queue_redraw()
	elif menu == "shop":
		(town.get_node("ShopPanel") as ShopPanel).open_with([&"pickpockets_whisper", &"lockbox_seal", &"second_wind"])
	else:
		(town.get_node("Binder") as Binder).open()


func _combat_preview() -> void:
	var forest: Node = load("res://scenes/world/thornveil.tscn").instantiate()
	add_child(forest)
	await get_tree().process_frame
	GameState.add_loose_card(GameState.PLAYER, &"harbor_lantern")
	GameState.add_loose_card(GameState.PLAYER, &"coral_coin")
	var player := forest.get_node("Player") as Player
	player.global_position = Vector2(-190, -170)
	_rival(forest, &"raider").global_position = Vector2(-110, -240)


func _rival(zone: Node, id: StringName) -> Rival:
	for node in zone.get_children():
		if node is Rival and node.collector_id == id:
			return node
	return null
