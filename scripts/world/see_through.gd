class_name SeeThrough
extends Node
## Fades a building or big tree while the player walks behind it, so you can always
## see where you're going. Behind: the player is inside the drawn sprite (a little in
## from its sides) and north of its base, the origin of the body the sprite belongs
## to; the whole body fades (its lit windows too). Add one as a child of the Sprite2D
## or AnimatedSprite2D.

@export var faded := 0.42
## How much of the sprite's width, either side, doesn't count (leaves, eaves).
@export var inset := 0.15

static var _player: Node2D

var _sprite: Node2D


func _ready() -> void:
	_sprite = get_parent() as Node2D


func _process(delta: float) -> void:
	if not is_instance_valid(_player):
		_player = get_tree().get_first_node_in_group(&"player") as Node2D
		if _player == null:
			return
	var feet := _player.global_position
	var want := 1.0
	if absf(feet.x - _sprite.global_position.x) < 260.0 and absf(feet.y - _sprite.global_position.y) < 360.0:
		want = faded if _behind(feet) else 1.0
	var body := _sprite.get_parent() as CanvasItem
	if body and not is_equal_approx(body.modulate.a, want):
		body.modulate.a = move_toward(body.modulate.a, want, delta * 3.0)


func _behind(feet: Vector2) -> bool:
	var base := _sprite.get_parent() as Node2D
	if base == null or feet.y >= base.global_position.y:
		return false
	var rect := _local_rect()
	if not rect.has_area():
		return false
	rect = rect.grow_individual(-rect.size.x * inset, 0, -rect.size.x * inset, 0)
	var body := _sprite.get_global_transform().affine_inverse() * (feet + Vector2(0, -10))
	return rect.has_point(body)


func _local_rect() -> Rect2:
	if _sprite is Sprite2D:
		return (_sprite as Sprite2D).get_rect()
	var animated := _sprite as AnimatedSprite2D
	if animated and animated.sprite_frames:
		var tex := animated.sprite_frames.get_frame_texture(animated.animation, animated.frame)
		if tex:
			var size := tex.get_size()
			return Rect2(-size / 2.0 + animated.offset if animated.centered else animated.offset, size)
	return Rect2()
