# Main 공통 시장원천 배포와 다음 영업일 기동 준비

확인일: 2026-10-09 KST. Owner: `MainMarketSourceConsolidation1009`.

사용자가 남은 성능 검증을 설명받은 뒤 즉시 배포와 최종 릴리스의 다음 영업일 정상기동 가능 여부 확인을 지시했다. **배포 완료, 10/12 기동 준비 PASS**다. 성능 미완료를 통과로 바꾸지 않았으며 휴장일 강제 기동은 수행하지 않았다.

## 1. 최종 릴리스와 정책

| 항목 | 확인 결과 |
|---|---|
| 선택 릴리스 | `/home/ubuntu/KORStockScan-runtime-releases/main-market-source-20261009-v1` |
| Commit | `9d6cff39d0c9455386647612c18055d6825944d6` |
| 기존 선택 | `main-market-weakness-20261009-v1`, `7e1a826318e7b8418afd2e2436b79bf2febf8f67` |
| 검증과 설치의 일치 | review-v2 통합 회귀 1,436건·Python 36파일 compile 통과, 최종 릴리스 36개 source hash 동일 |
| 미래 정책 | source/publication 10/8, effective 10/12, 기존 기계·보조 정책 내용 동일 |
| 새 bundle hash | `ac267bfb42f355a51dc3be080495336a2456c39668160d888e53b2b12ad96889` |
| 현재 활성 정책 | 갱신 전 포인터와 byte 동일; 미래 정책 조기 활성화 없음 |
| 실제 Main PID | 없음. `actual_pid_consumed=false` |

이미 발행된 미래 후보를 `stage_code_refresh`의 엄격한 원 릴리스 검증·CAS·동일 정책 비교로 새 코드에 연결했다. release-set/selection lock 아래에서 선택했다. 다른 HP 미커밋 변경을 포함하지 않았고 기존 배포된 MW 코드는 계승했다. 정책 재선정, AI/Provider 호출, 주문 또는 퇴역 실행 복원은 없다.

## 2. 장후 인계와 기동 준비

새 릴리스에서 기존 결과의 보조 consumer metadata와 정식 summary handoff를 갱신한 뒤, source 10/8의 native 최종화 `--recover-closed-target`를 수행했다. 연구 producer를 다시 실행하지 않았다. Telegram 전송은 끈 상태로 검사했다.

| 검증 | 최종 결과 |
|---|---|
| Whole strict와 controller | PASS / done, controller terminal issues 없음 |
| Cleanup와 final detector | 완료, finalization DONE `2026-10-09T17:01:05+0900` |
| 최종화 세대 별도 재검사 | PASS, `issues=[]`; `strict_checklist_generation_stale` 없음 |
| 10/12 PREOPEN | PASS, findings 없음, `validation_scope=current_full_contract`, 선택 commit 일치 |
| 예약 경로 | cron active, 필수 경로 8개 검증, 07:35 PREOPEN·07:55 Main |
| Release-set | passed; 퇴역 owner 설치 0, PID 소비는 아직 없음 |

10/12 checklist 원 봉인본 SHA `6a5428aaa23200c9a7d71ff6ac47286908237d29dfcab6d55d1dd36cb69751b9`는 canonical historical snapshot으로 보존했다. 정식 builder가 새 정책/summary를 반영한 자동 구간만 갱신했으며 자동 구간 밖의 수동 내용은 원본과 동일하다. 새 준비 영수증은 이 현재 checklist와 summary/controller에 결속된다.

최종화 chain SHA: `d2b7014cb59a1bf9ddcc355d00f82a4bdbfea9cf8faf393ce9b7b72c4e81ebf4`.
Snapshot generation SHA: `4bc277df6498e5edad7417afd6e29e73c3128759ea5ac4e8a8bc6f1ed5b735b4`.

정식 cleanup의 micro-reversion storage maintenance는 검증된 압축 22건으로 2,862,916,867 bytes를 회수했다. purge는 비활성·0건이고 원천 retention 삭제는 유보됐다. 이는 신규 연구 원장 생성이나 전략 변경이 아니다.

## 3. 남은 관측과 검증 경계

- G5: 정상 0D max 35.7422ms의 상대 기준 미통과, Main 및 장후 전체 cold/warm 성능 미계측을 동일 OPEN owner에 보존했다. 이번 배포 선행 차단으로 사용하지 않는다.
- Final detector 전체 severity는 warning이다. `code_improvement_workorder` 생성 시한 경고, `update_kospi_status=completed_with_warnings`, 변하지 않은 과거 로그 경고가 남았다. 실행 중 finalizer를 가리킨 `pending_self_audit`는 child detector 당시 상태이며 이후 DONE과 별도 세대 검사가 완료됐다. 오류 검출 전체를 무경고 PASS로 보고하지 않는다.
- 정상기동 가능 여부는 현재 선택·정책·원천·bootstrap·예약 경로 검증으로 판단했다. 10/12 실제 기동·PID 정책 소비, 자연 신호/주문/청산과 수익은 아직 관측 시점 전이다.
- 배포 source는 검증 후보와 동일하여 통합 pytest를 반복 실행하지 않았다. 문서 변경에는 print-only parser, 링크/owner/whitespace 검사를 사용하고 외부 Project/Calendar sync는 실행하지 않았다.

## 4. 근거

- [배포 최종 영수증](../../data/report/main_market_source_deployment/2026-10-09/deployment-final.json)
- [정책 동일성 및 코드 연결](../../data/report/main_market_source_deployment/2026-10-09/policy-refresh.json)
- [PREOPEN 전체 계약](../../data/report/main_market_source_deployment/2026-10-09/preopen-final-verify.json)
- [최종화 세대 검사](../../data/report/main_market_source_deployment/2026-10-09/finalization-final-verify.json)
- [필수 cron 검사](../../data/report/main_market_source_deployment/2026-10-09/cron-final.json)
- [10/12 시작 경로](../../data/report/main_market_source_deployment/2026-10-09/start-plan-final.json)
- [원 봉인본 보존](../../data/report/main_market_source_deployment/2026-10-09/historical-checklist.json)
- [선행 코드·성능 리뷰](main-market-source-consolidation-review-deployment-2026-10-09.md)
- [현재 실행 owner](../checklists/2026-10-09-stage2-todo-checklist.md)
