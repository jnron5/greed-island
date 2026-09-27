extends StaticBody2D
## A forest tree (scenes/world/props/forest_*.tscn): a PixelLab-animated sway strip
## on an AnimatedSprite2D, collision at the trunk. Each tree starts on a different
## frame and sways at a slightly different speed (from its position, so it's the
## same on every load), so a grove moves like a grove, not in lockstep.

func _ready() -> void:
	var sprite := $AnimatedSprite2D as AnimatedSprite2D
	var h := absi(int(position.x) * 73856093 ^ int(position.y) * 19349663)
	sprite.frame = h % maxi(sprite.sprite_frames.get_frame_count(sprite.animation), 1)
	sprite.speed_scale = 0.8 + float(h % 7) / 15.0
	sprite.flip_h = h % 3 == 0
	sprite.play()
