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
	hurt.emit(hitbox)
	hitbox.hit_landed.emit(self)
