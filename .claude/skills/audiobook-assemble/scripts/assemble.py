#!/usr/bin/env python3
"""Master chapter WAVs into per-chapter MP3s and one chaptered .m4b audiobook.

Reads  BOOK_DIR/audio/chNN.wav  (from kokoro-narrate; audition files like ch01.bf_emma.wav are ignored) and  BOOK_DIR/book.yaml:
    title: The Thief of Greyfell
    author: Your Name
    narrator: Kokoro (bm_george)
    year: 2026
    cover: cover.jpg            # optional, relative to BOOK_DIR
    chapters:                   # optional stem -> title; default is the stem
      ch01: "Chapter One: The Greyfell Road"

Writes BOOK_DIR/audio/chNN.mp3 and BOOK_DIR/audio/<Title>.m4b.
(The `narration:` block of book.yaml is used by kokoro-narrate, not here.)
Each chapter gets 1 s of lead-in silence and 2 s of tail silence, and is loudness-normalised
two-pass to -19 LUFS integrated / -3 dBTP (ACX-style, mono).
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

LUFS, TP, LRA = -19, -3, 11
HEAD, TAIL = 1.0, 2.0


def ff(*args, capture=False):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y", *args],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])
    return r.stderr if capture else None


def master(src, dst):
    """Pad with silence and apply two-pass loudnorm -> 44.1 kHz mono WAV."""
    pad = f"adelay={int(HEAD * 1000)},apad=pad_dur={TAIL}"
    log = ff("-i", str(src), "-af", f"{pad},loudnorm=I={LUFS}:TP={TP}:LRA={LRA}:print_format=json",
             "-f", "null", "-", capture=True)
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", log).group(0))
    ln = (f"loudnorm=I={LUFS}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
          f":offset={m['target_offset']}:linear=true")
    ff("-i", str(src), "-af", f"{pad},{ln}", "-ar", "44100", "-ac", "1", str(dst))


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip())


def meta_escape(s):
    return re.sub(r"([=;#\\\n])", r"\\\1", str(s))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("book_dir", type=Path)
    ap.add_argument("--bitrate", default="64k", help="AAC/MP3 bitrate (64k is plenty for mono speech)")
    a = ap.parse_args()

    book = yaml.safe_load((a.book_dir / "book.yaml").read_text()) or {}
    out = a.book_dir / "audio"
    wavs = sorted(w for w in out.glob("ch*.wav") if re.fullmatch(r"ch\d+", w.stem))
    if not wavs:
        sys.exit("no chNN.wav files in audio/ — run kokoro-narrate first")
    titles = book.get("chapters") or {}
    title = book.get("title", a.book_dir.name)
    tags = {"title": title, "album": title, "artist": book.get("author", ""),
            "album_artist": book.get("author", ""), "composer": book.get("narrator", ""),
            "date": book.get("year", ""), "genre": "Audiobook"}

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        mastered, chapters, t = [], [], 0.0
        for i, w in enumerate(wavs, 1):
            ch_title = titles.get(w.stem, w.stem)
            print(f"[{i}/{len(wavs)}] mastering {w.name} — {ch_title}")
            m = tmp / w.name
            master(w, m)
            d = duration(m)
            chapters.append((t, t + d, ch_title))
            t += d
            mastered.append(m)
            ff("-i", str(m), "-c:a", "libmp3lame", "-b:a", a.bitrate,
               *[x for k, v in {**tags, "title": ch_title, "track": i}.items() for x in ("-metadata", f"{k}={v}")],
               str(out / f"{w.stem}.mp3"))

        (tmp / "list.txt").write_text("".join(f"file '{m}'\n" for m in mastered))
        meta = [";FFMETADATA1", *(f"{k}={meta_escape(v)}" for k, v in tags.items())]
        for s, e, ct in chapters:
            meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(s * 1000)}", f"END={int(e * 1000)}",
                     f"title={meta_escape(ct)}"]
        (tmp / "meta.txt").write_text("\n".join(meta) + "\n")

        safe = re.sub(r"[^\w\- ]", "", title).strip() or "audiobook"
        m4b = out / f"{safe}.m4b"
        cover = a.book_dir / book["cover"] if book.get("cover") else None
        args = ["-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-i", str(tmp / "meta.txt")]
        if cover and cover.exists():
            args += ["-i", str(cover), "-map", "0:a", "-map", "2:v", "-c:v", "copy", "-disposition:v", "attached_pic"]
        else:
            args += ["-map", "0:a"]
        args += ["-map_metadata", "1", "-map_chapters", "1", "-c:a", "aac", "-b:a", a.bitrate,
                 "-movflags", "+faststart", "-f", "mp4", str(m4b)]
        print("building", m4b.name)
        ff(*args)
    print(f"done: {m4b}  ({t / 60:.1f} min, {len(chapters)} chapters)  + {len(wavs)} chapter MP3s in {out}")


if __name__ == "__main__":
    main()
