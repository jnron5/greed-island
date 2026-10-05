extends Node
## Travellers roam the towns and the wild, moving on each day, never wearing a local's
## face, talking about the place they're in; and after dark the wild's monsters turn
## savage (tougher, harder-hitting, richer) with a warning when night falls, but not
## underground.
## Run: godot --headless --path . res://tests/test_travellers.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)
	TimeOfDay.day = 3
	var seen := {}
	var twice := false
	var local := false
	for zone: String in Travellers.QUOTA:
		var here := Travellers.todays(zone)
		_check("%s gets its %d travellers" % [zone.get_file(), Travellers.QUOTA[zone]], here.size() == Travellers.QUOTA[zone])
		for t: Dictionary in here:
			twice = twice or seen.has(t.id)
			seen[t.id] = true
			local = local or t.sprite in Travellers.LOCAL_SPRITES.get(zone, [])
	_check("nobody is in two places at once", not twice)
	_check("no traveller wears a local's face", not local)
	var today := Travellers.todays(WorldMap.KALMORA).map(func(t: Dictionary) -> String: return t.id)
	TimeOfDay.day = 4
	var tomorrow := Travellers.todays(WorldMap.KALMORA).map(func(t: Dictionary) -> String: return t.id)
	_check("they move on the next day", today != tomorrow)

	TimeOfDay.set_hour(12.0)
	var town := await _load(WorldMap.KALMORA)
	var walkers := town.get_children().filter(func(n: Node) -> bool: return n is Npc and String(n.name).begins_with("Traveller_"))
	_check("Kalmora has its travellers out by day", walkers.size() == 5 and walkers.all(func(n: Npc) -> bool: return n.visible))
	var npc := walkers[0] as Npc if not walkers.is_empty() else null
	_check("they roam the town", npc != null and npc.roam_points.size() > 4)
	_check("and talk about Kalmora", npc != null and Array(npc.lines).any(func(l: String) -> bool: return l in Travellers.CITY_LINES.kalmora))
	await get_tree().create_timer(4.0).timeout
	_check("and actually walk", walkers.any(func(n: Npc) -> bool: return n.velocity.length() > 1.0 or n.position.distance_to(n.roam_points[0]) > 0.0))

	var forest := await _load(WorldMap.THORNVEIL)
	var road := forest.get_children().filter(func(n: Node) -> bool: return n is Npc and String(n.name).begins_with("Traveller_"))
	_check("a traveller on the forest road talks about the road", road.size() == 1
		and Array((road[0] as Npc).lines).any(func(l: String) -> bool: return l in Travellers.WILD_LINES))
	var beast := get_tree().get_first_node_in_group(&"monsters") as Monster
	var day_health := beast.max_health
	var day_hit := beast.attack_damage
	_check("by day a monster is itself", not beast.night)
	var notes: Array[String] = []
	EventBus.notify.connect(func(t: String) -> void: notes.append(t))
	TimeOfDay.set_hour(22.0)
	beast._update_night()
	_check("after dark it's savage", beast.night and beast.max_health > day_health and beast.attack_damage == day_hit + 1)
	forest._night_clock = 0.0
	await get_tree().process_frame
	await get_tree().process_frame
	_check("and you're told so", notes.any(func(t: String) -> bool: return t.begins_with("Night has fallen")))
	TimeOfDay.set_hour(8.0)
	beast._update_night()
	_check("dawn calms it", not beast.night and beast.max_health == day_health)

	TimeOfDay.set_hour(22.0)
	var cave := await _load(WorldMap.SORENDA_HOLLOW)
	var bear := get_tree().get_first_node_in_group(&"monsters") as Monster
	_check("underground there's no night", bear != null and not bear.night)
	_check("and no travellers", not cave.get_children().any(func(n: Node) -> bool: return String(n.name).begins_with("Traveller_")))
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _load(path: String) -> Zone:
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame
	while get_tree().current_scene == null or get_tree().current_scene.scene_file_path != path:
		await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().physics_frame
	return get_tree().current_scene as Zone


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
