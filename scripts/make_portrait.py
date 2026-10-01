"""Convert Bayram's GitHub photograph into a fixed-width ASCII source file.

Optional authoring tool (Pillow required); daily refreshes use portrait-*.txt.
Usage: python scripts/make_portrait.py /path/to/github-avatar.jpg
"""

import sys
from pathlib import Path
from PIL import Image, ImageOps

# The full figure visible in the 460px avatar. The precise hair/ear outline
# excludes the background without changing the head's natural proportions.
OUTLINE = [(205,135.5),(197,137),(189,140),(184,145),(181,150),
           (180,157),(180.5,168),(181.5,177),(179,178.5),(178.5,183),
           (179.5,188),(181.5,192),(184,195),(185.5,197),
           (186.5,205),(189,212),(190,218),(184,225),(174,229),(147,240),
           (142,248),(140,270),(139,294),(134,314),(130,326),
           (132,344),(131,366),(133,386),(136,409),(139,419),
           (145,421),(151,439),(159,460),(273,460),(275,441),
           (283,429),(290,417),(294,402),(296,383),(298,365),
           (299,346),(297,333),(296,319),(292,305),(291,286),
           (287,269),(286,249),(279,239),(261,233),(240,227),
           (229,223),(226.5,217),(227,212),(230,203),
           (232,196),(234.5,194),(236,190),(236.5,184),
           (235.5,179),(234,176),(234,166),(232,156),(230,149),
           (226,143),(219,139),(212,137)]
HOLES = [
    [(158,321),(162,326),(165,339),(164,353),(159,369),(155,379),(155,365),(158,344)],
    [(267,329),(272,330),(274,349),(272,366),(269,362)],
]
CROP = (124, 131, 306, 460)
COLUMNS = 76
# Match the renderer's cell width and row height; avoid stretching the face.
ROWS = round(COLUMNS * (CROP[3] - CROP[1]) / (CROP[2] - CROP[0]) * 4.05 / 6.94)


def inside(x, y, polygon=OUTLINE):
    result = False
    previous = polygon[-1]
    for current in polygon:
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
            if (not all(inside(sx+dx, sy+dy) for dx, dy in ((0,0),(-.35,0),(.35,0),(0,-.35),(0,.35)))
                    or any(inside(sx, sy, hole) for hole in HOLES)):
                row.append(" ")
                continue
            luminance = (photo.getpixel((x,y))/255)**.8
            density = luminance if theme == "dark" else 1-luminance
            row.append(ramp[min(len(ramp)-1, int(density*(len(ramp)-1)))])
        rows.append("".join(row).rstrip())
    target = Path(__file__).resolve().parents[1] / "assets" / f"portrait-{theme}.txt"
    target.write_text("\n".join(rows).rstrip() + "\n")
    print(f"Wrote {photo.width} × {photo.height} {theme} text portrait")
