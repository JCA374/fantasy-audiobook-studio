#!/usr/bin/env python3
"""Render narration scripts to WAV with Kokoro TTS (CPU).

Script format (produced by the narration-prep skill), paragraphs separated by blank lines:
    Plain paragraph                -> narrator voice
    [[Mira]] "Run," she said.      -> voice mapped to Mira in book.yaml narration.characters (falls back to narrator)
    [pause 2.0]                    -> 2 s of silence
    [Kael](/kˈeɪl/)                -> inline phoneme override (native Kokoro/misaki markup)

Voice settings come from the `narration:` block of BOOK_DIR/book.yaml.
Each paragraph is cached under audio/.cache/ keyed by text+voice+speed, so re-running after
edits only re-renders changed paragraphs.

Usage:
    narrate.py BOOK_DIR [--chapters ch01 ch02]       render audio/chNN.txt -> audio/chNN.wav
    narrate.py BOOK_DIR --chapters ch01 --voice bf_emma   audition: -> audio/ch01.bf_emma.wav
    narrate.py --sample "Text" --voice bm_george [--speed 1.0] [-o sample.wav]
    narrate.py --list-voices
"""
import argparse
import hashlib
import re
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "fantasy-novella" / "scripts"))
import evidence  # noqa: E402  (pipeline.log.jsonl: proof this stage ran)

SR = 24000
VOICES = {
    "American female": "af_heart af_bella af_nicole af_aoede af_kore af_sarah af_nova af_sky af_alloy af_jessica af_river",
    "American male": "am_michael am_fenrir am_puck am_echo am_eric am_liam am_onyx am_adam",
    "British female": "bf_emma bf_isabella bf_alice bf_lily",
    "British male": "bm_george bm_fable bm_lewis bm_daniel",
}
DEFAULT_CFG = {"narrator": "af_heart", "speed": 1.0, "paragraph_pause": 0.6, "characters": {}}
PAUSE_RE = re.compile(r"^\[pause\s+([\d.]+)\]$", re.I)
SPEAKER_RE = re.compile(r"^\[\[([^\]]+)\]\]\s*(.*)$", re.S)

_pipelines = {}


def pipeline_for(voice):
    from kokoro import KPipeline
    lang = voice[0]  # 'a' American, 'b' British — must match the voice prefix
    if lang not in _pipelines:
        _pipelines[lang] = KPipeline(lang_code=lang, repo_id="hexgrad/Kokoro-82M")
    return _pipelines[lang]


def synth(text, voice, speed):
    chunks = [r.audio.numpy() for r in pipeline_for(voice)(text, voice=voice, speed=speed) if r.audio is not None]
    return np.concatenate(chunks) if chunks else np.zeros(0, dtype=np.float32)


def silence(sec):
    return np.zeros(int(SR * sec), dtype=np.float32)


def parse(script):
    """Yield ('pause', seconds) or ('say', speaker|None, text)."""
    for para in re.split(r"\n\s*\n", script.strip()):
        para = " ".join(para.split())
        if not para:
            continue
        if m := PAUSE_RE.match(para):
            yield ("pause", float(m.group(1)))
        elif m := SPEAKER_RE.match(para):
            yield ("say", m.group(1).strip(), m.group(2))
        else:
            yield ("say", None, para)


def render_chapter(src, dst, cfg, cache_dir):
    parts, done, fresh = [], 0, 0
    items = list(parse(src.read_text(encoding="utf-8")))
    n_say = sum(1 for i in items if i[0] == "say")
    t0 = time.time()
    for item in items:
        if item[0] == "pause":
            parts.append(silence(item[1]))
            continue
        _, speaker, text = item
        voice = cfg["characters"].get(speaker, cfg["narrator"]) if speaker else cfg["narrator"]
        key = hashlib.sha1(f"{voice}|{cfg['speed']}|{text}".encode()).hexdigest()[:16]
        cached = cache_dir / f"{key}.wav"
        if cached.exists():
            audio, _ = sf.read(cached, dtype="float32")
        else:
            audio = synth(text, voice, cfg["speed"])
            sf.write(cached, audio, SR)
            fresh += 1
        parts += [audio, silence(cfg["paragraph_pause"])]
        done += 1
        print(f"\r  {src.stem}: {done}/{n_say} paragraphs ({fresh} rendered)", end="", flush=True)
    out = np.concatenate(parts) if parts else silence(0.1)
    sf.write(dst, out, SR)
    took = time.time() - t0
    print(f"\n  -> {dst}  {len(out) / SR / 60:.1f} min audio in {took / 60:.1f} min")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("book_dir", nargs="?", type=Path)
    ap.add_argument("--chapters", nargs="*", help="chapter stems to render (default: all)")
    ap.add_argument("--sample", help="render this text only")
    ap.add_argument("--script", type=Path, help="render one script file (with [pause]/[[Name]] markup) to -o")
    ap.add_argument("--voice", help="narrator voice (book mode: override book.yaml and write chNN.<voice>.wav)")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("-o", "--output", type=Path, default=Path("sample.wav"))
    ap.add_argument("--list-voices", action="store_true")
    a = ap.parse_args()

    if a.list_voices:
        for group, names in VOICES.items():
            print(f"{group:16} {names}")
        return
    if a.sample:
        t0 = time.time()
        audio = synth(a.sample, a.voice or "af_heart", a.speed)
        sf.write(a.output, audio, SR)
        print(f"{a.output}: {len(audio) / SR:.1f}s audio in {time.time() - t0:.1f}s")
        return
    if a.script:
        cfg = {**DEFAULT_CFG, "narrator": a.voice or "af_heart", "speed": a.speed}
        cache = a.script.parent / ".cache"
        cache.mkdir(exist_ok=True)
        render_chapter(a.script, a.output, cfg, cache)
        return
    if not a.book_dir:
        ap.error("give BOOK_DIR, --sample, --script or --list-voices")

    audio_dir = a.book_dir / "audio"
    book_path = a.book_dir / "book.yaml"
    book = (yaml.safe_load(book_path.read_text()) or {}) if book_path.exists() else {}
    cfg = {**DEFAULT_CFG, **(book.get("narration") or {})}
    cfg["characters"] = cfg.get("characters") or {}
    suffix = ""
    if a.voice:
        cfg["narrator"], suffix = a.voice, f".{a.voice}"
    scripts = sorted(s for s in audio_dir.glob("ch*.txt") if re.fullmatch(r"ch\d+", s.stem))
    if a.chapters:
        scripts = [s for s in scripts if s.stem in a.chapters]
    if not scripts:
        sys.exit(f"no chNN.txt scripts found in {audio_dir}")
    (cache := audio_dir / ".cache").mkdir(exist_ok=True)
    print(f"narrator={cfg['narrator']} speed={cfg['speed']} characters={cfg['characters'] or '-'}")
    if suffix:                                             # a voice audition is not the pipeline
        for s in scripts:
            render_chapter(s, audio_dir / f"{s.stem}{suffix}.wav", cfg, cache)
        return
    with evidence.logged(a.book_dir, "kokoro-narrate", scripts + [book_path]) as run:
        for s in scripts:
            render_chapter(s, audio_dir / f"{s.stem}.wav", cfg, cache)
            run.outputs.append(audio_dir / f"{s.stem}.wav")
        run.facts.update(narrator=cfg["narrator"], speed=cfg["speed"], chapters=len(scripts))


if __name__ == "__main__":
    main()
