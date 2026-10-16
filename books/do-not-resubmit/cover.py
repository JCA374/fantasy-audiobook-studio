"""Cover for "Do Not Resubmit": a tall narrow house at night, one window lit at the top, a lamp left on.

    python3 cover.py cover.jpg

Pure PIL + numpy.
"""
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 2400
OUT = sys.argv[1] if len(sys.argv) > 1 else "cover.jpg"
FONT = "/usr/share/fonts/truetype/noto/NotoSerif-"
random.seed(11)

# ---------------------------------------------------------------- sky: blue-grey night, lighter at the horizon
y = np.linspace(0, 1, H)[:, None]
top, bottom = np.array([14, 18, 32]), np.array([46, 52, 70])
sky = (top + (bottom - top) * y ** 1.4)[:, None, :].repeat(W, axis=1).reshape(H, W, 3)
img = Image.fromarray(sky.astype(np.uint8))
d = ImageDraw.Draw(img)

# faint stars
for _ in range(140):
    x, yy = random.randint(0, W), random.randint(0, int(H * 0.45))
    r = random.choice([1, 1, 2, 2, 3])
    c = random.randint(120, 200)
    d.ellipse([x - r, yy - r, x + r, yy + r], fill=(c, c, c + 20))

# ---------------------------------------------------------------- terrace: neighbours in silhouette
HOUSE = (930, 700, 1470, H)      # the tall narrow house (x0, roof y, x1, ground)
dark, darker = (22, 24, 34), (16, 17, 25)
for x0, x1, roof in [(0, 520, 1150), (520, 930, 980), (1470, 1900, 1050), (1900, W, 1250)]:
    d.rectangle([x0, roof, x1, H], fill=darker)
    for cx in range(x0 + 60, x1 - 60, 150):          # chimney pots
        d.rectangle([cx, roof - 70, cx + 40, roof], fill=darker)
d.rectangle(HOUSE, fill=dark)
d.polygon([(HOUSE[0] - 20, HOUSE[1]), (HOUSE[2] + 20, HOUSE[1]), (HOUSE[2] - 30, HOUSE[1] - 90), (HOUSE[0] + 30, HOUSE[1] - 90)], fill=dark)
d.rectangle([1330, HOUSE[1] - 220, 1390, HOUSE[1] - 60], fill=dark)

# dark windows, four floors; the top one will be lit
win_w, win_h = 150, 260
cols = [1040, 1250]
floors = [820, 1180, 1540, 1900]
for fy in floors:
    for cx in cols:
        d.rectangle([cx, fy, cx + win_w, fy + win_h], fill=(30, 33, 46))
        d.line([cx + win_w // 2, fy, cx + win_w // 2, fy + win_h], fill=dark, width=10)
        d.line([cx, fy + win_h // 2, cx + win_w, fy + win_h // 2], fill=dark, width=10)

# railings at the bottom
for rx in range(0, W, 46):
    d.rectangle([rx, 2230, rx + 10, H], fill=(10, 10, 16))
    d.polygon([(rx - 6, 2235), (rx + 16, 2235), (rx + 5, 2205)], fill=(10, 10, 16))
d.rectangle([0, 2240, W, 2256], fill=(10, 10, 16))

# ---------------------------------------------------------------- the lit window
lx, ly = cols[1], floors[0]
glow = Image.new("RGB", (W, H), (0, 0, 0))
gd = ImageDraw.Draw(glow)
cx, cy = lx + win_w // 2, ly + win_h // 2
for r, a in [(520, 30), (360, 55), (230, 90), (140, 140)]:
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(a, int(a * 0.72), int(a * 0.35)))
glow = glow.filter(ImageFilter.GaussianBlur(90))
img = Image.fromarray(np.clip(np.asarray(img, dtype=np.int16) + np.asarray(glow, dtype=np.int16), 0, 255).astype(np.uint8))
d = ImageDraw.Draw(img)
pane = Image.new("RGB", (win_w, win_h))
pd = ImageDraw.Draw(pane)
for i in range(win_h):                                   # warm gradient inside the window
    t = i / win_h
    pd.line([0, i, win_w, i], fill=(int(255 - 30 * t), int(196 - 50 * t), int(110 - 50 * t)))
pd.ellipse([win_w // 2 - 34, 92, win_w // 2 + 34, 160], fill=(255, 244, 205))   # lamp shade glow
pd.rectangle([win_w // 2 - 4, 160, win_w // 2 + 4, 222], fill=(120, 80, 40))    # lamp stem
pd.rectangle([win_w // 2 - 22, 222, win_w // 2 + 22, 232], fill=(120, 80, 40))  # lamp base
pd.rectangle([0, 232, win_w, win_h], fill=(150, 96, 52))                        # sill
img.paste(pane, (lx, ly))
d.line([lx, ly + 70, lx + win_w, ly + 70], fill=dark, width=8)          # transom
d.line([lx + win_w // 2, ly, lx + win_w // 2, ly + 70], fill=dark, width=8)
d.rectangle([lx - 14, ly - 14, lx + win_w + 14, ly], fill=dark)
d.rectangle([lx - 20, ly + win_h, lx + win_w + 20, ly + win_h + 18], fill=(40, 38, 46))

# light spill down the façade under the lit window
spill = Image.new("L", (W, H), 0)
ImageDraw.Draw(spill).polygon([(lx - 10, ly + win_h + 18), (lx + win_w + 10, ly + win_h + 18), (lx + win_w + 120, ly + win_h + 420), (lx - 120, ly + win_h + 420)], fill=40)
spill = spill.filter(ImageFilter.GaussianBlur(40))
img = Image.composite(Image.new("RGB", (W, H), (200, 150, 90)), img, spill)

# ---------------------------------------------------------------- type
d = ImageDraw.Draw(img)
cream = (240, 228, 205)


def centred(text, font, yy, fill, spacing=0):
    if spacing:
        widths = [d.textlength(ch, font=font) for ch in text]
        total = sum(widths) + spacing * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, widths):
            d.text((x, yy), ch, font=font, fill=fill)
            x += w + spacing
    else:
        d.text(((W - d.textlength(text, font=font)) / 2, yy), text, font=font, fill=fill)


centred("DO NOT", ImageFont.truetype(FONT + "Regular.ttf", 150), 150, cream, spacing=40)
centred("RESUBMIT", ImageFont.truetype(FONT + "Bold.ttf", 230), 320, cream, spacing=30)
centred("a novella", ImageFont.truetype(FONT + "Italic.ttf", 70), 600, (200, 190, 175))
centred("JONAS", ImageFont.truetype(FONT + "Regular.ttf", 90), 2290 - 0, cream, spacing=30)

img.convert("RGB").save(OUT, quality=92)
print("wrote", OUT)
