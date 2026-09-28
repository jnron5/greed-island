class_name Readable
extends Node2D
## Something in a room worth a closer look (a letter, a ledger, a portrait): press
## interact nearby to read it in the dialogue box. Invisible itself (the room art
## draws it); a small sparkle marks it until it's been read once this game.

const RANGE := 26.0

@export var title := "Note"
@export_multiline var lines: PackedStringArray = []

var _time := randf() * TAU


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if GameState.menus_open > 0 or not event.is_action_pressed(&"interact") or not _player_near():
		return
	get_viewport().set_input_as_handled()
	GameState.quest_flags[_read_key()] = true
	var zone := Zone.current(get_tree())
	GameState.note(title, zone.display_name if zone else "", lines)
	Quests.read(title)
	DialogueBox.say(get_tree(), title, lines)


func _read_key() -> StringName:
	return StringName("read:%s:%s" % [owner.scene_file_path if owner else "", name])


func _player_near() -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position) <= RANGE


func _draw() -> void:
	if not GameState.quest_flags.get(_read_key(), false):
		var glow := 0.6 + 0.4 * sin(_time * 3.0)
		draw_rect(Rect2(-1, -1, 2, 2), Color(1, 0.95, 0.65, glow))
		draw_rect(Rect2(-3, 0, 1, 1), Color(1, 0.95, 0.65, glow * 0.6))
		draw_rect(Rect2(2, -2, 1, 1), Color(1, 0.95, 0.65, glow * 0.6))
	if _player_near():
		WorldPrompt.draw(self, Vector2(0, -14), "E", "Read")
