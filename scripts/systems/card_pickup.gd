class_name CardPickup
extends Area2D
## A card lying on the ground in a small satchel: spilled by a collector who was
## beaten or fainted, or dropped by a monster or boss as it died. Any collector body
## (player or rival) with a `collector_id` property picks it up on touch; it arrives
## in the Loose state. Kills never put cards straight into anyone's hands: the
## winner has to walk over and take it, and anyone quicker can beat them to it.
## Hand-placed pickups are remembered once taken so they don't return when the
## zone reloads; dropped cards are tracked per zone in GameState.zone_drops.

@export var card_id: StringName
## The gate you must open to reach this card, if any. Rivals skip it unless
## they can pay for that gate (and then they do).
@export var behind_gate: StringName

## Set for cards dropped at runtime that should persist in their zone.
var zone_drop_of: String
## The collector who lost this card (a death drop), or empty (a monster's drop).
var dropped_by: StringName
## Where it flies out from when spawned (a body falling); INF = it's just there.
var fling_from := Vector2.INF

var _time := randf() * TAU
var _landed := true
var _hop := 0.0


func _ready() -> void:
	if _is_hand_placed() and GameState.collected_pickups.has(_persist_key()):
		queue_free()
		return
	add_to_group(&"card_pickups")
	body_entered.connect(_on_body_entered)
	if fling_from != Vector2.INF:
		_fling()


## Pops out of the body in a little arc and lands; it can't be taken mid-air.
func _fling() -> void:
	_landed = false
	monitoring = false
	var land := position
	position = fling_from
	var tween := create_tween().set_parallel()
	tween.tween_property(self, "position", land, 0.55).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tween.tween_method(func(t: float) -> void: _hop = sin(t * PI) * 18.0, 0.0, 1.0, 0.55)
	tween.chain().tween_callback(func() -> void:
		_hop = 0.0
		_landed = true
		monitoring = true
		for body in get_overlapping_bodies():
			_on_body_entered(body))


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


func _on_body_entered(body: Node2D) -> void:
	if not _landed:
		return
	var collector: Variant = body.get(&"collector_id")
	if not (collector is StringName) or (body.has_method(&"can_pick_up") and not body.can_pick_up()):
		return
	if not GameState.add_loose_card(collector, card_id):
		return
	_announce(collector, body)
	if _is_hand_placed():
		GameState.collected_pickups[_persist_key()] = true
	elif zone_drop_of != "":
		GameState.remove_zone_drop(zone_drop_of, card_id, position)
	EventBus.card_picked_up.emit(collector, card_id, dropped_by)
	queue_free()


## Tells the player who took what: their own lost card back, a rival's card, or a
## rival grabbing the card the player dropped.
func _announce(collector: StringName, body: Node2D) -> void:
	var card := CardDatabase.get_card(card_id)
	var name := card.display_name if card else String(card_id)
	if collector == GameState.PLAYER:
		if dropped_by == GameState.PLAYER:
			EventBus.notify.emit("You got your %s back." % name)
		elif dropped_by != &"":
			EventBus.notify.emit("You took the %s's %s." % [_who(dropped_by), name])
		else:
			EventBus.notify.emit("+ %s" % name)
	elif dropped_by == GameState.PLAYER:
		EventBus.notify.emit("The %s picked up your %s!" % [_who(collector), name])
		if body.has_method(&"say"):
			body.say(&"stole")


static func _who(id: StringName) -> String:
	var profile := GameState.rival_profile(id)
	return profile.display_name if profile else String(id)


## Placed in the editor (owned by a saved scene) rather than spawned by code.
func _is_hand_placed() -> bool:
	return owner != null and owner.scene_file_path != ""


func _persist_key() -> String:
	return persist_key(owner.scene_file_path, String(owner.get_path_to(self)))


## Shared with WorldMap, which reads pickups straight from scene files.
static func persist_key(scene_path: String, node_path: String) -> String:
	return "%s:%s" % [scene_path, node_path]


func _draw() -> void:
	# A dropped satchel (cards are never left lying loose): a small leather pouch with
	# a card's corner showing, bobbing gently so it catches the eye. A collector's lost
	# card glows in the colour of a warning, so you can see it from across the field.
	var card := CardDatabase.get_card(card_id)
	var rare := card != null and card.rarity != CardData.Rarity.COMMON
	var y := roundf(sin(_time * 3.0) * 1.5) - 4.0 - _hop
	draw_rect(Rect2(-6, 5, 12, 2), Color(0, 0, 0, 0.25))                          # shadow
	if dropped_by != &"" and _landed:
		draw_circle(Vector2(0, y + 3), 9.0 + sin(_time * 4.0), Color(1.0, 0.85, 0.4, 0.18))
	draw_rect(Rect2(-5, y - 1, 10, 8), Color(0.18, 0.1, 0.05))                     # outline
	draw_rect(Rect2(-4, y, 8, 6), Color(0.55, 0.34, 0.17))                         # leather
	draw_rect(Rect2(-4, y, 8, 2), Color(0.66, 0.43, 0.22))                         # flap
	draw_rect(Rect2(-1, y + 1, 2, 2), Color(0.85, 0.7, 0.3))                       # clasp
	draw_rect(Rect2(1, y - 4, 4, 4), Color(0.1, 0.08, 0.06))                       # the card peeking out
	draw_rect(Rect2(2, y - 3, 2, 3), Color(0.95, 0.8, 0.35) if rare else Color(0.92, 0.9, 0.84))
