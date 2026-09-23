@tool
class_name CardData
extends Resource
## One card definition. Each card lives as a .tres in res://data/cards/.

enum Rarity { COMMON, RARE, BOSS }
enum Category { SET, BUFF_TEMP, BUFF_PASSIVE, SPELL }
## Where copies come from. The soft-lock validator picks its formula from this.
enum Source { LOOSE, MONSTER, BOSS, SHOP, QUEST }

@export var id: StringName
@export var display_name: String
@export_multiline var description: String
@export var rarity: Rarity = Rarity.COMMON
@export var category: Category = Category.SET
@export var source: Source = Source.LOOSE
## Counts toward the complete set needed to win at Vetrassa.
@export var is_final_set_member := false
## Can be spent to open gates.
@export var gate_card := false
## How many copies one collector needs in the final set.
@export var final_set_count := 1
@export var sell_value := 0
@export var icon: Texture2D

@export_group("Supply")
## Hand-placed loose copies in the world.
@export var copies_in_world := 0
## Commons that also drop from respawning monsters are effectively infinite.
@export var respawning_monster_drop := false
@export var boss_starting_drops := 0
@export var boss_drops_per_kill := 0
## Boss kills allowed per playthrough (design target: 3-4).
@export var boss_kill_cap := 0
## Copies the design expects to leave supply through selling. Sold cards are
## permanently removed from the world, so the validator counts this as demand.
@export var sale_allowance := 0
## Other places a lost copy can be recovered (e.g. "rebuy_merchant", quest ids).
@export var replacement_sources: PackedStringArray


func max_possible_copies() -> int:
	if source == Source.BOSS:
		return boss_starting_drops + boss_drops_per_kill * boss_kill_cap
	return copies_in_world


func is_effectively_infinite() -> bool:
	return respawning_monster_drop
