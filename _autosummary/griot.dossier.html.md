# griot.dossier

The dossier — what research found, in one record the writer reads.

A [`Dossier`](#griot.dossier.Dossier) is evidence, not prose: every fact carries the URL it came
from, lyrics and annotations are kept verbatim, and what a researcher could
*not* find is recorded in `missing` so the writer is told rather than left
to invent. It serialises to plain JSON (`to_dict` / `from_dict`) so a
pipeline can save it beside the script it produced, and renders to the flat
text brief (`as_brief`) that the July Hamilton writers were fed — the shape
that produced the scripts that worked.

### Functions

| [`merge`](#griot.dossier.merge)(topic, parts)   | Fold several researchers' dossiers into one.   |
|------------------------------------------------------------------------|------------------------------------------------|

### Classes

| [`Annotation`](#griot.dossier.Annotation)(fragment, body[, url, verified, ...])   | A Genius-style annotation: a lyric fragment and what someone said about it.   |
|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`Dossier`](#griot.dossier.Dossier)(topic[, subject, artist, summary, ...])    | Everything the writer may lean on, and nothing it may not.                    |
| [`Fact`](#griot.dossier.Fact)(text, source_url)                             | One checkable statement, with the page it came from.                          |
| [`Source`](#griot.dossier.Source)(url[, title, kind, note])                   | Where a piece of the dossier came from.                                       |
| [`TimedLine`](#griot.dossier.TimedLine)(index, start_s, end_s, text)             | One synced lyric line with a half-open `[start_s, end_s)` window.             |

### *class* griot.dossier.Annotation(fragment, body, url='', verified=False, votes=0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A Genius-style annotation: a lyric fragment and what someone said about it.

### *class* griot.dossier.Dossier(topic, subject=None, artist=None, summary='', facts=(), lyrics=None, annotations=(), timed_lines=(), sources=(), missing=())

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

Inverse of [`to_dict()`](#griot.dossier.Dossier.to_dict).

* **Return type:**
  [`Dossier`](#griot.dossier.Dossier)

#### *property* is_empty *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

True when research found nothing usable at all.

#### to_dict()

Plain JSON-able form.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]

### *class* griot.dossier.Fact(text, source_url)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One checkable statement, with the page it came from.

### *class* griot.dossier.Source(url, title='', kind='', note='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Where a piece of the dossier came from.

### *class* griot.dossier.TimedLine(index, start_s, end_s, text)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One synced lyric line with a half-open `[start_s, end_s)` window.

### griot.dossier.merge(topic, parts)

Fold several researchers’ dossiers into one.

Scalars are first-non-empty-wins in researcher order; sequences are
concatenated in that order, with duplicate sources (by URL) dropped.

* **Return type:**
  [`Dossier`](#griot.dossier.Dossier)
