---
name: kokoro-narrate
description: "Render a book's narration scripts to speech with Kokoro TTS running locally on CPU. Use when the user wants to narrate, voice, record or render audio for a book or chapter, audition or pick narrator/character voices, preview a sample, or re-render chapters after edits. Input is books/<slug>/audio/chNN.txt from narration-prep; output is audio/chNN.wav for audiobook-assemble."
---

# Kokoro Narrate

> From another project: run these commands through the **voice-text** skill's launcher (`voice.sh <command> voice/<slug>`); there `books/<slug>` = `voice/<slug>`.

Local, free TTS with Kokoro-82M (Apache-2.0). Runs on CPU at **~1.7× real time** on this laptop (i5-8250U): a 1,000-word chapter (~6 min of audio) takes ~3.5 min, a 15k-word book (~100 min of audio) about 1 h. So:

- Always audition with `--sample` before a full render.
- Run full renders with `run_in_background` and tell the user roughly how long it will take: about `words / 170` minutes of audio, rendered in roughly 60 % of that time.
- Renders are **cached per paragraph**. After editing a script, re-run the same command and only the changed paragraphs get re-rendered.

Python: `.venv/bin/python` at the project root (it has kokoro, soundfile and pyyaml). If the venv is missing: `python3 -m venv --system-site-packages .venv && .venv/bin/pip install kokoro soundfile pyyaml`. System package `espeak-ng` improves fallback pronunciation of unknown words. If `which espeak-ng` is empty, ask the user to run `! sudo apt install -y espeak-ng`.

## Commands

```bash
PY=.venv/bin/python; N=.claude/skills/kokoro-narrate/scripts/narrate.py
$PY $N --list-voices
$PY $N --sample "A paragraph from the book…" --voice bm_george -o /tmp/…/sample.wav
$PY $N books/<slug>                       # all chapters
$PY $N books/<slug> --chapters ch03 ch04  # just these
$PY $N books/<slug> --chapters ch01 --voice bf_emma   # audition: writes audio/ch01.bf_emma.wav, ignores book.yaml voice
$PY $N --script training/03-dates.after.txt --speed 0.95 -o training/03-dates.after.wav   # one script file
```

For a full-chapter audition, render the same chapter once per candidate voice, then convert each to MP3 so the user can listen:
`ffmpeg -i audio/ch01.<voice>.wav -af loudnorm=I=-19:TP=-3 -ac 1 -b:a 96k audio/ch01.<voice>.mp3`.
Once the user has chosen a voice, set it in `book.yaml` and delete the `ch01.<voice>.*` audition files (ask first).

## Voice config: `narration:` block in `books/<slug>/book.yaml`

```yaml
narration:
  narrator: af_heart       # house default (author's choice); one voice carries the book
  speed: 1.0               # 0.9–1.0 suits fiction; drop to 0.95 for dense prose
  paragraph_pause: 0.6     # seconds between paragraphs
  characters:              # optional: dialogue lines tagged [[Name]] by narration-prep
    Mira: bf_emma
```

**The voice's first letter sets the accent**: `a` = American, `b` = British. You can mix them; each accent gets its own pipeline. Good fantasy narrators: `bm_george` and `bm_fable` (British male), `bf_emma` (British female), `af_heart` (the highest-quality voice overall), `am_michael`. Stick to **2–3 character voices at most**. Constant voice switching gets jarring; most audiobooks use a single narrator.

When auditioning, render the same 2–3 sentence passage (one with dialogue and a made-up name) in 3–4 candidate voices to the scratchpad. Tell the user the file paths so they can listen. Don't pick a voice for them.

## Script format (what narrate.py reads)

Paragraphs are separated by blank lines, and line breaks inside a paragraph are joined.

| Markup | Effect |
|---|---|
| plain paragraph | narrator voice |
| `[[Mira]] "Run," she said.` | the whole paragraph in Mira's voice (falls back to the narrator if Mira isn't mapped) |
| `[pause 1.5]` alone on a line | that many seconds of silence |
| `[Kaelith](/kˈIlɪθ/)` | phoneme override (Kokoro/misaki markup) |

## After rendering

Check the console summary: minutes of audio per chapter, and about 150 words per minute. A chapter that's far shorter than its word count suggests means text was dropped (usually a markup error). Then hand off to **audiobook-assemble**.
