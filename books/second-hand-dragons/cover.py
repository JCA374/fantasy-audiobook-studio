"""Cover for "Second-Hand Dragons": a small curled dragon in a coal scuttle, one candle flame, snow at night.

    python3 cover.py cover.jpg

Pure PIL + numpy, like the other covers.
"""
import math
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 2400
OUT = sys.argv[1] if len(sys.argv) > 1 else "cover.jpg"
FONT = "/usr/share/fonts/truetype/noto/NotoSerif-"
random.seed(11)

CX, CY = W // 2, 1560          # scuttle centre
FLAME = (CX + 330, 1250)       # candle flame


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


# ---------------------------------------------------------------- night sky, cold blue
yy, xx = np.mgrid[0:H, 0:W].astype(float)
t = yy / H
base = np.stack([14 + 10 * t, 20 + 14 * t, 38 + 18 * t], axis=-1)
# warm glow round the flame, fading into the cold
r = np.hypot(xx - FLAME[0], yy - FLAME[1])
glow = np.exp(-(r / 620) ** 2)[..., None]
warm = np.array([235, 150, 70])
img = Image.fromarray((base * (1 - glow * 0.85) + warm * glow * 0.85).clip(0, 255).astype(np.uint8)).convert("RGBA")

# ---------------------------------------------------------------- floorboards
d = ImageDraw.Draw(img)
for i in range(9):
    y0 = 1790 + i * 70
    shade = 28 + i * 3
    d.rectangle([0, y0, W, y0 + 66], fill=(shade + 10, shade, shade - 6, 255))

# ---------------------------------------------------------------- coal scuttle (iron bucket with a lip and handle)
sc = layer()
s = ImageDraw.Draw(sc)
s.polygon([(CX - 430, CY - 150), (CX + 300, CY - 230), (CX + 360, CY + 260), (CX - 380, CY + 260)], fill=(34, 32, 36, 255))
s.ellipse([CX - 450, CY - 260, CX + 330, CY - 110], fill=(48, 44, 48, 255))
s.ellipse([CX - 420, CY - 240, CX + 300, CY - 135], fill=(18, 16, 18, 255))
s.arc([CX - 380, CY - 520, CX + 260, CY - 60], 200, 340, fill=(60, 56, 58, 255), width=26)
img.alpha_composite(sc)

# ---------------------------------------------------------------- the dragon: a coil of old-penny scales
dr = layer()
g = ImageDraw.Draw(dr)
copper = (150, 92, 52, 255)
# body: a ring of overlapping scales round the scuttle mouth
for k in range(70):
    a = math.radians(200 + k * 4.4)
    rx, ry = 300 - k * 1.6, 70 - k * 0.3
    x, y = CX - 60 + rx * math.cos(a), CY - 215 + ry * math.sin(a)
    rad = 46 - k * 0.45
    tone = 0.75 + 0.25 * math.sin(k * 0.9)
    g.ellipse([x - rad, y - rad * 0.8, x + rad, y + rad * 0.8],
              fill=(int(copper[0] * tone), int(copper[1] * tone), int(copper[2] * tone), 255))
# head resting on the rim, turned towards the flame
hx, hy = CX + 170, CY - 300
g.ellipse([hx - 130, hy - 85, hx + 120, hy + 75], fill=(150, 92, 54, 255))
g.polygon([(hx + 70, hy - 50), (hx + 270, hy - 5), (hx + 250, hy + 30), (hx + 70, hy + 60)], fill=(150, 92, 54, 255))   # snout
g.ellipse([hx + 225, hy - 12, hx + 245, hy + 4], fill=(60, 34, 22, 255))      # nostril
g.polygon([(hx - 80, hy - 60), (hx - 170, hy - 190), (hx - 20, hy - 80)], fill=(122, 74, 44, 255))   # horn
g.polygon([(hx - 10, hy - 75), (hx - 40, hy - 175), (hx + 40, hy - 80)], fill=(122, 74, 44, 255))    # horn
g.ellipse([hx + 30, hy - 38, hx + 70, hy - 8], fill=(214, 214, 204, 255))    # milky eye
g.line([(hx + 90, hy + 30), (hx + 230, hy + 22)], fill=(90, 52, 30, 255), width=6)   # mouth
img.alpha_composite(dr)

# ---------------------------------------------------------------- candle and flame
cd = ImageDraw.Draw(img)
cd.rectangle([FLAME[0] - 34, FLAME[1] + 60, FLAME[0] + 34, FLAME[1] + 420], fill=(232, 222, 196, 255))
cd.ellipse([FLAME[0] - 70, FLAME[1] + 400, FLAME[0] + 70, FLAME[1] + 450], fill=(70, 62, 58, 255))
fl = layer()
f = ImageDraw.Draw(fl)
f.ellipse([FLAME[0] - 40, FLAME[1] - 90, FLAME[0] + 40, FLAME[1] + 60], fill=(255, 170, 60, 255))
f.ellipse([FLAME[0] - 20, FLAME[1] - 40, FLAME[0] + 20, FLAME[1] + 50], fill=(255, 240, 190, 255))
img.alpha_composite(fl.filter(ImageFilter.GaussianBlur(6)))
halo = layer()
ImageDraw.Draw(halo).ellipse([FLAME[0] - 170, FLAME[1] - 200, FLAME[0] + 170, FLAME[1] + 150], fill=(255, 190, 90, 90))
img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(60)))

# ---------------------------------------------------------------- snow
sn = layer()
n = ImageDraw.Draw(sn)
for _ in range(900):
    x, y = random.uniform(0, W), random.uniform(0, 1800)
    rad = random.choice([2, 3, 3, 4, 5, 7])
    n.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(235, 240, 250, random.randint(90, 200)))
img.alpha_composite(sn.filter(ImageFilter.GaussianBlur(1.2)))

# ---------------------------------------------------------------- type
d = ImageDraw.Draw(img)
cream = (244, 232, 210, 255)


def centred(text, font, yy, fill, spacing=0):
    widths = [d.textlength(ch, font=font) for ch in text]
    x = (W - sum(widths) - spacing * (len(text) - 1)) / 2
    for ch, w in zip(text, widths):
        d.text((x, yy), ch, font=font, fill=fill)
        x += w + spacing


centred("SECOND-HAND", ImageFont.truetype(FONT + "Regular.ttf", 150), 170, cream, spacing=34)
centred("DRAGONS", ImageFont.truetype(FONT + "Bold.ttf", 260), 340, cream, spacing=30)
centred("a novella", ImageFont.truetype(FONT + "Italic.ttf", 70), 660, (215, 200, 180, 255))
centred("JONAS", ImageFont.truetype(FONT + "Regular.ttf", 90), 2270, cream, spacing=30)

img.convert("RGB").save(OUT, quality=92)
print("wrote", OUT)
