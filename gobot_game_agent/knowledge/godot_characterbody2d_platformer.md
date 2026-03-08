Godot 4 CharacterBody2D platformer essentials:

- Use the built-in 'velocity' property (Vector2).
- In _physics_process(delta):
  - Horizontal: velocity.x = Input.get_axis("ui_left","ui_right") * SPEED
  - Gravity: if not is_on_floor(): velocity.y += GRAVITY * delta
  - Jump: if is_on_floor() and Input.is_action_just_pressed("ui_accept"): velocity.y = JUMP_VELOCITY
  - Call move_and_slide() with no args.
- Functions in GDScript must start with 'func'.