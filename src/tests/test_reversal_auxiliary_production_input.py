"""Native registry opt-in preserves incumbent bytes and exact research input."""

import copy
import json
from types import SimpleNamespace

import pytest

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_production_input as M
from src.engine.scalping import reversal_auxiliary_risk_role_experiment as X
from src.engine.scalping import reversal_auxiliary_wire as W
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W
from src.tests.test_reversal_extended_policy import FIXTURES


def definitions(fixture=None):
    fixture = fixture or next(iter(FIXTURES.values()))
    event = fixture["event"]
    sid = (
        M.C.cell_key(event["symbol"], event["market"], event["confirmation_price"])
        + "|"
        + event["venue"]
    )
    original = G.definition(M.U.V1.ARMS[1], input_version=M.U.VERSION)
    parent = G.compact_definition(original, research_wire_contract=OLD_W.contract())
    current = G.production_definition(parent, scope_ids=[sid])
    return original, parent, current


@pytest.mark.parametrize("fixture", list(FIXTURES.values()))
def test_exact_production_projection_preserves_native_signals_and_wire(
    fixture, tmp_path, monkeypatch
):
    from src.engine.scalping import reversal_auxiliary_intraday as I

    original, parent, current = definitions(fixture)
    snap = (fixture["event"], fixture["source"])
    before = copy.deepcopy((snap, original, parent))
    baseline = G.production_request(snap, parent)
    projected, prompt, schema = G.production_request(snap, current)
    expected = X.project(baseline[0], expected_contract=X.contract(M.MODE))
    assert projected == expected and projected["signals"] == baseline[0]["signals"]
    assert prompt == baseline[1] and schema == M.U.response_schema(expected)
    env = G.envelope(projected, current)
    assert env == W.envelope(expected, prompt, schema)
    req = G.request(snap, current)
    assert req["candidate_input"] == env["wire_input"]
    assert req["candidate"]["system_prompt"] == env["final_prompt"]
    assert req["candidate"]["response_schema"] == env["wire_schema"]
    assert req["candidate"]["logical_input_sha256"] == P.digest(projected)
    assert req["candidate_input_sha256"] == P.digest(env["wire_input"])
    assert req["paired_replay_id"] != G.request(snap, parent)["paired_replay_id"]
    assert G.production_request(snap, original) == baseline
    assert (snap, original, parent) == before
    assessment = dict(
        action="ENTER_NOW",
        policy_version="continuous_reversal_policy_v6",
        signal_set_hash=P.digest(baseline[0]["signals"]),
    )
    monkeypatch.setattr(I, "selected_definition", lambda *args: (current, None))
    result = I.apply_request(
        tmp_path, {"bundle_sha256": "a" * 64}, snap, (assessment, *baseline)
    )
    assert result[1:] == (projected, prompt, schema)
    assert result[0]["signal_set_hash"] == assessment["signal_set_hash"]
    assert result[0]["auxiliary_registry_sha256"] == current["registry_sha256"]
    assert result[0]["auxiliary_wire_hashes"] == env["hashes"]
    for action in ("BLOCK", "RECHECK"):
        denied = ({**assessment, "action": action}, *baseline)
        assert I.apply_request(tmp_path, {}, snap, denied) is denied
    for registry in original, parent, current:
        G.register(tmp_path, registry)
    assert G.load(tmp_path, parent["registry_sha256"]) == parent
    assert G.load(tmp_path, current["registry_sha256"]) == current


@pytest.mark.parametrize(
    "defect",
    ["missing", "empty", "mode", "source", "transform", "scope", "parent", "version"],
)
def test_malformed_registry_fails_even_with_rehashed_identity(defect):
    _, _, value = definitions()
    bad = copy.deepcopy(value)
    contract = bad["production_input_contract"]
    if defect == "missing":
        bad.pop("production_input_contract")
    if defect == "empty":
        bad["production_input_contract"] = {}
    if defect == "mode":
        contract["mode"] = "ROLE"
    if defect == "source":
        contract["source_sha256"] = "a" * 64
    if defect == "transform":
        contract["transform_sha256"] = "a" * 64
    if defect == "scope":
        contract["scope_ids"] = ["other_non_fixed|PRE|LT_20000|KRX"]
    if defect == "parent":
        bad["production_parent_registry_sha256"] = "invalid"
    if defect == "version":
        bad["input_version"] = "continuous_reversal_union_auxiliary_v2"
    bad["registry_sha256"] = P.digest(
        {k: v for k, v in bad.items() if k != "registry_sha256"}
    )
    with pytest.raises(ValueError):
        G.validate(bad)


def test_parent_and_scope_cannot_leak_or_be_silently_replaced(tmp_path):
    original, parent, current = definitions()
    for registry in original, parent, current:
        G.register(tmp_path, registry)
    G.directory(tmp_path).joinpath(parent["registry_sha256"] + ".json").unlink()
    with pytest.raises((ValueError, OSError)):
        G.load(tmp_path, current["registry_sha256"])
    fixture = next(iter(FIXTURES.values()))
    baseline = G.production_request((fixture["event"], fixture["source"]), parent)[0]
    other = copy.deepcopy(baseline)
    other["common_context"]["venue"] = "NXT"
    with pytest.raises(ValueError, match="scope_mismatch"):
        M.project(other, expected_contract=current["production_input_contract"])
    for scopes in (
        [],
        current["production_input_contract"]["scope_ids"] * 2,
        ["invalid"],
    ):
        with pytest.raises(ValueError):
            G.production_definition(parent, scope_ids=scopes)


@pytest.mark.parametrize(
    "defect",
    [
        "untransformed",
        "changed_value",
        "missing_fact",
        "changed_binding",
        "changed_role",
    ],
)
def test_wire_and_decode_fail_closed_for_unprojected_or_altered_input(defect):
    _, parent, current = definitions()
    f = next(iter(FIXTURES.values()))
    snap = (f["event"], f["source"])
    logical = G.production_request(snap, current)[0]
    bad = copy.deepcopy(logical)
    setup = bad["entry_setup_evidence_v1"]
    fact = next(
        f for f in setup["context_facts"] if "/observed_target_progress_v1/" in f["id"]
    )
    if defect == "untransformed":
        bad = G.production_request(snap, parent)[0]
    if defect == "changed_value":
        fact["value"] += 1
    if defect == "missing_fact":
        setup["context_facts"].remove(fact)
    if defect == "changed_binding":
        setup["risk_fact_bindings"]["OBSERVED_TARGET_PROGRESS_CONCERN"].remove(
            fact["id"]
        )
    if defect == "changed_role":
        setup["context_facts"].remove(fact)
        setup["contradicting_facts"].append(fact)
    with pytest.raises(ValueError):
        G.envelope(bad, current)
    with pytest.raises(ValueError):
        G.decode_response({}, bad, current)


def test_live_sdk_wire_identity_and_new_numeric_citation(tmp_path, monkeypatch):
    from src.tests.test_ai_engine_openai_transport import _build_engine
    from src.engine import ai_engine_openai as E
    from src.utils import constants

    original, parent, current = definitions()
    for value in original, parent, current:
        G.register(tmp_path, value)
    f = next(iter(FIXTURES.values()))
    snap = (f["event"], f["source"])
    logical, prompt, schema = G.production_request(snap, current)
    env = G.envelope(logical, current)
    fact = next(
        f
        for f in logical["entry_setup_evidence_v1"]["context_facts"]
        if "/observed_target_progress_v1/" in f["id"]
    )
    raw = dict(
        assessed={env["citation_map"][s["ref"]]: True for s in logical["signals"]},
        screen=dict(
            verdict="CAUTION",
            risk="OBSERVED_TARGET_PROGRESS_CONCERN",
            fact=env["citation_map"][fact["id"]],
        ),
        confidence=55,
    )
    engine = _build_engine()
    calls = []
    captures = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            output_text=json.dumps(raw), id="production-input-test", status="completed"
        )

    engine.client = SimpleNamespace(responses=SimpleNamespace(create=create))
    monkeypatch.setattr(constants, "DATA_DIR", tmp_path)
    monkeypatch.setattr(E, "capture_ai_request", lambda **kw: captures.append(kw) or {})
    result = engine._call_openai_safe(
        prompt,
        json.dumps(logical, ensure_ascii=True, sort_keys=True, separators=(",", ":")),
        model_override=current["model"],
        schema_name=E.ENTRY_RISK_ADJUDICATION_SCHEMA,
        endpoint_name="analyze_target",
        transport_mode_override="http",
        metadata_extra={
            "entry_setup_live_policy_selected_prompt_version": G.binding(current)[
                "prompt_version"
            ]
        },
        response_schema_override=schema,
        auxiliary_registry_sha256=current["registry_sha256"],
        replay_context=logical,
        auxiliary_identity_context=dict(
            policy_version="continuous_reversal_policy_v6",
            registry_sha256=current["registry_sha256"],
        ),
    )
    assert result == raw and len(calls) == 1
    sent = calls[0]
    assert sent["instructions"] == env["final_prompt"]
    assert sent["input"] == json.dumps(
        env["wire_input"], ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    assert sent["text"]["format"]["schema"] == env["wire_schema"]
    assert (
        sent["text"]["format"]["name"] == W.VERSION and sent["model"] == "gpt-5.4-nano"
    )
    assert (
        sent["max_output_tokens"] == 1024
        and sent["reasoning"] == {"effort": "none"}
        and "temperature" not in sent
    )
    assert G.decode_response(result, logical, current)["contradicting_fact_ids"] == [
        fact["id"]
    ]
    meta = engine._consume_last_transport_meta()
    identity = G.validate_identity(meta["entry_auxiliary_policy_identity"])
    assert (
        identity["semantic"]["production_input_contract"]
        == current["production_input_contract"]
    )
    assert (
        "allowed_runtime_apply" not in identity["semantic"]["production_input_contract"]
    )
    baseline, p, _ = G.production_request(snap, parent)
    legacy_env = G.envelope(baseline, parent)
    legacy_payload = dict(
        sent,
        instructions=legacy_env["final_prompt"],
        input=json.dumps(legacy_env["wire_input"]),
        text=dict(format=dict(schema=legacy_env["wire_schema"])),
    )
    old_identity = G.provider_identity(
        legacy_payload,
        dict(
            policy_version="continuous_reversal_policy_v6",
            registry_sha256=parent["registry_sha256"],
        ),
    )
    assert "production_input_contract" not in old_identity["semantic"]
    assert old_identity["identity_sha256"] != identity["identity_sha256"]
    assert captures[0]["metadata"]["auxiliary_wire_envelope"]["hashes"] == env["hashes"]


@pytest.mark.parametrize("spread", [0.0, 0.2, 0.4])
def test_legacy_spread_contract_preserves_exact_research_projection(spread):
    from src.tests.test_reversal_auxiliary_risk_role_experiment import legacy

    logical, _ = legacy(spread)
    common = logical["common_context"]
    sid = (
        M.C.cell_key(common["symbol"], common["market"], common["confirmation_price"])
        + "|"
        + common["venue"]
    )
    contract = M.contract([sid])
    transformed = M.project(logical, expected_contract=contract)
    assert transformed == X.project(logical, expected_contract=X.contract(M.MODE))
    assert M.validate_projected(transformed, expected_contract=contract) == transformed
    assert transformed["signals"] == logical["signals"]


@pytest.mark.parametrize(
    "response_kind", ["completed", "native_changed_after_response"]
)
def test_full_live_consumer_retains_native_and_response_guards(
    tmp_path, monkeypatch, response_kind
):
    from src.tests import test_reversal_auxiliary_wire as live

    original, parent, current = definitions()
    G.register(tmp_path, original)
    G.register(tmp_path, parent)
    monkeypatch.setattr(live, "definitions", lambda: (original, current))
    live.test_full_analyze_target_records_raw_then_decodes(
        tmp_path, monkeypatch, response_kind
    )


def test_unknown_transform_bytes_cannot_use_the_reviewed_production_contract(
    monkeypatch,
):
    _, _, current = definitions()
    original_hash = P.file_hash
    monkeypatch.setattr(
        P,
        "file_hash",
        lambda path: "0" * 64 if str(path) == X.__file__ else original_hash(path),
    )
    with pytest.raises(
        ValueError, match="auxiliary_production_input_transform_changed"
    ):
        M.validate(current["production_input_contract"])


def frozen_formatted_definitions():
    """Build original-schema fixtures, preserving their physical source stamps."""
    from src.engine.automation.intraday_release_handoff import _formatting_review
    from src.engine.scalping import reversal_auxiliary_compatibility as C

    review = _formatting_review()
    original, _, current = definitions()
    original["projector_sha256"] = review[
        "src/engine/scalping/reversal_extended_union.py"
    ]["before_sha256"]
    original["registry_sha256"] = P.digest(
        {k: v for k, v in original.items() if k != "registry_sha256"}
    )
    wire = dict(
        W.contract(),
        source_sha256=C.REVIEWED_CONTRACT_SOURCE_PAIRS[
            "src/engine/scalping/reversal_auxiliary_wire.py"
        ][0][0],
    )
    parent = G.compact_definition(
        original, research_wire_contract=OLD_W.contract(), wire_contract=wire
    )
    contract = dict(
        current["production_input_contract"],
        source_sha256=C.REVIEWED_CONTRACT_SOURCE_PAIRS[
            "src/engine/scalping/reversal_auxiliary_production_input.py"
        ][0][0],
        transform_sha256=review[
            "src/engine/scalping/reversal_auxiliary_risk_role_experiment.py"
        ]["before_sha256"],
    )
    current = G.production_definition(
        parent, scope_ids=contract["scope_ids"], production_contract=contract
    )
    return original, parent, current


def test_frozen_registry_full_consumer_preserves_identity_and_guards(tmp_path):
    original, parent, current = frozen_formatted_definitions()
    fixture = next(iter(FIXTURES.values()))
    snapshot = (fixture["event"], fixture["source"])
    originals = copy.deepcopy((original, parent, current))
    for item in originals:
        G.register(tmp_path, item)
    assert G.load(tmp_path, current["registry_sha256"]) == current
    assert G.load(tmp_path, parent["registry_sha256"]) == parent
    logical, prompt, schema = G.production_request(snapshot, current)
    fresh = definitions()[2]
    assert G.production_request(snapshot, fresh) == (logical, prompt, schema)
    envelope = G.envelope(logical, current)
    assert envelope["contract"] == current["wire_contract"]
    assert envelope["hashes"] == G.envelope(logical, fresh)["hashes"]
    envelope["contract"]["source_sha256"] = "0" * 64
    assert current == originals[2]
    request = G.request(snapshot, current)
    request["candidate"]["compact_runtime_contract"] = copy.deepcopy(
        parent["wire_contract"]
    )
    _, _, aliases = W.encode(logical)
    raw = dict(
        assessed={aliases[s["ref"]]: True for s in logical["signals"]},
        screen=dict(
            verdict="PASS",
            risk="NO_BLOCKING_RISK",
            fact=aliases["observed_machine_signal"],
        ),
        confidence=50,
    )
    response = W.response(
        dict(candidate_response=raw), request, logical, current["base_arm"]
    )
    assert response == W.decode(raw, logical, current["base_arm"])
    before = copy.deepcopy(request)
    bad = copy.deepcopy(raw)
    bad["assessed"] = {}
    with pytest.raises(ValueError):
        W.response(dict(candidate_response=bad), request, logical, current["base_arm"])
    assert request == before and (original, parent, current) == originals


@pytest.mark.parametrize(
    "field",
    [
        "projector",
        "wire_source",
        "wire_version",
        "input_source",
        "transform",
        "scope",
        "authority",
        "unknown_field",
    ],
)
def test_frozen_contract_never_accepts_unknown_semantics_even_when_resealed(field):
    _, _, value = frozen_formatted_definitions()
    value = copy.deepcopy(value)
    if field == "projector":
        value["projector_sha256"] = "0" * 64
    elif field == "wire_source":
        value["wire_contract"]["source_sha256"] = "0" * 64
    elif field == "wire_version":
        value["wire_contract"]["decoder_version"] = "unknown"
    elif field == "input_source":
        value["production_input_contract"]["source_sha256"] = "0" * 64
    elif field == "transform":
        value["production_input_contract"]["transform_sha256"] = "0" * 64
    elif field == "scope":
        value["production_input_contract"]["scope_ids"] = ["foreign|scope"]
    elif field == "authority":
        value["production_input_contract"]["decision_authority"] = "MACHINE_PROMOTION"
    else:
        value["production_input_contract"]["unexpected"] = True
    value["registry_sha256"] = P.digest(
        {k: v for k, v in value.items() if k != "registry_sha256"}
    )
    with pytest.raises(ValueError):
        G.validate(value)


@pytest.mark.parametrize("source", ["wire", "production", "transform", "projector"])
def test_frozen_contract_rejects_changed_current_source(source, monkeypatch):
    from src.engine.scalping import reversal_auxiliary_compatibility as C

    _, _, value = frozen_formatted_definitions()
    name = dict(
        wire=W.__file__,
        production=M.__file__,
        transform=X.__file__,
        projector=M.U.__file__,
    )[source]
    original = P.file_hash
    monkeypatch.setattr(
        P, "file_hash", lambda path: "f" * 64 if str(path) == name else original(path)
    )
    with pytest.raises(ValueError):
        G.validate(value)


def test_frozen_contract_fails_if_review_manifest_changed(monkeypatch):
    from src.engine.automation import intraday_release_handoff as H

    _, _, value = frozen_formatted_definitions()
    monkeypatch.setattr(H, "_FORMATTING_REVIEW_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="formatting_review_invalid"):
        G.validate(value)


@pytest.mark.parametrize(
    "mixed", ["old_source_new_transform", "new_source_old_transform"]
)
def test_frozen_contract_rejects_unissued_mixed_source_generation(mixed):
    _, _, value = frozen_formatted_definitions()
    original = value["production_input_contract"]
    current = M.contract(original["scope_ids"])
    bad = dict(original)
    key = "transform_sha256" if mixed == "old_source_new_transform" else "source_sha256"
    bad[key] = current[key]
    with pytest.raises(ValueError, match="contract_changed"):
        M.validate(bad)


def test_identifier_successor_keeps_frozen_contracts_without_mixing_generations():
    from src.engine.scalping import reversal_auxiliary_compatibility as C
    from src.engine.scalping import reversal_auxiliary_production_input as I
    from src.engine.scalping import reversal_auxiliary_wire as W

    # Exercise the actual physical readers, including the current frozen source.
    prod = C._source_generations(I.__file__)
    wire = C._source_generations(W.__file__)
    assert len(prod) == 6 and len(wire) == 3
    actual = dict(source_sha256=prod[0], wire_sha256=wire[0], mode="unchanged")
    sources = dict(source_sha256=I.__file__, wire_sha256=W.__file__)
    for p, w in (
        (prod[0], wire[0]),
        (prod[1], wire[0]),
        (prod[2], wire[0]),
        (prod[-2], wire[-2]),
        (prod[-1], wire[-1]),
    ):
        assert C.contract_matches(
            dict(actual, source_sha256=p, wire_sha256=w), actual, sources
        )
    assert not C.contract_matches(
        dict(actual, source_sha256=prod[0], wire_sha256=wire[-2]), actual, sources
    )
    assert not C.contract_matches(dict(actual, source_sha256="0" * 64), actual, sources)
    assert not C.contract_matches(dict(actual, mode="changed"), actual, sources)


def _completed_context(epoch, item):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    end = datetime.fromtimestamp(epoch, ZoneInfo("Asia/Seoul")).replace(
        second=0, microsecond=0
    ) - timedelta(minutes=1)
    # Exact MCNEX 2026-10-29 08:00..08:04 completed OHLCV values.
    values = [
        (20250, 20300, 19990, 20150, 4017),
        (20150, 20550, 20050, 20400, 6934),
        (20400, 20650, 20350, 20600, 12567),
        (20600, 20900, 20600, 20800, 18002),
        (20800, 21100, 20650, 20650, 31602),
    ]
    return dict(
        schema="entry_candle_context_v1",
        request_code=item,
        session="premarket_krx_like",
        rest_route="_NX",
        ws_route="nxt_only",
        route_equivalence="not_proven",
        bar_schema=dict(order="oldest_to_latest", timezone="Asia/Seoul", interval="1m"),
        source_quality=dict(
            status="fresh_consistent",
            blockers=[],
            decision_window=dict(
                provider_call_allowed=True, end_timestamp=end.isoformat()
            ),
        ),
        bars=[
            dict(
                t=(end - timedelta(minutes=4 - i)).strftime("%H:%M"),
                **dict(zip(("o", "h", "l", "c", "v"), row)),
                forming=False,
                partial_volume=False,
            )
            for i, row in enumerate(values)
        ],
    )


def test_completed_candle_registry_to_wire_and_consumer_with_exact_mcnex_values(
    tmp_path, monkeypatch
):
    from src.engine.scalping import reversal_auxiliary_intraday as I

    f = next(iter(FIXTURES.values()))
    snap = (f["event"], f["source"])
    original, parent, old = definitions(f)
    scope = old["production_input_contract"]["scope_ids"]
    new = G.production_definition(
        parent,
        scope_ids=scope,
        production_contract=M.contract(scope, completed_candles=True),
    )
    context = _completed_context(f["event"]["epoch"], f["event"]["source_item"])
    before = copy.deepcopy(context)
    inp, prompt, schema = G.production_request(snap, new, entry_context=context)
    source = inp[M.CANDLE_FIELD]
    assert source["status"] == "observed"
    assert source["latest_upper_wick_ratio"] == pytest.approx(2 / 3)
    assert source["latest_close_return_pct"] == pytest.approx(100 * (20650 / 20800 - 1))
    assert source["latest_volume_ratio"] == pytest.approx(31602 / 18002)
    assert context == before
    for registry in (original, parent, new):
        G.register(tmp_path, registry)
    assert G.load(tmp_path, new["registry_sha256"]) == new
    from src.engine.scalping import reversal_auxiliary_compatibility as compatibility

    forged = dict(
        new["production_input_contract"],
        source_sha256=compatibility.REVIEWED_CONTRACT_SOURCE_PAIRS[
            "src/engine/scalping/reversal_auxiliary_production_input.py"
        ][0][0],
    )
    with pytest.raises(ValueError, match="completed_candle_contract_changed"):
        M.validate(forged)
    env = G.envelope(inp, new)
    req = G.request(snap, new, entry_context=context)
    assert req["candidate_input"] == env["wire_input"]
    aliases = W.encode(inp)[2]
    response = dict(
        assessed={aliases[s["ref"]]: True for s in inp["signals"]},
        screen=dict(verdict="CAUTION", risk=M.CANDLE_RISK, fact=aliases[M.CANDLE_FACT]),
        confidence=50,
    )
    assert G.decode_response(response, inp, new)["contradicting_fact_ids"] == [
        M.CANDLE_FACT
    ]
    base = G.production_request(snap, parent)
    a = dict(
        action="ENTER_NOW",
        policy_version="continuous_reversal_policy_v6",
        signal_set_hash=P.digest(base[0]["signals"]),
    )
    monkeypatch.setattr(I, "selected_definition", lambda *args: (new, None))
    assert I.apply_request(
        tmp_path, dict(bundle_sha256="a" * 64), snap, (a, *base), entry_context=context
    )[1:] == (inp, prompt, schema)
    assert (
        M.CANDLE_FIELD not in G.production_request(snap, old, entry_context=context)[0]
    )
    bad = copy.deepcopy(inp)
    bad[M.CANDLE_FIELD]["latest_upper_wick_ratio"] = 0
    with pytest.raises(ValueError, match="projection_changed"):
        G.envelope(bad, new)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "other_item",
        "forming",
        "future",
        "stale",
        "prior_day",
        "blocked",
        "invalid_bar",
        "sparse",
    ],
)
def test_completed_candle_missing_or_invalid_never_becomes_adverse_fact(fault):
    f = next(iter(FIXTURES.values()))
    _, parent, old = definitions(f)
    scope = old["production_input_contract"]["scope_ids"]
    new = G.production_definition(
        parent,
        scope_ids=scope,
        production_contract=M.contract(scope, completed_candles=True),
    )
    context = _completed_context(f["event"]["epoch"], f["event"]["source_item"])
    if fault == "missing":
        context = None
    if fault == "other_item":
        context["request_code"] = "097520_AL"
    if fault == "forming":
        context["bars"][-1]["forming"] = True
    if fault == "future":
        context["bars"][-1]["t"] = "23:59"
    if fault == "stale":
        context["source_quality"]["status"] = "stale"
    if fault == "prior_day":
        context["source_quality"]["decision_window"][
            "end_timestamp"
        ] = "2000-01-01T08:04:00+09:00"
    if fault == "blocked":
        context["source_quality"]["blockers"] = ["route_conflict"]
    if fault == "invalid_bar":
        context["bars"][-1]["h"] = 1
    if fault == "sparse":
        context["bars"][-1]["t"] = context["bars"][-2]["t"]
    inp = G.production_request((f["event"], f["source"]), new, entry_context=context)[0]
    assert inp[M.CANDLE_FIELD]["status"] == "unavailable"
    assert M.CANDLE_RISK not in inp["entry_setup_evidence_v1"]["risk_fact_bindings"]
    G.envelope(inp, new)


def test_forming_suffix_does_not_hide_completed_predecessors():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    common = dict(
        epoch=datetime(
            2026, 10, 29, 8, 5, 29, tzinfo=ZoneInfo("Asia/Seoul")
        ).timestamp(),
        source_item="097520_NX",
    )
    context = _completed_context(common["epoch"], common["source_item"])
    before = M.completed_candle_source(context, common)
    context["bars"].append(
        dict(
            t="08:05",
            o=20650,
            h=20900,
            l=20600,
            c=20850,
            v=100,
            forming=True,
            partial_volume=True,
        )
    )
    assert M.completed_candle_source(context, common) == before


def test_aftermarket_first_uptick_exact_capture_projection_and_old_response():
    from pathlib import Path
    from src.engine.scalping import reversal_extended_union as U

    fixture = json.loads(
        (
            Path(__file__).parent
            / "fixtures/reversal_extended/aftermarket_030960_confirmation.json"
        ).read_text()
    )
    inp = fixture["logical_input"]
    event = fixture["native_event"]
    common = inp["common_context"]
    sid = (
        M.C.cell_key(common["symbol"], common["market"], common["confirmation_price"])
        + "|"
        + common["venue"]
    )
    contract = M.contract([sid], confirmation_only=True)
    untouched = copy.deepcopy(inp)
    out = M.project(inp, expected_contract=contract, native_event=event)
    signal = out["signals"][0]
    assert inp == untouched and "confirmation_pct" not in inp["signals"][0]["facts"]
    assert signal["confirmation_observation"]["status"] == "observed"
    assert signal["facts"]["confirmation_pct"] == pytest.approx(0.29806259314455463)
    assert signal["facts"]["confirmation_pct"] > signal["facts"]["spread_pct"]
    assert out["entry_setup_evidence_v1"] == inp["entry_setup_evidence_v1"]
    assert M.validate_projected(out, expected_contract=contract) == out
    wire, _, _ = W.encode(out)
    assert (
        wire["signals"][0]["facts"]["confirmation_pct"]
        == signal["facts"]["confirmation_pct"]
    )
    response = dict(
        schema=U.VERSION,
        decision_scope="COMMON_OPPORTUNITY",
        assessed_signal_refs=[signal["ref"]],
        risk_verdict="CAUTION",
        risk_codes=["ENTRY_SPREAD_CONCERN"],
        supporting_fact_ids=[],
        contradicting_fact_ids=out["entry_setup_evidence_v1"]["risk_fact_bindings"][
            "ENTRY_SPREAD_CONCERN"
        ][:1],
        confidence=50,
    )
    assert U.validate_response(response, out, arm=U.V1.ARMS[-1]) == []


@pytest.mark.parametrize(
    "defect", ["missing", "epoch", "original", "value", "projection"]
)
def test_aftermarket_confirmation_provenance_fails_closed(defect):
    from pathlib import Path

    fixture = json.loads(
        (
            Path(__file__).parent
            / "fixtures/reversal_extended/aftermarket_030960_confirmation.json"
        ).read_text()
    )
    inp, event = fixture["logical_input"], fixture["native_event"]
    c = inp["common_context"]
    contract = M.contract(
        [
            M.C.cell_key(c["symbol"], c["market"], c["confirmation_price"])
            + "|"
            + c["venue"]
        ],
        confirmation_only=True,
    )
    signal = next(iter(event["branch_signals"].values()))
    if defect == "missing":
        signal.pop("confirmation_pct")
        projected = M.project(inp, expected_contract=contract, native_event=event)
        assert (
            projected["signals"][0]["confirmation_observation"]["status"]
            == "unavailable"
        )
        assert "confirmation_pct" not in projected["signals"][0]["facts"]
        M.validate_projected(projected, expected_contract=contract)
        return
    if defect == "epoch":
        signal["native_epoch"] += 1
    if defect == "original":
        signal["signal_proof"]["original_confirmation"]["low_price"] += 1
    if defect == "value":
        signal["confirmation_pct"] += 0.1
        signal["signal_proof"]["original_confirmation"]["confirmation_pct"] += 0.1
    if defect == "projection":
        projected = M.project(inp, expected_contract=contract, native_event=event)
        projected["signals"][0]["facts"]["confirmation_pct"] += 0.1
        with pytest.raises(ValueError, match="confirmation_observation_changed"):
            M.validate_projected(projected, expected_contract=contract)
        return
    with pytest.raises(ValueError, match="auxiliary_confirmation"):
        M.project(inp, expected_contract=contract, native_event=event)


def test_confirmation_nonfirst_is_explicitly_not_applicable():
    fixture = next(
        x for x in FIXTURES.values() if x["event"]["decision_phase"] != "FIRST_UPTICK"
    )
    event, source = fixture["event"], fixture["source"]
    inp = M.U.production_request(source, M.U.V1.ARMS[1], event=event)[0]
    c = inp["common_context"]
    contract = M.contract(
        [
            M.C.cell_key(c["symbol"], c["market"], c["confirmation_price"])
            + "|"
            + c["venue"]
        ],
        confirmation_only=True,
    )
    out = M.project(inp, expected_contract=contract, native_event=event)
    assert all(
        s["confirmation_observation"]["status"] == "not_applicable"
        and "confirmation_pct" not in s["facts"]
        for s in out["signals"]
    )
    M.validate_projected(out, expected_contract=contract)


def test_exact_aftermarket_capture_through_native_registry_and_wire(tmp_path):
    from pathlib import Path

    fixture = json.loads(
        (
            Path(__file__).parent
            / "fixtures/reversal_extended/aftermarket_030960_confirmation.json"
        ).read_text()
    )
    snapshot = fixture["native_snapshot"]
    original = G.definition(M.U.V1.ARMS[-1], input_version=M.U.VERSION)
    parent = G.compact_definition(original, research_wire_contract=OLD_W.contract())
    event = snapshot[0]
    sid = (
        M.C.cell_key(event["symbol"], event["market"], event["confirmation_price"])
        + "|"
        + event["venue"]
    )
    contract = M.contract([sid], confirmation_only=True)
    current = G.production_definition(
        parent, scope_ids=[sid], production_contract=contract
    )
    for value in (original, parent, current):
        G.register(tmp_path, value)
    assert G.load(tmp_path, current["registry_sha256"]) == current
    baseline, _, _ = G.production_request(snapshot, parent)
    assert baseline == fixture["logical_input"]
    projected, prompt, schema = G.production_request(snapshot, current)
    assert projected["signals"][0]["facts"]["confirmation_pct"] == pytest.approx(
        0.29806259314455463
    )
    env = G.envelope(projected, current)
    assert env["wire_input"]["signals"][0]["facts"][
        "confirmation_pct"
    ] == pytest.approx(0.29806259314455463)
    request = G.request(snapshot, current)
    assert request["candidate_input"] == env["wire_input"]
    assert request["candidate"]["response_schema"] == env["wire_schema"]
    assert request["candidate"]["system_prompt"] == env["final_prompt"]
    assert schema == M.U.response_schema(projected)


def test_missing_original_confirmation_is_unknown_without_synthetic_value():
    from pathlib import Path

    fixture = json.loads(
        (
            Path(__file__).parent
            / "fixtures/reversal_extended/aftermarket_030960_confirmation.json"
        ).read_text()
    )
    inp, event = fixture["logical_input"], fixture["native_event"]
    original = next(iter(event["branch_signals"].values()))["signal_proof"][
        "original_confirmation"
    ]
    original.pop("low_price")
    c = inp["common_context"]
    contract = M.contract(
        [
            M.C.cell_key(c["symbol"], c["market"], c["confirmation_price"])
            + "|"
            + c["venue"]
        ],
        confirmation_only=True,
    )
    out = M.project(inp, expected_contract=contract, native_event=event)
    assert out["signals"][0]["confirmation_observation"]["status"] == "unavailable"
    assert "confirmation_pct" not in out["signals"][0]["facts"]
    M.validate_projected(out, expected_contract=contract)


def test_completed_candle_predecessor_remains_exactly_bound():
    _, parent, current = definitions()
    scopes = current["production_input_contract"]["scope_ids"]
    candle = M.contract(scopes, completed_candles=True)
    predecessor = dict(
        candle,
        source_sha256="642381efec468d62a1ba68582b6a74b35fc36ee8cc2738c8cc2271eed80214bb",
    )
    assert M.validate(predecessor) == predecessor
    for changed in (
        dict(predecessor, source_sha256="0" * 64),
        dict(predecessor, source_boundary="changed"),
    ):
        with pytest.raises(ValueError):
            M.validate(changed)
