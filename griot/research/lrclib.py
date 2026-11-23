"""LRCLIB researcher — crowd-synced lyric line timings, free, no key.

Line timing is what makes a lyric quotable *as audio*: a ``[start, end)`` window
per line is exactly what a segment source needs to cut a clip. This researcher
needs an artist, so it reads the subject and artist an earlier researcher
(``genius``) resolved; with no artist it records the miss.
"""

from __future__ import annotations

from typing import Any

from songsrc import parse_lrc as _parse_lrc

from ..dossier import Dossier, Source, TimedLine
from . import Http, register_researcher
from .wikipedia import split_topic

API = "https://lrclib.net/api"


def parse_lrc(synced: str) -> list[TimedLine]:
    """Parse an LRC blob into :class:`TimedLine` rows (``songsrc.parse_lrc`` under the dossier's row type)."""
    return [
        TimedLine(index=r.index, start_s=r.start_s, end_s=r.end_s, text=r.text)
        for r in _parse_lrc(synced)
    ]


def fetch_synced(http: Http, *, track: str, artist: str) -> dict[str, Any] | None:
    """The best LRCLIB record with ``syncedLyrics`` for a song, or ``None``."""
    try:
        rec = http.json(
            f"{API}/get", params={"track_name": track, "artist_name": artist}
        )
        if isinstance(rec, dict) and rec.get("syncedLyrics"):
            return rec
    except Exception:  # noqa: BLE001 — /get 404s on a miss; fall through to search
        pass
    for rec in http.json(f"{API}/search", params={"q": f"{track} {artist}"}) or []:
        if rec.get("syncedLyrics"):
            return rec
    return None


@register_researcher("lrclib")
def lrclib(topic: str, *, prior: Dossier, http: Http) -> Dossier:
    """Bring synced timings (and plain lyrics, if nobody else did) for the song.

    Reads the song and artist an earlier researcher resolved; failing that,
    ``"<work> by <artist>"`` in the topic itself. With neither, it records the
    miss — LRCLIB search without an artist returns covers first.
    """
    track, artist = prior.subject, prior.artist
    if not (track and artist):
        work, by = split_topic(topic)
        if by:
            track, artist = work, by
    if not (track and artist):
        return Dossier(
            topic=topic,
            missing=("lrclib: no song + artist to time (say '<song> by <artist>')",),
        )
    rec = fetch_synced(http, track=track, artist=artist)
    if rec is None:
        return Dossier(
            topic=topic,
            missing=(f"lrclib: no synced lyrics for {track!r} by {artist!r}",),
        )
    lines = parse_lrc(rec["syncedLyrics"])
    url = f"https://lrclib.net/api/get/{rec.get('id')}"
    plain = (rec.get("plainLyrics") or "").strip()
    return Dossier(
        topic=topic,
        subject=None if prior.subject else rec.get("trackName"),
        artist=None if prior.artist else rec.get("artistName"),
        lyrics=None if prior.lyrics else (plain or None),
        timed_lines=tuple(lines),
        sources=(
            Source(
                url=url,
                title=f"LRCLIB: {rec.get('trackName')} — {rec.get('artistName')}",
                kind="lrclib",
            ),
        ),
    )
