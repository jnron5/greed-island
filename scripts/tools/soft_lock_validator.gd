@tool
extends EditorScript
## Run from the Script editor: File > Run (Ctrl+Shift+X) with this file open.
## Headless: godot --headless --path . res://scripts/tools/run_soft_lock_check.tscn


func _run() -> void:
	SoftLockCheck.print_report(SoftLockCheck.run())
