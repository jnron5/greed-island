class_name FishingSpot
extends Node2D
## A place to fish (the end of Neri's dock on Lake Serin). Press interact to cast;
## the bobber sits in the water a few seconds, then dips: press interact again while
## it's under to land a fish. Too early and it's spooked, too late and it's gone.
## Walk away and you reel in. Lake trout are food (they mend hearts), so fishing is
## a way to heal that costs time instead of gold.

enum Phase { IDLE, WAITING, BITE }

const RANGE := 40.0
const BITE_WINDOW := 0.75

## Where the bobber lands, relative to the spot.
@export var cast_to := Vector2(-46, 6)
@export var catch_item: StringName = &"lake_trout"

var _phase := Phase.IDLE
var _timer := 0.0
var _near := false
var _rng := RandomNumberGenerator.new()


func _process(delta: float) -> void:
	var near := _player_near()
	if near != _near:
		_near = near
		if not near and _phase != Phase.IDLE:
			_phase = Phase.IDLE
	match _phase:
		Phase.WAITING:
			_timer -= delta
			if _timer <= 0.0:
				_phase = Phase.BITE
				_timer = BITE_WINDOW
				Sfx.play(&"ui_tick")
		Phase.BITE:
			_timer -= delta
			if _timer <= 0.0:
				_phase = Phase.IDLE
				EventBus.notify.emit("It took the bait and swam off.")
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if GameState.menus_open > 0 or not event.is_action_pressed(&"interact") or not _player_near():
		return
	get_viewport().set_input_as_handled()
	match _phase:
		Phase.IDLE:
			cast()
		Phase.WAITING:
			_phase = Phase.IDLE
			EventBus.notify.emit("Too soon. Whatever was nosing the bait is gone.")
		Phase.BITE:
			reel_in()


func cast() -> void:
	_phase = Phase.WAITING
	_timer = _rng.randf_range(2.0, 5.0)


## Lands whatever is on the line: mostly trout, now and then a coin off the bottom.
func reel_in() -> void:
	_phase = Phase.IDLE
	var roll := _rng.randf()
	if roll < 0.85:
		GameState.add_item(catch_item)
		Sfx.play(&"chest")
		var item := Items.get_item(catch_item)
		EventBus.notify.emit("You land a %s!" % (item.display_name if item else "fish"))
	else:
		GameState.add_currency(5)
		Sfx.play(&"coins")
		EventBus.notify.emit("Not a fish: an old coin, green with weed. Five gold.")


func is_waiting() -> bool:
	return _phase == Phase.WAITING


func is_biting() -> bool:
	return _phase == Phase.BITE


func _player_near() -> bool:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	return player != null and player.global_position.distance_to(global_position) <= RANGE


func _draw() -> void:
	if _phase != Phase.IDLE:
		var t := Time.get_ticks_msec() / 1000.0
		var bob := cast_to + Vector2(0, sin(t * 3.0) * 0.8 + (3.0 if _phase == Phase.BITE else 0.0))
		draw_line(Vector2(-4, -22), bob, Color(0.9, 0.9, 0.85, 0.6), 1.0)
		draw_set_transform(cast_to, 0.0, Vector2(1.0, 0.45))
		var ring := 6.0 + fmod(t * 6.0, 8.0)
		draw_arc(Vector2.ZERO, ring, 0, TAU, 20, Color(1, 1, 1, 0.35 * (1.0 - (ring - 6.0) / 8.0)), 1.0)
		draw_set_transform(Vector2.ZERO)
		if _phase == Phase.WAITING:
			draw_circle(bob, 2.2, Color(0.9, 0.2, 0.15))
			draw_circle(bob + Vector2(0, -1), 1.2, Color.WHITE)
		else:
			draw_circle(bob + Vector2(0, 1), 1.6, Color(0.9, 0.2, 0.15, 0.7))
			WorldPrompt.draw(self, Vector2(0, -44), "E", "Reel in!")
		return
	if _near and GameState.menus_open == 0:
		WorldPrompt.draw(self, Vector2(0, -44), "E", "Fish")
