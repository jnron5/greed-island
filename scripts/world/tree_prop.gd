@tool
extends StaticBody2D
## Thornveil tree (PixelLab sprites): trunk collision at the origin, canopy drawn
## upward. Picks leafy or fir from its position so forests mix both but look the
## same on every load.

const TEXTURES: Array[Texture2D] = [
	preload("res://assets/sprites/tiles/thornveil/tree_leafy.png"),
	preload("res://assets/sprites/tiles/thornveil/tree_fir.png"),
]
## Pixel row of each texture's trunk base (so it sits on the node origin).
const BASES: Array[int] = [77, 83]

## -1 = choose from position; 0 = leafy; 1 = fir.
@export_range(-1, 1) var variant := -1:
	set(value):
		variant = value
		queue_redraw()
## Kept for scenes that set them; the sprite art has its own size and colours.
@export var radius := 18.0
@export var tint := Color(0.2, 0.42, 0.22)


func _draw() -> void:
	var v := variant if variant >= 0 else absi(int(position.x) * 7 + int(position.y) * 13) % TEXTURES.size()
	var tex := TEXTURES[v]
	draw_set_transform(Vector2(0, 2), 0.0, Vector2(1.0, 0.35))
	draw_circle(Vector2.ZERO, 12.0, Color(0, 0, 0, 0.22))
	draw_set_transform(Vector2.ZERO)
	draw_texture(tex, Vector2(-tex.get_width() / 2.0, -BASES[v]))
