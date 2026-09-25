"""The style library — the voice guide, the checklist, twenty critic voices.

Shipped as package data (``griot/data/style``), moved from braidio's
``misc/docs/style`` where nothing could import it. A writer *blends* 2–4 voices
and never impersonates one; the voice cards are read as prose into the prompt.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources
from pathlib import Path

__all__ = ["checklist", "list_voices", "voice_card", "voice_guide_rules"]


def _style_dir() -> Path:
    return Path(str(resources.files("griot").joinpath("data", "style")))


@lru_cache(maxsize=None)
def checklist() -> str:
    """The anti-platitude checklist, verbatim (the "paste into writer prompts" file)."""
    return (_style_dir() / "anti-platitude-checklist.md").read_text(encoding="utf-8")


def list_voices() -> list[str]:
    """The voice names available to a writer (file stems under ``voices/``)."""
    return sorted(
        p.stem
        for p in (_style_dir() / "voices").glob("*.md")
        if not p.stem.startswith("_")
    )


@lru_cache(maxsize=None)
def voice_card(name: str) -> str:
    """One critic's card: how they write, what they pay attention to, borrow this, don't imitate."""
    path = _style_dir() / "voices" / f"{name}.md"
    if not path.exists():
        raise KeyError(f"unknown voice {name!r}; known: {list_voices()}")
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def voice_guide_rules() -> str:
    """The guide's own one-rule-under-all-thirteen and the mixing rules (§ 'The core method')."""
    text = (_style_dir() / "commentary-voice-guide.md").read_text(encoding="utf-8")
    start = text.find("### The one rule underneath all thirteen")
    end = text.find("## 2. The Style Axes")
    rule = text[start:end].strip() if start >= 0 and end > start else ""
    mstart = text.find("### The core method")
    mend = text.find("## 4. Index")
    mixing = text[mstart:mend].strip() if mstart >= 0 and mend > mstart else ""
    return (rule + "\n\n" + mixing).strip()
