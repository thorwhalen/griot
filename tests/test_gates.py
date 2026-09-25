"""The gates: each one fires on the failure it exists for, and only on that."""

from __future__ import annotations

from griot.gates import DraftFacts, run_gates

TAGGED = (
    "[curious] the take in June changed what the song was for, and the two men who had made it did not know it yet. "
    "[pause] and then the room went quiet for a long while, the tape still turning on the machine in the corner. "
    "[dryly] nobody noticed, which is the part of the story that people leave out when they tell it now."
)


def facts(**kw) -> DraftFacts:
    base = dict(
        narration=[TAGGED] * 5,
        beat_count=5,
        hinted_beats=5,
        target_words=325,
        tags_expected=True,
        lyrics=None,
    )
    base.update(kw)
    return DraftFacts(**base)


def test_clean_draft_passes():
    assert run_gates(facts()).ok


def test_platitudes_name_the_beat_and_the_tic():
    r = run_gates(
        facts(
            narration=["Here's the thing: listen to how it lands. " + TAGGED]
            + [TAGGED] * 4
        )
    )
    gates = {f.gate for f in r.findings}
    assert "platitudes" in gates
    assert any("beat 0" in f.message and "heres-the" in f.message for f in r.findings)


def test_expressiveness_only_when_the_delivery_renders_tags():
    flat = [
        "the take in June changed what the song was for and then the room went quiet and nobody noticed at all."
    ] * 5
    assert any(
        f.gate == "expressiveness" for f in run_gates(facts(narration=flat)).findings
    )
    assert not any(
        f.gate == "expressiveness"
        for f in run_gates(facts(narration=flat, tags_expected=False)).findings
    )


def test_lyric_leak_catches_a_whole_line_but_not_a_fragment():
    lyrics = "Hello darkness, my old friend\nI've come to talk with you again"
    leak = [TAGGED + " Hello darkness, my old friend."] + [TAGGED] * 4
    assert any(
        f.gate == "lyric_leak"
        for f in run_gates(facts(narration=leak, lyrics=lyrics)).findings
    )
    fragment = [TAGGED + ' the "old friend" of the first line.'] + [TAGGED] * 4
    assert not any(
        f.gate == "lyric_leak"
        for f in run_gates(facts(narration=fragment, lyrics=lyrics)).findings
    )


def test_length_is_a_band_around_the_budget():
    assert any(
        f.gate == "length" and "under" in f.message
        for f in run_gates(facts(target_words=900)).findings
    )
    assert any(
        f.gate == "length" and "over" in f.message
        for f in run_gates(facts(target_words=100)).findings
    )


def test_shape_wants_beats_and_a_hint_per_beat():
    r = run_gates(
        facts(beat_count=2, hinted_beats=1, narration=[TAGGED] * 2, target_words=120)
    )
    msgs = [f.message for f in r.findings if f.gate == "shape"]
    assert len(msgs) == 2 and "picture hint" in msgs[1]
