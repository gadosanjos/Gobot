Godot 4 .tscn basics:

- .tscn starts with: [gd_scene load_steps=... format=3]
- Resource paths inside .tscn use res://...
- Attaching scripts uses ext_resource:
  [ext_resource type="Script" path="res://scripts/Player.gd" id="1"]
  script = ExtResource("1")
- Instancing another scene uses PackedScene ext_resource:
  [ext_resource type="PackedScene" path="res://scenes/Player.tscn" id="1"]
  [node name="Player" parent="." instance=ExtResource("1")]