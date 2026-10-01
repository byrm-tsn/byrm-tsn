"""Convert Bayram's GitHub photograph into a fixed-width ASCII source file.

Optional authoring tool (Pillow required); daily refreshes use portrait-*.txt.
Usage: python scripts/make_portrait.py /path/to/github-avatar.jpg
"""

import sys
from pathlib import Path
from PIL import Image, ImageOps

# Hair, ears, and jaw traced on the original 460px public avatar. The previous
# bust outline admitted bright background beside the head; no neck or clothing
# belongs in this head-only portrait.
OUTLINE = [(205,135.5),(197,137),(189,140),(184,145),(181,150),
           (180,157),(180.5,168),(181.5,177),(179,178.5),(178.5,183),
           (179.5,188),(181.5,192),(184,195),(185.5,197),
           (186.5,202),(189,207),(193,212),(199,216),(205,218),
           (211,218),(217,215.5),(223,212),(227,208),(230,203),
           (232,196),(234.5,194),(236,190),(236.5,184),
           (235.5,179),(234,176),(234,166),(232,156),(230,149),
           (226,143),(219,139),(212,137)]
CROP = (175, 131, 241, 222)
COLUMNS = 76
# Match the renderer's cell width and row height; avoid stretching the face.
ROWS = round(COLUMNS * (CROP[3] - CROP[1]) / (CROP[2] - CROP[0]) * 4.05 / 6.94)


def inside(x, y):
    result = False
    previous = OUTLINE[-1]
    for current in OUTLINE:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > y) != (y2 > y) and x < (x2-x1)*(y-y1)/(y2-y1)+x1:
            result = not result
        previous = current
    return result


photo = Image.open(sys.argv[1]).convert("L")
w, h = photo.size
photo = photo.crop((round(w * CROP[0]/460), round(h * CROP[1]/460),
                    round(w * CROP[2]/460), round(h * CROP[3]/460)))
photo = ImageOps.autocontrast(photo, cutoff=1).resize((COLUMNS, ROWS), Image.Resampling.LANCZOS)
ramp = " .,:;irsXA253hMHGS#9B&@"
for theme in ("dark", "light"):
    rows = []
    for y in range(photo.height):
        row = []
        for x in range(photo.width):
            sx = CROP[0] + (x+.5) * (CROP[2]-CROP[0]) / COLUMNS
            sy = CROP[1] + (y+.5) * (CROP[3]-CROP[1]) / ROWS
            # Keep samples just inside the edge, removing the pale background halo.
            if not all(inside(sx+dx, sy+dy) for dx, dy in ((0,0),(-.35,0),(.35,0),(0,-.35),(0,.35))):
                row.append(" ")
                continue
            luminance = (photo.getpixel((x,y))/255)**.8
            density = luminance if theme == "dark" else 1-luminance
            row.append(ramp[min(len(ramp)-1, int(density*(len(ramp)-1)))])
        rows.append("".join(row).rstrip())
    target = Path(__file__).resolve().parents[1] / "assets" / f"portrait-{theme}.txt"
    target.write_text("\n".join(rows).rstrip() + "\n")
    print(f"Wrote {photo.width} × {photo.height} {theme} text portrait")
