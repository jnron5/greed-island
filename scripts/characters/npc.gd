class_name Npc
extends CharacterBody2D
## A resident of the island (a dog or cat townsperson). Idles or wanders near
## home, turns to face you, and talks when you press interact nearby. What it
## says comes from the quest system first (Quests.dialogue_for), then its own
## ambient lines, cycling. Then, if they have topics (TalkTopics) or a shop, a
## question list: ask about something, browse their wares, or say goodbye.
## 4-directional animations "idle_<dir>" / "walk_<dir>".

const DIRECTIONS_4: Array[String] = ["east", "south", "west", "north"]
const TALK_RANGE := 34.0

@export var npc_id: StringName
@export var display_name := "Resident"
@export var sprite_frames: SpriteFrames
@export var sprite_offset_y := -26.0
## Ambient things to say, one line per conversation (in order, looping).
@export_multiline var lines: PackedStringArray = []
## 0 = stands still at home.
@export var wander_radius := 0.0
@export var walk_speed := 30.0
## A daily round: points (relative to home) walked in order, pausing at each.
## Overrides wandering.
@export var patrol: PackedVector2Array = []
## Roaming (travellers, Travellers): global points to walk between along the zone's
## paths (Zone.find_path), pausing a few seconds at each.
@export var roam_points: PackedVector2Array = []
## Places a roamer never stops near (doors), Travellers.DOOR_CLEAR px.
@export var avoid_points: PackedVector2Array = []
@export var patrol_pause := 3.0
## Shopkeepers: after talking, open the shop with this stock.
@export var shop_stock: Array[StringName] = []
## Whether this shopkeeper also buys set cards (card merchants do; a baker doesn't).
@export var shop_buys_cards := true
## The shop's name on its window (defaults to the shopkeeper's).
@export var shop_title := ""
## An inn keeper: offers a room for half a day or a full day (Inn).
@export var inn_rooms := false
## What the keeper says when you ask for a room, and when you can't pay.
@export var room_prompt := "A bed, clean sheets, quiet. How long will you sleep?"
@export var room_broke := "That's %d gold. Come back when your purse is heavier."
## A resident who serves a meal at a set hour (Tally's dinner at five): for the
## hour from meal_hour they say meal_lines and the meal mends every heart; in the
## hour before, they say one of pre_meal_lines. -1 = no meal.
@export var meal_hour := -1.0
@export_multiline var meal_lines: PackedStringArray = []
@export_multiline var pre_meal_lines: PackedStringArray = []

## What an inn keeper says when a collector who fainted on the road comes round in
## one of their beds (one per waking, rotating).
@export_multiline var wake_lines: PackedStringArray = []

@export_group("Day and night")
## Where this resident spends the night in this zone (zone-local): after dusk they
## walk there (by the zone's paths) and wander round it; at dawn they walk back.
@export var has_night_spot := false
@export var night_spot := Vector2.ZERO
@export var night_wander := 0.0
## The hours they're out and about here; the rest of the time they're elsewhere
## (indoors, or out, if this is the indoor copy): hidden, silent, no collision.
## Equal = always here. Wraps past midnight (20 -> 6 is the night).
@export var out_from := 0.0
@export var out_to := 0.0
## What they say after dark instead of `lines` (at a party, on watch), if anything.
@export_multiline var night_lines: PackedStringArray = []
## Things they call out now and then in a speech bubble when you're nearby (a party
## after dark: toasts, songs, gossip). Only after dark unless `chatter_by_day`.
@export var chatter: PackedStringArray = []
@export var chatter_by_day := false

const NIGHT_FROM := 20.0
const NIGHT_TO := 6.5

## Where each resident is in their lines, kept across visits (a scene reload makes
## a new Npc), so coming back doesn't start the same speech over.
static var _next_line: Dictionary = {}

var facing := Vector2.DOWN

var _home := Vector2.ZERO
var _goal := Vector2.ZERO
var _wait := 0.0
var _talking := false
var _patrol_index := 0
var _pausing := true
var _day_home := Vector2.ZERO
var _day_wander := 0.0
var _night := false
var _route := PackedVector2Array()
var _route_time := 0.0
var _here := true
var _clock := 0.0
var _roam_route := PackedVector2Array()
var _bubble := ""
var _bubble_time := 0.0
var _chatter_wait := randf_range(2.0, 9.0)

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
	add_to_group(&"npcs")
	if sprite_frames:
		sprite.sprite_frames = sprite_frames
	sprite.offset.y = sprite_offset_y
	_day_home = position
	_day_wander = wander_radius
	_home = position
	# Coming into the zone after dark: they're already where they spend the night.
	if has_night_spot and is_night():
		_night = true
		_settle_at(night_spot, night_wander)
	_goal = position
	_wait = randf_range(1.0, 4.0)
	_set_here(is_out(), true)


## Night by the clock (the hours residents keep to their night spot).
static func is_night() -> bool:
	return TimeOfDay.hour >= NIGHT_FROM or TimeOfDay.hour < NIGHT_TO


## Whether this resident is out and about here at this hour.
func is_out() -> bool:
	if is_equal_approx(out_from, out_to):
		return true
	var h := TimeOfDay.hour
	return h >= out_from and h < out_to if out_from < out_to else h >= out_from or h < out_to


func _settle_at(spot: Vector2, radius: float) -> void:
	position = spot
	_home = spot
	_goal = spot
	wander_radius = radius
	_route = PackedVector2Array()


## Come and go: shown and solid, or gone (indoors / out) without a sound. Never
## vanishes or appears in front of the player: it waits until it's off screen.
func _set_here(here: bool, force := false) -> void:
	if here == _here and not force:
		return
	if not force and _on_screen():
		return
	_here = here
	visible = here
	$CollisionShape2D.set_deferred(&"disabled", not here)


func _on_screen() -> bool:
	var view := get_viewport_rect()
	var rect := get_canvas_transform().affine_inverse() * view
	return rect.grow(40.0).has_point(global_position)


## Dusk and dawn: set off for the night spot (or back home) along the zone's paths;
## a resident who can't find a way goes there when nobody's looking.
func _keep_hours(delta: float) -> void:
	_clock -= delta
	if _clock > 0.0:
		return
	_clock = 1.0
	_set_here(is_out())
	if not has_night_spot or is_night() == _night:
		return
	_night = is_night()
	var target := night_spot if _night else _day_home
	wander_radius = 0.0
	_route = PackedVector2Array()
	var zone := get_tree().current_scene as Zone
	if zone and zone.has_method(&"find_path"):
		_route = zone.find_path(global_position, get_parent().to_global(target) if get_parent() is Node2D else target)
	if _route.is_empty():
		_route = PackedVector2Array([get_parent().to_global(target) if get_parent() is Node2D else target])
	_route_time = 0.0


func _follow_route(delta: float) -> void:
	_route_time += delta
	var target := _route[0]
	if global_position.distance_to(target) < 4.0:
		_route.remove_at(0)
		if _route.is_empty():
			_arrive()
		return
	velocity = global_position.direction_to(target) * walk_speed * 1.2
	# Stuck on the way: finish the trip off screen.
	if _route_time > 45.0 and not _on_screen():
		_arrive()


## A traveller's day: walk to one of `roam_points` (a little off it, never on a
## doorstep), stand a while, pick another.
func _roam(delta: float) -> void:
	if _roam_route.is_empty():
		velocity = Vector2.ZERO
		_wait -= delta
		if _wait > 0.0:
			return
		var target := roam_points[randi() % roam_points.size()] + Vector2(randf_range(-16.0, 16.0), randf_range(6.0, 20.0))
		for door in avoid_points:
			if door.distance_to(target) < Travellers.DOOR_CLEAR:
				target = door + door.direction_to(target).normalized() * Travellers.DOOR_CLEAR if door != target else door + Vector2(0, Travellers.DOOR_CLEAR)
		var zone := get_tree().current_scene as Zone
		_roam_route = zone.find_path(global_position, target) if zone else PackedVector2Array([target])
		_route_time = 0.0
		if _roam_route.is_empty():
			_wait = 2.0
		return
	_route_time += delta
	var next := _roam_route[0]
	if global_position.distance_to(next) < 4.0:
		_roam_route.remove_at(0)
		if _roam_route.is_empty():
			velocity = Vector2.ZERO
			_wait = randf_range(3.0, 9.0)
			# Ended up by a door anyway (a partial path): move on at once.
			for door in avoid_points:
				if door.distance_to(global_position) < Travellers.DOOR_CLEAR:
					_wait = 0.0
		return
	velocity = global_position.direction_to(next) * walk_speed
	if _route_time > 40.0:                      # stuck: stand here a moment, then go elsewhere
		_roam_route = PackedVector2Array()
		_wait = 1.0


func _arrive() -> void:
	velocity = Vector2.ZERO
	_settle_at(night_spot if _night else _day_home, night_wander if _night else _day_wander)


func _physics_process(delta: float) -> void:
	_keep_hours(delta)
	if not _here:
		velocity = Vector2.ZERO
		return
	_chatter(delta)
	if _talking:
		velocity = Vector2.ZERO
	elif not _route.is_empty():
		_follow_route(delta)
	elif not roam_points.is_empty():
		_roam(delta)
	elif not patrol.is_empty() and not _night:
		_wait -= delta
		var target := _home + patrol[_patrol_index]
		if _pausing:
			velocity = Vector2.ZERO
			if _wait <= 0.0:                      # rested: on to the next stop
				_pausing = false
				_patrol_index = (_patrol_index + 1) % patrol.size()
				_wait = 12.0                      # give up on a stop that can't be reached
		elif position.distance_to(target) < 3.0 or _wait <= 0.0:
			_pausing = true
			_wait = patrol_pause
			velocity = Vector2.ZERO
		else:
			velocity = position.direction_to(target) * walk_speed
	elif wander_radius > 0.0:
		_wait -= delta
		if position.distance_to(_goal) < 3.0:
			velocity = Vector2.ZERO
			if _wait <= 0.0:
				_goal = _home + Vector2.from_angle(randf() * TAU) * randf_range(8.0, wander_radius)
				_wait = randf_range(2.0, 5.0)
		else:
			velocity = position.direction_to(_goal) * walk_speed
			if _wait < -6.0:
				_goal = position  # Stuck against something: give up on this spot.
	move_and_slide()
	_update_animation()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if _talking or not _here or GameState.menus_open > 0 or not event.is_action_pressed(&"interact"):
		return
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if player == null or player.global_position.distance_to(global_position) > TALK_RANGE:
		return
	get_viewport().set_input_as_handled()
	talk(player)


func talk(player: Node2D) -> void:
	_talking = true
	facing = global_position.direction_to(player.global_position)
	var said: PackedStringArray = Quests.dialogue_for(npc_id)
	if said.is_empty():
		said = Errands.dialogue_for(npc_id)
	if said.is_empty():
		said = _meal_talk()
	if said.is_empty() and not night_lines.is_empty() and is_night():
		said = PackedStringArray([next_line(night_lines)])
	if said.is_empty() and not lines.is_empty():
		said = PackedStringArray([next_line(lines)])
	DialogueBox.say(get_tree(), display_name, said, _done_talking, DialogueBox.portrait_from(sprite.sprite_frames))


## The player has just come round in this keeper's inn: they turn to them and say
## welcome back, then `on_done` runs (the lost card is shown).
func welcome_back(on_done: Callable) -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if player:
		facing = global_position.direction_to(player.global_position)
	var line := next_line(wake_lines) if not wake_lines.is_empty() else "Welcome back. You gave us a fright."
	DialogueBox.say(get_tree(), display_name, PackedStringArray([line]), on_done,
		DialogueBox.portrait_from(sprite.sprite_frames))


## The next of `pool`, one per conversation, looping; remembered across visits.
## Starts somewhere random so two playthroughs don't open the same way.
func next_line(pool: PackedStringArray) -> String:
	var key := String(npc_id) + ":" + str(pool.size())
	if not _next_line.has(key):
		_next_line[key] = randi() % pool.size()
	var i: int = _next_line[key] % pool.size()
	_next_line[key] = i + 1
	return pool[i]


## Around the meal hour: the meal itself (and every heart mended), or the warning
## that it's coming. Empty the rest of the day.
func _meal_talk() -> PackedStringArray:
	if meal_hour < 0.0:
		return PackedStringArray()
	var h := TimeOfDay.hour
	if h >= meal_hour and h < meal_hour + 1.0 and not meal_lines.is_empty():
		var player := get_tree().get_first_node_in_group(&"player") as Player
		if player and player.health < player.max_health:
			player.heal(player.max_health)
			Sfx.play(&"heal")
			EventBus.notify.emit("Dinner. Every heart mended.")
		return meal_lines
	if h >= meal_hour - 1.0 and h < meal_hour and not pre_meal_lines.is_empty():
		return PackedStringArray([next_line(pre_meal_lines)])
	return PackedStringArray()


func _done_talking() -> void:
	Quests.talked_to(npc_id)
	Errands.talked_to(npc_id)
	_offer_topics()


## The question list after a chat: this resident's topics, their shop, goodbye.
func _offer_topics() -> void:
	var topics := TalkTopics.for_npc(npc_id)
	if topics.is_empty() and shop_stock.is_empty() and not inn_rooms:
		_talking = false
		return
	var options := PackedStringArray()
	for topic: Array in topics:
		options.append(topic[0])
	if inn_rooms:
		options.append("I'd like a room")
	if not shop_stock.is_empty():
		options.append("Let me see your wares")
	options.append("Goodbye")
	DialogueBox.ask(get_tree(), display_name, "Anything else?", options, _on_topic,
		DialogueBox.portrait_from(sprite.sprite_frames))


func _on_topic(index: int) -> void:
	var topics := TalkTopics.for_npc(npc_id)
	if index < topics.size():
		DialogueBox.say(get_tree(), display_name, PackedStringArray(topics[index][1]), _offer_topics,
			DialogueBox.portrait_from(sprite.sprite_frames))
		return
	var at := topics.size()
	if inn_rooms:
		if index == at:
			_offer_room()
			return
		at += 1
	_talking = false
	if index == at and not shop_stock.is_empty():
		var shop := get_tree().get_first_node_in_group(&"shop_panel") as ShopPanel
		if shop:
			shop.open_with(shop_stock, shop_title if shop_title != "" else display_name, shop_buys_cards)


## Half a day or a full day; pay, sleep, wake mended.
func _offer_room() -> void:
	var offers := Inn.offers()
	var options := PackedStringArray()
	for offer: Array in offers:
		options.append(offer[0])
	options.append("Never mind")
	var portrait := DialogueBox.portrait_from(sprite.sprite_frames)
	DialogueBox.ask(get_tree(), display_name, room_prompt, options,
		func(pick: int) -> void:
			if pick >= offers.size():
				_offer_topics()
				return
			var offer: Array = offers[pick]
			if not Inn.sleep(get_tree(), offer[1], offer[2]):
				DialogueBox.say(get_tree(), display_name, PackedStringArray([room_broke % offer[2] if "%d" in room_broke else room_broke]),
					_offer_topics, portrait)
				return
			_talking = false
			EventBus.notify.emit("You slept %s. Every heart mended." % ("half a day" if offer[1] < 24.0 else "a full day")),
		portrait)


func _update_animation() -> void:
	if sprite.sprite_frames == null:
		return
	if velocity.length() > 1.0:
		facing = velocity.normalized()
	var dir := DIRECTIONS_4[wrapi(roundi(facing.angle() / (PI / 2.0)), 0, 4)]
	var action := "walk" if velocity.length() > 1.0 else "idle"
	for candidate in [action, "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


## Now and then a line from `chatter` in a bubble over their head, while you're near.
func _chatter(delta: float) -> void:
	if chatter.is_empty():
		return
	if _bubble != "":
		_bubble_time -= delta
		if _bubble_time <= 0.0:
			_bubble = ""
		queue_redraw()
		return
	_chatter_wait -= delta
	if _chatter_wait > 0.0:
		return
	_chatter_wait = randf_range(7.0, 15.0)
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if _talking or (not chatter_by_day and not is_night()) or player == null \
			or player.global_position.distance_to(global_position) > 260.0:
		return
	_bubble = chatter[randi() % chatter.size()]
	_bubble_time = 3.4


func _draw() -> void:
	if _bubble != "":
		WorldPrompt.bubble(self, Vector2(0, sprite_offset_y * 2 - 6), _bubble, clampf(_bubble_time * 2.0, 0.0, 1.0))
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	var marker := Quests.marker_for(npc_id)
	if marker == "":
		marker = Errands.marker_for(npc_id)
	if marker != "":
		WorldPrompt.marker(self, Vector2(0, sprite_offset_y * 2 - 8), marker, Color(1, 0.85, 0.3))
	if player and not _talking and player.global_position.distance_to(global_position) <= TALK_RANGE:
		WorldPrompt.draw(self, Vector2(0, sprite_offset_y * 2), "E", "Talk")
