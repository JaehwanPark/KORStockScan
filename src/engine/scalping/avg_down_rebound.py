"""Holding adapters for the selected Main signal; no entry claim or order owner."""

from __future__ import annotations

import hashlib
import math
import re
from datetime import date


def holding_policy_position_tag(stock):
    """Keep historical fixed admission/custody while selecting its Main policy.

    A holding may outlive its admission day or market session. Requiring a
    current WATCHING generation would silently exclude overnight positions.
    Current market/activation and custody guards remain with their owners.
    """
    from src.engine.scalping import main_fixed_watch as fixed

    tag = str(stock.get("position_tag") or "SCALP_BASE").upper()
    if stock.get("watch_origin") != fixed.WATCH_ORIGIN:
        return tag
    match = re.fullmatch(
        r"FIXED-(\d{4}-\d{2}-\d{2})-(\d{6})-([A-Za-z_]+)-([a-z_]+)-([0-9a-f]{12})",
        str(stock.get("watch_admission_id") or ""),
    )
    if not fixed.is_fixed_watch(stock) or tag != "SCALP_BASE" or match is None:
        raise ValueError("holding_fixed_watch_admission_invalid")
    day, code, bucket, route, _ = match.groups()
    date.fromisoformat(day)
    if code != stock.get("code") or (bucket, route) not in {
        ("krx_like_premarket", "nxt_only"),
        ("krx_regular", "krx_nxt_integrated"),
        ("KRX_NXT_AFTERMARKET", "krx_nxt_integrated"),
    }:
        raise ValueError("holding_fixed_watch_scope_invalid")
    generation = hashlib.sha256(
        f"{day}|{code}|{bucket}|{route}".encode("ascii")
    ).hexdigest()
    if stock.get("watch_generation_id") != generation:
        raise ValueError("holding_fixed_watch_generation_invalid")
    return "SCANNER"


def _rebound_branch(branch_id, seen=()):
    """Classify the registered definition, never infer rebound from its name."""
    from src.engine.scalping import reversal_extended_catalog as catalog

    if branch_id in seen or len(seen) >= 16:
        return False
    definition = catalog.definition(branch_id)
    original = definition.get("original_definition_ref")
    if original:
        return _rebound_branch(original["branch_id"], (*seen, branch_id))
    root = definition.get("root_contract")
    if root:
        return root.get("signal") == "native_first_turn"
    if definition.get("kind") == "cumulative_root":
        from src.engine.scalping.reversal_cumulative_catalog import root_contract

        return (
            root_contract(definition["root_confirmation"])["signal"]
            == "native_first_turn"
        )
    return definition.get("decision_phase") in {"FIRST_UPTICK", "CONFIRMED_UPTICK"}


def resolve_krx_aftermarket_source(
    *, stock_code, ws_data, now, position_tag, receipt, configured_prompt_version
):
    """Resolve the separately issued ADD-only source, never an entry policy."""
    from pathlib import Path
    from src.engine.scalping import entry_setup_live_policy as entry
    from src.engine.scalping import entry_setup_scalping_rollout as rollout
    from src.engine.scalping import holding_path_vote_policy as votes
    from src.engine.scalping import mechanistic_entry_runtime_policy as machine
    from src.engine.scalping.ai_market_snapshot import realtime_type_provenance
    from src.utils.constants import DATA_DIR

    day = now.date().isoformat()
    if (
        not votes.runtime_krx_aftermarket_add_source_enabled(receipt, active_date=day)
        or str(position_tag or "").upper() not in entry.CANARY_POSITION_TAGS
        or configured_prompt_version
        != entry.DECISION_QUALITY_V2_13_RECOVERY_CONFIRMATION_PROMPT_VERSION
        or not entry._enabled_by_operator(cohort=entry.DEFAULT_COHORT)
    ):
        return None
    rows = realtime_type_provenance(ws_data, now_ts=now.timestamp())
    if any(
        row.get("quality") != "fresh"
        or row.get("item") != stock_code
        or row.get("market_suffix") != ""
        or row.get("market_route") != "krx_only"
        or row.get("effective_venue") not in {"", "KRX"}
        for row in (rows["0B"], rows["0D"])
    ):
        return None
    auto = rollout.load_auto_promotion(now=now)
    legacy = rollout.load_rollout(now=now)
    if (auto is not None and not auto.get("valid")) or not (
        auto and auto.get("valid") or legacy and legacy.get("valid")
    ):
        return None
    # The only waived error is the existing entry rollout's missing KRX AFTER
    # scope: the separate dated ADD scope above owns that one permission.
    errors = entry._runtime_probe_contract_errors(
        target_date=day, cohort=("KRX", "KRX_NXT_AFTERMARKET"), now=now
    )
    if any(error != "runtime_contract_exact_rollout_scope_missing" for error in errors):
        return None
    bundle = machine.load_effective(
        data_root=Path(DATA_DIR), target_date=day, _immutable=True
    )
    family = (bundle or {}).get("continuous_reversal") or {}
    if family.get("schema") != "continuous_reversal_policy_v6":
        return None
    return dict(
        enabled=True,
        status="add_rebound_krx_aftermarket_source_only",
        machine_bundle_sha256=bundle["bundle_sha256"],
        continuous_reversal=family,
        add_rebound_source_scope=receipt["add_rebound_source_scope"],
        holding_vote_bundle_sha256=receipt["bundle_sha256"],
    )


def evaluate_native_rebound(live, *, stock_code, ws_data, session, now_ts):
    """Read and assess the existing native buffer without consuming a claim.

    The full selected union is assessed by the same pure Main dispatcher.
    ADD additionally requires a matched branch rooted in a price reversal;
    continuation-only Main entries cannot become averaging-down permission.
    """
    from src.engine.scalping.reversal_source_diagnostics import observe_snapshot
    from src.engine.scalping.continuous_reversal_policy import _assess
    from src.engine.scalping.mechanistic_entry_runtime_policy import digest
    from src.trading.market.session_contract import market_source_partition_venue

    family = live["continuous_reversal"]
    item = (ws_data.get("last_realtime_type_item") or {}).get("0B")
    if item not in {stock_code, stock_code + "_AL", stock_code + "_NX"}:
        return dict(should_add=False, reason="shared_main_rebound_native_item_missing")
    snapshot, receipt = observe_snapshot(
        stock_code,
        market_source_partition_venue(item),
        session,
        now=now_ts,
        item=item,
        family_sha256=family["family_sha256"],
    )
    base = dict(
        should_add=False,
        machine_bundle_sha256=live["machine_bundle_sha256"],
        machine_family_sha256=family["family_sha256"],
        native_source_status=receipt.get("reason"),
    )
    if snapshot is None:
        # An observed FALSE union is a valid non-entry, not a missing feed.
        observed_false = (
            receipt.get("reason") == "no_matching_pattern"
            and receipt.get("native_source_current") is True
            and receipt.get("native_quote_current") is True
        )
        return dict(
            base,
            reason=(
                "shared_main_rebound_not_confirmed"
                if observed_false
                else "shared_main_rebound_native_source_unavailable"
            ),
            machine_action="WAIT" if observed_false else None,
        )
    event = snapshot[0]
    epoch = event.get("epoch")
    if (
        not isinstance(epoch, (int, float))
        or isinstance(epoch, bool)
        or not math.isfinite(epoch)
        or not 0 <= now_ts - epoch <= 5
        or event.get("symbol") != stock_code
        or event.get("source_item") != item
    ):
        return dict(base, reason="shared_main_rebound_native_source_invalid")
    if live.get("add_rebound_source_scope"):
        from src.engine.scalping import reversal_registered_catalog as catalog
        from src.engine.scalping.continuous_reversal_policy_v6 import scope_id

        price = event.get("confirmation_price")
        if (
            item != stock_code
            or event.get("venue") != "KRX"
            or event.get("market") != "AFTER"
            or not isinstance(price, (int, float))
            or isinstance(price, bool)
            or not math.isfinite(price)
            or price <= 0
        ):
            return dict(base, reason="shared_main_rebound_native_scope_invalid")
        key = catalog.cell_key(stock_code, session, price)
        if not family.get("machine_cells", {}).get(key, {}).get("routes", {}).get(
            "KRX"
        ) or not family.get("operating_manifest", {}).get("scopes", {}).get(
            scope_id(key, "KRX")
        ):
            return dict(base, reason="shared_main_rebound_native_scope_missing")
    assessment, _, _, _ = _assess(family, snapshot, symbol=stock_code, session=session)
    branches = [
        bid for bid in assessment.get("matched_branches", []) if _rebound_branch(bid)
    ]
    # Early native policies expose an explicit reversal fact instead of a union.
    rebound = bool(branches) or (
        not event.get("branch_signals")
        and assessment.get("price_reversal_confirmed") is True
    )
    return dict(
        base,
        should_add=rebound and assessment["action"] == "ENTER_NOW",
        reason=(
            "shared_main_rebound_confirmed"
            if rebound and assessment["action"] == "ENTER_NOW"
            else "shared_main_rebound_not_confirmed"
        ),
        source_signal_id=digest(
            dict(
                symbol=stock_code,
                bundle=live["machine_bundle_sha256"],
                native_event=event,
                rebound_branches=branches,
            )
        ),
        native_signal_id=assessment.get("signal_id") or assessment.get("event_id"),
        native_signal_expires_at=epoch + 5,
        machine_action=assessment["action"],
        machine_policy_version=assessment["policy_version"],
        structure_phase_family="CONTINUOUS_REVERSAL",
        rebound_branches=branches,
        holding_vote_bundle_sha256=live.get("holding_vote_bundle_sha256"),
        add_rebound_source_scope=live.get("add_rebound_source_scope"),
    )
