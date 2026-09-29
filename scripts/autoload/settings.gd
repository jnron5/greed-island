extends Node
## Player settings kept between sessions (user://settings.cfg): sound levels for now.
## 0..1 on the sliders, applied to Sfx and Ambience as decibels.

const PATH := "user://settings.cfg"

var sfx_volume := 0.8
var ambience_volume := 0.7


func _ready() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(PATH) == OK:
		sfx_volume = cfg.get_value("sound", "sfx", sfx_volume)
		ambience_volume = cfg.get_value("sound", "ambience", ambience_volume)
	_apply()


func set_sfx(v: float) -> void:
	sfx_volume = v
	_apply()
	_save()
	Sfx.play(&"ui_tick")


func set_ambience(v: float) -> void:
	ambience_volume = v
	_apply()
	_save()


func _apply() -> void:
	Sfx.volume_db = _db(sfx_volume) - 2.0
	Ambience.set_volume(_db(ambience_volume) - 6.0)


static func _db(v: float) -> float:
	return -80.0 if v <= 0.001 else linear_to_db(v)


func _save() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("sound", "sfx", sfx_volume)
	cfg.set_value("sound", "ambience", ambience_volume)
	cfg.save(PATH)
