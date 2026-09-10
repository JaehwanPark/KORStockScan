# 2026-09-10 10:50 장중 수정 재리뷰

요청: 장중 수정 사항을 코드리뷰하고 결함이 없어질 때까지 수정·재검증. 범위는 [10:50 모니터링](2026-09-10-intraday-monitoring-1050.md)의 R1 매도 outbox·R2 packet 지연 계측·R3 테스트 저장 경로 격리와 직접 producer/consumer다. Plan Rebase §1~§8, 당일 checklist 목적/강제 규칙과 `korstockscan-review-gate`를 적용했다. 별도 작업 중인 Entry bootstrap/PREOPEN, adaptive 주문·위젯·registry 변경은 이번 코드 승인 범위가 아니다.

## 재현된 결함과 수정

| Finding | 수정 전 재현 | 보완 및 재검토 |
|---|---|---|
| F1 / 높은 중요도: recheck terminal companion의 잘못된 ACK | 원본 sell_completed의 exact 검증 이후 companion은 append 성공 bool만 보았다. 다른 attempt·손익·비용·권한·stage·record·symbol 또는 fields가 없는 payload도 durable outbox를 해제할 수 있었다. | [sniper_execution_receipts.py](../../src/engine/sniper_execution_receipts.py)는 기존 terminal 입력과 귀속 필드를 emit 전에 문자열 계약으로 고정한다. pipeline/stage/record/symbol, raw append 상태와 모든 고정 필드가 일치해야 ACK한다. 불일치는 기존 pending/replay에 남고 새 매도 주문을 만들지 않는다. |
| F2 / 보통 중요도: 선택적 packet 시각이 stale 기록을 누락 | infinite packet clock의 float→int 변환이 OverflowError를 내어 0B/0D 모두 기존 INVALID_EXCHANGE_TIMESTAMP 대신 ISOLATED_ERROR가 됐다. boolean/소수형 강제 변환도 거짓 지연 시각을 만들 수 있었다. | [forward_collector.py](../../src/engine/scalping/micro_reversion/forward_collector.py)는 로컬 adapter 계약의 양수 정수 epoch ms만 받는다. bool/문자열/소수/NaN/inf/역전/신뢰 결손은 null로 남기고 기존 stale 판정·제외 count·bounded tail을 보존한다. |

최초 반례 실행은 56 FAIL/18 PASS였다. F1 변조 9종×금액·비용 표현 6조합의 54실패와 F2 infinite의 0B/0D 2실패다. 수정 후 해당 74개가 통과했고, pipeline 변조·boolean·fractional·numeric-string을 추가한 최종 회귀도 통과했다. R1의 금액 int/float/string 및 비용률 원본 표현 보존을 유지하며 실제 validator를 무조건 성공으로 모킹하지 않는다. 정상 legacy attribution과 v3 full-position, full/partial/mixed/불완전 경제성 경계도 기존 시험으로 재확인했다.

R3는 운영 sim/probe 저장 경로가 공통 pytest tmp 아래로 이동하는지, 실제 persist가 두 임시 파일에만 기록하는지, default-path 동일성 및 과거 session 차단이 유지되는지를 추가 시험했다. 테스트 격리는 과거 sim source 손실 복원이나 sim 경제성 승인이 아니다.

## 독립 재검증

- 최종 8개 관련 test module: **578 PASS / 퇴역 ADM/LDM fixture 18 SKIP / warning 1**. 결과 `tmp/intraday-review-20260910-1050/final-tests.log`. 앞선 중복 실행 숫자를 더하지 않는다.
- 기존 매도 원장 `leg_sha256=d64e06983c4e1627c11123f2e0c11987017c80f95ed6b9fbd04230d19c7d9a3c`를 in-memory emitter로 검증: `sell_completed → entry_opportunity_recheck_sell_completed` 성공. `offline-leg-final.json`에 원본 hash와 반환 payload를 보존했다. 운영 원장·pipeline 쓰기/ACK는 하지 않았다.
- [최종 계측 측정](2026-09-10-micro-packet-review-latency-validation.json.txt): valid0B 25,000회 내부 p95 최대0.025681ms/p99 최대0.047222ms, queue drop/worker error0. rejected0B 5,000회 p95 0.009705ms/p99 0.015751ms; rejected0D 5,000회 p95 0.009073ms/p99 0.014486ms. 각각 tail64/전체거절5000을 유지했다. 기존 한도 p95 1ms/p99 2ms와 freshness10초를 바꾸지 않았다.
- 측정 receipt의 source SHA를 실제 WS/collector 파일과 검증하는 회귀를 추가했다. 과거 [첫 측정](2026-09-10-micro-packet-diagnostic-latency-validation.json.txt)과 frozen 운영 baseline은 보존했다. 이 synthetic 측정은 전체 WS adapter/live 부하 또는 비용후 수익성 검증이 아니다.
- Kiwoom 공식 HEAD 재확인: `234560d213acd8871ae344b5481aecd2f30287fa`. 같은 SHA의 `kiwoom/core/ws_client.py`, `kiwoom/realtime/decoders.py`, `kiwoom/realtime/packets.py` 재열람; 이전 spec/manifest 조회 근거를 보존했다. `kiwoom_docs`는 해당 revision에 없으며 wire/FID/REG/로그인 계약을 변경하지 않았다. 기록: `tmp/intraday-review-20260910-1050/official-reference.json`.
- 검토한 producer→terminal attribution→raw stringify→durable ACK/replay, adapter packet→observer rejected counter/tail→snapshot/canary 연결에서 재리뷰 후 미해결 코드 finding0. Black/compile/diff/link/print-only parser 검증은 아래 최종 receipt에 기록한다.

## 목표·자동화·반영 경계

기대효과는 정상 완료 매도의 무한 재전송을 끝내고 정확한 비용후 성과 표본을 후속 분석에 전달하며, micro 거절의 수신 전/내부 지연을 구분하는 것이다. BUY 빈도·순이익 증가를 입증한 변경은 아니다. 누락/변조 표본을 정상 수익으로 채우거나 수량·threshold·hard safety·Provider route를 바꾸지 않는다.

정상 코드가 로드되면 기존 `sniper_sync`의 durable replay가 자동으로 pending 기록을 재검증한다. 수동 원장 재작성이나 새 주문은 필요하지 않다. 이 진단 수리에 추가 경제성 floor나 PREOPEN 승격 조건을 붙이지 않았다. exact ACK는 실제 비용모델 값/귀속 보존 검사이며 주문 참여를 줄이는 새 거래 gate가 아니다.

11:18 이후 process 조회에서 PID375167(08:45:53 시작)이 남아 있음을 확인했다. 이번 작업에서 main 재기동·env/policy/lock/주문 변경은 없으며 수정 코드의 새 PID 소비·자연 ACK는 미검증이다. 기존 사용자 재기동 승인은 유지한다. 공유 작업트리의 별도 Entry/주문 변경까지 로드될 수 있으므로 전체 배포 source 검토·broker 대사 후 재기동하는 기존 선행조건을 보존한다. 새 승인을 요구하는 것은 아니다.

자연 확인은 기존 `RuntimeEnvIntradayObserve0910`, `MainAIQualitySourceGapMicroReversionForwardCollectorContinuity0910`, `SimProbeIntradayCoverage0910`에서 이어간다. code review 완료를 현재 runtime 반영·과거 원천 복원·경제성 완료로 바꾸지 않으며 OPEN ID를 중복 생성하거나 닫지 않는다.

최종 source hashes와 검증 receipt: `tmp/intraday-review-20260910-1050/review-receipt.json`.

최종 Black10파일·compile·diff·링크 검증 PASS, print-only parser 전체28건 중 당일 OPEN12개/중복0. 원천 코드10개 hash 변경0을 확인했다. 외부 sync는 실행하지 않았으며 필요 시 사용자 실행 명령은 다음 하나다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
