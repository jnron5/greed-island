class_name SoftLockCheck
extends RefCounted
## No-soft-lock rule. Every finite card must have enough copies for all three
## collectors' final sets plus every gate that consumes it plus expected sales
## (sold cards leave the world permanently, so sales count as consumption).
##
##   finite supply >= final_set_count x 3 + gate consumption + sale_allowance
##
## Boss cards use max_possible_copies = starting drops + drops per kill x kill cap.
## Commons that drop from respawning monsters are effectively infinite.
##
## Used by the editor script (soft_lock_validator.gd) and the headless runner.

const COMPETITORS := 3
const CARD_DIR := "res://data/cards/"
const GATE_DIR := "res://data/gates/"
const BOSS_DIR := "res://data/bosses/"


static func run() -> Dictionary:
	var cards: Dictionary[StringName, CardData] = {}
	var gates: Array[GateData] = []
	var errors: PackedStringArray = []
	var warnings: PackedStringArray = []
	var lines: PackedStringArray = []

	for file in ResourceLoader.list_directory(CARD_DIR):
		if not file.ends_with(".tres"):
			continue
		var card := load(CARD_DIR + file) as CardData
		if card == null:
			errors.append("%s is not a CardData" % file)
		elif card.id == &"":
			errors.append("%s has no id" % file)
		elif cards.has(card.id):
			errors.append("Duplicate card id '%s' (%s)" % [card.id, file])
		else:
			cards[card.id] = card
	for file in ResourceLoader.list_directory(GATE_DIR):
		if file.ends_with(".tres"):
			var gate := load(GATE_DIR + file) as GateData
			if gate:
				gates.append(gate)

	var gate_use: Dictionary[StringName, int] = {}
	for gate in gates:
		var cost := cards.get(gate.cost_card_id) as CardData
		if cost == null:
			errors.append("Gate '%s' costs unknown card '%s'" % [gate.id, gate.cost_card_id])
			continue
		if not cost.gate_card:
			errors.append("Gate '%s' costs '%s', which is not flagged gate_card" % [gate.id, cost.id])
		gate_use[cost.id] = int(gate_use.get(cost.id, 0)) + gate.cost_amount

	for id in cards:
		var card: CardData = cards[id]
		var gate_need: int = gate_use.get(id, 0)
		if card.gate_card and not gate_use.has(id):
			warnings.append("'%s' is a gate card but no gate uses it" % id)
		if card.category != CardData.Category.SET:
			continue
		var set_need := card.final_set_count * COMPETITORS if card.is_final_set_member else 0
		var need := set_need + gate_need + card.sale_allowance
		if card.is_effectively_infinite():
			lines.append("  ok   %-24s respawning drop (infinite), demand %d" % [id, need])
			continue
		var supply := card.max_possible_copies()
		if supply < need:
			errors.append("'%s' supply %d < demand %d (set %d + gates %d + sales %d)"
				% [id, supply, need, set_need, gate_need, card.sale_allowance])
		else:
			lines.append("  ok   %-24s supply %d >= demand %d" % [id, supply, need])
		if card.source == CardData.Source.BOSS and not (card.boss_kill_cap >= 3 and card.boss_kill_cap <= 4):
			warnings.append("'%s' boss kill cap is %d (design target 3-4)" % [id, card.boss_kill_cap])

	# Hand-placed pickups across every zone can't exceed a finite card's supply.
	var placed: Dictionary[StringName, int] = {}
	for pickup: Dictionary in WorldMap.all_placed_pickups():
		placed[pickup.card_id] = placed.get(pickup.card_id, 0) + 1
		if pickup.gate != &"" and _find_gate(gates, pickup.gate) == null:
			errors.append("Pickup %s is behind unknown gate '%s'" % [pickup.key, pickup.gate])
	for id in placed:
		var card := cards.get(id) as CardData
		if card == null:
			errors.append("A zone places unknown card '%s'" % id)
		elif not card.is_effectively_infinite() and card.source != CardData.Source.BOSS 				and placed[id] > card.copies_in_world:
			errors.append("'%s' is placed %d times but only %d copies exist" % [id, placed[id], card.copies_in_world])

	# Bosses: kills beyond the first need respawn gates, and the drops must be
	# boss cards whose kill cap matches (that's what their supply is computed from).
	for file in ResourceLoader.list_directory(BOSS_DIR):
		var boss := load(BOSS_DIR + file) as BossData if file.ends_with(".tres") else null
		if boss == null:
			continue
		var respawn_gates := 0
		for gate in gates:
			if gate.respawns_boss == boss.id:
				respawn_gates += 1
		if respawn_gates + 1 < boss.kill_cap:
			warnings.append("Boss '%s' has kill cap %d but only %d respawn gate(s): at most %d kills possible"
				% [boss.id, boss.kill_cap, respawn_gates, respawn_gates + 1])
		for drop in boss.drop_card_ids:
			var card := cards.get(drop) as CardData
			if card == null:
				errors.append("Boss '%s' drops unknown card '%s'" % [boss.id, drop])
			elif card.source != CardData.Source.BOSS or card.boss_kill_cap != boss.kill_cap:
				errors.append("Boss '%s' drop '%s' should be a BOSS card with kill cap %d" % [boss.id, drop, boss.kill_cap])

	return {
		"cards": cards.size(),
		"gates": gates.size(),
		"errors": errors,
		"warnings": warnings,
		"lines": lines,
	}


static func _find_gate(gates: Array[GateData], id: StringName) -> GateData:
	for gate in gates:
		if gate.id == id:
			return gate
	return null


static func print_report(result: Dictionary) -> void:
	print("No-soft-lock check: %d cards, %d gates" % [result.cards, result.gates])
	for line in result.lines:
		print(line)
	for w in result.warnings:
		print("  WARN %s" % w)
	for e in result.errors:
		printerr("  FAIL %s" % e)
	print("PASS" if result.errors.is_empty() else "FAILED with %d error(s)" % result.errors.size())
