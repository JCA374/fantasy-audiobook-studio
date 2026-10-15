---
name: audiobook-assemble
description: "Master rendered chapter WAVs into a finished audiobook: loudness-normalised per-chapter MP3s plus one .m4b with chapter markers, cover art and metadata. Use when the user wants to build, export, package, master or finish the audiobook, make an m4b/mp3, or add chapters/cover/metadata. Input is books/<slug>/audio/chNN.wav from kokoro-narrate."
---

# Audiobook Assemble

```bash
.venv/bin/python .claude/skills/audiobook-assemble/scripts/assemble.py books/<slug> [--bitrate 64k]
```

Needs `books/<slug>/book.yaml`. Create it if it's missing:

```yaml
title: The Thief of Greyfell
author: <ask the user>
narrator: Kokoro TTS (bm_george)
year: 2026
cover: cover.jpg                     # optional; square JPG, ≥1400 px, relative to the book dir
chapters:                            # stem -> title as shown in the player
  ch01: "Chapter One: The Greyfell Road"
```

What the script does, per chapter:
- adds 1 s of lead-in silence and 2 s of tail silence
- normalises loudness in two passes to **−19 LUFS integrated, −3 dBTP** (ACX-style), mono 44.1 kHz
- writes `audio/chNN.mp3`

Then it concatenates everything into `audio/<Title>.m4b` (AAC) with chapter markers taken from the actual durations. Chapters are ordered by filename, so keep the `ch01`, `ch02`… zero-padding.

## Verify before reporting done

```bash
ffprobe -v error -show_chapters -of compact "books/<slug>/audio/<Title>.m4b"      # chapter count + titles
ffmpeg -nostats -i books/<slug>/audio/ch01.mp3 -af ebur128 -f null - 2>&1 | grep ' I:'   # ≈ -19 LUFS
```

## Export for the phone

The author listens in **BookPlayer** (iOS), importing from Google Drive. After verifying, copy only the `.m4b` (not the chapter MP3s, which BookPlayer would import as a duplicate book) to the project's export folder:

```bash
mkdir -p export/Audiobooks && cp "books/<slug>/audio/<Title>.m4b" export/Audiobooks/
```

The author uploads `export/Audiobooks/` to Google Drive themselves; there is no Drive sync on this machine.

Then publish to the website (m4b, chapter MP3s and a fresh EPUB): `site/publish.sh "<slug>: new audio"`.

Report the total runtime, the number of chapters and the output paths. This is AI narration: if the user plans to publish on Audible/ACX or another storefront, remind them to check that store's current rules on AI-narrated audiobooks.
