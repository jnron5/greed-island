extends Node
## Hearts carry from area to area (walking through a door heals nothing), and a
## room at an inn costs gold, moves the clock on half a day or a full day and mends
## every heart. Every town has an inn keeper who rents rooms.
## Run: godot --headless --path . res://tests/test_inn.tscn

const INNS := {
	"res://scenes/world/interiors/kalmora_tavern.tscn": &"jobelle",
	"res://scenes/world/interiors/sorenda_inn.tscn": &"mate",
	"res://scenes/world/interiors/verdana_inn.tscn": &"tally",
	"res://scenes/world/interiors/seabright_hotel.tscn": &"fennick",
	"res://scenes/world/interiors/frisalle_inn.tscn": &"ottilie",
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

	# Fishing off Neri's dock: cast, wait for the bite, reel in; pulling early spooks it.
	var fisher: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(fisher)
	var spot := FishingSpot.new()
	add_child(spot)
	fisher.global_position = spot.global_position + Vector2(10, 0)
	await get_tree().process_frame
	spot.cast()
	_check("a cast waits for a bite", spot.is_waiting())
	spot._timer = 0.0
	await get_tree().process_frame
	_check("then the float goes under", spot.is_biting())
	var trout := GameState.item_count(&"lake_trout")
	var gold := GameState.currency
	spot.reel_in()
	_check("reeling in on the bite lands a trout (or a coin)",
		GameState.item_count(&"lake_trout") == trout + 1 or GameState.currency == gold + 5)
	_check("a lake trout mends two hearts", Items.get_item(&"lake_trout") != null and Items.get_item(&"lake_trout").heal == 2)
	var lake: Node = load("res://scenes/world/lake_serin.tscn").instantiate()
	_check("Lake Serin has fishing spots (the dock and the wreck)", lake.find_children("FishingSpot*", "", false, false).size() == 2)
	lake.free()
	fisher.queue_free()
	spot.queue_free()

	# Keepers' lines rotate, and carry on from where they were after you leave and
	# come back (a new room scene makes a new Npc).
	var said: Array[String] = []
	for visit in 3:
		var tavern: Node = load("res://scenes/world/interiors/kalmora_tavern.tscn").instantiate()
		var jobelle := tavern.get_node("Npc_jobelle") as Npc
		said.append(jobelle.next_line(jobelle.lines))
		tavern.free()
	_check("Jobelle says something new each visit", said[0] != said[1] and said[1] != said[2])
	# Tally serves dinner at five sharp, and it mends every heart.
	var verdana: Node = load("res://scenes/world/interiors/verdana_inn.tscn").instantiate()
	add_child(verdana)
	await get_tree().process_frame
	var tally := verdana.get_node("Npc_tally") as Npc
	var diner := verdana.get_node("Player") as Player
	diner.health = 1
	TimeOfDay.set_hour(16.5)
	_check("before five, Tally warns you dinner's coming", tally._meal_talk().size() == 1 and diner.health == 1)
	TimeOfDay.set_hour(17.2)
	_check("at five, dinner: every heart mended", tally._meal_talk() == tally.meal_lines and diner.health == diner.max_health)
	TimeOfDay.set_hour(20.0)
	_check("after six, no dinner", tally._meal_talk().is_empty())
	verdana.queue_free()
	await get_tree().process_frame

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
