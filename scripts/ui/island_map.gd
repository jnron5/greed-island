class_name IslandMap
extends Control
## The island map in the pause menu: every outdoor area as a parchment plaque at its
## place on the island (WorldMap origins), the roads between them (gated roads drawn
## dashed and marked with a lock until their gate opens), and a gold marker where you
## are. Interiors show as the town they're in.

const INK := Color(0.28, 0.16, 0.08)
const PAPER := Color(0.93, 0.85, 0.68)
const PAPER_DARK := Color(0.8, 0.68, 0.48)
const SEA := Color(0.16, 0.36, 0.46)
const GOLD := Color(1.0, 0.8, 0.35)
var FONT: Font = get_theme_default_font()

var _time := 0.0


func _ready() -> void:
	clip_contents = true


func _process(delta: float) -> void:
	_time += delta
	if is_visible_in_tree():
		queue_redraw()


func _areas() -> Array[String]:
	var out: Array[String] = []
	for zone: String in WorldMap.ZONES:
		if not "interiors" in zone:
			out.append(zone)
	return out


## Where on this control an island position lands (the areas fitted in with a margin).
func _layout() -> Dictionary:
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for zone in _areas():
		var o: Vector2 = WorldMap.ZONES[zone].origin
		lo = lo.min(o)
		hi = hi.max(o)
	var span := (hi - lo).max(Vector2(1, 1))
	var inner := size - Vector2(170, 110)
	var k := minf(inner.x / span.x, inner.y / span.y)
	var offset := (size - span * k) / 2.0 - lo * k
	return {"k": k, "offset": offset}


func _at(zone: String, layout: Dictionary) -> Vector2:
	return (WorldMap.ZONES[zone].origin as Vector2) * layout.k + layout.offset


func _here() -> String:
	var scene := get_tree().current_scene
	var path := scene.scene_file_path if scene else ""
	if "interiors" in path:
		return WorldMap.SORENDA if "sorenda" in path else WorldMap.KALMORA
	return path


func _draw() -> void:
	# Sea, with a parchment island under the areas.
	draw_rect(Rect2(Vector2.ZERO, size), SEA)
	for i in 6:
		var y := 14.0 + i * size.y / 6.0
		draw_line(Vector2(8, y), Vector2(size.x - 8, y + 4), Color(1, 1, 1, 0.05), 1.0)
	var layout := _layout()
	for zone in _areas():
		draw_circle(_at(zone, layout), 40.0, PAPER_DARK)
	for zone in _areas():
		draw_circle(_at(zone, layout), 36.0, PAPER)
	# Roads.
	var drawn := {}
	for edge in WorldMap.EDGES:
		var key := [edge.from, edge.to]
		key.sort()
		if drawn.has(str(key)) or not layout.has("k"):
			continue
		drawn[str(key)] = true
		var a := _at(edge.from, layout)
		var b := _at(edge.to, layout)
		var open: bool = edge.gate == &"" or GameState.opened_gates.has(edge.gate)
		if open:
			draw_line(a, b, INK, 2.0)
		else:
			draw_dashed_line(a, b, Color(INK, 0.7), 2.0, 5.0)
			var mid := (a + b) / 2.0
			draw_rect(Rect2(mid - Vector2(4, 2), Vector2(8, 7)), INK)
			draw_arc(mid - Vector2(0, 2), 3.0, PI, TAU, 8, INK, 1.5)
	# Plaques.
	var here := _here()
	for zone in _areas():
		var p := _at(zone, layout)
		var text := WorldMap.zone_name(zone)
		var w := FONT.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x + 12
		var plaque := Rect2(p - Vector2(w / 2.0, 9), Vector2(w, 16))
		draw_rect(plaque.grow(1), INK)
		draw_rect(plaque, PAPER if zone != here else GOLD)
		draw_string(FONT, plaque.position + Vector2(6, 12), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, INK)
		if WorldMap.is_town(zone):
			draw_rect(Rect2(p + Vector2(-3, 10), Vector2(6, 5)), INK)       # a little house for towns
			draw_colored_polygon(PackedVector2Array([p + Vector2(-5, 10), p + Vector2(5, 10), p + Vector2(0, 5)]), INK)
	# Where a quest or favour needs you: a bobbing gold "!".
	for zone in Quests.map_goals():
		if zone in WorldMap.ZONES:
			var q := _at(zone, layout) + Vector2(26, -22 + roundf(sin(_time * 3.0 + zone.length()) * 1.5))
			draw_circle(q, 7.0, INK)
			draw_circle(q, 6.0, GOLD)
			draw_string(FONT, q + Vector2(-2, 4), "!", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, INK)
	# You are here.
	if here in WorldMap.ZONES:
		var p := _at(here, layout) + Vector2(0, -20 + roundf(sin(_time * 4.0) * 2.0))
		draw_colored_polygon(PackedVector2Array([p + Vector2(-5, -7), p + Vector2(5, -7), p]), GOLD)
		draw_polyline(PackedVector2Array([p + Vector2(-5, -7), p + Vector2(5, -7), p, p + Vector2(-5, -7)]), INK, 1.0)
	draw_string(FONT, Vector2(8, size.y - 8), "Virelia Isle   (dashed: a gate still shut   !: a quest or favour)", HORIZONTAL_ALIGNMENT_LEFT, -1, 10,
		Color(1, 1, 1, 0.75))
