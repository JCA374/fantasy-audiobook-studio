#!/usr/bin/env python3
"""Show how Kokoro will pronounce words, and audition alternative respellings.

    g2p.py Kaelith "Kay lith" "Kai lith"            # print phonemes for each
    g2p.py --lang a Vaeloth                          # American G2P (default: b = British)
    g2p.py --say "Kai lith" --voice bm_george        # also render say.wav to listen

Copy the phonemes of the respelling that sounds right into the glossary; narration-prep turns
them into Kokoro markup:  [Kaelith](/kˈIlɪθ/)
"""
import argparse
import warnings

warnings.filterwarnings("ignore")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words", nargs="*")
    ap.add_argument("--lang", default="b", choices=["a", "b"])
    ap.add_argument("--say", help="render this text to say.wav")
    ap.add_argument("--voice", default="bm_george")
    a = ap.parse_args()

    from kokoro import KPipeline
    p = KPipeline(lang_code=a.lang, repo_id="hexgrad/Kokoro-82M", model=bool(a.say))
    for w in a.words:
        _, tokens = p.g2p(w)
        print(f"{w:24} /{''.join((t.phonemes or '') + t.whitespace for t in tokens).strip()}/")
    if a.say:
        import numpy as np
        import soundfile as sf
        audio = np.concatenate([r.audio.numpy() for r in p(a.say, voice=a.voice)])
        sf.write("say.wav", audio, 24000)
        print("wrote say.wav")


if __name__ == "__main__":
    main()
