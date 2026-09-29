class_name ZoneExit
extends Area2D
## Takes the player to another zone scene, arriving at the spawn marker named
## `target_spawn` there. Edge exits trigger by walking into them; doors
## (`needs_interact`) show a prompt and wait for the interact key. An interior's way
## out (`exit_hint`) shows a bobbing gold arrow when the player is close.

const DOOR_RANGE := 26.0
const HINT_RANGE := 90.0

@export_file("*.tscn") var target_scene: String
@export var target_spawn: StringName
@export var needs_interact := false
@export var prompt := "Enter"
@export var exit_hint := false

var _near := false


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	set_process(needs_interact or exit_hint)
	if needs_interact or exit_hint:
		z_index = 20  # The prompt draws over the player standing at the door.


func _process(_delta: float) -> void:
	if exit_hint:
		queue_redraw()
		return
	var near := _player_near()
	if near != _near:
		_near = near
		queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not needs_interact or GameState.menus_open > 0 or not event.is_action_pressed(&"interact") \
			or not _player_near():
		return
	get_viewport().set_input_as_handled()
	_go()


func _on_body_entered(body: Node2D) -> void:
	if body is Player and not needs_interact:
		_go()


func _go() -> void:
	if target_scene == "":
		return
	GameState.pending_spawn = target_spawn
	if needs_interact:
		Sfx.play(&"door")
	Transition.go(target_scene)


func _player_near(within := DOOR_RANGE) -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position) <= within


func _draw() -> void:
	if exit_hint and _player_near(HINT_RANGE):
		WorldPrompt.marker(self, Vector2(0, -14), "v", Color(1.0, 0.84, 0.45))
	if _near and GameState.menus_open == 0:
		WorldPrompt.draw(self, Vector2(0, -40), "E", prompt)
