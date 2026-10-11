"""Retired compatibility CLI for documented historical invocations.

Active callers have moved to their role owners. Remove this surface when the
remaining historical command references are retired by the document owner.
"""

import json
from src.engine.lifecycle.retirement import retired_status
from src.engine.lifecycle.archive.scalp_entry_action_decision_matrix_compat_paths import (
    report_paths,
)
from src.engine.lifecycle.archive.scalp_entry_action_decision_matrix_readers import (
    _adm_lookup_closure_summary,
    _backfill_score_context,
    _backfill_sim_lineage,
    _base_row,
    _chosen_action,
    _classify_adm_lookup_not_applicable,
    _entry_price_skip_followup_cumulative_summary,
    _event_paths,
    _iter_relevant_events,
    _joined_sample_cumulative_summary,
    _load_sim_evaluations,
    _outcome_join_diagnostic,
    _score_source,
    _unknown_bucket_summary,
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
