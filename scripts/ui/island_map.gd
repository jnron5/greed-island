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
const ROOM_AREAS := {
	"kalmora_": WorldMap.KALMORA, "sorenda_": WorldMap.SORENDA, "verdana_": WorldMap.VERDANA,
	"serin_": WorldMap.LAKE_SERIN, "starfall_": WorldMap.STARFALL, "seabright_": WorldMap.SEABRIGHT, "frisalle_": WorldMap.FRISALLE, "duskara_": WorldMap.DUSKARA, "vetrassa_": WorldMap.VETRASSA, "halmeer_": WorldMap.HALMEER,
}
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


## Each area's name plaque, centred on it, then pushed apart a few times so no two
## overlap (areas close together on the island keep readable names).
func _plaques(layout: Dictionary) -> Dictionary:
	var out := {}
	for zone in _areas():
		var p := _at(zone, layout)
		var w := FONT.get_string_size(WorldMap.zone_name(zone), HORIZONTAL_ALIGNMENT_LEFT, -1, 10).x + 12
		out[zone] = Rect2(p - Vector2(w / 2.0, 9), Vector2(w, 16))
	var zones := _areas()
	for _pass in 24:
		var moved := false
		for i in zones.size():
			for j in range(i + 1, zones.size()):
				var a: Rect2 = out[zones[i]]
				var b: Rect2 = out[zones[j]]
				var gap := a.grow(1).intersection(b.grow(1))
				if gap.size.x <= 0.0 or gap.size.y <= 0.0:
					continue
				# Push apart along whichever way overlaps less (mostly up and down).
				var push := Vector2(0, gap.size.y / 2.0 + 0.5) if gap.size.y < gap.size.x * 1.5 else Vector2(gap.size.x / 2.0 + 0.5, 0)
				var dir := 1.0 if a.get_center().y <= b.get_center().y else -1.0
				if push.x > 0.0:
					dir = 1.0 if a.get_center().x <= b.get_center().x else -1.0
				out[zones[i]] = Rect2(a.position - push * dir, a.size)
				out[zones[j]] = Rect2(b.position + push * dir, b.size)
				moved = true
		if not moved:
			break
	return out


func _here() -> String:
	var scene := get_tree().current_scene
	var path := scene.scene_file_path if scene else ""
	if "interiors" in path:
		# A room shows as the area it stands in (interiors are named after it).
		for prefix: String in ROOM_AREAS:
			if path.get_file().begins_with(prefix):
				return ROOM_AREAS[prefix]
		return WorldMap.KALMORA
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
	# Plaques (nudged apart where neighbouring areas would overlap).
	var here := _here()
	var plaques := _plaques(layout)
	for zone in _areas():
		var p := _at(zone, layout)
		var text := WorldMap.zone_name(zone)
		var plaque: Rect2 = plaques[zone]
		draw_rect(plaque.grow(1), INK)
		draw_rect(plaque, PAPER if zone != here else GOLD)
		draw_string(FONT, plaque.position + Vector2(6, 12), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 10, INK)
		p = Vector2(plaque.get_center().x, plaque.position.y + 9)
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
