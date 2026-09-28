extends SceneTree
## Builds the game's UI theme (assets/ui/theme.tres) from the kit pieces cut by
## scripts/tools/build_ui_kit.py and the PixelLab pixel fonts. The project uses it
## as its default theme, so every Control picks it up.
## Run: godot --headless --path . -s scripts/tools/make_theme.gd

const UI := "res://assets/ui/"
const CREAM := Color(0.97, 0.92, 0.8)
const INK := Color(0.24, 0.14, 0.07)
const GOLD := Color(1.0, 0.84, 0.45)
const SHADOW := Color(0.06, 0.04, 0.03)
## Body text size: the 16px pixel fonts at 10 (a little larger than the crisp half
## size, 8, which read too small).
const TEXT_SIZE := 10


func _init() -> void:
	var text_font := _pixel_font("res://assets/fonts/virelia_text.ttf", "res://assets/fonts/virelia_text.tres")
	var title_font := _pixel_font("res://assets/fonts/virelia_title.ttf", "res://assets/fonts/virelia_title.tres")
	var theme := Theme.new()
	theme.default_font = text_font
	theme.default_font_size = TEXT_SIZE

	# Plain labels: cream with a dark outline, so they read over the world.
	theme.set_color(&"font_color", &"Label", CREAM)
	theme.set_color(&"font_outline_color", &"Label", SHADOW)
	theme.set_constant(&"outline_size", &"Label", 3)
	theme.set_constant(&"line_spacing", &"Label", 1)

	# Text on parchment (dialogue, cards): dark ink, no outline.
	theme.set_type_variation(&"InkLabel", &"Label")
	theme.set_color(&"font_color", &"InkLabel", INK)
	theme.set_constant(&"outline_size", &"InkLabel", 0)

	# Titles and names.
	theme.set_type_variation(&"TitleLabel", &"Label")
	theme.set_font(&"font", &"TitleLabel", title_font)
	theme.set_color(&"font_color", &"TitleLabel", GOLD)
	theme.set_font_size(&"font_size", &"TitleLabel", TEXT_SIZE)

	# Windows: the teal kit window with shell corners.
	var window := _box("window.png", 9, 9, 9, 9, 10, 9)
	theme.set_stylebox(&"panel", &"PanelContainer", window)
	theme.set_stylebox(&"panel", &"Panel", window)
	theme.set_type_variation(&"DialoguePanel", &"PanelContainer")
	theme.set_stylebox(&"panel", &"DialoguePanel", _box("dialogue_panel.png", 22, 20, 22, 20, 20, 14))
	theme.set_type_variation(&"NamePlate", &"PanelContainer")
	theme.set_stylebox(&"panel", &"NamePlate", _box("name_plate.png", 12, 10, 12, 10, 10, 2))
	theme.set_type_variation(&"InsetPanel", &"PanelContainer")
	theme.set_stylebox(&"panel", &"InsetPanel", _box("slot.png", 4, 4, 4, 4, 5, 4))

	# Buttons: kit buttons with hover, pressed and disabled looks.
	for state in ["normal", "hover", "pressed", "disabled", "focus"]:
		var file := "button.png" if state in ["normal", "focus"] else "button_%s.png" % state
		theme.set_stylebox(state, &"Button", _box(file, 5, 5, 5, 5, 6, 3))
	theme.set_color(&"font_color", &"Button", CREAM)
	theme.set_color(&"font_hover_color", &"Button", GOLD)
	theme.set_color(&"font_pressed_color", &"Button", GOLD)
	theme.set_color(&"font_disabled_color", &"Button", Color(0.62, 0.62, 0.6))
	theme.set_color(&"font_outline_color", &"Button", SHADOW)
	theme.set_constant(&"outline_size", &"Button", 3)

	# Slim gold scroll bars.
	var grabber := StyleBoxFlat.new()
	grabber.bg_color = Color(0.85, 0.62, 0.3)
	grabber.border_color = SHADOW
	grabber.set_border_width_all(1)
	var track := StyleBoxFlat.new()
	track.bg_color = Color(0.05, 0.16, 0.2, 0.8)
	for bar in [&"VScrollBar", &"HScrollBar"]:
		theme.set_stylebox(&"grabber", bar, grabber)
		theme.set_stylebox(&"grabber_highlight", bar, grabber)
		theme.set_stylebox(&"grabber_pressed", bar, grabber)
		theme.set_stylebox(&"scroll", bar, track)

	var err := ResourceSaver.save(theme, UI + "theme.tres")
	print("theme saved" if err == OK else "theme save failed: %d" % err)
	quit()


func _pixel_font(src: String, out: String) -> FontFile:
	var font := (load(src) as FontFile).duplicate(true) as FontFile
	font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	font.hinting = TextServer.HINTING_NONE
	font.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	font.generate_mipmaps = false
	font.fallbacks = [ThemeDB.fallback_font]   # symbols the pixel font lacks
	ResourceSaver.save(font, out)
	return load(out)


func _box(file: String, l: int, t: int, r: int, b: int, pad_x: int, pad_y: int) -> StyleBoxTexture:
	var box := StyleBoxTexture.new()
	box.texture = load(UI + file)
	box.texture_margin_left = l
	box.texture_margin_top = t
	box.texture_margin_right = r
	box.texture_margin_bottom = b
	box.content_margin_left = pad_x
	box.content_margin_right = pad_x
	box.content_margin_top = pad_y
	box.content_margin_bottom = pad_y
	return box
