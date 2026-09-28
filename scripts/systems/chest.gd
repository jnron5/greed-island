class_name Chest
extends StaticBody2D
## A chest out in the world: press interact beside it to open it and take what's
## inside (a card, gold, or both). Opened once per game by whoever gets there first,
## player or rival (GameState.collected_pickups, keyed like the old card pickups, so
## WorldMap reads chests straight from the scene files and off-screen rivals can
## loot them too). A chest behind a gate only opens once that gate is open.
## Its Base collider is a child in the scene; the sprite is set up here.

const RANGE := 30.0

@export var chest_id: StringName
@export var card_id: StringName
@export var gold := 0
@export var hint := ""
## The gate you must open to reach this chest, if any (rivals pay it like a pickup's).
@export var behind_gate: StringName
@export var closed_texture: Texture2D
@export var open_texture: Texture2D

var _sprite: Sprite2D
var _near := false


func _ready() -> void:
	_sprite = Sprite2D.new()
	add_child(_sprite)
	if card_id != &"" and not is_open():
		add_to_group(&"card_pickups")
	_refresh()


func is_open() -> bool:
	return GameState.collected_pickups.has(persist_key())


func persist_key() -> String:
	if owner and owner.scene_file_path != "":
		return CardPickup.persist_key(owner.scene_file_path, String(owner.get_path_to(self)))
	return "chest:%s" % chest_id


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


## The player opens it: the card and gold go to them, with a word about what was inside.
func open() -> void:
	if is_open():
		return
	open_for(GameState.PLAYER)
	var lines := PackedStringArray()
	if hint != "":
		lines.append(hint)
	var found := PackedStringArray()
	if card_id != &"":
		var card := CardDatabase.get_card(card_id)
		found.append("a card: %s" % (card.display_name if card else String(card_id)))
	if gold > 0:
		found.append("%d gold" % gold)
	lines.append("Inside: %s." % (" and ".join(found) if not found.is_empty() else "nothing but dust"))
	DialogueBox.say(get_tree(), "A chest", lines)


## Anyone opens it (a rival walking up to it calls this too). Returns false if it was
## already open or its gate is still shut.
func open_for(collector: StringName) -> bool:
	if is_open() or (behind_gate != &"" and not GameState.opened_gates.has(behind_gate)):
		return false
	GameState.collected_pickups[persist_key()] = true
	remove_from_group(&"card_pickups")
	if card_id != &"":
		GameState.add_loose_card(collector, card_id)
	if gold > 0 and collector == GameState.PLAYER:
		GameState.add_currency(gold)
	_refresh()
	queue_redraw()
	return true


func _player_near() -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position) <= RANGE


func _draw() -> void:
	if _near and GameState.menus_open == 0:
		WorldPrompt.draw(self, Vector2(0, -44), "E", "Open")
