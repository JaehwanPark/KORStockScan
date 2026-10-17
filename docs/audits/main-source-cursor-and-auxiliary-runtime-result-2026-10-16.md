# 원천 cursor·누적 보조정책 통합 배포 결과 — 2026-10-16

19:59 KST 확인. 사용자가 승인한 연구 커밋 `7d62534e3`과 cursor 수리를 통합하여 코드리뷰·추가 수리·정규 배포·재기동을 마쳤다. 실제 선택 코드와 정책 소비, 자연 판정은 아래처럼 구분한다.

| 항목 | 실제 결과 |
| --- | --- |
| 선택 릴리스 | `source-cursor-aux-final-20261016`, commit `082096071879429bd677a1b0947f7b30d5e60dab` |
| 정규 전환 | 19:54:19 `pass/complete`. 원 PID334173에서 새 PID389707/start21197003으로 전환 |
| 정책 인계 | 정지 전 active-policy·delay·stop·holding PASS, native128 scope/76,800행/594 hits·mismatch0 |
| 새 PID 기동 | 정확 cwd/start 및 native startup consumption `ready` |
| startup observer | 새 actor389707/21197003로 기존 producer/lock에서 게시, producer_exit0/observer_exit0 |
| 전체 건강 점검 | 19:56:09 FAIL0/PASS6/WARN1. cron·프로세스·인증·로그 오류·자원·lock PASS |
| 감시 cursor | v3 실제 게시·소비. 19:56:30부터 새10분 관측창을 확보 중이며 과거 결손은 소급 복구하지 않음 |
| 원본118행 재검증 | incremental/fresh118, count/hash 일치, mismatch0 |
| 보조정책 발행 | 19:54:46 최종 overlay `8185f25786b793366fecfc27fa6b2a0f01a445c10fd1a82ab2eaf33a018c6564` |
| 보조 변경 범위 | 주성 AFTER/GE_100000/SOR와 기타 비삼성 PRE/20000_TO_100000/NXT, 2개 scope. 다른126 binding 유지 |
| 연구 호출 | 이번 발행 전 재검증·배포 중 신규0. 앞선 연구147회·누적800/800 보존 |

최종 보조 overlay는 발행·reader 검증을 통과했다. **19:59 확인까지 새 PID의 보조 consumption receipt에는 최종 overlay가 아직 기록되지 않았고, 해당 scope의 첫 자연 요청도 미관측**이다. 이를 PID 적용 완료나 주문·수익 증거로 보고하지 않는다. 기존 reader는 다음 유효 평가에서 current overlay의 변경을 감지하는 경로를 유지한다. PRE는 이미 끝난 시간대이며 자연 소비 수용은 기존 `DirectFamilySourceRepairCompactAuxiliary`/`AuxiliaryCircuitRecoveryRepair1012` owner에 남긴다. 추가 강제 판정·과거 ready 재발행·가상 PID receipt 생성은 하지 않았다.

WARN1은 기존 보유 익절 source gap들과 observer semantic coverage partial을 담는다. 감시의 provider identity 불일치1은 이전 actor에서 보존한 관측이며 새 actor의 machine issue는0, 현재 machine observation도0이다. 이를 새 PID의 정상 판정이나 과거 수리 완료로 바꾸지 않는다. source cursor의 정상 관측창 확보 pending도 별도다. `strict_checklist_generation_stale` cron 실패는 이번 점검에서 관측되지 않았다.

003540/417860의 과거 exact lease 수신 결손은 복구 증거가 없다. 19:58의 새 WS snapshot은034020_NX·196170_NX 두 등록 종목에서 실제0B/0D 수신과 연결을 보여 주었으며, 그 사실로 앞의 두 종목을 정상화하지 않는다. 기존 원천 owner `NonfixedDispatchReadinessReview1012`는 다음 같은 item/lease의 wire→정규화→native 증빙을 확인한다. local 등록, 연결 success와 귀속 unknown은 보존한다.

첫c0fb7faab 후보는 정지 전 delay source 계약에서 거부됐고 Main을 중지하지 않았다. 원PREOPEN→검토한 cursor bytes의 exact source pair를 추가하고 변조/dirty/원 digest 회귀50건 및 ordered 배포187건을 재검증한 뒤 최종 후보로 전환했다. 선행 영향3,211건과 probe71건도 통과했다. 이전 연구348건은 별도 검증 이력이다. 원 정책·PREOPEN·strict/controller·실패 기록·수동/retired custody와 hard safety를 보존했다.

구현·리뷰: [통합 검토](main-source-cursor-and-auxiliary-integration-review-2026-10-16.md). 불변 실행 증빙: [최종 runtime 검증](/home/ubuntu/KORStockScan/tmp/source-gap-cursor-aux-integration-20261016/final-runtime-verification.json), [원118행 검증](/home/ubuntu/KORStockScan/tmp/source-gap-cursor-aux-integration-20261016/actual-118-row-repair.json), [실제 보조 발행](/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/cumulative-20261016/deployment-adoption-results.json).
