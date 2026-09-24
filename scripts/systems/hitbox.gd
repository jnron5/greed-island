class_name Hitbox
extends Area2D
## Deals damage to any Hurtbox it overlaps. Detection happens on the Hurtbox
## side, so a Hitbox only needs to be monitorable on the right attack layer.

signal hit_landed(hurtbox: Hurtbox)

@export var damage := 1
@export var knockback := 120.0
## Collector id of whoever owns this attack (for combat steals and friendly fire).
var source_id: StringName
## Level the attack was made on; -1 = work it out from the attacker's position.
var level := -1


## The attack only lands on targets standing on the same level.
func attack_level() -> int:
	if level != -1:
		return level
	var node: Node = self
	while node and not (node is CharacterBody2D):
		node = node.get_parent()
	var zone := Zone.current(get_tree())
	return zone.level_at((node as Node2D).global_position) if zone and node else -1
