extends Node
## Collider audit: for every solid thing with art in every zone (a StaticBody2D with a
## Sprite2D / AnimatedSprite2D under it, a tree, a resident), compares its collision
## shapes with the opaque part of its art and reports the ones that don't match: a
## collider off centre from what's drawn, wider than it, poking out below its feet or
## above its top. Run: godot --headless --path . res://scripts/tools/run_collider_audit.tscn

const TOLERANCE := 6.0

var problems := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	var zones: Array[String] = []
	for path: String in WorldMap.ZONES:
		zones.append(path)
	for path in zones:
		var packed := load(path) as PackedScene
		if packed == null:
			continue
		var zone := packed.instantiate()
		add_child(zone)
		for body in zone.find_children("*", "CollisionObject2D", true, false):
			_check(path.get_file(), body as CollisionObject2D)
		zone.queue_free()
		await get_tree().process_frame
	print("collider audit: %d problem(s)" % problems)
	get_tree().quit(1 if problems else 0)


func _check(zone: String, body: CollisionObject2D) -> void:
	if not (body is StaticBody2D or body is CharacterBody2D):
		return
	var art := _art_rect(body)
	if art.size == Vector2.ZERO:
		return
	for shape_node in body.find_children("*", "CollisionShape2D", false, false):
		var cs := shape_node as CollisionShape2D
		var rect := _shape_rect(cs)
		if rect.size == Vector2.ZERO:
			continue
		var issues: PackedStringArray = []
		# The foot should sit inside the drawn width and centred under it (for a
		# collider at least half the art's width; small feet under one side, like a
		# cave mouth's pillars, are on purpose).
		if rect.size.x > art.size.x + TOLERANCE * 2:
			issues.append("wider than its art (%d vs %d)" % [rect.size.x, art.size.x])
		if rect.size.x >= art.size.x * 0.5 and absf(rect.get_center().x - art.get_center().x) > maxf(TOLERANCE, art.size.x * 0.12):
			issues.append("off centre by %d" % (rect.get_center().x - art.get_center().x))
		if rect.end.y > art.end.y + TOLERANCE * 2:
			issues.append("reaches %d below its art" % (rect.end.y - art.end.y))
		if rect.position.y < art.position.y - TOLERANCE:
			issues.append("taller than its art")
		if rect.position.x > art.end.x or rect.end.x < art.position.x:
			issues.append("outside its art")
		# A narrow foot (a trunk, a character's feet) should still stand under the
		# middle of what's drawn, and every foot should reach down to the art's base.
		var single := body.find_children("*", "CollisionShape2D", false, false).size() == 1
		if single and rect.size.x < art.size.x * 0.5 \
				and absf(rect.get_center().x - art.get_center().x) > maxf(TOLERANCE, art.size.x * 0.18):
			issues.append("foot off centre by %d" % (rect.get_center().x - art.get_center().x))
		if single and rect.end.y < art.end.y - 16.0:
			issues.append("foot %d above the art's base" % (art.end.y - rect.end.y))
		if not issues.is_empty():
			problems += 1
			print("  %s  %s/%s: %s" % [zone, body.name, cs.name, ", ".join(issues)])


## The opaque part of a body's art in global coordinates (the union of its sprites).
func _art_rect(body: Node) -> Rect2:
	var out := Rect2()
	for node in body.find_children("*", "", true, false):
		var tex: Texture2D = null
		var sprite_node := node as Node2D
		if node is Sprite2D and (node as Sprite2D).texture:
			tex = (node as Sprite2D).texture
		elif node is AnimatedSprite2D and (node as AnimatedSprite2D).sprite_frames:
			var asp := node as AnimatedSprite2D
			var anims := asp.sprite_frames.get_animation_names()
			if anims.size() > 0 and asp.sprite_frames.get_frame_count(anims[0]) > 0:
				tex = asp.sprite_frames.get_frame_texture(anims[0], 0)
		if tex == null or not sprite_node.visible:
			continue
		var img := tex.get_image()
		if img == null:
			continue
		if img.is_compressed():
			img.decompress()
		var used := img.get_used_rect()
		if used.size == Vector2i.ZERO:
			continue
		var size := Vector2(img.get_size())
		var origin := Vector2.ZERO
		var centered := true
		var offset := Vector2.ZERO
		var flip := false
		if node is Sprite2D:
			centered = (node as Sprite2D).centered
			offset = (node as Sprite2D).offset
			flip = (node as Sprite2D).flip_h
		else:
			centered = (node as AnimatedSprite2D).centered
			offset = (node as AnimatedSprite2D).offset
			flip = (node as AnimatedSprite2D).flip_h
		origin = offset - (size / 2.0 if centered else Vector2.ZERO)
		var r := Rect2(Vector2(used.position), Vector2(used.size))
		if flip:
			r.position.x = size.x - r.end.x
		r.position += origin
		var xf := sprite_node.global_transform
		var a := xf * r.position
		var b := xf * r.end
		var g := Rect2(Vector2(minf(a.x, b.x), minf(a.y, b.y)), (b - a).abs())
		out = g if out.size == Vector2.ZERO else out.merge(g)
	return out


func _shape_rect(cs: CollisionShape2D) -> Rect2:
	var xf := cs.global_transform
	if cs.shape is RectangleShape2D:
		var half := (cs.shape as RectangleShape2D).size / 2.0
		var a := xf * -half
		var b := xf * half
		return Rect2(Vector2(minf(a.x, b.x), minf(a.y, b.y)), (b - a).abs())
	if cs.shape is CircleShape2D:
		var r := (cs.shape as CircleShape2D).radius
		return Rect2(xf.origin - Vector2(r, r), Vector2(r, r) * 2.0)
	if cs.shape is CapsuleShape2D:
		var c := cs.shape as CapsuleShape2D
		return Rect2(xf.origin - Vector2(c.radius, c.height / 2.0), Vector2(c.radius * 2.0, c.height))
	return Rect2()
