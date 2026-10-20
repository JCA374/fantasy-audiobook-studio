# Fantasy Audiobook Studio

Short fantasy novels (10–20k words) written with [Claude Code](https://claude.com/claude-code) and narrated locally
with [Kokoro TTS](https://huggingface.co/hexgrad/Kokoro-82M), and the documented process behind them.

**Website:** https://jca374.github.io/fantasy-audiobook-studio/ (the pipeline, every skill, training cases with
before/after audio, and the books as .m4b audiobook and .epub).

| Path | What |
|---|---|
| `.claude/skills/` | the skills that run each stage (six ours, five vendored from rhavekost/author-toolkit, MIT) |
| `books/<slug>/` | one flat folder per book: bible, outline, chapters, `book.yaml`, `audio/` |
| `training/` | "this sounds wrong" cases with before/after scripts and audio |
| `site/` | the website generator (`build.py`), its content and `publish.sh` |

## Voice text from other projects

The audio skills also work outside this repo. **voice-text** voices any doc, story or video script with the same
rewrite rules and Whisper check. Link the skills once per machine:

```bash
S=$PWD/.claude/skills
for s in voice-text speech-flow narration-prep kokoro-narrate listen-check audiobook-assemble; do ln -sfn "$S/$s" ~/.claude/skills/$s; done
```

Then, in any project, ask Claude to "voice docs/notes.md". Lessons learned there come back to `training/` here.

Skills, scripts and the site generator: MIT licence (`LICENSE`), © 2026 Jonas Carlsson. Book text, audio and covers © the author, all rights reserved. Vendored skills keep their own licence (`.claude/skills/AUTHOR-TOOLKIT-LICENSE`).
