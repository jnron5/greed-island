class_name WorldPrompt
## Small in-world hints in the game's UI style, drawn by the node they belong to:
## a dark plate with a gold key cap and the action ("[E] Talk"), and bobbing quest
## or alert markers. Text uses the theme's smooth body font (sharp under the 2x
## canvas scale); markers use the gold pixel title font at its native 16px.

const TITLE_FONT := preload("res://assets/fonts/virelia_title.tres")
const NATIVE := 16
const SIZE := 9
const PLATE := Color(0.05, 0.13, 0.16, 0.9)
const RIM := Color(0.85, 0.62, 0.3)
const CREAM := Color(0.97, 0.92, 0.8)
const INK := Color(0.2, 0.11, 0.05)


## "[key] action" centred on `center` (the plate's middle), e.g. key "E", text "Talk".
static func draw(ci: CanvasItem, center: Vector2, key: String, text: String) -> void:
	var font := _font()
	var text_w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, SIZE).x
	var cap_w := font.get_string_size(key, HORIZONTAL_ALIGNMENT_LEFT, -1, SIZE).x + 4.0
	var w := roundf(cap_w + text_w + 10)
	var h := 13.0
	var origin := (center - Vector2(w / 2.0, h / 2.0)).round()
	ci.draw_rect(Rect2(origin + Vector2(1, 0), Vector2(w - 2, h)), PLATE)       # plate, corners cut
	ci.draw_rect(Rect2(origin + Vector2(0, 1), Vector2(w, h - 2)), PLATE)
	ci.draw_rect(Rect2(origin + Vector2(1, h - 1), Vector2(w - 2, 1)), RIM)      # gold underline
	var cap := Rect2(origin + Vector2(2, 2), Vector2(cap_w, h - 4))
	ci.draw_rect(cap, RIM)
	ci.draw_string(font, Vector2(cap.position.x + 2, origin.y + 10), key, HORIZONTAL_ALIGNMENT_LEFT, -1, SIZE, INK)
	ci.draw_string(font, Vector2(cap.end.x + 4, origin.y + 10), text, HORIZONTAL_ALIGNMENT_LEFT, -1, SIZE, CREAM)


## A bobbing marker ("!" for news, "?" for suspicion) above a character.
static func marker(ci: CanvasItem, at: Vector2, mark: String, color: Color) -> void:
	var bob := roundf(sin(Time.get_ticks_msec() / 220.0) * 1.5)
	var pos := (at + Vector2(-3, bob)).round()
	ci.draw_string_outline(TITLE_FONT, pos, mark, HORIZONTAL_ALIGNMENT_LEFT, -1, NATIVE, 4, Color(0.08, 0.05, 0.03))
	ci.draw_string(TITLE_FONT, pos, mark, HORIZONTAL_ALIGNMENT_LEFT, -1, NATIVE, color)


static func _font() -> Font:
	var theme := ThemeDB.get_project_theme()
	return theme.default_font if theme and theme.default_font else ThemeDB.fallback_font
