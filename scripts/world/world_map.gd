class_name WorldMap
extends RefCounted
## The island's layout: where each zone sits (for "nearest town"), which zones
## are towns, how zones connect (for rival travel), and what hand-placed cards
## each zone holds (read straight from the scene file, so rivals can collect
## them while the player is elsewhere).
##
## Add every new zone/town/connection here when its scene is created. Origins
## line up the zone exits: e.g. Thornveil's south exit (local y 125) meets
## Kalmora's north exit (local y -360), so Thornveil sits 485px north of Kalmora.

const KALMORA := "res://scenes/world/kalmora.tscn"
const THORNVEIL := "res://scenes/world/thornveil.tscn"
const SORENDA := "res://scenes/world/sorenda.tscn"
const WARDENS_GROVE := "res://scenes/world/wardens_grove.tscn"
const LAKE_VEYRA := "res://scenes/world/lake_veyra.tscn"

const PICKUP_SCENE := "res://scenes/systems/card_pickup.tscn"

## Zone scene -> { name, origin on the island, monster drops (for off-screen farming) }
const ZONES := {
	KALMORA: { "name": "Kalmora", "origin": Vector2(0, 0), "monster_drops": [] },
	THORNVEIL: { "name": "Thornveil Forest", "origin": Vector2(0, -485),
		"monster_drops": [&"thorn_sprig", &"moss_lantern", &"veyra_reed", &"hollow_acorn"] },
	SORENDA: { "name": "Sorenda", "origin": Vector2(0, -1490), "monster_drops": [] },
	WARDENS_GROVE: { "name": "Warden's Grove", "origin": Vector2(1030, -885), "monster_drops": [] },
	LAKE_VEYRA: { "name": "Lake Veyra", "origin": Vector2(-1070, -985),
		"monster_drops": [&"veyra_reed", &"moss_lantern", &"thorn_sprig"] },
}

## Town scene -> { spawn marker (under "Spawns") people wake at, its local position }
const TOWNS := {
	KALMORA: { "spawn": &"town", "position": Vector2(0, 40) },
	SORENDA: { "spawn": &"town", "position": Vector2(0, 0) },
}

## Walkable connections. `exit` is where you leave `from` (local position of its
## ZoneExit), `spawn`/`entry` are the arrival marker in `to` and its position.
## A `gate` must be open (or paid for) to pass in either direction.
const EDGES: Array[Dictionary] = [
	{ "from": KALMORA, "to": THORNVEIL, "exit": Vector2(0, -360), "spawn": &"from_kalmora",
		"entry": Vector2(0, 60), "gate": &"kalmora_north_gate" },
	{ "from": THORNVEIL, "to": KALMORA, "exit": Vector2(0, 125), "spawn": &"from_thornveil",
		"entry": Vector2(0, -270), "gate": &"kalmora_north_gate" },
	{ "from": THORNVEIL, "to": SORENDA, "exit": Vector2(0, -830), "spawn": &"from_thornveil",
		"entry": Vector2(0, 120), "gate": &"" },
	{ "from": SORENDA, "to": THORNVEIL, "exit": Vector2(0, 175), "spawn": &"from_sorenda",
		"entry": Vector2(0, -760), "gate": &"" },
	{ "from": THORNVEIL, "to": WARDENS_GROVE, "exit": Vector2(535, -400), "spawn": &"from_thornveil",
		"entry": Vector2(-400, 0), "gate": &"" },
	{ "from": WARDENS_GROVE, "to": THORNVEIL, "exit": Vector2(-495, 0), "spawn": &"from_grove",
		"entry": Vector2(460, -400), "gate": &"" },
	{ "from": THORNVEIL, "to": LAKE_VEYRA, "exit": Vector2(-535, -250), "spawn": &"from_thornveil",
		"entry": Vector2(470, 250), "gate": &"thornveil_bramble_arch" },
	{ "from": LAKE_VEYRA, "to": THORNVEIL, "exit": Vector2(535, 250), "spawn": &"from_lake",
		"entry": Vector2(-460, -250), "gate": &"thornveil_bramble_arch" },
]

static var _pickup_cache: Dictionary = {}


static func zone_name(zone: String) -> String:
	return ZONES.get(zone, {}).get("name", "somewhere")


static func is_town(zone: String) -> bool:
	return TOWNS.has(zone)


## Island-space position of `local_pos` inside `zone`.
static func to_island(zone: String, local_pos: Vector2) -> Vector2:
	return ZONES.get(zone, {}).get("origin", Vector2.ZERO) + local_pos


## Scene path of the town closest to `local_pos` in `zone` (straight-line).
static func nearest_town(zone: String, local_pos: Vector2) -> String:
	var here := to_island(zone, local_pos)
	var best := KALMORA
	var best_dist := INF
	for town: String in TOWNS:
		var d := here.distance_to(to_island(town, TOWNS[town].position))
		if d < best_dist:
			best = town
			best_dist = d
	return best


static func town_name(town: String) -> String:
	return zone_name(town)


static func town_spawn(town: String) -> StringName:
	return TOWNS.get(town, {}).get("spawn", &"town")


static func edges_from(zone: String) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for edge in EDGES:
		if edge.from == zone:
			out.append(edge)
	return out


## Can `collector` walk this edge now? Open gates are free; closed ones need the
## cost card in hand (and a willingness to spend it).
static func can_use(edge: Dictionary, collector: StringName, will_pay: bool) -> bool:
	if edge.gate == &"" or GameState.opened_gates.has(edge.gate):
		return true
	if not will_pay:
		return false
	var gate := CardDatabase.get_gate(edge.gate)
	return gate != null and GameState.collection(collector).count(gate.cost_card_id) >= gate.cost_amount


## First edge on the shortest usable route from `from` to `to`, or {} if there is none.
static func next_hop(from: String, to: String, collector: StringName, will_pay: bool) -> Dictionary:
	if from == to:
		return {}
	var first: Dictionary = {}  # zone -> first edge taken to reach it
	var queue: Array[String] = [from]
	var seen := { from: true }
	while not queue.is_empty():
		var zone: String = queue.pop_front()
		for edge in edges_from(zone):
			if seen.has(edge.to) or not can_use(edge, collector, will_pay):
				continue
			seen[edge.to] = true
			first[edge.to] = first.get(zone, edge)
			if edge.to == to:
				return first[edge.to]
			queue.append(edge.to)
	return {}


## Zones reachable from `from`, nearest first.
static func reachable(from: String, collector: StringName, will_pay: bool) -> Array[String]:
	var out: Array[String] = []
	var queue: Array[String] = [from]
	var seen := { from: true }
	while not queue.is_empty():
		var zone: String = queue.pop_front()
		for edge in edges_from(zone):
			if not seen.has(edge.to) and can_use(edge, collector, will_pay):
				seen[edge.to] = true
				out.append(edge.to)
				queue.append(edge.to)
	return out


## Hand-placed card pickups in `zone` that nobody has taken yet:
## Array of { "key": persist key, "card_id": StringName, "gate": guarding gate or &"" }.
static func remaining_pickups(zone: String) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for pickup: Dictionary in _all_pickups(zone):
		if not GameState.collected_pickups.has(pickup.key):
			out.append(pickup)
	return out


## Remaining pickups `collector` can actually get to: behind no gate, an open
## one, or one it's willing and able to pay for.
static func reachable_pickups(zone: String, collector: StringName, will_pay: bool) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for pickup in remaining_pickups(zone):
		if can_use({ "gate": pickup.gate }, collector, will_pay):
			out.append(pickup)
	return out


## Every hand-placed pickup in every zone (for the soft-lock validator).
static func all_placed_pickups() -> Array:
	var out := []
	for zone: String in ZONES:
		out.append_array(_all_pickups(zone))
	return out


## Reads the pickups out of the packed scene without instancing it.
static func _all_pickups(zone: String) -> Array:
	if _pickup_cache.has(zone):
		return _pickup_cache[zone]
	var found := []
	var packed := load(zone) as PackedScene
	if packed:
		var state := packed.get_state()
		for i in state.get_node_count():
			var instance := state.get_node_instance(i)
			if instance == null or instance.resource_path != PICKUP_SCENE:
				continue
			var card_id: StringName = &""
			var gate: StringName = &""
			for p in state.get_node_property_count(i):
				match state.get_node_property_name(i, p):
					&"card_id":
						card_id = state.get_node_property_value(i, p)
					&"behind_gate":
						gate = state.get_node_property_value(i, p)
			var path := String(state.get_node_path(i)).trim_prefix("./")
			found.append({ "key": CardPickup.persist_key(zone, path), "card_id": card_id, "gate": gate })
	_pickup_cache[zone] = found
	return found
