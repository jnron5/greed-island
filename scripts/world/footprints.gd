class_name Footprints
extends Node2D
## Footprints left in sand by everyone walking on it (player, rivals, residents).
## A pair of small dents per stride, pressed a little darker than the sand; each
## stays a moment, then fades. The zone creates this when its surface map marks
## sand (green channel) and tells it where that map sits.

const STRIDE := 7.0        # px walked per print
const HOLD := 1.6          # seconds a print stays fully visible
const FADE := 1.4          # seconds it takes to fade out
const MAX_PRINTS := 400
const COLOR_PRINT := Color(0.4, 0.27, 0.13, 0.55)
const COLOR_RIM := Color(1.0, 0.95, 0.82, 0.4)

var surface: Image
var origin := Vector2.ZERO   # local position of the surface map's top-left pixel

var _last := {}              # node instance id -> [last print position, next foot (-1 or 1)]
var _prints: Array = []      # [position, direction, age]


func _ready() -> void:
	z_index = -9
	z_as_relative = false


func on_sand(local_pos: Vector2) -> bool:
	var p := Vector2i((local_pos - origin).floor())
	if p.x < 0 or p.y < 0 or p.x >= surface.get_width() or p.y >= surface.get_height():
		return false
	return surface.get_pixel(p.x, p.y).g > 0.5


func _physics_process(delta: float) -> void:
	for i in range(_prints.size() - 1, -1, -1):
		_prints[i][2] += delta
		if _prints[i][2] > HOLD + FADE:
			_prints.remove_at(i)
	var seen := {}
	for group in [&"collectors", &"npcs"]:
		for node: Node2D in get_tree().get_nodes_in_group(group):
			if not node.visible or not node.is_inside_tree():
				continue
			var id := node.get_instance_id()
			seen[id] = true
			var pos := to_local(node.global_position)
			if not _last.has(id):
				_last[id] = [pos, 1]
				continue
			var step: Vector2 = pos - _last[id][0]
			if step.length() > 64.0:          # teleported (spawn, respawn): start over
				_last[id] = [pos, 1]
			elif step.length() >= STRIDE:
				if on_sand(pos):
					var dir := step.normalized()
					var side: Vector2 = Vector2(-dir.y, dir.x) * 1.5 * _last[id][1]
					_prints.append([pos + side, dir, 0.0])
					if _prints.size() > MAX_PRINTS:
						_prints.pop_front()
				_last[id] = [pos, -_last[id][1]]
	for id in _last.keys():
		if not seen.has(id):
			_last.erase(id)
	queue_redraw()


func _draw() -> void:
	for p in _prints:
		var alpha := 1.0 - clampf((p[2] - HOLD) / FADE, 0.0, 1.0)
		var at: Vector2 = (p[0] as Vector2).round()
		var dir: Vector2 = p[1]
		# A small oval dent: 2x3 px along the walking direction, with a light lip ahead.
		var long := absf(dir.y) > absf(dir.x)
		var size := Vector2(2, 3) if long else Vector2(3, 2)
		draw_rect(Rect2(at - (size / 2.0).floor(), size), Color(COLOR_PRINT, COLOR_PRINT.a * alpha))
		var lip := (at + (dir * 2.0).round() - Vector2(0.5, 0.5)).floor()
		draw_rect(Rect2(lip, Vector2.ONE), Color(COLOR_RIM, COLOR_RIM.a * alpha))
