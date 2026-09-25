"""Gates — what a draft must pass before it is voiced, and what it failed.

Every gate is a pure function over the draft's narration text and its dossier;
none spends. They encode the failures real episodes were sent back for:

- **platitudes** — braidio's regex audit of the recycled tics (director's cue,
  "Here's the…", reduction, straw-man negation, naming the machinery).
- **expressiveness** — braidio's audio-tag density band (1.5–6 per 100 words,
  varied), because under-tagged reads as somniferous on a v3 delivery.
- **lyric_leak** — no source lyric line of four or more words verbatim in
  the narration: brief attributed fragments are commentary, a stanza is not.
- **length** — within a band around the word budget the price was quoted on.
- **shape** — enough beats to have movement, and a picture hint for each.

A failing report is data the writer quotes back into one bounded revision;
a still-failing draft is *returned with its report*, never silently shipped.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence

from braidio.style import audit_expressiveness, audit_platitudes

__all__ = ["Finding", "GateReport", "GATES", "run_gates"]

MIN_BEATS = 3
LENGTH_TOLERANCE = 0.30
LYRIC_LEAK_MIN_WORDS = 4


@dataclass(frozen=True)
class Finding:
    """One thing a gate objected to, in words a writer can act on."""

    gate: str
    message: str


@dataclass(frozen=True)
class GateReport:
    """The outcome of every gate on one draft."""

    findings: tuple[Finding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    def as_notes(self) -> str:
        """The findings as a numbered list for the revision prompt."""
        return "\n".join(f"{i}. [{f.gate}] {f.message}" for i, f in enumerate(self.findings, 1))


@dataclass(frozen=True)
class DraftFacts:
    """What the gates look at — decoupled from the Draft class itself."""

    narration: Sequence[str]  # one string per narration beat
    beat_count: int
    hinted_beats: int  # beats that have a picture hint
    target_words: int
    tags_expected: bool  # the delivery renders [audio tags]
    lyrics: str | None


Gate = Callable[[DraftFacts], Iterable[Finding]]


def _words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def gate_platitudes(d: DraftFacts) -> Iterable[Finding]:
    for i, text in enumerate(d.narration):
        for f in audit_platitudes(text):
            yield Finding("platitudes", f"beat {i}: {f.pattern} — {f.match!r}")


def gate_expressiveness(d: DraftFacts) -> Iterable[Finding]:
    if not d.tags_expected:
        return
    for msg in audit_expressiveness("\n".join(d.narration)):
        yield Finding("expressiveness", msg)


def gate_lyric_leak(d: DraftFacts) -> Iterable[Finding]:
    if not d.lyrics:
        return
    prose = " ".join(re.sub(r"\[[^\]]+\]", " ", t).lower() for t in d.narration)
    prose = re.sub(r"[^a-z0-9' ]+", " ", prose)
    prose = re.sub(r"\s+", " ", prose)
    for line in d.lyrics.splitlines():
        line = line.strip()
        if not line or line.startswith("["):
            continue
        norm = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9' ]+", " ", line.lower())).strip()
        if len(norm.split()) >= LYRIC_LEAK_MIN_WORDS and norm in prose:
            yield Finding("lyric_leak", f"the lyric line {line!r} appears verbatim; quote a fragment, attributed")


def gate_length(d: DraftFacts) -> Iterable[Finding]:
    n = sum(_words(t) for t in d.narration)
    lo = int(d.target_words * (1 - LENGTH_TOLERANCE))
    hi = int(d.target_words * (1 + LENGTH_TOLERANCE))
    if n < lo:
        yield Finding("length", f"{n} words is under the {d.target_words}-word budget (floor {lo}); add substance, not padding")
    elif n > hi:
        yield Finding("length", f"{n} words is over the {d.target_words}-word budget (ceiling {hi}); cut, the price was quoted on it")


def gate_shape(d: DraftFacts) -> Iterable[Finding]:
    if d.beat_count < MIN_BEATS:
        yield Finding("shape", f"{d.beat_count} beats; a film needs at least {MIN_BEATS} so the picture can change")
    if d.hinted_beats < d.beat_count:
        yield Finding("shape", f"{d.beat_count - d.hinted_beats} beat(s) have no picture hint; every beat needs one")


GATES: dict[str, Gate] = {
    "platitudes": gate_platitudes,
    "expressiveness": gate_expressiveness,
    "lyric_leak": gate_lyric_leak,
    "length": gate_length,
    "shape": gate_shape,
}


def run_gates(facts: DraftFacts, *, names: Iterable[str] = tuple(GATES)) -> GateReport:
    """Run the named gates and collect every finding."""
    findings: list[Finding] = []
    for name in names:
        findings.extend(GATES[name](facts))
    return GateReport(findings=tuple(findings))
