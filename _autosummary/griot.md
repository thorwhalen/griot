# griot

griot — research a subject, then write the spoken commentary about it.

A griot knows the record and performs it. This package does the two halves
that sit *before* a braidio production: **research** (tokenless fetchers that
turn a topic into a [`Dossier`](#griot.Dossier) of sourced evidence) and **writing**
(reusable, parametrized [`Writer`](#griot.Writer) objects that turn a dossier into a
gated `braidio.Script` plus one picture hint per beat). The output is what
`braidio.weave_project` voices and what a picture track is planned over.

Shortest path:

```default
import griot

w = griot.get_writer("song")
dossier = griot.research("The Sound of Silence by Simon & Garfunkel", researchers=w.researchers)
q = griot.quote(w, dossier, minutes=3)        # priced before anything runs
draft = griot.write(w, dossier, minutes=3)    # one LLM call (+ one gated revision), cached
draft.script                                   # a braidio.Script
draft.picture_hints                            # one per beat, with why
draft.report                                   # the gates' findings, empty when it passed
```

The LLM path is `falaw` (fal any-llm), so the price is on the plan and the
call is content-cached; `write(..., complete=fake)` replaces it for tests.

### Functions

| [`build_prompt`](#griot.build_prompt)(writer, dossier, \*, minutes[, ...])   | The `(system, user)` pair for one write or one revision.                                                   |
|------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| [`checklist`](#griot.checklist)()                                         | The anti-platitude checklist, verbatim (the "paste into writer prompts" file).                             |
| [`draft_from_reply`](#griot.draft_from_reply)(reply, writer, dossier, \*, ...)   | Parse the model's JSON into a gated [`Draft`](#griot.Draft).                |
| [`get_writer`](#griot.get_writer)(name)                                    | Resolve a name to a [`Writer`](#griot.Writer); a Writer passes through.      |
| [`list_voices`](#griot.list_voices)()                                       | The voice names available to a writer (file stems under `voices/`).                                        |
| [`merge`](#griot.merge)(topic, parts)                                 | Fold several researchers' dossiers into one.                                                               |
| [`plan_write`](#griot.plan_write)(writer, dossier, \*, minutes[, ...])     | The one-call falaw plan for a write (or a revision).                                                       |
| [`quote`](#griot.quote)(writer, dossier, \*[, minutes])               | Price the write (all its calls) and the voicing (from the word budget).                                    |
| [`register_researcher`](#griot.register_researcher)(name[, fn])                     | Register `fn` under `name`; usable as a decorator.                                                         |
| [`register_writer`](#griot.register_writer)(writer)                             | Make `writer` available by name (replaces a same-named one).                                               |
| [`research`](#griot.research)(topic, \*[, researchers, http])            | Run `researchers` in order on `topic` and merge what they found.                                           |
| [`run_gates`](#griot.run_gates)(facts, \*[, names])                       | Run the named gates and collect every finding.                                                             |
| [`voice_card`](#griot.voice_card)(name)                                    | One critic's card: how they write, what they pay attention to, borrow this, don't imitate.                 |
| [`write`](#griot.write)(writer, dossier, \*[, minutes, angle, ...])   | Research → this.                                                                                           |
| [`writer_from_markdown`](#griot.writer_from_markdown)(text)                          | Build a [`Writer`](#griot.Writer) from a front-matter + brief Markdown file. |

### Classes

| [`Annotation`](#griot.Annotation)(fragment, body[, url, verified, ...])   | A Genius-style annotation: a lyric fragment and what someone said about it.                                   |
|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| [`Dossier`](#griot.Dossier)(topic[, subject, artist, summary, ...])    | Everything the writer may lean on, and nothing it may not.                                                    |
| [`Draft`](#griot.Draft)(script, picture_hints, report, ...[, ...])   | A written, gated script — the writer's deliverable.                                                           |
| [`Fact`](#griot.Fact)(text, source_url)                             | One checkable statement, with the page it came from.                                                          |
| [`Finding`](#griot.Finding)(gate, message)                             | One thing a gate objected to, in words a writer can act on.                                                   |
| [`GateReport`](#griot.GateReport)(findings)                               | The outcome of every gate on one draft.                                                                       |
| [`Http`](#griot.Http)(\*args, \*\*kwargs)                           | The bytes-in seam: two verbs, both GET.                                                                       |
| [`HttpxHttp`](#griot.HttpxHttp)([user_agent, timeout, ...])              | The default [`Http`](#griot.Http): httpx, a polite interval, bounded retries. |
| [`PictureHint`](#griot.PictureHint)(beat_index, query, subject, why)       | What picture the writer wants over a beat, and why — the placement's provenance.                              |
| [`Quote`](#griot.Quote)(llm_usd, llm_unknown, tts_usd, ...)          | The price of writing and voicing, composed before anything runs.                                              |
| [`Source`](#griot.Source)(url[, title, kind, note])                   | Where a piece of the dossier came from.                                                                       |
| [`TimedLine`](#griot.TimedLine)(index, start_s, end_s, text)             | One synced lyric line with a half-open `[start_s, end_s)` window.                                             |
| [`Writer`](#griot.Writer)(name, title, brief[, blurb, ...])           | A reusable author.                                                                                            |

### *class* griot.Annotation(fragment, body, url='', verified=False, votes=0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A Genius-style annotation: a lyric fragment and what someone said about it.

### *class* griot.Dossier(topic, subject=None, artist=None, summary='', facts=(), lyrics=None, annotations=(), timed_lines=(), sources=(), missing=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Everything the writer may lean on, and nothing it may not.

#### topic

the user’s words, untouched.

#### subject

the resolved title (a page, a song), or `None` if nothing
resolved.

#### artist

the performer / author, when the subject is a work.

#### summary

the lead paragraphs, plain text.

#### facts

sentences worth citing, each with its source page.

#### lyrics

the full lyric text, verbatim, when the subject is a song.

#### annotations

per-line commentary (Genius), best first.

#### timed_lines

synced lyric lines, when a timing source was found.

#### sources

every page consulted.

#### missing

what was looked for and not found — the writer is told.

#### as_brief(, max_annotations=16, annotation_chars=550)

The flat evidence brief handed to the writer.

Sections are only emitted when they have content; the `missing`
section is emitted whenever something was looked for and not found,
because that is the one thing a writer must not paper over.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### *classmethod* from_dict(d)

Inverse of [`to_dict()`](#griot.Dossier.to_dict).

* **Return type:**
  [`Dossier`](griot.dossier.md#griot.dossier.Dossier)

#### *property* is_empty *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

True when research found nothing usable at all.

#### to_dict()

Plain JSON-able form.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* griot.Draft(script, picture_hints, report, dossier, writer, model, minutes, revisions=0, cost_usd_actual=0.0, sources_used=(), dropped=(), raw=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A written, gated script — the writer’s deliverable.

#### to_dict()

JSON-able; the script in braidio’s JSON shape (a `type` per beat).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* griot.Fact(text, source_url)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One checkable statement, with the page it came from.

### *class* griot.Finding(gate, message)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One thing a gate objected to, in words a writer can act on.

### *class* griot.GateReport(findings)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The outcome of every gate on one draft.

#### as_notes()

The findings as a numbered list for the revision prompt.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* griot.Http(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

The bytes-in seam: two verbs, both GET.

#### json(url, , params=None, headers=None)

GET `url` and return the decoded JSON body.

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)

#### text(url, , params=None, headers=None)

GET `url` and return the body as text.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* griot.HttpxHttp(user_agent='griot/0.0 (+https://github.com/thorwhalen/griot)', timeout=30.0, min_interval=0.34, max_retries=3, \_last=0.0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The default [`Http`](#griot.Http): httpx, a polite interval, bounded retries.

### *class* griot.PictureHint(beat_index, query, subject, why, source=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What picture the writer wants over a beat, and why — the placement’s provenance.

### *class* griot.Quote(llm_usd, llm_unknown, tts_usd, tts_unknown, calls, target_words, model, tts_model)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The price of writing and voicing, composed before anything runs.

### *class* griot.Source(url, title='', kind='', note='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Where a piece of the dossier came from.

### *class* griot.TimedLine(index, start_s, end_s, text)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One synced lyric line with a half-open `[start_s, end_s)` window.

### *class* griot.Writer(name, title, brief, blurb='', format_id='solo_explainer', voices=(), researchers=('wikipedia',), words_per_minute=150, max_revisions=1, model='anthropic/claude-sonnet-4.5', gates=('platitudes', 'expressiveness', 'lyric_leak', 'length', 'shape'), default_minutes=3)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A reusable author. See the module docstring.

### griot.build_prompt(writer, dossier, , minutes, angle='', findings=None, previous=None)

The `(system, user)` pair for one write or one revision.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### griot.checklist()

The anti-platitude checklist, verbatim (the “paste into writer prompts” file).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### griot.draft_from_reply(reply, writer, dossier, , minutes, revisions=0, cost_usd_actual=0.0)

Parse the model’s JSON into a gated [`Draft`](#griot.Draft). Raises `ValueError` on malformed JSON.

* **Return type:**
  [`Draft`](griot.writers.md#griot.writers.Draft)

### griot.get_writer(name)

Resolve a name to a [`Writer`](#griot.Writer); a Writer passes through.

* **Return type:**
  [`Writer`](griot.writers.md#griot.writers.Writer)

### griot.list_voices()

The voice names available to a writer (file stems under `voices/`).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### griot.merge(topic, parts)

Fold several researchers’ dossiers into one.

Scalars are first-non-empty-wins in researcher order; sequences are
concatenated in that order, with duplicate sources (by URL) dropped.

* **Return type:**
  [`Dossier`](griot.dossier.md#griot.dossier.Dossier)

### griot.plan_write(writer, dossier, , minutes, angle='', findings=None, previous=None)

The one-call falaw plan for a write (or a revision). Pure; spends nothing.

* **Return type:**
  `Plan`

### griot.quote(writer, dossier, , minutes=None)

Price the write (all its calls) and the voicing (from the word budget).

* **Return type:**
  [`Quote`](griot.writers.md#griot.writers.Quote)

### griot.register_researcher(name, fn=None)

Register `fn` under `name`; usable as a decorator.

### griot.register_writer(writer)

Make `writer` available by name (replaces a same-named one).

* **Return type:**
  [`Writer`](griot.writers.md#griot.writers.Writer)

### griot.research(topic, , researchers=('wikipedia',), http=None)

Run `researchers` in order on `topic` and merge what they found.

An unknown researcher name raises rather than being skipped, because a
writer that silently lost its research would write from memory. A
researcher that *fails* (a 403, a timeout) is recorded under `missing`
and the rest still run: the writer is told, not the exception.

* **Return type:**
  [`Dossier`](griot.dossier.md#griot.dossier.Dossier)

### griot.run_gates(facts, , names=('platitudes', 'expressiveness', 'lyric_leak', 'length', 'shape'))

Run the named gates and collect every finding.

* **Return type:**
  [`GateReport`](griot.gates.md#griot.gates.GateReport)

### griot.voice_card(name)

One critic’s card: how they write, what they pay attention to, borrow this, don’t imitate.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### griot.write(writer, dossier, , minutes=None, angle='', complete=None, use_cache=True)

Research → this. Write, gate, revise at most `max_revisions` times, return the draft with its report.

* **Return type:**
  [`Draft`](griot.writers.md#griot.writers.Draft)

### griot.writer_from_markdown(text)

Build a [`Writer`](#griot.Writer) from a front-matter + brief Markdown file.

* **Return type:**
  [`Writer`](griot.writers.md#griot.writers.Writer)

### Modules

| [`dossier`](griot.dossier.md#module-griot.dossier)   | The dossier — what research found, in one record the writer reads.        |
|---------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`gates`](griot.gates.md#module-griot.gates)       | Gates — what a draft must pass before it is voiced, and what it failed.   |
| [`style`](griot.style.md#module-griot.style)       | The style library — the voice guide, the checklist, twenty critic voices. |
| [`tools`](griot.tools.md#module-griot.tools)       | The SSOT verbs — plain functions, JSON-able in, JSON-able out.            |
| [`writers`](griot.writers.md#module-griot.writers)   | Writers — reusable, parametrized authors of spoken commentary.            |
