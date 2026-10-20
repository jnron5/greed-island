extends Node
## Duskara's Card Souk: five dealers each with their own trade (spells, brews,
## charms, way-cards for every town, and a broker selling the island's set cards, a
## different handful each day, at BROKER_MARKUP x their worth); and what the new cards
## do: brews and veils run as timed boons, Glass Skin turns blows aside, the Dust Devil
## stuns everyone close, a Mirage Veil hides you from a rival's eyes.
## Run: godot --headless --path . res://tests/test_souk.tscn

const P := &"player"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	TimeOfDay.set_hour(12.0)
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var town: Zone = load(WorldMap.DUSKARA).instantiate()
	add_child(town)
	await get_tree().process_frame
	var dealers := {}
	for id in [&"vash", &"hana", &"ammar", &"tamsa", &"isra"]:
		for n in town.get_children():
			if n is Npc and n.npc_id == id:
				dealers[id] = n
	_check("five dealers in the souk, each with a shop", dealers.size() == 5
		and dealers.values().all(func(n: Npc) -> bool: return n.has_shop()))
	var tamsa: Npc = dealers.get(&"tamsa")
	_check("Tamsa sells a way-card for every town", tamsa != null
		and CardSpells.RETURN_CARDS.keys().all(func(id: StringName) -> bool: return tamsa.shop_stock.has(id)))
	var isra: Npc = dealers.get(&"isra")
	var today := isra.current_stock()
	var sets := today.filter(func(id: StringName) -> bool: return CardDatabase.get_card(id).category == CardData.Category.SET)
	_check("Isra has four set cards on her counter today", sets.size() == 4)
	_check("the same four all day", isra.current_stock() == today)
	TimeOfDay.day += 1
	_check("a different handful tomorrow", isra.current_stock() != today)
	var card := CardDatabase.get_card(sets[0])
	_check("at a steep price", GameState.card_price(card) == maxi(card.sell_value, 8) * GameState.BROKER_MARKUP)
	GameState.currency = 1000
	var had := GameState.collection(P).count(card.id)
	_check("you can buy one", GameState.buy_card(P, card.id) and GameState.collection(P).count(card.id) == had + 1
		and GameState.currency == 1000 - GameState.card_price(card))
	_check("the new spells and brews are on the counters", dealers[&"vash"].shop_stock.has(CardSpells.MIRAGE)
		and dealers[&"vash"].shop_stock.has(CardSpells.DUST_DEVIL) and dealers[&"hana"].shop_stock.has(CardSpells.GLASS_SKIN)
		and dealers[&"ammar"].shop_stock.has(CardSpells.SCARAB_WARD))
	_check("every card for sale has a price", dealers.values().all(func(n: Npc) -> bool:
		return n.current_stock().all(func(id: StringName) -> bool:
			return Items.get_item(id) != null or GameState.card_price(CardDatabase.get_card(id)) > 0)))
	town.queue_free()
	await get_tree().process_frame

	# What the cards do.
	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(player)
	await get_tree().process_frame
	player.set_physics_process(false)
	for id in [CardSpells.GLASS_SKIN, CardSpells.SWIFTSAND, CardSpells.SCARAB_FURY, CardSpells.MIRAGE, CardSpells.DUST_DEVIL]:
		GameState.add_loose_card(P, id)
	_check("Glass Skin is used from the binder and runs as a boon", CardSpells.is_usable(CardSpells.GLASS_SKIN)
		and CardSpells.use(player, CardSpells.GLASS_SKIN) and GameState.has_boon(P, CardSpells.GLASS_SKIN)
		and GameState.collection(P).count(CardSpells.GLASS_SKIN) == 0)
	var before := player.health
	player._on_hurt(_hit(2))
	await get_tree().create_timer(0.4).timeout
	_check("under Glass Skin a blow glances off", player.health == before)
	GameState.boons.clear()
	player._on_hurt(_hit(1))
	_check("and when it's gone, blows land again", player.health == before - 1)
	_check("Swiftsand and Scarab Fury start their boons", CardSpells.use(player, CardSpells.SWIFTSAND)
		and CardSpells.use(player, CardSpells.SCARAB_FURY) and GameState.has_boon(P, CardSpells.SWIFTSAND))
	GameState.add_boon(P, &"test", 0.2)
	await get_tree().create_timer(0.4).timeout
	_check("boons run out", not GameState.has_boon(P, &"test"))

	var monster: Monster = load("res://scenes/characters/dune_caracal.tscn").instantiate()
	add_child(monster)
	monster.global_position = player.global_position + Vector2(60, 0)
	var far: Monster = load("res://scenes/characters/dune_caracal.tscn").instantiate()
	add_child(far)
	far.global_position = player.global_position + Vector2(600, 0)
	await get_tree().process_frame
	_check("the Dust Devil stuns beasts close by, not far off", CardSpells.cast_dust_devil(player)
		and monster._frozen > 0.0 and far._frozen == 0.0)

	var rival: Rival = load("res://scenes/characters/rival.tscn").instantiate()
	rival.apply_profile(GameState.rival_profile(GameState.active_rivals[0]))
	add_child(rival)
	rival.global_position = player.global_position + Vector2(0, 40)
	await get_tree().process_frame
	var seen := rival.awareness.perceived_gain(player)
	CardSpells.use(player, CardSpells.MIRAGE)
	_check("a Mirage Veil hides you from a rival's eyes", seen > 0.0 and rival.awareness.perceived_gain(player) == 0.0
		and GameState.is_veiled(P))
	rival.stun(1.0)
	_check("a rival can be stunned too", rival._stunned > 0.0)
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _hit(damage: int) -> Hitbox:
	var hitbox := Hitbox.new()
	hitbox.source_id = Combat.MONSTER
	hitbox.damage = damage
	hitbox.knockback = 0.0
	add_child(hitbox)
	return hitbox


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
