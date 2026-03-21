import joblib
import pandas as pd
from xgboost import XGBClassifier

from common_v2 import (
    BASE_START, BASE_END, FEATURES_XGB, HYBRID_XGB_PATH,
    get_top_kospi_codes, split_by_unique_dates, recency_sample_weight,
    class_balance, fit_calibrator, apply_calibrator, threshold_table,
    precision_at_k_by_day, select_daily_candidates
)
from dataset_builder_v2 import build_panel_dataset


TARGET_COL = 'target_loose'


def train_hybrid_xgb_v2():
    codes = get_top_kospi_codes(limit=300)

    print(f"[1/4] Hybrid XGB용 패널 생성 중... ({BASE_START} ~ {BASE_END})")
    panel = build_panel_dataset(codes, BASE_START, BASE_END, min_rows=150, include_labels=True)
    if panel.empty:
        print("❌ 학습 데이터가 없습니다.")
        return

    train_df, valid_df, calib_df, test_df = split_by_unique_dates(panel, ratios=(0.65, 0.15, 0.10, 0.10))
    y_train = train_df[TARGET_COL].astype(int)
    y_valid = valid_df[TARGET_COL].astype(int)
    y_calib = calib_df[TARGET_COL].astype(int)
    y_test = test_df[TARGET_COL].astype(int)

    pos, neg, spw = class_balance(y_train)
    sw = recency_sample_weight(train_df['date'])

    print(f"[2/4] 학습 시작 - target={TARGET_COL}")
    print(f"   Train Pos={pos}, Neg={neg}, scale_pos_weight={spw:.2f}")

    model = XGBClassifier(
        n_estimators=700,
        learning_rate=0.03,
        max_depth=4,
        min_child_weight=10,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.5,
        reg_lambda=2.0,
        scale_pos_weight=spw,
        eval_metric='aucpr',
        random_state=42,
        n_jobs=-1
    )

    model.fit(
        train_df[FEATURES_XGB], y_train,
        sample_weight=sw,
        eval_set=[(valid_df[FEATURES_XGB], y_valid)],
        verbose=False
    )

    print("[3/4] Calibration 및 검증...")
    calib_raw = model.predict_proba(calib_df[FEATURES_XGB])[:, 1]
    calibrator = fit_calibrator(calib_raw, y_calib)

    test_raw = model.predict_proba(test_df[FEATURES_XGB])[:, 1]
    test_score = apply_calibrator(calibrator, test_raw)

    eval_df = test_df[['date', 'code', 'name', 'bull_regime', 'target_loose', 'target_strict']].copy()
    eval_df['score'] = test_score

    print("\n[Threshold Table - target_loose]")
    print(threshold_table(eval_df, score_col='score', target_col='target_loose'))

    print(f"\n[Precision@5/day - target_loose] {precision_at_k_by_day(eval_df, 'score', 'target_loose', k=5):.2%}")
    print(f"[Precision@5/day - target_strict] {precision_at_k_by_day(eval_df, 'score', 'target_strict', k=5):.2%}")

    picks = select_daily_candidates(eval_df, score_col='score')
    strict_precision = picks['target_strict'].mean() if len(picks) > 0 else 0.0
    print(f"[Daily Top-K Picks] picks={len(picks)} / strict_precision={strict_precision:.2%}")

    artifact = {
        'model': model,
        'calibrator': calibrator,
        'features': FEATURES_XGB,
        'target_col': TARGET_COL,
        'model_name': 'hybrid_xgb_v2'
    }
    joblib.dump(artifact, HYBRID_XGB_PATH)

    print(f"[4/4] 저장 완료: {HYBRID_XGB_PATH}")


if __name__ == "__main__":
    train_hybrid_xgb_v2()