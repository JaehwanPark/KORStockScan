"""Entry observations for dedicated gate/replay owners, without matrix policy.

The legacy module retains the shared event normalization and identity helpers;
this adapter never reads matrix artifacts, builds buckets, or writes reports.
"""

from typing import Any

from src.engine import scalp_entry_action_decision_matrix as observations


def load_entry_observations(target_date: str) -> dict[str, Any]:
    import json
    from src.utils.constants import DATA_DIR
    from src.engine.automation.source_data_retirement import digest
    retirement=DATA_DIR/'report/additional_unused_raw_retirement/2026-10-07/retired-snapshots.json'
    retired=[]
    if retirement.is_file():
        receipt=json.loads(retirement.read_text())
        if receipt.get('content_sha256')!=digest({k:v for k,v in receipt.items() if k!='content_sha256'}):
            raise ValueError('entry_observation_retirement_receipt_invalid')
        retired=[r for r in receipt.get('deleted_files',[]) if r['source_date']==target_date]
    source = [
        observations._base_row(event)
        for event in observations._iter_relevant_events(target_date)
    ]
    followups = [
        row
        for row in source
        if row.get("stage") == "entry_ai_price_canary_skip_followup"
    ]
    raw = [
        row
        for row in source
        if row.get("stage") != "entry_ai_price_canary_skip_followup"
    ]
    observations._backfill_sim_lineage(raw)
    rows = observations._dedupe_rows(raw)
    observations._backfill_score_context(rows, source_rows=raw)
    observations._attach_entry_price_skip_followups(rows, followups)
    return {
        "date": target_date,
        "status": "pass" if rows else "retired_source" if retired else "no_observations",
        "retired_snapshot_fallbacks": retired,
        "report_type": "entry_observation_source",
        "rows": rows,
        "runtime_effect": False,
        "decision_authority": "source_only",
        "allowed_runtime_apply": False,
    }
