class_name HealingSpring
extends StaticBody2D
## A spring you can drink from (the Heartwood shrine in Thornveil): press interact
## beside it to heal fully. Free and endless; it's a place worth walking back to.

const RANGE := 64.0


var _near := false


func _process(_delta: float) -> void:
	var near := _player_near()
	if near != _near:
		_near = near
		queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if GameState.menus_open > 0 or not event.is_action_pressed(&"interact") or not _player_near():
		return
	get_viewport().set_input_as_handled()
	var player := get_tree().get_first_node_in_group(&"player") as Player
	if player:
		player.heal(player.max_health)
	DialogueBox.say(get_tree(), "The Heartwood spring", PackedStringArray([
		"You cup your hands and drink. The water is cold and tastes of rain and bark. Your wounds close.",
	]))


func _player_near() -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position + Vector2(0, 20)) <= RANGE


func _draw() -> void:
	if _near and GameState.menus_open == 0:
		WorldPrompt.draw(self, Vector2(0, -70), "E", "Drink")
