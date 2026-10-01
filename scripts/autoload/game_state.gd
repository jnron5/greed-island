extends Node
## Run state: every collector's cards, currency, quest flags, opened gates,
## live world supply, and which 2 of the 3 rivals are racing.

const PLAYER := &"player"
const RIVALS: Array[StringName] = [&"hoarder", &"raider", &"runner"]
## Default pairing until the rival selection screen exists.
const DEFAULT_RIVALS: Array[StringName] = [&"raider", &"runner"]
const STARTING_GOLD := 60
## Seconds to slot one card into the binder outside a safe zone (instant inside).
const FIELD_BIND_TIME := 1.5
## How long a Lockbox Seal protects one card.
const LOCKBOX_SECONDS := 90.0
## A robbed collector can't be robbed again (by any method) for this long.
const GRACE_SECONDS := 15.0
const RIVAL_PROFILE_DIR := "res://data/rivals/"
const BOSS_DIR := "res://data/bosses/"

var active_rivals: Array[StringName] = []
var collections: Dictionary[StringName, CardCollection] = {}
var currency := 0
## The player's satchel: item id -> count (healing items; see ItemData).
var items: Dictionary[StringName, int] = {}
var quest_flags: Dictionary[StringName, Variant] = {}
var opened_gates: Dictionary[StringName, StringName] = {}  # gate id -> opener
## Copies that can still exist for finite cards. Consuming or selling a card
## permanently subtracts from this; respawning commons are not tracked.
var world_supply: Dictionary[StringName, int] = {}
## Open menus; the player ignores gameplay input while this is above 0.
var menus_open := 0
## collector -> number of safe zones they are standing in
var _safe_zones: Dictionary[StringName, int] = {}
## collector -> { card id -> lock expiry in msec }. A lock protects one copy.
var _locks: Dictionary[StringName, Dictionary] = {}
## collector -> msec when they were last robbed (grace period)
var _robbed_at: Dictionary[StringName, int] = {}
## Spawn marker name the next zone should place the player at (&"" = scene default).
var pending_spawn: StringName
## The player's hearts, carried from area to area (-1 = full). Only rest, food,
## healing springs and charms mend them; walking through a door doesn't.
var player_health := -1
## Message for the HUD to show once the next zone loads (e.g. after fainting).
var pending_notice := ""
## Where each active rival is: { "zone": scene path, "position": Vector2 or null }.
## null position = appear at the zone's RivalSpots/<id> marker.
var rival_locations: Dictionary[StringName, Dictionary] = {}
var _rival_profiles: Dictionary[StringName, RivalProfile] = {}
## boss id -> { "kills": int, "alive": bool }. Bosses start alive; after a kill
## they only return when a gate naming them in respawns_boss opens.
var bosses: Dictionary[StringName, Dictionary] = {}
var _boss_data: Dictionary[StringName, BossData] = {}
## Hand-placed pickups already taken ("scene path:node path"), so they don't
## come back when a zone reloads.
var collected_pickups: Dictionary[String, bool] = {}
## Cards dropped on the ground (e.g. when fainting), per zone scene path:
## Array of { "card_id": StringName, "position": Vector2 }.
var zone_drops: Dictionary[String, Array] = {}
## Card ids the player has held at least once (the first of each kind is revealed).
var seen_cards: Dictionary[StringName, bool] = {}
## Things the player has read (letters, ledgers, signs), in the order found:
## Array of { "title": String, "place": String, "lines": PackedStringArray }.
var journal: Array[Dictionary] = []
## Passive buff cards the player wears (the loadout), at most EQUIP_SLOTS. A worn
## card is held Exposed, so it can be stolen like any card in use.
var equipped: Array[StringName] = []
## Set cards the player spent on gates: card id -> copies. The card merchant sells
## them back (the rebuy safety net), at REBUY_MARKUP x the card's worth.
var spent_on_gates: Dictionary[StringName, int] = {}
const REBUY_MARKUP := 5
const EQUIP_SLOTS := 2


func _ready() -> void:
	for res in CardDatabase.load_all(RIVAL_PROFILE_DIR):
		if res is RivalProfile:
			_rival_profiles[res.id] = res
	for res in CardDatabase.load_all(BOSS_DIR):
		if res is BossData:
			_boss_data[res.id] = res
	new_game(DEFAULT_RIVALS)


func new_game(rivals: Array[StringName]) -> void:
	assert(rivals.size() == 2, "Pick exactly 2 of the 3 rivals")
	active_rivals = rivals.duplicate()
	collections.clear()
	for id in collectors():
		collections[id] = CardCollection.new(id)
	currency = STARTING_GOLD
	items.clear()
	items[&"bread"] = 2
	_locks.clear()
	_robbed_at.clear()
	collected_pickups.clear()
	zone_drops.clear()
	seen_cards.clear()
	journal.clear()
	equipped.clear()
	spent_on_gates.clear()
	pending_spawn = &""
	player_health = -1
	rival_locations.clear()
	bosses.clear()
	for id in _boss_data:
		bosses[id] = { "kills": 0, "alive": true }
	for id in active_rivals:
		var profile := rival_profile(id)
		rival_locations[id] = { "zone": profile.start_zone if profile else WorldMap.KALMORA, "position": null }
	quest_flags.clear()
	opened_gates.clear()
	world_supply.clear()
	for card in CardDatabase.all_cards():
		if not card.is_effectively_infinite():
			world_supply[card.id] = card.max_possible_copies()
	_emit_tracker()
	EventBus.currency_changed.emit(currency)
	if has_node(^"/root/RivalDirector"):
		get_node(^"/root/RivalDirector").reset()


func collectors() -> Array[StringName]:
	var out: Array[StringName] = [PLAYER]
	out.append_array(active_rivals)
	return out


func collection(collector: StringName) -> CardCollection:
	return collections.get(collector)


func add_loose_card(collector: StringName, card_id: StringName) -> bool:
	var col := collection(collector)
	if col == null or CardDatabase.get_card(card_id) == null:
		return false
	col.add(card_id, CardCollection.State.LOOSE)
	EventBus.card_added.emit(collector, card_id)
	_emit_tracker()
	return true


func change_state(collector: StringName, card_id: StringName, from: CardCollection.State, to: CardCollection.State) -> bool:
	var col := collection(collector)
	if col == null or not col.move(card_id, from, to):
		return false
	EventBus.card_state_changed.emit(collector, card_id, from, to)
	return true


## Loose -> Bound: slot into the binder (protected from theft).
func bind_card(collector: StringName, card_id: StringName) -> bool:
	return change_state(collector, card_id, CardCollection.State.LOOSE, CardCollection.State.BOUND)


## Bound -> Exposed: taken out for use (vulnerable again).
func expose_card(collector: StringName, card_id: StringName) -> bool:
	return change_state(collector, card_id, CardCollection.State.BOUND, CardCollection.State.EXPOSED)


## Exposed -> Bound: put back into the binder.
func rebind_card(collector: StringName, card_id: StringName) -> bool:
	return change_state(collector, card_id, CardCollection.State.EXPOSED, CardCollection.State.BOUND)


## Moves one stealable copy from victim to thief (arrives loose). Bound and
## lockbox-protected copies are safe, and so is anyone inside their grace period.
## `states` narrows what the method can take.
func steal_card(thief: StringName, victim: StringName, card_id: StringName, method: StringName,
		states: Array[CardCollection.State] = CardCollection.STEALABLE) -> bool:
	var from := collection(victim)
	var to := collection(thief)
	if from == null or to == null or thief == victim or grace_left(victim) > 0.0 \
			or stealable_copies(victim, card_id, states) == 0:
		return false
	for state in states:
		if from.remove(card_id, state):
			to.add(card_id, CardCollection.State.LOOSE)
			_robbed_at[victim] = Time.get_ticks_msec()
			EventBus.card_stolen.emit(thief, victim, card_id, method)
			_emit_tracker()
			if victim == PLAYER:
				check_loadout()
			return true
	return false


## Permanently spends one copy (gate cost, spell use). Takes the least protected copy first.
func consume_card(collector: StringName, card_id: StringName, reason: StringName) -> bool:
	var col := collection(collector)
	if col == null:
		return false
	for state in [CardCollection.State.LOOSE, CardCollection.State.EXPOSED, CardCollection.State.BOUND]:
		if col.remove(card_id, state):
			_reduce_supply(card_id)
			if collector == PLAYER and reason == &"gate":
				spent_on_gates[card_id] = spent_on_gates.get(card_id, 0) + 1
			EventBus.card_consumed.emit(collector, card_id, reason)
			_emit_tracker()
			return true
	return false


## Removes one loose copy without consuming it (it goes back on the ground, so
## world supply is unchanged). The caller places the pickup.
func drop_card(collector: StringName, card_id: StringName) -> bool:
	var col := collection(collector)
	if col == null or not col.remove(card_id, CardCollection.State.LOOSE):
		return false
	EventBus.card_consumed.emit(collector, card_id, &"dropped")
	_emit_tracker()
	return true


## Sells one copy. Sold cards leave the world for good (not recycled via the merchant).
func sell_card(collector: StringName, card_id: StringName) -> int:
	var card := CardDatabase.get_card(card_id)
	if card == null or not consume_card(collector, card_id, &"sold"):
		return 0
	add_currency(card.sell_value)
	EventBus.card_sold.emit(collector, card_id, card.sell_value)
	return card.sell_value


## Copies of `card_id` that could be stolen right now (minus one if lockbox-protected).
func stealable_copies(collector: StringName, card_id: StringName,
		states: Array[CardCollection.State] = CardCollection.STEALABLE) -> int:
	var col := collection(collector)
	if col == null:
		return 0
	var n := 0
	for state in states:
		n += col.count(card_id, state)
	return maxi(n - (1 if is_locked(collector, card_id) else 0), 0)


func stealable_card_ids(collector: StringName,
		states: Array[CardCollection.State] = CardCollection.STEALABLE) -> Array[StringName]:
	var out: Array[StringName] = []
	var col := collection(collector)
	if col:
		for id in col.card_ids():
			if stealable_copies(collector, id, states) > 0:
				out.append(id)
	return out


## Spends a Lockbox Seal to protect one copy of `card_id` for LOCKBOX_SECONDS.
func lock_card(collector: StringName, card_id: StringName, lockbox_id: StringName) -> bool:
	if card_id == lockbox_id or is_locked(collector, card_id) or stealable_copies(collector, card_id) == 0:
		return false
	if not consume_card(collector, lockbox_id, &"spell"):
		return false
	if not _locks.has(collector):
		_locks[collector] = {}
	_locks[collector][card_id] = Time.get_ticks_msec() + int(LOCKBOX_SECONDS * 1000.0)
	EventBus.card_locked.emit(collector, card_id, LOCKBOX_SECONDS)
	return true


func is_locked(collector: StringName, card_id: StringName) -> bool:
	return lock_time_left(collector, card_id) > 0.0


func lock_time_left(collector: StringName, card_id: StringName) -> float:
	var expiry: int = _locks.get(collector, {}).get(card_id, 0)
	return maxf((expiry - Time.get_ticks_msec()) / 1000.0, 0.0)


## Seconds until `collector` can be robbed again.
func grace_left(collector: StringName) -> float:
	if not _robbed_at.has(collector):
		return 0.0
	return maxf(GRACE_SECONDS - (Time.get_ticks_msec() - _robbed_at[collector]) / 1000.0, 0.0)


## Ends a grace period early (tests and debugging).
func clear_grace(collector: StringName) -> void:
	_robbed_at.erase(collector)


func buy_card(collector: StringName, card_id: StringName) -> bool:
	var card := CardDatabase.get_card(card_id)
	if card == null or card.shop_price <= 0 or currency < card.shop_price:
		return false
	add_currency(-card.shop_price)
	return add_loose_card(collector, card_id)


## What buying back a spent card costs.
func rebuy_price(card_id: StringName) -> int:
	var card := CardDatabase.get_card(card_id)
	return maxi(card.sell_value, 10) * REBUY_MARKUP if card else 0


## Buys back one copy of a card the player spent on a gate (it comes back Loose).
func rebuy_card(card_id: StringName) -> bool:
	var price := rebuy_price(card_id)
	if spent_on_gates.get(card_id, 0) <= 0 or currency < price:
		return false
	add_currency(-price)
	spent_on_gates[card_id] -= 1
	if spent_on_gates[card_id] <= 0:
		spent_on_gates.erase(card_id)
	if world_supply.has(card_id):
		world_supply[card_id] += 1
	return add_loose_card(PLAYER, card_id)


func set_in_safe_zone(collector: StringName, inside: bool) -> void:
	var n: int = _safe_zones.get(collector, 0) + (1 if inside else -1)
	_safe_zones[collector] = maxi(n, 0)
	EventBus.safe_zone_changed.emit(collector, is_in_safe_zone(collector))


func is_in_safe_zone(collector: StringName) -> bool:
	return _safe_zones.get(collector, 0) > 0


## Seconds to bind one card right now: instant in towns, slower in the field.
func bind_time(collector: StringName) -> float:
	return 0.0 if is_in_safe_zone(collector) else FIELD_BIND_TIME


func boss_data(id: StringName) -> BossData:
	return _boss_data.get(id)


func all_bosses() -> Array[BossData]:
	var out: Array[BossData] = []
	out.assign(_boss_data.values())
	return out


func is_boss_alive(id: StringName) -> bool:
	return bosses.get(id, {}).get("alive", false)


func boss_kills_left(id: StringName) -> int:
	var data := boss_data(id)
	return data.kill_cap - bosses.get(id, {}).get("kills", 0) if data else 0


## Records a boss kill. Returns false if it wasn't alive (already dead).
func kill_boss(id: StringName, killer: StringName) -> bool:
	if not is_boss_alive(id):
		return false
	bosses[id].kills += 1
	bosses[id].alive = false
	EventBus.boss_defeated.emit(id, killer)
	return true


func _respawn_boss(id: StringName, gate_id: StringName) -> void:
	if bosses.has(id) and not bosses[id].alive and boss_kills_left(id) > 0:
		bosses[id].alive = true
		EventBus.boss_returned.emit(id, gate_id)


func rival_profile(id: StringName) -> RivalProfile:
	return _rival_profiles.get(id)


## Sends a rival to `zone`. With no position it appears at that zone's RivalSpots/<id>.
func move_rival(id: StringName, zone: String, pos: Variant = null) -> void:
	rival_locations[id] = { "zone": zone, "position": pos }


## Called when a zone scene loads: presence in the old zone's areas is gone.
func reset_zone_presence() -> void:
	_safe_zones.clear()
	menus_open = 0


func add_zone_drop(zone: String, card_id: StringName, pos: Vector2) -> void:
	if not zone_drops.has(zone):
		zone_drops[zone] = []
	zone_drops[zone].append({ "card_id": card_id, "position": pos })


func remove_zone_drop(zone: String, card_id: StringName, pos: Vector2) -> void:
	var drops: Array = zone_drops.get(zone, [])
	for i in drops.size():
		if drops[i].card_id == card_id and drops[i].position.is_equal_approx(pos):
			drops.remove_at(i)
			return


## Records that the player has now held `card_id`; true the first time only.
func mark_card_seen(card_id: StringName) -> bool:
	if seen_cards.has(card_id):
		return false
	seen_cards[card_id] = true
	return true


## Adds something the player read to the journal (once per title and place).
func note(title: String, place: String, lines: PackedStringArray) -> void:
	for entry in journal:
		if entry.title == title and entry.place == place:
			return
	journal.append({ "title": title, "place": place, "lines": lines })


func push_menu() -> void:
	menus_open += 1
	EventBus.menus_changed.emit(menus_open)


func pop_menu() -> void:
	menus_open = maxi(menus_open - 1, 0)
	EventBus.menus_changed.emit(menus_open)


func open_gate(gate_id: StringName, by: StringName) -> bool:
	var gate := CardDatabase.get_gate(gate_id)
	if gate == null or opened_gates.has(gate_id):
		return false
	var col := collection(by)
	if col == null or col.count(gate.cost_card_id) < gate.cost_amount:
		return false
	for i in gate.cost_amount:
		consume_card(by, gate.cost_card_id, &"gate")
	opened_gates[gate_id] = by
	EventBus.gate_opened.emit(gate_id, by)
	if gate.respawns_boss != &"":
		_respawn_boss(gate.respawns_boss, gate_id)
	return true


## Wears a passive buff card (moves one copy to Exposed). False if the slots are
## full, it isn't a passive card, or no free copy is held.
func equip(card_id: StringName) -> bool:
	var card := CardDatabase.get_card(card_id)
	var col := collection(PLAYER)
	if card == null or card.category != CardData.Category.BUFF_PASSIVE or equipped.size() >= EQUIP_SLOTS \
			or equipped.has(card_id):
		return false
	var from := CardCollection.State.LOOSE if col.count(card_id, CardCollection.State.LOOSE) > 0 else CardCollection.State.BOUND
	if not col.move(card_id, from, CardCollection.State.EXPOSED):
		return false
	equipped.append(card_id)
	EventBus.loadout_changed.emit()
	return true


## Takes a worn card off, back into the binder (Bound).
func unequip(card_id: StringName) -> bool:
	if not equipped.has(card_id):
		return false
	equipped.erase(card_id)
	collection(PLAYER).move(card_id, CardCollection.State.EXPOSED, CardCollection.State.BOUND)
	EventBus.loadout_changed.emit()
	return true


func is_equipped(card_id: StringName) -> bool:
	return equipped.has(card_id)


## Drops worn cards the player no longer holds (stolen while worn).
func check_loadout() -> void:
	var col := collection(PLAYER)
	for id in equipped.duplicate():
		if col.count(id, CardCollection.State.EXPOSED) == 0:
			equipped.erase(id)
			EventBus.loadout_changed.emit()


func add_item(id: StringName, amount := 1) -> void:
	items[id] = items.get(id, 0) + amount
	if items[id] <= 0:
		items.erase(id)
	EventBus.items_changed.emit()


func item_count(id: StringName) -> int:
	return items.get(id, 0)


## Buys one of an item at its price. False when unaffordable or unknown.
func buy_item(id: StringName) -> bool:
	var item := Items.get_item(id)
	if item == null or currency < item.price:
		return false
	add_currency(-item.price)
	add_item(id)
	return true


## Uses one item on the player (heals). False when none are carried, it's unknown,
## or it would do nothing (already at full health).
func use_item(id: StringName) -> bool:
	var item := Items.get_item(id)
	if item == null or item_count(id) <= 0:
		return false
	var player := get_tree().get_first_node_in_group(&"player") as Player
	if item.heal > 0 and (player == null or player.health >= player.max_health):
		return false
	if player and item.heal > 0:
		player.heal(item.heal)
		Sfx.play(&"heal")
	add_item(id, -1)
	return true


func add_currency(amount: int) -> void:
	currency += amount
	EventBus.currency_changed.emit(currency)


func tracker_counts() -> Dictionary[StringName, int]:
	var final_set := CardDatabase.final_set()
	var out: Dictionary[StringName, int] = {}
	for id in collectors():
		out[id] = collection(id).set_progress(final_set)
	return out


func _reduce_supply(card_id: StringName) -> void:
	if world_supply.has(card_id):
		world_supply[card_id] = maxi(world_supply[card_id] - 1, 0)


func _emit_tracker() -> void:
	EventBus.tracker_changed.emit(tracker_counts())
