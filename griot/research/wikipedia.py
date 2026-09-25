"""Wikipedia researcher — search, the summary, and the lead of the top page.

Two tokenless endpoints: the MediaWiki action API for search and the plain
extract, and the REST summary for the description line. The top search hit is
taken only when its title shares a content word with the topic; otherwise the
dossier records the miss instead of a page about something else.
"""

from __future__ import annotations

import re

from ..dossier import Dossier, Fact, Source
from . import Http, register_researcher

API = "https://en.wikipedia.org/w/api.php"
REST_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
PAGE = "https://en.wikipedia.org/wiki/"

MAX_EXTRACT_CHARS = 6000
"""How much of the page's plain extract becomes facts (the lead and a little)."""

_STOP = {"the", "a", "an", "of", "and", "in", "on", "by", "to", "for", "is", "song", "about", "film", "book", "album"}


def content_words(text: str) -> set[str]:
    """Lower-cased alphanumeric words minus stopwords, plurals folded."""
    out = set()
    for w in re.findall(r"[a-z0-9']+", text.lower()):
        if w in _STOP or len(w) < 2:
            continue
        out.add(w[:-1] if w.endswith("s") and len(w) > 3 else w)
    return out


def split_topic(topic: str) -> tuple[str, str | None]:
    """``"Burn by Original Broadway Cast"`` -> ``("Burn", "Original Broadway Cast")``; no ``by`` -> ``(topic, None)``."""
    m = re.match(r"^(.*\S)\s+(?:by|-|—)\s+(\S.*)$", topic.strip(), re.I)
    if m and len(m.group(1)) >= 2:
        return m.group(1).strip().strip('"'), m.group(2).strip()
    return topic.strip().strip('"'), None


def best_hit(results: list[dict], work: str, *, artist: str | None = None) -> dict | None:
    """The hit whose title is most nearly the work; ``None`` when no title shares a content word.

    Score = precision (share of the title's content words found in the work)
    + recall (share of the work's words found in the title) + 1 for an exact
    title match + 0.25 when the artist's name appears in the title (a "(Simon
    & Garfunkel song)" disambiguator) + a small bonus for search rank, so a
    near-tie goes to Wikipedia's own ordering.
    """
    wanted = content_words(work)
    if not wanted:
        return None
    # A named work (an artist was given) must match nearly whole: "Actually
    # Sweet" must not resolve to "Actually Romantic". A loose topic may.
    min_fit = 1.5 if artist else 0.6
    best, best_score = None, 0.0
    for rank, r in enumerate(results):
        title = r["title"]
        tw = content_words(title)
        if not tw & wanted:
            continue
        fit = len(tw & wanted) / len(tw) + len(tw & wanted) / len(wanted)
        if fit < min_fit:
            continue
        score = fit + 0.3 / (rank + 1)
        if re.sub(r"\s+", " ", title.lower()) == re.sub(r"\s+", " ", work.lower()):
            score += 1.0
        if artist and content_words(artist) & content_words(title):
            score += 0.25
        if score > best_score:
            best, best_score = r, score
    return best


def _paragraph_facts(extract: str, url: str) -> list[Fact]:
    paras = [p.strip() for p in extract.split("\n") if p.strip()]
    facts: list[Fact] = []
    used = 0
    for p in paras:
        if p.startswith("=="):  # section heading
            continue
        if used + len(p) > MAX_EXTRACT_CHARS:
            break
        facts.append(Fact(text=p, source_url=url))
        used += len(p)
    return facts


@register_researcher("wikipedia")
def wikipedia(topic: str, *, prior: Dossier, http: Http) -> Dossier:
    """Resolve ``topic`` to one page and read its lead."""
    work, artist = split_topic(prior.subject or topic)
    artist = artist or prior.artist
    query = f'"{work}" {artist}' if artist else work
    hits = http.json(
        API,
        params={"action": "query", "list": "search", "srsearch": query, "srlimit": 6, "format": "json"},
    )
    results = (hits.get("query") or {}).get("search") or []
    if not results:
        return Dossier(topic=topic, missing=(f"wikipedia: no page found for {query!r}",))
    top = best_hit(results, work, artist=artist)
    if top is None:
        titles = ", ".join(r["title"] for r in results[:3])
        return Dossier(topic=topic, missing=(f"wikipedia: nothing matching {query!r} (nearest: {titles})",))
    title = top["title"]
    url = PAGE + title.replace(" ", "_")

    summary = http.json(REST_SUMMARY + title.replace(" ", "_"))
    description = summary.get("description") or ""
    lead = summary.get("extract") or ""

    page = http.json(
        API,
        params={"action": "query", "prop": "extracts", "explaintext": 1, "titles": title, "format": "json", "redirects": 1},
    )
    pages = (page.get("query") or {}).get("pages") or {}
    extract = next(iter(pages.values()), {}).get("extract", "") if pages else ""

    return Dossier(
        topic=topic,
        subject=title,
        summary=(f"{title} — {description}\n\n" if description else "") + lead,
        facts=tuple(_paragraph_facts(extract, url)),
        sources=(Source(url=url, title=title, kind="wikipedia"),),
    )
