"""Retired historical CLI; forensic readers live in lifecycle.archive."""

import json
from src.engine.lifecycle.retirement import retired_status


def build_report(*args, **kwargs):
    return retired_status("opening_rotation_backtest")


def render_markdown(*args, **kwargs):
    return retired_status("opening_rotation_backtest")


def write_report(*args, **kwargs):
    return retired_status("opening_rotation_backtest")


def main(argv=None):
    print(json.dumps(retired_status("opening_rotation_backtest")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
