"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.scalping_pyramid_intraday_feedback_readers import (
    _one_share_record,
    _one_share_summary,
    _update_real_entry_lifecycle,
    _update_scout_ai_execution_attribution,
    _update_sell,
)


def build_report(*args, **kwargs):
    return retired_status("scalping_pyramid_intraday_feedback")


def write_outputs(*args, **kwargs):
    return retired_status("scalping_pyramid_intraday_feedback")


def main(argv=None):
    print(json.dumps(retired_status("scalping_pyramid_intraday_feedback")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
