# griot

Research a subject, then write the spoken commentary about it — reusable, parametrized **writers** for [braidio](https://github.com/thorwhalen/braidio) productions.

A griot knows the record and performs it. `griot` does the two halves that come *before* a production is voiced: **research** (free, tokenless fetchers that turn a topic into a dossier of sourced evidence) and **writing** (named writers that turn the dossier into a gated `braidio.Script`, plus one picture hint per beat for the film that goes over it).

```bash
pip install griot
```

```python
import griot

w = griot.get_writer("song")                                   # general | technical | song
dossier = griot.research("The Sound of Silence by Simon & Garfunkel", researchers=w.researchers)
q = griot.quote(w, dossier, minutes=3)      # priced before anything runs
draft = griot.write(w, dossier, minutes=3)  # one LLM call (+ one gated revision), cached
draft.script                                 # a braidio.Script — voice it with braidio.weave_project
draft.picture_hints                          # one per beat, with why
draft.ok, draft.report                       # the gates' verdict and findings
```

Or from the shell: `python -m griot write "Trinity Church Manhattan" --writer general --out draft.json` (`--fake` runs the whole path with no key and no spend).

## Why writers

Three commentary films were written by a frontier model in a session, from Genius annotations, Wikipedia and LRCLIB timings, and rewritten after two complaints that each came with a measurement: too many designed turns of phrase reads as machine-written (*kitsch*), too few `[audio tags]` reads as flat (*somniferous*). A writer here is that craft, made reusable: a brief, a braidio format's own scripting guidance, two to four critic voices blended from a style library, the anti-platitude checklist, the house rules, and gates that send a draft back once before it is voiced.

| writer | for | researchers |
|---|---|---|
| `general` | any subject — a book, a film, a place, a person, an idea | wikipedia |
| `technical` | how a mechanism, method or result works | wikipedia |
| `song` | one song: what it says, how it is built, the recording's story | genius, wikipedia, lrclib |

A fourth writer is one Markdown file in `griot/data/writers/`, or `griot.register_writer(griot.Writer(...))`.

## Research

Every fact carries its source URL. What could not be found is recorded and the writer is told — it never substitutes the nearest match. `wikipedia` needs nothing; `lrclib` needs `"<song> by <artist>"`; `genius` works through the official API when `GENIUS_ACCESS_TOKEN` is set and records a miss otherwise (its tokenless public API is refused by Cloudflare as of 2026-09-25 — lyrics then come from LRCLIB, annotations are unavailable).

## Cost

`quote()` composes the exact falaw plan `write()` runs, so the price is known before the call, an unpriced model reads as *unknown* rather than free, and the call is content-cached — the same inputs never bill twice.

## Where it sits

griot → `braidio.Script` → **braidio** voices it → **illustration** finds the pictures the hints ask for → **braidio**'s picture track cuts the film → **reelee** runs all of it as one job from the studio. griot imports braidio and falaw; nothing imports griot but the application layer.
