"""Writers — reusable, parametrized authors of spoken commentary.

A :class:`Writer` is **data**: a brief (how this writer writes and what it
looks for), a braidio format whose ``scripting`` guidance it inherits, two to
four critic voices it blends from the style library, the researchers it sends
out first, a word budget, a gate list, a model. Three ship — ``general``,
``technical``, ``song`` — read from ``griot/data/writers/*.md``; more are one
Markdown file away (:func:`register_writer` for an in-process one).

Writing is **one planned LLM call** through ``falaw`` (``plan_write``), so the
price is on the plan before anything is spent (``quote``), the call is
content-cached, and an unpriced model sets ``has_unknown_costs`` rather than
reading as free. ``write`` runs the call, parses the reply into a real
``braidio.Script`` plus one picture hint per beat, runs the gates, and — if
they fail — sends the findings back for at most ``max_revisions`` rewrites.
A draft that still fails is returned *with its report*; nothing is silently
shipped and nothing is silently dropped.

The ``complete`` seam on :func:`write` is how tests and dry runs replace the
LLM: any ``(plan) -> (reply_text, cost_usd)`` callable.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any, Callable

import braidio
from braidio.cost import tts_cost_usd
from braidio.formats import FORMATS
from falaw import Plan, execute_plan_isolated, plan_llm_complete

from .dossier import Dossier
from .gates import DraftFacts, GateReport, run_gates
from .style import checklist, voice_card, voice_guide_rules

__all__ = [
    "DEFAULT_MODEL",
    "Draft",
    "PictureHint",
    "Quote",
    "WRITERS",
    "Writer",
    "draft_from_reply",
    "get_writer",
    "plan_write",
    "quote",
    "register_writer",
    "write",
]

DEFAULT_MODEL = "anthropic/claude-sonnet-4.5"
"""A fal any-llm id with a per-token rate in falaw's table; the seam is ``Writer.model``."""

RECORD_VOICE_ID = "nPczCjzI2devNBz1zQrb"
"""The second voice for the documented record (Brian): deep, level, ~4 semitones under the presenter."""

CHARS_PER_WORD = 6.5
"""Spoken English incl. spaces and a tag budget — what the TTS quote is computed on."""

OUTPUT_TOKENS_PER_WORD = 4
OUTPUT_TOKENS_FLOOR = 1500
TEMPERATURE = 0.7

Complete = Callable[[Plan], tuple[str, float]]
"""``(plan) -> (reply_text, cost_usd_actual)`` — the LLM seam."""


# ---------------------------------------------------------------------------
# The nouns
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Writer:
    """A reusable author. See the module docstring."""

    name: str
    title: str
    brief: str
    blurb: str = ""
    format_id: str = "solo_explainer"
    voices: tuple[str, ...] = ()
    researchers: tuple[str, ...] = ("wikipedia",)
    words_per_minute: int = 150
    max_revisions: int = 1
    model: str = DEFAULT_MODEL
    gates: tuple[str, ...] = ("platitudes", "expressiveness", "lyric_leak", "length", "shape")
    default_minutes: int = 3

    def target_words(self, minutes: float) -> int:
        return int(round(minutes * self.words_per_minute))

    @property
    def format(self):  # -> braidio.formats.Format
        return FORMATS[self.format_id]


@dataclass(frozen=True)
class PictureHint:
    """What picture the writer wants over a beat, and why — the placement's provenance."""

    beat_index: int
    query: str
    subject: str
    why: str
    source: str | None = None  # "wikimedia" | "openverse" | None (any)


@dataclass(frozen=True)
class Draft:
    """A written, gated script — the writer's deliverable."""

    script: braidio.Script
    picture_hints: tuple[PictureHint, ...]
    report: GateReport
    dossier: Dossier
    writer: str
    model: str
    minutes: float
    revisions: int = 0
    cost_usd_actual: float = 0.0
    sources_used: tuple[str, ...] = ()
    dropped: tuple[str, ...] = ()  # beats the parser refused, with why
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.report.ok

    def narration_text(self) -> str:
        return "\n\n".join(b.text for b in self.script.beats if isinstance(b, braidio.Narration))

    def to_dict(self) -> dict[str, Any]:
        """JSON-able; the script in braidio's MCP shape."""
        from braidio.mcp._helpers import to_json as _script_to_json

        return {
            "writer": self.writer,
            "model": self.model,
            "minutes": self.minutes,
            "revisions": self.revisions,
            "ok": self.ok,
            "findings": [{"gate": f.gate, "message": f.message} for f in self.report.findings],
            "cost_usd_actual": self.cost_usd_actual,
            "script": _script_to_json(self.script),
            "picture_hints": [h.__dict__ for h in self.picture_hints],
            "sources_used": list(self.sources_used),
            "dropped": list(self.dropped),
        }


@dataclass(frozen=True)
class Quote:
    """The price of writing and voicing, composed before anything runs."""

    llm_usd: float | None
    llm_unknown: bool
    tts_usd: float | None
    tts_unknown: bool
    calls: int
    target_words: int
    model: str
    tts_model: str

    @property
    def total_usd(self) -> float:
        return (self.llm_usd or 0.0) + (self.tts_usd or 0.0)

    @property
    def has_unknown_costs(self) -> bool:
        return self.llm_unknown or self.tts_unknown

    def to_dict(self) -> dict[str, Any]:
        return {
            "llm_usd": self.llm_usd,
            "llm_unknown": self.llm_unknown,
            "tts_usd": self.tts_usd,
            "tts_unknown": self.tts_unknown,
            "calls": self.calls,
            "target_words": self.target_words,
            "model": self.model,
            "tts_model": self.tts_model,
            "total_usd": self.total_usd,
            "has_unknown_costs": self.has_unknown_costs,
        }


# ---------------------------------------------------------------------------
# The registry
# ---------------------------------------------------------------------------

_LIST_FIELDS = {"voices", "researchers", "gates"}
_INT_FIELDS = {"words_per_minute", "max_revisions", "default_minutes"}


def _parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("a writer file starts with a '---' front-matter block")
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def writer_from_markdown(text: str) -> Writer:
    """Build a :class:`Writer` from a front-matter + brief Markdown file."""
    meta, brief = _parse_front_matter(text)
    kw: dict[str, Any] = {"brief": brief}
    for k, v in meta.items():
        if k in _LIST_FIELDS:
            kw[k] = tuple(x.strip() for x in v.split(",") if x.strip())
        elif k in _INT_FIELDS:
            kw[k] = int(v)
        else:
            kw[k] = v
    return Writer(**kw)


def _writers_dir() -> Path:
    return Path(str(resources.files("griot").joinpath("data", "writers")))


@lru_cache(maxsize=None)
def _shipped_writers() -> dict[str, Writer]:
    out: dict[str, Writer] = {}
    for path in sorted(_writers_dir().glob("*.md")):
        w = writer_from_markdown(path.read_text(encoding="utf-8"))
        out[w.name] = w
    return out


WRITERS: dict[str, Writer] = dict(_shipped_writers())
"""Every writer by name — the three shipped ones plus anything registered."""


def register_writer(writer: Writer) -> Writer:
    """Make ``writer`` available by name (replaces a same-named one)."""
    WRITERS[writer.name] = writer
    return writer


def get_writer(name: str | Writer) -> Writer:
    """Resolve a name to a :class:`Writer`; a Writer passes through."""
    if isinstance(name, Writer):
        return name
    try:
        return WRITERS[name]
    except KeyError:
        raise KeyError(f"unknown writer {name!r}; known: {sorted(WRITERS)}") from None


# ---------------------------------------------------------------------------
# The prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You write spoken commentary that will be read aloud by a text-to-speech voice and cut into a short film over still pictures. You answer with ONE JSON object and nothing else: no prose before or after it, no code fence.

The JSON object:
{
  "title": string,                       // the film's title
  "id_slug": string,                     // short, lowercase, hyphenated
  "beats": [                             // in speaking order
    {"type": "narration", "text": string, "role": "presenter" | "record", "lead_gap_s": number},
    {"type": "segment", "reference": string, "placement": "before" | "after" | "under"}   // ONLY if TIMED LINES were provided; reference = the exact timed-line text
  ],
  "picture_hints": [                     // exactly one per beat, by index into "beats"
    {"beat_index": int, "query": string, "subject": string, "why": string, "source": "wikimedia" | "openverse" | null}
  ],
  "sources_used": [string]               // the URLs from the dossier you actually leaned on
}

"role": "presenter" is your argument. "role": "record" is the documented record — dates, names, sourced quotes, a passage from a source — read by a second, graver voice; write it declaratively, chronologically, with almost no tags. Use "record" only when the material genuinely is record.
"lead_gap_s" is silence before the beat (0.3–0.6 after a clip or before a record block, else 0).
A picture hint's "query" is a search query for a freely-licensed photograph or artwork that fits the words spoken over THAT beat — specific, drawn from the research (a place, a person, an object, a period document), never the topic name alone. "subject" is the short label a viewer will read under the picture ("Trinity Church, Manhattan"); "why" is one sentence on why this picture over these words. Prefer "wikimedia" for a named person, place, artwork or document; "openverse" for texture and mood."""

HOUSE_RULES = """HOUSE RULES (each one cost a real episode):
- Every claim comes from the dossier. If the dossier does not have it, do not say it. If something you need is listed under NOT FOUND, work around it or say plainly that it is unknown — never invent a lyric, a quote, a date, an annotation.
- Never impersonate the artist or any real person. Quote briefly and attribute; do not write in their first person.
- Quote lyrics only as brief, attributed fragments (a few words). Never a whole line of four or more words verbatim, never a stanza.
- Ration the designed epigram: at most two memorable turns of phrase in three minutes. The rest is plain talk — contractions, fragments, uneven sentence length. A polished line at the end of every beat is the machine tell.
- Write the performance into the text: 2–5 inline [audio tags] per 100 words, and vary them — [laughs] [sighs] [dryly] [incredulous] [excited] [quietly] [rushed] [slowly] [pause] [beat] [curious] [wryly]. Under-tagged reads as somniferous.
- Vary the shape of the movements. Not claim → example → analysis every time. Open cold on a concrete particular at least once; let one beat be a single sentence; put a record block between two of your own.
- Give documented fact a second voice ("record") rather than folding it into your own; the handoff tells the listener the register changed without a word of signposting.
- Every beat gets a picture that fits the words spoken over it, and the hint says why. A picture chosen for the topic rather than the sentence is a decoration nobody can defend.
- Hit the word budget. It is what the price was quoted on."""


def _fence_strip(text: str) -> str:
    t = text.strip()
    m = re.match(r"^```(?:json)?\s*(.*?)\s*```$", t, re.S)
    return m.group(1) if m else t


def build_prompt(
    writer: Writer,
    dossier: Dossier,
    *,
    minutes: float,
    angle: str = "",
    findings: GateReport | None = None,
    previous: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """The ``(system, user)`` pair for one write or one revision."""
    target = writer.target_words(minutes)
    fmt = writer.format
    parts: list[str] = []
    parts.append(f"=== THE WRITER: {writer.title} ===\n{writer.brief}")
    if writer.voices:
        cards = "\n\n".join(voice_card(v) for v in writer.voices)
        parts.append(
            "=== VOICES TO BLEND (borrow from each; impersonate none) ===\n"
            f"{voice_guide_rules()}\n\n{cards}"
        )
    parts.append("=== ANTI-PLATITUDE CHECKLIST ===\n" + checklist())
    parts.append(f"=== THE FORMAT ({fmt.id}) ===\n{fmt.scripting}")
    parts.append(HOUSE_RULES)
    job = [
        f"Length: {minutes:g} minutes spoken ≈ {target} words of narration (±20%).",
        f"Delivery: {fmt.narration_delivery.model_id} ({'renders [audio tags]' if fmt.narration_delivery.supports_audio_tags else 'reads tags as text — use none'}).",
    ]
    if dossier.timed_lines:
        job.append("Source clips: TIMED LINES are available; you may cut 2–4 short segments (1–3 consecutive lines each), placed before/after/under a beat. Their rights are third-party.")
    else:
        job.append("Source clips: none available. Narration only — do not emit segment beats.")
    if angle:
        job.append(f"The angle the user asked for: {angle}")
    parts.append("=== THE JOB ===\n" + "\n".join(job))
    parts.append("=== THE DOSSIER (your only evidence) ===\n" + dossier.as_brief())
    if previous is not None and findings is not None:
        parts.append(
            "=== REVISION ===\nYour previous draft failed these gates. Fix each finding and return the whole JSON object again, keeping what worked.\n"
            f"FINDINGS:\n{findings.as_notes()}\n\nPREVIOUS DRAFT:\n{json.dumps(previous, ensure_ascii=False)}"
        )
    return SYSTEM_PROMPT, "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Plan, quote, write
# ---------------------------------------------------------------------------


def plan_write(
    writer: Writer,
    dossier: Dossier,
    *,
    minutes: float,
    angle: str = "",
    findings: GateReport | None = None,
    previous: dict[str, Any] | None = None,
) -> Plan:
    """The one-call falaw plan for a write (or a revision). Pure; spends nothing."""
    system, user = build_prompt(writer, dossier, minutes=minutes, angle=angle, findings=findings, previous=previous)
    target = writer.target_words(minutes)
    call = plan_llm_complete(
        user,
        system=system,
        model=writer.model,
        temperature=TEMPERATURE,
        output_kind="json",
        input_tokens=len(user.encode("utf-8")) + len(system.encode("utf-8")),  # upper bound: a token per byte
        max_output_tokens=max(OUTPUT_TOKENS_FLOOR, target * OUTPUT_TOKENS_PER_WORD),
        metadata={
            "griot": {"writer": writer.name, "format": writer.format_id, "minutes": minutes, "revision": previous is not None}
        },
    )
    return Plan(calls=(call,))


def quote(writer: Writer | str, dossier: Dossier, *, minutes: float | None = None) -> Quote:
    """Price the write (all its calls) and the voicing (from the word budget)."""
    w = get_writer(writer)
    minutes = w.default_minutes if minutes is None else minutes
    plan = plan_write(w, dossier, minutes=minutes)
    calls = 1 + w.max_revisions
    per_call = plan.total_cost_usd if not plan.has_unknown_costs else None
    target = w.target_words(minutes)
    tts_model = w.format.narration_delivery.model_id
    tts = tts_cost_usd("x" * int(target * CHARS_PER_WORD), model_id=tts_model)
    return Quote(
        llm_usd=None if per_call is None else per_call * calls,
        llm_unknown=plan.has_unknown_costs,
        tts_usd=tts,
        tts_unknown=tts is None,
        calls=calls,
        target_words=target,
        model=w.model,
        tts_model=tts_model,
    )


def _complete_via_falaw(plan: Plan, *, use_cache: bool = True) -> tuple[str, float]:
    report = execute_plan_isolated(plan, use_cache=use_cache, halt_on_failure=True)
    report.artifacts_or_raise()
    art = list(report.produced)[0]
    if not art.path:
        raise RuntimeError("the LLM artifact has no path to read")
    return Path(art.path).read_text(encoding="utf-8"), float(art.cost_usd or 0.0)


def draft_from_reply(
    reply: str,
    writer: Writer,
    dossier: Dossier,
    *,
    minutes: float,
    revisions: int = 0,
    cost_usd_actual: float = 0.0,
) -> Draft:
    """Parse the model's JSON into a gated :class:`Draft`. Raises ``ValueError`` on malformed JSON."""
    try:
        obj = json.loads(_fence_strip(reply))
    except json.JSONDecodeError as e:
        raise ValueError(f"the writer's reply was not valid JSON ({e}); first 200 chars: {reply[:200]!r}") from e
    if not isinstance(obj, dict) or not isinstance(obj.get("beats"), list):
        raise ValueError("the writer's reply is not an object with a 'beats' list")

    beats: list[Any] = []
    dropped: list[str] = []
    timed_texts = {t.text.strip().lower() for t in dossier.timed_lines}
    for i, b in enumerate(obj["beats"]):
        kind = (b or {}).get("type")
        if kind == "narration":
            text = str(b.get("text") or "").strip()
            if not text:
                dropped.append(f"beat {i}: empty narration")
                continue
            role = b.get("role") or "presenter"
            gap = float(b.get("lead_gap_s") or 0.0)
            if role == "record":
                beats.append(
                    braidio.Narration(
                        text,
                        voice=RECORD_VOICE_ID,
                        style="archive",
                        voice_settings=braidio.V3_NARRATOR.voice_settings,
                        lead_gap_s=max(gap, 0.5),
                    )
                )
            else:
                beats.append(braidio.Narration(text, lead_gap_s=gap))
        elif kind == "segment":
            ref = str(b.get("reference") or "").strip()
            if not dossier.timed_lines or ref.lower() not in timed_texts:
                dropped.append(f"beat {i}: segment {ref!r} does not name a timed line")
                continue
            placement = b.get("placement") or "before"
            beats.append(braidio.SegmentBeat(ref, rights="copyright-third-party", placement=placement))
        else:
            dropped.append(f"beat {i}: unknown beat type {kind!r}")

    hints: list[PictureHint] = []
    for h in obj.get("picture_hints") or []:
        try:
            hints.append(
                PictureHint(
                    beat_index=int(h["beat_index"]),
                    query=str(h["query"]).strip(),
                    subject=str(h.get("subject") or "").strip(),
                    why=str(h.get("why") or "").strip(),
                    source=h.get("source") or None,
                )
            )
        except (KeyError, TypeError, ValueError):
            dropped.append(f"picture hint {h!r} is malformed")

    title = str(obj.get("title") or dossier.subject or dossier.topic)
    slug = re.sub(r"[^a-z0-9]+", "-", str(obj.get("id_slug") or title).lower()).strip("-")[:48] or "film"
    script = braidio.Script(title=title, id_slug=slug, beats=beats)

    narr = [b.text for b in beats if isinstance(b, braidio.Narration)]
    hinted = len({h.beat_index for h in hints if 0 <= h.beat_index < len(beats)})
    facts = DraftFacts(
        narration=narr,
        beat_count=len(beats),
        hinted_beats=hinted,
        target_words=writer.target_words(minutes),
        tags_expected=writer.format.narration_delivery.supports_audio_tags,
        lyrics=dossier.lyrics,
    )
    report = run_gates(facts, names=writer.gates)
    return Draft(
        script=script,
        picture_hints=tuple(hints),
        report=report,
        dossier=dossier,
        writer=writer.name,
        model=writer.model,
        minutes=minutes,
        revisions=revisions,
        cost_usd_actual=cost_usd_actual,
        sources_used=tuple(str(s) for s in obj.get("sources_used") or ()),
        dropped=tuple(dropped),
        raw=obj,
    )


def write(
    writer: Writer | str,
    dossier: Dossier,
    *,
    minutes: float | None = None,
    angle: str = "",
    complete: Complete | None = None,
    use_cache: bool = True,
) -> Draft:
    """Research → this. Write, gate, revise at most ``max_revisions`` times, return the draft with its report."""
    w = get_writer(writer)
    minutes = w.default_minutes if minutes is None else minutes
    run: Complete = complete if complete is not None else (lambda p: _complete_via_falaw(p, use_cache=use_cache))
    spent = 0.0
    plan = plan_write(w, dossier, minutes=minutes, angle=angle)
    reply, cost = run(plan)
    spent += cost
    draft = draft_from_reply(reply, w, dossier, minutes=minutes, cost_usd_actual=spent)
    for n in range(1, w.max_revisions + 1):
        if draft.ok:
            break
        plan = plan_write(w, dossier, minutes=minutes, angle=angle, findings=draft.report, previous=draft.raw)
        reply, cost = run(plan)
        spent += cost
        draft = draft_from_reply(reply, w, dossier, minutes=minutes, revisions=n, cost_usd_actual=spent)
    return replace(draft, cost_usd_actual=spent)

