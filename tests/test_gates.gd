extends Node
## Every GateData is placed exactly once in the world, gated cards sit in the same
## zone as their gate, the Warden's respawn gates all exist, and rivals respect
## (or pay for) gates on routes and pickups.
## Run: godot --headless --path . res://tests/test_gates.tscn

const GATE_SCENE := "res://scenes/systems/card_gate.tscn"
const R := &"runner"
const RAIDER := &"raider"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)

	# Where each gate is placed (read from the zone scene files).
	var placed: Dictionary = {}  # gate id -> Array of zones
	for zone: String in WorldMap.ZONES:
		var state := (load(zone) as PackedScene).get_state()
		for i in state.get_node_count():
			var inst := state.get_node_instance(i)
			if inst == null or inst.resource_path != GATE_SCENE:
				continue
			for p in state.get_node_property_count(i):
				if state.get_node_property_name(i, p) == &"gate_id":
					var id: StringName = state.get_node_property_value(i, p)
					if not placed.has(id):
						placed[id] = []
					placed[id].append(zone)
	for gate in CardDatabase.all_gates():
		_check("gate %s placed once" % gate.id, placed.get(gate.id, []).size() == 1)

	for zone: String in WorldMap.ZONES:
		for pickup: Dictionary in WorldMap.remaining_pickups(zone):
			if pickup.gate != &"":
				_check("%s is in the same zone as its gate" % pickup.key.get_file(),
					placed.get(pickup.gate, []).has(zone))

	var respawn_gates := CardDatabase.all_gates().filter(func(g: GateData) -> bool: return g.respawns_boss == &"canopy_warden")
	_check("all 3 Warden respawn gates are in the world (4 kills reachable)", respawn_gates.size() == 3
		and respawn_gates.all(func(g: GateData) -> bool: return placed.has(g.id)))

	# Routes into Lake Veyra go through the Bramble Arch.
	GameState.opened_gates[&"kalmora_north_gate"] = GameState.PLAYER
	_check("no sprigs, no way to the lake", WorldMap.next_hop(WorldMap.THORNVEIL, WorldMap.LAKE_VEYRA, R, true).is_empty())
	GameState.add_loose_card(R, &"thorn_sprig")
	GameState.add_loose_card(R, &"thorn_sprig")
	_check("two sprigs open the way for the Runner", not WorldMap.next_hop(WorldMap.THORNVEIL, WorldMap.LAKE_VEYRA, R, true).is_empty())
	GameState.add_loose_card(RAIDER, &"thorn_sprig")
	GameState.add_loose_card(RAIDER, &"thorn_sprig")
	_check("the Raider won't pay, even with sprigs", WorldMap.next_hop(WorldMap.THORNVEIL, WorldMap.LAKE_VEYRA, RAIDER, false).is_empty())

	# Gated pickups: off-screen rivals only take what they can pay to reach.
	GameState.move_rival(R, WorldMap.LAKE_VEYRA)
	var gated_before := _gated_left(WorldMap.LAKE_VEYRA)
	for i in 10:
		RivalDirector.act_offscreen(R, WorldMap.LAKE_VEYRA)
		if GameState.rival_locations[R].zone != WorldMap.LAKE_VEYRA:
			break
	_check("without the cost cards, gated lake cards stay put", _gated_left(WorldMap.LAKE_VEYRA) == gated_before)

	GameState.new_game(GameState.DEFAULT_RIVALS)
	GameState.move_rival(R, WorldMap.LAKE_VEYRA)
	GameState.add_loose_card(R, &"moss_lantern")
	GameState.kill_boss(&"canopy_warden", GameState.PLAYER)  # So the respawn below means something.
	var pearls_before := GameState.collection(R).count(&"veyra_pearl")
	for i in 10:
		RivalDirector.act_offscreen(R, WorldMap.LAKE_VEYRA)
		if GameState.rival_locations[R].zone != WorldMap.LAKE_VEYRA:
			break
	_check("with a Moss Lantern the Runner pays for the bridge", GameState.opened_gates.get(&"thornveil_moss_bridge") == R)
	_check("and takes the island pearl", GameState.collection(R).count(&"veyra_pearl") > pearls_before)
	_check("opening the Moss Bridge counts as a Warden respawn gate", GameState.bosses[&"canopy_warden"].alive)

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _gated_left(zone: String) -> int:
	return WorldMap.remaining_pickups(zone).filter(func(p: Dictionary) -> bool: return p.gate != &"").size()


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
