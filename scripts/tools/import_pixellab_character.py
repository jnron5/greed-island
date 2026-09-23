"""Turn a PixelLab character download (zip) into Godot sprite sheets + SpriteFrames.

Usage: python scripts/tools/import_pixellab_character.py <zip> <out_dir res-relative> <name> [fps...]
  e.g. python scripts/tools/import_pixellab_character.py player.zip assets/sprites/player player idle=5 run=12

Each animation becomes <name>_<anim>.png: one row per direction (DIRS order), one column per frame.
Directions that weren't generated (4-direction monsters, partial batches) are left out.
Missing idle animations fall back to the still rotations. The SpriteFrames .tres names animations "<anim>_<direction>" (e.g. run_south_east), which is
what scripts/characters/player.gd plays. Frames are cropped to a shared box so feet line up.
"""
import io, sys, zipfile, os
from PIL import Image

DIRS = ["south", "south-east", "east", "north-east", "north", "north-west", "west", "south-west"]
# One-shot actions play once instead of looping.
ONE_SHOT = {"attack", "sword", "pistol"}

def main():
    zpath, out_dir, name = sys.argv[1], sys.argv[2], sys.argv[3]
    fps = {k: float(v) for k, v in (a.split("=") for a in sys.argv[4:])}
    z = zipfile.ZipFile(zpath)
    names = [n for n in z.namelist() if n.endswith(".png")]
    anims = sorted({n.split("/")[2] for n in names if "/animations/" in n})

    frames = {}  # anim -> dir -> [Image]
    for anim in anims:
        frames[anim] = {}
        for d in DIRS:
            files = sorted(n for n in names if f"/animations/{anim}/{d}/" in n)
            if not files:
                continue  # Direction not generated (yet): the game falls back to another animation.
            frames[anim][d] = [Image.open(io.BytesIO(z.read(f))).convert("RGBA") for f in files]
    if "idle" not in frames:
        # No idle animation generated: use the still rotations as 1-frame idles.
        frames["idle"] = {d: [Image.open(io.BytesIO(z.read(r))).convert("RGBA")]
                          for d in DIRS
                          for r in [next((n for n in names if n.endswith(f"/rotations/{d}.png")), None)] if r}
        anims = sorted(frames)

    # Shared crop box across every frame, padded by 1px, so all cells are identical in size.
    boxes = [im.getbbox() for a in frames.values() for fs in a.values() for im in fs if im.getbbox()]
    l = max(min(b[0] for b in boxes) - 1, 0); t = max(min(b[1] for b in boxes) - 1, 0)
    r = max(b[2] for b in boxes) + 1; btm = max(b[3] for b in boxes) + 1
    cw, ch = r - l, btm - t
    feet_y = max(b[3] for b in boxes) - t  # baseline inside a cell

    os.makedirs(out_dir, exist_ok=True)
    ext, subs, anim_entries = [], [], []
    for ai, anim in enumerate(anims):
        n = max(len(fs) for fs in frames[anim].values())
        sheet = Image.new("RGBA", (cw * n, ch * len(DIRS)))
        for row, d in enumerate(DIRS):
            for col, im in enumerate(frames[anim].get(d, [])):
                sheet.paste(im.crop((l, t, r, btm)), (col * cw, row * ch))
        png = f"{name}_{anim}.png"
        sheet.save(os.path.join(out_dir, png))
        ext_id = f"{ai + 1}_{anim}"
        ext.append(f'[ext_resource type="Texture2D" path="res://{out_dir}/{png}" id="{ext_id}"]')
        for row, d in enumerate(DIRS):
            if d not in frames[anim]:
                continue
            refs = []
            for col in range(len(frames[anim][d])):
                sid = f"Atlas_{anim}_{d.replace('-', '_')}_{col}"
                subs.append(f'[sub_resource type="AtlasTexture" id="{sid}"]\natlas = ExtResource("{ext_id}")\n'
                            f'region = Rect2({col * cw}, {row * ch}, {cw}, {ch})\n')
                refs.append(f'{{\n"duration": 1.0,\n"texture": SubResource("{sid}")\n}}')
            anim_entries.append(f'{{\n"frames": [{", ".join(refs)}],\n"loop": {"false" if anim in ONE_SHOT else "true"},\n'
                                f'"name": &"{anim}_{d.replace("-", "_")}",\n"speed": {fps.get(anim, 8.0)}\n}}')

    tres = [f'[gd_resource type="SpriteFrames" format=3]\n', *ext, "", *subs,
            "[resource]", f'animations = [{", ".join(anim_entries)}]', ""]
    open(os.path.join(out_dir, f"{name}_frames.tres"), "w", newline="\n").write("\n".join(tres))
    print(f"{len(anims)} anims {anims}, cell {cw}x{ch}, feet at y={feet_y} (offset.y = {ch / 2 - feet_y:+.0f})")

main()
