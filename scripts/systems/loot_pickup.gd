class_name LootPickup
extends Area2D
## Gold or a satchel item lying where a monster fell. It flies out of the body,
## lands, and the player picks it up by walking over it (rivals race for cards,
## not coins). It doesn't outlive the visit: leave the zone and it's gone.

## Gold in this pile (0 = none).
@export var gold := 0
## A satchel item (Items catalogue id), or empty.
@export var item_id: StringName

var fling_from := Vector2.INF

var _time := randf() * TAU
var _landed := true
var _hop := 0.0
var _icon: Texture2D


func _init() -> void:
	collision_layer = 0
	collision_mask = 2   # the player's body
	monitorable = false
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 8.0
	shape.shape = circle
	add_child(shape)


func _ready() -> void:
	body_entered.connect(_on_body_entered)
	if item_id != &"":
		var item := Items.get_item(item_id)
		_icon = item.icon if item else null
	if fling_from != Vector2.INF:
		_landed = false
		monitoring = false
		var land := position
		position = fling_from
		var tween := create_tween().set_parallel()
		tween.tween_property(self, "position", land, 0.5).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tween.tween_method(func(t: float) -> void: _hop = sin(t * PI) * 14.0, 0.0, 1.0, 0.5)
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
	if not _landed or not body.is_in_group(&"player") or (body.has_method(&"can_pick_up") and not body.can_pick_up()):
		return
	if gold > 0:
		GameState.add_currency(gold)
		Sfx.play(&"coins")
		EventBus.notify.emit("+ %d gold" % gold)
	if item_id != &"":
		GameState.add_item(item_id)
		var item := Items.get_item(item_id)
		EventBus.notify.emit("+ %s" % (item.display_name if item else String(item_id)))
	queue_free()


func _draw() -> void:
	var y := roundf(sin(_time * 3.0) * 1.0) - 3.0 - _hop
	draw_rect(Rect2(-5, 4, 10, 2), Color(0, 0, 0, 0.22))
	if _icon:
		var s := _icon.get_size() * 0.5
		draw_texture_rect(_icon, Rect2(Vector2(-s.x / 2.0, y - s.y + 4), s), false)
		return
	# A little pile of coins.
	for i in mini(4, maxi(1, gold / 2)):
		var o := Vector2([-3, 2, -1, 3][i], [0, 1, -2, -1][i])
		draw_circle(Vector2(o.x, y + o.y), 2.5, Color(0.45, 0.3, 0.05))
		draw_circle(Vector2(o.x, y + o.y - 0.5), 2.0, Color(1.0, 0.82, 0.3))
