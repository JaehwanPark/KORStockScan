# 2026-04-09 Scalp Remaining Plan

기준 시각: `2026-04-09 16:10 KST`
범위: `스캘핑 매매`만 포함, `스윙` 과제는 제외
최종 목적: `기대값/순이익 극대화`
현재 단계: `1단계 - 음수 leakage 제거 + 주문전 차단 구조 분해`

## 오늘 잔여 시간단위 작업

| 시간대 | 작업 | 판단 기준 | 산출물 |
| --- | --- | --- | --- |
| `17:30~18:30` | 익일 장전 실행안 확정 | `내일 바로 바꿀 것`과 `관찰 유지할 것`을 분리 | `2026-04-10` 장전 실행 체크포인트 |

## 오늘 완료된 시간단위 작업

| 시간대 | 완료 내용 | 산출물 |
| --- | --- | --- |
| `12:15~13:00` | `12:00` 스냅샷 해석 고정, `fallback` 손익과 `BUY 후 미진입` 기회비용을 함께 보는 기준 확정 | 체크리스트 `12:00` 해석 섹션 |
| `13:00~14:00` | `trade_review` 정합성 점검, `GOOD_EXIT`와 단순 손실 분리 해석 축 추가 | 정합성 메모, 원격 `post-sell` 반영 |
| `14:00~15:20` | `latency guard miss` 전수 집계 완료, 로컬/원격 JSONL 기준 비교 가능 상태 확보 | 전수 집계표, 원격 비교 메모 |
| `15:30~16:10` | 장후 스캘핑 canary 1차 결론 작성, 원격 raw snapshot 비교 반영 | 체크리스트 장후 결론, 익일 원격 수집 자동화 |
| `16:10~16:20` | `latency -> dynamic strength -> overbought` 완화 우선순위 확정 | 우선순위 메모, 익일 장전 전 검토축 고정 |

## 완화 우선순위 확정

| 우선순위 | 축 | 오늘 판정 | 근거 | 내일 원칙 |
| --- | --- | --- | --- | --- |
| `1` | `latency guard` | 최우선 완화 검토 | `latency_block 13건`, 전수 집계 `1,253건 / 21종목`, `MISSED_WINNER` 비중도 높음. 다만 원격도 공유 종목군에서는 `ws_age_ms/stale`가 더 나쁜 경우가 있어 단일 `ws_age` 완화는 부적절 | 전역 완화 금지, `quote_stale=False` 또는 특정 분포 구간 중심의 조건부 완화안 1~2개만 검토 |
| `2` | `dynamic strength` | 제한적 완화 검토 | `blocked_strength_momentum 5건`, `missed_winner_rate 60.0%`. 빈도는 `latency`보다 낮지만 기대값 훼손 가능성이 큼 | `threshold_profile`, `momentum_tag`별로 분리해 국소 완화 후보만 검토 |
| `3` | `overbought` | 관찰 유지, 즉시 완화 보류 | `blocked_overbought 1건`이지만 `MISSED_WINNER 100%`. 표본이 너무 적어 바로 완화하면 과잉 반응 위험이 큼 | 추가 표본 확보 전 실전 완화 금지, 장후 사례 메모만 유지 |

- 제외/후순위 메모:
  - `fallback 수량 canary`는 오늘 음수였지만, 병목 주원인이 `수량축` 단독으로 확정되지 않아 우선순위에서 제외한다.
  - `trade_review`/`buy_pause_guard`의 `fallback cohort` 정합성 보정은 완화안과 별개인 `운영 필수 보정`으로 내일 장전 전 확인 대상으로 둔다.

## 내일 시간단위 계획 작업

| 시간대 | 작업 | 판단 기준 | 산출물 |
| --- | --- | --- | --- |
| `08:00~08:30` | 전일 결론 재확인 및 배포 상태 점검 | 전일 장후 결론과 코드/설정 상태 일치 여부 | 장전 상태 확인 메모 |
| `08:30~08:50` | `fallback` canary 유지 여부 최종 확인 | `entry_mode` 복원 결과, 전일 손익, 미진입 비용을 종합해 유지/조정 결정 | 장전 적용 여부 확정 |
| `08:50~09:00` | 모니터링/비교 리포트 경로 점검 | `10:00` 스냅샷, `server_comparison`, `buy pause guard` 준비 여부 | 장전 운영 준비 완료 |
| `09:00~09:30` | 장초 체결/미진입 흐름 관찰 | `AI BUY`, `entry_armed`, `latency_block`, `blocked_strength_momentum` 초기 패턴 확인 | 장초 관찰 메모 |
| `09:30~10:00` | 1차 압축 모니터링 | `fallback` 실체결 수, `BUY 후 미진입` 누적, `latency` 빈도 | 09:30~10:00 판단기준표 |
| `10:00~10:10` | `10:00` 스냅샷 해석 | `손익 표본`과 `미진입 비용` 동시 해석 | 10:00 중간 결론 |
| `10:10~12:00` | 장중 병목 추적 | `latency guard`, `dynamic strength`, `overbought` 중 오늘 주병목 확인 | 병목 우선순위 업데이트 |
| `12:00~12:20` | `12:00` 스냅샷 해석 | `canary 유지/강화 보류/롤백 검토` 중 임시 결론 | 12:00 1차 실질 해석 |
| `15:20~15:30` | 원격 `songstockscan` 로그 자동 수집 | `fetch_remote_scalping_logs`가 원격 `pipeline_events`, `post_sell`, `receipts`를 수집해 `tmp/remote_YYYY-MM-DD`로 해제하는지 확인 | 원격 비교 원본 확보 |
| `15:30~16:30` | 장후 최종 결론 | 당일 손익 + 기회비용 + 체결 품질 + 비교 리포트 반영 | 장후 스캘핑 결론 |

## 익일 장전 실행안 확정본

| 구분 | 항목 | 내일 처리 | 필수 확인 | 비고 |
| --- | --- | --- | --- | --- |
| `즉시 유지` | `fallback 수량 canary` | `유지` | 장전 전 `trade_review`/`buy_pause_guard`의 `fallback cohort` 정합성 재확인 | 오늘 음수였지만 주병목 단독 원인 아님 |
| `즉시 유지` | `overbought` 차단 | `그대로 유지` | 추가 표본 확보 전 완화 금지 | 오늘 표본 `1건`으로 부족 |
| `즉시 유지` | 공통 hard time stop | `shadow-only 유지` | 실청산 ON 금지 확인 | 오늘과 동일 |
| `장전 필수 확인` | `trade_review` 정합성 | `우선 점검` | `entry_mode`, `exit_rule`, `fallback` cohort가 리포트/guard에 같은 수치로 보이는지 확인 | 실패 시 당일 해석 신뢰도 하락 |
| `장전 필수 확인` | 원격 수집 경로 | `유지` | `2026-04-10 16:00` 자동 수집 cron과 로그 경로 확인 | 원격 비교 연속성 확보 |
| `조건부 검토` | `latency guard` | `후보안 1~2개만 검토` | 전역 완화 금지, `quote_stale=False` 또는 특정 분포 구간 중심인지 확인 | 1순위 병목 |
| `조건부 검토` | `dynamic strength` | `국소 완화 검토` | `threshold_profile`, `momentum_tag`별 분리 검토 여부 확인 | 2순위 병목 |
| `보류` | `overbought` 완화 | `보류` | 표본 추가 전 반영 금지 | 3순위 |

### 금일 실행계획 미완료건 처리

| 미완료 항목 | 상태 | 내일 처리 시점 | 처리 원칙 |
| --- | --- | --- | --- |
| 공통 hard time stop 후보안 영향 추정 | `이월` | 장후 | 장전 적용 대상 아님, 백테스트 후 판단 |
| `AI WAIT/latency/liquidity` missed case 요약표 | `부분 완료 후 이월` | 장중/장후 | 오늘 수집본 유지, 내일 표본 추가 후 보강 |
| 스윙 Gatekeeper missed case 정리 | `이월` | 장후 | 스캘핑 장전 실행안과 분리 |
| 스윙 missed case 요약표 + threshold 완화 검토 | `이월` | 장후 | 스윙 전용 문서로 처리 |
| 스캘핑 진입종목의 스윙 자동전환 검토 프레임 | `이월` | 장후 | shadow 검증 전 실전 반영 금지 |

### 운영 반영 전 필수 확인

1. `trade_review`와 `buy_pause_guard`에서 `fallback` 실체결 수가 같은지 확인
2. `latency` 완화안이 전역 완화가 아닌지 확인
3. `quote_stale=True` 구간이 완화 대상에 섞이지 않았는지 확인
4. `dynamic strength`는 `momentum_tag`/`threshold_profile`별 분리 검토인지 확인
5. `overbought` 완화가 실행안에 포함되지 않았는지 확인

### 추가 검토 후 반영할 사항

1. `latency` 완화 후보안 세부 수치
2. `dynamic strength` 국소 완화 범위
3. `fallback` cohort 정합성 보정 결과에 따른 canary 해석 조정
4. 원격 `trade_review/post_sell` 차이를 활용한 청산 품질 보정 여부

## 잔여 일단위 계획 작업

| 일자 범위 | 핵심 작업 | 완료 기준 | 비고 |
| --- | --- | --- | --- |
| `D0 (오늘)` | `fallback canary` 해석을 `손익`만이 아니라 `미진입 기회비용`까지 포함한 기준으로 고정 | 장후 결론에 `실현손익 + 기회비용 + 정합성 이슈`가 같이 기록됨 | 오늘 최우선 |
| `D0 (오늘)` | `빠른 손절/빠른 청산`이 실제로는 적정 종료였는지 구분하는 해석 축 추가 | `post_sell_feedback` 기준 `GOOD_EXIT`와 단순 손실을 분리 기록 | 비교서버 사례 반영 |
| `D1` | `trade_review`/`buy_pause_guard`의 `fallback cohort` 정합성 보정 | `fallback` 실체결이 리포트와 guard에 같은 수치로 잡힘 | 리포트 신뢰성 복구 |
| `D1~D2` | `latency guard miss` 완화 후보안 정리 | `latency miss` 표본군에 대한 완화안 1~2개와 리스크 메모 작성 | 스캘핑 실행 병목 우선 |
| `D1~D2` | `dynamic strength` 차단 후보안 정리 | `blocked_strength_momentum` 표본의 missed-winner 비중 기반 완화안 작성 | 2순위 |
| `D2~D3` | `overbought` 차단 필요성 재평가 | `엠플러스`류 표본이 일회성인지 반복성인지 확인 | 3순위 |
| `D2~D4` | `본서버 vs songstockscan` 비교를 A/B 참고축으로 축적 | 최소 2거래일 이상 `거래수`, `후속평가 건수`, `미진입` 차이 누적 | benchmark가 아니라 참조축 |
| `D3~D5` | `fallback` canary 확대/유지/해제 판단 | `fallback 전용 표본`이 분리 집계되고, `평균손실/손실총액/기회비용`까지 같이 해석 가능 | 그 전까지는 성급한 결론 금지 |

## 운영 메모

- 오늘 12시 기준 스캘핑 해석의 핵심은 `손익 음수` 자체보다 `주문전 차단 구조`가 더 큰 음수 기여를 만들고 있다는 점이다.
- 현재 우선순위는 `fallback 수량축 추가 조정`보다 `latency miss`와 `fallback 표본 복원 정합성`이다.
- `profit_rate NULL -> 0` 같은 fallback 정규화가 해석을 왜곡할 수 있으므로, 비교 리포트는 계속 `safe-only` 기준으로 본다.
- 비교서버 기준 `에스앤에스텍(101490)`은 `2026-04-09 14:38:52` 진입 후 `43초` 보유, `-0.23%` 종료였지만 `post_sell_feedback`에서는 `GOOD_EXIT`로 평가됐다. 따라서 `빠른 손절/빠른 청산`은 손익 부호만이 아니라 `매도 후 1/3/5/10분 경로`까지 보고 적정성 여부를 분리해야 한다.
- 비교서버 `entry-pipeline-flow` API가 비어 있었던 원인은 `sniper_state_handlers_info.log`에 `[ENTRY_PIPELINE]` 텍스트 로그가 없었기 때문이다. 하지만 원격 `pipeline_events_2026-04-09.jsonl` 원본을 확보했으므로, `latency guard miss` 전수 비교는 `API`가 아니라 `JSONL 원본` 기준으로 수행한다.
- 동일 기준(`09:00~15:20`, `ENTRY_PIPELINE`, `stage=latency_block`, `decision=REJECT_DANGER`) 전수 집계 결과는 로컬 `1,253건 / 21종목`, 원격 `481건 / 12종목`이다. 겹치는 상위 종목은 `희림`, `비츠로셀`, `티엘비`, `RF머트리얼즈`, `에스앤에스텍`이고, 로컬 상위였던 `테크윙`, `롯데케미칼`, `머큐리`, `SK텔레콤`은 원격 상위군과 다르다.
- 겹치는 종목 기준으로도 원격이 일관되게 더 낫지는 않다. 예를 들어 `희림`은 로컬 `164건 / ws_age_avg=273.1ms / stale=2`인데 원격은 `91건 / 525.2ms / stale=18`, `RF머트리얼즈`는 로컬 `56건 / 322.0ms / stale=0`인데 원격은 `21건 / 1730.0ms / stale=15`다. 따라서 로컬/원격 차이는 단순 네트워크 품질보다 `후보 종목군`, `진입 시도 분포`, `실제 퍼널 진입 수` 차이로 해석하는 편이 맞다.
- 원격 서버는 `15:45` 기준 `trade_review_2026-04-09.json`, `post_sell_feedback_2026-04-09.json`, `performance_tuning_2026-04-09.json` 스냅샷이 생성된다. raw snapshot 직접 비교 결과 `trade_review`는 로컬 `4건/-18,590원`, 원격 `2건/215원`, `post_sell_feedback`은 로컬 `good_exit_rate=25%`, 원격 `100%`, `missed_upside_rate`는 로컬 `50%`, 원격 `0%`였다. 반면 `performance_tuning` metrics diff는 `0건`이었다.
- 내일 `2026-04-10 16:00 KST`에는 원격 로그+스냅샷 자동 수집 1회 실행이 예약되어 있다. 실행 명령은 `python -m src.engine.fetch_remote_scalping_logs --date 2026-04-10 --include-snapshots-if-exist`이며, 로그는 `logs/remote_scalping_fetch_20260410_1600.log`에 남긴다.
