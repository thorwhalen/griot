# griot.gates

Gates — what a draft must pass before it is voiced, and what it failed.

Every gate is a pure function over the draft’s narration text and its dossier;
none spends. They encode the failures real episodes were sent back for:

- **platitudes** — braidio’s regex audit of the recycled tics (director’s cue,
  “Here’s the…”, reduction, straw-man negation, naming the machinery).
- **expressiveness** — braidio’s audio-tag density band (1.5–6 per 100 words,
  varied), because under-tagged reads as somniferous on a v3 delivery.
- **lyric_leak** — no source lyric line of four or more words verbatim in
  the narration: brief attributed fragments are commentary, a stanza is not.
- **length** — within a band around the word budget the price was quoted on.
- **shape** — enough beats to have movement, and a picture hint for each.

A failing report is data the writer quotes back into one bounded revision;
a still-failing draft is *returned with its report*, never silently shipped.

### Functions

| [`run_gates`](#griot.gates.run_gates)(facts, \*[, names])   | Run the named gates and collect every finding.   |
|----------------------------------------------------------------------------------|--------------------------------------------------|

### Classes

| [`Finding`](#griot.gates.Finding)(gate, message)   | One thing a gate objected to, in words a writer can act on.   |
|---------------------------------------------------------------------------|---------------------------------------------------------------|
| [`GateReport`](#griot.gates.GateReport)(findings)     | The outcome of every gate on one draft.                       |

### *class* griot.gates.Finding(gate, message)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One thing a gate objected to, in words a writer can act on.

### *class* griot.gates.GateReport(findings)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The outcome of every gate on one draft.

#### as_notes()

The findings as a numbered list for the revision prompt.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### griot.gates.run_gates(facts, , names=('platitudes', 'expressiveness', 'lyric_leak', 'length', 'shape'))

Run the named gates and collect every finding.

* **Return type:**
  [`GateReport`](#griot.gates.GateReport)
