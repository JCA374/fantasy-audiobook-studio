# Setup

Claude Code: when asked to set this up, run these steps, check each one, and stop to ask the user only for commands
that need their password (suggest they type them with a `!` prefix).

1. **System tools.** Check `ffmpeg -version` and `espeak-ng --version`.
   - Linux (Debian/Ubuntu): `sudo apt install -y ffmpeg espeak-ng`
   - macOS: `brew install ffmpeg espeak-ng`
   - Windows: use WSL, then the Linux line.
2. **Python environment** (Python 3.10–3.12):
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```
   This pulls CPU PyTorch through kokoro (a few GB). On a machine with system PyTorch already installed,
   `python3 -m venv --system-site-packages .venv` avoids a second copy.
3. **Smoke test.** The first run downloads the Kokoro model (~330 MB) and the Whisper model:
   ```bash
   .venv/bin/python .claude/skills/kokoro-narrate/scripts/narrate.py --sample "The kettle had opinions." -o /tmp/sample.wav
   python3 .claude/skills/speech-flow/scripts/test_rules.py
   ```
   The sample should be a few seconds of speech, and all rule tests should pass.
4. **Initialise git** (recommended, so every draft and revision is kept): `git init && git add -A && git commit -m "Starter kit"`.
5. **Optional: voice text in other projects.** If the user wants the audio skills everywhere, link them into their
   global skills folder: `for s in voice-text speech-flow narration-prep kokoro-narrate listen-check audiobook-assemble; do ln -sfn "$PWD/.claude/skills/$s" ~/.claude/skills/$s; done`.
   Ask first: this changes every Claude Code project on the machine. The links point to this folder, so don't move it afterwards.
6. Tell the user they're ready, and suggest the first step: *"Start a new book with story-seed."*
