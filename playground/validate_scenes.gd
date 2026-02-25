extends SceneTree

func _init() -> void:
	var paths = [
		"res://scenes/Player.tscn",
		"res://scenes/Level.tscn",
	]

	for p in paths:
		var res = ResourceLoader.load(p)
		if res == null:
			push_error("FAILED_TO_LOAD: " + p)
			quit(2)
			return

	print("OK: all scenes loaded")
	quit(0)
