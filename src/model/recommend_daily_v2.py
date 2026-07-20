import json
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from .common_v2 import (
        META_MODEL_PATH,
        RECO_PATH,
        RECO_DIAGNOSTIC_PATH,
        RECO_DIAGNOSTIC_JSON_PATH,
        META_FEATURES,
        SWING_SELECTION_OWNER,
        SWING_FLOOR_BULL,
        SWING_FLOOR_BEAR,
        SWING_FALLBACK_FLOOR_BULL,
        SWING_SELECTION_TOP_K,
        get_top_kospi_codes,
        get_latest_quote_date,
        select_daily_candidates,
        daily_selection_stats,
        load_model_artifact,
        build_base_score_frame,
        resolve_bull_specialist_mode,
    )
    from .dataset_builder_v2 import build_panel_dataset
except ImportError:
    from common_v2 import (
        META_MODEL_PATH,
        RECO_PATH,
        RECO_DIAGNOSTIC_PATH,
        RECO_DIAGNOSTIC_JSON_PATH,
        META_FEATURES,
        SWING_SELECTION_OWNER,
        SWING_FLOOR_BULL,
        SWING_FLOOR_BEAR,
        SWING_FALLBACK_FLOOR_BULL,
        SWING_SELECTION_TOP_K,
        get_top_kospi_codes,
        get_latest_quote_date,
        select_daily_candidates,
        daily_selection_stats,
        load_model_artifact,
        build_base_score_frame,
        resolve_bull_specialist_mode,
    )
    from dataset_builder_v2 import build_panel_dataset


def _attach_recommendation_provenance(score_df, stats_df):
    out = score_df.copy()
    out["meta_score"] = out["score"]
    out["score_rank"] = (
        out.groupby("date")["meta_score"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    if not stats_df.empty:
        merge_cols = ["date", "floor_used", "safe_pool_count", "candidate_count"]
        out = out.merge(stats_df[merge_cols], on="date", how="left")
    else:
        out["floor_used"] = 0.0
        out["safe_pool_count"] = 0
        out["candidate_count"] = len(out)

    out["selection_owner"] = SWING_SELECTION_OWNER
    out["generated_at"] = datetime.now().isoformat(timespec="seconds")
    return out


def _save_recommendation_outputs(score_df, picks, stats_df, latest_date, *, bull_mode):
    score_df = _attach_recommendation_provenance(score_df, stats_df)
    selected_index = pd.MultiIndex.from_arrays([[], []], names=["date", "code"])
    if not picks.empty:
        selected_index = pd.MultiIndex.from_frame(picks[["date", "code"]])

    diagnostic = score_df.copy()
    diagnostic_index = pd.MultiIndex.from_frame(diagnostic[["date", "code"]])
    diagnostic["selection_mode"] = "DIAGNOSTIC_ONLY"
    diagnostic.loc[diagnostic_index.isin(selected_index), "selection_mode"] = "SELECTED"

    if picks.empty:
        diagnostic = (
            diagnostic.sort_values("meta_score", ascending=False).head(10).copy()
        )
        diagnostic["selection_mode"] = "FALLBACK_DIAGNOSTIC"
        empty_reco = score_df.iloc[0:0].copy()
        empty_reco["selection_mode"] = pd.Series(dtype="object")
        empty_reco.to_csv(RECO_PATH, index=False, encoding="utf-8-sig")
        selection_mode = "EMPTY"
    else:
        score_index = pd.MultiIndex.from_frame(score_df[["date", "code"]])
        pick_df = score_df[score_index.isin(selected_index)].copy()
        pick_df["selection_mode"] = "SELECTED"
        pick_df = pick_df.sort_values("meta_score", ascending=False).reset_index(
            drop=True
        )
        pick_df.to_csv(RECO_PATH, index=False, encoding="utf-8-sig")
        selection_mode = "SELECTED"

    diagnostic = diagnostic.sort_values(
        ["date", "meta_score"], ascending=[True, False]
    ).reset_index(drop=True)
    diagnostic.to_csv(RECO_DIAGNOSTIC_PATH, index=False, encoding="utf-8-sig")

    latest_stats = {}
    if not stats_df.empty:
        latest_stats = stats_df.iloc[-1].to_dict()
    summary = {
        "owner": SWING_SELECTION_OWNER,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "latest_date": str(pd.to_datetime(latest_date).date()),
        "selection_mode": selection_mode,
        "recommendation_path": RECO_PATH,
        "diagnostic_path": RECO_DIAGNOSTIC_PATH,
        "fallback_written_to_recommendations": False,
        "selected_count": int(len(picks)),
        "diagnostic_count": int(len(diagnostic)),
        "floor_bull": SWING_FLOOR_BULL,
        "floor_bear": SWING_FLOOR_BEAR,
        "fallback_floor_bull": SWING_FALLBACK_FLOOR_BULL,
        "selection_top_k": SWING_SELECTION_TOP_K,
        "bull_specialist_mode": bull_mode,
        "bull_score_source": (
            str(score_df["bull_score_source"].iloc[0])
            if "bull_score_source" in score_df.columns and not score_df.empty
            else ""
        ),
        "bull_artifact_used": (
            bool(score_df["bull_artifact_used"].iloc[0])
            if "bull_artifact_used" in score_df.columns and not score_df.empty
            else False
        ),
        "latest_stats": latest_stats,
        "score_distribution": {
            "hybrid_mean_max": (
                float(score_df["hybrid_mean"].max()) if not score_df.empty else 0.0
            ),
            "hybrid_mean_p95": (
                float(score_df["hybrid_mean"].quantile(0.95))
                if not score_df.empty
                else 0.0
            ),
            "meta_score_max": (
                float(score_df["meta_score"].max()) if not score_df.empty else 0.0
            ),
            "meta_score_p95": (
                float(score_df["meta_score"].quantile(0.95))
                if not score_df.empty
                else 0.0
            ),
        },
    }
    with open(RECO_DIAGNOSTIC_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)

    return summary


def recommend_daily_v2(bull_mode=None):
    bull_mode = resolve_bull_specialist_mode(bull_mode)
    latest_date = get_latest_quote_date()
    start_date = (latest_date - pd.Timedelta(days=400)).strftime("%Y-%m-%d")
    end_date = latest_date.strftime("%Y-%m-%d")

    print(f"[1/4] 최신 추천용 패널 생성 중... ({start_date} ~ {end_date})")
    codes = get_top_kospi_codes(limit=300)
    panel = build_panel_dataset(
        codes, start_date, end_date, min_rows=120, include_labels=False
    )
    if panel.empty:
        print("❌ 최신 패널 생성 실패")
        return

    latest_rows = panel[panel["date"] == latest_date].copy()
    if latest_rows.empty:
        print("❌ 최신 거래일 데이터가 없습니다.")
        return

    print(f"[2/4] 모델 로드 및 base score 생성 중... (bull_mode={bull_mode})")
    meta_artifact = load_model_artifact(META_MODEL_PATH)

    score_df = build_base_score_frame(
        latest_rows,
        bull_mode=bull_mode,
        include_columns=[
            "date",
            "code",
            "name",
            "close",
            "bull_regime",
            "idx_ret20",
            "idx_atr_ratio",
        ],
    )

    # recommend_daily_v2.py 내부 [3/4] 단계 부분 교체

    print("[3/4] Meta score (Ranker) 생성 중...")
    # Ranker는 확률이 아니므로 predict_proba 대신 predict를 사용하고 클리핑을 생략합니다.
    score_df["score"] = meta_artifact["model"].predict(score_df[META_FEATURES])

    # 새로 정의된 투트랙 필터링 적용 (hybrid_mean이 1차 안전망 역할)
    picks = select_daily_candidates(
        score_df,
        score_col="score",
        prob_col="hybrid_mean",
        floor_bull=SWING_FLOOR_BULL,
        floor_bear=SWING_FLOOR_BEAR,
        fallback_floor=SWING_FALLBACK_FLOOR_BULL,
        top_k_bull=SWING_SELECTION_TOP_K,
        top_k_bear=max(1, min(SWING_SELECTION_TOP_K, 2)),
    )
    stats_df = daily_selection_stats(
        score_df,
        prob_col="hybrid_mean",
        floor_bull=SWING_FLOOR_BULL,
        floor_bear=SWING_FLOOR_BEAR,
        fallback_floor=SWING_FALLBACK_FLOOR_BULL,
    )
    summary = _save_recommendation_outputs(
        score_df, picks, stats_df, latest_date, bull_mode=bull_mode
    )

    if picks.empty:
        print("⚠️ 오늘 추천 종목이 없습니다 (안전망 통과 종목 0건).")
        print(f"진단용 fallback만 저장: {RECO_DIAGNOSTIC_PATH}")
        print(f"정식 추천 CSV는 빈 상태로 저장: {RECO_PATH}")
        return

    picks = picks.sort_values("score", ascending=False).reset_index(drop=True)

    print("[4/4] 오늘의 추천 종목")
    print(
        picks[
            ["date", "code", "name", "score", "hx", "hl", "bx", "bl", "bull_regime"]
        ].to_string(index=False)
    )
    print(
        f"\n✅ 저장 완료: {RECO_PATH} (selected={summary['selected_count']}, floor={summary['latest_stats'].get('floor_used')})"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate swing v2 daily recommendations."
    )
    parser.add_argument(
        "--bull-mode", default=None, choices=["enabled", "disabled", "hold_current"]
    )
    args = parser.parse_args()
    recommend_daily_v2(bull_mode=args.bull_mode)
