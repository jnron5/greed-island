extends SceneTree
## Headless runner for CI: exits 1 if any card can soft-lock the race.


func _init() -> void:
	var result := SoftLockCheck.run()
	SoftLockCheck.print_report(result)
	quit(0 if result.errors.is_empty() else 1)
