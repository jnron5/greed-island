class_name CardView
extends Control
## One card at its native pixel size (112x180), front or back.
## Front: the card's illustration (CardData.icon, 66x47) in the picture window, its
## name on the banner and its description in the panel below. Back: its name and
## lore (CardData.lore; keep it to about 190 characters so it fits). The frames are
## built by scripts/tools/build_card_frame.py.
## Scale the control to show it bigger.

const SIZE := Vector2(112, 180)
const FRONT := preload("res://assets/cards/frames/card_front.png")
const BACK := preload("res://assets/cards/frames/card_back.png")
const WINDOW := Rect2(21, 26, 66, 47)
const NAME_Y := 90
## Room for the name inside the banner's scroll ends.
const NAME_WIDTH := 64.0
const TEXT := Rect2(22, 108, 64, 28)
const LORE := Rect2(22, 28, 64, 107)
const INK := Color(0.28, 0.16, 0.08)
const INK_SOFT := Color(0.36, 0.23, 0.13)

var card: CardData:
	set(value):
		card = value
		if is_node_ready():
			_refresh()
## Which side faces the viewer.
var showing_back := false:
	set(value):
		showing_back = value
		if is_node_ready():
			_refresh()

var _front: Control
var _back: Control
var _art: TextureRect
var _name: Label
var _text: Label
var _back_name: Label
var _lore: Label


var _placeholder: Label

func _ready() -> void:
	custom_minimum_size = SIZE
	size = SIZE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_front = _side()
	var clip := Control.new()
	clip.clip_contents = true
	clip.position = WINDOW.position
	clip.size = WINDOW.size
	_front.add_child(clip)
	# Behind the art: a deep sea-teal ground, and for cards whose art isn't painted
	# yet, the card's initial in gold, so the window never shows the world through it.
	var ground := ColorRect.new()
	ground.color = Color(0.09, 0.2, 0.24)
	ground.size = WINDOW.size
	clip.add_child(ground)
	var glow := ColorRect.new()
	glow.color = Color(0.2, 0.36, 0.38)
	glow.position = Vector2(3, 3)
	glow.size = WINDOW.size - Vector2(6, 6)
	clip.add_child(glow)
	_placeholder = _text_label(clip, Rect2(Vector2.ZERO, WINDOW.size), 24, Color(1.0, 0.82, 0.4), HORIZONTAL_ALIGNMENT_CENTER)
	_placeholder.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_art = TextureRect.new()
	_art.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	_art.size = WINDOW.size
	clip.add_child(_art)
	_front.add_child(_image(FRONT))
	_name = _text_label(_front, Rect2(12, NAME_Y - 8, SIZE.x - 24, 16), 9, INK, HORIZONTAL_ALIGNMENT_CENTER)
	_text = _text_label(_front, TEXT, 6, INK_SOFT, HORIZONTAL_ALIGNMENT_CENTER)
	_back = _side()
	_back.add_child(_image(BACK))
	_back_name = _text_label(_back, Rect2(LORE.position - Vector2(0, 1), Vector2(LORE.size.x, 11)), 8, INK, HORIZONTAL_ALIGNMENT_CENTER)
	var rule := ColorRect.new()
	rule.color = Color(INK, 0.45)
	rule.position = LORE.position + Vector2(12, 12)
	rule.size = Vector2(LORE.size.x - 24, 1)
	_back.add_child(rule)
	_lore = _text_label(_back, Rect2(LORE.position + Vector2(0, 15), LORE.size - Vector2(0, 15)), 6, INK_SOFT,
			HORIZONTAL_ALIGNMENT_LEFT)
	_lore.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	_lore.add_theme_constant_override(&"line_spacing", -2)
	_refresh()


func _side() -> Control:
	var side := Control.new()
	side.size = SIZE
	side.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(side)
	return side


func _image(texture: Texture2D) -> TextureRect:
	var rect := TextureRect.new()
	rect.texture = texture
	return rect


func _text_label(parent: Control, rect: Rect2, font_size: int, color: Color, align: HorizontalAlignment) -> Label:
	var label := Label.new()
	# Card text is small and the card is often shown scaled, so it keeps the smooth
	# font in dark ink rather than the game's outlined pixel font.
	label.theme_type_variation = &"InkLabel"
	label.add_theme_font_override(&"font", ThemeDB.fallback_font)
	label.position = rect.position
	label.size = rect.size
	label.horizontal_alignment = align
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.clip_text = true
	label.add_theme_color_override(&"font_color", color)
	label.add_theme_font_size_override(&"font_size", font_size)
	label.add_theme_constant_override(&"line_spacing", -2)
	parent.add_child(label)
	return label


## Shrinks a one-line label's font until its text fits `width` (long names on the
## banner, like "Sorenda Star Map").
func _fit(label: Label, width: float, largest: int) -> void:
	label.autowrap_mode = TextServer.AUTOWRAP_OFF
	var font := ThemeDB.fallback_font
	var size := largest
	while size > 5 and font.get_string_size(label.text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x > width:
		size -= 1
	label.add_theme_font_size_override(&"font_size", size)


## The card's outline as a solid shape (the frame with its window filled in), for
## effects that should stay on the card, like the reveal's shine.
static func silhouette() -> Texture2D:
	var image: Image = FRONT.get_image()
	image.convert(Image.FORMAT_RGBA8)
	image.fill_rect(Rect2i(WINDOW), Color.WHITE)
	return ImageTexture.create_from_image(image)


func _refresh() -> void:
	_front.visible = not showing_back
	_back.visible = showing_back
	if card == null:
		return
	_art.texture = card.icon
	_placeholder.visible = card.icon == null
	_placeholder.text = card.display_name.left(1)
	_name.text = card.display_name
	_fit(_name, NAME_WIDTH, 9)
	_text.text = card.description
	_back_name.text = card.display_name
	_lore.text = card.lore
