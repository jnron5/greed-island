class_name CardGate
extends StaticBody2D
## A card-locked gate (GateData). Interact nearby while holding the cost card to
## spend it and open the gate for good. Cards do double duty: the card spent here
## is one you might have needed for the final set.

@export var gate_id: StringName
## Visual width of the gate in pixels (the collision shape is set in the scene).
@export var width := 40.0

var _player_near := false

@onready var body_shape: CollisionShape2D = $CollisionShape2D
@onready var prompt_area: Area2D = $PromptArea


func _ready() -> void:
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


func _draw() -> void:
	var half := width / 2.0
	var stone := Color(0.55, 0.52, 0.48)
	draw_rect(Rect2(-half - 8, -28, 8, 36), stone)
	draw_rect(Rect2(half, -28, 8, 36), stone)
	draw_rect(Rect2(-half - 8, -34, width + 16, 8), stone.darkened(0.15))
	if not is_open():
		# Closed bars with a glowing card slot.
		for i in 5:
			draw_rect(Rect2(-half + 2 + i * (width - 4) / 4.0 - 1, -26, 3, 32), Color(0.3, 0.25, 0.2))
		draw_rect(Rect2(-5, -32, 10, 5), Color(0.95, 0.8, 0.35))
	if _player_near and not is_open():
		var gate := CardDatabase.get_gate(gate_id)
		var card := CardDatabase.get_card(gate.cost_card_id) if gate else null
		if card:
			var text := "E: Open (%d %s)" % [gate.cost_amount, card.display_name]
			var font := ThemeDB.fallback_font
			draw_string_outline(font, Vector2(-half - 10, -40), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
			draw_string(font, Vector2(-half - 10, -40), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color.WHITE)
