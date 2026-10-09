"""Pure, advisory postclose projection, as-of joins and paired statistics.

No runtime evaluator, provider, broker, publisher or notification transport is
called here. Missing identities, listing metadata and outcomes remain missing.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import hashlib
import json
import math
import random
import sqlite3
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.market_panic_breadth_collector import (
    market_weakness_observation_contract_errors,
)
from src.engine.risk.market_weakness_state import advance_market_latch
from src.engine.risk.market_weakness_threshold_policy import observation_thresholds

KST = ZoneInfo("Asia/Seoul")
VERSION = "main_market_weakness_research_v1"
LABEL = dict(
    target_net_pct=0.4, stop_net_pct=-3.0, cost_rate=0.0023, horizon_seconds=1800
)
AUTH = dict(
    decision_authority="postclose_research_advisory_only",
    runtime_effect=False,
    allowed_runtime_apply=False,
    actual_order_submitted=False,
    broker_order_forbidden=True,
)
FEATURES = ("volume_ratio_60s", "drawdown_5m_pct")
DELAYS = (0, 60, 180)


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def seal(value):
    value = {k: v for k, v in value.items() if k != "artifact_content_sha256"}
    return dict(value, artifact_content_sha256=digest(value))


def number(value):
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return n if math.isfinite(n) else None


def timestamp(value):
    """Research timestamps require an explicit offset; never guess naive KST."""
    try:
        t = datetime.fromisoformat(str(value))
        return t.astimezone(KST) if t.tzinfo is not None else None
    except (ValueError, TypeError, OverflowError):
        return None


def scope_key(row):
    return digest(
        {
            k: row.get(k)
            for k in (
                "symbol",
                "listing_market",
                "session",
                "route",
                "machine_hash",
                "auxiliary_hash",
                "decision_origin",
                "classification_kind",
                "outcome_kind",
                "policy_scope",
                "scope_parent_machine_payload_sha256",
            )
        }
    )


def project_trace(raw, source_date, listing_market=None):
    """Project actual ai_decision_trace_v1, including pre-provider non-entry."""
    if (
        raw.get("schema") != "ai_decision_trace_v1"
        or raw.get("decision_stage") != "entry_screen"
    ):
        return None, "not_entry_trace"
    at = timestamp(raw.get("decision_ts"))
    symbol = raw.get("stock_code")
    native = raw.get("continuous_reversal_consumption")
    native = native if isinstance(native, dict) else {}
    assessment = raw.get("entry_mechanistic_policy_decision")
    assessment = assessment if isinstance(assessment, dict) else {}
    event = assessment.get("event")
    event = event if isinstance(event, dict) else {}
    canonical = (
        assessment.get("canonical_opportunity_id")
        or native.get("canonical_opportunity_id")
        or event.get("canonical_opportunity_id")
    )
    trace_id, attempt = raw.get("decision_trace_id"), raw.get("evaluation_attempt_id")
    stage = raw.get("source_event_stage")
    if not (
        at
        and at.date().isoformat() == source_date
        and isinstance(symbol, str)
        and len(symbol) == 6
        and symbol.isdigit()
        and trace_id
        and attempt
        and stage
    ):
        return None, "trace_identity_or_time_invalid"
    identity = str(canonical) if canonical else digest([trace_id, attempt, stage])
    verdict = raw.get("entry_ai_risk_verdict")
    called = raw.get("provider_called") is True
    valid_ai = bool(
        called
        and raw.get("decision_evaluation_status") == "evaluated"
        and raw.get("result_source") in {"live", "prior_valid"}
        and raw.get("prompt_version")
        and (
            raw.get("entry_ai_component_sha256")
            or native.get("auxiliary_component_sha256")
        )
    )
    if not valid_ai:
        verdict = "not_called" if not called else "not_evaluated"
    elif verdict not in {"PASS", "VETO", "CAUTION", "INSUFFICIENT"}:
        verdict = "not_evaluated"
    features = {k: number(event.get(k)) for k in FEATURES}
    ask = number(event.get("entry_ask"))
    row = dict(
        opportunity_id=identity,
        identity_grade="canonical" if canonical else "trace_only",
        decision_trace_id=trace_id,
        evaluation_attempt_id=attempt,
        source_event_stage=stage,
        source_date=source_date,
        decision_ts=at.isoformat(),
        time_precision="exact",
        machine_confirmed_at=event.get("at"),
        auxiliary_completed_at=raw.get("response_completed_at"),
        submit_at=None,
        symbol=symbol,
        listing_market=listing_market,
        session=raw.get("session_bucket"),
        route=raw.get("market_data_route"),
        machine_hash=raw.get("machine_bundle_sha256"),
        auxiliary_hash=raw.get("entry_ai_component_sha256")
        or native.get("auxiliary_component_sha256"),
        auxiliary_version=raw.get("prompt_version"),
        machine_action=raw.get("entry_mechanistic_action"),
        auxiliary_verdict=verdict,
        event_id=native.get("event_id") or assessment.get("event_id"),
        entry_ask=ask,
        features=features,
        decision_origin="natural_decision",
        outcome="U",
        outcome_reason="exact_label_binding_missing",
        outcome_kind="counterfactual_price_path",
        fill_kind="unobserved",
        cost_status="configured_label_cost",
        classification_time_basis=(
            "auxiliary_completion"
            if timestamp(raw.get("response_completed_at"))
            else "recorded_decision_proxy"
        ),
        **AUTH,
    )
    return row, None


def project_replay(record, event, source_date, parent_hash, listing_market=None):
    at = timestamp(event.get("at"))
    epoch = number(event.get("epoch"))
    ask = number(event.get("entry_ask"))
    if not (
        at
        and epoch is not None
        and abs(at.timestamp() - epoch) < 0.001
        and at.date().isoformat() == source_date
        and record.get("day") == source_date
        and event.get("symbol") == record.get("symbol")
        and record.get("opportunity_key")
        and record.get("native_alias") == event.get("canonical_opportunity_id")
    ):
        return None, "replay_identity_or_time_invalid"
    row = dict(
        opportunity_id=record["opportunity_key"],
        canonical_alias=record["native_alias"],
        identity_grade="canonical",
        policy_scope=record.get("scope"),
        source_date=source_date,
        decision_ts=at.isoformat(),
        time_precision="exact",
        machine_confirmed_at=at.isoformat(),
        auxiliary_completed_at=None,
        submit_at=None,
        symbol=event["symbol"],
        listing_market=listing_market,
        session=event.get("session"),
        route=event.get("venue"),
        machine_hash=parent_hash,
        auxiliary_hash=None,
        auxiliary_version=None,
        machine_action="ENTER_NOW",
        auxiliary_verdict="not_called",
        event_id=event.get("event_id"),
        entry_ask=ask,
        features={k: number(event.get(k)) for k in FEATURES},
        decision_origin="confirmation_replay",
        outcome_kind="counterfactual_price_path",
        fill_kind="unobserved",
        cost_status="configured_label_cost",
        **AUTH,
    )
    row["outcome"], row["outcome_reason"] = label_value(
        record.get("outcome"), ask, LABEL
    )
    return row, None


def label_value(label, ask, contract):
    if contract != LABEL or ask is None or ask <= 0 or not isinstance(label, dict):
        return "U", "label_contract_or_actual_ask_missing"
    status = label.get("status")
    if status == "WIN":
        delay = number(label.get("delay_sec"))
        if delay is None or not 0 <= delay <= 1800:
            return "U", "target_time_unverified"
        return "W", None
    if status in {"FAIL_STOP", "FAIL_TIMEOUT"}:
        return "F", None
    return "U", label.get("reason") or "outcome_unresolved"


class ObservationIndex:
    """Validate the retained day once and search only the original 300-second window."""

    def __init__(self, observations):
        entries = []
        for o in observations:
            at = timestamp(o.get("as_of"))
            if at and not market_weakness_observation_contract_errors(o):
                entries.append((at, str(o["observation_id"]), o))
        self.entries = sorted(entries, key=lambda item: (item[0], item[1]))
        self.times = [entry[0] for entry in self.entries]

    def __len__(self):
        return len(self.entries)

    def window(self, at):
        low = bisect_left(self.times, at - timedelta(seconds=300))
        high = bisect_right(self.times, at)
        return (entry[2] for entry in self.entries[low:high])


def join_snapshot(row, observations, *, delay=0):
    """No future source or availability. Listing market and execution are separate."""
    at = timestamp(row.get("auxiliary_completed_at") or row.get("decision_ts"))
    market = row.get("listing_market")
    if not (
        at
        and market in {"KOSPI", "KOSDAQ"}
        and row.get("machine_hash")
        and row.get("session")
        and row.get("route")
    ):
        return dict(grade="U", reason="scope_or_listing_market_missing")
    if row.get("time_precision") == "minute":
        at = at.replace(second=0, microsecond=0)
    candidates = []
    index = (
        observations
        if isinstance(observations, ObservationIndex)
        else ObservationIndex(observations)
    )
    for o in index.window(at):
        t = timestamp(o.get("as_of"))
        if not t or t.date() != at.date():
            continue
        available = timestamp(o.get("observed_available_at"))
        available = max(t, available) if available else t + timedelta(seconds=delay)
        if available > at or not 0 <= (at - t).total_seconds() <= 300:
            continue
        known_delay = number(o.get("observed_source_delay_sec"))
        if known_delay is not None and known_delay > 180:
            continue
        candidates.append((t, available, o))
    if not candidates:
        return dict(grade="U", reason="source_unavailable_stale_or_future")
    t, available, o = max(candidates, key=lambda p: (p[0], str(p[2]["observation_id"])))
    raw = o["raw_state"]
    affected, recovered = o.get("affected_markets", []), o.get(
        "recovery_evidence_markets", []
    )
    state = (
        "WEAKNESS"
        if market in affected
        else ("RECOVERY" if market in recovered else "NEAR_WEAKNESS_BOUNDARY")
    )
    if raw == "UNKNOWN":
        state = "UNKNOWN"
    grade = (
        "C"
        if row.get("time_precision") == "minute"
        else (
            "A"
            if o.get("availability_receipt_verified") is True
            and timestamp(o.get("observed_available_at")) is not None
            else "B"
        )
    )
    return dict(
        grade=grade,
        state=state,
        observation_id=o["observation_id"],
        as_of=t.isoformat(),
        available_at=available.isoformat(),
        availability_assumed=grade != "A",
        age_sec=(at - t).total_seconds(),
        index_change_pct=number(
            (o.get("evidence", {}).get("market_index_change_pct") or {}).get(market)
        ),
        episode_id=o.get("reconstructed_episode_ids", {}).get(market)
        or o["observation_id"],
        reconstructed_active=o.get("reconstructed_active", {}).get(market),
        policy_hash=(o.get("hysteresis_policy") or {}).get("policy_hash"),
        classification_kind="raw_market_snapshot",
        legacy_research_metadata=(o.get("response_research_contract") or {}).get(
            "status"
        )
        != "source_only_observation_no_execution_bridge",
    )


def reconstruct_latches(observations):
    """Research reconstruction only; source policy changes break the lineage."""
    states, previous_key, previous_at, episode = {}, None, None, {}
    result = []
    for original in sorted(
        observations,
        key=lambda o: timestamp(o.get("as_of")) or datetime.min.replace(tzinfo=KST),
    ):
        o = dict(original)
        at = timestamp(o.get("as_of"))
        if not at or market_weakness_observation_contract_errors(o):
            continue
        activation, release, spacing = observation_thresholds(o)
        key = (
            o["target_date"],
            (o.get("hysteresis_policy") or {}).get("policy_hash"),
            activation,
            release,
        )
        if key != previous_key:
            states, previous_at, episode = {}, None, {}
        if previous_at is None or (at - previous_at).total_seconds() >= spacing:
            for m in ("KOSPI", "KOSDAQ"):
                classification = (
                    "unknown"
                    if o.get("raw_state") == "UNKNOWN"
                    else (
                        "weak"
                        if m in o.get("affected_markets", [])
                        else (
                            "recovery"
                            if m in o.get("recovery_evidence_markets", [])
                            else "neutral"
                        )
                    )
                )
                before = states.get(m, {})
                states[m] = advance_market_latch(
                    before, classification, activation=activation, release=release
                )
                if classification == "weak" and before.get("last_class") != "weak":
                    episode[m] = digest([key, m, o["observation_id"]])
            previous_at = at
        o["reconstructed_active"] = {
            m: states.get(m, {}).get("active", False) for m in ("KOSPI", "KOSDAQ")
        }
        o["reconstructed_episode_ids"] = dict(episode)
        result.append(o)
        previous_key = key
    return result


def attach_joins(row, observations):
    row = dict(
        row,
        joins={str(d): join_snapshot(row, observations, delay=d) for d in DELAYS},
        classification_kind="raw_market_snapshot",
    )
    row["scope_key"] = scope_key(row)
    return row


def quantile(histogram, fraction):
    pairs = sorted((float(k), v) for k, v in histogram.items())
    count = sum(v for _, v in pairs)
    if not count:
        return None
    rank, passed = max(1, math.ceil(count * fraction)), 0
    for value, n in pairs:
        passed += n
        if passed >= rank:
            return value


def freeze_candidates(previous_daily, source_generation):
    """Use outcome-independent previous sealed feature histograms; no cross product."""
    scopes = {}
    for sid, summary in previous_daily.get("scopes", {}).items():
        candidates = []
        hist = summary.get("feature_histograms", {})
        for feature in FEATURES:
            for q in (0.25, 0.5, 0.75):
                x = quantile(hist.get("index_change_pct", {}), q)
                y = quantile(hist.get(feature, {}), q)
                if x is None or y is None or x > 0:
                    continue
                definition = dict(
                    kind="post_auxiliary_withhold_cf",
                    axis=feature,
                    weakness_index_max_pct=x,
                    feature_max_exclusive=y,
                    before="no_additional_withhold",
                    after=y,
                    unit="ratio" if feature == "volume_ratio_60s" else "pct",
                    operator="lt",
                    parent_hash=summary["scope"].get("machine_hash"),
                    auxiliary_hash=summary["scope"].get("auxiliary_hash"),
                    policy_scope=summary.get("policy_scope"),
                    scope_parent_machine_payload_sha256=summary.get(
                        "scope_parent_machine_payload_sha256"
                    ),
                    auxiliary_binding=summary.get("auxiliary_binding"),
                )
                if definition not in [c["definition"] for c in candidates]:
                    candidates.append(
                        dict(candidate_id=digest(definition), definition=definition)
                    )
        scopes[sid] = dict(
            scope=summary["scope"],
            candidates=candidates[:6],
            fixed_after_source_date=previous_daily["source_date"],
            seed_source_generation=source_generation,
            machine_status="numeric_adjustment_unidentifiable",
        )
    return seal(
        dict(
            schema=VERSION + ":fixed_candidates",
            fixed_after_source_date=previous_daily["source_date"],
            seed_source_generation=source_generation,
            scopes=scopes,
            **AUTH,
        )
    )


def selection(row, candidate, join):
    if join.get("grade") not in {"A", "B"} or row.get("identity_grade") != "canonical":
        return None
    d = candidate["definition"]
    if d["kind"] != "post_auxiliary_withhold_cf":
        return None
    if row.get("auxiliary_verdict") != "PASS" or not row.get("auxiliary_hash"):
        return None
    value, index = number(row.get("features", {}).get(d["axis"])), number(
        join.get("index_change_pct")
    )
    if value is None or index is None:
        return None
    withhold = (
        join.get("state") == "WEAKNESS"
        and index <= d["weakness_index_max_pct"]
        and value < d["feature_max_exclusive"]
    )
    return not withhold


def metric(counts):
    w, f, u = (counts.get(k, 0) for k in ("W", "F", "U"))
    return dict(
        W=w, F=f, U=u, resolved=w + f, raw_win_rate=w / (w + f) if w + f else None
    )


def pair_delta(counts, *, worst_u=False):
    selected, excluded = counts["selected"], counts["excluded"]
    baseline = Counter(selected) + Counter(excluded)
    if worst_u:
        base_n = sum(baseline.get(k, 0) for k in ("W", "F", "U"))
        selected_n = sum(selected.get(k, 0) for k in ("W", "F", "U"))
        b = (baseline.get("W", 0) + excluded.get("U", 0)) / base_n if base_n else None
        c = selected.get("W", 0) / selected_n if selected_n else None
    else:
        b, c = metric(baseline)["raw_win_rate"], metric(selected)["raw_win_rate"]
    return c - b if b is not None and c is not None else None


def subtract_pairs(total, part):
    return {
        field: {
            k: total[field].get(k, 0) - part[field].get(k, 0) for k in ("W", "F", "U")
        }
        for field in ("selected", "excluded")
    }


def merge_pairs(pairs):
    result = dict(selected=Counter(), excluded=Counter())
    for p in pairs:
        for field in result:
            result[field].update(p[field])
    return result


class Aggregator:
    """Consume compact rows once; retain per-day/episode counts, never AI bodies."""

    def __init__(self, candidates=None, *, scratch_root=None):
        self.candidates = candidates or {}
        self.census, self.scopes = Counter(), {}
        self.pairs = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: defaultdict(
                        lambda: dict(selected=Counter(), excluded=Counter())
                    )
                )
            )
        )
        self.historical_pairs = defaultdict(
            lambda: defaultdict(lambda: dict(selected=Counter(), excluded=Counter()))
        )
        self.conflicts = set()
        self.conflict_scopes = set()
        self._temp = None
        if scratch_root is not None:
            Path(scratch_root).mkdir(parents=True, exist_ok=True)
            self._temp = tempfile.TemporaryDirectory(
                prefix="aggregate-", dir=scratch_root
            )
        self.db = sqlite3.connect(
            str(Path(self._temp.name) / "dedup.sqlite") if self._temp else ":memory:"
        )
        self.db.execute("PRAGMA cache_size=-2048")
        self.db.execute(
            "CREATE TABLE identities(identity TEXT PRIMARY KEY,scope TEXT,binding TEXT,row TEXT,conflict INTEGER)"
        )
        self._finished = False

    def close(self):
        self.db.close()
        if self._temp:
            self._temp.cleanup()

    def add(self, row):
        if self._finished:
            raise ValueError("aggregate_already_finalized")
        self.census["projected_rows"] += 1
        self.census[
            "origin_"
            + str(row.get("decision_origin"))
            + "_"
            + str(row.get("response_origin", "no_stored_auxiliary"))
        ] += 1
        self.census["attempt_machine_" + str(row.get("machine_action"))] += 1
        self.census["attempt_auxiliary_" + str(row.get("auxiliary_verdict"))] += 1
        sid = row["scope_key"]
        identity = digest([row.get("decision_origin"), row.get("opportunity_id"), sid])
        # Retry/response timestamps are attempt evidence, not new outcome units.
        binding = digest(
            {
                k: row.get(k)
                for k in (
                    "event_id",
                    "machine_confirmed_at",
                    "entry_ask",
                    "features",
                    "outcome",
                )
            }
        )
        old = self.db.execute(
            "SELECT binding,row,conflict FROM identities WHERE identity=?", (identity,)
        ).fetchone()
        if old:
            self.census["duplicate_rows"] += 1
            if old[0] != binding:
                self.conflicts.add(identity)
                self.conflict_scopes.add(sid)
                self.db.execute(
                    "UPDATE identities SET conflict=1 WHERE identity=?", (identity,)
                )
            elif not old[2]:
                first = json.loads(old[1])
                # The first actually evaluated response is deterministic and label independent.
                if first.get("auxiliary_verdict") in {
                    "not_called",
                    "not_evaluated",
                } and row.get("auxiliary_verdict") not in {
                    "not_called",
                    "not_evaluated",
                }:
                    self.db.execute(
                        "UPDATE identities SET row=? WHERE identity=?",
                        (json.dumps(row, sort_keys=True), identity),
                    )
            return
        self.db.execute(
            "INSERT INTO identities VALUES(?,?,?,?,0)",
            (identity, sid, binding, json.dumps(row, sort_keys=True)),
        )

    def finalize(self):
        if not self._finished:
            for (raw,) in self.db.execute(
                "SELECT row FROM identities WHERE conflict=0 ORDER BY identity"
            ):
                self._add(json.loads(raw))
            self.census["quarantined_conflicts"] = len(self.conflicts)
            self._finished = True

    def merge(self, aggregate):
        self.finalize()
        self.census.update(aggregate["census"])
        self.conflict_scopes.update(aggregate.get("conflict_scopes", []))
        for sid, source in aggregate["scopes"].items():
            if sid not in self.scopes:
                self.scopes[sid] = dict(
                    scope=source["scope"],
                    counts=Counter(),
                    feature_histograms=defaultdict(Counter),
                    policy_scope=source.get("policy_scope"),
                    auxiliary_binding=source.get("auxiliary_binding"),
                    scope_parent_machine_payload_sha256=source.get(
                        "scope_parent_machine_payload_sha256"
                    ),
                )
            self.scopes[sid]["counts"].update(source["counts"])
            for k, h in source["feature_histograms"].items():
                self.scopes[sid]["feature_histograms"][k].update(h)
        for sid, cid, pair in aggregate.get("historical_pairs", []):
            target = self.historical_pairs[sid][cid]
            for k in target:
                target[k].update(pair[k])
        for sid, cid, delay, cluster, pair in aggregate.get("pairs", []):
            target = self.pairs[sid][cid][delay][tuple(cluster)]
            for k in target:
                target[k].update(pair[k])

    def export(self):
        self.finalize()
        pairs = [
            [sid, cid, delay, list(cluster), pair]
            for sid, cs in self.pairs.items()
            for cid, ds in cs.items()
            for delay, clusters in ds.items()
            for cluster, pair in clusters.items()
        ]
        return dict(
            census=dict(self.census),
            scopes=self.scopes,
            pairs=pairs,
            conflict_scopes=sorted(self.conflict_scopes),
            historical_pairs=[
                [sid, cid, pair]
                for sid, cs in self.historical_pairs.items()
                for cid, pair in cs.items()
            ],
        )

    def _add(self, row):
        sid = row["scope_key"]
        if sid not in self.scopes:
            self.scopes[sid] = dict(
                scope={
                    k: row.get(k)
                    for k in (
                        "symbol",
                        "listing_market",
                        "session",
                        "route",
                        "machine_hash",
                        "auxiliary_hash",
                        "decision_origin",
                        "classification_kind",
                        "outcome_kind",
                    )
                },
                counts=Counter(),
                feature_histograms=defaultdict(Counter),
                policy_scope=row.get("policy_scope"),
                auxiliary_binding=row.get("auxiliary_binding"),
                scope_parent_machine_payload_sha256=row.get(
                    "scope_parent_machine_payload_sha256"
                ),
            )
        summary = self.scopes[sid]
        join = row["joins"]["0"]
        summary["counts"]["rows"] += 1
        summary["counts"]["join_" + join["grade"]] += 1
        summary["counts"]["identity_" + str(row.get("identity_grade"))] += 1
        if join["grade"] == "U":
            summary["counts"]["join_U_reason_" + str(join.get("reason"))] += 1
        if row["outcome"] == "U":
            summary["counts"]["outcome_U_reason_" + str(row.get("outcome_reason"))] += 1
        summary["counts"]["machine_" + str(row.get("machine_action"))] += 1
        summary["counts"]["auxiliary_" + str(row.get("auxiliary_verdict"))] += 1
        summary["counts"]["outcome_" + row["outcome"]] += 1
        summary["counts"]["state_" + join.get("state", "UNKNOWN")] += 1
        summary["counts"][
            "cohort_" + str(row.get("auxiliary_verdict")) + "_" + row["outcome"]
        ] += 1
        summary["counts"][
            "state_" + join.get("state", "UNKNOWN") + "_" + row["outcome"]
        ] += 1
        for delay in DELAYS:
            summary["counts"][
                "delay_" + str(delay) + "_join_" + row["joins"][str(delay)]["grade"]
            ] += 1
        if join["grade"] in {"A", "B"} and row.get("identity_grade") == "canonical":
            for key, value in dict(
                row.get("features", {}), index_change_pct=join.get("index_change_pct")
            ).items():
                value = number(value)
                if key in (*FEATURES, "index_change_pct") and value is not None:
                    summary["feature_histograms"][key][str(value)] += 1
        candidates = (
            self.candidates.get("scopes", {}).get(sid, {}).get("candidates", [])
        )
        if not candidates or row.get("auxiliary_verdict") != "PASS":
            return
        decisions = {
            c["candidate_id"]: {
                str(delay): selection(row, c, row["joins"][str(delay)])
                for delay in DELAYS
            }
            for c in candidates
        }
        if any(v is None for d in decisions.values() for v in d.values()):
            summary["counts"]["candidate_common_range_gap"] += 1
            return
        summary["counts"]["candidate_common_range"] += 1
        for c in candidates:
            selected = decisions[c["candidate_id"]]["0"]
            self.historical_pairs[sid][c["candidate_id"]][
                "selected" if selected else "excluded"
            ][row["outcome"]] += 1
        if row["source_date"] <= self.candidates.get("scopes", {}).get(sid, {}).get(
            "fixed_after_source_date", "9999"
        ):
            return
        summary["counts"]["prospective_common_range"] += 1
        for c in candidates:
            for delay in DELAYS:
                selected = decisions[c["candidate_id"]][str(delay)]
                cluster = (
                    row["source_date"],
                    row["joins"][str(delay)].get("episode_id"),
                )
                target = self.pairs[sid][c["candidate_id"]][str(delay)][cluster]
                target["selected" if selected else "excluded"][row["outcome"]] += 1

    def diagnostics(self):
        result = {}
        for sid, summary in self.scopes.items():
            counts = summary["counts"]
            total = metric({k: counts.get("outcome_" + k, 0) for k in ("W", "F", "U")})
            passed = metric(
                {k: counts.get("cohort_PASS_" + k, 0) for k in ("W", "F", "U")}
            )
            result[sid] = dict(
                all_opportunities=total,
                auxiliary_PASS=passed,
                nonPASS_missed_W=sum(
                    counts.get("cohort_" + v + "_W", 0)
                    for v in (
                        "VETO",
                        "CAUTION",
                        "INSUFFICIENT",
                        "not_called",
                        "not_evaluated",
                    )
                ),
                PASS_remaining_F=counts.get("cohort_PASS_F", 0),
                states={
                    state: metric(
                        {
                            k: counts.get("state_" + state + "_" + k, 0)
                            for k in ("W", "F", "U")
                        }
                    )
                    for state in (
                        "WEAKNESS",
                        "RECOVERY",
                        "NEAR_WEAKNESS_BOUNDARY",
                        "UNKNOWN",
                    )
                },
            )
        return result

    def daily(self, source_date):
        self.finalize()
        return seal(
            dict(
                schema=VERSION + ":daily",
                source_date=source_date,
                scopes=self.scopes,
                diagnostic_metrics=self.diagnostics(),
                census=dict(self.census),
                conflicting_identities=sorted(self.conflicts),
                conflict_scopes=sorted(self.conflict_scopes),
                **AUTH,
            )
        )

    def comparison(self, generation):
        self.finalize()
        results = []
        for sid, declared in self.candidates.get("scopes", {}).items():
            local = []
            for c in declared["candidates"]:
                clusters = self.pairs[sid][c["candidate_id"]]["0"]
                totals = merge_pairs(clusters.values())
                baseline = Counter(totals["selected"]) + Counter(totals["excluded"])
                delta = pair_delta(totals)
                dates = sorted({day for day, _ in clusters})
                day_pairs = {
                    day: merge_pairs(p for (d, _), p in clusters.items() if d == day)
                    for day in dates
                }
                seed = digest([declared, sid, VERSION, "cluster1000"])
                rng = random.Random(seed)
                draws = []
                cluster_deltas = {pair_delta(p) for p in clusters.values()}
                if (
                    len(dates) > 1
                    and len(cluster_deltas - {None}) >= 2
                    and sum(totals["excluded"].values())
                ):
                    for _ in range(1000):
                        value = pair_delta(
                            merge_pairs(day_pairs[rng.choice(dates)] for _ in dates)
                        )
                        if value is not None:
                            draws.append(value)
                lower = sorted(draws)[49] if len(draws) == 1000 else None
                leave_dates = [
                    pair_delta(subtract_pairs(totals, p)) for p in day_pairs.values()
                ]
                leave_episodes = [
                    pair_delta(subtract_pairs(totals, p)) for p in clusters.values()
                ]
                delayed = {
                    str(d): pair_delta(
                        merge_pairs(self.pairs[sid][c["candidate_id"]][str(d)].values())
                    )
                    for d in (60, 180)
                }
                u_delta = pair_delta(totals, worst_u=True)
                changes = sum(totals["excluded"].values())
                cluster_deltas = {pair_delta(p) for p in clusters.values()}
                status = "hold_observation"
                if sid in self.conflict_scopes:
                    status = "source_gap"
                elif delta is None or lower is None or len(cluster_deltas - {None}) < 2:
                    status = "uncertainty_unresolved"
                elif any(v is None or v <= 0 for v in delayed.values()):
                    status = "join_sensitive"
                elif u_delta is None or u_delta <= 0:
                    status = "outcome_sensitive"
                elif (
                    changes
                    and delta > 0
                    and lower > 0
                    and leave_dates
                    and leave_episodes
                    and all(
                        v is not None and v > 0 for v in leave_dates + leave_episodes
                    )
                ):
                    status = "eligible_advisory"
                local.append(
                    dict(
                        scope_key=sid,
                        scope=declared["scope"],
                        candidate_id=c["candidate_id"],
                        definition=c["definition"],
                        status=status,
                        baseline=metric(baseline),
                        prospective_after_source_date=declared[
                            "fixed_after_source_date"
                        ],
                        full_cumulative_descriptive_delta=pair_delta(
                            self.historical_pairs[sid][c["candidate_id"]]
                        ),
                        full_cumulative_baseline=metric(
                            Counter(
                                self.historical_pairs[sid][c["candidate_id"]][
                                    "selected"
                                ]
                            )
                            + Counter(
                                self.historical_pairs[sid][c["candidate_id"]][
                                    "excluded"
                                ]
                            )
                        ),
                        full_cumulative_candidate=metric(
                            self.historical_pairs[sid][c["candidate_id"]]["selected"]
                        ),
                        candidate=metric(totals["selected"]),
                        delta_raw_win_rate=delta,
                        excluded_opportunities=changes,
                        added_opportunities=0,
                        missed_W=totals["excluded"].get("W", 0),
                        removed_F=totals["excluded"].get("F", 0),
                        source_dates=dates,
                        episode_count=len(clusters),
                        bootstrap_iterations=1000,
                        bootstrap_valid_iterations=len(draws),
                        bootstrap_seed=seed,
                        empirical_lower_5pct_delta=lower,
                        statistical_95pct_guarantee=False,
                        delayed_common_range_delta=delayed,
                        worst_outcome_U_delta=u_delta,
                        leave_date_delta=leave_dates,
                        leave_episode_delta=leave_episodes,
                        join_counts=dict(self.scopes.get(sid, {}).get("counts", {})),
                        comparison_complete=True,
                        generation=generation,
                        **AUTH,
                    )
                )
            eligible = [r for r in local if r["status"] == "eligible_advisory"]
            winner = max(
                eligible,
                key=lambda r: (r["delta_raw_win_rate"], r["candidate_id"]),
                default=None,
            )
            for r in local:
                r["scope_winner"] = bool(
                    winner and r["candidate_id"] == winner["candidate_id"]
                )
            results += local
        return seal(
            dict(
                schema=VERSION + ":comparison",
                generation=generation,
                census=dict(self.census),
                scope_observations=self.scopes,
                diagnostic_metrics=self.diagnostics(),
                candidate_manifest_sha256=self.candidates.get(
                    "artifact_content_sha256"
                ),
                comparisons=results,
                candidate_count=len(results),
                **AUTH,
            )
        )
