class_name Chest
extends StaticBody2D
## A chest out in the world: press interact beside it to open it and take what's
## inside (a card, gold, a satchel item, or several). Every collector (the player and
## each rival) opens it once: a rival getting there first doesn't empty it for you
## (GameState.collected_pickups, keyed per collector by WorldMap.taken_key, so WorldMap
## reads chests straight from the scene files and off-screen rivals loot them too).
## A chest behind a gate only opens once that gate is open. It looks open once the
## player has opened it.
## Its Base collider is a child in the scene; the sprite is set up here.

const RANGE := 30.0

@export var chest_id: StringName
@export var card_id: StringName
@export var gold := 0
## A satchel item inside (bread, a tonic), and how many.
@export var item_id: StringName
@export var item_count := 1
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
	if card_id != &"":
		add_to_group(&"card_pickups")
	_refresh()


## Whether the player has opened it (what the sprite shows).
func is_open() -> bool:
	return is_open_for(GameState.PLAYER)


func is_open_for(collector: StringName) -> bool:
	return GameState.collected_pickups.has(WorldMap.taken_key(persist_key(), collector))


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


## The player opens it: what was inside goes to them, and a line says what it was
## (no dialogue: a new card pops up on its own the first time you get one).
func open() -> void:
	if is_open() or not open_for(GameState.PLAYER):
		return
	Sfx.play(&"chest")
	var found := PackedStringArray()
	if card_id != &"":
		var card := CardDatabase.get_card(card_id)
		found.append("a card: %s" % (card.display_name if card else String(card_id)))
	if item_id != &"" and Items.get_item(item_id):
		var item := Items.get_item(item_id)
		found.append(("%s x%d" % [item.display_name, item_count]) if item_count > 1 else item.display_name)
	if gold > 0:
		found.append("%d gold" % gold)
	EventBus.notify.emit("Found %s" % (", ".join(found) if not found.is_empty() else "nothing but dust"))


## Anyone opens it (a rival walking up to it calls this too). Returns false if it was
## already open or its gate is still shut.
func open_for(collector: StringName) -> bool:
	if is_open_for(collector) or (behind_gate != &"" and not GameState.opened_gates.has(behind_gate)):
		return false
	GameState.collected_pickups[WorldMap.taken_key(persist_key(), collector)] = true
	if card_id != &"":
		GameState.add_loose_card(collector, card_id)
	if collector == GameState.PLAYER:
		if gold > 0:
			GameState.add_currency(gold)
		if item_id != &"":
			GameState.add_item(item_id, item_count)
	_refresh()
	queue_redraw()
	return true


func _player_near() -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position) <= RANGE


func _draw() -> void:
	if _near and GameState.menus_open == 0:
		WorldPrompt.draw(self, Vector2(0, -44), "E", "Open")
