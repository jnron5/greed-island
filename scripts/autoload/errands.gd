extends Node
## Errands: set cards (and a few other rewards) that residents hand over, some just
## for a chat, most for a small favour: bring them something from your satchel, pay
## them, clear out monsters, go and see a place, or turn up with a few cards. One per
## resident at most. Npc.talk() asks dialogue_for() after the Quests autoload; when the
## favour is done, talking again hands over the card.
##
## Each collector can have each errand's card once, like a chest: rivals do the same
## errands off screen (WorldMap lists errand cards as pickups of their zone, keyed
## "errand:<id>", so RivalDirector collects them with the zone's chests).
##
## Progress lives in GameState.quest_flags ("errand:<id>" = 1 when asked, 99 when done;
## kill counts under "kills:<monster>").

const ASKED := 1
const DONE := 99

## id -> {
##   npc: resident id, zone: the outdoor zone rivals count it under, card: set card id,
##   need: "talk" | "item" | "gold" | "kills" | "visit" | "cards",
##   item/count, gold, monster/count, place (zone path) + place_name, count (cards),
##   ask: lines when asking, waiting: line while it isn't done yet, give: lines on handing over,
##   after: line once it's done }
const ERRANDS := {
	# ---- Kalmora ----
	&"luca_feather": {
		"npc": &"sailor", "zone": "res://scenes/world/kalmora.tscn", "card": &"gull_feather", "need": "talk",
		"give": [
			"First race, is it? Here. Every deckhand trades a gull feather before a long haul.",
			"It's a card, mind. Everything worth having on this island is. Keep it bound in town and nobody can lift it off you.",
		],
		"after": "Fair winds, racer. Bind your cards before you leave town.",
	},
	&"pip_bread": {
		"npc": &"pip", "zone": "res://scenes/world/kalmora.tscn", "card": &"fishers_knot", "need": "item",
		"item": &"bread", "count": 1,
		"ask": [
			"Fish all day, fish for supper, fish for breakfast. I'd trade anything for a bit of bread.",
			"Bring me a loaf? Rosa sells them at her stall, or Greta has them in her shop. I'll make it worth your while.",
		],
		"waiting": "Just one loaf. I can smell Rosa's stall from here and it's torture.",
		"give": [
			"Bread! Real bread! Here, take this. Grandad's knot. Nobody knows who tied the first one.",
			"Cards open gates, see? Or you keep 'em for the set. Your call which.",
		],
		"after": "Mm. Still warm, nearly.",
	},
	&"rosa_coin": {
		"npc": &"baker", "zone": "res://scenes/world/kalmora.tscn", "card": &"coral_coin", "need": "talk",
		"give": [
			"A racer! My till is full of these old coral coins. From before the cards, when money was money.",
			"Have one. Nobody takes them anymore, but they count toward a set, so I hear.",
		],
		"after": "Warm bread! Two coins a loaf, or one if you tell me a good rumour.",
	},
	&"tomas_hounds": {
		"npc": &"tomas", "zone": "res://scenes/world/kalmora.tscn", "card": &"tide_bell", "need": "kills",
		"monster": &"briar_hound", "count": 3,
		"ask": [
			"Hear that? Hounds, up past the north gate in Thornveil. They howl all night at my light.",
			"You carry a sword under that cloak, I'd bet. Go and thin them out. Three will do. Strike, dash out of the way when one crouches to lunge, strike again.",
			"There's an old bell in my cottage that's no use to me. It's yours if you do.",
		],
		"waiting": "Still howling. %d of 3 hounds down.",
		"give": [
			"Quiet as a church last night. Thank you.",
			"The Tide Bell. It rings an hour before high water, and on nights when strange ships come in. Take it.",
		],
		"after": "Slept like a stone. Mind the lens room: that door stays shut.",
	},
	&"mirela_racer": {
		"npc": &"mirela", "zone": "res://scenes/world/kalmora.tscn", "card": &"harbor_lantern", "need": "cards",
		"count": 3,
		"ask": [
			"A racer with no cards is a tourist. Come back when you've three in hand and I'll take you seriously.",
		],
		"waiting": "Three cards, racer. You've %d.",
		"give": [
			"Three cards. You're serious, then.",
			"Take a harbor lantern. Every pier in Kalmora hangs one. They count toward the set, and the King's men keep the tally honest.",
		],
		"after": "Everything on my quay is stamped. Everything.",
	},
	&"otto_compass": {
		"npc": &"otto", "zone": "res://scenes/world/kalmora.tscn", "card": &"salt_compass", "need": "talk",
		"give": [
			"A sailor paid his tab with this last week and never came back for it. Salt Compass. Needle points to sea.",
			"Guard Rook won't lift the north bar for anything else. Go on, take it. Somebody should get out of this town.",
		],
		"after": "Sit anywhere that isn't sticky.",
	},
	&"nonna_fish": {
		"npc": &"nonna", "zone": "res://scenes/world/kalmora.tscn", "card": &"terracotta_tile", "need": "item",
		"item": &"smoked_fish", "count": 1,
		"ask": [
			"I'd make you soup, but I've no fish. My knees don't go down to the market anymore.",
			"Bring me a smoked fish from Greta and I'll give you something from the roof. The storm knocked a tile loose, a stamped one.",
		],
		"waiting": "One smoked fish, dear. Greta keeps them by the counter.",
		"give": [
			"There. Soup tonight. And the tile, stamped with the old port crest.",
			"My grandfather laid that roof. Funny, a thing like that counting toward a fortune.",
		],
		"after": "The racers never come back for soup. You might.",
	},
	&"brannoc_gold": {
		"npc": &"brannoc", "zone": "res://scenes/world/kalmora.tscn", "card": &"net_mender", "need": "gold",
		"gold": 30,
		"ask": [
			"Got a net mender here a fisher traded me for a hook. Bone, older than the forge.",
			"Thirty gold and it's yours. That's a card, not a bargain. Cards are worth what somebody needs them for.",
		],
		"waiting": "Thirty gold for the net mender. The anvil doesn't haggle and neither do I.",
		"give": ["Done. Mind the anvil on your way out."],
		"after": "Forty pickaxe heads a month. Must be a very big hole.",
	},
	&"ilse_visit": {
		"npc": &"ilse", "zone": "res://scenes/world/kalmora.tscn", "card": &"lighthouse_wick", "need": "visit",
		"place": "res://scenes/world/sorenda.tscn", "place_name": "Sorenda",
		"ask": [
			"I map the island, but my knees stop at the north gate. Walk to Sorenda for me, the village in Thornveil Forest, and tell me it's still where I drew it.",
			"Keeper Tomas left a wick here when he came to have his lamp room measured. I'll trade it for the news.",
		],
		"waiting": "Sorenda. North through the gate, through Thornveil, and up the forest road.",
		"give": [
			"Still there? Good. I'll ink it darker.",
			"Here's Tomas's wick. He'll never miss it. He's got three more and forgets them all.",
		],
		"after": "Every map of Virelia has a blank where Duskara's mine should be. I'm working on that.",
	},
	# ---- Sorenda ----
	&"harl_charm": {
		"npc": &"harl", "zone": "res://scenes/world/sorenda.tscn", "card": &"thatch_charm", "need": "kills",
		"monster": &"moss_boar", "count": 2,
		"ask": [
			"Moss boars have been rooting up the trail through Thornveil. Tusks like hatchets.",
			"Watch for when one lowers its head and paws the ground. That's the charge coming. Dash aside, then hit it while it turns.",
			"Put two down and I'll give you a charm off my roof. Keeps the rain out. Counts in the race, too.",
		],
		"waiting": "%d of 2 boars. They're down in Thornveil's lowlands, by the south clearing.",
		"give": ["Trail's clear. Here, a Thatch Charm, woven from my own roof."],
		"after": "Mind the brambles. They grow back by morning.",
	},
	&"wren_quill": {
		"npc": &"wren", "zone": "res://scenes/world/sorenda.tscn", "card": &"owl_quill", "need": "talk",
		"give": [
			"You're the racer Pell was on about. Take a quill. Sorenda's scribes write only with these.",
			"You'll want to write things down out there. The forest has a way of making you forget.",
		],
		"after": "I copy the old stories out every winter so they don't fade.",
	},
	&"juniper_tonic": {
		"npc": &"juniper", "zone": "res://scenes/world/sorenda.tscn", "card": &"mushroom_ring", "need": "item",
		"item": &"healers_tonic", "count": 1,
		"ask": [
			"I brew my own, but I want to see what Kalmora sells as a Healer's Tonic. Probably mostly sugar.",
			"Bring me one? I'll trade a ring from the mushroom circle. Step inside one and the forest goes quiet.",
		],
		"waiting": "A Healer's Tonic from Kalmora. Greta sells them. Or you'll find one.",
		"give": ["Hm. Sugar, sea salt, and... not bad, actually. Here's your ring."],
		"after": "Moss is the best medicine. Mostly.",
	},
}


func _ready() -> void:
	EventBus.monster_defeated.connect(_on_monster_defeated)
	EventBus.area_entered.connect(func(_title: String, _interior: bool) -> void: _note_visit())


func state(id: StringName) -> int:
	return GameState.quest_flags.get(StringName("errand:%s" % id), 0)


func errand_for(npc_id: StringName) -> StringName:
	for id: StringName in ERRANDS:
		if ERRANDS[id].npc == npc_id:
			return id
	return &""


## What `npc_id` says about their errand (empty = nothing to say about it).
## Talking can also hand over the card: call talked_to() when the chat ends.
func dialogue_for(npc_id: StringName) -> PackedStringArray:
	var id := errand_for(npc_id)
	if id == &"":
		return PackedStringArray()
	var e: Dictionary = ERRANDS[id]
	match state(id):
		DONE:
			return PackedStringArray()
		ASKED:
			if is_met(id):
				return PackedStringArray(e.give)
			return PackedStringArray([String(e.waiting) % _progress(id) if "%d" in String(e.waiting) else e.waiting])
		_:
			if e.need == "talk" or is_met(id):
				return PackedStringArray(e.give)
			return PackedStringArray(e.ask)


## After a chat: first time marks the errand asked; once it's met, pays it out.
func talked_to(npc_id: StringName) -> void:
	var id := errand_for(npc_id)
	if id == &"" or state(id) == DONE:
		return
	if is_met(id):
		_complete(id)
	elif state(id) != ASKED:
		GameState.quest_flags[StringName("errand:%s" % id)] = ASKED
		EventBus.notify.emit("Favour: %s" % summary(id))


## "!" before you've spoken, "?" when you can hand it in.
func marker_for(npc_id: StringName) -> String:
	var id := errand_for(npc_id)
	if id == &"" or state(id) == DONE:
		return ""
	if is_met(id) or (state(id) != ASKED and ERRANDS[id].need == "talk"):
		return "?" if state(id) == ASKED else "!"
	return "!" if state(id) != ASKED else ""


func is_met(id: StringName) -> bool:
	var e: Dictionary = ERRANDS[id]
	match e.need:
		"talk":
			return true
		"item":
			return GameState.item_count(e.item) >= e.count
		"gold":
			return GameState.currency >= e.gold
		"kills":
			return _kills(e.monster) >= e.count
		"visit":
			return GameState.quest_flags.has(StringName("visited:%s" % e.place))
		"cards":
			return _cards_held() >= e.count
	return false


## One line for the HUD's tracker.
func summary(id: StringName) -> String:
	var e: Dictionary = ERRANDS[id]
	var who := _npc_name(e.npc)
	match e.need:
		"item":
			var item := Items.get_item(e.item)
			return "bring %s %s" % [who, item.display_name if item else String(e.item)]
		"gold":
			return "%s sells a card for %d gold" % [who, e.gold]
		"kills":
			return "%s: defeat %s (%d/%d)" % [who, String(e.monster).replace("_", " ") + "s", mini(_kills(e.monster), e.count), e.count]
		"visit":
			return "%s: visit %s" % [who, e.place_name]
		"cards":
			return "%s: hold %d cards (%d)" % [who, e.count, _cards_held()]
	return "talk to %s" % who


## Tracker lines for errands asked but not yet handed in.
func tracker_lines() -> PackedStringArray:
	var out := PackedStringArray()
	for id: StringName in ERRANDS:
		if state(id) == ASKED:
			out.append(("%s: ready to hand in" % _npc_name(ERRANDS[id].npc)) if is_met(id) else summary(id))
	return out


## Errand cards for WorldMap's pickup list: { "key", "card_id", "gate" } for `zone`.
static func pickups_in(zone: String) -> Array:
	var out := []
	for id: StringName in ERRANDS:
		if ERRANDS[id].zone == zone:
			out.append({ "key": "errand:%s" % id, "card_id": ERRANDS[id].card, "gate": &"" })
	return out


func _complete(id: StringName) -> void:
	var e: Dictionary = ERRANDS[id]
	match e.need:
		"item":
			GameState.add_item(e.item, -int(e.count))
		"gold":
			GameState.add_currency(-e.gold)
	GameState.quest_flags[StringName("errand:%s" % id)] = DONE
	GameState.collected_pickups["errand:%s" % id] = true
	GameState.add_loose_card(GameState.PLAYER, e.card)
	var card := CardDatabase.get_card(e.card)
	EventBus.notify.emit("Received %s" % (card.display_name if card else String(e.card)))


func _progress(id: StringName) -> int:
	var e: Dictionary = ERRANDS[id]
	match e.need:
		"kills":
			return mini(_kills(e.monster), e.count)
		"cards":
			return _cards_held()
	return 0


func _kills(monster: StringName) -> int:
	return GameState.quest_flags.get(StringName("kills:%s" % monster), 0)


func _cards_held() -> int:
	var c := GameState.collection(GameState.PLAYER)
	if c == null:
		return 0
	var n := 0
	for id in c.card_ids():
		n += c.count(id)
	return n


func _on_monster_defeated(kind: StringName, killer: StringName) -> void:
	if killer != GameState.PLAYER:
		return
	var key := StringName("kills:%s" % kind)
	GameState.quest_flags[key] = GameState.quest_flags.get(key, 0) + 1
	for id: StringName in ERRANDS:
		if state(id) == ASKED and ERRANDS[id].need == "kills" and ERRANDS[id].monster == kind:
			EventBus.notify.emit(summary(id))


func _note_visit() -> void:
	var zone := get_tree().current_scene
	if zone and zone.scene_file_path != "":
		GameState.quest_flags[StringName("visited:%s" % zone.scene_file_path)] = true


func _npc_name(npc_id: StringName) -> String:
	const NAMES := {
		&"sailor": "Luca", &"pip": "Pip", &"baker": "Rosa", &"tomas": "Keeper Tomas", &"mirela": "Mirela",
		&"otto": "Otto", &"nonna": "Nonna Vess", &"brannoc": "Brannoc", &"ilse": "Ilse",
		&"harl": "Harl", &"wren": "Wren", &"juniper": "Juniper",
	}
	return NAMES.get(npc_id, String(npc_id).capitalize())
