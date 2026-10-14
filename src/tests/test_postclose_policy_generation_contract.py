"""Report-only structural monitoring, native evidence, and stable recovery."""

import copy
import json
from pathlib import Path
import pytest
from src.engine.monitoring import policy_generation_contract as generation
from src.engine.monitoring import semantic_incident_contract as incidents


def test_code_cache_invalidates_only_corrected_file_and_never_caches_costs(tmp_path, monkeypatch):
    import os
    from src.engine.lifecycle import holding_window_generation as window
    files=[tmp_path/'first.py',tmp_path/'second.py']
    for path in files:path.write_text('original')
    cost=tmp_path/'cost.json';cost.write_text('cost-one')
    native=window.byte_generation
    reads=[]
    def recorded(path):
        reads.append(path)
        return native(path)
    monkeypatch.setattr(window,'byte_generation',recorded)
    window._code_generation.cache_clear();window._code_file_generation.cache_clear()
    original=window.cached_code_generation(files)
    assert reads==files
    reads.clear()
    assert window.cached_code_generation(files)==original and reads==[]
    stamp=files[1].stat()
    files[1].write_text('modified')
    os.utime(files[1],ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
    corrected=window.cached_code_generation(files)
    assert reads==[files[1]] and corrected[str(files[1])]!=original[str(files[1])]
    before=window.byte_generation(cost)['sha256']
    cost.write_text('cost-two')
    assert window.cached_code_generation(files)==corrected
    assert window.byte_generation(cost)['sha256']!=before


def attest(root, family):
    code = generation.code_generation(family)
    path = root / "report/postclose_generation_validation" / f"{family}_{code}.json"
    body = dict(
        schema="postclose_generation_fixture_receipt_v1",
        family=family,
        code_sha256=code,
        status="pass",
        closure_tests=["synthetic_eligible_source_to_native_reader"],
        unresolved_findings=[],
        runtime_effect=False,
    )
    body["receipt_sha256"] = generation.digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body))
    return path


def test_native_cutover_reports_unverified_without_reopening_legacy():
    assert (
        generation.inspect(None, family="auxiliary", day="2026-10-08")["findings"] == []
    )
    after = generation.inspect(None, family="auxiliary", day="2026-10-12")
    assert after["findings"] == ["policy_generation_unverified"]
    assert after["observation_complete"] is False


def test_fixture_schema_and_component_types_are_verified(tmp_path):
    import hashlib
    path=attest(tmp_path,'auxiliary')
    payload=dict(date='2026-10-12')
    contract=generation.native(payload,family='auxiliary',day='2026-10-12',
        data_root=tmp_path,source_state='complete',comparison_state='complete',handoff_state='carry')
    value=json.loads(path.read_text());value['schema']='foreign_receipt_v1'
    value['receipt_sha256']=generation.digest({k:v for k,v in value.items() if k!='receipt_sha256'})
    path.write_text(json.dumps(value))
    contract['fixture_receipt']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    assert generation.inspect(contract,family='auxiliary',day='2026-10-12',
        payload=payload,data_root=tmp_path)['status']=='unverified'
    contract['components']['comparison']=[]
    contract['contract_sha256']=generation.digest({k:v for k,v in contract.items() if k!='contract_sha256'})
    with pytest.raises(ValueError,match='component_type_invalid'):
        generation.inspect(contract,family='auxiliary',day='2026-10-12',payload=payload,data_root=tmp_path)


@pytest.mark.parametrize("family", list(generation.COMPONENTS))
def test_valid_empty_does_not_conceal_missing_generation_component(tmp_path, family):
    attest(tmp_path, family)
    payload = dict(date="2026-10-12", status="valid_empty", count=0)
    original = copy.deepcopy(payload)
    c = generation.native(
        payload,
        family=family,
        day="2026-10-12",
        data_root=tmp_path,
        source_state="valid_empty",
        comparison_state="hold_sample",
        handoff_state="incumbent_carried",
    )
    assert payload == original
    assert (
        generation.inspect(
            c, family=family, day="2026-10-12", payload=payload, data_root=tmp_path
        )["status"]
        == "verified"
    )
    assert (
        generation.inspect(c, family=family, day="2026-10-12", payload=payload)[
            "status"
        ]
        == "unverified"
    )
    c["components"]["comparison"]["status"] = "unsupported"
    c["contract_sha256"] = generation.digest(
        {k: v for k, v in c.items() if k != "contract_sha256"}
    )
    answer = generation.inspect(
        c, family=family, day="2026-10-12", payload=payload, data_root=tmp_path
    )
    assert (
        answer["status"] == "structurally_blocked"
        and answer["source_state"] == "valid_empty"
    )
    assert (
        answer["allowed_runtime_apply"] is False and answer["realized_profit"] is None
    )
    payload["count"] = 1
    with pytest.raises(ValueError, match="native_generation_mismatch"):
        generation.inspect(
            c, family=family, day="2026-10-12", payload=payload, data_root=tmp_path
        )


def test_fixture_receipt_correction_is_unverified_and_clock_rebuild_is_same_incident(
    tmp_path,
):
    path = attest(tmp_path, "holding_vote")
    payload = dict(date="2026-10-12")
    c = generation.native(
        payload,
        family="holding_vote",
        day="2026-10-12",
        data_root=tmp_path,
        source_state="source_gap",
        comparison_state="incomplete",
        handoff_state="not_published",
    )
    path.write_text("{}")
    assert (
        generation.inspect(
            c,
            family="holding_vote",
            day="2026-10-12",
            payload=payload,
            data_root=tmp_path,
        )["status"]
        == "unverified"
    )
    first = dict(
        stage="policy_generation",
        scope="holding_vote",
        source_date="2026-10-12",
        reason="selection_missing",
        source_generation=c["source_generation"],
        code_sha256=c["code_sha256"],
        artifact="native.json",
        generation="report-1",
    )
    second = dict(first, generation="report-2")
    assert incidents.fingerprint(first) == incidents.fingerprint(second)
    assert incidents.bound_observation(
        {"policy_generation_observation": [{"family": "unbound"}]}, first, "2026-10-12"
    ) == ({}, False)


def test_native_observation_requires_matching_source_code_and_scope(tmp_path):
    root = tmp_path / "repo"
    data = root / "data"
    attest(data, "rising_missed")
    report = dict(date="2026-10-12", status="valid_empty")
    report["policy_generation"] = generation.native(
        report,
        family="rising_missed",
        day="2026-10-12",
        data_root=data,
        source_state="valid_empty",
        comparison_state="hold_sample",
        handoff_state="not_published",
    )
    path = (
        data
        / "report/rising_missed_classifier_prior/rising_missed_classifier_prior_2026-10-12.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(report))
    observations = generation.observations(root, "2026-10-12")
    native = observations[0]
    assert native["status"] == "verified"
    incident = dict(
        stage="policy_generation",
        scope="rising_missed",
        source_date="2026-10-12",
        reason="selection_missing",
    )
    assert not incidents.closure_verified(incident, native, False)
    assert incidents.closure_verified(incident, native, True)
    assert not incidents.closure_verified(
        dict(incident, scope="auxiliary"), native, True
    )


def holding_rebinding_fixture(tmp_path, monkeypatch):
    from src.engine.scalping import holding_vote_experiment as vote
    monkeypatch.setattr(vote, 'code_sha', lambda: 'b' * 64)
    day = '2026-10-13'
    replay = dict(vote_numeric_research=dict(schema='holding_vote_numeric_research_v1',
        status='experiment_not_armed', code_sha256='a' * 64, selected_cells={}, cells={},
        allowed_runtime_apply=False, actual_profit_verified=False, parent={'values': {'min_votes': 2}}),
        cost_after_paired_ev_krw=None, allowed_runtime_apply=False)
    replay['policy_generation'] = generation.native(replay, family='holding_vote', day=day,
        data_root=tmp_path, source_state='source_gap', comparison_state='experiment_not_armed',
        handoff_state='incumbent_carried')
    original = dict(date=day, meta={'snapshot_profile': 'postclose_exit'}, holding_path_vote_replay=replay)
    current = copy.deepcopy(original)
    current['holding_path_vote_replay']['vote_numeric_research']['code_sha256'] = 'b' * 64
    original_path = tmp_path / 'original.json'
    original_path.write_text(json.dumps(original))
    path = tmp_path / 'report/monitor_snapshots' / f'holding_exit_observation_{day}.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(current))
    return day, original_path, path


def test_unarmed_code_rebinding_preserves_snapshot_and_never_verifies_fixture(tmp_path, monkeypatch):
    day, original, path = holding_rebinding_fixture(tmp_path, monkeypatch)
    before = path.read_bytes()
    assert generation.observations(tmp_path.parent, day, data_root=tmp_path)[0]['reason'] == 'policy_generation_native_generation_mismatch'
    receipt = generation.publish_holding_code_rebinding(day, original_path=original, data_root=tmp_path)
    observed = generation.observations(tmp_path.parent, day, data_root=tmp_path)[0]
    assert path.read_bytes() == before
    assert observed['status'] == 'unverified' and observed['native_validated'] is False
    assert observed['findings'] == ['policy_generation_unverified']
    assert observed['source_state'] == 'source_gap' and observed['realized_profit'] is None
    assert observed['allowed_runtime_apply'] is False
    assert observed['binding_repair']['sha256'] == receipt['sha256']
    assert generation.publish_holding_code_rebinding(day, original_path=original, data_root=tmp_path) == receipt


def test_rebinding_remains_historical_unverified_after_code_deployment(tmp_path, monkeypatch):
    from src.engine.scalping import holding_vote_experiment as vote
    day, original, path = holding_rebinding_fixture(tmp_path, monkeypatch)
    reference = generation.publish_holding_code_rebinding(day, original_path=original, data_root=tmp_path)
    before = path.read_bytes(), Path(reference['path']).read_bytes()
    observed_before = generation.observations(tmp_path.parent, day, data_root=tmp_path)[0]
    monkeypatch.setattr(vote, 'code_sha', lambda: 'c'*64)
    monkeypatch.setattr(generation, 'code_generation', lambda family: 'd'*64)
    observed = generation.observations(tmp_path.parent, day, data_root=tmp_path)[0]
    assert observed['status']=='unverified' and observed['observation_complete'] is True
    assert observed['native_validated'] is False and observed['allowed_runtime_apply'] is False
    assert observed['code_sha256']==observed_before['code_sha256'] != 'd'*64
    assert observed['findings']==['policy_generation_unverified']
    assert before == (path.read_bytes(), Path(reference['path']).read_bytes())
    # Reading old custody does not authorize re-publication under new code.
    with pytest.raises(ValueError, match='not_unarmed_code_only'):
        generation.publish_holding_code_rebinding(day, original_path=original, data_root=tmp_path)


@pytest.mark.parametrize('change', ['selected', 'armed', 'profit', 'parent', 'meta', 'unknown_code', 'unsealed_original'])
def test_unarmed_code_rebinding_rejects_source_economics_or_policy_changes(tmp_path, monkeypatch, change):
    day, original, path = holding_rebinding_fixture(tmp_path, monkeypatch)
    current = json.loads(path.read_text())
    numeric = current['holding_path_vote_replay']['vote_numeric_research']
    if change == 'selected': numeric['selected_cells'] = {'cell': {'value': 1}}
    elif change == 'armed': numeric['status'] = 'selected'
    elif change == 'profit': current['holding_path_vote_replay']['cost_after_paired_ev_krw'] = 0
    elif change == 'parent': numeric['parent']['values']['min_votes'] = 1
    elif change == 'meta': current['meta']['snapshot_profile'] = 'full'
    elif change == 'unknown_code': numeric['code_sha256'] = 'c' * 64
    else:
        previous = json.loads(original.read_text())
        previous['holding_path_vote_replay']['vote_numeric_research']['parent']['values']['min_votes'] = 3
        original.write_text(json.dumps(previous))
    path.write_text(json.dumps(current))
    with pytest.raises(ValueError):
        generation.publish_holding_code_rebinding(day, original_path=original, data_root=tmp_path)


@pytest.mark.parametrize('change', ['seal', 'runtime', 'contract', 'symlink', 'source_changed', 'fixture'])
@pytest.mark.parametrize('code_advanced', [False, True])
def test_rebinding_reader_fails_closed_for_changed_or_unsafe_receipts(tmp_path, monkeypatch, change, code_advanced):
    from pathlib import Path
    day, original, source = holding_rebinding_fixture(tmp_path, monkeypatch)
    reference = generation.publish_holding_code_rebinding(day, original_path=original, data_root=tmp_path)
    if code_advanced:
        from src.engine.scalping import holding_vote_experiment as vote
        monkeypatch.setattr(vote, 'code_sha', lambda: 'c'*64)
        monkeypatch.setattr(generation, 'code_generation', lambda family: 'd'*64)
    path = Path(reference['path'])
    if change == 'symlink':
        moved = path.with_suffix('.original')
        path.rename(moved)
        path.symlink_to(moved)
    elif change == 'source_changed':
        current = json.loads(source.read_text())
        current['holding_path_vote_replay']['cost_after_paired_ev_krw'] = 0
        source.write_text(json.dumps(current))
    else:
        body = json.loads(path.read_text())
        if change == 'seal': body['receipt_sha256'] = '0' * 64
        elif change == 'runtime': body['runtime_effect'] = True
        elif change == 'fixture':
            body['contract']['fixture_receipt'] = {'path': '/unreviewed', 'sha256': 'e'*64}
            body['contract']['contract_sha256'] = generation.digest({k:v for k,v in body['contract'].items() if k!='contract_sha256'})
        else: body['contract']['source_state'] = 'complete'
        if change != 'seal': body['receipt_sha256'] = generation.digest({k:v for k,v in body.items() if k != 'receipt_sha256'})
        path.write_text(json.dumps(body))
    observed = generation.observations(tmp_path.parent, day, data_root=tmp_path)[0]
    assert observed['status'] == 'unobservable' and observed['native_validated'] is False
    assert observed['findings'] == ['policy_generation_contract_invalid']
