extends CharacterBody2D
var SPEED = 100.0
func _physics_process(delta):
    var input_dir = Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
    velocity = input_dir * SPEED
    move_and_slide()
    if Input.is_action_just_pressed("ui_accept"):
        velocity = Vector2(0, -SPEED)
