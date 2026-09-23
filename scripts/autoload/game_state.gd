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

var active_rivals: Array[StringName] = []
var collections: Dictionary[StringName, CardCollection] = {}
var currency := 0
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


func _ready() -> void:
	new_game(DEFAULT_RIVALS)


func new_game(rivals: Array[StringName]) -> void:
	assert(rivals.size() == 2, "Pick exactly 2 of the 3 rivals")
	active_rivals = rivals.duplicate()
	collections.clear()
	for id in collectors():
		collections[id] = CardCollection.new(id)
	currency = STARTING_GOLD
	_locks.clear()
	_robbed_at.clear()
	quest_flags.clear()
	opened_gates.clear()
	world_supply.clear()
	for card in CardDatabase.all_cards():
		if not card.is_effectively_infinite():
			world_supply[card.id] = card.max_possible_copies()
	_emit_tracker()
	EventBus.currency_changed.emit(currency)


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
			EventBus.card_consumed.emit(collector, card_id, reason)
			_emit_tracker()
			return true
	return false


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


func set_in_safe_zone(collector: StringName, inside: bool) -> void:
	var n: int = _safe_zones.get(collector, 0) + (1 if inside else -1)
	_safe_zones[collector] = maxi(n, 0)
	EventBus.safe_zone_changed.emit(collector, is_in_safe_zone(collector))


func is_in_safe_zone(collector: StringName) -> bool:
	return _safe_zones.get(collector, 0) > 0


## Seconds to bind one card right now: instant in towns, slower in the field.
func bind_time(collector: StringName) -> float:
	return 0.0 if is_in_safe_zone(collector) else FIELD_BIND_TIME


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
