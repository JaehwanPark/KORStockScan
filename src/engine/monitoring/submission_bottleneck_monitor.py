"""Observe Sentinel's exact machine funnel; notification has no trading authority."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.notify_error_detection_admin import (
    _load_state, _load_telegram_config, _send_telegram, _write_state,
)
from src.utils.constants import PROJECT_ROOT

SCHEMA = "submission_bottleneck_monitor_v1"
KST = ZoneInfo("Asia/Seoul")
# Diagnostic persistence only. Never used by a trading policy or guard.
WINDOW_SEC = 1800
GRACE_SEC = 600
PERSIST_SEC = 900
MIN_PROMOTIONS = 10


def stamp(value):
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)
    except (ValueError, TypeError):
        return None


ECONOMIC_STAGES = frozenset({"entry_ai_economic_plan_observed", "entry_ai_economic_source_gap"})


def economic_evidence(fields, stock_code=None):
    """Project frozen producer proof, without replay, account reads or inferred values."""
    from src.engine.scalping.strategy_owner_replay import _entry_seed_valid, entry_conditional_capital_envelope
    from src.engine.scalping.strategy_owner_components import digest

    status = fields.get("entry_economic_source_status")
    blocker = str(fields.get("entry_economic_source_blocker") or "")
    result = {"status": status, "blocker": blocker or None,
        "capacity_blocker": fields.get("entry_economic_capacity_blocker") or None,
        "owner": fields.get("entry_economic_source_owner") or "main_entry_execution_owners",
        "closure_test": fields.get("entry_economic_source_closure_test") or "exact frozen plan/cost/capital source reaches evaluator",
        "plan_sha256": fields.get("entry_economic_plan_sha256"), "valid_economics": False}
    guard = fields.get("entry_economic_guard_receipt")
    if isinstance(guard, str):
        try:
            guard = json.loads(guard)
        except (ValueError, TypeError):
            guard = None
    if isinstance(guard, dict):
        result["observation_guard"] = guard
    if status != "recorded_source_only":
        if blocker.startswith("common_guard_block:") or blocker == "owner_sizing_zero_or_invalid":
            result["status"] = "guard_excluded"
        elif status == "unsupported_scope":
            result["status"] = "unsupported_scope"
        else:
            result["status"] = "source_gap"
            result["blocker"] = blocker or "economic_producer_status_missing"
        return result
    try:
        seed = fields.get("entry_opportunity_replay_seed")
        seed = json.loads(seed) if isinstance(seed, str) else seed
        if not _entry_seed_valid(seed) or seed.get("plan_sha256") != fields.get("entry_execution_sizing_plan_sha256"):
            raise ValueError("economic_seed_or_plan_binding_invalid")
        for key, field in (("scanner_promotion_id", "scanner_promotion_id"),
                           ("evaluation_attempt_id", "evaluation_attempt_id")):
            if seed.get(key) != fields.get(field):
                raise ValueError("economic_attempt_binding_invalid:" + key)
        if stock_code and seed.get("stock_code") != stock_code:
            raise ValueError("economic_symbol_binding_invalid")
        if fields.get("entry_economic_plan_sha256") != seed.get("plan_sha256"):
            raise ValueError("economic_published_plan_hash_mismatch")
        context = seed.get("operating_contract") or {}
        if not context or context.get("sha256") != digest({k:v for k,v in context.items() if k != "sha256"}):
            raise ValueError("economic_operating_contract_missing_or_hash_invalid")
        for name in ("cost_provenance", "cost_policy_version", "exit_policy_version", "initial_fill_exit_state", "order_leg_ttl_sec"):
            if not context.get(name):
                raise ValueError("economic_operating_field_missing:" + name)
        if any(type(context.get(k)) not in (int, float) or not math.isfinite(context[k])
               for k in ("budget_krw", "cost_rate")) or not 0 <= context["cost_rate"] < 1:
            raise ValueError("economic_budget_or_cost_invalid")
        if not 0 < sum(x["qty"] * x["price"] for x in seed["legs"]) <= context["budget_krw"]:
            raise ValueError("economic_frozen_reserve_budget_invalid")
        capital = context.get("capital_source") or {}
        if capital.get("status") != "recorded_source_only":
            raise ValueError("economic_capital_source:" + str(capital.get("blocker") or "missing"))
        if capital.get("sha256") != digest({k:v for k,v in capital.items() if k != "sha256"}):
            raise ValueError("economic_capital_source_hash_invalid")
        entry_conditional_capital_envelope([seed])
        result.update(status="recorded_source_only", blocker=None, seed_sha256=seed["seed_sha256"],
                      capital_source_sha256=capital["sha256"], evaluation_role="source_contract_only_not_model_validation")
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        result.update(status="source_gap", blocker=str(exc))
    return result


def snapshot(events, as_of):
    """Reuse already loaded events and the existing identity/terminal owner."""
    from src.engine.buy_funnel_sentinel import (
        _machine_primary_entry_funnel, _is_machine_primary_event, _machine_primary_evaluation_key,
        _machine_primary_identity_components,
    )

    now = stamp(as_of)
    recent = [e for e in events if 0 <= (now - stamp(e.emitted_at)).total_seconds() <= 2700]
    funnel = _machine_primary_entry_funnel(recent)
    missing_rows = []
    historical_samples = []
    identified_clocks = []
    # Reuse already loaded cache rows for legacy incident metadata only; no
    # second raw scan or historical funnel/recovery calculation. Bound output.
    for e in events:
        at = stamp(e.emitted_at)
        if at.date() != now.date() or at > now:
            continue
        if e.pipeline != "ENTRY_PIPELINE" or not _is_machine_primary_event(e):
            continue
        if _machine_primary_evaluation_key(e):
            if (now - at).total_seconds() <= 2700:
                identified_clocks.append(at)
            continue
        detail = dict(
            evidence_id=hashlib.sha256(repr((e.emitted_at, e.stage, e.stock_code,
                e.record_id, sorted(e.fields.items()))).encode()).hexdigest(),
            occurred_at=at.isoformat(), stock_code=e.stock_code, stage=e.stage,
            record_id=e.record_id,
            missing_fields=[k for k, v in _machine_primary_identity_components(e).items()
                if not v or v.lower() in {"none", "null", "unknown", "-", "0"}])
        if (now - at).total_seconds() <= 2700:
            missing_rows.append(detail)
        else:
            historical_samples.append(detail)
            # Keep the most recent old receipts even when input is unsorted.
            if len(historical_samples) > 128:
                historical_samples.sort(key=lambda r: (r['occurred_at'], r['evidence_id']))
                historical_samples.pop(0)
    missing_rows.sort(key=lambda row: (row["occurred_at"], row["evidence_id"]))
    retained_missing = [r for r in missing_rows
        if (now - stamp(r["occurred_at"])).total_seconds() <= WINDOW_SEC]
    current_missing = [r for r in missing_rows
        if (now - stamp(r["occurred_at"])).total_seconds() < GRACE_SEC]
    current_identified = [at for at in identified_clocks if (now - at).total_seconds() < GRACE_SEC]
    identity_observation = dict(schema="machine_identity_recency_v1", window_sec=GRACE_SEC,
        status="current_gap" if current_missing else "no_recurrence_observed" if current_identified else "unobservable",
        missing_event_count=len(current_missing), identified_event_count=len(current_identified),
        current_missing_first_at=current_missing[0]["occurred_at"] if current_missing else None,
        current_missing_last_at=current_missing[-1]["occurred_at"] if current_missing else None,
        latest_identified_at=max(current_identified).isoformat() if current_identified else None,
        missing_first_at=missing_rows[0]["occurred_at"] if missing_rows else None,
        missing_last_at=missing_rows[-1]["occurred_at"] if missing_rows else None,
        examples=current_missing[:3])
    economic = {}
    economic_by_revision = {}
    chain_status = {r["evaluation_key"]: r["revision_chain_status"] for r in funnel["evaluation_ledger"]}
    economic_history = defaultdict(list)
    for e in sorted(recent, key=lambda event: stamp(event.emitted_at)):
        if e.stage not in ECONOMIC_STAGES:
            continue
        key = _machine_primary_evaluation_key(e)
        if key:
            value = e.fields.get("economic_source_monitor_projection")
            value = json.loads(value) if isinstance(value, str) else value
            value = value if isinstance(value, dict) else economic_evidence(e.fields, e.stock_code)
            # Older slim-cache projections omitted this diagnostic, but the
            # original field was retained. No raw rescan or proof regeneration.
            value = {**value, "capacity_blocker": e.fields.get("entry_economic_capacity_blocker")
                     or value.get("capacity_blocker")}
            observation = {"observed_at": stamp(e.emitted_at).isoformat(), "stage": e.stage,
                "mechanistic_action": e.fields.get("entry_mechanistic_action"),
                "machine_observation_sha256": e.fields.get("machine_observation_sha256"),
                "evidence": dict(value)}
            if observation not in economic_history[key]:
                economic_history[key].append(observation)
            revision_key = (key, e.fields.get("machine_observation_sha256")) if chain_status.get(key) == "valid" else (key, None)
            old = economic_by_revision.get(revision_key, {})
            if (old.get("blocker") == "economic_observation_conflicting_proofs"
                or old.get("status") == value.get("status") == "recorded_source_only"
                and old.get("seed_sha256") != value.get("seed_sha256")):
                value = {**old, "status": "source_gap", "blocker": "economic_observation_conflicting_proofs"}
            economic_by_revision[revision_key] = value
            economic[key] = value
    for row in funnel["evaluation_ledger"]:
        row["economic_history"] = economic_history.get(row["evaluation_key"], [])
        feature_guard = (row["mechanistic_action"] == "RECHECK"
                         and row["ai_screen_status"] == "not_requested_required_feature_insufficient"
                         and not row["conflict_reasons"])
        row["economic_source"] = economic.get(row["evaluation_key"], {
            "status": ("guard_excluded" if feature_guard else
                       "not_applicable_machine_source_invalid" if row["mechanistic_action"] not in {"ENTER_NOW", "BLOCK", "RECHECK"}
                       else "source_gap" if stamp(row["first_evaluated_at"]).date().isoformat() >= "2026-09-21" else "historical_not_required"),
            "blocker": ("required_feature_input_insufficient" if feature_guard else
                        "economic_observation_event_missing"
                        if row["mechanistic_action"] in {"ENTER_NOW", "BLOCK", "RECHECK"}
                        else None),
            "owner": "main_entry_execution_owners->pipeline_event_logger->sentinel_cache",
            "closure_test": "same exact attempt publishes its pre-AI economic observation"})
        if row["revision_chain_status"] == "valid":
            missing = {"status": "source_gap", "blocker": "economic_observation_event_missing",
                "owner": "main_entry_execution_owners->pipeline_event_logger->sentinel_cache",
                "closure_test": "same exact revision publishes its pre-AI economic observation"}
            final_hash = row["decision_history"][-1]["machine_observation_sha256"]
            row["economic_source"] = economic_by_revision.get((row["evaluation_key"], final_hash), missing)
            # A later revision's success cannot retrospectively repair an
            # earlier ENTER_NOW's missing proof. Guard exclusions are separate.
            for observed in row["decision_history"]:
                proof = economic_by_revision.get((row["evaluation_key"], observed["machine_observation_sha256"]), missing)
                if observed["action"] == "ENTER_NOW" and proof.get("status") == "source_gap":
                    row["economic_source"] = {**proof, "machine_observation_sha256": observed["machine_observation_sha256"]}
                    break
    return {
        "schema": SCHEMA, "as_of": now.isoformat(),
        "latest_event_at": max((stamp(e.emitted_at) for e in recent), default=now - timedelta(days=1)).isoformat(),
        "auxiliary_ai_semantic_status_counts": funnel.get("auxiliary_ai_semantic_status_counts", {}),
        "auxiliary_ai_semantic_issue_counts": funnel.get("auxiliary_ai_semantic_issue_counts", {}),
        "identity_missing_events": funnel["evaluation_identity_missing_event_count"],
        "rows": [{k: r[k] for k in (
            "evaluation_key", "scanner_promotion_id", "stock_code", "effective_venue",
            "session_bucket", "policy_bundle_hash", "first_evaluated_at", "last_event_at",
            "mechanistic_action", "ai_screen_status", "auxiliary_ai_semantics", "broker_acceptance_observed",
            "final_guard_blocked", "final_state", "conflict_reasons", "source_invalid_decomposition", "economic_source",
            "decision_history", "initial_observed_action", "latest_observed_action",
            "enter_now_observed", "economic_history", "revision_chain_status",
        )} for r in funnel["evaluation_ledger"]],
        "missing_identity_evidence": sorted({r["evidence_id"] for r in retained_missing}),
        "missing_identity_examples": retained_missing[:3],
        "missing_identity_first_at": retained_missing[0]['occurred_at'] if retained_missing else None,
        "missing_identity_last_at": retained_missing[-1]['occurred_at'] if retained_missing else None,
        "historical_identity_samples": historical_samples,
        "identity_observation": identity_observation,
    }


def _nonentry_capacity_observation_gap(row):
    """Only explicit no-fetch non-entry misses are coverage, not submit faults."""
    economic = row.get("economic_source") or {}
    return (row.get("mechanistic_action") in {"BLOCK", "RECHECK"}
            and row.get("ai_screen_status") == "not_requested_machine_nonentry"
            and not row.get("conflict_reasons")
            and not row.get("enter_now_observed")
            and not row.get("broker_acceptance_observed")
            and row.get("final_state") in {"machine_block_point_drop", "machine_recheck_observation"}
            and economic.get("status") == "source_gap"
            and economic.get("blocker") == "exact_broker_capacity_missing"
            and economic.get("capacity_blocker") == "capacity_observation_cache_miss_nonentry")


def _nonentry_downstream_gap(row):
    """An uncalled execution replay is not a machine admission contract."""
    return (row.get("mechanistic_action") in {"BLOCK", "RECHECK"}
            and row.get("ai_screen_status") == "not_requested_machine_nonentry"
            and not row.get("conflict_reasons") and not row.get("enter_now_observed")
            and not row.get("broker_acceptance_observed")
            and row.get("final_state") in {"machine_block_point_drop", "machine_recheck_observation"}
            and (row.get("economic_source") or {}).get("status") == "source_gap")


def _small_json(path):
    if path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("semantic_artifact_size_limit")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("semantic_artifact_invalid")
    return value


def machine_semantics(data_root, now, *, tail_bytes=8 * 1024 * 1024):
    """Bounded receipt audit, not a replay, policy publisher or outcome estimator."""
    from src.engine.scalping import entry_strategy_policy as strategy
    from src.engine.scalping import mechanistic_entry_runtime_policy as runtime
    from src.engine.scalping.ai_decision_trace import _json_bytes
    from src.engine.buy_funnel_sentinel import _canonical_session

    now = stamp(now)
    day = now.date().isoformat()
    result = dict(status="unobservable", metric_role="source_quality_gate",
        decision_authority="report_only", window_policy="recent_30m_bounded_tail",
        sample_floor="none_for_receipt_checks", primary_decision_metric="receipt_mismatch_count",
        source_quality_gate="exact_observation_hash_scope_and_frozen_policy",
        forbidden_uses=["automatic_policy_change", "realized_pnl", "missing_as_zero_ev"],
        selection={}, scopes={}, issues={}, examples=[], observation_count=0,
        source_invalid_count=0, required_feature_guard_count=0, source_invalid_blockers={}, action_replay_performed=False)
    issues = Counter()
    try:
        current = runtime.load_effective(data_root=data_root, target_date=day)
        if not current:
            raise ValueError("current_policy_missing")
        result["current_bundle_sha256"] = current["bundle_sha256"]
        report = _small_json(data_root / "report/ai_decision_action_outcome_calibration" / f"machine_policy_{day}.json")
        digest = runtime.digest({k: v for k, v in report.items() if k != "artifact_content_sha256"})
        if digest != report.get("artifact_content_sha256") or report.get("target_date") != day:
            raise ValueError("selection_artifact_invalid")
        for scope, selected in report.get("selections", {}).items():
            economy = ((selected.get("machine_evidence") or {}).get("train") or {}).get("economics") or {}
            score = strategy.machine_support_adjusted_win_rate(economy)
            recorded = economy.get("support_adjusted_win_rate_pct")
            valid = selected.get("selection_basis") == strategy.MACHINE_SELECTION_VERSION
            if selected.get("promotion_pass"):
                valid = valid and score is not None and isinstance(recorded, (int, float)) and math.isclose(score, recorded, abs_tol=1e-8)
            result["selection"][scope] = dict(version=selected.get("selection_basis"), score_contract_valid=valid,
                promotion_pass=selected.get("promotion_pass"), reasons=selected.get("promotion_errors"),
                unique_opportunities=economy.get("selected_opportunity_count"), win_rate_pct=economy.get("win_rate_pct"),
                support_adjusted_score_pct=recorded, mean_net_path_ev_pct=economy.get("selected_path_ev_pct"),
                realized_pnl=False, report_is_activation_receipt=False)
            if not valid:
                issues["selection_score_contract_invalid"] += 1
        terminal = _small_json(data_root / "report/ai_decision_action_outcome_calibration" / f"machine_policy_terminal_{day}.json")
        if (terminal.get("report_sha256") != report["artifact_content_sha256"]
                or runtime.digest({k:v for k,v in terminal.items() if k != "artifact_content_sha256"}) != terminal.get("artifact_content_sha256")):
            raise ValueError("selection_terminal_binding_invalid")
        result["publication"] = dict(status=terminal.get("status"), activation=terminal.get("activation"),
            actual_pid_consumption="see_per_scope_live_pid_receipts")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result["selection_status"] = "unobservable:" + str(exc)[:160]
    path = data_root / "ai_decision_payloads" / f"ai_decision_payloads_{day}.jsonl"
    generations, seen = {}, set()
    try:
        with path.open("rb") as stream:
            size = path.stat().st_size
            start = max(0, size - tail_bytes)
            stream.seek(start)
            if start:
                stream.readline()
            result.update(tail_truncated=bool(start), source_bytes=size, read_limit_bytes=tail_bytes)
            for line in stream.read(max(0, size - stream.tell())).splitlines(keepends=True):
                if not line.endswith(b"\n"):
                    break
                try:
                    observation = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    issues["observation_json_invalid"] += 1
                    continue
                if not isinstance(observation, dict) or observation.get("schema") != "mechanistic_entry_observation_v1":
                    continue
                at = stamp(observation.get("captured_at"))
                if not at or not 0 <= (now - at).total_seconds() <= WINDOW_SEC:
                    continue
                observed_hash = observation.get("machine_observation_sha256")
                if observed_hash in seen:
                    continue
                seen.add(observed_hash)
                result["observation_count"] += 1
                try:
                    if hashlib.sha256(_json_bytes({k:v for k,v in observation.items() if k != "machine_observation_sha256"})).hexdigest() != observed_hash:
                        raise ValueError("machine_observation_hash_invalid")
                    receipt = observation["runtime_consumption"]
                    bundle_hash = observation["bundle_sha256"]
                    if not isinstance(bundle_hash, str) or len(bundle_hash) != 64 or any(c not in "0123456789abcdef" for c in bundle_hash):
                        raise ValueError("bundle_hash_invalid")
                    if bundle_hash not in generations:
                        bundle = _small_json(runtime.root(data_root) / "generations" / f"{bundle_hash}.json")
                        if runtime.digest({k:v for k,v in bundle.items() if k != "bundle_sha256"}) != bundle_hash:
                            raise ValueError("frozen_bundle_hash_invalid")
                        generations[bundle_hash] = bundle
                    context, source = observation["label_context"], observation["source"]
                    assessment = source.get("assessment") or {}
                    invalid = str(assessment.get("action", "")).upper() == "SOURCE_INVALID"
                    feature_guard = (assessment.get("schema") == "mechanistic_entry_required_feature_v1"
                        and assessment.get("action") == "RECHECK" and assessment.get("reason") == "required_feature_input_insufficient"
                        and (source.get("setup_evidence") or {}).get("source_quality_status") == "blocked")
                    if invalid or feature_guard:
                        result["source_invalid_count" if invalid else "required_feature_guard_count"] += 1
                        for blocker in (source.get("setup_evidence") or {}).get("source_quality_blockers", []):
                            result["source_invalid_blockers"][blocker] = result["source_invalid_blockers"].get(blocker, 0) + 1
                        continue
                    scope = (str(context["effective_venue"]).upper(), _canonical_session(context["session_bucket"]))
                    scoped = runtime.for_cohort(generations[bundle_hash], scope)
                    if not scoped:
                        raise ValueError("frozen_policy_scope_missing")
                    setup = source["setup_evidence"]
                    raw = setup.get("strategy_raw_input")
                    if not isinstance(raw, dict):
                        raise ValueError("machine_raw_input_missing")
                    if strategy.digest(raw) != setup.get("strategy_raw_sha256"):
                        raise ValueError("machine_raw_hash_invalid")
                    profile, selection = strategy.select(scoped["machine_policy"], raw, setup)
                    if (receipt.get("bundle_sha256") != bundle_hash
                            or receipt.get("policy_sha256") != selection["policy_sha256"]
                            or receipt.get("selector_leaf") != selection["leaf"]
                            or receipt.get("effective_thresholds") != profile):
                        raise ValueError("effective_policy_receipt_mismatch")
                    key = "|".join((*scope, bundle_hash, selection["policy_sha256"], selection["leaf"]))
                    counts = result["scopes"].setdefault(key, dict(matched_receipts=0, live_pid_receipts=0,
                        effective_thresholds=profile, current_bundle=bundle_hash == result.get("current_bundle_sha256")))
                    counts["matched_receipts"] += 1
                    try:
                        proc = Path('/proc') / str(int(receipt['pid']))
                        live = (str((proc/'cwd').resolve()) == receipt.get('cwd')
                            and (proc/'stat').read_text().split(') ', 1)[1].split()[19] == receipt.get('process_start_ticks'))
                    except (OSError, ValueError, KeyError, IndexError):
                        live = False
                    counts["live_pid_receipts"] += int(live)
                except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                    reason = str(exc)[:160]
                    issues[reason] += 1
                    if len(result["examples"]) < 3:
                        result["examples"].append(dict(observation_sha256=observed_hash, reason=reason))
    except OSError as exc:
        result["source_status"] = "unobservable:" + type(exc).__name__
    result["issues"] = dict(issues)
    if issues:
        result["status"] = "review_required"
    elif result.get("selection_status") or result.get("source_status"):
        result["status"] = "partial_unobservable"
    elif result["source_invalid_count"] or result["required_feature_guard_count"]:
        result["status"] = "source_invalid_observed"
    elif result["observation_count"]:
        result["status"] = "observed_receipts_match"
    return result


def attach_machine_semantics(result, semantics):
    """Persistent report-only receipt faults; absence never repairs old evidence."""
    result["machine_semantics"] = semantics
    key = "machine_policy_receipt_contract"
    old = result["incidents"].get(key, {})
    if semantics.get("issues"):
        now = stamp(result["as_of"])
        first = old.get("first_seen", result["as_of"]) if old.get("status") in {"pending", "active"} else result["as_of"]
        item = dict(scope=semantics.get("current_bundle_sha256", "unbound"), rule=key,
            category="structural_evidence", first_seen=first, last_seen=result["as_of"],
            status="active" if (now - stamp(first)).total_seconds() >= 240 else "pending",
            count=sum(semantics["issues"].values()), examples=semantics.get("examples", []),
            issues=semantics["issues"], owner="machine_observation->frozen_policy->runtime_receipt",
            closure_test="repair exact receipt source; absence does not repair historical observations",
            notified_status=old.get("notified_status") if old.get("status") in {"pending", "active"} else None)
        if old.get("history"):
            item["history"] = old["history"]
        if old.get("status") == "historical_unresolved":
            item["history"] = (list(old.get("history", [])) + [{k:v for k,v in old.items() if k != "history"}])[-8:]
        result["incidents"][key] = item
    elif old.get("status") == "active":
        result["incidents"][key] = {**old, "status": "historical_unresolved"}
    elif old.get("status") == "pending":
        result["incidents"].pop(key, None)
    item = result["incidents"].get(key, {})
    if item.get("status") == "active" and item.get("notified_status") != item["status"]:
        if key not in result["notification_pending"]:
            result["notification_pending"].append(key)


def evaluate(report, state, now):
    """Pure state transition. Old/stale evidence never triggers recovery or alerts."""
    now = stamp(now)
    source = report.get("submission_monitor") or {}
    as_of = stamp(source.get("as_of"))
    latest = stamp(source.get("latest_event_at"))
    today = now.date().isoformat()
    prior = state if state.get("date") == today and state.get("schema") == SCHEMA else {}
    incidents = dict(prior.get("incidents") or {})
    result = {"schema": SCHEMA, "date": today, "as_of": now.isoformat(),
              "runtime_effect": False, "status": "unobservable", "blocker": None,
              "notification_status": "idle",
              "incidents": incidents, "notification_pending": [], "scopes": {},
              "source_as_of": prior.get("source_as_of"),
              "identity_observation": {"status": "unobservable", "reason": "source_not_validated"},
              "last_notification_at": prior.get("last_notification_at")}
    result["economic_coverage_contract"] = {
        "metric_role": "funnel_count", "decision_authority": "report_only",
        "window_policy": "exact_attempts_current_30_minutes",
        "sample_floor": "none_for_counts_no_quality_acceptance",
        "primary_decision_metric": "economic_gap_action_counts",
        "source_quality_gate": "same_attempt_explicit_nonentry_cache_miss_only",
        "forbidden_uses": ["order_authority", "missing_as_zero_ev", "tuning_population_acceptance"],
    }
    if (report.get("target_date") != today or report.get("dry_run")
            or source.get("schema") != SCHEMA or not as_of or not latest
            or not 0 <= (now - as_of).total_seconds() <= 420
            or not 0 <= (now - latest).total_seconds() <= 600):
        result["blocker"] = "missing_stale_or_noncurrent_sentinel_evidence"
        return result
    if prior.get("source_as_of") and as_of <= stamp(prior["source_as_of"]):
        result["blocker"] = "duplicate_or_reversed_source_snapshot"
        return result
    result.update(status="observing", source_as_of=as_of.isoformat())
    # Preserve the original incident as superseded evidence, without reporting
    # alias normalization as recovery or double-counting its exact attempts.
    for old_key, old in list(incidents.items()):
        parts = str(old.get("scope", "")).split("|")
        if len(parts) != 3 or parts[1] != "KRX_LIKE_PREMARKET" or old.get("superseded_by"):
            continue
        parts[1] = "PREMARKET_KRX_LIKE"
        scope = "|".join(parts)
        key = hashlib.sha256(f"{scope}|{old['rule']}".encode()).hexdigest()[:24]
        def normalized_identity(value):
            fields = value.split("|")
            if len(fields) == 6 and fields[4] == "KRX_LIKE_PREMARKET":
                fields[4] = "PREMARKET_KRX_LIKE"
            return "|".join(fields)
        current = incidents.get(key, {})
        ids = sorted(set(current.get("evidence_ids", [])) | {
            normalized_identity(value) for value in old.get("evidence_ids", [])})
        incidents[key] = {**old, **current, "scope": scope,
            "evidence_ids": ids[:128], "count": max(len(ids), old.get("count", 0), current.get("count", 0)),
            "first_seen": min(old["first_seen"], current.get("first_seen", old["first_seen"])),
            "promotion_ids": sorted(set(old.get("promotion_ids", [])) | set(current.get("promotion_ids", []))),
            "examples": current.get("examples") or [{**example,
                "evaluation_key": normalized_identity(example["evaluation_key"])}
                for example in old.get("examples", [])]}
        incidents[old_key] = {**old, "status": "superseded_alias", "superseded_by": key}
    groups = defaultdict(list)
    for row in source.get("rows", []):
        start = stamp(row.get("first_evaluated_at"))
        if start and 0 <= (now - start).total_seconds() <= 2700:
            scope = "|".join(str(row.get(k) or "missing") for k in (
                "effective_venue", "session_bucket", "policy_bundle_hash"))
            groups[scope].append(row)
    if not groups:
        result.update(status="unobservable", blocker="no_identified_machine_evaluation")
    for scope, all_rows in groups.items():
        rows = [r for r in all_rows if (now - stamp(r["first_evaluated_at"])).total_seconds() <= WINDOW_SEC]
        # Count each promotion once for scarcity, but retain exact attempts for gaps.
        parents = {}
        for row in sorted(rows, key=lambda r: r["first_evaluated_at"]):
            parents[(row["scanner_promotion_id"], row["stock_code"])] = row
        valid = [r for r in parents.values() if not r["conflict_reasons"] and r["mechanistic_action"] != "SOURCE_INVALID"]
        entered = [r for r in valid if r["mechanistic_action"] == "ENTER_NOW"]
        veto = [r for r in entered if r["ai_screen_status"] == "veto"]
        accepted = [r for r in rows if r["broker_acceptance_observed"]]
        gaps = [r for r in all_rows if (now - stamp(r["first_evaluated_at"])).total_seconds() >= GRACE_SEC
                and (r["conflict_reasons"] or r["mechanistic_action"] == "SOURCE_INVALID"
                     or r["final_state"].startswith("lineage_gap")
                     or r["final_state"] == "pending_broker_reconciliation"
                     or (r["ai_screen_status"] == "pass" and r["final_state"] == "pending"))]
        economic_gaps = [r for r in all_rows
            if (now - stamp(r["first_evaluated_at"])).total_seconds() >= GRACE_SEC
            and (r.get("economic_source") or {}).get("status") == "source_gap"
            and not _nonentry_downstream_gap(r)]
        observation_gaps = [r for r in rows if _nonentry_capacity_observation_gap(r)]
        tests = {
            "economic_producer_gap": (economic_gaps, "structural_evidence", 240),
            "source_or_submit_lineage_gap": (gaps, "structural_evidence", 240),
            "enter_now_scarcity": (valid if len(valid) >= MIN_PROMOTIONS and not entered
                and not any(r.get("enter_now_observed") for r in rows) else [], "review_required", PERSIST_SEC),
            "ai_veto_concentration": (veto if len(entered) >= MIN_PROMOTIONS and len(veto) / len(entered) >= .9 and not accepted else [], "review_required", PERSIST_SEC),
        }
        result["scopes"][scope] = {"unique_promotions": len(parents), "valid_promotions": len(valid),
            "enter_now_observed_attempts": sum(bool(r.get("enter_now_observed")) for r in rows),
            "enter_now_observed_conflicting_attempts": sum(bool(r.get("enter_now_observed")) and bool(r["conflict_reasons"]) for r in rows),
            "enter_now": len(entered), "veto": len(veto), "accepted_attempts": len(accepted),
            "unresolved_attempts": len(gaps), "economic_producer_gaps": len(economic_gaps),
            "nonentry_capacity_observation_gaps": len(observation_gaps),
            "nonentry_downstream_observation_gaps": sum(_nonentry_downstream_gap(r) for r in rows),
            "economic_producer_gap_owner": "downstream_execution_replay_not_machine_tuning",
            "nonentry_capacity_observation_examples": [{k: r.get(k) for k in
                ("stock_code", "evaluation_key", "first_evaluated_at", "mechanistic_action", "economic_source")}
                for r in observation_gaps[:3]],
            "economic_gap_action_counts": {action: sum(r["mechanistic_action"] == action
                and (r.get("economic_source") or {}).get("status") == "source_gap" for r in rows)
                for action in ("ENTER_NOW", "BLOCK", "RECHECK", "SOURCE_INVALID")},
            "economic_status_counts": {status: sum((r.get("economic_source") or {}).get("status") == status for r in rows)
                for status in ("recorded_source_only", "source_gap", "guard_excluded", "unsupported_scope")}, "guard_blocked": sum(r["final_guard_blocked"] for r in rows)}
        for rule, (bad, category, persistence) in tests.items():
            key = hashlib.sha256(f"{scope}|{rule}".encode()).hexdigest()[:24]
            old = incidents.get(key, {})
            ids = sorted({r["evaluation_key"] for r in bad})
            if bad:
                first = old.get("first_seen", now.isoformat()) if old.get("status") in {"pending", "active"} else now.isoformat()
                # Ratios need new independent promotions, not repeated snapshots.
                identities = sorted({f'{r["scanner_promotion_id"]}|{r["stock_code"]}' for r in bad})
                new_support = bool(set(identities) - set(old.get("promotion_ids", [])))
                confirmed = bool(old) and (now - stamp(first)).total_seconds() >= persistence
                confirmed = confirmed and (category == "structural_evidence" or new_support or old.get("status") == "active")
                item = {"scope": scope, "rule": rule, "category": category, "first_seen": first,
                    "last_seen": now.isoformat(), "status": "active" if confirmed else "pending",
                    "evidence_ids": ids[:128], "promotion_ids": identities[:128],
                    "count": len(ids), "notified_status": old.get("notified_status"),
                    "examples": [{k: r.get(k) for k in ("stock_code", "evaluation_key", "mechanistic_action", "final_state", "conflict_reasons", "auxiliary_ai_semantics", "source_invalid_decomposition", "economic_source")} for r in bad[:3]],
                    "owner": (bad[0].get("economic_source") or {}).get("owner") if rule == "economic_producer_gap" else "buy_funnel_sentinel.machine_primary_entry_funnel",
                    "closure_test": "same attempt publishes valid frozen economic proof" if rule == "economic_producer_gap" else "same attempt receives a consistent terminal; ratios recover on new valid promotions"}
                if old.get("history"):
                    item["history"] = old["history"]
                if old.get("status") == "observation_only_unresolved":
                    item["history"] = (list(old.get("history") or []) + [
                        {k: v for k, v in old.items() if k != "history"}])[-8:]
                    item["notified_status"] = None
                incidents[key] = item
            elif (rule == "economic_producer_gap" and old
                  and old.get("status") in {"active", "pending"}
                  and old.get("count") == len(set(old.get("evidence_ids", [])))
                  and old.get("evidence_ids")
                  and set(old["evidence_ids"]) <= {r["evaluation_key"] for r in all_rows
                                                    if _nonentry_downstream_gap(r)}):
                # Reclassification is not source recovery. Preserve old proof
                # IDs/count/examples; unknown/expired/mixed incidents stay open.
                incidents[key] = {**old, "status": "observation_only_unresolved",
                    "classification_reason": "exact_nonentry_downstream_evidence_not_machine_tuning",
                    "classified_at": now.isoformat()}
            elif old and old.get("status") == "active":
                # Window expiration is not recovery. Require explicit closure evidence.
                old_ids = set(old.get("evidence_ids", []))
                resolved = {r["evaluation_key"] for r in all_rows if r["evaluation_key"] in old_ids
                    and ((r.get("economic_source") or {}).get("status") == "recorded_source_only"
                         if rule == "economic_producer_gap" else not r["conflict_reasons"]
                         and r["final_state"] in {"submit_pipeline_reached", "final_guard_blocked", "broker_rejected"})}
                healthy = bool(old_ids and old.get("count") == len(old_ids) and old_ids <= resolved) if category == "structural_evidence" else bool(accepted and any(r["evaluation_key"] not in old_ids for r in accepted))
                if healthy:
                    incidents[key] = {**old, "status": "recovered", "last_seen": now.isoformat()}
            elif old and old.get("status") == "pending":
                incidents.pop(key, None)
    missing = source.get("missing_identity_evidence") or []
    key = "unbound_machine_identity"
    old = incidents.get(key, {})
    observation = source.get("identity_observation") or {}
    current_status = (observation.get("status") if observation.get("schema") == "machine_identity_recency_v1"
                      else "unobservable")
    if current_status not in {"current_gap", "no_recurrence_observed", "unobservable"}:
        current_status = "unobservable"
    result["identity_observation"] = observation or {"status": "unobservable", "reason": "legacy_source_no_recency"}
    if missing:
        recurrence = (old.get("status") == "historical_unresolved" and current_status == "current_gap"
                      and bool(set(missing) - set(old.get("evidence_ids", []))))
        history = list(old.get("history") or [])
        if recurrence:
            history.append({k: v for k, v in old.items() if k != "history"})
        first = old.get("first_seen", now.isoformat()) if not recurrence else now.isoformat()
        status = "active"  # Exact current identity loss needs no ratio/persistence floor.
        if current_status != "current_gap":
            status = "historical_unresolved"
        # A shrinking window must not erase the already recorded old incident.
        preserve = bool(old) and not recurrence and (status == "historical_unresolved"
                                                    or old.get("status") == "historical_unresolved")
        if preserve:
            status = "historical_unresolved"
        incidents[key] = {**old, "scope": "unbound", "rule": "source_identity_missing",
            "category": "structural_evidence", "first_seen": first, "last_seen": now.isoformat(),
            "status": status, "current_status": current_status, "history": history,
            "count": old.get("count", len(missing)) if preserve else len(missing),
            "evidence_ids": old.get("evidence_ids", missing[:128]) if preserve else missing[:128],
            "examples": (old.get("examples") or []) if preserve else source.get("missing_identity_examples") or [],
            "occurred_first_at": old.get("occurred_first_at") if preserve else source.get("missing_identity_first_at"),
            "occurred_last_at": old.get("occurred_last_at") if preserve else source.get("missing_identity_last_at"),
            "notified_status": None if recurrence else old.get("notified_status"),
            "normal_observation_pending": False if recurrence else old.get("normal_observation_pending", False),
            "normal_observation_notified_at": None if recurrence else old.get("normal_observation_notified_at"),
            "owner": "ENTRY_PIPELINE machine producer identity",
            "closure_test": "new identified machine evaluations with no missing identity; old unbound rows remain unrepairable"}
    elif old:
        incidents[key] = {**old, "status": "historical_unresolved", "current_status": current_status}
    item = incidents.get(key, {})
    if (item.get("status") == "historical_unresolved"
            and old.get("status") == "active" and old.get("notified_status") == "active"):
        item["normal_observation_pending"] = True
    if item and not item.get('examples'):
        matched = {r['evidence_id']: r for r in (source.get('historical_identity_samples', [])
                    + source.get('missing_identity_examples', []))
                   if r.get('evidence_id') in set(item.get('evidence_ids', []))}
        if matched:
            details = sorted(matched.values(), key=lambda r: r['occurred_at'])
            item['examples'] = details[:3]
            item['detail_basis'] = 'existing_cache_exact_evidence_hash_match'
            if len(matched) == len(set(item.get('evidence_ids', []))) == item.get('count'):
                item['occurred_first_at'] = details[0]['occurred_at']
                item['occurred_last_at'] = details[-1]['occurred_at']
    if missing or old:
        result["scopes"]["unbound"] = {"missing_identity_events": len(missing),
            "current_missing_events": observation.get("missing_event_count"), "current_status": current_status}
    if observation.get("missing_event_count"):
        result["blocker"] = "machine_identity_missing_events"
        result["identity_missing_events"] = observation["missing_event_count"]
    # Absent scopes/stale sources retain incidents without asserting they resolved.
    result["notification_pending"] = [k for k, v in incidents.items()
        if _notification_kind(v, result) and v["scope"] in result["scopes"]]
    return result


def _notification_kind(item, result):
    status = item.get("status")
    if status in {"active", "recovered"} and item.get("notified_status") != status:
        return status
    observation = result.get("identity_observation") or {}
    if (status == "historical_unresolved" and item.get("rule") == "source_identity_missing"
            and item.get("normal_observation_pending")
            and observation.get("status") == "no_recurrence_observed"
            and observation.get("missing_event_count") == 0
            and observation.get("identified_event_count", 0) > 0):
        return "normal_observation"
    return None


def notify(result, path, send=None):
    keys = [key for key in result["notification_pending"]
            if _notification_kind(result["incidents"][key], result)]
    keys.sort(key=lambda key: _notification_kind(result["incidents"][key], result) != "active")
    last = stamp(result.get("last_notification_at"))
    if last and (stamp(result["as_of"]) - last).total_seconds() < 300:
        result["notification_status"] = "cooldown"
        return
    if not keys:
        return
    messages = []
    for key in keys[:4]:
        item = result["incidents"][key]
        if _notification_kind(item, result) == "normal_observation":
            obs = result["identity_observation"]
            messages.append(
                "현재 정상 관측: 식별자 결손 최근10분 0건 / "
                f'정상 식별 {obs["identified_event_count"]} 이벤트\n'
                "추가 점검 요청 없음. 과거 결손은 보고서에 보존하며 원천 복구를 뜻하지 않습니다.")
            continue
        if item["rule"] == "source_identity_missing":
            obs = result.get("identity_observation") or {}
            examples = obs.get("examples") or item.get("examples") or []
            sample = examples[0] if examples else {}
            messages.append(
                f'{item["status"]}: source_identity_missing\n'
                f'현재 최근10분: {item.get("current_status", "unobservable")} '
                f'/ 결손 {obs.get("missing_event_count", "미확인")}건\n'
                f'과거 원천 복구 주장 없음 / 보존 근거 {item["count"]} 이벤트 (주문 수 아님)\n'
                f'현재 결손 발생: {obs.get("current_missing_first_at") or item.get("occurred_first_at") or "미확인(구형 이력)"} ~ '
                f'{obs.get("current_missing_last_at") or item.get("occurred_last_at") or "미확인(구형 이력)"}\n'
                f'종목: {sample.get("stock_code") or "미확인(구형 이력)"} / '
                f'누락 필드: {", ".join(sample.get("missing_fields") or []) or "미확인(구형 이력)"}\n'
                f'대표 발생시각: {sample.get("occurred_at") or "미확인(구형 이력)"}')
            continue
        example = (item.get("examples") or [{}])[0]
        cause = ((example.get("economic_source") or {}).get("blocker")
                 if item["rule"] == "economic_producer_gap" else
                 (example.get("source_invalid_decomposition") or {}).get("primary_blocker")
                 or next(iter(example.get("conflict_reasons") or []), None)
                 or example.get("final_state") or example.get("reason")
                 or next(iter(item.get("issues") or {}), None))
        cause_text = f"첫 결손: {str(cause)[:180]}\n" if cause else ""
        if item["rule"] == "economic_producer_gap":
            detail = (example.get("economic_source") or {}).get("capacity_blocker")
            cause_text += (f"판정: {example.get('mechanistic_action') or '미확인'} / "
                           f"조회 원인: {detail or '자금 조회 외 계약 결손 또는 구형 근거'}\n"
                           "후단 실행 재생 증거 결손입니다. 기계 튜닝 실패나 실제 주문 실패 건수가 아닙니다.\n")
        messages.append(cause_text + f'{item["status"]}: {item["rule"]}\n{item["scope"]}\n근거 {item["count"]}건 / {item["category"]}\n' +
                        json.dumps(item.get("examples", [])[:1], ensure_ascii=False)[:350])
    actionable = any(_notification_kind(result["incidents"][key], result) == "active" for key in keys[:4])
    title = "제출병목 점검" if actionable else "제출병목 정상 확인"
    message = f"[{title}] 자동 매매 변경 없음\n" + "\n".join(messages) + f"\n근거: {path}"
    if actionable:
        message += "\nCodex에서 원천과 제출 경로를 점검하세요."
    if send is None:
        try:
            token, admin = _load_telegram_config()
        except (OSError, ValueError):
            result["notification_status"] = "configuration_invalid"
            return
        if not token or not admin:
            result["notification_status"] = "configuration_missing"
            return
        send = lambda text: _send_telegram(token, admin, text)
    try:
        send(message[:4000])
    except Exception as exc:
        # Never leak a token-bearing HTTP exception into logs.
        result["notification_status"] = f"retry_required:{type(exc).__name__}"
        return
    for key in keys[:4]:
        if _notification_kind(result["incidents"][key], result) == "normal_observation":
            result["incidents"][key]["normal_observation_pending"] = False
            result["incidents"][key]["normal_observation_notified_at"] = result["as_of"]
        result["incidents"][key]["notified_status"] = result["incidents"][key]["status"]
    result["notification_status"] = "sent"
    result["last_notification_at"] = result["as_of"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--notify", action="store_true")
    args = parser.parse_args()
    state_path = PROJECT_ROOT / "tmp/submission_bottleneck_monitor_state.json"
    output = PROJECT_ROOT / "data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json"
    try:
        if args.report.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("report_size_limit")
        report = json.loads(args.report.read_text())
        if not isinstance(report, dict):
            report = {}
    except (OSError, ValueError):
        report = {}
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        result = evaluate(report, _load_state(state_path), datetime.now(KST))
        attach_machine_semantics(result, machine_semantics(PROJECT_ROOT / "data", result["as_of"]))
        if args.notify:
            notify(result, output)
        _write_state(state_path, result)
        _write_state(output, result)
        _write_state(output.with_name(f"submission_bottleneck_monitor_{result['date']}.json"), result)
    print(json.dumps({k: result.get(k) for k in ("status", "blocker", "notification_status")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
