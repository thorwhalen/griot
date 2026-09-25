"""The writers: registry, prompt, plan/quote, the gated write, the revision loop."""

from __future__ import annotations

import json

import braidio
import pytest

import griot
from griot.writers import RECORD_VOICE_ID, plan_write

from .conftest import good_reply


def test_three_writers_ship_and_are_data():
    assert {"general", "technical", "song"} <= set(griot.WRITERS)
    for w in griot.WRITERS.values():
        assert w.brief and w.title and w.blurb
        assert 2 <= len(w.voices) <= 4, (
            f"{w.name}: blend 2-4 voices, never impersonate one"
        )
        for v in w.voices:
            griot.voice_card(v)  # raises on an unknown voice
        assert w.format_id in braidio.formats.FORMATS
        assert w.researchers and all(r in griot.RESEARCHERS for r in w.researchers)


def test_a_writer_is_one_markdown_file_away():
    w = griot.writer_from_markdown(
        "---\nname: film\ntitle: The film critic\nvoices: david-sims, sean-fennessey\nwords_per_minute: 160\n---\nYou review films.\n"
    )
    assert (
        w.name == "film"
        and w.voices == ("david-sims", "sean-fennessey")
        and w.words_per_minute == 160
    )
    assert w.brief == "You review films."
    griot.register_writer(w)
    assert griot.get_writer("film") is w
    del griot.WRITERS["film"]
    with pytest.raises(KeyError, match="unknown writer"):
        griot.get_writer("film")


def test_the_prompt_carries_the_evidence_the_rules_and_the_voices(dossier):
    w = griot.get_writer("song")
    system, user = griot.build_prompt(w, dossier, minutes=3, angle="the 1965 overdub")
    assert '"picture_hints"' in system and '"record"' in system
    assert "Hello darkness, my old friend" in user  # the lyric sheet is evidence
    assert "TIMED LINES" in user and "Tom Wilson" in user
    assert "the 1965 overdub" in user
    assert "DO NOT" in user  # the checklist
    assert w.format.scripting[:40] in user
    for v in w.voices:
        assert griot.voice_card(v)[:60] in user
    assert "450 words" in user


def test_no_timed_lines_means_narration_only_is_demanded(dossier):
    d = griot.Dossier(
        topic=dossier.topic, subject=dossier.subject, summary=dossier.summary
    )
    _, user = griot.build_prompt(griot.get_writer("general"), d, minutes=2)
    assert "do not emit segment beats" in user


def test_plan_is_one_priced_call_and_quote_covers_every_call(dossier):
    w = griot.get_writer("general")
    plan = plan_write(w, dossier, minutes=3)
    assert len(plan.calls) == 1
    assert not plan.has_unknown_costs and plan.total_cost_usd > 0
    call = plan.calls[0]
    assert call.arguments["model"] == w.model and call.output_kind == "json"
    assert call.metadata["griot"]["writer"] == "general"
    q = griot.quote(w, dossier, minutes=3)
    assert q.calls == 1 + w.max_revisions
    assert q.llm_usd == pytest.approx(plan.total_cost_usd * q.calls)
    assert q.tts_usd and q.tts_usd > 0 and not q.has_unknown_costs
    assert q.total_usd == pytest.approx(q.llm_usd + q.tts_usd)
    assert q.target_words == 450


def test_an_unpriced_model_is_unknown_never_free(dossier):
    w = griot.Writer(name="x", title="x", brief="x", model="nobody/no-such-model")
    q = griot.quote(w, dossier, minutes=1)
    assert q.llm_unknown and q.llm_usd is None and q.has_unknown_costs


def test_write_parses_into_a_braidio_script_with_a_second_voice_for_the_record(dossier):
    w = griot.get_writer("song")
    calls = []

    def complete(plan):
        calls.append(plan)
        return good_reply(dossier), 0.02

    draft = griot.write(w, dossier, minutes=3, complete=complete)
    assert draft.ok, draft.report.findings
    assert len(calls) == 1 and draft.revisions == 0
    assert (
        isinstance(draft.script, braidio.Script)
        and draft.script.id_slug == "two-silences"
    )
    beats = draft.script.beats
    assert len(beats) == 5 and all(isinstance(b, braidio.Narration) for b in beats)
    record = beats[2]
    assert (
        record.voice == RECORD_VOICE_ID
        and record.style == "archive"
        and record.lead_gap_s >= 0.5
    )
    assert beats[0].voice is None  # the format's presenter
    assert len(draft.picture_hints) == 5 and draft.picture_hints[0].why
    assert draft.cost_usd_actual == pytest.approx(0.02)
    assert draft.sources_used == (dossier.sources[0].url,)
    payload = draft.to_dict()
    assert payload["ok"] and payload["script"]["beats"][2]["voice"] == RECORD_VOICE_ID


def test_a_failing_draft_gets_one_revision_with_the_findings_quoted_back(dossier):
    w = griot.get_writer("song")
    prompts = []

    def complete(plan):
        prompts.append(plan.calls[0].arguments["prompt"])
        return (
            good_reply(dossier, lyric_leak=True)
            if len(prompts) == 1
            else good_reply(dossier)
        ), 0.01

    draft = griot.write(w, dossier, minutes=3, complete=complete)
    assert len(prompts) == 2 and draft.revisions == 1 and draft.ok
    assert (
        "REVISION" in prompts[1]
        and "lyric_leak" in prompts[1]
        and "Hello darkness" in prompts[1]
    )
    assert draft.cost_usd_actual == pytest.approx(0.02)


def test_a_draft_that_still_fails_is_returned_with_its_report_not_shipped_silently(
    dossier,
):
    w = griot.get_writer("song")
    draft = griot.write(
        w,
        dossier,
        minutes=3,
        complete=lambda p: (good_reply(dossier, lyric_leak=True), 0.0),
    )
    assert not draft.ok and draft.revisions == w.max_revisions
    assert any(f.gate == "lyric_leak" for f in draft.report.findings)


def test_segments_are_kept_only_when_they_name_a_timed_line(dossier):
    w = griot.get_writer("song")
    obj = json.loads(good_reply(dossier))
    obj["beats"].insert(
        1,
        {
            "type": "segment",
            "reference": "Hello darkness, my old friend",
            "placement": "after",
        },
    )
    obj["beats"].insert(
        2, {"type": "segment", "reference": "a line the song does not have"}
    )
    obj["beats"].append({"type": "song", "text": "?"})
    draft = griot.draft_from_reply(json.dumps(obj), w, dossier, minutes=3)
    segs = [b for b in draft.script.beats if isinstance(b, braidio.SegmentBeat)]
    assert (
        len(segs) == 1
        and segs[0].rights == "copyright-third-party"
        and segs[0].placement == "after"
    )
    assert len(draft.dropped) == 2 and "does not name a timed line" in draft.dropped[0]


def test_malformed_json_raises_a_clear_error(dossier):
    with pytest.raises(ValueError, match="not valid JSON"):
        griot.draft_from_reply(
            "```json\n{not json", griot.get_writer("general"), dossier, minutes=1
        )
    with pytest.raises(ValueError, match="'beats' list"):
        griot.draft_from_reply(
            '{"title": "x"}', griot.get_writer("general"), dossier, minutes=1
        )


def test_fenced_json_is_tolerated(dossier):
    reply = "```json\n" + good_reply(dossier) + "\n```"
    assert griot.draft_from_reply(
        reply, griot.get_writer("song"), dossier, minutes=3
    ).ok


def test_a_quote_before_research_is_a_ceiling_over_the_quote_after(dossier):
    w = griot.get_writer("song")
    before = griot.quote(
        w,
        griot.Dossier(topic=dossier.topic),
        minutes=3,
        extra_input_tokens=griot.DOSSIER_TOKEN_ALLOWANCE,
    )
    after = griot.quote(w, dossier, minutes=3)
    assert before.llm_usd >= after.llm_usd and before.tts_usd == after.tts_usd


def test_picture_hints_follow_their_beats_when_an_earlier_beat_is_dropped(dossier):
    """A dropped beat must not shift every later picture onto the wrong words."""
    w = griot.get_writer("song")
    obj = json.loads(good_reply(dossier))
    obj["beats"].insert(
        1, {"type": "segment", "reference": "not a timed line"}
    )  # dropped
    obj["picture_hints"] = [
        {"beat_index": i, "query": f"q{i}", "subject": f"s{i}", "why": "w"}
        for i in range(len(obj["beats"]))
    ]
    draft = griot.draft_from_reply(json.dumps(obj), w, dossier, minutes=3)
    assert len(draft.script.beats) == 5
    # raw beat 2 (the first after the dropped one) is kept beat 1, and its hint says so
    by_index = {h.beat_index: h for h in draft.picture_hints}
    assert by_index[1].query == "q2" and by_index[0].query == "q0"
    assert all(0 <= h.beat_index < 5 for h in draft.picture_hints)
    assert any("names no kept beat" in d for d in draft.dropped)
