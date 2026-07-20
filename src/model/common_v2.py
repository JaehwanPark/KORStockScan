import os
import sys
import warnings
import json
import joblib
import numpy as np
import pandas as pd
import FinanceDataReader as fdr
from pathlib import Path
from sqlalchemy import create_engine, text
from sklearn.isotonic import IsotonicRegression

try:
    from .feature_engineering_v2 import calculate_all_features
except ImportError:
    from feature_engineering_v2 import calculate_all_features

warnings.filterwarnings("ignore")

# ==========================================
# 경로 / DB / 파일 경로
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
MODEL_OUTPUT_DIR = os.getenv("KORSTOCKSCAN_SWING_MODEL_OUTPUT_DIR", DATA_DIR)
os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
MODEL_REGISTRY_DIR = os.getenv(
    "KORSTOCKSCAN_SWING_MODEL_REGISTRY_DIR",
    os.path.join(DATA_DIR, "model_registry", "swing_v2"),
)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quant_admin:quant_password_123!@localhost:5432/korstockscan",
)
engine = create_engine(DB_URL)

HYBRID_XGB_PATH = os.path.join(MODEL_OUTPUT_DIR, "hybrid_xgb_v2.pkl")
HYBRID_LGBM_PATH = os.path.join(MODEL_OUTPUT_DIR, "hybrid_lgbm_v2.pkl")
BULL_XGB_PATH = os.path.join(MODEL_OUTPUT_DIR, "bull_xgb_v2.pkl")
BULL_LGBM_PATH = os.path.join(MODEL_OUTPUT_DIR, "bull_lgbm_v2.pkl")
META_MODEL_PATH = os.path.join(MODEL_OUTPUT_DIR, "stacking_meta_v2.pkl")

AI_PRED_PATH = os.path.join(MODEL_OUTPUT_DIR, "ai_predictions_v2.csv")
RECO_PATH = os.path.join(DATA_DIR, "daily_recommendations_v2.csv")
RECO_DIAGNOSTIC_PATH = os.path.join(
    DATA_DIR, "daily_recommendations_v2_diagnostics.csv"
)
RECO_DIAGNOSTIC_JSON_PATH = os.path.join(
    DATA_DIR, "daily_recommendations_v2_diagnostics.json"
)

SWING_SELECTION_OWNER = "SwingModelSelectionFunnelRepair"
BULL_SPECIALIST_MODES = {"enabled", "disabled", "hold_current"}


def _env_float(name, default):
    try:
        raw = os.getenv(name)
        if raw in (None, ""):
            return default
        return float(raw)
    except (TypeError, ValueError):
        return default


def _env_int(name, default):
    try:
        raw = os.getenv(name)
        if raw in (None, ""):
            return default
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def _env_str(name, default):
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return str(raw)


SWING_FLOOR_BULL = _env_float("KORSTOCKSCAN_SWING_FLOOR_BULL", 0.35)
SWING_FLOOR_BEAR = _env_float("KORSTOCKSCAN_SWING_FLOOR_BEAR", 0.40)
SWING_FALLBACK_FLOOR_BULL = _env_float("KORSTOCKSCAN_SWING_FALLBACK_FLOOR_BULL", 0.35)
SWING_SELECTION_TOP_K = _env_int("KORSTOCKSCAN_SWING_SELECTION_TOP_K", 3)

# ==========================================
# 학습 기간 설정
# ==========================================
BASE_START = "2024-01-01"
BASE_END = "2025-12-31"

META_START = "2026-01-01"
META_END = "2026-03-20"
BULL_BASE_START = _env_str("KORSTOCKSCAN_SWING_BULL_BASE_START", BASE_START)
BULL_BASE_END = _env_str("KORSTOCKSCAN_SWING_BULL_BASE_END", BASE_END)

# ==========================================
# 피처 정의
# ==========================================
FEATURES_XGB = [
    "return_1d",
    "ma_ratio",
    "macd",
    "macd_sig",
    "close_vwap_ratio",
    "obv_change_5",
    "up_trend_2d",
    "dist_ma5",
    "dual_net_buy",
    "foreign_net_roll5",
    "inst_net_roll5",
    "bbb",
    "bbp",
    "atr_ratio",
    "rsi",
    "breakout_20",
    "turnover_shock",
    "rs_20_vs_index",
]

FEATURES_LGBM = [
    "bbp",
    "rsi",
    "rsi_slope",
    "range_ratio",
    "vol_momentum",
    "vol_change",
    "atr_ratio",
    "bbb",
    "foreign_vol_ratio",
    "inst_vol_ratio",
    "margin_rate_change",
    "margin_rate_roll5",
    "turnover_shock",
    "breakout_20",
    "gap_ratio",
    "body_ratio",
    "rs_20_vs_index",
]

META_FEATURES = [
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
    "bull_regime",
    "idx_ret20",
    "idx_atr_ratio",
]


# ==========================================
# 유틸
# ==========================================
class IdentityCalibrator:
    def fit(self, x, y):
        return self

    def transform(self, x):
        arr = np.asarray(x, dtype=float)
        return np.clip(arr, 0.0, 1.0)


class PassThroughCalibrator:
    """LGBMRanker 등 확률 캘리브레이션이 필요 없는 모델을 위한 패스스루 클래스"""

    def transform(self, x):
        return np.asarray(x, dtype=float)


class PredictProbaScoreAdapter:
    """Expose classifier positive probability through a ranker-like predict API."""

    def __init__(self, model, positive_class_index=1):
        self.model = model
        self.positive_class_index = positive_class_index

    def predict(self, x):
        proba = self.model.predict_proba(x)
        return np.asarray(proba)[:, self.positive_class_index]


def ensure_pickle_compat():
    """Load legacy artifacts that pickled PassThroughCalibrator from __main__."""
    main_mod = sys.modules.get("__main__")
    if main_mod is not None and not hasattr(main_mod, "PassThroughCalibrator"):
        setattr(main_mod, "PassThroughCalibrator", PassThroughCalibrator)
    if main_mod is not None and not hasattr(main_mod, "PredictProbaScoreAdapter"):
        setattr(main_mod, "PredictProbaScoreAdapter", PredictProbaScoreAdapter)


def load_model_artifact(path):
    ensure_pickle_compat()
    return joblib.load(path)


def swing_model_current_manifest_path():
    return Path(MODEL_REGISTRY_DIR) / "current.json"


def load_swing_model_current_manifest(path=None):
    manifest_path = (
        Path(path) if path is not None else swing_model_current_manifest_path()
    )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def resolve_bull_specialist_mode(mode=None, manifest=None):
    candidate = mode or os.getenv("KORSTOCKSCAN_SWING_BULL_SPECIALIST_MODE")
    if candidate in (None, ""):
        source = (
            manifest if manifest is not None else load_swing_model_current_manifest()
        )
        candidate = (
            source.get("bull_specialist_mode") if isinstance(source, dict) else None
        )
    candidate = str(candidate or "enabled").strip().lower()
    if candidate not in BULL_SPECIALIST_MODES:
        return "enabled"
    return candidate


def bull_mode_runtime_provenance(mode):
    mode = resolve_bull_specialist_mode(mode)
    if mode == "disabled":
        return {
            "bull_specialist_mode": mode,
            "bull_score_source": "neutralized_from_hybrid",
            "bull_artifact_used": False,
        }
    return {
        "bull_specialist_mode": mode,
        "bull_score_source": "artifact",
        "bull_artifact_used": True,
    }


def fit_calibrator(raw_prob, y_true):
    raw_prob = np.asarray(raw_prob, dtype=float)
    y_true = np.asarray(y_true, dtype=int)

    if len(raw_prob) < 50 or len(np.unique(y_true)) < 2:
        return IdentityCalibrator()

    try:
        cal = IsotonicRegression(out_of_bounds="clip")
        cal.fit(raw_prob, y_true)
        return cal
    except Exception:
        return IdentityCalibrator()


def apply_calibrator(calibrator, raw_prob):
    raw_prob = np.asarray(raw_prob, dtype=float)
    return np.clip(calibrator.transform(raw_prob), 0.0, 1.0)


def normalize_code(code):
    return str(code).replace(".0", "").strip().zfill(6)


def normalize_codes(codes):
    return [normalize_code(c) for c in codes]


def sql_code_tuple(codes):
    codes = normalize_codes(codes)
    if len(codes) == 1:
        return f"('{codes[0]}')"
    return str(tuple(codes))


def get_latest_quote_date():
    query = "SELECT MAX(quote_date) AS max_date FROM daily_stock_quotes"
    with engine.connect() as conn:
        latest = pd.read_sql(text(query), conn).iloc[0, 0]
    return pd.to_datetime(latest).normalize()


def get_top_kospi_codes(limit=300):
    print(f"[Universe] KOSPI 우량주 상위 {limit}개 추출 중...")
    try:
        df_krx = fdr.StockListing("KOSPI")
        if "Marcap" in df_krx.columns:
            top_500 = df_krx.sort_values(by="Marcap", ascending=False).head(500)
        else:
            top_500 = df_krx.copy()

        if "Volume" in top_500.columns:
            target = top_500.sort_values(by="Volume", ascending=False).head(limit)
        else:
            target = top_500.head(limit)

        codes = normalize_codes(target["Code"].tolist())
        print(f"✅ FDR 기준 {len(codes)}개 종목 추출 완료")
        return codes

    except Exception as e:
        print(f"⚠️ FDR 실패: {e} / DB fallback 사용")
        latest_date = get_latest_quote_date().strftime("%Y-%m-%d")
        query = f"""
            SELECT stock_code
            FROM daily_stock_quotes
            WHERE quote_date = '{latest_date}'
            ORDER BY volume DESC
            LIMIT {limit}
        """
        with engine.connect() as conn:
            top_codes_df = pd.read_sql(text(query), conn)

        codes = normalize_codes(top_codes_df["stock_code"].tolist())
        print(f"✅ DB 기준 {len(codes)}개 종목 추출 완료")
        return codes


def split_by_unique_dates(df, ratios, date_col="date"):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col]).dt.normalize()

    ratios = np.asarray(ratios, dtype=float)
    ratios = ratios / ratios.sum()

    dates = np.array(sorted(df[date_col].unique()))
    n = len(dates)

    if n < len(ratios) * 5:
        raise ValueError(f"유니크 날짜 수가 너무 적습니다: {n}")

    cut_idxs = []
    cum = 0.0
    for r in ratios[:-1]:
        cum += r
        idx = int(np.floor(n * cum))
        idx = max(1, min(n - 1, idx))
        cut_idxs.append(idx)

    boundaries = [dates[i - 1] for i in cut_idxs]

    splits = []
    prev = None
    for bound in boundaries + [None]:
        if prev is None and bound is not None:
            mask = df[date_col] <= bound
        elif prev is not None and bound is not None:
            mask = (df[date_col] > prev) & (df[date_col] <= bound)
        else:
            mask = df[date_col] > prev
        splits.append(df.loc[mask].copy())
        prev = bound

    return splits


def recency_sample_weight(date_series, half_life=63):
    ds = pd.to_datetime(date_series)
    age_days = (ds.max() - ds).dt.days
    weight = np.exp(-np.log(2) * age_days / half_life)
    return weight.values


def class_balance(y):
    y = pd.Series(y)
    pos = int((y == 1).sum())
    neg = int((y == 0).sum())
    ratio = 1.0 if pos == 0 else neg / max(pos, 1)
    return pos, neg, ratio


def threshold_table(
    df,
    score_col="score",
    target_col="target_strict",
    thresholds=(0.45, 0.50, 0.55, 0.60),
):
    rows = []
    for th in thresholds:
        pred = (df[score_col] >= th).astype(int)
        picks = int(pred.sum())
        precision = float(df.loc[pred == 1, target_col].mean()) if picks > 0 else 0.0
        rows.append({"threshold": th, "picks": picks, "precision": precision})
    return pd.DataFrame(rows)


def precision_at_k_by_day(df, score_col="score", target_col="target_strict", k=5):
    total = 0
    hit = 0
    for _, g in df.groupby("date"):
        top = g.sort_values(score_col, ascending=False).head(k)
        total += len(top)
        hit += int(top[target_col].sum())
    return 0.0 if total == 0 else hit / total


def build_meta_feature_frame(df):
    out = df.copy()
    out["mean_prob"] = out[["hx", "hl", "bx", "bl"]].mean(axis=1)
    out["std_prob"] = out[["hx", "hl", "bx", "bl"]].std(axis=1)
    out["max_prob"] = out[["hx", "hl", "bx", "bl"]].max(axis=1)
    out["min_prob"] = out[["hx", "hl", "bx", "bl"]].min(axis=1)
    out["bull_mean"] = out[["bx", "bl"]].mean(axis=1)
    out["hybrid_mean"] = out[["hx", "hl"]].mean(axis=1)
    out["bull_hybrid_gap"] = out["bull_mean"] - out["hybrid_mean"]
    return out


def score_artifact(artifact, df):
    model = artifact["model"]
    calibrator = artifact["calibrator"]
    features = artifact["features"]

    raw = model.predict_proba(df[features])[:, 1]
    return apply_calibrator(calibrator, raw)


def build_base_score_frame(
    source_df,
    *,
    bull_mode=None,
    hybrid_xgb_path=None,
    hybrid_lgbm_path=None,
    bull_xgb_path=None,
    bull_lgbm_path=None,
    include_columns=None,
):
    """Build hx/hl/bx/bl and meta features with a stable META_FEATURES contract."""
    mode = resolve_bull_specialist_mode(bull_mode)
    hybrid_xgb = load_model_artifact(hybrid_xgb_path or HYBRID_XGB_PATH)
    hybrid_lgbm = load_model_artifact(hybrid_lgbm_path or HYBRID_LGBM_PATH)

    base_cols = list(include_columns or [])
    for required in (
        "date",
        "code",
        "name",
        "bull_regime",
        "idx_ret20",
        "idx_atr_ratio",
    ):
        if required in source_df.columns and required not in base_cols:
            base_cols.append(required)
    score_df = (
        source_df[base_cols].copy()
        if base_cols
        else pd.DataFrame(index=source_df.index)
    )
    score_df["hx"] = score_artifact(hybrid_xgb, source_df)
    score_df["hl"] = score_artifact(hybrid_lgbm, source_df)

    if mode == "disabled":
        score_df["bx"] = score_df["hx"]
        score_df["bl"] = score_df["hl"]
    else:
        bull_xgb = load_model_artifact(bull_xgb_path or BULL_XGB_PATH)
        bull_lgbm = load_model_artifact(bull_lgbm_path or BULL_LGBM_PATH)
        score_df["bx"] = score_artifact(bull_xgb, source_df)
        score_df["bl"] = score_artifact(bull_lgbm, source_df)

    score_df = build_meta_feature_frame(score_df)
    provenance = bull_mode_runtime_provenance(mode)
    for key, value in provenance.items():
        score_df[key] = value
    return score_df


# common_v2.py 내부의 해당 함수 교체


def select_daily_candidates(
    scored_df,
    score_col="score",  # Meta Ranker의 상대 점수 컬럼
    prob_col="hybrid_mean",  # Base 모델의 절대 확률 컬럼 (안전망)
    date_col="date",
    top_k_bull=5,
    top_k_bear=2,
    floor_bull=0.45,  # 절대 확률 필터링 임계치
    floor_bear=0.50,
    fallback_floor=0.42,
):
    if scored_df.empty:
        return scored_df.copy()

    picks = []
    for dt, g in scored_df.groupby(date_col):
        bull = int(g["bull_regime"].iloc[0]) if "bull_regime" in g.columns else 0
        top_k = top_k_bull if bull == 1 else top_k_bear
        floor = floor_bull if bull == 1 else floor_bear

        # [1단계] 절대 평가: Base 확률 기준 위험 종목 컷오프
        if prob_col in g.columns:
            safe_pool = g[g[prob_col] >= floor].copy()
        else:
            safe_pool = g.copy()

        # 상승장 추천 0건 방지 장치 (안전망 임계치 소폭 하향)
        if safe_pool.empty and bull == 1 and prob_col in g.columns:
            safe_pool = g[g[prob_col] >= fallback_floor].copy()

        if safe_pool.empty:
            continue

        # [2단계] 상대 평가: 살아남은 후보 중 Meta Ranker 점수로 K개 픽업
        day_pick = safe_pool.sort_values(score_col, ascending=False).head(top_k)
        picks.append(day_pick)

    if not picks:
        return pd.DataFrame(columns=scored_df.columns)

    result = pd.concat(picks, axis=0).reset_index(drop=True)
    return result


def daily_selection_stats(
    scored_df,
    *,
    prob_col="hybrid_mean",
    date_col="date",
    floor_bull=SWING_FLOOR_BULL,
    floor_bear=SWING_FLOOR_BEAR,
    fallback_floor=SWING_FALLBACK_FLOOR_BULL,
):
    """Return per-date floor/provenance stats used by the live recommendation job."""
    if scored_df.empty:
        return pd.DataFrame(
            columns=[
                date_col,
                "bull_regime",
                "floor_used",
                "primary_floor",
                "fallback_floor",
                "safe_pool_count",
                "candidate_count",
                "selection_mode",
            ]
        )

    rows = []
    for dt, g in scored_df.groupby(date_col):
        bull = int(g["bull_regime"].iloc[0]) if "bull_regime" in g.columns else 0
        primary_floor = floor_bull if bull == 1 else floor_bear
        floor_used = primary_floor

        if prob_col in g.columns:
            safe_pool_count = int((g[prob_col] >= primary_floor).sum())
        else:
            safe_pool_count = int(len(g))

        if safe_pool_count == 0 and bull == 1 and prob_col in g.columns:
            fallback_count = int((g[prob_col] >= fallback_floor).sum())
            if fallback_count > 0:
                safe_pool_count = fallback_count
                floor_used = fallback_floor

        rows.append(
            {
                date_col: dt,
                "bull_regime": bull,
                "floor_used": float(floor_used),
                "primary_floor": float(primary_floor),
                "fallback_floor": float(fallback_floor),
                "safe_pool_count": safe_pool_count,
                "candidate_count": int(len(g)),
                "selection_mode": "SELECTED" if safe_pool_count > 0 else "EMPTY",
            }
        )

    return pd.DataFrame(rows)
