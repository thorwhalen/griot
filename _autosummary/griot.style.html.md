# griot.style

The style library — the voice guide, the checklist, twenty critic voices.

Shipped as package data (`griot/data/style`), moved from braidio’s
`misc/docs/style` where nothing could import it. A writer *blends* 2–4 voices
and never impersonates one; the voice cards are read as prose into the prompt.

### Functions

| [`checklist`](#griot.style.checklist)()         | The anti-platitude checklist, verbatim (the "paste into writer prompts" file).             |
|----------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| [`list_voices`](#griot.style.list_voices)()       | The voice names available to a writer (file stems under `voices/`).                        |
| [`voice_card`](#griot.style.voice_card)(name)    | One critic's card: how they write, what they pay attention to, borrow this, don't imitate. |
| [`voice_guide_rules`](#griot.style.voice_guide_rules)() | The guide's own one-rule-under-all-thirteen and the mixing rules (§ 'The core method').    |

### griot.style.checklist()

The anti-platitude checklist, verbatim (the “paste into writer prompts” file).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### griot.style.list_voices()

The voice names available to a writer (file stems under `voices/`).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### griot.style.voice_card(name)

One critic’s card: how they write, what they pay attention to, borrow this, don’t imitate.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### griot.style.voice_guide_rules()

The guide’s own one-rule-under-all-thirteen and the mixing rules (§ ‘The core method’).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
