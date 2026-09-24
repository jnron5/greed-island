extends Node
## Headless runner for CI: exits 1 if any card can soft-lock the race.
## Run: godot --headless --path . res://scripts/tools/run_soft_lock_check.tscn
## (A scene rather than a -s script so the autoloads the zone scan needs exist.)


func _ready() -> void:
	var result := SoftLockCheck.run()
	SoftLockCheck.print_report(result)
	get_tree().quit(0 if result.errors.is_empty() else 1)
