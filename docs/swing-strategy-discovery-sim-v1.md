# Swing Strategy Discovery Sim v1

## 목적

`swing_strategy_discovery_sim_v1`은 기존 스윙 머신러닝(ML) 모델이 고른 소수 종목을 그대로 신뢰하지 않고, 스윙 후보 전체를 가상 생애주기(lifecycle) 실험 대상으로 넓혀 진입, 보유, 추가매수, 청산 조합의 기대값(EV)을 찾기 위한 시뮬레이션 framework다.

v1은 실주문 전환 기능이 아니다. 모든 row는 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false`, `decision_authority=swing_sim_exploration_only`를 유지한다.

## 확정 설계

- 후보군(universe): 기존 추천 진단 CSV의 safe pool 전체.
- 기존 ML 모델: 최종 selector가 아니라 낮은 가중치의 feature 및 비교 cohort로만 사용한다.
- 다양성(diversity): v1은 가격 위치 태그, 기존 blocker, 변동성 bucket을 필수 축으로 사용한다.
- 섹터/테마: v1 row에 `sector`, `industry`, `theme_tags`를 수집하고, v2에서 필수 확장 축으로 다룬다.
- 가중치 정책: 개별 수치를 일일이 수동 조절하지 않고 `swing_lifecycle_ev_label_weight_policy_v1`, `swing_lifecycle_composite_ev_policy_v1` bundle로 관리한다.
- arm 정책: 완전 조합 탐색이 아니라 bounded 8-arm set으로 시작한다.
- 저장소: DB table이 source of truth이고 JSON/Markdown은 감사용 report artifact다.

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

## DB Schema

신규 table은 세 개다.

- `swing_strategy_discovery_candidates`: source date, stock code, selection arm, diversity bucket, 기존 ML feature, lifecycle bootstrap score, source feature contract를 저장한다.
- `swing_strategy_discovery_arms`: candidate별 8개 가상 전략 arm과 가상 진입가/수량/금액, status를 저장한다.
- `swing_strategy_discovery_labels`: 향후 label horizon별 MFE/MAE/close/final return을 저장한다. v1에서는 schema를 먼저 열고 label 산출은 후속 단계에서 채운다.

`recommendation_history`는 유지한다. discovery sim은 별도 table을 사용해 기존 추천 기록과 섞지 않는다.

## Report Artifact

생성 경로:

- `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.json`
- `data/report/swing_strategy_discovery_sim/swing_strategy_discovery_sim_YYYY-MM-DD.md`

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

운영 DB를 건드리지 않는 검증:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.swing_strategy_discovery_sim --date YYYY-MM-DD --no-persist --output-dir /tmp/swing_strategy_discovery_sim
```

## 후속 단계

1. label builder를 추가해 다음날/5일/10일 MFE, MAE, close return, final return을 채운다.
2. `swing_lifecycle_composite_ev_policy_v1` 기준으로 arm별 기대값(EV)을 산출한다.
3. sector/theme v2 source를 보강해 diversity bundle에 편입한다.
4. 장후 자동화체인에는 source bundle/report로만 연결하고, 실주문 또는 runtime apply는 별도 approval artifact 없이는 열지 않는다.
