class_name TiledAnimation
extends Sprite2D
## Repeats an animated tile over `region_rect`: every frame of `strip` (a horizontal
## strip of equal square frames) is cut out once, and the sprite swaps between them at
## `fps`. Used for the animated sea, clipped to the water by its parent.

@export var strip: Texture2D
@export var frame_count := 8
@export var fps := 6.0

var _frames: Array[Texture2D] = []
var _time := 0.0


func _ready() -> void:
	texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	region_enabled = true
	var image := strip.get_image()
	var w := image.get_width() / frame_count
	for k in frame_count:
		_frames.append(ImageTexture.create_from_image(image.get_region(Rect2i(k * w, 0, w, image.get_height()))))
	texture = _frames[0]


func _process(delta: float) -> void:
	_time += delta
	texture = _frames[int(_time * fps) % frame_count]
