class_name Merchant
extends Area2D
## Town stall. Press interact nearby to open the shop panel with this stock.

@export var stock: Array[StringName] = [&"pickpockets_whisper", &"lockbox_seal", &"second_wind"]
## Stall art; falls back to a drawn placeholder when unset.
@export var stall_texture: Texture2D

var _player_near := false


func _ready() -> void:
	body_entered.connect(func(body: Node2D) -> void: _set_near(body, true))
	body_exited.connect(func(body: Node2D) -> void: _set_near(body, false))


func _set_near(body: Node2D, near: bool) -> void:
	if body is Player:
		_player_near = near
		queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if _player_near and GameState.menus_open == 0 and event.is_action_pressed(&"interact"):
		var shop := get_tree().get_first_node_in_group(&"shop_panel") as ShopPanel
		if shop:
			shop.open_with(stock)
			get_viewport().set_input_as_handled()


func _draw() -> void:
	if stall_texture:
		draw_texture(stall_texture, Vector2(-stall_texture.get_width() / 2.0, 8.0 - stall_texture.get_height()))
		_draw_prompt()
		return
	# Placeholder stall: awning over a counter.
	draw_rect(Rect2(-18, -6, 36, 12), Color(0.55, 0.38, 0.22))
	draw_rect(Rect2(-20, -26, 40, 8), Color(0.8, 0.35, 0.25))
	for i in 5:
		draw_rect(Rect2(-20 + i * 8, -26, 4, 8), Color(0.95, 0.92, 0.85))
	draw_rect(Rect2(-17, -18, 2, 12), Color(0.4, 0.28, 0.16))
	draw_rect(Rect2(15, -18, 2, 12), Color(0.4, 0.28, 0.16))
	_draw_prompt()


func _draw_prompt() -> void:
	if _player_near:
		var font := ThemeDB.fallback_font
		draw_string_outline(font, Vector2(-16, -58), "E: Shop", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
		draw_string(font, Vector2(-16, -58), "E: Shop", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color.WHITE)
