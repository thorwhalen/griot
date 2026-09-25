"""Genius researcher — a song's lyrics and its per-line annotations, no token.

Genius serves the same JSON envelope on its public web API
(``https://genius.com/api``) as on the official one, without a token, and the
lyrics come from the rendered song page. This is the tokenless path that made
three productions (Hamilton, Actually Romantic, Two Silences), graduated from
``hamilton_genius`` (Hamilton#60).

Two rules a real episode paid for:

- **The nearest match is not the match.** "Actually Sweet" does not exist and
  the search returns something; the researcher refuses a top hit that shares no
  content word with the topic and records the miss.
- **Annotations describe the WORK, not the RECORDING.** What is here is what
  Genius knows about the song; who made a particular take, when, and why is
  Wikipedia's job (and is why ``song`` writers run both).
"""

from __future__ import annotations

import os
import re
from typing import Any

from bs4 import BeautifulSoup, NavigableString, Tag

from ..dossier import Annotation, Dossier, Source
from . import Http, register_researcher
from .wikipedia import content_words, split_topic

PUBLIC_API = "https://genius.com/api"
OFFICIAL_API = "https://api.genius.com"
TOKEN_ENV = "GENIUS_ACCESS_TOKEN"
"""A Client Access Token (genius.com/api-clients). With it the official API serves search, songs and
referents; without it the public API is tried, which Cloudflare has been refusing to non-browsers
since at least 2026-09-25. Lyrics come from the song page either way, and that page is behind the
same wall — LRCLIB's ``plainLyrics`` is the fallback the ``lrclib`` researcher provides."""
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
"""The public endpoints and the song pages want a browser-like UA."""

MAX_ANNOTATIONS = 24
_JUNK_SELECTORS = (
    '[class*="LyricsHeader"]',
    '[class*="RightSidebar"]',
    '[class*="Ad__"]',
    "[data-exclude-from-selection]",
)


def _api(token: str | None) -> tuple[str, dict[str, str]]:
    """``(base_url, headers)`` — the official API when a token is set, else the public one."""
    if token:
        return OFFICIAL_API, {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
    return PUBLIC_API, {"User-Agent": BROWSER_UA, "Accept": "application/json"}


def search_songs(
    http: Http, query: str, *, limit: int = 5, token: str | None = None
) -> list[dict[str, Any]]:
    """Song stubs matching ``query``, best first (each has ``id``, ``title``, ``url``)."""
    base, headers = _api(token)
    path = "/search" if token else "/search/song"
    resp = http.json(f"{base}{path}", params={"q": query}, headers=headers)["response"]
    sections = resp.get("sections")
    hits = sections[0]["hits"] if sections else resp.get("hits", [])
    return [h["result"] for h in hits[:limit]]


def song(http: Http, song_id: int, *, token: str | None = None) -> dict[str, Any]:
    """The full song object."""
    base, headers = _api(token)
    return http.json(
        f"{base}/songs/{song_id}", params={"text_format": "plain"}, headers=headers
    )["response"]["song"]


def referents(
    http: Http,
    song_id: int,
    *,
    per_page: int = 50,
    max_pages: int = 6,
    token: str | None = None,
) -> list[dict[str, Any]]:
    """Every referent (annotated fragment) for a song, paginated."""
    base, headers = _api(token)
    out: list[dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        resp = http.json(
            f"{base}/referents",
            params={
                "song_id": song_id,
                "text_format": "plain",
                "per_page": per_page,
                "page": page,
            },
            headers=headers,
        )["response"]
        refs = resp.get("referents") or []
        out.extend(refs)
        if len(refs) < per_page:
            break
    return out


def extract_lyrics(html: str) -> str:
    """Plain-text lyrics from a Genius song page; ``""`` when there is no container."""
    soup = BeautifulSoup(html, "html.parser")
    containers = soup.select('div[data-lyrics-container="true"]')
    if not containers:
        legacy = soup.select_one(".lyrics")
        containers = [legacy] if legacy else []
    text = "\n".join(
        t for t in (_container_text(c) for c in containers if c is not None) if t
    )
    text = text.replace("\r\n", "\n").replace("\xa0", " ")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _container_text(container: Tag) -> str:
    for sel in _JUNK_SELECTORS:
        for junk in container.select(sel):
            junk.decompose()
    out: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, NavigableString):
            out.append(str(node))
            return
        if not isinstance(node, Tag):
            return
        if node.name == "br":
            out.append("\n")
            return
        for child in node.children:
            walk(child)
        if node.name in {"div", "p"}:
            out.append("\n")

    walk(container)
    return "".join(out)


def _annotations(refs: list[dict[str, Any]]) -> list[Annotation]:
    out: list[Annotation] = []
    for r in refs:
        fragment = (r.get("fragment") or "").strip()
        for a in r.get("annotations") or []:
            body = ((a.get("body") or {}).get("plain") or "").strip()
            if not body or not fragment:
                continue
            out.append(
                Annotation(
                    fragment=fragment,
                    body=body,
                    url=a.get("url") or r.get("url") or "",
                    verified=bool(a.get("verified")),
                    votes=int(a.get("votes_total") or 0),
                )
            )
    out.sort(key=lambda a: (-int(a.verified), -a.votes))
    return out[:MAX_ANNOTATIONS]


@register_researcher("genius")
def genius(topic: str, *, prior: Dossier, http: Http) -> Dossier:
    """Resolve ``topic`` to one song; bring its lyrics and annotations."""
    token = os.environ.get(TOKEN_ENV) or None
    work, artist_hint = split_topic(prior.subject or topic)
    query = f"{work} {artist_hint}" if artist_hint else work
    stubs = search_songs(http, query, token=token)
    wanted = content_words(work)
    top = next((s for s in stubs if content_words(s.get("title") or "") & wanted), None)
    if top is None:
        nearest = ", ".join(
            (s.get("full_title") or s.get("title") or "?") for s in stubs[:3]
        )
        return Dossier(
            topic=topic,
            missing=(
                f"genius: no song matching {query!r}"
                + (f" (nearest: {nearest})" if nearest else ""),
            ),
        )
    full = song(http, int(top["id"]), token=token)
    title = full.get("title") or top.get("title") or ""
    artist = (full.get("primary_artist") or {}).get("name") or (
        top.get("primary_artist") or {}
    ).get("name")
    url = full.get("url") or top.get("url") or ""
    missing: list[str] = []
    lyrics = ""
    try:
        html = http.text(url, headers={"User-Agent": BROWSER_UA}) if url else ""
        lyrics = extract_lyrics(html) if html else ""
    except Exception as e:  # noqa: BLE001 — the page is behind Cloudflare; lrclib carries plain lyrics
        missing.append(f"genius: the lyrics page was refused ({type(e).__name__})")
    anns = _annotations(referents(http, int(top["id"]), token=token))
    if not lyrics and not missing:
        missing.append(f"genius: the page for {title!r} had no lyrics container")
    if not anns:
        missing.append(f"genius: {title!r} has no annotations")
    release = full.get("release_date_for_display") or full.get("release_date") or ""
    summary = f"{title} — {artist}" + (f" ({release})" if release else "")
    return Dossier(
        topic=topic,
        subject=title,
        artist=artist,
        summary=summary,
        lyrics=lyrics or None,
        annotations=tuple(anns),
        sources=(
            Source(url=url, title=full.get("full_title") or title, kind="genius"),
        ),
        missing=tuple(missing),
    )
