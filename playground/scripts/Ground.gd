extends Node2D
func _ready():
    var collision = CollisionShape2D.new()
    add_child(collision)
