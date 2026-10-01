"""Convert Bayram's supplied portrait into a fixed-width ASCII source file.

Optional authoring tool (Pillow, NumPy and OpenCV); daily refreshes use saved data.
Usage: python scripts/make_portrait.py /path/to/IMG_0677.jpg
"""

import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageOps

# Coordinates fitted to the 1262 x 1575 IMG_0677 photograph. Retain the
# complete visible bust and follow the hair, ears, jaw and shirt silhouette.
REFERENCE_SIZE = (1262, 1575)
OUTLINE = [
    (309,576),(302,558),(299,536),(300,507),(311,476),
    (329,450),(352,433),(386,417),(423,412),(450,400),
    (478,384),(501,385),(519,376),(542,383),(568,379),
    (594,384),(616,383),(638,386),(661,396),(690,403),
    (714,420),(743,437),(766,461),(772,487),(789,510),
    (809,533),(818,551),(819,569),(830,598),(833,627),
    (836,652),(833,685),(833,713),(833,744),(830,773),
    (839,770),(848,779),(856,800),(860,825),(862,850),
    (858,879),(858,906),(860,931),(852,946),(840,952),
    (831,952),(816,950),(811,973),(809,1000),(803,1033),
    (798,1060),(797,1115),(812,1142),(839,1174),
    (872,1198),(909,1214),(934,1221),(953,1233),
    (971,1241),(990,1247),(1007,1261),(1020,1263),
    (1039,1277),(1054,1292),(1079,1308),(1103,1318),
    (1136,1321),(1164,1333),(1200,1344),(1238,1351),
    (1262,1371),(1262,1575),(0,1575),(0,1480),
    (25,1447),(45,1414),(73,1380),(100,1347),
    (133,1322),(207,1294),(276,1270),(343,1243),
    (384,1224),(409,1210),(406,1197),(382,1170),
    (363,1140),(347,1104),(338,1071),(329,1038),
    (323,1009),(319,982),(315,969),(314,951),
    (317,933),(313,904),(314,854),(311,812),
    (309,778),(308,740),(306,714),(300,682),
    (298,646),(287,623),(288,601),
]
CROP = (0, 360, 1262, 1575)
COLUMNS = 80
# Match the renderer's cell width and row height; avoid stretching the face.
ROWS = round(COLUMNS * (CROP[3] - CROP[1]) / (CROP[2] - CROP[0]) * 4.05 / 7.8)


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
# Smooth small skin textures before local contrast so character shapes carry
# the facial structure instead of turning the beard and hair into fine noise.
gray = np.asarray(photo)
gray = cv2.bilateralFilter(gray, 9, 35, 25)
local = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(gray)
detail = cv2.addWeighted(gray, .55, local, .45, 0)
detail = cv2.addWeighted(detail, 1.4, cv2.GaussianBlur(detail, (0, 0), 4), -.4, 0)
photo = Image.fromarray(detail)
# Average only subject pixels within each character cell. Resizing the full
# photograph first would mix bright background pixels into edge characters.
samples = ImageChops.multiply(photo, mask).resize((COLUMNS, ROWS), Image.Resampling.BOX)
coverage = mask.resize((COLUMNS, ROWS), Image.Resampling.BOX)
rows = []
ramp = " .,:;-=+*#%@"
for y in range(ROWS):
    row = []
    for x in range(COLUMNS):
        sx = CROP[0] + (x+.5) * (CROP[2]-CROP[0]) / COLUMNS
        sy = CROP[1] + (y+.5) * (CROP[3]-CROP[1]) / ROWS
        alpha = coverage.getpixel((x,y))
        if alpha < 153 or not all(inside(sx+dx, sy+dy) for dx, dy in ((0,0),(-2,0),(2,0),(0,-2),(0,2))):
            row.append(" ")
        else:
            luminance = min(1, samples.getpixel((x,y))/alpha)
            # Use the same printed-shadow direction in both themes. Dark
            # features get dense symbols; highlights are punctuation or space.
            density = 1 - luminance**1.55
            row.append(ramp[min(len(ramp)-1, int(density * len(ramp)))])
    rows.append("".join(row).rstrip())
assets = Path(__file__).resolve().parents[1] / "assets"
for theme in ("dark", "light"):
    target = assets / f"portrait-{theme}.txt"
    target.write_text("\n".join(rows).rstrip() + "\n")
    print(f"Wrote {COLUMNS} × {ROWS} {theme} text portrait")
