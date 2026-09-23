extends Node
## Rival zone travel: WorldMap routes and pickup scanning, off-screen simulation
## (collect real cards, bind in town, pay a gate, cross zones, hunters follow the
## player), and an on-screen rival walking out of Kalmora when it runs dry.
## Run: godot --headless --path . res://tests/test_rival_travel.tscn

const R := &"runner"
const RAIDER := &"raider"

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null  # Survive zone changes.
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)

	# --- Scene scan matches the real pickups (same persist keys).
	var kalmora: Node = load(WorldMap.KALMORA).instantiate()
	add_child(kalmora)
	await get_tree().process_frame
	var live_keys: Array[String] = []
	for node in get_tree().get_nodes_in_group(&"card_pickups"):
		live_keys.append((node as CardPickup)._persist_key())
	var scanned_keys: Array[String] = []
	for p in WorldMap.remaining_pickups(WorldMap.KALMORA):
		scanned_keys.append(p.key)
	live_keys.sort()
	scanned_keys.sort()
	_check("scene scan finds Kalmora's pickups (%d)" % scanned_keys.size(), not scanned_keys.is_empty() and live_keys == scanned_keys)
	kalmora.queue_free()
	await get_tree().process_frame

	# --- Routes respect gates.
	_check("closed gate, no compass: no route north", WorldMap.next_hop(WorldMap.KALMORA, WorldMap.SORENDA, R, true).is_empty())
	_check("Raider won't pay gates", not WorldMap.can_use(WorldMap.EDGES[0], RAIDER, false))
	GameState.add_loose_card(R, &"salt_compass")
	var hop := WorldMap.next_hop(WorldMap.KALMORA, WorldMap.SORENDA, R, true)
	_check("with a compass the route runs through Thornveil", hop.get("to") == WorldMap.THORNVEIL)
	GameState.consume_card(R, &"salt_compass", &"test")

	# --- Off-screen: the player is away in Sorenda.
	RivalDirector.player_zone_override = WorldMap.SORENDA
	var start_left := WorldMap.remaining_pickups(WorldMap.KALMORA).size()
	for i in start_left + 2:
		if GameState.rival_locations[R].zone != WorldMap.KALMORA:
			break
		RivalDirector.act_offscreen(R, WorldMap.KALMORA)
	_check("Runner cleared Kalmora's cards off-screen", WorldMap.remaining_pickups(WorldMap.KALMORA).is_empty())
	var col := GameState.collection(R)
	var loose := 0
	for id in col.card_ids():
		loose += col.count(id, CardCollection.State.LOOSE)
	_check("and bound them in town", loose <= 1)
	_check("then paid the north gate to move on", GameState.opened_gates.get(&"kalmora_north_gate") == R)
	_check("Runner is in transit", GameState.rival_locations[R].zone == "")
	RivalDirector.tick_rival(R, RivalDirector.TRAVEL_SECONDS + 1.0)
	_check("Runner arrived in Thornveil at the entrance", GameState.rival_locations[R].zone == WorldMap.THORNVEIL
		and GameState.rival_locations[R].position == Vector2(0, 60))

	# Full hands in the field: head for a town.
	for i in 6:
		if GameState.rival_locations[R].zone != WorldMap.THORNVEIL:
			break
		RivalDirector.act_offscreen(R, WorldMap.THORNVEIL)
	RivalDirector.tick_rival(R, RivalDirector.TRAVEL_SECONDS + 1.0)
	_check("Runner took its haul to a town", WorldMap.is_town(GameState.rival_locations[R].zone))

	# Hunter follows the player out into the field when they carry loose cards.
	GameState.move_rival(RAIDER, WorldMap.SORENDA)
	RivalDirector.player_zone_override = WorldMap.THORNVEIL
	_check("idle Raider leaves town to hunt monsters in the field",
		not WorldMap.is_town(RivalDirector.choose_destination(RAIDER, WorldMap.SORENDA)))
	GameState.add_loose_card(GameState.PLAYER, &"fern_sigil")
	_check("Raider goes after a player carrying cards", RivalDirector.choose_destination(RAIDER, WorldMap.SORENDA) == WorldMap.THORNVEIL)

	# --- On-screen: a fresh game, Kalmora picked clean except what the Runner holds.
	GameState.new_game(GameState.DEFAULT_RIVALS)
	for p in WorldMap.remaining_pickups(WorldMap.KALMORA):
		GameState.collected_pickups[p.key] = true
	GameState.add_loose_card(R, &"salt_compass")
	RivalDirector.enabled = true
	get_tree().change_scene_to_file(WorldMap.KALMORA)
	var left := false
	for i in 30:
		await get_tree().create_timer(1.0).timeout
		if GameState.rival_locations[R].zone != WorldMap.KALMORA:
			left = true
			break
	_check("on-screen Runner walked out of Kalmora", left)
	_check("it opened the gate on the way", GameState.opened_gates.get(&"kalmora_north_gate") == R)
	for i in 20:
		await get_tree().create_timer(1.0).timeout
		if GameState.rival_locations[R].zone == WorldMap.THORNVEIL:
			break
	_check("and reached Thornveil", GameState.rival_locations[R].zone == WorldMap.THORNVEIL)

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
