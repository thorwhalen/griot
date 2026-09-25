"""``python -m griot`` — the CLI over :mod:`griot.tools`, via ``cw``.

python -m griot writers
python -m griot research "The Sound of Silence" --writer song
python -m griot quote "The Sound of Silence" --writer song --minutes 3
python -m griot write "The Sound of Silence" --writer song --minutes 3 --out draft.json
python -m griot write "Trinity Church Manhattan" --fake      # no key, no spend
"""

from __future__ import annotations

import json
import sys

from . import tools


def _print_json(result, *, out=None, err=None) -> None:
    if result is not None:
        print(json.dumps(result, ensure_ascii=False, indent=2), file=out or sys.stdout)


def main(argv: list[str] | None = None) -> int:
    """Dispatch a verb; cw prints the JSON result and returns the exit code."""
    try:
        import cw
    except ImportError:  # pragma: no cover - cli extra not installed
        print("install the CLI extra: pip install 'griot[cli]'", file=sys.stderr)
        return 2
    return cw.dispatch(
        [tools.writers, tools.research, tools.quote, tools.write],
        argv=argv,
        egress=_print_json,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
