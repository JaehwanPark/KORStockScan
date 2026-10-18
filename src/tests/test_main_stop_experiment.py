"""Stop experiment producers keep historical study and future promotion apart."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json

import pytest

from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping import main_stop_experiment as experiment
from src.engine.scalping.main_stop_policy import StopValues, digest
from src.engine.scalping.main_stop_replay import candidates


def parameters():
    parent = StopValues(-3.0, 60, 20, 8, 3, .67, 1.0, -5.0, -4.0, -2.0, -.3)
    grid = {name: asdict(value) for name, value in candidates(parent).items()
            if name == "parent" or name.startswith("grace_sec:")}
    return dict(parent_sha256=digest(asdict(parent)), code_sha256="c" * 64,
                operator_lock_sha256="a" * 64, allowed_keys=["grace_sec"],
                max_daily_change={"grace_sec": 60}, split_at=2000., embargo_sec=60.,
                min_train=2, min_holdout=2, minimum_paired_ev_krw=0.,
                max_censoring_ratio=.2, max_standard_error_krw=100.,
                candidate_grid=grid, source_start_at=100., source_end_at=3000.,
                hypothesis="Compare a fixed soft stop with shorter grace.")


def register(tmp_path, monkeypatch, *, mode="prospective", at=1000., **changes):
    monkeypatch.setattr(experiment.time, "time", lambda: at)
    p = parameters()
    p.update(changes)
    ref = experiment.register_experiment(tmp_path / "registry", experiment_id="grace-study",
                                        revision=1, cell="SCANNER|REGULAR", parameters=p, mode=mode)
    return ref, p


def source(tmp_path):
    path = tmp_path / "source.jsonl"
    path.write_text('{"at":200.0}\n{"at":2700.0}\n')
    return {str(path): byte_generation(path)}


def performance(tmp_path, inventory, *, mode="prospective"):
    # This is a gate fixture, not a claim that unit tests measured Main latency.
    body = dict(schema="main_stop_performance_v1", code_sha256="c" * 64,
                status="pass", scope="runtime_and_postclose", unresolved_findings=[])
    if mode == "historical_report_only":
        body.update(status="measured", scope="offline_research_and_pure_decisions",
                    source_sha256=digest(inventory), allowed_runtime_apply=False,
                    metrics={"replayed_positions": 4, "wall_seconds": .05},
                    unresolved_findings=["live_capture_latency_not_measured"])
    path = tmp_path / "performance.json"
    path.write_text(json.dumps(body, sort_keys=True))
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def isolate_legacy_performance_gate(monkeypatch):
    """Only legacy artifact/downstream contract tests use this explicit seam.

    The archived v1 label fixture is not native full-performance evidence. Keep
    its original validator semantics while testing unrelated immutable/source
    contracts. Separate strict authority tests never install this isolation.
    """
    verify=experiment._verify_performance
    def legacy(reference,code_sha,*,mode,source_sha,require_native=False):
        return verify(reference,code_sha,mode=mode,source_sha=source_sha,require_native=False)
    monkeypatch.setattr(experiment,'_verify_performance',legacy)


def finalize(tmp_path, monkeypatch, ref, *, mode="prospective", at=3500.,isolate_native_gate=True):
    monkeypatch.setattr(experiment.time, "time", lambda: at)
    inventory = source(tmp_path)
    measured = performance(tmp_path, inventory, mode=mode)
    if mode=='prospective' and isolate_native_gate:isolate_legacy_performance_gate(monkeypatch)
    c = experiment.finalize_experiment(tmp_path / "registry", ref,
        source_inventory=inventory, performance_receipt=measured,
        observed_start_at=200., observed_end_at=2700.)
    return c, inventory


def validate(contract, inventory, *, promote=True):
    return experiment.validate_experiment_v2(contract,
        parent_sha=parameters()["parent_sha256"], source_sha=digest(inventory),
        code_sha="c" * 64, require_promotion=promote)


def test_producers_freeze_before_source_then_finalize_without_rewriting(tmp_path, monkeypatch):
    ref, _ = register(tmp_path, monkeypatch)
    prereg_path = tmp_path / "registry/grace-study/preregistration_1.json"
    frozen = prereg_path.read_bytes()
    prereg = json.loads(frozen)
    assert prereg["frozen_at"] == 1000.
    assert "source_sha256" not in prereg and "source_sha256" not in prereg["parameters"]
    assert not list(tmp_path.rglob("source_seal_*.json"))
    contract, inventory = finalize(tmp_path, monkeypatch, ref)
    assert prereg_path.read_bytes() == frozen
    assert contract["schema"] == "main_stop_experiment_v2"
    assert contract["frozen_at"] == 1000.
    assert contract["source_sha256"] == digest(inventory)
    assert validate(contract, inventory) == contract
    assert len(list(tmp_path.rglob("experiment_1_*.json"))) == 1


def test_source_seal_and_research_preparation_exist_before_any_performance_contract(tmp_path,monkeypatch):
    ref,p=register(tmp_path,monkeypatch,selection_cost_grade='broker_total_allocated')
    monkeypatch.setattr(experiment.time,'time',lambda:3500.)
    inventory=source(tmp_path)
    sealed=experiment.seal_experiment_sources(tmp_path/'registry',ref,source_inventory=inventory,
        observed_start_at=200.,observed_end_at=2700.)
    prepared=experiment.prepare_experiment(ref,sealed)
    assert prepared['schema']=='main_stop_experiment_preparation_v1'
    assert 'performance_receipt' not in prepared and prepared['allowed_runtime_apply'] is False
    assert not list(tmp_path.rglob('experiment_1_*.json'))
    with pytest.raises(ValueError,match='binding_invalid'):
        validate(prepared,inventory)
    # A performance gate failure preserves real source evidence, never a final
    # runtime contract. Later measurement can bind this exact same source seal.
    with pytest.raises(ValueError,match='native_producer_required'):
        experiment.finalize_experiment(tmp_path/'registry',ref,source_inventory=inventory,
            performance_receipt=performance(tmp_path,inventory),observed_start_at=200.,observed_end_at=2700.)
    assert experiment.prepare_experiment(ref,sealed)==prepared
    assert not list(tmp_path.rglob('experiment_1_*.json'))


def test_historical_study_uses_real_freeze_time_and_never_promotes(tmp_path, monkeypatch):
    ref, _ = register(tmp_path, monkeypatch, mode="historical_report_only", at=3500.)
    contract, inventory = finalize(tmp_path, monkeypatch, ref, mode="historical_report_only")
    assert contract["frozen_at"] == 3500. > contract["source_end_at"]
    assert contract["allowed_runtime_apply"] is False
    assert validate(contract, inventory, promote=False) == contract
    with pytest.raises(ValueError, match="historical_experiment_report_only"):
        validate(contract, inventory)


def test_cost_grade_is_frozen_without_pooling_or_promoting_legacy_performance(tmp_path,monkeypatch):
    ref,p=register(tmp_path,monkeypatch,selection_cost_grade='broker_total_allocated')
    original=json.loads(__import__('pathlib').Path(ref['path']).read_text())
    assert original['parameters']['selection_cost_grade']=='broker_total_allocated'
    with pytest.raises(ValueError,match='native_producer_required'):
        finalize(tmp_path,monkeypatch,ref,isolate_native_gate=False)
    # Revision conflict persists even if a different grade has more samples.
    monkeypatch.setattr(experiment.time,'time',lambda:1001.)
    p['selection_cost_grade']='exact_execution'
    with pytest.raises(ValueError,match='revision_conflict'):
        experiment.register_experiment(tmp_path/'registry',experiment_id='grace-study',
            revision=1,cell='SCANNER|REGULAR',parameters=p)


@pytest.mark.parametrize('grade',[None,'exact_execution','broker_total_allocated'])
def test_new_prospective_finalization_requires_native_performance_even_without_cost_grade(tmp_path,monkeypatch,grade):
    changes={} if grade is None else {'selection_cost_grade':grade}
    ref,_=register(tmp_path,monkeypatch,**changes)
    with pytest.raises(ValueError,match='native_producer_required'):
        finalize(tmp_path,monkeypatch,ref,isolate_native_gate=False)
    assert list(tmp_path.rglob('source_seal_*.json'))
    assert not list(tmp_path.rglob('experiment_1_*.json'))


@pytest.mark.parametrize('grade',['mixed','actual','exact_execution+broker_total_allocated',None])
def test_unregistered_or_pooled_cost_grade_is_not_accepted(tmp_path,monkeypatch,grade):
    with pytest.raises(ValueError,match='cost_grade_invalid'):
        register(tmp_path,monkeypatch,selection_cost_grade=grade)


@pytest.mark.parametrize("forbidden", ["frozen_at", "source_sha256", "performance_receipt", "allowed_runtime_apply"])
def test_registration_cannot_backdate_or_inject_finalization(tmp_path, monkeypatch, forbidden):
    with pytest.raises(ValueError, match="parameters_invalid"):
        register(tmp_path, monkeypatch, **{forbidden: 1})
    assert not list(tmp_path.rglob("preregistration_*.json"))


def test_registration_after_holdout_cannot_claim_prospective(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="not_frozen_before_holdout"):
        register(tmp_path, monkeypatch, at=1950.)
    with pytest.raises(ValueError, match="historical_source_window_in_future"):
        register(tmp_path, monkeypatch, at=1000., mode="historical_report_only")


def test_same_revision_is_immutable_and_retry_keeps_original_time(tmp_path, monkeypatch):
    first, p = register(tmp_path, monkeypatch)
    monkeypatch.setattr(experiment.time, "time", lambda: 4000.)
    again = experiment.register_experiment(tmp_path / "registry", experiment_id="grace-study",
        revision=1, cell="SCANNER|REGULAR", parameters=p)
    assert again == first
    changed = dict(p, hypothesis="A different hypothesis.")
    with pytest.raises(ValueError, match="revision_conflict"):
        experiment.register_experiment(tmp_path / "registry", experiment_id="grace-study",
            revision=1, cell="SCANNER|REGULAR", parameters=changed)
    monkeypatch.setattr(experiment.time, "time", lambda: 1100.)
    second = experiment.register_experiment(tmp_path / "registry", experiment_id="grace-study",
        revision=2, cell="SCANNER|REGULAR", parameters=changed)
    assert second["path"] != first["path"]
    assert json.loads(open(first["path"]).read())["parameters"]["hypothesis"] == p["hypothesis"]


@pytest.mark.parametrize("change", ["grid", "parent", "safety", "empty_allowed", "bad_key"])
def test_registration_rejects_grid_drift_and_safety_axes(tmp_path, monkeypatch, change):
    p = parameters()
    if change == "grid":
        del p["candidate_grid"]["grace_sec:0"]
    elif change == "parent":
        p["parent_sha256"] = "d" * 64
    elif change == "safety":
        p["candidate_grid"]["grace_sec:0"]["hard_stop_pct"] = -6.
    elif change == "empty_allowed":
        p["allowed_keys"] = []
    else:
        p["allowed_keys"] = ["hard_stop_pct"]
    monkeypatch.setattr(experiment.time, "time", lambda: 1000.)
    with pytest.raises(ValueError):
        experiment.register_experiment(tmp_path, experiment_id="grace", revision=1,
            cell="SCANNER|REGULAR", parameters=p)


@pytest.mark.parametrize("now,first,last", [(2999., 200., 2700.), (3500., 99., 2700.),
                                            (3500., 200., 3001.), (3500., 2700., 200.)])
def test_finalization_rejects_future_or_out_of_window_source(tmp_path, monkeypatch, now, first, last):
    ref, _ = register(tmp_path, monkeypatch)
    inventory = source(tmp_path)
    measured = performance(tmp_path, inventory)
    monkeypatch.setattr(experiment.time, "time", lambda: now)
    with pytest.raises(ValueError, match="source_window_invalid"):
        experiment.finalize_experiment(tmp_path / "registry", ref, source_inventory=inventory,
            performance_receipt=measured, observed_start_at=first, observed_end_at=last)
    assert not list(tmp_path.rglob("source_seal_*.json"))


@pytest.mark.parametrize("target", ["preregistration", "source", "performance", "seal"])
def test_changed_dependency_invalidates_validation(tmp_path, monkeypatch, target):
    ref, _ = register(tmp_path, monkeypatch)
    contract, inventory = finalize(tmp_path, monkeypatch, ref)
    path = {"preregistration": ref["path"], "source": next(iter(inventory)),
            "performance": contract["performance_receipt"]["path"],
            "seal": contract["source_seal"]["path"]}[target]
    with open(path, "a") as handle:
        handle.write(" ")
    with pytest.raises(ValueError):
        validate(contract, inventory)


@pytest.mark.parametrize("field,value", [("min_train", 20), ("mode", "historical_report_only"),
                                        ("frozen_at", 900.), ("allowed_runtime_apply", True)])
def test_resealed_contract_cannot_change_preregistration(tmp_path, monkeypatch, field, value):
    ref, _ = register(tmp_path, monkeypatch)
    contract, inventory = finalize(tmp_path, monkeypatch, ref)
    changed = deepcopy(contract)
    changed[field] = value
    changed["experiment_sha256"] = digest({k: v for k, v in changed.items() if k != "experiment_sha256"})
    with pytest.raises(ValueError):
        validate(changed, inventory, promote=False)


def test_historical_measurement_cannot_satisfy_prospective_gate(tmp_path, monkeypatch):
    ref, _ = register(tmp_path, monkeypatch)
    inventory = source(tmp_path)
    measured = performance(tmp_path, inventory, mode="historical_report_only")
    monkeypatch.setattr(experiment.time, "time", lambda: 3500.)
    with pytest.raises(ValueError, match="native_producer_required"):
        experiment.finalize_experiment(tmp_path / "registry", ref, source_inventory=inventory,
            performance_receipt=measured, observed_start_at=200., observed_end_at=2700.)


def test_repeated_finalization_returns_original_seal_without_rewriting(tmp_path, monkeypatch):
    ref, _ = register(tmp_path, monkeypatch)
    contract, inventory = finalize(tmp_path, monkeypatch, ref)
    monkeypatch.setattr(experiment.time, "time", lambda: 4000.)
    again = experiment.finalize_experiment(tmp_path / "registry", ref, source_inventory=inventory,
        performance_receipt=contract["performance_receipt"], observed_start_at=200., observed_end_at=2700.)
    assert again == contract


def test_source_correction_creates_new_seal_and_preserves_preregistration(tmp_path, monkeypatch):
    ref, _ = register(tmp_path, monkeypatch)
    first, inventory = finalize(tmp_path, monkeypatch, ref)
    original_ref = deepcopy(first["source_seal"])
    path = next(iter(inventory))
    with open(path, "a") as handle:
        handle.write('{"at":2800.0}\n')
    changed = {path: byte_generation(path)}
    monkeypatch.setattr(experiment.time, "time", lambda: 4000.)
    second = experiment.finalize_experiment(tmp_path / "registry", ref,
        source_inventory=changed, performance_receipt=first["performance_receipt"],
        observed_start_at=200., observed_end_at=2800.)
    assert second["preregistration"] == first["preregistration"] == ref
    assert second["source_seal"] != original_ref
    assert second["experiment_sha256"] != first["experiment_sha256"]
    assert validate(second, changed) == second
    with pytest.raises(ValueError, match="source_generation_changed"):
        validate(first, inventory)


def test_expected_parent_code_and_source_generation_are_mandatory(tmp_path, monkeypatch):
    ref, _ = register(tmp_path, monkeypatch)
    contract, inventory = finalize(tmp_path, monkeypatch, ref)
    expected = dict(parent_sha=parameters()["parent_sha256"], source_sha=digest(inventory), code_sha="c" * 64)
    for key in expected:
        changed = dict(expected, **{key: "d" * 64})
        with pytest.raises(ValueError, match="binding_invalid"):
            experiment.validate_experiment_v2(contract, **changed)


def test_reference_symlink_and_invalid_revision_paths_are_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(experiment.time, "time", lambda: 1000.)
    with pytest.raises(ValueError, match="preregistration_invalid"):
        experiment.register_experiment(tmp_path, experiment_id="../escape", revision=1,
            cell="SCANNER|REGULAR", parameters=parameters())
    real = tmp_path / "real"
    real.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="path_invalid"):
        experiment.register_experiment(alias, experiment_id="grace", revision=1,
            cell="SCANNER|REGULAR", parameters=parameters())


def native_contract(tmp_path, monkeypatch, *, revision=1, mode='prospective', setup=None):
    from src.engine.automation import main_stop_postclose as post
    from src.engine.scalping import main_stop_policy as policy
    from src.tests.test_main_stop_policy import publication, baseline, seal
    data=tmp_path/'data'
    if setup is None:
        _, original, parent, source_path=publication(data)
        setup=(original,parent,source_path)
    original,parent,source_path=setup
    base=1791766800.
    p=parameters()
    p.update(code_sha256=post.code_sha(),operator_lock_sha256=digest([]),
        source_start_at=base,source_end_at=base+1200,split_at=base+500,
        max_censoring_ratio=0.,max_standard_error_krw=0.,hypothesis=f'Frozen native grace comparison {revision}.')
    monkeypatch.setattr(experiment.time,'time',lambda:base-100 if mode=='prospective' else base+2000)
    ref=experiment.register_experiment(tmp_path/'registry',experiment_id='native-grace',revision=revision,
        cell='SCANNER|REGULAR',parameters=p,mode=mode)
    measured=dict(schema='main_stop_performance_v1',status='pass',scope='runtime_and_postclose',
        code_sha256=p['code_sha256'],unresolved_findings=[])
    if mode=='historical_report_only':
        measured.update(status='measured',scope='offline_research_and_pure_decisions',
            allowed_runtime_apply=False,source_sha256=original['source_sha256'],
            metrics={'fixture_only':True},unresolved_findings=['live_capture_latency_not_measured'])
    performance_ref=seal(tmp_path/f'performance_{revision}.json',measured)
    monkeypatch.setattr(experiment.time,'time',lambda:base+2000)
    if mode=='prospective':isolate_legacy_performance_gate(monkeypatch)
    contract=experiment.finalize_experiment(tmp_path/'registry',ref,
        source_inventory=original['source_inventory'],performance_receipt=performance_ref,
        observed_start_at=base,observed_end_at=base+1108)
    parents={f'{role}|{market}':baseline() for role in policy.ROLES for market in policy.MARKETS}
    publication_args=dict(data_root=data,source_date='2026-10-12',target_date='2026-10-13',
        parents=parents,parent_receipt=parent)
    return contract,publication_args,setup


def test_prospective_manifest_producer_native_reader_and_publisher(tmp_path,monkeypatch):
    from src.engine.automation import main_stop_postclose as post
    contract,args,(original,parent,source_path)=native_contract(tmp_path,monkeypatch)
    output=tmp_path/'prepared/experiments_2026-10-12.json'
    receipt=experiment.publish_experiment_manifest(output,{'SCANNER|REGULAR':contract},**args)
    original_bytes=output.read_bytes()
    assert receipt['allowed_runtime_apply'] is False and receipt['target_policy_published'] is False
    assert experiment.publish_experiment_manifest(output,{'SCANNER|REGULAR':contract},**args)==receipt
    assert output.read_bytes()==original_bytes
    # This is the normal CLI's exact reader and schema, followed by its native publisher.
    loaded=post.bounded(output)[0]
    assert set(loaded)=={'SCANNER|REGULAR'}
    completed=json.loads((args['data_root']/'costs.json').read_text())['rows']
    bundle,_=post.publish(args['data_root'],args['source_date'],args['target_date'],
        parents=args['parents'],parent_receipt=parent,snapshot_receipt=original['snapshot_receipt'],
        source_paths=[source_path],experiments=loaded,completed=completed,
        economic_sources=original['economic_sources'])
    assert bundle['cells']['SCANNER|REGULAR']['status']=='selected'
    assert bundle['cells']['SCANNER|REGULAR']['values']['grace_sec']==0
    loaded['SCANNER|REGULAR']['candidate_grid']['grace_sec:0']['hard_stop_pct']=-6.
    output.write_text(json.dumps(loaded))
    with pytest.raises(ValueError,match='binding_invalid'):
        post.publish(args['data_root'],args['source_date'],args['target_date'],
            parents=args['parents'],parent_receipt=parent,snapshot_receipt=original['snapshot_receipt'],
            source_paths=[source_path],experiments=post.bounded(output)[0],completed=completed,
            economic_sources=original['economic_sources'])


def test_new_manifest_does_not_republish_legacy_performance_as_new_authority(tmp_path,monkeypatch):
    original=experiment._verify_performance
    contract,args,_=native_contract(tmp_path,monkeypatch)
    monkeypatch.setattr(experiment,'_verify_performance',original)
    output=tmp_path/'prepared/experiments_2026-10-12.json'
    with pytest.raises(ValueError,match='native_producer_required'):
        experiment.publish_experiment_manifest(output,{'SCANNER|REGULAR':contract},**args)
    assert not output.exists()


def test_manifest_replacement_requires_cas_and_preserves_original_bytes(tmp_path,monkeypatch):
    first,args,setup=native_contract(tmp_path,monkeypatch)
    output=tmp_path/'prepared/experiments_2026-10-12.json'
    receipt=experiment.publish_experiment_manifest(output,{'SCANNER|REGULAR':first},**args)
    before=output.read_bytes()
    second,_,_=native_contract(tmp_path,monkeypatch,revision=2,setup=setup)
    with pytest.raises(ValueError,match='cas_conflict'):
        experiment.publish_experiment_manifest(output,{'SCANNER|REGULAR':second},**args)
    assert output.read_bytes()==before
    changed=experiment.publish_experiment_manifest(output,{'SCANNER|REGULAR':second},**args,
        expected_sha256=receipt['sha256'])
    assert changed['sha256']!=receipt['sha256']
    archived=output.parent/'manifest_history'/output.stem/(receipt['sha256']+'.json')
    assert archived.read_bytes()==before


@pytest.mark.parametrize('fault',['historical','cell','parent','operator','multiple_cells'])
def test_manifest_does_not_bypass_native_contract_or_authority(tmp_path,monkeypatch,fault):
    contract,args,_=native_contract(tmp_path,monkeypatch,
        mode='historical_report_only' if fault=='historical' else 'prospective')
    mapping={'SCANNER|REGULAR':contract}
    if fault=='cell':mapping={'SCANNER|PREMARKET':contract}
    elif fault=='parent':args['parents']['SCANNER|REGULAR']=StopValues(-3.,30,20,8,3,.67,1.,-5.,-4.,-2.,-.3)
    elif fault=='operator':
        from src.engine.automation import operator_policy_succession
        def veto(*args,**kwargs):raise ValueError('stop_operator_veto_or_unclassified_lock')
        monkeypatch.setattr(operator_policy_succession,'stop_key_authority',veto)
    elif fault=='multiple_cells':mapping['SCANNER|PREMARKET']=contract
    output=tmp_path/'prepared/experiments_2026-10-12.json'
    with pytest.raises(ValueError):
        experiment.publish_experiment_manifest(output,mapping,**args)
    assert not output.exists()


@pytest.mark.parametrize('relative',[
    'runtime/runtime_release_selection.json',
    'threshold_cycle/main_stop_confirmation/main_stop_confirmation_policy_2026-10-13.json',
    'runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-13.json',
    'runtime/research/main_stop_confirmation/experiments_2026-10-11.json',
    'elsewhere/experiments_2026-10-12.json'])
def test_manifest_cannot_overwrite_other_live_artifact_even_with_matching_cas(tmp_path,monkeypatch,relative):
    contract,args,_=native_contract(tmp_path,monkeypatch)
    output=args['data_root']/relative
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(b'{"protected":true}\n');original=output.read_bytes()
    with pytest.raises(ValueError,match='output_scope_invalid'):
        experiment.publish_experiment_manifest(output,{'SCANNER|REGULAR':contract},**args,
            expected_sha256=hashlib.sha256(original).hexdigest())
    assert output.read_bytes()==original and not output.with_name(output.name+'.lock').exists()


def test_manifest_accepts_only_exact_native_path_inside_data_root(tmp_path,monkeypatch):
    contract,args,_=native_contract(tmp_path,monkeypatch)
    output=args['data_root']/'runtime/research/main_stop_confirmation/experiments_2026-10-12.json'
    receipt=experiment.publish_experiment_manifest(output,{'SCANNER|REGULAR':contract},**args)
    assert receipt['path']==str(output) and output.exists()
    with pytest.raises(ValueError,match='output_scope_invalid'):
        experiment.publish_experiment_manifest(tmp_path/'private/policy.json',{'SCANNER|REGULAR':contract},**args)
