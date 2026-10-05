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


## A speech bubble: a parchment plate with dark text and a little tail, centred on
## `center` (its bottom middle), fading with `alpha`.
static func bubble(ci: CanvasItem, center: Vector2, text: String, alpha := 1.0) -> void:
	var font := _font()
	var w := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, SIZE).x + 10
	var h := 14.0
	var origin := (center - Vector2(w / 2.0, h)).round()
	var paper := Color(0.96, 0.9, 0.76, 0.95 * alpha)
	var edge := Color(0.36, 0.22, 0.12, alpha)
	ci.draw_rect(Rect2(origin + Vector2(1, -1), Vector2(w - 2, h + 2)), edge)
	ci.draw_rect(Rect2(origin + Vector2(-1, 1), Vector2(w + 2, h - 2)), edge)
	ci.draw_rect(Rect2(origin + Vector2(1, 0), Vector2(w - 2, h)), paper)
	ci.draw_rect(Rect2(origin + Vector2(0, 1), Vector2(w, h - 2)), paper)
	var tip := (center + Vector2(0, 4)).round()
	ci.draw_colored_polygon(PackedVector2Array([tip, tip + Vector2(-4, -5), tip + Vector2(4, -5)]), paper)
	ci.draw_string(font, origin + Vector2(5, 10), text, HORIZONTAL_ALIGNMENT_LEFT, -1, SIZE, Color(INK, alpha))


## Something worth a look (a readable, a quest clue): a pool of warm light on the
## ground at `ground` and a bobbing gold four-point star `height` above it, orange
## with a "!" beside it when a running quest wants it. `time` drives the pulse.
const INTEREST := Color(1.0, 0.86, 0.42)
const INTEREST_QUEST := Color(1.0, 0.62, 0.22)


static func interest(ci: CanvasItem, ground: Vector2, height: float, time: float, quest := false) -> void:
	var colour := INTEREST_QUEST if quest else INTEREST
	var pulse := 0.5 + 0.5 * sin(time * 3.0)
	ci.draw_circle(ground + Vector2(0, 2), 12.0, Color(colour, 0.12 + 0.08 * pulse))
	ci.draw_circle(ground + Vector2(0, 2), 6.0, Color(colour, 0.2 + 0.12 * pulse))
	var at := ground + Vector2(0, height + roundf(sin(time * 2.2) * 1.5))
	star(ci, at, 8.5 + pulse, Color(0.12, 0.07, 0.03), 2.6)
	star(ci, at, 7.0 + pulse, colour, 1.8)
	ci.draw_rect(Rect2(at - Vector2(1, 1), Vector2(2, 2)), Color(1, 1, 0.9))
	if quest:
		marker(ci, at + Vector2(9, -2), "!", colour)


## A four-point star of `radius` centred on `at` (`waist`: how thin between points).
static func star(ci: CanvasItem, at: Vector2, radius: float, colour: Color, waist: float) -> void:
	var points := PackedVector2Array()
	for i in 8:
		points.append(at + Vector2.from_angle(i * PI / 4.0 - PI / 2.0) * (radius if i % 2 == 0 else waist))
	ci.draw_colored_polygon(points, colour)


## A bobbing marker ("!" for news, "?" for suspicion) above a character.
static func marker(ci: CanvasItem, at: Vector2, mark: String, color: Color) -> void:
	var bob := roundf(sin(Time.get_ticks_msec() / 220.0) * 1.5)
	if mark == "!" or mark == "?":
		_glyph_mark(ci, (at + Vector2(0, bob - 10)).round(), mark, color)
		return
	var pos := (at + Vector2(-3, bob)).round()
	ci.draw_string_outline(TITLE_FONT, pos, mark, HORIZONTAL_ALIGNMENT_LEFT, -1, NATIVE, 4, Color(0.08, 0.05, 0.03))
	ci.draw_string(TITLE_FONT, pos, mark, HORIZONTAL_ALIGNMENT_LEFT, -1, NATIVE, color)


static func _font() -> Font:
	var theme := ThemeDB.get_project_theme()
	return theme.default_font if theme and theme.default_font else ThemeDB.fallback_font


## A drawn "!" or "?" (the pixel font's own read as a plain bar at this size): a
## tapered stroke and a dot in `color`, outlined dark, `top` its top middle.
static func _glyph_mark(ci: CanvasItem, top: Vector2, mark: String, color: Color) -> void:
	var dark := Color(0.08, 0.05, 0.03)
	var rects: Array[Rect2] = []
	if mark == "!":
		rects = [Rect2(-2, 0, 5, 3), Rect2(-2, 3, 5, 3), Rect2(-1, 6, 3, 3), Rect2(-1, 11, 3, 3)]
	else:
		rects = [Rect2(-3, 0, 7, 2), Rect2(-4, 1, 2, 4), Rect2(3, 1, 2, 4), Rect2(1, 4, 3, 2), Rect2(-1, 6, 3, 3), Rect2(-1, 11, 3, 3)]
	for r in rects:
		ci.draw_rect(Rect2(top + r.position - Vector2(1, 1), r.size + Vector2(2, 2)), dark)
	for r in rects:
		ci.draw_rect(Rect2(top + r.position, r.size), color)
	# a highlight on the stroke
	ci.draw_rect(Rect2(top + Vector2(-1, 1), Vector2(1, 4)), Color(1, 1, 0.85, 0.8))
