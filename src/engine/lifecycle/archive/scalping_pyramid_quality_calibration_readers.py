"""Historical read-only helpers; no active policy publisher or CLI.

Only existing forensic consumers retain these calculations. Live callers use
their native role owners and permanent retirement fences.
"""

from __future__ import annotations


import math


from typing import Any


PROFIT_GRID_MIN_ELIGIBLE = 20


PROFIT_GRID_RUNTIME_STEP = 0.1


def _nearest_grid_row(
    grid: list[dict[str, Any]], threshold: float
) -> dict[str, Any] | None:
    if not grid:
        return None
    return min(
        grid, key=lambda row: abs(float(row.get("min_profit_pct") or 0.0) - threshold)
    )


def _profit_grid_decision(
    current: dict[str, Any], grid: list[dict[str, Any]]
) -> dict[str, Any]:
    current_threshold = float(current["min_profit_pct"])
    current_row = _nearest_grid_row(grid, current_threshold)
    current_row_exact = bool(
        current_row
        and math.isclose(
            float(current_row.get("min_profit_pct") or 0.0),
            current_threshold,
            abs_tol=1e-9,
        )
    )
    eligible_rows = [
        row
        for row in grid
        if int(row.get("eligible_count") or 0) >= PROFIT_GRID_MIN_ELIGIBLE
    ]
    if not grid:
        return {
            "status": "unavailable",
            "reason": "no_rows_with_max_and_final_profit",
            "objective": "maximize_fee_aware_expected_net_profit_contribution",
            "selected_min_profit_pct": current_threshold,
            "recommended_next_min_profit_pct": current_threshold,
            "exploratory_selected_min_profit_pct": None,
            "current_min_profit_pct": current_threshold,
            "current_row": current_row,
            "selected_row": None,
        }
    if not current_row_exact:
        return {
            "status": "hold",
            "reason": "current_threshold_outside_profit_grid",
            "objective": "maximize_fee_aware_expected_net_profit_contribution",
            "selected_min_profit_pct": current_threshold,
            "recommended_next_min_profit_pct": current_threshold,
            "candidate_next_min_profit_pct": None,
            "exploratory_selected_min_profit_pct": None,
            "current_min_profit_pct": current_threshold,
            "current_row": None,
            "selected_row": None,
            "candidate_next_row": None,
        }
    if not eligible_rows:
        return {
            "status": "hold",
            "reason": "grid_eligible_rows_lt_20",
            "objective": "maximize_fee_aware_expected_net_profit_contribution",
            "selected_min_profit_pct": current_threshold,
            "recommended_next_min_profit_pct": current_threshold,
            "exploratory_selected_min_profit_pct": None,
            "current_min_profit_pct": current_threshold,
            "current_row": current_row,
            "selected_row": None,
        }
    exploratory_selected = max(
        eligible_rows,
        key=lambda row: (
            float(row.get("equal_weight_expected_net_profit_contribution_pct") or 0.0),
            -float(row.get("loss_or_flat_rate") or 0.0),
            float(row.get("min_profit_pct") or 0.0),
        ),
    )
    current_contribution = (
        float(
            current_row.get("equal_weight_expected_net_profit_contribution_pct") or 0.0
        )
        if current_row
        else 0.0
    )
    exploratory_threshold = float(exploratory_selected["min_profit_pct"])
    if abs(exploratory_threshold - current_threshold) < 0.05:
        recommended_threshold = current_threshold
    else:
        direction = -1.0 if exploratory_threshold < current_threshold else 1.0
        recommended_threshold = round(
            current_threshold + (direction * PROFIT_GRID_RUNTIME_STEP), 1
        )
    candidate_next = _nearest_grid_row(grid, recommended_threshold)
    candidate_next_contribution = (
        float(
            candidate_next.get("equal_weight_expected_net_profit_contribution_pct")
            or 0.0
        )
        if candidate_next
        else current_contribution
    )
    contribution_delta = candidate_next_contribution - current_contribution
    if abs(exploratory_threshold - current_threshold) < 0.05:
        status = "hold"
        reason = "grid_selected_current_threshold"
    elif not candidate_next or int(candidate_next.get("eligible_count") or 0) < (
        PROFIT_GRID_MIN_ELIGIBLE
    ):
        status = "hold"
        reason = "grid_next_step_eligible_rows_lt_20"
    elif contribution_delta <= 0.0:
        status = "hold"
        reason = "grid_next_step_net_contribution_not_improved"
    elif candidate_next_contribution <= 0.0:
        status = "hold"
        reason = "grid_next_step_net_contribution_non_positive"
    elif recommended_threshold < current_threshold:
        status = "adjust_down"
        reason = "grid_loosen_profit_threshold_one_step"
    else:
        status = "adjust_up"
        reason = "grid_tighten_profit_threshold_one_step"
    return {
        "status": status,
        "reason": reason,
        "objective": "maximize_fee_aware_expected_net_profit_contribution",
        "selected_min_profit_pct": (
            recommended_threshold if status != "hold" else current_threshold
        ),
        "recommended_next_min_profit_pct": (
            recommended_threshold if status != "hold" else current_threshold
        ),
        "candidate_next_min_profit_pct": recommended_threshold,
        "exploratory_selected_min_profit_pct": exploratory_threshold,
        "current_min_profit_pct": current_threshold,
        "current_equal_weight_expected_net_profit_contribution_pct": (
            current_contribution
        ),
        "current_source_quality_adjusted_ev_pct": current_contribution,
        "selected_equal_weight_expected_net_profit_contribution_pct": (
            candidate_next_contribution if status != "hold" else current_contribution
        ),
        "candidate_next_equal_weight_expected_net_profit_contribution_pct": (
            candidate_next_contribution
        ),
        "candidate_next_source_quality_adjusted_ev_pct": candidate_next_contribution,
        "source_quality_adjusted_ev_delta_pct": contribution_delta,
        "equal_weight_expected_net_profit_contribution_delta_pct": (contribution_delta),
        "exploratory_selected_equal_weight_expected_net_profit_contribution_pct": (
            float(
                exploratory_selected.get(
                    "equal_weight_expected_net_profit_contribution_pct"
                )
                or 0.0
            )
        ),
        "current_avg_incremental_exit_profit_pct": (
            float(current_row.get("avg_incremental_exit_profit_pct") or 0.0)
            if current_row
            else 0.0
        ),
        "selected_avg_incremental_exit_profit_pct": (
            float(
                (candidate_next if status != "hold" else current_row).get(
                    "avg_incremental_exit_profit_pct"
                )
                or 0.0
            )
        ),
        "current_row": current_row,
        "selected_row": candidate_next if status != "hold" else current_row,
        "candidate_next_row": candidate_next,
        "exploratory_selected_row": exploratory_selected,
        "max_runtime_step_pct": PROFIT_GRID_RUNTIME_STEP,
    }
