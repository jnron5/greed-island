class_name Combat
extends RefCounted
## Rules shared by every fight: monsters, bosses and rival confrontations.
## - Nobody damages themselves or their own team (all monsters are one team).
## - Collectors can't fight each other while either one is in a safe zone (towns).
## - Beating a collector in a fight takes one of their loose or exposed cards.

const MONSTER := &"monster"


static func is_collector(id: StringName) -> bool:
	return id == GameState.PLAYER or id in GameState.RIVALS


static func can_damage(source_id: StringName, victim_id: StringName) -> bool:
	if source_id == victim_id:
		return false
	if is_collector(source_id) and is_collector(victim_id):
		return not GameState.is_in_safe_zone(source_id) and not GameState.is_in_safe_zone(victim_id)
	return true


## Winner takes one random loose/exposed card from the loser (none if the loser
## is in their grace period or has nothing stealable). Returns the card id or &"".
static func resolve_defeat(winner_id: StringName, loser_id: StringName) -> StringName:
	if not is_collector(winner_id) or not is_collector(loser_id):
		return &""
	var options := GameState.stealable_card_ids(loser_id)
	if options.is_empty() or GameState.grace_left(loser_id) > 0.0:
		EventBus.combat_won.emit(winner_id, loser_id, &"")
		return &""
	var card_id: StringName = options.pick_random()
	GameState.steal_card(winner_id, loser_id, card_id, &"combat")
	EventBus.combat_won.emit(winner_id, loser_id, card_id)
	return card_id


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
