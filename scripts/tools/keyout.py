"""Make a map object's flat background transparent: flood fill from the border
through pixels close to the corner colour, then trim to the opaque bounding box."""
import sys
from collections import deque
from PIL import Image

def keyout(path, tol=22):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    px = im.load()
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    bg = max(set(corners), key=corners.count)
    close = lambda p: p[3] == 0 or sum(abs(p[i] - bg[i]) for i in range(3)) <= tol
    seen = bytearray(w * h)
    q = deque((x, y) for x in range(w) for y in (0, h - 1)) + deque((x, y) for y in range(h) for x in (0, w - 1)) if False else deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or seen[y * w + x]:
            continue
        seen[y * w + x] = 1
        if not close(px[x, y]):
            continue
        px[x, y] = (0, 0, 0, 0)
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    im.save(path)
    return im.getbbox()

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p.rsplit("/", 1)[-1], keyout(p))
