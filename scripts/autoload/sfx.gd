extends Node
## Sound effects (assets/audio/sfx/, made by scripts/tools/make_sfx.py). Sfx.play(&"sword")
## anywhere; a small pool of players so sounds overlap; each play varies its pitch a
## little so repeats don't sound mechanical. Also listens to EventBus for the sounds
## that belong to game events (cards, gold, gates, steals), so gameplay code only calls
## play() for its own actions.

const DIR := "res://assets/audio/sfx/"
const POOL := 10
## Master level for effects, in dB.
var volume_db := -6.0

var _streams: Dictionary[StringName, AudioStream] = {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for i in POOL:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)
	EventBus.card_added.connect(func(who: StringName, _id: StringName) -> void:
		if who == GameState.PLAYER:
			play(&"card"))
	EventBus.currency_changed.connect(_on_currency)
	EventBus.gate_opened.connect(func(_id: StringName, _by: StringName) -> void: play(&"gate"))
	EventBus.card_stolen.connect(func(thief: StringName, victim: StringName, _c: StringName, _m: StringName) -> void:
		if thief == GameState.PLAYER or victim == GameState.PLAYER:
			play(&"steal"))
	EventBus.monster_defeated.connect(func(_k: StringName, _by: StringName) -> void: play(&"monster_down"))


var _gold := -1


func _on_currency(amount: int) -> void:
	if _gold >= 0 and amount > _gold:
		play(&"coins")
	_gold = amount


func play(name: StringName, volume := 0.0, pitch_spread := 0.06) -> void:
	if DisplayServer.get_name() == "headless":
		return
	var stream := _stream(name)
	if stream == null:
		return
	var p := _players[_next]
	_next = (_next + 1) % POOL
	p.stream = stream
	p.volume_db = volume_db + volume
	p.pitch_scale = 1.0 + randf_range(-pitch_spread, pitch_spread)
	p.play()


func _stream(name: StringName) -> AudioStream:
	if not _streams.has(name):
		var path := DIR + String(name) + ".wav"
		_streams[name] = load(path) if ResourceLoader.exists(path) else null
	return _streams[name]


func _exit_tree() -> void:
	for p in _players:
		p.stop()
		p.stream = null
	_streams.clear()
