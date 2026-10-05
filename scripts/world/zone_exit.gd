class_name ZoneExit
extends Area2D
## Takes the player to another zone scene, arriving at the spawn marker named
## `target_spawn` there. Edge exits trigger by walking into them; doors
## (`needs_interact`) show a prompt and wait for the interact key. An interior's way
## out (`exit_hint`) shows a bobbing gold arrow when the player is close.
## An exit near the edge of the zone's ground grows to cover the whole opening and
## everything past it (`_fit_to_edge`), so walking off anywhere near it leaves; the
## zone walls the rest of its edge (`Zone._wall_edges`).

const DOOR_RANGE := 26.0
const HINT_RANGE := 90.0
## Edge exits: how close to the ground's edge counts, how wide the opening is taken
## to be, how far inside the edge it starts and how far past it reaches.
const EDGE_NEAR := 72.0
const EDGE_SPAN := 220.0
const EDGE_IN := 28.0
const EDGE_OUT := 400.0

@export_file("*.tscn") var target_scene: String
@export var target_spawn: StringName
@export var needs_interact := false
@export var prompt := "Enter"
@export var exit_hint := false

var _near := false
## Which way the zone's edge lies from here (zero: not an edge exit).
var edge_side := Vector2.ZERO


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	_fit_to_edge()
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


## Grows a walk-in exit by the zone's edge into a band across the whole opening.
func _fit_to_edge() -> void:
	var zone := get_parent() as Zone
	if needs_interact or exit_hint or zone == null or zone.interior:
		return
	var rect := zone.ground_rect()
	if not rect.has_area():
		return
	var p := position
	var sides := {
		Vector2.LEFT: p.x - rect.position.x, Vector2.RIGHT: rect.end.x - p.x,
		Vector2.UP: p.y - rect.position.y, Vector2.DOWN: rect.end.y - p.y,
	}
	var side := Vector2.ZERO
	for s: Vector2 in sides:
		if side == Vector2.ZERO or sides[s] < sides[side]:
			side = s
	var d: float = sides[side]
	if d > EDGE_NEAR:
		return
	edge_side = side
	rotation = 0.0  # (side-on exits were turned to fit their old small box)
	var start := minf(-8.0, d - EDGE_IN)
	var depth := d + EDGE_OUT - start
	var box := RectangleShape2D.new()
	box.size = Vector2(depth, EDGE_SPAN) if side.x != 0 else Vector2(EDGE_SPAN, depth)
	var collider := get_node(^"CollisionShape2D") as CollisionShape2D
	collider.shape = box
	collider.position = side * (start + depth / 2.0)


func _go() -> void:
	if target_scene == "" or Transition.busy:
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
