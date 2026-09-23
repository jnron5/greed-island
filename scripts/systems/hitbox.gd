class_name Hitbox
extends Area2D
## Deals damage to any Hurtbox it overlaps. Detection happens on the Hurtbox
## side, so a Hitbox only needs to be monitorable on the right attack layer.

signal hit_landed(hurtbox: Hurtbox)

@export var damage := 1
@export var knockback := 120.0
## Collector id of whoever owns this attack (for combat steals and friendly fire).
var source_id: StringName
