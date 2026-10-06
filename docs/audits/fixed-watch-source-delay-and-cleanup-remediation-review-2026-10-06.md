# 삼성·두산 고정감시 원천 지연과 장후 정리 결함 보완

- 점검일: 2026-10-06 KST.
- 사용자 범위: 확인된 결함 수정·리뷰 반복, 체결·호가 원천 지연과 기존 `cleanup_failed` 해결. 앞서 승인한 두산 Main 배포·재기동의 후속 보완이다.
- 코드 소유: 기존 Main 상태 처리기, WS 공유 원천 생산자, offline Provider 예산 원장. 새 engine-root 모듈·별도 주문 소유자를 만들지 않는다.
- 관련 소유 문서: [두산 전환 계획](../proposals/doosan-episode-retirement-main-fixed-watch-initial-policy-plan-2026-10-06.md), [기존 전환 증빙](doosan-main-fixed-watch-implementation-review-2026-10-06.md), [당일 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md).

## 확인과 수정

1. `_entry_ai_policy_position_tag`가 삼성전자만 하드코딩했다. 두산의 실제 `SCALP_BASE` 고정감시는 `fallback_position_owner_out_of_scope`로 빠졌다. 등록된 fixed-watch 종목과 당일 종목별 admission/generation을 확인해 기존 기계정책을 선택한다. 저장 position tag·scanner population·watch ID는 바꾸지 않는다. 삼성/두산·잘못된 종목/날짜/admission/generation의 회귀검증을 추가했다.
2. 완료봉 저장과 모델 입력은 다른 증거다. 두산 canonical candidate에 완료봉 19개가 있었던 반면, 기존 fallback의 실제 요청 `076b9565…`에는 `entry_candle_context` 자체가 없었다. 요청의 분석도 completed count 0 / `unusable`였다. 이를 단순히 모델의 결손 오판으로 처리하지 않는다. 기계정책 연결을 고쳐 기존 경로 우회를 제거하고 기계의 BLOCK/RECHECK가 Provider 전에 종료되는 기존 소비 계약을 검증했다. 과거 요청에 봉을 소급 합성하지 않는다.
3. 공유 스냅샷이 불필요한 전체 history를 WS lock 안에서 복사하고 health도 중복 계산했다. dashboard에 필요한 필드와 실제 writer가 내보내는 최근 120개 exact-route 체결·호가만 동결한다. live getter의 전체 history와 writer의 출력은 유지한다. 원천 행·item/route/epoch/sequence/관측 시각을 보존하고 health 계산은 writer가 lock 밖에서 수행한다.
4. dashboard worker가 에피소드 연구 fact 저장까지 기다려 다음 스냅샷 작성을 막았다. 연구 writer를 하나의 별도 bounded worker로 분리하고 기존 cross-process writer lock을 유지한다. 느린 연구 저장 중 다음 frame을 쓰는 회귀검증, 중복 worker 차단, 시작 실패 시 guard 해제를 검증했다. 추가 API·REG·재연결·연구 거래 권한은 없다.
5. collector projection이 늦어도 frame의 생성 기준은 실제 lock 안 동결 시각이다. 관측 시각을 뒤로 옮겨 오래된 원천을 새 원천처럼 표시하지 않는다. 늦은 projection에 대한 시각 회귀검증을 추가했다.
6. 10월 3일 offline compact replay의 Provider 원장은 예약 18·정산 18개인데 필수 `.json` 요약을 발행하지 않았다. 모든 원장 생산자가 예약/정산 append와 같은 lock 안에서 canonical summary를 발행하도록 수정했다. `write_summary`도 같은 lock으로 head 경쟁을 방지한다. 발행 실패의 예약은 환불하지 않으며 새 Provider permit도 반환하지 않는다. symlink·해시·가격·예산·일자 검증을 유지한다.

## 원본 복구와 정리 수용

- 원장: `data/offline_provider_budget/ai_micro_reversion_provider_budget_2026-10-03.jsonl`.
- 기존 ledger 111337 bytes / 36개 기록과 manifest 해시를 먼저 확인했다. 리뷰된 가격 파일·원 가격 원천·budget contract를 기존 생산자로 검증하고 15:04:55에 요약만 재발행했다. ledger/manifest bytes는 동일하고 미정산 0, Provider 호출 0이다. 가격 기준 `operator_accounting_zero_cost`는 원 계약 그대로이며 매매 비용/수익 0의 증거가 아니다.
- 네이티브 closed-target finalization 복구는 현재 v3 계약과 과거 v2 선행 영수증의 차이로 정리 전에 차단됐다. 10월 2일 terminal을 v3 성공으로 합성하거나 퇴역 Widget producer를 다시 실행하지 않았다.
- 원래 immutable d0a539ab release의 소유 log runner로 정리만 재실행했다. **15:09:46, target 2026-10-02, `log_rotation_cleanup DONE`**, storage/partition/candidate/recovery/compression/data-maintenance failures 모두 0이다. 과거 FAIL receipt는 보존한다.
- 전체 과거 finalization은 `predecessor_terminal_failure`가 남으며, 정리 PASS와 구분한다. 소유 원천은 `data/report/postclose_stage_terminal/2026-10-02/*.json`이다. 다음 native 10월 6일 장후는 새 v3 source→summary→strict/controller/finalization을 검증한다. 과거 전체 chain의 성공이나 다음 정책/PID/수익은 이 정리 복구로 입증하지 않는다.

## 리뷰와 검증

- 구현 → producer/consumer·권한·concurrency 자체 리뷰 → 테스트 보완 → 재리뷰를 수행했다. 테스트 fixture의 필수 token ceiling 누락 2건을 수정한 뒤 재검증했다.
- 관련 pytest 합계 **642개 고유 case PASS**: fixed watch / 초기 policy resolver / WS / budget ledger / storage / Doosan retirement / AI transport. 최종 WS 추가 회귀 포함 194 PASS. live Provider·실주문 호출을 검증에 사용하지 않았다.
- Python compile, `git diff --check`, 체크리스트 print-only parser를 실행한다. wrapper 코드는 수정하지 않았다. 자동 sync를 실행하지 않는다.
- 26개 종목·route별 500개 체결/호가의 오프라인 모의 복사 비교: 중앙값 152.381ms → 32.954ms. exported machine-route window 동일. 네트워크 지연이나 실제 운영 개선율의 측정값으로 사용하지 않는다.
- 공식 Kiwoom 현재 HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`, 재조회 2026-10-06T14:59:03+09:00. `kiwoom/specs.py`, `kiwoom/realtime/{stream,packets,schemas,decoders}.py`를 다시 확인했다. 기존 같은 SHA의 packaged spec/core/Postman 점검을 대조했다. `kiwoom_docs`가 없는 revision이다. request/FID/route/REG/REMOVE/login/continuation/real-demo protocol은 변경하지 않는다.
- 재현 증거: `tmp/fixed-watch-source-cleanup-remediation-20261006/`의 official-reference, tests-round2/3/4, snapshot-benchmark, budget-before/recovery, cleanup-recovery-receipt. 임시 증거는 운영 artifact의 대체물이 아니다.

## 운영 후속 수용

코드 리뷰는 닫혔다. 앞서 승인된 정책 보존 handoff로 새 immutable release를 반영한 뒤 Main PID·삼성/두산 exact source·두산 machine trace·publication 지연을 확인한다. 등록 cap, stale floor, API read reserve, Provider 정책, threshold, 수량, custody, 수동 veto 및 다른 에피소드의 현재 PID는 변경하지 않는다. 짧은 자연 관찰로 종일 원천 지연 0이나 실제 수익 개선을 선언하지 않는다.


### 배포·자연 관찰 완료 기록

- 코드 commit `af780d9b5a58b3f7e263ec43e27dc1b9e239786d`, immutable root `/home/ubuntu/KORStockScan-runtime-releases/fixed-watch-source-cleanup-20261006-af780d9b`, 현재 Main PID `13210` / start ticks `88806571`. 15:13:54 당일 bootstrap/PID handoff PASS. 새 release의 공유 mount/selector를 네이티브 검증 후 재기동했다. 준비 중 selector workspace/flag 경로 오류는 재기동 전에 수정하고 다시 검증했다.
- 15:13:23 새 broker readback: 두산 잔고/미체결/미정산 intent 0, blocking retired process 없음. native release-set PASS. 다른 에피소드 PID와 policy pin은 변경하지 않았다.
- bootstrap·PREOPEN·prepared 원 파일 5개의 해시는 handoff 전후 동일하다. bundle `bd76748c…aedabe` 그대로다. 실제 DB target와 현재 PID의 공개 정책 설정으로 두 종목 모두 `SCANNER` machine-selection tag / `active_bounded_krx_canary` / `mechanistic_entry_adjudicator`를 읽기 전용 확인했다. 잘못 축약한 진단 env의 fallback을 실제 PID 결함으로 사용하지 않았다.
- 15:15:04~15:17:04 수동 조회·API 없는 121개 passive sample: PID/commit 121/121 일치, 연결 121/121, epoch 1 유지. snapshot age 중앙값 0.662초 / p95 1.156초 / 최대 1.471초. 기존 관찰의 최대 5.389초와 구분해 기록한다. 서로 다른 시간창이며 통제된 성능 개선율이 아니다.
- 삼성 quote/trade 최대 2.082/2.124초, 두산 2.223/2.667초. 두 종목 모두 3초 초과 0/121. 자연 대기·체결 희소가 사라졌다는 뜻이 아니다.
- capture lock 중앙값 201.732ms / p95 421.130ms / 최대 535.411ms, CPU 약 100.53%/한 core는 남는다. 시작 직후 23ms 한 frame이나 모의 33ms를 운영 대표값으로 사용하지 않는다. 이번 창에서 publication 3초 초과는 관측되지 않았으며 CPU의 종일 원인/수익 효과는 입증하지 않는다.
- 새 자연 fixed-watch machine trace는 이 bounded window에 미관측이다. 기동의 실제 소비·source와 읽기 전용 resolver PASS를 자연 ENTER_NOW/RECHECK/BLOCK 소비로 바꾸지 않는다. 체크리스트 A3/A4는 다음 자연 판정/장후 수용으로 OPEN이다. 과거 전체 finalization v2/v3 predecessor blocker도 보존한다.
- 마지막 소비 증거: `tmp/fixed-watch-source-cleanup-remediation-20261006/native-acceptance.json`, native intraday consumed receipt, 실제 `data/runtime/runtime_release_selection.json`, `data/runtime/kiwoom_ws_snapshot/latest.json`, 원 `logs/log_rotation_cleanup_cron.log` DONE.
