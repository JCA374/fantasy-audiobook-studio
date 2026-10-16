# Fantasy Novel Collection

_Split from the original project brief (kept unchanged, outside git, as `books/the-one-in-the-chair-v1/original-brief.md`). Series-wide notes live here; per-book facts live in each book's folder (`story-bible.md`, `glossary.md`, `continuity.md`)._

## 1. Project overview

- A collection of standalone fantasy novels, written as short chapters, drafted with Claude.
- The finished text is meant to become an audiobook: Claude writes the manuscript, then a separate text-to-speech (TTS) tool reads it aloud.
- Language: English, British spelling throughout (colour, grey, recognise, centre, etc.). The user sometimes switches to Swedish in conversation, but the story itself is written and read in English.
- Current stage: novel 1 is finished (second edition, 2026-10-16). Novel 2 is next: pick one of the premises below.

## 2. The collection

Four premises are being kept, one per novel. A fifth (a world of soul-bound animal companions, with a dragon nobody believes in) was dropped.

1. **The reaper and the furniture**, published title ***The One in the Chair*** (first novel; drafted, revised and narrated 2026-10-14). When people die they are demoted into objects. The protagonist is a reaper trying to free her mother's soul from a chair.
2. **The cartographer.** She inherits a magical atlas. Whatever she draws becomes real, and she has been carelessly erasing a kingdom by neglecting its borders. The theme is whether power like that can ever be used responsibly.
3. **The debt war.** Two kingdoms fight with borrowed years of life, memories and luck, lent out by mages called actuaries. A collections agent is sent after a vanished war hero who borrowed impossible sums. It turns out he gave it all to war orphans.
4. **The liar.** Magic runs on stories, and a convincing lie can reshape reality. The heroine is the world's worst liar, which makes her immune to a plague of magical propaganda.

## 8. Audiobook production notes

- Plan: write the manuscript chapter by chapter, then generate audio with a TTS service (ElevenLabs, Google Cloud Text-to-Speech, Microsoft Azure Speech or OpenAI TTS; several have good voices).
- A possible Python script would take a folder of chapter text files, send each to a TTS API and save one MP3 per chapter, with light editing afterwards in something like Audacity.
- Check each service's terms before any commercial release, and note that distributors such as Storytel and Audible have their own rules on AI narration.
- Listen through everything, since names, invented terms and English words in foreign-sounding contexts can be mispronounced. Respelling a word phonetically in the manuscript often fixes it.

> **Update (2026-10-14):** TTS is now Kokoro, running locally (see the kokoro-narrate skill). Pronunciation is fixed through each book's `glossary.md` and phoneme markup in the generated audio scripts, so the manuscript keeps normal spelling.
