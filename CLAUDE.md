# Fantasy novella → audiobook studio

Short fantasy novels (10–20k words, English) written with Claude and narrated locally with Kokoro TTS.
One flat folder per book: `books/<slug>/` (chapter files, bible files, book.yaml, and a single `audio/` folder). Start with the **fantasy-novella** skill — it owns the layout,
the pipeline order, and says which skill handles each stage.

- Writing: fantasy-novella (hub) + vendored author-toolkit skills (fiction-workshop, story-structure,
  character-archetypes, prose-mechanics, avoid-ai-writing — see .claude/skills/VENDORED.txt; don't edit them,
  so they can be re-synced from upstream).
- Audio: speech-flow (fixes the manuscript for the ear) → narration-prep → kokoro-narrate → audiobook-assemble.
  `training/` holds the author's "sounds wrong" examples with before/after audio; lessons go into speech-flow or narration-prep.
- Python: `.venv/bin/python` (kokoro, soundfile, pyyaml; reuses system CPU torch). ffmpeg is system-wide.
- Kokoro renders at ~1.7× real time (about 1 h per 15k-word book) on this CPU-only laptop: run full-book renders in the background.
- The manuscript (`books/<slug>/chNN.md`) is the source of truth; audio scripts are derived and regenerable.
- Website (GitHub Pages) is generated from the repo by `site/build.py` (content in `site/content/`). After any change
  to text, audio, skills or `training/`, publish with `site/publish.sh "what changed"`; Actions rebuilds and deploys.
  New skills need an entry in `site/content/skills.yaml`. WAVs are never committed (training WAVs become MP3s).
