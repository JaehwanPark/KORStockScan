"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.institutional_flow_context_compat_paths import (
    report_paths,
)
from src.engine.lifecycle.archive.institutional_flow_context_readers import (
    _load_pipeline_event_codes,
    normalize_institutional_flow_context,
    resolve_institutional_flow_context,
)


def build_institutional_flow_context_report(*args, **kwargs):
    return retired_status("institutional_flow_context")


def render_institutional_flow_context_markdown(*args, **kwargs):
    return retired_status("institutional_flow_context")


def main(argv=None):
    print(json.dumps(retired_status("institutional_flow_context")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
