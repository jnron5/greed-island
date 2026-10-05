extends Node
## Travellers roam the towns and the wild by day, moving on each day, talking about
## the place they're in, and all come back to Kalmora for the night; and after dark the wild's monsters turn
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
	for zone: String in Travellers.QUOTA:
		var here := Travellers.todays(zone)
		_check("%s gets its %d travellers" % [zone.get_file(), Travellers.QUOTA[zone]], here.size() == Travellers.QUOTA[zone])
		for t: Dictionary in here:
			twice = twice or seen.has(t.id)
			seen[t.id] = true
	_check("nobody is in two places at once", not twice)
	_check("they wear the traveller sprites", Travellers.ROSTER.all(func(t: Dictionary) -> bool:
		return String(t.sprite).begins_with("traveller_") and ResourceLoader.exists("res://assets/sprites/npcs/%s/%s_frames.tres" % [t.sprite, t.sprite])))
	var today := Travellers.todays(WorldMap.KALMORA).map(func(t: Dictionary) -> String: return t.id)
	TimeOfDay.day = 4
	var tomorrow := Travellers.todays(WorldMap.KALMORA).map(func(t: Dictionary) -> String: return t.id)
	_check("they move on the next day", today != tomorrow)

	TimeOfDay.set_hour(12.0)
	var town := await _load(WorldMap.KALMORA)
	var walkers := town.get_children().filter(func(n: Node) -> bool: return n is Npc and String(n.name).begins_with("Traveller_"))
	var out_by_day := walkers.filter(func(n: Npc) -> bool: return n.visible)
	_check("Kalmora has its day's visitors out by day", out_by_day.size() == Travellers.QUOTA[WorldMap.KALMORA])
	var npc := out_by_day[0] as Npc if not out_by_day.is_empty() else null
	_check("they roam the town", npc != null and npc.roam_points.size() > 4)
	var doors := Travellers.doors_of(town)
	_check("never to a doorstep", walkers.all(func(n: Npc) -> bool: return Array(n.roam_points).all(func(p: Vector2) -> bool:
		return doors.all(func(d: Vector2) -> bool: return d.distance_to(p) >= Travellers.DOOR_CLEAR))))
	_check("and you can walk through them", walkers.all(func(n: Npc) -> bool: return n.collision_layer == 0))
	_check("they come and go by the roads", walkers.all(func(n: Npc) -> bool: return n.exit_points.size() == 2))
	var told := Travellers.travel_line(Travellers.ROSTER[0].id, WorldMap.KALMORA)
	var yesterday := Travellers.where(Travellers.ROSTER[0].id, TimeOfDay.day - 1)
	_check("they say truly where they were yesterday", yesterday == "" or yesterday == WorldMap.KALMORA
		or Travellers.zone_name(yesterday) in told)
	_check("and talk about Kalmora", npc != null and Array(npc.lines).any(func(l: String) -> bool: return l in Travellers.CITY_LINES.kalmora))
	await get_tree().create_timer(4.0).timeout
	_check("and actually walk", out_by_day.any(func(n: Npc) -> bool: return n.velocity.length() > 1.0))
	TimeOfDay.set_hour(22.0)
	town = await _load(WorldMap.KALMORA)
	var at_night := town.get_children().filter(func(n: Node) -> bool: return n is Npc and String(n.name).begins_with("Traveller_") and n.visible)
	_check("at night every traveller is back in Kalmora", at_night.size() == Travellers.ROSTER.size())
	_check("with something to say about the night", at_night.all(func(n: Npc) -> bool: return not n.night_lines.is_empty()))
	# Dusk while you watch: a visitor walks off down the road rather than vanishing,
	# and Kalmora's night crowd walks in from its roads.
	TimeOfDay.set_hour(19.0)
	var dusk := await _load(WorldMap.VERDANA)
	var visitor := dusk.get_children().filter(func(n: Node) -> bool: return n is Npc and String(n.name).begins_with("Traveller_") and n.visible)
	if not visitor.is_empty():
		var watched := visitor[0] as Npc
		var me := get_tree().get_first_node_in_group(&"player") as Node2D
		me.global_position = watched.global_position + Vector2(30, 0)
		(me.get_node(^"Camera2D") as Camera2D).reset_smoothing()
		for _i in 10:
			await get_tree().process_frame
		TimeOfDay.set_hour(19.6)
		await get_tree().create_timer(1.5).timeout
		var gone_by_road := not watched.visible and Array(watched.exit_points).any(func(e: Vector2) -> bool: return e.distance_to(watched.global_position) < 40.0)
		_check("at dusk a visitor in view walks off down the road", (watched.visible and watched._leaving) or gone_by_road)
	TimeOfDay.set_hour(19.0)
	var evening := await _load(WorldMap.KALMORA)
	var hidden := evening.get_children().filter(func(n: Node) -> bool: return n is Npc and String(n.name).begins_with("Traveller_") and not n.visible)
	TimeOfDay.set_hour(19.6)
	await get_tree().create_timer(1.5).timeout
	_check("and the night crowd walks into Kalmora from its roads", not hidden.is_empty() and hidden.all(func(n: Npc) -> bool:
		return n.visible and Array(n.exit_points).any(func(e: Vector2) -> bool: return e.distance_to(n.global_position) < 60.0)))
	TimeOfDay.set_hour(22.0)
	var verdana := await _load(WorldMap.VERDANA)
	_check("and Verdana's visitors have gone", not verdana.get_children().any(func(n: Node) -> bool:
		return n is Npc and String(n.name).begins_with("Traveller_") and n.visible))
	TimeOfDay.set_hour(12.0)

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
