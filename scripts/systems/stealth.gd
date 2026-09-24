class_name Stealth
extends RefCounted
## Stealth steals: free, chance-based, one loose card. A failed attempt alerts
## the target. Works in both directions: player -> rival (chance from the
## rival's Awareness meter) and rival -> player (chance from the player's facing).

const STEAL_RANGE := 26.0

const CHANCE_BY_LEVEL := {
	Awareness.Level.UNAWARE: 0.85,
	Awareness.Level.SUSPICIOUS: 0.5,
	Awareness.Level.ALERT: 0.1,
}
const BEHIND_BONUS := 0.1
## A rival that already caught someone stays hard to rob.
const WARY_MULTIPLIER := 0.6
## A successful lift still makes the target a little uneasy.
const SUCCESS_BUMP := 25.0

## The player has no awareness meter: it comes down to which way they face.
const PLAYER_BEHIND := 0.6
const PLAYER_SIDE := 0.35
const PLAYER_FACING := 0.12


static func success_chance(thief: Node2D, victim: Node2D) -> float:
	var awareness := victim.get_node_or_null(^"Awareness") as Awareness
	if awareness:
		var chance: float = CHANCE_BY_LEVEL[awareness.level]
		if is_behind(thief, victim):
			chance += BEHIND_BONUS
		if awareness.is_wary():
			chance *= WARY_MULTIPLIER
		return clampf(chance, 0.05, 0.95)
	var dot := _facing_dot(thief, victim)
	if dot < -0.3:
		return PLAYER_BEHIND
	if dot > 0.3:
		return PLAYER_FACING
	return PLAYER_SIDE


static func is_behind(thief: Node2D, victim: Node2D) -> bool:
	return _facing_dot(thief, victim) < -0.3


## Why a stealth attempt can't happen right now, or "" if it can.
static func blocker(thief: Node2D, victim: Node2D) -> String:
	var victim_id: StringName = victim.get(&"collector_id")
	if thief.global_position.distance_to(victim.global_position) > STEAL_RANGE:
		return "Too far away"
	if not Zone.same_level(thief.get_tree(), thief.global_position, victim.global_position):
		return "Out of reach from here"
	if GameState.grace_left(victim_id) > 0.0:
		return "They were just robbed"
	if GameState.stealable_card_ids(victim_id, CardCollection.LOOSE_ONLY).is_empty():
		return "No loose cards to lift"
	return ""


## Rolls a stealth steal. `roll` in [0, 1) forces the outcome (tests); < 0 = random.
## Returns { ok: bool, card_id: StringName, reason: String }.
static func attempt(thief: Node2D, victim: Node2D, roll := -1.0) -> Dictionary:
	var thief_id: StringName = thief.get(&"collector_id")
	var victim_id: StringName = victim.get(&"collector_id")
	var reason := blocker(thief, victim)
	if reason != "":
		return { "ok": false, "card_id": &"", "reason": reason }

	var chance := success_chance(thief, victim)
	if roll < 0.0:
		roll = randf()
	var awareness := victim.get_node_or_null(^"Awareness") as Awareness
	if roll < chance:
		var card_id: StringName = GameState.stealable_card_ids(victim_id, CardCollection.LOOSE_ONLY).pick_random()
		GameState.steal_card(thief_id, victim_id, card_id, &"stealth", CardCollection.LOOSE_ONLY)
		if awareness:
			awareness.bump(SUCCESS_BUMP)
		return { "ok": true, "card_id": card_id, "reason": "" }

	if awareness:
		awareness.alarm()
	EventBus.stealth_failed.emit(thief_id, victim_id)
	return { "ok": false, "card_id": &"", "reason": "Caught" }


static func _facing_dot(thief: Node2D, victim: Node2D) -> float:
	var facing: Vector2 = victim.get(&"facing")
	return facing.normalized().dot(victim.global_position.direction_to(thief.global_position))
