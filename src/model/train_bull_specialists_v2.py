import joblib
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier, early_stopping, log_evaluation

from common_v2 import (
    BASE_START, BASE_END, FEATURES_XGB, FEATURES_LGBM,
    BULL_XGB_PATH, BULL_LGBM_PATH,
    get_top_kospi_codes, split_by_unique_dates, recency_sample_weight,
    class_balance, fit_calibrator, apply_calibrator, threshold_table,
    precision_at_k_by_day, select_daily_candidates
)
from dataset_builder_v2 import build_panel_dataset


TARGET_COL = 'target_strict'


def train_bull_specialists_v2():
    codes = get_top_kospi_codes(limit=300)

    print(f"[1/5] Bull Specialist용 패널 생성 중... ({BASE_START} ~ {BASE_END})")
    panel = build_panel_dataset(codes, BASE_START, BASE_END, min_rows=150, include_labels=True)
    if panel.empty:
        print("❌ 학습 데이터가 없습니다.")
        return

    train_df, valid_df, calib_df, test_df = split_by_unique_dates(panel, ratios=(0.65, 0.15, 0.10, 0.10))

    # Bull regime row만 사용
    train_bull = train_df[train_df['bull_regime'] == 1].copy()
    valid_bull = valid_df[valid_df['bull_regime'] == 1].copy()
    calib_bull = calib_df[calib_df['bull_regime'] == 1].copy()
    test_bull = test_df[test_df['bull_regime'] == 1].copy()

    if min(len(train_bull), len(valid_bull), len(calib_bull), len(test_bull)) == 0:
        print("❌ Bull regime 샘플이 부족합니다.")
        return

    y_train = train_bull[TARGET_COL].astype(int)
    y_valid = valid_bull[TARGET_COL].astype(int)
    y_calib = calib_bull[TARGET_COL].astype(int)

    pos, neg, spw = class_balance(y_train)
    sw = recency_sample_weight(train_bull['date'])

    print(f"[2/5] Bull XGB 학습 시작 - target={TARGET_COL}")
    print(f"   Train Pos={pos}, Neg={neg}, scale_pos_weight={spw:.2f}")

    bull_xgb = XGBClassifier(
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

    bull_xgb.fit(
        train_bull[FEATURES_XGB], y_train,
        sample_weight=sw,
        eval_set=[(valid_bull[FEATURES_XGB], y_valid)],
        verbose=False
    )

    calib_raw_x = bull_xgb.predict_proba(calib_bull[FEATURES_XGB])[:, 1]
    cal_x = fit_calibrator(calib_raw_x, y_calib)

    test_raw_x = bull_xgb.predict_proba(test_bull[FEATURES_XGB])[:, 1]
    test_score_x = apply_calibrator(cal_x, test_raw_x)

    eval_x = test_bull[['date', 'code', 'name', 'bull_regime', 'target_strict']].copy()
    eval_x['score'] = test_score_x

    print("\n[Bull XGB Threshold Table - target_strict]")
    print(threshold_table(eval_x, score_col='score', target_col='target_strict'))
    print(f"[Bull XGB Precision@5/day] {precision_at_k_by_day(eval_x, 'score', 'target_strict', k=5):.2%}")

    print("[3/5] Bull LGBM 학습 시작...")
    bull_lgbm = LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=5,
        min_child_samples=40,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=spw,
        random_state=42,
        n_jobs=-1,
        force_col_wise=True
    )

    bull_lgbm.fit(
        train_bull[FEATURES_LGBM], y_train,
        sample_weight=sw,
        eval_set=[(valid_bull[FEATURES_LGBM], y_valid)],
        eval_metric='auc',
        callbacks=[early_stopping(100), log_evaluation(100)]
    )

    calib_raw_l = bull_lgbm.predict_proba(calib_bull[FEATURES_LGBM])[:, 1]
    cal_l = fit_calibrator(calib_raw_l, y_calib)

    test_raw_l = bull_lgbm.predict_proba(test_bull[FEATURES_LGBM])[:, 1]
    test_score_l = apply_calibrator(cal_l, test_raw_l)

    eval_l = test_bull[['date', 'code', 'name', 'bull_regime', 'target_strict']].copy()
    eval_l['score'] = test_score_l

    print("\n[Bull LGBM Threshold Table - target_strict]")
    print(threshold_table(eval_l, score_col='score', target_col='target_strict'))
    print(f"[Bull LGBM Precision@5/day] {precision_at_k_by_day(eval_l, 'score', 'target_strict', k=5):.2%}")

    picks = select_daily_candidates(eval_l, score_col='score')
    strict_precision = picks['target_strict'].mean() if len(picks) > 0 else 0.0
    print(f"[Bull Daily Top-K Picks] picks={len(picks)} / strict_precision={strict_precision:.2%}")

    joblib.dump({
        'model': bull_xgb,
        'calibrator': cal_x,
        'features': FEATURES_XGB,
        'target_col': TARGET_COL,
        'model_name': 'bull_xgb_v2'
    }, BULL_XGB_PATH)

    joblib.dump({
        'model': bull_lgbm,
        'calibrator': cal_l,
        'features': FEATURES_LGBM,
        'target_col': TARGET_COL,
        'model_name': 'bull_lgbm_v2'
    }, BULL_LGBM_PATH)

    print(f"[4/5] 저장 완료: {BULL_XGB_PATH}")
    print(f"[5/5] 저장 완료: {BULL_LGBM_PATH}")


if __name__ == "__main__":
    train_bull_specialists_v2()