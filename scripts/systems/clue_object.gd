class_name ClueObject
extends StaticBody2D
## Something the player can examine with interact (quest clues, notes, signs).
## What it says comes from Quests.inspect(clue_id); a sparkle shows while it
## still has something new to tell.

const RANGE := 30.0

@export var clue_id: StringName
@export var title := "Unmarked crate"
@export var texture: Texture2D


func _ready() -> void:
	Quests.quest_changed.connect(func(_id: StringName, _s: int) -> void: queue_redraw())


func _process(_delta: float) -> void:
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if GameState.menus_open > 0 or not event.is_action_pressed(&"interact") or not _player_near():
		return
	get_viewport().set_input_as_handled()
	DialogueBox.say(get_tree(), title, Quests.inspect(clue_id))


func _player_near() -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position) <= RANGE


func _draw() -> void:
	if texture:
		var bottom := texture.get_height()
		draw_texture(texture, Vector2(-texture.get_width() / 2.0, -bottom + 2))
	var fresh := Quests.stage(&"unmarked_cargo") == 1 and not Quests.clue_found(clue_id)
	if fresh:
		var t := Time.get_ticks_msec() / 300.0
		draw_circle(Vector2(0, -28 + sin(t) * 2.0), 2.0 + sin(t * 1.7), Color(1, 0.95, 0.6, 0.9))
	if _player_near():
		var font := ThemeDB.fallback_font
		draw_string_outline(font, Vector2(-18, -36), "E: Look", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
		draw_string(font, Vector2(-18, -36), "E: Look", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color.WHITE)
