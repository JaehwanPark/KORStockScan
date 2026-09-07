# 2026-09-07 전체 소스 통합·장후 재생성 handoff

## 범위와 권한

사용자 최신 지시는 `전체 커밋&푸시&main병합` 및 필요한 장후 산출물 재생성이다. 전체 모니터링·복구·추천 intake는 이미 실행 중인 다른 세션이 소유한다. 이 통합 작업은 그 세션의 실행을 중복하거나 봇 재기동·최초 정책 승인·env/lock/provider/order 변경을 수행하지 않는다.

출발점은 `main` / `4eb27061`; 원격 main과 divergence 0을 확인했다. 별도 기능 브랜치가 없으므로 검증된 전체 source/docs 변경을 main에 직접 통합한다. 캐시·원시 데이터·실행 중 자연 생성 report/runtime 및 analysis 출력은 소스 커밋에서 제외하고 원본을 보존한다. 저장소 밖 review skill도 이 커밋 대상이 아니다.

## 검토 범위

- Main AI R0-R3 producer → current-axis registration/candidate → PREOPEN/실제 Entry AI 전달 → source-only consumer/attribution, legacy #81 OFF 유지.
- Daily threshold/WAIT 관측 → 비용 차감 counterfactual → window/source 격리 → AI review manifest → EV/PREOPEN/verifier. 신규 WAIT 관측은 실제 BUY/action 변경이 아니다.
- 장후 복구 세션의 source-only workorder owner 정정, cron/lock detector, holding force-exit 계측 및 smoothing row-exclusion/verifier. 불량 raw를 수정하거나 safety를 완화하지 않는다.
- 운영문서/체크리스트의 현재 owner, 권한, 폐기 상태와 parser 계약.

## 성능 기준 참조 보완

1차 통합 회귀 2,110 PASS / frozen baseline 1 FAIL을 확인했다. 기존 8/13 기준이 현재 collector source hash와 달랐다. 새 9/7 성능 receipt 2개의 자기해시 및 측정 source 48개가 현재 코드와 일치함을 재확인한 뒤, `configs/scalp_micro_reversion_canary_guard.toml`의 `baseline_id`와 `baseline_artifact`만 준비된 9/7 기준으로 연결했다. 한도·derivation·stop 규칙·권한 필드는 모두 불변이다. 과거 측정값/hash를 덮어쓰지 않았다.

게시 시 해당 main wrapper는 21:44:45에 종료했고 canary/collector/bot 또는 해당 코드의 운영 producer가 실행 중이지 않음을 확인했다. 자연 생성 보고서·실행 snapshot은 교체하지 않았다. frozen baseline 포함 직접 회귀 27 PASS. 이 게시가 Main AI 활성화, 성능 향상률, 실거래 경제성 또는 새 PID 적용을 의미하지 않는다. 측정 당시 prospective 상태는 원본 증거로 유지한다.

## 재생성 판정과 단일 owner

| 경로 | 확인한 세대/필요 작업 | 실행 owner |
| --- | --- | --- |
| Main AI #77/current-axis/#80 | wrapper snapshot SHA `63cb2f238beb056818574bbdc457b22bdc2f606cb8fab960c37177d9b0e7c695`가 이번 source와 일치. 21:39 R0-R3 및 21:41 consumer 생성. git commit 자체 때문에 재실행할 필요 없음 | 기존 장후 controller/follower; terminal detailed 후 지정된 재결속만 |
| Daily/cumulative/calibration/AI/EV 및 smoothing verifier | 21:44 실패 뒤 21:47 이후 수정되었으므로 새 코드의 최소 producer→하류 재생성 필요. 이전 산출물을 이번 commit의 산출물로 주장하지 않음 | [진행 중인 장후 복구 세션](2026-09-07-postclose-monitoring-recovery-review.md), 기존 `AutomationTriggerDecisionSummary0907` |
| Workorder/Samsung/low-price | 복구 세션이 21:51 이후 최소 재생성, workorder v4 세대 `2026-09-07-e930940341be` 확인. 후속 source hash 변화 시 같은 owner가 영향 하류만 재결속 | 같은 복구 세션 |
| Verifier/controller/finalization | 마지막 source 재생성 뒤 최신 terminal을 다시 확인해야 함. 21:44 main FAIL과 21:55 finalization FAIL을 git 통합 성공으로 덮지 않음 | 같은 복구 세션 |
| Callback benchmark 기준 | 새 측정과 frozen hash 검사로 종결; 경제성 report 재생성 불필요 | 이번 소스 통합 |

이 세션은 운영 report의 별도 중복 재실행을 시작하지 않는다. 기존 source-only 경고·유효 R3 후보 부재 및 등록/승인 미발행은 자연 acceptance owner를 유지한다. 코드 통합 완료와 장후 GREEN/fixed-point 완료는 다른 판정이다.

## 최종 검증

- 최종 통합 33-file 회귀 **2,174 PASS / 90.19초**, 추가 실제 점수 gate/관측 회귀 **5 PASS**. 후자는 pandas_ta의 기존 pandas 옵션 deprecation warning 1건이며 테스트 실패가 아니다. 총 **2,179 PASS**, 앞서 실패한 frozen 기준 검사도 최종 통합에 포함했다.
- 저장소 전체 Black no-cache **880개 파일 PASS**, 신규/직접 보완 9 production 모듈 Ruff PASS, staged Python 전체 compile, shell wrapper 2개 `bash -n`, staged/working diff check PASS.
- Print-only 문서 parser PASS(64 OPEN). 문서 계약 테스트 3개는 위 통합 회귀에 포함했다. 외부 Project/Calendar sync 또는 token 확인은 수행하지 않았다.
- 테스트 후 `src/deploy/configs`의 unstaged diff 0으로 검사 대상과 index가 일치함을 확인했다. 병행 복구의 추가 코드는 변경됐다는 이유만으로 무검증 포함하지 않는다.
- 위 producer/consumer/authority·문서 및 frozen 참조의 검토 범위 미해결 finding 0. 저장소의 모든 무관한 테스트, 자연 시장 부하, Provider 성능/실거래 EV까지 검증했다는 뜻은 아니다.

장후 전체 상태는 이 통합의 완료조건이 아니며 복구 세션의 최신 terminal 보고를 따른다. main push와 자연 재생성 결과를 혼동하지 않는다.
