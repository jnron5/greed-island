"""Write a static prop scene for a sprite: its opaque bottom sits on the node
origin and a rectangular footprint collides at the base.

Usage: python scripts/tools/make_prop.py <name> <texture res path> <footprint w> <footprint h>
Writes scenes/world/props/<name>.tscn.
"""
import os
import sys

from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))


def make_prop(name: str, texture: str, fw: int, fh: int) -> None:
    im = Image.open(texture.replace("res://", "")).convert("RGBA")
    w, h = im.size
    bottom = im.getbbox()[3]
    node = "".join(part.title() for part in name.split("_"))
    open(f"scenes/world/props/{name}.tscn", "w", newline="\n").write(f'''[gd_scene load_steps=3 format=3]

[ext_resource type="Texture2D" path="{texture}" id="1_tex"]

[sub_resource type="RectangleShape2D" id="RectangleShape2D_base"]
size = Vector2({fw}, {fh})

[node name="{node}" type="StaticBody2D"]

[node name="Sprite2D" type="Sprite2D" parent="."]
position = Vector2(0, {h / 2 - bottom})
texture = ExtResource("1_tex")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
position = Vector2(0, {-fh / 2})
shape = SubResource("RectangleShape2D_base")
''')


if __name__ == "__main__":
    make_prop(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
