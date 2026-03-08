extends CharacterBody2D
var SPEED = 100.0
func _physics_process(delta):
	var input_dir = Input.get_axis("ui_left", "ui_right")
	velocity.x = input_dir * SPEED
	move_and_slide()
