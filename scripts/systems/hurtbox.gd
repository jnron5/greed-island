class_name Hurtbox
extends Area2D
## Receives hits from Hitboxes on the layers in its collision mask, filtered by
## Combat.can_damage (own team, towns). The owner sets `owner_id`.

signal hurt(hitbox: Hitbox)

var invulnerable := false
## Collector id, or Combat.MONSTER for monsters.
var owner_id: StringName


func _ready() -> void:
	area_entered.connect(_on_area_entered)


func _on_area_entered(area: Area2D) -> void:
	var hitbox := area as Hitbox
	if invulnerable or hitbox == null or not Combat.can_damage(hitbox.source_id, owner_id):
		return
	if not _same_level(hitbox):
		return  # Across a cliff: out of reach.
	hurt.emit(hitbox)
	hitbox.hit_landed.emit(self)


func _same_level(hitbox: Hitbox) -> bool:
	var zone := Zone.current(get_tree())
	if zone == null:
		return true
	var mine := zone.level_at((get_parent() as Node2D).global_position)
	var theirs := hitbox.attack_level()
	return mine == -1 or theirs == -1 or mine == theirs
