---
name: voice-text
description: "Turn any text into checked narration from any project: a doc, article, README, notes, story chapters or a video voiceover script. Rewrites it for the ear (speech-flow), renders it locally with Kokoro (af_heart), has Whisper listen back for skipped or garbled words and misheard names, and exports MP3/.m4b (or per-scene MP3s with timings for a video). Use when the user wants to voice, narrate, read aloud, make audio or a voiceover of a text, or turn a file into an MP3 or audiobook, outside the audiobook studio's own books."
---

# Voice Text

The studio's audio pipeline (from `fantasy-audiobook-studio`), for text that lives in another project. The stage skills do the work; this one sets up a work dir they understand, gives the commands a path that works from anywhere, and says what changes for prose and voiceovers.

**Every command** runs through the launcher, which uses the studio's Python and scripts:

```bash
V=~/.claude/skills/voice-text/scripts/voice.sh
```

The stage skills (speech-flow, narration-prep, kokoro-narrate, listen-check, audiobook-assemble) show commands like `.venv/bin/python .claude/skills/<skill>/scripts/x.py books/<slug>`. From another project, translate them: `$V <command> voice/<slug>`, where `books/<slug>` = `voice/<slug>`. Inside the studio repo, use its own commands as they are.

## 1. Make the work dir

```bash
$V new docs/intro.md --kind prose                 # one doc -> voice/<slug>/ch01.md
$V new docs/guide.md --kind prose --split         # a long doc (> 3k words): one chapter per ## section
$V new story/ch*.md --kind fiction --slug my-tale # chapters, copied as written
$V new video/script.md --kind voiceover           # one chapter per ## scene; scene titles aren't spoken
```

`voice/<slug>/` looks like a book folder: `chNN.md`, `book.yaml` (`kind`, voice af_heart, speed, chapter titles, `sources:` = original file + sha1 per chapter), `glossary.md`, `audio/`. `voice/.gitignore` keeps WAVs and the render cache out of git. Re-running `new` on the same slug refuses, because the work dir may hold approved rewrites. `--force` rebuilds the chapters from the sources but keeps the glossary and voice settings.

For prose and voiceover, `new` turns the markdown into plain paragraphs and prints a `rewrite:` line for each thing a listener can't use: dropped code blocks and tables, lists, bare URLs. Handle those in step 2.

| kind | for | differences |
|---|---|---|
| `fiction` | stories, chapters | everything as in the studio, dialogue rules included |
| `prose` | docs, articles, notes, READMEs | no dialogue checks (bare short line, clipped dialogue). Speed 0.95 |
| `voiceover` | narration over a video or slides | as prose, plus speed 1.05, and export writes unpadded per-scene MP3s and `timings.json` |

## 2. Rewrite for the ear (speech-flow)

```bash
$V scan voice/<slug>
```

Then follow the **speech-flow** skill: the scan candidates plus the listening read-through, a report table, and fixes only once the user approves them. For prose, also rewrite what `new` listed: say in a sentence what a table or code block shows (or leave it out), name a site instead of reading its URL, give a list a lead-in sentence so it doesn't arrive as fragments, and spell out abbreviations that look odd aloud (e.g. → for example, CLI → command line).

**The fixes go into the work dir copy** (`voice/<slug>/chNN.md`), never silently into the user's file. A doc written for the eye often has good reasons for its tables and parentheses. Once the fixes are approved, offer to copy them back to the original (the `sources:` path in book.yaml). For fiction, recommend doing so: the manuscript should stay the source of truth. If `sources:` shows a sha1 that no longer matches the original, the original changed after `new`. Tell the user, and rebuild with `--force` only after their ear rewrites are copied back or written down.

## 3. Names, script, render, listen, export

1. **Glossary**: list the invented or unusual names (people, products, places, jargon) in `glossary.md` and check each one with `$V g2p "Name" "respelling"`, as in **narration-prep** §1. Ask how a name should sound; don't guess. For a product name with a standard pronunciation, ask the user or mark it `ok` if Kokoro already gets it right.
2. `$V prep voice/<slug>`, then review the scripts as in narration-prep §3. The learned rules (short questions, case 01 and 09) apply here too.
3. `$V narrate voice/<slug> --sample "<the most name-dense paragraph>" -o <scratchpad>/sample.wav` first, then `$V narrate voice/<slug>`. Run it in the background when there's more than ~1,000 words: ~1.7× real time, about `words / 150` minutes of audio. Voice: **af_heart** unless the user asks for another (**kokoro-narrate** covers auditions).
4. `$V listen voice/<slug>`, and report the flags as timestamps, as in **listen-check**.
5. `$V export voice/<slug>`, which gives `audio/chNN.mp3` (−19 LUFS) and a `.m4b`. For a voiceover it also gives `audio/voiceover/chNN.mp3` (no lead-in or tail) and `timings.json`, with each scene's length in seconds for the video edit.
6. `$V status voice/<slug>` checks every audio stage against the evidence log (`pipeline.log.jsonl`). Report its table. Exit 0 means done.

## 4. Lessons go back to the studio

There's one set of rules for every project. When the user says something sounds wrong, or listen-check confirms a problem, make a training case **in the studio**, `~/.claude/skills/voice-text/../../../training/` (see its README.md). Include in the note which project and file it came from. Put the rule in the stage skill it belongs to, and run `$V test-rules`, which must pass. Then tell the user the studio repo has uncommitted lesson changes: they commit and publish there (`site/publish.sh`). Don't commit in the studio from another project.

## Set-up (once per machine)

```bash
S=~/code/other/fantasy-audiobook-studio/.claude/skills   # the studio checkout
for s in voice-text speech-flow narration-prep kokoro-narrate listen-check audiobook-assemble; do ln -sfn "$S/$s" ~/.claude/skills/$s; done
```

The studio needs its `.venv` (see `site/starter/SETUP.md`); the launcher says so if it's missing. Scripts follow the symlinks back to the studio, so evidence logging, the render cache format and the rule tests are the same everywhere.
