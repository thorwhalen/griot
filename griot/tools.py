"""The SSOT verbs — plain functions, JSON-able in, JSON-able out.

``python -m griot`` dispatches these with ``cw``; an MCP or HTTP adapter
references them by string (``griot.tools:write``) and gets a dict back. No
live object crosses the boundary and nothing here prints or exits.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .dossier import Dossier
from .research import research as _research
from .writers import WRITERS, get_writer
from .writers import quote as _quote
from .writers import write as _write

__all__ = ["quote", "research", "write", "writers"]


def writers() -> list[dict[str, Any]]:
    """The writers available, with what a picker needs to show."""
    return [
        {
            "name": w.name,
            "title": w.title,
            "blurb": w.blurb,
            "format_id": w.format_id,
            "voices": list(w.voices),
            "researchers": list(w.researchers),
            "default_minutes": w.default_minutes,
            "words_per_minute": w.words_per_minute,
            "model": w.model,
        }
        for w in WRITERS.values()
    ]


def research(topic: str, *, writer: str = "general") -> dict[str, Any]:
    """Run the writer's researchers on ``topic``; the dossier as JSON."""
    w = get_writer(writer)
    return _research(topic, researchers=w.researchers).to_dict()


def quote(topic: str, *, writer: str = "general", minutes: float = 0.0) -> dict[str, Any]:
    """Price the write and the voicing for ``topic`` before spending anything (research runs; it is free)."""
    w = get_writer(writer)
    d = _research(topic, researchers=w.researchers)
    q = _quote(w, d, minutes=minutes or None)
    return {**q.to_dict(), "subject": d.subject, "missing": list(d.missing)}


def write(
    topic: str,
    *,
    writer: str = "general",
    minutes: float = 0.0,
    angle: str = "",
    out: str = "",
    fake: bool = False,
) -> dict[str, Any]:
    """Research, write, gate; the draft as JSON (and to ``out`` if given).

    ``fake=True`` replaces the LLM with a canned reply so the whole path runs
    without a key or a cent — the CLI's smoke test.
    """
    w = get_writer(writer)
    d = _research(topic, researchers=w.researchers)
    complete = _fake_complete(w, d, minutes or w.default_minutes) if fake else None
    draft = _write(w, d, minutes=minutes or None, angle=angle, complete=complete)
    payload = draft.to_dict()
    payload["dossier"] = d.to_dict()
    if out:
        Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payload["written_to"] = out
    return payload


def _fake_complete(w, d: Dossier, minutes: float):
    """A reply-shaped stand-in: enough beats and hints to pass the gates."""
    target = w.target_words(minutes)
    n_beats = 5
    per = max(1, target // n_beats)
    tags = ["[curious]", "[pause]", "[dryly]", "[quietly]", "[beat]", "[wryly]"]
    subject = d.subject or d.topic
    beats = []
    for i in range(n_beats):
        words: list[str] = []
        k = 0
        while len(words) < per:
            words.extend([tags[(i + k) % len(tags)], "about", subject + ",", "and", "then", "what", "it", "meant", "to", "them", "that", "year", "in", "the", "city."])
            k += 1
        beats.append({"type": "narration", "text": " ".join(words[:per + 3]), "role": "record" if i == 2 else "presenter", "lead_gap_s": 0.4 if i else 0.0})
    hints = [{"beat_index": i, "query": f"{subject} beat {i}", "subject": subject, "why": "fake", "source": None} for i in range(n_beats)]
    reply = json.dumps({"title": subject, "id_slug": "fake", "beats": beats, "picture_hints": hints, "sources_used": [s.url for s in d.sources]})
    return lambda plan: (reply, 0.0)
