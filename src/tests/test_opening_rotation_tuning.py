"""Permanent retirement supersedes historical tuning/publishing acceptance."""
import json
from dataclasses import replace
import pytest
from src.engine.scalping.opening_rotation import OpeningRotationRuntimePolicy,load_runtime_policy
from src.engine.scalping import opening_rotation_tuning as mod

@pytest.mark.parametrize("name",["build_postclose_report","write_postclose","apply_preopen","verify_artifacts"])
def test_retired_entrypoints_cannot_read_write_or_select(name,monkeypatch,tmp_path):
    def forbidden(*args,**kwargs):raise AssertionError("retired producer performed I/O")
    monkeypatch.setattr(type(tmp_path),"read_text",forbidden)
    monkeypatch.setattr(type(tmp_path),"write_text",forbidden)
    result=getattr(mod,name)("2026-10-12")
    assert result["status"]=="retired"
    assert result["allowed_runtime_apply"] is False

def test_runtime_loader_rejects_non_tunable_profile_mutation(tmp_path):
    baseline = OpeningRotationRuntimePolicy(target_date="2026-08-09")
    tampered = replace(
        baseline,
        entry=replace(baseline.entry, min_buy_pressure_pct=55.0),
    )
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(tampered.as_artifact()), encoding="utf-8")

    with pytest.raises(ValueError, match="non-tunable entry field"):
        load_runtime_policy(path)
