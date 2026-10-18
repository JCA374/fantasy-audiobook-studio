# Fantasy novella → audiobook studio

Short fantasy novels (10–20k words, English) written with Claude and narrated locally with Kokoro TTS.
Set up from the Fantasy Audiobook Studio starter kit (https://jca374.github.io/fantasy-audiobook-studio/).
If `.venv/` doesn't exist yet, follow `SETUP.md` first.

One flat folder per book: `books/<slug>/` (chapter files, bible files, book.yaml, and a single `audio/` folder).
A new book starts with the **story-seed** skill (one-line idea → `seed.md`), then **fantasy-novella**, the hub:
it owns the layout and the pipeline order, and says which skill handles each stage.

- Writing: story-seed, fantasy-novella + vendored author-toolkit skills (fiction-workshop, story-structure,
  character-archetypes, prose-mechanics, avoid-ai-writing; see .claude/skills/VENDORED.txt, MIT licence in
  .claude/skills/AUTHOR-TOOLKIT-LICENSE).
- Audio: speech-flow (fixes the manuscript for the ear) → narration-prep → kokoro-narrate → listen-check (automatic
  listener, Whisper) → audiobook-assemble. Rule tests: `python3 .claude/skills/speech-flow/scripts/test_rules.py`.
- `training/` holds the lessons the skills were built from (cases 01–07, rule tests). Add your own cases the same way;
  the audio for the original cases is on the website's Improvements page.
- Python: `.venv/bin/python` (kokoro, soundfile, pyyaml, numpy, faster-whisper). ffmpeg must be installed system-wide.
- Kokoro renders at about 1.7× real time on a CPU-only laptop (about 1 h per 15k-word book): run full-book renders in the background.
- The manuscript (`books/<slug>/chNN.md`) is the source of truth; audio scripts are derived and regenerable.
- Series premises and house style go in `books/collection.md`.
- Licence: MIT (Jonas Carlsson), see `LICENSE`; the vendored skills keep their own MIT licence. Your own books are yours.
- **No website in this kit.** Skip any step that mentions `site/publish.sh` or the website. Finished audiobooks stay in
  `books/<slug>/audio/`; copy the .m4b wherever you like.
