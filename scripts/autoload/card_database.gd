extends Node
## Loads every CardData and GateData resource and looks them up by id.

const CARD_DIR := "res://data/cards/"
const GATE_DIR := "res://data/gates/"

var _cards: Dictionary[StringName, CardData] = {}
var _gates: Dictionary[StringName, GateData] = {}


func _ready() -> void:
	for res in load_all(CARD_DIR):
		if res is CardData:
			_cards[res.id] = res
	for res in load_all(GATE_DIR):
		if res is GateData:
			_gates[res.id] = res


static func load_all(dir: String) -> Array[Resource]:
	var out: Array[Resource] = []
	# list_directory resolves .remap files in exported builds.
	for file in ResourceLoader.list_directory(dir):
		if file.ends_with(".tres"):
			var res := load(dir + file)
			if res:
				out.append(res)
	return out


func get_card(id: StringName) -> CardData:
	return _cards.get(id)


func get_gate(id: StringName) -> GateData:
	return _gates.get(id)


func all_cards() -> Array[CardData]:
	var out: Array[CardData] = []
	out.assign(_cards.values())
	return out


func all_gates() -> Array[GateData]:
	var out: Array[GateData] = []
	out.assign(_gates.values())
	return out


func final_set() -> Array[CardData]:
	var out: Array[CardData] = []
	out.assign(_cards.values().filter(func(c: CardData) -> bool: return c.is_final_set_member))
	return out
