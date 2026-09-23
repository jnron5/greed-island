extends Node
## Moves rivals around the island, including zones the player isn't in.
##
## - Rivals in the player's zone are Rival nodes running their own AI; they ask
##   plan_departure() when they want to move on, walk to the exit, and depart().
## - Rivals elsewhere are simulated coarsely here, one action per think_seconds:
##   bind in towns, collect the zone's remaining hand-placed cards (the same
##   cards the player would find), farm monster drops in the field, and travel
##   along WorldMap edges (paying gate cards like anyone else).
## - Crossing between zones takes TRAVEL_SECONDS; a rival in transit is in no zone.
##   When it arrives in the player's zone it walks in through the entrance.
## - Hunters (Raider) go after a boss when it's alive and they still lack one of
##   its final-set cards (never just to deny the player). Off-screen that's a
##   risky roll: win and take the drops, lose and wake in the nearest town.

signal rival_departed(id: StringName, from_zone: String, to_zone: String)
signal rival_arrived(id: StringName, zone: String)

const TICK := 1.0
const TRAVEL_SECONDS := 12.0
## Off-screen chance per action of taking a monster drop in a field zone.
const FARM_CHANCE := 0.5
## Off-screen chance per attempt that a hunter beats a boss.
const BOSS_WIN_CHANCE := 0.2

## Tests switch this off to keep rivals where they put them.
var enabled := true
## Tests set this to pretend the player is in a zone.
var player_zone_override := ""

var _timer := 0.0
## id -> { "busy": seconds until next off-screen action, "travel": edge or {}, "travel_left": seconds }
var _sim: Dictionary[StringName, Dictionary] = {}


func _process(delta: float) -> void:
	if not enabled:
		return
	_timer += delta
	if _timer < TICK:
		return
	var dt := _timer
	_timer = 0.0
	for id in GameState.active_rivals:
		tick_rival(id, dt)


func player_zone() -> String:
	if player_zone_override != "":
		return player_zone_override
	var scene := get_tree().current_scene
	return scene.scene_file_path if scene is Zone else ""


func tick_rival(id: StringName, dt: float) -> void:
	var sim := _sim_for(id)
	if not sim.travel.is_empty():
		sim.travel_left -= dt
		if sim.travel_left <= 0.0:
			_arrive(id, sim.travel)
		return
	var zone: String = GameState.rival_locations[id].zone
	if zone == "" or zone == player_zone():
		return  # In transit elsewhere, or the Rival node is in charge.
	sim.busy -= dt
	if sim.busy > 0.0:
		return
	var profile := GameState.rival_profile(id)
	sim.busy = profile.think_seconds
	act_offscreen(id, zone)


## One coarse off-screen action for rival `id` in `zone`.
func act_offscreen(id: StringName, zone: String) -> void:
	if WorldMap.is_town(zone):
		bind_all(id)
	var boss := wanted_boss(id, zone)
	if boss and boss.zone == zone:
		fight_boss_offscreen(id, boss)
		return
	var destination := choose_destination(id, zone)
	if destination != zone:
		var edge := WorldMap.next_hop(zone, destination, id, GameState.rival_profile(id).pays_gates)
		if not edge.is_empty():
			start_travel(id, edge, TRAVEL_SECONDS)
			return
	_collect_offscreen(id, zone)


## Where rival `id` wants to be next, by personality. Returns `zone` to stay.
func choose_destination(id: StringName, zone: String) -> String:
	var profile := GameState.rival_profile(id)
	var pays := profile.pays_gates
	var col := GameState.collection(id)
	var carrying := 0
	for card in col.card_ids():
		carrying += col.count(card, CardCollection.State.LOOSE)

	# Full hands: get to a town to bind (every style).
	if carrying >= profile.carry_limit and not WorldMap.is_town(zone):
		return _nearest_reachable_town(id, zone, pays)

	# Hunt a boss for a card we still need.
	var boss := wanted_boss(id, zone)
	if boss:
		return boss.zone

	match profile.travel_style:
		RivalProfile.TravelStyle.HUNTER:
			# Follow the player when they're carrying something worth taking.
			var target := player_zone()
			if target != "" and target != zone and not WorldMap.is_town(target) \
					and not GameState.stealable_card_ids(GameState.PLAYER).is_empty() \
					and not WorldMap.next_hop(zone, target, id, pays).is_empty():
				return target
			# Otherwise hunt monsters out in the field.
			if WorldMap.is_town(zone):
				for other in WorldMap.reachable(zone, id, pays):
					if not WorldMap.is_town(other):
						return other
			return zone
		RivalProfile.TravelStyle.HOMEBODY:
			if WorldMap.is_town(zone):
				# Only short trips out, and only when there's something close to fetch.
				for other in WorldMap.reachable(zone, id, pays):
					if not WorldMap.remaining_pickups(other).is_empty() and randf() < 0.2:
						return other
				return zone
			return zone if carrying == 0 and not WorldMap.remaining_pickups(zone).is_empty() \
				else _nearest_reachable_town(id, zone, pays)
		_:
			# EXPLORER: stay while cards are left here, else rush to where they are.
			if not WorldMap.remaining_pickups(zone).is_empty():
				return zone
			for other in WorldMap.reachable(zone, id, pays):
				if not WorldMap.remaining_pickups(other).is_empty():
					return other
			return zone


## A boss rival `id` should go after from `zone`: it hunts, the boss is alive,
## the rival still lacks one of its final-set cards, and it can get there.
func wanted_boss(id: StringName, zone: String) -> BossData:
	var profile := GameState.rival_profile(id)
	if profile == null or not profile.hunts:
		return null
	for boss in GameState.all_bosses():
		if not GameState.is_boss_alive(boss.id) or not _needs_any(id, boss.drop_card_ids):
			continue
		if boss.zone == zone or not WorldMap.next_hop(zone, boss.zone, id, profile.pays_gates).is_empty():
			return boss
	return null


## Off-screen boss fight. `roll` in [0, 1) forces the outcome (tests); < 0 = random.
func fight_boss_offscreen(id: StringName, boss: BossData, roll := -1.0) -> bool:
	if roll < 0.0:
		roll = randf()
	if roll < BOSS_WIN_CHANCE and GameState.kill_boss(boss.id, id):
		for card in boss.drop_card_ids:
			GameState.add_loose_card(id, card)
		return true
	# Beaten: wake in the nearest town like anyone else.
	GameState.move_rival(id, WorldMap.nearest_town(boss.zone, Vector2.ZERO))
	return false


func _needs_any(id: StringName, cards: Array[StringName]) -> bool:
	var col := GameState.collection(id)
	for card_id in cards:
		var card := CardDatabase.get_card(card_id)
		if card and card.is_final_set_member and col.count(card_id) < card.final_set_count:
			return true
	return false


## On-screen rivals: the edge to leave by, or {} to stay. Pays the gate if it
## has to, so the path is open by the time it gets there.
func plan_departure(rival: Rival) -> Dictionary:
	var zone := player_zone()
	var destination := choose_destination(rival.collector_id, zone)
	if destination == zone:
		return {}
	var edge := WorldMap.next_hop(zone, destination, rival.collector_id, GameState.rival_profile(rival.collector_id).pays_gates)
	if not edge.is_empty():
		_pay_gate(rival.collector_id, edge)
	return edge


## A Rival node reached its exit: take it off the map and send it on its way.
func depart(rival: Rival, edge: Dictionary) -> void:
	# It already walked to the exit, so the crossing itself is short.
	start_travel(rival.collector_id, edge, TRAVEL_SECONDS * 0.25)


func start_travel(id: StringName, edge: Dictionary, seconds: float) -> void:
	_pay_gate(id, edge)
	var sim := _sim_for(id)
	sim.travel = edge
	sim.travel_left = seconds
	GameState.move_rival(id, "")  # In transit.
	rival_departed.emit(id, edge.from, edge.to)


func bind_all(id: StringName) -> void:
	var col := GameState.collection(id)
	for card in col.card_ids():
		while col.count(card, CardCollection.State.LOOSE) > 0:
			GameState.bind_card(id, card)


func _arrive(id: StringName, edge: Dictionary) -> void:
	var sim := _sim_for(id)
	sim.travel = {}
	sim.busy = GameState.rival_profile(id).think_seconds
	GameState.move_rival(id, edge.to, edge.entry)
	var zone := get_tree().current_scene as Zone
	if zone and zone.scene_file_path == edge.to and player_zone_override == "":
		zone.spawn_rival(id)
	rival_arrived.emit(id, edge.to)


func _collect_offscreen(id: StringName, zone: String) -> void:
	var pickups := WorldMap.remaining_pickups(zone)
	if not pickups.is_empty():
		var pickup: Dictionary = pickups.pick_random()
		if GameState.add_loose_card(id, pickup.card_id):
			GameState.collected_pickups[pickup.key] = true
		return
	var drops: Array = WorldMap.ZONES.get(zone, {}).get("monster_drops", [])
	if not drops.is_empty() and randf() < FARM_CHANCE:
		GameState.add_loose_card(id, drops.pick_random())


func _pay_gate(id: StringName, edge: Dictionary) -> void:
	if edge.gate != &"" and not GameState.opened_gates.has(edge.gate):
		GameState.open_gate(edge.gate, id)


func _nearest_reachable_town(id: StringName, zone: String, pays: bool) -> String:
	for other in WorldMap.reachable(zone, id, pays):
		if WorldMap.is_town(other):
			return other
	return zone


func _sim_for(id: StringName) -> Dictionary:
	if not _sim.has(id):
		var profile := GameState.rival_profile(id)
		# Stagger first actions so rivals don't all move on the same tick.
		_sim[id] = { "busy": randf() * (profile.think_seconds if profile else 5.0), "travel": {}, "travel_left": 0.0 }
	return _sim[id]


## Forget in-flight travel (new game).
func reset() -> void:
	_sim.clear()
	player_zone_override = ""
