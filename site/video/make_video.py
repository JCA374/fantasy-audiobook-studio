#!/usr/bin/env python3
"""Render the "How it works" explainer video from script.yaml.

    .venv/bin/python site/video/make_video.py      -> site/video/how-it-works.mp4 + .vtt

Slides are drawn with PIL (1280x720, the site's dark palette). Host lines are spoken by Kokoro through
kokoro-narrate's synth(). Real book audio is cut from the repo's mp3s. Everything is joined with ffmpeg.
Rendered lines are cached in site/video/.cache/ (by voice+speed+text), so a re-run only renders edited lines.
"""
import ast
import hashlib
import re
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / ".claude/skills/kokoro-narrate/scripts"))
from narrate import SR, synth  # noqa: E402

CACHE = HERE / ".cache"
OUT = HERE / "how-it-works.mp4"
W, H = 1280, 720
LINE_GAP, SCENE_GAP = 0.35, 0.5

# site/assets/style.css, dark theme
BG, SURFACE, INK, MUTED, LINE, ACCENT = "#17140f", "#201c16", "#ede3d2", "#a89983", "#3a3228", "#e0814f"
GROUP = {"write": "#d2a764", "voice": "#6fb8b5", "ship": "#c38fc6"}
GROUP_LABEL = {"write": "Writing", "voice": "Voice", "ship": "Package"}
NOTO = "/usr/share/fonts/truetype/noto/"
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # has ◆ and →, which Noto Sans lacks
MARKUP = re.compile(r"\[([^\]]+)\]\((?:/[^)]*/|[+-]\d+)\)")


def font(name, size):
    return ImageFont.truetype(NOTO + name, size)


def plain(text):
    """Kokoro markup -> what a reader should see: [Mira](/mˈiɹə/) -> Mira."""
    return MARKUP.sub(r"\1", text)


def load_stages():
    src = (ROOT / "site/build.py").read_text(encoding="utf-8")
    node = next(n for n in ast.parse(src).body
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "STAGES")
    return ast.literal_eval(node.value)


STAGES = load_stages()
SKILLS = yaml.safe_load((ROOT / "site/content/skills.yaml").read_text(encoding="utf-8"))
GUIDE = yaml.safe_load((ROOT / "site/content/skills-guide.yaml").read_text(encoding="utf-8"))


def group_of(skill):
    return next((g for _, _, g, sk, _ in STAGES if skill in sk), "write")


# ---------------------------------------------------------------- slides

def canvas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((56, H - 44), "◆ Fantasy Audiobook Studio", font=ImageFont.truetype(DEJAVU, 18), fill=MUTED)
    return img, d


def wrap(d, text, fnt, width):
    """Wrap text to a pixel width, keeping explicit newlines."""
    out = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            trial = f"{line} {word}".strip()
            if d.textlength(trial, font=fnt) <= width:
                line = trial
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def draw_lines(d, xy, lines, fnt, fill, spacing=1.35):
    x, y = xy
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += int(fnt.size * spacing)
    return y


def slide_cover(s):
    img, d = canvas()
    cover = Image.open(ROOT / "books/do-not-resubmit/cover.jpg").convert("RGB").resize((520, 520))
    img.paste(cover, (W - 520 - 80, (H - 520) // 2 - 10))
    d.text((80, 220), "How the studio", font=font("NotoSerif-Bold.ttf", 60), fill=INK)
    d.text((80, 295), "makes a book", font=font("NotoSerif-Bold.ttf", 60), fill=INK)
    d.text((82, 400), "Idea → chapters → voice → audiobook", font=ImageFont.truetype(DEJAVU, 25), fill=ACCENT)
    return img


def centred(content):
    """Centre a slide's content block vertically (above the footer)."""
    img, _ = canvas()
    diff = np.abs(np.asarray(content, dtype=np.int16) - np.asarray(Image.new("RGB", (W, H), BG), dtype=np.int16)).sum(2)
    rows = np.where(diff.any(1))[0]
    top, bottom = rows.min(), rows.max()
    img.paste(content.crop((0, top, W, bottom + 1)), (0, max(40, (H - 60 - (bottom - top)) // 2)))
    return img


def slide_text(s):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    y = 70
    if s.get("kicker"):
        d.text((80, y), s["kicker"].upper(), font=font("NotoSans-Bold.ttf", 22), fill=ACCENT)
        y += 46
    hf = font("NotoSerif-Bold.ttf", 52)
    y = draw_lines(d, (80, y), wrap(d, s["heading"], hf, W - 160), hf, INK, 1.2) + 30
    if s.get("bullets"):
        bf = font("NotoSans-Regular.ttf", 34)
        for b in s["bullets"]:
            d.ellipse([86, y + 17, 98, y + 29], fill=ACCENT)
            d.text((120, y), b, font=bf, fill=INK)
            y += 64
    if s.get("quote"):
        qf = font("NotoSerif-Regular.ttf", 36)
        lines = wrap(d, s["quote"] if s.get("raw") else plain(s["quote"]), qf, W - 260)
        box_h = len(lines) * int(36 * 1.4) + 70 + (34 if s.get("label") else 0)
        d.rounded_rectangle([80, y, W - 80, y + box_h], radius=18, fill=SURFACE, outline=LINE, width=2)
        d.rectangle([80, y + 18, 88, y + box_h - 18], fill=ACCENT)
        ty = y + 30
        if s.get("label"):
            d.text((120, ty), s["label"].upper(), font=font("NotoSans-Bold.ttf", 18), fill=MUTED)
            ty += 34
        draw_lines(d, (120, ty), lines, qf, INK, 1.4)
    return centred(img)


def slide_pipeline(s):
    img, d = canvas()
    hl = s.get("highlight")
    d.text((80, 70), "THE PIPELINE", font=font("NotoSans-Bold.ttf", 22), fill=ACCENT)
    d.text((80, 112), "Eleven stages, always in this order", font=font("NotoSerif-Bold.ttf", 48), fill=INK)
    cols, cw, ch, gx, gy = 4, 266, 128, 22, 18
    x0, y0 = (W - (cols * cw + (cols - 1) * gx)) // 2, 200
    for i, (n, name, g, skills, out) in enumerate(STAGES):
        r, c = divmod(i, cols)
        x, y = x0 + c * (cw + gx), y0 + r * (ch + gy)
        on = hl is None or hl == g
        col = GROUP[g] if on else LINE
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=14, fill=SURFACE, outline=col, width=3 if hl == g else 2)
        d.text((x + 18, y + 12), str(n), font=font("NotoSerif-Bold.ttf", 40), fill=col)
        nf = font("NotoSans-Bold.ttf", 24)
        draw_lines(d, (x + 18, y + 62), wrap(d, name, nf, cw - 36)[:2], nf, INK if on else MUTED, 1.2)
    lx = W - 80
    for g in reversed(GROUP):
        lf = font("NotoSans-Bold.ttf", 20)
        tw = d.textlength(GROUP_LABEL[g], font=lf)
        lx -= tw
        d.text((lx, 80), GROUP_LABEL[g], font=lf, fill=GROUP[g] if hl in (None, g) else LINE)
        lx -= 30
    return img


def slide_skill(s):
    img, d = canvas()
    name = s["name"]
    g, meta, guide = group_of(name), SKILLS[name], GUIDE[name]
    col = GROUP[g]
    d.rectangle([0, 0, 14, H], fill=col)
    d.text((80, 80), f"STAGE {meta['stage']} · {GROUP_LABEL[g].upper()} · {meta['origin'].upper()}",
           font=font("NotoSans-Bold.ttf", 22), fill=col)
    d.text((80, 122), name, font=font("NotoSerif-Bold.ttf", 76), fill=INK)
    pf = font("NotoSerif-Regular.ttf", 36)
    y = draw_lines(d, (80, 250), wrap(d, guide["plain"], pf, W - 160), pf, INK, 1.4) + 40
    sf_ = font("NotoSans-Regular.ttf", 26)
    for label, key in (("In", "input"), ("Out", "output")):
        d.text((80, y), label.upper(), font=font("NotoSans-Bold.ttf", 20), fill=MUTED)
        y = draw_lines(d, (170, y - 4), wrap(d, guide[key], sf_, W - 260)[:2], sf_, MUTED, 1.3) + 14
    # stage track along the bottom
    tx, tw = 80, (W - 160) // len(STAGES)
    for n, _, gg, sk, _ in STAGES:
        on = name in sk
        d.rounded_rectangle([tx, H - 110, tx + tw - 8, H - 80], radius=6,
                            fill=GROUP[gg] if on else SURFACE, outline=GROUP[gg] if on else LINE)
        d.text((tx + 10, H - 108), str(n), font=font("NotoSans-Bold.ttf", 18), fill=BG if on else MUTED)
        tx += tw
    return img


def slide_loop(s):
    img, d = canvas()
    d.text((80, 70), "SELF-IMPROVEMENT", font=font("NotoSans-Bold.ttf", 22), fill=ACCENT)
    d.text((80, 112), "Every fix becomes a rule", font=font("NotoSerif-Bold.ttf", 48), fill=INK)
    steps = ["Author hears something wrong", "Claude finds the cause", "Before and after renders",
             "Author picks by ear", "Fix becomes a rule in a skill", "A test guards the rule"]
    cx, cy, rx, ry = W // 2, 430, 400, 190
    pts = [(cx + rx * np.cos(-np.pi / 2 + i * 2 * np.pi / len(steps)),
            cy + ry * np.sin(-np.pi / 2 + i * 2 * np.pi / len(steps))) for i in range(len(steps))]
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=LINE, width=3)
    bf = font("NotoSans-Bold.ttf", 21)
    for i, ((x, y), txt) in enumerate(zip(pts, steps)):
        lines = wrap(d, txt, bf, 230)
        bw, bh = 260, 30 * len(lines) + 26
        d.rounded_rectangle([x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2], radius=12, fill=SURFACE,
                            outline=GROUP["voice"], width=2)
        for j, ln in enumerate(lines):
            d.text((x - d.textlength(ln, font=bf) / 2, y - bh / 2 + 13 + 30 * j), ln, font=bf, fill=INK)
    cf = font("NotoSerif-Italic.ttf", 26)
    for j, ln in enumerate(["The automatic listener", "finds the next one"]):
        d.text((cx - d.textlength(ln, font=cf) / 2, cy - 30 + 36 * j), ln, font=cf, fill=ACCENT)
    return img


def slide_close(s):
    img, d = canvas()
    d.text((80, 230), "Every book, skill and fix,", font=font("NotoSerif-Bold.ttf", 58), fill=INK)
    d.text((80, 305), "with the audio:", font=font("NotoSerif-Bold.ttf", 58), fill=INK)
    d.text((82, 420), "jca374.github.io/fantasy-audiobook-studio", font=font("NotoSans-Bold.ttf", 34), fill=ACCENT)
    return img


LAYOUTS = {"cover": slide_cover, "text": slide_text, "pipeline": slide_pipeline, "skill": slide_skill,
           "loop": slide_loop, "close": slide_close}


# ---------------------------------------------------------------- audio

def tts(text, voice, speed):
    key = hashlib.sha1(f"{voice}|{speed}|{text}".encode()).hexdigest()[:16]
    p = CACHE / f"{key}.wav"
    if not p.exists():
        sf.write(p, synth(text, voice, speed), SR)
    return sf.read(p, dtype="float32")[0]


def clip(path, start, dur):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(start), "-t", str(dur), "-i", str(ROOT / path),
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, dtype=np.float32).copy()
    fade = int(SR * 0.08)
    a[:fade] *= np.linspace(0, 1, fade)
    a[-fade:] *= np.linspace(1, 0, fade)
    return a


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)


def vtt_time(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def main():
    cfg = yaml.safe_load((HERE / "script.yaml").read_text(encoding="utf-8"))
    voices, speed = cfg["voices"], cfg["speed"]
    CACHE.mkdir(exist_ok=True)
    track, cues, concat, t = [], [], [], 0.0
    for i, scene in enumerate(cfg["scenes"]):
        png = CACHE / f"slide{i:02d}.png"
        LAYOUTS[scene["slide"]["layout"]](scene["slide"]).save(png)
        start = t
        for item in scene["lines"]:
            (kind, val), = item.items()
            if kind == "pause":
                a = silence(val)
            elif kind == "clip":
                a = clip(*val)
            else:
                a = tts(val, voices[kind], speed[kind])
                cues.append((t, t + len(a) / SR, ("♪ " if kind == "book" else "") + plain(val)))
                a = np.concatenate([a, silence(LINE_GAP)])
            track.append(a)
            t += len(a) / SR
        track.append(silence(SCENE_GAP))
        t += SCENE_GAP
        concat.append(f"file '{png}'\nduration {t - start:.3f}")
        print(f"scene {i:02d} {scene['slide']['layout']:<8} {t - start:5.1f}s", flush=True)
    concat.append(f"file '{CACHE / f'slide{len(cfg['scenes']) - 1:02d}.png'}'")  # concat demuxer needs the last frame twice

    audio = np.concatenate(track)
    audio *= 0.9 / max(1e-6, np.abs(audio).max())
    wav = CACHE / "track.wav"
    sf.write(wav, audio, SR)
    lst = CACHE / "slides.txt"
    lst.write_text("\n".join(concat) + "\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(wav),
                    "-c:v", "libx264", "-tune", "stillimage", "-r", "25", "-pix_fmt", "yuv420p", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k", "-af", "loudnorm=I=-16:TP=-1.5", "-shortest",
                    "-movflags", "+faststart", str(OUT)], check=True)
    vtt = ["WEBVTT", ""] + [f"{vtt_time(a)} --> {vtt_time(b)}\n{txt}\n" for a, b, txt in cues]
    OUT.with_suffix(".vtt").write_text("\n".join(vtt), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}  {t / 60:.1f} min, {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
