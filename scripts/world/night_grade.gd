class_name NightGrade
extends CanvasLayer
## The night colour grade for an outdoor zone (assets/shaders/night_grade.gdshader),
## on a layer above the world and below the HUD. Follows TimeOfDay.night_factor().

const SHADER := preload("res://assets/shaders/night_grade.gdshader")

var _mat: ShaderMaterial
var _rect: ColorRect


func _ready() -> void:
	layer = 1
	_rect = ColorRect.new()
	_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mat = ShaderMaterial.new()
	_mat.shader = SHADER
	_rect.material = _mat
	add_child(_rect)


func _process(_delta: float) -> void:
	var night := TimeOfDay.night_factor()
	_rect.visible = night > 0.01
	_mat.set_shader_parameter(&"night", night)
