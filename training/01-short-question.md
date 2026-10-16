# 01 · Short question sounds cut off

Source: *The One in the Chair*, ch01 (Elin's reply to Mira at intake).

> "It's not bad. Most people would take teapot." She finally looked up at him, and allowed herself the smallest flicker of the thing that passed for kindness in this job — not softness, exactly, but attention. "You want to appeal it?"
>
> "Can I?"

**Heard:** "Can I?" doesn't end like a question; it sounds like a fragment of one, cut off.

**Cause:** Kokoro's phonemes are `kˌæn ˌI?`: two weak (secondary) stresses and no main stress.
With no stressed word to carry the pitch, a short question has nothing to rise from and ends flat.
Longer questions have a stressed word, which is why they sound fine.

**Tried** (each rendered with the paragraph before and the first line after, for context). Only `before` and
the chosen fix (`after`) are kept; the other renders are in git history (tag `v1-first-edition`).
- stress on I, `"Can [I](+2)?"` → `kˌæn ˈI?`, and stress on Can, `"[Can](+2) I?"` → `kˈæn ˌI?`.
  Author: "b is the best but not quite there".
- refinements of stress on Can: `I` fully unstressed, a trailing `I…?`, a doubled `??`, both words stressed,
  a lengthened "Can".

**Decision:** author picked the doubled question mark (`"[Can](+2) I??"`, now `after`) as the best markup fix, but feels the real fix is in the
writing: a bare two-word question gives the voice too little to work with. Writing alternative to consider
in the manuscript: add an action beat or tag after it (`"Can I?" He sounded surprised.`).
