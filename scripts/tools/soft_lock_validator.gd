@tool
extends EditorScript
## Run from the Script editor: File > Run (Ctrl+Shift+X) with this file open.
## Headless: godot --headless -s res://scripts/tools/run_soft_lock_check.gd


func _run() -> void:
	SoftLockCheck.print_report(SoftLockCheck.run())
