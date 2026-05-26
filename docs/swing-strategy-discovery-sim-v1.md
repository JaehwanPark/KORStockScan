# Swing Strategy Discovery Sim v1

## 목적

`swing_strategy_discovery_sim_v1`은 기존 스윙 머신러닝(ML) 모델이 고른 소수 종목을 그대로 신뢰하지 않고, 스윙 후보 전체를 가상 생애주기(lifecycle) 실험 대상으로 넓혀 진입, 보유, 추가매수, 청산 조합의 기대값(EV)을 찾기 위한 시뮬레이션 framework다.

v1은 실주문 전환 기능이 아니다. 모든 row는 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false`, `decision_authority=swing_sim_exploration_only`를 유지한다.

## 확정 설계

- 후보군(universe): 기존 추천 진단 CSV의 safe pool 전체.
- 기존 ML 모델: 최종 selector가 아니라 낮은 가중치의 feature 및 비교 cohort로만 사용한다.
- 다양성(diversity): v1은 가격 위치 태그, 기존 blocker, 변동성 bucket을 필수 축으로 사용한다.
- 섹터/테마: v1 row에 `sector`, `industry`, `sector_code`, `market_type`, `theme_tags`, source-quality를 수집한다. 섹터/업종은 수동 관리 reference 파일을 우선 source로 쓰고, 테마는 키움 `ka90001 qry_tp=2` 종목별 조회만 사용한다. 수집 실패 시 후보 제외 없이 `missing` source-quality로 남긴다.
- 가중치 정책: 개별 수치를 일일이 수동 조절하지 않고 `swing_lifecycle_ev_label_weight_policy_v1`, `swing_lifecycle_composite_ev_policy_v1` bundle로 관리한다.
- arm 정책: 완전 조합 탐색이 아니라 bounded 8-arm set으로 시작한다.
- 저장소: DB table이 source of truth이고 JSON/Markdown은 감사용 report artifact다. candidate/arm 생성 이후 label builder와 EV report가 같은 DB row를 갱신/집계한다.

## Candidate Allocation

하루 최대 후보 수는 기본 `50`개다. v1 allocation은 아래 bundle로 고정한다.

| 구분 | 비중 | 의미 |
| --- | ---: | --- |
| 생애주기 탐색 랭크(lifecycle_rank) | 60% | 기존 score 단조 가정 대신 bootstrap lifecycle score 상위 후보 |
| 다양성 탐색(diversity_exploration) | 30% | 가격 위치, blocker, 변동성 조합이 다른 후보를 강제로 포함 |
| 기존 ML 비교군(legacy_ml) | 10% | 기존 final ensemble scanner 또는 추천 모델의 선택 종목을 비교 cohort로 유지 |

이 비중은 개별 threshold가 아니라 하나의 family bundle로 본다. 변경이 필요하면 bundle version을 새로 만든다.

## Arm Set

각 후보는 8개 가상 arm으로 확장된다.

| arm_id | 진입 정책 | 수량 정책 | 청산 정책 |
| --- | --- | --- | --- |
| `arm01_next_open_equal_fixed5d` | 다음 시가 진입 | 동일 금액 | 5일 고정 |
| `arm02_next_open_vol_fixed10d` | 다음 시가 진입 | 변동성 조정 | 10일 고정 |
| `arm03_pullback_equal_fixed10d` | 눌림 지정가 진입 | 동일 금액 | 10일 고정 |
| `arm04_pullback_risk_mae_time` | 눌림 지정가 진입 | 리스크 제한 | 최대 불리폭(MAE) 또는 시간 청산 |
| `arm05_breakout_conf_trailing` | 돌파 확인 진입 | confidence 가중 | 최대 유리폭(MFE) 이후 trailing |
| `arm06_gap_fade_risk_fixed5d` | 갭 되돌림 진입 | 리스크 제한 | 5일 고정 |
| `arm07_pullback_vol_scale_recovery` | 눌림 지정가 진입 | 변동성 조정 | 회복형 추가매수 |
| `arm08_breakout_risk_mae_time` | 돌파 확인 진입 | 리스크 제한 | 최대 불리폭(MAE) 또는 시간 청산 |

## Label/Lifecycle Builder

`src.engine.swing_strategy_discovery_label_builder`가 arm 상태를 전개한다.

| 상태 | 의미 |
| --- | --- |
| `PENDING_ENTRY` | 가상 진입 조건이 아직 충족되지 않았거나 quote가 부족함 |
| `ENTERED` | 가상 진입은 됐지만 arm 청산 조건/기간이 아직 미성숙 |
| `EXITED` | arm exit policy 기준 가상 청산 완료 |
| `EXPIRED` | entry trigger가 충족되지 않아 가상 진입 실패 |

entry 정책은 다음 시가, 눌림 지정가, 돌파 확인, 갭 되돌림 4종이다. exit 정책은 5일/10일 고정, MAE stop+time stop, MFE 이후 trailing, scale-in recovery 4종이다. 같은 일자에 high/low가 동시에 trigger를 만족하면 보수적으로 불리한 순서를 적용한다.

label horizon은 `1d`, `5d`, `10d`, `policy_exit` 네 종류다. `1d/5d/10d`는 horizon close 기준 MFE/MAE/close/final return을 저장하고, `policy_exit`는 arm policy final return과 realized exit return을 저장한다. 미래 quote가 부족하면 `pending_future_quotes`로 남기고 다음 postclose `--refresh-matured` 실행에서 idempotent하게 채운다.

entry-day 관찰 bucket은 일봉 OHLC proxy로만 만든다. `entry_price_delta_bucket`, `entry_day_gap_bucket`, `entry_day_low_from_entry_bucket`, `entry_day_close_from_entry_bucket`, `stop_touch_outcome_bucket`, `entry_position_opportunity_bucket`을 `arm_features`와 `label_features`에 남긴다. `stop_touch_outcome_bucket`은 `no_touch`, `wick_stop_recovered_close_above_stop`, `close_below_stop`, `not_entered_or_pending` 중 하나다. `entry_position_opportunity_bucket`은 흔들리는 종목을 제외하기 위한 값이 아니라 `pullback_retest_observation`, `momentum_chase_observation`, `discount_entry_observation`처럼 더 좋은 가격 또는 모멘텀 진입 위치를 비교하기 위한 source-only 관찰값이다.

이 관찰 bucket은 source-only다. 후보 제외, 변동성 종목 제외, 시간대 hard gate, stop 완화/강화, dry-run guard 변경, real canary approval standalone 근거로 쓰지 않는다. 기존 `MAE_STOP_PCT=-3.0` exit policy 동작도 바꾸지 않는다. 실제 09:00~09:30 분봉 판정은 별도 source-only v2 대상이다.

## EV Report

`src.engine.swing_strategy_discovery_ev_report`가 arm/entry/sizing/exit/selection/legacy/position/volatility/block/sector/theme 축으로 누적 EV를 집계한다.

primary metric은 `equal_weight_avg_final_return_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct`다. 보조 진단은 `diagnostic_win_rate`, `entry_fill_rate`, `expired_rate`, `downside_p10_pct`, `mae_p90_pct`다.

`morning_turbulence_analysis`는 entry-day 관찰 bucket별 source-only EV를 별도로 집계한다. metric contract는 `metric_role=sim_probe_ev`, `decision_authority=swing_sim_exploration_only`, `window_policy=rolling_90d`, `sample_floor=5`, `sample_floor_behavior=hold_sample`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `allowed_runtime_apply=false`다. forbidden use에는 시간대 hard gate, runtime threshold apply, stop 완화/강화, dry-run guard 변경, real canary 단독 승인, 변동성 종목 제외가 포함된다.

리포트는 아래 세 결론을 명시한다.

- `surviving_arms`: sample floor 충족, EV 양수, downside guard 통과 arm
- `legacy_vs_discovery`: 기존 ML cohort와 discovery cohort 비교
- `avoid_buckets`: 표본 충분하고 EV/꼬리손실이 나쁜 후보군

이 결과는 source-only다. 실주문, `recommendation_history` 대체, runtime env apply 권한이 없다.

## DB Schema

신규 table은 세 개다.

- `swing_strategy_discovery_candidates`: source date, stock code, selection arm, diversity bucket, 기존 ML feature, lifecycle bootstrap score, source feature contract를 저장한다.
- `swing_strategy_discovery_arms`: candidate별 8개 가상 전략 arm과 가상 진입가/수량/금액, status를 저장한다.
- `swing_strategy_discovery_labels`: label horizon별 MFE/MAE/close/final return, realized exit return, scale-in delta, label feature를 저장한다.

`recommendation_history`는 유지한다. discovery sim은 별도 table을 사용해 기존 추천 기록과 섞지 않는다.

## Report Artifact

생성 경로:

- `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.json`
- `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.md`
- `data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_YYYY-MM-DD.json`
- `data/report/swing_strategy_discovery_labels/swing_strategy_discovery_labels_YYYY-MM-DD.md`
- `data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_YYYY-MM-DD.json`
- `data/report/swing_strategy_discovery_ev/swing_strategy_discovery_ev_YYYY-MM-DD.md`
- `data/runtime/swing_strategy_discovery/sector_theme_map_YYYY-MM-DD.json`

`sector_theme_map`은 수동 섹터 reference와 키움 테마 reference를 합친 cache다. 수동 파일은 `KORSTOCKSCAN_SWING_SECTOR_MANUAL_FILE`로 지정하거나 `docs/reference/swing_sector_manual_YYYYMMDD.{csv,xlsx}`, `docs/reference/data_5126_YYYYMMDD.xlsx`, `docs/reference/data_5039_YYYYMMDD.csv` 순서로 탐색한다. 현재 `data_5126_20260520.xlsx` 포맷은 `Issue code`, `Market type`, `Sector code`, `Industry` 컬럼을 사용한다. `ka90002` 구성종목 fan-out 조회는 장후 기본 경로에서 사용하지 않는다.

report는 candidate/arm count, allocation breakdown, diversity distribution, forbidden uses, source 경로, quote feature coverage warning을 담는다. report artifact는 감사용이며 runtime apply 권한이 없다.

## 금지선

- broker 주문 제출 금지
- real execution 품질 주장 금지
- Telegram BUY 알림 금지
- threshold-cycle runtime apply 금지
- 기존 recommendation_history 대체 금지
- 기존 ML score를 단독 BUY/SELL 근거로 사용 금지

## 실행 명령

schema 생성:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.swing_strategy_discovery_schema
```

리포트와 DB row 생성:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.swing_strategy_discovery_sim --date YYYY-MM-DD
```

수동 섹터 reference 단독 확인:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.swing_sector_theme_source --date YYYY-MM-DD --codes 005930 000660 --manual-sector-file docs/reference/data_5126_YYYYMMDD.xlsx --no-external
```

성숙 label 갱신:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.swing_strategy_discovery_label_builder --date YYYY-MM-DD --refresh-matured
```

EV report 생성:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.swing_strategy_discovery_ev_report --date YYYY-MM-DD
```

운영 DB를 건드리지 않는 검증:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.swing_strategy_discovery_sim --date YYYY-MM-DD --no-persist --output-dir /tmp/swing_strategy_discovery_sim
```

## 자동화체인 편입

`deploy/run_threshold_cycle_postclose.sh`는 `swing_daily_simulation` 이후 discovery sim, label builder, EV report를 실행한다. `threshold_cycle_ev`, `runtime_approval_summary`, `code_improvement_workorder`는 요약/source-only order만 소비한다. `THRESHOLD_CYCLE_RUN_SWING_STRATEGY_DISCOVERY=false`로 끌 수 있지만 기본값은 `true`다.
