class_name WorldMap
extends RefCounted
## The island's layout: where each zone sits (for "nearest town"), which zones
## are towns, how zones connect (for rival travel), and what hand-placed cards
## each zone holds (read straight from the scene file, so rivals can collect
## them while the player is elsewhere).
##
## Add every new zone/town/connection here when its scene is created. Origins
## line up the zone exits: e.g. Thornveil's south exit (local y 125, island y -360)
## meets Kalmora's north road exit (local y -756), so Kalmora's origin is y 396.

const KALMORA := "res://scenes/world/kalmora.tscn"
const THORNVEIL := "res://scenes/world/thornveil.tscn"
const SORENDA := "res://scenes/world/sorenda.tscn"
const WARDENS_GROVE := "res://scenes/world/wardens_grove.tscn"
const LAKE_VEYRA := "res://scenes/world/lake_veyra.tscn"
const SORENDA_HOLLOW := "res://scenes/world/sorenda_hollow.tscn"
const AUREWIND := "res://scenes/world/aurewind_plains.tscn"
const VERDANA := "res://scenes/world/verdana.tscn"
const LAKE_SERIN := "res://scenes/world/lake_serin.tscn"
const STARFALL := "res://scenes/world/starfall_range.tscn"
const VERDANA_INN := "res://scenes/world/interiors/verdana_inn.tscn"
const VERDANA_FARMHOUSE := "res://scenes/world/interiors/verdana_farmhouse.tscn"
const VERDANA_SCHOLAR := "res://scenes/world/interiors/verdana_scholar.tscn"
const VERDANA_WEAVER := "res://scenes/world/interiors/verdana_weaver.tscn"
const VERDANA_BAKERY := "res://scenes/world/interiors/verdana_bakery.tscn"
const VERDANA_BARN := "res://scenes/world/interiors/verdana_barn.tscn"
const VERDANA_MILL := "res://scenes/world/interiors/verdana_mill.tscn"
const SERIN_FISHER_HUT := "res://scenes/world/interiors/serin_fisher_hut.tscn"
const STARFALL_GROTTO := "res://scenes/world/starfall_grotto.tscn"
const STARFALL_CABIN := "res://scenes/world/interiors/starfall_cabin.tscn"
const SORENDA_LONGHOUSE := "res://scenes/world/interiors/sorenda_longhouse.tscn"
const SORENDA_SCRIBE := "res://scenes/world/interiors/sorenda_scribe_house.tscn"
const SORENDA_HERBALIST := "res://scenes/world/interiors/sorenda_herbalist_house.tscn"
const SORENDA_WOODCUTTER := "res://scenes/world/interiors/sorenda_woodcutter.tscn"
const SORENDA_FAMILY := "res://scenes/world/interiors/sorenda_family_home.tscn"
const SORENDA_TREE_HOUSE := "res://scenes/world/interiors/sorenda_tree_house.tscn"
const SORENDA_INN := "res://scenes/world/interiors/sorenda_inn.tscn"
const KALMORA_TAVERN := "res://scenes/world/interiors/kalmora_tavern.tscn"
const KALMORA_CARD_SHOP := "res://scenes/world/interiors/kalmora_card_shop.tscn"
const KALMORA_NONNA_HOUSE := "res://scenes/world/interiors/kalmora_nonna_house.tscn"
const KALMORA_RED_HOUSE := "res://scenes/world/interiors/kalmora_red_house.tscn"
const KALMORA_GENERAL_STORE := "res://scenes/world/interiors/kalmora_general_store.tscn"
const KALMORA_FORGE := "res://scenes/world/interiors/kalmora_forge.tscn"
const KALMORA_HARBOR_OFFICE := "res://scenes/world/interiors/kalmora_harbor_office.tscn"
const KALMORA_WAREHOUSE := "res://scenes/world/interiors/kalmora_warehouse.tscn"
const KALMORA_BLUE_COTTAGE := "res://scenes/world/interiors/kalmora_blue_cottage.tscn"
const KALMORA_CALLOWAY_HOUSE := "res://scenes/world/interiors/kalmora_calloway_house.tscn"
const KALMORA_TEAL_HOUSE := "res://scenes/world/interiors/kalmora_teal_house.tscn"
const KALMORA_MILL := "res://scenes/world/interiors/kalmora_mill.tscn"

const PICKUP_SCENE := "res://scenes/systems/card_pickup.tscn"
const CHEST_SCRIPT := "res://scripts/systems/chest.gd"

## Zone scene -> { name, origin on the island, monster drops (for off-screen farming) }
const ZONES := {
	KALMORA: { "name": "Kalmora", "origin": Vector2(0, 396), "monster_drops": [] },
	THORNVEIL: { "name": "Thornveil Forest", "origin": Vector2(-28, -488),
		"monster_drops": [&"thorn_sprig", &"moss_lantern", &"veyra_reed", &"hollow_acorn"] },
	SORENDA: { "name": "Sorenda", "origin": Vector2(-30, -2268), "monster_drops": [] },
	# The cave under Sorenda's roots, past the moss gate. A real zone (rivals can go in).
	SORENDA_HOLLOW: { "name": "The Hollow", "origin": Vector2(1070, -3340),
		"monster_drops": [&"root_knot", &"briar_wren"] },
	WARDENS_GROVE: { "name": "Warden's Grove", "origin": Vector2(1456, -1764), "monster_drops": [] },
	LAKE_VEYRA: { "name": "Lake Veyra", "origin": Vector2(-1582, -1978),
		"monster_drops": [&"veyra_reed", &"moss_lantern", &"thorn_sprig"] },
	# Past Kalmora's west gate (built by build_region.py): the plains west of Kalmora,
	# Verdana in their south, Lake Serin north of them, the Starfall Range beyond.
	AUREWIND: { "name": "Aurewind Plains", "origin": Vector2(-2344, 79),
		"monster_drops": [&"bristle_fleece", &"thatch_charm", &"fern_sigil", &"thorn_sprig"] },
	VERDANA: { "name": "Verdana", "origin": Vector2(-2644, 1623), "monster_drops": [] },
	LAKE_SERIN: { "name": "Lake Serin", "origin": Vector2(-2894, -1625),
		"monster_drops": [&"hollow_acorn", &"moss_lantern", &"thorn_sprig"] },
	STARFALL: { "name": "Starfall Range", "origin": Vector2(-3194, -3201),
		"monster_drops": [&"iron_wolf_collar", &"owl_quill", &"briar_wren"] },
	STARFALL_GROTTO: { "name": "The Frost Grotto", "origin": Vector2(-1886, -3880),
		"monster_drops": [&"iron_wolf_collar", &"owl_quill", &"briar_wren"] },
	# Interiors sit where their buildings stand in town. They have no EDGES, so
	# rivals never wander in; you enter through the building's door.
	KALMORA_TAVERN: { "name": "The Salted Lantern", "origin": Vector2(214, 220), "monster_drops": [] },
	KALMORA_CARD_SHOP: { "name": "Sable's Card Emporium", "origin": Vector2(360, 388), "monster_drops": [] },
	KALMORA_NONNA_HOUSE: { "name": "Nonna Vess's House", "origin": Vector2(771, -150), "monster_drops": [] },
	KALMORA_RED_HOUSE: { "name": "The Tamsin Home", "origin": Vector2(-451, 147), "monster_drops": [] },
	KALMORA_GENERAL_STORE: { "name": "Greta's Provisions", "origin": Vector2(-262, 220), "monster_drops": [] },
	KALMORA_FORGE: { "name": "Brannoc's Forge", "origin": Vector2(-419, 346), "monster_drops": [] },
	KALMORA_HARBOR_OFFICE: { "name": "Harbormaster's Office", "origin": Vector2(-472, 640), "monster_drops": [] },
	KALMORA_WAREHOUSE: { "name": "Harbor Warehouse", "origin": Vector2(-304, 640), "monster_drops": [] },
	KALMORA_BLUE_COTTAGE: { "name": "Old Fenn's Cottage", "origin": Vector2(522, -182), "monster_drops": [] },
	KALMORA_CALLOWAY_HOUSE: { "name": "Calloway House", "origin": Vector2(757, 27), "monster_drops": [] },
	KALMORA_TEAL_HOUSE: { "name": "Ilse's Map House", "origin": Vector2(872, 27), "monster_drops": [] },
	KALMORA_MILL: { "name": "The Windmill", "origin": Vector2(-766, 142), "monster_drops": [] },
	VERDANA_INN: { "name": "The Sheaf & Sickle", "origin": Vector2(-2644, 1393), "monster_drops": [] },
	VERDANA_FARMHOUSE: { "name": "Marta's Farmhouse", "origin": Vector2(-3104, 1503), "monster_drops": [] },
	VERDANA_SCHOLAR: { "name": "Aldous's House", "origin": Vector2(-2024, 1293), "monster_drops": [] },
	VERDANA_WEAVER: { "name": "Oda's Cottage", "origin": Vector2(-2564, 2023), "monster_drops": [] },
	VERDANA_BAKERY: { "name": "Pim's Bakery", "origin": Vector2(-2284, 1743), "monster_drops": [] },
	VERDANA_BARN: { "name": "The Hensley Barn", "origin": Vector2(-3204, 1913), "monster_drops": [] },
	VERDANA_MILL: { "name": "Verdana Mill", "origin": Vector2(-2164, 1963), "monster_drops": [] },
	SERIN_FISHER_HUT: { "name": "Neri's Hut", "origin": Vector2(-2074, -1735), "monster_drops": [] },
	STARFALL_CABIN: { "name": "Hald's Cabin", "origin": Vector2(-2574, -3311), "monster_drops": [] },
	SORENDA_LONGHOUSE: { "name": "The Elder's Longhouse", "origin": Vector2(-30, -2518), "monster_drops": [] },
	SORENDA_SCRIBE: { "name": "Wren's House", "origin": Vector2(-370, -2482), "monster_drops": [] },
	SORENDA_HERBALIST: { "name": "Juniper's Cottage", "origin": Vector2(320, -2454), "monster_drops": [] },
	SORENDA_WOODCUTTER: { "name": "Harl's Cottage", "origin": Vector2(-480, -2244), "monster_drops": [] },
	SORENDA_FAMILY: { "name": "Pell's Home", "origin": Vector2(-270, -2092), "monster_drops": [] },
	SORENDA_TREE_HOUSE: { "name": "The Old Tree House", "origin": Vector2(350, -2148), "monster_drops": [] },
	SORENDA_INN: { "name": "The Copper Kettle", "origin": Vector2(185, -2020), "monster_drops": [] },
}

## Town scene -> { spawn marker (under "Spawns") people wake at, the local point
## "nearest town" distances are measured to (a big town's gate, not its centre) }
const TOWNS := {
	KALMORA: { "spawn": &"town", "position": Vector2(-13, -609) },
	SORENDA: { "spawn": &"town", "position": Vector2(0, 0) },
	VERDANA: { "spawn": &"town", "position": Vector2(-200, -600) },
}

## Walkable connections. `exit` is where you leave `from` (local position of its
## ZoneExit), `spawn`/`entry` are the arrival marker in `to` and its position.
## A `gate` must be open (or paid for) to pass in either direction.
const EDGES: Array[Dictionary] = [
	{ "from": KALMORA, "to": THORNVEIL, "exit": Vector2(0, -756), "spawn": &"from_kalmora",
		"entry": Vector2(28, 56), "gate": &"kalmora_north_gate" },
	{ "from": THORNVEIL, "to": KALMORA, "exit": Vector2(28, 124), "spawn": &"from_thornveil",
		"entry": Vector2(-13, -609), "gate": &"kalmora_north_gate" },
	{ "from": THORNVEIL, "to": SORENDA, "exit": Vector2(-2, -1500), "spawn": &"from_thornveil",
		"entry": Vector2(0, 236), "gate": &"" },
	{ "from": SORENDA, "to": THORNVEIL, "exit": Vector2(0, 282), "spawn": &"from_sorenda",
		"entry": Vector2(-2, -1414), "gate": &"" },
	{ "from": SORENDA, "to": SORENDA_HOLLOW, "exit": Vector2(604, -532), "spawn": &"from_sorenda",
		"entry": Vector2(-496, 448), "gate": &"sorenda_hollow" },
	{ "from": SORENDA_HOLLOW, "to": SORENDA, "exit": Vector2(-496, 540), "spawn": &"from_hollow",
		"entry": Vector2(604, -498), "gate": &"sorenda_hollow" },
	{ "from": THORNVEIL, "to": WARDENS_GROVE, "exit": Vector2(1084, -1276), "spawn": &"from_thornveil",
		"entry": Vector2(-400, 0), "gate": &"" },
	{ "from": WARDENS_GROVE, "to": THORNVEIL, "exit": Vector2(-495, 0), "spawn": &"from_grove",
		"entry": Vector2(1027, -1279), "gate": &"" },
	{ "from": THORNVEIL, "to": LAKE_VEYRA, "exit": Vector2(-1084, -1240), "spawn": &"from_thornveil",
		"entry": Vector2(470, 250), "gate": &"thornveil_bramble_arch" },
	{ "from": LAKE_VEYRA, "to": THORNVEIL, "exit": Vector2(535, 250), "spawn": &"from_lake",
		"entry": Vector2(-1028, -1240), "gate": &"thornveil_bramble_arch" },
	# West of Kalmora: the Warden's card opens the west gate.
	{ "from": KALMORA, "to": AUREWIND, "exit": Vector2(-1108, -277), "spawn": &"from_kalmora",
		"entry": Vector2(1160, 40), "gate": &"kalmora_west_gate" },
	{ "from": AUREWIND, "to": KALMORA, "exit": Vector2(1236, 40), "spawn": &"from_aurewind",
		"entry": Vector2(-1032, -277), "gate": &"kalmora_west_gate" },
	{ "from": AUREWIND, "to": VERDANA, "exit": Vector2(-500, 884), "spawn": &"from_aurewind",
		"entry": Vector2(-200, -600), "gate": &"" },
	{ "from": VERDANA, "to": AUREWIND, "exit": Vector2(-200, -660), "spawn": &"from_verdana",
		"entry": Vector2(-500, 820), "gate": &"" },
	{ "from": AUREWIND, "to": LAKE_SERIN, "exit": Vector2(150, -916), "spawn": &"from_aurewind",
		"entry": Vector2(700, 720), "gate": &"" },
	{ "from": LAKE_SERIN, "to": AUREWIND, "exit": Vector2(700, 788), "spawn": &"from_lake_serin",
		"entry": Vector2(150, -840), "gate": &"" },
	{ "from": LAKE_SERIN, "to": STARFALL, "exit": Vector2(-300, -788), "spawn": &"from_lake_serin",
		"entry": Vector2(0, 720), "gate": &"" },
	{ "from": STARFALL, "to": LAKE_SERIN, "exit": Vector2(0, 788), "spawn": &"from_starfall",
		"entry": Vector2(-300, -710), "gate": &"" },
	{ "from": STARFALL, "to": STARFALL_GROTTO, "exit": Vector2(860, -224), "spawn": &"from_starfall",
		"entry": Vector2(-448, 400), "gate": &"" },
	{ "from": STARFALL_GROTTO, "to": STARFALL, "exit": Vector2(-448, 476), "spawn": &"from_grotto",
		"entry": Vector2(860, -150), "gate": &"" },
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


## Cards placed in `zone` (in chests) that `collector` hasn't taken yet. Every
## collector opens each chest once, so one collector emptying it leaves it full for
## the others: Array of { "key": persist key, "card_id": StringName, "gate": guarding gate or &"" }.
static func remaining_pickups(zone: String, collector: StringName = &"player") -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for pickup: Dictionary in _all_pickups(zone):
		if not GameState.collected_pickups.has(taken_key(pickup.key, collector)):
			out.append(pickup)
	return out


## The GameState.collected_pickups key for `collector` having emptied pickup `key`
## (the player's is the bare key, as it always was).
static func taken_key(key: String, collector: StringName) -> String:
	return key if collector == &"player" else "%s@%s" % [key, collector]


## Remaining pickups `collector` can actually get to: behind no gate, an open
## one, or one it's willing and able to pay for.
static func reachable_pickups(zone: String, collector: StringName, will_pay: bool) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for pickup in remaining_pickups(zone, collector):
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
			# Loose pickups (older scenes) and chests that hold a card.
			var instance := state.get_node_instance(i)
			var is_pickup := instance != null and instance.resource_path == PICKUP_SCENE
			var card_id: StringName = &""
			var gate: StringName = &""
			var is_chest := false
			for p in state.get_node_property_count(i):
				match state.get_node_property_name(i, p):
					&"card_id":
						card_id = state.get_node_property_value(i, p)
					&"behind_gate":
						gate = state.get_node_property_value(i, p)
					&"script":
						var script := state.get_node_property_value(i, p) as Script
						is_chest = script != null and script.resource_path == CHEST_SCRIPT
			if not is_pickup and not (is_chest and card_id != &""):
				continue
			var path := String(state.get_node_path(i)).trim_prefix("./")
			found.append({ "key": CardPickup.persist_key(zone, path), "card_id": card_id, "gate": gate })
	found.append_array(Errands.pickups_in(zone))
	_pickup_cache[zone] = found
	return found
