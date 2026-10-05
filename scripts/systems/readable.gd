class_name Readable
extends Node2D
## Something in a room worth a closer look (a letter, a ledger, a portrait): press
## interact nearby to read it in the dialogue box. Invisible itself (the art draws
## it); until it's been read once this game a gold four-point star bobs over it with
## a soft glow on the ground, brighter and with a "!" when a running quest wants it
## (`Quests.wants`). Once read, a small faint star stays so it can be found again.

const RANGE := 26.0

@export var title := "Note"
@export_multiline var lines: PackedStringArray = []
## What it reads after dark instead (a telescope on the sea, a window), if anything.
@export_multiline var night_lines: PackedStringArray = []

var _time := randf() * TAU


func _ready() -> void:
	# Only a sparkle and a prompt are drawn here: keep them over whoever stands close.
	z_index = 20


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if GameState.menus_open > 0 or not event.is_action_pressed(&"interact") or not _player_near():
		return
	get_viewport().set_input_as_handled()
	GameState.quest_flags[_read_key()] = true
	var at_night := not night_lines.is_empty() and Npc.is_night()
	var text := night_lines if at_night else lines
	var zone := Zone.current(get_tree())
	GameState.note(title, zone.display_name if zone else "", text)
	Quests.read(title, at_night)
	DialogueBox.say(get_tree(), title, text)


func _read_key() -> StringName:
	return StringName("read:%s:%s" % [owner.scene_file_path if owner else "", name])


func _player_near() -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position) <= RANGE


func _draw() -> void:
	var unread: bool = not GameState.quest_flags.get(_read_key(), false)
	var wanted := Quests.wants(title, Npc.is_night())
	if unread or wanted:
		WorldPrompt.interest(self, Vector2.ZERO, -14.0, _time, wanted)
	else:
		WorldPrompt.star(self, Vector2(0, -8), 3.0, Color(WorldPrompt.INTEREST, 0.35), 0.8)
	if _player_near():
		WorldPrompt.draw(self, Vector2(0, -28), "E", "Read")
