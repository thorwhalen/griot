"""The SSOT verbs and the CLI over them, with the network and the LLM faked."""

from __future__ import annotations

import importlib
import json

import griot
from griot import tools
from griot.__main__ import main

from .conftest import FakeHttp
from .test_research import wiki_http


def test_writers_verb_lists_what_a_picker_needs():
    rows = tools.writers()
    assert {r["name"] for r in rows} >= {"general", "technical", "song"}
    assert all({"title", "blurb", "default_minutes", "voices"} <= set(r) for r in rows)


def test_write_fake_runs_the_whole_path_without_a_key(monkeypatch, tmp_path):
    monkeypatch.setattr(importlib.import_module("griot.research"), "HttpxHttp", lambda: wiki_http("Trinity Church (Manhattan)"))
    out = tmp_path / "draft.json"
    payload = tools.write("Trinity Church Manhattan", writer="general", minutes=2, fake=True, out=str(out))
    assert payload["ok"], payload["findings"]
    assert payload["dossier"]["subject"] == "Trinity Church (Manhattan)"
    assert len(payload["script"]["beats"]) == 5 and len(payload["picture_hints"]) == 5
    assert json.loads(out.read_text())["writer"] == "general"


def test_quote_verb_prices_before_spending(monkeypatch):
    monkeypatch.setattr(importlib.import_module("griot.research"), "HttpxHttp", lambda: wiki_http("Trinity Church (Manhattan)"))
    q = tools.quote("Trinity Church Manhattan", writer="technical", minutes=3)
    assert q["subject"] == "Trinity Church (Manhattan)" and q["total_usd"] > 0 and not q["has_unknown_costs"]
    assert q["calls"] == 2


def test_cli_prints_json(capsys):
    assert main(["writers"]) in (0, None)
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["name"] == "general"


def test_research_verb_uses_the_writers_researchers(monkeypatch):
    http = FakeHttp()
    monkeypatch.setattr(importlib.import_module("griot.research"), "HttpxHttp", lambda: http)
    d = tools.research("x", writer="song")
    assert [m.split(":")[0] for m in d["missing"]] == ["genius", "wikipedia", "lrclib"]
