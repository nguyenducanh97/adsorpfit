# -*- coding: utf-8 -*-
"""Rebuild css/marks.css from the PNGs in assets/.

Generates a light variant of each mark for the dark theme, then inlines both
variants as data URIs behind a --img-<name> custom property. Run from the
project root:  python tools/make_marks.py
"""
import base64, colorsys, io, os
from PIL import Image

NAMES = [("swat", "196 / 53"), ("skku", "199 / 48"), ("utop", "130 / 48")]


def make_light(src, dst):
    """Lift dark ink to a readable light tone, leave brand colours alone."""
    im = Image.open(src).convert("RGBA")
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            hh, ll, ss = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
            if ss < 0.22:                       # neutral ink
                nl = 0.97 - ll * 0.42
            else:                               # brand colour
                nl = ll if ll > 0.62 else 0.62 + (ll / 0.62) * 0.18
            nr, ng, nb = colorsys.hls_to_rgb(hh, min(1.0, nl), ss)
            px[x, y] = (int(nr * 255), int(ng * 255), int(nb * 255), a)
    im.save(dst)


def uri(path):
    return "url(data:image/png;base64,%s)" % base64.b64encode(
        io.open(path, "rb").read()).decode("ascii")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    for n, _ in NAMES:
        make_light("assets/%s.png" % n, "assets/%s-light.png" % n)
    lines = [":root {"]
    lines += ["  --img-%s: %s;" % (n, uri("assets/%s.png" % n)) for n, _ in NAMES]
    lines += ["}", "", ':root[data-theme="dark"] {']
    lines += ["  --img-%s: %s;" % (n, uri("assets/%s-light.png" % n)) for n, _ in NAMES]
    lines += ["}", "", ".mark {",
              "  display: block; background-repeat: no-repeat;",
              "  background-position: center; background-size: contain;",
              "  background-color: transparent;", "}"]
    lines += [".mark-%s { background-image: var(--img-%s); aspect-ratio: %s; }"
              % (n, n, r) for n, r in NAMES]
    io.open("css/marks.css", "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("css/marks.css rebuilt")


if __name__ == "__main__":
    main()
