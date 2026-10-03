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
	# ---- Thornveil ----
	&"tobin_sigil": {
		"npc": &"tobin", "zone": "res://scenes/world/thornveil.tscn", "card": &"fern_sigil", "need": "gold",
		"gold": 40,
		"ask": [
			"A racer! Sit, sit, the kettle's on. I trade in whatever the forest gives up.",
			"Hunters leave these fern sigils at their camps. I've a spare. Forty gold, and it's yours: a card's a card.",
		],
		"waiting": "Forty gold for the sigil. I'll keep the kettle on.",
		"give": ["A pleasure. Mind the boars on the way down; they don't like strangers."],
		"after": "Every racer who's ever passed has stopped for tea. Most of them.",
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
	# ---- Past Kalmora's west gate ----
	&"tilly_rams": {
		"npc": &"tilly", "zone": "res://scenes/world/aurewind_plains.tscn", "card": &"shepherds_bell", "need": "kills",
		"monster": &"bristle_ram", "count": 3, "hunt": "res://scenes/world/aurewind_plains.tscn",
		"ask": [
			"The bristle rams are wild ones. They charge my flock and scatter it halfway to the downs.",
			"They lower their horns before they come at you, and they can't turn once they're running. Step aside and they'll go right past.",
			"Drive off three and you can have Bramble's old bell. She was my first ewe. The bell's a card now, Grandad says. Everything with a story is.",
		],
		"waiting": "%d of 3 rams. They graze all over the plains.",
		"give": ["The flock's settling already. Here's Bramble's bell. Ring it on the downs and every sheep for a mile looks up."],
		"after": "Count them for me? One, two... never mind, they keep moving.",
	},
	&"marta_bread": {
		"npc": &"marta", "zone": "res://scenes/world/verdana.tscn", "card": &"golden_sheaf", "need": "item",
		"item": &"smoked_fish", "count": 1,
		"ask": [
			"Our own bread's all sold to the Company before it's out of the oven. Imagine that. A baker's town with no bread.",
			"I'd kill for something that isn't flour. Bring me a smoked fish from the coast? I'll trade you the first sheaf of the harvest. The Company hasn't counted that one yet.",
		],
		"waiting": "A smoked fish. Greta in Kalmora has them, or Bruno at the inn when he's feeling generous.",
		"give": ["Oh, that smells like the harbor. Here: the first sheaf, red ribbon and all. Hang it somewhere it'll bring you luck."],
		"after": "Harvest waits for nobody. Mind the rams on your way.",
	},
	&"oda_news": {
		"npc": &"oda", "zone": "res://scenes/world/verdana.tscn", "card": &"harvest_oak_leaf", "need": "visit",
		"place": "res://scenes/world/lake_serin.tscn", "place_name": "Lake Serin",
		"ask": [
			"You're going places. Would you go to Lake Serin for me? My grandson went that way with the Company carts.",
			"Just look. Ask the fisher there if he saw a young sheepdog with a red scarf. I knitted it. Then come back and tell me, whatever it is.",
			"I'll give you the leaf the Harvest Oak dropped the day he was born. I kept it for him. It's a card now. Everything is, these days.",
		],
		"waiting": "Lake Serin, north of the plains. Ask after a red scarf.",
		"give": [
			"...The barges. North. At night. I see.",
			"Take the leaf. Somebody should carry it somewhere.",
		],
		"after": "Every thread is somebody.",
	},
	&"neri_tonic": {
		"npc": &"neri", "zone": "res://scenes/world/lake_serin.tscn", "card": &"heron_plume", "need": "item",
		"item": &"healers_tonic", "count": 1,
		"ask": [
			"Bad leg. Cold water, forty years. Don't get old by a lake.",
			"If you've a Healer's Tonic spare, I'll trade you a heron plume for it. Wore it in my hat forty years. Didn't make me any more patient.",
		],
		"waiting": "A Healer's Tonic, if you've one. The leg's not getting younger.",
		"give": ["Ahh. Better already, or I'm imagining it. Here's the plume. Mind, the herons will want it back."],
		"after": "Still water, still fish, still me.",
	},
	# Sully, Loki and Xena's estranged son (adopted by Jobelle, Mate and Tilly), keeps
	# the escape line's way-station in the Frost Grotto, against his own mother's mine.
	&"sully_trout": {
		"npc": &"sully", "zone": "res://scenes/world/starfall_grotto.tscn", "card": &"moss_lantern", "need": "item",
		"item": &"lake_trout", "count": 2,
		"ask": [
			"Easy. I'm not Company, and I can see you're not either. Company don't come in here since the wolves.",
			"People come through this cave. Not crates, people. Tired ones, from a long way south. They need feeding before the ice.",
			"Two trout from Serin. Neri lets anyone fish off his dock. Bring them and you can have one of my lanterns. They've shown a lot of folk the way.",
		],
		"waiting": "Two lake trout. Off Neri's dock on Serin. Quietly, if you can.",
		"give": [
			"That's two more who'll make it to the ice wall with something in them. Thank you.",
			"Take the lantern. Moss glows when nothing else will. If you ever see a light like it down south, under the dunes, follow it.",
		],
		"after": "If you meet a woman who looks like me, all in black, carrying a ledger: that's my mother. Don't tell her you saw me.",
	},
	# ---- Seabright Quay: the royal cousins on holiday ----
	&"sparkle_dare": {
		"npc": &"sparkle", "zone": "res://scenes/world/seabright_quay.tscn", "card": &"sunken_crown_shard", "need": "visit",
		"place": "res://scenes/world/starfall_grotto.tscn", "place_name": "the Frost Grotto",
		"ask": [
			"You look like you've been somewhere dangerous. I'm jealous. Everyone here keeps saying 'not on holiday, dear'.",
			"There's an ice cave up in the Starfall Range, the Frost Grotto. Wolves, crystals, a wall of ice you can see daylight through. I'm not allowed. You are.",
			"Go in, all the way, and come back and tell me everything. I'll give you the best thing I've ever found diving off this pier.",
		],
		"waiting": "The Frost Grotto, up in the Starfall Range, past the cave mouth in the east shoulder. All the way in!",
		"give": [
			"A wall of ice with the sun behind it? And crates? And WOLVES? That's the best thing I've ever heard. I'm going next year. Don't tell Sassy.",
			"Here. I found it on the seabed right under the pier. It's a bit of a crown. Not one of ours. Nobody can tell me whose.",
		],
		"after": "Next summer: the Grotto. This summer: the cliff on the headland. Watch me!",
	},
	&"sassy_gift": {
		"npc": &"sassy", "zone": "res://scenes/world/seabright_quay.tscn", "card": &"sea_glass", "need": "talk",
		"give": [
			"Oh! Are you one of those card people? How fun. Here, I think this is a card. It was in my sun hat. Or my drink.",
			"It's sea glass. From Kalmora, I think. I collect pretty things and then I forget I have them. You have it. It's prettier on you.",
		],
		"after": "Did I give you something? I feel like I gave you something. Lovely.",
	},
	# ---- Frisalle ----
	&"ottilie_stew": {
		"npc": &"ottilie", "zone": "res://scenes/world/frisalle.tscn", "card": &"frisalle_hearthstone", "need": "item",
		"item": &"seabright_stew", "count": 1,
		"ask": [
			"Forty years I've cooked in this kitchen, and I've never once eaten anybody else's cooking. Isn't that a sad thing to say out loud?",
			"They say a cook down at Seabright Quay makes Chef's own stew, the one Vetrassa queues round the square for. Bring me a bowl, love. Just one. I want to know what all the fuss is.",
			"I'll give you the hearthstone out of this fire. It's been warming in there since before the inn had a name.",
		],
		"waiting": "A Seabright Stew, from the terrace out on the water at Seabright Quay, south of Verdana. Keep it under your cloak; it's a long cold road.",
		"give": [
			"...Oh. Oh, that's saffron. Somebody's put saffron in a fish stew and made it sing. Don't you dare tell my regulars.",
			"Here. The hearthstone. Put it in your bed at night and think of an old dog who learned something new.",
		],
		"after": "I've been trying the saffron. Sven says it tastes of money. Sven can make his own supper.",
	},
	&"hald_wolves": {
		"npc": &"hald", "zone": "res://scenes/world/starfall_range.tscn", "card": &"starfall_edelweiss", "need": "kills",
		"monster": &"frost_wolf", "count": 3, "hunt": "res://scenes/world/starfall_range.tscn",
		"ask": [
			"The wolves have been circling the cabin since the slide. Hungry. Something drove them down off the pass.",
			"They come in low and fast, and they don't give up. Keep your back to a rock and your pistol ready.",
			"Thin the pack by three and I'll give you an edelweiss. Picked it the spring my boy went over the pass. I've kept it long enough.",
		],
		"waiting": "%d of 3 wolves. They hunt the shelf below the pass.",
		"give": ["Quiet out there at last. Take the flower. Carry it somewhere warmer than here."],
		"after": "Snow's coming. Snow's always coming.",
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
			# Favours that cost you something (an item, gold) always ask first; the
			# handing over happens next time you talk, never by surprise.
			if e.need == "talk" or (is_met(id) and not _costly(id)):
				return PackedStringArray(e.give)
			return PackedStringArray(e.ask)


## After a chat: first time marks the errand asked; once it's met, pays it out.
func talked_to(npc_id: StringName) -> void:
	var id := errand_for(npc_id)
	if id == &"" or state(id) == DONE:
		return
	if state(id) != ASKED and _costly(id):
		GameState.quest_flags[StringName("errand:%s" % id)] = ASKED
		EventBus.notify.emit("Favour: %s" % summary(id))
	elif is_met(id):
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


## Favours paid for with your own things (satchel items, gold).
func _costly(id: StringName) -> bool:
	return ERRANDS[id].need in ["item", "gold"]


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
		&"harl": "Harl", &"wren": "Wren", &"juniper": "Juniper", &"tobin": "Tobin",
		&"tilly": "Tilly", &"sully": "Sully", &"sparkle": "Sparkle", &"sassy": "Sassy", &"ottilie": "Ottilie", &"mirren": "Mirren", &"marta": "Marta", &"neri": "Neri", &"hald": "Hald", &"oda": "Oda",
	}
	return NAMES.get(npc_id, String(npc_id).capitalize())
