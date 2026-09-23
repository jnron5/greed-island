class_name Hurtbox
extends Area2D
## Receives hits from Hitboxes on the layers in its collision mask.

signal hurt(hitbox: Hitbox)

var invulnerable := false


func _ready() -> void:
	area_entered.connect(_on_area_entered)


func _on_area_entered(area: Area2D) -> void:
	var hitbox := area as Hitbox
	if invulnerable or hitbox == null:
		return
	hurt.emit(hitbox)
	hitbox.hit_landed.emit(self)
