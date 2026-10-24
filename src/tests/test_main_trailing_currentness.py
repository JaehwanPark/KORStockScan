import json
from pathlib import Path
import pytest
from src.engine.monitoring import main_trailing_currentness as monitor
from src.engine.automation import main_trailing_all_scope_research as research
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping.pre_submit_delay_initial_policy import digest

SOURCE = "2026-10-16"
TARGET = "2026-10-19"


def seal(path, value):
    value = dict(value)
    value.pop("artifact_sha256", None)
    value["artifact_sha256"] = digest(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    return value


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(monitor, "code_contract", lambda: "b" * 64)
    monkeypatch.setattr(research, "code_contract", lambda: "b" * 64)
    root = data / "report/main_all_scope_trailing" / SOURCE / "generations"
    manifest = root / "new/manifest.json"
    seal(manifest, dict(source_data_root=str(data)))
    report = dict(
        schema="main_all_scope_exit_research_v2",
        status="complete",
        source_date=SOURCE,
        target_date=TARGET,
        code_contract_sha256="a" * 64,
        allowed_runtime_apply=False,
        input_window_generation_sha256="w" * 64,
        input_manifest_path=str(manifest),
        initial_policy=dict(policy_sha256="p" * 64),
        scope=dict(scope_count=3),
    )
    old = root / "old/research.json"
    seal(old, report)
    current = root / "new/research.json"
    report["code_contract_sha256"] = "b" * 64
    seal(current, report)
    holding = dict(
        date=SOURCE,
        meta=dict(snapshot_profile="postclose_exit"),
        all_scope_trailing_research=monitor._extension(
            json.loads(old.read_bytes()), old, byte_generation(old)
        ),
    )
    path = data / "report/monitor_snapshots" / f"holding_exit_observation_{SOURCE}.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(holding))
    calls = []

    def verify(path, *, target_date):
        calls.append((path, target_date))
        return json.loads(path.read_bytes()), byte_generation(path)

    monkeypatch.setattr(monitor.native, "verify_report", verify)
    return data, path, holding, current, calls


def test_full_native_issuance_preserves_original_policy_and_health_only(bundle):
    data, path, holding, current, calls = bundle
    before = path.read_bytes()
    assert (
        monitor.observe(data, holding, target_date=TARGET)["status"] == "source_invalid"
    )
    receipt = monitor.issue(
        data, source_date=SOURCE, target_date=TARGET, report_path=current
    )
    assert calls == [(current, TARGET)] and path.read_bytes() == before
    assert (
        receipt["runtime_effect"] is False and receipt["allowed_runtime_apply"] is False
    )
    result = monitor.observe(data, holding, target_date=TARGET)
    assert result["status"] == "generation_current"
    assert result["basis"] == "separate_full_native_revalidation"
    assert result["original_findings"] == ["main_trailing_research_handoff_invalid"]
    assert result["policy_effect"] == "unchanged"
    assert (
        monitor.issue(data, source_date=SOURCE, target_date=TARGET, report_path=current)
        == receipt
    )


@pytest.mark.parametrize(
    "defect",
    ["native_failure", "source_date", "data_root", "policy", "scope", "outside"],
)
def test_issuance_rejects_invalid_native_or_changed_identity(
    bundle, monkeypatch, defect
):
    data, path, holding, current, calls = bundle
    if defect == "native_failure":

        def fail(*a, **kw):
            raise ValueError("native_source_invalid")

        monkeypatch.setattr(monitor.native, "verify_report", fail)
    elif defect == "data_root":
        seal(current.parent / "manifest.json", dict(source_data_root=str(data.parent)))
    elif defect == "outside":
        new = data / "outside.json"
        new.write_bytes(current.read_bytes())
        current = new
    else:
        body = json.loads(current.read_bytes())
        if defect == "source_date":
            body["source_date"] = "2026-10-15"
        elif defect == "policy":
            body["initial_policy"]["policy_sha256"] = "changed"
        else:
            body["scope"]["scope_count"] = 4
        seal(current, body)
    with pytest.raises(ValueError):
        monitor.issue(data, source_date=SOURCE, target_date=TARGET, report_path=current)
    assert not monitor._paths(data, SOURCE, TARGET)[2].exists()


@pytest.mark.parametrize(
    "defect",
    [
        "original",
        "new_report",
        "receipt",
        "date",
        "authority",
        "code",
        "policy",
        "scope",
        "symlink",
    ],
)
def test_observer_preserves_failure_for_tampered_generation(bundle, defect):
    data, path, holding, current, _ = bundle
    monitor.issue(data, source_date=SOURCE, target_date=TARGET, report_path=current)
    receipt_path = monitor._paths(data, SOURCE, TARGET)[2]
    receipt = json.loads(receipt_path.read_bytes())
    if defect == "original":
        path.write_bytes(path.read_bytes() + b" ")
    elif defect == "new_report":
        current.write_bytes(current.read_bytes() + b" ")
    elif defect == "symlink":
        dest = current.with_suffix(".original")
        current.rename(dest)
        current.symlink_to(dest)
    elif defect in {"policy", "scope"}:
        body = json.loads(current.read_bytes())
        body["initial_policy" if defect == "policy" else "scope"] = {}
        seal(current, body)
    else:
        if defect == "receipt":
            receipt["full_native_validation"] = False
        elif defect == "date":
            receipt["target_date"] = "2026-10-20"
        elif defect == "authority":
            receipt["allowed_runtime_apply"] = True
        else:
            receipt["code_contract_sha256"] = "c" * 64
        seal(receipt_path, receipt)
    result = monitor.observe(data, holding, target_date=TARGET)
    assert result["status"] == "source_invalid" and result["findings"] == [
        "main_trailing_research_handoff_invalid"
    ]
    assert result["currentness_findings"]


def test_other_contract_failure_cannot_use_refresh_receipt(bundle):
    data, path, holding, current, _ = bundle
    monitor.issue(data, source_date=SOURCE, target_date=TARGET, report_path=current)
    holding["all_scope_trailing_research"] = None
    result = monitor.observe(data, holding, target_date=TARGET)
    assert result["status"] == "source_invalid"


@pytest.mark.parametrize(
    "damage", [None, "digest", "universe", "source", "membership", "clock"]
)
def test_reobservation_clock_requires_exact_native_scope_and_sealed_universe(
    bundle, damage
):
    from src.engine.scalping.main_exit_scope import build_scope
    from src.engine.lifecycle import research_storage as storage

    data, holding_path, holding, current, _ = bundle
    old = Path(holding["all_scope_trailing_research"]["report_path"])
    for path, clock in ((old, 1000), (current, 2000)):
        manifest = dict(
            source_data_root=str(data),
            universe=[dict(symbol="005930", known_at=1, tradable=True)],
            as_of=clock,
            universe_source_sha256="a" * 64,
        )
        scope = build_scope(
            manifest["universe"], as_of=clock, universe_source_sha256="a" * 64
        )
        ref = storage.write_tree(path.parent, scope.pop("scopes"))
        scope["scopes_ref"] = ref
        if path == current:
            if damage == "digest":
                scope["universe_snapshot_sha256"] = "0" * 64
            elif damage == "universe":
                manifest["universe"][0]["symbol"] = "000660"
            elif damage == "source":
                manifest["universe_source_sha256"] = "b" * 64
            elif damage == "membership":
                scope["symbol_count"] += 1
            elif damage == "clock":
                scope["as_of"] = -1
        manifest_path = path.parent / "manifest.json"
        seal(manifest_path, manifest)
        body = json.loads(path.read_bytes())
        body.update(
            scope=scope,
            input_manifest_path=str(manifest_path),
            input_manifest_generation=byte_generation(manifest_path),
        )
        seal(path, body)
    holding["all_scope_trailing_research"] = monitor._extension(
        json.loads(old.read_bytes()), old, byte_generation(old)
    )
    holding_path.write_text(json.dumps(holding))
    before = holding_path.read_bytes()
    if damage:
        with pytest.raises(ValueError):
            monitor.issue(
                data, source_date=SOURCE, target_date=TARGET, report_path=current
            )
    else:
        monitor.issue(data, source_date=SOURCE, target_date=TARGET, report_path=current)
        assert (
            monitor.observe(data, holding, target_date=TARGET)["status"]
            == "generation_current"
        )
    assert holding_path.read_bytes() == before
