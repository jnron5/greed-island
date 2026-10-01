extends Node
## Hearts carry from area to area (walking through a door heals nothing), and a
## room at an inn costs gold, moves the clock on half a day or a full day and mends
## every heart. Every town has an inn keeper who rents rooms.
## Run: godot --headless --path . res://tests/test_inn.tscn

const INNS := {
	"res://scenes/world/interiors/kalmora_tavern.tscn": &"jobelle",
	"res://scenes/world/interiors/sorenda_inn.tscn": &"mate",
	"res://scenes/world/interiors/verdana_inn.tscn": &"tally",
}

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)
	# Hurt in one place, still hurt in the next.
	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(player)
	await get_tree().process_frame
	_check("a new wanderer starts whole", player.health == player.max_health)
	player.health = 2
	player.queue_free()
	await get_tree().process_frame
	var next: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(next)
	await get_tree().process_frame
	_check("arriving somewhere new doesn't heal", next.health == 2)

	# A room: pay, sleep, wake whole, the clock moved on.
	GameState.currency = 5
	TimeOfDay.set_hour(20.0)
	_check("no room for an empty purse", not Inn.sleep(get_tree(), 12.0, Inn.HALF_DAY_PRICE)
		and GameState.currency == 5 and next.health == 2)
	GameState.currency = 100
	_check("half a day's sleep", Inn.sleep(get_tree(), 12.0, Inn.HALF_DAY_PRICE)
		and GameState.currency == 100 - Inn.HALF_DAY_PRICE)
	_check("wake at eight in the morning", is_equal_approx(TimeOfDay.hour, 8.0))
	_check("every heart mended", next.health == next.max_health)
	next.health = 1
	_check("a full day's sleep", Inn.sleep(get_tree(), 24.0, Inn.FULL_DAY_PRICE)
		and is_equal_approx(TimeOfDay.hour, 8.0) and next.health == next.max_health)
	next.queue_free()

	# Every town's inn has a keeper who rents rooms.
	for path: String in INNS:
		var room: Node = load(path).instantiate()
		var keeper := room.get_node_or_null("Npc_%s" % INNS[path]) as Npc
		_check("%s: %s rents rooms" % [path.get_file(), INNS[path]], keeper != null and keeper.inn_rooms)
		room.free()
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
