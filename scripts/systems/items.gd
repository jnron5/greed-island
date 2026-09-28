class_name Items
## The catalogue of satchel items (data/items/*.tres, ItemData), looked up by id.

const DIR := "res://data/items/"

static var _cache: Dictionary = {}


static func get_item(id: StringName) -> ItemData:
	if not _cache.has(id):
		var path := DIR + String(id) + ".tres"
		_cache[id] = load(path) as ItemData if ResourceLoader.exists(path) else null
	return _cache[id]


static func is_item(id: StringName) -> bool:
	return get_item(id) != null


## Every item, cheapest first.
static func all_items() -> Array[ItemData]:
	var out: Array[ItemData] = []
	for file in ResourceLoader.list_directory(DIR):
		if file.ends_with(".tres"):
			var item := get_item(StringName(file.trim_suffix(".tres")))
			if item:
				out.append(item)
	out.sort_custom(func(a: ItemData, b: ItemData) -> bool: return a.price < b.price)
	return out


## Eats or drinks the healing item best suited to the player's wounds. Returns what
## was used, or null (nothing carried, or already at full health).
static func quick_heal() -> ItemData:
	var player := (Engine.get_main_loop() as SceneTree).get_first_node_in_group(&"player") as Player
	if player == null or player.health >= player.max_health:
		return null
	var item := best_heal(player.max_health - player.health)
	if item and GameState.use_item(item.id):
		EventBus.notify.emit("Used %s." % item.display_name)
		return item
	return null


## The healing item best suited to `missing` hearts: the smallest that covers it,
## else the strongest carried. Null when the satchel has nothing that heals.
static func best_heal(missing: int) -> ItemData:
	var carried: Array[ItemData] = []
	for item in all_items():
		if item.heal > 0 and GameState.item_count(item.id) > 0:
			carried.append(item)
	if carried.is_empty():
		return null
	carried.sort_custom(func(a: ItemData, b: ItemData) -> bool: return a.heal < b.heal)
	for item in carried:
		if item.heal >= missing:
			return item
	return carried[-1]
