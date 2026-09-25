"""The dossier — what research found, in one record the writer reads.

A :class:`Dossier` is evidence, not prose: every fact carries the URL it came
from, lyrics and annotations are kept verbatim, and what a researcher could
*not* find is recorded in ``missing`` so the writer is told rather than left
to invent. It serialises to plain JSON (``to_dict`` / ``from_dict``) so a
pipeline can save it beside the script it produced, and renders to the flat
text brief (``as_brief``) that the July Hamilton writers were fed — the shape
that produced the scripts that worked.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Iterable

__all__ = [
    "Annotation",
    "Dossier",
    "Fact",
    "Source",
    "TimedLine",
    "merge",
]


@dataclass(frozen=True)
class Source:
    """Where a piece of the dossier came from."""

    url: str
    title: str = ""
    kind: str = ""  # "wikipedia" | "genius" | "lrclib" | ...
    note: str = ""


@dataclass(frozen=True)
class Fact:
    """One checkable statement, with the page it came from."""

    text: str
    source_url: str


@dataclass(frozen=True)
class Annotation:
    """A Genius-style annotation: a lyric fragment and what someone said about it."""

    fragment: str
    body: str
    url: str = ""
    verified: bool = False
    votes: int = 0


@dataclass(frozen=True)
class TimedLine:
    """One synced lyric line with a half-open ``[start_s, end_s)`` window."""

    index: int
    start_s: float
    end_s: float | None
    text: str


@dataclass(frozen=True)
class Dossier:
    """Everything the writer may lean on, and nothing it may not.

    Attributes:
        topic: the user's words, untouched.
        subject: the resolved title (a page, a song), or ``None`` if nothing
            resolved.
        artist: the performer / author, when the subject is a work.
        summary: the lead paragraphs, plain text.
        facts: sentences worth citing, each with its source page.
        lyrics: the full lyric text, verbatim, when the subject is a song.
        annotations: per-line commentary (Genius), best first.
        timed_lines: synced lyric lines, when a timing source was found.
        sources: every page consulted.
        missing: what was looked for and not found — the writer is told.
    """

    topic: str
    subject: str | None = None
    artist: str | None = None
    summary: str = ""
    facts: tuple[Fact, ...] = ()
    lyrics: str | None = None
    annotations: tuple[Annotation, ...] = ()
    timed_lines: tuple[TimedLine, ...] = ()
    sources: tuple[Source, ...] = ()
    missing: tuple[str, ...] = ()

    # -- serialisation ---------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """Plain JSON-able form."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Dossier":
        """Inverse of :meth:`to_dict`."""
        return cls(
            topic=d["topic"],
            subject=d.get("subject"),
            artist=d.get("artist"),
            summary=d.get("summary", ""),
            facts=tuple(Fact(**f) for f in d.get("facts", ())),
            lyrics=d.get("lyrics"),
            annotations=tuple(Annotation(**a) for a in d.get("annotations", ())),
            timed_lines=tuple(TimedLine(**t) for t in d.get("timed_lines", ())),
            sources=tuple(Source(**s) for s in d.get("sources", ())),
            missing=tuple(d.get("missing", ())),
        )

    # -- what the writer reads -------------------------------------------
    @property
    def is_empty(self) -> bool:
        """True when research found nothing usable at all."""
        return not (self.summary or self.facts or self.lyrics or self.annotations)

    def as_brief(
        self, *, max_annotations: int = 16, annotation_chars: int = 550
    ) -> str:
        """The flat evidence brief handed to the writer.

        Sections are only emitted when they have content; the ``missing``
        section is emitted whenever something was looked for and not found,
        because that is the one thing a writer must not paper over.
        """
        parts: list[str] = [f"=== TOPIC ===\n{self.topic}"]
        if self.subject:
            head = self.subject + (f" — {self.artist}" if self.artist else "")
            parts.append(f"=== SUBJECT (resolved) ===\n{head}")
        if self.summary:
            parts.append(f"=== SUMMARY ===\n{self.summary.strip()}")
        if self.facts:
            lines = [f"- {f.text}  [{f.source_url}]" for f in self.facts]
            parts.append("=== FACTS (each with its source) ===\n" + "\n".join(lines))
        if self.lyrics:
            parts.append(
                f"=== FULL LYRICS (verbatim; do NOT quote at length) ===\n{self.lyrics.strip()}"
            )
        if self.timed_lines:
            lines = [f"[{t.index:02d}] {t.text}" for t in self.timed_lines]
            parts.append(
                "=== TIMED LINES (exact text; these are the only clips that can be cut) ===\n"
                + "\n".join(lines)
            )
        if self.annotations:
            top = sorted(self.annotations, key=lambda a: (-int(a.verified), -a.votes))
            lines = []
            for a in top[:max_annotations]:
                tag = "VERIFIED" if a.verified else f"{a.votes} votes"
                lines.append(f'- "{a.fragment}" ({tag}): {a.body[:annotation_chars]}')
            parts.append(
                "=== ANNOTATIONS (mine for the concrete and the surprising) ===\n"
                + "\n".join(lines)
            )
        if self.sources:
            lines = [f"- {s.title or s.url} <{s.url}>" for s in self.sources]
            parts.append("=== SOURCES CONSULTED ===\n" + "\n".join(lines))
        if self.missing:
            lines = [f"- {m}" for m in self.missing]
            parts.append(
                "=== NOT FOUND (say so if it matters; never invent it) ===\n"
                + "\n".join(lines)
            )
        return "\n\n".join(parts)


def merge(topic: str, parts: Iterable[Dossier]) -> Dossier:
    """Fold several researchers' dossiers into one.

    Scalars are first-non-empty-wins in researcher order; sequences are
    concatenated in that order, with duplicate sources (by URL) dropped.
    """
    parts = list(parts)
    out: dict[str, Any] = {"topic": topic}
    for f in fields(Dossier):
        if f.name == "topic":
            continue
        values = [getattr(p, f.name) for p in parts]
        if f.type.startswith("tuple"):
            seq: list[Any] = []
            seen: set[str] = set()
            for v in values:
                for item in v:
                    key = getattr(item, "url", None) if f.name == "sources" else None
                    if key is not None:
                        if key in seen:
                            continue
                        seen.add(key)
                    seq.append(item)
            out[f.name] = tuple(seq)
        else:
            out[f.name] = next(
                (v for v in values if v), Dossier.__dataclass_fields__[f.name].default
            )
    return Dossier(**out)
