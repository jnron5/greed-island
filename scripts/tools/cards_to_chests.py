"""Cards aren't left lying on the ground: turn a scene's placed CardPickup nodes into
chests that hold those cards (scripts/systems/chest.gd), at the same spots and behind
the same gates. Anyone who opens a chest first (player or rival) takes the card.

Usage: python scripts/tools/cards_to_chests.py scenes/world/<zone>.tscn ...
Builders that write scenes themselves call chest_node() directly.
"""
import os
import re
import sys

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

CHEST_EXT = [
    ('Script', "res://scripts/systems/chest.gd", "70_chest"),
    ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest.png", "70_chest_shut"),
    ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest_open.png", "70_chest_open"),
]
SHAPE = '[sub_resource type="RectangleShape2D" id="ChestBase"]\nsize = Vector2(30, 10)\n'


def chest_node(name, x, y, card, gate="", hint="", gold=0, zone="", ids=("70_chest", "70_chest_shut", "70_chest_open")):
    script, shut, opened = ids
    hint = hint.replace('"', '\\"')
    return (f'[node name="{name}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n'
            f'script = ExtResource("{script}")\nchest_id = &"{zone}_{name.lower()}"\ncard_id = &"{card}"\ngold = {gold}\n'
            f'hint = "{hint}"\n' + (f'behind_gate = &"{gate}"\n' if gate else "")
            + f'closed_texture = ExtResource("{shut}")\nopen_texture = ExtResource("{opened}")\n\n'
            f'[node name="Base" type="CollisionShape2D" parent="{name}"]\nposition = Vector2(0, -5)\n'
            f'shape = SubResource("ChestBase")\n')


def ensure_resources(scene):
    """Adds the chest's ext resources and base shape to a scene text if missing."""
    for kind, path, rid in CHEST_EXT:
        if path not in scene:
            last = [m.end() for m in re.finditer(r'\[ext_resource [^\n]*\]\n', scene)][-1]
            scene = scene[:last] + f'[ext_resource type="{kind}" path="{path}" id="{rid}"]\n' + scene[last:]
    if 'id="ChestBase"' not in scene:
        scene = scene.replace("\n\n[node name=", "\n\n" + SHAPE + "\n[node name=", 1)
    return scene


def resource_id(scene, path):
    return re.search(r'path="%s" id="([^"]+)"' % re.escape(path), scene).group(1)


def convert(path):
    scene = open(path, encoding="utf-8").read()
    m = re.search(r'path="res://scenes/systems/card_pickup.tscn" id="([^"]+)"', scene)
    if not m:
        print(f"{path}: no card pickups")
        return
    pick = m.group(1)
    scene = ensure_resources(scene)
    ids = tuple(resource_id(scene, p) for _, p, _ in CHEST_EXT)
    zone = os.path.basename(path)[:-5]
    count = 0

    def repl(node):
        nonlocal count
        count += 1
        body = node.group(2)
        pos = re.search(r'position = Vector2\((-?[\d.]+), (-?[\d.]+)\)', body)
        card = re.search(r'card_id = &"([^"]+)"', body).group(1)
        gate = re.search(r'behind_gate = &"([^"]+)"', body)
        return chest_node(node.group(1), pos.group(1), pos.group(2), card, gate.group(1) if gate else "", zone=zone, ids=ids) + "\n"
    scene = re.sub(r'\[node name="([^"]+)" parent="\." instance=ExtResource\("%s"\)\]\n((?:(?!\[node )[^\n]*\n)*)' % re.escape(pick),
                   repl, scene)
    # The pickup scene is no longer placed here.
    if f'ExtResource("{pick}")' not in scene:
        scene = re.sub(r'\[ext_resource [^\n]*id="%s"\]\n' % re.escape(pick), "", scene)
    open(path, "w", encoding="utf-8", newline="\n").write(scene)
    print(f"{path}: {count} cards now in chests")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        convert(p)
