class_name CardGate
extends StaticBody2D
## A card-locked gate (GateData). Interact nearby while holding the cost card to
## spend it and open the gate for good. Cards do double duty: the card spent here
## is one you might have needed for the final set.

@export var gate_id: StringName
## Visual width of the gate in pixels (the collision shape is set in the scene).
@export var width := 40.0
## Stands across an east-west passage instead of a north-south one.
@export var vertical := false
## How it looks: "gate" (stone posts and a sealed wooden gate, PixelLab art),
## "bars" (iron bars with a card seal, for an archway that is already drawn, like
## Kalmora's north gate) or "seal" (only a glowing card seal, on a drawn door).
@export var look: StringName = &"gate"

const CLOSED := preload("res://assets/sprites/gates/card_gate_closed.png")
const OPEN := preload("res://assets/sprites/gates/card_gate_open.png")
const GAP := 40.0                          # px between the posts in the gate art
const IRON := Color(0.16, 0.15, 0.17)
const IRON_LIGHT := Color(0.42, 0.4, 0.44)
const GOLD := Color(1.0, 0.8, 0.35)

var _time := 0.0

var _player_near := false

@onready var body_shape: CollisionShape2D = $CollisionShape2D
@onready var prompt_area: Area2D = $PromptArea


func _ready() -> void:
	if vertical:
		body_shape.rotation = PI / 2.0
	prompt_area.body_entered.connect(func(b: Node2D) -> void: _set_near(b, true))
	prompt_area.body_exited.connect(func(b: Node2D) -> void: _set_near(b, false))
	EventBus.gate_opened.connect(_on_gate_opened)
	if is_open():
		_apply_open()


func is_open() -> bool:
	return GameState.opened_gates.has(gate_id)


func _set_near(body: Node2D, near: bool) -> void:
	if body is Player:
		_player_near = near
		queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if not _player_near or is_open() or GameState.menus_open > 0 or not event.is_action_pressed(&"interact"):
		return
	get_viewport().set_input_as_handled()
	var gate := CardDatabase.get_gate(gate_id)
	var card := CardDatabase.get_card(gate.cost_card_id)
	if GameState.open_gate(gate_id, GameState.PLAYER):
		EventBus.notify.emit("%s opened (spent %d %s)" % [gate.display_name, gate.cost_amount, card.display_name])
	else:
		EventBus.notify.emit("Needs %d %s" % [gate.cost_amount, card.display_name])


func _on_gate_opened(id: StringName, _by: StringName) -> void:
	if id == gate_id:
		_apply_open()


func _apply_open() -> void:
	body_shape.set_deferred(&"disabled", true)
	queue_redraw()


func _process(delta: float) -> void:
	_time += delta
	if not is_open():
		queue_redraw()


func _draw() -> void:
	var glow := 0.75 + 0.25 * sin(_time * 3.0)
	match look:
		&"bars":
			if not is_open():
				var half := width / 2.0
				for i in 6:
					var x := roundf(-half + 3 + i * (width - 6) / 5.0)
					draw_rect(Rect2(x - 1, -30, 3, 34), IRON)
					draw_rect(Rect2(x - 1, -30, 1, 34), IRON_LIGHT)
					draw_rect(Rect2(x - 1, -33, 3, 3), GOLD.darkened(0.3))          # spear tips
				draw_rect(Rect2(-half, -22, width, 3), IRON)
				draw_rect(Rect2(-half, -6, width, 3), IRON)
				_draw_seal(Vector2(0, -16), glow)
		&"seal":
			if not is_open():
				_draw_seal(Vector2(0, -14), glow)
		_:
			if vertical:
				_draw_side_on(glow)
			else:
				var tex := OPEN if is_open() else CLOSED
				var sx := width / GAP
				var size := Vector2(tex.get_width() * sx, tex.get_height())
				draw_texture_rect(tex, Rect2(Vector2(-size.x / 2.0, 8 - 72), size), false)
				if not is_open():
					draw_circle(Vector2(0, -38), 7.0, Color(1.0, 0.8, 0.35, 0.18 * glow))   # the seal's glow
	if _player_near and not is_open():
		var gate := CardDatabase.get_gate(gate_id)
		var card := CardDatabase.get_card(gate.cost_card_id) if gate else null
		if card:
			WorldPrompt.draw(self, Vector2(0, -44), "E", "Open (%d %s)" % [gate.cost_amount, card.display_name])


## Across an east-west passage the same gate is seen from the side: one post behind
## the other (north further up the screen), and between them the gate itself edge-on,
## a narrow wooden panel with iron bands and the gold seal on its face. Opened, the
## two leaves stand folded back against the posts.
func _draw_side_on(glow: float) -> void:
	var half := width / 2.0
	var post := Rect2(8, 10, 24, 62)                  # the left post in the gate art, with its moss
	var wood := Color(0.36, 0.2, 0.13)
	var wood_light := Color(0.5, 0.3, 0.18)
	var iron := Color(0.2, 0.2, 0.24)
	# The north post first (it's further away), then the gate, then the south post.
	draw_texture_rect_region(CLOSED, Rect2(Vector2(-post.size.x / 2.0, -half - post.size.y + 6), post.size), post)
	if is_open():
		for y0 in [-half + 2.0, half - 10.0]:
			draw_rect(Rect2(-2, y0 - 26, 4, 34), wood)
			draw_rect(Rect2(-2, y0 - 26, 1, 34), wood_light)
	else:
		var top := -half - 30.0
		draw_rect(Rect2(-3, top, 6, width + 30), wood)
		draw_rect(Rect2(-3, top, 2, width + 30), wood_light)
		for y in [top + 8.0, half - 10.0]:
			draw_rect(Rect2(-4, y, 8, 3), iron)
		_draw_seal(Vector2(0, top + (width + 30) / 2.0), glow)
	draw_texture_rect_region(CLOSED, Rect2(Vector2(-post.size.x / 2.0, half - post.size.y + 6), post.size), post)


## A small card-shaped plate glowing gold: pay a card here to open.
func _draw_seal(at: Vector2, glow: float) -> void:
	draw_circle(at, 9.0, Color(1.0, 0.8, 0.35, 0.18 * glow))
	draw_rect(Rect2(at + Vector2(-4, -6), Vector2(8, 11)), Color(0.18, 0.1, 0.05))
	draw_rect(Rect2(at + Vector2(-3, -5), Vector2(6, 9)), GOLD * Color(glow, glow, glow))
	draw_rect(Rect2(at + Vector2(-1, -2), Vector2(2, 3)), Color(0.45, 0.2, 0.1))
