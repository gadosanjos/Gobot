extends CharacterBody2D
var velocity = Vector2.ZERO
func _physics_process(delta: float) -> void:
    velocity = Input.get_vector('ui_left', 'ui_right', 'ui_up', 'ui_down').normalized() * 100
    move_and_slide()
