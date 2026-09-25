"""Shared fakes: an in-memory :class:`griot.Http` and a canned dossier.

No test here reaches the network. ``FakeHttp`` answers by URL prefix (and
optionally by a param value) from dicts the test builds; an unknown URL
raises, which is what a researcher's soft-failure path is tested against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

import griot


@dataclass
class FakeHttp:
    """``json`` / ``text`` served from tables; every call is recorded."""

    json_routes: dict[str, Any] = field(default_factory=dict)
    text_routes: dict[str, str] = field(default_factory=dict)
    calls: list[tuple[str, dict | None]] = field(default_factory=list)

    def _match(self, table: dict[str, Any], url: str, params: dict | None) -> Any:
        self.calls.append((url, params))
        for key, value in table.items():
            if url.startswith(key):
                return value(params) if callable(value) else value
        raise RuntimeError(f"fake http: no route for {url}")

    def json(
        self, url: str, *, params: dict | None = None, headers: dict | None = None
    ) -> Any:
        return self._match(self.json_routes, url, params)

    def text(
        self, url: str, *, params: dict | None = None, headers: dict | None = None
    ) -> str:
        return self._match(self.text_routes, url, params)


@pytest.fixture
def dossier() -> griot.Dossier:
    return griot.Dossier(
        topic="The Sound of Silence by Simon & Garfunkel",
        subject="The Sound of Silence",
        artist="Simon & Garfunkel",
        summary="The Sound of Silence is a song by Simon & Garfunkel, released in 1964.",
        facts=(
            griot.Fact(
                "The acoustic version flopped in 1964.",
                "https://en.wikipedia.org/wiki/The_Sound_of_Silence",
            ),
            griot.Fact(
                "Tom Wilson overdubbed electric instruments in June 1965.",
                "https://en.wikipedia.org/wiki/The_Sound_of_Silence",
            ),
        ),
        lyrics="Hello darkness, my old friend\nI've come to talk with you again\nBecause a vision softly creeping\nLeft its seeds while I was sleeping",
        annotations=(
            griot.Annotation(
                "Hello darkness, my old friend",
                "Simon wrote it in the bathroom with the lights off.",
                votes=120,
            ),
        ),
        timed_lines=(
            griot.TimedLine(0, 0.0, 4.0, "Hello darkness, my old friend"),
            griot.TimedLine(1, 4.0, 8.0, "I've come to talk with you again"),
        ),
        sources=(
            griot.Source(
                "https://en.wikipedia.org/wiki/The_Sound_of_Silence",
                "The Sound of Silence",
                "wikipedia",
            ),
        ),
    )


def good_reply(
    dossier: griot.Dossier,
    *,
    words: int = 450,
    beats: int = 5,
    lyric_leak: bool = False,
) -> str:
    """A reply that passes every gate (or leaks a lyric line when asked)."""
    import json

    tags = [
        "[curious]",
        "[pause]",
        "[dryly]",
        "[quietly]",
        "[beat]",
        "[wryly]",
        "[slowly]",
    ]
    per = words // beats
    out = []
    for i in range(beats):
        toks: list[str] = []
        k = 0
        while len(toks) < per:
            toks += [
                tags[(i + k) % len(tags)],
                "the",
                "take",
                "in",
                "June",
                "nineteen",
                "sixty-five",
                "changed",
                "what",
                "the",
                "song",
                "was",
                "for,",
                "and",
                "the",
                "two",
                "men",
                "who",
                "had",
                "made",
                "it",
                "did",
                "not",
                "know",
                "it",
                "yet.",
            ]
            k += 1
        text = " ".join(toks[:per])
        if lyric_leak and i == 1:
            text += " Hello darkness, my old friend."
        out.append(
            {
                "type": "narration",
                "text": text,
                "role": "record" if i == 2 else "presenter",
                "lead_gap_s": 0.4 if i else 0,
            }
        )
    hints = [
        {
            "beat_index": i,
            "query": f"Columbia Studio A 1965 session {i}",
            "subject": "Columbia Studio A",
            "why": "the overdub session",
            "source": "wikimedia",
        }
        for i in range(beats)
    ]
    return json.dumps(
        {
            "title": "Two Silences",
            "id_slug": "two-silences",
            "beats": out,
            "picture_hints": hints,
            "sources_used": [dossier.sources[0].url],
        }
    )
