"""Cover for "The Worst Liar in Pennyford": a stone bridge at dusk, a toll gate gone thin as glass,
and a brass Crier's bell in the foreground.

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
random.seed(7)


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


# ---------------------------------------------------------------- dusk sky: plum at the top, amber at the horizon
yy, xx = np.mgrid[0:H, 0:W].astype(float)
t = np.clip(yy / 1350, 0, 1)[..., None]
top, low = np.array([38, 30, 58]), np.array([226, 150, 84])
sky = top * (1 - t ** 1.6) + low * t ** 1.6
sun = np.exp(-(np.hypot(xx - 1550, yy - 1240) / 380) ** 2)[..., None]
sky = sky * (1 - sun * 0.6) + np.array([255, 214, 140]) * sun * 0.6
img = Image.fromarray(sky.clip(0, 255).astype(np.uint8)).convert("RGBA")
d = ImageDraw.Draw(img)

# ---------------------------------------------------------------- far bank: roofs and a church tower
far = layer()
f = ImageDraw.Draw(far)
dark = (52, 40, 58, 255)
f.rectangle([0, 1180, W, 1400], fill=dark)
x = -40
while x < W:
    w = random.randint(140, 260)
    h = random.randint(70, 170)
    f.rectangle([x, 1180 - h, x + w, 1185], fill=dark)
    f.polygon([(x - 10, 1180 - h), (x + w / 2, 1180 - h - random.randint(60, 120)), (x + w + 10, 1180 - h)], fill=dark)
    if random.random() < 0.5:
        wx = x + random.randint(30, w - 60)
        f.rectangle([wx, 1180 - h + 50, wx + 26, 1180 - h + 84], fill=(250, 196, 110, 255))
    x += w + random.randint(-20, 30)
f.rectangle([420, 760, 560, 1190], fill=dark)                      # church tower
f.polygon([(400, 770), (490, 600), (580, 770)], fill=dark)
img.alpha_composite(far)

# ---------------------------------------------------------------- river
riv = np.zeros((H, W, 4), np.uint8)
ry = np.arange(1400, 1900)
riv[1400:1900, :, :3] = np.array([70, 62, 92])
riv[1400:1900, :, 3] = 255
img.alpha_composite(Image.fromarray(riv))
rl = layer()
r = ImageDraw.Draw(rl)
for _ in range(260):                                               # glints of the sunset on the water
    gx, gy = random.gauss(1550, 260), random.uniform(1420, 1880)
    r.line([(gx - random.randint(20, 90), gy), (gx + random.randint(20, 90), gy)], fill=(255, 200, 130, random.randint(60, 170)), width=4)
img.alpha_composite(rl.filter(ImageFilter.GaussianBlur(1.5)))

# ---------------------------------------------------------------- the bridge: five arches
br = layer()
b = ImageDraw.Draw(br)
stone = (96, 78, 76, 255)
b.rectangle([0, 1300, W, 1460], fill=stone)                        # deck and parapet
b.rectangle([0, 1270, W, 1310], fill=(116, 96, 92, 255))
for i in range(5):
    cx = 240 + i * 480
    b.ellipse([cx - 190, 1400, cx + 190, 1780], fill=(70, 62, 92, 255))   # arch openings show the river
    b.rectangle([cx - 190, 1590, cx + 190, 1900], fill=(70, 62, 92, 255))
for i in range(6):                                                  # piers
    px = i * 480
    b.rectangle([px - 50, 1460, px + 50, 1900], fill=stone)
img.alpha_composite(br)

# ---------------------------------------------------------------- toll gate and hut, thin as glass
tg = layer()
g = ImageDraw.Draw(tg)
ghost = (236, 226, 214, 120)
g.rectangle([1780, 1020, 2080, 1270], outline=ghost, width=10)       # hut
g.polygon([(1750, 1030), (1930, 900), (2110, 1030)], outline=ghost)
g.line([(1750, 1030), (1930, 900), (2110, 1030)], fill=ghost, width=10)
g.rectangle([1890, 1150, 1970, 1270], outline=ghost, width=8)      # door
for k in range(6):                                                  # gate bars across the road
    gx = 1180 + k * 100
    g.line([(gx, 1110), (gx, 1272)], fill=ghost, width=12)
g.line([(1160, 1120), (1720, 1120)], fill=ghost, width=12)
g.line([(1160, 1200), (1720, 1200)], fill=ghost, width=12)
g.line([(1180, 1120), (1680, 1200)], fill=ghost, width=10)
img.alpha_composite(tg.filter(ImageFilter.GaussianBlur(2.5)))

# ---------------------------------------------------------------- foreground: a brass hand-bell on the weigh-house counter
fg = layer()
h = ImageDraw.Draw(fg)
h.rectangle([0, 1900, W, H], fill=(46, 34, 30, 255))
for i in range(5):
    h.line([(0, 1960 + i * 90), (W, 1960 + i * 90)], fill=(58, 44, 38, 255), width=6)
BX, BY = 560, 1880
brass = (204, 156, 72, 255)
h.polygon([(BX - 210, BY + 170), (BX - 130, BY - 120), (BX + 130, BY - 120), (BX + 210, BY + 170)], fill=brass)
h.ellipse([BX - 230, BY + 120, BX + 230, BY + 220], fill=(176, 128, 54, 255))
h.ellipse([BX - 140, BY - 170, BX + 140, BY - 70], fill=brass)
h.rectangle([BX - 34, BY - 420, BX + 34, BY - 150], fill=(92, 58, 34, 255))      # wooden handle
h.ellipse([BX - 50, BY - 460, BX + 50, BY - 380], fill=(92, 58, 34, 255))
h.polygon([(BX - 60, BY - 100), (BX - 20, BY - 100), (BX - 110, BY + 150), (BX - 160, BY + 150)], fill=(250, 214, 140, 200))  # shine
img.alpha_composite(fg)
shine = layer()
ImageDraw.Draw(shine).ellipse([BX - 300, BY - 260, BX + 300, BY + 260], fill=(255, 200, 120, 60))
img.alpha_composite(shine.filter(ImageFilter.GaussianBlur(80)))

# ---------------------------------------------------------------- type
d = ImageDraw.Draw(img)
cream = (246, 236, 216, 255)


def centred(text, font, yy, fill, spacing=0):
    widths = [d.textlength(ch, font=font) for ch in text]
    x = (W - sum(widths) - spacing * (len(text) - 1)) / 2
    for ch, w in zip(text, widths):
        d.text((x, yy), ch, font=font, fill=fill)
        x += w + spacing


centred("THE WORST LIAR", ImageFont.truetype(FONT + "Bold.ttf", 200), 150, cream, spacing=18)
centred("in Pennyford", ImageFont.truetype(FONT + "Italic.ttf", 150), 400, cream)
centred("a novella", ImageFont.truetype(FONT + "Italic.ttf", 70), 640, (226, 210, 190, 255))
centred("JONAS", ImageFont.truetype(FONT + "Regular.ttf", 90), 2270, cream, spacing=30)

img.convert("RGB").save(OUT, quality=92)
print("wrote", OUT)
