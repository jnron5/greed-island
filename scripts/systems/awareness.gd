class_name Awareness
extends Node
## Awareness meter for a rival (child of the rival body). Rises while the watched
## target is in the sight cone or within hearing range, scaled by how much noise
## the target makes; decays otherwise. A failed steal attempt alarms it outright
## and leaves the owner wary for a while.

signal level_changed(level: Level)

enum Level { UNAWARE, SUSPICIOUS, ALERT }

## Thresholds with hysteresis so the level doesn't flicker at a boundary.
const SUSPICIOUS_AT := 35.0
const UNAWARE_BELOW := 20.0
const ALERT_AT := 75.0
const CALM_BELOW := 50.0

@export var sight_radius := 130.0
@export var sight_half_angle_deg := 55.0
@export var hearing_radius := 45.0
## Gain per second at point-blank range in the cone; falls off with distance.
@export var sight_gain := 90.0
@export var hearing_gain := 35.0
@export var decay := 18.0
@export var wary_duration := 20.0

var value := 0.0
var level := Level.UNAWARE
var wary_time := 0.0
## Direction the owner is looking; the owner sets this every frame.
var facing := Vector2.DOWN


func update(delta: float, target: Node2D) -> void:
	var gain := perceived_gain(target)
	if wary_time > 0.0:
		wary_time -= delta
		gain *= 1.5
	if gain > 0.0:
		value = minf(value + gain * delta, 100.0)
	else:
		value = maxf(value - decay * (0.5 if is_wary() else 1.0) * delta, 0.0)
	_update_level()


## How fast awareness would rise right now from `target` (0 if unnoticed).
func perceived_gain(target: Node2D) -> float:
	var body := get_parent() as Node2D
	if target == null or body == null:
		return 0.0
	var to := target.global_position - body.global_position
	var dist := to.length()
	var gain := 0.0
	if can_see(to):
		gain = sight_gain * (1.0 - dist / sight_radius) + 10.0
	elif dist <= hearing_radius:
		gain = hearing_gain
	var noise: Variant = target.call(&"noise") if target.has_method(&"noise") else 1.0
	return gain * float(noise)


func can_see(to_target: Vector2) -> bool:
	var dist := to_target.length()
	if dist > sight_radius:
		return false
	return dist < 1.0 or absf(rad_to_deg(facing.angle_to(to_target))) <= sight_half_angle_deg


## Failed steal attempt: straight to alert, and stay wary.
func alarm() -> void:
	value = 100.0
	wary_time = wary_duration
	_update_level()


func bump(amount: float) -> void:
	value = minf(value + amount, 100.0)
	_update_level()


func is_wary() -> bool:
	return wary_time > 0.0


func _update_level() -> void:
	var next := level
	match level:
		Level.UNAWARE:
			if value >= ALERT_AT:
				next = Level.ALERT
			elif value >= SUSPICIOUS_AT:
				next = Level.SUSPICIOUS
		Level.SUSPICIOUS:
			if value >= ALERT_AT:
				next = Level.ALERT
			elif value < UNAWARE_BELOW:
				next = Level.UNAWARE
		Level.ALERT:
			if value < UNAWARE_BELOW:
				next = Level.UNAWARE
			elif value < CALM_BELOW:
				next = Level.SUSPICIOUS
	if next != level:
		level = next
		level_changed.emit(level)
