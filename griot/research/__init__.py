"""Research — tokenless fetchers that turn a topic into a :class:`~griot.dossier.Dossier`.

A *researcher* is a plain function ``(topic, *, prior, http) -> Dossier``:
``prior`` is what earlier researchers found (so ``lrclib`` can read the artist
``genius`` resolved), ``http`` is the one seam through which bytes come in
(:class:`Http`; tests pass a fake). Researchers are looked up by name in
:data:`RESEARCHERS`; :func:`research` runs a writer's list in order and merges.

Three ship, each free and keyless: ``wikipedia`` (search + summary + lead
extract), ``genius`` (song search, lyrics, per-line annotations — the tokenless
path graduated from ``hamilton_genius``, Hamilton#60) and ``lrclib`` (synced
lyric timings). A researcher that finds nothing contributes nothing and says
so in ``missing``; none of them substitutes the nearest match.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Protocol

import httpx

from ..dossier import Dossier, merge

__all__ = [
    "Http",
    "HttpxHttp",
    "RESEARCHERS",
    "Researcher",
    "register_researcher",
    "research",
]

USER_AGENT = "griot/0.0 (+https://github.com/thorwhalen/griot)"
"""Descriptive, per Wikimedia's policy — a vague UA is throttled like abuse."""


class Http(Protocol):
    """The bytes-in seam: two verbs, both GET."""

    def json(
        self, url: str, *, params: dict | None = None, headers: dict | None = None
    ) -> Any:
        """GET ``url`` and return the decoded JSON body."""

    def text(
        self, url: str, *, params: dict | None = None, headers: dict | None = None
    ) -> str:
        """GET ``url`` and return the body as text."""


@dataclass
class HttpxHttp:
    """The default :class:`Http`: httpx, a polite interval, bounded retries."""

    user_agent: str = USER_AGENT
    timeout: float = 30.0
    min_interval: float = 0.34
    max_retries: int = 3
    _last: float = field(default=0.0, repr=False)

    def _get(
        self, url: str, params: dict | None, headers: dict | None
    ) -> httpx.Response:
        h = {"User-Agent": self.user_agent, **(headers or {})}
        last: Exception | None = None
        for attempt in range(self.max_retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                r = httpx.get(
                    url,
                    params=params,
                    headers=h,
                    timeout=self.timeout,
                    follow_redirects=True,
                )
                if r.status_code == 429 or r.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"transient {r.status_code}", request=r.request, response=r
                    )
                r.raise_for_status()
                return r
            except httpx.HTTPError as e:
                last = e
                if attempt == self.max_retries:
                    break
                time.sleep(min(2**attempt, 8))
        raise RuntimeError(f"GET {url} failed after retries: {last}") from last

    def json(
        self, url: str, *, params: dict | None = None, headers: dict | None = None
    ) -> Any:
        return self._get(url, params, headers).json()

    def text(
        self, url: str, *, params: dict | None = None, headers: dict | None = None
    ) -> str:
        return self._get(url, params, headers).text


Researcher = Callable[..., Dossier]
"""``(topic: str, *, prior: Dossier, http: Http) -> Dossier``."""

RESEARCHERS: dict[str, Researcher] = {}


def register_researcher(name: str, fn: Researcher | None = None):
    """Register ``fn`` under ``name``; usable as a decorator."""

    def _reg(f: Researcher) -> Researcher:
        RESEARCHERS[name] = f
        return f

    return _reg if fn is None else _reg(fn)


def research(
    topic: str,
    *,
    researchers: Iterable[str] = ("wikipedia",),
    http: Http | None = None,
) -> Dossier:
    """Run ``researchers`` in order on ``topic`` and merge what they found.

    An unknown researcher name raises rather than being skipped, because a
    writer that silently lost its research would write from memory. A
    researcher that *fails* (a 403, a timeout) is recorded under ``missing``
    and the rest still run: the writer is told, not the exception.
    """
    http = http if http is not None else HttpxHttp()
    prior = Dossier(topic=topic)
    parts: list[Dossier] = []
    for name in researchers:
        try:
            fn = RESEARCHERS[name]
        except KeyError:
            raise KeyError(
                f"unknown researcher {name!r}; known: {sorted(RESEARCHERS)}"
            ) from None
        try:
            part = fn(topic, prior=prior, http=http)
        except Exception as e:  # noqa: BLE001 — one blocked source must not sink the film
            part = Dossier(
                topic=topic,
                missing=(f"{name}: failed ({type(e).__name__}: {str(e)[:160]})",),
            )
        parts.append(part)
        prior = merge(topic, parts)
    return prior


# Register the shipped researchers (import for side effect).
from . import genius as _genius  # noqa: E402,F401
from . import lrclib as _lrclib  # noqa: E402,F401
from . import wikipedia as _wikipedia  # noqa: E402,F401
