class_name Travellers
extends RefCounted
## Travellers: folk on the road who walk about the towns and the wild (Npc with
## `roam_points`: every spawn marker and rival spot of the zone, all reachable on
## foot). By day the roster is dealt out afresh each day (TimeOfDay.day) to the zones
## in QUOTA, so the pedlar you met in Verdana yesterday is in Frisalle today; at dusk
## they all leave for Kalmora and spend the night in its streets (till the small
## hours), out of the wild before the beasts turn savage (Monster night strength).
## Eight PixelLab traveller sprites (assets/sprites/npcs/traveller_*) are shared by
## the twenty of them. What they say: their own couple of lines plus what anyone
## passing through says about the place they're in (CITY_LINES), or about the road
## (WILD_LINES) in the wild.

const NPC_SCENE := preload("res://scenes/characters/npc.tscn")
## The traveller sprites came out a little taller than the residents (hats, staffs):
## drawn at this scale, with each one's feet offset (from import_pixellab_character.py).
const SPRITE_SCALE := 0.8
const FEET := {
	"traveller_pedlar": -36.0, "traveller_pilgrim": -32.0, "traveller_courier": -34.0, "traveller_bard": -35.0,
	"traveller_tinker": -31.0, "traveller_botanist": -34.0, "traveller_sailor": -34.0, "traveller_drover": -32.0,
}
const KALMORA := "res://scenes/world/kalmora.tscn"
## Out by day in the town they're visiting, till they set off for Kalmora at dusk.
const DAY_HOURS := Vector2(7.0, 19.5)
const WILD_HOURS := Vector2(7.5, 18.5)
## In Kalmora: the ones visiting it today from morning, everyone from dusk, till late.
const KALMORA_DAY_HOURS := Vector2(7.0, 1.5)
const KALMORA_NIGHT_HOURS := Vector2(19.5, 1.5)

## How many travellers each zone has on any day (dealt in this order).
const QUOTA := {
	"res://scenes/world/kalmora.tscn": 4,
	"res://scenes/world/verdana.tscn": 3,
	"res://scenes/world/sorenda.tscn": 2,
	"res://scenes/world/seabright_quay.tscn": 2,
	"res://scenes/world/frisalle.tscn": 2,
	"res://scenes/world/aurewind_plains.tscn": 1,
	"res://scenes/world/thornveil.tscn": 1,
	"res://scenes/world/lake_serin.tscn": 1,
	"res://scenes/world/starfall_range.tscn": 1,
}
## Zone -> key into CITY_LINES (anything else is the wild).
const CITY := {
	"res://scenes/world/kalmora.tscn": "kalmora",
	"res://scenes/world/verdana.tscn": "verdana",
	"res://scenes/world/sorenda.tscn": "sorenda",
	"res://scenes/world/seabright_quay.tscn": "seabright",
	"res://scenes/world/frisalle.tscn": "frisalle",
}
## id, name, sprite (one of the eight traveller sprites), their own lines, and for one
## or two a little stock to sell.
const ROSTER := [
	{ "id": "hob", "name": "Pedlar Hob", "sprite": "traveller_pedlar", "shop": [&"bread", &"healers_tonic"], "lines": [
		"Bread, tonics, a bit of luck in a bottle. Well. Bread and tonics.",
		"I walk a circle round the island every month. My boots have seen more of Virelia than the King has.",
	] },
	{ "id": "ash", "name": "Pilgrim Ash", "sprite": "traveller_pilgrim", "lines": [
		"I'm walking to every standing stone on the island. Seven so far. They all hum the same note.",
		"A pilgrim travels light. Except for these stones. I keep picking up stones.",
	] },
	{ "id": "fen", "name": "Courier Fen", "sprite": "traveller_courier", "lines": [
		"Letters for Vetrassa, Verdana, Frisalle. Don't ask me what's in them. I don't read them. Much.",
		"Half my bag these days is letters to Duskara that never get an answer.",
	] },
	{ "id": "lute", "name": "Lute the Bard", "sprite": "traveller_bard", "lines": [
		"I'm writing a song about the race. I need a rhyme for 'forty-seven'. 'Heaven' is taken.",
		"Every town wants the song about itself. Nobody wants the song about the mine. I sing it anyway, quietly.",
	] },
	{ "id": "brisk", "name": "Tinker Brisk", "sprite": "traveller_tinker", "lines": [
		"Pots mended, locks oiled, gates squeaked. I mean de-squeaked.",
		"I fixed a lock in the Duke's own bungalow once. Strangest thing: it locked from the outside.",
	] },
	{ "id": "ivy", "name": "Ivy the Botanist", "sprite": "traveller_botanist", "lines": [
		"I'm pressing one of every flower on the island. The snow ones are the hardest. They melt on the page.",
		"Glowcaps, frostbells, harvest clover. The island grows everything except an honest answer.",
	] },
	{ "id": "corm", "name": "Corm, on Shore Leave", "sprite": "traveller_sailor", "lines": [
		"Three weeks ashore and I already miss the sea. Don't tell the sea.",
		"Our ship carries 'mineral ore' from the south cape. Ore doesn't cry in the hold at night.",
	] },
	{ "id": "dell", "name": "Fishwife Dell", "sprite": "traveller_drover", "lines": [
		"I walk the catch inland to the farms. They pay double for fish up there and complain triple.",
		"Smell? That's the smell of honest work. Mostly herring.",
	] },
	{ "id": "bess", "name": "Drover Bess", "sprite": "traveller_drover", "lines": [
		"Lost a ram somewhere between here and the plains. If you see a ram looking smug, that's him.",
		"Rams are the island's toughest racers. They've never once stopped for a gate.",
	] },
	{ "id": "garr", "name": "Woodsman Garr", "sprite": "traveller_tinker", "lines": [
		"Cut timber for the mine shafts for twenty years. Then I asked what the shafts were for. Then I stopped.",
		"An axe is the only honest tool. It does exactly what it says.",
	] },
	{ "id": "tad", "name": "Tad the Miller's Lad", "sprite": "traveller_courier", "lines": [
		"Off to see the world! Well, the island. Well, the next town.",
		"Mum says don't talk to racers. You don't seem so bad. Do you steal? You can say.",
	] },
	{ "id": "nell", "name": "Hen-wife Nell", "sprite": "traveller_botanist", "lines": [
		"Eggs! Eggs for sale! I mean, they would be, if the hens had laid any. They're on strike.",
		"My hens can smell a storm a day off. And a racer. They don't like either.",
	] },
	{ "id": "rye", "name": "Rye the Journeyman Baker", "sprite": "traveller_pedlar", "lines": [
		"Walking the island, learning every town's loaf. Kalmora's is the best. I'm from Kalmora.",
		"Frisalle bakes bread you could build a chalet with. I mean that kindly.",
	] },
	{ "id": "kestrel", "name": "Scout Kestrel", "sprite": "traveller_courier", "lines": [
		"I map the paths for the King's road crews. And the paths that aren't on any map. Those I don't map.",
		"If you're racing, take the high road. The low road has hounds and the middle road has the Raider.",
	] },
	{ "id": "dunn", "name": "Dunn the Stonemason", "sprite": "traveller_tinker", "lines": [
		"Built half the stairs on this island. You're welcome. Mind the third step in Kalmora, it's mine and it's crooked.",
		"Somebody's paying good gold for stone carvers to go south to the dunes. Nobody comes back to say how good.",
	] },
	{ "id": "wick", "name": "Wick the Chandler", "sprite": "traveller_pilgrim", "lines": [
		"Candles, wicks, lamp oil. Darkness is my business, and business is good.",
		"Seabright orders more lamp oil than any town on the island. For a place that sleeps all day, they burn a lot at night.",
	] },
	{ "id": "wynn", "name": "Goatherd Wynn", "sprite": "traveller_drover", "lines": [
		"My goats are up the mountain. I'm down here. We're both happier.",
		"A goat will climb anything. A goat will also eat your map. Don't bring a map near a goat.",
	] },
	{ "id": "sol", "name": "Sol the Lamplighter", "sprite": "traveller_bard", "lines": [
		"I light the road lamps between the towns. Every one, every dusk. My legs are very strong.",
		"The lamps keep the dark back. Not the things in it, mind. Just the dark.",
	] },
	{ "id": "rusk", "name": "Rusk the Ferryman", "sprite": "traveller_sailor", "lines": [
		"Ran the ferry across Lake Serin till the bridge-tax ate me. Now I walk, like everyone.",
		"Something big moves in the lake at night. Neri says it's a fish. Neri says everything's a fish.",
	] },
	{ "id": "mags", "name": "Mags the Card Sharp", "sprite": "traveller_bard", "lines": [
		"Fancy a game? No? Wise. I've never lost. Except to a quiet fellow by the fire on the plains. Never again.",
		"Cards are just paper till somebody wants them. Then they're worth a life. Funny island.",
	] },
]

## What anyone passing through says about a town.
const CITY_LINES := {
	"kalmora": [
		"Kalmora never sleeps, they say. The lanterns are up all night and so's everyone under them.",
		"Best bread on the island at Rosa's stall. Best gossip at the Salted Lantern. Worst cider, also the Salted Lantern.",
		"Watch the north road out of town after dark. The forest gets mean once the sun's gone.",
		"The harbormaster stamps everything that comes off the boats. Everything, she says. Not the crates on the night tide.",
		"First time in Kalmora? Climb up to the lighthouse lawn. You can see half the island from there.",
	],
	"verdana": [
		"Verdana: one street, one green, one stream and a thousand opinions about wheat.",
		"Dinner's at FIVE at the Sheaf & Sickle. Not five past. I learned that the hard way.",
		"Old Aldous up on the green knows the stones better than anyone. Bring him something to read.",
		"Don't cross the plains after dark if you can help it. The rams get bold and the stones get louder.",
		"The millstream runs north to the lake. Folk say it carried a boy away once. Folk say a lot.",
	],
	"sorenda": [
		"Sorenda's quiet. Too quiet. I like it, but I keep looking over my shoulder.",
		"Mate at the Copper Kettle says her stew beats Chef's. I've had both. Don't make me choose.",
		"The forest round here is fine by day. At night the hounds come out of the Hollow's side of the woods, bigger than you'd think.",
		"Have you seen the old tree house? Somebody built a whole house up in an oak and then never came down.",
	],
	"seabright": [
		"Seabright's paradise if you've the gold. I haven't. I'm just here for the view.",
		"The Saltglass Terrace does Chef's stew. Same recipe as Vetrassa, half the price, twice the gulls.",
		"Nobody asks who pays for all this. That's what makes it a resort.",
		"Bungalow 3's guests never come out by day. Lamps going all night, though.",
	],
	"frisalle": [
		"Frisalle! Cold enough to freeze your whiskers to your face. Best cocoa on the island, though.",
		"The pass was closed by a slide. Funny slide. Very tidy edges.",
		"Ottilie at the Hearth & Horn will feed you till you can't move. Don't argue with her.",
		"Don't go down the valley after dark. The wolves come up off the snowfield in packs.",
	],
}
## What they say on the road.
const WILD_LINES := [
	"Out here on the road between towns, you meet everybody sooner or later. Racers, pedlars, worse.",
	"I keep to the paths and I'm in a town by sundown. After dark the beasts out here get bigger and nastier. Hungrier too.",
	"They say the monsters that come out at night carry more on them. Coin, cards. Not worth your neck, if you ask me.",
	"Lovely day for walking. Lovely days are the dangerous ones: you forget the time and the sun goes.",
	"Mind the quiet stretches. Nothing makes a noise right before it jumps.",
]


## Puts today's travellers into `zone` (called by Zone on arrival, outdoors only).
static func populate(zone: Zone) -> void:
	var path := zone.scene_file_path
	if not QUOTA.has(path):
		return
	var points := _points(zone)
	if points.size() < 2:
		return
	var player := zone.get_tree().get_first_node_in_group(&"player") as Node2D
	var here := todays(path)
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(path) + TimeOfDay.day
	var visiting := here.map(func(t: Dictionary) -> String: return t.id)
	# Kalmora: everyone, for the night (today's visitors from the morning).
	var people: Array = ROSTER if path == KALMORA else here
	for t: Dictionary in people:
		var hours := DAY_HOURS if CITY.has(path) else WILD_HOURS
		if path == KALMORA:
			hours = KALMORA_DAY_HOURS if t.id in visiting else KALMORA_NIGHT_HOURS
		var npc := NPC_SCENE.instantiate() as Npc
		npc.name = "Traveller_" + String(t.id)
		npc.npc_id = StringName("traveller_" + String(t.id))
		npc.display_name = t.name
		npc.sprite_frames = load("res://assets/sprites/npcs/%s/%s_frames.tres" % [t.sprite, t.sprite])
		npc.sprite_offset_y = FEET.get(t.sprite, -26.0)
		var pool := PackedStringArray(t.lines)
		pool.append_array(CITY_LINES.get(CITY.get(path, ""), WILD_LINES))
		npc.lines = pool
		npc.roam_points = points
		npc.walk_speed = 26.0
		npc.out_from = hours.x
		npc.out_to = hours.y
		if t.has("shop"):
			var stock: Array[StringName] = []
			stock.assign(t.shop)
			npc.shop_stock = stock
			npc.shop_buys_cards = false
			npc.shop_title = t.name
		# Start at one of the points, not on top of the player.
		var start := points[rng.randi() % points.size()]
		for _i in 6:
			if player == null or start.distance_to(player.global_position) > 90.0:
				break
			start = points[rng.randi() % points.size()]
		npc.position = zone.to_local(start)
		zone.add_child(npc)
		npc.sprite.scale = Vector2(SPRITE_SCALE, SPRITE_SCALE)


## Today's travellers in the zone at `path`: the roster shuffled by the day and dealt
## out to the zones in QUOTA order.
static func todays(path: String) -> Array:
	var order := range(ROSTER.size())
	var rng := RandomNumberGenerator.new()
	rng.seed = 7919 + TimeOfDay.day * 104729
	for i in range(order.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp: int = order[i]
		order[i] = order[j]
		order[j] = tmp
	var used := {}
	for zone: String in QUOTA:
		var out := []
		for k: int in order:
			if out.size() >= QUOTA[zone]:
				break
			if used.has(k):
				continue
			used[k] = true
			out.append(ROSTER[k])
		if zone == path:
			return out
	return []


## Where travellers walk: every spawn marker and rival spot (all reachable on foot).
static func _points(zone: Zone) -> PackedVector2Array:
	var out := PackedVector2Array()
	for group in ["Spawns", "RivalSpots"]:
		var holder := zone.get_node_or_null(group)
		if holder == null:
			continue
		for marker in holder.get_children():
			out.append((marker as Node2D).global_position)
	return out
