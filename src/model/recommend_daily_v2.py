import joblib
import pandas as pd

from common_v2 import (
    HYBRID_XGB_PATH, HYBRID_LGBM_PATH, BULL_XGB_PATH, BULL_LGBM_PATH,
    META_MODEL_PATH, RECO_PATH, META_FEATURES,
    get_top_kospi_codes, get_latest_quote_date,
    build_meta_feature_frame, score_artifact, apply_calibrator,
    select_daily_candidates
)
from dataset_builder_v2 import build_panel_dataset


def recommend_daily_v2():
    latest_date = get_latest_quote_date()
    start_date = (latest_date - pd.Timedelta(days=400)).strftime('%Y-%m-%d')
    end_date = latest_date.strftime('%Y-%m-%d')

    print(f"[1/4] 최신 추천용 패널 생성 중... ({start_date} ~ {end_date})")
    codes = get_top_kospi_codes(limit=300)
    panel = build_panel_dataset(codes, start_date, end_date, min_rows=120, include_labels=False)
    if panel.empty:
        print("❌ 최신 패널 생성 실패")
        return

    latest_rows = panel[panel['date'] == latest_date].copy()
    if latest_rows.empty:
        print("❌ 최신 거래일 데이터가 없습니다.")
        return

    print("[2/4] 모델 로드 및 base score 생성 중...")
    hybrid_xgb = joblib.load(HYBRID_XGB_PATH)
    hybrid_lgbm = joblib.load(HYBRID_LGBM_PATH)
    bull_xgb = joblib.load(BULL_XGB_PATH)
    bull_lgbm = joblib.load(BULL_LGBM_PATH)
    meta_artifact = joblib.load(META_MODEL_PATH)

    score_df = latest_rows[['date', 'code', 'name', 'bull_regime', 'idx_ret20', 'idx_atr_ratio']].copy()
    score_df['hx'] = score_artifact(hybrid_xgb, latest_rows)
    score_df['hl'] = score_artifact(hybrid_lgbm, latest_rows)
    score_df['bx'] = score_artifact(bull_xgb, latest_rows)
    score_df['bl'] = score_artifact(bull_lgbm, latest_rows)

    score_df = build_meta_feature_frame(score_df)

    print("[3/4] Meta score 생성 중...")
    meta_raw = meta_artifact['model'].predict_proba(score_df[META_FEATURES])[:, 1]
    score_df['score'] = apply_calibrator(meta_artifact['calibrator'], meta_raw)

    picks = select_daily_candidates(score_df, score_col='score')

    if picks.empty:
        print("⚠️ 오늘 추천 종목이 없습니다.")
        score_df.sort_values('score', ascending=False).head(10).to_csv(RECO_PATH, index=False, encoding='utf-8-sig')
        print(f"대신 상위 스코어 10개 저장: {RECO_PATH}")
        return

    picks = picks.sort_values('score', ascending=False).reset_index(drop=True)
    picks.to_csv(RECO_PATH, index=False, encoding='utf-8-sig')

    print("[4/4] 오늘의 추천 종목")
    print(picks[['date', 'code', 'name', 'score', 'hx', 'hl', 'bx', 'bl', 'bull_regime']].to_string(index=False))
    print(f"\n✅ 저장 완료: {RECO_PATH}")


if __name__ == "__main__":
    recommend_daily_v2()