# 삼성전자 오전 2-leg 독립 매매기계

## 결정

- 기존 KORStockScan 진입·보유·청산·ADM/LDM·AI·수량결정 로직과 분리한 전용 상태기계를 사용한다.
- 하루 신규 매수 episode는 `005930` 최대 2회이며, 2026-08-13 사용자 수량 변경 이후 각 episode는 각각 10주인 두 주문(최대 20주)으로 고정한다. 첫 episode는 NXT PREMARKET이 우선이고 각 NXT leg의 취소·미체결이 계좌조회로 확인된 뒤에만 그 leg의 09:00 SOR 통합 주문을 허용한다. 두 leg가 모두 목표 청산된 경우에만 09:00~10:00 KRX 정규장 SOR 추가 episode를 최대 1회 허용한다. 기존 package/unit 파일명은 호환성을 위해 유지한다.
- 사용자의 2026-08-12 실운용 지시에 따라 전용 systemd timer로 예약한다. 기존 widget 자동매매는 중지·필터링·재기동하지 않고 자체 판단으로 계속 거래한다.

고정 정책은 다음과 같다.

| 순서 | 시장 | 기준가 | 매수가 | 주문 종료 |
|---:|---|---|---|---|
| 1 | NXT PREMARKET | 08:00 첫 1분봉 시가 | 10주: 기준가 대비 -3.0% base, 10주: base +1호가 | 08:10 |
| 2 | SOR 정규장 | KRX 09:00 첫 1분봉 시가를 가격 기준점으로 사용 | NXT 미체결 leg별 10주: -0.75% base 또는 base +1호가 | 09:30 |
| 3 | SOR 정규장 추가 episode | 첫 episode 두 leg 목표 청산 후 15봉 저점 유지·회복 신호의 확인종가 | 10주: 확인종가 -1호가, 10주: 확인종가 -2호가 | 신호 후 완료봉 3개 |

각 leg 전량 체결 후 실제 평균 체결가에서 동일 수량 지정가 매도를 별도로 낸다. 기존 baseline은 +2호가였고, 2026-08-14 09:21:07 KST 사용자 오버라이드 이후 새로 생성하는 오전·추가 episode 목표는 +3호가다. 이미 접수된 목표 주문은 취소·교체하지 않는다. 1~9주 부분체결이면 그 주문번호의 남은 매수수량만 취소·재확인한 뒤 최종 확인 체결수량만 목표 주문으로 낸다. 목표 주문 부분체결도 잔여 보유수량에 반영한다. 목표 주문에는 시간청산과 손절이 없다. 브로커에서 목표 미체결 종료가 확인되면 해당 잔여수량을 그대로 보유한다. 하나만 체결되거나 하나만 목표 청산돼도 다른 leg의 주문·보유 귀속은 독립적으로 유지한다. 목표 주문 취소, 최우선 지정가 강제매도, 다음 날 자동 목표 재주문, 보유 중 신규 episode는 하지 않는다.

09:00 이후 `SOR`는 주문 라우트다. `ka10080`의 기본 `005930` 09:00 봉은 정규장 가격 기준점으로만 사용하며, 이를 SOR 통합 체결 스트림이라고 해석하지 않는다.

## 추가 1개월 분석

키움 공식 `ka10080` 연속조회로 2026-05-06~2026-08-10 자료를 확인했다. KRX 24,868봉·66거래일, NXT 45,320봉·66거래일을 확보했고, 두 시장의 필수 시가 봉이 모두 존재한 64일만 분석했다. 2026-06-08과 2026-07-31은 KRX 09:00 봉이 없어 제외했다.

판정 규칙은 매수 분봉의 `low <= 지정가`를 체결 가능으로 보고, 같은 분봉의 고가는 시간 순서를 알 수 없어 매도 성공으로 쓰지 않았다. 기존 비교에서는 목표가가 다음 분봉 이후 12분 안에 도달했는지도 관측했다. 이는 과거 도달시간 진단값일 뿐 현재 runtime의 청산 제한이 아니다. 체결가는 지정가로 가정했으며 주문대기열, SOR 라우팅/BBO, 분봉 내부 체결 순서와 실제 수수료·세금은 재구성하지 않았다.

| 기간 | 권한 | 유효일 | 진입 | +2호가 도달 | 일 기준 성공률 | 조건부 도달률 | 평균 총수익률 | 비용 0.20% 가정 후 평균 | 중앙 도달시간 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-05-06~06-04 | archive/audit only | 20 | 14 | 14 | 70.00% | 100.00% | 0.3512% | 0.1512% | 1분 |
| 2026-06-05~08-10 | clean baseline | 44 | 35 | 35 | 79.55% | 100.00% | 0.3576% | 0.1576% | 1분 |
| 전체 참고 | 혼합, live 근거 금지 | 64 | 49 | 49 | 76.56% | 100.00% | 0.3558% | 0.1558% | 1분 |

`+1호가`는 두 기간 모두 도달률 100%였지만 비용 0.20% 가정 후 평균이 clean -0.0212%, archive -0.0244%였다. `+3호가`는 clean 91.43%, archive 92.86%로 도달 안정성이 낮아졌다. 최초 선정 시점에는 비용 여유와 반복성의 균형을 위해 `+2호가`를 baseline으로 선택했다. 2026-08-14에 사용자가 삼성전자의 clean `+3호가` 도달률 91.43%를 감당 가능한 위험으로 판단하고 비용·슬리피지 여유를 늘리도록 명시적 오버라이드했다.

추가 월의 2026-05-26 NXT 08:00 봉은 297,000원 시가, 240,000원 저가, 거래량 227주이고 다음 봉은 08:04에 시작해 297,000원 이상으로 복귀했다. 지정가 체결을 288,000원으로 가정할 때 분봉상 최대 불리폭은 -16.67%다. 이는 +2호가 도달 여부와 별개로 NXT 초기 유동성·분봉 순서 및 무손절 보유 위험이 매우 크다는 증거다. 사용자의 명시적 무손절·미청산 보유 및 2026-08-13 수량 변경 원칙을 적용해 신규 주문은 총 20주·leg당 10주 상한을 유지한다.

진입가 재평가에 따라 기존 base 지정가만으로 아랫꼬리 반등을 놓치는 위험을 줄이기 위해 `base+1호가` 실행확률 leg를 추가했다. 과거 분봉의 `low <= 지정가`는 가격 touch만 보여 주며 주문대기열 체결을 증명하지 않으므로 두 leg 성과는 runtime에서 별도 귀속한다.

## 지표 계약

- `metric_role`: counterfactual morning-pattern robustness research
- `decision_authority`: clean-baseline policy evidence; pre-baseline rows are archive/audit only
- `window_policy`: at most one two-leg NXT-premarket-first/SOR-regular-fallback entry episode per trading date; each unfilled target becomes held inventory
- `sample_floor`: at least 60 common complete dates; observed 64
- `primary_decision_metric`: `equal_weight_avg_profit_pct`, with successful-day and conditional target-hit rates as diagnostics
- `source_quality_gate`: valid unique completed 1-minute OHLCV, exact NXT 08:00 and KRX 09:00 anchors, next-bar-or-later exit label
- `forbidden_uses`: queue-fill or SOR-routing proof, real execution-quality approval, pre-baseline live promotion, provider/bot/cap/hard-safety change

## KRX/SOR 추가 진입 episode 연구

2026-06-05~2026-08-10 clean baseline의 기존 KRX·NXT 1분봉만 사용해, 현재 NXT 우선/SOR fallback 첫 episode의 두 leg가 모두 목표 청산된 날에 한해 SOR 추가 episode를 탐색했다. 원천 46거래일은 시장별 세션 커버리지를 통과했고, NXT 08:00·KRX 09:00 기준점이 모두 있는 공통 44일 중 첫 episode 완료일은 35일이다. 과거 시세를 다시 조회하거나 broker·token·runtime에는 접근하지 않았다.

직접 저점진입 계열과 회복 확인 종가분할 계열은 마지막 16일 평가에서 각각 `HELD` 3leg, 4leg가 생겨 탈락했다. 세 번째 수동적 분할가 계열은 다음 source-only 후보를 만들었다.

- 첫 episode 두 leg가 모두 `COMPLETE`인 뒤에만 1회 탐색한다.
- 최근 연속 15개 완료봉의 고가 대비 종가 하락률이 0.75% 이상이고, 저가 대비 종가 거리가 0.35% 이하여야 한다.
- setup 저가를 다음 완료봉 2개가 깨지 않고, 두 번째 확인봉 종가가 setup 종가보다 1호가 이상 회복해야 한다. 신호 탐색 종료는 10:00이다.
- 주문 기준점은 두 번째 확인봉 종가다. 기준점 -1호가와 -2호가에 각각 10주를 놓고 다음 완료봉부터 3개 봉까지만 체결 가능성을 판정한다. 체결 leg별 baseline 목표는 +2호가였으나 2026-08-14 09:21:07 KST 이후 신규 episode는 +3호가를 쓴다. 손절·시간청산은 없고, 목표 미청산은 그대로 보유한다.

28일 보정 구간은 17 episode·34 주문시도 중 완료 32leg, 미체결 2leg, 보유 0leg, 비용 0.20% 차감 `notional_weighted_ev_pct +0.113550%`였다. 마지막 16일은 12 episode·24 주문시도 중 완료 19leg, 미체결 5leg, 보유 0leg, `notional_weighted_ev_pct +0.170116%`였다. 전체 44일은 29 episode·58 주문시도 중 완료 51leg, 미체결 7leg, 보유 0leg다.

연구 산출물 자체는 [research producer](/home/ubuntu/KORStockScan/src/engine/monitoring/samsung_morning_reentry_research.py)와 [frozen report](/home/ubuntu/KORStockScan/data/report/samsung_morning_reentry_research/samsung_morning_reentry_research_2026-08-10.json)의 `source_only_no_runtime_or_order_authority` 계약에 계속 한정된다. 분봉 저가 touch는 실제 체결 증거가 아니고, 세 후보 계열이 같은 마지막 16일을 순차 평가했으므로 단일 계열의 완전 미사용 holdout으로 해석하지 않는다.

사용자가 2026-08-12 별도 실기계 반영을 승인해 [reentry state machine](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share/reentry.py)과 same-day PREOPEN authority v5를 구현했다. 연구 report SHA256 `6135da3fa280aa8188ade85c62463cc9f7c144cb4c911b68a89be41e9c6b909a`를 고정 provenance로 사용하며, 첫 episode와 추가 episode는 서로 다른 상태파일·주문번호 ledger를 소유한다. 추가 episode가 `HELD`, 열린 주문, 모호한 broker write로 남으면 다음 거래일 첫 episode도 차단한다. 2026-08-13 07:57 PREOPEN이 새 authority를 생성하고 07:59 timer가 service를 시작한 이후부터 적용한다.

## 독립성과 안전 경계

전용 구현은 [package](/home/ubuntu/KORStockScan/src/trading/samsung_morning_one_share) 아래에 있다. 기존 전략에서 공유하는 것은 전략 판단이 아니라 다음 인프라·안전 경계뿐이다.

- 캐시된 키움 인증 토큰 읽기. 발급·갱신·폐기 금지.
- 공식 KRX 호가단위 계산.
- 전역 신규매수 중단 veto.
- `005930`이 메인 봇의 명시적 `manual_operator` 제외 대상인지 확인한다. 이는 메인 봇과의 주문권 경계이며 독립 widget 자동매매를 막지 않는다.

전용 기계와 widget은 같은 계좌에서 동시에 `005930`을 거래할 수 있지만 서로의 장부를 공유하지 않는다. 전용 기계는 자기 상태 파일의 leg별 broker 주문번호만 조회하고 해당 주문의 확인 체결수량만 매도하며, 매수 잔량 취소도 그 원주문번호에만 한다. 첫 episode, 추가 episode, 각 episode의 두 leg 사이에도 주문번호·체결·목표가·보유수량을 합치지 않는다. widget 역시 자기 episode/order ledger만 소유한다. 계좌의 삼성전자 총보유수량이나 상대 전략의 주문은 어느 한쪽의 매도수량·취소대상이 아니며, 상대 주문의 존재를 신규진입 차단 사유로 쓰지 않는다.

`WIDGET_EPISODE_MARKET_WEAKNESS_ENTRY_FREEZE_OPEN_BUY_CANCEL_V2`의 당일 KOSPI `active|release_pending` latch가 확인되면 NXT·SOR 신규 leg 제출을 차단한다. 이미 접수된 leg는 전용 기계 owned-order ledger의 당일 원주문번호와 broker snapshot의 현재 미체결 잔량이 확인된 경우에만 그 원주문 잔량을 취소한다. NXT 취소가 확인돼 SOR fallback leg로 전환되더라도 latch 해제 전에는 SOR 주문을 제출하지 않는다. 부분체결분의 목표 주문, 기존 보유, SELL/target, widget·main bot·수동 주문에는 영향을 주지 않는다.

모든 broker write 전에 intent를 원자적으로 기록한다. 호출 중 프로세스가 끊긴 상태에서는 자동 재주문하지 않고 `broker_write_interrupted`로 차단한다. 전일 목표 주문이나 보유수량이 남아 있으면 다음 날 신규매수를 금지한다. 목표 주문이 전일 이후에도 브로커에서 열려 있으면 원주문일 기준으로 계속 조회하고, 미체결 종료가 확인되면 자동 매도 없이 `HELD`로 닫는다.

`ka10080` 분봉 읽기는 다른 독립 에피소드 기계와 공용 요청 제어를 사용한다. 같은 KST 분 안의 정상 완료봉 snapshot은 직전 1분 완료봉까지 포함한 경우에만 프로세스 안에서 재사용한다. 분 경계에서 아직 그 봉이 공개되지 않은 정상 응답은 캐시하지 않아 다음 bounded poll이 재조회한다. 프로세스 간 호출은 관측 요청량에 여유를 둔 로컬 0.4초 간격으로 직렬화한다. 명시적인 `1700`/HTTP 429 읽기만 최대 2회 bounded backoff 재시도하며, 실패·계약오류 snapshot은 캐시하지 않는다. 주문·취소 API는 중복 주문 방지를 위해 이 재시도 경로에서 제외한다.

키움 공식 참조는 `Kiwoom-Securities/Kiwoom-REST-API` commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`이며, `kiwoom_docs/차트.md`, `주문.md`, `계좌.md`, `kiwoom/specs.py`, `kiwoom/core`, API spec, Postman을 2026-08-13 10:07:49 KST에 다시 대조했다. 공식 `ka10080`의 `/api/dostk/chart`, `005930_AL`, 1분봉 OHLC·`cntr_tm` 계약과 `kt10000/kt10001/kt10003/kt00007`의 SOR 주문·조회 계약을 확인했다. 공식 자료는 `1700`을 요청량 오류로 정의하지만 구체적인 pacing 수치를 제시하지 않는다. 사용 API는 `ka10080`, `kt10000`, `kt10001`, `kt10003`, `kt00007`뿐이다.

## 2026-08-13 기동 설정

실주문은 다음 네 조건이 동시에 있어야 코드상 가능하다.

1. `KORSTOCKSCAN_SAMSUNG_MORNING_ONE_SHARE_ENABLED=true`
2. CLI `--live --confirm 005930_MORNING_TWO_EPISODE_LIVE`
3. `005930`의 명시적 `manual_operator` 제외 소유권
4. 당일 07:57 PREOPEN 점검에서 생성한 `data/runtime/samsung_morning_one_share_authority.json`

`korstockscan-samsung-morning-one-share.timer`는 평일 07:57에 live service와 필수 preflight service를 단일 systemd transaction으로 시작한다. 별도 preflight timer는 같은 oneshot을 두 번 실행할 수 있어 retired됐으며 installer가 기존 설치본을 disable/remove한다. preflight는 당일 KRX 거래일 여부, 공유 캐시 토큰, 메인 봇 제외 소유권, 전일 추가 episode 주문·보유 해소를 확인한다. 평일 휴장일은 authority를 만들지 않고 dependency를 fail-closed한다. 메인 봇 준비는 tmux 세션 이름만 보지 않고 exact-date threshold runtime env를 로드한 단일 `bot_main.py` PID의 `threshold_cycle_preopen_apply --verify --pid` pass를 요구하며, authority v7에 PID와 검증 상태를 함께 고정한다. preflight와 live unit은 이 PID의 `/proc` 환경을 읽는 main bot과 동일한 `User=ubuntu`, `Group=ubuntu` fs credential 계약을 사용한다. procfs 접근 자체가 거부되면 개별 env key missing으로 오인하지 않고 `runtime_env_pid_unreadable`로 차단한다. live service는 같은 transaction의 `Requires`/`After` dependency가 terminal success일 때만 이어서 시작한다. PREOPEN이 늦으면 NXT 08:00~08:10을 소급 실행하지 않고 SOR 09:00~09:30 계약 안에서만 기다리며, 09:25가 되면 authority 생성 없이 fail-closed한다. service는 첫 episode가 `COMPLETE`이면 추가 episode의 terminal 상태까지 계속 custody하고, 첫 episode가 `NO_TRADE`, `HELD`, `BLOCKED`이면 추가 매수를 열지 않고 종료한다. timer는 `Persistent=false`라 설치 시각에 이미 지난 당일 작업을 소급 실행하지 않는다.

preflight 서비스는 메인 봇의 사용자 tmux 소켓을 확인해야 하므로 `PrivateTmp` 격리를 사용하지 않는다. 실매매 서비스는 별도 임시 디렉터리 격리인 `PrivateTmp=true`를 유지한다.

전용 기계는 `COMPLETE`, `NO_TRADE`, `HELD`, `BLOCKED`에서 종료한다. `HELD`는 하나 이상의 목표가 매도가 체결되지 않아 해당 leg를 그대로 보유하는 정상 종결 상태다. 실패 재시작도 당일 권한 artifact와 원자적 write-intent 상태를 다시 검증하므로 모호한 broker write를 반복하지 않는다. active legacy 1주 상태와 leg 간 주문번호 충돌은 자동 이관하지 않고 차단한다. 전용 기계 문제가 생기면 다음 unit만 중지하며 widget unit에는 손대지 않는다.

2026-08-12 장전 점검에서 설치 unit의 구형 1주 confirmation과 오전 preflight의 tmux 소켓 격리를 보완했다. 검증된 unit을 설치하고 daemon-reload한 뒤, timer 예약 흐름에서 당일 authority와 서비스 기동을 다시 확인한다.

## 장후 진입 기준 누적 관찰

라이브 episode가 arm될 때 state의 `signal_features`에 NXT/SOR route, 실제 opening price, 적용 drawdown, 진입창, 두 leg 지정가와 해당 신호시각의 목표 호가·runtime source·policy hash를 고정한다. 2026-08-14 09:21:07 KST 이전 신호는 기존 +2호가 exact-date hash, 이후 신규 신호는 +3호가 operator-overlay hash로 별도 귀속한다. 20:10 `samsung_machine_entry_tuning` report는 당일 state와 자기 이전 일별 report만 읽으며 시세나 과거 원천을 재조회하지 않는다. 실제 주문·체결·목표 결과만 leg별로 누적하고 주문번호와 audit는 복사하지 않는다. 신규 목표주문 대사는 broker `kt00007.cntr_uv` 매도 체결단가를 state에 보존하며, 과거 목표가 proxy 표본은 진단용으로만 남아 후보 표본 하한을 충족하지 못한다. 오전은 route별 현재 drawdown 정책의 실제 결과만 관찰하며, 신호가 없던 날의 미관측 가격을 이용한 완화 threshold 반사실은 만들지 않는다.

report 자체는 `runtime_effect=false`, `allowed_runtime_apply=false`이고, clean v2 complete episode/leg 표본, source-quality preflight, rolling/cumulative EV, `HELD`·열린 주문 guard를 통과한 결과만 다음 PREOPEN candidate로 넘긴다. 오전은 관찰된 대안 정책이 없으므로 현재 NXT 3.0%·SOR 0.75% baseline만 carry-forward한다.

2026-08-13부터 `samsung_machine_entry_tuning_report_v4`는 추가 episode 상태를 `morning_reentry` cohort로 별도 수집한다. 실제 제출·체결·목표·`HELD`만 누적하고 첫 episode나 다른 시간대 표본과 합치지 않는다. 이 cohort의 fixed user-approved 정책은 관찰 전용이며 기존 morning/midday/afternoon threshold 자동변경 후보에 섞지 않는다.

preflight wrapper는 정확일자 applied artifact를 먼저 생성하고 service는 schema/hash가 검증된 오전 policy만 읽는다. 후보 없음/기간 만료는 baseline으로 닫고, 최신 후보 또는 이미 생성된 당일 artifact가 손상되면 broker gateway 생성 전에 기동을 차단한다. 당일 기본 artifact는 덮어쓰지 않고, 2026-08-14 09:21:07 KST 후부터는 명시적 사용자 오버라이드를 시간 제한 overlay로 결합해 신규 목표만 +3호가로 검증한다. 무손절·미청산 보유, 신규 leg별 10주 두 개, 독립 주문원장, provider/bot/cap/broker guard는 튜닝 축이 아니다. 목표 호가도 postclose 자동 튜닝 축은 아니며, 명시적 사용자 지시와 before/after·효력시각·rollback 기록으로만 변경한다. 배포 전부터 소유한 1주 leg는 호환 custody로 유지하며 10주로 소급 확대하거나 매도수량을 바꾸지 않는다.

```bash
sudo systemctl disable --now korstockscan-samsung-morning-one-share.timer
sudo systemctl stop korstockscan-samsung-morning-one-share.service korstockscan-samsung-one-share-preflight.service
```
