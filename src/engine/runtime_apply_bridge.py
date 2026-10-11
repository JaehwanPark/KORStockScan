"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.runtime_apply_bridge_compat_paths import (
    greenfield_real_env_policy_path,
    ldm_scale_in_runtime_bridge_artifact_path,
    runtime_apply_bridge_markdown_path,
    runtime_apply_bridge_report_path,
)
from src.engine.lifecycle.archive.runtime_apply_bridge_readers import (
    GREENFIELD_REAL_ENV_FAMILY,
    SCALE_IN_BRIDGE_FAMILY,
    _scale_candidate,
    _scale_confirmation_reports,
    _state_for_bucket,
    validate_greenfield_policy_file,
)


def build_runtime_apply_bridge_report(*args, **kwargs):
    return retired_status("runtime_apply_bridge")


def write_runtime_apply_bridge_report(*args, **kwargs):
    return retired_status("runtime_apply_bridge")


def main(argv=None):
    print(json.dumps(retired_status("runtime_apply_bridge")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
