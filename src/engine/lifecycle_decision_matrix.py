"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.lifecycle_decision_matrix_compat_paths import (
    report_paths,
)
from src.engine.lifecycle.archive.lifecycle_decision_matrix_readers import (
    ENTRY_BUCKET_SAMPLE_FLOOR,
    SCALE_IN_BUCKET_SAMPLE_FLOOR,
    SCALE_IN_EV_LABEL_VERSION,
    SUBMIT_BUCKET_SAMPLE_FLOOR,
    _aggregate_bucket_rows,
    _aggregate_existing_daily_lifecycle_reports,
    _apply_institutional_flow_features,
    _enrich_scale_in_rows_with_counterfactual_ev,
    _entry_bucket_attribution,
    _entry_bucket_features,
    _entry_bucket_row,
    _entry_score_band,
    _entry_strength_bucket_from_features,
    _exit_bucket_attribution,
    _exit_bucket_features,
    _exit_combo_bucket_id,
    _flow_record,
    _holding_bucket_attribution,
    _holding_bucket_features,
    _holding_combo_bucket_id,
    _institutional_flow_attribution,
    _labels,
    _lifecycle_flow_bucket_attribution,
    _load_scale_in_counterfactual_labels,
    _load_scale_in_counterfactual_source_status,
    _load_scale_in_counterfactual_source_statuses,
    _load_scalp_sim_holding_rows,
    _load_scalp_sim_overnight_rows,
    _load_scalp_sim_panic_rows,
    _load_scalp_sim_scale_in_rows,
    _load_scalp_sim_submit_rows,
    _overnight_bucket_attribution,
    _row_flow_identity,
    _runtime_features,
    _scale_in_bucket_attribution,
    _scale_in_bucket_row,
    _submit_bucket_attribution,
    _submit_bucket_row,
    _submit_runtime_features,
    fixed_threshold_contract,
)


def build_lifecycle_decision_matrix_report(*args, **kwargs):
    return retired_status("lifecycle_decision_matrix")


def render_lifecycle_decision_matrix_markdown(*args, **kwargs):
    return retired_status("lifecycle_decision_matrix")


def main(argv=None):
    print(json.dumps(retired_status("lifecycle_decision_matrix")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
