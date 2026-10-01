"""Convert Bayram's GitHub photograph into a fixed-width ASCII source file.

Optional authoring tool (Pillow required); daily refreshes use portrait.txt.
Usage: python scripts/make_portrait.py /path/to/github-avatar.jpg
"""

import sys
from pathlib import Path
from PIL import Image, ImageOps

# Outline measured on the 460px public avatar. It leaves background cells blank
# while retaining the original photographic luminance inside the silhouette.
OUTLINE = [(180,153),(189,138),(205,133),(221,137),(232,145),(237,163),
           (242,169),(239,192),(231,207),(227,220),(252,230),(279,237),
           (289,253),(296,287),(298,335),(304,367),(313,440),(132,440),
           (134,387),(128,354),(134,293),(141,259),(151,239),(184,224),
           (185,213),(175,196),(174,178)]


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
photo = photo.crop((int(w * 123/460), int(h * 125/460), int(w * 302/460), int(h * 345/460)))
photo = ImageOps.autocontrast(photo, cutoff=1).resize((76, 54), Image.Resampling.LANCZOS)
ramp = " .,:;irsXA253hMHGS#9B&@"
for theme in ("dark", "light"):
    rows = []
    for y in range(photo.height):
        row = []
        for x in range(photo.width):
            if not inside(123 + (x+.5)*179/76, 125 + (y+.5)*220/54):
                row.append(" ")
                continue
            luminance = (photo.getpixel((x,y))/255)**.8
            density = luminance if theme == "dark" else 1-luminance
            row.append(ramp[min(len(ramp)-1, int(density*(len(ramp)-1)))])
        rows.append("".join(row).rstrip())
    target = Path(__file__).resolve().parents[1] / "assets" / f"portrait-{theme}.txt"
    target.write_text("\n".join(rows) + "\n")
    print(f"Wrote {photo.width} × {photo.height} {theme} text portrait")
