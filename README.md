# Fantasy Audiobook Studio

Short fantasy novels (10–20k words) written with [Claude Code](https://claude.com/claude-code) and narrated locally
with [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M), and the documented process behind them.

**Website:** https://jca374.github.io/fantasy-audiobook-studio/ (the pipeline, every skill, training cases with
before/after audio, and the books as .m4b audiobook and .epub).

| Path | What |
|---|---|
| `.claude/skills/` | the skills that run each stage (five ours, five vendored from rhavekost/author-toolkit, MIT) |
| `books/<slug>/` | one flat folder per book: bible, outline, chapters, `book.yaml`, `audio/` |
| `training/` | "this sounds wrong" cases with before/after scripts and audio |
| `site/` | the website generator (`build.py`), its content and `publish.sh` |

Book text © the author. Vendored skills keep their own license (`.claude/skills/AUTHOR-TOOLKIT-LICENSE`).
