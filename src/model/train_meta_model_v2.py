import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from common_v2 import (
    META_START, META_END,
    HYBRID_XGB_PATH, HYBRID_LGBM_PATH, BULL_XGB_PATH, BULL_LGBM_PATH,
    META_MODEL_PATH, AI_PRED_PATH, META_FEATURES,
    get_top_kospi_codes, split_by_unique_dates,
    fit_calibrator, apply_calibrator, threshold_table,
    precision_at_k_by_day, build_meta_feature_frame,
    score_artifact, select_daily_candidates
)
from dataset_builder_v2 import build_panel_dataset


def train_meta_model_v2():
    print(f"[1/5] Meta 학습용 패널 생성 중... ({META_START} ~ {META_END})")
    codes = get_top_kospi_codes(limit=300)
    panel = build_panel_dataset(codes, META_START, META_END, min_rows=60, include_labels=True)
    if panel.empty:
        print("❌ 메타 학습 데이터가 없습니다.")
        return

    print("[2/5] Base model 로드 중...")
    hybrid_xgb = joblib.load(HYBRID_XGB_PATH)
    hybrid_lgbm = joblib.load(HYBRID_LGBM_PATH)
    bull_xgb = joblib.load(BULL_XGB_PATH)
    bull_lgbm = joblib.load(BULL_LGBM_PATH)

    meta_df = panel[['date', 'code', 'name', 'bull_regime', 'idx_ret20', 'idx_atr_ratio',
                     'target_loose', 'target_strict', 'realized_ret_3d']].copy()

    meta_df['hx'] = score_artifact(hybrid_xgb, panel)
    meta_df['hl'] = score_artifact(hybrid_lgbm, panel)
    meta_df['bx'] = score_artifact(bull_xgb, panel)
    meta_df['bl'] = score_artifact(bull_lgbm, panel)

    meta_df = build_meta_feature_frame(meta_df)

    # meta 구간도 train / calib / test 분리
    meta_train, meta_calib, meta_test = split_by_unique_dates(meta_df, ratios=(0.60, 0.20, 0.20))

    y_train = meta_train['target_strict'].astype(int)
    y_calib = meta_calib['target_strict'].astype(int)

    print("[3/5] Meta Logistic 학습 중...")
    meta_model = LogisticRegression(
        max_iter=1000,
        C=0.5,
        random_state=42
    )
    meta_model.fit(meta_train[META_FEATURES], y_train)

    calib_raw = meta_model.predict_proba(meta_calib[META_FEATURES])[:, 1]
    meta_calibrator = fit_calibrator(calib_raw, y_calib)

    test_raw = meta_model.predict_proba(meta_test[META_FEATURES])[:, 1]
    meta_test = meta_test.copy()
    meta_test['score'] = apply_calibrator(meta_calibrator, test_raw)

    print("\n[전문가 의견 상관관계]")
    print(meta_test[['hx', 'hl', 'bx', 'bl']].corr().round(3))

    print("\n[Threshold Table - target_strict]")
    print(threshold_table(meta_test, score_col='score', target_col='target_strict'))

    print(f"\n[Precision@5/day - strict] {precision_at_k_by_day(meta_test, 'score', 'target_strict', k=5):.2%}")
    print(f"[Precision@3/day - strict] {precision_at_k_by_day(meta_test, 'score', 'target_strict', k=3):.2%}")

    picks = select_daily_candidates(meta_test, score_col='score')
    strict_precision = picks['target_strict'].mean() if len(picks) > 0 else 0.0

    print(f"\n[Daily Top-K Picks]")
    print(f" picks={len(picks)}")
    print(f" strict_precision={strict_precision:.2%}")

    artifact = {
        'model': meta_model,
        'calibrator': meta_calibrator,
        'features': META_FEATURES,
        'model_name': 'stacking_meta_v2'
    }
    joblib.dump(artifact, META_MODEL_PATH)

    # 백테스트/리포트용 저장
    save_cols = [
        'date', 'code', 'name',
        'bull_regime', 'idx_ret20', 'idx_atr_ratio',
        'hx', 'hl', 'bx', 'bl',
        'mean_prob', 'std_prob', 'max_prob', 'min_prob',
        'bull_mean', 'hybrid_mean', 'bull_hybrid_gap',
        'score', 'target_loose', 'target_strict', 'realized_ret_3d'
    ]
    save_df = meta_test[save_cols].copy()
    save_df = save_df.sort_values(['date', 'code']).reset_index(drop=True)
    save_df.to_csv(AI_PRED_PATH, index=False, encoding='utf-8-sig')

    print(f"[4/5] Meta 저장 완료: {META_MODEL_PATH}")
    print(f"[5/5] 예측 결과 저장 완료: {AI_PRED_PATH}")


if __name__ == "__main__":
    train_meta_model_v2()