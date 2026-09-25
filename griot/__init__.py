"""griot — research a subject, then write the spoken commentary about it.

A griot knows the record and performs it. This package does the two halves
that sit *before* a braidio production: **research** (tokenless fetchers that
turn a topic into a :class:`Dossier` of sourced evidence) and **writing**
(reusable, parametrized :class:`Writer` objects that turn a dossier into a
gated ``braidio.Script`` plus one picture hint per beat). The output is what
``braidio.weave_project`` voices and what a picture track is planned over.

Shortest path::

    import griot

    w = griot.get_writer("song")
    dossier = griot.research("The Sound of Silence by Simon & Garfunkel", researchers=w.researchers)
    q = griot.quote(w, dossier, minutes=3)        # priced before anything runs
    draft = griot.write(w, dossier, minutes=3)    # one LLM call (+ one gated revision), cached
    draft.script                                   # a braidio.Script
    draft.picture_hints                            # one per beat, with why
    draft.report                                   # the gates' findings, empty when it passed

The LLM path is ``falaw`` (fal any-llm), so the price is on the plan and the
call is content-cached; ``write(..., complete=fake)`` replaces it for tests.
"""

from .dossier import Annotation, Dossier, Fact, Source, TimedLine, merge
from .gates import Finding, GateReport, run_gates
from .research import RESEARCHERS, Http, HttpxHttp, register_researcher, research
from .style import checklist, list_voices, voice_card
from .writers import (
    DEFAULT_MODEL,
    WRITERS,
    Draft,
    PictureHint,
    Quote,
    Writer,
    build_prompt,
    draft_from_reply,
    get_writer,
    plan_write,
    quote,
    register_writer,
    write,
    writer_from_markdown,
)

__all__ = [
    "Annotation",
    "DEFAULT_MODEL",
    "Dossier",
    "Draft",
    "Fact",
    "Finding",
    "GateReport",
    "Http",
    "HttpxHttp",
    "PictureHint",
    "Quote",
    "RESEARCHERS",
    "Source",
    "TimedLine",
    "WRITERS",
    "Writer",
    "build_prompt",
    "checklist",
    "draft_from_reply",
    "get_writer",
    "list_voices",
    "merge",
    "plan_write",
    "quote",
    "register_researcher",
    "register_writer",
    "research",
    "run_gates",
    "voice_card",
    "write",
    "writer_from_markdown",
]
