"""Write an animated prop scene from a horizontal strip of equal frames: the
frames' opaque bottom sits on the node origin and a rectangular footprint
collides at the base (like make_prop.py, but with an AnimatedSprite2D).

Usage: python scripts/tools/make_animated_prop.py <name> <strip res path> <frames> <fps> <footprint w> <footprint h>
Writes scenes/world/props/<name>.tscn.
"""
import os
import sys

from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))


def make_animated_prop(name: str, strip: str, frames: int, fps: float, fw: int, fh: int) -> None:
    im = Image.open(strip.replace("res://", "")).convert("RGBA")
    w, h = im.width // frames, im.height
    bottom = max(im.crop((k * w, 0, (k + 1) * w, h)).getbbox()[3] for k in range(frames))
    node = "".join(part.title() for part in name.split("_"))
    atlases = "".join(f'[sub_resource type="AtlasTexture" id="Frame{k}"]\natlas = ExtResource("1_tex")\n'
                      f'region = Rect2({k * w}, 0, {w}, {h})\n\n' for k in range(frames))
    refs = ", ".join(f'{{\n"duration": 1.0,\n"texture": SubResource("Frame{k}")\n}}' for k in range(frames))
    open(f"scenes/world/props/{name}.tscn", "w", newline="\n").write(f'''[gd_scene load_steps={frames + 4} format=3]

[ext_resource type="Texture2D" path="{strip}" id="1_tex"]

{atlases}[sub_resource type="SpriteFrames" id="SpriteFrames_anim"]
animations = [{{
"frames": [{refs}],
"loop": true,
"name": &"default",
"speed": {fps}
}}]

[sub_resource type="RectangleShape2D" id="RectangleShape2D_base"]
size = Vector2({fw}, {fh})

[node name="{node}" type="StaticBody2D"]

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
position = Vector2(0, {h / 2 - bottom})
sprite_frames = SubResource("SpriteFrames_anim")
autoplay = "default"

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
position = Vector2(0, {-fh / 2 - 4})
shape = SubResource("RectangleShape2D_base")
''')


if __name__ == "__main__":
    make_animated_prop(sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))
