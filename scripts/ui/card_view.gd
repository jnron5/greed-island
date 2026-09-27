class_name CardView
extends Control
## One card drawn at its native pixel size (112x160): the shared frame, the card's
## illustration (CardData.icon) cropped to the frame's window, and its name in the
## banner. Scale the control to show it bigger; it stays pixel-crisp.

const SIZE := Vector2(112, 160)
## Frame art and where its picture window and name banner sit (frame pixels).
const FRAMES := {
	&"a": { "texture": "res://assets/cards/frames/frame_a.png", "window": Rect2i(21, 26, 66, 67), "name_y": 110 },
	&"b": { "texture": "res://assets/cards/frames/frame_b.png", "window": Rect2i(25, 26, 66, 67), "name_y": 112 },
	&"c": { "texture": "res://assets/cards/frames/frame_c.png", "window": Rect2i(20, 29, 68, 66), "name_y": 117 },
	&"d": { "texture": "res://assets/cards/frames/frame_d.png", "window": Rect2i(25, 31, 66, 63), "name_y": 117 },
}
## The frame every card uses (the design Jordan picks).
const FRAME := &"a"
const NAME_COLOR := Color(0.28, 0.16, 0.08)

var card: CardData:
	set(value):
		card = value
		if is_node_ready():
			_refresh()

var _art: TextureRect
var _frame: TextureRect
var _name: Label


func _ready() -> void:
	custom_minimum_size = SIZE
	size = SIZE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var spec: Dictionary = FRAMES[FRAME]
	var window: Rect2i = spec.window
	var clip := Control.new()
	clip.clip_contents = true
	clip.position = window.position
	clip.size = window.size
	add_child(clip)
	_art = TextureRect.new()
	_art.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	_art.size = window.size
	clip.add_child(_art)
	_frame = TextureRect.new()
	_frame.texture = load(spec.texture)
	add_child(_frame)
	_name = Label.new()
	_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_name.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_name.add_theme_color_override(&"font_color", NAME_COLOR)
	_name.add_theme_font_size_override(&"font_size", 9)
	_name.position = Vector2(12, spec.name_y - 8)
	_name.size = Vector2(SIZE.x - 24, 16)
	add_child(_name)
	_refresh()


## The card's outline as a solid shape (the frame with its window filled in), for
## effects that should stay on the card, like the reveal's shine.
static func silhouette() -> Texture2D:
	var spec: Dictionary = FRAMES[FRAME]
	var image: Image = (load(spec.texture) as Texture2D).get_image()
	image.convert(Image.FORMAT_RGBA8)
	image.fill_rect(spec.window, Color.WHITE)
	return ImageTexture.create_from_image(image)


func _refresh() -> void:
	if card == null:
		return
	_art.texture = card.icon
	_name.text = card.display_name
