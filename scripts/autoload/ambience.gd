extends Node
## The background soundscape (assets/audio/ambience/, made by make_ambience.py): each
## place gets a looping bed, crossfaded as you arrive: the harbor's surf and gulls in
## Kalmora, wind and birds in the forest (crickets after dark), a hum and drips in
## caves, a hearth's crackle indoors; wind and larks on the plains, lapping water at Lake
## Serin, wind moaning over the Starfall Range.

const DIR := "res://assets/audio/ambience/"
const FADE := 1.5
var volume_db := -10.0

var _a: AudioStreamPlayer
var _b: AudioStreamPlayer
var _current := &""
var _outdoor_forest := false


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_a = AudioStreamPlayer.new()
	_b = AudioStreamPlayer.new()
	add_child(_a)
	add_child(_b)
	EventBus.area_entered.connect(func(_t: String, _i: bool) -> void: _pick.call_deferred())


func _process(_delta: float) -> void:
	# The forest's bed follows the hour.
	if _outdoor_forest:
		var bed := &"forest_night" if TimeOfDay.night_factor() > 0.6 else &"forest_day"
		if bed != _current:
			_play(bed)


func _pick() -> void:
	var zone := get_tree().current_scene as Zone
	_outdoor_forest = false
	if zone == null:
		_play(&"")
		return
	if zone.interior:
		_play(&"room")
	elif zone.underground:
		_play(&"cave")
	elif zone.scene_file_path in [WorldMap.KALMORA, WorldMap.SEABRIGHT]:
		_play(&"harbor")
	elif zone.scene_file_path in [WorldMap.AUREWIND, WorldMap.VERDANA]:
		_play(&"meadow")
	elif zone.scene_file_path == WorldMap.LAKE_SERIN:
		_play(&"lake")
	elif zone.scene_file_path in [WorldMap.STARFALL, WorldMap.FRISALLE]:
		_play(&"mountain")
	else:
		_outdoor_forest = true
		_play(&"forest_night" if TimeOfDay.night_factor() > 0.6 else &"forest_day")


func _play(bed: StringName) -> void:
	if bed == _current or DisplayServer.get_name() == "headless":
		return
	_current = bed
	var old := _a if _a.playing else _b
	var new := _b if old == _a else _a
	if old.playing:
		var t := create_tween()
		t.tween_property(old, "volume_db", -60.0, FADE)
		t.tween_callback(old.stop)
	if bed == &"":
		return
	var stream := load(DIR + String(bed) + ".wav") as AudioStreamWAV
	if stream == null:
		return
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_begin = 0
	stream.loop_end = stream.data.size() / 2
	new.stream = stream
	new.volume_db = -60.0
	new.play()
	create_tween().tween_property(new, "volume_db", volume_db, FADE)


func set_volume(db: float) -> void:
	volume_db = db
	for p in [_a, _b]:
		if p.playing and p.volume_db > -59.0:
			p.volume_db = db
