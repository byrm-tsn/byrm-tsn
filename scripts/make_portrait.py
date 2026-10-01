"""Convert Bayram's supplied portrait into a fixed-width ASCII source file.

Optional authoring tool (Pillow required); daily refreshes use portrait-*.txt.
Usage: python scripts/make_portrait.py /path/to/IMG_0899.png
"""

import sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageOps

# Coordinates fitted to the upright IMG_0899 portrait, expressed in its
# 1342 x 1856 preview space. Keep the upper body, scarf, coat and sunglasses;
# follow the solid hair silhouette rather than including bright sky flyaways.
REFERENCE_SIZE = (1342, 1856)
OUTLINE = [
    (627,645),(623,618),(624,590),(631,561),(642,538),
    (648,526),(660,512),(666,496),(682,490),(699,482),
    (716,480),(733,476),(754,479),(772,474),(789,481),
    (806,479),(824,484),(841,492),(849,500),(865,506),
    (873,520),(882,536),(884,554),(888,565),(887,576),
    (897,596),(902,621),(902,645),(905,663),(930,673),
    (945,679),(944,687),(940,697),(932,719),(926,733),
    (918,741),(899,745),(897,777),(892,798),(883,819),
    (879,835),(909,855),(939,877),(970,900),(982,911),
    (1023,925),(1048,939),(1078,961),(1096,983),
    (1109,1017),(1122,1053),(1136,1092),(1149,1135),
    (1162,1180),(1175,1228),(1186,1269),(1206,1304),
    (1222,1334),(1235,1378),(1239,1414),(1250,1450),
    (1254,1479),(1250,1503),(1258,1525),(1262,1564),
    (1262,1605),(1259,1637),(1259,1675),(1251,1712),
    (1258,1747),(1250,1778),(1256,1810),(1249,1840),
    (1246,1856),(505,1856),(481,1825),(470,1793),
    (458,1771),(434,1738),(425,1702),(409,1677),
    (393,1639),(375,1604),(361,1566),(348,1520),
    (342,1487),(337,1460),(339,1429),(351,1394),
    (357,1342),(367,1270),(375,1219),(389,1154),
    (396,1116),(406,1075),(416,1044),(439,1015),
    (467,992),(496,972),(520,949),(549,931),(576,889),
    (602,854),(617,828),(625,813),(645,804),(657,800),
    (655,776),(653,753),(640,752),(630,745),(625,733),
    (621,720),(618,706),(617,692),(621,678),(620,666),
    (628,658),(631,658),
]
CROP = (326, 455, 1274, 1856)
COLUMNS = 96
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


photo = ImageOps.exif_transpose(Image.open(sys.argv[1])).convert("L")
w, h = photo.size
bounds = (round(w * CROP[0]/REFERENCE_SIZE[0]), round(h * CROP[1]/REFERENCE_SIZE[1]),
          round(w * CROP[2]/REFERENCE_SIZE[0]), round(h * CROP[3]/REFERENCE_SIZE[1]))
photo = photo.crop(bounds)
mask = Image.new("L", photo.size, 0)
ImageDraw.Draw(mask).polygon([(x*w/REFERENCE_SIZE[0]-bounds[0], y*h/REFERENCE_SIZE[1]-bounds[1])
                             for x, y in OUTLINE], fill=255)
photo = ImageOps.autocontrast(photo, cutoff=1, mask=mask)
# Average only subject pixels within each character cell. Resizing the full
# photograph first would mix bright background pixels into edge characters.
samples = ImageChops.multiply(photo, mask).resize((COLUMNS, ROWS), Image.Resampling.BOX)
coverage = mask.resize((COLUMNS, ROWS), Image.Resampling.BOX)
ramp = " .,:;irsXA253hMHGS#9B&@"
for theme in ("dark", "light"):
    rows = []
    for y in range(ROWS):
        row = []
        for x in range(COLUMNS):
            sx = CROP[0] + (x+.5) * (CROP[2]-CROP[0]) / COLUMNS
            sy = CROP[1] + (y+.5) * (CROP[3]-CROP[1]) / ROWS
            # Keep samples just inside the edge, removing the pale background halo.
            alpha = coverage.getpixel((x,y))
            if alpha < 153 or not all(inside(sx+dx, sy+dy) for dx, dy in ((0,0),(-2,0),(2,0),(0,-2),(0,2))):
                row.append(" ")
                continue
            luminance = min(1, samples.getpixel((x,y))/alpha)**.8
            density = luminance if theme == "dark" else 1-luminance
            row.append(ramp[min(len(ramp)-1, int(density*(len(ramp)-1)))])
        rows.append("".join(row).rstrip())
    target = Path(__file__).resolve().parents[1] / "assets" / f"portrait-{theme}.txt"
    target.write_text("\n".join(rows).rstrip() + "\n")
    print(f"Wrote {COLUMNS} × {ROWS} {theme} text portrait")
