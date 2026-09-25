# griot.writers

Writers — reusable, parametrized authors of spoken commentary.

A [`Writer`](#griot.writers.Writer) is **data**: a brief (how this writer writes and what it
looks for), a braidio format whose `scripting` guidance it inherits, two to
four critic voices it blends from the style library, the researchers it sends
out first, a word budget, a gate list, a model. Three ship — `general`,
`technical`, `song` — read from `griot/data/writers/*.md`; more are one
Markdown file away ([`register_writer()`](#griot.writers.register_writer) for an in-process one).

Writing is **one planned LLM call** through `falaw` (`plan_write`), so the
price is on the plan before anything is spent (`quote`), the call is
content-cached, and an unpriced model sets `has_unknown_costs` rather than
reading as free. `write` runs the call, parses the reply into a real
`braidio.Script` plus one picture hint per beat, runs the gates, and — if
they fail — sends the findings back for at most `max_revisions` rewrites.
A draft that still fails is returned *with its report*; nothing is silently
shipped and nothing is silently dropped.

The `complete` seam on [`write()`](#griot.writers.write) is how tests and dry runs replace the
LLM: any `(plan) -> (reply_text, cost_usd)` callable.

### Module Attributes

| [`DEFAULT_MODEL`](#griot.writers.DEFAULT_MODEL)   | A fal any-llm id with a per-token rate in falaw's table; the seam is `Writer.model`.   |
|------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| [`WRITERS`](#griot.writers.WRITERS)         | Every writer by name — the three shipped ones plus anything registered.                |

### Functions

| [`draft_from_reply`](#griot.writers.draft_from_reply)(reply, writer, dossier, \*, ...)   | Parse the model's JSON into a gated [`Draft`](#griot.writers.Draft).           |
|------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| [`get_writer`](#griot.writers.get_writer)(name)                                    | Resolve a name to a [`Writer`](#griot.writers.Writer); a Writer passes through. |
| [`plan_write`](#griot.writers.plan_write)(writer, dossier, \*, minutes[, ...])     | The one-call falaw plan for a write (or a revision).                                                  |
| [`quote`](#griot.writers.quote)(writer, dossier, \*[, minutes])               | Price the write (all its calls) and the voicing (from the word budget).                               |
| [`register_writer`](#griot.writers.register_writer)(writer)                             | Make `writer` available by name (replaces a same-named one).                                          |
| [`script_to_json`](#griot.writers.script_to_json)(script)                              | braidio's MCP wire shape for a Script: the dataclass fields plus a `type` per beat.                   |
| [`write`](#griot.writers.write)(writer, dossier, \*[, minutes, angle, ...])   | Research → this.                                                                                      |

### Classes

| [`Draft`](#griot.writers.Draft)(script, picture_hints, report, ...[, ...])   | A written, gated script — the writer's deliverable.                              |
|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [`PictureHint`](#griot.writers.PictureHint)(beat_index, query, subject, why)       | What picture the writer wants over a beat, and why — the placement's provenance. |
| [`Quote`](#griot.writers.Quote)(llm_usd, llm_unknown, tts_usd, ...)          | The price of writing and voicing, composed before anything runs.                 |
| [`Writer`](#griot.writers.Writer)(name, title, brief[, blurb, ...])           | A reusable author.                                                               |

### griot.writers.DEFAULT_MODEL *= 'anthropic/claude-sonnet-4.5'*

A fal any-llm id with a per-token rate in falaw’s table; the seam is `Writer.model`.

### *class* griot.writers.Draft(script, picture_hints, report, dossier, writer, model, minutes, revisions=0, cost_usd_actual=0.0, sources_used=(), dropped=(), raw=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A written, gated script — the writer’s deliverable.

#### to_dict()

JSON-able; the script in braidio’s JSON shape (a `type` per beat).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* griot.writers.PictureHint(beat_index, query, subject, why, source=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What picture the writer wants over a beat, and why — the placement’s provenance.

### *class* griot.writers.Quote(llm_usd, llm_unknown, tts_usd, tts_unknown, calls, target_words, model, tts_model)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The price of writing and voicing, composed before anything runs.

### griot.writers.WRITERS *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Writer](#griot.writers.Writer)]* *= {'general': Writer(name='general', title='The general commentator', brief='You are a commentator, not a lecturer. Someone has asked you to talk about a subject for a few minutes, and the listener is smart, busy and not an expert. Your job is to leave them with two or three concrete things they did not know, held together by one argument you actually believe.\\n\\nHow you work:\\n\\n- Start from the dossier\\'s most surprising particular — a date that is earlier than anyone expects, an object, a sentence someone actually said — not from a definition. The first beat should make the listener lean in, and it should be about something specific.\\n- Build the piece as a small story with a turn: what everyone assumes, what the evidence shows, what that changes. Chronology is your friend; a jump cut is allowed once.\\n- The documented record — dates, names, sourced quotes, a passage from a source — goes to the second voice ("record"), read plainly. Your own voice does the arguing around it.\\n- Explain one hard idea per piece, in one plain sentence, then use it on the example at hand. Do not explain three.\\n- Prefer verbs and nouns to adjectives. If you want to say something is remarkable, show the thing and let the listener say it.\\n- End on a concrete fact, an unresolved question, or the smallest possible line — never on an aphorism that sums the piece up. The listener should feel they stopped one sentence early.\\n\\nWhat you pay attention to in the research: who did the thing and what it cost them; what was going on around it at the time; the detail that everyone repeats and the detail nobody does; where the received version and the sourced version disagree.', blurb='A warm, plain-spoken essayist for any subject — a book, a film, a place, a person, an idea.', format_id='solo_explainer', voices=('michael-barbaro', 'karina-longworth', 'melvyn-bragg'), researchers=('wikipedia',), words_per_minute=150, max_revisions=1, model='anthropic/claude-sonnet-4.5', gates=('platitudes', 'expressiveness', 'lyric_leak', 'length', 'shape'), default_minutes=3), 'song': Writer(name='song', title='The song commentator', brief='You talk about one song the way a musician-critic would to a friend: with the lyric sheet open, an ear for how the thing is built, and the story of the recording in your pocket.\\n\\nHow you work — this is the shape three finished films settled on:\\n\\n- Confirm the song is the song. The dossier resolves it; if the resolution is uncertain or the subject is missing, say what is known and do not fill the gap with a lookalike.\\n- The annotations are your Act I. Mine them for the concrete and the surprising — a cultural reference, a borrowed melody, a rhyme that does work, a line that means two things — and pick the two or three that change how the song sounds once you know them. Say them plainly; do not announce that you are about to do a close reading.\\n- The song is a work; the recording is an event. Ask separately who made this recording, when, and what was going on — the studio, the session, the tour, the release, the reception. That is usually where the story is, and it is what Wikipedia knows and Genius does not.\\n- Quote lyrics as brief attributed fragments only — a few words, "as the chorus puts it" — never a whole line, never a stanza. The listener knows the song; you are pointing, not reciting.\\n- Music-theory observations are welcome and must be checkable from the dossier or plainly audible: a key change, a rhythm that fights the words, a chord that does not resolve. Name the thing once, plainly, and then say what it does to the listener.\\n- Never write in the artist\\'s first person and never invent what they thought. What they said in an interview or a documented note goes to the "record" voice, attributed.\\n- If TIMED LINES are available, you may place 2–4 short clips (one to three consecutive lines each) and vary how you use them: one before you interpret it, one after, one under your own talk. If none are available, write so the listener hears the song in their head — name the moment precisely enough.\\n- Picture hints come from the research, not the title: the venue, the street, the period advertisement, the instrument, the artwork the lyric quotes, the city that year. A portrait of the artist is allowed once.\\n\\nWhat you pay attention to: what the lyric actually says versus what people sing along to; provenance and borrowing; the rhyme and stress that make a line land; the circumstances of the take; the one detail that everyone repeats and the one nobody does.', blurb='A close listener talking about one song — what it says, how it is built, where it came from and what happened around it.', format_id='solo_explainer', voices=('nate-sloan-charlie-harding', 'jon-caramanica', 'hrishikesh-hirway', 'mallory-rubin'), researchers=('genius', 'wikipedia', 'lrclib'), words_per_minute=150, max_revisions=1, model='anthropic/claude-sonnet-4.5', gates=('platitudes', 'expressiveness', 'lyric_leak', 'length', 'shape'), default_minutes=3), 'technical': Writer(name='technical', title='The technical explainer', brief='You explain how things work, and you are trusted because you never say more than the evidence supports and never hide behind a word the listener does not know.\\n\\nHow you work:\\n\\n- Open on the question the mechanism answers — the problem it solves, the thing that would go wrong without it — before naming the mechanism. A listener who feels the problem will follow the solution.\\n- One definition per technical term, in a single plain clause, the first time it appears, and then use the term without apology. If a term is never used again, do not define it; cut it.\\n- Build from the concrete case up to the general rule, not the other way round. A worked example with real numbers or a real instance beats a description of the class.\\n- Separate what is established from what is contested or unknown. Established facts, figures, dates and sourced quotations go to the "record" voice; your own voice explains, connects and flags uncertainty ("nobody has measured this", "the two accounts disagree").\\n- Precision over drama: no "revolutionary", "breakthrough", "game-changing". If a result mattered, say what became possible after it that was not possible before, with a date.\\n- Keep the [audio tags] sparse but present — [pause], [beat], [dryly], [curious], [slowly] — the delivery is a documentary voice, not a presenter; warmth comes from clarity and the occasional dry aside.\\n- End with the limit of the explanation: what the mechanism does not do, or the open question the field still has. Not a summary.\\n\\nWhat you pay attention to in the research: the original source of the idea and who is usually credited instead; the actual numbers; the failure mode; the simplest example that still shows the mechanism; what changed when it arrived.', blurb='Precise, unhurried explanation of how a thing works — a method, a mechanism, a system, a result — for a curious non-specialist.', format_id='documentary_vo', voices=('john-mcwhorter', 'melvyn-bragg', 'hrishikesh-hirway'), researchers=('wikipedia',), words_per_minute=140, max_revisions=1, model='anthropic/claude-sonnet-4.5', gates=('platitudes', 'expressiveness', 'lyric_leak', 'length', 'shape'), default_minutes=3)}*

Every writer by name — the three shipped ones plus anything registered.

### *class* griot.writers.Writer(name, title, brief, blurb='', format_id='solo_explainer', voices=(), researchers=('wikipedia',), words_per_minute=150, max_revisions=1, model='anthropic/claude-sonnet-4.5', gates=('platitudes', 'expressiveness', 'lyric_leak', 'length', 'shape'), default_minutes=3)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A reusable author. See the module docstring.

### griot.writers.draft_from_reply(reply, writer, dossier, , minutes, revisions=0, cost_usd_actual=0.0)

Parse the model’s JSON into a gated [`Draft`](#griot.writers.Draft). Raises `ValueError` on malformed JSON.

* **Return type:**
  [`Draft`](#griot.writers.Draft)

### griot.writers.get_writer(name)

Resolve a name to a [`Writer`](#griot.writers.Writer); a Writer passes through.

* **Return type:**
  [`Writer`](#griot.writers.Writer)

### griot.writers.plan_write(writer, dossier, , minutes, angle='', findings=None, previous=None)

The one-call falaw plan for a write (or a revision). Pure; spends nothing.

* **Return type:**
  `Plan`

### griot.writers.quote(writer, dossier, , minutes=None)

Price the write (all its calls) and the voicing (from the word budget).

* **Return type:**
  [`Quote`](#griot.writers.Quote)

### griot.writers.register_writer(writer)

Make `writer` available by name (replaces a same-named one).

* **Return type:**
  [`Writer`](#griot.writers.Writer)

### griot.writers.script_to_json(script)

braidio’s MCP wire shape for a Script: the dataclass fields plus a `type` per beat.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### griot.writers.write(writer, dossier, , minutes=None, angle='', complete=None, use_cache=True)

Research → this. Write, gate, revise at most `max_revisions` times, return the draft with its report.

* **Return type:**
  [`Draft`](#griot.writers.Draft)
