# Claude Scalping Pattern Lab 폐기 검증

작성일: 2026-09-18 KST. 사용자 승인: 구현·반복 리뷰/수정/검증·관련 commit/push·immutable 배포와 불필요 산출물 삭제. 봇 재시작·주문·조기 PREOPEN 확정은 제외한다.

Owning plan: [PLR0–PLR6](../proposals/claude-scalping-pattern-lab-and-automation-retirement-plan-2026-09-18.md). 관련 source만 격리 worktree에서 검증하며 다른 세션 변경과 실행 중 release를 보존한다.

## 변경과 리뷰

- 전용 Claude 코드/config/prompt/output·scalping automation·cron wrapper와 전용 테스트를 삭제했다. Main 및 보조 tuning override 실행도 제거했다.
- EV/workorder/runtime summary/tower/checklist의 source intake와 Main trigger/controller/verifier/freshness 요구를 폐기했다. source identity로 과거 orders/non-selected를 제외하며 같은 ID의 다른 독립 owner와 기존 family는 보존한다.
- 공용 currentness/AI review/propagation은 기존 Swing caller 때문에 유지한다. 삭제 모듈 import·Claude producer 소비를 제거하고 Main `--exclude-swing` 호출은 파일/provider 접근 전 retired terminal을 반환한다. Swing OFF를 활성화하지 않는다. 공유 observability는 기존 Gemini caller의 계산만 보존한다.
- 리뷰에서 삭제 import, old monitoring override, unknown-profile recovery, obsolete source fingerprint, preserved AUTO task 전이 및 retired OFF에 따른 verifier false warning을 보완했다. 비퇴역 source/hash/정책 검사와 hard safety는 유지한다.

## 검증·배포·삭제 증거

격리 successor의 targeted pytest 20파일 **1,135 PASS**(Main consumer375 + 기타 계약760), 수정 Python33개 compile PASS, shell3개 `bash -n` PASS, `git diff --check` PASS와 print-only parser PASS다. 저장 보고서와 반환값의 일치, 삭제/과거 양수 입력, unknown-profile recovery 차단 및 독립 owner 보존을 검증했다. 합성 회귀는 자연 경제성 실증이 아니다. `tmp/claude-lab-retirement-20260918/validation.json` 및 두 tests 로그를 따른다. 배포·제한 refresh·cleanup은 후속 실제 receipt에서 고정한다.

## 정책과 경제성 경계

Lab 전용 실전 정책은 없으며 이번 폐기는 기존 다음 적용일 정책 값을 새로 계산하거나 승격하지 않는다. 모델 ΔEV·실제 순익·인과적 EV 개선은 이번 코드 제거로 입증되지 않는다. 9/21 정책/PREOPEN 원천의 보호 SHA와 자연 적용·완료 손익은 기존 독립 owner의 경계를 유지한다. 선택된 successor는 미래 invocation에 사용되고 실제 Main PID 소비/재시작은 수행하지 않는다.

## PLR0–PLR6 최종 판정

| 단계 | 판정 | 실제 근거 |
| --- | --- | --- |
| PLR0 | 완료 | producer/consumer/shared caller·active consumer·protected owner·canonical merge manifest |
| PLR1 | 완료 | 전용 CLI/shell 삭제, Main/보조 override 제거, legacy true flag 회귀, 실제 전용 cron0 |
| PLR2 | 완료 | Main source intake/복구/trigger/verifier/freshness·AUTO 일정 전이 차단; 저장값 회귀 및 자연 보고서 source 검증 |
| PLR3 | 완료 | Claude 전용 코드와 automation 삭제; 기존 Swing shared caller와 Gemini observability 계산만 보존 |
| PLR4 | 완료 | 20파일1,135PASS·Python33 compile·shell3·diff/parser PASS; 배포본 추가223PASS |
| PLR5 | 완료 | source50cc737bc atomic main/review push·immutable successor 선택·router print-plan 및 제한 공용 refresh |
| PLR6 | 완료 | 불필요643개7,996,508bytes 삭제·보호SHA15개 불변·활성/유예0·삭제 후 consumer/fingerprint/source generation 검증 |

Source commit: `50cc737bce0bfddd2ef29d614a2f9cfaa5ff2615`. 선택 root: `/home/ubuntu/KORStockScan-runtime-releases/claude-lab-retired-reviewed-20260918`. 원격 main과 review branch push는 성공했으며, 선택은 future invocation 전용이다. 선택 receipt의 `actual_pid_consumed=false`이며 Main PID 기동/재시작·주문·조기 PREOPEN 확정은 수행하지 않았다. 실행 중 이전 immutable release는 직접 수정하지 않았다. Canonical working copy는 task diff를 3-way로 반영해 기존 독립 변경을 보존했다. 관련 문서 evidence는 후속 문서 커밋으로 push하며 runtime source hash는 위 source commit이다.

9/17 원천에서 EV → workorder → 최종 EV → 최종 workorder → runtime summary → runtime gap → trigger → tower → 9/21 checklist를 제한 갱신했다. 원 grid/개별 튜너/원천 적재·새 provider 계산은 반복하지 않았다. runtime gap candidate0에 AI review `not_required`다. 날짜별 정책 값은 보존했으며 publication9/18·next apply9/21을 자연 적용과 분리했다. 실제 workorder fingerprint와 tower source generation은 current이며 active Claude/scalping/shared Main Lab source 참조 및 Lab missing/stale/handoff issue는0이다. 제거 경로는 검증 후 재생성되지 않았다.

Cleanup manifest는 현재 policy/PREOPEN/선택 배포 근거17개를 제한 스트리밍 확인했다. 해당 후보 파일의 보호 hash/필수 경로 참조는0이며, old stepwise outputs에도 활성 cwd/lock holder가 없었다. 검증된 future successor 선택·공용 consumer refresh 후 ignored 파생물639개와 이미 관련 diff로 삭제된 tracked output4개를 대사했다. 별도 중복 CLI 임시 JSON3개18,995,147bytes도 정리하고 canonical 산출물 hash/size receipt를 보존했다. raw/order/custody·정책·서명 원천 bundle·이전 release 전체는 삭제하지 않았다.

최종 receipts: `validation.json`, `deployment.json`, `router-postclose-plan.json`, `router-tuning-plan.json`, `refresh-actions.json`, `consumer-closure.json`, `cleanup-manifest.json`, `cleanup-receipt.json`, `temporary-output-cleanup.json`, `deployed-tests.log`, `parser-canonical.log` (모두 `tmp/claude-lab-retirement-20260918/`).

## 전체 체인의 기존 OPEN과 적용 경계

실제 native verifier는 Lab 범위 결함0·stale links0·source generation warnings0·handoff warnings0이나 **전체 status는 FAIL**이다. 저가주9/17 report/policy contract/hash/schema/authority/profile/date 불일치, machine timing applied-policy FileNotFoundError, 이전 postclose fail marker 및 Swing simulation/audit missing이 그대로 남는다. 이는 이번 폐기 scope의 수리/재실행 대상이 아니며 verifier를 완화하거나 전체 DONE/9/21 실전 승인을 합성하지 않았다. 상세 원인은 `consumer-closure.json`의 `preexisting_out_of_scope_issues`와 native verifier를 따른다. 실행 owner는 기존 low-price·machine timing·postclose-chain checklist를 유지하며 새 중복 OPEN을 만들지 않는다.

따라서 이번 완료는 **Lab 계통의 코드·소비·복구·불필요 산출물 폐기 및 승인된 선택 배포**다. 다음 영업일 자연 invocation/PID 소비와 기존 정책의 PREOPEN 확인·완료 비용 손익/인과적 개선은 별도 기존 OPEN이다. Lab 정책이나 신규 양수 EV는 생성/보장하지 않는다.

## 후속 재리뷰·수정보완 및 중복 임시 산출물 정리

폐기된 원천을 `cross_domain`/`swing`, 대문자·공백 domain, symbolic source label, flat filename 또는 owner field로 표시하면 기존 domain-only 필터를 우회했다. 또한 deterministic currentness 실패의 재주입은 최초 필터 이후에 실행되어 과거 Claude 검사가 작업지시로 재등장할 수 있었다. 신규 회귀2건에서 수리 전 실제 실패를 재현했다.

원본 provider response/hash는 변경하지 않고, effective conclusions와 orders 생성 경계에서 폐기 Lab identity를 제외한다. metadata-only response refresh와 deterministic 재주입에도 동일 검사를 적용한다. 기존 Swing owner, source-quality fail-closed와 provider budget·hash/currentness 검사는 보존한다. 전역 퇴역 필터를 확장하지 않으며 비-Claude 진단 resolution을 제거하지 않는다. 과거 Claude fixture로 남은 generic integrity 검사는 현행 Swing fixture로 전환해 실패 강제·35개 전체 검사·native owner 중복 방지 검증을 유지했다.

영향 범위5파일 pytest **427 PASS**, 변경 Python3개 compile 및 diff check PASS다. 테스트는 통제 입력이며 자연 경제성/실제 손익 증거가 아니다. 운영 wrapper·정책 생성 로직은 이번 후속에서 바뀌지 않아 전체 장후 재실행·provider 호출·조기 PREOPEN을 수행하지 않는다. 기존 전체 verifier FAIL/타 축 OPEN을 이 결과로 닫지 않는다.

추가 삭제는 최종 영수증과 동일 정보인 중간 3-way merge 사본44개 **6,044,845bytes**다. 활성 FD0 및 보호 정책·원천15개 SHA 불변을 확인하고 파일별 hash/size를 남겼다. 이전 삭제643개는 재삭제/신규 실적으로 중복 계수하지 않는다. 현행 전용 산출물 경로는 비어 있다. 다른 worktree의 tracked 과거 source 사본, immutable release, raw/order/custody 및 최종 검증·배포 영수증은 보존한다.

추가 evidence: `tmp/claude-lab-retirement-20260918/followup-review-tests.log`, `followup-validation.json`, `followup-cleanup-receipt.json`, `followup-deployment.json`. 관련 source를 기존 격리 branch에서 commit/push하고 검증된 immutable successor로 선택하며 실제 선택 SHA/root는 마지막 deployment receipt가 소유한다. 이전 선택본을 직접 수정하거나 Main PID를 재시작하지 않는다.
