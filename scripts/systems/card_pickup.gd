class_name CardPickup
extends Area2D
## A loose card lying in the world. Any collector body (player or rival) with a
## `collector_id` property picks it up on touch; it arrives in the Loose state.

@export var card_id: StringName

var _time := randf() * TAU


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _on_body_entered(body: Node2D) -> void:
	var collector: Variant = body.get(&"collector_id")
	if collector is StringName and GameState.add_loose_card(collector, card_id):
		queue_free()


func _draw() -> void:
	# Placeholder card glyph until card art exists: a small bobbing card with a glint.
	var card := CardDatabase.get_card(card_id)
	var rare := card != null and card.rarity != CardData.Rarity.COMMON
	var y := sin(_time * 3.0) * 2.0 - 6.0
	draw_rect(Rect2(-4, y + 7, 8, 2), Color(0, 0, 0, 0.25))
	draw_rect(Rect2(-4, y - 5, 8, 11), Color(0.1, 0.08, 0.06))
	draw_rect(Rect2(-3, y - 4, 6, 9), Color(0.95, 0.8, 0.35) if rare else Color(0.9, 0.9, 0.85))
	draw_rect(Rect2(-2, y - 3, 4, 3), Color(0.8, 0.3, 0.2) if rare else Color(0.3, 0.5, 0.7))
