# Fantasy novella → audiobook studio

Short fantasy novels (10–20k words, English) written with Claude and narrated locally with Kokoro TTS.
One flat folder per book: `books/<slug>/` (chapter files, bible files, book.yaml, and a single `audio/` folder). Start with the **fantasy-novella** skill — it owns the layout,
the pipeline order, and says which skill handles each stage.

- Writing: fantasy-novella (hub) + vendored author-toolkit skills (fiction-workshop, story-structure,
  character-archetypes, prose-mechanics, avoid-ai-writing — see .claude/skills/VENDORED.txt; don't edit them,
  so they can be re-synced from upstream).
- Audio: speech-flow (fixes the manuscript for the ear) → narration-prep → kokoro-narrate → listen-check (automatic
  listener, Whisper base.en ~6x real time) → audiobook-assemble. Rule tests: `python3 .claude/skills/speech-flow/scripts/test_rules.py` must pass before publishing.
  `training/` holds the author's "sounds wrong" examples with before/after audio; lessons go into speech-flow or narration-prep.
- Python: `.venv/bin/python` (kokoro, soundfile, pyyaml; reuses system CPU torch). ffmpeg is system-wide.
- Kokoro renders at ~1.7× real time (about 1 h per 15k-word book) on this CPU-only laptop: run full-book renders in the background.
- The manuscript (`books/<slug>/chNN.md`) is the source of truth; audio scripts are derived and regenerable.
  Chapter WAVs are deleted after assembly: re-running kokoro-narrate rebuilds them from the paragraph cache in seconds.
- New book: start with the story-seed skill (one-line idea → `seed.md`), then the fantasy-novella skill; series premises and house style are in `books/collection.md`.
  Finished books get a second edition by the steps on the website's pipeline page ("Revising a finished book").
- Website (GitHub Pages) is generated from the repo by `site/build.py` (content in `site/content/`). After any change
  to text, audio, skills or `training/`, publish with `site/publish.sh "what changed"`; Actions rebuilds and deploys.
  New skills need an entry in `site/content/skills.yaml`. WAVs are never committed (training WAVs become MP3s).
