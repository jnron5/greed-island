class_name Npc
extends CharacterBody2D
## A resident of the island (a dog or cat townsperson). Idles or wanders near
## home, turns to face you, and talks when you press interact nearby. What it
## says comes from the quest system first (Quests.dialogue_for), then its own
## ambient lines, cycling. 4-directional animations "idle_<dir>" / "walk_<dir>".

const DIRECTIONS_4: Array[String] = ["east", "south", "west", "north"]
const TALK_RANGE := 34.0

@export var npc_id: StringName
@export var display_name := "Resident"
@export var sprite_frames: SpriteFrames
@export var sprite_offset_y := -26.0
## Ambient things to say, one line per conversation (in order, looping).
@export_multiline var lines: PackedStringArray = []
## 0 = stands still at home.
@export var wander_radius := 0.0
@export var walk_speed := 30.0
## Shopkeepers: after talking, open the shop with this stock.
@export var shop_stock: Array[StringName] = []

var facing := Vector2.DOWN

var _home := Vector2.ZERO
var _goal := Vector2.ZERO
var _wait := 0.0
var _talking := false
var _line_index := 0

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
	add_to_group(&"npcs")
	if sprite_frames:
		sprite.sprite_frames = sprite_frames
	sprite.offset.y = sprite_offset_y
	_home = position
	_goal = position
	_wait = randf_range(1.0, 4.0)


func _physics_process(delta: float) -> void:
	if _talking:
		velocity = Vector2.ZERO
	elif wander_radius > 0.0:
		_wait -= delta
		if position.distance_to(_goal) < 3.0:
			velocity = Vector2.ZERO
			if _wait <= 0.0:
				_goal = _home + Vector2.from_angle(randf() * TAU) * randf_range(8.0, wander_radius)
				_wait = randf_range(2.0, 5.0)
		else:
			velocity = position.direction_to(_goal) * walk_speed
			if _wait < -6.0:
				_goal = position  # Stuck against something: give up on this spot.
	move_and_slide()
	_update_animation()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if _talking or GameState.menus_open > 0 or not event.is_action_pressed(&"interact"):
		return
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if player == null or player.global_position.distance_to(global_position) > TALK_RANGE:
		return
	get_viewport().set_input_as_handled()
	talk(player)


func talk(player: Node2D) -> void:
	_talking = true
	facing = global_position.direction_to(player.global_position)
	var quest_lines := Quests.dialogue_for(npc_id)
	var said: PackedStringArray = quest_lines
	if said.is_empty() and not lines.is_empty():
		said = PackedStringArray([lines[_line_index % lines.size()]])
		_line_index += 1
	DialogueBox.say(get_tree(), display_name, said, _done_talking)


func _done_talking() -> void:
	_talking = false
	Quests.talked_to(npc_id)
	if not shop_stock.is_empty():
		var shop := get_tree().get_first_node_in_group(&"shop_panel") as ShopPanel
		if shop:
			shop.open_with(shop_stock)


func _update_animation() -> void:
	if sprite.sprite_frames == null:
		return
	if velocity.length() > 1.0:
		facing = velocity.normalized()
	var dir := DIRECTIONS_4[wrapi(roundi(facing.angle() / (PI / 2.0)), 0, 4)]
	var action := "walk" if velocity.length() > 1.0 else "idle"
	for candidate in [action, "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	var marker := Quests.marker_for(npc_id)
	var font := ThemeDB.fallback_font
	if marker != "":
		draw_string_outline(font, Vector2(-3, sprite_offset_y * 2 - 8), marker, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, 3, Color.BLACK)
		draw_string(font, Vector2(-3, sprite_offset_y * 2 - 8), marker, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(1, 0.85, 0.3))
	if player and not _talking and player.global_position.distance_to(global_position) <= TALK_RANGE:
		var text := "E: Talk"
		draw_string_outline(font, Vector2(-14, sprite_offset_y * 2 + 4), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
		draw_string(font, Vector2(-14, sprite_offset_y * 2 + 4), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color.WHITE)
