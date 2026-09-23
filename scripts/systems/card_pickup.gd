class_name CardPickup
extends Area2D
## A loose card lying in the world. Any collector body (player or rival) with a
## `collector_id` property picks it up on touch; it arrives in the Loose state.
## Hand-placed pickups are remembered once taken so they don't return when the
## zone reloads; dropped cards are tracked per zone in GameState.zone_drops.

@export var card_id: StringName

## Set for cards dropped at runtime that should persist in their zone.
var zone_drop_of: String

var _time := randf() * TAU


func _ready() -> void:
	if _is_hand_placed() and GameState.collected_pickups.has(_persist_key()):
		queue_free()
		return
	add_to_group(&"card_pickups")
	body_entered.connect(_on_body_entered)


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _on_body_entered(body: Node2D) -> void:
	var collector: Variant = body.get(&"collector_id")
	if not (collector is StringName) or (body.has_method(&"can_pick_up") and not body.can_pick_up()):
		return
	if not GameState.add_loose_card(collector, card_id):
		return
	if _is_hand_placed():
		GameState.collected_pickups[_persist_key()] = true
	elif zone_drop_of != "":
		GameState.remove_zone_drop(zone_drop_of, card_id, position)
	queue_free()


## Placed in the editor (owned by a saved scene) rather than spawned by code.
func _is_hand_placed() -> bool:
	return owner != null and owner.scene_file_path != ""


func _persist_key() -> String:
	return "%s:%s" % [owner.scene_file_path, owner.get_path_to(self)]


func _draw() -> void:
	# Placeholder card glyph until card art exists: a small bobbing card with a glint.
	var card := CardDatabase.get_card(card_id)
	var rare := card != null and card.rarity != CardData.Rarity.COMMON
	var y := sin(_time * 3.0) * 2.0 - 6.0
	draw_rect(Rect2(-4, y + 7, 8, 2), Color(0, 0, 0, 0.25))
	draw_rect(Rect2(-4, y - 5, 8, 11), Color(0.1, 0.08, 0.06))
	draw_rect(Rect2(-3, y - 4, 6, 9), Color(0.95, 0.8, 0.35) if rare else Color(0.9, 0.9, 0.85))
	draw_rect(Rect2(-2, y - 3, 4, 3), Color(0.8, 0.3, 0.2) if rare else Color(0.3, 0.5, 0.7))
