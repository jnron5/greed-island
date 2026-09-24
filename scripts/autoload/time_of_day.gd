extends Node
## The island clock. One in-game day passes in DAY_SECONDS of play. Zones tint
## themselves with tint() (a CanvasModulate), and lamps glow with night_factor().
## Interiors ignore the clock and keep their own warm light.

signal hour_changed(hour: float)

const DAY_SECONDS := 720.0
const START_HOUR := 16.0

## Colour of the world at each hour (wraps at 24).
const KEYS := [
	[0.0, Color(0.36, 0.42, 0.62)],
	[5.0, Color(0.42, 0.46, 0.66)],
	[6.5, Color(0.95, 0.78, 0.7)],
	[8.0, Color(1.0, 0.97, 0.92)],
	[16.0, Color(1.0, 0.95, 0.86)],
	[18.5, Color(1.0, 0.78, 0.6)],
	[20.0, Color(0.62, 0.58, 0.78)],
	[21.5, Color(0.38, 0.43, 0.64)],
	[24.0, Color(0.36, 0.42, 0.62)],
]

var hour := START_HOUR
## Tests and screenshots freeze the clock.
var paused := false


func _process(delta: float) -> void:
	if paused:
		return
	hour = fmod(hour + delta * 24.0 / DAY_SECONDS, 24.0)
	hour_changed.emit(hour)


func tint() -> Color:
	for i in KEYS.size() - 1:
		var a: Array = KEYS[i]
		var b: Array = KEYS[i + 1]
		if hour >= a[0] and hour <= b[0]:
			return (a[1] as Color).lerp(b[1], (hour - a[0]) / (b[0] - a[0]))
	return KEYS[0][1]


## 0 in daylight, 1 at night; lamps scale their energy by this.
func night_factor() -> float:
	if hour >= 7.0 and hour <= 17.5:
		return 0.0
	if hour > 17.5 and hour < 20.5:
		return (hour - 17.5) / 3.0
	if hour > 5.0 and hour < 7.0:
		return (7.0 - hour) / 2.0
	return 1.0


func set_hour(value: float) -> void:
	hour = fmod(value, 24.0)
	hour_changed.emit(hour)
