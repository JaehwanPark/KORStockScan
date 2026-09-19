# Compact AI 경제성 최적화 구현·배포 리뷰

작성일: 2026-09-19 KST. 범위: [통합 계획 §11–§18](../proposals/compact-ai-postclose-source-paired-evaluation-and-preopen-consumer-integration-plan-2026-09-19.md)의 실행 가능한 후속 구현, 리뷰, 배포와 source9/17 제한 재생성.

## 결론

실행 가능한 구조 결손 수리는 완료했다. 정상 운영 producer가 만든 frozen plan을 경제성 비교와 정책 소비까지 전달하는 기존 경로를 재사용했고, 응답 오류의 잘못된 scope 분류·stale projection 재사용·최종 phase 상태·표본 미달 연구값 관측을 보완했다. 자연21건은 여전히 경제 비교 불가이므로 양수 후보·모델 ΔEV·실제 이익을 주장하지 않는다.

최종 commit은 `411ec0efdf993ec11e36b3fc79b78a5a7a36a6e1`; main push와 immutable release `compact-economic-optimized-reviewed-20260919-411ec0efd` 선택을 확인했다. 이전 WS economics release의 변경을 포함한다. 실제 PID 소비는 false이며 봇 재기동·주문·조기 PREOPEN·provider/수량/cap/hard guard 변경은 없다.

## 구현과 리뷰

1. `compact_auxiliary_paired_replay`가 자연 provider/model·transport·semantic 오류를 구분하며 모두 source gap으로 처리한다. `unsupported_scope`는 명시 route/model/자본 지원 범위 판정에만 사용한다.
2. projection contract v6가 과거 v4/v5의 frozen `natural_contract_evidence`로만 blocker를 migration한다. raw 전수 재스캔과 과거 응답 추정이 없다. migration 뒤 동일 입력은 current hash로 재사용한다.
3. paired 결과에 decision changed/unchanged와 비용 반영 research status, promotion primary metric, 모델 ΔEV와 실제 이익 분리를 기록한다. 기존 수량·예산·guard·모델 오차·stress·holdout·tail 승격 조건은 변경하지 않았다.
4. blocker 영수증은 첫 producer owner와 closure test를 가리킨다. prepare/evaluate/finalize 실행 상태와 경제 상태를 분리하고 terminal handoff는 consumer receipt로 확인한다.
5. 기존 runtime producer 회귀는 KRX/NXT/SOR 및 프리마켓·정규장·통합 애프터마켓, census, stop/cost, owner replay, reserve/exposure를 통과한다. 직접 작성한 evaluator row만으로 producer 완료를 주장하지 않는다.

첫 리뷰에서 새 분류가 유효한 과거 projection/report 캐시에 반영되지 않는 문제를 찾아 v5 bounded migration을 추가했다. 제한 재생성에서 timeout8이 semantic으로 합쳐지는 문제를 다시 찾아 timeout evidence 계약을 보완하고 v6 migration을 추가했다. 두 보완 모두 raw를 읽지 않는 회귀로 재검증했다.

## 검증

- 최초 영향 범위: 590 passed.
- 다른 세션 WS pricing commit 재배치 후: 295 passed, 경고1은 기존 pandas-ta deprecation.
- cache migration·분류 보완: 3 passed, 6 passed, 재배치 후49 passed.
- immutable release: 중간13/9/10 passed, 최종 release10 passed.
- Python compile, `bash -n` wrapper, `git diff --check` PASS.
- source9/17 compact strict verifier: `PASS`, `scope=compact_auxiliary_only`, `whole_native_chain_done_claimed=false`.

초기 release 조립에서 `restart.flag` link 누락과 중간 selector의 잘못 확장한 full SHA를 router가 각각 차단했다. 실행은 시작되지 않았고 link·정확한 Git SHA를 보완한 뒤 postclose9/19와 PREOPEN9/21 print-plan이 최종 release/commit을 가리키는 것을 확인했다.

## 제한 재생성과 준비 정책

| 항목 | 결과 |
| --- | --- |
| source/publication/effective | 2026-09-17 / 2026-09-19 / 2026-09-21 |
| screen/source gap/eligible/comparable | 21 / 21 / 0 / 0 |
| first blocker | stop10, transport8, semantic1, label identity2 |
| provider 호출/raw 재스캔 | 0 / 0 (`raw_not_read=true`) |
| ΔEV·일별 순익·robust lower·실제 이익 | null / null / null / null |
| 후보·승격 scope | 0 / `[]` |
| 정책 | `entry_machine_auxiliary_compact_v3` incumbent carry |
| bundle | `fb4870b8ab479897c7580d79a92acb2595889c2d7c95b75087bcef6cfb6f74c5` |
| 소비 | effective9/21 consumer 연결, scoped strict PASS |

재생성 전후 보호 raw size/mtime는 불변이다. machine policy와 비compact scope9도 보존했다. 정책 파일 생성은 실제 PID 소비나 수익 개선이 아니다.

## 남은 자연 OPEN

`KiwoomCommonHealthOpportunityCostAcceptance0917`가 다음 정상 producer 입력의 plan/stop/cost/census, scope별 actual calibration과 선행 model holdout, 독립 candidate holdout, 정규 PREOPEN/PID issued prompt, joint-version 완료 비용 손익을 확인한다. 현재 과거21건은 재평가 대상으로 반복하지 않는다. 다음 입력에서 지원 경제값이 나오면 표본 미달 연구값도 표시되며, 승격은 기존 독립 검증을 모두 통과할 때만 발생한다.

운영 증거: `tmp/compact-economic-optimization-20260919/deployment.json`, `regeneration.json`, `before-regeneration/manifest.json`. selector와 consumer 모두 actual PID false다.

## 후속 재리뷰와 과거 산출물 정리

후속 코드리뷰에서 compact 계산·분류·승격·fallback 코드의 새 결함은 발견하지 않았다. 다만 Git의 9/21 checklist handoff가 이전 bundle `833053c3…`에 머문 반면 실제 정책·consumer와 shared checklist는 `fb4870b8…`를 소비하고 있었다. 현재 consumer에서 생성된 compact handoff 블록만 Git 문서에 다시 결속했으며 다른 자동 생성 구간은 가져오지 않았다.

writer·postclose process와 lock holder가 없음을 확인한 뒤, 현재 v6 projection이 직접 가리키는 v5 `71b27cb2…`와 그 원본 v4 `c7ee6dd0…`를 보존하고 참조되지 않는 구 generation 8개를 삭제했다. 중복 prepare/evaluate/finalize 출력·중복 parser/test 로그와 최종 selector가 참조하지 않는 중간 selection backup 17개도 삭제했다. 총 25개, 411,256 bytes다. 현재 projection/report·원 trace/payload·정책·consumer·직계 migration lineage·selected/previous release rollback·배포/재생성/strict 영수증은 보존했다. 삭제 목록과 보호 hash는 `tmp/compact-artifact-cleanup-20260919/manifest.json`에 기록했다.

영향 범위 333건 PASS 후 정리했으며, 삭제 뒤 compact scoped strict verifier와 consumer handoff 검증이 다시 PASS했다. `whole_native_chain_done_claimed=false`, 실제 PID 소비 false, ΔEV·실제 순익 null은 변하지 않는다.

정리·handoff commit `8143121b6005b908520fc3c8dca5160f82c50d2f`을 main에 push하고 immutable release `compact-economic-cleanup-reviewed-20260919-8143121b6`를 선택했다. 물리 release 6건, compile·wrapper syntax, POSTCLOSE9/19·PREOPEN9/21 route print-plan과 배포 후 scoped strict/consumer 검증을 통과했다. 영수증은 `tmp/compact-artifact-cleanup-20260919/deployment.json`이다. future invocation만 전환했으며 bot 재기동·주문·조기 PREOPEN은 없다.
