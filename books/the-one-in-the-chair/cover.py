"""Cover for "The One in the Chair" — an empty chair lit from behind by an open window at dawn.

    python3 cover.py cover.jpg

Pure PIL + numpy. The scene is modelled in 3D (centimetres; x right, y up, z away from the viewer)
and projected through one camera, so the chair, its shadow, the window and the light pool agree.
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

# ---------------------------------------------------------------- camera
YAW, PITCH, DIST, FOCAL = math.radians(22), math.radians(10), 360.0, 3500.0
CHAIR_SCREEN = (840, 2090)      # where the chair's floor centre lands


def cam(p):
    x, y, z = p
    c, s = math.cos(YAW), math.sin(YAW)
    x, z = c * x + s * z, -s * x + c * z
    c, s = math.cos(PITCH), math.sin(PITCH)
    y, z = c * y + s * z, -s * y + c * z
    return x, y - 55, z + DIST           # camera ~1.3 m up, looking slightly down


_c0 = cam((0, 0, 0))
_ox = CHAIR_SCREEN[0] - FOCAL * _c0[0] / _c0[2]
_oy = CHAIR_SCREEN[1] + FOCAL * _c0[1] / _c0[2]


def proj(p):
    x, y, z = cam(p)
    return (_ox + FOCAL * x / z, _oy - FOCAL * y / z)


def poly(pts):
    return [proj(p) for p in pts]


# ---------------------------------------------------------------- scene constants
ZW = 150                         # back wall plane
WIN = (46, 120, 44, 138)         # window x0, x1, y0, y1 on the back wall
RAY = np.array([-0.55, -1.0, -0.85])   # dawn light travelling in through the window


def on_floor(p):
    """Follow the light ray from p down to the floor (y = 0)."""
    p = np.array(p, float)
    t = p[1] / -RAY[1]
    return tuple(p + t * RAY)


def vgrad(w, h, top, bot):
    a = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - a) + np.array(bot)[None, None, :] * a)
    return Image.fromarray(np.repeat(arr, w, axis=1).astype(np.uint8))


def layer():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def blurred(lay, r):
    return lay.filter(ImageFilter.GaussianBlur(r))


# ---------------------------------------------------------------- wall + floor
img = vgrad(W, H, (22, 28, 40), (30, 36, 50)).convert("RGBA")
d = ImageDraw.Draw(img)
floor_l, floor_r = proj((-900, 0, ZW)), proj((900, 0, ZW))
floor_poly = [floor_l, floor_r, (W, H), (0, H)]
fl = Image.new("L", (W, H), 0)
ImageDraw.Draw(fl).polygon(floor_poly, fill=255)
img.paste(vgrad(W, H, (34, 28, 25), (14, 12, 11)), (0, 0), fl)

# faint wallpaper stripes
stripes = layer()
sd = ImageDraw.Draw(stripes)
for x in range(-600, 600, 22):
    sd.line(poly([(x, 0, ZW), (x, 400, ZW)]), fill=(255, 255, 255, 6), width=3)
img = Image.alpha_composite(img, stripes)

# floorboards running towards the wall
boards = layer()
bd = ImageDraw.Draw(boards)
for x in range(-500, 500, 14):
    bd.line(poly([(x, 0, ZW), (x, 0, -400)]), fill=(0, 0, 0, 70), width=3)
for z in range(-380, ZW, 61):     # staggered board ends
    for x in range(-500, 500, 14):
        if random.random() < 0.35:
            bd.line(poly([(x, 0, z), (x + 14, 0, z)]), fill=(0, 0, 0, 55), width=2)
boards.putalpha(Image.composite(boards.getchannel("A"), Image.new("L", (W, H), 0), fl))
img = Image.alpha_composite(img, boards)
d = ImageDraw.Draw(img)

# skirting board
d.polygon(poly([(-900, 0, ZW), (900, 0, ZW), (900, 9, ZW), (-900, 9, ZW)]), fill=(18, 21, 29))

# ---------------------------------------------------------------- window
x0, x1, y0, y1 = WIN
win_quad = poly([(x0, y0, ZW), (x1, y0, ZW), (x1, y1, ZW), (x0, y1, ZW)])
xs, ys = [p[0] for p in win_quad], [p[1] for p in win_quad]
bx0, by0, bx1, by1 = int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1
sky = vgrad(bx1 - bx0, by1 - by0, (246, 228, 190), (170, 186, 204)).convert("RGBA")
sk = ImageDraw.Draw(sky)
# rooftops and chimneys of the sideways city
base = (by1 - by0) * 0.80
x = -10
while x < bx1 - bx0:
    w = random.randint(50, 120)
    h = random.randint(40, 150)
    sk.rectangle([x, base - h, x + w, by1 - by0], fill=(118, 132, 156))
    if random.random() < 0.5:
        cxp = x + random.randint(8, max(9, w - 24))
        sk.rectangle([cxp, base - h - 34, cxp + 16, base - h], fill=(118, 132, 156))
    x += w + random.randint(-6, 10)
sky = sky.filter(ImageFilter.GaussianBlur(2))
mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(mask).polygon(win_quad, fill=255)
full = layer()
full.paste(sky, (bx0, by0))
img = Image.composite(full, img, mask)

# light pool on the floor and spill on the wall
light = layer()
ld = ImageDraw.Draw(light)
pool = poly([on_floor((x0, y0, ZW)), on_floor((x1, y0, ZW)), on_floor((x1, y1, ZW)), on_floor((x0, y1, ZW))])
ld.polygon(pool, fill=(250, 226, 182, 92))
ld.polygon(win_quad, fill=(250, 226, 182, 70))
img = Image.alpha_composite(img, blurred(light, 34))
halo = layer()
ImageDraw.Draw(halo).polygon(win_quad, fill=(250, 226, 182, 110))
img = Image.alpha_composite(img, blurred(halo, 110))
d = ImageDraw.Draw(img)

# frame, mullion, sill
frame = (16, 18, 24)
d.line(win_quad + [win_quad[0]], fill=frame, width=26, joint="curve")
xm = (x0 + x1) / 2
d.line(poly([(xm, y0, ZW), (xm, y1, ZW)]), fill=frame, width=12)
d.line(poly([(x0, (y0 + y1) / 2, ZW), (x1, (y0 + y1) / 2, ZW)]), fill=frame, width=12)
d.polygon(poly([(x0 - 8, y0, ZW), (x1 + 8, y0, ZW), (x1 + 8, y0, ZW - 12), (x0 - 8, y0, ZW - 12)]), fill=(44, 46, 54))
d.polygon(poly([(x0 - 8, y0, ZW - 12), (x1 + 8, y0, ZW - 12), (x1 + 8, y0 - 4, ZW - 12), (x0 - 8, y0 - 4, ZW - 12)]), fill=(24, 25, 31))

# the left casement, swung open into the room
ang = math.radians(68)
hx, pw = x0, (x1 - x0) / 2
ex, ez = hx + pw * math.cos(ang) * -1 + pw * 0, ZW - pw * math.sin(ang)
ex = hx - pw * math.cos(ang) * -1 if False else hx + pw * math.cos(ang)
case = poly([(hx, y0, ZW), (ex, y0, ez), (ex, y1, ez), (hx, y1, ZW)])
d.polygon(case, fill=(52, 62, 80))
d.line(case + [case[0]], fill=frame, width=14, joint="curve")
d.line(poly([(hx, (y0 + y1) / 2, ZW), (ex, (y0 + y1) / 2, ez)]), fill=frame, width=9)
glint = layer()
ImageDraw.Draw(glint).polygon(case, fill=(220, 210, 190, 30))
img = Image.alpha_composite(img, glint)

# sheer curtain on the right, lifting in the air
cur = layer()
cd = ImageDraw.Draw(cur)
top, bot = proj((x1 - 4, y1 + 6, ZW - 2)), proj((x1 - 4, y0 + 2, ZW - 2))
pts_l, pts_r = [], []
for i in range(41):
    t = i / 40
    y = top[1] + (bot[1] - top[1]) * t
    billow = 210 * math.sin(math.pi * t) ** 1.4 * (0.6 + 0.4 * t)
    wave = 18 * math.sin(t * 9)
    pts_l.append((top[0] - 70 - billow + wave, y))
    pts_r.append((top[0] + 30 - billow * 0.25, y))
cd.polygon(pts_l + pts_r[::-1], fill=(245, 240, 230, 78))
for k in range(4):   # folds
    off = 18 + k * 22
    cd.line([(p[0] + off * (1 - 0.3 * k), p[1]) for p in pts_l], fill=(255, 255, 255, 34), width=6)
img = Image.alpha_composite(img, blurred(cur, 5))

# ---------------------------------------------------------------- chair (3D boxes)
WOOD, CUSH = np.array([96, 62, 40]), np.array([158, 74, 48])


def box(x0, x1, y0, y1, z0, z1, col=WOOD):
    return (x0, x1, y0, y1, z0, z1, col)


parts = []
for sx in (-20, 17):
    parts.append(box(sx + 0.5, sx + 3.5, 0, 44, -21, -18))   # front legs
    parts.append(box(sx + 0.5, sx + 3.5, 0, 100, 17.5, 20.5))  # back posts
    parts.append(box(sx + 1, sx + 3, 13, 16, -17, 17))       # side stretchers
parts += [
    box(-17, 17, 9, 12, -20, -18),                           # front stretcher
    box(-23, 23, 42, 47, -23, 23),                           # seat
    box(-21, 21, 47, 53, -21, 19, CUSH),                     # cushion
    box(-23, 23, 92, 99, 16.5, 21.5),                        # top rail
    box(-23, 23, 58, 62, 17, 21),                            # lower back rail
]
for sx in (-11, -1.25, 8.5):
    parts.append(box(sx, sx + 2.5, 62, 92, 18, 20))          # spindles
for sx in (-26, 22):
    parts.append(box(sx, sx + 4, 63, 67, -22, 21))           # arms, worn smooth
    parts.append(box(sx + 0.8, sx + 3.2, 47, 63, -20, -17))  # arm supports

L = -RAY / np.linalg.norm(RAY)
FILL = np.array([-0.5, 0.3, -1.0]); FILL /= np.linalg.norm(FILL)


def faces(b):
    x0, x1, y0, y1, z0, z1, col = b
    v = lambda x, y, z: (x, y, z)
    return [
        ([v(x0, y1, z0), v(x1, y1, z0), v(x1, y1, z1), v(x0, y1, z1)], (0, 1, 0)),
        ([v(x0, y0, z0), v(x1, y0, z0), v(x1, y1, z0), v(x0, y1, z0)], (0, 0, -1)),
        ([v(x0, y0, z1), v(x1, y0, z1), v(x1, y1, z1), v(x0, y1, z1)], (0, 0, 1)),
        ([v(x0, y0, z0), v(x0, y0, z1), v(x0, y1, z1), v(x0, y1, z0)], (-1, 0, 0)),
        ([v(x1, y0, z0), v(x1, y0, z1), v(x1, y1, z1), v(x1, y1, z0)], (1, 0, 0)),
        ([v(x0, y0, z0), v(x1, y0, z0), v(x1, y0, z1), v(x0, y0, z1)], (0, -1, 0)),
    ]


def hull(points):
    pts = sorted(set(points))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


# cast shadow: every part pushed along the light rays onto the floor
shadow = layer()
sh = ImageDraw.Draw(shadow)
for b in parts:
    x0b, x1b, y0b, y1b, z0b, z1b, _ = b
    corners = [(x, y, z) for x in (x0b, x1b) for y in (y0b, y1b) for z in (z0b, z1b)]
    sh.polygon(hull([proj(on_floor(c)) for c in corners]), fill=(0, 0, 0, 255))
shadow = blurred(shadow, 10)
shadow.putalpha(shadow.getchannel("A").point(lambda a: int(a * 0.62)))
img = Image.alpha_composite(img, shadow)

# warmth still in the cushion
warm = layer()
cx, cy = proj((0, 52, 0))
ImageDraw.Draw(warm).ellipse([cx - 330, cy - 200, cx + 330, cy + 150], fill=(232, 140, 70, 70))
img = Image.alpha_composite(img, blurred(warm, 90))

d = ImageDraw.Draw(img)
cam_faces = []
for b in parts:
    for pts, n in faces(b):
        n = np.array(n, float)
        centre = np.mean(np.array(pts), axis=0)
        cc = np.array(cam(tuple(centre)))
        nc = np.array(cam(tuple(centre + n))) - cc
        if np.dot(nc, cc) >= 0:      # facing away from the camera
            continue
        cam_faces.append((cc[2], pts, n, b[6]))
for _, pts, n, col in sorted(cam_faces, key=lambda f: -f[0]):
    key = max(0.0, float(np.dot(n, L)))          # dawn light from behind
    fill = max(0.0, float(np.dot(n, FILL)))      # dim warm fill from the room
    shade = 0.30 + 0.85 * key + 0.25 * fill
    c = np.clip(col * shade + np.array([10, 4, 0]) * fill, 0, 255).astype(int)
    d.polygon(poly(pts), fill=tuple(c))
# rim light along the tops of the rail and arms
for b in parts:
    x0b, x1b, y0b, y1b, z0b, z1b, col = b
    if y1b == 99:
        d.line(poly([(x0b, y1b, z1b), (x1b, y1b, z1b)]), fill=(200, 160, 116), width=3)

# ---------------------------------------------------------------- dust in the light
dust = layer()
dd = ImageDraw.Draw(dust)
pool_mask = Image.new("L", (W, H), 0)
beam = [win_quad[0], win_quad[1], pool[2], pool[3]] if False else win_quad + pool[::-1]
ImageDraw.Draw(pool_mask).polygon(hull([tuple(p) for p in beam]), fill=255)
pm = np.array(pool_mask)
for _ in range(170):
    x, y = random.randrange(W), random.randrange(H)
    if pm[y, x]:
        r = random.choice((2, 2, 3, 4))
        dd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 210, random.randint(40, 120)))
img = Image.alpha_composite(img, blurred(dust, 1.2))

# ---------------------------------------------------------------- vignette + grain
vig = Image.new("L", (W, H), 0)
ImageDraw.Draw(vig).ellipse([-500, -350, W + 500, H + 450], fill=255)
vig = blurred(vig, 260)
img = Image.composite(img, Image.new("RGBA", (W, H), (6, 7, 10, 255)), vig)
noise = Image.effect_noise((W, H), 28).convert("RGBA")
noise.putalpha(14)
img = Image.alpha_composite(img, noise)

# ---------------------------------------------------------------- type
d = ImageDraw.Draw(img)
cream, muted = (241, 232, 212), (196, 184, 160)


def centred(text, font, y, fill, spacing=0, shadow=True):
    widths = [d.textlength(ch, font=font) for ch in text] if spacing else None
    total = (sum(widths) + spacing * (len(text) - 1)) if spacing else d.textlength(text, font=font)
    x = (W - total) / 2
    if shadow:
        sl = layer()
        ImageDraw.Draw(sl).text((x, y + 6), text, font=font, fill=(0, 0, 0, 160)) if not spacing else None
        return_layer = blurred(sl, 8)
        globals()["img"] = Image.alpha_composite(globals()["img"], return_layer)
    dd = ImageDraw.Draw(globals()["img"])
    if spacing:
        for ch, w in zip(text, widths):
            dd.text((x, y), ch, font=font, fill=fill)
            x += w + spacing
    else:
        dd.text((x, y), text, font=font, fill=fill)


centred("THE ONE", ImageFont.truetype(FONT + "Regular.ttf", 92), 150, muted, spacing=34)
centred("in the Chair", ImageFont.truetype(FONT + "BoldItalic.ttf", 236), 270, cream)
d = ImageDraw.Draw(img)
d.line([(W / 2 - 150, 610), (W / 2 + 150, 610)], fill=(196, 160, 110), width=3)
centred("Some sentences can be appealed.", ImageFont.truetype(FONT + "Italic.ttf", 56), 650, muted)
centred("JONAS", ImageFont.truetype(FONT + "Regular.ttf", 74), 2200, cream, spacing=30)

img.convert("RGB").save(OUT, quality=93)
print("wrote", OUT)
