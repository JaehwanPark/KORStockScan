"""Retired historical CLI; forensic readers live in lifecycle.archive."""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.scale_in_incremental_counterfactual_compat_paths import (
    _event_path,
    report_paths,
)


def build_backfill_report(*args, **kwargs):
    return retired_status("scale_in_incremental_counterfactual")


def build_report(*args, **kwargs):
    return retired_status("scale_in_incremental_counterfactual")


from src.engine.lifecycle.archive.scale_in_incremental_counterfactual_readers import (
    compute_fixed_exit_incremental_economics,
)


def write_outputs(*args, **kwargs):
    return retired_status("scale_in_incremental_counterfactual")


def main(argv=None):
    print(json.dumps(retired_status("scale_in_incremental_counterfactual")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
