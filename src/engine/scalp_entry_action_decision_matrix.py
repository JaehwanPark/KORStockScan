"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.scalp_entry_action_decision_matrix_compat_paths import (
    report_paths as report_paths,
)
from src.engine.lifecycle.archive.scalp_entry_action_decision_matrix_readers import (
    _adm_lookup_closure_summary as _adm_lookup_closure_summary,
    _classify_adm_lookup_not_applicable as _classify_adm_lookup_not_applicable,
    _entry_price_skip_followup_cumulative_summary as _entry_price_skip_followup_cumulative_summary,
    _joined_sample_cumulative_summary as _joined_sample_cumulative_summary,
    _load_sim_evaluations as _load_sim_evaluations,
    _outcome_join_diagnostic as _outcome_join_diagnostic,
    _unknown_bucket_summary as _unknown_bucket_summary,
)
from src.engine.scalping.entry_observation_events import (
    _backfill_score_context as _backfill_score_context,
    _backfill_sim_lineage as _backfill_sim_lineage,
    _base_row as _base_row,
    _chosen_action as _chosen_action,
    _event_paths as _event_paths,
    _iter_relevant_events as _iter_relevant_events,
    _score_source as _score_source,
)


def build_scalp_entry_action_decision_matrix_report(*args, **kwargs):
    return retired_status("scalp_entry_action_decision_matrix")


def render_scalp_entry_action_decision_matrix_markdown(*args, **kwargs):
    return retired_status("scalp_entry_action_decision_matrix")


def main(argv=None):
    print(json.dumps(retired_status("scalp_entry_action_decision_matrix")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
