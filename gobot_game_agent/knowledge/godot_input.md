Godot 4 input notes:

- Input.get_axis(negative_action, positive_action) returns -1..1.
  Example: Input.get_axis("ui_left","ui_right")
- Input.get_vector(left,right,up,down) returns a normalized Vector2 for top-down movement.
- Jump commonly uses "ui_accept" by default.