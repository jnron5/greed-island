extends Node
## The island clock. One in-game day passes in DAY_SECONDS of play. Zones tint
## themselves with tint() (a CanvasModulate), and lamps glow with night_factor().
## Interiors ignore the clock and keep their own warm light.

signal hour_changed(hour: float)

## 30 minutes of play per day (12 was too quick to enjoy either half).
const DAY_SECONDS := 1800.0
const START_HOUR := 16.0

## Colour of the world at each hour (wraps at 24).
const KEYS := [
	[0.0, Color(0.3, 0.36, 0.56)],
	[5.0, Color(0.36, 0.4, 0.6)],
	[6.5, Color(0.95, 0.78, 0.7)],
	[8.0, Color(1.0, 0.97, 0.92)],
	[16.0, Color(1.0, 0.95, 0.86)],
	[18.5, Color(1.0, 0.78, 0.6)],
	[20.0, Color(0.62, 0.58, 0.78)],
	[21.5, Color(0.32, 0.37, 0.58)],
	[24.0, Color(0.3, 0.36, 0.56)],
]

var hour := START_HOUR
## Days gone by since the race began (travellers move on each day).
var day := 0
## Tests and screenshots freeze the clock.
var paused := false


func _process(delta: float) -> void:
	if paused:
		return
	var next := hour + delta * 24.0 / DAY_SECONDS
	if next >= 24.0:
		day += 1
	hour = fmod(next, 24.0)
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


## The hour as people say it: "Dawn", "Morning", ... "Night".
func part_of_day() -> String:
	if hour >= 5.0 and hour < 7.0:
		return "Dawn"
	if hour >= 7.0 and hour < 11.0:
		return "Morning"
	if hour >= 11.0 and hour < 14.0:
		return "Midday"
	if hour >= 14.0 and hour < 17.5:
		return "Afternoon"
	if hour >= 17.5 and hour < 20.5:
		return "Dusk"
	return "Night"


## Night, when the wild is more dangerous (and residents keep their night spots).
func is_night() -> bool:
	return hour >= 20.0 or hour < 6.5


func set_hour(value: float) -> void:
	day += int(floorf(value / 24.0)) if value >= 24.0 else 0
	hour = fmod(value, 24.0)
	hour_changed.emit(hour)
