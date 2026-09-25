# 스캘핑 트레일링 4축 과거 원천 가용성 조사

기준일: 2026-09-25 KST. 읽기 전용 조사. 범위는 clean baseline 이후 메인 실거래 완료 포지션이며, 가격 경로 진단과 정책 변경 근거를 분리한다.

## 확인한 보존 원천

| 원천 | 관측 | 판정 |
| --- | --- | --- |
| `data/report/monitor_snapshots/holding_exit_observation_2026-09-23.json` | 완료·유효 수익률 329행, `completed_population_quality.complete=false`; 여러 거래일의 완료 census가 구형·미봉인이고 일부 일자 trade review snapshot이 없다. | 329를 엄격 완료 모수로 승격 불가 |
| `data/report/monitor_snapshots/trade_review_2026-09-23.json` | 9/23 완료 projection 8행. 6행에 정확한 SELL 시각이 있고 2행은 없다. 8행 모두 구형 projection으로 `strict_completion_status`, BUY/SELL fill legs, 구조화 trailing source 영수증이 없다. `exit_signal.inferred=true` 8행. | 현행 공통 BUY/SELL 수량·비용 계약과 시점별 4축 재생을 통과한 행 0 |
| `data/report/monitor_snapshots/trade_review_2026-09-24.json`, `...09-25.json` | 완료 projection 0행. | 새 자연 적격 완료 표본 0 |
| `data/pipeline_event_summaries/pipeline_event_summary_2026-09-23.jsonl`, `data/runtime/sentinel_event_cache/holding_exit_sentinel_events_2026-09-23.jsonl` | 보존된 요약·sentinel 파일에서 `scalp_trailing_input_transition` 문자열 확인 0건. 437 MB 압축 원시 partition은 아래 현행 trade-review 빌더의 정상 구조화 projection 경로로 한 번 다시 읽었다. | 요약·sentinel만으로 peak/bid/score/잔량의 시각순 경로 복원 불가 |
| [9/24 분봉 API 조사](2026-09-24-tp-post-sell-minute-api-audit.md) | 분봉의 후행 고가는 가격 진단용이며 초 단위 first crossing·실행가능 bid/잔량은 없다. | `historical_diagnostic`에 한정 |

9/23 projection 8행을 현재 `_strict_completed_reasons`로 재판정하면 8행 전부 `source_gap_real_custody_unproven`과 `source_gap_strict_completion_receipt_missing`이다. 마지막 2행에는 정확 비용·SELL 수량 보존 결손도 있다. 이 결과는 9/23 보고서의 329건을 0건의 경제 성과로 바꾸는 뜻이 아니다. **현재 보존 형태에서 4축 정책 비교에 필요한 엄격 기초 모수와 시각순 원천이 0건**이라는 뜻이다.

현행 `build_trade_review_report('2026-09-23')`로 압축 원시 partition까지 다시 읽은 추가 투영에서도 완료 projection은 8행, `buy_fill_legs=0`·`sell_fill_legs=0` 8행, `strict_completion_status=excluded` 8행이었다. 구조화 원천 상태는 `source_gap_structured_projection_malformed`, 동일 원천 영수증 hash는 `0256ea032731fe985d4be9a6725d2b1fbfd4798c39e84638530c767aaefa42be9`다. 현재 엄격 계약의 첫 결손은 BUY 체결 권한/비용, SELL 체결 권한·수량 보존과 실거래 custody이며, 과거 저장 보고서의 6건 비용 표시를 새 체결 leg 증거로 소급할 수 없다.

## 축별 최초 결손과 후속 경로

| 축 | 과거 확인 범위 | 최초 결손 |
| --- | --- | --- |
| 시작 | 9/23 보존 완료 행 및 기존 분봉 가격 진단 | 봉인 완료 census·BUY/SELL leg·직접 신호·처음 arm의 시각순 호가 |
| 점수 경계 | 위와 같음 | 평가별 유효 AI 원점수·TTL·provider와 강약 경계 변화 |
| 약폭·강폭 | 위와 같음 | 평가별 peak/bid/최우선 잔량 및 후보별 최초 crossing; 늦은 후보의 실제 청산 뒤 실행가능 경로 |

새 장후 보고서의 `trailing_historical_source_availability`는 DB 완료/유효/엄격 적격 ID, 기초 모수 탈락 사유, 4축 원천 탈락 사유, 직접·복원 등급을 분리한다. 원시 로그나 추가 영수증으로 9/23 결손을 ID별 복원할 수 있다면 엄격 기초 계약부터 다시 대사해야 한다. 정책 후보는 `historical_direct|historical_reconstructed`의 비용 후 paired 결과와 독립 날짜 검증을 통과한 경우에만 검토한다. 현재 조사에서는 임계치·선택 정책·PID를 변경하지 않았다.

후속 요청으로 [과거 완료 표시 중립 추정 시뮬레이션](2026-09-25-scalp-trailing-legacy-neutral-scenario-review.md)을 별도 진단 블록에 구현했다. 추정 결과 312건의 계산 가능 표시는 위 엄격 적격 0건을 대체하거나 실제 체결 비용 EV로 승격하지 않는다.
