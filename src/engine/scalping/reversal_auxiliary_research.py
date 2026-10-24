"""Explicit operator-funded auxiliary research in the shared comparison store.

Owns research configuration and a single durable allowance, not live policy or
orders. Experiments share request objects but never the postclose latest pointer.
"""

from __future__ import annotations

import re
from pathlib import Path
from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_registry as G

SCHEMA = "main_auxiliary_research_v1"
RESEARCH_ID = "aux_prompt_research_20261008_01"
AUTHORITY = "USER_APPROVED_ADDITIONAL_200_RESEARCH_CALLS_20261008"
LIMIT = 200
TOPUP_LIMIT = 400
TOPUP_AUTHORITY = "USER_APPROVED_ADDITIONAL_200_TOTAL_400_RESEARCH_CALLS_20261008"
CONTINUATION_LIMIT = 600
CONTINUATION_AUTHORITY = "USER_APPROVED_COMPLETE_RESEARCH_TOTAL_600_CALLS_20261008"
FOLLOWUP_LIMIT = 800
FOLLOWUP_AUTHORITY = "USER_APPROVED_COMPLETE_RESEARCH_TOTAL_800_CALLS_20261008"
DISCRIMINATIVE_LIMIT = 1400
DISCRIMINATIVE_AUTHORITY = (
    "USER_APPROVED_ADDITIONAL_600_TOTAL_1400_RESEARCH_CALLS_20261017"
)
NEXT_STUDY_LIMIT = 2000
NEXT_STUDY_AUTHORITY = "USER_APPROVED_ADDITIONAL_600_TOTAL_2000_RESEARCH_CALLS_20261017"
DIRECT_LIMIT = 2047
DIRECT_AUTHORITY = (
    "USER_APPROVED_ADDITIONAL_47_TOTAL_2047_DIRECT_RESEARCH_CALLS_20261017"
)
SOURCE_SCOPE_AUTHORITY = "USER_APPROVED_CUMULATIVE_AUXILIARY_RESEARCH_SCOPE_20261016"
NOT_SENT_RECOVERY_AUTHORITY = "RESEARCH_ONLY_VERIFIED_CREDENTIALS_NOT_SENT_RECOVERY"


def root(data_root):
    return Path(data_root) / "report/reversal_auxiliary_tuning/research" / RESEARCH_ID


def directory(data_root, experiment):
    if not isinstance(experiment, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9_-]{0,79}", experiment
    ):
        raise ValueError("auxiliary_research_experiment_invalid")
    return root(data_root) / "experiments" / experiment


def read(path):
    import json

    v = json.loads(Path(path).read_text())
    if v.get("artifact_content_sha256") != P.seal(v)["artifact_content_sha256"]:
        raise ValueError("auxiliary_research_artifact_changed")
    return v


def grant(data_root):
    v = read(root(data_root) / "allowance.json")
    if (
        v.get("schema") != SCHEMA
        or v.get("research_id") != RESEARCH_ID
        or v.get("authority") != AUTHORITY
        or v.get("call_limit") != LIMIT
        or v.get("budget_key") != "research_auxiliary:" + RESEARCH_ID
        or not v.get("source_dates")
        or not v.get("approval_reference")
    ):
        raise ValueError("auxiliary_research_allowance_invalid")
    return v


def budget(data_root):
    base = grant(data_root)
    path = root(data_root) / "allowance-topup-400.json"
    if not path.exists():
        if any(
            (root(data_root) / f"allowance-topup-{n}.json").exists()
            for n in (600, 800, 1400, 2000, 2047)
        ):
            raise ValueError("auxiliary_research_previous_funding_required")
        return base
    topup = read(path)
    if (
        topup.get("research_id") != RESEARCH_ID
        or topup.get("authority") != TOPUP_AUTHORITY
        or topup.get("base_allowance_sha256") != base["artifact_content_sha256"]
        or topup.get("from_limit") != LIMIT
        or topup.get("call_limit") != TOPUP_LIMIT
        or topup.get("budget_key") != base["budget_key"]
        or not topup.get("approval_reference")
    ):
        raise ValueError("auxiliary_research_topup_invalid")
    result = dict(
        base, call_limit=TOPUP_LIMIT, funding_sha256=topup["artifact_content_sha256"]
    )
    continuation = root(data_root) / "allowance-topup-600.json"
    if continuation.exists():
        value = read(continuation)
        if (
            value.get("schema") != SCHEMA
            or value.get("research_id") != RESEARCH_ID
            or value.get("authority") != CONTINUATION_AUTHORITY
            or value.get("previous_funding_sha256") != topup["artifact_content_sha256"]
            or value.get("from_limit") != TOPUP_LIMIT
            or value.get("call_limit") != CONTINUATION_LIMIT
            or value.get("budget_key") != base["budget_key"]
            or not value.get("approval_reference")
        ):
            raise ValueError("auxiliary_research_continuation_invalid")
        result.update(
            call_limit=CONTINUATION_LIMIT,
            funding_sha256=value["artifact_content_sha256"],
        )
    followup = root(data_root) / "allowance-topup-800.json"
    if followup.exists():
        value = read(followup)
        if (
            result["call_limit"] != CONTINUATION_LIMIT
            or value.get("schema") != SCHEMA
            or value.get("research_id") != RESEARCH_ID
            or value.get("authority") != FOLLOWUP_AUTHORITY
            or value.get("previous_funding_sha256") != result["funding_sha256"]
            or value.get("from_limit") != CONTINUATION_LIMIT
            or value.get("call_limit") != FOLLOWUP_LIMIT
            or value.get("budget_key") != base["budget_key"]
            or not value.get("approval_reference")
        ):
            raise ValueError("auxiliary_research_followup_invalid")
        result.update(
            call_limit=FOLLOWUP_LIMIT, funding_sha256=value["artifact_content_sha256"]
        )
    discriminative = root(data_root) / "allowance-topup-1400.json"
    if discriminative.exists():
        value = read(discriminative)
        if (
            result["call_limit"] != FOLLOWUP_LIMIT
            or value.get("schema") != SCHEMA
            or value.get("research_id") != RESEARCH_ID
            or value.get("authority") != DISCRIMINATIVE_AUTHORITY
            or value.get("previous_funding_sha256") != result["funding_sha256"]
            or value.get("from_limit") != FOLLOWUP_LIMIT
            or value.get("call_limit") != DISCRIMINATIVE_LIMIT
            or value.get("budget_key") != base["budget_key"]
            or not isinstance(value.get("approval_reference"), str)
            or not value["approval_reference"].strip()
            or any(value.get(key) != expected for key, expected in P.AUTH.items())
        ):
            raise ValueError("auxiliary_research_discriminative_funding_invalid")
        result.update(
            call_limit=DISCRIMINATIVE_LIMIT,
            funding_sha256=value["artifact_content_sha256"],
        )
    next_study = root(data_root) / "allowance-topup-2000.json"
    if next_study.exists():
        value = read(next_study)
        if (
            result["call_limit"] != DISCRIMINATIVE_LIMIT
            or value.get("schema") != SCHEMA
            or value.get("research_id") != RESEARCH_ID
            or value.get("authority") != NEXT_STUDY_AUTHORITY
            or value.get("previous_funding_sha256") != result["funding_sha256"]
            or value.get("from_limit") != DISCRIMINATIVE_LIMIT
            or value.get("call_limit") != NEXT_STUDY_LIMIT
            or value.get("budget_key") != base["budget_key"]
            or not isinstance(value.get("approval_reference"), str)
            or not value["approval_reference"].strip()
            or any(value.get(key) != expected for key, expected in P.AUTH.items())
        ):
            raise ValueError("auxiliary_research_next_study_funding_invalid")
        result.update(
            call_limit=NEXT_STUDY_LIMIT, funding_sha256=value["artifact_content_sha256"]
        )
    direct = root(data_root) / "allowance-topup-2047.json"
    if direct.exists():
        value = read(direct)
        if (
            result["call_limit"] != NEXT_STUDY_LIMIT
            or value.get("schema") != SCHEMA
            or value.get("research_id") != RESEARCH_ID
            or value.get("authority") != DIRECT_AUTHORITY
            or value.get("previous_funding_sha256") != result["funding_sha256"]
            or value.get("from_limit") != NEXT_STUDY_LIMIT
            or value.get("call_limit") != DIRECT_LIMIT
            or value.get("budget_key") != base["budget_key"]
            or not isinstance(value.get("approval_reference"), str)
            or not value["approval_reference"].strip()
            or any(value.get(key) != expected for key, expected in P.AUTH.items())
        ):
            raise ValueError("auxiliary_research_direct_funding_invalid")
        result.update(
            call_limit=DIRECT_LIMIT, funding_sha256=value["artifact_content_sha256"]
        )
    return result


def authorize_direct_comparison(data_root, *, confirm, approval_reference):
    """Append 47 attempts to the existing budget; never reset prior charges."""
    if (
        confirm != DIRECT_AUTHORITY
        or not isinstance(approval_reference, str)
        or not approval_reference.strip()
    ):
        raise ValueError("auxiliary_research_direct_authority_required")
    with S.Store(data_root):
        previous = budget(data_root)
        if previous["call_limit"] not in {NEXT_STUDY_LIMIT, DIRECT_LIMIT}:
            raise ValueError("auxiliary_research_previous_funding_required")
        funding = read(root(data_root) / "allowance-topup-2000.json")
        value = P.seal(
            dict(
                schema=SCHEMA,
                research_id=RESEARCH_ID,
                authority=DIRECT_AUTHORITY,
                previous_funding_sha256=funding["artifact_content_sha256"],
                from_limit=NEXT_STUDY_LIMIT,
                call_limit=DIRECT_LIMIT,
                budget_key=previous["budget_key"],
                approval_reference=approval_reference,
                **P.AUTH,
            )
        )
        immutable(root(data_root) / "allowance-topup-2047.json", value)
    return budget(data_root)


def authorize_next_study(data_root, *, confirm, approval_reference):
    """Append 600 attempts; preserve previous spending and unused allowance."""
    if (
        confirm != NEXT_STUDY_AUTHORITY
        or not isinstance(approval_reference, str)
        or not approval_reference.strip()
    ):
        raise ValueError("auxiliary_research_next_study_authority_required")
    with S.Store(data_root):
        previous = budget(data_root)
        if previous["call_limit"] not in {DISCRIMINATIVE_LIMIT, NEXT_STUDY_LIMIT}:
            raise ValueError("auxiliary_research_previous_funding_required")
        funding = read(root(data_root) / "allowance-topup-1400.json")
        value = P.seal(
            dict(
                schema=SCHEMA,
                research_id=RESEARCH_ID,
                authority=NEXT_STUDY_AUTHORITY,
                previous_funding_sha256=funding["artifact_content_sha256"],
                from_limit=DISCRIMINATIVE_LIMIT,
                call_limit=NEXT_STUDY_LIMIT,
                budget_key=previous["budget_key"],
                approval_reference=approval_reference,
                **P.AUTH,
            )
        )
        immutable(root(data_root) / "allowance-topup-2000.json", value)
    return budget(data_root)


def authorize_discriminative(data_root, *, confirm, approval_reference):
    """Append the approved 600 attempts to the existing 800-attempt budget."""
    if (
        confirm != DISCRIMINATIVE_AUTHORITY
        or not isinstance(approval_reference, str)
        or not approval_reference.strip()
    ):
        raise ValueError("auxiliary_research_discriminative_authority_required")
    with S.Store(data_root):
        previous = budget(data_root)
        if previous["call_limit"] not in {FOLLOWUP_LIMIT, DISCRIMINATIVE_LIMIT}:
            raise ValueError("auxiliary_research_previous_funding_required")
        funding = read(root(data_root) / "allowance-topup-800.json")
        value = P.seal(
            dict(
                schema=SCHEMA,
                research_id=RESEARCH_ID,
                authority=DISCRIMINATIVE_AUTHORITY,
                previous_funding_sha256=funding["artifact_content_sha256"],
                from_limit=FOLLOWUP_LIMIT,
                call_limit=DISCRIMINATIVE_LIMIT,
                budget_key=previous["budget_key"],
                approval_reference=approval_reference,
                **P.AUTH,
            )
        )
        immutable(root(data_root) / "allowance-topup-1400.json", value)
    return budget(data_root)


def not_sent_executor_contract():
    """Identify the sole recoverable executor guard, before client creation."""
    import ast
    from src.engine.scalping import ai_decision_quality as executor

    path = Path(executor.__file__)
    tree = ast.parse(path.read_text())
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "execute_openai_prompt_v2_candidate"
    )
    guards = [
        node
        for node in function.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.UnaryOp)
        and isinstance(node.test.op, ast.Not)
        and isinstance(node.test.operand, ast.Name)
        and node.test.operand.id == "keys"
        and len(node.body) == 1
        and isinstance(node.body[0], ast.Raise)
        and isinstance(node.body[0].exc, ast.Call)
        and isinstance(node.body[0].exc.func, ast.Name)
        and node.body[0].exc.func.id == "RuntimeError"
        and len(node.body[0].exc.args) == 1
        and isinstance(node.body[0].exc.args[0], ast.Constant)
        and node.body[0].exc.args[0].value == "openai_api_key_unavailable"
    ]
    clients = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "OpenAI"
    ]
    sends = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "create"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "responses"
    ]
    if (
        len(guards) != 1
        or len(clients) != 1
        or len(sends) != 1
        or not guards[0].body[0].lineno < clients[0].lineno < sends[0].lineno
    ):
        raise ValueError("auxiliary_research_not_sent_executor_contract_invalid")
    return dict(
        executor_source_sha256=P.file_hash(path),
        executor_raise_line=guards[0].body[0].lineno,
    )


def requeue_not_sent(data_root, campaign_path, *, proof):
    """Requeue only proven missing-key failures; retain every attempt and charge.

    No generic uncertain-attempt reset is supported. Reconciliation precedes
    inspection so delayed responses and journal records cannot be bypassed.
    """
    from src.engine.scalping import reversal_auxiliary_tuning as T

    contract = not_sent_executor_contract()
    if (
        not isinstance(proof, dict)
        or proof.get("authority") != NOT_SENT_RECOVERY_AUTHORITY
        or not isinstance(proof.get("approval_reference"), str)
        or not proof["approval_reference"].strip()
        or any(proof.get(key) != value for key, value in contract.items())
        or not isinstance(proof.get("attempt_ids"), list)
        or not proof["attempt_ids"]
        or any(
            not isinstance(ident, str) or not re.fullmatch("[0-9a-f]{32}", ident)
            for ident in proof["attempt_ids"]
        )
        or len(set(proof["attempt_ids"])) != len(proof["attempt_ids"])
    ):
        raise ValueError("auxiliary_research_not_sent_proof_invalid")
    campaign = T.read(campaign_path)
    campaign, _, _ = T.load_campaign(data_root, campaign["source_date"], campaign_path)
    if not campaign.get("research"):
        raise ValueError("auxiliary_research_not_sent_research_only")
    allowance = validate_campaign(data_root, campaign)
    recovery_rows = []
    with S.Store(data_root) as store:
        store.reconcile()
        if store.activation().get("writer_enabled") is not True:
            raise ValueError("auxiliary_research_not_sent_writer_disabled")
        T.validate_campaign(store, campaign)
        before = store.budget_used(allowance["budget_key"])
        request_ids = sorted(
            {rid for pair in campaign["pairs"] for rid in pair["requests"].values()}
        )
        for rid in request_ids:
            state, result_obj = store.db.execute(
                "SELECT state,result_obj FROM requests WHERE id=?", (rid,)
            ).fetchone()
            if state != "reserved":
                continue
            if result_obj is not None:
                raise ValueError("auxiliary_research_not_sent_request_has_result")
            attempts = store.db.execute(
                "SELECT attempt,state,result_obj,source FROM attempts WHERE request_id=? ORDER BY attempt",
                (rid,),
            ).fetchall()
            if not attempts:
                raise ValueError("auxiliary_research_not_sent_attempt_unproven")
            verified = []
            for ident, attempt_state, obj, source in attempts:
                if (
                    ident not in proof["attempt_ids"]
                    or attempt_state != "reserved"
                    or obj is None
                    or source != "provider"
                ):
                    raise ValueError("auxiliary_research_not_sent_attempt_unproven")
                keys = {
                    r[0]
                    for r in store.db.execute(
                        "SELECT budget_key FROM attempt_budgets WHERE attempt=?",
                        (ident,),
                    )
                }
                if keys != {allowance["budget_key"]}:
                    raise ValueError("auxiliary_research_not_sent_foreign_budget")
                response_objs = {
                    r[0]
                    for r in store.db.execute(
                        "SELECT result_obj FROM attempt_responses WHERE attempt=?",
                        (ident,),
                    )
                }
                if obj not in response_objs:
                    raise ValueError("auxiliary_research_not_sent_response_unproven")
                hashes = []
                for response_obj in sorted(response_objs):
                    record = store.get(response_obj)
                    frames = record.get("error_frames")
                    if (
                        set(record)
                        != {
                            "error_type",
                            "error_frames",
                            "validation_errors",
                            "transport_invoked",
                        }
                        or record["error_type"] != "RuntimeError"
                        or record["transport_invoked"] is not True
                        or record["validation_errors"] != ["provider_attempt_uncertain"]
                        or not isinstance(frames, list)
                        or len(frames) != 2
                        or any(not isinstance(frame, dict) for frame in frames)
                        or frames[0].get("file") != Path(T.__file__).name
                        or frames[0].get("function") != "calls"
                        or type(frames[0].get("line")) is not int
                        or frames[0]["line"] <= 0
                        or frames[1]
                        != dict(
                            file="ai_decision_quality.py",
                            function="execute_openai_prompt_v2_candidate",
                            line=contract["executor_raise_line"],
                        )
                    ):
                        raise ValueError(
                            "auxiliary_research_not_sent_response_unproven"
                        )
                    hashes.append(P.digest(record))
                verified.append(dict(attempt_id=ident, response_sha256=hashes))
            recovery_rows.append(
                dict(
                    request_id=rid,
                    request_sha256=P.digest(store.request(rid)),
                    attempts=verified,
                )
            )
        if not recovery_rows:
            return P.seal(
                dict(
                    status="no_reserved_requests",
                    campaign_sha256=campaign["artifact_content_sha256"],
                    requeued_requests=0,
                    budget_used_unchanged=before,
                    **P.AUTH,
                )
            )
        receipt = P.seal(
            dict(
                schema="auxiliary_research_not_sent_recovery_v1",
                authority=NOT_SENT_RECOVERY_AUTHORITY,
                campaign_sha256=campaign["artifact_content_sha256"],
                research_id=RESEARCH_ID,
                proof=proof,
                code_sha256=P.file_hash(__file__),
                reason="missing_credentials_guard_before_openai_client_and_send",
                requests=recovery_rows,
                budget_key=allowance["budget_key"],
                budget_used_unchanged=before,
                requeued_requests=len(recovery_rows),
                attempts_preserved=True,
                **P.AUTH,
            )
        )
        for row in recovery_rows:
            updated = store.db.execute(
                "UPDATE requests SET state='planned' WHERE id=? AND state='reserved' AND result_obj IS NULL",
                (row["request_id"],),
            )
            if updated.rowcount != 1:
                raise ValueError("auxiliary_research_not_sent_request_changed")
        if store.budget_used(allowance["budget_key"]) != before:
            raise ValueError("auxiliary_research_not_sent_budget_changed")
        # The complete receipt and state changes commit together. A filesystem
        # publication failure cannot erase the durable recovery evidence.
        store.checkpoint(
            "auxiliary-not-sent-recovery:" + receipt["artifact_content_sha256"], receipt
        )
    immutable(
        root(data_root)
        / "not-sent-recoveries"
        / (receipt["artifact_content_sha256"] + ".json"),
        receipt,
    )
    return receipt


def authorize_followup(data_root, *, confirm, approval_reference):
    if confirm != FOLLOWUP_AUTHORITY or not approval_reference:
        raise ValueError("auxiliary_research_followup_authority_required")
    with S.Store(data_root):
        previous = budget(data_root)
        if previous["call_limit"] not in {CONTINUATION_LIMIT, FOLLOWUP_LIMIT}:
            raise ValueError("auxiliary_research_previous_funding_required")
        topup = read(root(data_root) / "allowance-topup-600.json")
        value = P.seal(
            dict(
                schema=SCHEMA,
                research_id=RESEARCH_ID,
                authority=FOLLOWUP_AUTHORITY,
                previous_funding_sha256=topup["artifact_content_sha256"],
                from_limit=CONTINUATION_LIMIT,
                call_limit=FOLLOWUP_LIMIT,
                budget_key=previous["budget_key"],
                approval_reference=approval_reference,
                **P.AUTH,
            )
        )
        immutable(root(data_root) / "allowance-topup-800.json", value)
    return budget(data_root)


def authorize_continuation(data_root, *, confirm, approval_reference):
    if confirm != CONTINUATION_AUTHORITY or not approval_reference:
        raise ValueError("auxiliary_research_continuation_authority_required")
    with S.Store(data_root):
        previous = budget(data_root)
        if previous["call_limit"] not in {TOPUP_LIMIT, CONTINUATION_LIMIT}:
            raise ValueError("auxiliary_research_previous_funding_required")
        topup = read(root(data_root) / "allowance-topup-400.json")
        value = P.seal(
            dict(
                schema=SCHEMA,
                research_id=RESEARCH_ID,
                authority=CONTINUATION_AUTHORITY,
                previous_funding_sha256=topup["artifact_content_sha256"],
                from_limit=TOPUP_LIMIT,
                call_limit=CONTINUATION_LIMIT,
                budget_key=previous["budget_key"],
                approval_reference=approval_reference,
                **P.AUTH,
            )
        )
        immutable(root(data_root) / "allowance-topup-600.json", value)
    return budget(data_root)


def authorize_topup(data_root, *, confirm, approval_reference):
    if confirm != TOPUP_AUTHORITY or not approval_reference:
        raise ValueError("auxiliary_research_topup_authority_required")
    base = grant(data_root)
    value = P.seal(
        dict(
            schema=SCHEMA,
            research_id=RESEARCH_ID,
            authority=TOPUP_AUTHORITY,
            base_allowance_sha256=base["artifact_content_sha256"],
            from_limit=LIMIT,
            call_limit=TOPUP_LIMIT,
            budget_key=base["budget_key"],
            approval_reference=approval_reference,
            **P.AUTH,
        )
    )
    with S.Store(data_root):
        immutable(root(data_root) / "allowance-topup-400.json", value)
    return budget(data_root)


def current_bindings(data_root, parent):
    """Use an actual reader capture when research code has a different hash.

    This is an offline baseline, never a substitute for the publisher's live
    parent and reader validation. The immutable release validates inheritance
    before producing the capture.
    """
    from src.engine.scalping import reversal_auxiliary_intraday as I

    path = root(data_root) / "current-bindings" / (parent["bundle_sha256"] + ".json")
    if not path.exists():
        return I.effective_bindings(data_root, parent)
    value = read(path)
    if (
        value.get("parent_bundle_sha256") != parent["bundle_sha256"]
        or value.get("family_sha256") != parent["continuous_reversal"]["family_sha256"]
        or value.get("reader_validated") is not True
        or not value.get("source_receipts")
    ):
        raise ValueError("auxiliary_research_binding_capture_invalid")
    for receipt in value["source_receipts"]:
        if P.file_hash(receipt["path"]) != receipt["sha256"]:
            raise ValueError("auxiliary_research_binding_capture_source_changed")
    from src.engine.scalping import continuous_reversal_policy_v5 as V

    family = parent["continuous_reversal"]
    expected = {
        V.scope_id(key, route)
        for key, route in V.scopes()
        if family["machine_cells"][key]["routes"][route]["backend"]
        in {"union_v5", "union_v6"}
    }
    if set(value.get("bindings", {})) != expected:
        raise ValueError("auxiliary_research_binding_capture_scope_changed")
    for sid, ident in value["bindings"].items():
        key, route = sid.rsplit("|", 1)
        if (
            G.load(data_root, ident)["input_version"]
            != parent["continuous_reversal"]["auxiliary_cells"][key]["routes"][route][
                "payload"
            ]["binding"]["input_version"]
        ):
            raise ValueError("auxiliary_research_binding_capture_version_changed")
    return value["bindings"]


def prior_attempt_inventory(data_root, keys, *, before_epoch, exclude_generations=()):
    """Read all retained memberships and both response landing locations.

    Superseded/non-research generations and imported legacy attempts matter.
    Uncertain attempts conservatively count as prior exposure. This function
    only reports provenance; it does not reset, refund, retry or publish.
    """
    import math
    from collections import defaultdict

    wanted = sorted(set(keys))
    if (
        not wanted
        or any(not isinstance(k, str) or not k for k in wanted)
        or type(before_epoch) not in (int, float)
        or not math.isfinite(before_epoch)
        or before_epoch <= 0
    ):
        raise ValueError("auxiliary_prior_inventory_arguments_invalid")
    excluded = set(exclude_generations)
    categories = defaultdict(set)
    proofs = []
    descriptors = {}
    objects = {}
    with S.Store(data_root, readonly=True) as store:
        for start in range(0, len(wanted), 400):
            chunk = wanted[start : start + 400]
            query = (
                """SELECT DISTINCT gp.generation,g.descriptor_obj,m.request_id,o.value,
                at.attempt,at.created,at.state,at.source,at.result_obj,ar.result_obj
                FROM members m JOIN strings o ON o.id=m.opportunity
                JOIN partition_members pm ON pm.member_id=m.id
                JOIN generation_parts gp ON gp.partition_id=pm.partition_id
                JOIN generations g ON g.generation=gp.generation
                JOIN attempts at ON at.request_id=m.request_id
                LEFT JOIN attempt_responses ar ON ar.attempt=at.attempt
                WHERE o.value IN ("""
                + ",".join("?" for _ in chunk)
                + ") AND at.created<?"
            )
            for (
                gen,
                desc,
                rid,
                key,
                attempt,
                created,
                state,
                source,
                aobj,
                robj,
            ) in store.db.execute(query, (*chunk, before_epoch)):
                if gen in excluded:
                    continue
                observed = []
                for obj in sorted({v for v in (aobj, robj) if v is not None}):
                    if obj not in objects:
                        record = store.get(obj)
                        prov = record.get("result", {}).get("provider_provenance") or {}
                        objects[obj] = dict(
                            object_id=obj,
                            record_sha256=P.digest(record),
                            provider=prov.get("provider"),
                            response_id=prov.get("response_id"),
                            provider_none=prov.get("provider_none"),
                        )
                    observed.append(objects[obj])
                actual = any(
                    v["response_id"] and v["provider_none"] is not True
                    for v in observed
                )
                category = "actual_response" if actual else "uncertain_prior_attempt"
                categories[key].add(category)
                if gen is not None and gen not in descriptors:
                    value = store.get(desc)
                    descriptors[gen] = dict(
                        descriptor_obj=desc,
                        descriptor_sha256=P.digest(value),
                        schema=value.get("schema"),
                        source_date=value.get("source_date"),
                    )
                proofs.append(
                    dict(
                        source_key=key,
                        generation=gen,
                        request_id=rid,
                        attempt=attempt,
                        created_epoch=created,
                        state=state,
                        source=source,
                        attempt_result_obj=aobj,
                        attempt_response_obj=robj,
                        observed=observed,
                        classification=category,
                    )
                )
    # No inferred "not sent" exception exists here. Even a local historical
    # error stays conservatively excluded unless a separate exact repair owns it.
    return P.seal(
        dict(
            schema="auxiliary_prior_attempt_inventory_v1",
            before_epoch=before_epoch,
            requested_keys_sha256=P.digest(wanted),
            requested_key_count=len(wanted),
            excluded_generations=sorted(excluded),
            blocked_source_keys=sorted(categories),
            classifications={k: sorted(v) for k, v in sorted(categories.items())},
            generations=descriptors,
            proofs=proofs,
            unknown_counts_as_exposed=True,
            **P.AUTH,
        )
    )


def immutable(path, value):
    if Path(path).exists():
        if read(path) != value:
            raise ValueError("auxiliary_research_immutable_conflict")
    else:
        S.atomic_json(path, value)


def authorize_source_scope(
    data_root, *, source_dates, approval_reference, as_of, confirm
):
    """Extend source scope on explicit instruction, without adding call funds."""
    from datetime import date, datetime
    from zoneinfo import ZoneInfo

    dates = sorted(set(source_dates))
    cutoff = date.fromisoformat(as_of)
    if (
        cutoff > datetime.now(ZoneInfo("Asia/Seoul")).date()
        or confirm != SOURCE_SCOPE_AUTHORITY
        or not approval_reference
        or not dates
        or any(
            date.fromisoformat(day).isoformat() != day
            or not "2026-09-29" <= day <= cutoff.isoformat()
            for day in dates
        )
    ):
        raise ValueError("auxiliary_research_source_scope_invalid")
    base = grant(data_root)
    value = P.seal(
        dict(
            schema="auxiliary_research_source_scope_v1",
            research_id=RESEARCH_ID,
            allowance_sha256=base["artifact_content_sha256"],
            authority=SOURCE_SCOPE_AUTHORITY,
            budget_key=base["budget_key"],
            source_dates=dates,
            as_of=as_of,
            approval_reference=approval_reference,
            call_limit_unchanged=True,
            **P.AUTH,
        )
    )
    with S.Store(data_root):
        immutable(
            root(data_root)
            / "source-scopes"
            / (value["artifact_content_sha256"] + ".json"),
            value,
        )
    return value


def source_scope(data_root, ident):
    if not isinstance(ident, str) or not re.fullmatch(r"[0-9a-f]{64}", ident):
        raise ValueError("auxiliary_research_source_scope_invalid")
    value = read(root(data_root) / "source-scopes" / (ident + ".json"))
    base = grant(data_root)
    dates = value.get("source_dates")
    from datetime import date, datetime
    from zoneinfo import ZoneInfo

    try:
        cutoff = date.fromisoformat(value["as_of"]).isoformat()
        valid_dates = (
            isinstance(dates, list)
            and bool(dates)
            and cutoff <= datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
            and dates == sorted(set(dates))
            and all(
                date.fromisoformat(day).isoformat() == day
                and "2026-09-29" <= day <= cutoff
                for day in dates
            )
        )
    except (KeyError, TypeError, ValueError):
        valid_dates = False
    if (
        value.get("schema") != "auxiliary_research_source_scope_v1"
        or value.get("authority") != SOURCE_SCOPE_AUTHORITY
        or value.get("artifact_content_sha256") != ident
        or value.get("research_id") != RESEARCH_ID
        or value.get("allowance_sha256") != base["artifact_content_sha256"]
        or value.get("budget_key") != base["budget_key"]
        or value.get("call_limit_unchanged") is not True
        or not value.get("approval_reference")
        or not valid_dates
        or any(value.get(key) != expected for key, expected in P.AUTH.items())
    ):
        raise ValueError("auxiliary_research_source_scope_invalid")
    return value


def authorize(data_root, *, confirm, source_dates, approval_reference):
    from datetime import date

    if confirm != AUTHORITY or not approval_reference or not source_dates:
        raise ValueError("auxiliary_research_authority_required")
    dates = sorted(set(source_dates))
    for day in dates:
        if (
            date.fromisoformat(day).isoformat() != day
            or not "2026-06-05" <= day <= "2026-10-08"
        ):
            raise ValueError("auxiliary_research_source_date_invalid")
    v = P.seal(
        dict(
            schema=SCHEMA,
            research_id=RESEARCH_ID,
            authority=AUTHORITY,
            call_limit=LIMIT,
            budget_key="research_auxiliary:" + RESEARCH_ID,
            source_dates=dates,
            approval_reference=approval_reference,
            **P.AUTH,
        )
    )
    with S.Store(data_root):
        immutable(root(data_root) / "allowance.json", v)
    return v


def configure(
    data_root,
    *,
    experiment,
    candidate,
    scopes,
    seed,
    max_pairs,
    purpose="evaluation",
    include_keys=(),
    native_current=False,
    resolved_only=False,
    native_output_tokens_override=None,
    compact_wire=False,
    compact_candidate_only=False,
    source_scope_sha256=None,
    causal_prefix=False,
    causal_candidate_only=False,
    risk_role_mode=None,
    risk_role_roles=None,
):
    from src.engine.scalping import reversal_auxiliary_tuning as T
    from src.engine.scalping import continuous_reversal_policy_v5 as V

    allowance = grant(data_root)
    valid = {V.scope_id(k, r) for k, r in V.scopes()}
    if (
        purpose not in {"development", "evaluation"}
        or not scopes
        or not set(scopes) <= valid
        or type(max_pairs) is not int
        or not 1 <= max_pairs <= 100
        or not isinstance(seed, str)
        or not seed
        or (include_keys and purpose != "development")
        or (compact_candidate_only and not compact_wire)
        or (
            compact_wire
            and (native_current or native_output_tokens_override is not None)
        )
        or (
            native_output_tokens_override is not None
            and (not native_current or native_output_tokens_override != 1024)
        )
    ):
        raise ValueError("auxiliary_research_config_invalid")
    G.load(data_root, candidate)
    cfg = dict(
        schema=T.SCHEMA,
        enabled=True,
        candidate_registry=candidate,
        scopes=sorted(set(scopes)),
        seed=seed,
        max_pairs=max_pairs,
    )
    if native_current:
        cfg["native_current_contract"] = native_contract()
    if native_output_tokens_override is not None:
        cfg["native_output_tokens_override"] = native_output_tokens_override
    if resolved_only:
        cfg["resolved_only"] = True
    if (
        type(causal_prefix) is not bool
        or type(causal_candidate_only) is not bool
        or (causal_candidate_only and not causal_prefix)
    ):
        raise ValueError("auxiliary_research_causal_prefix_config_invalid")
    if causal_prefix:
        from src.engine.scalping import reversal_auxiliary_causal_experiment as E

        # No native-current proof may accidentally make an input experiment
        # publishable through the existing registry-only publisher.
        if (
            native_current
            or G.load(data_root, candidate)["input_version"] != E.U.VERSION
        ):
            raise ValueError("auxiliary_research_causal_prefix_input_unsupported")
        cfg["causal_prefix_contract"] = E.contract()
        if causal_candidate_only:
            cfg["causal_prefix_roles"] = ["candidate"]
    if risk_role_mode is not None:
        from src.engine.scalping import reversal_auxiliary_risk_role_experiment as X

        if (
            native_current
            or causal_prefix
            or G.load(data_root, candidate)["input_version"] != X.U.VERSION
        ):
            raise ValueError("auxiliary_research_risk_role_input_unsupported")
        cfg["risk_role_contract"] = X.contract(risk_role_mode)
        if risk_role_roles is not None:
            if risk_role_roles not in (["candidate"], ["current", "candidate"]):
                raise ValueError("auxiliary_research_risk_role_roles_invalid")
            cfg["risk_role_roles"] = list(risk_role_roles)
    elif risk_role_roles is not None:
        raise ValueError("auxiliary_research_risk_role_contract_missing")
    if compact_wire:
        from src.engine.scalping import reversal_auxiliary_research_wire as W

        cfg["compact_wire_contract"] = W.contract()
        if compact_candidate_only:
            cfg["compact_candidate_only"] = True
    v = P.seal(
        dict(
            schema=SCHEMA,
            research_id=RESEARCH_ID,
            experiment=experiment,
            allowance_sha256=allowance["artifact_content_sha256"],
            purpose=purpose,
            include_keys=sorted(set(include_keys)),
            config=P.seal(cfg),
            **P.AUTH,
        )
    )
    if source_scope_sha256 is not None:
        source_scope(data_root, source_scope_sha256)
        v = P.seal(dict(v, source_scope_sha256=source_scope_sha256))
    with S.Store(data_root):
        immutable(directory(data_root, experiment) / "configuration.json", v)
    return v


def context(data_root, experiment):
    v = read(directory(data_root, experiment) / "configuration.json")
    a = budget(data_root)
    if (
        v.get("schema") != SCHEMA
        or v.get("research_id") != RESEARCH_ID
        or v.get("experiment") != experiment
        or v.get("allowance_sha256") != a["artifact_content_sha256"]
        or v.get("purpose") not in {"development", "evaluation"}
    ):
        raise ValueError("auxiliary_research_context_invalid")
    if v.get("source_scope_sha256"):
        source_scope(data_root, v["source_scope_sha256"])
    if v["config"].get("causal_prefix_contract"):
        from src.engine.scalping import reversal_auxiliary_causal_experiment as E

        if (
            v["config"]["causal_prefix_contract"] != E.contract()
            or v["config"].get("native_current_contract")
            or v["config"].get("causal_prefix_roles") not in (None, ["candidate"])
        ):
            raise ValueError("auxiliary_research_causal_prefix_contract_invalid")
    elif v["config"].get("causal_prefix_roles"):
        raise ValueError("auxiliary_research_causal_prefix_contract_missing")
    if "risk_role_contract" in v["config"]:
        from src.engine.scalping import reversal_auxiliary_risk_role_experiment as X

        contract = v["config"]["risk_role_contract"]
        if (
            not isinstance(contract, dict)
            or contract != X.contract(contract.get("mode"))
            or v["config"].get("native_current_contract")
            or v["config"].get("causal_prefix_contract")
        ):
            raise ValueError("auxiliary_research_risk_role_contract_invalid")
        if "risk_role_roles" in v["config"] and v["config"]["risk_role_roles"] not in (
            ["candidate"],
            ["current", "candidate"],
        ):
            raise ValueError("auxiliary_research_risk_role_roles_invalid")
    elif "risk_role_roles" in v["config"]:
        raise ValueError("auxiliary_research_risk_role_contract_missing")
    return v


def validate_campaign(data_root, campaign):
    ref = campaign["research"]
    v = context(data_root, ref["experiment"])
    a = budget(data_root)
    fields = ("research_id", "experiment", "purpose", "allowance_sha256")
    dates = a["source_dates"]
    if v.get("source_scope_sha256"):
        fields += ("source_scope_sha256",)
        dates = source_scope(data_root, v["source_scope_sha256"])["source_dates"]
    if (
        ref != {k: v[k] for k in fields}
        or campaign["config_sha256"] != v["config"]["artifact_content_sha256"]
        or campaign["call_limit"]
        not in {
            LIMIT,
            TOPUP_LIMIT,
            CONTINUATION_LIMIT,
            FOLLOWUP_LIMIT,
            DISCRIMINATIVE_LIMIT,
            NEXT_STUDY_LIMIT,
            DIRECT_LIMIT,
        }
        or campaign["call_limit"] > a["call_limit"]
        or campaign["source_date"] not in dates
        or any(p["day"] not in dates for p in campaign["pairs"])
        or any(
            p["candidate_registry"] != v["config"]["candidate_registry"]
            for p in campaign["pairs"]
        )
    ):
        raise ValueError("auxiliary_research_campaign_invalid")
    return a


def native_contract():
    """Capture pure runtime request configuration, without a client or secrets."""
    from src.engine import ai_engine_openai as E

    engine = E.GPTSniperEngine.__new__(E.GPTSniperEngine)
    return dict(
        engine_sha256=P.file_hash(E.__file__),
        schema_name=E.ENTRY_RISK_ADJUDICATION_SCHEMA,
        max_output_tokens=engine._resolve_openai_max_output_tokens(require_json=True),
        reasoning_effort=engine._resolve_openai_reasoning_effort(
            model_name="gpt-5.4-nano"
        ),
        temperature=engine._resolve_openai_temperature(
            require_json=True, temperature_override=None, model_name="gpt-5.4-nano"
        ),
    )


def request(snapshot, registry, contract=None, *, output_tokens_override=None):
    """Native-current wire replay; registry identity still names the live parent."""
    import json

    req = G.request(snapshot, registry)
    if output_tokens_override is not None and (
        contract is None or output_tokens_override != 1024
    ):
        raise ValueError("auxiliary_research_output_override_invalid")
    if contract is None:
        return req
    if contract != native_contract():
        raise ValueError("auxiliary_native_wire_contract_changed")
    default = G.definition(
        registry["base_arm"], input_version=registry["input_version"]
    )
    if registry["registry_sha256"] != default["registry_sha256"]:
        # The actual registered-prompt path already transmits the registry's
        # exact raw prompt, typed schema and 1024-token contract. Do not wrap it
        # as a historical non-registry request or charge a duplicate replay.
        return req
    from src.engine import ai_engine_openai as E
    from src.engine.ai_prompt_contracts import (
        CONTINUOUS_REVERSAL_AUXILIARY_PROMPT_VERSIONS,
    )

    engine = E.GPTSniperEngine.__new__(E.GPTSniperEngine)
    candidate = req["candidate"]
    prompt_version = candidate["prompt_version"]
    user = json.dumps(
        req["candidate_input"], ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    candidate["system_prompt"] = engine._wrap_openai_prompt_contract(
        candidate["system_prompt"],
        require_json=True,
        schema_name=contract["schema_name"],
        endpoint_name="analyze_target",
    )
    req["candidate_input"] = user + (
        "\n\nReturn JSON only." if "json" not in user.lower() else ""
    )
    candidate.update(
        schema_name=contract["schema_name"],
        max_output_tokens=contract["max_output_tokens"],
        reasoning_effort=contract["reasoning_effort"],
        temperature=contract["temperature"],
        native_wire_contract=contract,
    )
    if prompt_version in CONTINUOUS_REVERSAL_AUXILIARY_PROMPT_VERSIONS:
        candidate.update(max_output_tokens=512, reasoning_effort="none")
    if output_tokens_override is not None:
        candidate["max_output_tokens"] = output_tokens_override
    req["candidate_input_sha256"] = P.digest(req["candidate_input"])
    req["paired_replay_id"] = P.digest(
        [
            G.A.opportunity(snapshot[0]),
            "NATIVE_CURRENT_WIRE",
            {k: req[k] for k in ("candidate_input", "candidate", "control", "stage")},
        ]
    )
    return req


def main(argv=None):
    import argparse
    import json
    import time
    from src.engine.scalping import reversal_auxiliary_tuning as T

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--mode", choices=["calls", "evaluate"], default="evaluate")
    parser.add_argument("--max-new-calls", type=int, default=20)
    args = parser.parse_args(argv)
    c = T.read(directory(args.data_root, args.experiment) / "latest-campaign.json")
    path = (
        directory(args.data_root, args.experiment)
        / "campaigns"
        / (c["artifact_content_sha256"] + ".json")
    )
    calls = None
    if args.mode == "calls":
        from src.engine.scalping.ai_decision_quality import _offline_openai_api_keys

        if not _offline_openai_api_keys():
            raise ValueError("auxiliary_research_credential_unavailable")
        calls = T.calls(
            args.data_root,
            c["source_date"],
            campaign_path=path,
            max_new_calls=args.max_new_calls,
            stop_epoch=time.time() + 600,
        )
    evaluated = T.evaluate(args.data_root, c["source_date"], campaign_path=path)
    print(
        json.dumps(
            dict(
                new_calls=calls["new_calls"] if calls else 0,
                call_budget=calls["call_budget"] if calls else None,
                evaluation_sha256=evaluated["artifact_content_sha256"],
                paired_points=sum(
                    v["paired_points"] for v in evaluated["scopes"].values()
                ),
                improved_scopes=[
                    s for s, v in evaluated["scopes"].items() if v["improved"]
                ],
                runtime_effect=False,
            )
        )
    )


if __name__ == "__main__":
    main()
