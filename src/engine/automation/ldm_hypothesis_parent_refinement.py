"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.ldm_hypothesis_parent_refinement_compat_paths import (
    latest_observation_plan_path,
    observation_plan_path,
    report_paths,
)
from src.engine.lifecycle.archive.ldm_hypothesis_parent_refinement_readers import (
    Counter,
    HypothesisAggregate,
    OBSERVATION_PLAN_SCHEMA_VERSION,
    _diagnose_repeated_status,
    _latest_lifecycle_bucket_report,
    _previous_gap_count,
)


def build_refinement_report(*args, **kwargs):
    return retired_status("ldm_hypothesis_parent_refinement")


def render_markdown(*args, **kwargs):
    return retired_status("ldm_hypothesis_parent_refinement")


def write_report(*args, **kwargs):
    return retired_status("ldm_hypothesis_parent_refinement")


def main(argv=None):
    print(json.dumps(retired_status("ldm_hypothesis_parent_refinement")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
