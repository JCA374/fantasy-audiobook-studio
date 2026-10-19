#!/usr/bin/env python3
"""Automatic listener: check rendered chapters for audio problems without a human listening to all of it.

Three checks per chapter, written to books/<slug>/audio/chNN.listen.json and printed as a report:
  words   Whisper transcribes the audio; the transcript is aligned with the script. Skipped, swapped or
          garbled words are flagged with a timestamp. (Whisper guesses familiar spellings, so a name it
          writes correctly may still sound slightly off; a name it writes WRONG is worth a listen.)
  pace    words per second for every paragraph, from the render cache; outliers often mean garbled or
          rushed audio.
  stress  bare short lines, and short quoted questions even with a tag or beat, whose phonemes have no
          main stress (they end flat; training case 01/05).

usage:
  listen.py books/<slug> [--chapters ch01 ch02] [--model base.en] [--reuse]
  listen.py books/<slug> --clip ch01 63.5 71 -o training/06-name.heard.wav     # cut a clip for a training case
"""
import argparse
import difflib
import hashlib
import json
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "kokoro-narrate" / "scripts"))
from narrate import DEFAULT_CFG, parse  # noqa: E402

MARKUP = re.compile(r"\[([^\]]+)\]\((?:/[^)]*/|[+-]\d)\)")
NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven",
       "8": "eight", "9": "nine", "10": "ten", "11": "eleven", "12": "twelve", "13": "thirteen"}
FILLER = {"a", "an", "the", "and", "of", "to", "in", "uh", "um"}
NUMWORDS = re.compile(r"^(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|\w+teen|\w+ty|\w+ties|"
                      r"hundred|thousand|million|first|second|third|\w+th|and)$")
PACE_DEV = 0.30      # flag a paragraph whose words/second is >30 % off the chapter median
PACE_MIN_WORDS = 6
BARE_LINE = 6
SHORT_Q = 3        # words; a quoted question this short is checked even with a tag or beat


def plain(text):
    return MARKUP.sub(r"\1", text)


UK_US = [(r"^mum$", "mom"), (r"^mums$", "moms"), (r"our$", "or"), (r"ise$", "ize"), (r"ised$", "ized"), (r"ising$", "izing"), (r"isation$", "ization"),
         (r"^grey", "gray"), (r"tre$", "ter"), (r"ogue$", "og"), (r"lled$", "led"), (r"lling$", "ling")]
ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
       "seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def say_number(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else " " + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " and " + say_number(n % 100))
    return say_number(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + say_number(n % 1000))


def norm(word):
    w = word.lower().replace("’", "'").strip(".,;:!?\"“”'()—–-…*")
    w = w.replace("'", "")
    for pat, rep in UK_US:
        w = re.sub(pat, rep, w)
    return w


def expand_numbers(text):
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)                                   # 10,000 -> 10000
    text = re.sub(r"(\d+)s\b", lambda m: say_number(int(m.group(1)))[:-1] + "ies", text)   # 50s -> fifties
    return re.sub(r"\d+", lambda m: say_number(int(m.group(0))) if len(m.group(0)) < 7 else m.group(0), text)


def tokens(text):
    return [t for t in (norm(w) for w in re.split(r"[\s—–-]+", expand_numbers(plain(text)))) if t]


def mmss(sec):
    return f"{int(sec) // 60}:{int(sec) % 60:02d}"


def load_cfg(book):
    p = book / "book.yaml"
    meta = yaml.safe_load(p.read_text()) if p.exists() else {}
    cfg = {**DEFAULT_CFG, **(meta.get("narration") or {})}
    cfg["characters"] = cfg.get("characters") or {}
    return cfg


def glossary_names(book):
    """{normalised name: expected phonemes or None (= Kokoro already says it right)} from glossary.md."""
    p = book / "glossary.md"
    if not p.exists():
        return {}
    out = {}
    for m in re.finditer(r"^\|\s*([A-Z][\w'’-]+)\s*\|[^|]*\|\s*([^|]+?)\s*\|", p.read_text(), re.M):
        if m.group(1) != "Term":
            out[norm(m.group(1))] = None if m.group(2) in ("ok", "?") else m.group(2)
    return out


_G2P = {}


def phonemes(text, lang="a"):
    if lang not in _G2P:
        from kokoro import KPipeline
        _G2P[lang] = KPipeline(lang_code=lang, model=False, repo_id="hexgrad/Kokoro-82M")
    return re.sub(r"[ˈˌ\s“”\"?.!,]", "", " ".join(r.phonemes for r in _G2P[lang](text)))


def ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def name_sounds_right(name, expected, heard, lang, possessive=False):
    """Whisper spells names it doesn't know by sound ("Elin" -> "Ellen"). Compare sounds, not letters:
    the name passes if what was heard is closer to the glossary pronunciation than to Kokoro's own default."""
    if not heard:
        return False, {}
    h = phonemes(" ".join(heard), lang)
    naive = phonemes(name.capitalize(), lang)
    exp = re.sub(r"[ˈˌ\s]", "", expected) if expected else naive
    if possessive:
        exp, naive = exp + "z", naive + "z"
    detail = {"heard_ph": h, "expected_ph": exp, "default_ph": naive}
    if exp != naive:
        return ratio(h, exp) > ratio(h, naive) and ratio(h, exp) >= 0.5, detail
    return ratio(h, exp) >= 0.6, detail


# ---------------------------------------------------------------- checks

def check_pace(items, cfg, cache):
    rows = []
    for i, it in enumerate(items):
        if it[0] != "say":
            continue
        _, speaker, text = it
        voice = cfg["characters"].get(speaker, cfg["narrator"]) if speaker else cfg["narrator"]
        wav = cache / f"{hashlib.sha1(f'{voice}|{cfg["speed"]}|{text}'.encode()).hexdigest()[:16]}.wav"
        n = len(tokens(text))
        if wav.exists() and n >= PACE_MIN_WORDS:
            rows.append((i, n, sf.info(wav).duration, text))
    if len(rows) < 5:
        return []
    med = statistics.median(n / d for _, n, d, _ in rows)
    out = []
    for i, n, d, text in rows:
        wps = n / d
        if abs(wps - med) / med > PACE_DEV:
            out.append({"para": i, "wps": round(wps, 2), "median": round(med, 2),
                        "kind": "fast" if wps > med else "slow", "text": plain(text)[:120]})
    return out


def check_stress(items, voice):
    from kokoro import KPipeline
    g2p = KPipeline(lang_code=voice[0], model=False, repo_id="hexgrad/Kokoro-82M")
    out = []
    for i, it in enumerate(items):
        if it[0] != "say":
            continue
        if re.fullmatch(r'["“][^"”]+["”]', it[2]) and len(tokens(it[2])) <= BARE_LINE:
            lines = [it[2]]
        else:   # a short question with a tag or beat still ends flat: the beat doesn't stress it (case 01)
            lines = [f'"{q}"' for q in (re.split(r"(?<=[.!?…])\s+", a or b)[-1] for a, b in
                                        re.findall(r'"([^"]+)"|“([^”]+)”', it[2]))
                     if q.endswith("?") and not q.endswith(("...?", "…?")) and len(tokens(q)) <= SHORT_Q]
        for line in lines:
            ph = " ".join(r.phonemes for r in g2p(line))
            if "ˈ" not in ph:
                out.append({"para": i, "text": plain(line), "phonemes": ph})
    return out


def transcribe(audio, model_name):
    from faster_whisper import WhisperModel
    pcm = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1", "-ar", "16000",
                                        "-f", "f32le", "-"], capture_output=True, check=True).stdout, dtype=np.float32)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(pcm, language="en", word_timestamps=True, condition_on_previous_text=False)
    return [(w.word, w.start, w.end) for s in segs for w in s.words], len(pcm) / 16000


def check_words(items, heard, names, lang="a"):
    ref, ref_para = [], []
    for i, it in enumerate(items):
        if it[0] == "say":
            for t in tokens(it[2]):
                ref.append(t)
                ref_para.append(i)
    merged = []
    for w, s, e in heard:                                     # Whisper splits "10,000" into "10" + ",000"
        if merged and re.fullmatch(r"\s*,\d{3}", w) and re.search(r"\d$", merged[-1][0]):
            merged[-1] = (merged[-1][0] + w.strip(), merged[-1][1], e)
        else:
            merged.append((w, s, e))
    hyp, hyp_t = [], []
    for w, s, _ in merged:
        for t in tokens(w):
            hyp.append(t)
            hyp_t.append(s)
    out = []
    sm = difflib.SequenceMatcher(None, ref, hyp, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        exp, got = ref[i1:i2], hyp[j1:j2]
        if "".join(exp) == "".join(got):                      # "teapot" vs "tea pot"
            continue
        if exp and got and difflib.SequenceMatcher(None, "".join(exp), "".join(got)).ratio() >= 0.8:
            continue                                          # spelling variants: recognised/recognized
        if set(exp + got) <= FILLER:                          # a dropped "the" is usually Whisper, not Kokoro
            continue
        nb = {hyp[j1 - 1] if j1 else None, hyp[j2] if j2 < len(hyp) else None}
        if op == "insert" and len(set(got)) == 1 and got[0] in nb:
            continue                                          # Whisper echoes a word where its 30 s windows meet
        if exp and got and all(NUMWORDS.match(e) for e in exp) and any(re.search(r"\d", g) for g in got):
            continue                                          # "thirty one" written as "31"
        t = hyp_t[j1] if j1 < len(hyp_t) else (hyp_t[-1] if hyp_t else 0)
        para = ref_para[i1] if i1 < len(ref_para) else ref_para[-1]
        base = lambda e: e if e in names else (e[:-1] if e.endswith("s") and e[:-1] in names else None)
        hit_names = [e for e in exp if base(e)]
        extra = {}
        if hit_names and len(exp) == 1:
            ok, extra = name_sounds_right(base(exp[0]), names[base(exp[0])], got, lang, base(exp[0]) != exp[0])
            if ok:
                continue
        elif exp and got and len(exp) <= 3 and len(got) <= 3 and ratio(phonemes(" ".join(exp), lang), phonemes(" ".join(got), lang)) >= 0.75:
            continue                                          # sounds the same: won/one, route/root, pale/pail
        kind = "name" if hit_names else {"replace": "swapped", "delete": "missing", "insert": "extra"}[op]
        out.append({"time": round(t, 1), "para": para, "kind": kind,
                    "expected": " ".join(exp), "heard": " ".join(got), **extra})
    return out


def cache_wav(item, cfg, cache):
    _, speaker, text = item
    voice = cfg["characters"].get(speaker, cfg["narrator"]) if speaker else cfg["narrator"]
    return cache / f"{hashlib.sha1(f'{voice}|{cfg["speed"]}|{text}'.encode()).hexdigest()[:16]}.wav"


_CONFIRM = {}


def confirm(flags, items, cfg, cache, names, model_name="small.en"):
    """Second opinion: transcribe each flagged paragraph's own audio (from the render cache) with a slower model.
    A flag is kept only if the same expected words are still flagged in that paragraph."""
    if model_name not in _CONFIRM:
        from faster_whisper import WhisperModel
        _CONFIRM[model_name] = WhisperModel(model_name, device="cpu", compute_type="int8")
    model = _CONFIRM[model_name]
    by_para = {}
    for f in flags:
        by_para.setdefault(f["para"], []).append(f)
    kept, dismissed = [], []
    for para, fl in by_para.items():
        wav = cache_wav(items[para], cfg, cache)
        if not wav.exists():
            kept += fl
            continue
        pcm = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", "-f", "f32le",
                                            "-"], capture_output=True, check=True).stdout, dtype=np.float32)
        segs, _ = model.transcribe(pcm, language="en", word_timestamps=True)
        second = check_words([items[para]], [(w.word, w.start, w.end) for sg in segs for w in sg.words], names,
                             cfg["narrator"][0])
        second_exp = {x["expected"] for x in second} | {x["heard"] for x in second if x["kind"] == "extra"}
        for f in fl:
            key = f["expected"] if f["kind"] != "extra" else f["heard"]
            (kept if key in second_exp else dismissed).append({**f, "second": model_name})
    return kept, dismissed


# ---------------------------------------------------------------- main

def check_chapter(book, stem, model_name, cfg, names, reuse=False):
    audio = book / "audio"
    script = audio / f"{stem}.txt"
    items = list(parse(script.read_text(encoding="utf-8")))
    src = audio / f"{stem}.wav" if (audio / f"{stem}.wav").exists() else audio / f"{stem}.mp3"
    t0 = time.time()
    old = audio / f"{stem}.listen.json"
    prev = json.loads(old.read_text()) if reuse and old.exists() else {}
    if prev.get("transcript") and prev.get("model") == model_name:
        heard, dur = [(w, s, s) for w, s in prev["transcript"]], prev["duration"]
    else:
        heard, dur = transcribe(src, model_name)
    report = {"chapter": stem, "model": model_name, "audio": src.name, "duration": round(dur, 1),
              "checked": time.strftime("%Y-%m-%d"),
              "words": [],
              "pace": check_pace(items, cfg, audio / ".cache"),
              "stress": check_stress(items, cfg["narrator"]),
              "seconds": round(time.time() - t0),
              "transcript": [[w, round(st, 2)] for w, st, _ in heard]}
    first = check_words(items, heard, names, cfg["narrator"][0])
    report["words"], report["dismissed"] = confirm(first, items, cfg, audio / ".cache", names) if first else ([], [])
    report["seconds"] = round(time.time() - t0)
    (audio / f"{stem}.listen.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return report


def print_report(r):
    n = len(r["words"]) + len(r["pace"]) + len(r["stress"])
    print(f"== {r['chapter']}  {mmss(r['duration'])} audio, checked in {r['seconds']}s: {n} to listen to"
          f"  ({len(r.get('dismissed', []))} dismissed by the second model)")
    for w in r["words"]:
        print(f"  {mmss(w['time']):>6}  {w['kind']:<8} expected: {w['expected'] or '–'!r:<32} heard: {w['heard'] or '–'!r}")
    for p in r["pace"]:
        print(f"  ¶{p['para']:<5} pace {p['kind']}: {p['wps']} words/s (chapter {p['median']})  {p['text'][:60]}…")
    for s in r["stress"]:
        print(f"  ¶{s['para']:<5} no main stress: {s['text']}  /{s['phonemes']}/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("book_dir", type=Path)
    ap.add_argument("--chapters", nargs="*")
    ap.add_argument("--model", default="base.en", help="Whisper model: base.en (fast, default) or small.en (2nd opinion)")
    ap.add_argument("--reuse", action="store_true", help="re-analyse the stored transcript instead of transcribing again")
    ap.add_argument("--clip", nargs=3, metavar=("CHAPTER", "START", "END"))
    ap.add_argument("-o", "--output", type=Path)
    a = ap.parse_args()
    audio = a.book_dir / "audio"
    if a.clip:
        stem, start, end = a.clip
        src = audio / f"{stem}.wav" if (audio / f"{stem}.wav").exists() else audio / f"{stem}.mp3"
        out = a.output or Path(f"{stem}-{start}.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", start, "-to", end, "-i", str(src), str(out)], check=True)
        print("clip ->", out)
        return
    cfg, names = load_cfg(a.book_dir), glossary_names(a.book_dir)
    stems = sorted(p.stem for p in audio.glob("ch*.txt") if re.fullmatch(r"ch\d+", p.stem))
    for stem in stems if not a.chapters else [s for s in stems if s in a.chapters]:
        print_report(check_chapter(a.book_dir, stem, a.model, cfg, names, a.reuse))


if __name__ == "__main__":
    main()
