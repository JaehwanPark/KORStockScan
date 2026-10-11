"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.lifecycle_bucket_discovery_compat_paths import (
    bucket_catalog_path,
    contamination_window_path,
    discovery_markdown_path,
    discovery_report_path,
    sim_auto_approval_path,
)
from src.engine.lifecycle.archive.lifecycle_bucket_discovery_readers import (
    AI_REVIEW_MAX_CANDIDATES,
    AI_REVIEW_SHARD_CONTEXT_BUDGET_CHARS,
    LIFECYCLE_FLOW_CHILD_STANDALONE_MIN_JOINED_SAMPLE,
    LIFECYCLE_FLOW_SIM_PROBE_STATE,
    SCALE_IN_AI_SCORE_SOURCE_MISSING_GAP,
    SCALE_IN_AI_SCORE_SOURCE_MISSING_RESOLUTION,
    SCALE_IN_HELD_BUCKET_OBSERVATION_RESOLUTION,
    SCALE_IN_LIVE_AUTO_FAMILY,
    SCALE_IN_SOURCE_DIMENSION_OBSERVATION_RESOLUTION,
    SCALE_IN_SOURCE_DIMENSION_ROLLUP_BUCKETS,
    WAIT6579_ENTRY_BUCKET_KEY,
    _ai_review_config_for_shard,
    _apply_ai_review,
    _apply_ldm_refinement_pressure,
    _build_active_sim_priority_seeds,
    _build_ai_review_context,
    _build_ai_review_shards,
    _build_parent_conflict_resolution,
    _candidate_from_bucket,
    _classify_bucket,
    _classify_conflict_child,
    _compare_source_contracts,
    _entry_source_parent,
    _finalize_report,
    _lifecycle_flow_parent_dimensions,
    _normalize_candidate_runtime_metadata,
    _parse_ai_review_response,
    _policy_stage_candidates,
    _previous_report,
    _quiet_gap_summary,
    _render_markdown,
    _select_parent_level,
    _source_dimension_gap_summary,
    _write_sim_auto_approval,
)


def build_lifecycle_bucket_discovery_report(*args, **kwargs):
    return retired_status("lifecycle_bucket_discovery")


def write_lifecycle_bucket_discovery_report(*args, **kwargs):
    return retired_status("lifecycle_bucket_discovery")


def main(argv=None):
    print(json.dumps(retired_status("lifecycle_bucket_discovery")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
