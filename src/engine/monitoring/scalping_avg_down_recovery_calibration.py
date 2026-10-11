"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status


def build_report(*args, **kwargs):
    return retired_status("scalping_avg_down_recovery_calibration")


def write_outputs(*args, **kwargs):
    return retired_status("scalping_avg_down_recovery_calibration")


def main(argv=None):
    print(json.dumps(retired_status("scalping_avg_down_recovery_calibration")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
