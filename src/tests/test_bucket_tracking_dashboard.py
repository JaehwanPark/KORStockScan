import json
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_bucket_reports(root: Path, target_date: str = "2026-05-22") -> None:
    _write_json(
        root / "report" / "lifecycle_decision_matrix" / f"lifecycle_decision_matrix_{target_date}.json",
        {
            "date": target_date,
            "entry_bucket_attribution": {"summary": {"bucket_count": 2}},
            "scale_in_bucket_attribution": {"summary": {"bucket_count": 3}},
            "overnight_bucket_attribution": {"summary": {"bucket_count": 1}},
        },
    )
    _write_json(
        root / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target_date}.json",
        {
            "date": target_date,
            "summary": {
                "surfaced_candidate_count": 2,
                "sim_auto_approved_count": 1,
                "live_auto_apply_ready_count": 1,
                "code_patch_required_count": 0,
                "human_intervention_required": False,
                "ai_two_pass_review_status": "parsed",
                "source_contract_status": "pass",
            },
            "candidates": [
                {
                    "bucket_id": "entry:source_stage:wait6579_ev_cohort",
                    "stage": "entry",
                    "bucket_type": "source_stage",
                    "bucket_key": "wait6579_ev_cohort",
                    "classification_state": "sim_auto_approved",
                    "recommended_route": "candidate_recovery_or_relax",
                    "sample": 16,
                    "joined_sample": 16,
                    "source_quality_adjusted_ev_pct": 3.45,
                    "source_quality_gate": "pass",
                },
                {
                    "bucket_id": "entry:combo_entry_spot:score_66_69",
                    "stage": "entry",
                    "bucket_type": "combo_entry_spot",
                    "bucket_key": "score=score_66_69",
                    "classification_state": "live_auto_apply_ready",
                    "live_auto_apply_family": "entry_wait6579_score66_69_recovery_gate_v1",
                    "recommended_route": "candidate_recovery_or_relax",
                    "sample": 30,
                    "joined_sample": 28,
                    "source_quality_adjusted_ev_pct": 1.23,
                    "source_quality_gate": "pass",
                },
            ],
        },
    )
    _write_json(
        root / "report" / "runtime_apply_bridge" / f"runtime_apply_bridge_{target_date}.json",
        {
            "date": target_date,
            "status": "pass",
            "summary": {
                "candidate_count": 1,
                "live_auto_apply_ready_count": 1,
                "human_approval_required": False,
            },
            "candidates": [
                {
                    "candidate_id": "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22",
                    "family": "entry_wait6579_score66_69_recovery_gate_v1",
                    "stage": "entry",
                    "bridge_candidate_state": "live_auto_apply_ready",
                    "allowed_runtime_apply": True,
                    "live_auto_apply": True,
                    "approval_required": False,
                    "source_bucket_keys": ["score=score_66_69"],
                    "lifecycle_bucket_discovery_bucket_id": "entry:combo_entry_spot:score_66_69",
                    "runtime_effect_after_approval": "bounded_entry_probe_recovery_live_auto",
                    "rolling_confirmation": {"lifecycle_bucket_discovery_gate": "pass"},
                }
            ],
        },
    )


def test_bucket_tracking_api_returns_summary_timeline_buckets_and_missing(monkeypatch, tmp_path):
    import src.web.bucket_tracking_routes as routes

    monkeypatch.setattr(routes, "DATA_DIR", tmp_path)
    _seed_bucket_reports(tmp_path)

    model = routes.build_bucket_tracking_view_model(
        target_date="2026-05-22",
        days=2,
        stage_filter="all",
        state_filter="all",
        top=50,
    )

    assert model["summary"]["ldm_source_bucket_count"] == 6
    assert model["summary"]["surfaced_count"] == 2
    assert model["summary"]["sim_auto_approved_count"] == 1
    assert model["summary"]["live_auto_apply_ready_count"] == 1
    assert model["summary"]["mode"] == "current_date_with_history"
    assert model["timeline"]
    assert model["buckets"]
    assert model["groups"]
    assert {"date": "2026-05-21", "missing": [
        "lifecycle_bucket_discovery",
        "runtime_apply_bridge",
        "lifecycle_decision_matrix",
    ]} in model["missing_dates"]


def test_bucket_tracking_routes_and_dashboard_replace_ipo(monkeypatch, tmp_path):
    import src.web.bucket_tracking_routes as routes
    import src.web.app as web_app

    monkeypatch.setattr(routes, "DATA_DIR", tmp_path)
    _seed_bucket_reports(tmp_path)

    with web_app.app.test_client() as client:
        dashboard = client.get("/dashboard?tab=bucket-tracking&date=2026-05-22")
        assert dashboard.status_code == 200
        html = dashboard.data.decode("utf-8")
        assert "버킷 추적" in html
        assert "/bucket-tracking?date=2026-05-22" in html
        assert "IPO 1~2일차" not in html
        assert "/ipo-intraday" not in html

        fallback = client.get("/dashboard?tab=ipo-intraday&date=2026-05-22")
        assert fallback.status_code == 200
        fallback_html = fallback.data.decode("utf-8")
        assert "현재 보고 있는 탭: 일일 전략 리포트" in fallback_html
        assert "IPO 1~2일차" not in fallback_html

        page = client.get("/bucket-tracking?date=2026-05-22&days=1")
        assert page.status_code == 200
        page_html = page.data.decode("utf-8")
        assert "버킷 추적 대시보드" in page_html
        assert "현재 버킷 그룹" in page_html
        assert "현재 상세 버킷" in page_html
        assert "sim_auto_approved" in page_html
        assert "live_auto_apply_ready" in page_html

        api = client.get("/api/bucket-tracking?date=2026-05-22&days=1")
        assert api.status_code == 200
        data = api.get_json()
        assert set(["summary", "timeline", "groups", "buckets", "missing_dates"]).issubset(data)
        assert data["summary"]["current_date"] == "2026-05-22"

        removed = client.get("/ipo-intraday")
        assert removed.status_code == 404
