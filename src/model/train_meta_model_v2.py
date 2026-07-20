import joblib
import pandas as pd
from lightgbm import LGBMRanker, early_stopping, log_evaluation

try:
    from .common_v2 import (
        META_START,
        META_END,
        META_MODEL_PATH,
        AI_PRED_PATH,
        META_FEATURES,
        get_top_kospi_codes,
        split_by_unique_dates,
        precision_at_k_by_day,
        select_daily_candidates,
        PassThroughCalibrator,
        build_base_score_frame,
        resolve_bull_specialist_mode,
    )
    from .dataset_builder_v2 import build_panel_dataset
except ImportError:
    from common_v2 import (
        META_START,
        META_END,
        META_MODEL_PATH,
        AI_PRED_PATH,
        META_FEATURES,
        get_top_kospi_codes,
        split_by_unique_dates,
        precision_at_k_by_day,
        select_daily_candidates,
        PassThroughCalibrator,
        build_base_score_frame,
        resolve_bull_specialist_mode,
    )
    from dataset_builder_v2 import build_panel_dataset


def train_meta_model_v2(meta_start=None, meta_end=None, bull_mode=None):
    meta_start = meta_start or META_START
    meta_end = meta_end or META_END
    bull_mode = resolve_bull_specialist_mode(bull_mode)
    print(
        f"[1/5] Meta 학습용 패널 생성 중... (타겟: {meta_start} ~ {meta_end}, bull_mode={bull_mode})"
    )
    codes = get_top_kospi_codes(limit=300)

    # 💡 핵심 수정: 지표 워밍업(ma120 등)을 위해 200일 이전부터 데이터를 DB에서 끌어옵니다.
    meta_start_dt = pd.to_datetime(meta_start)
    fetch_start = (meta_start_dt - pd.Timedelta(days=200)).strftime("%Y-%m-%d")

    # 패널 생성은 과거부터 넉넉히 (min_rows=150으로 안전하게)
    panel = build_panel_dataset(
        codes, fetch_start, meta_end, min_rows=150, include_labels=True
    )
    if panel.empty:
        print("❌ 메타 학습 데이터 추출 실패.")
        return

    # 💡 지표 계산이 온전히 끝난 진짜 META_START 이후 데이터만 필터링
    panel = panel[panel["date"] >= meta_start_dt].copy()

    if panel.empty:
        print("❌ 날짜 필터링 후 메타 학습 데이터가 남지 않았습니다.")
        return

    print(f"✅ 메타 패널 준비 완료: {len(panel)} rows")

    print("[2/5] Base model 로드 및 예측 피처 병합 중...")

    # atr_ratio를 함께 가져옵니다 (Risk-Adjusted Return 계산용)
    meta_df = build_base_score_frame(
        panel,
        bull_mode=bull_mode,
        include_columns=[
            "date",
            "code",
            "name",
            "bull_regime",
            "idx_ret20",
            "idx_atr_ratio",
            "target_loose",
            "target_strict",
            "realized_ret_3d",
            "atr_ratio",
        ],
    )

    print("[3/5] Cross-Sectional 타깃(Top 10%) 생성 중...")
    # 변동성 대비 3일 실현 수익률 (Risk-Adjusted Return)
    meta_df["risk_adj_ret"] = meta_df["realized_ret_3d"] / (meta_df["atr_ratio"] + 1e-9)

    # 매일(date) 기준으로 횡단면 상위 10% 종목에 1, 나머지에 0 부여
    meta_df["target_rank_pct"] = meta_df.groupby("date")["risk_adj_ret"].rank(
        pct=True, ascending=True
    )
    meta_df["target_rank_label"] = (meta_df["target_rank_pct"] >= 0.90).astype(int)

    # Ranker 모델은 반드시 Group(여기서는 date) 단위로 연속 정렬되어 있어야 합니다.
    meta_df = meta_df.sort_values(["date", "code"]).reset_index(drop=True)

    # Meta 구간 분리: Train 75%, Valid 25% (Ranker는 Test 구간을 따로 빼기보다 바로 검증)
    meta_train, meta_valid, _, meta_test = split_by_unique_dates(
        meta_df, ratios=(0.75, 0.25, 0.0, 0.0)
    )

    # 날짜별 데이터 개수 배열 추출 (LGBMRanker 필수 파라미터)
    train_groups = meta_train.groupby("date").size().values
    valid_groups = meta_valid.groupby("date").size().values

    y_train = meta_train["target_rank_label"].astype(int)
    y_valid = meta_valid["target_rank_label"].astype(int)

    print("[4/5] Meta LGBMRanker 학습 중...")
    meta_model = LGBMRanker(
        n_estimators=800,
        learning_rate=0.03,
        num_leaves=15,  # 오버피팅 방지를 위해 Base 모델보다 작게
        max_depth=4,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        importance_type="gain",
    )

    meta_model.fit(
        meta_train[META_FEATURES],
        y_train,
        group=train_groups,
        eval_set=[(meta_valid[META_FEATURES], y_valid)],
        eval_group=[valid_groups],
        eval_metric="ndcg",
        callbacks=[early_stopping(50), log_evaluation(50)],
    )

    print("\n[5/5] 모델 검증 및 저장...")
    # Valid 셋 대상 최종 스코어 채점
    meta_valid = meta_valid.copy()
    meta_valid["score"] = meta_model.predict(meta_valid[META_FEATURES])

    print(
        f"[Valid Precision@5/day - strict] {precision_at_k_by_day(meta_valid, 'score', 'target_strict', k=5):.2%}"
    )
    print(
        f"[Valid Precision@3/day - strict] {precision_at_k_by_day(meta_valid, 'score', 'target_strict', k=3):.2%}"
    )

    # Ranker는 확률값(0~1)이 아닌 점수를 뱉으므로 별도의 Calibrator 연산 생략을 위해 PassThroughCalibrator 사용
    artifact = {
        "model": meta_model,
        "calibrator": PassThroughCalibrator(),
        "features": META_FEATURES,
        "model_name": "stacking_meta_ranker_v2",
        "bull_specialist_mode": bull_mode,
    }
    joblib.dump(artifact, META_MODEL_PATH)

    # 백테스트를 위해 전체 데이터셋 예측 후 저장
    save_df = meta_df.copy()
    save_df["score"] = meta_model.predict(save_df[META_FEATURES])

    save_cols = [
        "date",
        "code",
        "name",
        "bull_regime",
        "idx_ret20",
        "idx_atr_ratio",
        "hx",
        "hl",
        "bx",
        "bl",
        "mean_prob",
        "std_prob",
        "max_prob",
        "min_prob",
        "bull_mean",
        "hybrid_mean",
        "bull_hybrid_gap",
        "bull_specialist_mode",
        "bull_score_source",
        "bull_artifact_used",
        "score",
        "target_loose",
        "target_strict",
        "realized_ret_3d",
    ]
    save_df = save_df[save_cols].sort_values(["date", "code"]).reset_index(drop=True)
    save_df.to_csv(AI_PRED_PATH, index=False, encoding="utf-8-sig")

    print(f"✅ Meta 모델 저장 완료: {META_MODEL_PATH}")
    print(f"✅ 예측 결과 저장 완료: {AI_PRED_PATH}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train swing v2 meta ranker.")
    parser.add_argument("--meta-start", default=None)
    parser.add_argument("--meta-end", default=None)
    parser.add_argument(
        "--bull-mode", default=None, choices=["enabled", "disabled", "hold_current"]
    )
    args = parser.parse_args()
    train_meta_model_v2(
        meta_start=args.meta_start, meta_end=args.meta_end, bull_mode=args.bull_mode
    )
