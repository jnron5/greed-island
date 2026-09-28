class_name Chest
extends StaticBody2D
## A chest out in the world: press interact beside it to open it and take the gold
## inside. Opened once per game (GameState.quest_flags), so it stays open when you come
## back. Its Base collider is a child in the scene; the sprite is set up here.

const RANGE := 30.0

@export var chest_id: StringName
@export var gold := 50
@export var hint := ""
@export var closed_texture: Texture2D
@export var open_texture: Texture2D

var _sprite: Sprite2D
var _near := false


func _ready() -> void:
	_sprite = Sprite2D.new()
	add_child(_sprite)
	_refresh()


func is_open() -> bool:
	return GameState.quest_flags.get(_flag(), false)


func _flag() -> StringName:
	return StringName("chest:%s" % chest_id)


func _refresh() -> void:
	_sprite.texture = open_texture if is_open() else closed_texture
	if _sprite.texture:
		var used := _sprite.texture.get_image().get_used_rect()
		_sprite.position = Vector2(0, _sprite.texture.get_height() / 2.0 - used.end.y)


func _process(_delta: float) -> void:
	var near := _player_near() and not is_open()
	if near != _near:
		_near = near
		queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if is_open() or GameState.menus_open > 0 or not event.is_action_pressed(&"interact") or not _player_near():
		return
	get_viewport().set_input_as_handled()
	open()


func open() -> void:
	if is_open():
		return
	GameState.quest_flags[_flag()] = true
	GameState.add_currency(gold)
	_refresh()
	queue_redraw()
	var lines := PackedStringArray()
	if hint != "":
		lines.append(hint)
	lines.append("Inside: %d gold." % gold)
	DialogueBox.say(get_tree(), "A chest", lines)


func _player_near() -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position) <= RANGE


func _draw() -> void:
	if _near and GameState.menus_open == 0:
		WorldPrompt.draw(self, Vector2(0, -44), "E", "Open")
