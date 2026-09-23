extends Node
## Loads Kalmora with a stocked binder and opens a menu, for screenshots:
## godot --path . --write-movie out.png --quit-after 30 res://tests/ui_preview.tscn
## Set `menu` to "binder", "shop", or "stealth" (player sneaking up on the Runner).

@export var menu := "binder"


func _ready() -> void:
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
		var runner := town.get_node("Runner") as Rival
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
