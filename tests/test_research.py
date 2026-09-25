"""The researchers, against a fake HTTP: resolution, refusal of the nearest match, soft failure, merge."""

from __future__ import annotations

import griot
from griot.research import research
from griot.research.wikipedia import best_hit, split_topic

from .conftest import FakeHttp

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"


def wiki_http(
    *titles: str, extract: str = "Lead paragraph.\n\n== History ==\nBuilt in 1846."
) -> FakeHttp:
    def api(params):
        if params.get("list") == "search":
            return {"query": {"search": [{"title": t} for t in titles]}}
        return {"query": {"pages": {"1": {"extract": extract}}}}

    return FakeHttp(
        json_routes={
            WIKI_API: api,
            WIKI_SUMMARY: {"description": "a church", "extract": "Lead paragraph."},
        }
    )


def test_split_topic():
    assert split_topic("The Sound of Silence by Simon & Garfunkel") == (
        "The Sound of Silence",
        "Simon & Garfunkel",
    )
    assert split_topic("Trinity Church Manhattan") == ("Trinity Church Manhattan", None)
    assert split_topic('"Burn" - Hamilton') == ("Burn", "Hamilton")


def test_best_hit_prefers_the_exact_title_over_the_album_ranked_first():
    hits = [
        {"title": "Sounds of Silence"},
        {"title": "The Sound of Silence"},
        {"title": "Simon & Garfunkel"},
    ]
    assert (
        best_hit(hits, "The Sound of Silence", artist="Simon & Garfunkel")["title"]
        == "The Sound of Silence"
    )
    assert best_hit([{"title": "Song"}, {"title": "Apple"}], "Trinity Church") is None


def test_wikipedia_resolves_and_cites_every_fact():
    http = wiki_http("Trinity Church (Manhattan)", "Trinity Church Cemetery")
    d = research("Trinity Church Manhattan", researchers=("wikipedia",), http=http)
    assert d.subject == "Trinity Church (Manhattan)"
    assert d.summary.startswith("Trinity Church (Manhattan) — a church")
    assert [f.text for f in d.facts] == ["Lead paragraph.", "Built in 1846."]
    assert all(
        f.source_url == "https://en.wikipedia.org/wiki/Trinity_Church_(Manhattan)"
        for f in d.facts
    )
    assert d.sources[0].kind == "wikipedia" and not d.missing


def test_wikipedia_refuses_the_nearest_match():
    d = research(
        "Actually Sweet by Taylor Swift",
        researchers=("wikipedia",),
        http=wiki_http("Actually Romantic", "Taylor Swift"),
    )
    assert d.subject is None and d.missing and "nothing matching" in d.missing[0]


def test_a_failing_researcher_is_recorded_not_raised():
    http = FakeHttp()  # every route raises
    d = research("anything", researchers=("genius", "wikipedia"), http=http)
    assert d.subject is None and len(d.missing) == 2
    assert d.missing[0].startswith("genius: failed") and d.missing[1].startswith(
        "wikipedia: failed"
    )
    assert "NOT FOUND" in d.as_brief()


def test_lrclib_times_and_carries_plain_lyrics_from_the_topic_alone():
    rec = {
        "id": 595765,
        "trackName": "The Sound of Silence",
        "artistName": "Simon & Garfunkel",
        "plainLyrics": "Hello darkness, my old friend\nI've come to talk with you again",
        "syncedLyrics": "[00:00.50] Hello darkness, my old friend\n[00:04.20] I've come to talk with you again\n[00:08.00] ",
    }
    http = FakeHttp(json_routes={"https://lrclib.net/api/get": rec})
    d = research(
        "The Sound of Silence by Simon & Garfunkel", researchers=("lrclib",), http=http
    )
    assert d.subject == "The Sound of Silence" and d.artist == "Simon & Garfunkel"
    assert d.lyrics.startswith("Hello darkness")
    assert [(t.index, t.start_s, t.end_s) for t in d.timed_lines] == [
        (0, 0.5, 4.2),
        (1, 4.2, 8.0),
    ]
    assert d.sources[0].kind == "lrclib"


def test_lrclib_without_an_artist_records_the_miss():
    d = research("Trinity Church", researchers=("lrclib",), http=FakeHttp())
    assert d.missing == ("lrclib: no song + artist to time (say '<song> by <artist>')",)


def test_genius_uses_the_official_api_with_a_token(monkeypatch):
    monkeypatch.setenv("GENIUS_ACCESS_TOKEN", "t0k")
    stub = {
        "id": 79538,
        "title": "The Sound of Silence",
        "full_title": "The Sound of Silence by Simon & Garfunkel",
        "url": "https://genius.com/x-lyrics",
        "primary_artist": {"name": "Simon & Garfunkel"},
    }
    http = FakeHttp(
        json_routes={
            "https://api.genius.com/search": {"response": {"hits": [{"result": stub}]}},
            "https://api.genius.com/songs/79538": {
                "response": {"song": {**stub, "release_date_for_display": "1964"}}
            },
            "https://api.genius.com/referents": {
                "response": {
                    "referents": [
                        {
                            "fragment": "Hello darkness",
                            "url": "u",
                            "annotations": [
                                {
                                    "body": {"plain": "bathroom, lights off"},
                                    "verified": True,
                                    "votes_total": 5,
                                }
                            ],
                        }
                    ]
                }
            },
        },
        text_routes={
            "https://genius.com/x-lyrics": '<div data-lyrics-container="true">Hello darkness<br/>my old friend</div>'
        },
    )
    d = research(
        "The Sound of Silence by Simon & Garfunkel", researchers=("genius",), http=http
    )
    assert d.subject == "The Sound of Silence" and d.artist == "Simon & Garfunkel"
    assert d.lyrics == "Hello darkness\nmy old friend"
    assert d.annotations[0].verified and d.annotations[0].body == "bathroom, lights off"
    api_calls = [u for u, _ in http.calls if "genius.com" in u and "-lyrics" not in u]
    assert len(api_calls) == 3 and all(
        u.startswith("https://api.genius.com") for u in api_calls
    )
    assert not d.missing


def test_genius_lyrics_page_refusal_is_soft(monkeypatch):
    monkeypatch.setenv("GENIUS_ACCESS_TOKEN", "t0k")
    stub = {
        "id": 1,
        "title": "Burn",
        "url": "https://genius.com/burn-lyrics",
        "primary_artist": {"name": "Cast"},
    }
    http = FakeHttp(
        json_routes={
            "https://api.genius.com/search": {"response": {"hits": [{"result": stub}]}},
            "https://api.genius.com/songs/1": {"response": {"song": stub}},
            "https://api.genius.com/referents": {"response": {"referents": []}},
        }
    )
    d = research("Burn by Cast", researchers=("genius",), http=http)
    assert d.subject == "Burn" and d.lyrics is None
    assert any("lyrics page was refused" in m for m in d.missing)


def test_merge_keeps_first_scalars_and_concatenates_sequences():
    a = griot.Dossier(
        topic="t",
        subject="A",
        facts=(griot.Fact("1", "u1"),),
        sources=(griot.Source("u1"),),
    )
    b = griot.Dossier(
        topic="t",
        subject="B",
        artist="X",
        facts=(griot.Fact("2", "u2"),),
        sources=(griot.Source("u1"), griot.Source("u2")),
    )
    m = griot.merge("t", [a, b])
    assert m.subject == "A" and m.artist == "X"
    assert [f.text for f in m.facts] == ["1", "2"] and [s.url for s in m.sources] == [
        "u1",
        "u2",
    ]
    assert griot.Dossier.from_dict(m.to_dict()) == m
