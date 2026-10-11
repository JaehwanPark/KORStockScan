"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.ldm_hypothesis_discovery_compat_paths import (
    observation_plan_path,
    report_paths,
)
from src.engine.lifecycle.archive.ldm_hypothesis_discovery_readers import (
    ARMING_OBSERVABLE_REQUIREMENT_FIELDS,
    FORBIDDEN_USES,
    OBSERVATION_PLAN_SCHEMA_VERSION,
    SourceRow,
    _feature_items,
    merge_sim_policy_catalogs,
)


def build_hypotheses(*args, **kwargs):
    return retired_status("ldm_hypothesis_discovery")


def build_observation_plan(*args, **kwargs):
    return retired_status("ldm_hypothesis_discovery")


def build_report(*args, **kwargs):
    return retired_status("ldm_hypothesis_discovery")


def render_markdown(*args, **kwargs):
    return retired_status("ldm_hypothesis_discovery")


def write_report(*args, **kwargs):
    return retired_status("ldm_hypothesis_discovery")


def main(argv=None):
    print(json.dumps(retired_status("ldm_hypothesis_discovery")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
